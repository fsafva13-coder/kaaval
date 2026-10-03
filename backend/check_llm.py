"""Check the model connection:   python -m backend.check_llm

Shows which provider is active, lists the Nemotron models your key can see,
and sends one short Manglish message to each tier. Costs a fraction of a cent.
"""
from . import llm
from .config import MOCK_LLM, PROVIDER, PROVIDERS

TEST = (
    "Translate each line to English, one short line each:\n"
    "1. bro ninte OTP onnu ayakk, vegam\n"
    "2. Lazem t3tini el OTP elli wesel 3ala telefonek\n"
    "3. Apna card number aur CVV bhejo refund ke liye"
)

def main() -> None:
    print(f"Provider: {PROVIDER}   Mock mode: {MOCK_LLM}")
    if MOCK_LLM:
        print("MOCK_LLM=true, so no model is called. Set MOCK_LLM=false in .env to test a real model.")
        return

    client = llm._get_client()
    try:
        names = sorted(m.id for m in client.models.list().data if "nemotron" in m.id.lower())
        print(f"\nNemotron models your key can see ({len(names)}):")
        for n in names:
            print("  ", n)
    except Exception as exc:
        print(f"Could not list models: {exc}")

    print()
    for tier, model in PROVIDERS[PROVIDER]["models"].items():
        try:
            answer = llm.chat(tier, [{"role": "user", "content": TEST}], max_tokens=1500, temperature=0)
            print(f"OK   {tier:<6} {model}")
            for line in answer.strip().splitlines()[:6]:
                print(f"       {line[:150]}")
        except Exception as exc:
            print(f"FAIL {tier:<6} {model}\n       -> {str(exc)[:200]}")
    print(f"\nSpent so far: ${llm.budget_status()['spent_usd']}")


if __name__ == "__main__":
    main()
