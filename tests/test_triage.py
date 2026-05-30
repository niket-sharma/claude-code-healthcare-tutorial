"""Tests for the async triage service."""

import json
from unittest.mock import AsyncMock, MagicMock

import app.services.triage as triage_module
from app.services.triage import TriageResult, triage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_openai_response(payload: dict) -> MagicMock:
    """Return a fake ChatCompletion response carrying *payload* as JSON content."""
    msg = MagicMock()
    msg.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def _install_mock_client(monkeypatch, response: MagicMock) -> AsyncMock:
    """Patch _client with an AsyncMock whose create returns *response*."""
    mock_create = AsyncMock(return_value=response)
    mock_client = MagicMock()
    mock_client.chat.completions.create = mock_create
    monkeypatch.setattr(triage_module, "_client", mock_client)
    return mock_create


# ---------------------------------------------------------------------------
# Red-flag short-circuit — OpenAI must NOT be called
# ---------------------------------------------------------------------------


class TestRedFlagShortCircuit:
    async def test_chest_pain_skips_openai(self, monkeypatch):
        mock_create = AsyncMock()
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(triage_module, "_client", mock_client)

        result = await triage(age=45, sex="male", symptoms_text="I have chest pain")

        mock_create.assert_not_called()
        assert result.triage_level == "seek_immediate_care"

    async def test_red_flag_returns_triage_result_type(self, monkeypatch):
        monkeypatch.setattr(triage_module, "_client", MagicMock())
        result = await triage(
            age=30, sex="female", symptoms_text="patient is unconscious"
        )
        assert isinstance(result, TriageResult)
        assert result.triage_level == "seek_immediate_care"

    async def test_red_flag_disclaimer_present(self, monkeypatch):
        monkeypatch.setattr(triage_module, "_client", MagicMock())
        result = await triage(age=25, sex="male", symptoms_text="I feel suicidal")
        assert "not a medical diagnosis" in result.disclaimer

    async def test_red_flag_rationale_non_empty(self, monkeypatch):
        monkeypatch.setattr(triage_module, "_client", MagicMock())
        result = await triage(
            age=60, sex="female", symptoms_text="difficulty breathing"
        )
        assert result.rationale


# ---------------------------------------------------------------------------
# Successful JSON parse — all three non-emergency triage levels
# ---------------------------------------------------------------------------


class TestSuccessfulParse:
    async def test_self_care_level(self, monkeypatch):
        payload = {
            "triage_level": "self_care",
            "rationale": "Mild cold symptoms.",
            "disclaimer": "This output is not a medical diagnosis. Always consult a qualified clinician for medical advice.",
        }
        mock_create = _install_mock_client(monkeypatch, _make_openai_response(payload))
        result = await triage(age=30, sex="female", symptoms_text="mild runny nose")
        assert result.triage_level == "self_care"
        assert result.rationale == "Mild cold symptoms."
        mock_create.assert_awaited_once()

    async def test_see_clinician_level(self, monkeypatch):
        payload = {
            "triage_level": "see_clinician",
            "rationale": "Persistent fever warrants evaluation.",
            "disclaimer": "This output is not a medical diagnosis. Always consult a qualified clinician for medical advice.",
        }
        _install_mock_client(monkeypatch, _make_openai_response(payload))
        result = await triage(age=40, sex="male", symptoms_text="fever for 4 days")
        assert result.triage_level == "see_clinician"

    async def test_urgent_level(self, monkeypatch):
        payload = {
            "triage_level": "urgent",
            "rationale": "High fever with stiff neck needs same-day care.",
            "disclaimer": "This output is not a medical diagnosis. Always consult a qualified clinician for medical advice.",
        }
        _install_mock_client(monkeypatch, _make_openai_response(payload))
        result = await triage(
            age=22, sex="female", symptoms_text="very high fever, stiff neck"
        )
        assert result.triage_level == "urgent"

    async def test_result_is_triage_result_instance(self, monkeypatch):
        payload = {"triage_level": "self_care", "rationale": "Minor issue."}
        _install_mock_client(monkeypatch, _make_openai_response(payload))
        result = await triage(age=35, sex="male", symptoms_text="small bruise")
        assert isinstance(result, TriageResult)

    async def test_disclaimer_present_on_successful_parse(self, monkeypatch):
        payload = {"triage_level": "self_care", "rationale": "Fine."}
        _install_mock_client(monkeypatch, _make_openai_response(payload))
        result = await triage(age=35, sex="male", symptoms_text="slight headache")
        assert "not a medical diagnosis" in result.disclaimer

    async def test_openai_called_once_for_non_red_flag(self, monkeypatch):
        payload = {"triage_level": "see_clinician", "rationale": "Worth checking out."}
        mock_create = _install_mock_client(monkeypatch, _make_openai_response(payload))
        await triage(age=50, sex="female", symptoms_text="mild back ache")
        mock_create.assert_awaited_once()


# ---------------------------------------------------------------------------
# Malformed JSON / error fallback — must always return see_clinician
# ---------------------------------------------------------------------------


class TestMalformedJsonFallback:
    async def test_invalid_json_falls_back_to_see_clinician(self, monkeypatch):
        msg = MagicMock()
        msg.content = "I am sorry, I cannot help with that."
        choice = MagicMock()
        choice.message = msg
        bad_response = MagicMock()
        bad_response.choices = [choice]
        _install_mock_client(monkeypatch, bad_response)

        result = await triage(age=50, sex="male", symptoms_text="stomach ache")
        assert result.triage_level == "see_clinician"

    async def test_missing_triage_level_key_falls_back(self, monkeypatch):
        payload = {"rationale": "Something is wrong."}
        _install_mock_client(monkeypatch, _make_openai_response(payload))
        result = await triage(age=50, sex="female", symptoms_text="back pain")
        assert result.triage_level == "see_clinician"

    async def test_invalid_enum_value_falls_back(self, monkeypatch):
        payload = {
            "triage_level": "emergency",
            "rationale": "Unexpected value from LLM.",
        }
        _install_mock_client(monkeypatch, _make_openai_response(payload))
        result = await triage(age=50, sex="male", symptoms_text="joint pain")
        assert result.triage_level == "see_clinician"

    async def test_fallback_has_disclaimer(self, monkeypatch):
        msg = MagicMock()
        msg.content = "not json at all"
        choice = MagicMock()
        choice.message = msg
        bad_response = MagicMock()
        bad_response.choices = [choice]
        _install_mock_client(monkeypatch, bad_response)

        result = await triage(age=30, sex="female", symptoms_text="mild cough")
        assert "not a medical diagnosis" in result.disclaimer

    async def test_openai_exception_falls_back(self, monkeypatch):
        mock_create = AsyncMock(side_effect=RuntimeError("connection refused"))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(triage_module, "_client", mock_client)

        result = await triage(age=40, sex="male", symptoms_text="sprained ankle")
        assert result.triage_level == "see_clinician"

    async def test_openai_exception_fallback_has_disclaimer(self, monkeypatch):
        mock_create = AsyncMock(side_effect=ConnectionError("timeout"))
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(triage_module, "_client", mock_client)

        result = await triage(age=28, sex="female", symptoms_text="mild rash")
        assert "not a medical diagnosis" in result.disclaimer
