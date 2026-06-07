"""Unit tests for the ReviewQueue SQLModel model (Task 1)."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.models.encounter import Encounter
from app.models.review_queue import ReviewQueue  # noqa: F401 — registers table


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _encounter(age: int = 30) -> Encounter:
    return Encounter(age=age, sex="male", symptoms_text="synthetic headache")


def test_review_queue_table_exists(session: Session):
    results = session.exec(select(ReviewQueue)).all()
    assert results == []


def test_review_queue_defaults(session: Session):
    enc = _encounter()
    session.add(enc)
    session.flush()

    item = ReviewQueue(encounter_id=enc.id)
    session.add(item)
    session.commit()
    session.refresh(item)

    assert item.id is not None
    assert item.encounter_id == enc.id
    assert item.review_status == "pending"
    assert item.reviewed_at is None
    assert item.reviewed_by is None
    assert item.created_at is not None


def test_review_queue_unique_encounter_id(session: Session):
    enc = _encounter(age=45)
    session.add(enc)
    session.flush()

    session.add(ReviewQueue(encounter_id=enc.id))
    session.commit()

    session.add(ReviewQueue(encounter_id=enc.id))
    with pytest.raises(IntegrityError):
        session.commit()
