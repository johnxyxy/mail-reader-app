# 存储与模型模块地图

## 文件

- `app/storage/database.py`
- `app/storage/models.py`
- `app/storage/account_repository.py`
- `app/services/account_service.py`
- `app/controllers/account_model.py`
- `app/controllers/mail_model.py`

## 数据库层

### `database.py`

职责：

- 定义 SQLite 路径
  - `data/mail_accounts.db`
- 创建 SQLAlchemy engine
- 提供 `session_scope()` 事务上下文
- `init_db()` 建表

### `models.py`

当前只有一个核心持久化表：

- `Account`

字段：

- `id`
- `email`
- `password`
- `client_id`
- `refresh_token`
- `remark`
- `last_refresh_time`
- `last_error`

## Repository 层

### `AccountRepository`

它是底层数据读写层。

职责：

- 检查邮箱唯一性
- 列出账号
- 按 id 取账号
- 新增账号
- 更新账号
- 删除账号
- 更新 refresh token 和 refresh time
- 记录最后错误

它不应该关心 QML。
它只应该处理数据库对象和底层数据规则。

## 账号服务层

### `AccountService`

职责：

- 规范化表单输入
- 校验必填字段
- 把 repository 的英文错误翻译成中文提示
- 把 SQLAlchemy 对象转成普通 dict

必填字段：

- `email`
- `client_id`
- `refresh_token`

## QML 模型层

### `AccountListModel`

作用：

- 把 Python 账号 dict 列表暴露给 QML ListView

主要角色：

- `accountId`
- `email`
- `password`
- `clientId`
- `refreshToken`
- `remark`
- `lastRefreshTime`
- `lastError`

### `MailListModel`

作用：

- 把 Python 邮件 dict 列表暴露给 QML ListView

主要角色：

- `uid`
- `subject`
- `fromName`
- `fromAddress`
- `toAddress`
- `dateText`
- `preview`
- `bodyText`
- `folder`
- `isRead`

## 项目统一数据形状

### 账号 dict

```text
{
  id,
  email,
  password,
  client_id,
  refresh_token,
  remark,
  last_refresh_time,
  last_error
}
```

### 邮件 dict

```text
{
  uid,
  subject,
  from_name,
  from_address,
  to_address,
  date_text,
  preview,
  body_text,
  folder,
  is_read
}
```

## 常见问题定位

### 账号保存成功但列表没显示

优先看：

- `AccountService.save_account()`
- repository 唯一性规则
- `AppController.refresh_accounts()`

### token 刷新成功但界面仍显示旧错误

优先看：

- `AccountRepository.update_refresh_token()`
- 是否把 `last_error` 清成 `None`

### Python 里字段有值，但 QML 看不到

优先看：

- `roleNames()`
- dict 键名拼写
- `Main.qml` 绑定关系
