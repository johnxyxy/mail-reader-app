# 邮件服务模块地图

## 文件

- `app/services/mail_service.py`
- `app/services/oauth_service.py`
- `app/services/imap_service.py`
- `app/services/mail_parser.py`

## 角色分工

### `MailService`

这是服务层总调度。

职责：

- 从 repository 取账号信息
- 获取可用 token
- 调 IMAP 服务
- 给错误加上账号和文件夹上下文
- 在内存中短时间缓存 access token
- 协调邮件删除

### `OAuthService`

职责：

- 使用 `refresh_token` 向微软换新的 `access_token`
- 解析微软返回
- 把错误翻译成更可读的提示

### `IMAPService`

职责：

- 用 XOAUTH2 登录 Outlook IMAP
- 读取邮件列表
- 读取单封邮件正文
- 删除指定邮件
- 输出邮件列表读取耗时日志

### `MailParser`

职责：

- 把原始邮件字节转成项目统一 mail dict
- 列表场景只解析头
- 详情场景解析完整正文

## Token 逻辑

### Token 来源

账号表里存：

- `client_id`
- `refresh_token`

### 刷新链路

1. `MailService._get_access_token()`
2. 如果内存缓存可用，直接复用
3. 否则调 `refresh_account_token()`
4. `OAuthService.refresh_access_token()`
5. 如果微软轮换了 refresh token，就写回数据库
6. 把 access token 在内存里缓存 45 分钟

## 邮件列表读取逻辑

### 当前策略

1. IMAP 连接
2. 打开文件夹
3. 搜索最近 UID
4. 批量读取邮件头
5. 批量失败则逐封读取邮件头
6. 还不行就逐封读取整封 RFC822
7. 解析成列表项

### 这样设计的原因

- 直接整封读取最近 20 封邮件太慢
- 但单纯的批量优化在 Outlook 上不够稳定
- 所以当前策略是：优先快，但绝不能因为优化导致空列表

## 邮件详情读取逻辑

1. IMAP 连接
2. 打开文件夹
3. 按 UID 读取整封 RFC822
4. 解析正文
5. 返回完整详情 dict

## 邮件删除逻辑

1. `MailService.delete_message()` 取账号信息和 access token
2. `IMAPService.delete_message()` 连接 IMAP 并打开目标文件夹
3. 先对目标 UID 标记 `\\Deleted`
4. 再执行 `expunge()` 真正清理

### 这样设计的原因

- 删除必须作用于服务器上的真实邮件，而不是只删除前端列表项
- IMAP 删除通常是“标记删除 + 清理”两步，单做一步不够可靠

## 解析逻辑

### 列表页

- `parse_header_bytes()`
- 只解析：
  - `subject`
  - `from`
  - `to`
  - `date`
- `body_text` 为空
- `preview` 使用占位文本

### 详情页

- `parse_message_bytes()`
- 会提取：
  - 头信息
  - 正文
  - HTML 正文
  - 预览

### 正文优先级

- 优先 `text/plain`
- 没有纯文本时，退到剥标签后的 HTML
- UI 展示时如果存在 `body_html`，会优先按富文本展示

## 耗时日志

`IMAPService.list_messages()` 会输出：

- `connect`
- `search`
- `fetch_headers`
- `parse`
- `total`

排查慢时可以快速分辨：

- 是微软 OAuth 刷新慢
- 还是 IMAP 连接慢
- 还是 IMAP 搜索/取头慢
- 还是本地解析慢

## 常见问题定位

### Token 刷新失败

优先看：

- `oauth_service.py`
- `client_id`
- `refresh_token`
- `scope`

### 邮件列表为空但账号和 token 看起来正常

优先看：

- `IMAPService.list_messages()`
- 批量取头 fallback 链
- 文件夹是否正确打开

### 邮件详情很慢

优先看：

- token 是否走缓存
- `fetch_message_detail()` 是否重复刷新 token
- 控制器侧是否有快速点击堆积

### 邮件删除失败

优先看：

- `delete_message()` 是否拿到了正确 UID
- `store +FLAGS (\\Deleted)` 是否成功
- `expunge()` 是否成功
- 当前文件夹是否和邮件所在文件夹一致

### 正文乱码或预览异常

优先看：

- `MailParser._decode_part()`
- multipart 处理
- HTML 去标签逻辑
