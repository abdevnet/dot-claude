#!/usr/bin/env python3
"""Resolve the current project + its one-hop linked notes for /my-world fast mode.

The old fast-mode flow cost at least three sequential tool round-trips: a
preflight bash block to refresh the index, a jq query to match the project, then
a batched Read of the project note and its links. The shell work is sub-100ms —
the latency that actually hurts is the model generating and waiting on each of
those round-trips in turn.

This script collapses all of it into ONE call. Given the working directory it:
  1. self-heals the index if a vault note changed since it was last built,
  2. matches the project note the way Step 1/2 of the command describes, and
  3. prints that note's body plus the body of every depends-on / depended-on-by
     project it links to, with clear delimiters.

The model reads stdout and writes its summary directly — no further tool calls.

Usage:  python3 resolve_fast.py "$PWD"
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index as bi  # noqa: E402


def index_is_fresh(payload: dict) -> bool:
    """True if the on-disk index covers every current vault note unchanged.

    Stat-only (no file reads/parsing), so it stays much cheaper than a rebuild.
    Directory mtimes catch adds/deletes; file mtimes catch edits.
    """
    if payload.get("schema_version") != bi.SCHEMA_VERSION:
        return False
    try:
        index_mtime = bi.OUTPUT.stat().st_mtime
    except OSError:
        return False
    for folder in bi.FOLDERS:
        root = bi.VAULT / folder
        if not root.is_dir():
            continue
        for path in (root, *root.rglob("*")):
            try:
                if path.stat().st_mtime > index_mtime:
                    return False
            except OSError:
                continue
    return True


def load_index() -> tuple[dict, bool]:
    """Return (payload, rebuilt). Rebuilds and rewrites when stale or unreadable."""
    if bi.OUTPUT.is_file():
        try:
            payload = json.loads(bi.OUTPUT.read_text(encoding="utf-8"))
            if index_is_fresh(payload):
                return payload, False
        except (OSError, json.JSONDecodeError):
            pass
    payload = bi.build_payload()
    bi.write_index(payload)
    return payload, True


def candidate_keys(cwd: str) -> list[str]:
    """Repo-name candidates derived from the path, in priority order.

    Mirrors the command's Step 1 rule: the first path segment after `projects/`
    is the repo name (so a worktree like .../sls/fairplay-sdk26 still resolves to
    `sls`). Deeper segments and the basename are kept as fallbacks.
    """
    parts = Path(cwd).expanduser().parts
    cands: list[str] = []
    if "projects" in parts:
        after = parts[parts.index("projects") + 1:]
        if after:
            cands.append(after[0])
            cands.extend(after[1:])
    if parts:
        cands.append(parts[-1])
    seen: set[str] = set()
    ordered: list[str] = []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


def repo_last_segment(repo: str) -> str:
    return repo.rstrip("/").split("/")[-1] if repo else ""


def find_project(projects: list[dict], cands: list[str]) -> dict | None:
    for cand in cands:
        for note in projects:
            if (
                note.get("title") == cand
                or note.get("repo") == cand
                or repo_last_segment(note.get("repo", "")) == cand
            ):
                return note
    return None


def emit_note(note: dict, label: str) -> None:
    path = bi.VAULT / note["file"]
    try:
        body = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"===== {label}: {note['file']} (unreadable: {exc}) =====\n")
        return
    print(f"===== {label}: {note['file']} =====")
    print(body.rstrip("\n"))
    print()


def emit_project_and_links(project: dict, by_title: dict) -> list[str]:
    """Emit the project note + every one-hop linked project. Returns link names."""
    emit_note(project, "CURRENT PROJECT")
    link_names: list[str] = []
    seen = {project["title"]}
    links = (
        [("DEPENDS-ON", d) for d in project.get("depends_on", [])]
        + [("DEPENDED-ON-BY", d) for d in project.get("depended_on_by", [])]
    )
    if not links:
        print("# NO_LINKS: project has no depends-on / depended-on-by entries")
        return link_names
    for label, name in links:
        if name in seen:
            continue
        seen.add(name)
        link_names.append(name)
        linked = by_title.get(name)
        if linked is None:
            print(f"===== {label}: {name} (no matching note in Projects/) =====\n")
        else:
            emit_note(linked, label)
    return link_names


def git_platform(cwd: str, project: dict) -> str:
    """One-line source-control platform note for the summary."""
    if "github-enterprise" in (project.get("tags") or []):
        return "GitHub Enterprise (swankmp.ghe.com) — from the note's github-enterprise tag"
    try:
        import subprocess

        out = subprocess.run(
            ["git", "-C", cwd, "remote", "-v"],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except (OSError, ValueError, subprocess.SubprocessError):
        return "unknown (git remote check failed)"
    if "swankmp.ghe.com" in out:
        return "GitHub Enterprise (swankmp.ghe.com) — consider adding the github-enterprise tag"
    if out.strip():
        first = out.strip().splitlines()[0]
        return f"Azure DevOps / other — {first}"
    return "no git remote found"


def emit_full(project: dict, link_names: list[str], notes: list[dict]) -> None:
    """Products (tag overlap), Concepts (tag or wikilink), Raw Sources (listing)."""
    project_tags = set(project.get("tags") or [])
    # Names a concept/raw-source can point at: the project, its links, matched products.
    pointed_at = {project["title"], *link_names}

    # --- Products: tag overlap with the project ---
    print("===== PRODUCTS (tag overlap) =====")
    matched_products = []
    for n in notes:
        if n.get("folder") != "Products":
            continue
        if project_tags & set(n.get("tags") or []):
            matched_products.append(n)
    if matched_products:
        for n in matched_products:
            pointed_at.add(n["title"])
        for n in matched_products:
            emit_note(n, "PRODUCT")
    else:
        print("# none\n")

    # --- Concepts: shared tags OR a wikilink to project / link / product ---
    candidates = []
    for n in notes:
        if n.get("folder") != "03 - Concepts":
            continue
        shared = project_tags & set(n.get("tags") or [])
        wl_hit = bool(set(n.get("wikilinks") or []) & pointed_at)
        if shared or wl_hit:
            candidates.append((len(shared), wl_hit, n))
    # Relevance order: wikilink match first, then more shared tags.
    candidates.sort(key=lambda c: (c[1], c[0]), reverse=True)
    dropped = 0
    if len(candidates) > 8:  # too many — keep strong matches only (2+ tags or a wikilink)
        kept = [c for c in candidates if c[0] >= 2 or c[1]]
        dropped = len(candidates) - len(kept)
        candidates = kept
    print(f"===== CONCEPTS ({len(candidates)} relevant" +
          (f", {dropped} weaker single-tag matches dropped" if dropped else "") + ") =====")
    if candidates:
        for shared_n, wl_hit, n in candidates:
            emit_note(n, f"CONCEPT (shared tags: {shared_n}; wikilink: {'yes' if wl_hit else 'no'})")
    else:
        print("# none\n")

    # --- Raw sources: unprocessed + related to project/link/product. Listing only. ---
    raw = []
    for n in notes:
        if n.get("folder") != "01 - Raw Sources":
            continue
        if n.get("processed"):
            continue
        if set(n.get("related") or []) & pointed_at:
            raw.append(n)
    print(f"===== UNPROCESSED RAW SOURCES ({len(raw)}) =====")
    if raw:
        for n in raw:
            src = n.get("source") or "(no source url)"
            rel = ", ".join(n.get("related") or [])
            print(f"- {n['title']} — {src}  (related: {rel})")
    else:
        print("# none")
    print()


def main() -> int:
    full = "--full" in sys.argv[1:]
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    cwd = positional[0] if positional else os.getcwd()

    payload, rebuilt = load_index()
    notes = payload["notes"]
    projects = [n for n in notes if n.get("folder") == "Projects"]
    by_title = {n["title"]: n for n in projects}

    cands = candidate_keys(cwd)
    print(f"# mode: {'full' if full else 'fast'}")
    print(f"# index: {'rebuilt' if rebuilt else 'fresh'} ({payload['note_count']} notes)")
    print(f"# cwd: {cwd}")
    print(f"# candidates: {', '.join(cands) or '(none)'}")
    print()

    project = find_project(projects, cands)
    if project is None:
        print(f"NO_PROJECT_NOTE\tNo Projects/*.md matched candidates: {', '.join(cands)}")
        return 0

    if full:
        print(f"# source-control: {git_platform(cwd, project)}")
        print()

    link_names = emit_project_and_links(project, by_title)

    if full:
        emit_full(project, link_names, notes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
