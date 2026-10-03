"""Central settings, loaded from the project-root .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# --- Model provider -------------------------------------------------------
# MOCK_LLM=true  -> no API calls at all (free, offline, rule-based answers)
# PROVIDER=nvidia -> NVIDIA's free developer API (build.nvidia.com), for early testing
# PROVIDER=nebius -> Nebius Token Factory (required for the final submission)
MOCK_LLM = _bool("MOCK_LLM", True)
PROVIDER = os.getenv("PROVIDER", "nebius").strip().lower()

PROVIDERS = {
    "nebius": {
        "base_url": "https://api.tokenfactory.nebius.com/v1/",
        "api_key_env": "NEBIUS_API_KEY",
        "models": {
            "nano": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
            "super": "nvidia/nemotron-3-super-120b-a12b",
            "ultra": "nvidia/Nemotron-3-Ultra-550b-a55b",
        },
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        # Free Nemotron models (about 20 requests/minute, 200/day). Nano has no free
        # version here, so the fast tier uses Nemotron 3.5 Lightning (also on Token Factory).
        "models": {
            "nano": os.getenv("OPENROUTER_NANO_MODEL", "nvidia/nemotron-3.5-lightning:free"),
            "super": os.getenv("OPENROUTER_SUPER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free"),
            "ultra": os.getenv("OPENROUTER_ULTRA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free"),
        },
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key_env": "NVIDIA_API_KEY",
        # Check build.nvidia.com for the exact IDs available to your account.
        "models": {
            "nano": os.getenv("NVIDIA_NANO_MODEL", "nvidia/nemotron-nano-3-30b-a3b"),
            "super": os.getenv("NVIDIA_SUPER_MODEL", "nvidia/nemotron-3-super-120b-a12b"),
            "ultra": os.getenv("NVIDIA_ULTRA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
        },
    },
}

# USD per 1M tokens (input, output), from the Token Factory model catalog.
PRICES = {
    "nano": (0.06, 0.24),
    "super": (0.30, 0.90),
    "ultra": (1.00, 3.00),
}

# Seconds to wait between calls, so free tiers are not rate-limited.
MIN_CALL_INTERVAL = {"openrouter": 3.2, "nvidia": 1.6, "nebius": 0.0}.get(PROVIDER, 0.0)

# true = customer replies come from the free rule-based assistant even in live
# mode, so only the fraud shield uses model calls (saves a daily request limit).
MOCK_REPLIES = _bool("MOCK_REPLIES", False)

# --- Budget guard ---------------------------------------------------------
BUDGET_HARD_CAP_USD = float(os.getenv("BUDGET_HARD_CAP_USD", "40"))
BUDGET_WARN_USD = float(os.getenv("BUDGET_WARN_USD", "30"))

# --- Demo protection ------------------------------------------------------
DAILY_MESSAGE_LIMIT = int(os.getenv("DAILY_MESSAGE_LIMIT", "30"))

# --- Storage --------------------------------------------------------------
DB_PATH = Path(os.getenv("KAAVAL_DB", ROOT / "kaaval.db"))

# --- Business persona -----------------------------------------------------
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "mirae.luxe_")
OWNER_PASSCODE = os.getenv("OWNER_PASSCODE", "change-me")
