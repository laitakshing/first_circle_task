# First Circle Data Engineer Take-Home Project

This repository contains a complete end-to-end Python application demonstrating:

1. **Database Design & Migrations**  
2. **Kafka-based Stream Ingestion**  
3. **CSV Batch Import** with Validation & Suspicious Transaction Flagging  
4. **Reporting API** powered by FastAPI  
5. **Scheduled Monthly Report Generation** via APScheduler  

---

## Architecture Overview

```text
+----------------+       +----------------+       +------------------+
| Kafka Producer |  -->  | Kafka (Docker) |  -->  | Kafka Consumer   |
| (app/ingestion/|       | localhost:9092 |       | (app/ingestion/  |
|  producer.py)  |       +----------------+       | consumers.py)    |
+----------------+                                +------------------+                                    
                                                      v
                                            +------------------+
                                            | PostgreSQL       |
                                            |   (Docker)       |
                                            |   firstcircle DB |
                                            +------------------+
                                                      ^
                                                      |
                 +---------------+---------------------+------------+
                 |                      |                           |                       
                 v                      v                           v                       
        +----------------------+  +----------------------+  +-----------------------+  
        | CSV Importer         |  | Reporting API        |  | Scheduler             |
        | (app/batch/csv_      |  | (app/main:app via    |  | (APScheduler)         |
        |  importer.py)        |  |  Uvicorn)            |  | generates monthly     |
        +----------------------+  +----------------------+  | CSV reports           |
                                                            +-----------------------+
```

- **Kafka Producer** (`app/ingestion/producer.py`) reads sample JSON lines and publishes to the `transactions` topic.  
- **Kafka Consumer** (`app/ingestion/consumer.py`) listens for messages, validates via Pydantic, and inserts into the `transactions` table.  
- **CSV Importer** (`app/batch/csv_importer.py`) loads transactions from a CSV, validates fields, flags suspicious amounts (> 10000), deduplicates, and writes to the database.  
- **FastAPI Reporting API** (`app/main.py`, `app/reporting/routers.py`) provides endpoints for per-user transaction lists and daily totals.  
- **APScheduler Job** (`app/scheduler.py`) runs daily at midnight, computing daily totals for each user for the previous month and writing `reports/monthly_report_<DATE>.csv`.  

---

## Prerequisites

- **Docker & Docker Compose** (for Kafka, Zookeeper, and PostgreSQL)  
- **Python 3.10+**  
- **`psql` CLI** (or any Postgres client)  

---

## Repository Structure

```text
first-circle-data-engineer/
├── alembic/                     # Alembic DB migrations
│   ├── env.py
│   └── versions/
├── app/                         # Application source code
│   ├── main.py                  # FastAPI app + scheduler setup
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models: users, currency, transactions
│   │   └── session.py           # SessionLocal (engine & sessionmaker)
│   ├── ingestion/
│   │   ├── consumer.py          # Kafka consumer logic
│   │   ├── producer.py          # Kafka producer for sample data
│   │   └── schemas.py           # Pydantic schemas for incoming JSON
│   ├── batch/
│   │   ├── validator.py         # Pure-Python row validation + suspicious logic
│   │   └── csv_importer.py      # CSV import, validation, dedupe, DB insert
│   ├── reporting/
│   │   ├── service.py           # SQL queries for reporting
│   │   └── routers.py           # FastAPI endpoints for payments & daily totals
│   └── scheduler.py             # APScheduler job to generate monthly reports
├── sample_data/                 # Sample data files
│   ├── sample_kafka_messages.jsonl
│   ├── sample_transactions.csv
│   └── ini.sql                  # Seed data: users & currency inserts
├── tests/                       # pytest unit tests for validator
│   └── test_validator.py
├── docker-compose.yml           # Docker Compose for Zookeeper, Kafka, Postgres
├── requirements.txt             # Python dependencies
├── .env                         # Environment variable config
└── README.md                    # Project documentation (this file)
```

