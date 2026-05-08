---
name: android-memory-stress-test
description: Run a Detail-open / Watch / Back stress test on an Android TV app APK against a connected adb device, capture per-cycle meminfo / activity / DRM dumps, and produce a memory-leak analysis report (Java retention, native heap, PSS, MediaDrm sessions) with side-by-side comparison against prior versions. Use this skill whenever the user has a new APK to validate (EaselTV, Prism, or any similar TV/playback app), wants to verify a memory-leak fix, asks to "run a stress test" / "memory test" / "leak test" on a build, or mentions reboots, OOM kills, LMK, native heap growth, MediaDrm exhaustion, or per-cycle Activity retention. Trigger this even if the user only says "test the new APK" or "run another memory test" — this is the established workflow.
---

# Android Memory Stress Test

This skill drives a memory-leak stress test on an Android TV app APK using `adb` against
a connected device, parses per-cycle `dumpsys` snapshots into a metrics CSV, and produces
a markdown analysis report comparing the run against prior versions.

The test reproduces a realistic "patient browses, plays, backs out, picks another" cycle
that historically surfaces leaks in Activity / View / AppContext retention, MediaDrm
session pools, and native heap growth. Seven cycles of ~110 s each — about 13 min total.

## When to use

- New APK build of EaselTV (`com.swank.android`) or Prism (`com.swank.patient`) to validate.
- The user wants to confirm a leak fix landed (e.g., "did 3.18.4 fix the Activity retention?").
- Field reports of reboots, OOM kills, surface render failures, or MediaDrm exhaustion.
- Comparison run against prior version's metrics CSV.

## Workflow

The full workflow has six stages. Don't skip ahead — each stage produces inputs for the
next, and stages 2-3 require manual setup that only the user can do.

### 1. Verify environment

Before doing anything, confirm:

```bash
adb devices -l                    # device attached and authorized
aapt dump badging <apk-path>      # confirm package + versionCode + versionName
```

Note the device model + Android version. This matters for the report — Android 11 vs
Android 14 handle zombie Activity records differently, and 1.5 GB vs 4 GB devices have
very different LMK behavior. Capture this in the report's hardware-under-test line.

### 2. Decide install strategy and install

Two options. Default to `-r` (re-install over data) because it preserves comparability
with prior runs and avoids first-cold-start noise. Use a clean install only when the
user specifically wants to confirm no carry-over state from a prior version's persisted
queues (e.g., "did the analytics fix actually clear out, or is it just suppressed?").

```bash
# Re-install over data (default)
adb install -r <apk-path>

# Clean install (only when explicitly requested)
adb uninstall <package-name>
adb install <apk-path>
```

Verify the install:

```bash
adb shell dumpsys package <package-name> | grep -E "versionName|versionCode" | head -3
```

If the user is ambivalent, briefly explain the trade-off and ask. See
`references/interpretation.md` § "Install strategy" for the full rationale.

### 3. Hand off manual setup to the user

You cannot do this — the user must physically navigate the device. Be explicit about
what you need from them:

1. Cold-launch via deep link into a target portal. Provide the exact `am start` command
   for their app — see `references/presets.md` for EaselTV and Prism.
2. Wait for the catalog to load.
3. Park focus on the row / tile they want the cycle to operate on. The same row each
   run is critical for comparability.
4. Tell you when ready.

### 4. Run the stress test

Use `scripts/runner.sh`. It is parameterized — pass the package name and an output
directory. Don't edit the script for each run; just pass arguments.

```bash
RUN_DIR=/tmp/<app>-<version>
mkdir -p "$RUN_DIR"
<skill-path>/scripts/runner.sh <package-name> "$RUN_DIR"
```

Default is 7 cycles (~13 min). Run it in the background so you can schedule a wakeup
rather than blocking on the foreground. Per-cycle metrics land in `$RUN_DIR/metrics.csv`,
console output in `$RUN_DIR/runner.out`, full dumpsys snapshots in `mem_*.txt`,
`act_*.txt`, `drm_*.txt`, plus a combined `detail.log`.

