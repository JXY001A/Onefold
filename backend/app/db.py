"""数据库连接层（SQLAlchemy 2.0）：PostgreSQL。

连接串由 settings.database_url 提供：
    postgresql+psycopg://user:pass@host:5432/db
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, future=True)


# 创建 SessionLocal 类，每次调用  SessionLocal() 都会创建一个新的数据库会话 session
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)
