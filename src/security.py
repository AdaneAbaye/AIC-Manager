"""
Shared input sanitization and safe error redaction for API and apps.
"""

from __future__ import annotations

import re

MAX_THESIS_LENGTH = 500
MAX_INVESTOR_NAME_LENGTH = 50

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|all)\s+instructions",
    r"disregard\s+(previous|prior|all)",
    r"forget\s+(everything|all|previous)",
    r"override\s+(system|instructions)",
    r"you\s+are\s+now",
    r"new\s+instructions",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"\[INST\]",
    r"<\|im_start\|>",
    r"ignore\s+(budget|monthly\s+budget)",
    r"disregard\s+(budget|allocation)",
    r"exceed\s+(the\s+)?budget",
    r"allocate\s+more\s+than",
    r"override\s+(budget|allocation)",
    r"no\s+budget\s+limit",
    r"unlimited\s+budget",
    r"forget\s+(the\s+)?budget",
]
INJECTION_REGEX = re.compile("|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE)

# Remove NULLs and most C0 control characters (keep newline/tab for thesis if needed — strip all for API)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_control_chars(text: str) -> str:
    return _CONTROL_CHARS_RE.sub("", text)


def sanitize_thesis(thesis: str) -> str:
    """Limit length, strip controls, redact basic prompt-injection phrases."""
    if not thesis or not isinstance(thesis, str):
        return ""
    thesis = strip_control_chars(thesis).strip()[:MAX_THESIS_LENGTH]
    if INJECTION_REGEX.search(thesis):
        thesis = INJECTION_REGEX.sub("[removed]", thesis)
    return thesis


def sanitize_investor_name(name: str) -> str:
    """Safe display name for agents: no controls, bounded length."""
    if not name or not isinstance(name, str):
        return "Investor"
    name = strip_control_chars(name).strip()
    if not name:
        return "Investor"
    if INJECTION_REGEX.search(name):
        name = INJECTION_REGEX.sub("[removed]", name)
    return name[:MAX_INVESTOR_NAME_LENGTH]


def redact_secrets(message: str) -> str:
    """Redact API keys and tokens from log output, HTTP responses, and user-visible errors."""
    if not message:
        return message
    msg = str(message)
    msg = re.sub(r"sk-[a-zA-Z0-9\-_]{20,}", "sk-[REDACTED]", msg)
    msg = re.sub(r"tvly-[a-zA-Z0-9\-_.]{16,}", "tvly-[REDACTED]", msg)
    msg = re.sub(r"Bearer\s+[a-zA-Z0-9\-_\.]+", "Bearer [REDACTED]", msg, flags=re.IGNORECASE)
    msg = re.sub(r"api_key=['\"]?[^'\"]+['\"]?", "api_key=[REDACTED]", msg, flags=re.IGNORECASE)
    return msg
