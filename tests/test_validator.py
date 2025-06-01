# tests/test_validator.py

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from app.batch.validator import (
    parse_uuid,
    parse_decimal,
    parse_timestamp,
    parse_currency,
    parse_status,
    is_suspicious,
    validate_row,
    ValidationError,
)

def test_parse_uuid_valid():
    u = parse_uuid("transaction_id", "00000000-0000-0000-0000-000000000001")
    assert isinstance(u, UUID)

def test_parse_uuid_invalid():
    with pytest.raises(ValidationError):
        parse_uuid("transaction_id", "not-a-uuid")

@pytest.mark.parametrize("amt_str,expected", [
    ("0.00", Decimal("0.00")),
    ("123.45", Decimal("123.45")),
])
def test_parse_decimal_valid(amt_str, expected):
    assert parse_decimal("amount", amt_str) == expected

@pytest.mark.parametrize("amt_str", ["-5.00", "abc", ""])
def test_parse_decimal_invalid(amt_str):
    with pytest.raises(ValidationError):
        parse_decimal("amount", amt_str)

def test_parse_timestamp_valid():
    ts = parse_timestamp("timestamp", "2025-05-10T08:15:00Z")
    assert isinstance(ts, datetime)
    assert ts.year == 2025 and ts.month == 5 and ts.day == 10

def test_parse_timestamp_invalid():
    with pytest.raises(ValidationError):
        parse_timestamp("timestamp", "not-a-time")

def test_parse_currency_valid():
    assert parse_currency("currency", "Usd") == "USD"

@pytest.mark.parametrize("c", ["US", "USDA", "1A2", ""])
def test_parse_currency_invalid(c):
    with pytest.raises(ValidationError):
        parse_currency("currency", c)

def test_parse_status_valid():
    for s in ["pending", "completed", "failed"]:
        assert parse_status("status", s) == s

def test_parse_status_invalid():
    with pytest.raises(ValidationError):
        parse_status("status", "oops")

@pytest.mark.parametrize("amt,expected", [
    (Decimal("5000"), False),
    (Decimal("15000"), True),
])
def test_is_suspicious(amt, expected):
    assert is_suspicious(amt) is expected

def test_validate_row_success(tmp_path):
    # Build a good CSV-like dict
    row = {
        "transaction_id": "00000000-0000-0000-0000-000000000001",
        "sender_id": "00000000-0000-0000-0000-000000000002",
        "receiver_id": "00000000-0000-0000-0000-000000000003",
        "amount": "250.00",
        "currency": "usd",
        "timestamp": "2025-05-10T08:15:00Z",
        "status": "completed",
    }
    parsed = validate_row(row)
    assert isinstance(parsed["transaction_id"], UUID)
    assert isinstance(parsed["amount"], Decimal)
    assert isinstance(parsed["timestamp"], datetime)
    assert parsed["currency"] == "USD"
    assert parsed["status"] == "completed"
    assert parsed["is_suspicious"] is False

def test_validate_row_invalid(tmp_path):
    row = {
        "transaction_id": "not-a-uuid",
        "sender_id": "00000000-0000-0000-0000-000000000002",
        "receiver_id": "00000000-0000-0000-0000-000000000003",
        "amount": "-5.00",
        "currency": "usd",
        "timestamp": "2025-05-10T08:15:00Z",
        "status": "completed",
    }
    with pytest.raises(ValidationError):
        validate_row(row)
