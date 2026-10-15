#!/usr/bin/env python3
"""Tie vault project notes to their local clones: staleness, hot repos, fetch.

Shared by /my-world (resolve.py), /wiki-lint and /wiki-refresh.

Staleness is measured against origin/<default branch>, not the checked-out
branch: a note should describe what's on main, and feature branches in
progress shouldn't make it look stale. That only works if origin refs are
recent, which is why /wiki-lint fetches the hot repos first.

CLI (used by /wiki-refresh):
  codestate.py stale                     project notes flagged POSSIBLY STALE
  codestate.py context <project> [...]   per-note change context since last edit
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote

PROJECTS_ROOT = Path.home() / "projects"
CLAUDE_SESSIONS = Path.home() / ".claude" / "projects"
STALE_COMMITS = 5
HOT_DAYS = 30
FETCH_TIMEOUT = 60
GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}


def git(cwd: Path | str, *args: str, timeout: int = 5) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=timeout, env=GIT_ENV
        ).stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""


@lru_cache(maxsize=None)
def is_repo_root(d: Path) -> bool:
    top = git(d, "rev-parse", "--show-toplevel")
    return bool(top) and Path(top) == d.resolve()


def repo_last_segment(repo: str) -> str:
    return repo.rstrip("/").split("/")[-1] if repo else ""


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


@lru_cache(maxsize=None)
def default_ref(repo: Path) -> str:
    ref = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if ref:
        return ref
    for cand in ("origin/main", "origin/master", "origin/develop"):
        if git(repo, "rev-parse", "--verify", "--quiet", cand):
            return cand
    return "HEAD"


def git_common_dir(repo: Path) -> Path:
    d = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(d) if d else repo / ".git"


def last_fetch(repo: Path) -> float:
    try:
        return (git_common_dir(repo) / "FETCH_HEAD").stat().st_mtime
    except OSError:
        return 0.0


def note_edited(note_path: Path, text: str | None = None) -> int:
    """Later of the file mtime and a `verified: YYYY-MM-DD` frontmatter date.
    /wiki-refresh sets `verified` when a note was checked and needed no change."""
    edited = int(note_path.stat().st_mtime)
    if text is None:
        try:
            text = note_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return edited
    m = re.search(r"^verified:\s*['\"]?(\d{4}-\d{2}-\d{2})", text[:2000], re.M)
    if m:
        verified = int(datetime.strptime(m.group(1), "%Y-%m-%d").timestamp()) + 86399
        edited = max(edited, verified)
    return edited


def day(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "never"


def code_state(note: dict, note_path: Path) -> dict:
    """Facts about a note's clone. `clone` is None when there's no local clone."""
    clones = find_clones(note)
    if not clones:
        return {"clone": None}
    stamps = {c: int(git(c, "log", "-1", "--format=%ct", default_ref(c)) or 0) for c in clones}
    repo = max(clones, key=stamps.get)
    ref = default_ref(repo)
    edited = note_edited(note_path)
    since = int(git(repo, "rev-list", "--count", "--no-merges", f"--since={edited}", ref) or 0)
    return {
        "clone": repo,
        "others": len(clones) - 1,
        "ref": ref,
        "branch": git(repo, "branch", "--show-current") or "detached",
        "last_commit": stamps[repo],
        "fetched": last_fetch(repo),
        "edited": edited,
        "since": since,
        "stale": since >= STALE_COMMITS,
        "claude_md": any((p / "CLAUDE.md").is_file() for p in {repo, repo.parent} if p != PROJECTS_ROOT),
    }


def status_line(st: dict) -> str:
    if not st["clone"]:
        return "code: no local clone under ~/projects"
    parts = [
        f"code: {str(st['clone']).replace(str(Path.home()), '~')}",
        f"on {st['branch']}",
        f"{st['ref']} last commit {day(st['last_commit'])}",
        f"fetched {day(st['fetched'])}",
        f"note edited {day(st['edited'])}",
        f"{st['since']} commits since" + (" — POSSIBLY STALE" if st["stale"] else ""),
        f"CLAUDE.md {'yes' if st['claude_md'] else 'no'}",
    ]
    if st["others"]:
        parts.append(f"+{st['others']} other clones of this repo")
    return " · ".join(parts)


def code_states(items: list[tuple[dict, Path]]) -> list[dict]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(lambda it: code_state(*it), items))


# --- hot repos + fetch -------------------------------------------------------

def _session_key(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "-", str(path)).lower()


def claude_session_times() -> dict[str, float]:
    """Encoded working dir → newest session file mtime, from ~/.claude/projects."""
    out: dict[str, float] = {}
    if not CLAUDE_SESSIONS.is_dir():
        return out
    for d in CLAUDE_SESSIONS.iterdir():
        if d.is_dir():
            mtimes = [f.stat().st_mtime for f in d.glob("*.jsonl")]
            if mtimes:
                out[d.name.lower()] = max(mtimes)
    return out


def author_key() -> str:
    email = git(Path.home(), "config", "--global", "user.email")
    return email.split("@")[0] if email else ""


def activity(repo: Path, sessions: dict[str, float], author: str, cutoff: float) -> tuple[float, float]:
    """(latest Claude session, latest own commit) in the window, 0 when none."""
    key = _session_key(repo.resolve())
    recent = [t for k, t in sessions.items() if (k == key or k.startswith(key + "-")) and t >= cutoff]
    commit = ""
    if author:
        commit = git(repo, "log", "-1", "--all", f"--author={author}", f"--since={int(cutoff)}", "--format=%ct")
    return max(recent, default=0.0), float(commit or 0)


def hot_repos(clone_sets: list[list[Path]], days: int = HOT_DAYS) -> dict[Path, str]:
    """One repo per distinct git dir (worktrees share refs), keyed to why it's hot."""
    cutoff = time.time() - days * 86400
    sessions = claude_session_times()
    author = author_key()
    groups: dict[Path, list[Path]] = {}
    for clones in clone_sets:
        for c in clones:
            members = groups.setdefault(git_common_dir(c).resolve(), [])
            if c not in members:
                members.append(c)

    def check(gd: Path) -> tuple[Path, str]:
        members = groups[gd]
        acts = [activity(c, sessions, author, cutoff) for c in members]
        session, commit = max(a[0] for a in acts), max(a[1] for a in acts)
        reasons = []
        if session:
            reasons.append(f"Claude session {day(session)}")
        if commit:
            reasons.append(f"your commit {day(commit)}")
        # Show the main clone (real .git dir) rather than a worktree.
        main = next((c for c in members if (c / ".git").is_dir()), members[0])
        return main, ", ".join(reasons)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, list(groups)))
    return {repo: why for repo, why in results if why}


