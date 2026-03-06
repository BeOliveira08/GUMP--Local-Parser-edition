from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Tuple

from cleaners import clean_text

SUPPORTED_EXTS = {".pdf", ".docx", ".txt", ".html", ".htm", ".eml", ".rtf", ".odt"}


def read_txt(path: Path) -> str:
    # tenta utf-8; se vier lixo, ignora
    return clean_text(path.read_text(encoding="utf-8", errors="ignore"))


def read_pdf_text(path: Path) -> str:
    import pdfplumber

    parts = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            t = clean_text(t)
            if t:
                parts.append(t)
    return clean_text("\n\n".join(parts))


def read_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts = []
    for p in doc.paragraphs:
        t = clean_text(p.text or "")
        if t:
            parts.append(t)
    return clean_text("\n".join(parts))


def read_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "html.parser")
        text = soup.get_text("\n")
        return clean_text(text)
    except Exception:
        # fallback sem bs4
        raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
        raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw)
        return clean_text(raw)


def read_eml(path: Path) -> str:
    import email
    from email import policy

    msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)

    parts = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    parts.append(part.get_content())
                except Exception:
                    pass
    else:
        try:
            parts.append(msg.get_content())
        except Exception:
            pass

    return clean_text("\n\n".join([p for p in parts if p]))


def read_rtf(path: Path) -> str:
    # Stripper simples mas funcional pra maioria dos RT
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
    raw = raw.replace("{", " ").replace("}", " ")
    raw = re.sub(r"\s+", " ", raw)
    return clean_text(raw)


def read_odt(path: Path) -> str:
    # ODT é zip. Pega content.xml e tira tags.
    with zipfile.ZipFile(str(path), "r") as z:
        xml = z.read("content.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"<[^>]+>", " ", xml)
    xml = re.sub(r"\s+", " ", xml)
    return clean_text(xml)


def extract_text(path: Path) -> Tuple[str, str]:
    ext = path.suffix.lower()

    if ext == ".pdf":
        return read_pdf_text(path), "pdfplumber"
    if ext == ".docx":
        return read_docx(path), "python-docx"
    if ext == ".txt":
        return read_txt(path), "text"
    if ext in (".html", ".htm"):
        return read_html(path), "html"
    if ext == ".eml":
        return read_eml(path), "eml"
    if ext == ".rtf":
        return read_rtf(path), "rtf"
    if ext == ".odt":
        return read_odt(path), "odt"

    raise ValueError(f"Extensão não suportada: {ext}")
