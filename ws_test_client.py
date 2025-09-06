# ws_test_client.py
import asyncio
import websockets
import json

# Replace with your backend host/port if different
WS_URI = "ws://127.0.0.1:8000/ws/updates"

async def listen_ws():
    print(f"🔹 Connecting to WebSocket at {WS_URI} ...")
    async with websockets.connect(WS_URI) as websocket:
        print("✅ Connected. Listening for updates...\n")
        try:
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                # Print summary
                print("=== WebSocket Update ===")
                fused = data.get("fused_scores", {})
                anomalies = data.get("anomalies", {})
                sentiment = data.get("sentiment", {})
                cv_scores = data.get("cv_scores", {})
                last_events = data.get("last_events", [])

                print("Fused Scores:")
                for k, v in fused.items():
                    print(f"  {k}: {v}")
                
                print("Anomalies:")
                if anomalies:
                    for k, v in anomalies.items():
                        print(f"  {k}: score={v['score']}, baseline={v['baseline']}, mult={v['mult']}")
                else:
                    print("  None")

                print("Sentiment (polarity / threat_level):")
                for k, v in sentiment.items():
                    print(f"  {k}: {v}")

                print("CV Scores:")
                for k, v in cv_scores.items():
                    print(f"  {k}: score={v.get('cv_score')}, objects={v.get('objects_detected')}")

                print("Last Events:")
                for e in last_events:
                    print(f"  {e.get('zone')} | {e.get('type')} | intent={e.get('intent')} | text={e.get('text')}")
                
                print("========================\n")
                
                await asyncio.sleep(5)  # optional, matches server broadcast interval

        except KeyboardInterrupt:
            print("🔹 WebSocket client stopped.")

# Run the async listener
asyncio.run(listen_ws())
