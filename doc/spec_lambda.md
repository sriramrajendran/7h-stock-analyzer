# 7H Stock Analyzer - Lambda Specification

Migrate the existing stock analyzer (which works per @spec_base_app.md) to run on AWS Lambda with EventBridge cron and FastAPI endpoint.

## 1. Goals

Automated daily recommendation engine using existing TA logic

Manual “Run Now” trigger via FastAPI endpoint

Historical recommendations persisted in S3 only

Pushover notifications

Static frontend reads JSON from S3 (React + Tailwind + Chart.js)

Minimal AWS cost

Clean, serverless architecture

## 2. Architecture
+--------------------+
| EventBridge Cron   |
+--------+-----------+
         |
         v
+-----------------------------+
| Lambda (Python 3.10)       |
| - Cron run                  |
| - FastAPI `/run-now`        |
| - Recommendation engine     |
| - Persist results in S3     |
| - Send Pushover notifications|
+--------+--------------------+
         |
         v
+-----------------------------+
| S3 (Static Website & JSON)  |
| - latest.json               |
| - daily/YYYY-MM-DD.json     |
+-----------------------------+
         ^
         |
+-----------------------------+
| Frontend (React + Tailwind) |
| - Dashboard & History Charts|
+-----------------------------+

## 3. Features
Feature	Description
Daily Cron	EventBridge triggers Lambda to run recommendations automatically
Manual Run API	FastAPI /run-now endpoint triggers same logic
Recommendation Engine	Preserves all existing TA logic (config-driven)
S3 Storage	latest.json + immutable daily files (daily/YYYY-MM-DD.json)
Notifications	Pushover notifications for each run
UI	React 18 + Tailwind + Chart.js reads latest.json & daily files, no backend API for history
## 4. Repository Structure
stock-app/
├── backend/
│   ├── app/
│   │   ├── main.py                 # Lambda entry (FastAPI + Cron)
│   │   ├── engine/
│   │   │   └── recommender.py      # Existing TA logic preserved
│   │   ├── services/
│   │   │   ├── s3_store.py
│   │   │   ├── pushover.py
│   │   │   └── market_data.py
│   │   ├── config.py
│   │   └── models.py
│   ├── requirements.txt
│   └── local_run.py
│
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/Dashboard.tsx
│   │   ├── components/
│   │   │   ├── RecommendationTable.tsx
│   │   │   └── PriceChart.tsx
│   │   └── api/history.ts        # Reads from S3 JSON
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── infra/
│   └── template.yaml               # SAM template
└── README.md

## 5. Lambda Behavior

### Unified Lambda (backend/app/main.py)

```python
from fastapi import FastAPI
from mangum import Mangum
from app.engine.recommender import run_engine
from app.services.s3_store import persist_results
from app.services.pushover import send_push

app = FastAPI(title="Stock Recommendation Engine")

# Manual Run API
@app.post("/run-now")
def run_now():
    results = run_engine()
    persist_results(results)
    send_push(results)
    return {"status": "ok", "recommendations": len(results)}

# Mangum adapter
asgi_handler = Mangum(app)

def handler(event, context):
    # Cron trigger
    if event.get("source") == "aws.events":
        results = run_engine()
        persist_results(results)
        send_push(results)
        return {"status": "cron executed", "count": len(results)}

    # API Gateway
    return asgi_handler(event, context)

## 6. S3 Layout
s3://stock-ui/
├── index.html
├── assets/
└── data/
    ├── latest.json
    └── daily/
        ├── 2026-02-01.json
        └── 2026-02-02.json


latest.json → dashboard load

daily/YYYY-MM-DD.json → historical charts

Immutable: daily files never overwritten

Cache: latest.json can have short TTL

## 7. Pushover Integration

Each run sends summary of recommendations

Optional: include confidence & price

Example call:

requests.post(
    "https://api.pushover.net/1/messages.json",
    data={
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": message
    }
)

## 8. EventBridge Cron Example

Runs at market open weekdays (EST):

Schedule: cron(30 14 ? * MON-FRI *)

## 9. Frontend

React 18 + Vite

Tailwind CSS for styling

Chart.js or Recharts for history charts

Loads JSON directly from S3, no API needed

Optional “Run Now” button calls /run-now endpoint (internal use)

async function runNow() {
  const res = await fetch("https://api.example.com/run-now", { method: "POST" });
  const data = await res.json();
  console.log(data);
}

## 10. AWS SAM Template (Skeleton)
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.10
    Timeout: 60
    MemorySize: 1024

Resources:
  StockAppFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.main.handler
      Policies:
        - S3FullAccess
      Events:
        Api:
          Type: HttpApi
        Cron:
          Type: Schedule
          Properties:
            Schedule: cron(30 14 ? * MON-FRI *)

## 11. Local Development

### Backend Cron Simulation

```bash
python backend/local_run.py
```

### Manual Run FastAPI

```bash
uvicorn backend.app.main:app --reload
curl -X POST http://127.0.0.1:8000/run-now
```


### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 12. Costs (Approx.)
Service	Estimated Monthly Cost
Lambda	$0.05
EventBridge	$0
S3	$0.05
API Gateway	$0
Pushover	Depends on service
Total	<$0.20 / month
## 13. Key Rules / Notes

Single Lambda handles both cron and API.

S3 is source of truth; no database required.

Daily files immutable; latest.json is only mutable file.

Push notifications via Pushover each run.

UI is fully static, reads JSON from S3.

Manual “Run Now” exists for emergencies or tests.