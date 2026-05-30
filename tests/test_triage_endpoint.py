"""Integration tests for POST /triage endpoint."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.services.triage as triage_module
from app.api.main import app
from app.core.db import get_session
from app.models.encounter import Encounter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _make_openai_response(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTriageEndpoint:
    def test_red_flag_skips_openai(self, client, monkeypatch):
        mock_create = AsyncMock()
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(triage_module, "_client", mock_client)

        response = client.post(
            "/triage",
            json={"age": 45, "sex": "male", "symptoms_text": "I have chest pain"},
        )

        assert response.status_code == 201
        mock_create.assert_not_called()
        assert response.json()["triage_level"] == "seek_immediate_care"

    def test_normal_input_returns_parsed_result(self, client, monkeypatch):
        payload = {
            "triage_level": "self_care",
            "rationale": "Minor cold.",
            "disclaimer": "This output is not a medical diagnosis. Always consult a qualified clinician for medical advice.",
        }
        mock_create = AsyncMock(return_value=_make_openai_response(payload))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(triage_module, "_client", mock_client)

        response = client.post(
            "/triage",
            json={"age": 30, "sex": "female", "symptoms_text": "runny nose"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["triage_level"] == "self_care"
        assert data["rationale"] == "Minor cold."
        mock_create.assert_awaited_once()

    def test_disclaimer_present_on_red_flag(self, client, monkeypatch):
        monkeypatch.setattr(triage_module, "_client", MagicMock())

        response = client.post(
            "/triage",
            json={"age": 30, "sex": "male", "symptoms_text": "difficulty breathing"},
        )

        assert response.status_code == 201
        assert "not a medical diagnosis" in response.json()["disclaimer"]

    def test_disclaimer_present_on_normal_result(self, client, monkeypatch):
        payload = {"triage_level": "see_clinician", "rationale": "Worth checking."}
        mock_create = AsyncMock(return_value=_make_openai_response(payload))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(triage_module, "_client", mock_client)

        response = client.post(
            "/triage",
            json={"age": 40, "sex": "female", "symptoms_text": "mild cough"},
        )

        assert response.status_code == 201
        assert "not a medical diagnosis" in response.json()["disclaimer"]

    def test_encounter_saved_to_db(self, client, session, monkeypatch):
        payload = {
            "triage_level": "self_care",
            "rationale": "Nothing serious.",
            "disclaimer": "This output is not a medical diagnosis. Always consult a qualified clinician for medical advice.",
        }
        mock_create = AsyncMock(return_value=_make_openai_response(payload))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(triage_module, "_client", mock_client)

        client.post(
            "/triage",
            json={"age": 25, "sex": "male", "symptoms_text": "minor bruise"},
        )

        session.expire_all()
        encounters = session.exec(select(Encounter)).all()
        assert len(encounters) == 1
        enc = encounters[0]
        assert enc.age == 25
        assert enc.symptoms_text == "minor bruise"
        assert enc.triage_level == "self_care"

    def test_invalid_body_returns_422(self, client, monkeypatch):
        monkeypatch.setattr(triage_module, "_client", MagicMock())

        response = client.post(
            "/triage",
            json={"sex": "male", "symptoms_text": "headache"},  # missing age
        )

        assert response.status_code == 422
