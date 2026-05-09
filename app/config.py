from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthConfig:
    token_url: str = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
    scope: str = 'https://outlook.office.com/IMAP.AccessAsUser.All offline_access'


@dataclass(frozen=True)
class ImapConfig:
    host: str = 'outlook.live.com'
    port: int = 993
    default_folder: str = 'INBOX'
    page_size: int = 20


@dataclass(frozen=True)
class AppConfig:
    oauth: OAuthConfig = OAuthConfig()
    imap: ImapConfig = ImapConfig()


DEFAULT_CONFIG = AppConfig()
