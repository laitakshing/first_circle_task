# app/main.py

import logging
from fastapi import FastAPI
from app.reporting.routers import router as reporting_router
from app.scheduler import start_scheduler  

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="First Circle Payments API")

# Include the reporting router
app.include_router(reporting_router)

# Optionally start background scheduler here (e.g. APScheduler) for daily jobs
@app.on_event("startup")
async def on_startup():
    start_scheduler()

# Simple health check
@app.get("/health")
def health():
    return {"status": "ok"}
