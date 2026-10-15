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

from backend import assistant, db, llm  # noqa: E402
from backend.main import app  # noqa: E402

client = TestClient(app)
ROOT = Path(__file__).parent


def run_conversation(path: Path) -> dict:
    """Replay one conversation. Returns what happened to it."""
    sid, did = f"eval-{uuid.uuid4().hex[:8]}", f"dev-{uuid.uuid4().hex[:8]}"
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    blocked, sent, refused = False, 0, 0
    for text in lines:
        sent += 1
        r = client.post("/api/chat", json={"sender_id": sid, "device_id": did, "text": text})
        if r.status_code == 403:
            blocked = True
            break
        if r.json().get("reply") == assistant.REFUSAL:
            refused += 1
    return {"name": path.name, "blocked": blocked, "sent": sent, "refused": refused, "total": len(lines), "sid": sid}


def explain(result: dict) -> None:
    """Print what the screener decided for each message of one conversation."""
    for m in db.history(result["sid"], limit=50):
        if m["role"] != "user":
            continue
        sc = m.get("screen") or {}
        flag = "FLAG" if sc.get("sensitive") else " ok "
        why = ", ".join(sc.get("categories", [])) or "-"
        print(f"      {flag} [{sc.get('source', '?')}: {why}] {m['text'][:90]}")


def main() -> int:
    results, errors = {}, []
    wanted = [a for a in sys.argv[1:] if a in ("fraud", "innocent", "orders")] or ["fraud", "innocent", "orders"]
    for group in ["fraud", "innocent", "orders"]:
        files = sorted((ROOT / group).glob("*.txt")) if group in wanted else []
        results[group] = []
        for i, f in enumerate(files, 1):
            try:
                res = run_conversation(f)
            except Exception as exc:
                print(f"  [{group} {i}/{len(files)}] ERROR    {f.name}: {str(exc)[:120]}", flush=True)
                errors.append(f.name)
                continue
            status = "BLOCKED " if res["blocked"] else ("refused " if res["refused"] else "served  ")
            print(f"  [{group} {i}/{len(files)}] {status} {f.name}", flush=True)
            results[group].append(res)

    fraud = results["fraud"]
    blocked = [r for r in fraud if r["blocked"]]
    innocent = [r for g in ["innocent", "orders"] for r in results[g]]
    wrongly_blocked = [r for r in innocent if r["blocked"]]
    wrongly_refused = [r for r in innocent if r["refused"] and not r["blocked"]]

    mode = "rules only (mock)" if llm.is_mock() else f"rules + Nemotron via {llm.PROVIDER}"
    print("\nKaaval evaluation")
    print(f"Mode: {mode}   Groups: {', '.join(wanted)}   Model calls: {llm.calls_made}")
    print("-" * 40)
    if fraud:
        print(f"Fraud conversations blocked:    {len(blocked)}/{len(fraud)} ({100 * len(blocked) / len(fraud):.0f}%)")
    if blocked:
        print(f"Avg messages before block:      {sum(r['sent'] for r in blocked) / len(blocked):.1f}")
    if innocent:
        msgs = sum(r["total"] for r in innocent)
        refused_msgs = sum(r["refused"] for r in innocent)
        print(f"Innocent conversations blocked: {len(wrongly_blocked)}/{len(innocent)}  (target: 0)")
        print(f"Innocent messages refused:      {refused_msgs}/{msgs}  (target: 0)")
    else:
        print("Innocent conversations: not run in this pass")
    if errors:
        print(f"Conversations that errored (not counted): {len(errors)}")

    def lang(name: str) -> str:
        for key in ["kannur", "injection", "manglish", "malayalam", "arabizi", "hinglish"]:
            if key in name:
                return key
        return "english"

    if fraud:
        by_lang: dict[str, list[bool]] = {}
        for r in fraud:
            by_lang.setdefault(lang(r["name"]), []).append(r["blocked"])
        print("Catch rate by type:")
        for key, vals in sorted(by_lang.items()):
            print(f"  {key:<10} {sum(vals)}/{len(vals)}")

    # Explain every failure, message by message.
    for title, group in [("MISSED fraud", [r for r in fraud if not r["blocked"]]),
                         ("WRONGLY BLOCKED", wrongly_blocked), ("WRONGLY REFUSED", wrongly_refused)]:
        for r in group:
            print(f"\n  {title}: {r['name']}")
            explain(r)
    if not llm.is_mock():
        print(f"\nTotal spent so far (all runs): ${db.total_spend():.4f}")
    return 1 if wrongly_blocked else 0


if __name__ == "__main__":
    sys.exit(main())
