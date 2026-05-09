from collections.abc import Mapping
from typing import Any

from app.storage.account_repository import AccountRepository


class AccountService:
    """处理账号表单校验、错误翻译和数据转换。"""

    def __init__(self, repository: AccountRepository | None = None) -> None:
        self._repository = repository or AccountRepository()

    def list_accounts(self, search: str = '') -> list[dict[str, Any]]:
        """返回适合控制器和 QML 使用的账号字典列表。"""
        return [self._to_dict(account) for account in self._repository.list_accounts(search)]

    def save_account(self, data: Mapping[str, Any]) -> dict[str, Any]:
        """按是否带 id 决定新增账号还是更新账号。"""
        normalized = self._normalize(data)
        account_id = int(data.get('id', 0) or 0)
        try:
            if account_id > 0:
                return self._to_dict(self._repository.update_account(account_id, normalized))
            return self._to_dict(self._repository.create_account(normalized))
        except ValueError as exc:
            raise ValueError(self._translate_error(str(exc))) from exc

    def delete_account(self, account_id: int) -> bool:
        """删除指定账号，并把底层错误翻译成界面可读消息。"""
        try:
            return self._repository.delete_account(account_id)
        except ValueError as exc:
            raise ValueError(self._translate_error(str(exc))) from exc

    def update_refresh_token(self, account_id: int, refresh_token: str, last_refresh_time: str) -> dict[str, Any]:
        """更新账号的 refresh token 和最近刷新时间。"""
        try:
            account = self._repository.update_refresh_token(account_id, refresh_token, last_refresh_time)
        except ValueError as exc:
            raise ValueError(self._translate_error(str(exc))) from exc
        return self._to_dict(account)

    @staticmethod
    def _normalize(data: Mapping[str, Any]) -> dict[str, Any]:
        """清洗并校验账号表单输入。"""
        email = str(data.get('email', '')).strip()
        client_id = str(data.get('client_id', '')).strip()
        refresh_token = str(data.get('refresh_token', '')).strip()
        if not email:
            raise ValueError('请输入邮箱地址')
        if not client_id:
            raise ValueError('请输入 Client ID')
        if not refresh_token:
            raise ValueError('请输入 Refresh Token')

        return {
            'email': email,
            'password': str(data.get('password', '')).strip(),
            'client_id': client_id,
            'refresh_token': refresh_token,
            'remark': str(data.get('remark', '')).strip(),
        }

    @staticmethod
    def _translate_error(message: str) -> str:
        """把 repository 层的英文错误转换成中文提示。"""
        translations = {
            'email already exists': '该邮箱已存在',
            'account not found': '未找到该邮箱账号',
        }
        return translations.get(message, message)

    @staticmethod
    def _to_dict(account: Any) -> dict[str, Any]:
        """把 SQLAlchemy 账号对象转换成普通字典。"""
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
