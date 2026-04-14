#!/bin/bash
# wiki-lint.sh — structural health check for the Obsidian dev-projects vault.
# Single-process Python for speed + one permission prompt.

set -euo pipefail

VAULT="${WIKI_LINT_VAULT:-$HOME/projects/obsidian/dev-projects}"

exec python3 - "$VAULT" <<'PYEOF'
import os, re, sys
from pathlib import Path
from datetime import datetime

VAULT = Path(sys.argv[1])
IN_SCOPE = ["Projects", "Products", "03 - Concepts", "01 - Raw Sources", "Clippings"]
STALE_DAYS = 14
TODAY = datetime.now().date()

REQUIRED = {
    "project":    ["repo", "layer", "status", "stack"],
    "umbrella":   ["status"],
    "product":    ["tags"],
    "concept":    ["tags"],
    "clipping":   ["title", "source", "captured", "processed"],
    "initiative": ["status"],
    "reference":  [],
    "worktree":   [],
}

FM_RE       = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
WIKILINK_RE = re.compile(r'\[\[([^\]|#]+?)(?:[|#][^\]]*)?\]\]')


def parse_frontmatter(text):
    """Minimal YAML frontmatter parser: handles `key: value`, block lists, and flow lists."""
    m = FM_RE.match(text)
    if not m:
        return {}
    fm, current_list = {}, None
    for line in m.group(1).split('\n'):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if re.match(r'^\s*-\s', line) and current_list is not None:
            val = line.strip()[1:].strip().strip('"').strip("'")
            current_list.append(val)
            continue
        if ':' in line and not line.startswith(' '):
            key, _, val = line.partition(':')
            key, val = key.strip(), val.strip()
            if val == '':
                current_list = []
                fm[key] = current_list
            elif val.startswith('[') and val.endswith(']'):
                inner = val[1:-1].strip()
                fm[key] = [x.strip().strip('"').strip("'") for x in inner.split(',')] if inner else []
                current_list = None
            else:
                fm[key] = val.strip('"').strip("'")
                current_list = None
    return fm


def collect_in_scope():
    files = []
    for folder in IN_SCOPE:
        p = VAULT / folder
        if not p.exists():
            continue
        for f in p.glob('*.md'):
            if f.name.lower() == 'readme.md':
                continue
            files.append(f)
    return files


def strip_link(s):
    return re.sub(r'\[\[|\]\]', '', s).strip()


