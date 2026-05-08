# Report template

Use this exact structure for stress-test reports. Order matters — readers skim
top-down and stop when they have what they need.

## Filename

`<app>-<version>-stress-test.md` — e.g. `easeltv-3.18.4-stress-test.md`,
`prism-0.5.0-stress-test.md`.

Save to `~/Downloads/<app>-<version>/` alongside the run artifacts (csv, dump txts,
runner.sh, runner.out). The folder is the deliverable.

## Structure

````markdown
# <App display name> <Version> Memory Leak Re-test (<duration>-min stress)

**Date:** YYYY-MM-DD
**Subject:** `<apk-filename>` (`<package>` versionCode <code>)
**Hardware under test:** <device> (<Android version>, <RAM>)
**Install state:** Clean install / Re-install over data — <one-line rationale>
**Purpose:** <one sentence — what is this run validating>

Companion data files in this folder:
- `metrics.csv` — per-cycle metrics CSV
- `detail.log` — full dumpsys snapshots per cycle
- `runner.sh` / `runner.out` — test driver and console output

---

## Executive summary

<One paragraph. What changed (or didn't) since the last version, in plain language.
Lead with the verdict: "Java retention leak fixed", or "no change from prior", or
"new regression in X". Mention the most important number — typically the per-cycle
slope on Activities, and whether DRM is still flat at 3.>

<Second short paragraph: any failure modes observed in the window, or "no crashes,
no LMK kills, no surface-render failures within X cycles".>

---

## Findings

### 1. <First key finding — usually the Activity / View / AppContext result>

Per-cycle metrics over <duration>:

| Cycle | Elapsed | Activities (Java) | Views | AppContexts | Native MB | PSS MB | DRM |
|---|---|---|---|---|---|---|---|
| M0 | 0 s | <n> | <n> | <n> | <n> | <n> | <n> |
| C1 | 1 m 44 s | <n> | <n> | <n> | <n> | <n> | <n> |
| C2 | 3 m 30 s | <n> | <n> | <n> | <n> | <n> | <n> |
| ... | ... | ... | ... | ... | ... | ... | ... |
| Cn | <e> | <n> | <n> | <n> | <n> | <n> | <n> |

<Sentence interpreting the table — the per-cycle slope, whether it's flat from C2,
what shape this is.>

### 2. <Second finding — typically MediaDrm or native heap>

<Same pattern: claim, supporting data, sentence of interpretation.>

### 3. No catastrophic failures within <n> cycles

| Failure mode being watched | Observed? |
|---|---|
| App crash | no |
| Process killed by Low Memory Killer | no |
| Black surface / video failure to render | no |
| `BadTokenException` / WindowManager exhaustion | no |
| `MediaDrm` session pool exhaustion | no (DRM flat at <n>) |
| Codec / GraphicBuffer pool exhaustion | no |

---

## Side-by-side per-cycle delta

| Metric | <prior version> | <prior version> | <this version> | Verdict |
|---|---|---|---|---|
| `MediaDrm` session retention | <slope> | <slope> | <slope> | <fixed/unchanged/regressed> |
| `Activities` (Java) | <slope> | <slope> | <slope> | <fixed/unchanged/regressed> |
| Views | <slope> | <slope> | <slope> | <fixed/unchanged/regressed> |
| AppContexts | <slope> | <slope> | <slope> | <fixed/unchanged/regressed> |
| Native heap | <slope> MB/cycle | <slope> MB/cycle | <slope> MB/cycle | <verdict> |
| PSS | <slope> MB/cycle | <slope> MB/cycle | <slope> MB/cycle | <verdict> |

Slopes computed across C2 → final cycle. Note hardware in column header if comparing
across devices — slopes are comparable but absolute baselines are not.

---

## Test methodology

<Carry forward unchanged from prior report unless something differed. If parameters
changed (cycle count, play seconds, focus row), call that out explicitly.>

Cold-start via deep link into the <portal> portal, focus parked on a <row> tile,
automated cycle:

1. `KEYCODE_DPAD_CENTER` (open Detail), 4 s settle.
2. `KEYCODE_DPAD_CENTER` (Watch Now).
3. Sleep <play-seconds> while video plays.
4. `KEYCODE_BACK` (player → Detail), 3 s settle.
5. `KEYCODE_BACK` (Detail → catalog), 5 s GC settle.
6. Capture meminfo + activity stack + `media.resource_manager`.
7. `KEYCODE_DPAD_RIGHT × 5` to advance to a different title.

Captured commands per checkpoint:

```
adb shell dumpsys meminfo <package>
adb shell dumpsys activity activities
adb shell dumpsys media.resource_manager
```

Test runner: `runner.sh` in the same folder.

---

## Interpretation

<Root-cause hypothesis. What's the prime suspect for any residual growth, given the
PSS-vs-Native attribution? What does this version specifically improve or fail to
improve? What's the cheapest next experiment — typically LeakCanary on a debug build
or an extended-duration run.>

<If hardware caveats apply — e.g., this was on Streamer but production runs on PDi —
call them out. If the slope here doesn't necessarily prove the field issue is fixed,
say so explicitly.>
````

## Tone

Plain language, no marketing voice. State what is, then what it means. Numbers in
tables, claims in prose. "Fixed" and "unchanged" and "regressed" are the only verdict
words — don't say "improved" or "better" without quantifying.

If a result is good, say it plainly. If a result is bad or ambiguous, say that
plainly too. The audience for this report includes the team that wrote the leak.

## Common pitfalls

- Don't pad the report with throat-clearing introductions or "as we know" sentences.
- Don't include a section saying "what we tested" twice — methodology is one section.
- Don't claim a fix is verified on production hardware if the run was on a test bench.
  Always note hardware explicitly and recommend a re-run on production hardware if
  applicable.
- Don't compute slopes from C1. Always C2 onward.
- Don't include screenshots unless the user asks. Tables and slopes are the artifacts.
