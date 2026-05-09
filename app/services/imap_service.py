import imaplib
import re
import socket
import time
from collections.abc import Mapping
from typing import Any

from app.config import ImapConfig
from app.services.mail_parser import MailParser


class IMAPService:
    """Outlook IMAP network client."""

    def __init__(self, config: ImapConfig, parser: MailParser | None = None) -> None:
        self._config = config
        self._parser = parser or MailParser()

    def list_messages(
        self,
        account: Mapping[str, Any],
        access_token: str,
        folder: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        email = str(account.get('email', '')).strip()
        if not email:
            raise ValueError('缺少邮箱地址，无法连接 IMAP')
        if not access_token:
            raise ValueError('缺少 Access Token，无法连接 IMAP')

        folder_name = folder or self._config.default_folder
        page_size = limit or self._config.page_size
        started_at = time.perf_counter()
        client = self._connect(email, access_token)
        try:
            connected_at = time.perf_counter()
            # 列表页只需要邮件头，不能下载整封邮件，否则 20 封大邮件会明显拖慢首屏。
            self._select_folder(client, folder_name)
            uids = self._fetch_recent_uids(client, page_size)
            searched_at = time.perf_counter()
            # 优先批量取头，减少网络往返；Outlook 偶尔返回格式不稳定，所以后面还有逐封 fallback。
            headers_by_uid = self._fetch_headers_by_uid(client, uids)
            fetched_at = time.perf_counter()
            messages: list[dict[str, Any]] = []
            for uid in uids:
                raw_bytes = headers_by_uid.get(uid, b'')
                if not raw_bytes:
                    # 批量响应里没有这个 UID 时，逐封取头，仍然比整封下载轻。
                    raw_bytes = self._fetch_header_bytes(client, uid)
                if not raw_bytes:
                    # 最后的正确性兜底。速度慢一些，但不能因为优化导致有邮件却显示空。
                    raw_bytes = self._fetch_message_bytes(client, uid)
                    if not raw_bytes:
                        continue
                    messages.append(self._parser.parse_message_bytes(uid, folder_name, raw_bytes))
                else:
                    messages.append(self._parser.parse_header_bytes(uid, folder_name, raw_bytes))
            parsed_at = time.perf_counter()
            self._log(
                'list timing: '
                f'folder={folder_name}, uid_count={len(uids)}, '
                f'connect={connected_at - started_at:.2f}s, '
                f'search={searched_at - connected_at:.2f}s, '
                f'fetch_headers={fetched_at - searched_at:.2f}s, '
                f'parse={parsed_at - fetched_at:.2f}s, '
                f'total={parsed_at - started_at:.2f}s'
            )
            return messages
        finally:
            self._safe_logout(client)

    def fetch_message_detail(
        self,
        account: Mapping[str, Any],
        access_token: str,
        uid: str,
        folder: str | None = None,
    ) -> dict[str, Any]:
        email = str(account.get('email', '')).strip()
        if not email:
            raise ValueError('缺少邮箱地址，无法连接 IMAP')
        if not access_token:
            raise ValueError('缺少 Access Token，无法连接 IMAP')

        folder_name = folder or self._config.default_folder
        client = self._connect(email, access_token)
        try:
            # 详情页需要正文，所以这里读取整封 RFC822。列表页不要走这个路径。
            self._select_folder(client, folder_name)
            raw_bytes = self._fetch_message_bytes(client, uid)
            if not raw_bytes:
                raise ValueError('未找到该邮件内容')
            return self._parser.parse_message_bytes(uid, folder_name, raw_bytes)
        finally:
            self._safe_logout(client)

    def delete_message(
        self,
        account: Mapping[str, Any],
        access_token: str,
        uid: str,
        folder: str | None = None,
    ) -> None:
        # 这里做的是 IMAP 层面的真实删除，不是仅仅把前端列表项移除。
        email = str(account.get('email', '')).strip()
        if not email:
            raise ValueError('邮箱账号不能为空，无法连接 IMAP')
        if not access_token:
            raise ValueError('Access Token 不能为空，无法连接 IMAP')

        folder_name = folder or self._config.default_folder
        client = self._connect(email, access_token)
        try:
            self._select_folder(client, folder_name)
            # IMAP 删除通常分两步：先标记 \\Deleted，再 expunge 真正清理。
            status, _ = client.uid('store', uid, '+FLAGS', '(\\Deleted)')
            if status != 'OK':
                raise ValueError('邮件删除失败，服务器没有接受删除标记')

            expunge_status, _ = client.expunge()
            if expunge_status != 'OK':
                raise ValueError('邮件删除失败，服务器没有完成清理操作')
        finally:
            self._safe_logout(client)

    def _connect(self, email: str, access_token: str) -> imaplib.IMAP4_SSL:
        """Open the SSL connection and authenticate with Microsoft OAuth2."""

        try:
            client = imaplib.IMAP4_SSL(self._config.host, self._config.port, timeout=25)
        except TimeoutError as exc:
            raise ValueError('读取邮件失败：连接 Outlook IMAP 超时，请检查网络或代理后重试') from exc
        except OSError as exc:
            raise ValueError(f'读取邮件失败：无法连接 Outlook IMAP（{self._config.host}:{self._config.port}）') from exc

        auth_string = self._build_xoauth2_string(email, access_token)
        try:
            client.authenticate('XOAUTH2', lambda _: auth_string)
        except imaplib.IMAP4.error as exc:
            self._safe_logout(client)
            raise ValueError('读取邮件失败：IMAP 认证未通过，请确认该账号已授权 IMAP 权限，并重新刷新 Token') from exc
        except socket.timeout as exc:
            self._safe_logout(client)
            raise ValueError('读取邮件失败：IMAP 认证超时，请稍后重试') from exc
        return client

    def _select_folder(self, client: imaplib.IMAP4_SSL, folder_name: str) -> None:
        status, _ = client.select(folder_name)
        if status != 'OK':
            display_name = self._display_folder_name(folder_name)
            raise ValueError(f'读取邮件失败：无法打开“{display_name}”文件夹，请确认该文件夹在邮箱中存在')

    def _fetch_recent_uids(self, client: imaplib.IMAP4_SSL, limit: int) -> list[str]:
        status, data = client.uid('search', None, 'ALL')
        if status != 'OK':
            raise ValueError('读取邮件失败：邮箱服务器未能返回邮件列表')
        if not data or not data[0]:
            return []
        uids = data[0].decode('utf-8', errors='ignore').split()
        # IMAP 返回顺序是从旧到新，界面需要最新邮件在前面。
        return list(reversed(uids[-limit:]))

    def _fetch_message_bytes(self, client: imaplib.IMAP4_SSL, uid: str) -> bytes:
        status, data = client.uid('fetch', uid, '(RFC822)')
        if status != 'OK' or not data:
            return b''
        for item in data:
            if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes):
                return item[1]
        return b''

    def _fetch_headers_by_uid(self, client: imaplib.IMAP4_SSL, uids: list[str]) -> dict[str, bytes]:
        if not uids:
            return {}

        # BODY.PEEK 只读取邮件头，不会把邮件标记为已读。
        status, data = client.uid('fetch', ','.join(uids), '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO DATE)])')
        if status != 'OK' or not data:
            return {}

        headers_by_uid: dict[str, bytes] = {}
        for item in data:
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            metadata, header_bytes = item[0], item[1]
            if not isinstance(metadata, bytes) or not isinstance(header_bytes, bytes):
                continue
            # 批量 fetch 的每个响应都会带 UID，从这里把 header bytes 归到对应邮件。
            match = re.search(rb'\bUID\s+(\d+)\b', metadata)
            if match:
                headers_by_uid[match.group(1).decode('ascii')] = header_bytes
        return headers_by_uid

    def _fetch_header_bytes(self, client: imaplib.IMAP4_SSL, uid: str) -> bytes:
        status, data = client.uid('fetch', uid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO DATE)])')
        if status != 'OK' or not data:
            return b''
        for item in data:
            if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes):
                return item[1]
        return b''

    @staticmethod
    def _display_folder_name(folder_name: str) -> str:
        if folder_name == 'INBOX':
            return '收件箱'
        if folder_name == 'Junk':
            return '垃圾邮件'
        return folder_name

    @staticmethod
    def _build_xoauth2_string(email: str, access_token: str) -> bytes:
        # imaplib.authenticate() will base64-encode the callback result itself.
        # Returning an already encoded payload causes XOAUTH2 authentication to fail.
        return f'user={email}\x01auth=Bearer {access_token}\x01\x01'.encode('utf-8')

    @staticmethod
    def _safe_logout(client: imaplib.IMAP4_SSL) -> None:
        try:
            client.logout()
        except Exception:
            pass

    @staticmethod
    def _log(message: str) -> None:
        print(f'[IMAPService] {message}', flush=True)
