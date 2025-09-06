"""
🕶️ NeuroShield - Orchestrator (Hackathon MVP)

Supports:
- CLI mode (simulate, scores, agent, verify)
- FastAPI mode (REST + WebSocket for React frontend)
"""

import os
import random
import argparse
import time
import pandas as pd
import asyncio
import uuid

# --- Internal imports ---
from chain_ext import ChainExt
from agents import NeuroAgent
from nlp_utils import classify_intent
from models import simple_forecast, zscore_anomaly
from nlp_sentiment import analyze_sentiment
from cv_utils import analyze_image

# --- Optional FastAPI imports (graceful fallback) ---
try:
    from fastapi import FastAPI, WebSocket
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except Exception:
    FastAPI = None
    WebSocket = None
    CORSMiddleware = None
    uvicorn = None

# ---------------- Config ----------------
ZONES = [
    {"id": "DEL_CENT", "name": "Delhi-Central"},
    {"id": "MUM_SOUTH", "name": "Mumbai-South"},
    {"id": "BLR_CNTR", "name": "Bengaluru-Central"},
    {"id": "HYD_WEST", "name": "Hyderabad-West"},
    {"id": "CHN_NORTH", "name": "Chennai-North"},
]

NCRB_CSV = "data/NRCB_Data.csv"
chain = ChainExt("chain.json")

TELEGRAM = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", "")
}
TWILIO = {
    "sid": os.getenv("TWILIO_SID", ""),
    "auth": os.getenv("TWILIO_AUTH", ""),
    "from": os.getenv("TWILIO_FROM", "whatsapp:+14155238886"),
    "to": os.getenv("MY_WHATSAPP", "whatsapp:+919XXXXXXXXX")
}

agent = NeuroAgent(chain, telegram_cfg=TELEGRAM, twilio_cfg=TWILIO, autonomy="review_required")

# ---------------- Baseline Loader ----------------
def load_ncrb():
    if os.path.exists(NCRB_CSV):
        return pd.read_csv(NCRB_CSV)
    return pd.DataFrame()

ncrb_df = load_ncrb()

# ---------------- Fusion Engine ----------------
def compute_baseline(zone_id, crime_type="Theft"):
    if ncrb_df.empty:
        return 0.5

    zone_to_state = {
        "DEL_CENT": "Delhi",
        "MUM_SOUTH": "Maharashtra",
        "BLR_CNTR": "Karnataka",
        "HYD_WEST": "Telangana",
        "CHN_NORTH": "Tamil Nadu"
    }

    state = zone_to_state.get(zone_id)
    if not state:
        return 0.5

    df = ncrb_df[(ncrb_df["State"] == state) & (ncrb_df["Crime_Type"] == crime_type)]
    if df.empty:
        return 0.5

    reported_sum = df["Reported_Cases"].sum()
    if reported_sum == 0:
        return 0.5
    unsolved_ratio = (df["Reported_Cases"] - df["Solved_Cases"]).sum() / reported_sum
    return round(unsolved_ratio, 2)

def fuse_scores(live_risk, baseline_ratio):
    return round(0.6 * live_risk + 0.4 * baseline_ratio, 2)

# ---------------- Simulation Functions ----------------
def simulate_cycle():
    # --- Citizen report ---
    citizen = {
        "type": "citizen_report",
        "zone": random.choice(ZONES)["id"],
        "text": random.choice([
            "chain snatching at MG Road",
            "mob fight near station",
            "suspicious bag left"
        ])
    }
    citizen["intent"] = classify_intent(citizen["text"])
    citizen["sentiment"] = analyze_sentiment(citizen["text"])
    chain.add_block(citizen)

    # --- IoT snapshot ---
    iot = {
        z["id"]: {
            "noise": random.randint(40, 110),
            "traffic": random.random(),
            "temp": random.randint(20, 42)
        } for z in ZONES
    }
    chain.add_block({"type": "iot_snapshot", "payload": iot})

    # --- Social events ---
    social = {
        "type": "social",
        "events": [{
            "zone": random.choice(ZONES)["id"],
            "text": "phone snatch reported"
        }]
    }
    for e in social["events"]:
        e["intent"] = classify_intent(e["text"])
        e["sentiment"] = analyze_sentiment(e["text"])
    chain.add_block(social)

    # --- Darknet events ---
    darknet = {
        "type": "darknet",
        "events": [{
            "zone": random.choice(ZONES)["id"],
            "text": "fake Aadhaar sale"
        }]
    }
    chain.add_block(darknet)

    print("✅ Simulated live cycle logged.")

