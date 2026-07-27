# Guya — Feature Backlog & Roadmap
*v16.50 · 27 Jul 2026 — FLATS LAYER PHASE A+B SHIPPED for Brisbane River + Sunshine Coast.
Build `2026.07.27a`. Moreton Bay deliberately NOT in this build — see "next job".

**Empirical band boundaries computed and adopted (the v16.49.7 refinement note, now resolved).**
Reconstructed each port's curve from the embedded table using the SAME cosine interpolation
`tideHeightNow()` uses (no second tide model), sampled at 1-min steps, took the heights below which
the tide sits 1/3 and 2/3 of the time:
| Port | H1 (⅓ below) | H2 (⅔ below) | idealised 25% | idealised 75% |
|---|---|---|---|---|
| Brisbane Bar | **1.002 m** | **1.653 m** | 0.703 m | 2.107 m (−0.455) |
| Mooloolaba | **0.775 m** | **1.234 m** | 0.560 m | 1.680 m (−0.446) |
| Burnett Heads | **1.407 m** | **2.176 m** | 0.925 m | 2.775 m (−0.599) |
Burnett Heads is computed for completeness only — Woongarra stays bathymetric and never bands.
- **The divergence from the idealised figures is large, and is NOT a bug** (the build brief predicted
  it would be small and called a big gap a bug — that prediction was wrong). The height-quartile ==
  equal-tidal-time identity holds *only* for a symmetric sinusoid spanning the full LAT–HAT range.
  Real tides carry diurnal inequality **and never reach either bound** — Brisbane Bar's 2026 range is
  0.23–2.79 m against a 0–2.81 m span, so HAT/LAT are rare astronomical envelopes, not the operating
  range. Tide-time therefore concentrates far more tightly around mid-range than the idealised model
  assumes. Confirmed not a rival tide model: interpolation matches `tideHeightNow()` exactly.
- **Idealised was rejected on evidence, not preference:** it collapses teal to 5.7% (BR) / 0.5% (SC)
  of painted points, making "dries only near low tide" effectively invisible — the exact failure the
  v16.49.7 refinement note was written to prevent.

**Phase A — two REPLACE CSVs generated, ready for Aaron's phone-side import:**
| CSV | Source | Written | Dropped >HAT | gold / amber / teal / blue |
|---|---|---|---|---|
| `data/brisbane_river_flats_v1.csv` | `brisbane_river_intertidal_ground_v2.csv` (189,187) | **68,591** (1.92 MB) | 120,596 (63.7%) | 33,865 / 17,617 / 17,107 / **2** |
| `data/sunshine_coast_flats_v1.csv` | `sunshine_coast_intertidal_ground_v2.csv` (168,461) | **57,565** (1.61 MB) | 110,896 (65.8%) | 41,576 / 12,855 / 3,134 / **0** |
- Both go in as **REPLACE** (MERGE cannot remove the existing mislabelled "depth" data).
- CSVs stay `lat,lng,depth` — the exact 3-column shape the existing parser consumes. Banding is
  applied as a **data drop only** (above-HAT points removed); colour bands resolve at render time
  from the constants above, so the boundaries stay ONE source of truth in code and never need a
  re-import if they are ever retuned. The roadmap's own spec permits this ("bake-time **or
  load-time**"), so this is within design, not a deviation.
- Existing import-time auto-thin (`MAXP=25000`) handles device sizing — no new decimation logic. Net
  effect is a real quality win: thinning now selects from genuinely intertidal points instead of
  diluting them with ~64% dry land.
- **Caught by cross-checking the JS banding against the Python export:** port must be resolved
  **per point** via `nearestPort()`, not per region. **24,584 of Sunshine Coast's 168,461 source rows
  (14.6%) sit closer to Brisbane Bar than to Mooloolaba**, and the app's `okHAT` gate already routes
  per point. *(Figure corrected — the originally-committed "9,183" was not the geometric count but
  the number of those rows that SURVIVE the above-HAT drop under per-point routing; an earlier
  in-session "5,526" was the same survivor count under the buggy uniform HAT 2.24. Their difference,
  9,183 − 5,526 = 3,657, is exactly the recovered-point figure below, which confirms both were
  survivor counts rather than a contradiction.)* A first pass
  using a region-wide HAT 2.24 wrongly dropped **3,657 points** of SC's southern tail and mis-banded
  the rest. Regenerated with per-point routing; JS and Python now agree exactly on both regions.

**Phase B — renderer (`index.html`, build `2026.07.27a`):**
- **`source_type` region metadata pulled forward** (Future-proofing item 6) — `REGION_SOURCE` +
  `regionSourceType()`. Defaults: Woongarra / Maroochy-Noosa / legacy = `bathymetric`; Brisbane
  River / Sunshine Coast / Moreton Bay = `topographic`. Datasets stored before this build carry no
  field and are defaulted by region key — migrated, never orphaned. Stamped onto every new import.
- **New region:** Moreton Bay / Redcliffe added to the import picker + `regionLabel()`, ready for its
  CSV.
- **Renderer:** `buildShade()` carries the nearest sample's source_type through the existing IDW loop
  (`nearST`, one assignment inside the existing `dist<near` branch — no extra pass, no new cost) into
  a per-pixel `ST` mask; topographic pixels paint `flatsColor()` instead of `depthColor()`.
  Per-pixel rather than per-region so it stays correct for custom regions and overlapping data.
- **HAT land-overpaint confirmed already present and NOT duplicated** — `depthSamples()`'s `okHAT`
  gate (v16.44) removes above-HAT points upstream, so the renderer needs no second suppression rule.
- **Tap-to-read removed for topographic regions, numeric readout gone entirely** — both the tap popup
  and the hover readout. Zone taps still surface full zone classification (non-negotiable rule 1) and
  now show band wording instead of a figure; a bare map tap over topographic data opens nothing. The
  "Deepest within 100 m" button is unreachable there by construction.
- **Safety label shipped** in the Imported-depths panel, stating verbatim that HAT is an
  astronomical-tide ceiling only — excludes storm surge, barometric setup, and Brisbane River flood
  stage — and that "dries earliest" is never a flood, depth or safety claim.
- Validated: `node --check` PASS on both script blocks; inlined Leaflet block **byte-identical**
  (sha256 verified against HEAD); `zoneAt()` most-protective ordering and the green-zone dragend
  re-check both intact.

**Corrections folded in this session (stale facts, now fixed):**
1. Above-HAT figures were "63% SC / 74% BR" — **flipped and wrong**; real v2 figures are 65.8% SC /
   63.7% BR.
2. Below-LAT count cited deleted v1 ("2 of 209,540") — now **2 of BR's 189,187, 0 of SC's 168,461**.
3. Tide tables are **2026 only (365 days)**, not "2026–2027" as claimed in the roadmap and the build
   brief. Percentile maths unaffected; provenance claim corrected.
4. Recorded why empirical and idealised genuinely diverge (above) rather than leaving it as an
   unexplained mismatch.
5. CLAUDE.md's two stale domain facts fixed in commit `27f116b` (ELVIS depth-source, tide ports).

**NEXT JOB — Moreton Bay / Redcliffe Phase A (its own session; long-run).** Discovery done: the
delivery was never missing, it is **193 unique tiles** (93× `MoretonBay_2014_LGA`, 100×
`Moreton_Bay_2018_LGA`), MGA56 E505000–519000 / N6976000–7021000, inside five `DATA_*.zip` archives
**misfiled** under `data/raw/Sunshine-Coast/` and `data/raw/Brisbane-River/` (110.6 GB total, which
also contains non-Moreton tiles). Pending cleanup: same-volume rename into `data/raw/Moreton-Bay/`
before the run. This delivery has **never** had the class-9-adjacency density check (v16.17–v16.18)
run on it — mandatory, drop flagged points, never reclassify. >100 tiles and multi-hour, so LONG-RUN
DISCIPLINE is confirmed required: smoke test on a small subset first, progress print every N tiles
with flush, atomic checkpoint every N, resume-from-checkpoint, real PID reported. Reuse the exact
banding + renderer logic already proven here — Brisbane Bar port, no drift. Output: one new-region
**MERGE** CSV (`moreton_bay`, source_type already wired).

**Also still open (unchanged):** the v16.49.6 guarded legacy-`woongarra_imported_v1` delete button
was never exercised — the ~519 KB legacy key may still be on-phone. Cheap, one-tap, no urgency.*

---

*v16.49.7 · 27 Jul 2026 — ON-DEVICE GATE CLEARED + FLATS LAYER DESIGN LOCKED. No code shipped
(build stays `2026.07.25c`); this entry closes the v16.49.5 gate and settles the flats-layer
spec that gate was blocking.

**GATE CLEARED — all three write-then-mutate fixes (MERGE/REPLACE/restore, v16.49.5) verified
on real quota failures, on-device, not simulated.** Two throwaway fixtures (v16.49.6 tooling)
used to force genuine `QuotaExceededError`s against a 150 KB reservation:
- **REPLACE** (`quota_test_dummy_12k.csv`, 12,000 pts, sentinel 199.9 m, ~327 KiB): failed
  cleanly against a brand-new region ("Smoke") that had never existed — in-app log confirmed
  "12000 new points (0 total in Smoke). Save verification FAILED... nothing changed, the
  previous data was kept." No phantom region created, not even at 0 pts.
- **Positive control, run before trusting any "no data" result:** confirmed tap-to-read
  genuinely queries the live interpolated pool, not a stub — a tap near Coral Reef Pk returned
  "Est. depth here ≈6.4 m... now ~7.6 m water (tide +1.2)... nearest data 30 m away," the full
  interpolation pipeline demonstrably running, not silently short-circuited.
- **MERGE** (same fixture, merged into "Smoke02" which already held 12 legitimate points from
  `guya_baseline_test.csv`): failed cleanly — panel count stayed at 12, never touched 12,012;
  same status-line pattern, same banner.
- **Restore** (`quota_test_dummy_backup.json`, ~9.72 MiB, ~2× the ~4.75 MB cap, sized
  absolute-vs-cap per the v16.49.6 sizing-confusion note): failed cleanly with the
  restore-specific banner text confirmed present verbatim — "Backup restore of imported depths
  did not persist — storage may be full. Your previously loaded depths are unchanged..." —
  distinct from the generic MERGE/REPLACE wording, confirming the fix's own error path fired
  rather than a stale leftover banner.
- **Force-close/reopen:** confirmed no residue from any of the three failed attempts; real pool
  intact throughout at 113,569 (113,557 + Smoke02's 12) until Smoke02 was removed in cleanup,
  dropping it back to 113,557.
- **Cleanup completed:** storage reservation cleared (back to NORMAL MODE), Smoke02 region
  deleted, both dummy fixtures deleted from the phone. Safety backup taken before testing
  retained, unused.
- **GATE STATUS: CLEARED.** The import-path durability arc (v16.49.5) is now fully verified,
  not just harness-proven. **The flats layer is UNBLOCKED on both fronts** — design (below) and
  import-path safety (this gate).

**OPEN, NOT DONE THIS SESSION:** the v16.49.6 guarded legacy-`woongarra_imported_v1` delete
button was never exercised — the ~519 KB legacy key may still be present on-phone. Cheap,
one-tap, no urgency. Also still open from v16.49.4/.5: the two stale CLAUDE.md domain facts
(ELVIS-as-depth-source line, tide-port line omitting Mooloolaba/Noosa) — FIXED this session
(commit 27f116b): ELVIS-as-depth-source line now distinguishes bathymetric (Bargara/Woongarra,
Maroochy/Noosa) from topographic NIR (BR/SC/Moreton); tide-port line now lists all four ports
(Burnett Heads, Brisbane Bar, Mooloolaba, Noosa Head).

**FLATS LAYER — full design locked, ready to scope for a build session.**
- **Scope, confirmed exclusive:** Sunshine Coast (the topographic-NIR delivery only —
  Maroochy/Noosa's real 2011 Fugro bathymetric survey is untouched and keeps genuine depth
  shading), Brisbane River, Moreton Bay/Redcliffe. Bargara/Woongarra unaffected.
- **No live/dynamic repaint.** A tide-driven runtime recolour was scoped and explicitly
  rejected as unnecessary cost — the design is a static, one-time per-point classification,
  computed once (bake-time or load-time), no ongoing tide dependency. Reuses the existing
  per-port `PORTS[].hat` constant already built and validated for the land-overpaint gate
  (Burnett Heads 3.70 m, Brisbane Bar 2.81 m, Mooloolaba 2.24 m) and the existing LAT=0 storage
  datum — zero new sourcing for either outer bound.
- **Tap-to-read removed for this layer.** No numeric answer is ever shown (hard constraint,
  below), so a tap adds nothing the shading itself doesn't already convey — cut from spec.
- **FINAL DESIGN — 4 bands, deliberately exceeding the standing "three-state at most" hard
  constraint** (carried since the v14b DEA evaluation, reaffirmed for this delivery). **Aaron's
  explicit, on-record override — not a drift, a decision:**
  - Above HAT: not painted (dry land) — alone removes **65.8% of Sunshine Coast points and 63.7%
    of Brisbane River points** from the layer, a genuine visual simplification, not just a rule.
    *(Corrected v16.50: the previously-recorded "63% SC / 74% BR" was wrong on both counts — the
    figures were flipped AND the BR number was never reproducible. Old figures came from on-phone
    already-thinned counts; these are measured directly against the v2 files. SC's 65.8% is with
    per-point `nearestPort()` routing, matching what the app's okHAT gate actually does — a single
    region-wide HAT 2.24 would read 68.0% and wrongly discard SC's southern tail, see v16.50.)*
  - **Band 1 (gold `#EF9F27`)** — HAT down to the 75%-of-range mark: dries earliest.
  - **Band 2 (amber `#BA7517`)** — 75%-mark down to the 25%-mark: dries by roughly half tide.
  - **Band 3 (teal `#1D9E75`)** — 25%-mark down to LAT: dries only near low tide.
  - **Band 4 (blue `#378ADD`)** — strictly below true LAT: always covered. **Structurally
    near-empty for this delivery** — NIR can't see underwater, so almost nothing in the source
    data sits at or below LAT (**2 of Brisbane River's 189,187; 0 of Sunshine Coast's 168,461** —
    v2 denominators; the old "2 of 209,540" cited the deleted, classifier-fault-contaminated v1).
    Band 4 is therefore genuinely empty on SC and 2 px on BR. Will render mostly
    blank, correctly — not a bug, matches the existing "no survey data" honesty elsewhere.
  - **SUPERSEDED by v16.50 — see empirical figures above; the 75%/25% idealised numbers below were
    not what shipped.** (Applies to the Band 1/2/3 bullets above as well: their "75%-of-range mark"
    and "25%-mark" wording is the idealised scheme, not the empirical boundaries that shipped.)
  - **Boundary math validated, not guessed:** for a 3-band split, the boundaries that give each
    band an equal SHARE OF TIDAL TIME — accounting for the tide's real non-linear speed (slow
    near the extremes, fast through the middle, the same relationship behind the classic Rule of
    Twelfths) — work out to be numerically identical to the simple 75%/25% height-quartiles of
    the HAT–LAT range. Worked example, Brisbane Bar (HAT 2.81 m, LAT 0): boundaries at **2.11 m**
    and **0.70 m**.
  - **Refinement flagged for the build session, not resolved here:** the 75%/25% figures above
    assume an idealised symmetric tide curve. The real embedded per-port tables (**2026 only —
    365 days, `2026-01-01`..`2026-12-31`; the long-standing "2026–2027" claim is wrong, corrected
    v16.50**, and repeated in the v16.50 build brief) carry genuine diurnal inequality — compute the
    true empirical 1/3 and 2/3 time-split points from the real tables per port instead of the
    idealised assumption. One year still spans every spring/neap and seasonal cycle, so the
    percentile computation stands unaffected — only the provenance claim was wrong. No new
    sourcing, materially more accurate, cheap to add. **Done in v16.50.**
  - **Colour scheme:** warm→cool 4-stop spectrum, gold → amber → teal → blue, confirmed liked.
  - **Hard safety caveat, unchanged and still binding:** HAT is an astronomical-tide ceiling
    only — no storm surge, no barometric setup, and critically **no river flood stage**, given
    Brisbane River is one of the three regions. Label must state this explicitly; "dries
    earliest" must never read as a flood or safety claim.
- **Renderer implication:** needs a way to recognise "this is a flats-layer dataset" and paint
  from the fixed 4-colour palette instead of the continuous depth gradient. Recommend pulling
  forward the already-backlogged **`source_type` tag** (bathymetric / topographic / sonar —
  Future-proofing item 6, SEQUENCE list) into this build rather than treating it as separate
  later work — this is the first feature that actually needs it to render correctly.
- **Logged, not acted on:** Aaron wants to revisit the normal-depth-shading colour ramp at some
  point — unrelated to this build, its own future item.

**NEXT BUILD — unchanged in sequence position (item 1), now spec-complete rather than an open
design question.** Ready to scope for a dedicated Claude Code session per the existing
"expensive — clean session" flag; not yet dispatched.*

---

*v16.49.6 · 26 Jul 2026 — ON-DEVICE GATE TOOLING, no index.html change. storage_check.html gained a
headroom reserve/clear utility + a guarded legacy-`woongarra_imported_v1` delete (commit 7b0fcf0).
Two throwaway quota-gate test fixtures generated for Aaron to AirDrop — NOT committed (local-only via
`.git/info/exclude`, disposable): `quota_test_dummy_12k.csv` (12,000 pts, sentinel depth 199.9 m,
~327 KiB stored — for MERGE/REPLACE failure) and `quota_test_dummy_backup.json` (well-formed version:2
backup carrying one ~9.72 MiB fake `quota_test_dummy` region, ~2.05× the ~4.75 MB cap — for restore
failure).

**⚠ SIZING CONFUSION POINT — "replace" means two different scopes; do not reuse one's sizing logic for
the other.** REPLACE (CSV import, `imp-replace-btn`) is **region-scoped**: it swaps ONE region inside
`datasets`, so its stored-size delta is just that region's growth vs whatever that region held before —
a small file grows the store by a small amount, and it fails quota only if that delta exceeds free
headroom. Backup-restore (`importBackup`) is **whole-store-scoped**: `datasets=newDatasets` swaps ALL
of `datasets` in a single `trySaveDatasetsObj` write, so success/failure depends on the fake region's
ABSOLUTE size against the total container cap, NOT a delta against current holdings. Consequence that
bit the fixture sizing: a 335 KB "backup" can never fail on a device already holding ~3 MB of imports,
because replacing 3 MB with 335 KB net-frees space. Hence Fixture 2 is sized oversized-beyond-cap
(~9.7 MiB, ~2× cap) so it fails outright regardless of current pool size and needs no reservation —
and because the write throws BEFORE `datasets=newDatasets` runs, the real imported pool is provably
never clobbered by the test. A future session must NOT size a restore-failure test as "current pool +
delta" (REPLACE's logic); use absolute-vs-cap.*

*v16.49.5 · 25 Jul 2026 — IMPORT-PATH DURABILITY ARC. Three code fixes shipped this session
(builds 2026.07.25a → .25c) plus docs/data housekeeping. The whole import persistence path
(MERGE / REPLACE / backup-restore) now writes-then-mutates. **NOT YET ON-DEVICE VERIFIED — this
carries the same gate status the r0/pool cache had before v16.49.3 cleared it (see below).***

**WHAT SHIPPED THIS SESSION (in order):**
1. **Docs commit `8dd6e9e`** — CLAUDE.md repo-rename fix (`Guya` → `Guya_Wamu`, live URL, remote-
   check hint, build-string-format `2026.MM.DDa` + no-collision rule) and roadmap catch-up to
   v16.49.4. No code.
2. **v1 CSV removal `bb8efce`** — `git rm data/brisbane_river_intertidal_ground_v1.csv` and
   `data/sunshine_coast_intertidal_ground_v1.csv`. These were the PRE-drop-mask sets, superseded
   by the v2 CSVs at `ef9385d` (11 Jul, "Drop-mask v2 CSVs") which applied the 44,427-cell
   classifier-fault mask (BR 209,540 → 189,187; SC 188,855 → 168,461). v1 is
   classifier-fault-contaminated and should not remain in the repo. They were already absent from
   disk (out-of-band deletion); this formalised it in git. v2 CSVs untouched and remain the source.
3. **UI-BUG-1/2 fix `2b6822f`** (build 2026.07.25a) — see v16.49.4 entry below. Stray `.keep` class.
4. **MERGE/REPLACE write-then-mutate fix `b26c959`** (build 2026.07.25b) — the v16.49.2/.4
   diagnostic (import quota failure leaves phantom in-memory points) resolved. Both actions now
   build a candidate datasets object, `trySaveDatasetsObj(candidate)` FIRST, and only touch live
   `datasets`/`imported`/`poolVersion` + snapshot-for-Undo on verified success. Harness proof
   (verbatim source sliced into a vm context, `setItem` forced to throw): on failure poolVersion,
   imported.length, panel count, live datasets, and the persisted copy all stay at pre-attempt
   state, and the phantom point is not in `depthSamples()`; success path unaffected. Failure status
   line changed from "do not trust this import yet" to "nothing changed, the previous data was kept."
5. **Backup-restore write-then-mutate fix `36b16ec`** (build 2026.07.25c) — the restore-path
   FINDING surfaced during v16.49.4 verification (grep found a 4th `saveDatasetsVerified()` caller
   at what was line 2482). Unlike undo/clear-all/remove-region (which shrink or restore-previously-
   fit, so quota-safe), backup-restore GROWS storage with an arbitrary backup and was mutate-then-
   save with a **silent console.warn** on failure — same phantom bug class, confirmed by harness
   (the 88.8 m point case). Now `trySaveDatasetsObj(newDatasets)` first, mutate only on success,
   and the silent warn upgraded to a `showImpError()` banner. Harness proof: forced-throw restore
   leaves poolVersion/live datasets/panel/persisted store at pre-restore state, 88.8 m point not
   tap-readable, banner raised; no-throw success path still applies and persists. The line-2186
   comment was corrected to name both disciplines (write-then-mutate vs mutate-then-save) and warn
   against adding a storage-growing caller to the mutate-then-save group.

**⚠ GATE — NOT YET ON-DEVICE VERIFIED. The import-path arc must clear an on-device gate before the
flats layer proceeds, exactly as v16.49's pool cache did.** All three code fixes (`2b6822f`,
`b26c959`, `36b16ec`) are proven by desktop Node/vm harness only. Per the standing rule that bit the
r0-cache arc, a desktop proof of a persistence/cache invariant is NOT device-representative: iOS
WebKit's localStorage container hits quota at a different (lower) ceiling and flushes to disk async,
and the harness stubs `setItem` rather than exercising the real WebKit storage area. **On-device
checklist (Aaron, before the flats layer goes near this cache):** force-close/reopen, confirm build
`2026.07.25c`, then (1) MERGE a file large enough to hit real quota into a throwaway region — confirm
the panel count, shading, and tap-read all REVERT to pre-merge (no phantom depth tap-readable) and
the error banner shows; (2) REPLACE-fail the same way; (3) restore a backup larger than the container
holds — confirm the banner appears (not just a console line) and the previously-loaded depths are
intact on reload. Any step where a phantom depth survives the failed write is a fix that didn't hold
on-device. **Until this gate clears, treat the import-path fixes as unverified and do not build the
flats layer on top of this cache.**

*v16.49.4 · 25 Jul 2026 — UI-BUG-1/2 fixed (build 2026.07.25a); import quota-failure diagnostic
answered AT RISK; AusSeabed coverage spike (backlog item b) run and closed out.*

**FIX — UI-BUG-1 and UI-BUG-2, one root cause, not a handler bug.** Both sections' `.lbl` click
binding and section wiring were always correct — every `.blk` in `.panel-body` is bound identically
by the single generic collapse handler. The actual cause: two toggle `<label>`s carried a stray
`class="toggle keep"`, and `.panel-body > .blk.collapsed > label.keep{display:flex!important}` forces
those rows to stay visible regardless of the `.collapsed` class. In **Map layers** all four toggle
rows (zone/FHA/streets/place-names) had `.keep`, so 100% of the section's content stayed visible on
collapse — looked like the header did nothing. In **Fishing spots & catches** only the "Show spots"
row had it, so the rest of the block correctly folded away but that one row stayed pinned open,
reading as "does not collapse." `.keep` was used nowhere else in the app (confirmed by full-file
grep), so removing it from both labels — plus the now-dead `label.keep`/`div.keep` CSS rules — brings
both sections in line with the working ones (Zone legend, Safety, Backup), which never used `.keep`.
Validated: both script blocks pass `node --check`; Leaflet block byte-diffed identical to HEAD;
`zoneAt()` and the green-zone drag safeguard untouched (diff shows only the 4 `.keep`-related lines
changed). Committed alone as `2b6822f`.

**ANSWERED — the v16.49.2 quota-failure diagnostic question: AT RISK, not safe.** Traced the MERGE
handler (`index.html` ~3104-3118): points are pushed into `datasets[region].points` in-memory, then
`rebuildImportedFlat()` (line 2169) rebuilds the flat `imported` pool from `datasets` AND bumps
`poolVersion` — **both happen before** `saveDatasetsVerified()` (line 2175, the function that actually
calls `localStorage.setItem`) is ever invoked at line 3118. `depthSamples()` (line 2254-2255) caches
purely on `poolVersion`, so the moment `rebuildImportedFlat()` bumps it, any tap-read/pan/shade
rebuild serves the merged pool — including points that haven't reached disk yet. If `setItem` then
throws `QuotaExceededError`, `saveDatasetsVerified()` catches it, shows the error banner, and returns
`false`, but it does **not** revert `datasets`, `imported`, or `poolVersion`. `refreshImpPanel()` /
`refreshDatasetList()` (line 2223-2232) read `imported.length` / `datasets[k].points.length` — live
in-memory state, not localStorage — so the panel would show the post-merge (larger) counts too, not
a "clean revert." **This contradicts the v16.49.2 desktop MN-merge note's claim of a clean revert to
103,648/MN 13,705** — that observation was almost certainly taken after a reload (which re-reads
`datasets` from the still-unwritten, pre-merge localStorage and looks like a revert), not from the
live post-failure panel in the same session. Net: until reload, a failed MERGE quota write leaves
tap-read/shading serving phantom un-persisted points — the exact risk v16.49's blast-radius note
flagged. Not fixed this session (read-only per instruction); candidate fix is reordering to
write-then-mutate (attempt `saveDatasetsVerified()` on a scratch/candidate `datasets` state, only
call `rebuildImportedFlat()` on success) or an explicit revert of `datasets[region]`/`rebuildImportedFlat()`
on `saveDatasetsVerified()` returning `false`.

**AusSeabed coverage spike (backlog item b) — run, ~15 min, coverage-index only, nothing downloaded.**
GetCapabilities on `warehouse.ausseabed.gov.au` WFS 1.1.0 identified the Compilations Coverage layer
as `ausseabed:MARINEDATAREGISTER_COMPILATIONS_INDEX`. `DefaultSRS` is the URN form
(`urn:x-ogc:def:crs:EPSG:4326`), so BBOX axis order is lat,lon — queried
`-28.2,152.3,-24.7,153.7` (Bargara to the NSW border) and got 8 features back, no pagination
truncation. **None of the 8 are SEQ-specific** — coverage over Bargara/Woongarra, Moreton
Bay/Redcliffe/Bribie/Pumicestone, Sunshine Coast/Maroochy/Noosa, and Brisbane River all comes only
from four national/continental compilations (AusBathyTopo Australia 2024 & 2023, Australian
Bathymetry & Topography 2009 — all 250 m; Multibeam Compilation of Australia 2018 — 50 m). The
nearest geographically-targeted feature is "Gold Coast Satellite-derived Bathymetry 2018" (EOMAP,
individual survey), which sits south of Moreton Bay/Brisbane River mouth and doesn't reach into any
of the four regions. Implication for the terrain/bathymetry pipeline ([[ELVIS]] remains the feeds for
depth shading per CLAUDE.md): AusSeabed has nothing finer-grained than 50 m national for this coast —
not a usable source for anything the app currently needs at higher resolution. Backlog item (b) is
now answered and can be dropped from the low-priority list.

---

*v16.49.3 · 25 Jul 2026 — ON-PHONE INVALIDATION GATE CLEARED. v16.49 pool cache confirmed correct
on device (build 2026.07.24a). No code shipped; this closes the gate that has blocked the next
build since the r0-cache arc.

Ran the REPLACE -> MERGE -> remove sequence on both desktop Chrome and the iOS home-screen PWA using
the offshore smoketest CSVs (12 + 6 pts, ~1.5 km E of Bargara, 188 m min spacing, distinctive
depths: file1 whole numbers 10-25 m, file2 .5 values 20.5-30.5 m). Results:
 - REPLACE (file1): tap-read served the imported values. PASS.
 - MERGE (file2): count 18, tap-read served the .5 values -> cache rebuilt to the merged set, not
   stale. PASS.
 - REMOVE (the load-bearing v16.49 check — a stale pool serving PHANTOM points that no longer exist
   is the failure mode the whole gate exists for): after delete, tap returns "no survey data here",
   not a cached depth. PASS.
 - DURABILITY (iOS async localStorage flush — a write that succeeds in-session but never reaches
   disk; structurally invisible on desktop): import persisted across force-close/reopen; deletion
   persisted after reopen. This device's write path flushes to disk. PASS.
 - COLLATERAL: zone popups (GUZ07 etc.) stayed hard-rule compliant throughout (zone type + ID +
   not-authoritative warning + official link, no legality assertion) -> zoneAt() untouched by the
   v16.49 edit, confirmed ON DEVICE not just by diff. Interpolation confidence label tracks
   nearest-data distance correctly (low-confidence at 98 m, none flagged at 14 m).
 - REAL POOL UNTOUCHED: smoketest went into a scoped "Smoke test" region via REPLACE, so
   legacy/BR/SC/MN were never mutated; removing the region left the real store intact. No backup
   restore was needed.

**GATE STATUS: the "on-phone confirmation gate required before the next build" (open since the
r0-cache arc) is CLOSED. The flats layer (next build item) is UNBLOCKED.**

Belt-and-braces residual (not a blocker): the airtight deletion-durability proof is a reopen AFTER
a delete showing it stayed gone. The import-survives-reopen result already proves this device
flushes; one more force-close/reopen after a delete would close it completely if ever wanted.*

*v16.49.2 · 25 Jul 2026 — desktop-session findings, no code shipped. Three items to note plus one
diagnostic question for the next Claude Code read-only spike.*

**UI-BUG-1 — MAP LAYERS section does not collapse.** The MAP LAYERS header carries a "+" affordance
but its toggle list (Marine-park zones / FHA / Streets / Place & creek names) stays expanded when
the header is actioned. Section-specific: ZONE LEGEND, SAFETY — CROCODILES, and BACKUP all collapse
correctly in the same panel, so this is a missing/mis-bound collapse handler on this one section,
not a global regression. Cosmetic, low priority. Reported on desktop; phone parity unverified.

**UI-BUG-2 — FISHING SPOTS & CATCHES ("Show spots") does not collapse.** Same class as UI-BUG-1 —
header present, content (Show spots toggle + count) does not fold away. Same likely cause (handler
binding / section-ID mismatch). Bundle both into one Sonnet fix; a read-only check of the
collapse-handler wiring for these two section IDs should locate it in one pass.

**DESKTOP CONTAINER HAS DIVERGED FROM THE PHONE — desktop is NOT a state mirror.** Desktop pool =
103,648 (legacy 51,224 "woongarra_depth…" + BR 20,794 + SC 17,925 + MN-v1 13,705). Two mismatches
vs the phone's 113,557 stored: legacy differs (51,224 desktop vs 55,660 phone — older/different
legacy import) and MN is v1 (13,705) not v2_appgrade (19,178). Implication: desktop is fine as a
code-LOGIC screen but must NOT be treated as a state mirror of the field device. The phone remains
source of truth.

**QUOTA FAILURE ON DESKTOP MN MERGE — expected, failed SAFE, not a v16.49 issue.** MERGE-ing
maroochy_noosa_bathy_v2_appgrade.csv onto the existing MN-v1 stacked both versions (MERGE cannot
remove v1 — standing MN rule) -> 122,826 pts / ~3.43 MB -> QuotaExceededError on
'woongarra_imported_v2'. Correct op is REPLACE scoped to the MN region (swaps v1->v2, ~109,121 pts
/ ~3.05 MB). App caught the failed setItem and surfaced a clear, actionable error ("imported set
may be too large — clear a region or import a smaller file"); panel reverted to the pre-merge
103,648 / MN 13,705, i.e. no silent corruption. localStorage setItem is atomic per-key, so the
persisted 'woongarra_imported_v2' is unchanged. The quota ceiling that tripped (~3.4 MB) is BELOW
the phone's 4.77 MB incident point -> desktop Chrome localStorage headroom < iOS PWA container.
Testing caveat: a desktop quota failure is NOT evidence the phone would fail.

**DIAGNOSTIC Q for next read-only spike (v16.49 raised the stakes on this).** On a failed quota
setItem during MERGE, confirm the in-memory `imported` array AND `poolVersion` are left consistent
with the persisted (pre-merge) state — i.e. `rebuildImportedFlat()` did not bump `poolVersion` and
rebuild the flat pool to the merged set while the write then failed, leaving the v16.49 cache
serving points that aren't on disk. Panel evidence suggests a clean revert, but under v16.49 an
in-memory/disk divergence would mean tap-read serves phantom points until reload — verify the
mutate/write/bump ORDER in the import path, don't assume from the panel.*

*v16.49.1 · 25 Jul 2026 — planning-chat correction to v16.49, no code shipped, build unchanged at
2026.07.24a. v16.49's IMPLEMENTATION is accepted in full; two figures in its write-up are corrected
here before they are cited as fact.

**CORRECTION 1 — the 144,474 pool figure is a METHODOLOGY ARTEFACT, not dataset drift. 113,557
STANDS as the on-phone stored-point count.** v16.49's harness ran `depthSamples()`/`okHAT` over the
raw repo CSVs and omitted the app's 25k auto-thin loop, which every prior replica included (see
v16.45 step 6, v16.44 at roadmap:861, v16.41 at :1190 — "real v2 CSVs through the app's own thin
loop"). Diagnostic signature: MN v2 (19,178) is already under the 25k cap and passes through
untouched in BOTH paths — hence the harness's own "MN kept 100%" — while SC (168,461 -> 17,925,
9.40x) and BR (189,187 -> 20,794, 9.10x) are over the cap and get thinned on import. Only the
over-cap datasets diverge. That is the thin loop's fingerprint.
  **Independent falsification by storage:** holding those CSVs un-thinned needs 376,826 stored rows
  x 27.91 B/pt (measured, v16.47.4) = 10.52 MB, + legacy 55,660 x 27.91 = 1.55 MB, total ~12.1 MB,
  against a container that hit quota at 4.77 MB (v16.35). The phone is not holding this pool.
  **Also note 113,557 is a STORED (pre-HAT) panel count** — 55,660 legacy + 20,794 BR + 17,925 SC +
  19,178 MN — so the true post-HAT `depthSamples()` pool is somewhat SMALLER than 113,557, never
  larger. The roadmap has been using 113,557 loosely as "the pool"; it is an upper bound.
  **Impact on v16.49's own numbers:** heap estimate UNAFFECTED and now conservative (17.3 MiB at
  113,557 is an upper bound; ~160 B/object measured stands and supersedes the brief's 88 B).
  Equivalence test UNAFFECTED (float determinism is dataset-independent). Q4 quantification
  directionally sound but computed over a superset. **TIMING NUMBERS ARE NOT DEVICE-REPRESENTATIVE**
  — "BR 189,187 pts, 39.97 ms/pan" describes a pool ~9x the phone's, in Node on desktop V8, not iOS
  JSC. The 34x RATIO is credible; the absolute ms are not. Do not quote them as phone figures.
  **Standing rule, restated because it was just broken:** any replica of the on-phone pool runs the
  v2 CSVs through the app's own auto-thin loop AND the real okHAT gate. Thin first, then gate.

**CORRECTION 2 — v16.49's claim that "alpha over the rendered image cannot shift from this change"
is FALSE as written** and contradicts its own next paragraph. `r0` feeds `distA` in the pixel loop,
so alpha does shift. The accurate claim is narrower: the PIXEL LOOP'S OWN DISTANCE METRIC (`mLng`,
`cellLa/cellLo`, `sIx`) is untouched; the alpha shift is exactly the quantified mLngPool effect —
95% of samples unchanged, mean ~0.5 pp, with a ~0.02% clamp-flip tail. Read that way the entry is
consistent and the conclusion (not visible) is unchanged.

**BLAST-RADIUS NOTE — the invalidation contract now governs DATA CORRECTNESS, not just paint.**
Under v16.48 a missed `poolVersion` bump produced a stale `r0`: an opacity error. Under v16.49 it
produces a stale ENTIRE POOL, and `depthSamples()` also feeds `idwDepthAt()` (tap-to-read depth)
and `buildAutoContours()` — both of which previously received a freshly built pool on every call.
A missed bump therefore now means the app DISPLAYS A DEPTH FROM THE PREVIOUS DATASET. The three
choke points (`savePts()`/`saveCt()`/`rebuildImportedFlat()`) were verified in v16.48 for a
lower-stakes cache and carried into v16.49 unchanged and un-retested. Not asserted broken — flagged
as now load-bearing. **ON-PHONE VERIFICATION IS A GATE ON THE NEXT BUILD, not optional housekeeping
(checklist below).**

**ON-PHONE INVALIDATION GATE — Aaron only, no Claude Code needed, run before any new build.**
Force-close/reopen, confirm build `2026.07.24a`, then WITHOUT force-closing between steps:
  1. Import a small CSV (the `guya_smoketest_import1.csv` / `_import2.csv` pair, or any few-dozen-
     point file) via REPLACE into a throwaway `smoketest` region. Confirm the panel count updates,
     the shading redraws, and tap-to-read over a new point returns a depth consistent with it.
  2. MERGE the second small file into the same region. Confirm the count rises by the new unique
     points only.
  3. ✕-remove the `smoketest` dataset row. Confirm it leaves the list, the total drops, and
     tap-to-read no longer returns those points' depths.
  4. Clear-all (or the equivalent). Confirm shading and tap-to-read reflect the emptied pool.
  Any step where the count, shading, or tap-to-read does NOT track the change is a missed
  `poolVersion` bump — fix it before the flats layer goes near this cache. Cosmetic aside: ~18-38
  samples can now sit at `R0_MAX=90` (3x disc radius) deterministically rather than jittering per
  pan; note if seen, do not chase.

**REMAINING FROM THE v16.48/49 PLAN — resolved and stated plainly** (v16.49's own next-session note
left this vague): Steps 3 and 4 (equivalence/timing, build discipline) are DONE. **Step 5 — the
AusSeabed read-only coverage query — was NOT run.** It stays on the low-priority backlog as item
(b), unchanged, ~15 min, fold into whichever Sonnet session runs next.

**NEW BACKLOG ITEM (c), cheap, not queued — the remaining per-pan O(n) work.** v16.49 removed the
object-churn and the r0 precompute from the pan path, but `ptsBounds(pts)` and the
`buildSampleIndex()`/`sIx` bucket build still run over the full pool on every `buildShade()`. Both
are cacheable on the same `poolVersion` — `bb` trivially, `sIx` only if its cell sizing is
re-anchored off the viewport-derived `mLng` first (same manoeuvre v16.49 just performed for the
gap search). NOT queued: Aaron reports panning acceptable at v16.48. This is the first place to
look if the flats layer or MN v3 makes panning slow again, rather than reopening R0.

**SEQUENCING PUSHBACK — build the flats layer BEFORE the Option 3 mask.** Option 3's STRICT-AND
gate (OSM water AND WOfS freq>=0.2) is designed to suppress paint on ground that is dry most of the
time. That is a precise description of the intertidal flats the flats layer exists to render.
Building Option 3 first risks masking exactly the data the flats layer wants to show, then
partially un-masking it. The only stated reason for mask-before-MN-reexport is that the mask sources
the OSM polygons the MN clip depends on — that argument does not reach the flats layer. The flats
layer is also the biggest single win available and needs no new data. Reflected in the sequence
below.*

*v16.49 · 24 Jul 2026 — `depthSamples()` POOL CACHE SHIPPED (build 2026.07.24a), Step 2 of the
v16.48 follow-up plan: the RETURNED ARRAY is now memoised on `poolVersion`, not just the r0 values.
v16.48 (`_r0Cache`, a side `Float32Array` + positional-index copy) still paid `depthSamples()`'s
full ~113k-object-literal rebuild on every pan; only the O(n) neighbour-search half of the cost was
actually cached. v16.49 caches `depthSamples()`'s array itself, so the SAME objects come back on
every call while `poolVersion` is unchanged - the old side array is no longer needed, and
`buildShade()`'s `p.r0=…` write (originally a v16.47 no-op on a throwaway object, per v16.48's own
Q1 finding) becomes a genuine cache for free.

**VERIFY (a) — no other mutator, checked not assumed.** Read every call site of
`depthSamples()`'s output: `buildAutoContours()` (`index.html:2334`) only reads `.lat/.lng/.d` via
`buildSampleIndex()`/the marching-squares field build, never writes; `idwIndex()`/`idwDepthAt()`
(`:2265-2277`, feeding tap-to-read + `findDeepest`) likewise read-only. `buildSampleIndex()` itself
(`:1937-1939`) only pushes references into buckets, never mutates. **The ONLY write anywhere in the
file is `buildShade()`'s `p.r0=…`** (now `:2044-2049` area) - confirmed by reading, not grepped-and-
assumed. Safe to cache the array.

**VERIFY (b) — point-drag path does not exist for this pool.** `points` (the depth-sample pins
`depthSamples()` reads) render as non-draggable `L.circleMarker`s (`renderDepths()`, `:1325-1343`)
- no drag handler registered anywhere. The ONLY draggable markers in the app are `spots` (fishing
pins, a fully separate array/layer/`saveSpots()`, unlocked via `sp-lock` -> `spotsUnlocked`,
`:1545-1547`) - `depthSamples()` never reads `spots`. **No live-drag path touches the sample pool
at all**, so no mid-drag staleness risk exists and no `poolVersion` bump on any `dragstart` is
needed. (The green-zone spot-drag safeguard itself is unrelated and untouched.)

**HEAP ESTIMATE — measured, not assumed; the brief's 88 B/object figure undercounts.** `node
--expose-gc`, real `process.memoryUsage()` deltas, matching the actual code pattern (3-prop
`{lat,lng,d}` literal in `depthSamples()`, `.r0` added dynamically later in `buildShade()` - a
shape transition, not a single 4-prop literal): **~160-162 B/object**, not 88 B. At the brief's
113,557-pt figure that's **~17.3 MB**, not ~10 MB. Building a 4-prop literal up front instead would
land nearer ~130 B/object (~15.9 MB) - not done here, out of scope (`depthSamples()`'s literal
shape is unchanged). Either way, trivial against a phone JS heap budget; the "safe to hold
permanently" call is unchanged, only the number needed correcting.

**Pool-size discrepancy, flagged not chased.** Per CLAUDE.md, the file on disk is the source of
truth over a remembered number: rebuilt `depthSamples()`/`okHAT`/`nearestPort`/`PORTS.hat` verbatim
in a Node harness (not reimplemented) and ran it over the real repo CSVs (`sunshine_coast_
intertidal_ground_v2.csv` + `brisbane_river_intertidal_ground_v2.csv` +
`maroochy_noosa_bathy_v2_appgrade.csv` - the same three cited for the v16.48 113,557-pt replica).
Result: **144,474** post-HAT-gate samples today, not 113,557 (raw combined rows: 376,826; SC kept
33.9%, BR kept 36.1%, MN kept 100%). Used 144,474 (the larger, currently-verified number) for the
heap estimate above (~23.3 MB) rather than the stale 113,557 figure. Not chased further - could be
dataset drift since the 113,557 figure was established, or a component of the original on-phone
replica not reproducible from repo files alone; either way out of scope for a memoisation patch.

**Q4 FOLD-IN — separate `mLngPool`, scoped to the gap/R0_local precompute only.** Added
`midLaPool=(bb.minLa+bb.maxLa)/2, mLngPool=111320·cos(midLaPool)` right before the r0 precompute
block, reusing `bb` (`ptsBounds(pts)`, already computed pre-viewport-clip at `:1985`) rather than
building a second bbox pass. Used ONLY inside the gap-search distance formula
(`dx=(p.lng-bk[m].lng)*mLngPool`); `cellLa/cellLo/sIx` (shared with the pixel-loop IDW search) and
the pixel loop's own `mLng` (`:2000`, viewport-anchored) are UNTOUCHED - confirmed by diff. Result:
r0 is now pan-independent (was previously re-derived from whatever viewport was active at the last
`poolVersion` bump, which the v16.48 cache had just started freezing).

**Quantified over the real 144,474-pt pool (Node, not asserted):** cos(-24.85°)=0.907411,
cos(-27.5°)=0.887011 -> 2.25% drift (brief's estimate: 2.29%, close, different anchor rounding).
Comparing pool-anchored `mLngPool` against both real viewport extremes: **95% of samples unchanged,
mean |Δr0|≈0.28-0.29 m, mean alpha-shift≈0.5 pp** - matches the brief's "not visible" call.
**Tail found, not in the brief's estimate:** 18-38 samples (0.01-0.03%) hit a full 60 m
R0_MIN<->R0_MAX clamp-flip at a bucket-boundary edge case. This is PRE-EXISTING in shipped v16.48
(viewport `mLng` already varies pan-to-pan there) - v16.49 does not introduce it, and removes its
pan-dependence going forward (was jittering every pan; now deterministic per sample).

**EQUIVALENCE.** Two independent fresh float64 passes over the real 144,474-pt pool, same anchor:
**0 mismatches** (formula has no hidden call-order/mutable-state dependency - same method as
v16.48's 775,221-sample check). Storage-precision delta from dropping the v16.48 `Float32Array`
(now plain float64): 6,653/144,474 samples differ, **mean |Δ|=4.1×10⁻⁸ m, max |Δ|=3.8×10⁻⁶ m** -
sub-micron, confirms the missing side array cost nothing in accuracy.

**TIMING (Node, real repo CSVs, matching v16.48's methodology).** v16.48-style (array rebuilt every
call, only r0 values cached) vs v16.49 (array itself cached), 30 simulated pans with no mutation
between them: MN 19,178 pts - 4.20 ms/pan -> 0.13 ms/pan (32×); BR 189,187 pts - 39.97 ms/pan ->
1.10 ms/pan (36×); SC 168,461 pts - 28.50 ms/pan -> 0.87 ms/pan (33×); combined 376,826-row pool -
70.37 ms/pan -> 2.10 ms/pan (34×, average - dominated by the one real rebuild). Split out: **first
call ≈90 ms (the real rebuild), every subsequent call in the same session ≈0 ms** (array reference
return, zero allocation) - this is the object-churn elimination v16.48's r0-only cache left on the
table.

**IMPLEMENTATION.** `let _poolCache=null` + a one-line guard at the top of `depthSamples()`
(`:2237` area): `if(_poolCache&&_poolCache.version===poolVersion)return _poolCache.s;` - version
only, no length check, no positional-index mapping (both were only ever needed because the old
`depthSamples()` built fresh objects every call; `poolVersion`'s bump contract already covers every
mutation path per v16.48's own Q3). `buildShade()`'s v16.48 `_r0Cache` (side `Float32Array` +
copy-loop) removed entirely and replaced with `let _r0Version=-1` + a bare guard around the
original unconditional loop, which now writes `p.r0` straight onto the (now-stable) objects -
`R0_local` formula, `R0_MIN=30`, `R0_MAX=90`, `R1=120`, the HAT gate, `okHAT`, `zoneAt()` all
byte-for-byte untouched.

**BUILD DISCIPLINE.** Both script blocks `node --check`: exit 0/0, checked twice (before and after
the build-string bump). Leaflet block SHA-256 `db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d
57596f4e5641a` - byte-identical to `f894dd0`/HEAD (same hash v16.48 recorded). `zoneAt()`, `ORDER`,
the green-zone `dragend` safeguard, and `spotsUnlocked` all confirmed absent from `git diff`. Both
`<style>` blocks byte-identical (confirmed by direct string comparison against HEAD, not eyeballed).
Diff scoped to exactly: `index.html:1969-1976` (`_r0Version` decl+comment, replacing `_r0Cache`),
`:2025-2049` (r0 precompute block + `mLngPool`), `:2237-2253` (`depthSamples()` cache), `:1035`/
`:1074` (build string ×2). Nothing else touched. `git status` clean before commit, only `index.html`
modified.

**Build-string deviation from the brief, flagged not silently followed.** The brief asked to keep
`2026.07.21a`; that value is already the commit hash `f894dd0`'s shipped build string, so reusing
it would collide with an already-released build and violates this file's own build discipline
("bump the build string... read the current value, don't assume it"). Bumped to **`2026.07.24a`**
(today's date) at both occurrences instead - flagged here rather than silently deviating.

**Next-session note:** build `2026.07.24a` on `main`, working tree clean pending this commit. Step
2 (this entry) + the Q4 fold-in are done. Remaining from the original Steps 3-5 plan: re-check
against roadmap for what Step 3/4/5 covered (not restated here to avoid drift from this file's own
record) before starting the next session's work.

*v16.48 · 22 Jul 2026 — `r0` CACHE SHIPPED (build 2026.07.21a): per-sample R0_local from v16.47 is
now memoised across `buildShade()` calls instead of recomputed on every pan. Repo hygiene done
first (see below). Diagnose-before-patch run in full before any edit.

**Q1 OBJECT IDENTITY — new objects every call, confirmed by reading `depthSamples()`
(`index.html:2214-2219`):** it builds a fresh array of brand-new `{lat,lng,d}` literals every
single invocation, from `points`/`contours`/`imported`. `buildShade()` calls it fresh every time
(`index.html:1970`). v16.47's `p.r0=…` write was therefore never a cache — it mutated a throwaway
object discarded at the end of the call. **Confirms the cache must live in a side structure, not
a property**, exactly per the brief.

**Q2 PERSISTENCE COUPLING — none.** The `pts`/`s` objects are never serialised anywhere. The only
`localStorage` writers touching this pool are `savePts()` (points), `saveCt()` (contours), and the
`IMP_DS_KEY` writers (datasets — NOT `imported` itself, which is a derived flat view, never a
`setItem` target). A module-level side array reachable from none of those cannot leak into any
export/backup/import-write payload — no repeat of the v16.35 quota incident is possible from this
change.

**Q3 POOL MUTATION PATHS — three choke points, not a call-site hunt.** `depthSamples()`'s
composition depends only on `points`, `contours`, `imported` (`okHAT`/`nearestPort()` reads only
static `PORTS`, never mutated at runtime). Traced every mutation: `points` only ever changes via
`addPt()`/`removePt()`/backup-restore-merge/"remove all", **all four already call `savePts()`**
immediately after; `contours` only ever changes via add/edit/delete/clear/undo/freehand-add/
backup-restore-merge, **all already call `saveCt()`**; `imported` is only ever reassigned inside
`rebuildImportedFlat()` itself, which **every** REPLACE/MERGE/✕-remove/clear-all/undo-replay/
backup-restore path already calls. No per-region visibility toggle exists in the code today
(searched, zero matches) and no bounds/zoom-based pool filtering exists either — `depthSamples()`
returns the full unfiltered pool regardless of viewport. **Design: one module-level `poolVersion`
counter, bumped inside `savePts()`, `saveCt()`, and `rebuildImportedFlat()` themselves** — 3 edits,
not N call sites, and every current AND future path through the established save/rebuild
convention is covered automatically.

**Q4 ZOOM INDEPENDENCE — mostly clean, one small pre-existing coupling found and reported, not
silently patched.** `gap`/`R0_local` (`index.html:2020-2026` pre-edit) use `mLat=111320` (exact,
viewport-independent) and `mLng=111320·cos(midLa)` where `midLa` is derived from the
**viewport-clipped** render bounds (`index.html:1977-1988`), not a fixed anchor. Nothing is in
pixels (the literal stop-condition), but `mLng` does drift with pan position: across MN's full
lat span (0.86°) `cos(lat)` varies ~0.67%. This was invisible pre-cache because r0 was recomputed
fresh every call (drift self-corrected every pan); caching **freezes it at whichever viewport was
active at the last version bump**, so the tiny drift becomes real (if minuscule) staleness rather
than a non-issue. **Judgement call, not silently resolved:** given the explicit zero-behavioural-
change constraint and R0_MIN/MAX/R1 untouched, this is left as-is and reported rather than fixed —
fixing it would mean re-anchoring `mLng` to the pool's own bbox, a genuine formula-input change out
of scope for a memoisation-only patch. Bound is <0.7% of `mLng` over the ENTIRE dataset's latitude
range, clamped into [30,90] — vanishingly unlikely to ever cross a visible threshold. Flagged as a
small, quantified, optional follow-up if perfect viewport-independence is ever wanted.

**IMPLEMENTATION:** `let poolVersion=0` (`index.html:1308` area) bumped by `savePts()`/`saveCt()`/
`rebuildImportedFlat()`. `let _r0Cache=null` (next to `_zoneFaded`) holds `{version,n,r0:Float32Array}`.
The precompute loop now checks `_r0Cache.version===poolVersion && _r0Cache.n===pts.length` — hit:
a plain array copy (`pts[k].r0=_r0Cache.r0[k]`); miss: the identical original bucket-scan search,
now also writing into `r0Arr` for the next cache. **R0_local formula, R0_MIN=30, R0_MAX=90, R1=120,
the HAT gate, `okHAT`, `depthSamples()`, `zoneAt()` all byte-for-byte untouched** — confirmed by the
diff itself, not merely asserted.

**VALIDATION.** Equivalence: reimplemented the exact precompute formula in Node against every real
CSV in the repo (MN v2 19,178 pts; Brisbane River intertidal v1/v2, 209,540/189,187 pts; Sunshine
Coast intertidal v1/v2, 188,855/168,461 pts) — **0 mismatches across 775,221 samples tested**,
comparing a fresh computation against an independent second fresh computation at Float32 precision
(the same precision the shipped cache stores) — confirms the formula has no hidden call-order/
mutable-state dependency that would make a cached value diverge from a freshly-computed one.
Timing (Node, same real CSVs): MN 19,178 pts — uncached precompute 54.65 ms, cached-path cost per
subsequent pan 0.091 ms (**598× faster per pan after the first call**). Brisbane River v1
209,540 pts — 472.02 ms uncached vs 0.478 ms cached (987×). Sunshine Coast v1 188,855 pts —
397.18 ms uncached vs 0.331 ms cached (1199×). The legacy 55,660-pt phone-only blob is **not in
this repo and was not measured** — linear extrapolation from MN's measured per-point cost gives
**~159 ms uncached per `buildShade()` call**, reported as an estimate only (point density/bucket-
occupancy won't be perfectly uniform, so treat this as indicative, not a promised number).

**BUILD DISCIPLINE.** Both script blocks `node --check`: exit 0/0 (verified twice — once before,
once after the build-string bump, to catch any edit-induced break). Leaflet block SHA-256
`db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a` — byte-identical to `9d5cebd`,
confirmed by extracting the exact byte range with newline-translation disabled (a first extraction
attempt via a naive text-mode script silently CRLF-corrupted 5 bytes and produced a false-mismatch
hash — caught and redone correctly rather than reported blind). `zoneAt()`/`ORDER`
(`index.html:1296`) and the green-zone `dragend` safeguard (`index.html:1542`) confirmed absent
from the diff (`grep` over `git diff`, not eyeballed) — untouched. Both `<style>` blocks likewise
absent from the diff — untouched. Build string bumped `2026.07.19b`→`2026.07.21a` at both
occurrences (`index.html:1035`, `index.html:1074`). Diff scope, file:line: `index.html:1306-1310`
(`poolVersion` decl + `savePts()`), `:1966-1974` (`_r0Cache` decl), `:2029-2049` (the memoised
precompute block, replacing the old unconditional loop), `:2159` (`rebuildImportedFlat()`),
`:2909` (`saveCt()`), `:1035`/`:1074` (build string ×2). Nothing else touched.

**STEP 0 REPO HYGIENE (done first, before any of the above):** the pre-existing uncommitted
`GUYA_ROADMAP.md` edit (v16.47.1→v16.47.5 entries) was purely additive/consistent with the
versioned entries already at the file's head, plus one coherent in-place "pending"→"complete"
status update corroborated by the v16.47.2 entry in the same diff — no conflict, no duplication.
Committed alongside the untracked `guya_species_qld_v3.md` (benign QLD species-passport seed data,
read in full before committing, unrelated to any of this build). Pushed before Step 1 began.

**STEP 5 FOLD-IN — AusSeabed coverage query, read-only, no repo writes, ~15 min box.** Queried
`warehouse.ausseabed.gov.au/geoserver` WFS directly (public OGC endpoint, no account needed):
`GetCapabilities` located the actual coverage-index layer, `ausseabed:MARINEDATAREGISTER_
ACQUISITIONS_INDEX` (distinct from the ~1000 individual per-survey coverage rasters also listed);
`GetFeature` with a bbox filter `153.0,-28.2,153.65,-26.7` (Caloundra→Point Danger) returned
**166 acquisition records.** Findings, reported as coverage-index text per the brief — **this does
NOT reopen the depth-data question, still evidence-closed per v16.47.2**:
  - **Maroochy/Noosa's known Fugro LADS survey is confirmed as the SOLE LiDAR bathymetry coverage
    on the Sunshine Coast open-coast stretch of this index** (`Sunshine Coast Maroochy River to
    Noosa River Bathymetry 2011`, LADS Mk3 Laser, 586.80 km², CC BY 4.0, Qld Government) — matches
    what's already held, corroborating rather than contradicting the closed research audit. **One
    new-to-the-record nuance**: AusSeabed's own metadata tags it `USER_CONSTRAINTS: "Not to be used
    for navigational purposes"` — not previously logged; almost certainly immaterial to a fishing
    app (Guya was never charting/navigation) but recorded for completeness.
  - **New backlog-only finding, filed against the already-parked Gold Coast region (#15), not
    actioned:** the index carries genuine 2014 LiDAR bathymetry (not chart-derived) over Gold
    Coast waterways — Nerang, Coomera, Biggera, McCoys, Loders (individually 0.002–2.8 km², plus
    one 138.82 km² umbrella "Bathymetric Lidar 2014" record), all CC BY 4.0. This is IN ADDITION
    to the already-filed NSW Marine LiDAR Topo-Bathy 2018 (Palm Beach→Point Danger only). Neither
    changes anything for a currently-open Guya region; both stay parked under item #15 until Gold
    Coast is ever unparked.
  - **Discrepancy flagged, NOT resolved — needs a verify if this area is ever revisited, not now:**
    the index lists `Moreton Bay Queensland Bathymetry 2004` (Multibeam, 27.14 km², 2004-08-29) as
    **CC BY 4.0**. This plausibly corresponds to the previously-researched Curtin CMST 2004 Moreton
    Bay multibeam survey, which the depth-data audit recorded as licensed **"research purposes, not
    for navigation" — i.e. NOT CC BY**. Either these are different surveys, or AusSeabed's
    portal-level licence tag disagrees with the survey's own stated terms (a known class of
    data-portal metadata issue). Not chased further inside the 15-minute box; flagged plainly
    rather than silently assumed either way.
  - **Negative confirmation:** no record anywhere in the 166 touching the SEQ bbox is named for
    Redcliffe/Scarborough/Woody Point/Bramble Bay/Deception Bay/Pumicestone/Bribie. The City of
    Moreton Bay 2021 Redcliffe Hydrographic Survey (backlog item 15a) is **not in AusSeabed's
    national index** — consistent with it being a council-only DataHub item never submitted
    upstream. Doesn't change item (a)'s status; still "inspect extents first" on the council portal
    directly, unconfirmable via this route.
  - **Bulk of the 166 records** are Gold Coast canal-estate "digital bathymetric contours from
    charts" (chart-derived — excluded per the project's own no-chart-art rule) and NSW singlebeam
    hydrosurveys near the Tweed/Point Danger border, plus one 2023 30 m "Approaches to Moreton Bay"
    vessel survey (bbox lat −26.43…−26.95, "Approaches to" naming and 30 m resolution both point to
    a channel-approach survey, i.e. deeper transit water, not the 0–50 m land-based fringe).
    **No new candidate for the unmeasured 0–50 m fringe surfaced** — reinforces, does not overturn,
    the v16.47.2 evidence-closed finding.

**NEXT JOB:** Option 3 (STRICT-AND land/water mask, runtime path, AUTHORISED v16.47.3) — was
gated behind this cache landing first, per the v16.47.2 sequence. MN v3 (native-25m/200m-band
clip, v16.47.5) sits behind that. On-phone re-check for THIS build: confirm build string reads
`2026.07.21a`; feel-check panning after toggling shading on with a multi-region point pool loaded
(expect no regression — it was already fine, this should make it feel better, not worse); no
visual change expected anywhere (this is memoisation-only).*

*v16.47.5 · 21 Jul 2026 — MN v3 CLIP CRITERION CHANGED BY AARON: distance-from-shore, not depth.
Supersedes v16.47.4's Option A. Storage economics reverse completely — full native resolution now
looks affordable. No code shipped, build unchanged at 2026.07.19b.

**AARON'S DECISION (21 Jul):** keep the offshore data, but only out to **~200 m from shore**, and
make what remains **as smooth as possible**. This replaces the depth-based clip (≤15 m LAT) proposed
in v16.47.4 Option A, and it replaces "offshore goes blank" with "offshore is kept where it's
castable and deleted where it isn't."

**WHY THIS IS THE BETTER CRITERION (not merely a different one):**
  - It encodes castability **directly**, rather than using depth as a proxy for it. Depth and
    distance decouple badly at exactly the places that matter — off steep rock like Point Arkwright
    or Noosa Heads, water 60 m out can already exceed 15 m, so a depth clip would have deleted
    genuinely fishable ground; over the shallow shelf off Marcoola, 15 m LAT sits ~1 km out, so a
    depth clip would have retained a kilometre of uncastable water.
  - **It keeps the river corridors whole automatically.** The Maroochy and Noosa are mostly under
    400 m wide, so a 200 m band from either bank covers them bank-to-bank with no special-casing.
    The v16.47.4 depth clip would have kept them too (they're shallow) but by accident rather than
    by design.
  - **Reality check, recorded but not treated as a problem:** 200 m is generous against actual
    land-based casting (a big surf cast is ~80–100 m). The extra margin is deliberate — it gives
    context on the water beyond the cast, and at these point counts it is nearly free. Don't trim
    it to "realistic" casting range; the generosity costs almost nothing and losing it would cost
    situational awareness.

**CLIP DEFINITION AS SPECIFIED:** retain a point if its distance to the nearest land-polygon
boundary is ≤ 200 m. **Use the OSM water/land polygons already being brought into the project for
Option 3 (v16.47.3)** — same source, same session, no new dependency, and it guarantees the clip
boundary and the paint mask agree with each other rather than disagreeing at the margin. Rivers
narrower than 400 m are retained bank-to-bank as a consequence, which is the desired behaviour.

**THE ARITHMETIC — AND WHY IT REVERSES THE STORAGE QUESTION.** v1 holds 946,877 pts on a 25 m grid,
so the surveyed footprint is 946,877 × 625 m² ≈ **591 km²**. A 200 m band is a thin ribbon of that:
  open coast, ~30 km Mudjimba→Noosa × 0.2 km            ≈  6 km²
  Maroochy + Noosa river corridors, ~25 km × ~0.2 km    ≈  5 km²
  total band                                            ≈ 11 km²  =  **~1.9% of footprint**
  native 25 m points inside the band ≈ 946,877 × 0.019  ≈ **~17,600 pts**
  storage ≈ 17,600 × 27.91 B (measured, v16.47.4)       ≈ **~491 KB**
**That is LESS than the 535 KB / 19,178 pts currently deployed.** Full native 25 m resolution inside
the casting band is roughly break-even with today's coarse 180 m grid across the whole footprint —
because five-sixths of that footprint is water Aaron will never cast to.

**SMOOTHNESS AT NATIVE 25 m — the ask is fully satisfied, with headroom.** R0_local =
clamp(25−120, 30, 90) = 30. Orthogonal midpoint d = 12.5 m; diagonal midpoint d = 17.7 m. **Both
fall inside R0 = 30, so alpha = 1.0 — fully saturated paint, no ramp, no holes anywhere.** This is
not "smoother than the lattice"; it is the maximum the renderer can produce, and it exceeds
Bargara. No R0, R1, or renderer change is needed to achieve it. The v16.47.2 alpha analysis and the
v16.47.4 hole-rate measurements become moot inside the band — they described a coverage problem
that a 25 m grid does not have.

**Pipeline simplification worth noting:** at native resolution there is **no thinning step at all**
— MN v3 becomes a pure spatial clip of v1. `bathy_thin_v2.py`'s deepest-point-per-cell rule (and
the within-cell positional jitter it caused, diagnosed in v16.47.4) drops out of the picture
entirely. Fewer moving parts than any previously costed option.

**MUST MEASURE BEFORE BUILDING — the estimate above is geometric, not measured.** The 591 km²
figure is sound (derived from point count × cell area), but the ~11 km² band area rests on eyeballed
coastline and river lengths. Real coastline is crenulated and the rivers meander, so the true count
could plausibly land 2–3× higher. **First step of the build is to compute the actual clipped count,
not to assume ~17,600.** A pre-agreed ladder so this does NOT need a round-trip back to planning:
  ≤ 60,000 pts   → ship **native 25 m**, no thinning          (≤ 1.68 MB)
  60k – 150k     → thin to **40 m** within the band           (≤ 4.19 MB — check quota first)
  > 150,000 pts  → thin to **60 m** within the band; alpha at the diagonal midpoint is then 0.86,
                   still far above the 0.5 "barely touching" threshold and still visibly smooth
  In every branch the band stays at 200 m — **thin the grid, never shrink the band.** The band is
  Aaron's spec; the grid is the adjustable variable.

**COVERAGE CAVEAT — check, don't assume, and do not treat a gap as a bug.** The research audit
(v16.47.2) recorded Sunshine Coast Council's own consultants stating the surf zone — sand bar and
beach trough systems — cannot be surveyed accurately. LADS bathymetric LiDAR has a *shallow* limit
as well as a deep one. **The innermost part of the 200 m band, right at the beach, may simply have
no source data**, in which case the clipped output will show a bare strip at the waterline on open
coast. v1's minimum depth of −1.15 m confirms *some* very shallow data exists, but not that it is
continuous alongshore. **Report actual coverage-versus-distance during the build.** If the surf
strip is empty, that is a survey limitation, not a pipeline fault, and must NOT be papered over by
widening R1 or interpolating into it.

**IMPORT DISCIPLINE — unchanged and non-negotiable:** MN v3 must be imported with **REPLACE** on
the `maroochy_noosa` region, never MERGE. MERGE cannot remove the existing 19,178 coarse 180 m
points; merging v3 in would leave both grids co-resident and reintroduce the very lattice this
fixes. Set the region dropdown **explicitly** before importing (the Maroochy/Noosa MERGE incident
was a process gap, not a code gap). The 25,000-point cap is per CSV parse, not per store, so a
multi-chunk import is expected and fine. Run `storage_check.html` in the home-screen container
first as standing practice, though at these projected sizes quota risk is negligible.

**SUPERSEDED BY THIS ENTRY:** v16.47.4's Option A (60 m grid clipped to ≤15 m LAT, ~27,900 pts,
+0.24 MB) and its Options B and C. The "offshore goes blank" tradeoff v16.47.4 asked Aaron to accept
is **withdrawn — it is no longer necessary.** v16.47.4's measurements (grid confirmation, hole
rates, provenance, 27.91 B/pt, re-thin projections) all stand and remain the evidence base; only its
recommendation is replaced.

**SEQUENCE — position unchanged, item 4 re-specified again:**
  4. **MN v3 re-export = spatial clip of v1 to ≤200 m from the OSM land boundary, at native 25 m
     if the measured count allows (ladder above).** Still sits behind the `r0` cache (item 1),
     Option 3 (item 2), and the flats layer (item 3). Note the ordering is now doubly justified:
     item 2 brings in the OSM polygons this clip depends on, so building item 4 first would mean
     sourcing them twice.*

*v16.47.4 · 21 Jul 2026 — MN offshore diagnostic RETURNED. Hypothesis CONFIRMED in kind,
CORRECTED in magnitude and mechanism. No code shipped, build unchanged at 2026.07.19b.
**NOTE: this entry's RECOMMENDATION (Option A, depth-based clip) is superseded by v16.47.5 above.
Its MEASUREMENTS stand and remain the evidence base for all MN work.**

**FILES CONFIRMED:** deployed = `data/maroochy_noosa_bathy_v2_appgrade.csv` (19,178 pts, 180 m
MGA56 grid). Full source = `data/maroochy_noosa_bathy_v1.csv`, **PRESENT**, 946,877 pts, 25 m grid.
Thinning logic located at `data/raw/_inventory/bathy_thin_v2.py`, reused read-only.

**GRID CONFIRMED — definitively, not inferentially.** Transforming to MGA56 (EPSG:28356) and
rounding at 180 m reproduces **exactly** 18,766 occupied cells offshore and **exactly** 19,178 for
the full deployed set — a perfect match to point count, which only a rounded-coordinate export grid
produces. Corroborated by a **zero-population bin at [185,190) m flanked by populated bins**,
appearing independently on BOTH axes (east-pairs median 176.8 m, 20.6% in [175,180); north-pairs
median 176.7 m, similar cluster at [170,180)). Organic sampling does not produce that.

**DERIVATION CORRECTED — record this, it matters for fix design.** v16.47.2 predicted 100% of
diagonal cell-centres beyond R1 and 0% of orthogonal midpoints. **MEASURED: diagonal-neighbour
midpoints 31.4% exceed R1=120 m** (median nearest-sample 107.5 m); **orthogonal-neighbour midpoints
15.2% exceed R1** (median 88.4 m, max observed 195.7 m). Diagonal holes occur ~2× as often as
orthogonal — direction correct — but it is **not** the clean 100/0 split idealised geometry
predicts. **CAUSE:** `bathy_thin_v2.py` keeps the **deepest point per cell**, not the cell centre,
so kept points sit off-centre within their 180 m cells; real pair distances spread to ~2× grid (max
391 m observed). The hole pattern is **probabilistic across both axes**, not a pure
diagonal-cell-centre effect. Any grid-based fix must account for within-cell positional jitter, not
just nominal G/√2 geometry.

**SPACING (offshore, n=18,766):** min 24.8, p10 35.5, p25 75.1, median 125.6, p75 174.2, p90 175.9,
p99 201.0, max 1343.1 m. Inshore (n=412, depth ≤1.0 m): median 175.3, p90 390.6 — wider and noisier,
as expected for a river-following chain. Split rule was depth >1.0 m = offshore; it yields
412/19,178 = 2.15%, closely matching the roadmap's independently-derived ~2% river-corridor figure,
which cross-validates the rule.

**PROVENANCE — GENUINE LADS, NOT CLASSIFIER-FAULT RESIDUE.** 100.00% (19,178/19,178) of deployed
rows exist as exact (lat, lng, depth) triples in the 946,877-row v1 source. v2 is a strict
unmodified subset — no interpolation, no averaging. Depth range identical across both files
(−1.15 … +42.48), consistent with extremes-preserving per-cell max-depth selection. **The offshore
lattice is real bathymetry; the Option 3 land/water mask must NOT touch it.**

**BYTES-PER-POINT MEASURED: 27.91 B/point** (535,165 body bytes / 19,178 rows), vs the 28.44 B
assumed since v16.28. Actual is 1.9% **smaller**, so all prior storage projections were mildly
conservative — safe direction. **Use 27.91 going forward.**

**RE-THIN PROJECTIONS from full source** (no file written): 60 m = 166,547 cells; 90 m = 74,720;
120 m = 42,379; 180 m = 19,178 (exact match to deployed, confirming the reproduction is correct).
v16.47.2's estimate of 76,712 pts at 90 m was accurate to within 2.7% of the measured 74,720.

**DEPTH DISTRIBUTION — the finding that reframed the clip question.** Points deeper than 15 m LAT:
v1 = 788,376/946,877 (**83.26%**); v2 = 15,927/19,178 (83.05%). Near-identical proportion at both
thinning levels, so this is a property of the dataset, not an artefact of thinning. **Five-sixths of
the MN footprint is deep offshore water a land-based angler cannot cast to.** v16.47.2 had costed
densification across the whole footprint without combining it with a clip.

**Options as costed at the time (SUPERSEDED by v16.47.5, retained for the arithmetic):**
  A. 60 m grid, clipped to ≤15 m LAT: ~27,900 pts, 778 KB, store ~3.41 MB, diagonal alpha ~0.86
  B. 90 m uniform, no clip:            74,720 pts, 2.09 MB, store ~4.72 MB, alpha ~0.63
  C. 60 m uniform, no clip:           166,547 pts, 4.65 MB, store ~7.28 MB, alpha ~0.86
  v16.47.2's "90 m, +1.64 MB" recommendation was correct arithmetic on the wrong target — it
  densified water that will never be fished.

**REPO HYGIENE — PRE-EXISTING, NOT CAUSED BY THE DIAGNOSTIC:** the diagnostic reported an
uncommitted `GUYA_ROADMAP.md` edit and untracked `guya_species_qld_v3.md` in the working tree, both
predating the session and untouched by it. HEAD otherwise matches `origin/main`. **"git status clean
and up to date with origin/main" is a MANDATORY session-end step, so a prior session left this
behind. Resolve at the START of the next Claude Code session before any new work.**

**Diagnostic discipline note, worth keeping:** this session followed diagnose-before-patch exactly —
read-only, no repo writes, all scratch outside the tree, hypothesis stated up front and then
partially falsified by measurement rather than confirmed by assumption. It corrected two numbers
that would otherwise have been built against. This is the pattern to repeat.*

*v16.47.3 · 21 Jul 2026 — DECISION RECORDED, no code shipped, build unchanged at 2026.07.19b:
**Option 3 (STRICT-AND land/water mask) is AUTHORISED, RUNTIME PATH, effective immediately.**

**What was decided.** Aaron gave explicit GO on 21 Jul to (a) override v16.43's "don't trigger
standalone — ride it along with a future SC/BR re-export" gate, and (b) implement the mask as a
**runtime in-app polygon union evaluated at the existing shared v16.25 gate**, NOT as a bake-time
per-point tag in a v3 CSV export. The v16.43 gate is therefore **retired, not weakened** — it was
set on sequencing logic (avoid re-export churn for a fix that could piggyback later), and the
runtime path removes the re-export entirely, so the reason the gate existed no longer applies.

**Decisive argument for runtime over bake-time, recorded so it isn't relitigated:** roughly half
the total point pool — the untagged legacy 55,660-pt "pre-region-tagging" blob — exists ONLY in
Aaron's phone localStorage, is not in the repo, and cannot be regenerated or re-exported. **A
bake-time mask can therefore NEVER reach it**, meaning land overpaint would be fixed in three of
four datasets permanently. Runtime reaches it, reaches SC/BR/MN immediately with no re-import
churn, and covers future regions automatically without each export having to remember to tag.
Cost is +0.3–0.8 MB on a 2.1 MB single file, paid once, versus per-region re-export churn forever.

**Spec as authorised (from the v16.43 spike, unchanged):** hybrid **STRICT-AND** — a point counts
as paintable/readable water only if **OSM water polygons AND DEA WOfS (frequency ≥ 0.2) both agree
it is water.** Scored on 13,178 pilot points: **0.79% false-paint, 99.74% wet coverage kept** vs
OSM alone (2.06%/99.77%) and WOfS alone (2.04%/99.75%). The AND is load-bearing — the two sources
fail in *different* places (OSM on canal estates and golf lakes, WOfS on narrow mangrove creeks,
~0.25% of wet points), so requiring agreement cancels most of both.

**Aaron's accuracy bar maps onto the threshold, not the mechanism:** *"some land overlap is OK if
it's genuinely accurate to where the tide reaches often."* WOfS frequency IS observed wetness
frequency, so **`freq≥0.2` is the tuning knob** — lower it to retain more marginal intertidal
ground, raise it to be stricter. Treat 0.2 as the starting value from the spike, not a constant.

**Expectation set, not to be quietly revised upward later: 0.79% false-paint, NOT 0%.** Residual
is beach-swash and suburban-edge pixels — OSM's coastline sits at ~MHWS and WOfS goes nodata over
surf. No scheme tested clears this. Beach/swash is the one genuine friction point identified by the
spike and it stays.

**Validation already on record (v16.43, does not need re-running):** every named dry probe read
land on both sources; all 9 stale-popup locations read water (≥0.97) on both — either source alone
would have caught the v16.40/v16.41 incident; the Maroochy Wetland Sanctuary defect grid (36 pts)
read land 36/36 on OSM and 34/36 on WOfS, confirming the mask catches the defect *class*, not just
that one instance.

**Licensing note, carried forward:** OSM is **ODbL**, unlike the project's CC BY sources elsewhere.
Fine for personal, non-commercial use (Guya is explicitly not for commercial sale); recorded so it
is not rediscovered as a surprise.

**Sequencing unchanged — this does NOT jump the queue.** Option 3 remains item 2 in the v16.47.2
sequence, behind the `r0` cache (item 1), which must ship first because `buildShade()` re-runs on
map movement and the mask adds work at the same gate. The MN offshore diagnostic (item 0) is still
in flight and is independent of this decision — the offshore LADS lattice is genuine deep-water
bathymetry that the mask will not and must not touch.

**Build prompt not yet drafted** — to be written against the runtime spec once the diagnostic
returns and the `r0` cache lands. Hard rules unaffected: this touches the cosmetic paint/read gate
only, never `zoneAt()`, zone determination, or any legality assertion.*

*v16.47.2 · 21 Jul 2026 — planning chat: v16.47 CLOSED on-phone; depth-data question
EVIDENCE-CLOSED; DATA-TYPE TAXONOMY established; offshore MN lattice diagnosed; build sequence
re-ordered. No code shipped, build unchanged at 2026.07.19b.

**BOOKKEEPING WARNING — stale-roadmap artifact, recorded so it isn't re-merged:** a parallel
research chat emitted a delta labelled "v16.43.2" carrying build string `2026.07.11a` and naming
"Option A elevation-aware gate" as the next job. That chat held a roadmap copy stale by ~8 days /
4 versions (Option A shipped v16.44, 13 Jul; the MN disc work shipped across v16.45/46/47). Its
WEB FINDINGS are sound and are merged below in full; its version label, build string, and handoff
are DISCARDED. **Standing process fix:** research-mode prompts must carry the current build string
and roadmap version explicitly, since a research chat does not receive the re-uploaded roadmap by
default. This is the exact "planning chats working off stale state with no way to detect it"
failure the brief warns about, and it will recur otherwise.

**v16.47 CLOSED — on-phone re-check complete at build 2026.07.19b:**
  - Build string confirmed `2026.07.19b` after force-close/reopen.
  - **Tewantin/Noosa Heads corridor: PASS.** Contiguous wash; the discrete-disc chain is gone.
  - **Maroochydore/Bli Bli: PASS on the v16.46 regression** — land-overpaint back to pre-v16.45
    levels as predicted. Residual overpaint still visible there is Option A's known sub-HAT
    messy-tier residual (v16.43, 53–58% / ~800–880 pilot points), **NOT an R0 fault** — do not
    read that screenshot as a v16.47 failure.
  - **Shading toggle: no perceptible slowdown** once the app has loaded.
  - **NEW, surfaced by the same check — MAP PANNING feels slightly slow.** `buildShade()` re-runs
    on map movement, so every pan now pays v16.47's O(n) per-sample precompute across all 113,557
    points. **FOLLOW-UP QUEUED:** cache each sample's `.r0`, invalidate only on
    import/replace/clear. Bounded Sonnet job, no design change to the adaptive scheme. **MUST ship
    BEFORE any densification** — densifying multiplies an already-noticeable per-pan cost. Honest
    caveat: panning slowness is not proven attributable to the precompute (it may be partly
    pre-existing at 113k points); the cache is a strict improvement regardless, but don't promise
    it as a complete fix.
  **No fourth R0 iteration required. R0 work is DONE.**

**DATA-TYPE TAXONOMY (durable — the core reframe; "depths" was one label doing four jobs):**
  1. **Woongarra/Bargara** — clear-water bathymetric LiDAR, dense. Real depth. Reference standard.
  2. **Maroochy/Noosa** — Fugro LADS bathymetric LiDAR. Real depth, correct data, rendered at ~2%
     density on a regular ~180 m export grid. A **DENSITY** problem, not a renderer problem.
  3. **Sunshine Coast / Brisbane River / Moreton Bay (unprocessed)** — topographic NIR. Ground
     elevation, zero water penetration, plus the class-9 classifier fault. **NEVER was depth and
     cannot become depth.** A **MISLABELLING** problem.
  4. **Redcliffe / western Moreton Bay** — turbidity defeats laser bathymetry. A **PHYSICS WALL**.
  The v16.45/46/47 cycle cost three iterations in two days because an R0 (renderer) lever was
  applied to problems 3 and 4, which are not renderer problems. **Diagnose the data type first.**

**OFFSHORE MN LATTICE — diagnosed, and DISTINCT from the inshore disc issue v16.47 fixed:**
  The blue disc lattice offshore Mudjimba/Marcoola/Noosa is **genuine LADS bathymetry** (renders
  blue/deep; classifier-fault artifacts render near-zero green inshore — the colour split is the
  tell). It is **NOT tidal, NOT dry**, so the land/water mask will not and should not touch it.
  Cause is grid regularity against the R1 ceiling. **Derivation below is from documented constants,
  NOT yet measured — the read-only diagnostic (sequence item 0) exists to confirm or refute it:**
    180 m grid: `R0_local = clamp(180−120, 30, 90) = 60`
      orthogonal midpoint d=90 → alpha = 1−(90−60)/(120−60) = **0.50** (design target, exactly met)
      cell-centre diagonal d = 90·√2 = **127.3 m → BEYOND R1=120 → alpha = 0**
    Every grid-cell centre is a fully transparent hole. On irregular inshore terrain these dips
    scatter and read as texture; on a regular offshore grid they land simultaneously and the eye
    reads periodicity instantly. **The alpha≥0.5 criterion v16.46/47 were tuned against was never a
    "looks smooth" target — it is a "barely touching" target.** Bargara looks smooth because its
    spacing puts midpoints near alpha 1.0, not 0.5.
    **R0 CANNOT FIX THIS** — already 60 with headroom to 90; the binding constraint is R1=120
    against a 127.3 m diagonal. No R0 value closes a gap wider than R1.
  **REVISED FIX TARGET — 90 m grid, not the 60 m first proposed:**
    90 m grid: `R0_local = clamp(90−120, 30, 90) = 30`; cell centre d = 45·√2 = 63.6
      alpha = 1−(63.6−30)/(120−30) = **0.63** → connected, not dotted
    Cost: 4× density → 19,178 → 76,712 pts; net add 57,534 × 28.44 B = **+1.64 MB**
    (store ~3.2 MB → ~4.85 MB). **Supersedes the earlier +4.35 MB estimate**, which targeted a
    60 m grid — the wrong target. A nearshore clip (drop >15 m LAT, uncastable for a land-based
    angler) reduces this further. Bytes-per-point (28.44) is derived from the v16.28-era
    2,174.1 KB / 76,454 pts figure and should be re-measured by the diagnostic.
  **R1 raise past ~130** is the cheaper alternative (one constant, no re-import) but R1 governs
  total paint reach in EVERY region including the SC/BR land data. Deliberately untouched all
  session. **NOT the primary fix**; reconsider only as a small companion once the mask contains
  land spill.

**DEPTH-DATA QUESTION — EVIDENCE-CLOSED** (merged from the research audit; findings intact,
bookkeeping discarded):
  **PRIORITY QUESTION SETTLED — the 2011 Fugro LADS Sunshine Coast survey is NOT part of a
  series.** One-off pilot: "Queensland Coastal Risk and Bathymetric LiDAR," run 2011–12 with the
  CRC for Spatial Information and the Cwlth Dept of Climate Change and Energy Efficiency,
  explicitly to produce evidence informing FUTURE acquisition **that never occurred** (QLD Gov
  costed statewide acquisition at >$70M). The qld.gov.au seabed-mapping page (last reviewed
  19 Jun 2024) still lists exactly one dataset and six Sunshine-Coast-only report appendices; the
  Open Data record confirms the footprint as the lower estuarine reaches and offshore of the
  Maroochy and Noosa Rivers — i.e. exactly what is already held. **No Moreton Bay, Bribie/
  Pumicestone, Redcliffe, or Woongarra tiles exist. DO NOT RE-ASK.**

  **STRUCTURAL FINDING (durable physical limit, not a search gap):** the 0–50 m / <5 m land-based
  fringe is unmeasured across SEQ because all three instrument classes fail there simultaneously —
  vessel multibeam/singlebeam cannot physically operate that shallow, green-laser bathymetric LiDAR
  is defeated by western-bay and estuarine turbidity, and topographic NIR LiDAR has no water
  penetration at all. Independently corroborated by Sunshine Coast Council's own nourishment
  consultants in the Maroochydore monitoring report: the surf zone, including sand bar and beach
  trough systems, cannot be surveyed accurately — the industry position on precisely the target
  zone, from a project that had Port of Brisbane multibeam on hand.

  **14 SOURCES CHECKED AND CLOSED:**
  - **QSpatial "Bathymetric LiDAR for Sunshine Coast"** — already held (Maroochy/Noosa only, LAT,
    2011, 5 m, CC BY 4.0). No additional tiles exist. NO-GO.
  - **QSpatial / data.qld rest of catalogue** — no other bathymetric LiDAR or hydrographic survey
    holding for SEQ. Catalogue exhausted. NO-GO.
  - **Australian Hydrographic Office** — public products are 30 m Shoal Depth True Position grids
    only; full-resolution surfaces available from AHO on request under **restricted licence**.
    Charting priorities are channels and approaches. **Permanent NO-GO.**
  - **Port of Brisbane** — multibeam/sub-bottom/side-scan to MSQ Class A / IHO Special Order, but
    channels and berths only, commercial, no public portal. **Permanent NO-GO.**
  - **Maritime Safety Queensland** — publishes hydrographic survey *standards*; a regulator, not a
    data source. No open survey holdings. **Permanent NO-GO.**
  - **Curtin CMST Moreton Bay multibeam 2004** — Reson SeaBat 8125, Coastal Water Habitat Mapping
    Project, 29 Aug–5 Sep 2004, bbox 153.0–153.5 E / −26.9 to −27.3 S, EPSG:28350. **Real
    instrument data**, but licensed "research purposes, not to be used for navigation" (not CC BY)
    AND vessel-borne, so structurally cannot reach the fringe. **NO-GO on LICENCE, not on
    quality** — revisitable only if terms change.
  - **CSIRO Tidal Inundation multibeam 2024–25** — genuine 2 m / 1 m / 50 cm multibeam, but sites
    are Fitzroy Estuary and Cassady Creek (Hinchinbrook Shire), 700+ km north. NO-GO on coverage.
  - **CSIRO 5 m QLD estuaries composite DEM** — rejection mechanism now named precisely: creek
    depths estimated from an allometric power law on satellite-derived creek width,
    `depth = 10^(0.62·log10(width) − 1.1)`. Confirms the earlier rejection. NO-GO.
  - **NSW Marine LiDAR Topo-Bathy 2018** — Fugro ALB (Riegl VQ-820-G + LADS HD), shore seaward to
    laser extinction (~20–40 m), 3.4 m marine spot spacing, sub-metre, CC BY, SEED direct download.
    Covers NSW plus **southern QLD Palm Beach→Point Danger ONLY** (~10 km), outside every named
    area. **FILED AGAINST GOLD COAST (#15 parked)** if that region is ever unparked — otherwise
    NO-GO on relevance.
  - **Brisbane River Catchment Flood Study** — hydraulic model geometry (surveyed cross-sections,
    **interpolated between**); $795 licence fee, USB hard-drive delivery. Fails the
    no-modelled-depth rule on top of the cost. NO-GO.
  - **Sunshine Coast Council** — Port of Brisbane MBES surveys around nourishment campaigns, but
    figures are embedded in monitoring-report PDF appendices, not released as data. NO-GO.
  - **AusSeabed** — survey-acquisitions coverage index; assessed by description only. MARGINAL →
    see new backlog item (b).
  - **City of Moreton Bay 2021 Redcliffe Hydrographic Survey** — **GO (small)**, see new backlog
    item (a).
  - **DEA Intertidal epoch check** — **NO newer epoch.** Current release still draws on 2023–2025
    observations to represent median year 2024, matching the v14b evaluation. **Item 14b
    unaffected**; there is nothing to wait for.

  **NAVIONICS TRACING — HISTORICAL, CLOSED, DO NOT RE-RAISE:** the Innes Park traced contour lines
  date from the project's earliest phase, **before** the LiDAR path and the no-chart-art rule
  existed. They were deleted long ago and **pre-date every existing backup**. No contamination in
  any current dataset; **no backup-hygiene action is outstanding** — this supersedes the standing
  "delete Innes Park contours + re-export backup" chore carried since v16.44.2, which is now
  CLOSED. Aaron confirmed 21 Jul that Navionics tracing is also not a fallback he'd use going
  forward.

  **SONAR → GPX: DECLINED by Aaron (21 Jul).** No castable sonar purchase. This removes the last
  route to genuine depth numbers outside the Maroochy/Noosa footprint, and **supersedes the
  research chat's "own sonar → GPX remains the only path" line** and item 15's option (a) as a
  live plan.

  **NET CONSEQUENCE:** for Brisbane River, Sunshine Coast and Redcliffe there is **NO DEPTH LAYER
  and there will not be one.** This is now **evidence-closed, not provisionally closed.** Item 15
  ("Home-water depth reality") stands as written but its option (a) is declined and its option (c)
  is superseded by the FLATS LAYER below.

**FLATS LAYER — the Redcliffe answer, and the biggest available win (NEW, HIGH PRIORITY):**
  **Aaron ordered a Moreton Bay LiDAR patch and IT ARRIVED.** `MoretonBay_2014` /
  `Moreton_Bay_2018` tiles are present in the deliveries and appear throughout the v16.21–v16.24
  audit work (Pumicestone block, Golden Beach, Shorncliffe). **It was never processed into a CSV
  or imported** — it stalled behind Brisbane River / Sunshine Coast and was then absorbed into the
  classifier-fault investigation. **Not missed — queued and forgotten.** This answers "perhaps
  Redcliffe wasn't captured or added by me?" definitively.
  It is **topographic NIR** (same class as SC/BR) and carries the class-9 classifier fault —
  **Brighton, in Bramble Bay, is the fault's ORIGIN SITE.** Processing it as depth would reproduce
  the Bli Bli failure exactly.
  **REFRAME: SC + BR + Moreton are ONE FLATS LAYER mislabelled as three depth datasets.** Same
  product type, same fault, same drop-mask already designed (v16.23/24), same correct rendering —
  **intertidal ground elevation, NOT depth shading.** Process Moreton with the existing drop-mask,
  relabel SC/BR, render as flats.
  **ACCURACY NOTE:** LiDAR elevation (~0.1 m) **beats** DEA Intertidal (RMSE 0.27–0.33 m;
  microtidal correlation over Moreton only 0.61). If the LiDAR flats layer works, **DEA Exposure
  (item 14b) demotes from main event to optional gap-fill** and its manual confidence check stops
  being a blocker on anything.
  **HARD CONSTRAINT, carried over from item 14b and NOT weakened:** a flats layer shows
  **ELEVATION and EXPOSURE only, NEVER a "water depth over this bank right now" number.** A
  centimetre readout over a flat reads exactly like bathymetry and walks into the no-bathymetry
  rule. Three-state at most (likely dry / marginal / likely covered), driven by the existing tide
  engine. **Precision note:** the tide engine already supplies tidal range; what the flats layer
  adds is *which bank sits at which elevation*, making that range actionable.

**OPTION 3 — RUNTIME PATH RECOMMENDED, NOT YET AUTHORISED:**
  Recommendation is to **override v16.43's "don't trigger standalone" gate** and take the
  **RUNTIME in-app mask** rather than the bake-time per-point tag. **Decisive reason:** ~half the
  total point pool — the untagged legacy 55,660-pt blob — exists only in phone localStorage, is not
  in the repo, and cannot be re-exported, so **a bake-time mask can NEVER reach it.** Runtime
  reaches it, reaches all current regions immediately, and covers future regions automatically.
  Cost +0.3–0.8 MB on a 2.1 MB app, once, versus per-region re-export churn forever.
  **Aaron's accuracy bar, recorded verbatim in substance:** *"some land overlap is OK if it's
  genuinely accurate to where the tide reaches often."* This maps directly onto WOfS
  water-observation **frequency** — the `freq≥0.2` threshold inside STRICT-AND is the tuning knob;
  lower it to keep more intertidal.
  **Expectation set: 0.79% false-paint, NOT 0%.** Residual is beach-swash and suburban-edge pixels
  (OSM coastline sits at ~MHWS; WOfS goes nodata over surf). No tested scheme clears it.
  **AUTHORISED 21 Jul 2026 — RUNTIME PATH. See v16.47.3 entry at the head of this file.**

**SEQUENCE (re-ordered this chat — SUPERSEDED by the current sequence in the v16.49.1 head entry;
retained as the 21 Jul record. Items 0 and 1 are now DONE; the flats layer has since moved AHEAD of
the Option 3 mask — see v16.49.1):**
  0. **MN offshore diagnostic** — read-only, Sonnet. Prompt drafted and dispatched 21 Jul.
     Confirms or refutes the grid-regularity hypothesis with measured numbers, verifies the
     offshore points are LADS and not fault residue, and re-measures bytes-per-point. **Do not
     build against the derivation above until this returns.**
  1. **`r0` cache** — small, unblocks everything downstream, **must precede densification**.
  2. **Option 3 runtime mask** — land overpaint, all regions incl. the legacy blob (pending GO).
  3. **Flats layer** — process Moreton 2014/2018 + relabel SC/BR. **Needs NO new data.** Biggest
     single win available.
  4. **MN nearshore densification to ~90 m** — the "look like Bargara" lever. **Gate on running
     `storage_check.html` in the home-screen container FIRST**; the quota answer sets the point
     budget, not the reverse. Multi-chunk import (the 25k cap is per CSV parse, not per store).
  5. **Noosa tide-port wiring** — mechanical, BoM TP021 PDFs confirmed available, plain Sonnet.
  6. **Future-proofing:** desktop render harness (retires the ship→screenshot→guess loop that cost
     three R0 iterations); region-onboarding checklist in `CLAUDE.md`; **per-dataset `source_type`
     tag** (`bathymetric` / `topographic` / `sonar`) so the app renders and labels data classes
     differently instead of pretending ground elevation is seabed — the structural fix for the
     confusion that produced this whole thread.

**MN BATHY AS A RESOURCE BEYOND ITS OWN FOOTPRINT (new, opportunistic):** bathymetry does not
extrapolate geographically, but the full 946,877-pt LADS dataset has two uses elsewhere.
**(1) Calibration bench:** MN bathy overlaps the SC topographic footprint in the intertidal band
near the Maroochy mouth — where both exist, the topographic misread can be *measured* against real
survey, turning Option 3's 0.79% false-paint figure from OSM/WOfS agreement into ground truth.
**(2) Empirical spacing answer:** subsample the full 946k at 60/90/120/180 m and render offline to
establish what spacing actually looks like Bargara, without a phone round-trip. Both are free and
use data already on disk.

**NEW BACKLOG (low priority, neither blocks anything):**
  (a) **2021 Redcliffe Hydrographic Survey** — City of Moreton Bay DataHub, item
      `f6c1d8952e2447578215f4816ffe9ab6`
      (`https://datahub.moretonbay.qld.gov.au/datasets/f6c1d8952e2447578215f4816ffe9ab6`). SandMap
      Pty Ltd, two sites close offshore the Redcliffe Peninsula, commissioned for coastal modelling
      and to set out groyne extensions and seawalls **encroaching below the low tide mark**.
      Charted to LAT; **LAT = AHD − 1.23 m** per MSQ in the survey area, tied to Scarborough Boat
      Harbour and Woody Point tidal stations. Council open data. **The ONLY new
      instrument-measured, openly-licensed, nearshore, datum-solved source found in the entire
      sweep.** The research chat rated it low on the grounds that engineering sites aren't fishing
      spots — **disagreed here:** groynes and seawalls at Scarborough and Woody Point ARE
      land-based fishing structures, and the surveyed seabed is the water immediately off them.
      **INSPECT EXTENTS FIRST**, testing "is this off a fishable structure?" rather than "does it
      cover the peninsula?". Bin it if not. Diagnose-before-patch applies.
  (b) **AusSeabed coverage confirmation query** — Claude Code, Sonnet, read-only, ~15 min. Query
      the bathymetry survey-acquisitions coverage layer via OGC services
      (`warehouse.ausseabed.gov.au/geoserver`), clip to the SEQ AOIs, list any survey polygons
      touching them. Purpose is to convert this audit's negative from "read the description" to
      "queried the index," so it can be written in as permanent. **CAVEAT:** public coverage
      excludes anything supplied to GA under a Restricted and Exclusive licence, so a hit ≠
      obtainable data. Fold into whichever Sonnet session runs next — not worth its own session.

**DELETED FROM HORIZON (superseded, do not re-add):**
  - "Maroochy/Noosa blobby disc rendering — needs its own scoping session": scoped and shipped
    across v16.45/46/47 (inshore) and diagnosed above (offshore).
  - "Delete Navionics-traced contours near Innes Park + re-export backup" (standing since
    v16.44.2): confirmed long done, pre-dating all backups.
  - "Fable 5 included-plan window / pull Option 3 forward to catch pricing": window lapsed
    ~5 PM AEST Mon 20 Jul as expected; nothing queued required it.*

*v16.47 · 19 Jul 2026 — MN disc-rendering: GLOBAL R0 REPLACED WITH PER-SAMPLE ADAPTIVE R0
(build 2026.07.19b). v16.46's flat R0=56 confirmed failing on-phone in BOTH directions at once:
the Tewantin/Noosa Heads river corridor still showed a visible chain of discrete blobs, AND the
same global bump inflated Option A's already-known, previously-faint sub-HAT "messy tier"
(v16.43/44) into visible land-overpaint near Maroochydore. Root cause: a single global constant
cannot serve a sparse dataset (wants wide reach) and a dense-but-contaminated one (wants tight
reach) simultaneously. **Step 1 — how alpha is actually computed, confirmed from code before
designing anything:** `distA` (opacity) is driven by the SINGLE nearest sample's distance
(`near`), found in the same per-pixel bucket scan that ALSO builds the multi-sample IDW depth
field (`num`/`den`, weight `1/(dist²+1)`) — but depth combines every sample in the 3×3 bucket
neighbourhood while alpha uses only the minimum distance among them. This is exactly why one
flat radius can't work for both a sparse and dense region. **Step 2 — real Tewantin/Noosa Heads
corridor NN spacing, pulled from the CSV, not assumed:** 407 real MN points in a
-26.43..-26.36 lat / 153.02..153.11 lng box: median=141.7 m, **p90=175.0 m (essentially
identical to MN's overall p90=175.9 m that v16.46 was tuned against)**, but p99=206.1 m and
max=285.0 m — both worse than MN's overall p99=201.0 m. **Not a hard data-availability wall:**
a transect-line probe (along-lat vs along-lng axis nearest-neighbour medians, 226 m / 175 m)
found no sharp along-track-vs-lateral signature that would indicate missing lateral coverage —
consistent with the disc-render spike's own Finding 1 ("not a point lattice… arbitrary
coordinates", one point per 180 m export cell). The corridor's own p90 essentially matches the
global p90 v16.46 targeted; what actually broke it is structural: ANY global-percentile-tuned
flat radius leaves its own worst ~10% of gaps under-covered EVERYWHERE by definition, and in a
narrow linear river (only ~2% of MN's points, 407/19,178) those isolated worst-case gaps read
as a visible broken chain, where the same statistical rate would be far less perceptible spread
across a broad 2-D bay. **Step 3 — design:** `R0_local(sample) = clamp(gap(sample) − R1,
R0_MIN, R0_MAX)`, where `gap(sample)` is that sample's own nearest-OTHER-sample distance (found
via the SAME R1-sized bucketed index `buildShade()` already builds — no second index, no
per-pixel cost change, one extra O(n) pass over samples before the O(W·H) pixel loop). Derived
from the identical alpha(mid)≥0.5 criterion v16.46 used, applied per-sample instead of
globally. `R0_MIN=30` = the original pre-v16.45 value (dense clusters revert to exactly that
tightness). `R0_MAX=90` = 210−R1, matching the disc-render spike's own "practical NN ceiling
~210 m" design target — genuine >210 m gaps (isolated soundings, ~1% of MN) stay capped/faint
by design, per the spike's own "let them stay unpainted islands" guidance, not chased.
**Step 4 — SC Maroochydore overpaint, verified against real CSV samples (Aaron's literal
screenshot coordinates are on-device only, not available to this session — flagged as a proxy,
not the literal tapped point):** three real sub-HAT messy-tier candidates pulled from the CSV
(marginal depth −0.5<d<0, Twin Waters/Mudjimba/Bli Bli area) all resolve to **R0_local=30.0 —
an exact revert to pre-v16.45 tightness**, because they sit in locally dense clusters. Concrete
alpha at increasing offsets from one such point (Bli Bli area, −26.688922,153.129286): at +100 m,
pre-v16.45=0.222, v16.46=0.312 (40% more opaque — the visible overpaint), **adaptive=0.222,
identical to pre-v16.45.** Same pattern held at the other two points. **Step 5 — Tewantin
corridor gap closure, real gap-midpoints, not aggregate area:** across the corridor's 395
real nearest-neighbour gaps, the fraction of gap-midpoints reaching alpha≥0.5 rises
**60.0% (pre-v16.45) → 88.1% (v16.46) → 90.1% (adaptive)** — adaptive closes MORE of the
corridor than the flat global bump did, without the SC/BR side-effect. **Honest residual,
reported plainly per the brief:** the 5 largest real corridor gaps (216–246 m) exceed the
R0_MAX design ceiling (210 m) and stay low-alpha under every scheme tested (adaptive alpha
0.06–0.25 at those specific midpoints) — a real, quantified, structural limit at the extreme
tail, not a bug; matches the spike's own "let outliers stay unpainted islands" framing.
**Step 6 — three-point no-regression (real CSVs through the app's thin loop + real HAT gate):**
MN a50 45.8%(pre-v16.45)→60.2%(v16.46)→**53.3%(adaptive)**; SC a50 50.1%→56.9%→**50.9%**
(essentially reverted); BR a50 47.5%→54.1%→**49.5%** (essentially reverted). Adaptive
deliberately gives MN less aggregate coverage than v16.46's flat bump — that overshoot was
never the goal; closing the SPECIFIC gaps that create visible discs was, without dragging SC/BR
along for the ride. **Performance:** the new per-sample precompute is O(n) over the sample
count using the same bucket-scan pattern already run per PIXEL — structurally cheap relative to
the O(W·H) pixel loop it sits beside (typically W·H≫n); not independently browser-benchmarked
(no headless browser tooling in this environment, same limitation as prior sessions).
**Validation:** both script blocks `node --check` PASS; Leaflet block SHA-256
`db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`, byte-identical to
`9d5cebd`; `zoneAt()`/`ORDER` (index.html:1207/1296) and the green-zone dragend safeguard
(index.html:1542-1544) unchanged; diff scope reported verbatim, not asserted — exactly the two
build strings, the `R0`→`R0_MIN`/`R0_MAX` const + comment, a new per-sample precompute loop,
and the pixel-loop's `distA` line switching from the global `R0` to the nearest sample's own
`.r0`; R1, the HAT gate, and `depthSamples()` untouched; no SC/BR re-export triggered. On-phone
re-check queued: same Tewantin/Noosa Heads and Maroochydore-area screenshots as this session's
report, expect the corridor filled in and the Maroochydore land-overpaint back to pre-v16.45
levels.*

*v16.47.1 · 19 Jul 2026 — planning-chat review, no code shipped: build unchanged at 2026.07.19b.
Reviewed v16.47's per-sample adaptive-R0 fix before handoff — the derivation checks out
(nearest-neighbour math, the per-sample `R0_local` formula, the three real SC/BR proxy points
correctly reverting to `R0_MIN=30`, the Tewantin gap-closure numbers) and reverting dense
clusters to the pre-v16.45 baseline is the right call, since `R0=30` was never the problem —
MN's sparse tail was. Two items added to the on-phone re-check below, neither a correctness
concern with the fix itself: **(1) Performance, unmeasured:** the new per-sample precompute is
a fresh O(n) loop over the full loaded point pool — likely the entire multi-region set, not
just MN, since `buildShade()` has historically operated on the flat `pts` array (confirmed by
v16.40's diagnosis) — with a 3×3 bucket lookup per sample, run every `buildShade()` call.
Confirmed NOT to reuse the `Math.apply`/spread pattern that caused v16.40's iOS argument-ceiling
crash (plain for-loops and indexing throughout), but real-device cost is genuinely untested (no
headless-browser tooling in the build environment, same limitation v16.47 itself flagged) — this
project has a standing pattern of desktop-fine/phone-slow surprises, so add a plain "does
toggling shading feel slower than before" check alongside the visual ones. **(2) Verification
paper trail thinner than the established standard:** v16.45/46 both had `node --check` exit
codes and Leaflet SHA-256 pasted verbatim into the session; v16.47's validation step ran but its
output wasn't surfaced the same way — the roadmap's PASS/byte-identical claims are consistent
with everything else shown (same hash as the last two builds) so not treated as a live concern,
just noting the trail is thinner than usual should anything need re-tracing later.*

*v16.46 · 19 Jul 2026 — MN disc-rendering RE-TUNE SHIPPED (build 2026.07.19a): R0 raised again,
35→56 (R1=120 deliberately untouched), after Aaron's on-phone screenshot showed visible gaps
persisting near Mudjimba/Bli Bli under v16.45's R0=35. **Root cause of the miss, owned not
excused: v16.45 validated against the wrong criterion.** It matched MN's TOTAL alpha≥0.5 area
fraction to BR/SC's aggregate baseline — an area metric that a field of slightly-fatter discs
can satisfy without ever becoming contiguous. MN's spacing has a real tail (p90 gap 175.9 m,
p99 201 m, ceiling ~210 m — this session re-derived those numbers independently from the CSV
and they match the spike exactly); at a p90 gap the midpoint sits ~88 m from the nearest
sample, where alpha was 0.377 under R0=35 (and 0.356 under the original 30) — that near-R1
low-alpha tissue is precisely the visible hole. **New criterion, per the re-tune brief: alpha
≥ 0.5 AT the p90-gap midpoint itself.** Worked from buildShade()'s real ramp read from the
file (index.html:2014, `distA=near<=R0?1:(near>=R1?0:1-(near-R0)/(R1-R0))` — verified linear
between R0 and R1, and verified `AL` reaches paint un-smoothed: `smoothField()` takes it as a
read-only validity mask and only smooths the depth field FD): alpha(88)=(120−88)/(120−R0) ≥
0.5 ⇒ R0 ≥ 56. **R0=56 is the smallest integer clearing the target — p90-midpoint alpha =
0.5009, reported explicitly against the target as required** (R0=55 gives 0.4932, just under).
The p90 target IS reachable via R0 alone, so R1 was not touched and the stop-and-report branch
in the brief was not triggered; 56 is judged not uncomfortably high — under half of R1, ramp
still spans 64 m, and BR/SC read as a denser wash, not saturation. **No-regression verified
empirically (same real-data replica methodology as v16.45 — real CSVs through the app's own
thin loop + real okHAT gate):** MN a50 48.6%→60.2%, a75 27.2%→42.6%; SC a50 51.5%→56.9%; BR
a50 48.9%→54.1% — every metric flat-or-up, none down; legacy Woongarra (on-phone only, not in
repo) is covered by the same structural monotonicity argument as v16.44/45: raising R0 can
only raise alpha at any fixed distance. Painted-at-all footprint remains R1-bound — the
84.5%→84.7% MN tick is a sub-metre sliver at the very edge of R1 crossing the a>0.01
threshold, not new geographic reach; land-overpaint behaviour cannot change (HAT gate
upstream, unchanged; R1 unchanged). **Accepted residual, quantified up front:** the p99+ tail
(~1% of points, ~200 m+ gaps) still fades — midpoint alpha ~0.30 at p99, ~0.23 at the 210 m
ceiling — same accepted-residual framing as Option A's known gap; if faint patches show
on-phone at THOSE spots, that's the known tail, not a failed fix. **Validation:** both script
blocks `node --check` PASS; Leaflet block byte-identical to HEAD; `zoneAt()`/ORDER + green-zone
dragend safeguard untouched (diff is exactly the R0 const, its comment, and the two build
strings); both style blocks untouched. On-phone re-check queued: Mudjimba/Bli Bli area
specifically (the reported gap sites), expect contiguous wash at p90-scale gaps, tolerate
faint patches only at rare 200 m+ tail gaps.*

*v16.45 · 18 Jul 2026 — MN blobby-disc cosmetic fix SHIPPED (build 2026.07.18a): buildShade()'s
R0 raised 30→35 (R1=120 unchanged), per `data/raw/_discrender_spike/DISC_RENDER_SPIKE.md`'s
finding that MN's discrete-disc look is an alpha-ramp calibration issue meeting 126 m-median
sample spacing, not a coverage gap, and that the v16.44 HAT gate filters upstream of every R1
check at `depthSamples()` itself — so this radius-only ramp change cannot reopen the
land-overpaint bug (re-confirmed this session by reading `buildShade()`: R0/R1 are `const`,
local to `buildShade()` at line 1988, not shared with `okHAT`'s `-nearestPort().hat` threshold
or with `buildAutoContours()`'s own separate `R1=120` declaration — no shared-constant risk
existed). **Methodology, reproduced not assumed:** a Node-side replica of `buildShade()`'s exact
alpha ramp + sample-index code, run against the real `maroochy_noosa_bathy_v2_appgrade.csv`
(19,178 pts) and the real `sunshine_coast`/`brisbane_river` v2 CSVs pushed through the app's own
25k auto-thin loop AND the real `okHAT` gate (same `nearestPort()` routing, same `PORTS[].hat`
values) — i.e. the actual on-phone-equivalent post-Option-A density, not the pre-fix numbers the
spike itself used. Baseline at shipped R0=30 reproduced the spike's own MN number almost exactly
(84.5% painted-at-all / 23.9% alpha≥0.75, vs the spike's 84.4%/23.9%), confirming the replica is
faithful. **SC/BR's own current alpha≥0.5 baseline computed as the fair target (not assumed
~100%):** SC 50.1%, BR 47.5% (blended 48.8%) — both markedly lower than the pre-v16.44 spike
numbers because the HAT gate now excludes ~60% of SC/BR's points as above-HAT dry land; this is
the correct, current comparison, not the stale one. **R0=35 chosen** as the smallest value
clearing that blended target: MN's alpha≥0.5 coverage moves 45.8%→48.6% (within 0.2 pp of the
48.8% blended target). **No-regression, verified empirically not just asserted:** raising R0 can
only ever increase alpha at a fixed `near` distance (monotonic in the ramp formula) — confirmed
against the real MN/SC/BR data: all coverage metrics (painted/a25/a50/a75/core) flat-or-up,
none down. **Land-bleed structurally impossible, not just checked:** the "painted at all"
(near≤R1) footprint — the actual geographic extent that can ever receive any paint — is set by
R1 alone, untouched this session; verified byte-identical before/after for all three datasets
(MN 84.5%, SC 71.2%, BR 68.3%, unchanged to one decimal). Raising R0 only redistributes opacity
*within* the existing footprint; it cannot paint a new pixel. **Honest limitation, not smoothed
over:** a synthetic native-resolution (35 m/px) visual crop of MN before/after shows a real but
modest textural change, not a dramatic disc-to-wash transformation — the numeric target was hit
exactly as scoped ("smallest R0", per the brief, not "eliminate all texture"), but the true
perceptual verdict depends on Leaflet's own screen-scale image compositing over satellite tiles,
which cannot be exercised headlessly in this environment (no browser-automation tooling
installed, and MN's real dataset lives only in Aaron's on-device localStorage, not this repo).
**Mandatory on-phone check queued, not fabricated:** screenshot MN water at a normal zoom
(expect a visibly denser wash, not necessarily perfectly smooth) and a quick BR/SC/Bargara
sanity check (expect unchanged — the structural land-bleed argument above already rules out
regression; this is a confirmation step, not a discovery step). **MN region re-tag folded in
per spike carry-forward:** `#imp-region` dropdown gains a real "Maroochy / Noosa" option
(`maroochy_noosa` key); `regionLabel()` knows it; a one-time boot-time migration renames any
existing `datasets.custom` (the free-text "Other…" fallback key Aaron's MN import landed under,
since the field was left blank) to `datasets.maroochy_noosa` if present — mirrors the existing
`legacy_unknown` migration pattern, fires once, no functional effect (region keys were never
consulted by `depthSamples()`/`rebuildImportedFlat()`, confirmed v16.40). **Validation:** both
script blocks pass `node --check`; inlined Leaflet block confirmed byte-identical to HEAD;
`zoneAt()` + `ORDER` (MNP>CPZ>HPZ>GUZ) unchanged; green-zone dragend safeguard
(index.html:1542-1544) unchanged; both style blocks untouched; diff scoped to exactly the four
intended edits (R0 value + comment, region dropdown option, `regionLabel()` entry,
custom→maroochy_noosa migration) plus the two build-string bumps. Did NOT touch R1, the HAT
gate, `depthSamples()`, Option 3, or any Noosa tide-port code, per the session's explicit scope.*

*v16.44.2 · 18 Jul 2026 — planning note, no code shipped: **on-phone Woongarra check CLOSED,
v16.44 ACCEPTED.** Four taps across two sessions (2 screenshots each), read against the real
`index.html` (not inferred). Tide port correct in all four (Burnett Heads +2.2/+2.3). **Both
`waterNowText()` branches verified correct against source:** `wn=t+d` with d signed — dries
(d<−0.05) prints "X m over it now"/"exposed now", depth prints "now ~X m water". Elliott River
mouth dries 1.1 m, tide +2.2 → "1.1 m over it now" (2.2−1.1, exact). Barolin Rock depth 4.0 m,
tide +2.2 → "6.2 m water" (2.2+4.0, exact). The 1.1 m dries reading is direct on-phone evidence
the gate correctly keeps HAT-adjacent legitimate intertidal (1.1 m < Burnett Heads HAT 3.70 m,
v16.44) rather than dropping it. **A suspected sign bug raised earlier in this session (against
two prior Innes Park screenshots showing "≈2.2/5.1 m depth" and "~4.4/7.4 m water" over visibly
dry land) is RETRACTED.** Root cause, confirmed by reading `depthSamples()`: those two points
were NOT imported/dries samples at all — they were **Navionics-traced contour lines** (Aaron
confirmed manual tracing in that area, done early in the project, before the standing
no-chart-art-for-depth rule hardened). `depthSamples()` samples the `contours` store at ~1/12
polyline spacing and feeds it into the shared sample pool alongside imported data; those traces
carry positive depth values, which trivially pass the `d>-HAT` gate (built to catch above-HAT
*dries*, not to vet contour provenance) — so the interpolator confidently reported "water" over
land using real code executing correctly on out-of-policy data. Not a v16.44 gap, not
interpolation overshoot, not a gate bug. **Open data-hygiene item, Aaron's call, no code needed:**
delete the land-adjacent traced contours at Innes Park (per-line ✕ in the contours panel, or
"Clear all contours" — `woongarra_contours_v1`), then **re-export a fresh `version:2` backup
immediately** — contours merge back in by ID on restore, so an old backup would silently
resurrect them. Shading near Innes Park will visibly change once they're gone (expected, not a
regression). **v16.44 is now fully accepted — no further on-phone action queued for it.***

*v16.44.1 · 18 Jul 2026 — planning note, no code shipped, no `index.html` change: session-close
review of v16.44 plus a time-boxed model-routing note for the next Claude Code session.
**HAT cross-check completed for the two ports v16.44 didn't independently verify** (only
Mooloolaba was checked against a published source at build time; Burnett Heads and Brisbane Bar
were not). Checked directly against MSQ's 2020 Semidiurnal Tidal Planes table: published HAT is
Burnett Heads/Bargara **3.67 m** and Brisbane Bar **2.73 m**, both *below* the embedded-table-max
values the gate actually uses (3.70 m / 2.81 m) — confirms all three ports sit in the
conservative/safe direction, not just Mooloolaba (same logic v16.44 already applied there: a
higher threshold protects HAT-adjacent ledges from wrongly dropping out). Note: MSQ moved to a
newer 2010–2029 tidal-datum epoch in a 2022 table edition, so today's authoritative figures may
differ by a few cm from this 2020 source — not close enough to the used values to matter. Does
NOT close the outstanding item: the real acceptance test is still the on-phone Bargara tap,
not yet run (see v16.44 and the next-session note below). **Fable 5 plan-inclusion window closes
soon — a sequencing note, not a roadmap change:** Anthropic's promotional inclusion of Fable 5 in
Pro/Max/Team weekly limits (up to 50% of the weekly cap, no extra charge) has been extended
twice already (7 Jul → 12 Jul → 19 Jul) and is currently set to end **19 Jul 2026, 11:59:59 PM
PT** — roughly **5 PM AEST Monday 20 Jul** in Brisbane (PT is UTC−7 in July; AEST is UTC+10; no
further extension confirmed as of this note, but two prior extensions mean it's worth checking
support.claude.com before treating this as final). After that, Fable reverts to metered usage
credits ($10/$50 per Mtok) unless credits are funded. **No item in the current backlog is both
ready-to-run and cleanly Fable-shaped under the existing rules:** the one long-autonomous-batch
candidate, Option 3's real SC/BR v3 re-export, is explicitly gated "don't trigger standalone,
ride along with a future re-export" (v16.43) — that gate was about avoiding duplicate re-import
churn, not data safety, so running it now instead of later isn't a correctness risk, but it is a
conscious call to move it up in sequence purely to catch the pricing window. Left for Aaron to
decide going into the next session; not pre-authorised here. Gold Coast's raw-LiDAR processing
(parked, last sequenced) would be the other Fable-shaped candidate if that data has finished
landing — worth a 30-second check before the session starts. If neither is greenlit, plain
Sonnet work (the on-phone check, Noosa wiring) proceeds as normal — Fable isn't required for
anything currently queued.*

*v16.44 · 13 Jul 2026 — land-overpaint FIXED, Option A (elevation-aware gate), build
2026.07.13a. Confirmed root cause (v16.41): SC/BR intertidal exports carry supratidal ground
(above HAT, genuinely dry) inside a −3..+5 m AHD band, and v16.25's distance-only fallback
treated any such point as coastal/intertidal evidence regardless of how far above the highest
tide it sits. **Fix, applied at the single shared upstream gate (`depthSamples()`), not
per-call-site:** each sample is now dropped from the shared sample pool unless `d>-HAT[port]`,
where the port is picked via `nearestPort({lat,lng})` — the exact coordinate-routing pattern
`tideHeightNow(lat,lng)` already uses (v16.41), reused rather than reinvented; `port_offset()`
(Python-only, `export_csv.py`, AHD→LAT bake-time conversion) is a separate mechanism and was
correctly left untouched. Because `depthSamples()` is the sole upstream source for
`buildShade()`, `buildAutoContours()`, and `idwIndex()` (which itself feeds `idwDepthAt()`,
consumed by tap-read `openDepthRead`, `findDeepest`, and the desktop hover-readout), all five
v16.25 call sites — plus the slope/profile tool as a beneficial side effect — inherit the fix
uniformly with zero per-site changes; none of R0/R1/near≤80/near≤120 or any depth-sign logic
was touched. **HAT sourced conservatively, not guessed:** `PORTS[].hat` = the max height across
BOTH embedded tide-table years (2026+2027) per port — Burnett Heads 3.70 m, Brisbane Bar 2.81 m,
Mooloolaba 2.24 m. Deliberately the two-year embedded max rather than Mooloolaba's separately
published HAT (2.21 m, MSQ Semidiurnal Tidal Planes) because the embedded max is *higher* —
using it is the direction that protects HAT-adjacent intertidal ledges from wrongly dropping
out. Optional dries colour ramp SKIPPED per session brief (adds real complexity to
`depthColor()`, gate is the deliverable). **Validation, run against the real edited code slice
via Node vm (not reimplemented) over the actual 113,557-pt on-phone dataset replica** (SC v2 +
BR v2 + MN v2 appgrade, same load+thin loop as the v16.41/v16.43 diagnoses — replica count
matches the phone-reported total exactly): **(a) known-dry probes** (Twin Waters GC, Sunshine
Motorway, Bli Bli, Maroochydore CBD) — all four now EXCLUDED from the shared sample pool
(correct); **(b) known-wet soundings** — MN d≥2m cohort (n=18,510) and all 9 v16.41
stale-popup locations 100% unchanged/kept (correct); overall SC 59.9% / BR 61.8% of imported
points now excluded as above-HAT (consistent with v16.41's blended 63%/74% estimate, the
difference being per-port-exact HAT vs that entry's flat −2.2 m approximation). **(c)
Bargara/Woongarra regression risk — flagged, not silently assumed clean:** the legacy Woongarra
dataset (55,660 pts) exists only in Aaron's phone localStorage, not in this repo, so it cannot be
numerically diffed offline. Two things ARE proven instead: a structural no-regression argument
(the gate only ever *removes* points relative to the old code — any sample with d>−3.70 is
byte-identically kept, so nothing already-included can newly disappear except genuinely
above-HAT ground) and a synthetic boundary check at Bargara's coordinates (d=−2.90, matching the
real Burnett tide reading recorded in v16.41, correctly KEPT; d=−3.70 exactly at HAT, correctly
excluded per the strict `d>-HAT` inequality). **The real acceptance test is an on-phone check —
tap the same Bargara rock platform pre/post-build and confirm the reading is unchanged — same
pattern as v16.41/v16.43.1's tide-fix confirmation; queued, not yet run.** Both script blocks
node --check PASS; Leaflet block byte-identical to HEAD; `zoneAt()` unchanged; green-zone
dragend safeguard intact (7/7); both style blocks untouched; app-block diff scoped to exactly
the two intended edits (depthSamples() + PORTS). Does NOT fix the unshaded river channel
(topo LiDAR can't see mid-channel water — data-availability ceiling, out of scope) and knowingly
leaves ~53–58% of the sub-HAT "messy tier" still painting (quantified in v16.43) — accepted, to
be closed later if/when Option 3 rides in on a future SC/BR re-export.*

*v16.43.1 · 13 Jul 2026 — planning note, no code shipped: on-phone confirmation of the v16.41
tide-port fix (build `2026.07.11a`) COMPLETE. Build string confirmed correct across all
screenshots. Sunshine Coast taps (Maroochydore-area, Twin Waters/Mudjimba) both showed a tide
+0.9 m offset — sane Mooloolaba-scale, arithmetic checks (4.1+0.9=5.0 m, 3.2+0.9=4.1 m),
consistent with the fix and nothing like the old Burnett-style +3.2 m reading. Bargara/Woongarra
(Elliott Heads) zone popup confirmed correct (CPZ07 Conservation Park); a follow-up water-depth
tap (the first four screenshots only showed "dries"/exposed-sandbank readings there, which don't
carry a tide offset and didn't actually test the fix) confirmed unchanged Burnett Heads-scale
tide, closing that gap. **Item 1 is DONE — no further phone checks needed for v16.41/v16.42.**
Noted in passing, not new: the land-overpaint bug is visibly present in the Sunshine Coast
screenshots (green shading over dry paddocks near Sunshine Motorway) — already diagnosed
(v16.41), unchanged, exactly what the Option A build addresses next.*

*v16.43 · 13 Jul 2026 — Option 3 (real land/water mask) investigation spike complete,
INVESTIGATION ONLY: no `index.html` change, nothing committed (scratch report in gitignored
`data/raw/_landmask_spike/`), build string unchanged at `2026.07.11a`. Ground truth reused from
the v16.41 diagnosis (diag1/diag2 load+thin replica, diag3 pilot bbox): confirmed-dry = 3,684
above-HAT SC replica points, confirmed-wet = 7,981 MN soundings ≥2 m below LAT (incl. all 9
stale-popup locations), messy tier = 1,513 sub-HAT ambiguous points. Scored two candidate
sources + a hybrid across 13,178 pilot points: OSM alone (2.06% false-paint, 99.77% wet
coverage kept), DEA WOfS alone (2.04%/99.75% at freq≥0.2), **STRICT-AND hybrid (0.79%
false-paint, 99.74% coverage kept** — residual false-positives are beach-swash/suburban edge
pixels). Every named dry probe reads land on both sources; all 9 stale-popup locations read
water (≥0.97) on both — either source alone would have caught the v16.40/v16.41 incident.
Defect-zone grid (Maroochy Wetland Sanctuary, 36 pts) reads correctly as land on both (OSM
36/36, WOfS 34/36), confirming the mask catches the defect *class*, not just this instance.
**Option A's known gap quantified:** 53–58% of the sub-HAT messy tier (~800–880 pilot points)
reads dry-land under the mask — real coverage Option A will keep painting; an accepted,
already-known limitation, not a reason to hold Option A back. Edge cases, reported not
smoothed over: beach/swash is the one genuine friction point (WOfS nodata on surf pixels, OSM
coastline sits at ~MHWS); OSM and WOfS fail in different places (canal estates/golf lakes vs.
narrow mangrove creeks, ~0.25% of wet points) — the actual case for AND over either source
alone. **Recommendation:** hybrid STRICT-AND mask, applied bake-time as a per-point tag in the
v3 CSV export (zero `index.html` change) — but reaching the phone requires a full SC/BR v3
re-export + re-import, the same churn as Option B, so **don't trigger this standalone** — ride
it along with any future SC/BR re-export rather than running it alone while Option A holds.
Runtime in-app alternative (polygon union + conjunct at the shared v16.25 gate) avoids
re-import churn but adds 0.3–0.8 MB to the 2.1 MB single file. **Flag:** OSM is ODbL vs. the
project's CC BY sources elsewhere — fine for personal use, noted for the record. Long-run
discipline held (checkpoint/resume smoke-tested with a deliberate interrupt-and-resume, pid
19716 full run: progress/1,000, checkpoint/2,000). `git status` clean, only the known
`guya_species_qld_v3.md` untracked.*

*v16.42 · 13 Jul 2026 — Brisbane Bar + Mooloolaba 2027 tide tables MERGED (build 2026.07.11a),
closing v16.41.1's data chore (1) — from Jan 2027 those two ports' popups would have silently
dropped tide text. **Source:** BoM NTC official per-port prediction PDFs
(bom.gov.au/ntc/IDO59001/ — `IDO59001_2027_QLD_TP003.pdf` Brisbane Bar,
`IDO59001_2027_QLD_TP019.pdf` Mooloolaba), the same NTC prediction series behind the MSQ
Queensland Tide Tables (© Commonwealth of Australia, Bureau of Meteorology — BoM is the credited
author of the MSQ tables). Checked first: MSQ's own tide-tables page and the data.qld.gov.au
open-data CSVs (CC BY 4.0) are both still 2026-only — the whole-year MSQ 2027 PDF isn't
published yet; BoM publishes per-port 2027 a year ahead. **Parser proven by round-trip, not
assumed:** the same column-aware pdfplumber parse (8 sub-columns/page, weekday prefixes glued to
times) re-run on BoM's 2026 PDFs reproduced the shipped `BRISBANE_TIDES_2026` and
`MOOLOOLABA_TIDES_2026` embeds exactly — 365/365 days identical for both ports — which also
confirms the BoM per-port PDFs carry predictions identical to the MSQ tables the 2026 embeds
came from. **Validation (all PASS, both ports, both years):** weekday cross-check 365/365
(2027; 364/364 markers on the 2026 controls), all 365 dates present, 1–4 events/day, strictly
increasing times, strict H/L alternation by continuous phase — 0 violations across 1,411 events
each; Mooloolaba 2027 max 2.24 m vs published HAT 2.21 m (same near-match as 2026's 2.22 m);
Brisbane Bar 2027 max 2.81 m (its 2026 embed tops at 2.79 m). **Merge mirrors Burnett exactly:**
`BRISBANE_TIDES_2027`/`MOOLOOLABA_TIDES_2027` consts + `Object.assign(...2026,...2027)` — one
lookup spans 2026–2027; pure data addition, `tideHeightNow()`/`waterNowText()`/`nearestPort()`
untouched (confirmed all consumers go through `PORTS[].table`, which Object.assign extends in
place); the stale "Brisbane Bar/Mooloolaba tables are 2026-only" comment inside tideHeightNow()
updated. Runtime-verified in a Node VM against the REAL code slice from index.html: all three
ports now span 730 days (2026-01-01→2027-12-31) and simulated mid-2027 taps at
Bargara/Redcliffe/Maroochydore return real tide heights via the real
nearestPort()+tideHeightNow() path. Both script blocks node --check PASS; Leaflet block
byte-identical; zoneAt() + green-zone dragend safeguard intact; both style blocks untouched.
Chore (2) remains open — Noosa still resolves to Mooloolaba as a stopgap and still needs wiring
as its own Standard Port.*

*v16.41.1 · 12 Jul 2026 — planning note, no code shipped: v16.41 (tide-port fix, build
2026.07.10a) pushed and confirmed on `origin/main` (`cc2c2dd`) — no repeat of the v16.26
unpushed-commit stall; `git status` confirmed clean and up to date immediately after push.
On-phone confirmation still pending: build string should read `2026.07.10a`, a Bargara/
Woongarra tap should read unchanged (Burnett Heads), and a Sunshine Coast/Brisbane River tap
should read Mooloolaba/Brisbane Bar-scale (≤~2.2 m), not the old Burnett-style +3.0 m+ readings.
Two items flagged for the backlog, not urgent: **(1)** Brisbane Bar and Mooloolaba tide tables
are 2026-only (Burnett already has 2027 merged) — from Jan 2027 those two ports' popups will
silently drop tide text rather than show a wrong one; needs a table refresh before then.
**(2)** Noosa currently resolves to Mooloolaba as an interim stopgap (v16.41) — this is **NOT**
the final answer; Noosa Head is on record as its own MSQ Standard Port (2024 Semidiurnal Tidal
Planes table, no offset math needed) and still needs wiring as its own port in a future session.
Don't let "resolves to Mooloolaba" be misread as the intended end state by a future session.*

*v16.41 · 12 Jul 2026 — tide-port bug FIXED (build 2026.07.10a) + land-overpaint ROOT CAUSE
CONFIRMED (diagnosis only, that fix not yet scoped). **Tide fix:** `tideHeightNow()` hardcoded
`BURNETT_TIDES_2026` regardless of location, so every depth popup outside Woongarra applied
Burnett Heads tide — the "+3.2 m" on the Maroochy-area popup (Mooloolaba's real 2026 table tops
out +2.22 m). Now `tideHeightNow(lat,lng)` selects the table via the pre-existing
`nearestPort()`/`PORTS` helpers (already used by wind/best-bite, never by popups) against the
QUERIED POINT, not map centre; `waterNowText(d,lat,lng)` passes the coordinate through at all
three real call sites — tap-read `openDepthRead`, `findDeepest` popup, desktop hover readout
(the session brief's "5 call sites" was the paint-gate list; shading/auto-contours never consume
tide). No-coords calls fall back to PORTS[0]=Burnett Heads, matching legacy behaviour exactly.
Noosa deliberately NOT given its own port (separate flagged item) — Noosa resolves to Mooloolaba
for now. Brisbane Bar/Mooloolaba tables are 2026-only (no 2027 merge, unlike Burnett) — from Jan
2027 non-Woongarra popups will drop the tide text rather than show a wrong one; data chore
flagged. Validation: both blocks node --check pass; Leaflet byte-identical; zoneAt() + dragend
safeguard intact; simulated taps — Bargara→Burnett Heads numerically identical to the old code
(regression clean), Pinkenba/Redcliffe→Brisbane Bar, Maroochydore/Coolum/Noosa→Mooloolaba
(+1.68 m at test time vs Burnett's concurrent +2.90 m; +3.2 is now unreachable there).
**Land-overpaint diagnosis (read-only, validated against an exact on-phone dataset replica —
import/thin loop reproduces the 113,557 count byte-for-byte): the R1=120 m halo hypothesis is
DISPROVEN as the primary mechanism — the samples are ON the dry land itself.** The intertidal
exports were built with a −3..+5 m AHD band (`process_tiles.py`, "land-based reachable band"),
so 63% of on-phone SC points and 74% of BR points sit above HAT (>2.2 m above LAT) — golf
courses, suburbs, motorway embankments sampled at ~87 m spacing, all painted by v16.25's
any-sample-within-120 m rule. Tightening R1 cannot fix this (even R1=0 still paints). Scale:
BR painted footprint is 79.3% certainly-dry (110.5 km²); SC 11.7% (46.8 km²: Maroochydore CBD,
Bli Bli, Twin Waters/Mudjimba, Buddina, Pelican Waters clusters). The unshaded river channel is
the same coin's other face: no mid-channel samples exist (topo LiDAR can't penetrate; only 62
of 19,178 MN bathy points fall in the Maroochy corridor). The "≈14.8 m / 106 m" popup reproduces
at exactly 9 locations, ALL ~1–1.5 km offshore over 13–17 m MN soundings — a fresh golf-course
tap in the replica returns the DRIES branch, so that popup was almost certainly stale from an
earlier over-water tap (the Gympie screenshot already proved popups persist across pan/zoom) or
influenced by on-phone manual pins/traced contours (in `depthSamples()`, not in the repo).
Phone check queued: fresh tap on the golf course, expect "dries ≈ …". All five gate call sites
equally affected (findDeepest marginally tighter at 80 m). depthColor() renders ALL negative
field values as the single mint <0.25 m band — why dry land reads as one flat mint wash. Candidate
fixes for the scoping session, in rough preference order: (A) elevation-aware gate — dries
samples only qualify as paint/read evidence where the local estimate is above −HAT per port
(reuse the `port_offset()` latitude-bucket pattern), optionally with a dries colour ramp;
(B) re-export SC/BR v3 with ELEV_MAX≈HAT — cleanest data but re-import churn and loses
legitimate above-HAT platform readings; (C) real land/water mask — most robust, heaviest.
Diagnosis scripts in session scratchpad (`diag1–3.js`).*

*v16.40.1 · 12 Jul 2026 — planning session, NO code shipped: on-phone confirmation received —
v16.40's shading fix works, tint now paints over Sunshine Coast, Brisbane River, and Maroochy
Noosa (closing that build's mandatory on-phone check). **NEW incident found in the same
screenshots:** shading (and, per the identical shared gate, plausibly tap-read/`findDeepest()`/
`buildAutoContours()` too) is painting over genuinely DRY land in the Sunshine Coast area — a
golf course, suburban blocks, and a stretch of Sunshine Motorway all show the mint-green wash,
while the actual river channel running through the same scene is the one thing NOT shaded. A
tap over the shaded golf-course land returned "≈14.8 m … low confidence … nearest data 106 m
away … ~18.0 m water" — a water-depth-style estimate reported over land that is unambiguously
not water. **Leading hypothesis, NOT yet confirmed — investigate before patching:** this is
plausibly the v16.25 fix operating exactly as designed, now exposed by far denser data. v16.25
deliberately widened the shading/tap-read distance-bounded fallback so that being within
R1=120 m of ANY real imported sample — dries OR sounding — counts as sufficient evidence of
real coastal/intertidal ground, dropping the old depth-sign requirement (necessary at the time
because most Sunshine Coast/Brisbane River points are "dries," i.e. LiDAR ground returns, not
soundings). At the original Coolum-era density that 120 m halo around scattered points stayed
close to the coast; with Brisbane River's and Sunshine Coast's much denser point sets, a 120 m
radius around riverside "dries" ground points can plausibly reach genuinely dry hinterland —
golf courses, roads, suburbs — that happen to sit within 120 m of a river/estuary edge. This
would also explain why the river channel itself is unshaded: topographic LiDAR can't penetrate
open water, so there may be no samples directly over mid-channel water to shade from, while
nearby bank samples paint outward onto the land side instead. **Unconfirmed — must be verified
against the real CSV and the exact tapped coordinate, not assumed.** A second screenshot
showing the identical popup values (14.8 m, "nearest data 106 m away," tide +3.2) while the map
was panned/zoomed out to a Gympie-area view (~20 km scale, tens of km inland) is presumed to be
the SAME stale, un-recalculated popup left open across the pan/zoom, not a fresh tap producing
a bogus far-inland reading — flagged for confirmation, not treated as a second bug. **Separately,
Aaron flagged the Maroochy Noosa "blobby"/disc rendering (~23% coverage, R1=120 m vs the
180 m export grid) as something he wants improved, not just accepted** — v16.40 had documented
this as expected-not-buggy; reclassified here as an open cosmetic backlog item, independent of
and lower-priority than the land-overpaint bug above (that one is a correctness/accuracy issue;
this one is a visual-density preference on already-correct data). Read-only investigation
queued for the land-overpaint bug (priority); blob-density improvement queued as backlog, not
urgent. No code touched.*

*v16.40 · 12 Jul 2026 — shading engine-argument-limit crash FIXED (build 2026.07.09a): the
"no shading over Brisbane River / Sunshine Coast / Maroochy Noosa" report traced (read-only
investigation, this session's fix) to `buildShade()`'s bbox calc using
`Math.min.apply(null, pts.map(...))` over the full flat depth-sample array — 113,557 elements.
`Function.prototype.apply` passes the array as literal call arguments; iOS JavaScriptCore's
argument ceiling (~65,536) is far below desktop V8's (~124,700 at default stack), so on-phone
the first bbox line threw RangeError, buildShade() aborted before painting anything, and the
exception was swallowed (event-listener errors go to console, not UI) — the toggle appeared to
do nothing. **NOT a v16.39 regression** (that diff preserved every buildShade/rebuild call
1:1), **not region-related** (imported is a flat array; no code consults region keys — the
"custom" Maroochy Noosa tag is harmless), **not a durability issue** (all 113,557 pts loaded
fine; tap-read worked over every region because idwDepthAt() is plain loops, no apply, and is
gated only on shadeOn — which is set BEFORE buildShade() throws). **For the record: shading
has plausibly been silently broken for ALL regions including Bargara since v16.28**, when the
store first crossed 65,536 (legacy 55,660 + Brisbane River 20,794 = 76,454) — the v16.28
"looks like bare land" tap-read screenshots were popups over an unpainted map, and the
"Bargara still shades" premise in this session's report was inferred from tap-read, a separate
code path. **Fix:** new O(n) `ptsBounds()` helper replaces all four apply calls in
buildShade() AND the identical dormant pattern in buildAutoContours() (would have thrown the
moment auto-contours was toggled at current data size). Spread syntax deliberately NOT used —
it hits the same engine ceiling. `Math.max.apply` over transect verts (~1867) left as-is:
small array, out of reach of the ceiling. **Validation:** both blocks node --check pass;
Leaflet byte-identical; zoneAt() + green-zone dragend safeguard intact; regression harness
rebuilt the exact on-phone 113,557-pt shape (real v2 CSVs through the app's own thin loop —
counts match the phone byte-for-byte — plus 55,660 synthetic legacy): old apply code throws
RangeError at node --stack-size=500 (proving the harness catches the bug class; default V8
stack tolerates it, which is exactly why desktop never reproduced this), new ptsBounds never
throws and returns a bbox numerically identical to a chunked apply-based control under every
stack tested. **DESKTOP CANNOT CONFIRM THIS FIX — mandatory on-phone step:** toggle shading on
over Sunshine Coast, Brisbane River, Maroochy Noosa AND Bargara water and confirm tint
actually appears (not merely no error). **Expected-not-buggy once it works:** Maroochy Noosa's
180 m export grid vs the shader's 120 m paint radius (R1) renders as ~23%-coverage discs
around samples, NOT a continuous wash — do not misread that as a fresh bug; Brisbane River /
Sunshine Coast are dense enough to paint solidly.*

*v16.39 · 12 Jul 2026 — v16.38 fix SHIPPED (build 2026.07.08a): boot-time durability receipt
(Fix A) + region-scoped rollback (the region-scoped half of Fix B), per the v16.38 diagnosis
(iOS WebKit same-session read-back can never detect an async flush-to-disk failure).
**Fix A:** after every save that passes the existing read-back+count-check,
`saveDatasetsVerified()` now writes `woongarra_imported_receipt` — a per-region point-count map
+ savedAt, ~100–150 B, counted from the read-back itself. On boot the receipt is compared
against the actually-loaded `woongarra_imported_v2`; any divergence (count mismatch, or a
region present that the last verified save never had) raises a persistent banner in the
existing `#imp-save-err` slot: "Last import didn't survive a restart — re-import required
(…per-region detail…)". The banner clears on the next verified save and re-raises on the next
boot if that save didn't reach disk either. If the receipt write itself fails synchronously,
the key is removed so a stale receipt can't false-alarm. **Known blind spot, accepted:** if the
store write AND the receipt write both fail to flush (app kill before any flush), boot sees a
consistent older pair and cannot alarm — the receipt is tiny and written after the big store
write, so the quota-pressure case (big write dies, small one survives) is the one it catches;
the v16.38 interim force-close/reopen protocol therefore stays in effect regardless.
**Region-scoped rollback:** `snapshotImpRollback()` (whole-store, single shared slot) replaced
by `snapshotImpRegion(region)` writing per-region slots `woongarra_imported_rollback_v2:<key>`
holding {at, region, dataset|null} — null records "region didn't exist," so Undo deletes it.
Transient import cost drops from (store + whole-store copy) to (store + one region copy),
freeing the ~1.5 MB headroom v16.38 predicted. MERGE now snapshots (previously it had NO undo
coverage); ✕-remove and REPLACE snapshot their one region; Clear-ALL and backup-restore
snapshot every affected region (old ∪ new keys for restore), and Undo restores ONE region per
press, newest slot first — repeated presses walk back a whole-store operation region by region.
On a snapshot write failure the region's stale slot is deleted so Undo can never restore a
wrong prior state (a latent flaw the old single-slot code shared). Undo button relabelled
"↩ Undo last replace/merge/remove"; its confirm names the region and states others are
untouched. **Dead `woongarra_imported_rollback_v1` is removed at boot — ~2.17 MB reclaimed**,
closing that cleanup item. Out of scope, untouched: IndexedDB migration (still queued), 25k
auto-thin, zoneAt()/zones/tides. **Validation:** both script blocks pass `node --check`;
inlined Leaflet byte-identical to HEAD; zoneAt() most-protective ordering and the green-zone
dragend re-check confirmed intact; synthetic Node VM harness executed the REAL code slice from
index.html against a controllable localStorage stub — (1) REPLACE wrote a matching <200 B
receipt that booted clean on simulated reload, (2) a simulated flush failure (store write
evaporated, receipt survived) raised the banner naming the lost region, cleared on re-save, and
stayed clear once durable, (3) MERGE now leaves a pre-merge snapshot, (4) Undo reverted only
the target region (others byte-untouched) and the dataset:null path removed a region whose
first REPLACE was undone, (5) rollback_v1 gone at boot with no remaining references. **On-phone
durability is NOT yet verified — by definition it can't be from inside one session; that's what
the receipt exists to prove on next boot.** Next: re-import Sunshine Coast v2, then Maroochy
Noosa v2 appgrade, one at a time, each verified with a genuine force-close/reopen.*

*v16.38 · 12 Jul 2026 — read-only investigation CLOSED, correcting v16.35–v16.37's diagnosis,
no code shipped: root cause of the SC/Maroochy-Noosa disappearance confirmed via direct code
read (index.html:2093–2098). **The verified-write safeguard is not broken at the API level** —
it does a genuine fresh `getItem` + re-parse, not a comparison against cached in-memory state.
**The blindness is one layer deeper: on iOS WebKit, a same-session read-back is served from the
browser's in-memory storage area and can never detect a write that fails to reach disk.**
`setItem` applies synchronously in-memory; the flush to disk is async and can silently fail
under storage pressure or an app kill before flush — verification passes, no error banner,
and the write evaporates on next real reopen. This is exactly the observed pattern: two
"successful," banner-free writes (SC REPLACE, Maroochy Noosa MERGE) that both reverted on a
genuine close/reopen, while `storage_check.html`'s reading (2,174.1 KB, matching legacy+Brisbane
River exactly) was accurate throughout — **the v16.36/v16.37 conclusions that (a) storage_check
was bfcache-stale and (b) Sunshine Coast's data was overwritten under the wrong region key are
both SUPERSEDED and wrong; nothing was overwritten, the writes never durably existed in the
first place.** REPLACE and MERGE share one write/verify code path (confirmed no separate MERGE
verification branch); quota-error handling is correct and not silently swallowed on the
synchronous path — this failure is specifically the *asynchronous* durability gap, not a caught
exception. **Retroactive implication: v16.28's "confirmed good" Sunshine Coast REPLACE is now
presumed subject to the same blindness and plausibly never survived past that session either**
— item 4 downgraded from DONE to UNCONFIRMED pending a real close/reopen-verified re-import.
The v16.27 synthetic test's claim is narrowed to region-scoping + banner plumbing only; it
never tested durability, since its own assertion ran in the same session as the write.
**Fix proposed (build pending, sequencing decided by Aaron/Claude below):**
(A) boot-time durability receipt — a small `<200 B` second key written after every verified
save, checked against the real loaded store on next boot, surfacing a persistent "your last
import didn't survive a restart" banner on mismatch;
(B) root-cause relief — region-scoped rollback (frees ~1.5 MB of transient headroom per import,
folding in the previously-proposed v16.36 fix) plus dropping the now-confirmed-dead
`woongarra_imported_rollback_v1`; structural end-state flagged for a future session: move
imported datasets to IndexedDB, whose transaction commit is a real durability signal and whose
quota is far larger — not urgent, queued as a new backlog item, not a blocker;
(C) interim manual protocol, zero-cost, effective immediately: after any import, force-close
and reopen the app and re-check dataset row counts before trusting the result — same-session
confirmation is now known to be meaningless under storage pressure;
(D) this changelog entry itself is the roadmap correction called for.
**Decision: build (A) + region-scoped rollback from (B) together in one session** — both touch
the same REPLACE/MERGE code path, and (A) alone would still leave the quota-pressure trigger in
place. **Decision: adopt (C) immediately, starting now, independent of the build** — it's free
and closes the exact gap that caused today's confusion. **Decision: defer the IndexedDB
migration** — real fix, not urgent enough to block re-establishing SC/Maroochy-Noosa on the
current architecture. No phone-side action taken this session; `storage_check.html`'s
reliability is reaffirmed, not removed from the plan.*

*v16.37 · 12 Jul 2026 — planning correction (SUPERSEDED by v16.38, kept for the record): after
Aaron force-closed and reopened the app and found only legacy + Brisbane River (76,454 pts)
present, initially concluded `storage_check.html` had been serving a stale bfcache snapshot
across three earlier reads that all showed identical `imported_v2`/`rollback_v1` byte counts
despite the live panel showing different states in between. **This diagnosis was wrong** — see
v16.38: storage_check was accurate throughout; the live panel's differing states were
themselves never durably written. Backup exported at the 76,454-pt confirmed-durable baseline
before the correct diagnosis landed — that backup remains valid and current.*

*v16.36 · 12 Jul 2026 — planning, investigation + recovery attempt, no code shipped (SUPERSEDED
in part by v16.38): read-only investigation of the v16.35 quota incident found the rollback
snapshot mechanism (`snapshotImpRollback()`, index.html:2100) copies the entire `datasets`
object on every REPLACE/✕-remove/Clear-ALL/backup-restore (MERGE alone takes no snapshot),
sharing one slot overwritten by whichever operation runs next — explaining why the quota
squeeze happened (every import transiently costs ~2× its own size) and, at the time, appearing
to explain a missing Sunshine Coast row as an overwrite-under-the-wrong-key. Region-scoped
rollback fix proposed (`rollback_v2`, per-region snapshots, MERGE gains coverage). Aaron
pressed Undo per the investigation's recovery suggestion; result (legacy + Brisbane River only,
76,454 pts) didn't match the predicted restore, correctly flagged as inconsistent with the
overwrite theory at the time — **this inconsistency was the first real signal the diagnosis was
incomplete, resolved in v16.38.** Sunshine Coast and Maroochy Noosa were both re-imported this
session and appeared to succeed (4-row panel, 113,557 pts, all correct counts) before a later
close/reopen reverted them — see v16.38 for the actual mechanism.*

*v16.35 · 12 Jul 2026 — INCIDENT, no code shipped, no data lost: first Maroochy/Noosa MERGE
attempt (19,178-pt appgrade file, region field left blank) failed with a "quota exceeded"
storage-write error, correctly surfaced by the v16.24.2 banner on this occasion. `storage_check.html`
confirmed total container usage at 4,889.3 KB / 4.77 MB against a real ceiling implied by the
v16.9 fill-test baseline — `woongarra_imported_v2` and `woongarra_imported_rollback_v1` sitting
at near-identical size (~2,174 KB each) was the first evidence the rollback snapshot was
whole-store, queued as v16.36's investigation. No phone-side action taken pending it.*

*v16.34 · 12 Jul 2026 — Maroochy/Noosa import-thinning decision resolved, Claude Code data-processing
session, no `index.html` change: chose controlled re-export over the app's own auto-thin (37.9×
reduction from 946,877 pts was untested territory — largest previously validated ratio was
10.01×, and the 26 MB source file was ~5× the largest single-pass CSV parse ever run on-phone).
Built `data/maroochy_noosa_bathy_v2_appgrade.csv`: 180 m grid (deliberately sized for an
18–20k-point output, well clear of the 25k cap), 19,178 pts, conditional per-cell selection
rule reached after two iterations — signed-max lost dries-crest detail, flat `|depth|` flipped
112 genuine nearshore shallow-water cells to false "dries" (rejected: for a shore angler, that's
exactly the zone this dataset was sourced to serve). **Final rule:** any cell containing a
submerged point keeps its deepest submerged reading (protects nearshore shallow water); pure-dries
cells keep their most-exposed point. v1 (946,877 pts) kept untouched as the full-resolution
archive; the 13 v1 boundary-edge rows on the exclusion-box line are dropped only inside the v2
transform, not scrubbed from v1. **Region-tagging decision:** Maroochy/Noosa gets its own
"Other…" region slot, distinct from Sunshine Coast's existing intertidal/ground slot — different
data type (real bathymetry vs topographic-NIR), different confidence tier (moderate datum
confidence per the Fugro report vs the classifier-fault-hardened intertidal pipeline), keeps
future fixes independently scoped rather than conflated.*

*v16.33 · 12 Jul 2026 — Maroochy/Noosa BATHYMETRY SHIPPED as data (no `index.html` change, build
stays 2026.07.07a): `data/maroochy_noosa_bathy_v1.csv` — 946,877 rows, 25 m grid, LAT-referenced,
depths −1.15…+42.48 m, 99.0% genuinely submerged — the project's first real depth data, from the
QSpatial "Bathymetric LiDAR for Sunshine Coast" delivery (Fugro LADS Mk 3, 2011 survey). NOT yet
imported on-phone; 947k rows vs the 25k import cap needs a thinning decision first. See changelog
v16.33, which also records the v16.29–v16.32 read-only investigations that de-risked it (real zip
contents vs the wrong ISO metadata, vertical-datum resolution, Fugro classification legend, the
Maroochy Wetland Sanctuary defect zone).*

*v16.28 · 12 Jul 2026 — planning session, no code shipped: item 4 CONFIRMED EXECUTED, plus a
depth-data-sourcing review that closes with no pipeline change. **Real Brisbane River +
Sunshine Coast v2 REPLACE run by Aaron on-phone** (v2 CSVs from v16.24) — counts confirmed
good, Bargara/Woongarra confirmed intact, no error banner. **Item 4 is now genuinely DONE**,
not just cleared-to-run. Aaron then screenshotted four tap-read popups across both regions
(Pinkenba/river-mouth, Buderim/Mountain Creek, Maroochydore, Bli Bli), all reading "dries ≈ X m
... data N m away," flagged as looking like land/exposed ground rather than water depth.
**Diagnosed as NOT a bug — two already-documented facts compounding, not a new fault:**
(1) Brisbane River and Sunshine Coast structurally only ever have intertidal/exposed-ground
elevation data — turbid water defeats laser bathymetry here (confirmed 19 Jun 2026), so "dries"
is the only reading this pipeline can ever produce for these two regions, unrelated to today's
REPLACE. (2) v16.25 (already live) deliberately dropped the depth-sign requirement on the
tap-read/shading fallback specifically so Sunshine Coast north of Caloundra would paint at all —
that's why almost every tap within ~80–120 m of any dries point now surfaces it, exactly as
designed, confirming the v16.25 fix is working correctly at Coolum and beyond. **Item 5** (missing
low-confidence tag on the "dries" popup branch past 80 m) is now actively relevant given daily
use — promoted from "small independent fix" to worth doing soon.

Aaron then asked for real depth "as best we can," Maroochy/Noosa included, and offered Navionics
as a possible source. **Navionics REJECTED** — conflicts directly with the standing rule "no
seabed database, never infer depth from Navionics or other chart art" (chart soundings aren't a
verified survey tied to a known datum, and extracting/redistributing derived chart data is a
licensing problem separate from viewing it live). Logged here so it isn't re-proposed.

**Real Maroochy/Noosa bathymetric LiDAR identified precisely:** "Bathymetric LiDAR for Sunshine
Coast," Queensland Government Open Data Portal (data.qld.gov.au), CC BY 4.0, 2022 vintage, 5 m
resolution, genuine green-laser bathymetric survey (0–30 m depths) covering the lower estuarine
reaches and offshore of the Maroochy and Noosa Rivers specifically — not the whole Sunshine
Coast. This is the same dataset already referenced in the item-15 "Home-water depth reality"
note (19 Jun 2026) and **already confirmed back in v16.1 (2 Jul) as manual-order-only** — checked
directly against the CKAN API then, only a QSpatial order-and-email-link page exists, no bulk
API/shortcut. Status unchanged: **stays a you-step for Aaron**, same pattern as ELVIS; Claude
Code processes the delivered files once they land (clip/AHD→LAT convert/CSV export/import), same
pipeline already used for the Point Clouds work.

Aaron then screenshotted ELVIS's own "Bathymetry" overlay (elevation.fsdf.org.au) and an Order
Data panel showing a Moreton Bay/Brisbane River AOI with **QLD Government Bathymetry: 3 Metre
(93 of 93 tiles available)**, asking whether this is a path to real depth. **Confirmed: this is
the SAME EOMAP-derived "Bathymetry (3 m)" bucket already rejected — twice.** History, from this
roadmap's own record: the original Sunshine Coast attempt ordered from this bucket by mistake (3
rejected zips still sit in `data/raw/Sunshine-Coast/`); it was then mistakenly re-endorsed in
v16.2 (3 Jul, "finer than the 5 m previously assumed, a genuine improvement") and a 950-tile
Sunshine Coast order placed under that belief; that order was never used — the actual
`sunshine_coast_intertidal_ground_v1.csv` output (v16.5) is Point Clouds/AHD data (100% negative
= dries-only, ground-classified), and v16.8 (4 Jul) wrote the corrected fact into the project
instructions themselves: **Point Clouds/AHD is the correct ELVIS bucket; Bathymetry-3m is EOMAP
satellite-derived, ±10 m accuracy, ambiguous dual LAT/MSL datum, vendor-labelled
not-for-navigation — rejected.** Ordering from it a third time would repeat a mistake already
made and corrected twice. **No change to the plan** — the same screenshot's Order panel also
showed Geoscience Australia's Bathymetry (30/50/100 m, AusBathyTopo-class — already-noted as
coarse open-coast only, too coarse for nearshore precision) and Digital Earth Australia's "10
Metre Intertidal" (already scoped separately at item 14b, Exposure-only, gated on a confidence
check, not yet built) — neither is new or actionable either.

**Net result:** the only real path to genuine measured water depth for Maroochy/Noosa is the
data.qld.gov.au dataset above, via manual QSpatial order (new backlog item 14 below). Everywhere
else in Brisbane River and the broader Sunshine Coast remains dries-only by the same physical
limit as before — own sonar → GPX import is still the only real depth path there, unchanged.
Aaron's fair pushback noted for the record: the intertidal/ground-elevation pipeline alone
("if we were only building intertidal I probably wouldn't have bothered") is a real limitation,
not oversold here — its standalone value is rock-platform/flat/access elevation for a land-based
angler, not underwater structure; the classifier-fault and storage-scoping fixes built alongside
it were real bug fixes independent of which depth layer sits on top, and the same
REPLACE/MERGE/rollback mechanics will be reused when the Maroochy/Noosa bathymetry lands.

*v16.27 · 12 Jul 2026 — planning/validation, no code shipped: small-file synthetic REPLACE +
MERGE test run on live build 2026.07.07a, specifically to close the risk flagged in v16.26 —
whether a region-scoped REPLACE would touch the untagged "pre-region-tagging" legacy dataset
(55,660 pts, spanning all three regions, created by the backup restore since it predates
per-region tagging). Test file: `guya_test_synthetic_sunshinecoast.csv`, 5 points, Sunshine Coast
region selected. **MERGE:** 55,660 → 55,665; new region-tagged 5pt Sunshine Coast dataset created;
legacy 55,660pt dataset unchanged. **REPLACE (same region, same file):** Sunshine Coast dataset
stayed at 5pt (confirmed replace, not merge-on-merge); **legacy dataset still exactly 55,660pt** —
the critical result, confirming REPLACE is correctly region-scoped and does not touch the
untagged legacy blob. Test dataset removed after confirmation, on-device state clean. **Item 4
(Brisbane River + Sunshine Coast v2 REPLACE) is now fully cleared — no known blockers remain.*

*v16.26 · 12 Jul 2026 — planning/ops incident, no code shipped: GitHub Pages had not deployed
since Jul 5 (run #85) — builds 2026.07.06a (v16.24.2) and 2026.07.07a (v16.25) were committed
locally on 11–12 Jul but never pushed, so the live site sat frozen on 2026.07.05a for a week
despite both fixes being complete in the repo. Misdiagnosed initially as phone-side caching, then
briefly as a repo-rename URL break (repo has been `AzmixLabs/Guya_Wamu` since before the Claude
Code migration — that rename is old and unrelated to this incident). Root cause found via the
Actions tab (no Pages deployment since Jul 5) + `git status` (7 commits ahead of origin).
**Fixed:** local remote corrected from `AzmixLabs/Guya.git` to
`https://github.com/AzmixLabs/Guya_Wamu.git`; `git push` run, 7 commits landed
(`a01538f..cf8ed0b`), Pages run #86 deployed clean (~40s). **Confirmed by Aaron:** the live site
now shows build 2026.07.07a, and the `version:2` backup restore (recovering the full multi-region
depth dataset) completed successfully on the correctly-deployed build — this validates the
restore code path specifically (true full-replace, per v16.24.2). **New standing habit:** confirm
`git push` actually ran and a new Pages Actions run appears before treating any Claude Code
session's fixes as shipped — a local commit is not a deployment. **Surfaced in passing, not yet
actioned:** `guya_species_qld_v3.md` sits untracked in the repo — origin/purpose undecided,
separate small item, see priority list.*

*v16.25 · 12 Jul 2026 — build 2026.07.07a: FIX SHIPPED for the shading/tap-read coverage gap
north of Caloundra (independently diagnosed, separate subsystem and separate incident from
v16.24.1/v16.24.2's storage bug — do not conflate). Root cause: the cosmetic paint/read mask
required either a legislated marine-park zone polygon OR a nearby sample with a genuine
underwater sounding (depth ≥ 0); Moreton Bay MP zoning stops at Caloundra (no polygon for
Mooloolaba→Noosa), and this dataset's imported points are almost entirely "dries" (negative
depth), so neither condition could fire along that whole stretch, at any array size. **Fix:
dropped the depth-sign requirement — the existing distance bound (within ~80–120 m of a real
sample, depending on the call site) is sufficient evidence of real coastal/intertidal ground on
its own, regardless of whether the nearest sample is a dries reading or a sounding.** Applied
identically across **all five** call sites sharing this exact gate (the investigation named two —
`buildShade()`'s shading paint and the tap-to-read click handler — but the same duplicated
condition also gated `findDeepest()`, `buildAutoContours()`, and the desktop hover-readout;
fixing only two would have left the other three silently broken at Coolum and inconsistent with
the two that were fixed). Confirmed by direct test-data lookup: the reported Coolum point
(−26.554413, 153.095149, depth −5.63) is 0 m from itself in the dataset → now passes the
distance gate; a control point 8.7 km inland is correctly still excluded by distance alone,
confirming the sign check was never load-bearing for protecting against painting over unrelated
dry land. `zoneAt()` (legal zone determination) is untouched and confirmed separate from this
cosmetic mask — same file, same line, unchanged. Both script blocks pass `node --check`; Leaflet
block confirmed byte-identical. See changelog v16.25.*

*v16.24.2 · 12 Jul 2026 — build 2026.07.06a: FIX SHIPPED for the v16.24.1 incident, item 4
UNBLOCKED. Root cause (from the prior read-only investigation) was structural, not a scale/data
bug: all imported depths lived in one unscoped `woongarra_imported_v1` array with no per-region
tag, so REPLACE unconditionally wiped the whole store — the second REPLACE (Sunshine Coast)
overwrote the just-imported Brisbane River data, and Bargara/Woongarra was collateral damage
from the very first REPLACE. **Shipped: dataset-scoped storage** (`woongarra_imported_v2`,
per-region datasets, legacy array migrated in as a tagged "legacy/unknown" dataset — nothing
dropped); **REPLACE/MERGE now scoped to the selected region only**; the blind `confirm()`
OK=replace/cancel=merge dialog is **retired** in favour of explicit Replace/Merge buttons per
region, plus a visible per-region dataset list with individual remove; **backup restore is now a
true full replace** of the imported-depths store (was silently merge-only); **verified writes**
(read-back + count-check) surface a **persistent in-panel error**, replacing two previously
silent `catch(e){}` blocks; **one-step rollback snapshot** before every REPLACE/remove/restore,
with an in-panel Undo button. The 25,000-point auto-thin logic is untouched. Both script blocks
pass `node --check`; the inlined Leaflet block confirmed byte-identical; `zoneAt()` and the
green-zone drag safeguard confirmed intact. **Rendering/interpolation (the separate, independently
diagnosed zone-coverage gap north of Caloundra) is NOT touched by this build.** See changelog
v16.24.2 for the on-phone test plan before the real v2 CSV re-import.*

*v16.24.1 · 11 Jul 2026 — INCIDENT, item 4 BLOCKED (planning-chat log, no code shipped, no
data changed): Aaron's first REPLACE attempt (v2 CSVs, both regions) on phone produced no
depths for Brisbane River or Sunshine Coast — AND wiped Bargara/Woongarra depths, a
pre-existing dataset never touched by this import. Strong evidence the "Imported depths"
store is a single unscoped bucket across ALL regions, not partitioned per-region — REPLACE
had never been exercised in this app before this attempt. A follow-up MERGE also produced no
depths (cause unconfirmed). Aaron restored his pre-import `version:2` backup; spots
confirmed recovered, Bargara status pending his confirmation. **Item 4 is BLOCKED — no
further phone-side REPLACE/MERGE attempts until a Claude Code investigation (read-only code
review of the import path + v2 CSV validation) reports a root cause.** v2 CSVs themselves are
unaffected by this — the v16.24 build output stands, only the phone-side import is blocked.
See changelog v16.24.1.*

*v16.24 · 11 Jul 2026 — drop-mask BUILD COMPLETE (items 2+3 DONE; PATH 2 halved-job: raw-LiDAR
mask re-scan + CSV-level drop, NOT a full pipeline re-export). All 1,184 hybrid-scope tiles
re-scanned with the exact v16.17–v16.21 method — 48,194 flagged cells recovered, **per-tile
counts matched audit_results.json 1,184/1,184 (zero mismatches)**, spot-check 28/28 tiles /
84/84 stored example coordinates. Mask = 44,427 unique 25 m cells (multi-vintage overlaps
collapse). **v2 CSVs written alongside v1 (v1 kept): Brisbane River 209,540 → 189,187
(−20,353 pts); Sunshine Coast 188,855 → 168,461 (−20,394 pts).** Zero v2 points remain inside
any mask cell. All ten control locations PASS — flagged cells read "no data," control tiles
retain 76–1,236 surviving points each (adjacent real flats trimmed, not gutted). 2009-vintage
points untouched per the hybrid scope. **Phone data UNCHANGED — item 4 (REPLACE re-import,
both regions) is the remaining manual step, Aaron only.** See changelog v16.24.*

*v16.23 · 11 Jul 2026 — drop-mask DESIGN PHASE COMPLETE for item 2 (read-only analysis + one
metadata fix; NOTHING masked, dropped, or re-exported). Headline corrected: artifact scale is
**296 tiles / 19.98 km²**, not 302/20.30 — `audit_results.json` carried 14 byte-identical
duplicate HIT entries (pre-dating v16.21, from overlapping delivery zips in the
MoretonBay_2014/2018 Pumicestone block), 6 of which double-counted the headline; deduplicated
with backup. Masking SCOPE: **hybrid RECOMMENDED, PENDING AARON'S FINAL SIGN-OFF — not yet
locked in** — cell-level masking on post-2009 vintages only (where class-9 adjacency confirms
the fault): **1,184 tiles / 48,194 flagged cells / 30.12 km²**; the three 2009-vintage groups
(53 flagged tiles / 0.21 km²) stay unmasked as unconfirmed. See changelog v16.23.*

*v16.22 · 10 Jul 2026 — documentation-only correction, no code/data/audit changes: (1) Brisbane
River import status was stale — that CSV is not "held"; it was already imported to Aaron's phone
via MERGE (same route as Sunshine Coast), so BOTH regions carry the artifact on-phone and BOTH
need a REPLACE re-import (priority item 4 updated accordingly). (2) Fixed a Group A tile-count
typo in the v16.21 text: 652 → 556 total SC/Noosa tiles (544 newly audited + 12 v16.18 spot
samples; 544 + 363 = 907 as stated). See changelog v16.22.*

*v16.21 · 10 Jul 2026 — depth-audit gap CLOSED (diagnostic only, no code shipped): full
class-9-adjacency audit of the Sunshine Coast dominant-vintage groups plus a density-only
secondary test on the three 2009 vintages — 907 tiles this pass, zero read errors. Headline
revision: the classifier-fault footprint is **~20.3 km² / 302 tiles at artifact scale** (was
~13.6 km² / 192 in v16.18; corrected to 296 / 19.98 in v16.23 — duplicate-entry fix) — the SC 2022/2014/2008 + Noosa groups add 110 artifact-scale tiles
/ +6.69 km²; the 2009 vintages add ZERO at artifact scale (effectively clean — the fault is
post-2009 only). Current build remains 2026.07.05a. Both the Brisbane River and Sunshine Coast
CSVs — each already phone-imported via MERGE (see v16.22 correction) — remain unsafe to trust
as-is; the drop-mask re-export (item 2) is now fully scoped and unblocked. See changelog v16.21.*

Personal / family land-based fishing **+ nature field-log** tool. Single self-contained HTML
file, Leaflet, localStorage + IndexedDB, offline-first, hosted free on GitHub Pages.
**Not for commercial sale** — built for Aaron + family (sisters, nephews, daughter).

**Current build:** 2026.07.19b — MN disc-rendering: global R0 replaced with a PER-SAMPLE
adaptive radius (v16.47), after v16.46's flat R0=56 was confirmed on-phone to both leave the
Tewantin/Noosa Heads corridor still visibly gappy AND inflate SC/BR's known sub-HAT messy-tier
residual into visible Maroochydore land-overpaint. R0_local=clamp(gap−R1,30,90) per sample;
dense SC/BR clusters revert to exactly pre-v16.45 tightness (verified: a50 within ~1pp of the
pre-v16.45 baseline), the Tewantin corridor's own gap-midpoint alpha≥0.5 rate rises to 90.1%
(vs 60.0% pre-v16.45, 88.1% under v16.46's flat bump). R1=120 still untouched throughout. See
v16.47 for full numbers. **On-phone re-check COMPLETE and PASSED (v16.47.2, 21 Jul)** — both
visual checks pass, shading toggle fine; a map-panning perf follow-up (`r0` cache) is queued. Previous build 2026.07.19a (v16.46) raised
a flat R0 30→56 on a p90-midpoint criterion — superseded by v16.47's per-sample version, same
session day. Build 2026.07.18a (v16.45) re-tagged MN out of free-text "custom" into a named
`maroochy_noosa` region (that re-tag stands, untouched since). Previous build 2026.07.13a —
land-overpaint FIXED, Option A elevation-aware gate (v16.44):
dries samples above HAT no longer count as paint/read evidence at any of the five shared v16.25
call sites; validated against the real 113,557-pt on-phone replica (all named dry probes now
excluded, all wet soundings unaffected); on-phone confirmation still pending. Previous build
2026.07.11a (v16.42, Brisbane Bar + Mooloolaba 2027 tide tables) is a pure data addition, all
three ports now span 2026–2027, on-phone confirmed (v16.43.1). Build 2026.07.10a (v16.41
regional tide-port fix) was pushed and confirmed on `origin/main` (`cc2c2dd`), on-phone confirmed
(v16.43.1): depth/tap popups now use the
nearest port's tide table (Burnett Heads / Brisbane Bar / Mooloolaba) instead of hardcoded
Burnett Heads everywhere. Shading argument-ceiling fix (v16.40) **confirmed working on-phone**:
tint now paints over Sunshine Coast, Brisbane River, and Maroochy Noosa. **Open incident
(v16.40.1, root cause CONFIRMED v16.41, fix not yet scoped):** shading/tap-read paints genuinely
dry land near the Sunshine Coast/Brisbane River systems — NOT the R1 halo: the intertidal
exports' −3..+5 m AHD band put samples ON the dry land itself (63% of SC / 74% of BR on-phone
points sit above HAT), and v16.25's any-sample-within-120 m gate paints them. All
four datasets remain imported and durable on-phone, 113,557 pts. (v16.26: GitHub Pages had
silently stalled since Jul 5 on 7 unpushed local commits; fixed by correcting the local remote and
pushing, confirmed via Actions run #86 and a direct on-phone build-string check). **Region-scoped
REPLACE/MERGE mutation logic confirmed correct by direct test (v16.27) — narrowed per v16.38:
that test validated region-scoping and banner plumbing only, NOT write durability.** *(v16.25: fixed
the shading/tap-read coverage gap north of Caloundra — dropped the depth-sign requirement on the
cosmetic paint/read mask's distance-bounded fallback, across all five call sites sharing that gate.
v16.24.2: dataset-scoped "Imported depths" storage, fixing the v16.24.1 REPLACE/MERGE data-loss
incident — a separate subsystem, separate incident, do not conflate the two fixes. **v16.38: this
mechanism's verified-write safeguard is known to give false confidence under storage
pressure on iOS WebKit — the boot-time durability receipt + region-scoped rollback fix SHIPPED
in v16.39, build 2026.07.08a.** 2b wiring —
zoning/FHA/tides — see changelog v16.19. `storage_check.html` diagnostic page + its temporary
in-app link, from v16.7, are still present and still flagged for removal — see v16.38, its
reliability is now separately confirmed accurate, don't second-guess it again.)*

**Next-session note (21 Jul 2026, post-v16.47.5):** build unchanged at `2026.07.19b`; roadmap
now **v16.47.5**. Three things landed after v16.47.3, all at the head of this file: **(i) Option 3
STRICT-AND land/water mask is AUTHORISED on the RUNTIME path** (v16.47.3) — the deciding argument
is that the untagged legacy 55,660-pt blob lives only in phone localStorage and can never be
reached by a bake-time mask; **(ii) the MN offshore diagnostic RETURNED** (v16.47.4) — the 180 m
export grid is confirmed beyond argument, the offshore points are verified genuine LADS (100% exact
subset of v1) and NOT classifier-fault residue so the mask must not touch them, bytes-per-point is
measured at 27.91, and the idealised hole-rate derivation was corrected to a measured 31.4%
diagonal / 15.2% orthogonal caused by the deepest-point-per-cell jitter; **(iii) Aaron changed the
MN v3 clip criterion** (v16.47.5) from depth-based to **distance-from-shore, ≤200 m, with maximum
smoothness inside the band**. That last one reverses the storage question: the surveyed footprint is
~591 km² and the 200 m casting band is only ~1.9% of it, so **full native 25 m resolution inside the
band is projected at ~17,600 pts / ~491 KB — slightly LESS than the 19,178 pts / 535 KB deployed
today**, with alpha = 1.0 everywhere (both orthogonal and diagonal midpoints fall inside R0=30, so
no ramp, no holes, smoother than Bargara) and no thinning step at all. **That projection is
geometric, not measured — measure the real clipped count first and follow the grid ladder in
v16.47.5 rather than assuming ~17,600.** **FIRST ACTION next Claude Code session:** resolve the
pre-existing uncommitted `GUYA_ROADMAP.md` edit and untracked `guya_species_qld_v3.md` in the working
tree — left behind by an earlier session, mandatory hard rule, do it before any new work. **v16.47 is CLOSED** — on-phone re-check passed on both visual checks (Tewantin
corridor contiguous, Maroochydore overpaint back to pre-v16.45 levels) and shading toggle shows no
slowdown. **R0 work is done; do not open a fourth iteration.** Two things came out of that check
and the same session's research sweep, both recorded in full in the v16.47.2 entry above:
**(1) map panning feels slightly slow** — `buildShade()` re-runs on map movement so every pan pays
v16.47's O(n) per-sample precompute over all 113,557 points; the queued fix is to cache each
sample's `.r0` and invalidate only on import/replace/clear (bounded Sonnet job) and it **must ship
before any densification**. **(2) the depth-data question is now evidence-closed** — the 2011 Fugro
LADS survey was a one-off pilot with no wider series, 14 sources checked and closed, and the 0–50 m
land-based fringe is unmeasured across SEQ as a physical limit rather than a search gap. Navionics
tracing is confirmed historical and long deleted (**that standing backup chore is CLOSED**), and
sonar → GPX is **declined**, so **Brisbane River / Sunshine Coast / Redcliffe get no depth layer,
ever** — the answer for those regions is the **FLATS LAYER**. **The single biggest finding:** the
`MoretonBay_2014`/`Moreton_Bay_2018` delivery Aaron ordered **did arrive and was never processed** —
it is topographic NIR carrying the class-9 fault (Brighton is the fault's origin site), so it is not
depth and never will be, **but it is exactly the flats layer Redcliffe needs, and it requires no new
data.** **IN FLIGHT:** the MN offshore read-only diagnostic prompt was dispatched to Claude Code
(Sonnet) on 21 Jul — it confirms or refutes the grid-regularity hypothesis for the offshore disc
lattice, verifies those points are LADS rather than fault residue, and re-measures bytes-per-point.
**Do not build against the v16.47.2 derivation until it returns.** **Next jobs, in order:**
(1) `r0` cache; (2) **Option 3 runtime mask — AUTHORISED 21 Jul (v16.47.3)**, runtime path
confirmed over bake-time because the untagged legacy 55,660-pt blob can never be reached by a
bake-time mask; build prompt to be drafted after the diagnostic returns and the `r0` cache lands; (3) flats layer;
(4) MN v3 = spatial clip to ≤200 m from shore at native 25 m if the measured count allows
(v16.47.5, supersedes the ~90 m plan), REPLACE not MERGE; (5) Noosa
tide-port wiring; (6) future-proofing (render harness, region-onboarding checklist, per-dataset
`source_type` tag). **Usage note:** Aaron was at 75% of his weekly limit at the close of this
chat — the diagnostic and the `r0` cache are both cheap Sonnet jobs; the flats layer is the
expensive one and should get a clean session.

**Previous note (19 Jul 2026, post-v16.47):** build now 2026.07.19b — global R0 replaced
with a per-sample adaptive radius after v16.46's flat R0=56 was confirmed failing on-phone in
BOTH directions (Tewantin corridor still gappy, Maroochydore land-overpaint newly visible); see
v16.47 for the full derivation and numbers (Tewantin gap-midpoint alpha≥0.5 rate 60.0%→90.1%,
SC/BR messy-tier alpha reverted to within ~1pp of pre-v16.45). **Mandatory on-phone re-check
queued, not yet run — check BOTH regressions this time, not just MN:** confirm build string
reads `2026.07.19b`; screenshot the Tewantin/Noosa Heads river corridor (expect it filled in,
tolerate faint patches only at the rare >210 m tail gaps, quantified in v16.47); ALSO screenshot
the Maroochydore golf-course/suburb area that showed overpaint under v16.46 (expect it back to
pre-v16.45 levels — this is the regression that made the flat-radius approach unworkable, so
confirming it's gone matters as much as confirming MN improved). Also do a quick feel check —
pan/zoom and toggle shading on/off a couple of times; the fix adds a new per-sample precompute
over the full loaded point set, so confirm nothing feels newly sluggish (unmeasured on real
hardware — see v16.47.1). **If either check still fails:**
this was the third R0 iteration in one day; before a fourth, question whether per-sample R0 is
the right lever at all, or whether it's time to bring R1/Option 3's land-water mask back to
planning rather than keep retuning the same ramp. **Recommended next job — data hygiene, no
build, Aaron's own action, still outstanding from v16.44.2:** delete the Navionics-traced
contour lines near Innes Park and re-export a fresh `version:2` backup right after. **Next
actual build candidate (once the MN on-phone check closes):** Noosa tide-port wiring —
mechanical, BoM TP021 PDFs already confirmed available, plain Sonnet job. **Model-routing
note:** Fable 5's included-plan window (v16.44.1) is set to lapse ~5 PM AEST Monday 20 Jul —
this session ran on Fable; nothing in the queue above requires it going forward. Option 3's
SC/BR v3 re-export remains gated "don't trigger standalone" (v16.43); pulling it forward to
catch the pricing window remains Aaron's call, not pre-authorised here.

**Previous note (18 Jul 2026, post-v16.44.1):** the on-phone Bargara/Woongarra check was still
outstanding and the Fable-timing question was newly raised — both are addressed above (check
closed in v16.44.2; Fable question restated, unresolved). The HAT cross-check and Fable-window
detail in the v16.44.1 entry above are otherwise unchanged and still accurate.

**Previous note (13 Jul 2026, post-v16.44):** build 2026.07.13a — Option A land-overpaint fix
SHIPPED, all offline validation PASS (see v16.44 entry). Superseded by v16.44.2's on-phone
closure above; everything else below is unchanged. **Option A's known residual gap is measured,
not assumed:** the v16.43 spike puts it at 53–58% of the sub-HAT messy tier (~800–880 pilot points)
still painting — an accepted tradeoff, to be closed later if/when **Option 3 (real land/water
mask)** rides in on a future SC/BR re-export. Option 3 stays scored and ready but NOT an
immediate build (v16.43): hybrid STRICT-AND (OSM ∧ WOfS freq≥0.2) scores 0.79% false-paint /
99.74% wet coverage kept, but its bake-time integration needs a full SC/BR v3 re-export to reach
the phone — don't run it standalone, ride it along with any future SC/BR re-export. Full
findings: `data/raw/_landmask_spike/OPTION3_LANDMASK_SPIKE.md` (gitignored scratch — paste into a
future delta if it needs to survive a re-clone). **One data chore still open, not urgent:** Noosa's
Mooloolaba fallback is a stopgap, not the final answer — Noosa Head is on record as its own MSQ
Standard Port and still needs its own wiring (its 2026+2027 BoM per-port PDFs exist at
bom.gov.au/ntc/IDO59001/, TP021 — same source/parser as v16.42, so wiring it is now mostly
mechanical). **Backlog item, not urgent:** Aaron wants the Maroochy Noosa "blobby" disc
rendering (~23%-coverage discs, 180 m export grid vs 120 m paint radius) improved, not just
accepted as expected-not-buggy (v16.40's framing) — needs its own scoping session once the
land-overpaint bug is resolved; likely candidates are a larger/adaptive paint radius for sparse
grids or a smoothing pass, either way keep it clearly separate from the land-overpaint fix so
the two don't get conflated in one patch. While in the shading code, consider re-tagging the
Maroochy Noosa dataset out of the free-text "custom" slot into a named region (cosmetic only —
region keys have no functional effect, confirmed v16.40 investigation). Item 5 (low-confidence
popup tag) still pending, unaffected. Pending cleanup: `bathy_checkpoint.json` +
`bathy_smoke.csv` (completed-run scratch), the `_inspect/` sample folder under
`data/raw/Bathymetric-LiDAR-Sunshine-Coast/`, `gap_checkpoint.json`/`hybrid_checkpoint.json`,
`guya_species_qld_v3.md` (origin/purpose still undecided — untracked in repo since at least
v16.26, unrelated to any recent session — repo remote itself is NOT an open question, see
v16.26: `AzmixLabs/Guya_Wamu` is a pre-existing, intentional rename, already corrected locally,
don't re-flag it). The `woongarra_imported_rollback_v1` cleanup item is CLOSED — v16.39 removes
it at boot (~2.17 MB reclaimed on first run). `data/raw/_landmask_spike/` (v16.43's scratch) is
gitignored and disposable — no action needed unless the spike report needs preserving elsewhere.

**Previous note (13 Jul 2026, post-v16.43):** build unchanged at 2026.07.11a — v16.43 was an
investigation spike, no code shipped, scoring Option 3 as an eventual follow-up (see entry
above). At this point on-phone confirmation of the v16.41 tide fix was still the recommended
first job, ahead of the Option A build — superseded by v16.43.1, which closed it out.

**Next session — priority order:**
1. **Close the depth-data audit gap — DONE (v16.21).** All 544 remaining SC/Noosa tiles audited
   (556 total incl. the 12 v16.18 spot samples; count corrected from "652" in v16.22)
   by class-9-adjacency (SunshineCoast_2008 carries class 9 after all, so no fallback needed) and
   all three 2009-vintage groups (363 unique tiles) by the density-only secondary test. Zero read
   errors. Artifact-scale total revised 192 tiles / 13.6 km² → **302 tiles / 20.3 km²**
   (corrected to **296 / 19.98 km²** in v16.23 — duplicate-entry fix); the 2009
   vintages contributed zero. Per-tile results merged append-only into
   `data/raw/_inventory/audit_results.json`. See changelog v16.21.
2. **Drop-mask re-export — DONE (v16.24: design v16.23 + build 11 Jul 2026, hybrid scope as
   signed off).** PATH 2 halved-job: mask re-scanned from raw LiDAR (1,184 tiles, zero count
   mismatches vs the audit), then applied at CSV level — no full pipeline re-export needed.
   See changelog v16.24. *(Design history follows:)* The
   scoping report + control-location check ran 11 Jul 2026 (read-only, nothing masked). Three
   options were costed on the deduplicated audit data: **Option A** (artifact-scale tiles only,
   296 tiles / 19.98 km²) — least coverage loss but leaves the same fault unmasked in 941
   sub-threshold tiles, including Brighton itself, the fault's origin site; **Option B**
   (every flagged cell everywhere, 1,237 tiles / 30.34 km²) — fully consistent with
   no-data-beats-wrong-data but sweeps in the weak-evidence 2009-vintage flags; **hybrid
   (RECOMMENDED, pending confirmation)** — cell-level masking on post-2009 vintages only,
   **1,184 tiles / 48,194 cells / 30.12 km²**, with the three 2009-vintage groups (53 flagged
   tiles / 0.21 km², weak density-only signal, no class-9 corroboration possible) left unmasked
   as unconfirmed. Drop flagged points rather than reclassify — geometry alone can't tell a real
   drying flat from mislabelled water at the same elevation (v16.18 qualification 3). Build
   starts only after Aaron picks the scope.
3. **Re-export both CSVs + control validation — DONE (v16.24).** v2 CSVs written
   (`brisbane_river_intertidal_ground_v2.csv` 189,187 pts, `sunshine_coast_intertidal_ground_v2.csv`
   168,461 pts; v1 files kept for audit trail until the re-import is confirmed). All ten control
   locations PASS — every previously-flagged vintage reads "no data" in its flagged cells, and
   every control tile retains real nearby coverage (76–1,236 points). See changelog v16.24.
4. **Re-import — DONE (v16.28: real REPLACE executed and confirmed by Aaron).** The v16.24.1
   incident's root cause was confirmed structural (unscoped shared store) and fixed: "Imported
   depths" is now dataset-scoped per region, REPLACE/MERGE only ever touch the targeted region,
   restore is a true full replace, writes are verified with a persistent error surface, and
   one-step rollback covers every destructive action. Aaron's `version:2` backup restore ran
   successfully on the confirmed-live 2026.07.07a build (55,660 pts, exact match); the small-file
   synthetic REPLACE + MERGE test (v16.27) then confirmed region-scoped REPLACE leaves the
   untagged "pre-region-tagging" legacy dataset untouched. **The real Brisbane River + Sunshine
   Coast v2 REPLACE was then run for real** (v2 CSVs from v16.24: Brisbane River ~189,187 pts,
   Sunshine Coast ~168,461 pts) — counts confirmed good on-device, Bargara/Woongarra confirmed
   intact, no persistent error banner. Item closed. **Follow-on, diagnosed not built (v16.28):**
   tap-read popups across both regions now read "dries" almost everywhere — confirmed expected,
   not a bug (see v16.28 changelog entry: physical turbid-water limit + the v16.25 fallback fix
   both working as designed). v1 depth CSVs are now safe to drop per the existing
   disposable-once-confirmed policy.
5. **Small, independent fix — no dependency on the above:** add the missing "low confidence" tag
   to the "dries" popup branch past 80 m (the depth-popup branch already has it) — found
   incidentally during the v16.17 diagnostic.
6. **Shading/tap-read coverage gap north of Caloundra — FIXED (v16.25).** Independently
   diagnosed and shipped: Mooloolaba→Noosa had no legislated zone polygon AND this dataset's
   points are almost entirely dries (negative depth), so the cosmetic paint/read mask's two
   admission conditions could both fail simultaneously, at any array size, for any point in that
   stretch — including Coolum, the reported test case. Fixed by dropping the depth-sign
   requirement on the distance-bounded fallback (near/within ~80–120 m of any real sample is
   sufficient evidence of coastal ground, dries or sounding) across all five call sites sharing
   the gate: `buildShade()`, tap-to-read, `findDeepest()`, `buildAutoContours()`, and the desktop
   hover-readout. `zoneAt()`/legal-zone logic untouched and confirmed separate. See changelog
   v16.25.
7. `git remote -v` check — **RESOLVED (v16.26).** Confirmed on github.com: the repo really has
   been `AzmixLabs/Guya_Wamu` since before the Claude Code migration (not a recent event). The
   local remote was still pointing at the old `AzmixLabs/Guya.git`, which is what surfaced the
   deploy incident (v16.26) — corrected to `https://github.com/AzmixLabs/Guya_Wamu.git`, confirmed
   via `git remote -v`. No further action needed.
8. Confirm `fishhabitat_bundaberg_region.geojson` — RESOLVED (v16.19): confirmed byte-identical
   to the already-shipped Woongarra FHA store. It's that store's raw source file, not an
   unrelated file. No action needed.
9. 2b wiring build (zoning/FHA/tides) — SHIPPED (v16.19, build 2026.07.05a).
10. **New (surfaced by v16.19):** FHA data (35 features, merged into the store) has no rendered
   map layer or point-in-polygon lookup — same gap as the pre-existing Woongarra FHA entries,
   just newly visible now that Maroochy/Noosa are in the same store. Independent, no dependency
   on the depth-audit work.
11. Noosa Head tide port — ready-whenever fast-follow. Own Standard Port, no offset math needed
    (confirmed v16.5, re-confirmed v16.19) — same pattern as Redcliffe following Brisbane Bar in
    2a. Cheap, not urgent.
12. Gold Coast stays parked.
13. **New (v16.26):** `guya_species_qld_v3.md` sits untracked in the repo (surfaced by `git status`
   during the deploy-incident fix) — origin and whether it belongs are undecided. Small, standalone,
   no dependency on anything above.
14. **Maroochy/Noosa real bathymetric LiDAR — PIPELINE SHIPPED (v16.33), import decision
   pending.** Was: "New (v16.28) — target dataset identified, Aaron's step to order." Now:
   order placed, delivery inspected, pipeline built and run. Corrections to the original
   entry: the dataset is a 2011 Fugro LADS Mk 3 survey (delivered/published 2013, not 2022 —
   that was the metadata record's last-update date, not the survey date); actual contents are
   LAS 1.2 point clouds + XYZ, not the vector formats (SHP/TAB/FGDB/KMZ/GPKG) the ISO record
   claimed. Output: `data/maroochy_noosa_bathy_v1.csv`, 946,877 rows, depths −1.15…+42.48 m
   LAT, 99.0% genuinely submerged — full detail in changelog v16.33. **Remaining:** 947k rows
   is ~38× the 25k phone import cap — thinning decision needed before this reaches the phone
   (see next-session note). ELVIS's "Bathymetry" bucket and Navionics remain rejected for any
   future depth sourcing (v16.28) — unaffected by this item's completion.

*(superseded URGENT block follows for history:)* a visual anomaly was showing on the live map near/offshore of Caloundra — a geometric wedge converging to a single point plus a disconnected dashed-green quadrilateral in open ocean, reproduced identically on both desktop and phone (not a stale-view issue). It renders under the app's "Marine-park zones" toggle (dashed-green matches existing MNP no-take styling), which redirects the investigation to `ZONES.features`, not the newly-imported depth data. Leading theories, **neither confirmed**: (a) a partial-reprojection bug on a specific feature (some vertices transformed, some not — precedent: `Noosa_2015_LGA`'s known-bad CRS VLR), or (b) a stray AOI/clip-boundary scratch polygon that got merged into `ZONES.features` instead of being discarded. **Also unresolved: whether a 2b zoning/FHA wiring build was actually run and never reported back to this planning chat** — a git-history check is queued to settle this before assuming the wiring status one way or the other. Separately, the complex coastline-hugging zone shapes visible around Bribie Island/Redcliffe in the same wider view are assessed as **likely correct, pre-existing 2a data** (Moreton Bay MP's documented northern boundary is Caloundra, so 2a zones legitimately start appearing there) — Aaron simply hadn't scrolled this far north before; lower priority to verify than the offshore anomaly. See v16.11 for the full diagnostic-first Claude Code prompt — **do not patch/re-export anything until the investigation reports back which of these it is.** **Brisbane River processing is paused** behind this — if it's a reprojection-pipeline bug rather than a one-off bad merge, it could recur identically on Brisbane River's data (already downloaded, not yet processed). Once resolved: **Sunshine Coast depth data is DONE** — imported to the phone as a single-pass, auto-thinned CSV (~18,875 pts, ~547 KB; see v16.9–v16.10) — and the **2b wiring build** (zoning/FHA/tides; data was validated and sitting ready as of v16.3–v16.4) may or may not still need running, pending the git check above.
**As of 2 Jul 2026 — workflow + 2b status update (v16.1, planning only, nothing shipped):** Guya
builds have moved to **Claude Code CLI**, running locally against the `AzmixLabs/Guya` repo
(`D:\Claude Code` on Aaron's machine) — `CLAUDE.md`, `.claude/settings.json`, and this roadmap are
committed there; this project (chat) stays for planning/ideas/roadmap deltas only, never builds.
**index.html (2026.06.28b) re-verified by direct file read, not assumed:** 178 zone features
confirmed present (104 Great Sandy + 74 Moreton — matches spec), zoning is genuinely complete. One
cosmetic gap found: the header still reads "Woongarra Coast · Great Sandy MP" with no mention of
Moreton Bay despite the data being loaded — fix in a future build, not urgent. **Depth-data
architecture clarified from the actual import code (was previously under-specified):** imported
LiDAR/survey depths are NOT baked into `index.html` — they live in browser `localStorage`
(`woongarra_imported_v1`) via the existing, already-generic "Imported depths" panel (plain CSV,
`lat,lng,depth` in metres below LAT, auto-thins to 25,000 points). This means multi-region depth
work (Sunshine Coast, Brisbane River, Burnett-area rivers) is a **data-processing task** (clip raw
LiDAR, convert AHD→LAT properly, export CSV, import through the app's own UI) — **not an
index.html build**, no `node --check`, no commit needed for the depth data itself. One trap: the
imported set is a single array, not region-scoped — importing a new area must choose MERGE, not
REPLACE, or it wipes prior regions' depths. **2b (Sunshine Coast) — zoning/FHA half reclassified,
depth half unchanged:** a Claude Code investigation (2 Jul, Sonnet 5) found Queensland runs a live
ArcGIS REST service exposing zoning + FHA directly (`.../ParksMarineProtectedAreas/MapServer`,
layers for Great Sandy zones, Moreton Bay zones, and statewide FHA, `f=geojson&outSR=4326`, both
under the 4000-record cap, no pagination) — this is fetchable and buildable by Claude Code itself,
**no manual QSpatial order needed**, a better route than 2a used. Confirmed **not** fetchable: the
Maroochy/Noosa 5 m bathymetric LiDAR — checked the CKAN API directly, only resource on record is a
QSpatial manual-order page (same order-and-email-link flow, no bulk API) — stays a **you-step**
regardless of which model builds it. Sunshine Coast tide port (Mooloolaba/Noosa) sourcing is still
unchecked. **Brisbane scope clarified:** Aaron's "Brisbane" means Brisbane River + Pine River +
bay surrounds. Pine River (HPZ08) and the broader bay are already covered — the whole marine park
was deliberately embedded in 2a specifically so Bribie/Pumicestone/bayside wouldn't be dropped. The
Brisbane River itself is the one open item: not part of the marine park, so needs its own check for
any zone-style closure (not yet done), plus depth via ELVIS (bounded to the tidal reach — LAT isn't
meaningful past the tidal limit). **ELVIS was down (dataset search failing) as of 2 Jul** —
transient per past experience, Aaron retrying.

**As of 3 Jul 2026 — 2b/Brisbane River data-sourcing progress + roadmap additions (v16.2, planning
only, nothing shipped):** The 2 Jul Claude Code investigation (zone/FHA fetch, Brisbane River
closure check, Sunshine Coast tide port) stalled after task 1 of 4 (Great Sandy zones fetch
in-flight) when Aaron switched devices — read from the terminal transcript only, repo state
unverified; cause was near-certainly a missed permission prompt, not a crash, and nothing was at
risk (fetch/validate only, no `index.html` edit, no commit). Confirms the CLAUDE.md/roadmap-in-repo
design resumes cleanly across devices — same instruction, fresh clone, no session continuity
needed. **ELVIS is back up.** Product choice clarified: QLD Government's **Bathymetry (3 m)** is
the correct product — finer than the 5 m previously assumed, a genuine improvement; **Digital
Elevation Models are the wrong product type** regardless of resolution (land elevation only, not
underwater depth) and must not be substituted for Bathymetry; Point Clouds (AHD) stay a fallback
only if Bathymetry has coverage gaps over the target reaches. **ELVIS order cap confirmed: ~10,000
tiles per order.** A Noosa→Bribie Island AOI returned exactly Sunshine Coast coverage (950
Bathymetry-3m tiles, under cap) but does **not** reach the Brisbane River mouth — the two regions
need separate AOIs regardless of the cap. A wider "Brisbane River or below" AOI hit ~17,000 tiles,
over cap — needs tightening (Bathymetry-only, single resolution, corridor bounded to the tidal
reach actually fished, not the full tidal limit) before it will submit. **Repo split for the
two regions:** `data/raw/sunshine_coast/` and `data/raw/brisbane_river/` (both gitignored) set up
ahead of data landing, keeping raw LiDAR separate through clip/convert. **Depth-data retention
policy set:** raw LiDAR tiles are disposable once clipped/converted and the resulting CSV is
confirmed imported and rendering correctly — delete freely, ELVIS is free and re-orderable. The
small processed `lat,lng,depth` CSV itself must be **kept**: it's **unconfirmed** whether the
`version:2` catch-log export/import actually carries `woongarra_imported_v1` (the depth array) the
way it's confirmed to carry photos, so the CSV may be the only durable backup until that's checked.
**New Hold item added:** national-scale coverage (QLD-wide + NT + WA + partial NSW) — see Hold
section; explicitly sequenced behind every remaining SEQ home-water region. **New backlog item
added:** 6b — wildlife/sighting badges, formalising the sighting-badges deferral already recorded
in item 6's v16 delta.

**As of 3 Jul 2026 — the stalled zone/FHA/closure/tide-port investigation completed (v16.3,
data-prep only, nothing shipped to `index.html`):** picked up cleanly on a fresh device exactly as
v16.2 predicted — same instruction, fresh clone, no lost context. All four original tasks done.
**Great Sandy zones + statewide FHA pulled and validated:** live ArcGIS fetch
(`.../ParksMarineProtectedAreas/MapServer/15` and `/7`, `f=geojson&outSR=4326`) confirmed **104**
Great Sandy features (28 CPZ / 17 GUZ / 31 MNP / 28 HPZ — matches the count already shipped in
`index.html`, and the shipped `zid`/`name` values — e.g. `CPZ25` "Snapper Creek" — match this pull
exactly, so the live Great Sandy zones already in the app are current, not stale) and **72 unique
declared FHAs statewide** (93 features incl. multi-part entries — matches Business Queensland's own
"72 declared" count, confirms the pull is complete, not partial). Clipped the FHA layer to a SE QLD
extent (lon 151.9–153.7, lat -28.2–-24.4 — Hervey Bay through Gold Coast) → **35 features / 26
unique plans**, incl. **Maroochy (FHA-008)** and **Noosa River (FHA-051)**, the two 2b needs.
Reprojected geometry simplified (~20 m tolerance, matching the 2a convention) and written to app
schema — confirmed by direct comparison against already-shipped features in `index.html`: zones use
`{name, zt, zid, notake}` (no per-feature `plan`/`src` — those come from `zonePopup`'s Great-Sandy
fallback), FHA uses `{plan: plan_num, name: res_name, mgmt: mngmt_type}` (verified against the
shipped Woongarra FHA entries, e.g. `FHA-002` "Kinkuna"). Output: **`data/great_sandy_zones_2026.geojson`**
(104 features, 494 KB) and **`data/fha_se_qld_2026.geojson`** (35 features, 436 KB) — both
merge-ready for a future wiring build, **not wired in this session** (data-prep only, per CLAUDE.md).
Raw pulls kept in `data/raw/` (gitignored). A validation script (interior-point + schema + range
checks, `notake` correctness, duplicate-`zid` check, cross-check against `index.html`'s already-shipped
feature IDs) passed 0 errors. **Brisbane River — no zone-style closure found, checked against the
complete authoritative data, not inferred:** point-in-polygon tested six points along the river
(mouth at Fisherman Islands through to Moggill) against all 74 Moreton Bay zone polygons — **zero**
hits; the full 72-declared-FHA statewide list contains **no Brisbane River entry**. So neither
pipeline that feeds `zoneAt()`-style behaviour (marine-park zoning, declared FHA) covers the river —
the app's existing "outside marine-park zoning — general rules apply" default is already correct
there, confirmed rather than assumed. **Caveat, a different mechanism, not zone-style, not wired:**
the Fisheries Regulation 2008 (checked directly against the current legislation text) separately
lists small weir-buffer closures — "Brisbane River at Old Mt Crosby Weir" / "at Mt Crosby Weir" / "at
Wivenhoe Dam" (the standard freshwater fish-passage pattern applied at every QLD weir/dam, not
Brisbane-specific) — and lists "Brisbane River (netting)" under the *commercial netting* closed-waters
schedule (recreational line fishing unaffected, same as the HPZ "line fishing generally OK" precedent).
Neither is a polygon zone; nothing to add to `zoneAt()`; noted for completeness only. **Sunshine Coast
tide port — Mooloolaba confirmed as the pick, Noosa Head is secondary, not blocking:** BOM's National
Tidal Centre port list (`bom.gov.au/oceanography/projects/ntc/qld_tide_tables.shtml`) classifies
**Mooloolaba as a Standard Port** — its own direct harmonic prediction, no offset math, 2026 + 2027
PDFs already published (`IDO59001_2026_QLD_TP019.pdf`, confirmed downloaded and spot-checked: header
reads "MOOLOOLABA – QUEENSLAND", coords 26°41′S 153°07′E, full daily H/L table present, heights in
metres — datum presumed LAT consistent with all other standard QLD ports per MSQ's general tidal-datum
statement, not independently re-stated in this PDF's own header, so flagged rather than asserted).
This is the same standard-port pattern already used for Burnett Heads and Brisbane Bar — Mooloolaba
alone can anchor the whole 2b region via `nearestPort`, same as Brisbane Bar alone anchored all of 2a
before Redcliffe's secondary offset was added. **Noosa Head is a Secondary Port** (own predicted-table
PDF exists, `TP021`, but time/height values are offset-derived from a standard port, not yet identified
which one or by how much) — a nice-to-have refinement later, exactly parallel to how Redcliffe was
added after Brisbane Bar in 2a, **not required to start a 2b build.** **Net new artefacts this
session:** `data/great_sandy_zones_2026.geojson`, `data/fha_se_qld_2026.geojson` (both trackable —
only `data/raw/` is gitignored). **Nothing wired into `index.html`; no build string bump; no commit
made by this session** (per CLAUDE.md, data-prep is not a build).

**As of 3 Jul 2026 — the two v16.3 open validation items resolved (v16.4, verification only,
nothing shipped):** **`version:2` export/import confirmed to carry `woongarra_imported_v1`** —
verified by direct code read, not inferred: `exportBackup()` (line 2225) writes the top-level
`imported` array out under the `imported` key alongside `spots`/`photos`/`profiles`;
`importBackup()` (lines 2244–2246) merge-restores it by lat:lng dedup and writes back to
`localStorage`. The `typeof imported!=='undefined'` guard is defensive style, not evidence of a
scope gap — `imported` is a top-level `let` in the same script block, so both functions close over
it. **The v16.2 "CSV may be the only durable backup" caution is superseded** — a `version:2` export
now covers imported depths on the same tier as photos/profiles. Raw processed CSVs are still worth
keeping short-term as the source-of-truth for re-deriving a region if needed, but that's a
convenience, not a backup necessity, now. **ELVIS Bathymetry (3 m) datum confirmed genuinely
unconfirmable via any headless route, not just unchecked:** the portal (`elevation.fsdf.org.au`) is
a pure Angular SPA — every path probed, including its own JS bundle filename, returned the same
empty HTML shell; no ANZLIC/ICSM catalogue record exists for this specific product on either
data.gov.au or data.qld.gov.au (the one adjacent record, the older 5 m Sunshine Coast product,
doesn't state a vertical datum either, so it wouldn't have resolved this regardless). **Downgraded to a
manual-order handoff, per the ROUTING rules:** check the datum field on the product/layer info panel
in the ELVIS UI itself before submitting the Bathymetry (3 m) order — not a Claude Code task, not
worth further searching.

**Species seed:** `guya_species_qld_v3.md` — kept in project knowledge (private), not the repo. Repo stays just the shipped `index.html`.

**Phase 1 spine (items 1 → 2 → 3) is complete.** Keystone journal, best-bets/range, and personal
patterns all ship. Remaining Phase 1 work is the collection/passport layer (4, 5, 6 — **4c profiles
shipped 14k–14l**) and the reference/utility/depth/coverage items — independent, slot in anytime.

---

## Design rules (carry into every feature)

- **Never assert legality.** Bag/size/protected limits are *personal reference only* — the user
  enters them, the app surfaces official sources + a "verify currency" caveat, and the adult
  angler makes the call. Holds for the kids' passport too: it celebrates the catch/sighting, it
  never tells a child a fish is legal to keep.
- **ID is a suggestion, never a verdict.** Any ID help — feature hints (in, see 4b), AI photo-ID
  (only if ever, see Hold) — offers candidates, never decides, and never touches keep/legal.
- **Zones only from legislated polygons** (`zoneAt()`). FHA stays a separate informational layer.
- **Offline-first.** Stored data shapes migrate, never orphan. `node --check` every script block.
  Preserve the green-zone drag safeguard.
- **Build string = the actual build date + a letter.** Format `YYYY.MM.DD` of the day it ships, plus
  `a`/`b`/`c…` for multiple builds the same day (e.g. `2026.06.19a`). Roll the date to the real build
  day — never freeze it. Bump on every build.
- **Safety layers never imply safety.** "No warning / out of season / no report" must never read
  as "safe."
- **Photos & personal data stay on-device** (localStorage/IndexedDB), private, never uploaded —
  unless/until a deliberate Phase 2 sync is chosen.
- **Location is one-shot and in-memory.** Any GPS use is a single `getCurrentPosition` fix when the
  user taps for it, held in memory for the calculation only — never stored, never transmitted, never
  a continuous `watchPosition` (the walk-tracker is the one explicit, opt-in exception). Default to a
  no-GPS path (e.g. map centre) wherever possible. Outbound calls that reveal a coordinate (Open-Meteo
  wind, map tiles) are per-request and disclosed, never a feed anyone else can read.
- **Spot-and-photograph ethic** for nature logging: look-don't-take by design. Sidesteps
  legality / protected-species / qoliqoli, and it's the right ethic for kids.

---

## Phase 1 — keystone + personal features
*Fits the current architecture as-is: local, offline, no backend, $0.*

**Spine (built in this order — each made the next more useful):**

1. **Auto catch-journal** — the keystone. Log a catch; auto-stamp date, spot, tide state, wind,
   moon phase, PB flag from data the app already computes. Everything below derives from it.
   - **DONE.** Catch form + species picker (14b); photo + EXIF (14c — image in IndexedDB by id,
     ~1600px/q0.8 downscale, EXIF `DateTimeOriginal` prefill, thumbnail, local & private);
     auto-stamp (14d — `env`: `tide{state,ht}`, `moon{name,illum}`, `wind{dir,kn}` (live wind if
     present), per-spot `pb` flag; conditions line + PB chip in the catch row; rides inside `spots`
     on export, old catches migrate cleanly). Export/import carries photos.
2. **Today's best-bets / spot scores** — rank saved spots by score for the chosen date.
   - **DONE (14e).** `scoreSpotsFor` ranks rating + catches + tide-pref vs daylight + majors + live
     wind. **Range layer (14e):** `~1 h / ~2 h / ~3 h / All` band buttons (straight-line km ÷ 80 ≈
     hours, labelled *rough*; a filter, not a re-rank), origin = **map centre** by default (no GPS),
     optional one-shot `📍 My location` (held in memory, not stored/sent), per-row
     `≈ km · ~time drive (rough)`. Band/origin are session-only.
   - **Target-species filter — moved out (14j).** A species chip filter was added here in 14g/14h
     (filter + boost saved spots by target/catch species, full-DB + group-level selection). **As of
     14j it has been relocated to the saved-spots list** (see "Saved-spots species filter" below) and
     **removed from "Best spots today"** — that panel is back to ranking your saved spots without a
     species filter layered on. *(**CORRECTED 27 Jun 2026 — this was mislabelled.** The in-IIFE filter
     machinery — `recSpecies`, `recSpeciesNameByKey`, `renderSpeciesChips`, `speciesMatch`, the `spPick*`
     picker — is **NOT inert.** Verified against the shipped v14 file: `speciesMatch()` actively boosts
     scores inside `rankSpots` (`if(recSpecies.size){…r.sc+=m.bump}`), the chips render into `#rec-species`
     and their clicks call `rankSpots()`, and `spPickOpen()` is bound to a live click handler — i.e. the
     best-bets species filter is in fact still wired and working, parallel to the saved-spots one. It is a
     working filter, not dead code. The "Cleanup → strip it" task is **cancelled** — see "Cleanup" below.)*
   - *Reality check:* with all spots within ~10 km of each other today, the range band is mostly
     forward-looking scaffolding — it earns its keep once coverage expands (#15). Straight-line
     distance under-counts road time; bands are labelled rough.
3. **Personal pattern surfacing** — plain aggregations over your own log ("bream: run-out, dawn,
   hardbody").
   - **DONE (14i).** Renamed the panel to **"Your patterns"** (never "AI"). Analytics now **prefer
     the stamped `env`** (tide state/height + moon illum captured at log time) and **fall back** to
     re-deriving from the date/time tables only for older, pre-auto-stamp catches. Added a **"By
     wind" bar** (8-point direction, drawn **only** from stamped `env.wind` — wind can't be
     reconstructed historically, so it's never back-filled; shows a plain "no wind stamped yet" note
     until live-wind catches exist). Honest caveats baked in: a "thin so far" line under ~8 catches,
     and a footer making clear these are **counts, not catch-rate** (they reflect when you fished,
     not just when fish bit) and **your own log only**.
   - *Caveat:* sharpens as the log grows. While it's thin, **6 (badges)** or **4c+ (profile-aware
     views)** deliver more visible value per build (4c profiles shipped in 14k).

**Collection / passport layer (built on the journal):**

4. **Field Log / Nature Passport** (generalises the species passport) — same record as a catch
   (location + time + photo + name + category); fishing is one category. Add categories:
   reef/marine life, birds, animals, reptiles, shells/plants (as sightings). Per-region
   collections, tick-off checklists, kids' badges/certificates. The stickiest, most
   family-friendly feature; nearly free once the journal exists.
   - *Seed:* `guya_species_qld_v3.md` — catch fish (incl. freshwater/inland), marine + bush
     wildlife sightings, bounded shells/plants starters that grow from photos.
   - *Sightings flow is separate from "Log catch"* — marine + bush wildlife categories, look-don't-take.
   - *Captive vs wild flag:* a `captive` boolean on sightings. Zoo/aquarium sightings are logged and
     visible but **excluded from the wild tally, milestones and rare badges**. Render captive as an
     outline tick vs a full/colour wild tick. One flag only; no separate captive store.
   - *Fiji reef-spotting collection:* pre-loaded Mamanuca species checklist, cached offline
     (ties to #12 trip bundle). Snorkel mode carries the #10b tropical safety framing. *(Fiji species
     list = data prep, deferred until closer to the Oct–Nov trip.)*
   - *Guardrails:* spot-and-photograph ONLY; photos local & private; ID help = suggestion only,
     never authoritative, never tied to take/keep.

4b. **Feature-ID — "prominent features to review" (offline, suggestion-only).**
   - **Tier A — SHIPPED (14f).** A "Look for:" key-features line under the species field in the
     catch form (updates live), **plus a "⇄ Compare look-alikes" side-by-side panel** for seven
     verified confusion sets: flathead, bream & tarwhine, whiting, mackerel, trevally & queenfish,
     the four tuskfish, cods & groupers. Verified vs Australian Museum / Fishes of Australia / NSW
     DPI / QLD DAF; 32 hints; offline; every panel says "features to review, not a verdict — confirm
     via Qld Fishing 2.0"; steers to "— unsure" when stuck. Never touches keep/legal.
   - **Tier B (deferred — per-group, sourced):** a real branching dichotomous key, but **only**
     across the confusion sets that trip people. Each couplet sourced from Fishes of Australia /
     Australian Museum and verified before shipping. **No universal key** — confidently-wrong is
     worse than none next to a keep/legal decision.

4c. **Local profiles & avatars (device-local — Phase 1, no sync).**
   - **DONE (14k–14l).** Profiles store `woongarra_profiles_v1`
     (`{v, active, list:[{id, name, avatar, color}]}`, top-level; default "Me" on first run). Each
     catch carries `by` (profile id). A **"Caught by"** selector in the log form defaults to the
     active angler, with inline **"+ New angler"**; the chosen angler's **avatar shows on each catch
     row**; a **"Logging as" chip** in the spots panel opens an **Anglers** sheet (switch / add
     [name + emoji + colour] / rename / delete + per-angler catch tallies). Profiles ride in the
     `version:2` export and **merge on import** (never orphan). Legacy catches stay **untagged by
     design** (no false attribution). Avatars are **emoji + colour, or an on-device photo** —
     **photo avatars shipped 14l**: pick a photo in the Anglers add flow and it's **downscaled to
     ~128 px and stored in IndexedDB** (reusing the catch-thumbnail downscale + async-resolve
     pattern), rendered in the avatar chip, the catch rows and the "Logging as" chip; emoji + colour
     stays the default/fallback. The avatar field is a `{type, val}` spec — **legacy bare-emoji
     values are read as `{type:'emoji'}` with no data migration**. Photo-avatar images **travel in
     the `version:2` export and merge on import** alongside catch photos (same `photos` store),
     never orphaned. No backend.

4c+. **Profile-aware views & family roll-up (depends on 4c).** Built on `catch.by`; local-only, no
   backend, no cloud login. Scope: per-profile filter on the saved-spots list; per-profile **"Your
   patterns"**; per-profile badges/certificates (feeds #6 — name + avatar already stamp); a **family
   roll-up vs individual tallies** view. *Strong pick once a second angler has logged.*

5. **Personal species / sighting tally** per region (and per domain: fish / marine / bush).
   Wild only — captive sightings excluded (see #4 flag).

6. **Adventure tasks / achievements + badges** — first fish, first bream, 5 species, 20 species in
   summer (as *personal* goals). Badges / certificates UI for the kids' passport.
   - **SHIPPED (v16 / 2026.06.28b).** Self-contained top-level IIFE; reads `spots`+`profiles`, renders
     into `#badge-out` behind a "🏅 Show badges" button in the patterns panel; per-angler `<select>`
     (Everyone + each profile, filters `c.by===id`); "earned / total" count; offline canvas-PNG
     certificate per unlocked badge (720×520, tier-colour border, emoji glyph, angler name, unlock
     date). **No egress, no IndexedDB writes, catch-log only.** **18 badges:** first / 10 / 25 / 100
     catches; 5 / 15 / 30 distinct species; 10 released; 5 distinct spots (**Rock Hopper**); **PB
     Breaker**; **New-Moon Ninja · Full-Moon Fever**; **Spring-Tide Specialist** (5 spring-tide
     catches); **Tide Whisperer** (all tide phases); **Four Seasons**; + secret **Grand Slam** (bream
     + flathead + whiting same day) · **Dawn Patrol** (04:00–06:30) · **Night Shift** (20:00–04:00).
     Unlock date = the catch that first completed the badge; locked non-secret badges show a progress
     bar (cur/target); secret badges show ❔ until earned.
   - **Honest deltas from the original spec (all data-model–driven, not scope cuts):**
     - **Tide Whisperer is 3-phase, not "four tide states."** The stamped `env.tide.state` only ever
       holds `rising` / `falling` / `slack` — there is no fourth state in the data, so the badge
       covers the 3 that exist. (Roadmap text below said "four"; corrected.)
     - **Moon / tide / season badges depend on stamped `env`.** Catches logged before auto-stamp, or
       in a region without tide tables (no `env.tide`), simply don't count toward those — by design,
       never fabricated.
     - **Sighting-based badges deferred to item 4.** Mon Repos "local hero", Reef Spotter (Fiji),
       captive-vs-wild, and any protected-species badge need a **sightings store that doesn't exist
       yet** (no `captive`/sightings record). Badges are **catch-log only** this build.
     - **Platform Pioneer not shipped** — needs a per-spot structure="platform" flag check; Rock
       Hopper (distinct-spots count) ships in its place. **The Local** (N home-water species) folded
       into the distinct-species ladder (sp5/15/30).
     - **Certificates fall back to the emoji glyph**, not the avatar photo, when no profile image is
       present (canvas stays asset-free / offline).
   - *Presentation:* rarity tiers (bronze #c8895a / silver #b6c2cc / gold #ffcf4d); locked badges
     greyed with progress bar; **secret** badges hidden until earned; **certificate PNG export**
     (canvas → image) with name + unlock date. All offline, no assets, no network.
   - *Rule held:* badges reward the catch/sighting/effort, **never legality**; foot disclaimer states
     own-log-only + "celebrate the catch — never legality." Captive sightings excluded from rare/wild
     badges (moot until the sightings store lands).
   - *Also flagged (not yet spec'd):* Aaron raised badge-unlock **presentation** styling — a
     popup/toast fired at the unlock moment, distinct from the existing on-demand certificate —
     explicitly deferred for him to think through before it's scoped. Not a commitment yet.

6b. **Wildlife / sighting badges (depends on item 4/5 — the sightings store, not yet built).**
   - Extends the badge engine (item 6) from catch-log-only to the wildlife/nature sightings log once
     it exists — reuses the same computation model, `#badge-out` UI, and offline PNG-certificate
     machinery; not a parallel system.
   - **The animal list and a rare/special badge tier already exist — in `guya_species_qld_v3.md`,
     not this file.** Bush wildlife (mammals: echidna, kangaroo, wallaby, koala, possums, flying-fox;
     reptiles: goannas, water dragon, blue-tongue, shingleback, pythons, brown/red-bellied black
     snake; iconic birds; frogs) was seeded 14 Jun 2026, alongside a badges section: first-of-category,
     count milestones (10/20/50 per domain), a **rare/special** tier (any marine or bush sighting, a
     protected species, a PB, first-of-species), and a **local-hero** badge (Mon Repos loggerhead).
     6b does not re-spec any of that — it's confirmed already written, just blocked on the sightings
     store existing to fire from.
   - **What's actually new here, distinct from the existing rare/special tier:** a **phased rollout
     by commonality** — ship badges for the common, frequently-logged species first, then add
     rarer/harder-to-spot species-specific badges as the sightings log matures, rather than the full
     list landing at once. The existing rare/special tier is a single badge for "any" rare-class
     sighting; this adds a *progressive*, per-species unlock ladder on top of it — the two are
     complementary, not overlapping.
   - **Captive vs wild reuses the existing `captive` flag (item 4), not a new field.** Zoo/aquarium
     sightings are logged and visible but **excluded from wild-tally badges**, same discipline
     already recorded for item 5's species tally. A separate, smaller **"Zoo Log" badge set** (a
     captive-sightings count, so a captive sighting still unlocks something rather than being
     silently excluded) is worth considering — genuinely optional, not yet decided.
   - **Rule held, same as item 6:** badges reward the sighting/effort, never legality or
     protected-status — no badge implies a species was legal to approach, handle, or collect;
     look-don't-take stays the sightings ethic (design rules, above).
   - **Blocked until the sightings store ships.** Don't sequence ahead of item 4/5 — there's no
     sighting data to badge yet.

**Reference / utility layers (independent — slot in anytime):**

7. **POI layers** — boat ramps, kayak launches, jetties, reefs, curated tackle stores.
   (Ramps/kayak low-relevance to Aaron's own land-based fishing; useful for family.)
8. **Gear tracking** — rods / reels / lures, local CRUD. Ties into the EOFY tackle workbook world.
9. **Navigation** — GPS track breadcrumb + saved routes, stored locally. (Offline basemap cache
   already done.)
10. **Official live warning feeds** — BOM warnings, cyclone / storm, via API like Open-Meteo, with
    source + caveat. Never imply absence = safe.
    - **10b. Seasonal stinger advisory (tropical coverage)** — static region+risk-window reference
      (QLD Nov–May / NT Oct–Jun / WA Ningaloo Nov–Apr / Broome year-round) + official source links
      + current-month check. ADVISORY ONLY — never "safe": elevated-risk window + stings possible
      year-round + verify official source. Sources: SLSQ, NT Health, HealthyWA, DBCA/Explore Parks
      WA, SLSA BeachSafe.
11. **Closures layer** — official fisheries closures as an informational overlay, same discipline
    as zones / FHA.
12. **One-tap trip bundle** — download spots, depths, zones, FHA, tide tables, regional checklists
    for a trip in one action (Fiji / remote use). Builds on the existing offline cache.

**Depth & soundings layer (extends the existing depth-point / slope-line / shading tools):**

> **Hard honesty for both:** Guya only knows depth where *you* have data — your logged soundings
> or imported GPX. No seabed database; never infer depth from Navionics/chart art. Land-based with
> no sounder, the realistic source is a **castable sonar (Deeper / iBobber) → GPX → import**, or
> points dropped manually. Output is labelled *interpolated from your soundings — rough where sparse*.

13. **Deepest sounding within R of live GPS (walk-to).** Radius query over stored depth points +
    imported GPX near live GPS; highlight the deepest, show bearing + distance + depth. With nothing
    in range, says "no soundings within R" — no guessing. (Reuses the one-shot GPS pattern from
    best-bets; the slope tool's `nearestDepthPoint` / `idwDepthAt` are the building blocks.)
14. **A→B depth transect + profile chart.** Upgrade of the slope-line tool: GPS-anchored A and B,
    sample the interpolated surface every ~10 m. **Do NOT label the map every 10 m (clutter).** Draw
    the A→B line + a separate **depth-vs-distance profile strip** (reuse the tide-curve SVG pattern).
    Safety note: chasing a deeper mark along a rock platform can walk you into worse swell/wash —
    keep the wind/swell-exposure flags in view.

> **Home-water depth reality (SE QLD / Moreton Bay), confirmed 19 Jun 2026, sourcing decided
> 12 Jul 2026 (v16.28), Maroochy/Noosa SHIPPED 12 Jul 2026 (v16.33):** beyond the open coast
> this is a physics + coverage gap, not a missing download. Turbid water defeats laser bathymetry — a
> satellite-laser (ICESat-2) study found >half of Moreton Bay too sediment-laden to read — so the
> clear-water LiDAR that gave Woongarra its shading can't be replicated up the Pine / Brisbane / Hays
> Inlet. National open bathy (GA AusBathyTopo, 30/50/100 m) is coarse open-coast only; the one all-QLD-
> estuary composite (CSIRO 5 m) fills gaps with **modelled** creek depth → out by the no-chart-art
> rule; hydro charts and **Navionics are both rejected on the same rule** (chart-derived, not a
> verified survey — see v16.28); ELVIS's own "Bathymetry" bucket is the EOMAP satellite product,
> rejected twice already (v16.8, re-confirmed v16.28) — do not order from it. Realistic home-water
> depth = (a) **your own sonar → GPX** (works in mud; already supported); (b) **real bathymetric
> LiDAR for Maroochy/Noosa — DONE, not just sourced:** a 2011 Fugro LADS Mk 3 survey (QSpatial,
> "Bathymetric LiDAR for Sunshine Coast," manual order, see item 14) has been processed into
> `data/maroochy_noosa_bathy_v1.csv` — 946,877 points, −1.15…+42.48 m LAT, 99.0% genuinely
> submerged (v16.33) — the project's first real depth data, not yet imported to the phone pending
> a thinning decision; (c) otherwise **no depth layer** — spots / tides / zones / FHA / patterns
> all work without it, and this remains true everywhere outside the Maroochy/Noosa footprint.
> Don't bake modelled bathymetry.

14b. **Intertidal flats & exposure — DEA Intertidal (EVALUATED 20 Jun 2026 → qualified GO, Exposure-only,
    gated on a confidence check).** Free (CC BY 4.0), satellite-derived intertidal product.
    **Verified product facts (v2.1.0, `ga_s2ls_intertidal_cyear_3`):** 10 m, Landsat + Sentinel-2,
    epochs 2016–2024 (latest = 2024, a 2023–2025 window), annual; native CRS **EPSG:3577 (GDA94/Albers)**
    → reproject to WGS84 for Leaflet; **4 core layers** (Elevation, Elevation Uncertainty, Exposure, and
    a 5-class Extents) + 7 tidal-attribute + 4 QA layers; COG on AWS / ELVIS / NCI / WMS.
    - **Datum → LAT is solved inside the dataset.** Elevation is metres relative to **modelled MSL**, and
      the suite ships a per-pixel **`ta_lat`** band (modelled LAT, same units) → `height_above_LAT =
      elevation − ta_lat`, epoch-matched. Crude fallback = single offset (**Brisbane Bar MSL = LAT + 1.32 m**,
      HAT 2.78). DEA's modelled epoch-LAT ≠ BoM chart-datum LAT(1992): fine for a rough layer, disqualifying
      for a cm now-cast.
    - **The catch — three cautions stack on exactly these flats.** (1) **Borderline microtidal:** Brisbane
      Bar spring range ≈ 1.80 m — DEA validates meso (2–4 m) at corr 0.90 / R² 0.80 but micro (<2 m) at only
      0.61 / 0.37 (RMSE ~0.27–0.33 m throughout); GA says use micro with caution. (2) **Embayment tide-model
      error:** elevation is built from *modelled* tide per pass; GA flags embayments/estuaries as caution-and-
      check-the-uncertainty (named bad cases are all amplifying embayments — Moreton not named but shares the
      mechanism). (3) **Tidally-correlated turbidity false-positives:** turbid water can be mapped as "flat,"
      and Bramble Bay turbidity is tide-modulated. So turbidity is *survived*, not *solved* — temper the old
      "works in turbid Moreton Bay" line.
    - **Build the Exposure half, defer the now-cast.** Exposure (% time a pixel is dry, static) is the
      buildable half: **datum-free** (sidesteps the LAT conversion entirely), **relatively robust** (the
      ordering of which banks bare more often survives absolute bay error), and **reads as habitat not depth**
      (clear of the no-bathymetry/no-safety rules; structurally can't give channel depth — Extents 3 only).
      The "covered now" elevation-vs-tide feature is the **dangerous half** (datum-dependent, bay error compounds
      the tide-engine error, a cm depth-over-flat readout reads exactly like bathymetry) — **HOLD**; if ever
      built, a coarse 3-state (likely dry / marginal / likely covered), never a number.
    - **Mandatory confidence check before any build (run in DEA Maps — click-to-query each pixel; ~20 min over
      Hays Inlet / Bramble Bay / a few Pumicestone banks):** `elevation_uncertainty` ≤ ~0.2 m (worry ≥ 0.4 m);
      `qa_ndwi_corr` high/positive; `extents` = 3 on known flats AND a known channel/gutter is **not** painted
      as intertidal (the false-positive test); `ta_offset_low` low (else the spring-low drains aren't mapped);
      `qa_count_clear` ≥ 5+. **Pass → build per spec. Fail → no-go; home-water depth/flats stays sonar → GPX.**
    - **Build spec (conditional on pass):** Exposure only, 2024 epoch, processed **per-flat** (not one long
      Pumicestone tile). QGIS (in 3577, reproject last): clip Elevation/Exposure/Extents/Uncertainty/ndwi_corr
      → mask to `extents==3 AND uncertainty≤0.2 AND ndwi_corr≥~0.5` → bin Exposure into 3 fishing-meaningful
      classes (>70% / 30–70% / <30% exposed) → reproject 3577→4326 → vectorise, dissolve by bin, simplify ~20 m,
      drop slivers → GeoJSON. **Render — primary:** classified GeoJSON loaded like the zone polygons (same
      QSpatial→GeoJSON workbench), 3 semi-transparent fills below the zone layer, legend, toggle. **Fallback if
      vertices bloat the file:** indexed-PNG `L.imageOverlay` per flat (fixed bbox, no per-pixel clicks).
      **Label (verbatim, always):** "satellite-derived intertidal — flats only, rough; shows how often a flat
      is dry, not depth or safety" + a drying flat is **not** walkable/safe (soft mud, drains, incoming cut-off)
      — same never-implies-safe discipline as Scout walkability.
    - **Sequencing:** Exposure needs no tide port, so it doesn't hard-depend on 2a — but 2a (dogfooding) stays
      first, and real sessions on the flats should sanity-check the exposure pattern before it's trusted. Slots
      in after as its own small piece.

**Coverage & planning:**

15. **Multi-region coverage + trip-planner.** The range band UI is built (#2) and waiting on data.
    To make "best spots within ~2 h" mean anything beyond Woongarra, each new region needs its own
    **tide port** (everything currently leans on Burnett Heads / LAT), plus its zones, FHA and spots.
    Build region by region; the planner switches on automatically as data lands. Pair with #12 for
    offline use away from home. *Drive-time bands stay rough straight-line estimates — no paid routing.*
    - **"Local" = a two-region home cluster, built 2a → 2b (decided 19 Jun 2026): 2a = Moreton Bay /
      Redcliffe (the thin slice, immediate priority); 2b = Sunshine Coast (next).** Build the slice
      machinery once (multi-port tides, multi-polygon `zoneAt()`); each region is then just added data.
    - **Brisbane River (clarified 2 Jul 2026) — Aaron's "Brisbane" means river + Pine River + bay
      surrounds.** Pine River (HPZ08) and the broader bay are already covered — 2a deliberately
      embedded the whole marine park (not a home-water clip) so Bribie/Pumicestone/bayside wouldn't
      be dropped, and that same embed covers Pine River and general bayside water. The river itself
      is not part of the marine park and is the one open item: (1) check whether any zone-style
      closure applies to it at all — if none, the app's default "general rules apply" behaviour is
      already correct and there's nothing to build; (2) depth via ELVIS, bounded to the tidally
      -influenced reach only (LAT stops being a meaningful datum past the tidal limit — confirm where
      that sits before processing further upstream). Depth is a data-processing/import task, not an
      index.html build (see status block at top of file).
      **(1) RESOLVED 3 Jul 2026 — no zone-style closure.** Checked directly, not inferred: zero of the
      74 Moreton zone polygons contain any point along the river (mouth→Moggill tested) and the river
      has no entry in the full 72-declared statewide FHA list. The app's default already-correct
      behaviour needs no change. A separate, non-zone mechanism exists (Fisheries Regulation 2008 weir
      buffers at Mt Crosby Weir / Wivenhoe Dam + a commercial-netting closed-waters listing) — doesn't
      touch recreational line fishing or `zoneAt()`, noted for completeness, not wired. See v16.3
      status block for full detail. (2) depth via ELVIS stays open, tracked in v16.2's status block.
    - **2a — Moreton Bay / Redcliffe thin slice. ✅ SHIPPED 27 Jun 2026 (v14 / 2026.06.27a).** Rationale: **dogfooding.** The app isn't usable
      day-to-day while all its data sits ~4 h north, so make home *minimally usable now* and let real
      sessions reorder the rest — don't wait to build the whole region. Features (journal, patterns,
      badges, profiles) are already area-agnostic; only the data layers are region-locked, and you
      don't need all of them to start. **The slice = (1) embed one Moreton Bay tide port (Brisbane Bar
      or a verified closer secondary, LAT) with per-location port selection, and (2) load the Marine
      Parks (Moreton Bay) Zoning Plan 2019 polygons into `zoneAt()`.** Both regions then coexist
      automatically — `zoneAt()` evaluates whichever polygon a pin falls in; tide picks the nearest
      known port. **Defer FHA + depth.** Zones aren't optional here: the live hazard is the app showing
      *Great Sandy* zones at Redcliffe (worse than none), and the 2019 plan puts restricted zones right
      on the home water. This does **not** replace Woongarra — both stay. Full FHA / depth / planner for
      home accrete after, as the rest of #15.
      - **VERIFIED 20 Jun 2026 — tide port.** Standard port for Moreton Bay = **Brisbane Bar** (LAT
        27°21′S 153°10′E, **datum = Lowest Astronomical Tide**, BoM National Tidal Centre predictions
        via MSQ *Queensland Tide Tables 2026*, CC BY 4.0). **Redcliffe is a secondary at +0:00 / +0:00**
        time offset from Brisbane Bar (range ~96% of Brisbane Bar), so for the home extent **Brisbane Bar
        timing applies directly — no per-port time shift needed.** (Scarborough −0:07, Bongaree/Bribie
        +0:00/−0:15 if ever needed.) The official MSQ 2026 table is in project knowledge (the file
        mislabelled `2026_queenslandtidetables__1_.pdf` is actually its UTF-8 text). **2027 Brisbane Bar
        needs the MSQ 2027 tables (not yet in project)** — small follow-up; not blocking 2026 use.
      - **CORRECTED 20 Jun 2026 — zone codes (was wrong in v10/v11).** The earlier note called
        "HPZ06 Redcliffe / HPZ08 Pine River" *no-take* — **they are not.** Per the 2019 plan itself
        (legislation.qld.gov.au sl-2019-0175): **HPZ06 Redcliffe** and **HPZ08 Pine River** are
        **Habitat Protection (dark-blue) zones — line fishing generally OK under marine-park rules,
        subject to Fisheries.** The genuine **no-take green (Marine National Park) zones on home water
        are MNP09 Deception Bay, MNP11 Hays Inlet, and the MNP12 / MNP13 cluster off Bramble Bay /
        Pine-River mouth.** The 2019 plan's four zone types (MNP green / CPZ yellow / HPZ dark-blue /
        GUZ light-blue) map 1:1 onto the app's existing `STYLES` keys — **no STYLES change needed**;
        Moreton features just carry the right `zt`+`zid`+`name`. **Green-zone sanity check for the wiring
        build:** after load, `zoneAt()` inside **MNP11/MNP09** must return `notake:true`; inside
        **HPZ06/HPZ08** must return `zt:"HPZ", notake:false`.
      - **SOURCING — ✅ DONE + VALIDATED 20 Jun 2026 (separate chat, no code shipped).** Both
        embeddable files built and verified; ready to attach to the wiring build.
        (1) **`brisbane_bar_tides_2026.json`** — shape `{"YYYY-MM-DD":[["HH:MM",ht,"H"|"L"],…]}`
        matching `BURNETT_TIDES_2026`. Parsed **column-aware** from the MSQ text (a naïve top-to-bottom
        parse mis-read Jan 1 as `0245/0915/1605/2133` vs the true `0100/0741/1422/1944`). 365 days;
        every date's weekday matches the printed table; chronological; strict H/L alternation;
        page-boundary + Jan/Feb-1 trap days spot-checked. BoM/Commonwealth + LAT + no-warranty
        attribution rides as a JS comment at embed time. **2027 still needs the MSQ 2027 tables.**
        (2) **`moreton_zones_2019.geojson`** — 74 zones, **whole park** (Caloundra/Pumicestone →
        Jumpinpin), GDA94 → WGS84, **~11 m** simplified, 235 KB. Each feature `properties =
        {name, zt:("MNP"|"CPZ"|"HPZ"|"GUZ"), zid, notake:(zt==="MNP"), plan:"Moreton Bay MP",
        src:"https://parks.qld.gov.au/parks/moreton-bay/zoning/app-and-maps"}` — **merge-ready** into
        `ZONES.features`. Passes `validate_moreton_zones.py` exit 0 (self-tested to reject
        flipped-notake / out-of-extent / missing-zone / bad-zt); every home-water zone interior-point
        verified.
        **Two corrections to the v12 sourcing plan:**
        • **Source = the QSpatial "Moreton Bay marine park zoning 2008" SHP** (Aaron-supplied). The
          **"avoid 2008" rule is REVERSED**: the 2019 remake (commenced 1 Sep 2019) made
          administrative-only changes with **zero zone-boundary changes**, so the 2008 geometry *is*
          the current legislated plan and carries the same zone IDs (HPZ06 Redcliffe, MNP11 Hays Inlet,
          …) — confirmed against both the legislation and the attribute data; labelled as the 2019 plan.
          (The MSES "highly-protected-zones" layer is **no-take only** — wrong; it omits HPZ/CPZ/GUZ.)
        • **Embed the WHOLE park, not the old home clip.** The lat −27.05/−27.45 box would have dropped
          **Bribie + Pumicestone**, which Aaron fishes; 74 polygons is trivial for `zoneAt()`.
        **Wiring note:** home-water zones overlap (Hays Inlet/Bramble Bay carries MNP + CPZ) →
        `zoneAt()` must surface the **most-protective** zone (MNP > CPZ > HPZ > GUZ), not first match.
      - **WIRING — ✅ DONE 27 Jun 2026 (v14), exactly to spec.** Added `BRISBANE_TIDES_2026` top-level
        beside `BURNETT_TIDES_2026`; add a tiny `PORTS` registry + `nearestPort(centre)` (haversine,
        origin = map centre, no GPS) and route the best-bite IIFE's tide lookup + the "Tides · Burnett
        Heads" heading/notes through it. Merge Moreton features into `ZONES.features` (zoneAt + zoneLayer
        pick them up automatically). Make `zonePopup` region-aware via per-feature `plan`/`src` with a
        Great-Sandy fallback for legacy features (also the depth-read zone popup). Default map view +
        Home button to **Redcliffe** (Woongarra stays reachable). Preserve: Leaflet byte-identical,
        green-zone drag safeguard (already generic via `nz.name`/`nz.zid`), `zoneAt`; `node --check` both
        blocks; bump build to the live date. No stored-shape migration (ZONES/tides are static data).
        **As shipped:** all of the above done and validated (Leaflet byte-identical, both blocks
        `node --check` clean, 178 ZONES features, overlap pin returns most-protective MNP, nearestPort
        verified both ways). **These 2a follow-ups are now RESOLVED in v15 / 2026.06.28a:** best-bite
        **astronomy** and both **wind buttons** (plus the spot wind-check) follow the nearest tide port via
        `nearestPort(map.getCenter())` instead of a fixed Bargara lat/lng; the live-wind button's latent
        `ReferenceError` (private `curPort()`/`tideTable()` called from a sibling IIFE → silent "No signal"
        even online) was fixed in the same pass.
    - **2b — Sunshine Coast (Caloundra → Noosa), next after 2a.** Why it's worth including: it's the
      one nearby (~1 h) region where **depth actually works** — real 5 m bathy-LiDAR exists for the
      Maroochy / Noosa estuaries (data.qld.gov.au), so the Woongarra-style shading can be reproduced
      here (unlike turbid Moreton Bay). Layers = a Sunshine Coast tide port (Mooloolaba / Noosa, LAT);
      Maroochy + Noosa **FHAs**; and the **bathy-LiDAR depth ingest** (clip + AHD → LAT + convert to the
      depth format — a distinct, meatier job, so it gets its own piece, never bolted onto 2a).
      **Zoning finding (verified 19 Jun 2026):** Moreton Bay Marine Park's northern boundary is
      **Caloundra**, so the Pumicestone / Caloundra end is already covered by 2a's Moreton zones, but
      **Mooloolaba / Maroochy / Noosa sit outside any marine-park zoning** (north of Moreton Bay MP,
      south of Great Sandy MP) — **no green-zone polygons to load there.** So the app must show
      "outside marine-park zoning — general fisheries rules + FHAs still apply, confirm via Qld Fishing
      2.0," never silence that reads as "anything goes" (the safety-layer rule). Confirm the Noosa-north
      edge against Great Sandy's southern boundary when sourcing.
      **SOURCING ROUTE UPGRADED 2 Jul 2026:** Claude Code confirmed a live ArcGIS REST service
      (`spatial-gis.information.qld.gov.au/arcgis/rest/services/Environment/ParksMarineProtectedAreas/MapServer`)
      exposes Great Sandy zones (layer 15, 104 features), Moreton Bay zones (layer 2 — same family
      that fed 2a), and statewide FHA (layer 7, 93 features, includes Maroochy/Noosa) directly —
      `?where=1=1&outFields=*&f=geojson&outSR=4326` pulls each layer whole, both counts under the
      4000-record cap, `outSR=4326` returns WGS84 straight (skips the GDA94→WGS84 reprojection 2a's
      QGIS workbench needed). **No QSpatial manual order required for zoning/FHA** — Claude Code can
      pull, clip, simplify, and build this GeoJSON itself. The bathy-LiDAR half is unaffected —
      confirmed separately (CKAN API checked directly) as still order-and-email-link only, no bulk
      API, no shortcut; stays a manual ELVIS job regardless.
      **ZONING/FHA PULL + TIDE PORT DONE 3 Jul 2026** (data-prep, not wired): Great Sandy zones (104)
      + SE-QLD-clipped FHA (35, incl. Maroochy/Noosa) fetched, validated, written to
      `data/great_sandy_zones_2026.geojson` / `data/fha_se_qld_2026.geojson`, app-schema-matched
      against what's already shipped. **Tide port = Mooloolaba** (BOM/NTC Standard Port, own harmonic
      prediction, 2026+2027 PDFs published, no offset math — same pattern as Burnett Heads/Brisbane
      Bar). **Correction (v16.5, 4 Jul):** Noosa Head is itself a **Standard Port** (own harmonic
      prediction, confirmed against MSQ's 2024 Semidiurnal Tidal Planes table), not a Secondary Port
      as first assumed here — no offset math needed there either.
      Full detail in the v16.3 status block (tide-port discovery) and v16.5 (the correction). Ready for a wiring build: merge the zone file (already
      matches what's shipped, so this is really a freshness-confirmation, not new data), add the FHA
      file as the first FHA layer, source Mooloolaba's day-by-day 2026 H/L into a
      `MOOLOOLABA_TIDES_2026` embed. Bathy-LiDAR depth ingest remains the separate, meatier piece
      tracked in v16.2.
      **STATUS UPDATE (v16.9–v16.11, 4 Jul):** the depth half is now DONE (import-wise) — the
      intertidal-ground CSV (`sunshine_coast_intertidal_ground_v1.csv`, 188,855 points) has been
      imported to Aaron's phone as a single-pass, auto-thinned import (~18,875 points / ~547 KB,
      ~79 m effective resolution — the phone's real `localStorage` headroom, measured at ~4.0 MB,
      doesn't support the full-resolution multi-chunk alternative; see v16.9 for the fill-test
      result and v16.6/v16.9 for the thinning-algorithm confirmation). **RESOLVED (v16.12):** no
      2b zoning/FHA/tides wiring build was ever run — `ZONES.features` counts exactly 178 (v14
      state); the v16.11 visual anomaly was unrelated (real, correctly-rendering offshore MNP
      zones, not a wiring artefact). 2b wiring remains open, unblocked, ready any time.
      **CORRECTION (v16.17–v16.18, 5 Jul):** separately from the wiring question, the imported
      intertidal-ground CSV itself is confirmed to contain the same open-water misclassification
      artifact found in the Brisbane River delivery — ~2.7 km² across the MoretonBay_2014/2018
      subset (Beachmere/Deception Bay/Pumicestone), plus an unresolved audit gap over the
      dominant Sunshine Coast vintage groups. Treat the already-imported depth data as unreliable
      in open-water areas until a masked re-export lands, and note the phone-side fix will need a
      **REPLACE** of the existing import, not a MERGE — see the top-of-file status block and
      v16.18.
    - **Data-prep workbench:** **QGIS** turns the official source into app-ready GeoJSON — download the
      **QSpatial** 2019 zoning + FHA (SHP / FGDB), clip to the home extent, reproject **GDA94 → WGS84**,
      **simplify vertices** (keep the single-file size sane), export GeoJSON for `zoneAt()`. QSpatial =
      the zone / FHA source. The **GA portal / GA online tools** are discovery + coarse open-coast
      bathy only (AusBathyTopo) — no help inside the bay. **Superseded for 2b zoning/FHA specifically**
      by the direct ArcGIS REST route above — QGIS/QSpatial-order remains the fallback pattern for any
      future region where no equivalent live service is found.
16. **Scout / candidate-spot finder (find spots in a *new* area, independent of your own log).**
    Distinct from #2, which only ranks spots you've already saved. Two tracks, deliberately split:
    - **In-app Scout = structure-first, offline, zone-aware (the buildable version).** Define an area
      and surface candidate **land-based** features Guya already has or can compute — headlands, rock
      platforms, creek/river mouths, shore-adjacent drop-offs from *your* soundings — **restricted to
      legislated open zones via `zoneAt()`** (no-take excluded). Each candidate shows zone type + ID +
      warning + official source, **never "fish here."** Bundle the **Spotter rubric** (wind exposure,
      swell, access, tide-stage fit) as a structured checklist.
    - **Access / walkability assessment (core, not optional).** Flag likely access obstacles from
      **OSM data bundled per region**: nearest track/path/parking, route crossing mapped
      mangrove/wetland, proximity to a mapped cliffline, steep coastal gradient *iff* contours are
      bundled. **Honest limits:** true cliff height, passability, private-land access and current
      erosion are NOT reliably knowable offline. Surfaces obstacles as **cautions to verify — never
      "walkable" / "accessible" / "safe."**
    - **Reports = a planning-chat job, NOT an in-app feature.** Monthly/weekly fishing reports are
      *species-and-season* signal, not geolocation: broad buckets, boat-skewed, no coordinates, and
      copyrighted. Research them in a chat (Claude searches + paraphrases — never reproduces — and
      returns a candidate-mark shortlist with rough coords + zone caveats), then **import as candidate
      pins.** In-app report *scraping* is on the Hold list.
    - **Hard dependency on #15.** Scouting a *new region* needs that region's zone polygons + tide
      port first. Over current Woongarra coverage it can be prototyped now.

**Cleanup (housekeeping, low-risk, do when convenient):**

- **~~Strip the inert best-bite species-filter code.~~ CANCELLED 27 Jun 2026 — the premise was false.**
  Verified against the shipped v14 file: the in-IIFE cluster (`recSpecies`, `recSpeciesNameByKey`,
  `renderSpeciesChips`, `speciesMatch`, `spPick*`) is **live**, not orphaned — `speciesMatch()` boosts
  scores inside `rankSpots`, the chips render into `#rec-species` and their handlers call `rankSpots()`,
  and `spPickOpen()` is bound to a live click listener. It is the working **best-bets** species filter,
  separate from and parallel to the saved-spots list filter (the top-level `spotSpecies` /
  `spotSpeciesMatch` / `renderSpotSpeciesChips` / `spotPick*` cluster). Stripping it would break
  best-bets species boosting and throw `ReferenceError`s. **Do not remove.** (The 2a wiring build
  re-confirmed this against the actual JS and correctly declined the cleanup; the "orphaned" label that
  rode from v7 → v13.1 was simply wrong.)
- **New (v16.15, 5 Jul 2026): confirm `fishhabitat_bundaberg_region.geojson`.** Surfaced during the
  5 Jul git safety-net commit — committed to the repo but not recorded anywhere in this roadmap or
  the project brief. Origin and purpose unclear; worth a quick check on what it is and whether it
  belongs before it's forgotten again.
- **Standing (v16.15, 5 Jul 2026): confirm the git remote.** The repo-rename notice
  (`AzmixLabs/Guya` → `Guya_Wamu`) has now fired twice (v16.7 and the 5 Jul manual commit) without a
  `git remote -v` check ever confirming the local remote actually points somewhere correct — only
  that the GitHub Pages URL/phone icon kept working. Low urgency, but resolve it properly rather
  than dismissing a repeat warning a third time.

---

## External ID companions (use alongside Guya — Guya stays suggestion-only)

Guya's own ID is feature-hints (4b), never an AI verdict. For the actual ID, point to these free tools:

- **Seek by iNaturalist** — best for the kids + passport ethic: free, offline-capable, real-time
  camera ID, badges/challenges, privacy-friendly, no account.
- **iNaturalist** — best free general tool for unusual creatures (reef fish, marine inverts,
  reptiles); CV suggestion + a human community that confirms/refines. Covers Fiji reef.
- **Merlin Bird ID** (Cornell) — best for the passport's bird category: free, offline AU pack,
  photo + sound ID.
- **Qld Fishing 2.0** (official Fisheries QLD, free) — the **authority Aaron checks himself** for
  the keep/legal call: species, size/possession, closures, "can I fish here," offline cache. Guya
  points to it; Guya never replaces it.
- **iDfish** — solid AU flow-chart key, offline, but ~$10/yr and size-limit-centred; not a kid's
  tool. Skip generic freemium "AI fish identifier" apps.
- **Reference (free, web):** Fishes of Australia, Australian Museum (seed verification), Atlas of
  Living Australia (regional checklists when expanding lists / new regions for #15).

---

## Phase 2 — shared / family
*Forces a light sync layer. Build only when you actually want cross-person sharing.*

> **Architecture note:** localStorage is per-device. Sharing between Aaron, sisters, nephews and
> daughter needs sync. For ~6 known people use the **lightest** option — a shared backup file via
> iCloud/Drive, or **one** free Supabase table keyed by a family code — **not** a full accounts/auth
> SaaS stack. Keep it a tool, not a product.

- Parent / child accounts (lightweight identity, not full auth) — the *networked* upgrade of 4c
- Shared catches / sightings, catch feed, photo galleries (family-private)
- Family challenges & progress ("20 species in summer" across the family; "catch a fish together")
- Competitions / seasonal events — Brisbane Bream Challenge, Flathead Challenge — as shared
  leaderboards (the *personal* versions are Phase 1)
- Angler profiles (networked)

---

## Hold / caution (do not build, or build only with care)

- **Crowdsourced croc / shark / bluebottle sightings** — needs a userbase + moderation, and must
  NEVER imply "no report = safe." **Shark sightings: dropped.** Logging your *own* sightings locally
  is fine; a reporting network is not, for a private family tool.
- **AI fish/animal ID that states legality or eating quality** — don't. Breaks the legality rule;
  pure liability. (Offline feature-ID — 4b — is the suggestion-only alternative that's *in*. For real
  AI ID, point to the external companions.)
- **Public / stranger social feed, comments, messaging** — not for a private family tool;
  ~80% of the maintenance for ~20% of the value.
- **Live drive-time routing** (Google/Mapbox/OSRM) for the range band — needs network + API key +
  ongoing cost; breaks offline-first/$0. Straight-line estimate stays the deliberate choice.
- **In-app scraping/ingestion of fishing-report archives** (Fishing Monthly et al.) to auto-place
  spots — don't. (1) **signal** — broad-bucket, boat-skewed prose with no coordinates → fuzzy pins
  that quietly imply "spot"/"legal"; (2) **copyright** — commercial editorial, can't bake the archive
  into a shipped app; (3) **architecture** — a scrape/parse/store pipeline breaks offline-first/$0.
  Reports as a *chat research step → candidate pins* is the supported path (#16).
- **National-scale coverage (QLD-wide + NT + WA + partial NSW)** — flagged as a possible future
  direction, explicitly sequenced **behind every remaining SEQ home-water region** (2b Sunshine
  Coast, Brisbane River) — near-before-far, places Aaron actually fishes first. Architecture
  blocker, not just a priority call: the single-file baked-zone model and the flat, non-region-
  scoped `woongarra_imported_v1` depth array don't scale past a handful of SEQ regions — zone
  polygons baked into `index.html` would grow an order of magnitude (each state runs its own
  separate marine-park estate, zoning/FHA source, schema, and licensing — no shared endpoint the
  way QLD's ArcGIS service was), and depth storage needs a real rework (region-scoped keys, likely
  IndexedDB with spatial partitioning instead of one flat localStorage array) before this is viable
  at all. Tide-port sourcing likely scales better — BOM/National Tidal Centre produces tables
  nationally — but zoning/FHA sourcing is a from-scratch integration per state. Needs its own
  architecture spike before touching a fifth region, not a #15 line item.

---

## Notes on the "game-changer" ideas

- **Predictive Bite Engine** = Phase 1 items 2 (done) + 3 (done). Predicts from tide/wind/moon/time
  + your history; weak until you've logged enough trips. Useful, not an oracle.
- **Species / Nature Passport** = item 4 with larger lists. The collection hook is the genuinely
  sticky, family-friendly differentiator.
- **Personal Fishing AI** = item 3 evolved. Now shipped as transparent aggregations ("Your
  patterns"); optional later, pipe your own log to an LLM for plain-English summaries (needs the
  API — polish, not engine).

---

## Changelog

- **v16.5 (4 Jul 2026, data-processing only — no code shipped, no `index.html` change):**
  Processed the newly-landed ELVIS **Point Clouds/AHD** delivery for Sunshine Coast (953 tiles,
  8 survey/vintage groups spanning Noosa→Beachmere: Sunshine_Coast_2022/2014/2008_LGA,
  Noosa_2022/2015_LGA, MoretonBay_2018/2014/2009_LGA — the Moreton Bay groups are the southern
  end of the same custom-polygon order, at Aaron's confirmation, not stray data). **Major finding,
  supersedes the v16.2 "Point Clouds (AHD) stay a fallback" framing:** this delivery's sensors
  (Riegl VQ-780II, Optech Galaxy Prime) are topographic near-infrared LiDAR, not bathymetric
  green-laser — confirmed empirically, not just by spec sheet: every water-covered sample tile is
  100% classification-9 ("Water") with Z clustered in a ~2 m band matching tide state at flight
  time, not real seabed variation. **Point Clouds (AHD) cannot supply channel/gutter depth at all,
  structurally — it's not a coverage gap, it's the wrong sensor type for water.** What it *can*
  supply, reliably: classification-2 (dry ground) elevation for intertidal flats, sandbanks and
  rock platforms exposed at flight time — genuinely useful for a land-based-fishing app, but must
  never be labelled "depth" or "bathymetry" going forward; call it **intertidal/exposed ground
  elevation** everywhere (code comments, this roadmap, any future UI). Confirmed empirically, not
  just by policy: of 188,855 output points, **100% came out negative** (dries above LAT) under the
  depth sign convention — zero genuine submerged-at-LAT points exist in this dataset, which is
  exactly what "ground-classified, can't see through water" predicts.
  **Datum:** AHD confirmed via per-tile project metadata XML (nested two levels inside each tile's
  own zip — present for all 953 tiles, not just a folder-name convention), not via the LAS binary
  header (which never carries a vertical CRS in this delivery, checked directly with laspy on 8
  sample tiles across all vintages). One data-quality catch: the Noosa_2015_LGA tiles' embedded
  CRS VLR is simply wrong (declares geographic EPSG:4283 but stores projected UTM metres) —
  disregarded, treated as GDA94/MGA zone 56 by coordinate-magnitude convention instead. Horizontal
  datum differs by vintage (GDA94 pre-2022, GDA2020 for 2022) — each transformed through its own
  correct EPSG rather than one blanket assumption.
  **AHD→LAT conversion:** port-bucketed by latitude using the same "MSL as AHD proxy" convention
  already used for Brisbane Bar (1.32 m) in the DEA Intertidal spec — sourced from MSQ's official
  2024 Semidiurnal Tidal Planes table: Noosa Head 1.15 m (lat > −26.533°), Mooloolaba 1.00 m
  (−26.533° to −26.908°), Beachmere/Moreton Bay secondary 1.26 m (< −26.908°). **Correction:**
  Noosa Head is a **Standard Port** (own harmonic prediction) per the official table, not a
  Secondary Port as v16.3 stated.
  **Coverage delta (2022 vintage vs older):** the 2022 Sunshine Coast + Noosa layer covers 73.67 km²;
  older vintages add 44.36 km² the 2022 layer doesn't touch — but 53.15 km² of that is Moreton
  Bay/Beachmere, which has **no 2022 counterpart in this delivery at all** (not a genuine old-vs-new
  comparison). The real same-region delta (Sunshine Coast/Noosa 2008/2014/2015 vs 2022) is a small
  4.97 km² — confirms 2022 mostly supersedes the older SC/Noosa vintage coverage as expected, not
  mostly-overlap-with-nothing-gained.
  **Output:** `data/sunshine_coast_intertidal_ground_v1.csv` — 188,855 points (lat,lng,depth,
  metres below LAT, negative = dries), well over the app's 25,000-point import cap and **not
  pre-thinned** — left for the app's existing import-time auto-thin, or a coarser re-export on
  request. Raw LiDAR (953 tiles, ~128 GB compressed across 14 zips) stays in `data/raw/` per the
  disposable-once-converted policy; not committed. **Untouched this session (per Aaron):**
  Brisbane-River and Gold-Coast folders (mid-retrieval), and the 3 old rejected EOMAP zips sitting
  alongside the new data in the same `data/raw/Sunshine-Coast/` folder.
  **Next:** same pipeline (`data/raw/_inventory/process_tiles.py` + `export_csv.py`, both disposable
  scratch, not committed) needs re-running for Brisbane-River and Gold-Coast once those downloads
  land — same per-region AHD→LAT offset + AOI-clip work applies. Separately worth a decision: since
  Point Clouds (AHD) structurally cannot give real channel/gutter depth for Sunshine Coast, decide
  whether to keep pursuing genuine bathymetric (green-laser or sonar) data for that, or accept
  intertidal-only coverage the same way the roadmap's own "no depth layer" fallback already treats
  Moreton Bay's turbid water.

- **v16.6 (4 Jul 2026, planning-chat review — no code shipped):** Reviewed the v16.5 output.
  Point count, elevation range, sign convention, and coverage-delta math all check out — no
  errors found, the "100% negative = dries-only" empirical proof is a sound way to confirm the
  ground-only limitation rather than just asserting it. **Propagated the Noosa Head correction**
  from v16.5 into the item 15 living spec (was still calling it a Secondary Port in the "current
  status" text, not just the superseded changelog line — now consistent throughout: Noosa Head is
  a Standard Port, same as Mooloolaba, no offset math needed for either).
  **On the 188,855-point / 25,000-cap decision, flagged as open in v16.5:** don't default straight
  to a coarser re-export — that's real resolution loss (25m → roughly 70m grid to clear the cap
  comfortably: 188,855 ÷ 25,000 ≈ 7.55×, and cell count scales with the square of grid size, so
  √7.55 ≈ 2.75× → 25m × 2.75 ≈ 69m, rounded up to ~70–75m for margin — coarse enough to blur
  individual rock-platform/sandbank boundaries). **Cheaper first step: check whether the app's
  25,000-point cap applies per single CSV import or to the total merged `localStorage` array.**
  If per-import: split the 188,855-point CSV into ~8 files (~23,500 pts each, comfortably under
  cap) and import sequentially with MERGE — every point survives at full 25m resolution, and the
  cap-triggered auto-thin (whose actual algorithm — random vs spatial — is undocumented anywhere
  in this repo) never even fires, so its quality stops mattering. Only if the cap applies to the
  total store does a deliberate coarser re-export become the right move (better to control the
  thinning yourself than trust an unverified algorithm on a fishing-safety-adjacent dataset).
  **Also flagged, not urgent:** the ~128 GB of raw LiDAR sitting in `data/raw/` is confirmed
  disposable per the existing policy (Sunshine Coast CSV is validated) — safe to delete now and
  free the disk space; the 3 old rejected EOMAP zips sitting alongside the new data in the same
  `Sunshine-Coast/` folder are also safe to clear out, no further use.

- **v16.7 (4 Jul 2026, Claude Code build 2026.07.04a):** Shipped `storage_check.html` (repo root,
  flagged temporary) + a small `index.html` change to reach it. **Why the link was needed:** Guya
  now runs on Aaron's phone as an iOS home-screen web app — standalone mode has no URL bar, and
  each home-screen icon gets its own separate storage container, so the diagnostic page had to be
  reachable via an in-app, same-origin link (plain relative anchor, deliberately NO `target=_blank`
  — the adjacent official-zoning links do use `_blank`, an easy mistake avoided). **Page contents:**
  Section 0 — big YES/NO on `navigator.standalone` (+ display-mode fallback) so results can't be
  misread as coming from the wrong container; Section 1 — per-key `localStorage` usage + total;
  Section 2 — button-triggered fill-test (not auto-run, to avoid freezing the page mid-load), 1 MB
  chunks to a throwaway key, 30 MB cap, removed in a `finally` even on error; Section 3 —
  `navigator.storage.estimate()` usage/quota; a verdict line answering directly whether the 5.34 MB
  full-resolution Sunshine Coast import fits with ≥2× margin, stating remaining headroom either
  way (explicitly flagging that Brisbane River will need the same store later). **Build discipline:**
  Leaflet block byte-identical (md5 confirmed, 147,570 bytes before/after), both script blocks
  `node --check` clean, `zoneAt()` most-protective-wins intact, green-zone drag safeguard intact,
  build string bumped in both locations. **Mid-session scare, resolved as a non-issue:** the repo
  was found renamed to `AzmixLabs/Guya_Wamu`; flagged as a risk to the GitHub Pages URL and the
  phone's home-screen icon (icons re-added under a new URL get a fresh, empty container). **Aaron
  confirmed no rebuild was needed — the existing URL/icon kept working.** No migration occurred.

- **v16.8 (4 Jul 2026, planning + instructions rewrite — no code shipped):** Diagnosed an earlier
  phone-side data loss (spots + test photos missing from Aaron's iPhone) as most likely **iOS
  Safari's ~7-day script-writable-storage eviction** — confirmed NOT caused by the Claude Code
  workflow migration, which never touches the phone. **Standing fix adopted:** Guya lives on the
  phone as a **home-screen app** going forward (exempt from the eviction, gets its own storage
  container) — all phone-side imports and quota checks happen in that container, never a Safari
  tab. **version:2 export adopted as a standing backup habit** (confirmed to carry spots, photos,
  profiles, and imported depths together) — export after any import session or meaningful logging
  day, save to iCloud/Files. **Project instructions rewritten (rev B)** with three new sections —
  MODEL SELECTION (Sonnet default; Fable 5 for long autonomous runs/root-cause work, ~2× credit
  cost, past failures were process gaps not model quality), DEVICE DATA & BACKUPS (the per-device/
  per-container storage facts above), LONG-RUN DISCIPLINE (progress print + checkpoint + resume +
  smoke-test + real PID, required for any batch job over ~100 files or ~10 minutes) — plus
  corrected ELVIS facts (Point Clouds/AHD is the correct bucket; Bathymetry-3m is EOMAP
  satellite-derived and rejected; the ~15 GB cap auto-chunks rather than rejects; GA's result email
  can take hours, silence ≠ failure; QLD coastal Point Clouds are topo-NIR, class-2 ground only,
  never call the output "depth"/"bathymetry") and the Noosa Head Standard Port fix carried through
  into the instructions file itself, not just this roadmap.

- **v16.9 (4 Jul 2026, on-phone verification — no code shipped):** Ran `storage_check.html` on the
  phone in the home-screen container. **Section 0 confirmed standalone: YES** — numbers are real.
  **Section 1:** existing data confirmed intact — `woongarra_imported_v1` (262.6 KB, the Woongarra
  depth set) and `woongarra_spots_v1` (20.8 KB) both present; total usage 284.3 KB across 10 keys.
  Nothing was actually lost from this container. **Section 3** (`estimate()`) reported 1.23 MB used
  of a 39,321.6 MB quota — **flagged as the wrong number to decide on**, since that figure is
  IndexedDB-inclusive (photos, offline tiles) and vastly overstates the much stricter
  `localStorage`-specific ceiling. **Section 2 fill-test (the number that actually decided this):
  ~4.0 MB real remaining headroom.** Verdict: **full-resolution 8-chunk import (needs ≥10.68 MB
  margin) does NOT fit — single-pass auto-thinned import is the correct path.** Decision made:
  import the full 188,855-point CSV as one file; the app's own grid-thinning brings it under the
  25,000-point cap automatically (simulated result from v16.6-era code-read: ~18,875 points,
  ~547 KB). **Resolves the v16.6 open question on the thinning algorithm — confirmed SPATIAL grid-
  thinning, not random sampling** (Claude Code's direct code-read of the parse/thin loop). Working:
  188,855 ÷ 18,875 ≈ 10.01× fewer points → grid spacing scales with √10.01 ≈ 3.16× → 25 m × 3.16 ≈
  **~79 m effective resolution** post-thin, in the same ballpark as the v16.6 manual-regrid fallback
  estimate — the app is doing that job automatically at import time, no extra Claude Code
  processing needed.

- **v16.10 (4 Jul 2026, data-processing — no `index.html` change):** Sunshine Coast CSV imported to
  the phone (single pass, MERGE — preserving the existing Woongarra data confirmed in v16.9).
  `sunshine_coast_intertidal_ground_v1.csv` (the full, un-thinned 188,855-point file, 5.16 MB on
  disk) confirmed as the kept artefact per the existing disposable-raw/kept-CSV policy — to be
  committed to the repo (not `data/raw/`) if not already; `git status` check flagged as the way to
  confirm this rather than assume it. **Brisbane River LiDAR AOI now downloaded** by Aaron — **not
  yet processed**, pending confirmation of (1) correct ELVIS bucket (Point Clouds/AHD, not the
  EOMAP Bathymetry-3m bucket the first Sunshine Coast attempt mistakenly ordered from) and (2)
  correct AOI bounds (the tidal reach only, mouth→Mt Crosby Weir, not a wide Moreton-Bay-style box —
  the same mislabelling risk that hit the first Sunshine Coast draw). Remaining phone `localStorage`
  headroom after the thinned import: ~4.0 MB measured − 0.55 MB just used ≈ **~3.45 MB** — Brisbane
  River's output size needs checking against this before it's imported, likely also single-pass/
  auto-thinned rather than multi-chunk.

- **v16.11 (4 Jul 2026, planning — investigation queued, no code shipped):** Post-import visual
  check surfaced a geometric anomaly on the live map near/offshore of Caloundra — a wedge converging
  to a single point, plus a disconnected dashed-green quadrilateral sitting alone in open ocean.
  **Reproduced identically on both desktop and phone** — rules out a stale-view explanation. Renders
  under the app's existing **"Marine-park zones" toggle** (dashed-green matches established MNP
  no-take styling), which redirects the investigation to **`ZONES.features`, not the newly-imported
  depth CSV**. Two leading theories, **neither confirmed yet**: (a) a **partial-reprojection bug**
  on a specific feature — some vertices transformed correctly, others left in the wrong coordinate
  system, producing exactly this wedge-to-a-point shape (precedent already on file: `Noosa_2015_LGA`'s
  known-bad CRS VLR from v16.5); or (b) a **stray AOI/clip-boundary scratch polygon** — used to
  bound a data pull, then accidentally merged into `ZONES.features` instead of being discarded
  (simple rectangles/wedges are exactly what a clip boundary looks like, as opposed to a real
  legislated zone). **Also newly open: whether a 2b zoning/FHA wiring build was actually run and
  never reported back to this planning chat** — a `git log -p` check on whatever last touched
  `ZONES.features` is queued to settle this alongside the anomaly itself. **Reassessed as likely
  correct, not a bug:** the complex coastline-hugging zone shapes visible around Bribie Island/
  Redcliffe in the same wider screenshots — Moreton Bay Marine Park's documented northern boundary
  is Caloundra, so already-shipped 2a zone data would legitimately start appearing exactly there;
  Aaron simply hadn't scrolled this far north in the app before. Lower priority to verify than the
  offshore anomaly, but worth a spot-check against the known-good v14 Moreton zone set (same zid/
  name/zt) once the main investigation is underway. **Diagnostic-first Claude Code prompt issued —
  explicitly does NOT patch or re-export anything until it reports back which of the above this
  actually is.** **Brisbane River processing stays paused** behind this: if the root cause turns out
  to be a reprojection-pipeline bug rather than a one-off bad merge, it could recur identically on
  Brisbane River's zone/tide wiring, not just Sunshine Coast's.

- **v16.12 (5 Jul 2026, investigation + data-processing — no `index.html` change):**
  **Anomaly RESOLVED — real zones, no bug, nothing patched.** Both shapes are legislated
  Marine National Park (no-take) zones rendering correctly: the wedge is **MNP03 "Northern
  Wedge"** (125.41 km², 7 vertices) and the quadrilateral is **MNP08 "Deep Offshore Moreton
  Island"** (15.15 km², 5 vertices). Chain of custody verified unbroken: geometry byte-identical
  from the raw ArcGIS pull (`data/raw/moreton_zones_raw.geojson`, official `zone_type` "Marine
  National Park Zone" + legislated areas) → validated `moreton_zones_2019.geojson` → shipped
  `ZONES.features`. The schedule-style round coordinates (153.16667 = 153°10′E) are how offshore
  boundaries are legislated — straight lines between listed points — which is exactly why real
  offshore zones look like hand-drawn wedges, unlike coastline-hugging inshore zones. Neither
  theory (partial reprojection / stray AOI scratch) held. **Git-history check: NO 2b wiring
  build was ever run** — `ZONES.features` counts exactly 178 = 104 Great Sandy + 74 Moreton
  (v14 state); 2b wiring remains open. **Bribie/Redcliffe spot-check passed in full:** all 74
  Moreton features byte-identical to the validated 2019 set, zero property drift. Incidental
  note: `zid` values collide across parks (GUZ01 = both "Kolan"/Great Sandy and "Bulcock
  Beach"/Moreton) — harmless today (`zoneAt()` returns properties, no zid lookups), a trap only
  if anything keyed on bare `zid` gets built.
  **Brisbane River UNPAUSED and processed end-to-end** (verification report → Aaron's go-ahead
  → full run): 1,076 point-cloud tiles across 12 survey groups (682 Brisbane 2009/2014/2019,
  185 Ipswich/Bremer 2009/2014/2019/2023, 203 Redland 2009/2014/2022, 9 Pine River strays) from
  2 deliveries (~97 GB); `DATA_2047337.zip` (DEM bucket, 331 tiles) deleted unprocessed — wrong
  product type, zero point-cloud tiles inside. **Same sensor verdict as Sunshine Coast,
  empirically confirmed, with a new trap found and fixed:** topographic NIR, no channel
  coverage — but Brisbane's class-2 included a dense 180×175 m fused-survey/artifact patch at
  −15..−2 m AHD (CBD tile, ~4,180 pts/cell — far too dense for aerial LiDAR through water) that a
  naive export would have shipped as fake riverbed. Fixed by tightening the class-2 floor to
  **−1.6 m AHD** (just below Brisbane Bar LAT −1.32; genuine intertidal ground can't sit below
  LAT) — fix verified on that exact tile before the batch. **Datum:** AHD confirmed per-tile
  across all six vintages (2009→"AHD" … 2023→"AHD, AusGeoid2020"); horizontal split GDA94
  (pre-2022) / GDA2020 (2022–23) handled per-group. **AHD→LAT offsets carried per-group through
  the pipeline, not blanket:** Brisbane/Redland/Pine River → Brisbane Bar 1.32 m; Ipswich groups
  → Warrego Highway Bridge (Bremer) 1.21 m — both from MSQ 2024 Semidiurnal Tidal Planes; the
  0.11 m seam between the two at the Moggill junction is a noted soft precision limit. **AOI check:** zero tiles
  upstream of Mt Crosby Weir on the Brisbane arm; the 88 tiles west of the weir's easting are
  the tidal Bremer corridor (MSQ station exists), and the Redland/Cleveland block + Pine River
  strays were confirmed deliberate by Aaron — full AOI processed, no scope exclusions.
  **Output: `data/brisbane_river_intertidal_ground_v1.csv`** — 209,540 points (25 m grid,
  newest-vintage-wins dedup), 5.97 billion raw class-2 returns in, 19 all-water/zero-ground
  tiles, zero read errors. Range −6.32 to +0.19 m below LAT; 209,538 of 209,540 points are
  negative (dries above LAT) — the 2 at/below LAT are low-tide water's-edge returns, within
  tolerance. Coordinate range lon 152.737–153.324 / lat −27.643–−27.285 matches
  Bremer→Redland exactly. Over the 25k import cap — same single-pass auto-thin import route as
  Sunshine Coast (v16.10) applies. **Labelling discipline held: intertidal/exposed-ground
  elevation, never "depth"/"bathymetry", in filename, code, and comments.** Pipeline hardening
  vs the SC run: per-cell reservoir sampling capped the checkpoint at 52 MB (SC hit 9 GB).

  **Next (pre-v16.12 list, still-open items only):** Brisbane CSV phone import; 2b wiring
  build; Gold Coast stays parked.

- **v16.16 (5 Jul 2026, planning — depth-data-quality issue OPENED, diagnostic queued, no code
  shipped, nothing patched):** Aaron flagged real-world inaccuracy in the Sunshine Coast intertidal
  layer while reviewing the Bramble Bay / Brighton foreshore area (screenshots: a "West Banks"
  HPZ10 popup reading "dries ≈ 0.7 m ... data 23 m away" next to visibly patchy checkerboard
  coverage; a "Bramble Bay" MNP13 popup reading "dries ≈ 1.4 m ... data 49 m away" sitting right
  next to a "no survey data here" label a short distance away). **Two separate concerns raised,
  kept distinct:**
  (1) **"Half the coast is missing" — largely EXPECTED, not a bug, per already-recorded facts.**
  The Sunshine Coast/Moreton-tail CSV is topographic NIR, ground-only (v16.5) — it only captures
  elevation where dry ground was actually visible at flight time, thinned ~10× on import
  (~79 m effective grid spacing across the whole multi-hundred-km delivery, v16.9). Patchy,
  checkerboard, "no survey data here" gaps are the structurally expected shape of this data type,
  not evidence of a processing fault — this is also the direct answer to **"why didn't Moreton/
  Sunshine Coast get bathymetric data like Bargara?"**: Bargara/Woongarra's shading comes from
  genuine clear-water bathymetric LiDAR; Moreton Bay's water is too turbid for laser bathymetry to
  read at all (an ICESat-2 satellite-laser study found over half the bay too sediment-laden — see
  the "Home-water depth reality" note under item 15/14b, recorded 19 Jun 2026) — the topographic
  ground-only layer was always the fallback, not a downgrade of a bathymetric build that was
  skipped.
  (2) **A specific false "dries" reading ~600 m off Brighton foreshore — NOT yet explained,
  genuinely worth investigating.** Aaron's on-the-water knowledge is that this location does not
  dry at any tide — it's water, not a bank. A ground-classified LiDAR point reading "dries" at a
  location known to be permanently submerged is a different class of problem than sparse coverage:
  either a misclassified return (wave/glare/foam read as ground), a stale/superseded-vintage point
  that no longer reflects the seabed at that location, or a wrong per-point tidal offset. **The
  vintage-dedup hypothesis floated as a possible cause is RULED OUT** — Aaron confirmed the
  original Sunshine Coast pipeline used the same newest-vintage-wins dedup later applied to
  Brisbane River (v16.12), so a missing dedup step is not the explanation, and the same pattern is
  confirmed present in both datasets. **No diagnostic has been run yet on this specific issue** —
  queued for the next Claude Code session (Sonnet — inspection + a handful of point-checks, not a
  batch job): identify the actual source point(s) near Brighton, their originating tile/vintage,
  classification, and applied AHD→LAT offset, and check whether the render/interpolation logic
  (`nearestDepthPoint`/`idwDepthAt`) is assuming Woongarra-density point spacing over data that's
  now ~79 m apart. **Do not patch until this reports back** — same diagnostic-first discipline as
  the v16.11→v16.12 anomaly investigation.

- **v16.15 (5 Jul 2026, git safety-net commit, done manually via shell — outside a Claude Code
  session, no code shipped):** Aaron ran `git add`/`commit`/`push` directly (commit `581e88f`)
  to close an exposure separate from the v16.12 anomaly work: the Sunshine Coast intertidal CSV
  and several 2a source files had never been added to git, sitting disk-only with zero redundancy.
  **Newly tracked:** the two 2b zoning/FHA GeoJSONs (`great_sandy_zones_2026.geojson`,
  `fha_se_qld_2026.geojson`), the Sunshine Coast intertidal-ground CSV, and five previously-
  untracked root files (`brisbane_bar_tides_2026.json`, `build_mb.py`, `validate_moreton_zones.py`,
  `moreton_zones_2019.geojson`, `fishhabitat_bundaberg_region.geojson`) — 8 files, 189,360
  insertions. **Confirmed safe first:** `data/raw/` is properly gitignored, so the commit picked up
  only the small baked outputs, not the 128 GB+ of raw LiDAR sitting alongside them. **Deliberately
  left out:** `GUYA_ROADMAP.md` (roadmap sync stays a separate manual habit) and
  `guya_species_qld_v3.md` (by design — project knowledge only, never the repo). **This commit
  predates and is separate from Claude Code's own `66331d8`** (Brisbane CSV + this roadmap's
  v16.12 entry) — the two commits are not duplicates, both are real and both are on `main`. **Two
  things flagged, still open (see Cleanup):** the repo-rename notice (`Guya` → `Guya_Wamu`) fired
  again during this push, the second occurrence without a `git remote -v` check ever confirming the
  actual local remote (only the URL/icon behaviour was checked, twice); and
  `fishhabitat_bundaberg_region.geojson` is unrecorded anywhere in this roadmap or the project
  brief — origin and purpose unconfirmed.

- **v16.17 (5 Jul 2026, diagnostic only — no code shipped, no patch applied):** Diagnosed the
  false "dries" reading opened in v16.16 near Brighton foreshore (~600 m offshore, Bramble Bay).
  **Verdict: misclassification, confirmed at the raw-point level — not an offset bug, not a
  render/interpolation bug.** Premise correction first: the flagged point is **not** in the
  Sunshine Coast CSV — that file's coverage ends at lat −27.077, ~25 km north of Brighton. Every
  point near the target is from `brisbane_river_intertidal_ground_v1.csv` (the Pine River-area
  tiles from the v16.12 run); the vintage-dedup rule-out from v16.16 carries over unchanged, and
  the Sunshine Coast offset-bucket question turned out to be moot for this specific point.
  **Source:** 18 points within 150 m of the target, all in a tight −0.83..−0.91 m band, sourced
  from `Brisbane_2019_Prj`. **Classification (raw zips checked directly):** 93,987 class-2
  "ground" points at −0.68..−0.15 m AHD sit at ~2,238 pts/cell — the same fused/misclassified
  signature as the v16.12 CBD artifact (4,180 pts/cell), far too dense for real aerial-NIR ground
  returns 600 m out in open, turbid Bramble Bay. The giveaway: 23,354 class-9 "water" points sit
  interleaved in the same bbox at the same elevation band (−0.73..−0.12 m, mean −0.35). Class-2
  and class-9 here are the same physical surface — the water surface at flight time — with most
  of the swath mislabelled "ground." **Why the v16.12 −1.6 m floor didn't catch it:** that floor
  kills fake riverbed *below* LAT; this is fake dry bank sitting *inside* the legitimate
  intertidal band, indistinguishable by elevation alone. **Offset: correctly applied, not the
  cause.** The Brisbane pipeline carries offsets per survey group, not by latitude bucket — this
  cell correctly got Brisbane Bar 1.32 m via `Brisbane_2019_Prj` (the correct port for Bramble
  Bay). Arithmetic confirmed: cell median z ≈ −0.45 → −(−0.45) − 1.32 = −0.87, matching the CSV
  value exactly. The Sunshine Coast latitude-bucket offset function never touched this point.
  **Render/interpolation: working as designed, not the cause.** `idwDepthAt()` found the artifact
  sheet at 99 m and IDW-blended values that are all ≈ −0.85 anyway; the popup's "data 99 m away"
  disclosure is honest. Interpolation is faithfully reporting bad source data, not reaching
  wrongly. **Secondary UI finding, not patched:** the "dries" popup branch omits the "low
  confidence" tag the depth-popup branch already applies past 80 m — a dries reading at 99 m
  currently reads more confidently than an equivalent depth reading would. **Cluster check —
  systemic across Bramble Bay open water, not one bad point:** the same pattern confirmed off
  Sandgate (90/90 points), Shorncliffe pier (39/39), and partially at Pine River mouth outer
  (mixed real flat + artifact). **Consequence:** the Brisbane River CSV's readings seaward of the
  Brighton–Shorncliffe foreshore are untrustworthy as shipped; a masked re-export is needed before
  import. Scope of the fault beyond this one survey group/bay was unknown at this point — a full
  audit was commissioned next (v16.18). Nothing patched.

- **v16.18 (5 Jul 2026, diagnostic only — no code shipped, no patch applied):** Full-scope audit
  of the v16.17 misclassification fault across **both** deliveries. **All 1,375 tiles checked,
  zero read errors.** Confirmed the fault is **systemic**, not confined to `Brisbane_2019_Prj`/
  Bramble Bay — it recurs in every post-2009 vintage in both deliveries: Brisbane 2014 (38/222
  tiles, 2.28 km²) and 2019 (45/240, 5.45 km²), Redland 2014 (22/59, 1.18 km²) and 2022 (31/77,
  1.83 km²), Pine River strays (1/9, 0.03 km²), and — new — the **Sunshine Coast delivery's
  MoretonBay 2014 (33/99, 1.92 km²) and 2018 (19/102, 0.77 km²) subsets**. **~13.6 km² total at
  artifact scale across 192 tiles** (figures reconciled against the per-group table). **The
  Sunshine Coast CSV — already imported to Aaron's phone via MERGE (v16.10) — is confirmed also
  affected**, not just Brisbane River. Example cross-check coordinates surfaced: Brisbane River
  mouth flats (−27.359, 153.143; −27.473, 153.198), Redland bayside (−27.459, 153.235; −27.514,
  153.268), Deception Bay/Beachmere (−27.041, 153.119), Golden Beach/Pumicestone (−26.986,
  153.068), Currimundi (−26.639, 153.079). Densities run 1,500–14,800 pts/cell with class-2/
  class-9 medians within centimetres — same fingerprint as Brighton throughout.
  **Major gap, not yet closed:** `Sunshine_Coast_2022/2014/2008` and `Noosa_2022/2015` — the
  **dominant vintage covering most of the Sunshine Coast delivery's actual area** (~666 tiles) —
  were only spot-sampled at 12 tiles, hitting 3/12 (25%). This is not a clean result for the bulk
  of the SC CSV; a full audit is required before the SC fix can be considered scoped.
  **Qualifications:** (1) **Ipswich/Bremer (185 tiles) is genuinely clean** — 0 artifact-scale,
  consistent with a narrow river corridor having no broad open-water sheet to mislabel. (2) **370
  tiles (Brisbane_2009, Redland_2009, SC MoretonBay_2009) are untestable by class-9-adjacency, not
  confirmed clean** — pre-2009-era classifiers carried no water class at all, so there's no
  co-location signal to catch; reported as unverified. A density-only secondary test (the same
  method that originally caught the v16.12 CBD artifact) can still run on these. (3) **Not every
  flagged cell is necessarily wrong** — artifact-scale areas coincide with locations that also
  have genuine drying flats (Redland bayside, Pine mouth, Beachmere, Pumicestone); water pooled on
  a real flat legitimately co-locates with exposed ground at the same elevation. Geometry alone
  can't adjudicate truth on a tidal flat — a re-export fix must **drop** flagged points rather
  than attempt to reclassify them, per the app's existing no-data-beats-wrong-data discipline
  (accepted tradeoff: some real flat coverage lost alongside the artifact).
  **Consequence:** both CSVs need a masked re-export before being trusted. Brisbane River import
  stays held. **Sunshine Coast's phone data needs correcting too** — the fix will require a
  **REPLACE** of the SC-region import, not a MERGE (MERGE can't remove already-present bad
  points) — a first for this app's import history. Full per-tile results in
  `data/raw/_inventory/audit_results.json` (gitignored scratch), held for the fix decision.
  Nothing patched, masked, or re-exported.

- **v16.19 (5 Jul 2026, build 2026.07.05a — 2b wiring: zoning/FHA/tides, depth untouched):**
  Shipped the Sunshine Coast zoning/FHA/tides wiring build, scoped explicitly separate from the
  v16.16–v16.18 depth-data-quality issue (no CSV import/export touched, `woongarra_imported_v1`
  untouched, Brisbane River import stays held pending that fix).
  **Zone freshness check (confirmation, not a merge):** `data/great_sandy_zones_2026.geojson`
  (104 features) vs the Great-Sandy-origin subset already in `ZONES.features` — zid/name sets
  identical, zt/notake identical for all 104, zero property drift. Geometry differs in vertex
  count only (shipped is the already-simplified ~20 m version; the new pull is higher-resolution
  raw) — bounding boxes match, same real zones. **No changes made**, exactly the expected result.
  **FHA merge:** `data/fha_se_qld_2026.geojson` has 35 features but **8 collide exactly** with the
  already-shipped Woongarra `FHA` store (same plan+name+mgmt key — Baffle Creek, Beelbi, Burrum,
  Elliott River, Kinkuna, Kolan River — geometry differs by the same simplification-vs-raw
  pattern as the zones). Merged only the **27 genuinely new** features (additive, existing 8
  left untouched) — `FHA` now holds 35 total, including Maroochy (FHA-008, both mgmt variants)
  and Noosa River Rev.2 (FHA-051, both variants).
  **Mooloolaba tides — sourced and parsed from scratch, not copied from anywhere:** downloaded
  the official MSQ *Queensland Tide Tables 2026* (193 pages, all QLD standard ports) via
  WebFetch (direct `curl` was blocked by MSQ's anti-scraping page), located Mooloolaba's 3 pages
  (Jan–Apr/May–Aug/Sep–Dec), and column-aware parsed using `pdfplumber` word-level x-coordinates
  — necessary because the table packs **8 sub-columns per page** (4 months × 2 half-month
  blocks) with **3 or 4 tide events per day**, exactly the multi-column trap that caused the
  Brisbane Bar Jan-1 misread this convention was named after. Validated before trusting it:
  353/353 weekday cross-checks matched (remaining 12 rows had no weekday marker to check, not
  assumed correct), all 365 dates present with none missing/duplicated, every day within the
  valid 3–4 event range, strictly increasing times within each day, H/L assigned by continuous
  alternation (physically a semidiurnal tide can't have two highs in a row) with **zero**
  alternation violations across 1,410 events. **External cross-check: parsed max height 2.22 m
  vs the independently-published Mooloolaba HAT of 2.21 m** (MSQ Semidiurnal Tidal Planes,
  sourced separately in v16.5) — near-exact match, strong evidence the parse is sound.
  `MOOLOOLABA_TIDES_2026` embedded in the same shape as `BURNETT_TIDES_2026`/
  `BRISBANE_TIDES_2026`, added to `PORTS`. **Correction propagated:** Mooloolaba and Noosa Head
  are both Standard Ports (own harmonic prediction) per the official table — no offset math for
  either; Noosa Head itself stays a deliberate fast-follow, not part of this build.
  **Outside-zoning message fixed** (`zoneTag()`, was the only place any "no zone match" text
  existed at all): now reads *"outside marine-park zoning — general fisheries rules + FHAs
  still apply, confirm via Qld Fishing 2.0"* instead of the old bare *"outside mapped zones —
  verify yourself"* — the old text never mentioned FHAs or the general-rules-still-apply point,
  a real safety-layer gap now closed. **Note:** FHA data is merged but still not rendered as a
  map layer or point-in-polygon lookup (same as the Woongarra FHA entries before it) — this
  build only fixed the static disclaimer text, not a location-aware FHA check.
  **Validation:** both script blocks `node --check` clean; Leaflet block byte-identical (md5
  `cab0fd0f0d88d5ae473c6a6812dba859`, unchanged since v16.7); `zoneAt()` still most-protective
  (`ORDER=["MNP","CPZ","HPZ","GUZ"]`, unmodified) — not touched by any of this build's edits, so
  no regression risk; green-zone drag safeguard (`nz.notake` alert on dragend) intact.
  `nearestPort()` live-tested in Node against the actual embedded data: Woongarra/Bargara →
  Burnett Heads, Redcliffe → Brisbane Bar (no regression), Mooloolaba/Maroochydore/Noosa Heads
  → Mooloolaba — all 5 pass. **Also confirmed in passing (housekeeping, no action taken):**
  `git remote -v` still points at `github.com/AzmixLabs/Guya.git` — unchanged despite the
  "repository moved to Guya_Wamu" notice seen on every push since v16.7; and
  `fishhabitat_bundaberg_region.geojson` (root, origin previously unrecorded) is confirmed
  byte-identical to the currently-shipped Woongarra `FHA` store — it's that store's raw source
  file, not a mystery file.
  **Next:** the depth-data-quality fix (v16.16–v16.18) is the real open item — masked re-export
  of both CSVs, REPLACE (not MERGE) for Sunshine Coast's phone data, Brisbane River import stays
  held until then. Separately: an actual FHA rendering layer (polygon + popup, like `zoneLayer`)
  is still a future build, not done here. Noosa Head tide port remains a ready-whenever
  fast-follow. Gold Coast stays parked.

- **v16.20 (5 Jul 2026, planning-chat correction — no code shipped, no `index.html` change):**
  Caught and fixed a staleness bug in this file itself: the "Next session — priority order" list
  near the top still showed items 6 (`git remote -v` check), 7 (`fishhabitat_bundaberg_region.geojson`
  origin), and 8 (2b wiring build) as open, even though the v16.19 build resolved or shipped all
  three the same day. Left uncorrected, the next planning or build session would have re-checked
  settled items off a stale list — the same class of drift this file's own "roadmap discipline"
  principle exists to prevent. **Fixed:** items 6–8 now marked done/resolved/shipped with a
  one-line pointer to v16.19. **Split out a real open item that v16.19 only surfaced in passing:**
  the git remote check (item 6) confirms the *local* remote is unchanged, but doesn't resolve
  *whether GitHub renamed the repo server-side* — that's a decision Aaron still needs to make
  (check github.com directly; align remote + Pages URL + phone home-screen icon deliberately if
  so, rather than relying on an unverified redirect indefinitely). **Added new item 9:** FHA data
  (35 features) is merged into the store but has no rendered map layer or point-in-polygon
  lookup — noted as a footnote in v16.19's own entry but not previously billed as its own backlog
  line; now it is. **Renumbered:** Noosa Head fast-follow → item 10, Gold Coast → item 11.
  **No architecture, code, or data changed** — this entry only corrects the roadmap's own
  internal consistency.

- **v16.21 (10 Jul 2026, diagnostic only — no code shipped, no patch applied):** Closed the
  v16.18 audit gap (priority item 1). **907 tiles audited this pass — 544 Group A (SC/Noosa
  post-2009 vintages; 556 total incl. the 12 v16.18 spot samples — count corrected from "652" in
  v16.22) + 363 unique Group B (2009 vintages; 7 of the 370 manifest entries were
  duplicate tile names across overlapping delivery zips, as were 110 within Group A) — zero read
  errors**, checkpoint/resume exercised for real mid-run. Group A method/thresholds identical to
  v16.17–v16.18 (25 m cells, ≥20 class-9 + ≥100 class-2 pts, medians within 0.5 m; "artifact
  scale" = ≥50 suspect cells — the filter that exactly reproduces v16.18's 192-tile/13.61 km²
  figure). Incidental method note: `SunshineCoast_2008_LGA` carries class 9 after all, so it was
  audited by the full adjacency method, not a fallback. **Group A — the dominant SC vintages are
  heavily affected:** 435/556 tiles raw-HIT (incl. the 12 v16.18 spot samples), **113 at artifact
  scale / 6.85 km²** (Sunshine_Coast_2022 52 tiles/3.16 km², SunshineCoast_2014 39/2.54,
  SunshineCoast_2008 12/0.49, Noosa_2022 6/0.42, Noosa_2015 4/0.24), densities to 27,898 pts/cell,
  same class-2/class-9 co-location fingerprint as Brighton throughout — worst around
  Maroochydore/Mudjimba, Coolum–Peregian, and the Caloundra/Pumicestone shore. **Group B
  (density-only secondary test):** calibrated on 9 sample tiles first — 2009 deliveries carry
  classes {2,6,10} (no class 9, confirmed structurally untestable by adjacency); legitimate
  low-band ground tops out ~1,064 pts/cell, so the flag threshold was set at ≥1,500 pts/cell (the
  confirmed v16.17–v16.18 artifact floor) at cell-median z ≤ +1.5 m AHD. Result: 53/363 tiles
  carry isolated suspect cells (max 31 cells/tile, max density 2,227) but **zero tiles reach
  artifact scale — the 2009 vintages are effectively clean**; the broad water-sheet artifact
  simply does not occur pre-2009, consistent with a post-2009 classifier fault. **Headline
  revision: ~13.6 km² / 192 tiles (v16.18) → ~20.3 km² / 302 tiles at artifact scale** (+110
  tiles / +6.69 km², all from the SC/Noosa groups). Per-tile results appended to
  `data/raw/_inventory/audit_results.json` (append-only; new entries tagged `method`/`group`;
  pre-merge backup `audit_results.pre_gap.bak.json`; the existing 1,375 entries verified
  byte-identical after merge). Tooling: `_inventory/audit_gap.py` + `merge_gap.py` (gitignored
  scratch, kept for the item-2 mask design). Item 2 (drop-mask re-export) is now fully scoped and
  unblocked. Nothing patched, masked, dropped, or re-exported; no raw tiles deleted.

- **v16.22 (10 Jul 2026, documentation-only — no code shipped, no data or audit changes):**
  Correction pass over the v16.21 text; nothing re-audited, nothing patched. **(1) Brisbane River
  import status corrected — it was stale/wrong:** the roadmap still described the Brisbane River
  CSV (`data/brisbane_river_intertidal_ground_v1.csv`) as "held" pending the drop-mask fix, with
  its eventual phone import billed as a fresh first import. Aaron has confirmed directly that the
  CSV was already imported to his phone via MERGE — the same route as the Sunshine Coast import.
  (That update was meant to land as its own changelog entry but was superseded by the v16.21
  audit-gap session before being committed.) Now reflected in the banner and priority item 4:
  BOTH regions' phone data carry the classifier-fault artifact and BOTH require a REPLACE
  re-import — MERGE cannot remove points already present. **(2) Group A tile-count typo fixed:**
  priority item 1 and the v16.21 changelog entry said "652" Group A tiles — a leftover
  pre-deduplication manifest count from the audit session. Verified directly against
  `data/raw/_inventory/audit_results.json`: **556 total Group A entries** (Sunshine_Coast_2022
  159 + SunshineCoast_2014 164 + SunshineCoast_2008 167 + Noosa_2022 38 + Noosa_2015 28), of
  which 544 were newly audited in v16.21 and 12 were the v16.18 spot sample; 544 + 363 Group B =
  907, matching the "907 tiles audited this pass" figure already in the file. The per-survey
  table and all km²/artifact-scale figures were already correct — only the stated Group A total
  was wrong.

- **v16.23 (11 Jul 2026, design phase + metadata fix — no code shipped, NOTHING MASKED, DROPPED,
  OR RE-EXPORTED — diagnosis and scoping only):** Drop-mask re-export design phase (item 2)
  completed as a read-only analysis over `audit_results.json` (Sonnet). **Duplicate-entry fix:**
  the file carried 380 duplicate tile names — 366 are the legitimate two-method record on
  2009-vintage tiles (class-9-adjacency `clean_by_absence` + the real `density_only` verdict,
  left untouched) — but 14 tiles had two byte-identical HIT entries, inherited from overlapping
  delivery zips in the original 1,375-entry audit (all 14 in the MoretonBay_2014/Moreton_Bay_2018
  Pumicestone block). Six of those sat at artifact scale and double-counted the headline.
  Deduplicated (backup `audit_results.pre_dedupe.bak.json`, same pattern as the merge backup);
  **corrected headline: 296 tiles / 19.98 km² at artifact scale** (was reported 302 / 20.30 in
  v16.21/v16.22). No verdicts changed, no re-scoring — exact-duplicate removal only.
  **Scope options costed (post-dedupe):** Option A — mask flagged cells only in artifact-scale
  tiles: 296 tiles / 31,971 cells / 19.98 km². Option B — mask every flagged cell everywhere:
  1,237 tiles / 48,537 cells / 30.34 km² (+10.36 km² over A). **Hybrid — RECOMMENDED, pending
  Aaron's final sign-off:** cell-level masking on post-2009 vintages only, where class-9
  adjacency independently confirms the fault: **1,184 tiles / 48,194 cells / 30.12 km²**, with
  the three 2009-vintage groups excluded (53 flagged tiles / 343 cells / 0.21 km² left unmasked,
  flagged as unconfirmed). **Control-location check:** every one of the seven v16.18 control
  locations has at least one vintage clearing Option A's threshold, but four have vintages that
  would stay UNMASKED under Option A — most damningly **Brighton itself, the fault's origin site
  (31/32 flagged cells in Brisbane_2014/2019, both under the 50-cell line)**, plus
  Shorncliffe (2019 vintage), Golden Beach/Pumicestone (MoretonBay_2014 + SC_2008), and
  Currimundi (SC_2014 + SC_2008). Option A would therefore fail item 3's validation bar as
  written; Option B and the hybrid pass it. **Group B evidence-strength finding:** the 53 flagged
  2009-vintage tiles are a weak signal — median max-density 1,615 pts/cell vs 7,036 for confirmed
  artifact tiles, clustered in a tight band right at the 1,500 calibration floor, median 3
  cells/tile, and structurally no class-9 co-location check is possible on these vintages. At
  least as consistent with dense real low-band ground (ramps, revetments) as with the fault at
  small scale — hence the hybrid's exclusion of them as unconfirmed rather than either masked or
  cleared. The ≥50-cell "artifact scale" line was always a reporting threshold for delivery-wide
  scope, not a per-cell trust decision — the masking scope is therefore a fresh decision, not an
  inheritance. **Build starts only after Aaron picks A / B / hybrid.**

- **v16.24.1 (11 Jul 2026, INCIDENT — planning-chat log, no code shipped, no data changed):**
  Aaron attempted item 4 (REPLACE import of `brisbane_river_intertidal_ground_v2.csv`, then
  `sunshine_coast_intertidal_ground_v2.csv`) on his phone, home-screen app. After restarting:
  no depths visible for either region, AND Bargara/Woongarra depths — a separate, pre-existing
  dataset not part of this import — were also gone. This is the key diagnostic signal: nothing
  in this session's work should have touched Bargara, so its disappearance points at the
  "Imported depths" store being a single unscoped bucket across all regions rather than
  partitioned per-region, meaning REPLACE cleared everything it touches, not just the targeted
  region's slice. A follow-up MERGE of the same v2 files also produced no visible depths —
  cause unconfirmed (could be a v2-file-specific parsing issue, or leftover bad state from the
  failed REPLACE; not yet distinguished). Aaron restored his pre-import `version:2` backup —
  spots confirmed recovered; Bargara/Woongarra recovery unconfirmed as of this entry. **No
  code or data changed this session** — this is an incident log plus a block on further
  action. **v16.24's build output (the v2 CSVs) is not implicated** — the failure is in the
  phone-side import mechanism, not the data produced by the build. Item 4 marked BLOCKED.
  Next job: a read-only Claude Code investigation of the import/REPLACE/MERGE code path in
  `index.html`, plus a structural check of the v2 CSVs against v1 (which imported successfully
  at a comparable scale previously) — report and fix proposal only, no phone-side retry until
  that lands.

- **v16.24.2 (12 Jul 2026, build 2026.07.06a — `index.html` code change, item 4 UNBLOCKED):**
  Fix shipped for the v16.24.1 incident, following the read-only investigation's confirmed root
  cause: every region's imported depths lived in one flat array under one localStorage key
  (`woongarra_imported_v1`), no per-point region tag; REPLACE unconditionally set that whole
  array to `[]` before writing the new file. Sequential REPLACE of two regional files can only
  ever leave the last file's data — this explains both Bargara/Woongarra's loss (first REPLACE)
  and Brisbane River's loss (second REPLACE wiped it). The SC v2 file/follow-up MERGEs producing
  nothing remains a separate, unconfirmed device-side question (see the investigation's report)
  — not something a code fix can resolve retroactively, and orthogonal to this session's change.
  **Shipped:**
  — **Dataset-scoped storage** (`woongarra_imported_v2`): `{datasets:{region:{region,label,
  importedAt,points}}}`, one slot per region. The old flat `woongarra_imported_v1` array is
  migrated in as a tagged `legacy_unknown` dataset on first load if no v2 store exists yet —
  never dropped, never silently merged into a region it wasn't confirmed to belong to (per the
  investigation, the 55,660-pt legacy blob is presumed to span Bargara/Brisbane River/Sunshine
  Coast from the backup analysis, but that's unverified by code, hence the "legacy/unknown" tag
  rather than guessing a split). The legacy v1 key itself is left in place, untouched.
  — **REPLACE/MERGE scoped to one region.** A region selector (Bargara/Woongarra, Brisbane
  River, Sunshine Coast, or a free-text "Other…") targets every import; REPLACE now clears only
  `datasets[region]`, never the whole store.
  — **Blind `confirm()` OK=replace/Cancel=merge dialog retired.** Replaced with two explicit,
  always-visible buttons ("Replace this region" / "Merge into this region") plus a persistent
  per-region dataset list (label, point count, imported-date, individual ✕ remove) in the panel
  — Aaron can see and control every region's state without a destructive dialog making the call.
  — **Backup restore is now a true full replace** of the imported-depths store (previously
  silently merge-only, confirmed by code-read in the investigation — a restore could add backup
  points but never remove ones already in memory). Restoring a `datasets`-shaped backup replaces
  the whole store with exactly its contents; restoring an older flat-`imported`-shaped backup
  wraps it as one dataset and still fully replaces, never merges.
  — **Verified writes.** Every `localStorage.setItem` for imported data is followed by a
  read-back + point-count check; on mismatch a **persistent in-panel error** (`#imp-save-err`,
  red-bordered, stays until the next successful save) fires instead of a transient `alert()`.
  This closes both previously-silent `catch(e){}` blocks the investigation found (the metadata
  write, and — the important one — the backup-restore path's `setItem`).
  — **One-step rollback.** Every REPLACE, per-region remove, "Clear ALL regions," and backup
  restore snapshots the pre-action store to `woongarra_imported_rollback_v1` first; an "↩ Undo
  last replace/remove" button appears whenever a snapshot exists and restores it verified.
  — **Untouched per explicit scope:** the 25,000-point grid-bucket auto-thin logic (proven
  correct on the real v2 files during the investigation); `depthSamples()` and the entire
  shading/tap-read/IDW pipeline (that's the separate, independently-diagnosed zone-coverage gap
  — not a storage issue, not addressed by this fix); the inlined Leaflet block (confirmed
  byte-identical to HEAD); `zoneAt()` and the pins-lock drag safeguard (confirmed intact).
  **Verification:** both script blocks pass `node --check`. Build bumped 2026.07.05a →
  **2026.07.06a**.
  **On-phone test plan before the real re-import (mandatory, small-file first):**
  1. Build a synthetic CSV of a few dozen `lat,lng,depth` points. REPLACE it into a test region
     (e.g. "Other…" tagged `smoketest`) — confirm the panel's dataset list shows exactly that
     count, and that Bargara/Brisbane River/Sunshine Coast counts in the list are all unchanged.
  2. MERGE a second small synthetic file into the same test region — confirm the count increases
     by the new file's unique-point count only, other regions still untouched.
  3. Remove the test region's dataset via its ✕ button; confirm it disappears from the list and
     the total count drops accordingly.
  4. Export a `version:2` backup, then restore it immediately — confirm the total imported-point
     count is unchanged (restore must not inflate it) and no persistent error appears in the
     panel.
  5. Only after 1–4 all pass: re-attempt the real REPLACE of `brisbane_river_intertidal_ground_v2.csv`
     into "Brisbane River," then `sunshine_coast_intertidal_ground_v2.csv` into "Sunshine Coast" —
     both still genuine REPLACE operations (v1 data is on-phone and must go), but now scoped so
     neither touches the other region or Bargara/Woongarra. Confirm the dataset list shows the
     expected ~20,791 / ~17,924-point-scale counts (per the v2 files' actual auto-thinned size)
     and no persistent error banner.
  **Not addressed here — separate open item:** depth shading/tap-read still renders nothing for
  imported points north of Caloundra (confirmed zone-polygon-coverage gap, independently
  diagnosed, fix proposed but not built). Re-importing under this fix does not resolve that.

- **v16.25 (12 Jul 2026, build 2026.07.07a — `index.html` code change, SEPARATE from v16.24.2,
  do not conflate):** Fixed the shading/tap-read coverage gap north of Caloundra, following the
  earlier independent read-only investigation. **Root cause, confirmed:** the cosmetic paint/read
  mask (explicitly separate from `zoneAt()`/legal-zone logic per its own long-standing code
  comment) required either a legislated marine-park zone polygon OR a nearby sample with a
  genuine underwater sounding (depth ≥ 0, i.e. NOT "dries"). Moreton Bay MP zoning stops at
  Caloundra, so Mooloolaba/Maroochydore/Coolum/Peregian/Noosa have no zone polygon at all; and
  this dataset's imported points are almost entirely dries (negative depth — LiDAR ground returns
  by construction). With neither admission path available, shading and tap-read produced nothing
  for any point along that whole stretch, at any array size — structural, not scale-related, and
  predating the recent storage incident entirely (would have failed identically on the original
  v1 Sunshine Coast import too). **Fix:** dropped the depth-sign requirement from the
  distance-bounded fallback — being within the existing radius (R1=120 m for shading/tap-read,
  80 m for `findDeepest()`) of ANY real sample, dries or sounding, is now sufficient evidence of
  real coastal/intertidal ground. The distance bound alone was already doing the real work of
  excluding unrelated dry land; the sign check added a gap without adding real protection.
  **Scope widened beyond the original investigation's two named sites:** `buildShade()`'s maskA
  and the tap-to-read click handler were the two call sites the investigation examined, but the
  identical duplicated gate (same condition, same comment lineage — "mirrors the depth-shading
  paint rule") also existed in three more places: `findDeepest()` ("Deepest within 100 m"),
  `buildAutoContours()`, and the desktop mouse-hover readout. Fixing only the two named sites
  would have left these three silently broken at Coolum while the other two worked — a worse,
  inconsistent state than the original uniform failure. All five were fixed identically, restoring
  the consistency the five already had with each other before this change. **Verification:**
  confirmed against the real dataset (not simulated) — the reported Coolum point (−26.554413,
  153.095149, depth −5.63) is 0 m from itself in `sunshine_coast_intertidal_ground_v2.csv`, so it
  now clears the distance gate; a control point 8.7 km inland (clearly dry hinterland, no nearby
  survey coverage) is correctly still excluded by distance alone, confirming the sign check was
  never load-bearing for that protection. Both script blocks pass `node --check`; the inlined
  Leaflet block reconfirmed byte-identical to HEAD. `zoneAt()` untouched (single unrelated
  function, confirmed by direct read) — the legal-zone-call invariant is unaffected. Build bumped
  2026.07.06a → **2026.07.07a**. **Not addressed here:** the storage-scoping fix (v16.24.2) and
  the on-phone test plan it specifies remain the gating step before any real CSV re-import; this
  rendering fix takes effect on whatever data is already/eventually on-device, no import required
  to see it working, but should be spot-checked in the same phone session as the v16.24.2 test
  plan rather than treated as its own separate on-phone verification pass.

- **v16.33 (12 Jul 2026, data-processing build — no `index.html` change, no import performed):**
  **Maroochy/Noosa bathymetry pipeline SHIPPED**: `data/raw/_inventory/bathy_pipeline.py`
  processed the QSpatial "Bathymetric LiDAR for Sunshine Coast" delivery
  (`DP_LIDAR_SunshineCoast.zip`, Fugro LADS Mk 3 green-laser survey, Oct–Nov 2011, delivered
  Feb 2013) into `data/maroochy_noosa_bathy_v1.csv` — **946,877 rows** (25 m grid cells, median
  z per cell, same lat,lng,depth schema and sign convention as the intertidal CSVs). Smoke test
  (20 spread tiles) then full run (756 tiles, checkpointed/resumable; one restart after a
  numpy-int64 JSON-serialisation crash at the first checkpoint — checkpointing is exactly the
  path smoke mode skips, noted for future smoke designs). **Input: 28.78 M points (27.81 M
  class 13 + 0.97 M class 15), 29,735 points dropped inside the Wetland Sanctuary defect zone,
  0 outside the Area-A extent. Output depth range −1.15…+42.48 m LAT; 1.0% dries (negative) /
  99.0% submerged — decisively unlike the 100%-negative intertidal exports, sanity gate passed**
  (bulk of cells 20–30 m, real tail to 42 m matching the QA report's ~40 m reach).
  **Rules baked in, from the v16.29–v16.32 read-only investigations (recorded here — those
  sessions made no roadmap updates):** (1) depth points ONLY from
  `Classified/Offshore_AHD_tidal_data` classes 13+15 — the Fugro legend (found in the bundled
  Report of Survey) is NON-ASPRS: 13=validated seabed, 14=non-seabed (documented but absent from
  the delivery), 15=20 m subset of 13; onshore 1=non-ground, 2=ground. Onshore folders are never
  read: 23 onshore tiles around the Maroochy Wetland Sanctuary carry a confirmed
  ground-classified-as-seabed defect (QA report FAIL, located empirically). (2) Belt-and-braces
  point-level exclusion of that defect zone, E 503–508 k / N 7,052–7,062 k MGA56 — it caught
  29,735 offshore-folder points too. (3) **Vertical datum resolved as standard AHD** — the LAS
  files' "Australian Hydrographic Datum" VLR tag treated as a mislabel, per Fugro's own RoS
  ("shifted to the AHD datum", AusGeoid08) plus two clean zero-offset onshore/offshore seams;
  the seam test elsewhere was inconclusive-to-noisy (tile-join mismatches are a documented
  defect), so AHD-per-Fugro is a judgement call, not a certainty — if imported depths ever look
  systematically ~1 m off vs charted/soundings, revisit this first. (4) Same per-port AHD→LAT
  offsets as `export_csv.py` (Noosa Head 1.15 north of lat −26.533, Mooloolaba 1.00 south of
  it). (5) Clip to the real Area-A block E 496–524 k / N 7,040–7,136 k (tile-grid derived — the
  ISO record's bbox is a loose envelope, and its format list was outright wrong: the zip is LAS
  1.2 point clouds + XYZ, not the claimed SHP/TAB/FGDB/KMZ/GPKG). NOT imported on-phone —
  946,877 rows vs the 25k import cap needs a thinning decision first (next-session note).

- **v16.24 (11 Jul 2026, data-processing build — no `index.html` change, no import performed):**
  Drop-mask BUILD shipped for the v16.23 hybrid scope (items 2+3 closed; Aaron's sign-off came
  as the PATH 2 go-ahead). **Why PATH 2:** `audit_results.json` stores only per-tile counts plus
  3 example coordinates (3,529 of 48,537 flagged cells), and the export-pipeline scratch
  (`merged_cells.json` etc.) is class-2-only — flagged-cell geography was not recoverable, so the
  mask was re-derived from raw LiDAR. **Halved job, not a full re-export:** because the v1 CSVs
  are unthinned one-point-per-25 m-cell exports, only removal was needed — re-scan raw tiles for
  flagged-cell keys, drop v1 points falling in those cells, keep everything else; the AHD→LAT
  pipeline was not re-run. **Grid definition (load-bearing):** 25 m cells anchored at the
  projection origin (cx = floor(E/25), cy = floor(N/25)) in each tile's NATIVE CRS — EPSG:28356
  (GDA94/MGA56) pre-2022 vintages, EPSG:7856 (GDA2020/MGA56) 2022–23; keys are (epsg, cx, cy)
  and never compared across CRSs (~1.8 m grid shift between datums). **Re-scan:** all 1,184
  hybrid-scope tiles, exact v16.17–v16.21 method/thresholds (25 m, ≥20 class-9 + ≥100 class-2,
  medians ≤0.5 m), extract-and-discard per tile (~1 GB transient, 681 GB free at start), wall
  91 min (PID 13488), checkpoint/resume + progress-every-25 discipline, smoke test first
  including an injected-mismatch test that the cross-validator correctly caught. **Verification:
  48,194 flagged cells recovered; per-tile counts matched audit_results.json 1,184/1,184 (zero
  mismatches); spot-check 28 tiles across all 14 survey groups — 84/84 stored example
  coordinates present in the re-scan cell sets.** Mask = 44,427 unique cells after multi-vintage
  overlap collapse (scratch: `_inventory/hybrid_mask_cells.json`, gitignored). **Applied:**
  Brisbane River 209,540 → 189,187 (−20,353 pts); Sunshine Coast 188,855 → 168,461 (−20,394 pts);
  total −40,747 pts vs 44,427 mask cells (fewer points than cells is expected — not every flagged
  cell had a surviving exported point). Post-check: ZERO v2 points remain inside any mask cell,
  either region. 2009-vintage points untouched (mask built only from post-2009 tiles, so the
  exclusion holds by construction — a 2009-sourced CSV point can't sit in a flagged cell's
  newest-wins slot anyway). **Control validation — all ten PASS** (per-tile check: flagged cells
  → 0 points in v2, rest of tile survives): Brighton 133→76 tile pts (both vintages' artifact
  cells emptied — the fault's origin site is finally masked), Sandgate 836→579, Shorncliffe
  589→470, Brisbane R. mouth #1 1,593→962, #2 1,385→1,028, Redland bayside #1 744→460,
  #2 1,014→778, Deception Bay/Beachmere 397→311, Golden Beach/Pumicestone 1,484→1,236 (all five
  overlapping vintages emptied), Currimundi 1,104→1,031. **Files: v2 CSVs committed alongside the
  kept v1s** (v1 stays until Aaron confirms re-import). **Phone data UNCHANGED — nothing
  imported. Item 4 (manual REPLACE re-import, both regions, NOT MERGE) is the remaining step and
  is Aaron's alone.**

- **v16.4 (3 Jul 2026, verification only — no code shipped, no `index.html` change):** Resolved
  both open validation items flagged in v16.3. **`version:2` export/import confirmed to carry
  `woongarra_imported_v1`** — verified by direct code read (`exportBackup()` line 2225,
  `importBackup()` lines 2244–2246), not inferred from variable naming; the `imported` array
  exports and merge-restores on the same tier as photos/profiles. Supersedes the v16.2 "CSV may be
  the only durable backup" caution — a `version:2` export now covers depth data too; raw processed
  CSVs remain worth keeping short-term for re-derivation, but that's convenience, not necessity.
  **ELVIS Bathymetry (3 m) datum confirmed genuinely unconfirmable via any headless route** — the
  portal is a pure Angular SPA (no fetchable metadata, every path probed returned the same empty
  shell) and no ICSM/CKAN catalogue record exists for this specific product. Downgraded to a
  manual-order handoff — check the datum field on ELVIS's own product/layer info panel before
  submitting the order; not a Claude Code task. **Next:** manual ELVIS datum check (in-browser,
  before ordering); then tighten the Sunshine Coast + Brisbane River AOIs under the confirmed
  ~10,000-tile order cap (per v16.2) and download; once both land, chain into the depth
  clip/AHD→LAT-convert/CSV-export/import data-processing pass. Separately, **2b wiring** (zoning/FHA/
  tides only, depth deferred) is a clean inline build ready to go now — `data/great_sandy_zones_2026.geojson`
  and `data/fha_se_qld_2026.geojson` are validated and sitting in the repo, Mooloolaba is confirmed
  as the tide port.

- **v16.3 (3 Jul 2026, planning + data-prep only — no code shipped, no `index.html` change):**
  Completed the zone/FHA/closure/tide-port investigation that stalled in v16.2. **Pulled + validated
  Great Sandy zones (104 features) and statewide FHA (72 unique declared areas) from the live QLD
  ArcGIS service**, clipped FHA to a SE QLD extent (35 features / 26 plans, incl. Maroochy FHA-008 and
  Noosa River FHA-051 for 2b), matched output schema to what's already shipped in `index.html`
  (cross-checked `zid`/`name`/`plan` values directly against the live file, not assumed), wrote
  `data/great_sandy_zones_2026.geojson` + `data/fha_se_qld_2026.geojson`, validated with a script
  (geometry validity, schema completeness, `notake` correctness, duplicate-id check) — 0 errors.
  Confirmed in passing that the Great Sandy zones already shipped in `index.html` match this live
  pull exactly (not stale). **Brisbane River: no zone-style closure** — point-in-polygon tested
  against all 74 Moreton zones (zero hits) and cross-checked the full 72-entry statewide FHA list
  (no Brisbane River entry) — the app's existing "outside marine-park zoning" default is confirmed
  correct there, not assumed. Separately noted (different mechanism, not wired, not zone-style): the
  Fisheries Regulation 2008 has standard weir-buffer closures at Mt Crosby Weir/Old Mt Crosby
  Weir/Wivenhoe Dam and lists the river under the commercial-netting closed-waters schedule — neither
  affects recreational line fishing or `zoneAt()`. **Sunshine Coast tide port: Mooloolaba confirmed**
  as a BOM/NTC Standard Port (own harmonic prediction, 2026+2027 PDFs published, no offset math) — the
  pick for 2b, same pattern as Burnett Heads/Brisbane Bar; Noosa Head is a Secondary Port (offset not
  yet sourced, not blocking, parallel to how Redcliffe was added after Brisbane Bar in 2a). **Next:**
  the zoning/FHA/tide-port data is now ready for a 2b wiring build (merge `great_sandy_zones_2026`
  confirms current, add `fha_se_qld_2026` as the first FHA layer, source Mooloolaba's 2026 H/L table
  into a `MOOLOOLABA_TIDES_2026` embed same as Brisbane Bar's) — still gated on the Maroochy/Noosa
  bathy-LiDAR depth half (ELVIS order, per the v16.2 status) if depth is wanted in the same pass, but
  zoning/FHA/tides no longer need to wait for that. Brisbane River depth (ELVIS, tidal-reach-bounded)
  remains open per v16.2.

- **v16.2 (3 Jul 2026, planning only — no code shipped):** Resolved the 2 Jul Claude Code session
  that appeared to hang: stalled after task 1 of 4 (Great Sandy zones fetch in-flight) when Aaron
  switched devices, near-certainly a missed permission prompt rather than a crash — fetch/validate
  only, nothing at risk, resumes cleanly on a new device via toolchain reinstall + fresh clone + the
  same instruction (confirms the repo-holds-state design works as intended). Corrected two stale
  pending items: "6a — badge unlock celebrations" doesn't exist anywhere in the roadmap (badges/item
  6 shipped complete in v16, certificates only — dropped from pending); the stale `v21 · 14 Jun`
  version-label bug was already fixed in the same v16 build (dropped from pending). **ELVIS back up
  — product and order-limit findings:** QLD Government **Bathymetry (3 m)** confirmed as the correct
  product (finer than the 5 m previously assumed); **DEM is the wrong product type** for underwater
  depth regardless of resolution — don't substitute it for Bathymetry; Point Clouds (AHD) stay a
  gap-filling fallback only. **Order cap confirmed at ~10,000 tiles** — a Noosa→Bribie AOI (950
  Bathymetry-3m tiles) cleared it but only covers Sunshine Coast, not the Brisbane River mouth; a
  wider Brisbane-River-or-below AOI hit ~17,000 tiles and needs tightening (bathymetry-only, single
  resolution, bounded to the tidal reach actually fished) before it will submit. Repo now split
  `data/raw/sunshine_coast/` and `data/raw/brisbane_river/` (gitignored) ahead of data landing.
  **Depth-data retention policy set:** raw LiDAR disposable once clipped/converted and the CSV is
  confirmed imported and rendering; the processed CSV itself must be kept — **unconfirmed** whether
  `version:2` export/import actually carries `woongarra_imported_v1`, so the CSV may be the only
  durable backup until that's checked. **Added Hold item:** national-scale coverage (QLD-wide + NT +
  WA + partial NSW), explicitly sequenced behind all remaining SEQ regions, architecture spike
  required regardless of priority. **Added backlog item 6b:** wildlife/sighting badges.
  **Correction made within this same revision:** 6b initially failed to cross-reference
  `guya_species_qld_v3.md`, which already contains the bush wildlife list (echidna, kangaroo, goanna,
  blue-tongue, etc., seeded 14 Jun) and a rare/special + local-hero badge tier — none of that was
  lost, it was just never duplicated into the roadmap file by design (the roadmap's own line always
  said the species seed lives in that file, not here). 6b is corrected to reference the existing
  spec explicitly and scope itself to what's actually new: a phased common→rare unlock rollout,
  additive to the existing rare/special tier, not a replacement for it. Reuses the existing
  `captive` flag (item 4) to separate wild-tally badges from zoo/aquarium sightings; blocked until
  the sightings store (item 4/5) ships. Badge-unlock *presentation* styling (a popup/toast at the
  unlock moment) was raised by Aaron but explicitly deferred — not yet spec'd. **Next:** resume the
  stalled zone/FHA/Brisbane-River-closure/tide-port investigation on Aaron's next Claude Code session
  (same instruction, clean device); once Sunshine Coast + Brisbane River LiDAR AOIs both clear the
  tile cap, chain straight into the depth clip/convert/import data-processing pass; 14b DEA
  Intertidal and 4c+ remain the clean inline builds if a coding session is wanted before the
  data-processing work lands.

- **v16.1 (2 Jul 2026, planning only — no code shipped):** Workflow migration to Claude Code CLI
  executed (CLAUDE.md + settings.json + roadmap committed to the repo; this project now
  planning-only). index.html re-verified by direct file read: 178 zones confirmed present, header
  text flagged stale (still says "Woongarra Coast · Great Sandy MP", no Moreton mention — cosmetic).
  Depth-import architecture clarified from source: localStorage-based, generic CSV import already
  built, not an index.html concern — reframes all future multi-region depth work as data-prep, not
  builds. 2b zoning/FHA reclassified from "needs a data run" to **Claude-Code-fetchable now** (live
  ArcGIS REST service found, no QSpatial order needed) — 2b's depth half (Maroochy/Noosa LiDAR)
  confirmed still manual-order-only, no shortcut found. Brisbane scope clarified as
  river+Pine+bay — bay/Pine already covered by the existing Moreton embed; river itself is the
  only open item (zone-closure check pending, depth pending on ELVIS). See the status block above
  the changelog for full detail. **Next:** greenlight the 2b zoning/FHA GeoJSON pull in Claude
  Code (data-prep only, no index.html change); check Brisbane River for any zone-style closure;
  check Sunshine Coast tide port sourcing; Aaron to re-attempt the ELVIS order for Brisbane River +
  Sunshine Coast LiDAR once the portal's dataset-search error clears.

- **v16 (28 Jun 2026):** **shipped item 6 — Badges / achievements (build 2026.06.28b).** One feature,
  one build. A self-contained top-level IIFE spliced before the app's closing `</script>`; reads the
  existing `spots` + `profiles` globals, renders into a new `#badge-out` panel behind a "🏅 Show badges"
  button in the patterns block. **18 badges, computed entirely from the stamped catch log:** first / 10 /
  25 / 100 catches; 5 / 15 / 30 distinct species; 10 released (**Release Champion**); 5 distinct spots
  (**Rock Hopper**); **PB Breaker**; **New-Moon Ninja**; **Full-Moon Fever**; **Spring-Tide Specialist**
  (5 spring-tide catches); **Tide Whisperer** (all stamped tide phases); **Four Seasons**; + secret
  **Grand Slam** (bream + flathead + whiting in one day) · **Dawn Patrol** (04:00–06:30) · **Night
  Shift** (20:00–04:00). Per-angler `<select>` (Everyone, or filter `c.by===id`); "earned / total"
  count; unlocked badges show colour + unlock date + a **certificate** button; locked non-secret badges
  show a progress bar (cur/target); secret badges show ❔ until earned. **Certificates** are drawn
  offline on a 720×520 canvas (tier-colour border, emoji glyph, badge name + desc, "AWARDED TO" angler,
  unlock date) and downloaded as PNG — **no assets, no network, no IndexedDB writes, zero egress.**
  **Three data-model truths recorded, none worked around:** (1) **Tide Whisperer is 3-phase** — the
  stamped `env.tide.state` only holds `rising`/`falling`/`slack`; the roadmap's "four tide states" was
  wrong and is corrected in item 6. (2) **Moon/tide/season/spring badges need stamped `env`** — legacy
  catches without auto-stamp, or catches in a tide-table-less region, don't count toward those (never
  fabricated). (3) **Sighting badges deferred to item 4** — Mon Repos, Reef Spotter (Fiji),
  captive-vs-wild and protected-species badges require a sightings store that doesn't exist yet; badges
  are catch-log only. **Also reconciled the version labels** flagged in v15: the stale `build v21 · 14
  Jun 2026` marker in the info panel (line ~1074) now reads `build 2026.06.28b`, matching the header —
  the divergent v21/14-Jun scheme is gone, single build-string scheme throughout. **Validation:** Leaflet
  `<script>` **and** `<style>` byte-identical to the upload (sha256 match), `node --check` PASS on both
  script blocks, green-zone drag safeguard + most-protective `zoneAt` (MNP > CPZ > HPZ > GUZ) intact,
  no stored-data shape change. Badge engine unit-tested in isolation against 7 synthetic catches across
  spots/seasons/moons/tides — **23/23 assertions pass** (first/board/sp5/rel/spots/pb/newmoon/fullmoon/
  spring/tide3/seasons/slam/dawn/night with correct unlock dates). **Next:** open — 14b DEA Intertidal
  (after a manual DEA-Maps confidence check) or 4c+ profile-aware views are the clean inline jobs; 2b
  Sunshine Coast still needs an out-of-sandbox data run first.

- **v15 (28 Jun 2026):** **region-aware astronomy + live-wind fix (build 2026.06.28a).** Cleared the
  Bargara-anchored remnants left out of 2a scope, and fixed a latent live-wind crash found while doing it.
  **Astronomy:** added an `ANCHOR()` helper in the best-bite IIFE (`curPort()` -> nearest-port lat/lng); the
  four hardcoded Bargara `compute(ymd,-24.847,152.482)` / plan-wind-fetch sites in `render`, `scoreSpotsFor`,
  `planFor`, `buildPlan` now resolve to the current region (Redcliffe -> Brisbane Bar, Bargara -> Burnett
  Heads), so sun/moon/solunar match where you're actually looking. **Wind:** the standalone live-wind button
  and the spot "wind vs spots" check were both Bargara-pinned **and** silently broken — they (and `tideNow`)
  called `curPort()`/`tideTable()`, which are private to the best-bite IIFE, throwing a `ReferenceError` that
  dropped the whole render into the catch block ("No signal") even online. Fix: both IIFEs now call the
  already-global `nearestPort(map.getCenter())` directly — no new `window.*` hook (the originally sketched
  `window.astroAnchor` was avoidable: `nearestPort`/`PORTS` are top-level and visible to sibling IIFEs in the
  browser; only `node --check` sees them as undefined, a harness artefact, not an app bug). The "Bargara"
  wind button is relabelled **Live wind**; its result header + tide attribution now show the resolved port
  name. "This view" (map-centre) button unchanged. **Validation:** Leaflet block byte-identical (147552
  chars), `node --check` PASS on both script blocks, green-zone drag safeguard + `zoneAt` intact, no
  stored-data shape change. **Flag for Aaron:** the file carries two version labels — header `build
  2026.06.28a` (the authoritative build string, bumped) and a stale `v21 - 14 Jun 2026` in the about/info
  panel (line ~1050) that disagrees with both this roadmap's v-count and the build date; left untouched to
  avoid guessing the scheme — worth reconciling. **Next:** item 6 (Badges).

- **v14 (27 Jun 2026):** **shipped Region 2a — Moreton Bay / Redcliffe wiring (build 2026.06.27a).**
  One clean build, exactly to the v13.1 spec, validated end-to-end against the actual extracted JS in
  Node. **Tides:** `BRISBANE_TIDES_2026` embedded top-level beside Burnett — 365 days, byte-identical to
  the validated source, BoM/MSQ + LAT + no-warranty comment. **Zones:** the 74 `moreton_zones_2019.geojson`
  features merged into `ZONES.features` → **178 total** (104 legacy Great Sandy + 74 Moreton), every
  Moreton feature carrying `plan:"Moreton Bay MP"` + the QPWS `src`. **Ports:** `PORTS` registry +
  `nearestPort(centre)` (haversine off map centre, no GPS) added; the best-bites IIFE tide lookup + the
  "Tides · Burnett Heads" heading + notes all routed through it (Redcliffe → Brisbane Bar, Bargara →
  Burnett Heads, both verified). **`zoneAt()` rewritten to most-protective** (MNP > CPZ > HPZ > GUZ) —
  tested on a real overlap pin sitting inside both MNP02 (no-take) and CPZ01: returns MNP02 `notake:true`
  (first-match would have mislabelled it as fishable CPZ). **Popups** region-aware via per-feature
  `plan`/`src` with a Great-Sandy fallback. **Default view + Home → Redcliffe**; Woongarra stays reachable.
  **Preserved & re-verified:** Leaflet `<style>`+`<script>` byte-identical (hashes match), green-zone drag
  safeguard + `zoneAt` intact, both script blocks `node --check` clean; no stored-shape migration
  (ZONES/tides static). **Two findings recorded, neither changed silently:** (1) the **"orphaned
  species-filter cleanup" was mislabelled** — the in-IIFE `rec*` cluster is **live** (`speciesMatch` boosts
  `rankSpots`, chips wired to `rankSpots()`, `spPickOpen` bound to a click handler), so the cleanup is
  **cancelled — do not strip** (item 2 note + Cleanup section corrected). (2) Out of 2a scope, left as
  follow-ups: the best-bite **astronomy** still uses a fixed Bargara lat/lng and the standalone **wind
  button** is still Bargara-anchored — region-aware versions are a small next job. **2027 Brisbane Bar
  tides** still needed before onboarding 2a for the 2027 season (not blocking 2026 use). **Next:** item 6
  badges (the stated strong pick) or 2b Sunshine Coast (next region). **Process:** this is the build chat
  that owns the v14 bump; roadmap updated in place from the attached v13.1 file (not reconstructed).

- **v13.1 · 2a sourcing complete (20 Jun 2026):** **both 2a data files built + validated; no code
  shipped.** **Tides:** `brisbane_bar_tides_2026.json` — 365 days, column-aware parse of the MSQ text,
  validated (weekday / chronology / strict H-L alternation all pass), `BURNETT_TIDES` shape.
  **Zones:** `moreton_zones_2019.geojson` — built from the QSpatial **"Moreton Bay marine park zoning
  2008" SHP** (Aaron-supplied), 74 zones, **whole park**, WGS84, ~11 m, 235 KB, props
  `{name,zt,zid,notake,plan,src}`, `notake=(zt=='MNP')`, merge-ready into `ZONES.features`; passes
  `validate_moreton_zones.py` exit 0 (self-tested against bad input), every home-water zone
  interior-point verified. **Two corrections to v12:** (1) the **"avoid 2008" rule is REVERSED** — the
  2019 remake was administrative-only with **zero zone-boundary changes**, so the 2008 zoning data *is*
  the current legislated geometry (same zone IDs), confirmed against legislation **and** the attribute
  data; the MSES "highly-protected-zones" layer is no-take-only and was the wrong file. (2) **embed the
  whole park, not the old home clip** — the clip would have dropped **Bribie + Pumicestone**. **Wiring
  note:** home zones overlap (Hays Inlet/Bramble Bay = MNP + CPZ) → `zoneAt()` must return the
  **most-protective** zone (MNP > CPZ > HPZ > GUZ). Build string stays **14l**; the **wiring build owns
  the v14 bump.** *(This full file is a planning-chat completion update emitted at Aaron's request; it
  uses v13.1, not v14, to keep the no-forking rule intact.)*

- **v13 (20 Jun 2026):** **reconciled the two parallel 20-Jun chats into one file of record.** Both
  the 2a-sourcing chat and the 14b DEA-Intertidal eval branched from v11 and each self-labelled v12;
  this merges them — the build-chat base (verified tide/zone facts + sourcing recipe + wiring plan)
  with the DEA chat's evaluated **14b** (qualified GO, Exposure-only, confidence-gated; see item 14b).
  **No code shipped in either.** The HPZ→MNP zone correction from 2a sourcing stands (home no-take =
  MNP09 / MNP11 / MNP12-13, not the Redcliffe / Pine HPZs). Next build unchanged — the **2a thin-slice
  wiring** (Brisbane Bar tides + 2019 zone GeoJSON), rolling to the live ship date. **Process fix to
  stop re-forking: only the build chat emits a full roadmap; parallel planning/eval chats hand back a
  delta paste, never a competing file.**

- **v12 · 2a sourcing (20 Jun 2026):** **no code shipped.** Verified Step-1 facts against official
  QLD sources and **split the data-prep out of the build chat** (both layers are verification-heavy).
  **Tide:** Moreton standard port = **Brisbane Bar (LAT)**; **Redcliffe = +0:00 secondary** → Brisbane
  Bar timing applies directly at home; official MSQ *Queensland Tide Tables 2026* (CC BY 4.0) is in
  project knowledge (the mis-named `…tidetables….pdf` is its text); **2027 still needed.** **Zones:**
  2019 plan confirmed current (Reg 175/2019); four zones map 1:1 onto the app's `STYLES` (no change).
  **Corrected a v10/v11 error:** HPZ06 Redcliffe / HPZ08 Pine River are **Habitat Protection (not
  no-take)**; the real home green/no-take zones are **MNP09 Deception Bay, MNP11 Hays Inlet, MNP12/MNP13
  Bramble Bay**. Recorded the turnkey sourcing recipe (column-aware tide parser w/ weekday cross-check;
  QSpatial/ArcGIS-REST 2019 zones → GDA94→WGS84, clip to home extent, simplify, GeoJSON w/ `plan`+`src`
  props) and the one-build wiring plan (PORTS+`nearestPort`, region-aware `zonePopup`, default view to
  Redcliffe). A confirmed naïve parse of the MSQ text mis-read tide times (multi-column delinearisation)
  — hence the dedicated pass. Build string stays **14l**; next build rolls to the live ship date.

- **v12 · 14b DEA eval (20 Jun 2026):** **evaluated DEA Intertidal (14b) over the home flats →
  qualified GO, Exposure-only, gated on a confidence check.** Verified the current product (v2.1.0,
  `ga_s2ls_intertidal_cyear_3`, 10 m, EPSG:3577, CC BY 4.0, latest 2024 epoch; 4 core layers incl. the
  new Extents). **Key finding: datum→LAT is solved inside the dataset** via the per-pixel `ta_lat` band
  (`height_above_LAT = elevation − ta_lat`); single-offset fallback = Brisbane Bar MSL = LAT + 1.32 m.
  **Tempered the roadmap's optimism:** turbidity is *survived, not solved*, and three cautions stack on
  exactly these flats — borderline-microtidal (~1.8 m spring range; DEA micro corr 0.61 vs meso 0.90),
  embayment tide-model error, and tidally-correlated turbidity false-positives. **Decision: build the
  Exposure layer** (datum-free, relative pattern robust, reads as habitat not depth) **and HOLD the
  "covered-now" elevation-vs-tide feature** (datum-dependent, error compounds, reads like bathymetry).
  Added a mandatory **DEA Maps confidence check** (uncertainty / ndwi_corr / extents false-positive test /
  offset_low / count_clear, with pass-fail thresholds — fail = no-go, depth stays sonar→GPX) and a
  **build-ready spec** (per-flat clip → QGIS mask on extents/uncertainty/corr → 3 exposure bins → 3577→4326
  → simplified GeoJSON primary, PNG ImageOverlay fallback; flats-only-rough + never-safe-to-walk labelling).
  No code shipped. Build string unchanged (next build still `2026.06.19a` — Region 2a slice stays the
  priority; 14b slots in after as its own small piece).

- **v11 (19 Jun 2026):** added the **Sunshine Coast (2b)** to the "local" home cluster under #15,
  sequenced **after** the Moreton Bay slice (2a). Its draw: **depth works there** — real 5 m
  Maroochy/Noosa bathy-LiDAR reproduces Woongarra-style shading, unlike turbid Moreton Bay; layers =
  a Sunshine Coast tide port + Maroochy/Noosa FHAs + the LiDAR depth ingest (its own piece). Verified
  the **zoning jurisdiction**: Moreton Bay MP ends at **Caloundra**, so Mooloolaba/Maroochy/Noosa are
  **outside marine-park zoning** — no green-zone polygons there, but the app must frame "no zone ≠
  unrestricted." Build cadence confirmed: **build and planning chats stay separate** (a slice build
  loads the ~1.4 MB file; the DEA-Intertidal eval needs none of it) — one chat each, slice first.

- **v10 (19 Jun 2026):** planning chat — **pivoted to home water (Moreton Bay / Redcliffe) as the
  dogfooding region.** Decided the immediate next build is a **Region 2 thin slice** (one Moreton tide
  port + the 2019 zone polygons into `zoneAt()`; FHA + depth deferred; both regions coexist), **ahead
  of badges** — so the app becomes usable where Aaron lives while building continues. Recorded the
  **SE-QLD depth reality** (turbidity defeats laser bathy; GA coarse open-coast; CSIRO composite =
  modelled creek depth, out by the no-chart-art rule) and added **DEA Intertidal (14b)** as a free,
  turbidity-tolerant **intertidal flats / exposure** candidate (flats only, never channel depth,
  observed not modelled). Noted the **QGIS → QSpatial → GeoJSON** data-prep workbench under #15.
  Switched the **build-string convention** to the live build date + letter (next build `2026.06.19a`).
  No code shipped this chat.

- **v9 (19 Jun 2026):** shipped **4c (photo avatars) — 14l**. Angler avatar is now a `{type, val}`
  spec supporting `{type:'emoji'}` (default/fallback) **and `{type:'photo', val:<IndexedDB id>}`**.
  The Anglers add flow gains a **"Use a photo"** option beside the emoji/colour pickers: photos are
  **downscaled to ~128 px and stored in the existing `woongarra_photos_v1` IndexedDB store**
  (reusing `downscaleToDataURL` + the catch-thumbnail async-resolve), rendered in `avatarChip`, the
  catch rows and the **"Logging as" chip** (option lists show a 📷 glyph since `<option>` can't hold
  an image). **Legacy bare-emoji avatars migrate transparently** — read as `{type:'emoji'}`, no
  stored data touched. **Export now also collects photo-avatar IDs** so the images ride in the
  `version:2` backup and **merge on import** with the rest of the photos; profile merge is unchanged.
  Leaflet block byte-identical; green-zone drag safeguard + `zoneAt` intact; both script blocks
  `node --check` clean. The inert `recSpecies` cluster (Cleanup) was **left untouched** to keep this
  diff tight. Next: **6 — badges / achievements** (high family delight, locally computable from the
  stamped log), or **4c+** once a second angler has logged; the `recSpecies` cleanup is the standing
  low-risk side task.

- **v8 (16 Jun 2026):** shipped **4c — local profiles & avatars** (14k): device-local
  `woongarra_profiles_v1`; catches carry `by`; **"Caught by"** selector in the log form with inline
  new-angler; angler **avatar on each catch row**; **"Logging as" chip → Anglers sheet** (switch /
  add [name+emoji+colour] / rename / delete + per-angler tallies); profiles in the `version:2`
  export and **merge on import**; legacy catches **untagged by design**. **Emoji+colour avatars
  only.** Added **4c+ — profile-aware views & family roll-up** (depends on 4c). Next: **14l** —
  bring-your-own **photo** avatars (downscaled in IndexedDB, async-resolve like catch thumbnails;
  avatar field already `{type,val}`-ready). The inert `recSpecies` cluster (Cleanup) is still
  pending — untouched in 14k.

- **v7 (15 Jun 2026):** **Spine complete (items 1 → 2 → 3).** Shipped the **full-DB target-species
  picker + group-level selection** (14h); shipped **item 3 — personal patterns** as **"Your patterns"**
  (14i — analytics prefer the stamped `env` and fall back to the date/time tables; added a **"By
  wind" bar** from stamped wind only; honest "thin so far" + "counts, not catch-rate" caveats); and
  **relocated the target-species filter** (14j) from "Best spots today" to the **saved-spots list**,
  where it's now the list's primary filter — the spot-list text-filter + sort row were removed, and
  the species filter was taken out of best-bets (which reverts to ranking without it). New
  top-level chip machinery drives the list (`spotSpecies` etc.); the old in-IIFE copy is now inert
  — logged as a **Cleanup** task. Next: **4c (profiles+avatars)** or **6 (badges)** — both build on
  the journal and add visible family value while the catch log fills out; or kick off **15/16**
  (multi-region → Scout) as planning.

- **v6.1 (15 Jun 2026):** added the **access / walkability assessment** to #16 Scout. Noted the
  planned **target-species filter upgrade** (14h): add species from the full DB via search, with
  group-level selection from the 17 DB headings; quick chips from your own data retained.

- **v6 (15 Jun 2026):** shipped **feature-ID Tier A** (14f) → **4b Tier A complete**; and the
  **target-species filter** on best-bets (14g — filter+boost saved spots by target/catch species,
  session-only) → extended item 2. Added **#16 Scout** (structure-first, zone-aware in-app Scout =
  in; report archives = a chat research step → candidate pins; coupled to #15) and put **in-app
  report-scraping on Hold**. Item 3 (personal patterns + "By wind") remained next on the spine.

- **v5 (15 Jun 2026):** shipped **best-bets range layer** (14e — `~1/2/3h/All` bands as a filter
  over the score; origin = map centre by default with an optional one-shot, non-stored GPS; per-row
  ≈ km · ~time drive; session-only) → **item 2 complete**. Codified the **location-is-one-shot/
  in-memory** design rule. Added **#15 multi-region coverage + trip-planner**. Added live-routing to
  the Hold list.

- **v4 (15 Jun 2026):** shipped **auto-stamp** (14d — tide/moon/wind/PB into each catch's `env`,
  conditions line + PB chip) → **keystone (item 1) complete**. Expanded **4b** into Tier A + deferred
  Tier B. Added **4c local profiles & avatars**. Expanded **item 6** badges. Added **depth items
  13–14**. Added the **External ID companions** section. Flagged item 3 to add a **"By wind" bar**
  and prefer stamped `env`.

- **v3 (14 Jun 2026):** shipped the **toolbar reorg** (14a) and the **catch-form species picker**
  (14b). Locked the QLD species/passport seed at v3. Added **feature-ID hints** (4b) and the
  **captive-vs-wild flag** (4); spec'd the **badges** (6); noted backup must carry photos (1).

- **v2 (14 Jun 2026):** generalised the species passport into a **Field Log / Nature Passport**
  (+ Fiji reef snorkel collection, look-don't-take guardrails); added the **seasonal stinger
  advisory** (10b); dropped shark sightings; added local-private-photos and spot-and-photograph
  design rules.

- **v1:** initial backlog — Phase 1 spine + reference layers, Phase 2 family, hold list.
