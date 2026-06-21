from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json, os, statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "telemetry.json")

def load_telemetry():
    with open(DATA_PATH) as f:
        return json.load(f)

@app.post("/api/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    telemetry = load_telemetry()
    result = {}

    for region in regions:
        records = [r for r in telemetry if r.get("region") == region]
        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes   = [r["uptime_pct"]  for r in records]

        sorted_lat = sorted(latencies)
        p95_idx    = int(len(sorted_lat) * 0.95)
        p95        = sorted_lat[min(p95_idx, len(sorted_lat) - 1)]

        result[region] = {
            "avg_latency": round(statistics.mean(latencies), 2),
            "p95_latency": round(p95, 2),
            "avg_uptime":  round(statistics.mean(uptimes), 4),
            "breaches":    sum(1 for l in latencies if l > threshold_ms),
        }

    return JSONResponse(content=result)

@app.get("/")
def root():
    return {"status": "ok", "service": "eShopCo Analytics"}
