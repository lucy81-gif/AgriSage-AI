import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.models import ClimateSignal, FarmRecord, PestSignal
from backend.app import models as _models  # noqa: F401 - registers every table with metadata


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_json(data_dir: Path, filename: str) -> list[dict[str, Any]]:
    with (data_dir / filename).open("r", encoding="utf-8") as data_file:
        payload = json.load(data_file)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list in {filename}")
    return payload


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def initialize_database(
    db_engine: Engine | None = None,
    data_dir: Path | None = None,
    seed_data: bool | None = None,
) -> dict[str, int]:
    """Create all tables and seed each empty table from the checked-in synthetic data."""

    active_engine = db_engine or engine
    active_data_dir = data_dir or PROJECT_ROOT / "data"
    should_seed = get_settings().seed_data if seed_data is None else seed_data

    Base.metadata.create_all(bind=active_engine)
    _upgrade_existing_columns(active_engine)
    if not should_seed:
        return _table_counts(active_engine)

    farms = _load_json(active_data_dir, "farms.json")
    climate_signals = _load_json(active_data_dir, "climate_signals.json")
    pest_signals = _load_json(active_data_dir, "pest_signals.json")

    session_factory = sessionmaker(
        bind=active_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    with session_factory() as db:
        has_farms = db.scalar(select(func.count()).select_from(FarmRecord)) or 0
        if has_farms == 0:
            db.add_all(
                [
                    FarmRecord(
                        **{
                            **row,
                            "planting_date": _parse_date(row.get("planting_date")),
                            "last_inspection_date": _parse_date(row.get("last_inspection_date")),
                        }
                    )
                    for row in farms
                ]
            )
            db.add_all(
                [
                    ClimateSignal(
                        **{
                            **row,
                            "source_type": row.get("source_type", "SYNTHETIC"),
                            "signal_date": _parse_date(row["signal_date"]),
                            "observed_at": _parse_datetime(row["observed_at"]),
                        }
                    )
                    for row in climate_signals
                ]
            )
            db.add_all(
                [
                    PestSignal(
                        **{
                            **row,
                            "report_date": _parse_date(row["report_date"]),
                        }
                    )
                    for row in pest_signals
                ]
            )

        db.commit()

    return _table_counts(active_engine)


def _upgrade_existing_columns(active_engine: Engine) -> None:
    """Add nullable columns introduced after an existing database was created."""

    inspector = inspect(active_engine)
    existing_tables = set(inspector.get_table_names())
    with active_engine.begin() as connection:
        for table_name in (
            "climate_signals",
            "tool_call_logs",
            "workflow_runs",
            "evaluation_results",
        ):
            if table_name not in existing_tables:
                continue
            known_columns = {column["name"] for column in inspector.get_columns(table_name)}
            model_table = Base.metadata.tables[table_name]
            for column in model_table.columns:
                if column.name in known_columns:
                    continue
                sql_type = column.type.compile(dialect=active_engine.dialect)
                connection.execute(
                    text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {sql_type}')
                )
        if "workflow_runs" in existing_tables:
            connection.execute(
                text("UPDATE workflow_runs SET tool_call_count = 0 WHERE tool_call_count IS NULL")
            )
        if "climate_signals" in existing_tables:
            connection.execute(
                text("UPDATE climate_signals SET source_type = 'SYNTHETIC' WHERE source_type IS NULL")
            )


def _table_counts(active_engine: Engine) -> dict[str, int]:
    session_factory = sessionmaker(
        bind=active_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    with session_factory() as db:
        return {
            "farms": db.scalar(select(func.count()).select_from(FarmRecord)) or 0,
            "climate_signals": db.scalar(select(func.count()).select_from(ClimateSignal)) or 0,
            "pest_signals": db.scalar(select(func.count()).select_from(PestSignal)) or 0,
        }


if __name__ == "__main__":
    print(initialize_database())
