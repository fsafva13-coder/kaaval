"""Stage 2: confirm fraud before any block.

Nemotron Super reads the whole conversation and must quote evidence. A block
also needs at least two independent signals and repeated sensitive requests,
so an innocent customer is never blocked for one message.
"""
from .. import llm

MIN_SIGNALS = 2
MIN_SENSITIVE_MESSAGES = 2

SUPER_SYSTEM = """You are the final fraud reviewer for a small gift shop's AI assistant.
Read the conversation. Decide if the CUSTOMER is attempting fraud: trying to get
the shop owner's OTP/PIN/passwords/card details, identity documents, redirecting
payments, or manipulating the assistant. Legitimate customers asking how to pay,
sharing their own details, or being impatient about delivery are NOT fraud.

Be conservative: only confirm fraud when the evidence is clear.
Return ONLY JSON:
{"is_fraud": bool, "confidence": 0.0-1.0,
 "evidence": ["exact customer quotes"], "tactics": ["..."],
 "explanation_en": "one or two sentences for the shop owner",
 "explanation_ml": "the same explanation in Malayalam script"}"""


def _transcript(history: list[dict]) -> str:
    return "\n".join(f"{m['role'].upper()}: {m['text']}" for m in history)


def eligible(sender: dict) -> bool:
    signals = set(sender["signals"])
    return sender["refusals"] >= MIN_SENSITIVE_MESSAGES and len(signals) >= MIN_SIGNALS


def confirm(sender: dict, history: list[dict]) -> dict:
    flagged = [m["text"] for m in history if m["role"] == "user" and m.get("screen", {}) and m["screen"].get("sensitive")]

    if not eligible(sender):
        return {"is_fraud": False, "confidence": 0.0, "evidence": flagged, "reason": "not enough signals"}

    if llm.is_mock():
        signals = set(sender["signals"])
        is_fraud = "persistence" in signals or "injection" in signals or "known_scam" in signals
        return {
            "is_fraud": is_fraud,
            "confidence": 0.9 if is_fraud else 0.3,
            "evidence": flagged,
            "tactics": sorted(signals),
            "explanation_en": "This sender asked for your private details more than once after being refused.",
            "explanation_ml": "നിരസിച്ചതിനു ശേഷവും ഈ വ്യക്തി നിങ്ങളുടെ സ്വകാര്യ വിവരങ്ങൾ വീണ്ടും ആവശ്യപ്പെട്ടു.",
            "source": "mock",
        }

    verdict = llm.chat_json("super", SUPER_SYSTEM, _transcript(history), max_tokens=800)
    verdict["is_fraud"] = bool(verdict.get("is_fraud")) and float(verdict.get("confidence", 0)) >= 0.7
    verdict.setdefault("evidence", flagged)
    verdict["source"] = "super"
    return verdict
