"""Shared redaction helpers for local ADX Harness state."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",
    re.IGNORECASE | re.DOTALL,
)

SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?i)\b(authorization\s*:\s*bearer\s+)[A-Za-z0-9._~+/=-]{8,}"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"\b(?:sk|rk|pk)-[A-Za-z0-9_-]{16,}\b"),
        "[REDACTED_TOKEN]",
    ),
    (
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        "[REDACTED_GITHUB_TOKEN]",
    ),
    (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "[REDACTED_AWS_KEY]",
    ),
    (
        re.compile(
            r"""(?ix)
            (
              ["']?
              (?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|
                 password|passwd|client[_-]?secret|secret|cookie)
              ["']?\s*[:=]\s*
            )
            (["']?)
            [^\s,;]+
            """
        ),
        r"\1\2[REDACTED]",
    ),
)

SENSITIVE_QUERY_RE = re.compile(
    r"""(?ix)
    (
      [?&]
      (?:
        access[_-]?token|refresh[_-]?token|id[_-]?token|token|
        x-amz-signature|x-amz-credential|x-goog-signature|
        signature|sig|credential|googleaccessid|
        key(?:[_-]?pair)?[_-]?id|api[_-]?key
      )
      =
    )
    [^&#\s]+
    """
)

EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    r"(?![A-Za-z0-9._%+-])"
)

KOREAN_MOBILE_RE = re.compile(
    r"(?<!\d)(?:(?:\+?82)[- .]?)?0?10[- .]?\d{3,4}[- .]?\d{4}(?!\d)"
)

KOREAN_PHONE_RE = re.compile(
    r"(?<!\d)0(?:2|[3-6]\d)[- .]?\d{3,4}[- .]?\d{4}(?!\d)"
)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    value = ANSI_RE.sub("", value)
    value = CONTROL_RE.sub("", value)
    value = PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", value)
    value = SENSITIVE_QUERY_RE.sub(r"\1[REDACTED]", value)
    for pattern, replacement in SECRET_PATTERNS:
        value = pattern.sub(replacement, value)
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    value = KOREAN_MOBILE_RE.sub("010-****-****", value)
    value = KOREAN_PHONE_RE.sub("[REDACTED_PHONE]", value)
    return value.strip()


def web_url_for_log(value: Any) -> str:
    url = str(value or "")
    try:
        parts = urlsplit(url)
    except ValueError:
        return url.split("?", 1)[0].split("#", 1)[0]
    if parts.scheme not in {"http", "https"}:
        return url.split("?", 1)[0].split("#", 1)[0]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
