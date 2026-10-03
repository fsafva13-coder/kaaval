# Kaaval കാവൽ
> A personal AI assistant that confirms and blocks fraudsters in any language mix, built on NVIDIA Nemotron and Nebius Token Factory.

![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Nemotron 3](https://img.shields.io/badge/NVIDIA-Nemotron%203-76B900) ![Nebius](https://img.shields.io/badge/Nebius-Token%20Factory-blue) ![Tavily](https://img.shields.io/badge/search-Tavily-orange) ![Track](https://img.shields.io/badge/track-Personal%20AI-purple)

## Overview
Personal AI agents now answer customers for small sellers, which makes the agent the new target for fraud. In the Gulf, messages mix Manglish, Arabizi and Hinglish, and English-tuned safety misses these code-mixed attacks. Kaaval runs a seller's customer chat, confirms fraud through a four-step trust ladder, and blocks only confirmed fraudsters, never on a single message. On our test set, adding Nemotron raised fraud blocked from 54% to 81% with 0 of 29 innocent conversations blocked.

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
[Screenshot: split screen, innocent customer vs fraudster]
[Screenshot: red Access ended screen]
[Screenshot: owner evidence alert in Malayalam]

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
Measured on a 55-conversation test set (26 fraud, 24 tricky innocent, 5 plain orders), run on Nebius Token Factory on 3 Oct 2026. Raw outputs are in `eval/results/`.

| Metric | Keyword rules only | Rules + Nemotron |
| --- | --- | --- |
| Fraud conversations blocked | 14 / 26 (54%) | **21 / 26 (81%)** |
| Innocent conversations blocked | 0 / 29 | **0 / 29** |
| Average messages before a block | 3.2 | 2.9 |

| Fraud type | Rules only | Rules + Nemotron |
| --- | --- | --- |
| English | 4 / 7 | 6 / 7 |
| Standard Manglish | 2 / 4 | 3 / 4 |
| Kannur-dialect Manglish | 2 / 5 | 4 / 5 |
| Arabizi | 0 / 3 | 2 / 3 |
| Hinglish | 2 / 3 | 2 / 3 |
| Malayalam script | 1 / 1 | 1 / 1 |
| Hidden instructions to the assistant | 3 / 3 | 3 / 3 |

The test set is small and written by the author, so these numbers show direction, not a benchmark. Reproduce with `python -m eval.run_eval`.

## Challenges & Learnings
[Placeholder: telling a customer asking for payment details apart from a fraudster; code-mixed text; tuning for zero false blocks]

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
