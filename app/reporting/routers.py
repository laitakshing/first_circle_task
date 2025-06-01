# app/reporting/routers.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.reporting.service import get_payments_by_user, get_daily_totals

router = APIRouter(prefix="/users/{user_id}", tags=["reporting"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/payments", summary="All payments for a user in a date range")
def read_payments(
    user_id: UUID,
    start: date,
    end: date,
    db: Session = Depends(get_db),
):
    if start > end:
        raise HTTPException(status_code=400, detail="start must be ≤ end")
    records = get_payments_by_user(db, str(user_id), start, end)
    return {"user_id": str(user_id), "start": start, "end": end, "payments": records}

@router.get("/daily-totals", summary="Daily total sent & received for a user")
def read_daily_totals(
    user_id: UUID,
    start: date,
    end: date,
    db: Session = Depends(get_db),
):
    if start > end:
        raise HTTPException(status_code=400, detail="start must be ≤ end")
    totals = get_daily_totals(db, str(user_id), start, end)
    return {"user_id": str(user_id), "start": start, "end": end, "daily_totals": totals}