def fetch_one(repo: Path) -> tuple[Path, bool, str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "fetch", "--quiet", "--prune", "origin"],
            capture_output=True, text=True, timeout=FETCH_TIMEOUT, env=GIT_ENV,
        )
    except subprocess.TimeoutExpired:
        return repo, False, f"timed out after {FETCH_TIMEOUT}s"
    except OSError as exc:
        return repo, False, str(exc)
    if r.returncode != 0:
        err = (r.stderr.strip().splitlines() or ["fetch failed"])[-1]
        return repo, False, err[:160]
    return repo, True, ""


def fetch_all(repos: list[Path]) -> list[tuple[Path, bool, str]]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch_one, repos))
    default_ref.cache_clear()
    return results


# --- /wiki-refresh context ---------------------------------------------------

def refresh_context(note: dict, note_path: Path, max_commits: int = 60) -> str:
    st = code_state(note, note_path)
    lines = [f"===== {note['title']}: {note_path} =====", status_line(st)]
    if not st["clone"]:
        return "\n".join(lines)
    repo, ref, since = st["clone"], st["ref"], f"--since={st['edited']}"
    log = git(repo, "log", "--no-merges", since, f"-{max_commits}", "--date=short",
              "--format=%h %ad %an: %s", ref, timeout=15)
    stat = git(repo, "log", "--no-merges", since, "--format=", "--shortstat", ref, timeout=15)
    files = git(repo, "log", "--no-merges", since, "--format=", "--name-only", ref, timeout=15)
    counts: dict[str, int] = {}
    for f in files.splitlines():
        if f:
            counts[f] = counts.get(f, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:40]
    ins = sum(int(m) for m in re.findall(r"(\d+) insertion", stat))
    dels = sum(int(m) for m in re.findall(r"(\d+) deletion", stat))
    lines.append(f"-- {st['since']} commits on {ref} since note edit (+{ins}/-{dels} lines, {len(counts)} files)")
    lines.append(log or "(no commits)")
    if top:
        lines.append("-- most-touched files:")
        lines.extend(f"{n:>3}  {f}" for f, n in top)
    if st["claude_md"]:
        cm = repo / "CLAUDE.md" if (repo / "CLAUDE.md").is_file() else repo.parent / "CLAUDE.md"
        lines.append(f"-- CLAUDE.md: {cm}")
    return "\n".join(lines)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("stale", "context") or (cmd == "context" and len(sys.argv) < 3):
        print(__doc__)
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_index as bi

    projects = {n["title"].lower(): n for n in bi.build_payload()["notes"] if n["folder"] == "Projects"}
    if cmd == "stale":
        items = [(n, bi.VAULT / n["file"]) for n in projects.values()]
        rows = [(n, st) for (n, _), st in zip(items, code_states(items)) if st.get("stale")]
        for n, st in sorted(rows, key=lambda r: -r[1]["since"]):
            print(f"{n['title']}\t{st['since']} commits since {day(st['edited'])}\tfetched {day(st['fetched'])}")
        return 0
    for name in sys.argv[2:]:
        note = projects.get(name.lower())
        if not note:
            print(f"===== {name}: no project note =====\n")
            continue
        print(refresh_context(note, bi.VAULT / note["file"]))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
