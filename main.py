from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from document_readers import SUPPORTED_EXTS, extract_text
from cleaners import safe_preview


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def iter_docs(input_dir: Path):
    for p in input_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            yield p


def write_jsonl_line(f, record: dict):
    f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def run(input_dir: str, output_dir: str):
    in_dir = Path(input_dir)
    if not in_dir.exists():
        raise FileNotFoundError(f"Input não existe: {in_dir}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = out_dir / f"documents_{timestamp}.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for file in iter_docs(in_dir):
            rec = {
                "file_name": file.name,
                "file_path": str(file),
                "file_ext": file.suffix.lower(),
                "file_size_bytes": file.stat().st_size,
                "file_hash": sha256_file(file),
                "extracted_at": now,
                "extract_status": "SUCCESS",
                "extract_error": None,
                "extract_engine": None,
                "raw_text": None,
                "text_preview": None,
            }

            try:
                text, engine = extract_text(file)
                rec["raw_text"] = text
                rec["text_preview"] = safe_preview(text, 400)
                rec["extract_engine"] = engine
                rec["extract_status"] = "EMPTY" if not text else "SUCCESS"
            except Exception as e:
                rec["extract_status"] = "FAILED"
                rec["extract_error"] = repr(e)

            write_jsonl_line(f, rec)
            count += 1

    print(f"OK: {count} arquivos processados")
    print(f"Saída: {out_path}")
    return out_path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Pasta de entrada com documentos misturados")
    p.add_argument("--output", required=True, help="Pasta de saída")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    run(a.input, a.output)
