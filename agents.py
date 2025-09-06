# agents.py
from chain_ext import ChainExt
from nlp_utils import classify_intent
from alerts import send_telegram, send_whatsapp
import time

class NeuroAgent:
    def __init__(self, chain: ChainExt, telegram_cfg=None, twilio_cfg=None, autonomy="review_required"):
        self.chain = chain
        self.telegram_cfg = telegram_cfg or {}
        self.twilio_cfg = twilio_cfg or {}
        self.autonomy = autonomy  # review_required, suggest_only, auto_execute

    def propose_actions(self, zone, fused_score, reasons):
        intent = classify_intent(" ".join(reasons))
        plan = {
            "zone": zone,
            "score": fused_score,
            "intent": intent,
            "actions": []
        }
        if fused_score > 0.8 or intent=="violent":
            plan["actions"] += ["Dispatch rapid-response units", "Push public WhatsApp alert", "Notify local police"]
        elif fused_score > 0.55:
            plan["actions"] += ["Increase patrol", "Deploy CCTV"]
        else:
            plan["actions"] += ["Monitor"]
        return plan

    def execute_plan(self, plan):
        msg = f"NeuroShield Action for {plan['zone']}: {'; '.join(plan['actions'])}"
        if self.telegram_cfg:
            send_telegram(self.telegram_cfg.get("bot_token"), self.telegram_cfg.get("chat_id"), msg)
        if self.twilio_cfg:
            send_whatsapp(self.twilio_cfg.get("sid"), self.twilio_cfg.get("auth"),
                          self.twilio_cfg.get("from"), self.twilio_cfg.get("to"), msg)
        self.chain.add_block({"type":"execution","plan":plan,"ts":time.time()})
        return True
