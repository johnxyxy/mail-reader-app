# 邮件读取器

一个基于 `Python + PySide6 + QML` 的桌面邮件读取工具，当前面向 Outlook / Hotmail 邮箱场景。

## 技术栈

- Python
- PySide6
- QML
- SQLite
- SQLAlchemy
- Requests

## 环境要求

- Python 3.10 或更高版本
- 可用的桌面图形环境
- 安装 `requirements.txt` 中的依赖

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动应用

```bash
python main.py
```

如果你使用 Conda，请先激活自己的环境，再执行上面的命令。

## 上传 GitHub 前的安全提醒

- `data/mail_accounts.db` 是本地运行数据，可能包含邮箱、密码、Client ID、Refresh Token 等敏感信息，已加入 `.gitignore`，不要提交到仓库。
- `.claude/`、`__pycache__/`、`.env*`、日志文件和本地数据库文件也应保持未提交状态。
- 如果误提交过数据库或 Token，请立即删除 Git 历史中的敏感文件，并到对应服务后台撤销/轮换凭据。


## 项目结构

```text
mail_reader_app/
├─ main.py
├─ requirements.txt
├─ data/
│  └─ mail_accounts.db   # 本地生成，不提交
├─ qml/
│  ├─ Main.qml
│  ├─ pages/
│  │  ├─ AccountPage.qml
│  │  ├─ MailPage.qml
│  │  └─ MailDetailPage.qml
│  ├─ components/
│  │  ├─ AccountCard.qml
│  │  └─ MailListItem.qml
│  └─ dialogs/
│     └─ AccountDialog.qml
└─ app/
   ├─ config.py
   ├─ controllers/
   │  ├─ app_controller.py
   │  ├─ account_model.py
   │  └─ mail_model.py
   ├─ services/
   │  ├─ account_service.py
   │  ├─ mail_service.py
   │  ├─ oauth_service.py
   │  ├─ imap_service.py
   │  └─ mail_parser.py
   ├─ storage/
   │  ├─ account_repository.py
   │  ├─ database.py
   │  └─ models.py
   └─ workers/
      └─ task_worker.py
```

## 分层说明

- `qml/`：界面与交互
- `app/controllers/`：QML 与 Python 业务层之间的桥接
- `app/services/`：账号、OAuth、IMAP、邮件解析等业务逻辑
- `app/storage/`：SQLite 与 SQLAlchemy 数据访问
- `app/workers/`：后台任务执行

## 依赖

项目当前运行依赖如下：

- `PySide6>=6.7`
- `SQLAlchemy>=2.0`
- `requests>=2.31`
