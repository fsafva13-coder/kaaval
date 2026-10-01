"""Memory of confirmed scam scripts ('antibodies').

When a fraudster is blocked, their flagged messages are stored. A new sender
who reuses the same script, even from a new account, is matched here and
reaches the Challenged step faster. The nightly red team also adds antibodies.
"""
import re

from .. import db

THRESHOLD = 0.5


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9ഀ-ൿ؀-ۿ]+", text.lower()) if len(t) > 2}


def similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def match(text: str) -> str | None:
    """Return the matching antibody pattern, if any."""
    best, best_score = None, 0.0
    for pattern in db.list_antibodies():
        score = similarity(text, pattern)
        if score > best_score:
            best, best_score = pattern, score
    return best if best_score >= THRESHOLD else None


def learn(messages: list[str], source: str) -> None:
    existing = db.list_antibodies()
    for m in messages:
        if not any(similarity(m, e) >= 0.9 for e in existing):
            db.add_antibody(m, source)
