# App Presets

Per-app specifics — package names, deep link schemes, segment IDs, and focus-row hints.
Use these when the user mentions an app by name or asks "the usual EaselTV test."

## EaselTV

The legacy outsourced patient entertainment app (`com.swank.android`). Currently in
production. Active leak-fix campaign — recent versions are 3.18.0, 3.18.2, 3.18.3, 3.18.4.

| Field | Value |
|---|---|
| Package | `com.swank.android` |
| Repo | (third-party — Falcon Heavy / EaselTV) |
| Deep link scheme | `swank://` (legacy) |
| Player tech | ExoPlayer 2 (end-of-life — Media3 migration planned) |
| DRM | Widevine via ExoPlayer 2 + Mux Data analytics |

### Portal segment IDs (shared with Prism)

| Portal | Segment ID |
|---|---|
| General | `a51dde65-6e7f-4292-a71b-36ee52ab7dc1` |
| Pediatric | `4ef22f6c-18ac-4fe9-8792-1519b61e0821` |
| Teen | `19313dc2-d3fb-435d-8a53-86b02ce4ba38` |

### Cold-start command (Pediatric portal example)

```bash
adb shell am start -a android.intent.action.VIEW \
  -d "swank://?segmentIds=4ef22f6c-18ac-4fe9-8792-1519b61e0821" \
  com.swank.android
```

If `swank://` doesn't work on the build under test, the EaselTV launcher may use a
different scheme — ask the user. The exact scheme has changed across EaselTV versions
and the user knows which one matches the build they're testing.

### Reference run methodology

For comparability with prior 3.18.x runs:
- **Portal:** Pediatric
- **Focus row:** Vooks
- **Cycles:** 7 (≈ 13 min)
- **Play seconds:** 90
- Hardware to call out in report: PDi A24C2 (Android 11, 1.5 GB) is the production
  fleet device. Google TV Streamer (Android 14, 4 GB) is the office test bench.

### Known leak history

Use this when interpreting new results. The "what was fixed" column tells you what to
expect to be flat in the next version, vs the baseline shape that was bad.

| Version | Per-cycle Activity slope | Per-cycle DRM slope | What was fixed |
|---|---|---|---|
| 3.18.0 | +1 | +1 | nothing — original baseline |
| 3.18.2 | +1 | 0 | MediaDrm.release() fix (Mux side) |
| 3.18.3 | +1 | 0 | re-test of 3.18.2 — no further changes |
| 3.18.4 | 0 (flat from C2) | 0 | Activity / View / AppContext retention fixed (analytics-side GC roots) |

Remaining suspects post-3.18.4: native heap +3.7 MB/cycle from off-heap codec / cache
allocations. ExoPlayer 2's `DefaultLoadControl.Allocator` pool, `SimpleCache` ownership,
and Mux Data SDK native side are the prime suspects. The team is migrating to Media3,
which should help (active maintenance + several Allocator-trim fixes in 1.x).

## Prism (Patient Entertainment Redone)

The in-house KMP rewrite. `com.swank.patient` Android side (KMP shared module + Compose
for TV).

| Field | Value |
|---|---|
| Package | `com.swank.patient` |
| Repo | `~/projects/android/PatientEntertainmentRedone` (Azure DevOps `Sandbox/android-pe-internal`) |
| Deep link scheme | `swankpatient://app/?segmentIds=...` |
| Player tech | Media3 / ExoPlayer 1.5.1 |
| DRM | Widevine via Media3 |

### Cold-start command (Pediatric portal example)

```bash
adb shell am start -a android.intent.action.VIEW \
  -d "swankpatient://app/?segmentIds=4ef22f6c-18ac-4fe9-8792-1519b61e0821" \
  com.swank.patient
```

### Sanity-check expectation

Prism is on Media3 1.5.1 with a clean single-Player-per-Activity architecture and
should show flat slopes on Activities / Views / AppContexts / DRM out of the box. If
slopes are non-zero on Prism, that's a real new bug in Prism — not a known issue.

Native heap slope on Prism is unknown until measured. The Media3 `DefaultLoadControl`
pool sizing means a small steady-state native heap is expected, but it should plateau
quickly. Worth running a 30-cycle extended test on Prism to establish a baseline.

## Adding a new app

If the user wants to test something other than EaselTV / Prism, you need three things
from them:

1. Package name (`adb shell pm list packages | grep <hint>` if they're not sure)
2. Deep link command (or "I'll cold-start manually")
3. Which row / starting tile to park focus on

Don't invent these — ask. The wrong package name silently produces empty dumps and the
runner will record zeros across the board.