def main():
    files = collect_in_scope()
    all_stems = {}
    for f in VAULT.rglob('*.md'):
        all_stems.setdefault(f.stem.lower(), f)

    data = {}
    for f in files:
        text = f.read_text(encoding='utf-8', errors='replace')
        fm = parse_frontmatter(text)
        body = FM_RE.sub('', text, count=1)
        # Unescape table-cell pipes so wikilink aliases like [[Foo\|Bar]] parse correctly
        body = body.replace('\\|', '|')
        links = set(m.group(1).strip() for m in WIKILINK_RE.finditer(body))
        for v in fm.values():
            if isinstance(v, list):
                for item in v:
                    links.update(m.group(1).strip() for m in WIKILINK_RE.finditer(item))
            elif isinstance(v, str):
                links.update(m.group(1).strip() for m in WIKILINK_RE.finditer(v))
        data[f] = {'fm': fm, 'links': links}

    inbound = {f.stem.lower(): set() for f in files}
    for f, d in data.items():
        for link in d['links']:
            key = strip_link(link).lower()
            if key in inbound:
                inbound[key].add(f.stem)

    # 1. Broken wikilinks
    broken = []
    for f, d in data.items():
        for link in d['links']:
            if strip_link(link).lower() not in all_stems:
                broken.append((f.relative_to(VAULT), link))

    # 2. Asymmetric dependencies (projects only)
    asym = []
    projects = {f.stem.lower(): (f, d) for f, d in data.items() if 'Projects' in str(f)}
    for stem, (f, d) in projects.items():
        deps = d['fm'].get('depends-on') or []
        if not isinstance(deps, list):
            deps = []
        for dep in deps:
            dep_clean = strip_link(dep).lower()
            if dep_clean in projects:
                other_dby = projects[dep_clean][1]['fm'].get('depended-on-by') or []
                if not isinstance(other_dby, list):
                    other_dby = []
                other_clean = [strip_link(x).lower() for x in other_dby]
                if stem not in other_clean:
                    asym.append(f"`{f.name}` → depends-on `[[{dep_clean}]]`; reverse missing in `{dep_clean}.md`")

    # 3. Missing required frontmatter
    missing = []
    for f, d in data.items():
        fm = d['fm']
        t = (fm.get('type') or '').lower().strip()
        if not t:
            p = str(f)
            if 'Projects' in p:        t = 'project'
            elif 'Products' in p:      t = 'product'
            elif 'Concepts' in p:      t = 'concept'
            elif 'Clippings' in p:     t = 'clipping'
            elif 'Raw Sources' in p:   t = 'clipping'
        req = REQUIRED.get(t, [])
        miss = [r for r in req if not fm.get(r) and fm.get(r) != False]
        if miss:
            missing.append(f"`{f.relative_to(VAULT)}` [{t or '?'}] — missing: {', '.join(miss)}")

    # 4. Orphans (projects/products/concepts only)
    orphans = []
    for f, d in data.items():
        p = str(f)
        if 'Clippings' in p or 'Raw Sources' in p:
            continue
        if not inbound.get(f.stem.lower()) and not d['links']:
            orphans.append(str(f.relative_to(VAULT)))

    # 5. Unprocessed raw sources + stale
    unprocessed, stale_count = [], 0
    for f, d in data.items():
        p = str(f)
        if 'Clippings' not in p and 'Raw Sources' not in p:
            continue
        fm = d['fm']
        processed = str(fm.get('processed', 'false')).lower()
        if processed == 'true':
            continue
        captured = fm.get('captured') or fm.get('created') or ''
        age_str = ''
        stale = False
        if captured:
            try:
                cap = datetime.strptime(captured[:10], '%Y-%m-%d').date()
                age = (TODAY - cap).days
                age_str = f" ({age}d old)"
                stale = age > STALE_DAYS
            except Exception:
                pass
        if stale:
            stale_count += 1
        unprocessed.append(f"`{f.name}`{age_str}{' — **STALE**' if stale else ''}")

    # 6. Clippings with no relations
    no_rel = []
    for f, d in data.items():
        p = str(f)
        if 'Clippings' not in p and 'Raw Sources' not in p:
            continue
        rel = d['fm'].get('related')
        if not rel:
            no_rel.append(f"`{f.name}`")

    # 7. One-off tags
    tag_count = {}
    for f, d in data.items():
        tags = d['fm'].get('tags') or []
        if isinstance(tags, list):
            for t in tags:
                tag_count[t] = tag_count.get(t, 0) + 1
    one_offs = sorted([t for t, c in tag_count.items() if c == 1])

    # --- Report ---
    out = []
    out.append(f"# Wiki Lint Report — {TODAY.isoformat()}")
    out.append(f"**Mode:** structural  ")
    out.append(f"**Scanned:** {len(files)} files across {len(IN_SCOPE)} folders")
    out.append("")
    out.append("## Summary")
    out.append(f"- {len(broken)} broken wikilinks")
    out.append(f"- {len(asym)} asymmetric dependencies")
    out.append(f"- {len(missing)} missing-frontmatter issues")
    out.append(f"- {len(orphans)} orphan notes")
    out.append(f"- {len(unprocessed)} unprocessed raw sources ({stale_count} stale)")
    out.append(f"- {len(no_rel)} clippings with no relations")
    out.append(f"- {len(one_offs)} one-off tags")
    out.append("")
    out.append("## Findings")

    def section(title, items):
        out.append(f"\n### {title} ({len(items)})")
        if not items:
            out.append("_(0) — none found_")
        else:
            for it in items:
                out.append(f"- {it}")

    section("1. Broken wikilinks", [f"`{p}` → `[[{l}]]`" for p, l in broken])
    section("2. Asymmetric dependencies", asym)
    section("3. Missing required frontmatter", missing)
    section("4. Orphan notes", orphans)
    section("5. Unprocessed raw sources", unprocessed)
    section("6. Clippings with no relations", no_rel)
    tag_display = one_offs[:15] + ([f"_… and {len(one_offs) - 15} more_"] if len(one_offs) > 15 else [])
    section("7. One-off tags", tag_display)

    print("\n".join(out))


main()
PYEOF
