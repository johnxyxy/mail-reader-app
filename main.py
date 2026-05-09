import os
import sys
from pathlib import Path

# 必须在导入 PySide6 之前指定样式。
# Windows 原生样式不允许自定义 TextField、ScrollBar 等控件的 background/contentItem。
# 项目里有大量自绘控件，所以统一使用 Basic 这种非原生样式，避免运行时警告。
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from app.controllers.app_controller import AppController


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName('邮件读取器')
    app.setOrganizationName('STMP')

    controller = AppController()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('appController', controller)

    qml_file = Path(__file__).resolve().parent / 'qml' / 'Main.qml'
    engine.load(str(qml_file))

    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
