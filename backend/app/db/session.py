from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_settings


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///") or database_url in {"sqlite://", "sqlite:///:memory:"}:
        return

    raw_path = database_url.removeprefix("sqlite:///")
    if raw_path == ":memory:":
        return

    database_path = Path(raw_path)
    if database_path.parent != Path("."):
        database_path.parent.mkdir(parents=True, exist_ok=True)


def normalize_database_url(database_url: str) -> str:
    """Use Psycopg 3 for Railway and other standard PostgreSQL URLs."""

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


settings = get_settings()
database_url = normalize_database_url(settings.resolved_database_url)
_ensure_sqlite_directory(database_url)

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    """Yield a database session for future FastAPI dependencies."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
