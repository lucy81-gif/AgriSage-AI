from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from backend.app.core.config import LOCAL_DATABASE_URL, Settings
from backend.app.db.init_db import initialize_database
from backend.app.db.session import normalize_database_url
from backend.app.models import AdvisoryRecord


def test_database_url_omission_uses_local_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)

    assert settings.database_url is None
    assert settings.resolved_database_url == LOCAL_DATABASE_URL


def test_postgresql_urls_select_psycopg_driver():
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    postgres_engine = create_engine(
        normalize_database_url("postgresql://user:pass@localhost:5432/agrisage"),
        future=True,
    )
    try:
        assert postgres_engine.dialect.name == "postgresql"
        assert postgres_engine.dialect.driver == "psycopg"
    finally:
        postgres_engine.dispose()


def test_advisory_survives_database_engine_recreation(tmp_path):
    database_url = URL.create("sqlite", database=str(tmp_path / "restart-check.db"))
    first_engine = create_engine(
        database_url, connect_args={"check_same_thread": False}, future=True
    )
    initialize_database(db_engine=first_engine, seed_data=True)

    with Session(first_engine) as db:
        db.add(
            AdvisoryRecord(
                advisory_id="ADV-RESTART-CHECK-F012",
                farm_id="F012",
                workflow_run_id="RUN-RESTART-CHECK",
                risk_level="HIGH",
                recommendation="Inspect the field and confirm symptoms with the extension officer.",
                evidence=[{"label": "rainfall", "source": "test", "detail": "Below normal"}],
                missing_information=[],
                confidence=0.8,
                status="PENDING_APPROVAL",
                action_type="draft_advisory",
                actor="agent",
                human_approval_required=True,
            )
        )
        db.commit()
    first_engine.dispose()

    restarted_engine = create_engine(
        database_url, connect_args={"check_same_thread": False}, future=True
    )
    with Session(restarted_engine) as db:
        advisory = db.scalar(
            select(AdvisoryRecord).where(
                AdvisoryRecord.advisory_id == "ADV-RESTART-CHECK-F012"
            )
        )
        assert advisory is not None
        assert advisory.status == "PENDING_APPROVAL"
        assert advisory.recommendation.startswith("Inspect the field")
    restarted_engine.dispose()
