from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db.init_db import initialize_database
from backend.app.db.session import get_db
from backend.app.models import AdvisoryRecord, ClimateSignal, FarmRecord, PestSignal, ToolCallLog
from backend.app.api.routes import router as api_router
from backend.app.schemas.bootstrap import BootstrapSummary


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Phase 1 data foundation for evidence-backed climate-smart agricultural advisory.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str | bool]:
    """Basic liveness/readiness check that also confirms database connectivity."""

    db.execute(select(1))
    return {"status": "ok", "database": "connected", "seed_data_enabled": settings.seed_data}


@app.get("/api/v1/bootstrap-summary", response_model=BootstrapSummary)
def bootstrap_summary(db: Session = Depends(get_db)) -> BootstrapSummary:
    """Return counts from the database; no statistics are hard-coded in the API."""

    districts = db.scalars(select(FarmRecord.district).distinct().order_by(FarmRecord.district)).all()
    crops = db.scalars(select(FarmRecord.crop).distinct().order_by(FarmRecord.crop)).all()
    return BootstrapSummary(
        farms=db.scalar(select(func.count()).select_from(FarmRecord)) or 0,
        climate_signals=db.scalar(select(func.count()).select_from(ClimateSignal)) or 0,
        pest_signals=db.scalar(select(func.count()).select_from(PestSignal)) or 0,
        advisory_records=db.scalar(select(func.count()).select_from(AdvisoryRecord)) or 0,
        tool_call_logs=db.scalar(select(func.count()).select_from(ToolCallLog)) or 0,
        districts=list(districts),
        crops=list(crops),
    )
