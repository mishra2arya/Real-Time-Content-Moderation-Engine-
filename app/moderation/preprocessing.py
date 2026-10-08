"""Robust text preprocessing and normalization for real-time moderation."""

import html
import re
import unicodedata
from typing import Optional

# Zero-width spaces, directional marks, and invisible format characters
ZERO_WIDTH_PATTERN = re.compile(r"[\u200B-\u200D\uFEFF\u00AD\u2060\u200E\u200F]")

# Whitespace normalization
WHITESPACE_PATTERN = re.compile(r"\s+")

# URL pattern
URL_PATTERN = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_+.~#?&/=]*"
)

# HTML tags pattern
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

# Repeated characters (e.g. "sooooo baaaad" -> "soo baad", capping at 2)
REPEAT_PATTERN = re.compile(r"(.)\1{2,}", re.IGNORECASE)

# Common leetspeak substitutions used to bypass filters
LEET_MAP = {
    "@": "a",
    "4": "a",
    "8": "b",
    "3": "e",
    "1": "i",
    "!": "i",
    "0": "o",
    "$": "s",
    "5": "s",
    "7": "t",
    "+": "t",
}


def clean_text(
    text: Optional[str],
    max_length: int = 10000,
    normalize_leet: bool = False,
    preserve_case: bool = False,
) -> str:
    """Clean and normalize raw text for transformer tokenization.

    Args:
        text: Input string to be normalized.
        max_length: Maximum allowed characters before truncation.
        normalize_leet: Whether to apply aggressive leetspeak mapping.
        preserve_case: If True, preserves original casing; otherwise converts to lower.

    Returns:
        Sanitized, normalized UTF-8 string.
    """
    if text is None:
        return ""

    # Ensure string type
    if not isinstance(text, str):
        text = str(text)

    # 1. Payload size guard
    if len(text) > max_length:
        text = text[:max_length]

    # 2. Unicode normalization (NFKD normalizes accents, ligature decompositions)
    text = unicodedata.normalize("NFKD", text)

    # 3. Strip zero-width & invisible control characters
    text = ZERO_WIDTH_PATTERN.sub("", text)

    # 4. Strip HTML tags first, then unescape HTML entities (&amp; -> &, &lt; -> <)
    text = HTML_TAG_PATTERN.sub(" ", text)
    text = html.unescape(text)

    # 5. Collapse excessive character repetition (e.g. "baaaaad" -> "baad")
    text = REPEAT_PATTERN.sub(r"\1\1", text)

    # 6. Optional leetspeak replacement
    if normalize_leet:
        chars = [LEET_MAP.get(c, c) for c in text]
        text = "".join(chars)

    # 7. Collapse multiple whitespace & strip
    text = WHITESPACE_PATTERN.sub(" ", text).strip()

    # 8. Lowercase if required
    if not preserve_case:
        text = text.lower()

    return text