---

## .env
Create a file named .env in the project root with the following contents (these values can be overridden by your environment):
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/firstcircle
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=transactions
KAFKA_CONSUMER_GROUP=first-circle-consumers
CSV_FILE=sample_data/sample_transactions.csv
REPORTS_DIR=reports
```

---

## Setup & Initialization

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd first-circle-data-engineer
```

### 2. Start Docker Services

```bash
docker-compose down -v   # Stop & remove containers and volumes (fresh start)
docker-compose up -d     # Launch Zookeeper, Kafka, and Postgres
```

- **Kafka** is available at `localhost:9092`.  
- **Postgres** (`firstcircle` DB) is available at `localhost:5432` with user/password `postgres/password`.
<img width="355" alt="image" src="https://github.com/user-attachments/assets/e98df33c-57f3-434b-b191-8a110a1f20c5" />

### 3. Python Environment & Dependencies

```bash
# (Optional) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Apply Database Migrations

Configure `DATABASE_URL` (if not hard-coded in `alembic.ini`):

```bash
export DATABASE_URL=postgresql://postgres:password@localhost:5432/firstcircle
```

Run Alembic migrations:

```bash
alembic upgrade head
```

- Creates tables: `users`, `currency`, `transactions` with all constraints & indexes.
<img width="540" alt="image" src="https://github.com/user-attachments/assets/cf3cf06a-92a9-4cfb-9c55-c6e44fd26a23" />


### 5. Seed Lookup Data (Users & Currency)

Run the provided SQL script to insert test users & currency codes:

```bash
psql $DATABASE_URL -f sample_data/ini.sql
```

The script inserts:

- Users with UUIDs (Alice, Bob, Charlie, etc.)  
- Currency codes: `USD`, `PHP`, `EUR`  

At this point, your database is fully initialized.

---

## Running Components

### 1. Kafka Ingestion

#### 1.1. Start the Kafka Consumer

In a terminal, from project root:

```bash
python -m app.ingestion.consumer
```

- Connects to Kafka `transactions` topic.  
- Logs insertion (or errors) as messages arrive.

#### 1.2. Produce Sample JSON Events

In another terminal:

```bash
python -m app.ingestion.producer
```

- Reads `sample_data/sample_kafka_messages.jsonl`.  
- Sends each JSON object (one per line) to Kafka topic `transactions` with a short delay.
<img width="451" alt="image" src="https://github.com/user-attachments/assets/b3dc42a9-92d9-4c7c-9bdb-e491400ef927" />


#### Verify Consumer Output

- Consumer logs should show `[Inserted] <transaction_id>` for valid events.  
- Schema-validation failures or duplicates are logged.

#### Verify DB Insertions

```bash
psql $DATABASE_URL -c "SELECT * FROM transactions ORDER BY timestamp;"
```

Expect only the valid messages from the JSON file.
<img width="1101" alt="image" src="https://github.com/user-attachments/assets/7a5ea77a-627b-4242-a23f-30d91ad3e56c" />


---

### 2. CSV Batch Import

#### 2.1. Truncate Existing Transactions (Optional)

Before re-running CSV import, clear out any Kafka-inserted rows:

```bash
psql $DATABASE_URL -c "TRUNCATE transactions;"
```

#### 2.2. Run the CSV Importer

```bash
python -m app.batch.csv_importer
```

- Processes `sample_data/sample_transactions.csv`.  
- Validates each row (UUIDs, amount ≥ 0, timestamp, status, currency) via `app/batch/validator.py`.  
- Flags any `amount > 10000` as `is_suspicious = true`.  
- Skips duplicates (in-memory & DB-level) and malformed rows.

#### Summarized Output

- `[Inserted] <transaction_id>` for each valid row  
- `[Duplicate-InMemory] …` or `[DB-Duplicate] …` for duplicates  
- `[ValidationError] …` for malformed rows
<img width="746" alt="image" src="https://github.com/user-attachments/assets/ca8dc3b9-996c-4406-9d4c-ce2101be49bc" />


#### Verify CSV-Inserted Rows

```bash
psql $DATABASE_URL -c "SELECT transaction_id, amount, currency, is_suspicious FROM transactions ORDER BY timestamp;"
```

Expect two inserted rows: one normal (`is_suspicious = false`), one flagged (`is_suspicious = true`).

<img width="743" alt="image" src="https://github.com/user-attachments/assets/9a2fe447-91b2-4a4d-8213-7a5f25fff660" />


---

### 3. Reporting API (FastAPI)

#### 3.1. Start the FastAPI Server

```bash
uvicorn app.main:app --reload
```

- Runs at `http://127.0.0.1:8000` by default.  
- Exposes docs at `http://127.0.0.1:8000/docs`.

