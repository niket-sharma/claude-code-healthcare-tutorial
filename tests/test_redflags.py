"""Tests for the deterministic red-flag screening module."""

import pytest

from app.core.red_flags import RedFlagResult, check_red_flags


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fires(text: str, age: int = 40) -> bool:
    return check_red_flags(text, age) is not None


def _result(text: str, age: int = 40) -> RedFlagResult | None:
    return check_red_flags(text, age)


# ---------------------------------------------------------------------------
# Positive cases — each category must trigger
# ---------------------------------------------------------------------------

class TestChestPain:
    def test_chest_pain(self):
        assert _fires("I have chest pain that started an hour ago")

    def test_chest_pressure(self):
        assert _fires("There is chest pressure radiating to my left arm")

    def test_chest_tightness(self):
        assert _fires("Feeling chest tightness and sweating")

    def test_tight_chest(self):
        assert _fires("My chest feels tight and I am short of breath")

    def test_case_insensitive(self):
        assert _fires("CHEST PAIN since this morning")

    def test_returns_seek_immediate_care(self):
        result = _result("severe chest pain")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"
        assert "emergency" in result.message.lower() or "911" in result.message


class TestDifficultyBreathing:
    def test_difficulty_breathing(self):
        assert _fires("Having difficulty breathing after the fall")

    def test_shortness_of_breath(self):
        assert _fires("Patient reports shortness of breath on exertion")

    def test_short_of_breath(self):
        assert _fires("I am short of breath and dizzy")

    def test_cant_breathe(self):
        assert _fires("I can't breathe properly")

    def test_cannot_breathe(self):
        assert _fires("She cannot breathe without pain")

    def test_trouble_breathing(self):
        assert _fires("Having trouble breathing since this morning")

    def test_triage_level(self):
        result = _result("shortness of breath")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"


class TestStrokeSigns:
    def test_face_drooping(self):
        assert _fires("noticed face drooping on the left side")

    def test_arm_weakness(self):
        assert _fires("sudden arm weakness on the right")

    def test_slurred_speech(self):
        assert _fires("slurred speech and confusion")

    def test_sudden_confusion(self):
        assert _fires("patient has sudden confusion and cannot tell where they are")

    def test_facial_droop(self):
        assert _fires("facial droop noted, onset 20 minutes ago")

    def test_cant_speak(self):
        assert _fires("patient can't speak clearly")

    def test_one_sided_weakness(self):
        assert _fires("one-sided weakness and facial droop")

    def test_triage_level(self):
        result = _result("slurred speech and arm weakness")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"


class TestSevereBleeding:
    def test_severe_bleeding(self):
        assert _fires("severe bleeding from leg wound")

    def test_heavy_bleeding(self):
        assert _fires("bleeding heavily, cannot stop it")

    def test_uncontrolled_bleeding(self):
        assert _fires("uncontrolled bleeding after surgery")

    def test_spurting_blood(self):
        assert _fires("spurting blood from the arm")

    def test_blood_wont_stop(self):
        assert _fires("blood won't stop flowing")

    def test_triage_level(self):
        result = _result("severe bleeding from laceration")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"


class TestSuicidalIdeation:
    def test_suicidal(self):
        assert _fires("patient reports feeling suicidal")

    def test_want_to_die(self):
        assert _fires("says they want to die")

    def test_kill_myself(self):
        assert _fires("thinking about killing myself")

    def test_end_my_life(self):
        assert _fires("considering ending my life tonight")

    def test_suicide(self):
        assert _fires("expressed thoughts of suicide")

    def test_dont_want_to_live(self):
        assert _fires("don't want to live anymore")

    def test_triage_level(self):
        result = _result("patient is suicidal")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"


class TestAnaphylaxis:
    def test_anaphylaxis(self):
        assert _fires("anaphylaxis after bee sting")

    def test_anaphylactic(self):
        assert _fires("anaphylactic reaction to peanuts")

    def test_throat_closing(self):
        assert _fires("throat closing, tongue swelling")

    def test_throat_swelling(self):
        assert _fires("throat swelling after eating shellfish")

    def test_severe_allergic_reaction(self):
        assert _fires("severe allergic reaction with hives")

    def test_epipen(self):
        assert _fires("used epipen but still swelling")

    def test_tongue_swelling(self):
        assert _fires("tongue swelling and difficulty breathing")

    def test_triage_level(self):
        result = _result("anaphylaxis after wasp sting")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"


