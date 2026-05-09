# 完整运行逻辑

## 应用启动链路

1. `run_app.bat` 设置运行环境。
2. `main.py` 在导入 PySide6 前强制 `Basic` 样式。
3. 创建 `QGuiApplication`。
4. 创建 `AppController`。
5. `AppController` 初始化数据库、模型、服务。
6. `AppController` 立即读取账号列表。
7. QML 引擎加载 `qml/Main.qml`。

## 账号列表链路

1. 左侧 QML 绑定 `appController.accountModel`。
2. `refresh_accounts()` 调 `AccountService.list_accounts()`。
3. `AccountService` 调 `AccountRepository.list_accounts()`。
4. repository 从 SQLite 读取 `accounts` 表。
5. 控制器把结果写入 `AccountListModel`。

## 打开邮箱链路

1. 用户双击左侧账号卡片。
2. `AccountPage.qml` 发出 `accountOpened(index)`。
3. `Main.qml` 调用 `appController.openAccountInbox(index)`。
4. 控制器设置：
   - `selectedAccountIndex`
   - `active_account_id`
   - `active_account_email`
5. 控制器清空当前邮件选中状态。
6. 控制器启动异步邮件列表读取。

## 邮件列表读取链路

1. `AppController._load_messages_for_account(account_id)`
2. 生成新的 `_mail_list_request_id`
3. 启动 `TaskWorker`
4. `MailService.list_messages()`：
   - 从 repository 拿账号信息
   - 获取可用 access token
   - 调 `IMAPService.list_messages()`
5. `IMAPService.list_messages()`：
   - 连接 Outlook IMAP
   - XOAUTH2 认证
   - 打开文件夹
   - 搜索最近邮件 UID
   - 读取邮件头
   - 必要时走 fallback
6. `MailParser.parse_header_bytes()` 把头信息转成列表项 dict
7. 控制器收到结果后写入 `MailListModel`

## 邮件详情读取链路

1. 用户点击中间某封邮件。
2. `AppController.selectMail(index)` 先立即更新选中态。
3. 控制器把这次点击写入 `_pending_mail_detail`。
4. 防抖计时器等待 250ms。
5. 如果当前没有详情请求在跑，就启动这次详情读取。
6. 如果已经有详情请求在跑，就不并发再开新请求，只保留最后一次点击。
7. 当前请求结束后，控制器只会读取最后一封待处理邮件。
8. `MailService.fetch_message_detail()` 调 `IMAPService.fetch_message_detail()`。
9. `IMAPService.fetch_message_detail()` 读取该 UID 的整封 RFC822。
10. `MailParser.parse_message_bytes()` 提取正文和预览。
11. 控制器把详情合并回 `MailListModel`。

## 邮件删除链路

1. 用户在 `MailListItem.qml` 左滑某封邮件。
2. 第一步露出“删除”按钮，但不立刻执行删除。
3. 用户点击“删除”后进入“确定 / 取消”确认态。
4. 用户点击“确定”后，`MailPage.qml` 发出 `mailDeleteRequested(index)`。
5. `Main.qml` 调用 `appController.deleteMail(index)`。
6. 控制器读取当前列表项的 UID 和 folder，并生成 `_mail_delete_request_id`。
7. `MailService.delete_message()` 获取 access token 并调用 `IMAPService.delete_message()`。
8. IMAP 层先标记 `\\Deleted`，再执行 `expunge()` 真正清理。
9. 控制器收到成功结果后更新列表、选中项和提示状态。

## 文件夹切换链路

1. 用户点击 `INBOX` 或 `Junk`。
2. 控制器更新 `currentFolder`。
3. 如果还没有激活邮箱，流程结束。
4. 如果已有激活邮箱：
   - 清空当前邮件选择状态
   - 重新读取当前文件夹邮件列表

## 异步安全规则

- 每类请求都有独立 request id
- 旧请求返回时，如果 id 不匹配，结果直接丢弃
- 邮件详情按 UID 校验，避免列表刷新后 index 串号
- 邮件删除按 request id、UID 和当前列表状态共同约束
- `loading` 用计数器，不是简单布尔值

## 出错处理逻辑

- OAuth / 网络 / IMAP 失败都会转换为可读错误信息
- `MailService` 会把错误写回账号的 `last_error`
- 如果刷新失败，但当前列表仍属于同一个账号和同一个文件夹，旧列表会保留

## 快速排查问题时该怎么想

### 现象：账号双击后没出邮件列表

检查链路：

- `openAccountInbox()`
- `_load_messages_for_account()`
- `MailService.list_messages()`
- `IMAPService.list_messages()`

### 现象：邮件列表有，但点邮件正文很慢

检查链路：

- `selectMail()`
- `_schedule_message_detail()`
- `MailService.fetch_message_detail()`
- `IMAPService.fetch_message_detail()`

### 现象：用户快速乱点时正文串了

检查状态：

- `_pending_mail_detail`
- `_mail_detail_inflight`
- `_mail_detail_inflight_request_id`
- `_mail_detail_timer`
- `_mail_detail_request_id`

### 现象：删除后列表不对或删错邮件

检查链路：

- `MailListItem.qml` 的确认流程
- `deleteMail()`
- `_mail_delete_request_id`
- `MailService.delete_message()`
- `IMAPService.delete_message()`
