from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

APP_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = APP_DIR / 'data'
DB_PATH = DATA_DIR / 'mail_accounts.db'


class Base(DeclarativeBase):
    pass


engine = create_engine(
    f'sqlite:///{DB_PATH}',
    echo=False,
    future=True,
    connect_args={'check_same_thread': False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """创建数据目录并初始化数据库表。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    from app.storage import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """提供带自动提交/回滚的数据库会话上下文。"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

