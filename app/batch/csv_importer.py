# app/batch/csv_importer.py

import csv
import logging
import os
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.db.models import Transaction as TransactionModel
from app.batch.validator import validate_row, ValidationError

# Configure a logger for the importer
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("csv_importer")


def import_csv(file_path: str):
    """
    Reads each row from file_path, validates, and inserts into DB.
    Skips duplicates and logs invalid rows.
    """
    inserted = 0
    skipped_validation = 0
    skipped_duplicate = 0
    total = 0

    seen_ids = set()
    db = SessionLocal()

    with open(file_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            txn_id_str = row.get("transaction_id", "")
            # Quick duplicate‐check in memory to avoid repeated DB queries
            if txn_id_str in seen_ids:
                logger.warning(f"[Duplicate-InMemory] {txn_id_str}, skipping row #{total}")
                skipped_duplicate += 1
                continue

            try:
                parsed = validate_row(row)
            except ValidationError as e:
                logger.error(f"[ValidationError] {e} - row #{total} → {row}")
                skipped_validation += 1
                continue

            seen_ids.add(str(parsed["transaction_id"]))

            # Insert into DB
            try:
                db_txn = TransactionModel(
                    transaction_id=parsed["transaction_id"],
                    sender_id=parsed["sender_id"],
                    receiver_id=parsed["receiver_id"],
                    amount=parsed["amount"],
                    currency=parsed["currency"],
                    timestamp=parsed["timestamp"],
                    status=parsed["status"],
                    is_suspicious=parsed["is_suspicious"],
                )
                db.add(db_txn)
                db.commit()
                inserted += 1
                logger.info(f"[Inserted] {parsed['transaction_id']}")
            except IntegrityError as ie:
                db.rollback()
                # This could happen if the TXN ID was already in DB from Kafka ingestion
                logger.warning(f"[DB-Duplicate] {parsed['transaction_id']}: {ie.orig}")
                skipped_duplicate += 1
            except Exception as e:
                db.rollback()
                logger.exception(f"[DB Error] {e} on row #{total} → {parsed['transaction_id']}")

    db.close()

    logger.info(f"=== CSV Import Summary ===")
    logger.info(f"Total rows read:       {total}")
    logger.info(f"Inserted:              {inserted}")
    logger.info(f"Skipped (validation):  {skipped_validation}")
    logger.info(f"Skipped (duplicate):   {skipped_duplicate}")


if __name__ == "__main__":
    # Default to sample_data/sample_transactions.csv if no override
    csv_path = os.getenv("CSV_FILE", "sample_data/sample_transactions.csv")
    logger.info(f"Starting CSV import from {csv_path}")
    import_csv(csv_path)
