"""
Deterministic red-flag screening module.

All trigger phrases are hard-coded here so a clinician can audit them without
reading any other file. This module MUST NOT call the network or load config
at runtime — it is the last safety layer before an LLM is consulted.
"""

from dataclasses import dataclass

_DISCLAIMER = (
    "This output is not a medical diagnosis. "
    "Always consult a qualified clinician for medical advice."
)

_SEEK_IMMEDIATE_CARE = "Seek immediate emergency care (call 911 or go to the nearest emergency room now)."


@dataclass(frozen=True)
class RedFlagResult:
    triage_level: str
    rationale: str
    message: str
    disclaimer: str = _DISCLAIMER


# Each entry: (category_label, [trigger phrases])
# Phrases are matched case-insensitively as substrings of the normalised text.
_RED_FLAG_CATEGORIES: list[tuple[str, list[str]]] = [
    (
        "chest pain or pressure",
        [
            "chest pain",
            "chest pressure",
            "chest tightness",
            "tight chest",
            "pressure in chest",
            "pain in chest",
            "squeezing in chest",
            "chest squeezing",
            "heaviness in chest",
            "chest heaviness",
        ],
    ),
    (
        "difficulty breathing",
        [
            "difficulty breathing",
            "trouble breathing",
            "can't breathe",
            "cannot breathe",
            "shortness of breath",
            "short of breath",
            "not breathing",
            "struggling to breathe",
            "labored breathing",
        ],
    ),
    (
        "signs of stroke",
        [
            "face drooping",
            "drooping face",
            "arm weakness",
            "weak arm",
            "slurred speech",
            "speech slurred",
            "sudden confusion",
            "sudden numbness",
            "sudden severe headache",
            "sudden vision",
            "can't speak",
            "cannot speak",
            "face droops",
            "facial droop",
            "one side weak",
            "one-sided weakness",
        ],
    ),
    (
        "severe bleeding",
        [
            "severe bleeding",
            "bleeding heavily",
            "heavy bleeding",
            "uncontrolled bleeding",
            "blood won't stop",
            "blood not stopping",
            "spurting blood",
            "bleeding profusely",
            "massive bleeding",
        ],
    ),
    (
        "suicidal ideation",
        [
            "suicidal",
            "want to die",
            "wants to die",
            "kill myself",
            "killing myself",
            "end my life",
            "ending my life",
            "take my own life",
            "taking my own life",
            "don't want to live",
            "don't want to be alive",
            "thinking about suicide",
            "suicide",
        ],
    ),
    (
        "anaphylaxis",
        [
            "anaphylaxis",
            "anaphylactic",
            "throat closing",
            "throat swelling",
            "tongue swelling",
            "swelling of throat",
            "swelling of tongue",
            "can't swallow",
            "cannot swallow",
            "severe allergic reaction",
            "epipen",
            "epinephrine",
            "whole body rash",
            "hives and swelling",
            "allergic shock",
        ],
    ),
    (
        "sudden severe headache",
        [
            "worst headache",
            "worst headache of my life",
            "worst headache of life",
            "thunderclap headache",
            "sudden severe headache",
            "sudden headache",
            "explosive headache",
        ],
    ),
    (
        "loss of consciousness",
        [
            "unconscious",
            "unresponsive",
            "passed out",
            "blacked out",
            "fainted",
            "not waking up",
            "won't wake up",
        ],
    ),
]


def check_red_flags(symptoms_text: str, age: int) -> RedFlagResult | None:  # noqa: ARG001
    """
    Scan *symptoms_text* for emergency indicators using keyword matching.

    Returns a :class:`RedFlagResult` if any red flag is detected, or ``None``
    if the text is clear.  The *age* parameter is accepted for API consistency
    and future age-stratified rules (e.g. paediatric fever thresholds).
    """
    normalised = symptoms_text.lower()

    for category, phrases in _RED_FLAG_CATEGORIES:
        for phrase in phrases:
            if phrase in normalised:
                return RedFlagResult(
                    triage_level="seek_immediate_care",
                    rationale=f"Red flag detected: {category} (matched: '{phrase}').",
                    message=_SEEK_IMMEDIATE_CARE,
                )

    return None
