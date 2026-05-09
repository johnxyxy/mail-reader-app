from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class MailListModel(QAbstractListModel):
    """把邮件字典列表暴露给 QML 使用。"""
    UidRole = Qt.UserRole + 1
    SubjectRole = Qt.UserRole + 2
    FromNameRole = Qt.UserRole + 3
    FromAddressRole = Qt.UserRole + 4
    ToAddressRole = Qt.UserRole + 5
    DateTextRole = Qt.UserRole + 6
    PreviewRole = Qt.UserRole + 7
    BodyTextRole = Qt.UserRole + 8
    BodyHtmlRole = Qt.UserRole + 9
    FolderRole = Qt.UserRole + 10
    IsReadRole = Qt.UserRole + 11

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
            self.UidRole: item.get('uid'),
            self.SubjectRole: item.get('subject'),
            self.FromNameRole: item.get('from_name'),
            self.FromAddressRole: item.get('from_address'),
            self.ToAddressRole: item.get('to_address'),
            self.DateTextRole: item.get('date_text'),
            self.PreviewRole: item.get('preview'),
            self.BodyTextRole: item.get('body_text'),
            self.BodyHtmlRole: item.get('body_html'),
            self.FolderRole: item.get('folder'),
            self.IsReadRole: item.get('is_read'),
            Qt.DisplayRole: item.get('subject'),
        }
        return role_map.get(role)

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.UidRole: b'uid',
            self.SubjectRole: b'subject',
            self.FromNameRole: b'fromName',
            self.FromAddressRole: b'fromAddress',
            self.ToAddressRole: b'toAddress',
            self.DateTextRole: b'dateText',
            self.PreviewRole: b'preview',
            self.BodyTextRole: b'bodyText',
            self.BodyHtmlRole: b'bodyHtml',
            self.FolderRole: b'folder',
            self.IsReadRole: b'isRead',
        }

    def set_items(self, items: list[dict[str, Any]]) -> None:
        """用新数据整体替换当前邮件列表内容。"""
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def get(self, index: int) -> dict[str, Any]:
        """按索引返回邮件字典，越界时返回空字典。"""
        if 0 <= index < len(self._items):
            return dict(self._items[index])
        return {}
