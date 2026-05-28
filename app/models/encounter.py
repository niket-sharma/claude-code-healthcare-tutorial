from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

_DISCLAIMER = (
    "This output is not a medical diagnosis. "
    "Always consult a qualified clinician for medical advice."
)


class Encounter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    age: int
    sex: str
    symptoms_text: str
    triage_level: Optional[str] = None
    rationale: Optional[str] = None
    disclaimer: str = Field(default=_DISCLAIMER)
