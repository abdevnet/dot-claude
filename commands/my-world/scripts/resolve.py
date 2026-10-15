#!/usr/bin/env python3
"""Load the slice of the dev-projects vault a task touches, for /my-world.

One call prints everything the model needs:
  1. SYSTEM MAP: every project (layer, one-liner, depends-on) plus concept and
     product one-liners. About 4K tokens, always printed.
  2. Seeds: the project matched from the working directory, any note named in
     the arguments, and (only when neither exists) the best keyword matches for
     the task text.
  3. Ranked notes: seeds, graph neighbours up to two hops, linked or tag-sharing
     concepts and products, and keyword matches. Bodies fill a token budget:
     near notes in full, far ones as cards (frontmatter + overview). Notes that
     don't fit are listed so the model can Read them on demand.

Hubs (heavily linked shared infra such as gitops) are loaded but not walked
through; otherwise two hops drags in most of the vault.

Usage:  resolve.py [--cwd DIR] [--budget TOKENS] [name ...] ["task text"]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index as bi  # noqa: E402

DEFAULT_BUDGET = 100_000
FULL_FLAG_BUDGET = 200_000
HUB_DEGREE = 10
MAX_DEPTH = 2
MIN_SCORE = 40
FULL_SCORE = 300
UPGRADE_SCORE = 100
STALE_COMMITS = 5
PROJECTS_ROOT = Path.home() / "projects"
DIST_SCORE = {0: 1000, 1: 500, 2: 150}
GENERIC_TAGS = {"project", "concept", "product", "raw-source", "source", "moc"}
RAW = "01 - Raw Sources"
STOPWORDS = set("""
the and for with from that this what which when where how why who into onto over under
about across between does did done have has had are was were will would could should can
not but any all our your their its out off use used using via per vs etc also just like
need needs want wants make makes change changes changing impact affect affects work works
""".split())


def tokens_of(text: str) -> int:
    return len(text) // 4 + 1


def index_is_fresh(payload: dict) -> bool:
    """Stat-only freshness check: dir mtimes catch adds/deletes, file mtimes catch edits."""
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
    """Repo-name candidates from the path; the first segment after `projects/` wins,
    so a worktree like .../sls/fairplay-sdk26 still resolves to `sls`."""
    parts = Path(cwd).expanduser().parts
    cands: list[str] = []
    if "projects" in parts:
        cands.extend(parts[parts.index("projects") + 1:])
    if parts:
        cands.append(parts[-1])
    return list(dict.fromkeys(c for c in cands if c))


def repo_last_segment(repo: str) -> str:
    return repo.rstrip("/").split("/")[-1] if repo else ""


def match_name(name: str, notes: list[dict]) -> dict | None:
    key = name.lower()
    for n in notes:
        if n["title"].lower() == key:
            return n
    for n in notes:
        if n.get("folder") == "Projects" and key in (
            (n.get("repo") or "").lower(), repo_last_segment(n.get("repo") or "").lower()
        ):
            return n
    return None


def git(cwd: Path | str, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""


@lru_cache(maxsize=None)
def is_repo_root(d: Path) -> bool:
    top = git(d, "rev-parse", "--show-toplevel")
    return bool(top) and Path(top) == d.resolve()


def norm_remote(url: str) -> str:
    u = unquote(url).strip().lower()
    u = re.sub(r"^[a-z+]+://", "", u)
    u = re.sub(r"^[^@/]+@", "", u)
    u = u.replace("ssh.dev.azure.com:v3/", "dev.azure.com/").replace(":", "/")
    return u.removesuffix(".git").rstrip("/")


@lru_cache(maxsize=None)
def origin_of(d: Path) -> str:
    return norm_remote(git(d, "remote", "get-url", "origin"))


def find_clones(note: dict) -> list[Path]:
    """Local clones of the note's repo. Sibling worktrees sharing its origin count too;
    a folder of unrelated repos (e.g. an umbrella of symlinks) never matches by name alone."""
    repo = note.get("repo") or ""
    if repo.startswith(("~", "/")):
        dirs, want = [Path(repo).expanduser()], ""
    else:
        want = norm_remote(repo) if repo else ""
        names = dict.fromkeys([note["title"], unquote(repo_last_segment(repo))])
        dirs = [PROJECTS_ROOT / n for n in names if n]
    for d in dirs:
        if not d.is_dir():
            continue
        if is_repo_root(d):
            want = want or origin_of(d)
            pool = [d]
            if d.parent != PROJECTS_ROOT:
                pool += [c for c in sorted(d.parent.iterdir()) if c != d and c.is_dir() and is_repo_root(c)]
        else:
            pool = [c for c in sorted(d.iterdir()) if c.is_dir() and is_repo_root(c)]
        clones = [c for c in pool if want and origin_of(c) == want]
        if not clones and is_repo_root(d):
            clones = [d]
        if clones:
            return clones
    return []


def code_status(note: dict) -> tuple[str, bool]:
    """One line tying a project note to its local clone, and whether the note looks stale."""
    clones = find_clones(note)
    if not clones:
        return "code: no local clone under ~/projects", False
    stamps = {c: int(git(c, "log", "-1", "--format=%ct") or 0) for c in clones}
    repo = max(clones, key=stamps.get)
    edited = int((bi.VAULT / note["file"]).stat().st_mtime)
    since = int(git(repo, "rev-list", "--count", "--no-merges", f"--since={edited}", "HEAD") or 0)
    day = lambda ts: datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    has_claude = any((p / "CLAUDE.md").is_file() for p in {repo, repo.parent} if p != PROJECTS_ROOT)
    stale = since >= STALE_COMMITS
    parts = [
        f"code: {str(repo).replace(str(Path.home()), '~')}",
        f"branch {git(repo, 'branch', '--show-current') or 'detached'}",
        f"last commit {day(stamps[repo])}",
        f"note edited {day(edited)}",
        f"{since} commits since" + (" — POSSIBLY STALE" if stale else ""),
        f"CLAUDE.md {'yes' if has_claude else 'no'}",
    ]
    if len(clones) > 1:
        parts.append(f"+{len(clones) - 1} other clones of this repo")
    return " · ".join(parts), stale


def read_text(note: dict, cache: dict) -> str:
    if note["file"] not in cache:
        try:
            cache[note["file"]] = (bi.VAULT / note["file"]).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            cache[note["file"]] = f"(unreadable: {exc})"
    return cache[note["file"]]


def make_card(text: str) -> str:
    fm, body = "", text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm, body = text[: end + 4].strip(), text[end + 4:]
    h1 = re.search(r"^# .*$", body, re.M)
    ov = re.search(r"^## Overview\s*\n.*?(?=^## |\Z)", body, re.M | re.S)
    if ov:
        part = ov.group(0).strip()
    else:
        paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip() and not p.strip().startswith("#")]
        part = paras[0] if paras else ""
    return "\n".join(x for x in (fm, h1.group(0) if h1 else "", part) if x)


def task_terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9_.-]{2,}", text.lower())
    return list(dict.fromkeys(w.strip(".-") for w in words if w not in STOPWORDS))


def keyword_score(note: dict, text: str, terms: list[str]) -> int:
    if not terms:
        return 0
    head = " ".join([note["title"], note.get("repo") or "", *(note.get("tags") or [])]).lower()
    low = text.lower()
    score = 0
    for t in terms:
        if t in head:
            score += 25
        score += min(len(re.findall(r"\b" + re.escape(t), low)), 10)
    return score


def git_platform(cwd: str) -> str:
    top = git(cwd, "rev-parse", "--show-toplevel")
    # The home folder is itself a repo; its remote says nothing about the project.
    if not top or Path(top) == Path.home():
        return ""
    out = git(cwd, "remote", "-v")
    if not out:
        return ""
    first = out.splitlines()[0]
    kind = "Azure DevOps" if ("dev.azure.com" in out or "visualstudio.com" in out) else "other"
    return f"{kind} — {first}"


def build_map(notes: list[dict], links: dict, hubs: set[str]) -> str:
    lines = ["===== SYSTEM MAP =====",
             "Projects: name [layer] (status if not active) — overview → depends-on. * = hub (loaded, not walked through)"]
    for n in sorted((n for n in notes if n["folder"] == "Projects"), key=lambda n: n["title"].lower()):
        layer = f" [{n['layer']}]" if n.get("layer") else ""
        status = f" ({n['status']})" if n.get("status") and n["status"] != "active" else ""
        deps = [t for rel, t in links.get(n["title"].lower(), []) if rel == "dependency"]
        arrow = f" → {', '.join(deps)}" if deps else ""
        hub = "*" if n["title"].lower() in hubs else ""
        lines.append(f"- {n['title']}{hub}{layer}{status} — {n.get('overview') or ''}{arrow}")
    for folder, label in (("03 - Concepts", "Concepts"), ("Products", "Products")):
        lines.append(f"{label}:")
        for n in sorted((n for n in notes if n["folder"] == folder), key=lambda n: n["title"].lower()):
            lines.append(f"- {n['title']} — {n.get('overview') or ''}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> tuple[str, int, list[str]]:
    cwd, budget, pos = os.getcwd(), DEFAULT_BUDGET, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--cwd" and i + 1 < len(argv):
            cwd, i = argv[i + 1], i + 2
        elif a == "--budget" and i + 1 < len(argv):
            raw = argv[i + 1].lower().replace(",", "")
            budget = int(float(raw[:-1]) * 1000) if raw.endswith("k") else int(raw)
            i += 2
        elif a == "--full":
            budget, i = max(budget, FULL_FLAG_BUDGET), i + 1
        else:
            pos.append(a)
            i += 1
    if pos and pos[0].startswith("/") and Path(pos[0]).is_dir():
        cwd = pos.pop(0)
    return cwd, budget, pos


def main() -> int:
    cwd, budget, pos = parse_args(sys.argv[1:])
    payload, rebuilt = load_index()
    allnotes = payload["notes"]
    notes = [n for n in allnotes if n["folder"] != RAW]
    by_key = {n["title"].lower(): n for n in notes}
    cache: dict[str, str] = {}

    # Links resolve against every folder, not just Projects/.
    links: dict[str, list[tuple[str, str]]] = {}
    unresolved: list[str] = []
    for n in notes:
        if n["folder"] != "Projects":
            continue
        out = []
        for rel, names in (("dependency", n.get("depends_on", [])), ("dependent", n.get("depended_on_by", []))):
            for name in names:
                target = by_key.get(name.lower())
                if target:
                    out.append((rel, target["title"]))
                else:
                    unresolved.append(f"{n['title']} → {name}")
        links[n["title"].lower()] = out
    hubs = {k for k, v in links.items() if len(v) >= HUB_DEGREE}

    # Seeds: working directory, then names in the arguments.
    seeds: dict[str, str] = {}
    cwd_project = None
    for cand in candidate_keys(cwd):
        hit = match_name(cand, [n for n in notes if n["folder"] == "Projects"])
        if hit:
            cwd_project = hit
            seeds[hit["title"].lower()] = "working directory"
            break
    unmatched: list[str] = []
    for arg in pos:
        if " " in arg.strip():
            continue
        hit = match_name(arg, notes)
        if hit:
            seeds.setdefault(hit["title"].lower(), "named in arguments")
        else:
            unmatched.append(arg)
    task_text = " ".join(a for a in pos if " " in a.strip() or a in unmatched)
    terms = task_terms(task_text)

    kw = {n["title"].lower(): keyword_score(n, read_text(n, cache), terms) for n in notes}
    for term in terms:
        hit = match_name(term, notes)
        if hit:
            seeds.setdefault(hit["title"].lower(), "named in task")
    if not seeds and terms:
        # Best project per term whose title contains it, then the top 3 overall.
        picks: dict[str, int] = {}
        for term in terms:
            titled = [k for k, n in by_key.items() if n["folder"] == "Projects" and term in k]
            if titled:
                best = max(titled, key=lambda k: kw[k])
                picks[best] = kw[best]
        for k in sorted(picks, key=picks.get, reverse=True)[:3]:
            seeds[k] = f"keyword match ({kw[k]})"

    # Graph walk from the seeds. Concept/product seeds expand once via their wikilinks.
    dist: dict[str, int] = {}
    via: dict[str, str] = {}
    queue: deque[str] = deque()
    for k, why in seeds.items():
        dist[k], via[k] = 0, f"seed: {why}"
        queue.append(k)
    while queue:
        k = queue.popleft()
        if dist[k] >= MAX_DEPTH or (k in hubs and k not in seeds):
            continue
        note = by_key[k]
        if note["folder"] == "Projects":
            nbrs = links.get(k, [])
        elif dist[k] == 0:
            nbrs = [("linked", by_key[w.lower()]["title"]) for w in note.get("wikilinks", [])
                    if w.lower() in by_key and by_key[w.lower()]["folder"] == "Projects"]
        else:
            nbrs = []
        for rel, title in nbrs:
            t = title.lower()
            if t not in dist:
                dist[t] = dist[k] + 1
                via[t] = f"{rel} of {note['title']}"
                queue.append(t)

    near = {k for k, d in dist.items() if d <= 1}
    seed_tags = set()
    for k in seeds:
        seed_tags |= set(by_key[k].get("tags") or [])
    seed_tags -= GENERIC_TAGS
    seed_wikilinks = {w.lower() for k in seeds for w in by_key[k].get("wikilinks", [])}

    scored: list[tuple[int, str, str]] = []
    for k, n in by_key.items():
        score, reasons = 0, []
        if k in dist:
            score += DIST_SCORE[dist[k]]
            reasons.append(f"d{dist[k]} {via[k]}")
        shared = (set(n.get("tags") or []) - GENERIC_TAGS) & seed_tags
        if n["folder"] != "Projects":
            wl = {w.lower() for w in n.get("wikilinks", [])}
            if k not in dist:
                if wl & set(seeds) or k in seed_wikilinks:
                    score += 300
                    reasons.append("links with a seed")
                elif wl & near:
                    score += 150
                    reasons.append("links with a neighbour")
            score += 40 * len(shared)
        elif k not in dist:
            score += 15 * len(shared)
        if shared:
            reasons.append(f"tags: {', '.join(sorted(shared))}")
        if kw[k]:
            score += 3 * kw[k]
            reasons.append(f"keywords {kw[k]}")
        if score >= MIN_SCORE:
            scored.append((score, k, "; ".join(reasons)))
    scored.sort(key=lambda s: (-s[0], s[1]))

    map_text = build_map(notes, links, hubs)
    used = tokens_of(map_text) + 300
    loaded: list[tuple[str, str, int, str, str]] = []
    omitted: list[tuple[str, int, int, str]] = []
    for score, k, why in scored:
        n = by_key[k]
        full = read_text(n, cache).rstrip("\n")
        forms = [("full", full), ("card", make_card(full))]
        if score < FULL_SCORE and k not in seeds:
            forms = forms[1:]
        for form, body in forms:
            if k in seeds or used + tokens_of(body) <= budget:
                used += tokens_of(body)
                loaded.append((form, k, score, why, body))
                break
        else:
            omitted.append((k, tokens_of(full), score, why))

    # Spare budget upgrades relevant cards to full notes, best first.
    for i, (form, k, score, why, body) in enumerate(loaded):
        if form != "card" or score < UPGRADE_SCORE:
            continue
        full = read_text(by_key[k], cache).rstrip("\n")
        extra = tokens_of(full) - tokens_of(body)
        if used + extra <= budget:
            used += extra
            loaded[i] = ("full", k, score, why, full)

    print(f"# my-world: budget {budget:,} tokens, used ~{used:,}; "
          f"index {'rebuilt' if rebuilt else 'fresh'} ({payload['note_count']} notes)")
    print(f"# cwd: {cwd}")
    if seeds:
        print("# seeds: " + "; ".join(f"{by_key[k]['title']} ({why})" for k, why in seeds.items()))
    else:
        print("# NO_SEED: no project matched the working directory, arguments, or task keywords. "
              "Map only; ask which projects the task touches.")
    if terms:
        print(f"# task terms: {', '.join(terms)}")
    if unmatched:
        print(f"# unmatched names (used as keywords): {', '.join(unmatched)}")
    if cwd_project:
        platform = git_platform(cwd)
        if platform:
            print(f"# source-control: {platform}")
    print(f"# hubs (loaded, not walked through): {', '.join(sorted(by_key[h]['title'] for h in hubs))}")
    if unresolved:
        print(f"# unresolved links: {', '.join(unresolved)}")
    code_lines: dict[str, str] = {}
    stale_notes: list[str] = []
    project_keys = [k for _, k, *_ in loaded if by_key[k]["folder"] == "Projects"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(lambda k: code_status(by_key[k]), project_keys)
    for k, (line, stale) in zip(project_keys, results):
        code_lines[k] = line
        if stale:
            stale_notes.append(by_key[k]["title"])
    if stale_notes:
        print(f"# possibly stale notes (≥{STALE_COMMITS} commits since last edit): {', '.join(stale_notes)}")
    print(f"# loaded: {sum(1 for l in loaded if l[0] == 'full')} full, "
          f"{sum(1 for l in loaded if l[0] == 'card')} cards; omitted: {len(omitted)}")
    print()
    print(map_text)

    for form, k, score, why, body in loaded:
        n = by_key[k]
        kind = {"Projects": "PROJECT", "03 - Concepts": "CONCEPT", "Products": "PRODUCT"}.get(n["folder"], "NOTE")
        hint = " — card; Read the path for the full note" if form == "card" else ""
        print(f"===== {kind} [{form}] score {score} · {why}: {n['file']}{hint} =====")
        if k in code_lines:
            print(f"> {code_lines[k]}")
        print(body)
        print()

    loaded_keys = {k for _, k, *_ in loaded}
    raw = [n for n in allnotes if n["folder"] == RAW and not n.get("processed")
           and {r.lower() for r in n.get("related") or []} & loaded_keys]
    if raw:
        print(f"===== UNPROCESSED RAW SOURCES ({len(raw)}) =====")
        for n in raw:
            print(f"- {n['title']} — {n.get('source') or '(no source url)'}  (related: {', '.join(n.get('related') or [])})")
        print()

    if omitted:
        print(f"===== OMITTED (over budget, {len(omitted)}) — Read on demand =====")
        for k, size, score, why in omitted:
            print(f"- {by_key[k]['file']} (~{size:,} tokens, score {score}; {why})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