class TestSuddenSevereHeadache:
    def test_worst_headache_of_life(self):
        assert _fires("worst headache of my life, came on suddenly")

    def test_worst_headache(self):
        assert _fires("this is the worst headache I have ever had")

    def test_thunderclap_headache(self):
        assert _fires("thunderclap headache with neck stiffness")

    def test_sudden_severe_headache(self):
        assert _fires("sudden severe headache starting 10 minutes ago")

    def test_triage_level(self):
        result = _result("worst headache of life with vomiting")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"


class TestLossOfConsciousness:
    def test_unconscious(self):
        assert _fires("patient is unconscious")

    def test_unresponsive(self):
        assert _fires("patient unresponsive, not reacting to stimuli")

    def test_passed_out(self):
        assert _fires("passed out after standing up")

    def test_not_waking_up(self):
        assert _fires("not waking up after 10 minutes")

    def test_triage_level(self):
        result = _result("found unconscious on the floor")
        assert result is not None
        assert result.triage_level == "seek_immediate_care"


# ---------------------------------------------------------------------------
# Negative cases — must NOT trigger
# ---------------------------------------------------------------------------

class TestNegativeCases:
    def test_mild_headache(self):
        assert not _fires("mild headache for the past day, relieved with paracetamol")

    def test_common_cold(self):
        assert not _fires("runny nose, sore throat, low-grade fever for two days")

    def test_stomach_ache(self):
        assert not _fires("mild stomach ache after eating spicy food")

    def test_sprained_ankle(self):
        assert not _fires("twisted ankle while jogging, some swelling and bruising")

    def test_rash_no_swelling(self):
        assert not _fires("small rash on forearm, not itchy, appeared yesterday")

    def test_fatigue(self):
        assert not _fires("general fatigue and feeling run down for two weeks")

    def test_empty_string(self):
        assert not _fires("")

    def test_normal_bleeding(self):
        # Minor cut — "bleeding" alone without qualifying words should not fire
        assert not _fires("small cut on finger, minor bleeding, stopped with pressure")

    def test_past_headache_history(self):
        # "worst headache" is a red-flag phrase regardless of framing — this
        # is intentional: the module errs on the side of caution.
        # This test documents that known behaviour.
        result = _result("I used to get the worst headaches but they stopped")
        # The module WILL flag this because "worst headache" is present.
        # We assert the behaviour rather than pretend it won't trigger.
        assert result is not None  # known conservative behaviour


# ---------------------------------------------------------------------------
# Return-value structure
# ---------------------------------------------------------------------------

class TestReturnValueStructure:
    def test_none_when_clear(self):
        result = check_red_flags("slight cough for three days", age=30)
        assert result is None

    def test_result_has_required_fields(self):
        result = check_red_flags("chest pain and sweating", age=55)
        assert result is not None
        assert result.triage_level == "seek_immediate_care"
        assert isinstance(result.rationale, str) and len(result.rationale) > 0
        assert isinstance(result.message, str) and len(result.message) > 0
        assert isinstance(result.disclaimer, str) and len(result.disclaimer) > 0

    def test_rationale_names_category(self):
        result = check_red_flags("slurred speech suddenly", age=70)
        assert result is not None
        assert "stroke" in result.rationale.lower()

    def test_age_parameter_accepted(self):
        # age must be accepted without error for all plausible values
        for age in (0, 1, 17, 40, 90, 120):
            check_red_flags("mild cough", age=age)  # no exception

    def test_result_is_immutable(self):
        result = check_red_flags("chest pain", age=45)
        assert result is not None
        with pytest.raises((AttributeError, TypeError)):
            result.triage_level = "self_care"  # type: ignore[misc]

    def test_disclaimer_present(self):
        result = check_red_flags("I feel suicidal", age=25)
        assert result is not None
        assert "not a medical diagnosis" in result.disclaimer