Script parameters (positional):
1. `package-name` — required (`com.swank.android`, `com.swank.patient`, etc.)
2. `run-dir` — required, must already exist
3. `cycles` — optional, default 7
4. `play-seconds` — optional, default 90 (per-cycle playback duration)

For typical extended-duration runs (testing whether native heap plateaus), pass cycles=30
or cycles=50 instead of the default 7.

### 5. Analyze the metrics

Read `metrics.csv`. The leak signal is the **per-cycle slope**, not absolute values.
Compute slopes across **C2 → C7** (or C2 → final) — exclude C1 because cold-start
allocates one-time analytics / DRM / Compose objects that aren't part of steady state.

Six metrics matter:

| Metric | What a leak looks like | Why |
|---|---|---|
| `activities` | +N per cycle | Activity Java retention — most damaging, unbounded |
| `views` | +N per cycle | Compose view tree pinned to leaked Activity |
| `appcontexts` | +N per cycle | Context wrapper retention — analytics listeners common cause |
| `native_kb` | +N MB per cycle | Codec buffers, bitmaps, OkHttp/Coil pools, libc fragmentation |
| `pss_kb` | +N MB per cycle | Total memory cost — what hits LMK |
| `drm_active` | +N per cycle | MediaDrm session pool — exhausts at ~10 on most chipsets |

Flat (zero slope) on Activities/Views/AppContexts means Java side is clean. Flat on
`drm_active` means MediaDrm cleanup is correct. PSS minus Native delta tells you if
growth is in malloc (codec/cache) or elsewhere (Dalvik, GL, ashmem).

See `references/interpretation.md` for the full breakdown including PSS vs Native heap,
GC reclaim behavior, and hardware-specific caveats (PDi A24C2 vs Google TV Streamer).

### 6. Write the report

Write the report to `~/Downloads/<app>-<version>/<app>-<version>-stress-test.md` (or
wherever the user wants — ask if it's not obvious). Mirror the structure in
`references/report-template.md`. The report has six sections:

1. Header (date, subject, hardware, install state, purpose)
2. Executive summary (one paragraph — did the leak shape change?)
3. Findings (numbered, one per metric with notable change, with the per-cycle table)
4. Side-by-side delta vs prior versions
5. Test methodology (carry forward unchanged unless something differed)
6. Interpretation (root-cause hypothesis, what to investigate next)

The most important slot is the side-by-side delta table — that's the artifact a reader
glances at first. Always include it, always cite the per-cycle slope (not absolute MB),
and always note which version is the comparison baseline.

After writing, also copy the run artifacts (csv, txt dumps, runner.sh, runner.out, the
report) to a single folder under `~/Downloads/` so the run is self-contained.

## Anti-patterns

- **Don't compute slopes from C1** — cold start adds one-shot allocations that masquerade
  as a leak. Always start the slope from C2.
- **Don't compare absolute MB across hardware** — Android 14 framework is heavier than
  Android 11. Compare slopes, not levels.
- **Don't treat flat Native Heap as "no leak"** — the libc allocator (jemalloc/scudo)
  retains free regions internally; PSS may stay elevated even after frees. Cross-check
  with PSS slope and with whether Activities/Views are also flat.
- **Don't run the test before the user confirms focus is parked** — if focus drifts
  during cycles, the runner navigates into wrong tiles and cycle measurements diverge.
- **Don't write the report before the run completes** — partial CSVs lead to wrong
  slopes. Wait for `>> done` in `runner.out`.

## Reference files

- `scripts/runner.sh` — the parameterized test driver. Captures meminfo, activity,
  media.resource_manager per cycle and parses into a CSV. Reads no env vars beyond
  what's documented.
- `references/presets.md` — EaselTV and Prism specifics: package names, deep link
  schemes, portal segment IDs, focus-row hints.
- `references/interpretation.md` — what each metric means, slope methodology,
  PSS vs Native Heap, hardware caveats, ExoPlayer / Media3 native-heap context.
- `references/report-template.md` — the markdown report structure with headings and
  table formats already filled in.
