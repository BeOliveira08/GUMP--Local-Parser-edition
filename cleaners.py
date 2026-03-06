from __future__ import annotations

import re
import unicodedata

# Remove caracteres de controle (exceto \n, \r, \t)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

# Zero-width + BOM
_ZERO_WIDTH_RE = re.compile(r"[\u200B\u200C\u200D\u2060\uFEFF]")

# Quebras e espaços
_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
_MANY_NEWLINES_RE = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    if text is None:
        return ""

    # Normaliza unicode
    text = unicodedata.normalize("NFKC", text)

    # Remove BOM / zero-width
    text = _ZERO_WIDTH_RE.sub("", text)

    # Remove \0 e controles
    text = text.replace("\x00", "")
    text = _CONTROL_CHARS_RE.sub("", text)

    # Normaliza quebras de linha
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normaliza espaços
    text = _WHITESPACE_RE.sub(" ", text)

    # Limita excesso de linhas vazias
    text = _MANY_NEWLINES_RE.sub("\n\n", text)

    return text.strip()


def safe_preview(text: str, max_chars: int = 400) -> str:
    t = clean_text(text)
    return t[:max_chars]
