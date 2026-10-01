"""Every model call goes through this file.

Two safety features live here:
1. MOCK_LLM mode: no network calls at all, so you can build for free.
2. Budget guard: every real call is priced and logged; once the hard cap is
   reached, all calls are refused, so your card is never charged.
"""
import json
import os
import re

from . import db
from .config import (
    BUDGET_HARD_CAP_USD,
    BUDGET_WARN_USD,
    MOCK_LLM,
    PRICES,
    PROVIDER,
    PROVIDERS,
)


class BudgetExceeded(Exception):
    """Raised when the spend cap is reached. The app shows 'demo paused'."""


_client = None


def is_mock() -> bool:
    return MOCK_LLM


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        cfg = PROVIDERS[PROVIDER]
        key = os.getenv(cfg["api_key_env"])
        if not key:
            raise RuntimeError(
                f"{cfg['api_key_env']} is not set. Add it to .env or set MOCK_LLM=true."
            )
        _client = OpenAI(base_url=cfg["base_url"], api_key=key)
    return _client


def budget_status() -> dict:
    spent = db.total_spend()
    return {
        "spent_usd": round(spent, 4),
        "warn_usd": BUDGET_WARN_USD,
        "cap_usd": BUDGET_HARD_CAP_USD,
        "warning": spent >= BUDGET_WARN_USD,
        "paused": spent >= BUDGET_HARD_CAP_USD,
        "mock": MOCK_LLM,
        "provider": PROVIDER,
    }


def chat(tier: str, messages: list[dict], **kwargs) -> str:
    """Call a model tier ('nano', 'super', 'ultra') and return the text."""
    if MOCK_LLM:
        raise RuntimeError("chat() called in mock mode; callers must check is_mock() first.")
    if db.total_spend() >= BUDGET_HARD_CAP_USD:
        raise BudgetExceeded("Budget cap reached; all model calls are off.")

    model = PROVIDERS[PROVIDER]["models"][tier]
    resp = _get_client().chat.completions.create(model=model, messages=messages, **kwargs)

    usage = resp.usage
    if usage is not None:
        p_in, p_out = PRICES[tier]
        cost = (usage.prompt_tokens * p_in + usage.completion_tokens * p_out) / 1_000_000
        db.record_spend(model, cost)
    return resp.choices[0].message.content or ""


def chat_json(tier: str, system: str, user: str, **kwargs) -> dict:
    """Ask for a JSON object and parse it robustly."""
    text = chat(
        tier,
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0,
        **kwargs,
    )
    # Reasoning models may wrap JSON in prose or code fences.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Model did not return JSON: {text[:200]}")
    return json.loads(match.group(0))
