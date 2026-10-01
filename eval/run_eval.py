"""Replay every test conversation and report Kaaval's headline numbers.

Each .txt file is one conversation (one customer message per line).
  eval/fraud/     -> should end BLOCKED
  eval/innocent/  -> must NEVER be blocked
  eval/orders/    -> must NEVER be blocked

Run from the project root:   python -m eval.run_eval
Uses whatever mode .env sets (MOCK_LLM=true is free).
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("KAAVAL_DB", os.path.join(tempfile.mkdtemp(), "eval.db"))
os.environ["DAILY_MESSAGE_LIMIT"] = "100000"

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

client = TestClient(app)
ROOT = Path(__file__).parent


def run_conversation(path: Path) -> tuple[bool, int]:
    """Return (was_blocked, messages_until_block)."""
    sid, did = f"eval-{uuid.uuid4().hex[:8]}", f"dev-{uuid.uuid4().hex[:8]}"
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    for i, text in enumerate(lines, 1):
        r = client.post("/api/chat", json={"sender_id": sid, "device_id": did, "text": text})
        if r.status_code == 403:
            return True, i
    return False, len(lines)


def main() -> int:
    results = {}
    for group in ["fraud", "innocent", "orders"]:
        files = sorted((ROOT / group).glob("*.txt"))
        results[group] = [(f.name, *run_conversation(f)) for f in files]

    fraud = results["fraud"]
    blocked = [r for r in fraud if r[1]]
    wrongly = [r for g in ["innocent", "orders"] for r in results[g] if r[1]]

    print("\nKaaval evaluation")
    print("-" * 40)
    if fraud:
        print(f"Fraud conversations blocked:    {len(blocked)}/{len(fraud)} ({100 * len(blocked) / len(fraud):.0f}%)")
    if blocked:
        print(f"Avg messages before block:      {sum(r[2] for r in blocked) / len(blocked):.1f}")
    print(f"Innocent conversations blocked: {len(wrongly)}  (target: 0)")
    for name, _, _ in [r for r in fraud if not r[1]]:
        print(f"  MISSED fraud: {name}")
    for name, _, _ in wrongly:
        print(f"  WRONGLY BLOCKED: {name}")
    return 1 if wrongly else 0


if __name__ == "__main__":
    sys.exit(main())
