#!/usr/bin/env python3
"""Build _index.json for the dev-projects Obsidian vault.

Scans Projects, Products, 03 - Concepts, and 01 - Raw Sources. Writes a single
JSON file at the vault root that the /my-world slash command queries via jq
instead of grepping the folders every run.

Stdlib only — no external deps. Minimal YAML frontmatter parser covers the
shapes actually used in this vault (scalar strings / bools, multi-line arrays,
inline flow arrays). Wikilinks are extracted from the body via regex.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path("/Users/andybarker/projects/obsidian/dev-projects")
OUTPUT = VAULT / "_index.json"
FOLDERS = ["Projects", "Products", "03 - Concepts", "01 - Raw Sources"]
SCHEMA_VERSION = 1

WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    body = text[3:end].strip("\n")
    out: dict = {}
    current_list: list | None = None
    for raw in body.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if current_list is not None and stripped.startswith("- "):
            current_list.append(stripped[2:].strip().strip("\"'"))
            continue
        current_list = None
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "":
            current_list = []
            out[key] = current_list
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            items = [i.strip().strip("\"'") for i in inner.split(",") if i.strip()]
            out[key] = items
        else:
            lower = val.lower()
            if lower in ("true", "false"):
                out[key] = lower == "true"
            else:
                out[key] = val.strip("\"'")
    return out


def extract_wikilinks(text: str) -> list[str]:
    targets: set[str] = set()
    for m in WIKILINK_RE.finditer(text):
        raw = m.group(1)
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            targets.add(target)
    return sorted(targets)


def wikilink_targets(values) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    out: list[str] = []
    for v in values:
        if not isinstance(v, str):
            continue
        m = WIKILINK_RE.search(v)
        if m:
            target = m.group(1).split("|", 1)[0].split("#", 1)[0].strip()
            if target:
                out.append(target)
        else:
            trimmed = v.strip()
            if trimmed:
                out.append(trimmed)
    return out


def main() -> int:
    if not VAULT.is_dir():
        print(f"vault not found: {VAULT}", file=sys.stderr)
        return 1

    notes = []
    for folder in FOLDERS:
        root = VAULT / folder
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = parse_frontmatter(text)
            rec = {
                "file": str(path.relative_to(VAULT)),
                "folder": folder,
                "title": path.stem,
                "tags": fm.get("tags") or [],
                "wikilinks": extract_wikilinks(text),
            }
            if folder == "Projects":
                rec["repo"] = fm.get("repo") or ""
                rec["depends_on"] = wikilink_targets(fm.get("depends-on"))
                rec["depended_on_by"] = wikilink_targets(fm.get("depended-on-by"))
            elif folder == "01 - Raw Sources":
                rec["processed"] = bool(fm.get("processed", False))
                rec["related"] = wikilink_targets(fm.get("related"))
            notes.append(rec)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "vault_root": str(VAULT),
        "note_count": len(notes),
        "notes": notes,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(notes)} notes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
