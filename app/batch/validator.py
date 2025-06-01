# app/batch/validator.py

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

# We can adjust this threshold as needed
SUSPICIOUS_THRESHOLD = Decimal("10000.00")
ACCEPTED_STATUSES = {"pending", "completed", "failed"}


class ValidationError(Exception):
    """Raise when any field fails validation."""
    pass


def parse_uuid(field_name: str, value: str) -> UUID:
    try:
        return UUID(value)
    except Exception:
        raise ValidationError(f"{field_name} is not a valid UUID: {value!r}")


def parse_decimal(field_name: str, value: str) -> Decimal:
    try:
        dec = Decimal(value)
    except InvalidOperation:
        raise ValidationError(f"{field_name} is not a valid decimal: {value!r}")
    if dec < 0:
        raise ValidationError(f"{field_name} must be non-negative: {value!r}")
    return dec


def parse_timestamp(field_name: str, value: str) -> datetime:
    # Expecting something like "2025-05-10T08:15:00Z"
    try:
        # Python’s fromisoformat doesn’t accept "Z", so replace it
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        raise ValidationError(f"{field_name} is not valid iso8601 datetime: {value!r}")


def parse_currency(field_name: str, value: str) -> str:
    c = value.strip().upper()
    # now ensure exactly 3 letters (A–Z)  
    if len(c) != 3 or not c.isalpha():
        raise ValidationError(f"{field_name} must be a 3-letter alphabetic code: {value!r}")
    return c


def parse_status(field_name: str, value: str) -> str:
    s = value.strip().lower()
    if s not in ACCEPTED_STATUSES:
        raise ValidationError(f"{field_name} must be one of {ACCEPTED_STATUSES}: {value!r}")
    return s


def is_suspicious(amount: Decimal) -> bool:
    return amount > SUSPICIOUS_THRESHOLD


def validate_row(row: dict) -> dict:
    """
    Takes a dict from csv.DictReader and returns a new dict with parsed/typed fields:
      {
        "transaction_id": UUID(...),
        "sender_id": UUID(...),
        "receiver_id": UUID(...),
        "amount": Decimal(...),
        "currency": "USD",
        "timestamp": datetime(...),
        "status": "completed",
        "is_suspicious": True/False
      }
    Raises ValidationError on any invalid field.
    """
    txn_id = parse_uuid("transaction_id", row.get("transaction_id", ""))
    sender = parse_uuid("sender_id", row.get("sender_id", ""))
    receiver = parse_uuid("receiver_id", row.get("receiver_id", ""))
    amount = parse_decimal("amount", row.get("amount", ""))
    currency = parse_currency("currency", row.get("currency", ""))
    timestamp = parse_timestamp("timestamp", row.get("timestamp", ""))
    status = parse_status("status", row.get("status", ""))

    return {
        "transaction_id": txn_id,
        "sender_id": sender,
        "receiver_id": receiver,
        "amount": amount,
        "currency": currency,
        "timestamp": timestamp,
        "status": status,
        "is_suspicious": is_suspicious(amount),
    }
