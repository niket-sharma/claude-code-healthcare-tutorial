import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.core.db import create_db_and_tables, get_session
from app.models.encounter import Encounter
from app.models.review_queue import ReviewQueue as _ReviewQueue  # noqa: F401 — registers table
from app.services.review_queue import enqueue_if_urgent
from app.services.triage import TriageResult, triage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="CareTriage API", lifespan=lifespan)


class TriageRequest(BaseModel):
    age: int
    sex: str
    symptoms_text: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/triage", status_code=201, response_model=TriageResult)
async def create_triage(
    body: TriageRequest,
    session: Session = Depends(get_session),
) -> TriageResult:
    result = await triage(body.age, body.sex, body.symptoms_text)
    encounter = Encounter(
        age=body.age,
        sex=body.sex,
        symptoms_text=body.symptoms_text,
        triage_level=result.triage_level,
        rationale=result.rationale,
        disclaimer=result.disclaimer,
    )
    session.add(encounter)
    try:
        session.flush()  # obtain encounter.id before enqueue
        enqueue_if_urgent(session, encounter)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to persist encounter or review queue entry")
        raise HTTPException(status_code=503, detail="Could not save encounter. Please try again.")
    return result
