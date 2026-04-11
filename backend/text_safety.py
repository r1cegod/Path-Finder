import re
import unicodedata


def _is_student_safe_char(ch: str) -> bool:
    if ch in "\n\r\t":
        return True
    category = unicodedata.category(ch)
    if category[0] in {"Z", "P", "N"}:
        return True
    if category.startswith("L"):
        return "LATIN" in unicodedata.name(ch, "")
    return False


def sanitize_student_stream_token(text: str) -> str:
    return "".join(ch if _is_student_safe_char(ch) else "" for ch in text)


def sanitize_student_reply(text: str) -> str:
    cleaned = "".join(ch if _is_student_safe_char(ch) else " " for ch in text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
