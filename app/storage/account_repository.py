from collections.abc import Mapping
from typing import Any

from sqlalchemy import select

from app.storage.database import session_scope
from app.storage.models import Account


class AccountRepository:
    """封装账号表的数据库读写操作。"""

    def email_exists(self, email: str, exclude_account_id: int | None = None) -> bool:
        """检查邮箱是否已存在，可排除当前正在编辑的账号。"""
        normalized = email.strip().lower()
        with session_scope() as session:
            stmt = select(Account).where(Account.email == normalized)
            account = session.scalar(stmt)

        if account is None:
            return False
        if exclude_account_id is not None and int(account.id) == exclude_account_id:
            return False
        return True

    def list_accounts(self, search: str = '') -> list[Account]:
        """按创建顺序倒序返回账号，并按关键字过滤邮箱或备注。"""
        with session_scope() as session:
            stmt = select(Account).order_by(Account.id.desc())
            accounts = list(session.scalars(stmt).all())

        keyword = search.strip().lower()
        if not keyword:
            return accounts

        return [
            account
            for account in accounts
            if keyword in account.email.lower() or keyword in (account.remark or '').lower()
        ]

    def get_account(self, account_id: int) -> Account | None:
        """按主键返回单个账号，不存在时返回 None。"""
        with session_scope() as session:
            return session.get(Account, account_id)

    def create_account(self, data: Mapping[str, Any]) -> Account:
        """创建新账号，并在写入前保证邮箱唯一。"""
        email = str(data.get('email', '')).strip().lower()
        if self.email_exists(email):
            raise ValueError('email already exists')

        with session_scope() as session:
            account = Account(
                email=email,
                password=self._clean_optional(data.get('password')),
                client_id=str(data.get('client_id', '')).strip(),
                refresh_token=str(data.get('refresh_token', '')).strip(),
                remark=self._clean_optional(data.get('remark')),
                last_refresh_time=self._clean_optional(data.get('last_refresh_time')),
                last_error=self._clean_optional(data.get('last_error')),
            )
            session.add(account)
            session.flush()
            session.refresh(account)
            return account

    def update_account(self, account_id: int, data: Mapping[str, Any]) -> Account:
        """更新已有账号的可编辑字段。"""
        email = str(data.get('email', '')).strip().lower()
        if self.email_exists(email, exclude_account_id=account_id):
            raise ValueError('email already exists')

        with session_scope() as session:
            account = session.get(Account, account_id)
            if account is None:
                raise ValueError('account not found')

            account.email = email or account.email
            account.password = self._clean_optional(data.get('password', account.password))
            account.client_id = str(data.get('client_id', account.client_id)).strip()
            account.refresh_token = str(data.get('refresh_token', account.refresh_token)).strip()
            account.remark = self._clean_optional(data.get('remark', account.remark))
            session.add(account)
            session.flush()
            session.refresh(account)
            return account

    def delete_account(self, account_id: int) -> bool:
        """删除指定账号，不存在时返回 False。"""
        with session_scope() as session:
            account = session.get(Account, account_id)
            if account is None:
                return False
            session.delete(account)
            return True

    def update_refresh_token(self, account_id: int, refresh_token: str, last_refresh_time: str) -> Account:
        """写回新的 refresh token，并清除上次错误。"""
        with session_scope() as session:
            account = session.get(Account, account_id)
            if account is None:
                raise ValueError('account not found')
            account.refresh_token = refresh_token
            account.last_refresh_time = last_refresh_time
            account.last_error = None
            session.add(account)
            session.flush()
            session.refresh(account)
            return account

    def mark_error(self, account_id: int, message: str) -> Account:
        """记录账号最近一次操作失败的错误信息。"""
        with session_scope() as session:
            account = session.get(Account, account_id)
            if account is None:
                raise ValueError('account not found')
            account.last_error = message
            session.add(account)
            session.flush()
            session.refresh(account)
            return account

    @staticmethod
    def _clean_optional(value: Any) -> str | None:
        """把空白可选字段归一化为 None。"""
        if value is None:
            return None
        text = str(value).strip()
        return text or None
