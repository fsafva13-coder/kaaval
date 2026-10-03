"""Every model call goes through this file.

Two safety features live here:
1. MOCK_LLM mode: no network calls at all, so you can build for free.
2. Budget guard: every real call is priced and logged; once the hard cap is
   reached, all calls are refused, so your card is never charged.
"""
import json
import os
import re
import time

from . import db
from .config import (
    BUDGET_HARD_CAP_USD,
    BUDGET_WARN_USD,
    MIN_CALL_INTERVAL,
    MOCK_LLM,
    PRICES,
    PROVIDER,
    PROVIDERS,
)


class BudgetExceeded(Exception):
    """Raised when the spend cap is reached. The app shows 'demo paused'."""


_client = None
_last_call = 0.0
calls_made = 0  # model calls in this process (the eval prints it)


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

    global _last_call, calls_made
    model = PROVIDERS[PROVIDER]["models"][tier]
    resp = None
    for attempt in range(4):
        wait = MIN_CALL_INTERVAL - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()
        try:
            resp = _get_client().chat.completions.create(model=model, messages=messages, **kwargs)
            calls_made += 1
            if not getattr(resp, "choices", None):
                # Some providers return an error object instead of raising.
                err = getattr(resp, "error", None) or "empty response"
                raise RuntimeError(f"429 or provider error from {model}: {err}")
            break
        except Exception as exc:  # rate limited: wait and retry
            if "429" in str(exc) and attempt < 3:
                time.sleep(15 * (attempt + 1))
                continue
            raise

    usage = resp.usage
    # Only Token Factory costs credits; NVIDIA's developer API is free.
    if usage is not None and PROVIDER == "nebius":
        p_in, p_out = PRICES[tier]
        cost = (usage.prompt_tokens * p_in + usage.completion_tokens * p_out) / 1_000_000
        db.record_spend(model, cost)
    msg = resp.choices[0].message
    text = msg.content or ""
    if not text.strip():
        # Reasoning models sometimes put everything in a separate reasoning field
        # (or run out of tokens while thinking). Use it rather than return nothing.
        extra = getattr(msg, "model_extra", None) or {}
        text = getattr(msg, "reasoning", None) or extra.get("reasoning") or extra.get("reasoning_content") or ""
    return text


def _extract_json(text: str) -> dict | None:
    """Return the last complete top-level JSON object in the text, if any.

    Reasoning models often wrap the answer in thinking text or code fences.
    """
    decoder = json.JSONDecoder()
    found, i = None, 0
    while (i := text.find("{", i)) != -1:
        try:
            obj, end = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            i += 1
            continue
        if isinstance(obj, dict):
            found = obj
        i = end
    return found


def chat_json(tier: str, system: str, user: str, **kwargs) -> dict:
    """Ask for a JSON object and parse it robustly (one retry if the reply has no JSON)."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text = ""
    for attempt in range(2):
        text = chat(tier, messages, temperature=0, **kwargs)
        found = _extract_json(text)
        if found is not None:
            return found
        messages.append({"role": "user", "content": "Reply with ONLY the JSON object, nothing else."})
    raise ValueError(f"Model did not return JSON: {text[:200]!r}")