# ---------------- Fused Score Calculation ----------------
def compute_fused_scores():
    blocks = chain._read()[-300:]
    zone_signals = {z["id"]: [] for z in ZONES}
    iot_snapshot = {}
    cv_scores = {}
    sentiment_scores = {}

    for b in blocks:
        d = b.get("data", {})
        z = d.get("zone")
        # --- Citizen/Social Reports ---
        if d.get("type") in ["citizen_report", "social", "social_report"]:
            if z:
                zone_signals.setdefault(z, []).append(d)
                if "sentiment" in d:
                    sentiment_scores[z] = d["sentiment"]
        # --- IoT ---
        if d.get("type") in ["iot_snapshot", "iot"]:
            payload = d.get("payload") or d.get("snapshot")
            if isinstance(payload, dict):
                iot_snapshot = payload
        # --- CV ---
        if d.get("type") == "cv_snapshot" and z:
            cv_scores[z] = {"cv_score": d.get("cv_score", 0), "objects_detected": d.get("objects_detected", [])}

    fused_scores = {}
    for z in ZONES:
        z_id = z["id"]
        score = 0.05
        # --- Intent-based weighting ---
        for e in zone_signals.get(z_id, []):
            intent = e.get("intent")
            if intent == "violent":
                score += 0.6
            elif intent == "property":
                score += 0.3
            elif intent == "cyber":
                score += 0.15
            else:
                score += 0.05
        # --- Sentiment contribution ---
        sentiment = sentiment_scores.get(z_id)
        if sentiment:
            score += sentiment.get("threat_level", 0) * 0.2
        # --- IoT contribution ---
        iot = iot_snapshot.get(z_id)
        if iot:
            noise_score = max(0, (iot.get("noise", 0) - 60) / 100)
            score += noise_score * 0.5 + iot.get("traffic", 0) * 0.2
        # --- CV contribution ---
        cv = cv_scores.get(z_id)
        if cv:
            score += cv.get("cv_score", 0) * 0.3

        fused_scores[z_id] = round(min(0.99, score), 2)

    baseline_ratios = {z["id"]: compute_baseline(z["id"]) for z in ZONES}
    fused_scores_final = {z: fuse_scores(fused_scores[z], baseline_ratios[z]) for z in fused_scores}

    anomalies = {
        z: {
            "score": fused_scores_final[z],
            "baseline": baseline_ratios[z],
            "mult": round(fused_scores_final[z] / (baseline_ratios[z] + 1e-6), 2)
        } for z in fused_scores_final if fused_scores_final[z] > max(0.5, baseline_ratios[z] * 1.5)
    }

    return fused_scores_final, anomalies

# ---------------- Agent Cycle ----------------
def run_agent():
    fused_scores, anomalies = compute_fused_scores()
    if not anomalies:
        print("✅ No anomalies detected. All zones stable.")
        return

    for z, info in anomalies.items():
        reasons = [f"baseline={info['baseline']} multiplier={info['mult']}"]
        plan = agent.propose_actions(z, info["score"], reasons)
        print(f"\n🚨 Proposal for {z} — score {info['score']} — intent={plan['intent']}")
        print("Suggested actions:", "; ".join(plan["actions"]))
        choice = input("Approve execution? (y/n): ").strip().lower()
        if choice == "y":
            agent.execute_plan(plan)
            print("✅ Executed. Alerts sent & logged.")
        else:
            print("❌ Skipped.")

