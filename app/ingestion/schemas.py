# app/ingestion/schemas.py

from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from uuid import UUID

ACCEPTED_STATUSES = {"pending", "completed", "failed"}

class TransactionIn(BaseModel):
    transaction_id: UUID
    sender_id: UUID
    receiver_id: UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    currency: str = Field(..., min_length=3, max_length=3)
    timestamp: datetime
    status: str

    @validator("status")
    def status_must_be_valid(cls, v: str) -> str:
        if v not in ACCEPTED_STATUSES:
            raise ValueError(f"status must be one of {ACCEPTED_STATUSES}")
        return v

    @validator("currency")
    def currency_uppercase(cls, v: str) -> str:
        c = v.upper()
        if len(c) != 3:
            raise ValueError("currency must be a 3-letter code")
        return c
