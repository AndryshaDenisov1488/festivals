# database.py — ПОЛНЫЙ ФАЙЛ
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse
from config import DATABASE_URL

# Определяем, sqlite ли это
def _is_sqlite(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return (parsed.scheme or "").startswith("sqlite")
    except Exception:
        return url.startswith("sqlite")

IS_SQLITE = _is_sqlite(DATABASE_URL)

# Создаём engine
# Важно: для SQLite — check_same_thread=False (бот + планировщик/потоки),
# pool_pre_ping=True — заранее проверяем соединение.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    future=True,
)

# Для SQLite — ставим полезные PRAGMA на каждом подключении
if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # ждём блокировку до 5 сек, чтобы реже ловить "database is locked"
        cursor.execute("PRAGMA busy_timeout = 5000;")
        # журнал в WAL — меньше конфликтов чтения/записи
        cursor.execute("PRAGMA journal_mode = WAL;")
        # чуть быстрее и достаточно надёжно для бота
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.close()

# Фабрика сессий
# expire_on_commit=False — объекты остаются «живыми» после commit()
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)

# (опционально) контекстный менеджер, если удобно использовать "with"
# from contextlib import contextmanager
# @contextmanager
# def session_scope():
#     session = SessionLocal()
#     try:
#         yield session
#         session.commit()
#     except:
#         session.rollback()
#         raise
#     finally:
#         session.close()
