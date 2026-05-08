# Interpreting the metrics

This is the part of the workflow that's easy to get wrong. The CSV is mechanical;
the analysis is judgment.

## What each metric is

The runner pulls six numbers per cycle from three `dumpsys` commands:

| CSV column | Source | What it actually counts |
|---|---|---|
| `activities` | `dumpsys meminfo` "Activities:" | `ActivityThread.mActivities.size()` — Java Activity instances retained on heap, regardless of whether AMS still considers them live. This is the leak-detection metric, not the AMS-visible activity stack. |
| `views` | `dumpsys meminfo` "Views:" | Live View instances tracked by `WindowManagerGlobal`. Compose-for-TV view trees inflate this fast; +37/cycle on EaselTV 3.18.3 was the entire Detail page tree being pinned. |
| `appcontexts` | `dumpsys meminfo` "AppContexts:" | `Application` and `ContextWrapper` instances. Analytics listeners (Sentry, Mux) commonly hold these. |
| `native_kb` | `dumpsys meminfo` "Native Heap" | malloc-managed C/C++ memory — codec buffers, bitmaps (since API 26), direct ByteBuffers, OkHttp/Coil pools, libc allocator overhead. |
| `pss_kb` | `dumpsys meminfo` "TOTAL PSS:" | Proportional Set Size — the process's RSS with shared pages divided by their sharer count. The OS-level "what does this process actually cost" number, the one that hits LMK. |
| `drm_active` | `dumpsys media.resource_manager` | Active `drm-session/*` lines for the process. Most chipsets cap MediaDrm sessions at ~10. |

`prodpages`, `players`, `mains` are heuristic regex counts in the activity stack —
informational only. Useful for catching zombie `t-1 f` records on Android 11 (which
the AMS keeps showing even after they're "finished"). Android 14 hides these so the
counts are usually 1/0/1 there even when retention is happening.

## Slope methodology

Compute slopes across **C2 → final cycle**, not C1 → final.

C1 always includes one-time cold-start cost: first network fetches, DRM provisioning,
Compose recomposition of the catalog tree, analytics SDK init, codec warm-up. None of
this is a leak — it's allocation that doesn't return to baseline because it's
load-bearing for the rest of the session.

If you compute the slope from C1 you'll over-attribute leaks. Always start from C2.

If C2 → C7 is bit-for-bit flat (Activities, Views, AppContexts identical across all
five cycles), that's the signature of a fixed leak. Random noise would show ±1
fluctuations cycle-to-cycle.

## PSS vs Native Heap

PSS is the total. Native Heap is one slice of it. The categories that sum to PSS:

- **Native Heap** — malloc/new
- **Dalvik Heap** — Java/Kotlin objects (ART GC)
- **Dalvik Other** — JIT cache, GC bookkeeping
- **Stack** — thread stacks
- **Ashmem** — Android shared memory (IPC, surface buffers)
- **`.so` / `.dex` / `.oat` / `.art` mmap** — code mappings
- **GL mtrack** — GPU memory attributed to the process
- **Unknown** — pages the kernel can't categorize

**PSS minus Native Heap** tells you where growth is.

- If both PSS and Native grow at the same rate → leak is in malloc (codec / cache /
  third-party native side).
- If PSS grows but Native is flat → leak is in Java heap (Dalvik), GL surfaces, or
  ashmem regions.
- If Native is flat AND PSS is flat → no real growth, congratulations.

In our data: 3.18.4 had PSS Δ ≈ Native Δ ≈ +18 MB across C2→C7. That's clean
attribution: the residual is entirely native, nothing in Java/GL/ashmem.

## Java GC and native heap

Common confusion: "won't the GC collect that native growth?"

Java GC doesn't free native memory directly, but most large native allocations are
*owned* by a Java wrapper (`Bitmap`, `ByteBuffer.allocateDirect`, `MediaCodec`,
`MediaPlayer`, etc.). When the wrapper becomes unreachable and a `Cleaner` /
`PhantomReference` / finalizer fires, the cleanup function frees the C++ memory.

So:

| Native allocation | Reclaimed by Java GC? |
|---|---|
| Codec buffers (post-`MediaCodec.release()`) | yes |
| Direct ByteBuffers | yes (Cleaner-based) |
| Bitmaps (Coil cache, view holders) | yes — but only after LRU eviction |
| OkHttp / Coil internal pools | bounded internally; doesn't shrink on GC |
| Mux Data native side | depends on impl; partial |
| libc allocator slack (jemalloc/scudo arena fragmentation) | **no** — pages stay in process |

This is why a 4 GB Streamer can show a steady +3.7 MB/cycle slope while a 1.5 GB PDi
running the same APK might self-regulate at the same workload — memory pressure
forces aggressive GC, finalizers fire faster, wrapper-owned native gets freed faster.
The constrained device is sometimes the better-behaved device.

## Install strategy

Two choices:

**`adb install -r <apk>`** (default) — re-install over data. Preserves prior runs'
shared prefs, OAuth tokens, device-registration state, image / HLS disk caches. Use
this for like-for-like comparison against the previous version's baseline. Avoids
first-cold-start anomalies (re-registration, full DRM provisioning, full catalog
warm-up) which would distort C1.

**`adb uninstall <pkg>` + `adb install <apk>`** (clean) — fresh install, no carry-over.
Use this when you want to verify a fix actually flushed prior version's persisted state
(e.g., "did the analytics fix actually clear out queued breadcrumbs, or is it just
suppressing them?"). Also use after a long break between runs where stale state could
have accumulated.

Default to `-r`. Switch to clean install when the user has a specific reason. Don't
silently change between runs in a comparison series — the install strategy needs to
match the prior runs you're comparing against.

## Hardware caveats

The same APK behaves differently on different hardware. Always note device + Android
version in the report header.

| Device | Android | RAM | Behavior |
|---|---|---|---|
| Google TV Streamer | 14 | 4 GB | Heavy framework overhead (PSS baseline ~190 MB), hides zombie `t-1 f` activity records, GC rarely runs under 4 GB headroom — leaks accumulate |
| PDi A24C2 | 11 | 1.5 GB | Lower framework baseline, AMS exposes zombie `t-1 f` records explicitly, aggressive memory pressure forces GC + finalizers — sometimes self-regulates |
| Amino Aria | 9 | varies | Older Android — different LMK heuristics |

A clean run on the Streamer is necessary but not sufficient. Field issues are typically
reported on the production fleet hardware (PDi). When the user says "nurses are
rebooting TVs," they mean PDi-class hardware. Re-run on real hardware before declaring
a fix verified.

## Failure modes worth watching

The runner doesn't detect these — you have to read the dumps if anything looks wrong.

| Failure | Where it shows up |
|---|---|
| App crashed mid-cycle | `act_*.txt` won't show the package's process; PSS dump will be empty |
| LMK kill | `dmesg` (not captured by default) — sudden PSS drop from Cn to Cn+1 with the package returning to a fresh state |
| MediaDrm pool exhaustion | `drm_active` keeps climbing past 5–6, eventually playback fails |
| Surface render failure | Not visible in dumps — visible on screen as black box during play |
| BadTokenException / WindowManager exhaustion | Logcat — not captured by default |
| Codec / GraphicBuffer pool exhaustion | GL mtrack section in `mem_*.txt` climbs unboundedly |

If the user reports "TV reboots itself," that's worse than LMK (Android would just
relaunch the app). It implies framework state corruption, surface render failure, or
DRM exhaustion. Cross-reference the user's symptom with these failure modes when
interpreting.