#### 3.2. Available Endpoints

1. **Health Check**  
   ```http
   GET /health
   ```  
   Response:  
   ```json
   { "status": "ok" }
   ```

2. **Get All Payments for a User**  
   ```http
   GET /users/{user_id}/payments?start={YYYY-MM-DD}&end={YYYY-MM-DD}
   ```  
   - **Parameters**:  
     • `user_id`: UUID (e.g. `00000000-0000-0000-0000-000000000001`)  
     • `start`: start date (inclusive)  
     • `end`: end date (inclusive)  
   - **Response**:  
     ```json
     {
       "user_id": "00000000-0000-0000-0000-000000000001",
       "start": "2025-05-01",
       "end": "2025-05-31",
       "payments": [
         {
           "transaction_id": "...",
           "sender_id": "...",
           "receiver_id": "...",
           "amount": 250.00,
           "currency": "USD",
           "timestamp": "2025-05-20T10:00:00+00:00",
           "status": "completed",
           "is_suspicious": false
         },
         …
       ]
     }
     ```
     ![image](https://github.com/user-attachments/assets/c6e79234-891d-4a4e-a4fb-47c5cd636e19)

3. **Get Daily Totals (Sent & Received) for a User**  
   ```http
   GET /users/{user_id}/daily-totals?start={YYYY-MM-DD}&end={YYYY-MM-DD}
   ```  
   - **Parameters**: same as above.  
   - **Response**:  
     ```json
     {
       "user_id": "00000000-0000-0000-0000-000000000001",
       "start": "2025-05-01",
       "end": "2025-05-31",
       "daily_totals": [
         { "day": "2025-05-20", "total_sent": 250.00, "total_received": 0.00 },
       ]
     }
     ```
     ![image](https://github.com/user-attachments/assets/e23224df-f539-49d2-b65c-6d8e580a3c88)


#### 3.3. Example

```bash
curl "http://127.0.0.1:8000/users/00000000-0000-0000-0000-000000000001/payments?start=2025-05-01&end=2025-05-31"
```

---

### 4. Scheduler (APScheduler)

The scheduler is configured to run daily at midnight (server time) and produce a CSV summarizing each user’s daily totals for the previous month.

#### 4.1. Verify Scheduler at Startup

When running:

```bash
uvicorn app.main:app --reload
```

You should see logs similar to:

```
[Scheduler] Scheduling monthly_report_job to run daily at 00:00
[apscheduler.scheduler] Added job "generate_monthly_reports" to job store "default"
[apscheduler.scheduler] Scheduler started
[Scheduler] Scheduler started
```

#### 4.2. Manually Trigger the Job (for Testing)

```bash
python - <<EOF
from app.scheduler import generate_monthly_reports
generate_monthly_reports()
EOF
```

- Immediately writes `reports/monthly_report_<YYYY-MM-DD>.csv` (e.g. `reports/monthly_report_2025-06-01.csv`).

#### 4.3. Inspect Generated Report

```bash
ls reports
head -n 10 reports/monthly_report_2025-06-01.csv
```

- **CSV columns**: `user_id, day, total_sent, total_received`  
- One row per user/day where they had activity in the previous month.

---

## Running Tests

Unit tests are provided for validation logic in `tests/test_validator.py`. Run:

```bash
python -m pytest
```

All tests should pass, ensuring `validator.py` functions behave as expected.

---

## Dependencies

See `requirements.txt`:

```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
kafka-python
apscheduler
alembic
pytest
```

---

## Summary

This project demonstrates a minimal yet realistic data engineering workflow:

- **Schema Design & Migrations** (Alembic + SQLAlchemy)  
- **Streaming Ingestion** (Kafka Producer & Consumer)  
- **Batch Ingestion** (CSV Import with Validation & Deduplication)  
- **RESTful Reporting** (FastAPI)  
- **Scheduled Reporting** (APScheduler)  

---



## Next Steps / TODO

1. **Data Warehouse & Analytical Decomposition**  
   - Design and implement a separate data warehouse schema (e.g., using a star or snowflake schema) for analytics.  
   - Build an ETL/ELT pipeline to transform and load cleaned transaction and user data from the OLTP PostgreSQL into fact and dimension tables (e.g., `dim_user`, `dim_date`, `fact_transactions`).  
   - Consider using a columnar or cloud-native warehouse (BigQuery, Redshift, Snowflake) and schedule a nightly job to populate it.  
   - Leverage the warehouse for complex analytical queries (e.g., cohort analysis, churn prediction, month-over-month growth) without impacting the OLTP database.

2. **Dockerize the Python App**  
   - Create one or more Dockerfiles to package:
     - The FastAPI server  
     - The Kafka consumer  
     - The CSV importer  
   - Update `docker-compose.yml` to include:
     - A build for each Python service image  
     - Networking so FastAPI, consumer, and importer communicate with Kafka and Postgres by service name  
     - Volume mounts for logs and generated reports  
   - Ensure environment variables from `app/config.py` are injected into containers.  
   - Verify that `docker-compose up --build` brings up the entire stack end-to-end, including schema migrations, consumers, and API.

3. **Security & Configuration Hardening**  
   - **Secrets Management**  
     - Move database and Kafka credentials into a secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.) or Docker secrets.  
     - Reference secrets via environment variables or mounted secret volumes instead of storing plaintext in `.env` or code.  
   - **API Authentication & Authorization**  
     - Add OAuth2/JWT or API-key–based authentication to FastAPI endpoints.  
     - Enforce that `/users/{user_id}/…` can only be accessed by the appropriate user or admin roles.  
     - Implement role-based access controls (e.g., admin vs. regular user).  
   - **Network & Transport Security**  
     - Enable TLS encryption for Kafka and PostgreSQL connections.  
     - Configure firewall rules so only necessary ports (9092, 5432, 8000) are exposed to allowed networks.  

4. **Monitoring & Observability**  
   - **Metrics & Instrumentation**  
     - Instrument the Kafka consumer, CSV importer, FastAPI, and scheduler with Prometheus metrics (e.g., message throughput, error rates, job runtimes).  
     - Expose a `/metrics` endpoint in FastAPI for Prometheus scraping.  
   - **Centralized Logging**  
     - Configure structured logging (JSON) and ship logs to a central system (ELK stack, Loki, or CloudWatch).  
     - Ensure logs include correlation IDs so you can trace a request or message across consumer, API, and scheduler components.  
   - **Alerting & Dashboards**  
     - Create Grafana dashboards to visualize key metrics (e.g., daily transaction volume, consumer lag, scheduler success/failure).  
     - Set up alerts (email/Slack) for critical conditions (e.g., consumer lag > threshold, high error rates, scheduler job failures).  
   - **Health Checks & Uptime**  
     - Add FastAPI’s built-in `/health` endpoint for basic liveness/liveness checks.  
     - Configure Kubernetes or your orchestrator to probe this endpoint and restart pods on failures.
