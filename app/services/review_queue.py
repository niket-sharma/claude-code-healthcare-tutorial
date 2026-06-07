from sqlmodel import Session

from app.models.encounter import Encounter
from app.models.review_queue import ReviewQueue

_QUEUE_ELIGIBLE = {"urgent", "seek_immediate_care"}


def is_queue_eligible(triage_level: str) -> bool:
    return triage_level in _QUEUE_ELIGIBLE


def enqueue_if_urgent(session: Session, encounter: Encounter) -> None:
    """Insert a ReviewQueue row when the encounter warrants clinician review.

    Uses the caller's session — does NOT commit. The caller owns the single
    commit so the queue insert and encounter write are atomic.
    """
    if not is_queue_eligible(encounter.triage_level or ""):
        return
    session.add(ReviewQueue(encounter_id=encounter.id))
