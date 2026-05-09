from collections.abc import Mapping
from typing import Any

import requests

from app.config import OAuthConfig


class OAuthService:
    """Refresh Microsoft OAuth access tokens from stored refresh tokens."""

    def __init__(self, config: OAuthConfig) -> None:
        self._config = config

    def refresh_access_token(self, account: Mapping[str, Any]) -> dict[str, str]:
        """Return a fresh access token and the latest refresh token value."""

        refresh_token = str(account.get('refresh_token', '')).strip()
        client_id = str(account.get('client_id', '')).strip()
        if not client_id:
            raise ValueError('刷新 Token 失败：缺少 Client ID，请编辑账号后填写')
        if not refresh_token:
            raise ValueError('刷新 Token 失败：缺少 Refresh Token，请编辑账号后填写')

        try:
            # Microsoft returns a short-lived access_token for IMAP and may rotate refresh_token.
            response = requests.post(
                self._config.token_url,
                data={
                    'client_id': client_id,
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'scope': self._config.scope,
                },
                timeout=25,
            )
        except requests.Timeout as exc:
            raise ValueError('刷新 Token 失败：连接微软登录服务超时，请检查网络或代理后重试') from exc
        except requests.ConnectionError as exc:
            raise ValueError('刷新 Token 失败：无法连接微软登录服务，请检查网络或代理后重试') from exc
        except requests.RequestException as exc:
            raise ValueError(f'刷新 Token 失败：请求微软登录服务时出错（{exc.__class__.__name__}）') from exc

        payload = self._parse_payload(response)
        access_token = str(payload.get('access_token', '')).strip()
        if not access_token:
            raise ValueError('刷新 Token 失败：微软返回结果中缺少 access_token')

        new_refresh_token = str(payload.get('refresh_token', '')).strip() or refresh_token
        return {
            'access_token': access_token,
            'refresh_token': new_refresh_token,
        }

    def _parse_payload(self, response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError('刷新 Token 失败：微软返回了无法解析的数据') from exc

        if response.ok:
            return payload

        error_code = str(payload.get('error', '')).strip()
        description = str(payload.get('error_description', '')).strip()
        raise ValueError(self._translate_error(error_code, description))

    @staticmethod
    def _translate_error(error_code: str, description: str) -> str:
        if error_code == 'invalid_grant':
            return '刷新 Token 失败：Refresh Token 已失效或授权已被撤销，需要重新获取 Refresh Token'
        if error_code == 'invalid_client':
            return '刷新 Token 失败：Client ID 无效，请检查应用 ID 是否填错'
        if error_code == 'invalid_scope':
            return '刷新 Token 失败：OAuth Scope 不正确，需要包含 IMAP.AccessAsUser.All 和 offline_access'
        if error_code == 'temporarily_unavailable':
            return '刷新 Token 失败：微软服务暂时不可用，请稍后重试'
        if description:
            return f'刷新 Token 失败：{description}'
        if error_code:
            return f'刷新 Token 失败：{error_code}'
        return '刷新 Token 失败：微软未返回具体错误原因'

    @property
    def token_url(self) -> str:
        return self._config.token_url

    @property
    def scope(self) -> str:
        return self._config.scope
