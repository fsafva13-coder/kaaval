# Kaaval കാവൽ
> A personal AI assistant that confirms and blocks fraudsters in any language mix, built on NVIDIA Nemotron and Nebius Token Factory.

![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Nemotron 3](https://img.shields.io/badge/NVIDIA-Nemotron%203-76B900) ![Nebius](https://img.shields.io/badge/Nebius-Token%20Factory-blue) ![Tavily](https://img.shields.io/badge/search-Tavily-orange) ![Track](https://img.shields.io/badge/track-Personal%20AI-purple)

## Overview
Personal AI agents now answer customers for small sellers, which makes the agent the new target for fraud. In the Gulf, messages mix Manglish, Arabizi and Hinglish, and English-tuned safety misses these code-mixed attacks. Kaaval runs a seller's customer chat, confirms fraud through a four-step trust ladder, and blocks only confirmed fraudsters, never on a single message. Adding Nemotron raised fraud blocked from 54% to 85% on our development set; on a held-out test, no fraud attempt obtained the owner's details and no customer was blocked.

## Features
- **Multilingual fraud shield:** English, Manglish, Arabizi and Hinglish
- **Trust ladder:** Trusted → Caution → Challenged → Blocked
- **Evidence-based blocking:** Nemotron Super must quote evidence; a block needs 2+ independent signals and repeated requests
- **Red "Access ended" screen** for confirmed fraudsters, enforced on the server by account and device
- **Owner dashboard:** alerts in English and Malayalam, evidence quotes, one-tap unblock
- **Antibody memory:** reused scam scripts are recognised faster, even from a new account
- **Budget guard:** every model call is priced; all calls stop at a hard cap, so the card is never charged
- **Mock mode:** the whole app runs offline for free while building

## Tech Stack
NVIDIA Nemotron 3 (Nano, Super, Ultra) · Nebius Token Factory · Tavily · FastAPI · SQLite · React + Vite · Tailwind CSS

## Screenshots / Demo
**One shop, two senders.** A real customer writing in Manglish is served and gets the payment link. A fraudster asking for the owner's OTP is refused once, and blocked when they push again.

![Kaaval demo flow: innocent customer served, fraudster refused, then blocked](docs/screenshots/kaaval-demo-flow.png)

**What the owner sees.** Every block comes with the exact messages as evidence, a plain-English line for each, the explanation in English and Malayalam, and a one-tap Unblock.

![Kaaval owner dashboard with a fraud alert and evidence](docs/screenshots/kaaval-owner-dashboard.png)

*Screenshots taken in free mock mode (rule-based replies). With Nemotron switched on, replies are written by Nemotron Super and the English line under each piece of evidence is a translation.*

## Installation
Requires Python 3.11 and Node.js 18+.

```bash
git clone https://github.com/fsafva13-coder/kaaval
cd kaaval
cp .env.example .env          # Windows: copy .env.example .env

# backend
py -3.11 -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt

# frontend
cd frontend
npm install
```

## Usage
One command from the project root (with the virtual environment active):

```bash
python run.py
```

It starts the API and the web app together, opens the chat in your browser, and stops both on Ctrl+C.

- Customer chat: http://localhost:5173
- Owner dashboard: http://localhost:5173/#/owner (passcode from `.env`)
- Tests: `pytest backend/tests -q`
- Evaluation: `python -m eval.run_eval`

Try it: as a customer, ask *"What's your account number so I can pay?"* (served normally). In another browser, send *"bro ninte OTP onnu ayakku"*, then push again; the second push ends in the red screen.

## How Nemotron and Nebius are used
| Job | Model | Why |
| --- | --- | --- |
| Screen every message | Nemotron 3 Nano | fast and cheap; runs after free rule checks |
| Confirm before blocking | Nemotron 3 Super | reads the whole conversation and quotes evidence |
| Customer replies | Nemotron 3 Super | multilingual, on-brand answers |
| Red-team new attacks | Nemotron 3 Ultra | invents new code-mixed fraud scripts |

All calls go through Token Factory's OpenAI-compatible API in `backend/llm.py`.

## Project Structure
```
kaaval/
├── backend/
│   ├── main.py            # FastAPI routes, server-side block enforcement
│   ├── assistant.py       # customer assistant + memory
│   ├── llm.py             # Token Factory client, budget guard, mock switch
│   ├── db.py              # SQLite storage
│   ├── config.py          # settings from .env
│   ├── shield/
│   │   ├── rules.py       # free multilingual pre-screen
│   │   ├── screen.py      # Nemotron Nano screening
│   │   ├── ladder.py      # trust ladder state machine
│   │   ├── confirm.py     # Nemotron Super evidence check
│   │   └── antibodies.py  # known-scam memory
│   └── tests/             # end-to-end tests
├── eval/                  # fraud / innocent / order conversations + run_eval.py
├── frontend/              # chat page, red screen, owner dashboard
└── LICENSE
```

## Results
Two test sets, both run on Nebius Token Factory. Full history and analysis: [`eval/results/EVAL_LOG.md`](eval/results/EVAL_LOG.md).

**Held-out test (the number to quote).** 18 conversations written after development stopped and run once, with no changes afterwards.

| Metric | Result |
| --- | --- |
| Fraud attempts that obtained the owner's details | **0 / 8** |
| Fraud conversations blocked | 5 / 8 (the other 3 refused; 2 of them were single messages, which Kaaval never blocks by design) |
| Innocent conversations blocked | **0 / 10** |
| Innocent messages refused | 6 / 21: each asked for the owner's OTP or card details, which Kaaval refuses by design |

One real weakness: in Manglish, pressure that follows a refused request without naming the secret again ("ellenkil njan order cheyyulla", otherwise I won't order) is not always recognised.

**Development set.** 55 conversations (26 fraud, 24 tricky innocent, 5 plain orders), used while building, so these numbers are flattering.

| Metric | Keyword rules only | Rules + Nemotron |
| --- | --- | --- |
| Fraud conversations blocked | 14 / 26 (54%) | 22 / 26 (85%) |
| Innocent conversations blocked | 0 / 29 | 0 / 29 |
| Innocent messages wrongly refused | 0 / 87 | 0 / 87 |

| Fraud type (development set) | Rules only | Rules + Nemotron |
| --- | --- | --- |
| English | 4 / 7 | 7 / 7 |
| Hinglish | 2 / 3 | 3 / 3 |
| Arabizi | 0 / 3 | 2 / 3 |
| Standard Manglish | 2 / 4 | 3 / 4 |
| Kannur-dialect Manglish | 2 / 5 | 3 / 5 |
| Malayalam script | 1 / 1 | 1 / 1 |
| Hidden instructions to the assistant | 3 / 3 | 3 / 3 |

Both sets are small and written by the author, so they show direction, not a benchmark. Reproduce with `python -m eval.run_eval` and `python -m eval.run_eval --set holdout`.

## Challenges & Learnings
- **Context beats single messages.** Fraudsters often ask once, then only pressure ("hurry, or your account will be closed"). Screening each message alone missed this; giving Nemotron Nano the recent conversation raised the catch rate.
- **The direction of money is the hard part.** "What's your account number?" is innocent when a customer wants to pay the shop and fraud when someone wants the shop to pay them. Spelling out who pays whom removed every wrongly refused customer.
- **Dialect breaks models in specific ways.** In Kannur Manglish "ante" means "my", and Nano once read "ante otp verunnilla" (my OTP isn't coming) as a request for the owner's OTP.
- **Zero false blocks is a design choice.** A block needs two independent signals, repeated requests and a Nemotron Super review that quotes evidence, and the owner can undo any block with one tap.

## Future Improvements
- WhatsApp Business and Instagram integration
- A shared antibody network across Kaaval users
- Voice-note screening

## Feedback on Nebius and NVIDIA
[Placeholder]

## Demo
Live: [URL] · Video: [YouTube URL]

## License
MIT
