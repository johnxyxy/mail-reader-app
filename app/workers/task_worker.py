from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal


class TaskWorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(str)


class TaskWorker(QRunnable):
    """在线程池里运行阻塞任务，并把结果通过 Qt Signal 发回主线程。"""

    def __init__(self, task: Callable[[], Any]) -> None:
        super().__init__()
        # PySide 的 QRunnable 默认会自动删除。这里关闭自动删除，由 AppController 持有并释放引用。
        self.setAutoDelete(False)
        self._task = task
        self.signals = TaskWorkerSignals()

    def run(self) -> None:
        # 任务在线程池中执行，不能直接更新 QML；只通过 Signal 把结果交回主线程。
        try:
            result = self._task()
        except Exception as exc:
            self.signals.failed.emit(str(exc))
            return

        self.signals.succeeded.emit(result)
