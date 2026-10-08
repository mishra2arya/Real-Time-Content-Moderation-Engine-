"""Unit tests for text preprocessing, sanitization, and normalization."""

from app.moderation.preprocessing import clean_text


def test_clean_text_normal():
    """Standard text should be normalized and lowercased."""
    raw = "Hello World! This is a test."
    cleaned = clean_text(raw)
    assert cleaned == "hello world! this is a test."


def test_clean_text_none_and_empty():
    """None and empty inputs should return empty string."""
    assert clean_text(None) == ""
    assert clean_text("") == ""
    assert clean_text("   \n\t  ") == ""


def test_clean_text_unicode_and_zero_width():
    """Zero-width spaces and invisible characters should be stripped."""
    # Contains zero-width space \u200B and non-breaking space
    raw = "h\u200be\u200bl\u200bl\u200bo\xa0world"
    cleaned = clean_text(raw)
    assert cleaned == "hello world"


def test_clean_text_html_entities_and_tags():
    """HTML tags should be stripped and HTML entities unescaped."""
    raw = "<p>You &amp; I should talk &lt;soon&gt;</p>"
    cleaned = clean_text(raw)
    assert cleaned == "you & i should talk <soon>"


def test_clean_text_repeated_characters():
    """Excessive repetitions (>2) should be collapsed to 2 characters."""
    raw = "haaaateeeeee yooouuuu"
    cleaned = clean_text(raw)
    assert cleaned == "haatee yoouu"


def test_clean_text_leetspeak():
    """Leetspeak normalization converts common obfuscations when enabled."""
    raw = "y0u @re 5tup1d"
    cleaned = clean_text(raw, normalize_leet=True)
    assert cleaned == "you are stupid"


def test_clean_text_max_length_truncation():
    """Extremely long text should be truncated to max_length."""
    huge_text = "ab " * 5000
    cleaned = clean_text(huge_text, max_length=500)
    assert len(cleaned) == 500


def test_clean_text_preserve_case():
    """Preserve case when flag is True."""
    raw = "Hello World"
    cleaned = clean_text(raw, preserve_case=True)
    assert cleaned == "Hello World"
