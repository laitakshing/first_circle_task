# app/scheduler.py

import os
import csv
import logging
from datetime import date, timedelta
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.reporting.service import get_daily_totals

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()

def generate_monthly_reports():
    logger.info("[Scheduler] Running generate_monthly_reports()")
    """
    For each user, compute daily totals (sent/received) for the previous month
    and write everything into a single CSV file under reports/.
    """
    db: Session = SessionLocal()
    try:
        # 1) Determine previous month range
        today = date.today()
        first_of_this_month = today.replace(day=1)
        last_of_last_month = first_of_this_month - timedelta(days=1)
        start_last_month = last_of_last_month.replace(day=1)
        end_last_month = last_of_last_month

        # 2) Fetch all user IDs
        result = db.execute(text("SELECT id FROM users"))
        user_ids = [row[0] for row in result.fetchall()]

        # 3) Prepare output directory & CSV file
        os.makedirs("reports", exist_ok=True)
        report_filename = f"monthly_report_{today.isoformat()}.csv"
        report_path = os.path.join("reports", report_filename)

        with open(report_path, mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # header columns
            writer.writerow([
                "user_id",
                "day",
                "total_sent",
                "total_received"
            ])

            # 4) For each user, fetch daily totals and write rows
            for uid in user_ids:
                # get_daily_totals expects a string UUID, plus Python date objects
                daily_rows = get_daily_totals(db, str(uid), start_last_month, end_last_month)
                for row in daily_rows:
                    # row is a dict: {"day": date, "total_sent": Decimal, "total_received": Decimal}
                    writer.writerow([
                        str(uid),
                        row["day"].isoformat(),
                        row["total_sent"],
                        row["total_received"],
                    ])

        print(f"[Scheduler] Wrote monthly report: {report_path}")

    except Exception as e:
        print(f"[Scheduler][Error] Failed to generate monthly reports: {e}")
    finally:
        db.close()

def start_scheduler():
    logger.info("[Scheduler] Scheduling monthly_report_job to run daily at 00:00")
    """
    Schedule generate_monthly_reports() to run every day at midnight.
    Call this function from FastAPI startup.
    """
    # Run daily at 00:00
    scheduler.add_job(
        generate_monthly_reports,
        trigger="cron",
        hour=0,
        minute=0,
        id="monthly_report_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] Scheduler started")

# def start_scheduler():
#     logger.info("[Scheduler] Scheduling monthly_report_job to run every minute (test mode)")
#     scheduler.add_job(
#         generate_monthly_reports,
#         trigger="interval",
#         minutes=1,
#         id="monthly_report_job",
#         replace_existing=True,
#     )
#     scheduler.start()
