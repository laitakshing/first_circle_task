# app/ingestion/consumer.py

import json
import logging
import os
from kafka import KafkaConsumer
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from app.db.session import SessionLocal
from app.db.models import Transaction as TransactionModel
from app.ingestion.schemas import TransactionIn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("queue_consumer")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
GROUP_ID = "first-circle-consumers"


def process_message(raw_msg: bytes):
    """
    1) Parse JSON
    2) Validate via Pydantic
    3) Insert into DB if not duplicate
    """
    try:
        payload = json.loads(raw_msg.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"[Invalid JSON] {e}: {raw_msg!r}")
        return

    # Pydantic validation
    try:
        txn_in = TransactionIn(**payload)
    except Exception as e:
        logger.error(f"[Schema Validation Failed] {e} → {payload}")
        return

    # Insert into Postgres
    db = SessionLocal()
    try:
        # Check for duplicate
        exists = (
            db.query(TransactionModel)
            .filter_by(transaction_id=txn_in.transaction_id)
            .first()
        )
        if exists:
            logger.warning(f"[Duplicate] {txn_in.transaction_id}, skipping.")
            return

        db_txn = TransactionModel(
            transaction_id=txn_in.transaction_id,
            sender_id=txn_in.sender_id,
            receiver_id=txn_in.receiver_id,
            amount=txn_in.amount,
            currency=txn_in.currency,
            timestamp=txn_in.timestamp,
            status=txn_in.status,
            is_suspicious=False,  # we'll flag in CSV step instead
        )
        db.add(db_txn)
        db.commit()
        logger.info(f"[Inserted] {txn_in.transaction_id}")
    except IntegrityError as ie:
        db.rollback()
        logger.error(f"[DB IntegrityError] {ie.orig} → {txn_in.transaction_id}")
    except Exception as e:
        db.rollback()
        logger.exception(f"[DB Error] {e} → {txn_in.transaction_id}")
    finally:
        db.close()


def run_consumer():
    """
    Start consuming from Kafka. Blocks forever.
    """
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: v,  # we decode ourselves in process_message
    )
    logger.info(f"Connected to Kafka broker at {KAFKA_BROKER}, topic={KAFKA_TOPIC}")

    for msg in consumer:
        process_message(msg.value)


if __name__ == "__main__":
    run_consumer()
