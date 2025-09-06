# test_neuroshield_live_sim.py
import asyncio
import json
import uuid
import time
import random
import requests
import websockets
import matplotlib.pyplot as plt
import matplotlib.animation as animation

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/updates"

ZONES = ["DEL_CENT", "MUM_SOUTH", "BLR_CNTR", "HYD_WEST", "CHN_NORTH"]

# ---------------- API Helpers ----------------
def post_event(event_type, zone, text=None, image_path=None):
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "type": event_type,
        "zone": zone
    }
    if text:
        event["text"] = text
    if image_path:
        event["image_path"] = image_path
    resp = requests.post(f"{BASE_URL}/api/v1/ingest", json=event)
    return resp.json()

def trigger_simulate():
    resp = requests.post(f"{BASE_URL}/api/v1/simulate")
    return resp.json()

def get_scores():
    resp = requests.get(f"{BASE_URL}/api/v1/scores")
    return resp.json()

def verify_chain():
    resp = requests.get(f"{BASE_URL}/api/v1/verify")
    return resp.json()

# ---------------- WebSocket Listener ----------------
async def ws_listener(update_queue, duration=30):
    async with websockets.connect(WS_URL) as ws:
        start = time.time()
        while time.time() - start < duration:
            msg = await ws.recv()
            data = json.loads(msg)
            await update_queue.put(data)
            await asyncio.sleep(0.5)

# ---------------- Real-time NeuroMap ----------------
class NeuroMap:
    def __init__(self, zones):
        self.zones = zones
        self.history = {z: [] for z in zones}
        self.anomalies = {z: [] for z in zones}
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.ax.set_xlim(0, 50)
        self.ax.set_ylim(0, 1)
        self.ax.set_xlabel("Time Step")
        self.ax.set_ylabel("Fused Score / Risk")
        self.ax.set_title("NeuroShield Live NeuroMap")
        self.ax.grid(True)
        self.ax_lines = {z: self.ax.plot([], [], label=z)[0] for z in zones}
        self.ax.legend()

    def update_data(self, data):
        fused = data.get("fused_scores", {})
        anomalies = data.get("anomalies", {})
        for z in self.zones:
            score = fused.get(z, 0)
            self.history[z].append(score)
            self.anomalies[z].append(1 if z in anomalies else 0)

    def animate(self, frame):
        self.ax.clear()
        self.ax.set_xlim(0, max(50, len(next(iter(self.history.values())))))
        self.ax.set_ylim(0, 1)
        self.ax.set_xlabel("Time Step")
        self.ax.set_ylabel("Fused Score / Risk")
        self.ax.set_title("NeuroShield Live NeuroMap")
        self.ax.grid(True)
        for z in self.zones:
            self.ax.plot(self.history[z], label=z)
            # Red X for anomalies
            for idx, val in enumerate(self.anomalies[z]):
                if val:
                    self.ax.scatter(idx, self.history[z][idx], color="red", marker="x")
        self.ax.legend()

# ---------------- Live Simulation ----------------
async def simulate_live_events(duration=30, interval=3):
    start = time.time()
    while time.time() - start < duration:
        for z in ZONES:
            # Random citizen report
            event_type = "citizen_report"
            text = random.choice([
                f"armed mob attack at {z}",
                f"major robbery reported at {z}",
                f"suspicious bag left in {z}"
            ])
            post_event(event_type, z, text=text)
            # Random CV snapshot
            post_event("cv_snapshot", z, image_path=f"data/test_image_{z}.jpg")
        # Trigger simulation
        trigger_simulate()
        await asyncio.sleep(interval)

# ---------------- Main ----------------
if __name__ == "__main__":
    print("=== Starting NeuroShield Live Simulation & NeuroMap ===\n")

    # 1. Verify chain
    verify = verify_chain()
    print("[CHAIN VERIFY]", verify)
    print(f"[VALIDATION] Chain Integrity: {'PASS' if verify.get('valid') else 'FAIL'}")

    # 2. Setup NeuroMap and update queue
    update_queue = asyncio.Queue()
    neuromap = NeuroMap(ZONES)
    ani = animation.FuncAnimation(neuromap.fig, neuromap.animate, interval=1000)

    # 3. Run WebSocket listener + live simulation concurrently
    async def main_loop():
        ws_task = asyncio.create_task(ws_listener(update_queue, duration=60))
        sim_task = asyncio.create_task(simulate_live_events(duration=60, interval=3))
        while not ws_task.done() or not sim_task.done():
            try:
                data = await asyncio.wait_for(update_queue.get(), timeout=1.0)
                neuromap.update_data(data)
            except asyncio.TimeoutError:
                continue
        await ws_task
        await sim_task

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_loop())
    plt.show()

    print("\n=== NeuroShield Live Simulation Complete ===")
