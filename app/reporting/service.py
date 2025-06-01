# app/reporting/service.py

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date

def get_payments_by_user(
    db: Session, user_id: str, start_date: date, end_date: date
):
    sql = text("""
        SELECT
          transaction_id,
          sender_id,
          receiver_id,
          amount,
          currency,
          timestamp,
          status,
          is_suspicious
        FROM transactions
        WHERE (sender_id = :user_id OR receiver_id = :user_id)
          AND timestamp BETWEEN :start_date AND :end_date
        ORDER BY timestamp;
    """)
    result = db.execute(sql, {"user_id": user_id, "start_date": start_date, "end_date": end_date})
    # Use .mappings() so each row is a mapping; .all() returns a list of Mapping objects
    return [dict(row) for row in result.mappings().all()]

def get_daily_totals(
    db: Session, user_id: str, start_date: date, end_date: date
):
    sql = text("""
        SELECT
          date_trunc('day', timestamp)::date AS day,
          SUM(CASE WHEN sender_id = :user_id THEN amount ELSE 0 END) AS total_sent,
          SUM(CASE WHEN receiver_id = :user_id THEN amount ELSE 0 END) AS total_received
        FROM transactions
        WHERE (sender_id = :user_id OR receiver_id = :user_id)
          AND timestamp BETWEEN :start_date AND :end_date
        GROUP BY day
        ORDER BY day;
    """)
    result = db.execute(sql, {"user_id": user_id, "start_date": start_date, "end_date": end_date})
    return [dict(row) for row in result.mappings().all()]
