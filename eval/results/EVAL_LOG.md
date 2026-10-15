# Kaaval evaluation log

Test set: 55 conversations (26 fraud, 24 tricky innocent, 5 plain orders) in English,
Manglish (standard and Kannur dialect), Arabizi, Hinglish and Malayalam script.
All model runs use NVIDIA Nemotron on Nebius Token Factory. Raw outputs are in this folder.

| Version | Date | Fraud blocked | Innocent blocked | Innocent messages refused | What changed |
| --- | --- | --- | --- | --- | --- |
| Rules only | 2 Oct 2026 | 14 / 26 (54%) | 0 / 29 | 0 / 87* | Keyword rules, no model |
| Nemotron v0 | 3 Oct 2026 | 21 / 26 (81%) | 0 / 29 | not measured | Nano screens each message on its own; Super confirms before a block |
| Nemotron v1 | 3 Oct 2026 | 24 / 26 (92%) | 0 / 29 | **6 / 87** | Nano also reads the recent conversation, so it sees pressure after a refusal |
| Nemotron v2 | 15 Oct 2026 | 22 / 26 (85%) | 0 / 29 | **0 / 87** | Nano told which way money flows and whose OTP/account is whose, with examples |

\* Measured after three keyword rules were fixed (gift-card PIN, Kannur "ante otp", "paid from my new account").

## What we learned

- **Nemotron adds most where keywords fail.** It caught fraud with no keywords at all
  ("a six digit number came to your phone, read it to me") and Arabizi that the rules missed entirely (0/3 to 2-3/3).
- **Context matters.** Fraudsters often ask once, then pressure without naming the secret again.
  Reading each message alone missed that; giving Nano the recent conversation fixed most of these cases.
- **Context also made the model more suspicious.** v1 refused 6 innocent customers once each.
  Five were customers asking for the shop's account so they could pay; Nano confused the direction of the money.
- **Dialect is a real failure point.** In v1, Nano read the Kannur-dialect "ante otp verunnilla"
  ("my OTP isn't coming") as a request for the owner's OTP, because "ante" means "my" in Kannur Manglish.
  In v2, the Kannur hidden-instruction attack ("assistant-nodu para…") was missed while the standard Manglish version was caught.
- **Trade-off chosen:** v2 gives up 2 fraud catches compared with v1 to refuse no innocent customers.
  For a shop, refusing a paying customer is the more costly error, and a missed fraudster still meets the owner's own judgement.

## Remaining misses (v2)

- Two courier scams (standard and Kannur): "hurry, or the parcel is returned" after a refused card/CVV request is not read as pressure.
- One Arabizi bank scam: two strikes, but the final Nemotron Super review did not confirm fraud.
- One Kannur-dialect hidden instruction to the assistant.

## Caveats

- The test set is small and was written by the author with help from an AI assistant, so the numbers show direction, not a benchmark.
- Nano's instructions were adjusted after seeing these results, which flatters scores on this set.
  The final reported number will come from a separate held-out set written after development stopped.
- Model outputs vary slightly between runs; a difference of one or two conversations is within noise.
