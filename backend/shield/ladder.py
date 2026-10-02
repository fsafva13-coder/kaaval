"""The trust ladder: Trusted -> Caution -> Challenged -> Blocked.

A sender only climbs on evidence. One sensitive request = Caution (polite
refusal, nothing visible). Asking again after a refusal = Challenged, which
triggers the Nemotron Super review. Only a confirmed review with 2+ signals
leads to Blocked.
"""
from .. import db
from . import antibodies, confirm

ORDER = ["trusted", "caution", "challenged", "blocked"]


def _climb(state: str) -> str:
    i = ORDER.index(state)
    return ORDER[min(i + 1, ORDER.index("challenged"))]


def step(sender: dict, text: str, screen: dict) -> dict:
    """Update the sender after one screened message. Returns the decision."""
    known = antibodies.match(text)
    if known and not screen["sensitive"]:
        # Reused scam script without an explicit ask yet: note it, don't refuse.
        sender["signals"].append("known_scam")

    # Threats or impersonation right after a refusal ("do it now or your account
    # will be blocked") count as pushing again, even if the secret isn't named.
    # Plain urgency does NOT: real customers often say "urgent, need it tonight!".
    hostile = set(screen.get("pressure", [])) & {"threat", "impersonation"}
    pushing = sender["state"] in ("caution", "challenged") and bool(hostile)
    if pushing and not screen["sensitive"]:
        screen = {**screen, "sensitive": True, "categories": ["pressure_after_refusal"], "tactics": screen["pressure"]}
        db.update_last_screen(sender["sender_id"], screen)

    if not screen["sensitive"]:
        db.save_sender(sender)
        return {"action": "reply", "state": sender["state"], "verdict": None}

    sender["signals"].append("sensitive_request")
    sender["signals"].extend(screen["tactics"])
    if "injection" in screen["categories"]:
        sender["signals"].append("injection")
    if known:
        sender["signals"].append("known_scam")
    if sender["refusals"] >= 1:
        sender["signals"].append("persistence")
    sender["refusals"] += 1
    sender["state"] = _climb(sender["state"])

    if known and sender["state"] == "caution":
        sender["state"] = "challenged"  # known scripts skip ahead, still need review

    verdict = None
    if sender["state"] == "challenged":
        history = db.history(sender["sender_id"])
        verdict = confirm.confirm(sender, history)
        if verdict.get("is_fraud"):
            sender["state"] = "blocked"
            db.block(sender["sender_id"], sender.get("device_id"))
            db.add_alert(sender["sender_id"], verdict)
            antibodies.learn(confirm.quotes(verdict), source=f"blocked:{sender['sender_id']}")

    db.save_sender(sender)
    action = "block" if sender["state"] == "blocked" else "refuse"
    return {"action": action, "state": sender["state"], "verdict": verdict}
