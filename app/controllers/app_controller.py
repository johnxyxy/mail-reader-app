from typing import Any

from PySide6.QtCore import Property, QObject, QThreadPool, QTimer, Signal, Slot

from app.controllers.account_model import AccountListModel
from app.controllers.mail_model import MailListModel
from app.services.account_service import AccountService
from app.services.mail_service import MailService
from app.storage.database import init_db
from app.workers.task_worker import TaskWorker


class AppController(QObject):
    """协调 QML、账号服务和邮件服务的应用控制器。"""

    accountModelChanged = Signal()
    mailModelChanged = Signal()
    selectedAccountIndexChanged = Signal()
    selectedAccountEmailChanged = Signal()
    selectedMailIndexChanged = Signal()
    selectedMailChanged = Signal()
    searchKeywordChanged = Signal()
    accountCountChanged = Signal()
    operationMessageChanged = Signal()
    loadingChanged = Signal()
    currentFolderChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        init_db()
        self._account_service = AccountService()
        self._mail_service = MailService()
        self._account_model = AccountListModel()
        self._mail_model = MailListModel()
        self._all_accounts: list[dict[str, Any]] = []
        self._search_keyword = ''
        # 列表里的高亮账号。它不等于“当前正在读取的邮箱”，因为账号卡片单击不应该触发读取。
        self._selected_account_index = -1
        # 当前真正打开的邮箱。只有双击账号后才会更新这两个字段。
        self._active_account_id: int | None = None
        self._active_account_email = ''
        self._selected_mail_index = -1
        self._operation_message = ''
        # loading 用计数维护。列表请求和详情请求可能同时进行，不能任意一个结束就关闭 loading。
        self._loading = False
        self._loading_count = 0
        self._current_folder = 'INBOX'
        # 记录当前邮件列表来自哪个账号/文件夹。读取失败时用它判断是否保留旧列表。
        self._loaded_account_id: int | None = None
        self._loaded_folder = 'INBOX'
        # 每类异步请求都有自己的序号。旧请求晚返回时，序号不匹配就丢弃结果。
        self._mail_list_request_id = 0
        self._mail_detail_request_id = 0
        self._mail_delete_request_id = 0
        self._token_request_id = 0
        # 邮件正文读取比列表慢。连续点击时只保留最后一次点击，避免同时打开多个 IMAP 详情连接。
        self._pending_mail_detail: tuple[int, int, dict[str, Any]] | None = None
        self._mail_detail_inflight = False
        self._mail_detail_inflight_request_id: int | None = None
        self._mail_detail_timer = QTimer(self)
        self._mail_detail_timer.setSingleShot(True)
        self._mail_detail_timer.setInterval(250)
        self._mail_detail_timer.timeout.connect(self._start_pending_mail_detail)
        self._thread_pool = QThreadPool(self)
        # Python 端必须持有 worker 引用，否则 QRunnable 信号可能在回调前被回收。
        self._active_workers: set[TaskWorker] = set()
        # 启动时只加载账号列表，不默认选中账号。
        self.refresh_accounts(select_first=False)

    @Property(QObject, notify=accountModelChanged)
    def accountModel(self) -> QObject:
        return self._account_model

    @Property(QObject, notify=mailModelChanged)
    def mailModel(self) -> QObject:
        return self._mail_model

    @Property(int, notify=selectedAccountIndexChanged)
    def selectedAccountIndex(self) -> int:
        return self._selected_account_index

    @Property(str, notify=selectedAccountEmailChanged)
    def selectedAccountEmail(self) -> str:
        return self._active_account_email

    @Property(int, notify=selectedMailIndexChanged)
    def selectedMailIndex(self) -> int:
        return self._selected_mail_index

    @Property(str, notify=searchKeywordChanged)
    def searchKeyword(self) -> str:
        return self._search_keyword

    @Property(int, notify=accountCountChanged)
    def accountCount(self) -> int:
        return len(self._all_accounts)

    @Property(str, notify=operationMessageChanged)
    def operationMessage(self) -> str:
        return self._operation_message

    @Property(bool, notify=loadingChanged)
    def loading(self) -> bool:
        return self._loading

    @Property(str, notify=currentFolderChanged)
    def currentFolder(self) -> str:
        return self._current_folder

    @Property('QVariantMap', notify=selectedMailChanged)
    def selectedMail(self) -> dict[str, Any]:
        """返回当前选中邮件的完整字典。"""
        return self._mail_model.get(self._selected_mail_index)

    @Slot()
    def refreshAccounts(self) -> None:
        """从数据库重新加载账号列表。"""
        self.refresh_accounts(select_first=False)

    @Slot()
    def clearOperationMessage(self) -> None:
        """清空界面上的操作提示文本。"""
        self._set_operation_message('')

    @Slot(str)
    def setSearchKeyword(self, keyword: str) -> None:
        """更新账号搜索关键字。"""
        self._search_keyword = keyword
        self.searchKeywordChanged.emit()

    @Slot()
    def showAllAccounts(self) -> None:
        """清空搜索条件并显示全部账号。"""
        self._search_keyword = ''
        self.searchKeywordChanged.emit()
        self._apply_account_filter(select_first=False)

    @Slot(str)
    def setCurrentFolder(self, folder: str) -> None:
        """切换当前文件夹，并在需要时重新加载邮件列表。"""
        normalized = folder if folder in ('INBOX', 'Junk') else 'INBOX'
        if self._current_folder == normalized:
            return

        self._current_folder = normalized
        self.currentFolderChanged.emit()

        # 没有双击打开过账号时，只切换按钮状态，不发网络请求。
        # 只有双击打开过邮箱后，切换文件夹才会重新读取邮件。
        if self._active_account_id is not None:
            self._clear_mail_selection(reset_loaded=True)
            self._load_messages_for_account(self._active_account_id)

    @Slot()
    def applyAccountSearch(self) -> None:
        """按当前关键字重新过滤账号列表。"""
        self._apply_account_filter(select_first=False)

    @Slot(int)
    def selectAccount(self, index: int) -> None:
        """保留给旧 QML 的兼容入口，当前不执行任何动作。"""
        # 保留这个 Slot 是为了兼容旧 QML；当前界面不再把单击绑定到任何动作。
        del index

    @Slot(int)
    def openAccountInbox(self, index: int) -> None:
        """把指定账号设为当前邮箱并加载其邮件列表。"""
        account = self._account_model.get(index)
        if not account:
            return

        # 双击才把账号设为“当前邮箱”。这样单击账号不会影响右侧邮件列表。
        self._selected_account_index = index
        self._active_account_id = int(account['id'])
        self._active_account_email = str(account.get('email', ''))
        self.selectedAccountIndexChanged.emit()
        self.selectedAccountEmailChanged.emit()
        self._clear_mail_selection(reset_loaded=True)
        # 双击账号才切换当前邮箱，并开始读取当前文件夹的邮件列表。
        self._log(f'account opened: index={index}, email={account.get("email", "")}, folder={self._current_folder}')
        self._load_messages_for_account(self._active_account_id)

    @Slot()
    def refreshCurrentMailbox(self) -> None:
        """重新加载当前激活邮箱的邮件列表。"""
        if self._active_account_id is None:
            self._set_operation_message('请先选择邮箱账号')
            return
        self._load_messages_for_account(self._active_account_id)

    @Slot(int)
    def selectMail(self, index: int) -> None:
        """更新选中邮件，并安排异步正文读取。"""
        mail_item = self._mail_model.get(index)
        if not mail_item:
            return

        # 先更新界面选中项，再异步读取正文。用户会马上看到选中状态，不必等网络返回。
        self._selected_mail_index = index
        self.selectedMailIndexChanged.emit()
        self.selectedMailChanged.emit()

        if self._active_account_id is None:
            return

        self._schedule_message_detail(self._active_account_id, index, mail_item)

    @Slot(int)
    def deleteMail(self, index: int) -> None:
        """删除当前列表中的目标邮件。"""
        if self._active_account_id is None:
            self._set_operation_message('请先打开一个邮箱后再删除邮件')
            return

        # 删除动作必须绑定发起时的账号和邮件 UID，避免用户中途切换邮箱后删错目标。
        account_id = self._active_account_id
        mail_item = self._mail_model.get(index)
        uid = str(mail_item.get('uid', ''))
        folder = str(mail_item.get('folder', self._current_folder))
        if not uid:
            self._set_operation_message('当前邮件缺少 UID，无法删除')
            return

        # 删除和加载详情一样走后台线程，避免 QML 主线程卡住。
        self._mail_delete_request_id += 1
        request_id = self._mail_delete_request_id
        self._begin_loading()
        self._log(f'mail delete started: account_id={account_id}, folder={folder}, uid={uid}, request_id={request_id}')

        worker = TaskWorker(lambda: self._mail_service.delete_message(account_id, uid, folder))
        worker.signals.succeeded.connect(
            lambda _payload, rid=request_id, deleted_index=index, deleted_uid=uid: self._handle_mail_deleted(
                rid,
                deleted_index,
                deleted_uid,
            )
        )
        worker.signals.failed.connect(
            lambda message, rid=request_id: self._handle_mail_delete_failed(rid, message)
        )
        self._start_worker(worker)

    @Slot('QVariantMap', result=bool)
    def saveAccount(self, payload: dict[str, Any]) -> bool:
        """保存账号，并在成功后刷新列表和高亮状态。"""
        try:
            saved = self._account_service.save_account(payload)
        except Exception as exc:
            self._set_operation_message(str(exc))
            return False

        self.refresh_accounts(select_first=False)
        self._selected_account_index = self._find_index_by_account_id(saved['id'])
        self.selectedAccountIndexChanged.emit()
        if self._active_account_id == int(saved['id']):
            self._active_account_email = str(saved.get('email', ''))
            self.selectedAccountEmailChanged.emit()
        self._set_operation_message('')
        return True

    @Slot(int)
    def refreshAccountToken(self, account_id: int) -> None:
        """后台刷新指定账号的 OAuth token。"""
        self._token_request_id += 1
        request_id = self._token_request_id
        self._begin_loading()
        self._log(f'token refresh started: account_id={account_id}, request_id={request_id}')

        worker = TaskWorker(lambda: self._mail_service.refresh_account_token(account_id))
        worker.signals.succeeded.connect(
            lambda payload, rid=request_id, aid=account_id: self._handle_token_refreshed(rid, aid, payload)
        )
        worker.signals.failed.connect(
            lambda message, rid=request_id: self._handle_token_refresh_failed(rid, message)
        )
        self._start_worker(worker)

    @Slot(int)
    def deleteAccount(self, account_id: int) -> None:
        """删除账号，并在必要时清空当前激活邮箱状态。"""
        self._account_service.delete_account(account_id)
        if self._active_account_id == account_id:
            self._active_account_id = None
            self._active_account_email = ''
            self._clear_mail_selection(reset_loaded=True)
            self.selectedAccountEmailChanged.emit()
        self._selected_account_index = -1
        self.refresh_accounts(select_first=False)
        self._log(f'account deleted: account_id={account_id}')

    @Slot(result='QVariantMap')
    def getSelectedAccount(self) -> dict[str, Any]:
        """返回当前高亮账号的数据。"""
        return self._account_model.get(self._selected_account_index)

    @Slot(int, result='QVariantMap')
    def getAccount(self, index: int) -> dict[str, Any]:
        """按索引返回账号数据。"""
        return self._account_model.get(index)

    def refresh_accounts(self, select_first: bool) -> None:
        """从服务层加载账号，并同步账号总数。"""
        self._all_accounts = self._account_service.list_accounts()
        self._apply_account_filter(select_first=select_first)
        self.accountCountChanged.emit()

    def _apply_account_filter(self, select_first: bool) -> None:
        """按关键字过滤账号，并尽量保持原有高亮项。"""
        keyword = self._search_keyword.strip().lower()
        # 搜索会重建列表，旧 index 可能指向别的账号，所以先保存账号 id 再恢复高亮。
        highlighted_account_id = self._selected_account_id()
        if keyword:
            filtered = [
                dict(item)
                for item in self._all_accounts
                if keyword in item.get('email', '').lower()
                or keyword in item.get('remark', '').lower()
            ]
        else:
            filtered = [dict(item) for item in self._all_accounts]

        self._account_model.set_items(filtered)
        if not filtered:
            self._selected_account_index = -1
            self.selectedAccountIndexChanged.emit()
            return

        if select_first:
            self.selectAccount(0)
        elif highlighted_account_id is not None:
            self._selected_account_index = self._find_index_by_account_id(highlighted_account_id)
            self.selectedAccountIndexChanged.emit()
        else:
            self._selected_account_index = -1
            self.selectedAccountIndexChanged.emit()

    def _set_operation_message(self, message: str) -> None:
        """更新界面提示消息，并在有内容时写日志。"""
        self._operation_message = message
        self.operationMessageChanged.emit()
        if message:
            self._log(f'operation message: {message}')

    @staticmethod
    def _log(message: str) -> None:
        print(f'[MailReader] {message}', flush=True)

    def _begin_loading(self) -> None:
        """进入一个新的加载阶段，并维护 loading 计数。"""
        # 可能同时存在“列表请求”和“详情请求”，用计数避免提前关闭 loading。
        self._loading_count += 1
        self._log(f'loading begin: count={self._loading_count}')
        if not self._loading:
            self._loading = True
            self.loadingChanged.emit()

    def _end_loading(self) -> None:
        """结束一个加载阶段，并在计数归零时关闭 loading。"""
        if self._loading_count > 0:
            self._loading_count -= 1
        self._log(f'loading end: count={self._loading_count}')
        if self._loading_count == 0 and self._loading:
            self._loading = False
            self.loadingChanged.emit()

    def _start_worker(self, worker: TaskWorker) -> None:
        """启动后台 worker，并持有其 Python 引用直到回调结束。"""
        # QThreadPool 只负责运行 QRunnable；这里保留 Python worker，避免 signals 被提前回收。
        self._active_workers.add(worker)
        worker.signals.succeeded.connect(lambda _payload, w=worker: self._release_worker(w))
        worker.signals.failed.connect(lambda _message, w=worker: self._release_worker(w))
        self._thread_pool.start(worker)

    def _release_worker(self, worker: TaskWorker) -> None:
        """释放已完成 worker 的引用。"""
        self._active_workers.discard(worker)
        self._log(f'worker released: active={len(self._active_workers)}')

    def _clear_mail_selection(self, reset_loaded: bool = False) -> None:
        """清空邮件列表选中状态，并废弃挂起的详情请求。"""
        self._mail_model.set_items([])
        self._selected_mail_index = -1
        # 清空列表时顺手废掉未完成的详情请求，避免旧正文写进新列表。
        self._mail_detail_request_id += 1
        self._pending_mail_detail = None
        self._mail_detail_timer.stop()
        self._mail_detail_inflight = False
        self._mail_detail_inflight_request_id = None
        if reset_loaded:
            self._loaded_account_id = None
        self._loaded_folder = self._current_folder
        self.selectedMailIndexChanged.emit()
        self.selectedMailChanged.emit()

    def _load_messages_for_account(self, account_id: int) -> None:
        """为指定账号启动一次新的邮件列表异步读取。"""
        self._mail_list_request_id += 1
        request_id = self._mail_list_request_id
        request_folder = self._current_folder
        self._begin_loading()
        self._log(f'mail list load started: account_id={account_id}, folder={request_folder}, request_id={request_id}')

        # 邮件列表读取放在线程池里，避免 IMAP 网络等待卡住 QML 界面。
        # 每次读取列表都生成 request_id。旧请求晚回来时会被忽略，避免覆盖新列表。
        worker = TaskWorker(lambda: self._mail_service.list_messages(account_id, request_folder))
        worker.signals.succeeded.connect(
            lambda payload, rid=request_id, aid=account_id, folder=request_folder: self._handle_messages_loaded(
                rid,
                aid,
                folder,
                payload,
            )
        )
        worker.signals.failed.connect(
            lambda message, rid=request_id, aid=account_id, folder=request_folder: self._handle_messages_failed(
                rid,
                aid,
                folder,
                message,
            )
        )
        self._start_worker(worker)

    def _schedule_message_detail(self, account_id: int, index: int, mail_item: dict[str, Any]) -> None:
        """记录最后一次点击的邮件，并按条件启动详情读取。"""
        self._pending_mail_detail = (account_id, index, dict(mail_item))
        if self._mail_detail_inflight:
            self._log(f'mail detail queued: index={index}, uid={mail_item.get("uid", "")}')
            return
        self._mail_detail_timer.start()

    def _start_pending_mail_detail(self) -> None:
        """在没有进行中请求时启动挂起的邮件详情读取。"""
        if self._mail_detail_inflight or self._pending_mail_detail is None:
            return

        account_id, index, mail_item = self._pending_mail_detail
        self._pending_mail_detail = None
        self._load_message_detail_now(account_id, index, mail_item)

    def _load_message_detail_now(self, account_id: int, index: int, mail_item: dict[str, Any]) -> None:
        """立即为指定邮件发起一次正文异步读取。"""
        uid = str(mail_item.get('uid', ''))
        folder = str(mail_item.get('folder', self._current_folder))
        if not uid:
            return

        self._mail_detail_request_id += 1
        request_id = self._mail_detail_request_id
        self._mail_detail_inflight = True
        self._mail_detail_inflight_request_id = request_id
        self._begin_loading()
        self._log(f'mail detail load started: account_id={account_id}, uid={uid}, folder={folder}, request_id={request_id}')

        # 详情单独异步读取；快速点击不同邮件时，只接受最后一次请求的结果。
        worker = TaskWorker(lambda: self._mail_service.fetch_message_detail(account_id, uid, folder))
        worker.signals.succeeded.connect(
            lambda payload, rid=request_id, idx=index, mail_uid=uid: self._handle_message_detail_loaded(
                rid,
                idx,
                mail_uid,
                payload,
            )
        )
        worker.signals.failed.connect(
            lambda message, rid=request_id: self._handle_message_detail_failed(rid, message)
        )
        self._start_worker(worker)

    def _handle_messages_loaded(
        self,
        request_id: int,
        account_id: int,
        folder: str,
        items: object,
    ) -> None:
        """接收最新有效的邮件列表结果并写回模型。"""
        self._end_loading()
        if request_id != self._mail_list_request_id:
            self._log(f'ignore stale mail list result: request_id={request_id}')
            return

        mails = list(items) if isinstance(items, list) else []
        self._mail_model.set_items(mails)
        self._loaded_account_id = account_id
        self._loaded_folder = folder
        # 列表加载完成后不自动打开第一封邮件。正文只在用户点击邮件时读取，首屏会快很多。
        self._selected_mail_index = -1
        self.selectedMailIndexChanged.emit()
        self.selectedMailChanged.emit()
        self._set_operation_message('')
        self._log(f'mail list loaded: account_id={account_id}, folder={folder}, count={len(mails)}')

    def _handle_messages_failed(
        self,
        request_id: int,
        account_id: int,
        folder: str,
        message: str,
    ) -> None:
        """处理邮件列表读取失败，并按条件保留旧列表。"""
        self._end_loading()
        if request_id != self._mail_list_request_id:
            self._log(f'ignore stale mail list error: request_id={request_id}')
            return

        preserve_existing = (
            self._loaded_account_id == account_id
            and self._loaded_folder == folder
            and self._mail_model.rowCount() > 0
        )
        # 刷新失败但旧列表仍属于同一个账号/文件夹时，保留旧列表，避免界面突然空掉。
        if not preserve_existing:
            self._clear_mail_selection()

        self._set_operation_message(message)
        self._log(f'mail list failed: account_id={account_id}, folder={folder}, preserve_existing={preserve_existing}, message={message}')

    def _handle_message_detail_loaded(
        self,
        request_id: int,
        index: int,
        uid: str,
        payload: object,
    ) -> None:
        """把最新有效的邮件详情合并回当前列表。"""
        self._end_loading()
        if request_id != self._mail_detail_request_id:
            self._finish_mail_detail_request(request_id)
            self._log(f'ignore stale mail detail result: request_id={request_id}, uid={uid}')
            return

        detail = dict(payload) if isinstance(payload, dict) else {}
        items = [self._mail_model.get(i) for i in range(self._mail_model.rowCount())]
        target_index = -1
        # 不能只按 index 更新详情，因为请求期间列表可能刷新；必须同时校验 UID。
        if 0 <= index < len(items) and str(items[index].get('uid', '')) == uid:
            target_index = index
        else:
            for current_index, item in enumerate(items):
                if str(item.get('uid', '')) == uid:
                    target_index = current_index
                    break

        if target_index < 0:
            self._finish_mail_detail_request(request_id)
            self._log(f'mail detail ignored because uid is no longer visible: uid={uid}')
            return

        items[target_index].update(detail)
        self._mail_model.set_items(items)
        if target_index == self._selected_mail_index:
            self.selectedMailChanged.emit()
        self._set_operation_message('')
        self._log(f'mail detail loaded: uid={uid}, index={target_index}')
        self._finish_mail_detail_request(request_id)

    def _handle_message_detail_failed(self, request_id: int, message: str) -> None:
        """处理邮件详情读取失败。"""
        self._end_loading()
        if request_id != self._mail_detail_request_id:
            self._finish_mail_detail_request(request_id)
            self._log(f'ignore stale mail detail error: request_id={request_id}')
            return
        self._set_operation_message(message)
        self._log(f'mail detail failed: request_id={request_id}, message={message}')
        self._finish_mail_detail_request(request_id)

    def _handle_mail_deleted(self, request_id: int, deleted_index: int, deleted_uid: str) -> None:
        """处理邮件删除成功后的列表和选中状态同步。"""
        self._end_loading()
        if request_id != self._mail_delete_request_id:
            self._log(f'ignore stale mail delete result: request_id={request_id}, uid={deleted_uid}')
            return

        items = [self._mail_model.get(i) for i in range(self._mail_model.rowCount())]
        target_index = -1
        # 优先用原始 index 命中；如果列表在等待期间发生过变化，再回退到 UID 精确定位。
        if 0 <= deleted_index < len(items) and str(items[deleted_index].get('uid', '')) == deleted_uid:
            target_index = deleted_index
        else:
            for current_index, item in enumerate(items):
                if str(item.get('uid', '')) == deleted_uid:
                    target_index = current_index
                    break

        if target_index < 0:
            self._set_operation_message('')
            self._log(f'mail delete ignored because uid is no longer visible: uid={deleted_uid}')
            return

        was_selected = target_index == self._selected_mail_index
        items.pop(target_index)
        self._mail_model.set_items(items)

        if was_selected:
            # 如果删掉的是当前右侧正在显示详情的邮件，必须把详情状态一起清空。
            self._selected_mail_index = -1
            self._mail_detail_request_id += 1
            self._pending_mail_detail = None
            self._mail_detail_timer.stop()
            self._mail_detail_inflight = False
            self._mail_detail_inflight_request_id = None
            self.selectedMailIndexChanged.emit()
            self.selectedMailChanged.emit()
        elif 0 <= self._selected_mail_index and target_index < self._selected_mail_index:
            # 删除的是当前选中项之前的邮件，选中索引要向前挪一位。
            self._selected_mail_index -= 1
            self.selectedMailIndexChanged.emit()
            self.selectedMailChanged.emit()

        self._set_operation_message('邮件已删除')
        self._log(f'mail deleted: uid={deleted_uid}, index={target_index}, remaining={len(items)}')

    def _handle_mail_delete_failed(self, request_id: int, message: str) -> None:
        """处理邮件删除失败。"""
        self._end_loading()
        if request_id != self._mail_delete_request_id:
            self._log(f'ignore stale mail delete error: request_id={request_id}')
            return
        self._set_operation_message(message)
        self._log(f'mail delete failed: request_id={request_id}, message={message}')

    def _finish_mail_detail_request(self, request_id: int) -> None:
        """结束当前详情请求，并在有排队项时继续下一次读取。"""
        if self._mail_detail_inflight_request_id not in (None, request_id):
            return
        self._mail_detail_inflight = False
        self._mail_detail_inflight_request_id = None
        if self._pending_mail_detail is not None:
            self._start_pending_mail_detail()

    def _handle_token_refresh_failed(self, request_id: int, message: str) -> None:
        """处理 token 刷新失败，并刷新账号列表中的错误状态。"""
        self._end_loading()
        if request_id != self._token_request_id:
            return
        self.refresh_accounts(select_first=False)
        self._set_operation_message(message)

    def _handle_token_refreshed(self, request_id: int, account_id: int, payload: object) -> None:
        """处理 token 刷新成功后的账号列表和提示更新。"""
        del payload
        self._end_loading()
        if request_id != self._token_request_id:
            return

        self.refresh_accounts(select_first=False)
        self._selected_account_index = self._find_index_by_account_id(account_id)
        self.selectedAccountIndexChanged.emit()
        self._set_operation_message('Token 刷新成功')

    def _selected_account_id(self) -> int | None:
        """返回当前高亮账号的 id，不存在时返回 None。"""
        account = self._account_model.get(self._selected_account_index)
        if not account:
            return None
        return int(account.get('id', 0))

    def _find_index_by_account_id(self, account_id: int) -> int:
        """按账号 id 在当前模型中查找索引。"""
        for index, account in enumerate(self._account_model.items()):
            if int(account.get('id', 0)) == account_id:
                return index
        return -1
