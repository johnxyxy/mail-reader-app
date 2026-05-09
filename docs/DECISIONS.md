# 项目决策记录

## 说明

这个文件记录项目里已经做出的关键实现决策，避免每次排查时重新猜一遍“为什么要这样写”。

---

## D001：统一使用 Qt `Basic` 样式

- 状态：启用中
- 原因：
  - Windows 原生 Qt 样式不允许深度自定义某些控件的 `background`、`contentItem`
  - 本项目大量使用 QML 自绘控件
- 落点：
  - `main.py`
  - `run_app.bat`
  - `qtquickcontrols2.conf`

---

## D002：QML 不直接访问数据库和 IMAP

- 状态：启用中
- 原因：
  - 保持 UI 和业务逻辑分层
  - 出问题时更容易定位
- 实际链路：
  - `QML -> AppController -> services -> storage/network`

---

## D003：账号单击不做任何事

- 状态：启用中
- 原因：
  - 用户不希望误触导致邮箱切换
  - 单击不应该触发任何网络请求
- 结果：
  - 只有双击账号才会真正打开邮箱

---

## D004：区分“高亮账号”和“当前激活邮箱”

- 状态：启用中
- 原因：
  - 左侧列表高亮不等于右侧真正打开的邮箱
  - 如果混用，账号点击会污染邮件列表状态
- 关键状态：
  - `selectedAccountIndex`
  - `active_account_id`
  - `active_account_email`

---

## D005：所有阻塞读取都必须走 `TaskWorker`

- 状态：启用中
- 原因：
  - OAuth 和 IMAP 都是阻塞网络调用
  - 放在主线程会卡住 QML 界面
- 主要位置：
  - `app/workers/task_worker.py`
  - `app/controllers/app_controller.py`

---

## D006：Python 侧必须持有 worker 引用

- 状态：启用中
- 原因：
  - `QRunnable` 默认会自动删除
  - 如果 Python 提前丢掉引用，信号回调可能不稳定
- 结果：
  - `TaskWorker.setAutoDelete(False)`
  - `AppController._active_workers`

---

## D007：使用 request id 屏蔽旧异步结果

- 状态：启用中
- 原因：
  - 用户可能在旧请求未返回前切换账号、文件夹、邮件，或重复执行删除/刷新
  - 旧结果不能覆盖新状态
- 已实现：
  - `_mail_list_request_id`
  - `_mail_detail_request_id`
  - `_mail_delete_request_id`
  - `_token_request_id`

---

## D008：邮件列表加载后不自动打开第一封

- 状态：启用中
- 原因：
  - 自动加载正文会拖慢首屏
  - 用户应自己决定看哪封邮件
- 结果：
  - 列表读取完成后 `selectedMailIndex = -1`

---

## D009：邮件列表优先读取邮件头

- 状态：启用中
- 原因：
  - 如果最近 20 封都读整封 RFC822，速度太慢
  - 列表页实际只需要主题、发件人、时间和占位摘要
- 实现位置：
  - `IMAPService.list_messages()`
  - `MailParser.parse_header_bytes()`

---

## D010：邮件头读取采用降级链路

- 状态：启用中
- 原因：
  - Outlook 批量取头返回格式不完全稳定
  - 优化不能导致“明明有邮件却显示空列表”
- 降级顺序：
  1. 批量取邮件头
  2. 逐封取邮件头
  3. 逐封取整封 RFC822

---

## D011：短时间复用 access token

- 状态：启用中
- 原因：
  - 列表读取和详情读取常常连续发生
  - 每次都去微软刷新 token 会增加额外延迟
- 当前策略：
  - 每个账号在内存里缓存 45 分钟 access token
- 实现位置：
  - `app/services/mail_service.py`

---

## D012：连续点击邮件时只保留最后一次详情读取

- 状态：启用中
- 原因：
  - IMAP 详情读取慢，而且请求一旦发出就不能真正取消
  - 用户快速点多封邮件时，后台不应该并发堆很多详情请求
- 当前策略：
  - 立即更新 UI 选中态
  - 250ms 防抖
  - 已有详情请求在跑时，只保留最后一次待读取邮件
- 实现位置：
  - `app/controllers/app_controller.py`

---

## D013：当前只支持两个文件夹

- 状态：启用中
- 文件夹：
  - `INBOX`
  - `Junk`
- 原因：
  - 目前范围是简单邮件读取，不做全量文件夹浏览器

---

## D014：数据库使用本地 SQLite

- 状态：启用中
- 原因：
  - 这是桌面工具，SQLite 依赖最少
  - 不需要额外数据库服务
- 数据库文件：
  - `data/mail_accounts.db`

---

## D015：账号表里持久化错误和刷新时间

- 状态：启用中
- 原因：
  - 左侧账号卡片需要显示上次错误原因
  - 需要知道 token 上次刷新时间
- 相关字段：
  - `last_error`
  - `last_refresh_time`

---

## D016：邮件删除采用两段确认交互

- 状态：启用中
- 原因：
  - 列表项上的删除动作容易误触
  - 直接删除会让邮件客户端体验过于激进
- 当前策略：
  - 第一步左滑露出“删除”按钮
  - 第二步点击“删除”进入“确定 / 取消”确认态
  - 真正删除才调用后台 IMAP 删除
- 实现位置：
  - `qml/components/MailListItem.qml`
  - `qml/pages/MailPage.qml`
  - `app/controllers/app_controller.py`
  - `app/services/imap_service.py`

---

## 当前已知技术债

- 仓库里还没有正式的自动化测试文件
- 目前验证主要依赖命令行 smoke test 和临时脚本验证
