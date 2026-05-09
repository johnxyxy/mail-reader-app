from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class AccountListModel(QAbstractListModel):
    """把账号字典列表暴露给 QML 使用。"""
    IdRole = Qt.UserRole + 1
    EmailRole = Qt.UserRole + 2
    PasswordRole = Qt.UserRole + 3
    ClientIdRole = Qt.UserRole + 4
    RefreshTokenRole = Qt.UserRole + 5
    RemarkRole = Qt.UserRole + 6
    LastRefreshTimeRole = Qt.UserRole + 7
    LastErrorRole = Qt.UserRole + 8

    def __init__(self) -> None:
        super().__init__()
        self._items: list[dict[str, Any]] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None

        item = self._items[index.row()]
        role_map = {
            self.IdRole: item.get('id'),
            self.EmailRole: item.get('email'),
            self.PasswordRole: item.get('password'),
            self.ClientIdRole: item.get('client_id'),
            self.RefreshTokenRole: item.get('refresh_token'),
            self.RemarkRole: item.get('remark'),
            self.LastRefreshTimeRole: item.get('last_refresh_time'),
            self.LastErrorRole: item.get('last_error'),
            Qt.DisplayRole: item.get('email'),
        }
        return role_map.get(role)

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.IdRole: b'accountId',
            self.EmailRole: b'email',
            self.PasswordRole: b'password',
            self.ClientIdRole: b'clientId',
            self.RefreshTokenRole: b'refreshToken',
            self.RemarkRole: b'remark',
            self.LastRefreshTimeRole: b'lastRefreshTime',
            self.LastErrorRole: b'lastError',
        }

    def set_items(self, items: list[dict[str, Any]]) -> None:
        """用新数据整体替换当前模型内容。"""
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def get(self, index: int) -> dict[str, Any]:
        """按索引返回账号字典，越界时返回空字典。"""
        if 0 <= index < len(self._items):
            return dict(self._items[index])
        return {}

    def items(self) -> list[dict[str, Any]]:
        """返回当前所有账号项的浅拷贝列表。"""
        return [dict(item) for item in self._items]
