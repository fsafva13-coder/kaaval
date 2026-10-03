"""Replay every test conversation and report Kaaval's headline numbers.

Each .txt file is one conversation (one customer message per line).
  eval/fraud/     -> should end BLOCKED
  eval/innocent/  -> must NEVER be blocked
  eval/orders/    -> must NEVER be blocked

Run from the project root:   python -m eval.run_eval            (everything)
                              python -m eval.run_eval fraud      (one group)
Uses whatever mode .env sets (MOCK_LLM=true is free).
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("KAAVAL_DB", os.path.join(tempfile.mkdtemp(), "eval.db"))
os.environ["DAILY_MESSAGE_LIMIT"] = "100000"
os.environ.setdefault("MOCK_REPLIES", "true")  # test the shield, not the replies

from fastapi.testclient import TestClient  # noqa: E402

from backend import llm  # noqa: E402
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
    results, errors = {}, []
    wanted = [a for a in sys.argv[1:] if a in ("fraud", "innocent", "orders")] or ["fraud", "innocent", "orders"]
    for group in ["fraud", "innocent", "orders"]:
        files = sorted((ROOT / group).glob("*.txt")) if group in wanted else []
        results[group] = []
        for i, f in enumerate(files, 1):
            try:
                was_blocked, n = run_conversation(f)
            except Exception as exc:
                print(f"  [{group} {i}/{len(files)}] ERROR    {f.name}: {str(exc)[:120]}", flush=True)
                errors.append(f.name)
                continue
            print(f"  [{group} {i}/{len(files)}] {'BLOCKED ' if was_blocked else 'served  '} {f.name}", flush=True)
            results[group].append((f.name, was_blocked, n))

    fraud = results["fraud"]
    blocked = [r for r in fraud if r[1]]
    wrongly = [r for g in ["innocent", "orders"] for r in results[g] if r[1]]

    mode = "rules only (mock)" if llm.is_mock() else f"rules + Nemotron via {llm.PROVIDER}"
    print("\nKaaval evaluation")
    print(f"Mode: {mode}   Groups: {', '.join(wanted)}   Model calls: {llm.calls_made}")
    print("-" * 40)
    if fraud:
        print(f"Fraud conversations blocked:    {len(blocked)}/{len(fraud)} ({100 * len(blocked) / len(fraud):.0f}%)")
    if blocked:
        print(f"Avg messages before block:      {sum(r[2] for r in blocked) / len(blocked):.1f}")
    innocent_run = [r for g in ["innocent", "orders"] for r in results[g]]
    if innocent_run:
        print(f"Innocent conversations blocked: {len(wrongly)}/{len(innocent_run)}  (target: 0)")
    else:
        print("Innocent conversations: not run in this pass")
    if errors:
        print(f"Conversations that errored (not counted): {len(errors)}")
    def lang(name: str) -> str:
        for key in ["kannur", "injection", "manglish", "malayalam", "arabizi", "hinglish"]:
            if key in name:
                return key
        return "english"

    by_lang: dict[str, list[bool]] = {}
    for name, was_blocked, _ in fraud:
        by_lang.setdefault(lang(name), []).append(was_blocked)
    print("Catch rate by type:")
    for key, vals in sorted(by_lang.items()):
        print(f"  {key:<10} {sum(vals)}/{len(vals)}")
    for name, _, _ in [r for r in fraud if not r[1]]:
        print(f"  MISSED fraud: {name}")
    for name, _, _ in wrongly:
        print(f"  WRONGLY BLOCKED: {name}")
    return 1 if wrongly else 0


if __name__ == "__main__":
    sys.exit(main())
