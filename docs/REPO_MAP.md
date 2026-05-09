# 项目总地图

## 项目定位

- 项目名：`mail_reader_app`
- 技术栈：`Python + PySide6 + QML + SQLite + SQLAlchemy`
- 核心目标：
  - 管理 Outlook 邮箱账号
  - 刷新 OAuth Token
  - 读取 `INBOX` 和 `Junk`
  - 展示邮件列表与邮件正文
  - 支持在列表中删除邮件

## 顶层目录

```text
mail_reader_app/
  main.py
  run_app.bat
  qtquickcontrols2.conf
  requirements.txt
  app/
    config.py
    controllers/
      app_controller.py
      account_model.py
      mail_model.py
    services/
      account_service.py
      mail_service.py
      oauth_service.py
      imap_service.py
      mail_parser.py
    storage/
      database.py
      models.py
      account_repository.py
    workers/
      task_worker.py
  qml/
    Main.qml
    pages/
      AccountPage.qml
      MailPage.qml
      MailDetailPage.qml
    components/
      AccountCard.qml
      MailListItem.qml
    dialogs/
      AccountDialog.qml
  data/
    mail_accounts.db
  docs/
    REPO_MAP.md
    DECISIONS.md
    modules/
```

## 入口文件

### `main.py`

作用：

- 创建 `QGuiApplication`
- 在导入 PySide6 前强制设置 `QT_QUICK_CONTROLS_STYLE=Basic`
- 创建 `AppController`
- 把 `appController` 注入到 QML 上下文
- 加载 `qml/Main.qml`

### `run_app.bat`

作用：

- 作为推荐启动脚本
- 统一设置运行环境，避免每次手动敲命令

会设置：

- `QT_QUICK_CONTROLS_STYLE=Basic`
- `PYTHONUTF8=1`
- `PYTHONIOENCODING=utf-8`
- `PYTHONPYCACHEPREFIX=.cache\pycache`

## 分层结构

### UI 层

- 路径：`qml/**`
- 职责：
  - 画界面
  - 接收用户操作
  - 把信号发给控制器
  - 绑定控制器暴露出来的属性

### 控制器层

- 路径：`app/controllers/**`
- 职责：
  - 连接 QML 和 Python 业务逻辑
  - 保存当前界面状态
  - 启动后台异步任务
  - 处理旧请求覆盖新状态的问题
  - 协调邮件详情读取与删除等用户动作

### 服务层

- 路径：`app/services/**`
- 职责：
  - 账号校验
  - OAuth 刷新
  - IMAP 登录与读取
  - 邮件删除
  - 邮件原文解析

### 存储层

- 路径：`app/storage/**`
- 职责：
  - 数据库连接
  - 表模型定义
  - 账号数据读写
  - Token/错误信息持久化

## 关键文件与问题定位

### 应用启动失败

优先看：

- `main.py`
- `run_app.bat`
- `qtquickcontrols2.conf`

### 账号列表异常

优先看：

- `qml/pages/AccountPage.qml`
- `qml/components/AccountCard.qml`
- `app/controllers/app_controller.py`
- `app/services/account_service.py`
- `app/storage/account_repository.py`

### 邮件列表为空或很慢

优先看：

- `app/controllers/app_controller.py`
- `app/services/mail_service.py`
- `app/services/imap_service.py`
- `app/services/oauth_service.py`
- `qml/pages/MailPage.qml`

### 邮件详情错误、串号、延迟

优先看：

- `app/controllers/app_controller.py`
- `app/services/mail_service.py`
- `app/services/imap_service.py`
- `app/services/mail_parser.py`
- `qml/pages/MailDetailPage.qml`

### 邮件删除异常

优先看：

- `qml/components/MailListItem.qml`
- `qml/pages/MailPage.qml`
- `app/controllers/app_controller.py`
- `app/services/mail_service.py`
- `app/services/imap_service.py`

### Token 刷新失败

优先看：

- `app/services/oauth_service.py`
- `app/services/mail_service.py`
- `app/storage/account_repository.py`

### 数据库问题

优先看：

- `app/storage/database.py`
- `app/storage/models.py`
- `app/storage/account_repository.py`
- `data/mail_accounts.db`

## 整体运行逻辑

1. `main.py` 启动应用并加载 QML。
2. `AppController.__init__()` 初始化数据库、模型和服务，然后加载账号列表。
3. 用户在左侧双击账号卡片。
4. `AppController.openAccountInbox()` 设置当前激活邮箱，并启动异步邮件列表读取。
5. `MailService.list_messages()` 先准备可用的 access token。
6. `IMAPService.list_messages()` 登录 Outlook IMAP 并读取最近邮件头。
7. 控制器把结果写入 `MailListModel`，中间列表显示出来。
8. 用户点击某封邮件。
9. `AppController.selectMail()` 立即更新选中状态，再安排正文异步读取。
10. `MailService.fetch_message_detail()` 按 UID 读取该邮件完整原文。
11. `MailParser.parse_message_bytes()` 提取正文、预览和头信息。
12. 控制器把详情合并回 `MailListModel`，右侧详情区显示正文。
13. 用户左滑某封邮件并确认删除。
14. `AppController.deleteMail()` 在后台调用 `MailService.delete_message()`。
15. `IMAPService.delete_message()` 对目标邮件执行 IMAP 删除并清理。
16. 控制器刷新/修正当前列表与选中状态。

## 关键状态词汇

- `selectedAccountIndex`
  - 左侧账号列表里当前高亮的账号索引
- `active_account_id`
  - 当前真正打开的邮箱账号 id
- `active_account_email`
  - 当前真正打开的邮箱地址
- `selectedMailIndex`
  - 当前选中的邮件索引
- `currentFolder`
  - 当前文件夹，只有 `INBOX` 或 `Junk`
- `loading`
  - 界面 loading 状态，由计数器控制

## 异步安全机制

- `TaskWorker`
  - 把阻塞任务放进线程池
- `_mail_list_request_id`
  - 防止旧邮件列表结果覆盖新列表
- `_mail_detail_request_id`
  - 防止旧邮件详情结果覆盖新详情
- `_mail_delete_request_id`
  - 防止旧删除回调覆盖新状态
- `_token_request_id`
  - 防止旧 token 刷新结果覆盖新状态
- `_pending_mail_detail`
  - 用户快速点击多封邮件时，只保留最后一次待读取邮件
- `_mail_detail_timer`
  - 邮件详情读取前的 250ms 防抖

## 当前一些不直观但重要的行为

- 账号单击不做任何事
- 账号双击才切换邮箱并读取邮件
- 邮件列表加载完成后不会自动打开第一封邮件
- 邮件列表优先只读取邮件头，不直接读取正文
- 批量取头失败时，会降级到逐封取头，再降级到整封读取
- 邮件删除采用左滑后确认的两段式交互，避免误触

## 可以忽略的目录

- `.cache/`
- `__pycache__/`

这些都是运行或编译生成内容，不是源码逻辑主体。
