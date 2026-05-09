# 控制器模块地图

## 文件

- `app/controllers/app_controller.py`

## 模块定位

`AppController` 是整个项目的状态中枢。

它负责：

- 持有界面状态
- 接收 QML 信号
- 调服务层
- 启动异步任务
- 屏蔽旧请求结果
- 决定哪些数据可以写回 UI

## 核心状态

### 账号相关状态

- `_selected_account_index`
  - 左侧列表高亮账号
- `_active_account_id`
  - 当前真正打开的邮箱 id
- `_active_account_email`
  - 当前真正打开的邮箱地址

### 邮件相关状态

- `_selected_mail_index`
  - 当前选中的邮件行
- `_loaded_account_id`
  - 当前邮件列表属于哪个账号
- `_loaded_folder`
  - 当前邮件列表属于哪个文件夹

### loading / 异步状态

- `_loading`
- `_loading_count`
- `_mail_list_request_id`
- `_mail_detail_request_id`
- `_mail_delete_request_id`
- `_token_request_id`
- `_active_workers`

### 快速点击详情调度状态

- `_pending_mail_detail`
- `_mail_detail_inflight`
- `_mail_detail_inflight_request_id`
- `_mail_detail_timer`

## 最重要的公开 Slot

### `refreshAccounts()`

- 从数据库重读账号列表

### `setCurrentFolder(folder)`

- 切换 `INBOX` / `Junk`
- 如果当前有激活邮箱，就重新读该文件夹邮件

### `openAccountInbox(index)`

- 真正打开邮箱的入口
- 只应该由账号双击触发

### `refreshCurrentMailbox()`

- 重新读取当前激活邮箱的邮件列表

### `selectMail(index)`

- 先更新 UI 选中状态
- 再安排正文异步读取

### `deleteMail(index)`

- 根据当前列表项删除目标邮件
- 删除动作在后台线程执行

### `saveAccount(payload)`

- 新增或更新账号

### `refreshAccountToken(account_id)`

- 手动刷新 token

### `deleteAccount(account_id)`

- 删除账号
- 如果删的是当前激活邮箱，会顺便清空右侧状态

## 最重要的内部方法

### `_load_messages_for_account(account_id)`

- 启动一次邮件列表异步读取
- 为这次读取分配 request id

### `_schedule_message_detail(account_id, index, mail_item)`

- 邮件正文读取调度入口
- 连续点击时只保留最后一次点击目标

### `_start_pending_mail_detail()`

- 在允许的时机真正开始正文读取

### `_load_message_detail_now(account_id, index, mail_item)`

- 真正发起一次正文读取 worker

### `_handle_messages_loaded(...)`

- 只接收最新的邮件列表结果

### `_handle_message_detail_loaded(...)`

- 只接收最新有效的正文结果
- 通过 UID 而不只是 index 更新详情

### `_handle_mail_deleted(...)`

- 只接收当前有效的删除结果
- 删除成功后修正列表和当前选中状态

### `_finish_mail_detail_request(request_id)`

- 结束当前正文读取状态
- 如果还有待处理邮件，就立即启动下一次详情读取

## 这个控制器强制执行的规则

- 账号单击不触发业务动作
- 账号双击才切换邮箱
- 右侧面板跟随激活邮箱，而不是左侧高亮
- 旧请求结果不能覆盖新状态
- 邮件正文读取不能无限并发堆积
- 邮件删除必须绑定发起时的账号、文件夹和 UID

## 常见问题定位

### 右侧显示的邮箱不对

先看：

- `_active_account_id`
- `_active_account_email`

### 新列表被旧列表覆盖

先看：

- `_mail_list_request_id`

### 快速点邮件时正文乱跳

先看：

- `_pending_mail_detail`
- `_mail_detail_inflight`
- `_mail_detail_inflight_request_id`
- `_mail_detail_timer`

### loading 一直不消失

先看：

- `_loading_count`

### worker 回调没执行

先看：

- `_active_workers`
- `TaskWorker.setAutoDelete(False)`

### 删除后列表状态不对

先看：

- `_mail_delete_request_id`
- `_handle_mail_deleted()`
- 当前选中索引是否已同步调整
