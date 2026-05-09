from collections.abc import Mapping
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime, parseaddr
from html import escape
from typing import Any


class MailParser:
    """把 IMAP 原始邮件解析成前端可直接消费的字典。"""

    def normalize_message(self, raw_message: Mapping[str, Any]) -> dict[str, Any]:
        """把已有邮件字典补齐为前端约定的数据形状。"""
        return {
            'uid': str(raw_message.get('uid', '')),
            'subject': str(raw_message.get('subject', '')),
            'from_name': str(raw_message.get('from_name', '')),
            'from_address': str(raw_message.get('from_address', '')),
            'to_address': str(raw_message.get('to_address', '')),
            'date_text': str(raw_message.get('date_text', '')),
            'preview': str(raw_message.get('preview', '')),
            'body_text': str(raw_message.get('body_text', '')),
            'body_html': str(raw_message.get('body_html', '')),
            'folder': str(raw_message.get('folder', 'INBOX')),
            'is_read': bool(raw_message.get('is_read', True)),
        }

    def parse_message_bytes(self, uid: str, folder: str, raw_bytes: bytes) -> dict[str, Any]:
        """把整封原始邮件解析成包含正文的详情字典。"""
        message = message_from_bytes(raw_bytes)
        subject = self._decode_header_value(message.get('Subject', ''))
        from_name, from_address = self._parse_mailbox(message.get('From', ''))
        _, to_address = self._parse_mailbox(message.get('To', ''))
        date_text = self._format_date(message.get('Date', ''))
        body_text, body_html = self._extract_bodies(message)
        preview = body_text.replace('\r', ' ').replace('\n', ' ').strip()[:180]
        return {
            'uid': uid,
            'subject': subject or '(无主题)',
            'from_name': from_name,
            'from_address': from_address,
            'to_address': to_address,
            'date_text': date_text,
            'preview': preview,
            'body_text': body_text,
            'body_html': body_html,
            'folder': folder,
            'is_read': True,
        }

    def parse_header_bytes(self, uid: str, folder: str, raw_bytes: bytes) -> dict[str, Any]:
        """把邮件头解析成列表页需要的轻量字典。"""
        message = message_from_bytes(raw_bytes)
        subject = self._decode_header_value(message.get('Subject', ''))
        from_name, from_address = self._parse_mailbox(message.get('From', ''))
        _, to_address = self._parse_mailbox(message.get('To', ''))
        date_text = self._format_date(message.get('Date', ''))
        return {
            'uid': uid,
            'subject': subject or '(无主题)',
            'from_name': from_name,
            'from_address': from_address,
            'to_address': to_address,
            'date_text': date_text,
            'preview': '',
            'body_text': '',
            'body_html': '',
            'folder': folder,
            'is_read': True,
        }

    @staticmethod
    def _decode_header_value(value: str) -> str:
        """解码可能带 MIME 编码的邮件头文本。"""
        if not value:
            return ''
        try:
            return str(make_header(decode_header(value)))
        except Exception:
            return value

    def _parse_mailbox(self, value: str) -> tuple[str, str]:
        """把邮箱头字段拆成显示名和地址。"""
        name, address = parseaddr(value)
        return self._decode_header_value(name), address

    @staticmethod
    def _format_date(value: str) -> str:
        """把邮件日期格式化为界面展示文本。"""
        if not value:
            return ''
        try:
            return parsedate_to_datetime(value).strftime('%Y-%m-%d %H:%M')
        except Exception:
            return value

    def _extract_bodies(self, message: Message) -> tuple[str, str]:
        """提取纯文本正文和 HTML 正文，并在必要时互相回填。"""
        # 同时保留纯文本和 HTML。
        # 列表预览继续用 body_text，详情区则可以优先显示 body_html。
        if message.is_multipart():
            plain_parts: list[str] = []
            html_parts: list[str] = []
            for part in message.walk():
                disposition = part.get_content_disposition()
                if disposition == 'attachment':
                    continue
                content_type = part.get_content_type()
                payload = self._decode_part(part)
                if not payload:
                    continue
                if content_type == 'text/plain':
                    plain_parts.append(payload)
                elif content_type == 'text/html':
                    html_parts.append(payload)

            body_text = '\n\n'.join(part.strip() for part in plain_parts if part.strip()).strip()
            body_html = '\n<hr>\n'.join(part.strip() for part in html_parts if part.strip()).strip()
            if not body_text and body_html:
                body_text = self._strip_html(body_html)
            if not body_html and body_text:
                body_html = self._plain_text_to_html(body_text)
            return body_text, body_html

        payload = self._decode_part(message).strip()
        if message.get_content_type() == 'text/html':
            return self._strip_html(payload), payload
        return payload, self._plain_text_to_html(payload) if payload else ''

    @staticmethod
    def _decode_part(part: Message) -> str:
        """按声明字符集解码单个 MIME part。"""
        payload = part.get_payload(decode=True)
        if payload is None:
            raw = part.get_payload()
            return raw if isinstance(raw, str) else ''
        charset = part.get_content_charset() or 'utf-8'
        try:
            return payload.decode(charset, errors='replace')
        except LookupError:
            return payload.decode('utf-8', errors='replace')

    @staticmethod
    def _strip_html(value: str) -> str:
        """把 HTML 正文粗略转换成纯文本。"""
        import re

        text = re.sub(r'<br\s*/?>', '\n', value, flags=re.IGNORECASE)
        text = re.sub(r'</p\s*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    @staticmethod
    def _plain_text_to_html(value: str) -> str:
        """把纯文本包装成可直接渲染的简单 HTML。"""
        if not value:
            return ''
        return '<div style="white-space: pre-wrap;">' + escape(value) + '</div>'
