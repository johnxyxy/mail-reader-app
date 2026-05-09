# QML 界面模块地图

## 文件

- `qml/Main.qml`
- `qml/pages/AccountPage.qml`
- `qml/pages/MailPage.qml`
- `qml/pages/MailDetailPage.qml`
- `qml/components/AccountCard.qml`
- `qml/components/MailListItem.qml`
- `qml/dialogs/AccountDialog.qml`

## 整体布局

### `Main.qml`

这是总容器。

三栏布局：

1. 左侧：账号页
2. 中间：邮件列表页
3. 右侧：邮件详情页

它本身几乎不做业务逻辑，主要负责：

- 加载页面组件
- 把页面信号接到 `appController`
- 传递控制器属性到各页面
- 打开新增/编辑账号弹窗

## 左侧：账号区

### `AccountPage.qml`

职责：

- 显示账号列表
- 搜索账号
- 显示账号总数
- 新增账号
- 编辑账号
- 删除账号
- 手动刷新 token

重要行为：

- 单击账号卡片不做任何事
- 双击账号卡片才打开邮箱

### `AccountCard.qml`

显示内容：

- 邮箱地址
- 备注
- `lastRefreshTime` 或 `lastError`

支持动作：

- 编辑
- 删除
- 刷新 token
- 双击打开邮箱

## 中间：邮件列表区

### `MailPage.qml`

显示内容：

- 当前激活邮箱地址
- loading 状态文字
- 刷新邮件按钮
- 文件夹切换按钮
- 邮件列表

向上发出的信号：

- `mailSelected(index)`
- `mailDeleteRequested(index)`
- `refreshRequested()`
- `folderChangedByUser(folder)`

### `MailListItem.qml`

显示单封邮件行：

- 主题
- 发件人
- 时间
- 已读/未读样式

重要行为：

- 支持左滑露出删除操作
- 第一步只露出“删除”按钮
- 第二步进入“确定 / 取消”确认态后才真正删除
- 滑动和点击由当前项自行处理，减少与列表滚动冲突

## 右侧：邮件详情区

### `MailDetailPage.qml`

显示内容：

- 主题
- 当前邮箱
- 发件人
- 收件人
- 时间
- 正文

重要行为：

- 如果 `body_text` 为空，会显示占位提示
- 如果 `body_html` 存在，会优先用富文本样式展示
- 这是正常行为，通常表示用户还没点邮件或详情还在读取

## 账号编辑弹窗

### `AccountDialog.qml`

字段：

- email
- password
- client id
- refresh token
- remark

保存时：

- 先组装 payload
- 再交给 `AppController.saveAccount()`

## UI 设计约定

- 大部分按钮使用 `Rectangle + MouseArea` 自绘
- 不依赖原生 Qt `Button` 风格
- 文件夹高亮完全由 `currentFolder` 决定
- 所有实际数据都来自控制器属性或 ListModel role
- 账号编辑共用同一个弹窗，通过 `accountData.id` 区分新增和编辑

## 常见问题定位

### 点了界面没反应

检查：

- 组件/页面里有没有正确发 signal
- `Main.qml` 有没有把 signal 接到 controller
- `AppController` 里对应 slot 是否存在

### Python 里有值但界面没显示

检查：

- ListModel 角色名
- delegate 里用的字段名
- `Main.qml` 里的属性绑定

### 右侧显示的账号不对

检查：

- `selectedAccountEmail` 绑定
- 再回头检查控制器里的 `active_account_email`

### 左滑删除体验不对

检查：

- `MailListItem.qml` 的滑动状态和确认态
- `MailPage.qml` 是否正确转发 `mailDeleteRequested(index)`
- `AppController.deleteMail()` 是否拿到了正确的 UID 和 folder
