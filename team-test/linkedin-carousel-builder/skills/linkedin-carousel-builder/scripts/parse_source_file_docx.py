"""DOCX parsing for parse_source_file.py."""
from pathlib import Path
from typing import Dict

from docx import Document


def parse_docx(path: Path) -> Dict:
    doc = Document(str(path))
    title = ""
    body_paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if not title and para.style.name.lower().startswith("heading"):
            title = text
            continue
        body_paragraphs.append(text)
    return {"title": title, "body": "\n\n".join(body_paragraphs)}
