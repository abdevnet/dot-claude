#!/usr/bin/env bash
# Mirror every instruction doc from the Swank ai-instructions repo into references/standards/ (flat).
# Usage: scripts/sync-standards.sh [--no-pull]
set -euo pipefail

REPO="${AI_INSTRUCTIONS_REPO:-$HOME/projects/ai-instructions}"
SRC="$REPO/AIInstructions/AIInstructions.Web/Documents"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="$SKILL_DIR/references/standards"
SELECTION="$SKILL_DIR/references/standards-selection.md"

[[ -d "$SRC" ]] || { echo "source not found: $SRC" >&2; exit 1; }

if [[ "${1:-}" != "--no-pull" ]]; then
  git -C "$REPO" pull --ff-only
fi

# The target is flat, so two source docs with the same basename would clobber each other.
dupes=$(find "$SRC" -name '*.md' -exec basename {} \; | sort | uniq -d)
[[ -z "$dupes" ]] || { echo "basename collision in source, refusing to sync: $dupes" >&2; exit 1; }

changed=0
while IFS= read -r f; do
  name=$(basename "$f")
  if ! cmp -s "$f" "$DST/$name"; then
    cp "$f" "$DST/$name"
    echo "updated  $name"
    changed=$((changed + 1))
  fi
  grep -q "$name" "$SELECTION" || echo "WARN     $name has no row in references/standards-selection.md"
done < <(find "$SRC" -name '*.md' | sort)

for f in "$DST"/*.md; do
  name=$(basename "$f")
  find "$SRC" -name "$name" | grep -q . || echo "STALE    $name is no longer in the source catalog (remove by hand)"
done

echo "$changed file(s) updated"
