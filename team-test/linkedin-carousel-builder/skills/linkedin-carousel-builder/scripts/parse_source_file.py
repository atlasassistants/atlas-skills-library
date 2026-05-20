#!/usr/bin/env python3
"""Parse a local source file into a brief structure."""
import json
import sys
from pathlib import Path
from typing import Dict

SUPPORTED_EXTENSIONS = {".md", ".txt", ".docx", ".pdf"}


def _parse_markdown(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = ""
    body_lines = []
    for line in lines:
        if not title and line.startswith("# "):
            title = line.lstrip("# ").strip()
            continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip()
    return {"title": title, "body": body}


def _parse_txt(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    title = lines[0].strip() if lines else ""
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else text
    return {"title": title, "body": body}


def parse(path_str: str) -> Dict:
    path = Path(path_str).resolve()
    if not path.exists():
        return {"ok": False, "error": f"File does not exist: {path}"}
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {"ok": False, "error": f"Unsupported extension: {ext}. Supported: {sorted(SUPPORTED_EXTENSIONS)}"}
    try:
        if ext == ".md":
            parsed = _parse_markdown(path)
        elif ext == ".txt":
            parsed = _parse_txt(path)
        elif ext == ".docx":
            from parse_source_file_docx import parse_docx
            parsed = parse_docx(path)
        elif ext == ".pdf":
            from parse_source_file_pdf import parse_pdf
            parsed = parse_pdf(path)
    except Exception as exc:
        return {"ok": False, "error": f"Parse error: {exc}"}
    if not parsed.get("body", "").strip():
        return {"ok": False, "error": "File parsed but body is empty."}
    return {"ok": True, "source_path": str(path), "author": "", **parsed}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: parse_source_file.py <path>"}))
        sys.exit(2)
    result = parse(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
