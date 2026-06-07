from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ReviewQueue(SQLModel, table=True):
    __tablename__ = "review_queue"

    id: Optional[int] = Field(default=None, primary_key=True)
    encounter_id: int = Field(foreign_key="encounter.id", unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    review_status: str = Field(default="pending")
    reviewed_at: Optional[datetime] = Field(default=None)
    reviewed_by: Optional[str] = Field(default=None)
