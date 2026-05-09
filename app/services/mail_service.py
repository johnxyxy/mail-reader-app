import time
from datetime import datetime
from typing import Any

from app.config import AppConfig, DEFAULT_CONFIG
from app.services.imap_service import IMAPService
from app.services.mail_parser import MailParser
from app.services.oauth_service import OAuthService
from app.storage.account_repository import AccountRepository


class MailService:
    """邮件业务层：把数据库账号、OAuth、IMAP 和邮件解析串起来。"""

    def __init__(
        self,
        repository: AccountRepository | None = None,
        oauth_service: OAuthService | None = None,
        imap_service: IMAPService | None = None,
        parser: MailParser | None = None,
        config: AppConfig = DEFAULT_CONFIG,
    ) -> None:
        self._repository = repository or AccountRepository()
        self._oauth_service = oauth_service or OAuthService(config.oauth)
        self._parser = parser or MailParser()
        self._imap_service = imap_service or IMAPService(config.imap, self._parser)
        self._config = config
        # access_token 有效期较短，但同一次运行里列表和详情通常会连续读取。
        # 缓存 45 分钟可以少走几次 Microsoft OAuth 网络请求。
        self._access_token_cache: dict[int, tuple[str, float]] = {}

    def refresh_account_token(self, account_id: int) -> dict[str, str]:
        # 从数据库取出 client_id/refresh_token，向微软换取新的 access_token。
        self._log(f'refresh token started: account_id={account_id}')
        account = self._get_account_dict(account_id)
        try:
            token_payload = self._oauth_service.refresh_access_token(account)
        except Exception as exc:
            # 刷新失败时写回 last_error，账号卡片上才能看到原因。
            self._repository.mark_error(account_id, str(exc))
            self._log(f'refresh token failed: account_id={account_id}, message={exc}')
            raise

        refresh_token = token_payload.get('refresh_token') or account.get('refresh_token', '')
        now_text = datetime.now().strftime('%Y-%m-%d %H:%M')
        # Microsoft 可能轮换 refresh_token，成功刷新后必须写回数据库，否则下次启动可能失效。
        self._repository.update_refresh_token(account_id, refresh_token, now_text)
        self._access_token_cache[account_id] = (str(token_payload.get('access_token', '')), time.monotonic() + 45 * 60)
        self._log(f'refresh token succeeded: account_id={account_id}, time={now_text}')
        return token_payload

    def list_messages(self, account_id: int, folder: str | None = None) -> list[dict[str, Any]]:
        # 拉取列表前取得 access_token，然后用它登录 IMAP。短时间内复用 token，减少额外网络等待。
        account = self._get_account_dict(account_id)
        target_folder = folder or self._config.imap.default_folder
        self._log(f'list messages started: account_id={account_id}, folder={target_folder}')
        try:
            access_token = self._get_access_token(account_id, account)
            messages = self._imap_service.list_messages(
                account=account,
                access_token=access_token,
                folder=target_folder,
                limit=self._config.imap.page_size,
            )
            self._log(f'list messages succeeded: account_id={account_id}, folder={target_folder}, count={len(messages)}')
            return messages
        except Exception as exc:
            self._repository.mark_error(account_id, self._with_read_context(str(exc), target_folder))
            self._log(f'list messages failed: account_id={account_id}, folder={target_folder}, message={exc}')
            raise

    def fetch_message_detail(self, account_id: int, uid: str, folder: str | None = None) -> dict[str, Any]:
        # 列表只显示摘要；点击某封邮件时再按 UID 拉取完整原文。
        account = self._get_account_dict(account_id)
        target_folder = folder or self._config.imap.default_folder
        self._log(f'fetch detail started: account_id={account_id}, folder={target_folder}, uid={uid}')
        try:
            access_token = self._get_access_token(account_id, account)
            detail = self._imap_service.fetch_message_detail(
                account=account,
                access_token=access_token,
                uid=uid,
                folder=target_folder,
            )
            self._log(f'fetch detail succeeded: account_id={account_id}, folder={target_folder}, uid={uid}')
            return detail
        except Exception as exc:
            self._repository.mark_error(account_id, self._with_read_context(str(exc), target_folder))
            self._log(f'fetch detail failed: account_id={account_id}, folder={target_folder}, uid={uid}, message={exc}')
            raise

    def delete_message(self, account_id: int, uid: str, folder: str | None = None) -> None:
        # 这一层只做业务编排：拿账号、拿 token、调用 IMAP 删除，并把错误统一回写到账号状态。
        account = self._get_account_dict(account_id)
        target_folder = folder or self._config.imap.default_folder
        self._log(f'delete message started: account_id={account_id}, folder={target_folder}, uid={uid}')
        try:
            access_token = self._get_access_token(account_id, account)
            self._imap_service.delete_message(
                account=account,
                access_token=access_token,
                uid=uid,
                folder=target_folder,
            )
            self._log(f'delete message succeeded: account_id={account_id}, folder={target_folder}, uid={uid}')
        except Exception as exc:
            self._repository.mark_error(account_id, self._with_read_context(str(exc), target_folder))
            self._log(f'delete message failed: account_id={account_id}, folder={target_folder}, uid={uid}, message={exc}')
            raise

    def _get_access_token(self, account_id: int, account: dict[str, Any]) -> str:
        cached = self._access_token_cache.get(account_id)
        if cached and cached[1] > time.monotonic():
            self._log(f'use cached access token: account_id={account_id}')
            return cached[0]

        # 缓存不存在或过期时才刷新。这里复用 refresh_account_token，让错误记录和数据库更新逻辑保持一致。
        token_payload = self.refresh_account_token(account_id)
        access_token = str(token_payload.get('access_token', ''))
        self._access_token_cache[account_id] = (access_token, time.monotonic() + 45 * 60)
        return access_token

    @staticmethod
    def _with_read_context(message: str, folder: str) -> str:
        # 底层已经翻译过的错误不重复包装；其他错误补上文件夹名称。
        if message.startswith('读取邮件失败：') or message.startswith('刷新 Token 失败：'):
            return message

        folder_name = '收件箱' if folder == 'INBOX' else '垃圾邮件' if folder == 'Junk' else folder
        return f'读取邮件失败：打开“{folder_name}”时出错，{message}'

    def _get_account_dict(self, account_id: int) -> dict[str, Any]:
        account = self._repository.get_account(account_id)
        if account is None:
            raise ValueError('未找到该邮箱账号')

        return {
            'id': int(account.id),
            'email': account.email,
            'password': account.password or '',
            'client_id': account.client_id or '',
            'refresh_token': account.refresh_token or '',
            'remark': account.remark or '',
            'last_refresh_time': account.last_refresh_time or '',
            'last_error': account.last_error or '',
        }

    @staticmethod
    def _log(message: str) -> None:
        print(f'[MailService] {message}', flush=True)