# ---------------- FastAPI Server & WebSocket ----------------
if FastAPI:
    app = FastAPI(title="NeuroShield API", version="0.1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class ConnectionManager:
        def __init__(self):
            self.active_connections: list = []

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

        def disconnect(self, websocket: WebSocket):
            try:
                self.active_connections.remove(websocket)
            except ValueError:
                pass

        async def broadcast(self, message: dict):
            for connection in list(self.active_connections):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection)

    manager = ConnectionManager()

    def build_update_payload():
        fused, anomalies = compute_fused_scores()
        blocks = chain._read()
        last_events = [b.get("data") for b in blocks[-5:] if "data" in b]

        sentiment_data = {}
        cv_data = {}
        for e in last_events:
            z = e.get("zone")
            if not z:
                continue
            if "sentiment" in e:
                sentiment_data[z] = e["sentiment"]
            if "cv_score" in e:
                cv_data[z] = {
                    "cv_score": e.get("cv_score", 0),
                    "objects_detected": e.get("objects_detected", [])
                }

        return {
            "fused_scores": fused,
            "anomalies": anomalies,
            "sentiment": sentiment_data,
            "cv_scores": cv_data,
            "last_events": last_events
        }

    @app.get("/api/v1/scores")
    async def api_get_scores():
        fused, anomalies = compute_fused_scores()
        return {"fused_scores": fused, "anomalies": anomalies}

    @app.post("/api/v1/ingest")
    async def api_ingest(event: dict):
        event = dict(event)
        event.setdefault("id", str(uuid.uuid4()))
        event.setdefault("timestamp", time.time())
        event.setdefault("type", event.get("type", "citizen_report"))

        zone = event.get("zone")
        event_type = event["type"]

        if event_type in ["citizen_report", "social", "social_report"] and "text" in event:
            event["intent"] = classify_intent(event["text"])
            event["sentiment"] = analyze_sentiment(event["text"])

        if event_type == "cv_snapshot" and "image_path" in event:
            cv_result = analyze_image(event["image_path"])
            event["cv_score"] = cv_result["cv_score"]
            event["objects_detected"] = cv_result["objects_detected"]

        chain.add_block(event)
        await manager.broadcast(build_update_payload())
        return {"status": "ok", "event": event}

    @app.post("/api/v1/simulate")
    async def api_simulate():
        simulate_cycle()
        await manager.broadcast(build_update_payload())
        return {"status": "ok", "message": "Simulated live cycle logged."}

    @app.get("/api/v1/verify")
    async def api_verify():
        ok, idx = chain.verify()
        if ok:
            return {"valid": True}
        else:
            return {"valid": False, "corrupt_index": idx}

    @app.get("/api/v1/chain")
    async def api_get_chain(limit: int = 20):
        blocks = chain._read()
        recent = blocks[-limit:] if len(blocks) >= limit else blocks
        events = [b.get("data") for b in recent if "data" in b]
        return {"events": events}

    @app.websocket("/ws/updates")
    async def websocket_endpoint(ws: WebSocket):
        await manager.connect(ws)
        try:
            while True:
                await asyncio.sleep(5)
                await manager.broadcast(build_update_payload())
        except Exception:
            manager.disconnect(ws)

# ---------------- CLI ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NeuroShield CLI")
    parser.add_argument("command", choices=["simulate", "scores", "agent", "verify"], help="Command to run")
    args = parser.parse_args()

    if args.command == "simulate":
        simulate_cycle()
    elif args.command == "scores":
        fused, anomalies = compute_fused_scores()
        print("Fused Scores:", fused)
        print("Anomalies:", anomalies)
    elif args.command == "agent":
        run_agent()
    elif args.command == "verify":
        ok, idx = chain.verify()
        print("Chain valid ✅" if ok else f"Chain corrupt at {idx}")
