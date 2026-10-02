"""Fast, free, rule-based screening.

Runs on every message before any model call. In MOCK_LLM mode it is the only
screener; in live mode Nemotron Nano runs after it and the stricter verdict
wins. Patterns cover English, Manglish, Arabizi and Hinglish.
"""
import re

# What a fraudster wants from the OWNER.
CREDENTIAL = re.compile(
    r"\b(otp|one[\s-]?time[\s-]?(password|code|pin)|pin\s*(number|code|no)?|cvv|cvc|"
    r"pass\s?word|passwd|passcode|card\s*(number|no|details|num)|"
    r"net\s?banking|bank\s*login|verification\s*code|sms\s*code)\b",
    re.I,
)
IDENTITY = re.compile(
    r"\b(emirates\s*id|eid\s*(no|number|copy)|passport|visa\s*copy|aadhaa?r|"
    r"date\s*of\s*birth|mother'?s\s*maiden)\b",
    re.I,
)
REDIRECT = re.compile(
    r"\b((new|other|different|another|updated|changed)\s+(bank\s+)?(account|iban|acc)|"
    r"(pay|transfer|send)\s+(it\s+|the\s+payment\s+|money\s+)?(to|into)\s+(this|my\s+new|another)\s+(account|iban|acc)|"
    r"change\s+(the\s+)?(bank|account|iban))\b",
    re.I,
)
INJECTION = re.compile(
    r"(ignore\s+(all\s+|any\s+)?(previous|prior|above|earlier)\s+(instructions|rules)|"
    r"you\s+are\s+now|system\s+prompt|developer\s+mode|"
    r"\bassistant[\s,:-]+(please\s+)?(send|share|forward|give|tell|reveal|ayakku|parayu|bhejo)|"
    r"owner'?s\s+(bank|otp|card|password|details|number|account)|"
    r"assistant-?(nodu|ode)\s+parayu)",
    re.I,
)

# Signs the request is aimed at the owner's secrets (Manglish/Arabizi/Hinglish).
YOUR = re.compile(r"\b(your|ur|ninte|ningalude|ninde|apna|apni|aapka|aapki|tumhara|ta3ak|taba3ak)\b", re.I)
GIVE = re.compile(
    r"\b(send|share|give|tell|forward|provide|ayakku|ayachu|tharu|thaa|tha|para|parayu|"
    r"bhejo|batao|dedo|3tini|a3tini|ersel|ersil|ib3at|sent|snd|sned|giv|gimme|plz|pls)\b",
    re.I,
)

# Innocent: a customer talking about THEIR OWN code ("my OTP isn't coming").
OWN_CREDENTIAL = re.compile(
    r"\b(my|ente|mera|meri|mine)\s+(otp|pin|cvv|card|password|passcode)|"
    r"\botp\s+(is\s*n.?t|not|illa|varunnilla|vannilla|didn.?t)|"
    r"(didn.?t|did\s+not|haven.?t|not)\s+(get|got|receive|received)\s+(the\s+|an?\s+|my\s+)?otp|"
    r"\bi\s+(got|received|have)\s+(the\s+|an?\s+)?otp",
    re.I,
)

# Innocent: a customer asking how to pay the seller.
BENIGN_PAY = re.compile(
    r"(so\s+(that\s+)?i\s+can\s+pay|to\s+pay\s+(you|for)|for\s+(the\s+)?payment|"
    r"how\s+(do|can|should)\s+i\s+pay|where\s+(do|should|can)\s+i\s+(pay|send\s+the\s+(money|payment))|"
    r"payment\s+(link|method|options?)|pay\s+(by|via|through)\s+(card|link|transfer|cash))",
    re.I,
)

URGENCY = re.compile(
    r"\b(urgent|urgently|immediately|right\s+now|asap|within\s+\d+\s*(min|mins|minutes|hour|hours)|"
    r"jaldi|vegam|pettannu|bsur3a|last\s+chance)\b",
    re.I,
)
IMPERSONATION = re.compile(
    r"\b(bank|police|courier|dhl|aramex|fedex|emirates\s*post|customs|etisalat|\bdu\b|"
    r"ministry|government|mohre|icp|tax\s+office|instagram\s+(support|team)|meta\s+(support|team))\b",
    re.I,
)
THREAT = re.compile(
    r"\b(legal\s+action|arrest|fine|penalty|court|case\s+will\s+be\s+filed|or\s+else|"
    r"will\s+be\s+(blocked|suspended|closed|frozen|cancelled))\b",
    re.I,
)

MANGLISH = re.compile(
    r"\b(ninte|ente|ante|alle|aano|aanu|aan|venam|venu|venda|parayu|para|tharu|thaa|ayakku|ayakk|ayakko|"
    r"chetta|chechi|bro\s+ithu|enthu|entha|vegam|illenkil|ellenkil|ningalude|ningalde|njan|und|ind|"
    r"cheyyan|cheyth|cheythu|pattumo|engane|enganeya|ippo|oru)\b",
    re.I,
)
HINGLISH = re.compile(r"\b(bhai|kya|hai|nahi|jaldi|bhejo|batao|apna|karo|kar\s+do)\b", re.I)
ARABIZI = re.compile(r"\b(habibi|yalla|inshallah|wallah|3|7|5ali|ana|enta|enti)\b|[a-z]+[3792][a-z]+", re.I)


def detect_language(text: str) -> str:
    if re.search(r"[ഀ-ൿ]", text):
        return "malayalam"
    if re.search(r"[؀-ۿ]", text):
        return "arabic"
    if MANGLISH.search(text):
        return "manglish"
    if ARABIZI.search(text):
        return "arabizi"
    if HINGLISH.search(text):
        return "hinglish"
    return "english"


def screen(text: str) -> dict:
    """Return a screening verdict for one message."""
    categories: list[str] = []
    span = None

    def hit(rx: re.Pattern, name: str) -> None:
        nonlocal span
        m = rx.search(text)
        if m:
            categories.append(name)
            span = span or m.group(0)

    hit(INJECTION, "injection")
    hit(REDIRECT, "payment_redirect")

    # A shop never needs a customer to mention the owner's OTP/PIN/CVV/password,
    # so any such mention counts, unless it is clearly about the customer's own.
    if not OWN_CREDENTIAL.search(text):
        hit(CREDENTIAL, "credential")
    # Identity documents only count when asked FROM the owner
    # ("do you need my passport?" is innocent).
    if YOUR.search(text) or GIVE.search(text):
        hit(IDENTITY, "identity")

    # A customer asking how to pay is innocent unless they also ask for secrets.
    benign_payment = bool(BENIGN_PAY.search(text)) and not (
        {"credential", "identity", "injection"} & set(categories)
    )
    if benign_payment and categories == ["payment_redirect"]:
        categories = []
        span = None

    tactics = []
    if URGENCY.search(text):
        tactics.append("urgency")
    if IMPERSONATION.search(text):
        tactics.append("impersonation")
    if THREAT.search(text):
        tactics.append("threat")

    sensitive = bool(categories)
    risk = 0.0
    if sensitive:
        risk = 0.6 + 0.1 * len(tactics) + (0.2 if "injection" in categories else 0)
    return {
        "sensitive": sensitive,
        "categories": categories,
        "tactics": tactics if sensitive else [],
        "pressure": tactics,  # urgency/impersonation/threat even without an explicit ask
        "span": span,
        "language": detect_language(text),
        "risk": round(min(risk, 1.0), 2),
        "benign_payment": benign_payment,
        "source": "rules",
    }
