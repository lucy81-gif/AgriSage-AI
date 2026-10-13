from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.db.init_db import initialize_database
from backend.app.models import ClimateSignal, FarmRecord, PestSignal
from backend.app.db.base import Base


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_synthetic_data_seeds_expected_records_and_is_idempotent():
    test_engine = create_engine("sqlite:///:memory:", future=True)

    first_counts = initialize_database(
        db_engine=test_engine,
        data_dir=PROJECT_ROOT / "data",
        seed_data=True,
    )
    second_counts = initialize_database(
        db_engine=test_engine,
        data_dir=PROJECT_ROOT / "data",
        seed_data=True,
    )

    assert first_counts == {"farms": 26, "climate_signals": 8, "pest_signals": 10}
    assert second_counts == first_counts

    with Session(test_engine) as db:
        missing_planting_date = db.scalar(
            select(FarmRecord).where(FarmRecord.farm_id == "F021")
        )
        unavailable_climate = db.scalar(
            select(ClimateSignal).where(ClimateSignal.availability_status == "UNAVAILABLE")
        )
        recent_high_pest = db.scalar(
            select(PestSignal).where(PestSignal.severity == "HIGH")
        )

    assert missing_planting_date is not None
    assert missing_planting_date.planting_date is None
    assert unavailable_climate is not None
    assert recent_high_pest is not None


def test_seed_does_not_add_demo_records_to_a_database_with_existing_farms():
    test_engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(test_engine)
    with Session(test_engine) as db:
        db.add(
            FarmRecord(
                farm_id="LOCAL-1",
                household_id="SYNTHETIC-LOCAL-1",
                district="Maseru",
                agroclimatic_zone="Lowlands",
                crop="maize",
                crop_variety="Local record",
                field_size_ha=0.5,
                irrigation_type="rainfed",
            )
        )
        db.commit()

    counts = initialize_database(
        db_engine=test_engine,
        data_dir=PROJECT_ROOT / "data",
        seed_data=True,
    )
    assert counts == {"farms": 1, "climate_signals": 0, "pest_signals": 0}
