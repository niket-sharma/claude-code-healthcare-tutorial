from __future__ import annotations

import json
import logging
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.red_flags import check_red_flags

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "This output is not a medical diagnosis. "
    "Always consult a qualified clinician for medical advice."
)

_SYSTEM_PROMPT = """\
You are a medical triage assistant for an educational demo application.
You are NOT a doctor and this is NOT a medical diagnosis.

Given a patient's age, sex, and symptom description, respond with a JSON object
containing exactly these three keys:

  "triage_level": one of "self_care", "see_clinician", or "urgent"
  "rationale":    a brief plain-English explanation (1-3 sentences)
  "disclaimer":   must be exactly: "This output is not a medical diagnosis. Always consult a qualified clinician for medical advice."

Rules:
- Use "self_care" for minor, self-limiting symptoms (e.g. mild cold, minor bruise).
- Use "see_clinician" for symptoms that warrant professional evaluation but are not emergencies.
- Use "urgent" for symptoms requiring same-day or next-day care.
- Do NOT use "seek_immediate_care" — that level is handled by a separate safety system.
- Respond with valid JSON only. No markdown, no code fences, no extra keys.\
"""


class TriageResult(BaseModel):
    triage_level: Literal["self_care", "see_clinician", "urgent", "seek_immediate_care"]
    rationale: str
    disclaimer: str = DISCLAIMER


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


async def triage(age: int, sex: str, symptoms_text: str) -> TriageResult:
    # 1. Deterministic red-flag gate — never calls OpenAI if triggered
    red_flag = check_red_flags(symptoms_text, age)
    if red_flag is not None:
        return TriageResult(
            triage_level=red_flag.triage_level,
            rationale=red_flag.rationale,
            disclaimer=red_flag.disclaimer,
        )

    # 2. OpenAI call with json_object response format
    user_content = f"Patient age: {age}\nPatient sex: {sex}\nSymptoms: {symptoms_text}"
    try:
        response = await _get_client().chat.completions.create(
            model=get_settings().openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        raw = response.choices[0].message.content or ""
    except Exception:
        logger.exception("OpenAI call failed; falling back to see_clinician")
        return TriageResult(
            triage_level="see_clinician",
            rationale="Could not reach triage service. Please consult a clinician.",
            disclaimer=DISCLAIMER,
        )

    # 3. Parse JSON with fail-safe fallback to see_clinician
    try:
        data = json.loads(raw)
        return TriageResult(
            triage_level=data["triage_level"],
            rationale=data["rationale"],
            disclaimer=data.get("disclaimer", DISCLAIMER),
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        logger.warning("Malformed JSON from OpenAI; raw=%r", raw)
        return TriageResult(
            triage_level="see_clinician",
            rationale="Response could not be parsed. Please consult a clinician.",
            disclaimer=DISCLAIMER,
        )
