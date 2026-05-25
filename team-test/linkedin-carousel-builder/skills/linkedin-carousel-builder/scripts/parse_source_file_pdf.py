"""PDF parsing for parse_source_file.py."""
from pathlib import Path
from typing import Dict

from pypdf import PdfReader


def parse_pdf(path: Path) -> Dict:
    reader = PdfReader(str(path))
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    full_text = "\n\n".join(t.strip() for t in pages_text if t.strip())

    lines = full_text.splitlines()
    title = ""
    body_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if not title and len(stripped) < 120 and (i < 3 or not body_lines):
            title = stripped
            continue
        body_lines.append(stripped)
    return {"title": title, "body": "\n".join(body_lines)}
