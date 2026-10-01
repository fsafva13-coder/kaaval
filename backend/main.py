"""Kaaval API.

Customer:  POST /api/chat, GET /api/chat/status
Owner:     GET /api/owner/alerts, GET /api/owner/senders, POST /api/owner/unblock, GET /api/owner/budget
"""
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import assistant, db, llm
from .config import DAILY_MESSAGE_LIMIT, OWNER_PASSCODE
from .shield import ladder, screen

app = FastAPI(title="Kaaval", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BLOCKED_BODY = {"blocked": True, "message": "This conversation has been closed."}
PAUSED_BODY = {"paused": True, "message": "The Kaaval demo is paused for today. Please try again later."}


class ChatIn(BaseModel):
    sender_id: str = Field(min_length=4, max_length=64)
    device_id: str | None = Field(default=None, max_length=128)
    text: str = Field(min_length=1, max_length=2000)


class UnblockIn(BaseModel):
    sender_id: str


def _owner(passcode: str | None) -> None:
    if passcode != OWNER_PASSCODE:
        raise HTTPException(status_code=401, detail="Wrong owner passcode")


@app.get("/api/health")
def health():
    return {"ok": True, "budget": llm.budget_status()}


@app.get("/api/chat/status")
def chat_status(sender_id: str, device_id: str | None = None):
    if db.is_blocked(sender_id, device_id):
        return JSONResponse(status_code=403, content=BLOCKED_BODY)
    return {"blocked": False, "history": db.history(sender_id)}


@app.post("/api/chat")
def chat(body: ChatIn):
    # 1. Blocks are enforced on the server, by sender AND device.
    if db.is_blocked(body.sender_id, body.device_id):
        return JSONResponse(status_code=403, content=BLOCKED_BODY)

    # 2. Protect credits: per-visitor daily limit and the global budget cap.
    if db.messages_today(body.sender_id) >= DAILY_MESSAGE_LIMIT:
        return JSONResponse(status_code=429, content={"limited": True, "message": "Daily demo limit reached."})
    if llm.budget_status()["paused"]:
        return JSONResponse(status_code=503, content=PAUSED_BODY)

    try:
        sender = db.get_sender(body.sender_id, body.device_id)
        verdict = screen.screen(body.text)
        db.add_message(body.sender_id, "user", body.text, verdict)
        decision = ladder.step(sender, body.text, verdict)

        if decision["action"] == "block":
            return JSONResponse(status_code=403, content={**BLOCKED_BODY, "state": "blocked"})

        if decision["action"] == "refuse":
            text = assistant.REFUSAL
        else:
            sender["profile"] = assistant.remember(sender["profile"], body.text)
            db.save_sender(sender)
            text = assistant.reply(body.text, db.history(body.sender_id), sender["profile"])

        db.add_message(body.sender_id, "assistant", text)
        # The customer never sees their trust state; only the owner does.
        return {"reply": text}
    except llm.BudgetExceeded:
        return JSONResponse(status_code=503, content=PAUSED_BODY)


@app.get("/api/owner/alerts")
def owner_alerts(x_owner_passcode: str | None = Header(default=None)):
    _owner(x_owner_passcode)
    return db.list_alerts()


@app.get("/api/owner/senders")
def owner_senders(x_owner_passcode: str | None = Header(default=None)):
    _owner(x_owner_passcode)
    rows = db.query("SELECT sender_id, state, refusals, signals, created_at FROM senders ORDER BY created_at DESC")
    return [dict(r) for r in rows]


@app.post("/api/owner/unblock")
def owner_unblock(body: UnblockIn, x_owner_passcode: str | None = Header(default=None)):
    _owner(x_owner_passcode)
    db.unblock(body.sender_id)
    return {"ok": True}


@app.get("/api/owner/budget")
def owner_budget(x_owner_passcode: str | None = Header(default=None)):
    _owner(x_owner_passcode)
    return llm.budget_status()
