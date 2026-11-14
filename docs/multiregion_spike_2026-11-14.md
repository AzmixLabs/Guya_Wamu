Model actually running: Fable 5.2 (claude-fable-5-2)

# Guya — Multi-region architecture spike (read-only design)

Output file: C:\Guya\Guya_Wamu\scratchpad\multiregion_spike.md. Appended phase by phase; each
phase ends with a CHECKPOINT line. This file supersedes the earlier 5,132-byte STOP report
(SHA256 ff6ec3e2…cffa6db), whose only finding — main 1 ahead of origin/main — is resolved by
Step A below.

## STEP A — SHIP GATE FOR 0c8d6ff (slope-exit v2): PASSED, PUSHED, DEPLOYED

A1. scratchpad\slope_exit_build_v2.txt: 16,117 bytes, SHA256
    9c308d8e1708f33f595a120303aae0318b3da3cd7c1673b2550b45e98b53877c. Present. V1, V2, V3, V4,
    V5, V6 each read PASS ("PHASE 3 -- VERIFY (ALL PASS)"). No STOP reported. Model line in
    that report: "Sonnet (Claude Sonnet 5, claude-sonnet-5)".
    Observation (not a STOP criterion): its Phase 4 says "RESULT: SHIPPED … commit (see Phase 4
    below)" but Phase 4 records only the commit message — no commit hash, no push, no Pages
    run. "SHIPPED" in that report meant "committed", which is how the push was missed.
A2. Re-verified independently this session:
    - `git rev-parse 0c8d6ff^` = 7f10308cc08eacae36350e568a01f0086c6a13c4. PASS.
    - `git show --numstat 0c8d6ff` = `4 3 index.html`, one file. PASS.
    - 4 hunks (`git show -U0`): @@ -1036 +1036 (#sbar: `<button id="sl-exit">Exit</button>`
      appended directly after `<button class="primary" id="sl-save">Save</button>`, no class
      attribute — not primary); @@ -1052 +1052 (build 2026.09.26b → 2026.10.01a); @@ -1091
      +1091 (same); @@ -1941,0 +1942 — inserted line is exactly
      `document.getElementById('sl-exit').onclick=exitSlope;` (od -c confirms it ends `;\n`,
      nothing else), directly after the sl-save handler line. PASS.
    - node --check: block 0 (Leaflet, 147,552 B) OK; block 1 (app, 2,151,081 B, SHA256
      3ae18360ba0d579574b1b4f09d00fd41e6934f1f73522aaa853917bab766ccbb) OK. PASS.
    - Leaflet body SHA256 (body only, tags excluded) =
      db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a, 147,552 B — matches the
      CLAUDE.md pin. PASS.
A3. `git push origin main`: `7f10308..0c8d6ff  main -> main`.
    Pages run ID 43520147979 ("pages build and deployment"), head_sha
    0c8d6ff6e30a18c2ef3169e2060b3de692982c7f, created 2026-11-13T22:32:47Z, status completed,
    conclusion success at 2026-11-13T22:33:33Z (public REST API,
    /repos/AzmixLabs/Guya_Wamu/actions/runs?head_sha=…).
    Live page https://azmixlabs.github.io/Guya_Wamu/index.html (cache-busted): HTTP 200,
    2,368,393 bytes, SHA256 9e15dbfa5a6c1dbab0399ae92c36d681e2f77e0a8e1fb617a8c1fc53efe47256;
    `cmp` against repo index.html: byte-identical. PASS.
A4. `git status -sb` = `## main...origin/main` (no ahead/behind), 0 porcelain lines. HEAD =
    origin/main = 0c8d6ff6e30a18c2ef3169e2060b3de692982c7f. PASS. The push was the only write
    to the repo/remote this session. No roadmap entry written.
    STILL OWED (planning chat): roadmap delta for 2026.10.01a, and the on-phone gate for the
    slope Exit button (v2 report P3 flags the 320 px width squeeze: ~17 px floor-estimate left
    for #sl-readout with four buttons).

## STEP B — SPIKE

## PHASE 0 — PRECONDITIONS (ALL PASS)

- git status: clean (0 porcelain lines), `## main...origin/main` — up to date after fetch. PASS.
- HEAD: 0c8d6ff6e30a18c2ef3169e2060b3de692982c7f (= origin/main).
- index.html: 2,368,393 bytes, SHA256
  9e15dbfa5a6c1dbab0399ae92c36d681e2f77e0a8e1fb617a8c1fc53efe47256.
- Build string read from the file: 2026.10.01a (index.html:1052 and :1091) — the later
  slope-exit build, not 2026.09.26b.
- Topmost GUYA_ROADMAP.md version (line 3): v16.77.18 · 1 Oct 2026. Roadmap file 939,803 bytes.
  No roadmap entry exists yet for 2026.10.01a.

CHECKPOINT: Phase 0 complete 2026-11-13T22:36Z

## PHASE 1 — INVENTORY: WHAT THE APP ASSUMES TODAY

All line numbers are index.html at HEAD 0c8d6ff (2,368,393 B). Quotes are verbatim, truncated
with … . Helper: scratchpad\mr_inventory.js (byte/feature census; read-only).

### 1a. Persistence map

Storage APIs present: localStorage and IndexedDB only. No Cache API, no service worker, no web
manifest, no sessionStorage (grep for `caches.`, `serviceWorker`, `rel="manifest"`,
`sessionStorage` over the whole file: zero hits). `navigator.storage` is used only by
storage_check.html, not by the app.

**localStorage (all in the one ~5 MiB WebKit per-origin container — roadmap v16.62 §2 bracket
[4,995.5, 5,919.6) KiB; 5,120 KiB assumed, not measured):**

| key | writer (file:line) | reader | shape | class | size driver |
|---|---|---|---|---|---|
| `woongarra_imported_v2` (`IMP_DS_KEY` :2711) | `trySaveDatasetsObj` :2762 `localStorage.setItem(IMP_DS_KEY,JSON.stringify({datasets:dsObj}))`; legacy wrap :2725; custom→maroochy_noosa retag :2735 | boot :2715 | `{datasets:{<regionKey>:{region,label,importedAt,points:[[lat,lng,depth],…],sourceType?}}}`; lat/lng 6 dp, depth 2 dp (:3976) | PUBLIC-DERIVED (LiDAR) | 134,372 pts = 3,849.1 KiB (roadmap v16.62 §4) — about 77% of the container |
| `woongarra_imported_v1` | none (legacy) | :2717, only if v2 is empty | flat `[[lat,lng,depth],…]` | public-derived, LEGACY | migrated into `datasets.legacy_unknown` at :2724; the v1 key is never removed by code |
| `woongarra_imported_meta_v1` | none | :2720; removed :4033 on Clear ALL | `{name,when}` | legacy meta | tiny |
| `woongarra_imported_receipt` (`IMP_RECEIPT_KEY`) | :2768 | boot check :2810 | `{v:1,counts:{region:n},savedAt}` | derived | tiny |
| `woongarra_imported_rollback_v2:<region>` (`IMP_RB2_PREFIX`) | `snapshotImpRegion` :2786 | `latestImpSnapshot` :2791; removed :2799 | `{at,region,dataset:<whole prior dataset> or null}` | public-derived COPY | up to one full extra copy of each region touched — this is the REPLACE rollback path and the transient-peak driver (v16.62 §9 item 6) |
| `woongarra_imported_rollback_v1` | — | removed unconditionally at boot :2713 | superseded whole-store snapshot | — | 0 after first boot |
| `woongarra_depthpoints_v1` (`STORE` :1345) | `savePts` :1352 | `loadPts` :1351 | `[{id,lat,lng,depth,label}]` | USER | own pins; small |
| `woongarra_spots_v1` (`SSTORE` :1423) | `saveSpots` :1425 (+ rating migration :1424) | `loadSpots` :1424 | `[{id,lat,lng,name,species,…,rating,tide,catches:[{id,…,photo:<photoId>,by:<profileId>}]}]` (:1621, :1799) | USER | catches; photo bodies are NOT here |
| `woongarra_rating_scale` | :1424 | :1424 | `'10'` migration flag | USER setting | — |
| `woongarra_profiles_v1` (`PSTORE` :1429) | `saveProfiles` :1435 | `loadProfiles` :1433 | `{v:1,active,list:[{id,name,avatar,color}]}` | USER | — |
| `woongarra_species_user_v1` (`SPU` :1628) | :1633 | :1629 | user-added species names | USER | — |
| `woongarra_transects_v1` (`TSTORE` :1881) | `saveTx` :1883 | `loadTx` :1882 | `[{id,name,verts:[…]}]` (:1941) | USER | — |
| `woongarra_walks_v1` (`WSTORE` :3331) | `saveWalks` :3333 | `loadWalks` :3332 | `[{id,name,date,pts:[…]}]` (:3370) | USER (opt-in GPS) | breadcrumb length |
| `woongarra_contours_v1` (`CSTORE` :3792) | `saveCt` :3794 | `loadCt` :3793 | `[{id,name,depth,pts:[[lat,lng],…]}]` (:3835, :4124) | USER | drawn / Navionics routes |
| `woongarra_sessions_v1` (+`_cur`) | :4064 / :4065, restore-merge :3319 | :4060 / :4061, :3262, :3771 | session log array + in-progress session | USER | — |
| `woongarra_shade_op` | :2701 | :2697 | number string | setting | — |
| `woongarra_collapsed_v2` | :4105 / :4107 | :4098 | `{<section label>:bool}` | setting | — |

Every user-data `save*` is `try{localStorage.setItem(…)}catch(e){}` — a quota failure on spots,
pins, walks, contours or transects is SILENT, e.g. :1425
`function saveSpots(){try{localStorage.setItem(SSTORE,JSON.stringify(spots));}catch(e){}}`.
Only the imported-depths path verifies (:2761-2771). Consequence: today the public LiDAR blob
and the user's irreplaceable logbook compete for the same 5 MiB, and it is the logbook that
fails silently when the blob fills it. That is the strongest single argument for moving the
depths out of localStorage, independent of multi-region.

**IndexedDB (StorageManager-quota'd; v16.62 §2 recorded estimate() quota 39,321.6 MB in the
home-screen container):**

| database / store | writer | reader | shape | class |
|---|---|---|---|---|
| `woongarra_photos_v1` / `photos` (:1730-1737) | `photoPut(id,dataUrl)` :1734; backup restore :3324 | `photoGet` :1735, `photoAll` :1737 (export) | key = photo id, value = downscaled image as a data-URL STRING | USER — irreplaceable |
| `woongarra_tiles_v1` / `tiles` (:1245-1252) | `idbPut(key,blob)` :1250 from `CachedTiles.createTile` :1259 (implicit, on view) and `saveViewOffline` :4197 (explicit, ≤1500 tiles per save :4193) | `idbGet` :1249 | key `'esri:z/x/y'`, value image Blob | PUBLIC cache (Esri Sat only) |

Both DBs are version 1 with one keyless object store each, opened fresh per call (no shared
connection, no `onversionchange` handling). The tile cache is the existing precedent for
"public data cached in IndexedDB, fetched over the network, explicit Save for offline" — the
named hypothesis already exists in miniature at :1244
(`/* ---------- OFFLINE TILE CACHE (IndexedDB, no service worker) ---------- */`).

**version:2 export / import.** `exportBackup` :3257-3269. Shape (:3262):
`{app:'woongarra',version:2,exported,spots,depthPoints:points,transects,contours,walks,imported,datasets,sessions,profiles,photos}`.
`imported` is the flat array AND `datasets` holds the same points again;
`JSON.stringify(data,null,2)` (:3263) pretty-prints. That is the 19.08 MB-for-3.85 MB double
storage (v16.62 §6). Photos are embedded as data-URL strings (only those referenced by a catch
or a profile avatar, :3259-3261). `importBackup` :3270-3328: user collections MERGE by id
(:3274-3280); imported depths are whole-store REPLACE — it builds `newDatasets` from
`d.datasets` (:3283-3287) or, for a pre-region backup, wraps `d.imported` as `legacy_unknown`
(:3288-3293), then write-then-mutate: `const ok=trySaveDatasetsObj(newDatasets);` (:3303), and
only on `ok` snapshots every affected region and swaps (:3305-3307). It never checks
`d.version` or `d.app`.

**REPLACE rollback-snapshot path.** CSV import :3942-4035. Parse → thin to `MAXP=25000` by
grid-dedupe (:3979-3984) → build `candidateDatasets` → `trySaveDatasetsObj(candidateDatasets)`
(:4008) → on success `snapshotImpRegion(region)` (:4011) THEN `datasets=candidateDatasets`
(:4012). The snapshot is written while live `datasets[region]` is still the PRIOR state, so the
slot holds the pre-import dataset. Peak localStorage demand during a REPLACE = the new store
plus a full copy of the prior region. Undo: `undoLastImpReplace` :2793-2801; the most recent
slot across regions wins (:2789-2792). The force-close/reopen ritual exists because of
:2765-2767: `/* durability receipt: on iOS WebKit this same-session read-back is served from the in-memory storage area and cannot see an async flush-to-disk failure …*/`.

### 1b. Baked-data map (byte breakdown of index.html)

Measured by scratchpad\mr_inventory.js. File 2,368,393 B; gzip-9 730,644 B; brotli 551,778 B.
What Pages actually transfers: 745,821 B gzip (measured, see 2b).

| block | bytes | % of file | records | source | consumers |
|---|---:|---:|---|---|---|
| Leaflet CSS (style 0) | 14,271 | 0.6 | — | Leaflet 1.9.4 | — |
| App CSS (style 1) | 34,631 | 1.5 | — | app | — |
| Leaflet JS (script 0) | 147,552 | 6.2 | — | Leaflet 1.9.4 (pinned SHA) | — |
| HTML markup + tags | 20,858 | 0.9 | — | derived: 2,368,393 − the four blocks | — |
| **App JS (script 1)** | **2,151,081** | **90.8** | | | |
| · `ZONES` :1219 | 1,148,809 (gz 312,320) | 48.5 | 178 features, 33,958 vertices | QSpatial legislated polygons | `zoneAt` :1335, `zoneLayer` :1286, `shadeMaskFeats` :2000 (→ scanline mask, `inWaterFast`), legend counts :1298 |
| ·· Great Sandy (no `plan` field) | 913,315 | 38.6 | 104 features (31 MNP, 28 CPZ, 28 HPZ, 17 GUZ), 23,980 vertices, 38.1 B/vertex | coords carry 15 significant digits (`[153.0040626700001,-25.90437222125784]`) | bbox W151.926 S−26.003 E153.415 N−24.498 |
| ·· Moreton Bay MP (`plan` + `src`) | 235,258 | 9.9 | 74 features (34 MNP, 10 CPZ, 15 HPZ, 15 GUZ), 9,978 vertices, 23.6 B/vertex | Moreton Bay Zoning Plan 2019; 5 dp | bbox W153.010 S−27.933 E153.612 N−26.802 |
| · `FHA` :1305 | 362,916 (gz 134,071) | 15.3 | 35 features / 26 distinct plans, 9,830 vertices | QLD FHA dataset, currency Aug 2023 | `fhaLayer` :1310, `fhaPopup` :1306; bbox W151.824 S−28.135 E153.480 N−24.387 |
| · Tide tables :3392-3444 | 257,256 (gz ≈58.8 k) | 10.9 | 4 ports × 2 years × 365 days, ≈32.15 kB per port-year | MSQ/BoM predictions (high/low events, not harmonics) | `PORTS` :3457-3468, `nearestPort` :3469, `tideHeightNow` :2942, best-bite IIFE, `FLATS_BOUNDS` :1987 |
| · `LANDMASK` :2827-2831 | 90,882 (gz ≈56.5 k) | 3.8 | 3 RLE bitmaps: woongarra 1113×1187, seq_coast 742×3748, brisbane_river 2301×1447 | OSM water ∧ DEA WOfS (Option 3) | `maskWater` :2878, `queryOnLand` :2904, `depthSamples` :2934 |
| · `LABELS` :1220 | 2,604 | 0.1 | 18 points | hand-curated | `placeLabels` :1320 |
| · `SPECIES_CATCH` :1627 (+ groups / feature hints :1635-1710) | ≈2.2 kB + code | <0.2 | seeded QLD species list | hand-curated | catch sheet |
| · remaining app code + comments | ≈288,600 | 12.2 | — | derived: 2,151,081 − 1,862,467 | — |

Three things this table says that matter for the design:

1. **Zones are the biggest thing in the file (48.5%) — not code, and not depth.** Depth is not
   in the file at all. Adding a third marine park at Great Sandy's vertex density adds roughly
   another 0.9 MB to every load. At "QLD coast" the single-file model breaks on ZONES before
   it breaks on anything else.
2. **Great Sandy costs 38.1 B/vertex against Moreton's 23.6**, purely from coordinate text
   precision (15 significant digits ≈ nanometres). Re-serialising GS at 7 dp (≈1.1 cm) would
   take roughly 340 kB out of the file with no legally meaningful change — but it changes the
   float operands of `pir()` and so can flip `zoneAt()` for a point within about a centimetre
   of an edge. That is a zone-geometry change: its own gated build with a full differential
   test, never a side-effect of this work. Flagged; not part of the recommended sequence.
3. **Tide tables are per-calendar-year and expire**: the embedded span ends 2027-12-31. The
   file needs an annual data refresh regardless of architecture; a design that fetches region
   data should carry tide tables the same way.

Zone IDs: 71 `zid` values are shared by more than one feature; cross-plan collisions confirmed
(`GUZ01` = Great Sandy "Kolan" AND Moreton "Bulcock Beach"; `CPZ01` = GS "Baffle Creek" AND
Moreton "Pumicestone Channel (north)"). Matches the CLAUDE.md domain fact.

### 1c. Depth-pool consumers

"Pool" = own pins + labelled-contour vertices + every imported point that passes the HAT gate
and the land mask, materialised by `depthSamples()`.

| consumer | file:line | whole pool resident? | viewport-scoped? | if only part of the pool were loaded |
|---|---|---|---|---|
| `rebuildImportedFlat()` | :2755 | YES — flattens every dataset into `imported / importedSrc / importedEx`, `poolVersion++` | no | works on whatever is in `datasets`; every region load/unload is a full re-flatten |
| `depthSamples()` | :2926-2941 | YES — allocates one `{lat,lng,d,st}` object per surviving point; per point calls `nearestPort` (4 haversines, :2929) and `maskWater` (:2934) | no; cached on `poolVersion` (:2927) | correct, but EVERY region arrival or eviction bumps `poolVersion` and re-runs the O(n) pass over the entire resident pool, not just the new region |
| `ptsBounds()` | :2214-2222 | YES (bbox of all) | no; cached on `poolVersion` | bbox changes with each load → `buildShade` extent (pool bbox ∩ padded viewport, :2427-2439) and the `cellLo` anchor (`mLngMin` from the pool's max abs-lat, :2506) change → index rebuild |
| `pooledSampleIndex()` / `buildSampleIndex()` | :2179 / :2138 | YES — one plain-object bucket store over the whole pool, 120 m cells | no; cached on `poolVersion` | rebuilt whole on every load. Key bound is fine to national extent (roadmap forward check, max key ≈8.63e8 < 2³²) |
| r0 precompute | :2540-2557 | YES — nearest-neighbour gap for every sample | no; `_r0Version` | recomputed whole on every load |
| `buildShade()` IDW pixel loop | :2571-2622 | reads only the 3×3 cells under each pixel | YES — grid ≤600² over the clipped rect (:2443) | correct for what is loaded. An unloaded area simply paints nothing, and nothing tells the user why |
| `scanlineMask()` | :2064-2116, call :2472 | n/a (zone corpus, not depth) | rows are viewport, but EVERY zone feature is visited per row (latitude reject only, :2080) | cost scales with the zone features resident, not with depth. Partial zone loading makes it cheaper — and makes "water" mean "inside a LOADED zone" |
| `idwIndex()` / `idwDepthAt()` (tap read, hover, deepest) | :2964-2981 | YES — a second whole-pool index, anchored at a fixed latitude: `mLng=111320*Math.cos(-24.85*Math.PI/180)` (:2970) | probe is local (3×3 cells) | cache key is LENGTH ONLY: `if(_idwCache&&_idwCache.n===s.length)return _idwCache;` (:2969). `buildShade` nulls it (:2404), so it is safe today; a region swap that leaves the count equal without a `buildShade()` would serve a stale index. Must become `poolVersion`-keyed before any partial loading. Also: the −24.85° anchor makes a cell 117.6 m wide at Redcliffe and 116.8 m at −28° (Gold Coast), below the 120 m `NEAR_MAX` the 3×3 probe is meant to cover — an existing constant that degrades southward |
| `openDepthRead()` (tap) | :2999-3043 | via `idwDepthAt` | local | prints `'No survey data within '+NEAR_MAX+' m here.'` (:3016) — indistinguishable from "survey data exists but is not loaded" |
| `findDeepest()` | :3061-3085 | via `idwDepthAt`, 29×29 lattice at 7 m | local (100 m disc) | `alert('No surveyed water within 100 m of that point.')` (:3076) — same ambiguity |
| `buildAutoContours()` | :3089 onward | same pattern as `buildShade` (`depthSamples`, `ptsBounds`, pool-anchored cells :3096-3122) | YES (grid ≤360², :3115) | same as `buildShade` |
| hover readout | :3910-3939 | via `idwDepthAt` | local | `'no survey data here'` (:3928) — same ambiguity; desktop only |
| slope snapping `nearestDepthPoint()` | :1899-1901 | NO — iterates `points` (own pins) only | screen-space 44 px | unaffected by any imported-pool change |
| best-bite / `scoreSpotsFor()` | :3644-3661 | NO — never touches the depth pool (rating, catches, tide table, wind) | n/a | unaffected by depth. It IS affected by zones: `zoneTag` :3641-3643 calls `zoneAt` and prints an outside-zoning line on null (see 1e) |
| compare tool `impIndex()` | :3861-3869 | YES — builds a fresh object array over all of `imported` per button press; same fixed −24.85° anchor (:3862) | no | compares own pins against whatever is loaded; silently finds nothing for an unloaded region |
| shade-toggle guard | :2705-2708 | counts `imported.length` | no | the "No depth data yet" alert would fire with regions available but unloaded |
| CSV import MERGE dedupe | :3994-3997 | region-scoped (`prevDs.points`) | no | needs that region's full prior dataset resident — fine if regions are the unit of loading |
| `exportBackup` / `importBackup` | :3262 / :3281-3316 | YES — serialises `imported` + `datasets` whole; restore REPLACES `datasets` whole | no | **the sharpest break.** If `datasets` held only the loaded regions, an export would silently omit the rest, and restoring that file would then DELETE them (whole-store replace). Public region data must leave the backup entirely, not be partially included |
| boot receipt check | :2810-2816 | compares per-region counts for everything | no | would false-alarm ("Last import didn't survive a restart") for any region deliberately not loaded |
| storage_check.html | repo root | reads localStorage key sizes; `estimate()` for the rest | n/a | blind to per-store IndexedDB / Cache contents; its section-3 caption is already known wrong (v16.62 §2) |

Summary: the PER-PAN path is already viewport-scoped and does not grow with region count (the
roadmap v16.62 §1 conclusion stands). What assumes whole-pool residency is (a) the per-load
materialisation chain `rebuildImportedFlat → depthSamples → ptsBounds → buildSampleIndex → r0`,
all keyed on one global `poolVersion`; (b) the second index in `idwIndex`; (c) backup and the
boot receipt. Under viewport-driven loading, (a) turns "pan into a new region" into an
O(resident pool) main-thread stall — measured in Phase 2d.

### 1d. Single-region assumptions

| # | assumption | file:line (verbatim) | should key on |
|---|---|---|---|
| 1 | Panel title + subtitle are constants | :1052 `<h1>Woongarra Coast</h1><div class="sub">Great Sandy MP · Zones + Depths · …build 2026.10.01a` | app name fixed ("Guya"); subtitle = the park(s) resolved for the map centre / view, or "outside marine parks", or "zone data not loaded" |
| 2 | Document + home-screen titles | :9 `content="Woongarra"`, :16 `<title>Woongarra Fishing Map</title>` | app name. Changing :9 does not rename an already-installed icon |
| 3 | Default view is Redcliffe while the title says Woongarra | :1228 `.setView([-27.2275,153.0950],12)` | last-used view (a setting) or a home region |
| 4 | Recentre target | :1327 `document.getElementById('home').onclick=()=>map.setView([-27.2275,153.0950],12);`, label :1204 `⌖ Recentre on Redcliffe` | per-region home list / user home |
| 5 | Park identity defaults to Great Sandy when a zone has no `plan` | :1280 `<div class="zid">${p.zid} · ${p.plan||'Great Sandy MP'}</div>` | a REQUIRED `park` on every zone record; no default — a missing value renders "park unknown", never a park name |
| 6 | Official-source link defaults to Great Sandy | :1282 `href="${p.src||'https://parks.qld.gov.au/parks/great-sandy-marine/management-and-zoning/app-and-maps'}"` | per-park `src` in a park table |
| 7 | **Rod/hook text is keyed on zone TYPE only** | :1223 `CPZ:{…rules:"Yellow zone — the marine park TIGHTENS the general limit here: 2 hand-held rods or handlines per person, and 2 hooks in total per person…"}` (also HPZ :1224, GUZ :1225: "3 hand-held rods or lines and 6 hooks or lures per person") | (park, zone type). CLAUDE.md rule 5 confirms these figures for Great Sandy and Moreton Bay ONLY. Today the text is right by coincidence — the only two parks baked are those two. The first GBR Coast MP polygon added would display "2 rods / 2 hooks" where the rule is 1 rod / 1 hook. The park-identity hazard is live in the data model now |
| 8 | "Unconfirmed limits" flag | no such flag exists in code (grep `unconfirm`: zero hits). Roadmap v16.77.18 backlog (e): "Zone cards state rod/hook limits as fact" | a per-park `limitsVerified:{date,source}`; absent → the card says limits are unconfirmed and shows no figures |
| 9 | About-panel legal links are Great Sandy only | :1200 `…/marine-parks/zoning/great-sandy-marine-park…` and `…/great-sandy-marine/…` | per-park links for the park(s) in view |
| 10 | Crocodile safety block is Bargara-specific prose | :1190 `Bargara sits <b>south of Queensland's formal croc-country management area</b> (it starts around the Boyne River near Gladstone)…` | region / latitude: north of the Boyne the statement is FALSE and understates risk. Region-scoped safety text, most-cautious wording when the region is unknown |
| 11 | Tide port = nearest of four, no distance cap | :3469 `function nearestPort(centre){…if(cl.lat==null)return PORTS[0];…for(const p of PORTS){…if(d<bd){bd=d;best=p;}}return best;}` | a region → port table, or nearest WITH a cap and an explicit "no tide port for this location" state |
| 12 | The 200 km cap exists but guards one feature only | :3470 `const PORT_MAX_KM=200;function portInRange(ll){…}` — sole caller :3782 (catch tide-stamp) | every tide consumer: `tideHeightNow` :2946, the `depthSamples` HAT gate :2929, `flatsBand` :1990, best-bite `curPort` :3509, live conditions :4133 all take `nearestPort` uncapped. A Cairns sounding today would be HAT-gated and "water now"-labelled from Burnett Heads tides, silently |
| 13 | Default port fallbacks | :3469 `return PORTS[0]` (Burnett Heads); :3511 `…:[-27.3667,153.1667]` (Brisbane Bar); :1864 `latitude='+(_wp?_wp.lat:-27.3667)` | no silent default; explicit unknown |
| 14 | Flats band fallback | :1990 `b=FLATS_BOUNDS[p.name]||FLATS_BOUNDS['Brisbane Bar']` | per-port bounds required; missing → no band |
| 15 | HAT per port, hand-entered | :3458-3467 `hat:3.70 … 2.81 … 2.24 … 2.37` | a port table shipped with region data |
| 16 | Region keys, labels, source types and mask exemptions are code constants | :1969-1970 `REGION_SOURCE={woongarra:'bathymetric',…,moreton_bay:'topographic'}`; :2753 `REGION_MASK_EXEMPT={woongarra:1,maroochy_noosa:1}`; :2802 `regionLabel` table; :1177 `<select id="imp-region">` with five options | a region manifest (data, not code): `{key,label,bbox,sourceType,maskExempt,port,parks[]}` |
| 17 | Depth-index longitude anchor | :2970 and :3862 `Math.cos(-24.85*Math.PI/180)` | pool-anchored like `buildShade` (:2506), or per-query latitude |
| 18 | Land-mask extents are three hard-coded rects; outside them everything is "water" | :2828-2830; :2887 `return true;` (roadmap :919: "includes Noosa north of −26.34 and all of the Gold Coast") | a mask shipped per region; "no mask here" must be a known state for topographic data, since the mask is what removes dry class-2 ground |
| 19 | Zones double as the "is this water" test | :1996 `/* Water mask from the legislated zone polygons — land (outside every zone) never gets shaded. */`; used at :3054, :3074, :3919 | fine while zones are complete. With partial zone loading, "not in any LOADED zone" ≠ land. Outside marine parks it is already false, which is why the `r.near<=NEAR_MAX` escape exists at :3054 |
| 20 | Legend counts computed once from the baked corpus | :1286 `counts[f.properties.zt]=…`, :1298 | coverage in view |
| 21 | Zone layer built once at init from the constant | :1286 `L.geoJSON(ZONES,{renderer:zoneRenderer,interactive:false,…})` | `zoneLayer.addData()` per loaded region; the `_shadeFeats` cache (:1997-1999, never invalidated) must be reset on every zone load |
| 22 | Storage / backup namespace | every key `woongarra_*`; :3262 `app:'woongarra'`; :3266 `'woongarra-backup-'…` | leave as-is. Renaming keys is a migration with no user benefit |
| 23 | Best-bite spot picker | :1061 / :3595 `Coast-wide` | cosmetic; already on the backlog as "Here" |
| 24 | Wind / forecast anchor | :3738 `ANCHOR()` = `curPort()` position | fine (map-centre driven) once #11 has a cap |

### 1e. Zone and FHA resolution path (verbatim)

`zoneAt` :1335
```
function zoneAt(lat,lng){let best=null,bi=99;for(const f of ZONES.features){const g=f.geometry;const polys=g.type==='Polygon'?[g.coordinates]:g.coordinates;let inside=false;for(const poly of polys){if(pip([lng,lat],poly)){inside=true;break;}}if(inside){const i=ORDER.indexOf(f.properties.zt);const rank=(i<0?98:i);if(rank<bi){bi=rank;best=f.properties;if(rank===0)return best;}}}return best;}
```
with :1227
`const ORDER=["MNP","CPZ","HPZ","GUZ"];const OUTPARK_TXT="Outside the marine park boundary. General Queensland fisheries rules still apply, and a Fish Habitat Area may too.";`

A linear scan of every feature, no bbox pre-reject, most-protective wins, early exit on MNP.
Returns the feature's `properties` object or `null`. `null` has exactly one meaning in the
code: "no polygon in `ZONES.features` contains this point".

`zonePopup` :1280-1282
```
function zonePopup(p){const s=STYLES[p.zt]||STYLES.GUZ;let h=`<div class="pop"><h2>${p.name}</h2><div class="zid">${p.zid} · ${p.plan||'Great Sandy MP'}</div><div class="ztype">…${s.name}</div>`;
  if(s.notake)h+=`<div class="notake">⛔ NO-TAKE — fishing prohibited. All gear stowed &amp; secured.</div>`;
  h+=`<div class="rules">${s.rules}</div><div class="warn">⚠ Simplified boundary — <b>not authoritative</b>. Confirm before fishing.<div class="links"><a href="${p.src||'https://parks.qld.gov.au/parks/great-sandy-marine/management-and-zoning/app-and-maps'}" …>Official maps & app ↗</a></div></div></div>`;return h;}
```
Note `STYLES[p.zt]||STYLES.GUZ`: an unrecognised zone type renders as General Use — the LEAST
restrictive style and rules text — and `zoneAt` ranks an unknown type 98 (least protective).
Harmless with four known types; the wrong direction to fail on the day another plan's zone type
(a GBR "Buffer" or "Scientific Research" zone, say) arrives.

`zoneCard` :1283
```
function zoneCard(ll){const z=zoneAt(ll.lat,ll.lng);return z?zonePopup(z):'<div class="pop"><div class="outpark">'+OUTPARK_TXT+'</div><div class="warn">Verify zone &amp; rules officially before fishing.</div></div>';}
```
`fhaPopup` :1306-1308
```
function fhaPopup(p){return '<div class="pop"><h2>'+p.name+' FHA</h2><div class="zid">'+p.plan+(p.mgmt?(' · Management '+p.mgmt):'')+' · Fisheries Act 1994</div>'+ … '<div class="warn">⚠ Indicative boundary, currency Aug 2023 (latest gazettal 21 May 2024) — <b>not authoritative</b>. …</div></div>';}
```
`fhaCard` :1309 `function fhaCard(ll,p){return zoneCard(ll)+fhaPopup(p);}`

FHA resolution is NOT a point-in-polygon lookup. There is no `fhaAt()`. The FHA block appears
only when Leaflet's canvas hit-test on `fhaLayer` fires the per-feature click handler
(:1314-1317):
`L.popup({maxWidth:300,minWidth:240}).setLatLng(e.latlng).setContent(fhaCard(e.latlng,f.properties)).openOn(map);L.DomEvent.stop(e);`.
So "no FHA here" is expressed by the ABSENCE of an FHA block, and it is absent in four
situations the user cannot tell apart: (i) genuinely no FHA; (ii) the FHA layer is toggled off
(:1318); (iii) a later-created canvas sits above the FHA canvas (roadmap backlog F7); (iv) a
tool mode. The only standing mitigation is the OUTPARK sentence "…and a Fish Habitat Area may
too", which appears only on the out-of-park card — an in-zone card with the FHA layer off says
nothing about FHAs at all.

**The OUTPARK branch — exactly what renders when `zoneAt` finds no polygon.** There are SEVEN
emit sites; four compose the OUTPARK HTML independently rather than calling `zoneCard`:

| site | file:line | renders on null |
|---|---|---|
| `zoneCard` | :1283 | `<div class="pop"><div class="outpark">Outside the marine park boundary. General Queensland fisheries rules still apply, and a Fish Habitat Area may too.</div><div class="warn">Verify zone &amp; rules officially before fishing.</div></div>` |
| map click, shading OFF | :3044 `const z0=zoneAt(…);…setContent(z0?zonePopup(z0):'<div class="pop"><div class="outpark">'+OUTPARK_TXT+'</div><div class="warn">Verify zone &amp; rules officially before fishing.</div></div>')` | the same HTML, composed inline |
| map click, shading ON, not water and no data within 120 m | :3054 `…setContent(zoneCard(e.latlng))…` | via `zoneCard` |
| map click, shading ON, depth read | :3058 `const z=zoneAt(…);openDepthRead(e.latlng,z?zonePopup(z):'<div class="pop"><div class="outpark">'+OUTPARK_TXT+…)` | the same HTML inline, as the prefix above the depth block |
| FHA tap | :1309 → `zoneCard` | OUTPARK block, then the FHA block |
| own depth-pin popup | :1362 ``else h+=`<div class="outpark">${OUTPARK_TXT}</div>`;`` | the OUTPARK sentence inside the pin popup; the pin list shows a grey `—` chip (:1373) |
| best-spots list `zoneTag` | :3642 `if(!z)return '<span class="bb-dim">outside marine-park zoning — general fisheries rules + FHAs still apply, confirm via Qld Fishing 2.0</span>';` | a differently-worded outside statement |

Plus two non-card consumers of the same null: pin colour (:1367, red ring only when
`z&&z.notake`) and the `inWaterFast(shadeMaskFeats(),…)` water proxy (:3054, :3074, :3919).

Consequence for every design in Phase 3: today `null` is truthful because the corpus is
complete for the two parks and baked. The moment zone polygons can be absent for a reason other
than "there are none", all seven sites assert "outside the marine park" for a location whose
zoning the app simply does not have. The fail-safe therefore cannot be a patch to `zoneCard`
alone: `zoneAt`'s contract has to become three-state, and all seven sites have to consume it.
The four inline copies should be collapsed into one function first — a behaviour-neutral
refactor that is its own build.

### 1f. Offline story today

- **No service worker, no manifest, no Cache API.** The only offline machinery is the IndexedDB
  Esri tile cache (:1244-1262, :4185-4203), labelled in the source `(IndexedDB, no service worker)`.
- **What works with no signal, and why:** everything baked into the file or held in
  localStorage / IndexedDB — zones + `zoneAt`, FHA polygons, tide tables and best-bite
  astronomy, land masks, measure, slope, own pins, imported depths + shading (localStorage),
  spots / catches, photos. That matches the About claim at :1201:
  `<b>Offline:</b> file, zones, measure & depth points work with no internet; depth points save in this browser. Map imagery streams (needs a connection).`
- **What does not:** QLD aerial (the DEFAULT base, :1243 / :1265 — not cached), OSM, CARTO
  labels (:1241), Open-Meteo wind / marine (:1864, :3738, :4152-4153). Only the Esri Sat base
  can be cached, and only by viewing it or pressing Save (:4186).
- **The gap in the claim — cold launch.** "File works with no internet" is true only while the
  document is already loaded. With no service worker, a COLD launch of the home-screen app
  with no signal must be satisfied from WebKit's HTTP cache. Pages serves the file with
  `Cache-Control: max-age=600` (measured this session, see 2b), and the page itself declares
  `<meta http-equiv="Cache-Control" content="no-cache, must-revalidate">` (:11). Whether iOS
  will serve a stale 2.37 MB document from HTTP cache to a standalone web app with no
  connectivity is outside the app's control. INFERRED: unreliable. UNVERIFIED on device — the
  roadmap records no deliberate cold-launch-in-flight-mode test (grep "service worker", "cold
  launch", "cold start": no hits). This is the largest offline risk in the current app and it
  is independent of multi-region: on a rock platform, if iOS has evicted the suspended app,
  Guya may not open at all. A service worker that precaches index.html fixes the app shell
  whichever option below is chosen.

CHECKPOINT: Phase 1 complete 2026-11-13T23:10Z

## PHASE 2 — MEASURE — **PARTIAL: SESSION CUT SHORT BY USAGE LIMIT. NOT CHECKPOINTED.**

Raw measurements and citations below are complete as far as they go. NOT done: 2a narrative
reconciliation, the 2d scale tables (i)/(ii)/(iii), and all analysis. A resuming session should
REDO Phase 2 as a whole using these numbers (re-run the two helpers to confirm), then continue.
Desktop Node v24.20.0 (V8) — ratios only, not device milliseconds.

### 2a. Depth pool (raw facts gathered)

- No on-phone backup JSON is reachable in the repo or scratchpad. Stored-pool figures are
  therefore ROADMAP figures (v16.62 §4), marked as such: 134,372 stored points in five datasets
  (legacy_unknown 55,660; brisbane_river 21,126; sunshine_coast 17,806; maroochy_noosa 19,178;
  moreton_bay 20,602) = 3,849.1 KiB; runtime pool after HAT gate + mask = 64,306.
- Processed CSVs in the repo (tracked, `data\`; rows excluding header):
  brisbane_river_flats_v1 68,591 (1,920,560 B); brisbane_river_intertidal_ground_v2 189,187
  (5,297,248 B); maroochy_noosa_bathy_v1 946,877 (26,427,826 B, 25 m grid);
  maroochy_noosa_bathy_v2_appgrade 19,178 (535,179 B, 180 m grid); moreton_bay_flats_v1 33,751
  (945,042 B); sunshine_coast_flats_v1 57,565 (1,611,834 B); sunshine_coast_intertidal_ground_v2
  168,461 (4,716,922 B). No Bargara/Woongarra CSV is in the repo (it exists only inside
  `legacy_unknown` on the phone) — a migration-relevant gap: that region cannot be rebuilt as a
  static file from repo sources without the phone's backup.
- Bytes/point as stored today, RE-DERIVED (scratchpad\mr_encode.js, the exact
  `{datasets:{k:{region,label,importedAt,points,sourceType}}}` shape of index.html:2762, points
  normalised as at :3976): 29.65 B/pt (Moreton flats, 33,751 pts), 29.66 (BR flats, 68,591),
  29.57 (MN v2, 19,178). Roadmap's 29.6 B/pt CONFIRMED.

### 2b. Candidate encodings (measured; B/pt raw | gzip-6 | gzip-9 | brotli)

| encoding | Moreton flats 33,751 pts | BR flats 68,591 pts | MN v2 19,178 pts | precision lost |
|---|---|---|---|---|
| CSV as committed | 28.00 / 6.58 / 6.51 / 4.51 | 28.00 / 6.96 / 6.91 / 4.74 | 27.91 / 8.53 / 8.37 / 5.62 | none |
| JSON as stored today | 29.65 / 6.51 / 6.41 / 4.88 | 29.66 / 6.87 / 6.80 / 5.10 | 29.57 / 8.40 / 8.24 / 6.00 | none |
| backup shape (pretty, points twice) | 141.29 / 15.37 / 14.03 / 10.58 | 141.32 / 16.28 / 14.72 / 11.00 | 141.13 / 19.67 / 18.50 / 12.99 | none |
| compact JSON (integer columns, sorted, lat/lng delta) | 12.00 / 3.88 / 3.82 / 3.44 | 12.01 / 3.98 / 3.93 / 3.59 | 12.90 / 4.74 / 4.74 / 4.35 | none vs stored (1e-6°, 1 cm) |
| binary Int32+Int32+Int16 interleaved | 10.00 / 5.63 / 5.63 / 3.83 | 10.00 / 5.95 / 5.95 / 4.15 | 10.00 / 7.83 / 7.83 / 5.18 | none (0 depth values clipped; Int16 cm caps at ±327.67 m) |
| binary Int32,Int32,Int16 columnar | 10.00 / 4.91 / 4.91 / 3.44 | 10.00 / 5.26 / 5.26 / 3.68 | 10.00 / 7.43 / 7.43 / 4.89 | none |
| binary delta-varint columnar (sorted) | 4.39 / 3.34 / 3.34 / 2.93 | 4.42 / 3.43 / 3.42 / 3.04 | 5.29 / 4.18 / 4.18 / 3.65 | none |
| binary bbox-relative Uint16+Uint16 @1e-5° + Int16 cm | 6.00 / 4.57 / 4.57 / 2.86 | 6.00 / 4.74 / 4.74 / 3.09 | n/a — bbox span 85,903 units > 65,535, needs sub-tiling | max 0.557 m lat, 0.495 m lng; depth 0 cm |

Readings: (1) the lossless delta-varint binary is 4.4–5.3 B/pt RAW — about 6.7× smaller than
today's 29.6 with zero precision loss, and it does not depend on the server compressing it.
(2) Compact integer-column JSON gzips to 3.8–4.7 B/pt — within ~15% of the best binary once
gzipped, and JSON is a content type Pages is MEASURED to gzip. (3) The lossy Uint16 grid buys
nothing over lossless varint. (4) Decode: JSON.parse vs typed-array view was 7×–55× slower on
desktop (ratio only; noisy).

**What Pages actually serves compressed (measured this session with curl against
azmixlabs.github.io/Guya_Wamu, 14 Nov 2026):** `index.html` → `Content-Encoding: gzip`,
745,821 B transferred for 2,368,393 B (local gzip-9 is 730,644, so the edge is not at max level);
`brisbane_bar_tides_2026.json` → gzip; `data/moreton_bay_flats_v1.csv` → gzip, 227,392 B for
945,042 B (6.74 B/pt), `Accept-Ranges: bytes`; `apple-touch-icon.png` → NOT compressed.
Requesting `Accept-Encoding: br` returned the full uncompressed 2,368,393 B — NO brotli.
`Cache-Control: max-age=600` on everything. UNVERIFIED: whether Pages gzips
`application/octet-stream` (.bin) — no such file is deployed to test, and it is undocumented.
Design consequence: either ship a self-compact binary (delta-varint, no server compression
needed) or JSON; do not rely on gzip for a `.bin`.
Aside found while measuring: `data\*.csv` and `apple-touch-icon.png` (2,538,569 B — larger than
index.html) are already publicly served by Pages because the whole repo root is the site.

### 2c. Platform limits (citations gathered)

| limit | value | source | status |
|---|---|---|---|
| Pages published site size | "Published GitHub Pages sites may be no larger than 1 GB." | https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits | documented |
| Pages source repo | "recommended limit of 1 GB" | same | documented (recommendation) |
| Pages bandwidth | "*soft* bandwidth limit of 100 GB per month" | same | documented, soft |
| Pages builds | "*soft* limit of 10 builds per hour"; deployments "timeout if they take longer than 10 minutes" | same | documented |
| Git file size | warning above 50 MiB; "GitHub blocks files larger than 100 MiB" | https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github | documented |
| Pages per-file limit | none stated beyond the Git 100 MiB block | same two pages | inferred |
| WebKit origin quota (iOS 17+) | browser app "up to 60% of the total disk space"; other apps 15%; a Home Screen web app "has the same origin quota and overall quota as when it is opened in a browser app"; overall 80% / 20% | https://webkit.org/blog/14403/updates-to-storage-policy/ (also MDN Storage quotas and eviction criteria) | documented. Consistent with the phone's measured estimate() quota of 39,321.6 MB (roadmap v16.62 §2) |
| Which stores count | "localStorage, Cache API, IndexedDB, Service Worker, and File System" | same | documented. NOTE: localStorage still has its own ~5 MiB per-origin cap (MDN: "Browsers can store up to 5 MiB of local storage … per origin") |
| Eviction | on overall-quota excess or storage pressure; "the data of an origin will be deleted as a whole"; least-recently-used; an origin with an active page may be excluded | webkit.org/blog/14403 | documented. KEY CONSEQUENCE: eviction is WHOLE-ORIGIN — a cached region pack and the user's spots/photos live or die together; public caches cannot be evicted "first" by the browser |
| persist() | default best-effort; "WebKit currently grants a request based on heuristics like whether the website is opened as a Home Screen Web App"; Storage API "fully supported" from Safari 17 / iOS 17 | webkit.org/blog/14403; https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist | documented that it exists and is heuristic; whether it returns true in Guya's home-screen container is UNVERIFIED on device. The app never calls it today |
| 7-day script-writable-storage deletion | applies to "Indexed DB, LocalStorage, Media keys, SessionStorage, Service Worker registrations and cache" after "seven days of Safari use without user interaction on the site" | https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/ | documented |
| Home-screen exemption | "Web applications added to the home screen are not part of Safari and thus have their own counter of days of use. Their days of use will match actual use of the web application which resets the timer. We do not expect the first-party in such a web application to have its website data deleted." | same (web.dev/articles/storage-for-the-web: the policy "does not apply to installed PWAs") | documented, and it covers IndexedDB + SW cache + localStorage alike (one list, one exemption). It is an expectation ("we do not expect"), not a guarantee |
| Service worker in iOS home-screen apps | Web Push for Home Screen web apps (iOS 16.4) is built on "Push API, Notifications API, and Service Workers all working together" | https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/ | INFERRED supported (no page fetched states general reliability). UNVERIFIED on device. Also note Guya has NO web manifest — it is a home-screen app only via `apple-mobile-web-app-capable` (index.html:6) |
| DecompressionStream | Baseline "since May 2023" | https://developer.mozilla.org/en-US/docs/Web/API/DecompressionStream | documented; exact iOS version not retrieved — UNVERIFIED |

### 2d. Scale check — only the runtime ratio was measured; tables NOT written

scratchpad\mr_scale.js replicates the per-LOAD chain (object materialisation as
`depthSamples()`, `buildSampleIndex()` verbatim, the r0 loop verbatim) on 121,520 real points
(Moreton flats + BR flats + MN v2), replicated N times at 1.5° offsets:

| resident points | objs ms | index ms | r0 ms | total | ratio | JS heap |
|---:|---:|---:|---:|---:|---:|---|
| 121,520 | 12 | 19 | 137 | 168 | 1.0× | ≈83 B/pt for the `[lat,lng,d]` arrays + ≈146 B/pt for sample objects + index |
| 243,040 | 23 | 37 | 307 | 368 | 2.2× | same per point |
| 486,080 | 30 | 59 | 594 | 683 | 4.1× | |
| 972,160 | 55 | 121 | 1,109 | 1,285 | 7.7× | |
| 1,944,320 | 335 | 398 | 2,475 | 3,208 | 19.1× | |
| 3,888,640 | 621 | 862 | 5,057 | 6,541 | 39.0× | |

Readings: the chain is linear in RESIDENT points (slightly super-linear past ~1 M), and it runs
on every `poolVersion` bump — so with a single global pool, each region load or eviction costs
time proportional to everything already loaded, not to the region arriving. Resident memory is
≈230 B per point of JS heap (desktop V8), i.e. ≈8× the 29.6 B stored: 1 M resident points
≈ 230 MB — not viable on a phone. Both findings point the same way: residency must be bounded
(per-region indexes built once per region, and a cap on loaded regions), whichever storage
option is chosen. (This omits the per-point `nearestPort` + `maskWater` calls in
`depthSamples()`, so it UNDERSTATES the real chain.)

NOT DONE in 2d: storage / file-count / runtime tables for SEQ complete, QLD coast, national.

## PHASES 3, 4, 5 — NOT STARTED

RESUME: "Resume the multi-region architecture spike. Read scratchpad\multiregion_spike.md. Phases
0 and 1 are checkpointed. Phase 2 is PARTIAL (raw measurements + citations recorded, no
checkpoint): complete 2a/2d and the analysis using the recorded numbers, write its CHECKPOINT,
then continue with Phases 3–5 under the original dispatch rules. Append, don't rewrite."

Findings so far that Phase 3 must carry (so they are not lost):
1. Rule-2 fail-safe needs a three-state `zoneAt` contract consumed at SEVEN null-handling sites
   (index.html:1283, :3044, :3054, :3058, :1309, :1362, :3642), four of which inline the OUTPARK
   HTML — collapse them first as a behaviour-neutral build.
2. FHA has no point lookup at all (no `fhaAt`); "no FHA" is expressed by absence. A "FHA data
   not loaded" state needs an `fhaAt()` + coverage index, not a tweak.
3. Park identity is currently "absence of `plan` ⇒ Great Sandy MP" (:1280) and rod/hook text is
   keyed on zone type alone (:1223-1225). Both must become (park, zone type) before any third
   park's polygons are added.
4. WebKit eviction is whole-origin: caching public region data in the same origin does not put
   user data at extra eviction risk from quota (60% of disk), but nor can it be sacrificed
   first. `navigator.storage.persist()` is never called today.
5. No service worker: cold launch with no signal is UNVERIFIED and likely unreliable today.
6. Backup must stop carrying public depth data once regions are partially loaded, or a restore
   deletes unloaded regions (:3303-3307 whole-store replace).
7. Bargara/Woongarra depth data has no source CSV in the repo — it exists only in the phone's
   `legacy_unknown` dataset.

---

## PHASE 2 — COMPLETION (same session, resumed after the usage limit reset)

This section completes Phase 2. The "PARTIAL / NOT CHECKPOINTED" banner, the "PHASES 3, 4, 5 —
NOT STARTED" marker and the RESUME text above are SUPERSEDED by this section and the checkpoint
at its end; the measurements and citations above stand unchanged and are not repeated.

### 2a (completed). Current pool — reconciliation

| quantity | value | source |
|---|---:|---|
| stored imported points (phone) | 134,372 in 5 datasets | ROADMAP v16.62 §4 (no backup file reachable this session) |
| stored bytes | 3,849.1 KiB = 3,941,478 B | ROADMAP v16.62 §4 |
| derived B/pt | 3,941,478 ÷ 134,372 = **29.33 B/pt** whole-store; per-dataset 28.92–29.66 | roadmap table; the 28.92 outlier is `legacy_unknown` |
| re-derived B/pt (this session, repo CSVs through the app's own normalisation and storage shape) | **29.57–29.66** | scratchpad\mr_encode.js |
| runtime pool after HAT gate + land mask | 64,306 (47.9% of stored) | ROADMAP v16.62 §4 |
| dead weight in storage | 70,066 pts ≈ 2,003.5 KiB (52%) | ROADMAP v16.62 §4 |

The roadmap's 29.6 B/pt is confirmed to within 0.1 B/pt for region-tagged datasets. More than
half of what occupies localStorage never reaches the runtime pool: a static region file built
offline would carry only survivors, so the comparable cost of today's five regions is 64,306
points, not 134,372.

### 2b (completed). Large-sample row and compression level

Fourth sample, `data\maroochy_noosa_bathy_v1.csv`, 946,877 points on the native 25 m grid
(background run, finished after the partial section was written):

| encoding | raw / gzip-6 / gzip-9 / brotli (B/pt) |
|---|---|
| CSV as committed | 27.91 / 5.53 / 5.29 / 2.89 |
| JSON as stored today | 29.57 / 5.43 / 5.18 / 3.01 |
| binary Int32,Int32,Int16 columnar | 10.00 / 2.71 / 2.71 / 1.83 |
| binary delta-varint columnar | **4.08 / 0.93 / 0.90 / 0.81** |

Decode ratio at this size: JSON.parse 295.7 ms vs typed-array scan 6.2 ms = 47.8× (desktop,
ratio only). A regular native grid compresses far better than thinned app-grade data (delta-
varint + gzip: 0.93 vs 3.3–4.2 B/pt) — relevant if the casting-band strategy (roadmap v16.47
series: full 25 m resolution inside a 200 m shoreline band) becomes the region-file standard.

Pages compression level, inferred: `moreton_bay_flats_v1.csv` is served as 227,392 B; local
`gzip -1` gives 282,476, `-6` 223,265, `-9` 221,000. The edge sits between levels 1 and 6
(INFERRED ≈ level 4–5). Budget on gzip-6 figures plus ~2%.

**Encoding conclusion.** Lossless delta-varint columnar binary: 4.1–5.3 B/pt with no reliance on
server compression, no precision loss against what the app stores today (1e-6°, i.e. ≤0.11 m,
and 1 cm), ~7–50× cheaper to decode than JSON. Integer-column JSON is the fallback if a binary
build pipeline is judged too heavy: 12 B/pt at rest, ~3.9–4.7 on the wire. Either is 2.5–7× better
at rest than today. The lossy 16-bit grid is rejected: no gain over lossless.

### 2c (completed). Limits — what binds, in one place

- **GitHub Pages:** 1 GB published site (documented), 100 MiB per file (documented Git block),
  100 GB/month soft bandwidth (documented), no brotli and `max-age=600` (measured). One user
  re-downloading every region monthly at national scale (~70 MB, see 2d) is <0.1% of bandwidth.
  Pages is not the binding constraint at any scale considered.
- **localStorage:** ~5 MiB per origin (MDN documented; phone bracket [4,995.5, 5,919.6) KiB
  measured in roadmap v16.62). THE binding constraint today.
- **IndexedDB / Cache API on iOS 17+:** origin quota up to ~60% of disk for a browser app and
  for a Home Screen web app (documented, webkit.org/blog/14403); the phone reported 39.3 GB.
  Not binding at any scale considered. Eviction is whole-origin, LRU, under storage pressure
  (documented) — the design cannot make public data "evict first".
- **7-day rule:** documented to cover IndexedDB, localStorage and service-worker registrations
  and caches alike, and documented NOT to be expected to fire for a home-screen web app that is
  actually used ("their own counter of days of use"). The exemption therefore covers IndexedDB
  and Cache API on the same footing as localStorage. Residual risk: it is a stated expectation,
  not a guarantee, and Guya opened in a Safari TAB (the wrong container) has no exemption.
- **persist():** exists on iOS 17+; grant is heuristic and home-screen status is the named
  heuristic (documented). Result in Guya's container: UNVERIFIED — must be probed on the phone.
- **Service worker in a home-screen app:** INFERRED available (Web Push for home-screen apps
  depends on it since iOS 16.4); general reliability and whether it serves a cold offline launch
  for a NO-MANIFEST `apple-mobile-web-app-capable` app: UNVERIFIED — must be probed on the phone.
- **Aaron's iOS version:** not recorded anywhere this session could read. Every "iOS 17+"
  statement above is conditional on it. UNVERIFIED.

### 2d (completed). Scale check

**Density models (both from roadmap figures).**
- D1 "app-grade region": the CSV importer thins to `MAXP=25000` (index.html:3979); the five
  stored datasets average 134,372 ÷ 5 = 26,874 (one is a 55,660-pt legacy blob). Use 25,000
  stored / ~12,000 surviving per region (47.9% survival, v16.62 §4).
- D2 "casting band at native 25 m" (roadmap ~:8624-8632): a 200 m band at 25 m spacing =
  200 × 1000 ÷ 625 = **320 points per km of fishable shoreline**. Roadmap's own check: ~55 km
  of Mudjimba→Noosa coast + river corridors ≈ 11 km² ≈ 17,600 pts.

**Shoreline lengths.** SEQ is built from region counts, not length. QLD mainland coastline
≈ 6,970 km and Australian mainland ≈ 35,900 km are FROM MEMORY (Geoscience Australia figures),
not looked up — the dispatch limits network use to platform docs. UNVERIFIED; estuary and river
banks are excluded, so a ×2 allowance is applied to D2. Treat (ii) and (iii) as order-of-
magnitude only.

**Bytes per point used:** today 29.6 (localStorage JSON); binary 4.5 raw (mid of 4.1–5.3);
resident JS heap ≈ 230 B/pt and load chain 168 ms per 121,520 pts = 1.38 µs/pt on desktop
(mr_scale.js; ratio basis only).

| | (i) SEQ complete | (ii) QLD coast | (iii) national Hold item |
|---|---|---|---|
| scope | Woongarra, Moreton/Redcliffe, Bribie, SC, BR, Gold Coast + existing Maroochy/Noosa = 7 regions | ~6,970 km mainland × 2 for estuaries | QLD + NT + WA + part NSW ≈ 25,000 km × 2 (guess) |
| points | D1: 7 × 25,000 = **175,000** stored (≈84,000 surviving). D2: 7 × ~17,600 = ~123,000 | D2: 6,970 × 2 × 320 ≈ **4.5 M**. D1 cross-check: 6,970 ÷ 55 km ≈ 127 regions × 25,000 = 3.2 M | D2: 25,000 × 2 × 320 ≈ **16 M** |
| at today's 29.6 B/pt | 5.18 MB — **exceeds the ~5 MiB localStorage cap before any user data** | 133 MB | 474 MB |
| as binary at 4.5 B/pt | 0.79 MB | 20 MB | 72 MB |
| vs Pages 1 GB | 0.08% | 2% | 7% (as CSV at 28 B/pt: 448 MB = 45% — binary matters here) |
| vs IndexedDB quota (39.3 GB measured) | negligible | 0.05% | 0.2% |
| file count | 7 depth files + manifest (+ masks) | ~130 region files, or ~260–400 quarter-degree tiles along the coast | ~500 regions or ~1,000–1,500 tiles — each well under 100 MiB |
| zone data | unchanged: both parks already baked (Moreton Bay MP reaches −27.93; the Gold Coast south of it is outside marine-park zoning) | adds GBR Coast MP and the GBRMP inshore zoning. Scaling Great Sandy's 913 kB per ~1.5° of coast over ~17.5° of latitude: **≈11 MB of zone JSON at current precision, ≈7 MB at 5 dp** (ESTIMATE, UNVERIFIED — real GBR polygon counts not measured). Cannot be baked into index.html | plus NT / WA / NSW estates, each a separate source and schema (roadmap Hold note) |
| all-resident heap at 230 B/pt | 40 MB — tolerable | **1.0 GB — impossible on a phone** | 3.7 GB — impossible |
| load chain if one global pool (desktop ms, ratio basis) | 175,000 × 1.38 µs ≈ 240 ms per pool change; 1.4× the 121k baseline | ≈6.2 s per pool change (37×) | ≈22 s (130×) |
| `zoneAt` linear scan | 178 features, as now | ~2,000–2,500 features if all resident: ~12–14× per call, and `renderDepths` calls it per pin (:1366), `scanlineMask` visits every feature per row (:2078) | worse again |
| what binds first | **storage only.** Runtime and residency are fine with everything loaded | **residency** (heap + per-load chain), then zone-corpus size in the single file, then the manual import path (127 field imports) | same as (ii), plus data availability and per-state zoning integration — not an architecture problem |

**The reading that drives Phase 3.** The three ceilings in roadmap v16.62 §8 do not bind at the
same scale:

1. At SEQ-complete — the only scale with a near-term plan — the ONLY thing that breaks is the
   5 MiB localStorage cap. 175,000 points resident costs ~40 MB of heap and a ~1.4× load chain.
   Viewport-driven loading buys nothing here.
2. Viewport/region-scoped loading becomes mandatory somewhere between ~500,000 and 1 M resident
   points (115–230 MB heap; 0.7–1.3 s desktop load chain, several seconds on the phone) — i.e.
   roughly 20–40 app-grade regions, well past SEQ.
3. Zones hit the single-file ceiling at the FIRST new marine park, independently of depth:
   +0.9 MB per Great-Sandy-sized park on a file whose every cold load is already 746 kB gzip.
4. The import-path ceiling ("unworkable for fifty") binds on human effort, not on bytes, and is
   the only one of the three that a storage migration alone does nothing for.

CHECKPOINT: Phase 2 complete 2026-11-14T03:02Z


## PHASE 3 — DESIGN OPTIONS

Four options: the three named, plus D, added because the evidence asks for it (see D).

Terminology. "Pack" = one static, versioned, public data file for one region and one kind of
data (depth, zones, FHA, land mask, tide table). "Installed" = present and hash-verified in
on-device storage. "Resident" = decoded in memory. "Assessed" = inside an extent for which the
app's zone (or FHA) knowledge has been checked complete against the official source.

### 3.0 Requirements common to EVERY option

These are stated once and referenced by each option. None is optional.

**3.0.1 A finding that precedes the options — the app already makes a false OUTPARK claim
today.** `zoneAt` returns null for any point outside the 178 baked polygons, and all seven sites
in 1e then assert "Outside the marine park boundary". The baked corpus is Great Sandy (north
limit −24.498, Baffle Creek) and Moreton Bay (south limit −27.933) only. CLAUDE.md records that
the Great Barrier Reef Coast Marine Park begins north of Baffle Creek. So a tap anywhere north
of about −24.5 — Agnes Water, Gladstone, Cairns — renders the OUTPARK card for water that is
inside a marine park the app holds no data for. Likewise south of the Queensland border (NSW
parks). The map opens at Redcliffe and nothing stops a pan north. This is a rule-2 defect in the
shipped build, code-derived (index.html:1335 + :1283 + the measured ZONES bbox in 1b), not a
future risk. It has not bitten because every field session has been inside the two parks or the
verified-outside Sunshine Coast gap. The fail-safe below fixes it; it should not wait for
multi-region.

**3.0.2 Rule 2 fail-safe — a three-state lookup backed by a baked coverage index.**

Data: `ZONE_COVERAGE`, a small table BAKED into index.html (never fetched, never cached, so
the fail-safe cannot itself be "not loaded"). One row per pack:
`{id, park, extent, source, checked, baked:true|false}` where `extent` is a simple polygon (or a
short list of rectangles) inside which that pack is COMPLETE — every legislated polygon of
every marine park intersecting the extent is in the pack. A verified-empty area is a row too:
e.g. `{id:'seq_gap_caloundra_noosa', park:null, extent:…, source:'Moreton Bay MP northern
boundary at Caloundra; no state marine park to Great Sandy southern boundary', checked:'…'}`
with zero polygons. "No marine park here" thus becomes a positive, sourced, dated assertion
rather than the absence of a hit.

Lookup: a new `zoneLookup(lat,lng)` returning one of four states:

| state | condition | card |
|---|---|---|
| `zone` | every coverage row containing the point is installed; ≥1 polygon contains it | the zone card (most protective first — see 3.0.3) |
| `outside` | every coverage row containing the point is installed; ≥1 row contains it; no polygon contains it | the OUTPARK card, exactly as today |
| `notloaded` | ≥1 coverage row containing the point is NOT installed (never downloaded, failed hash, evicted, or still loading at boot) | "Zone data not loaded here — zone unknown. Confirm officially before fishing." + the official link for that row's park + how to download. If an installed row already yields a hit, it is shown beneath as "At least:" — a partial MNP is still a no-take warning — but the card stays headed unknown |
| `unassessed` | no coverage row contains the point | "Guya has no zone data for this area — zone unknown. A marine park may apply. Confirm officially before fishing." |

OUTPARK is reachable from exactly one branch, and that branch requires a positive coverage hit.
A parse failure, an empty table or an exception in `zoneLookup` returns `unassessed`.

Where it sits: `zoneAt()` keeps its current body and meaning — "most-protective polygon among
resident features, or null" — so CLAUDE.md rule 3 and every differential test against it stay
valid. `zoneLookup()` wraps it. Every site in the 1e table switches from testing `zoneAt()`'s
null to consuming `zoneLookup()`: `zoneCard` :1283; map handler :3044, :3054, :3058; `fhaCard`
:1309; pin popup :1362 and list chip :1373; `zoneTag` :3642. Pin ring colour :1367 treats
`notloaded`/`unassessed` as its own colour, not as "not no-take". The water proxy
`inWaterFast(shadeMaskFeats(),…)` (:3054, :3074, :3919) is cosmetic but must not read
"not loaded" as "land": in `notloaded`/`unassessed` areas it defers to the `r.near` branch
that already exists at :3054. No direct caller of `zoneAt()` may render a claim; that becomes
a review rule.

**3.0.3 Overlap across pack boundaries (rule 3).** `zoneLookup` runs ONE scan over the union of
resident features from every installed pack covering the point, with the single existing rank
comparison (`ORDER.indexOf`, MNP > CPZ > HPZ > GUZ). There is never a per-pack answer that is
then merged, and never first-pack-wins. Three additions the current code does not need:
- A feature present in two packs (shared boundary polygons) is de-duplicated by a stable
  `uid` = park + zid + name, since `zid` alone collides across plans (1b).
- Rank ties across PARKS are real, not hypothetical: the state GBR Coast MP and the
  Commonwealth GBRMP overlap in tidal waters. On a tie the card lists every top-rank hit with
  its own park and limits; the headline is the most restrictive of them.
- An unrecognised zone type ranks MOST protective and renders "unrecognised zone type — treat
  as restricted until confirmed", reversing today's `STYLES[p.zt]||STYLES.GUZ` (:1280) and
  `rank=(i<0?98:i)` (:1335), which fail towards least restrictive.
Whole polygons are stored per pack — never clipped to a pack or tile edge. Clipping inserts
vertices the legislation does not contain and moves `pir()`'s float operands at every seam.

**3.0.4 Park identity.** Every zone record carries a REQUIRED `park` code, stamped at pack build
time from the source dataset — including the 104 Great Sandy features that today rely on
`p.plan||'Great Sandy MP'` (:1280). A baked `PARKS` table holds, per park: display name, plan /
legislation, official link, and `limits` per zone type with `verified:{date,source}`. `STYLES`
(:1221-1226) keeps colours only; the rod/hook sentence is built from `PARKS[park].limits[zt]`.
No entry, or no `verified` → the card prints "Limits not confirmed for this park — check the
official source" and NO figures. That is CLAUDE.md rule 5 expressed in data: Great Sandy and
Moreton Bay carry the two verified figures; every other park starts unconfirmed. A record with
a missing or unknown `park` renders "park unknown", never a default.

**3.0.5 FHA: a real lookup and its own not-loaded state.** Add `fhaAt(lat,lng)` (point-in-polygon
over FHA features with a bbox pre-reject) and an `FHA_COVERAGE` table with the same four states.
The card ALWAYS prints an FHA line: the FHA block(s); or "No declared Fish Habitat Area at this
point (data current to Aug 2023)" — only inside assessed, installed coverage; or "FHA data not
loaded here"; or "FHA not assessed for this area". The baked dataset's extent is lon 151.9–153.7,
lat −28.2 to −24.4 (roadmap :10211), so today everything outside that box is `unassessed`. This
removes the dependency on Leaflet's canvas hit-test for the FHA block and with it backlog F7.
The overlay layer and its toggle stay as drawing only.

**3.0.6 Privacy (the dispatch's "hard rule 5"; CLAUDE.md rule 6).** In every option the only new
network traffic is same-origin GET of static public files. Nothing user-created is sent, there
is no query string carrying position, and no option syncs user data. One exposure exists and
should be decided, not discovered: a request for a region file tells GitHub/Fastly which region
the device is interested in. Explicit download (D) reveals it once, from wherever the download
is done; viewport-driven fetching (A, C) reveals it continuously as the map moves, at region
grain (A) or tile grain (C). The same class of signal already goes to the imagery servers on
every pan (:1241, :1243, :1263), so this is not a new category — but it is a reason to prefer
explicit download.

**3.0.7 Two CLAUDE.md invariants every option except B touches.** "One `index.html`, … no build
step" and "Wind via Open-Meteo. No other backend calls at runtime." Static packs are extra
files and extra runtime fetches; a service worker must be its own file (it cannot be inlined).
Only Aaron edits CLAUDE.md. The honest restatement would be: one app file, static same-origin
data files, one service-worker file, no third-party backend.

**3.0.8 Migration and backup, common shape.** Existing `woongarra_imported_v2` datasets are
copied — not moved — into IndexedDB as LOCAL datasets (user-imported; includes `legacy_unknown`,
whose Bargara data has no source CSV in the repo). The localStorage copy stays until a later,
separate build removes it. Backup: `importBackup` keeps accepting the version:2 shape forever
(`datasets` object, or flat `imported` → `legacy_unknown`, as :3283-3293 do now) and writes it
to the local-dataset store. A new version:3 export drops the duplicated flat `imported` array
and the pretty-printing, carries LOCAL datasets in full, and carries installed PACKS as a list
of ids only — public data is re-downloadable and has no place in a personal backup.

---

### Option A — static region packs on Pages + IndexedDB cache + viewport-driven loading + service worker (the named hypothesis)

**Shape.** `regions/manifest.json` lists packs: id, kind, extent, bytes, SHA-256, version, port,
sourceType, maskExempt. The app fetches packs for regions intersecting the viewport, stores the
bytes in IndexedDB, decodes to typed arrays. A service worker precaches the app shell.

- **Capacity / what binds first.** Pages 1 GB ÷ 4.5 B/pt ≈ 220 M points (2d: national ≈ 72 MB).
  Storage never binds. What binds first is the HUMAN pipeline — producing, auditing and
  class-9-checking each region's LAS — then, for zones, per-state sourcing.
- **Runtime.** Resident = packs intersecting the padded viewport, LRU-capped (≈250,000 points:
  2× today's 121k baseline, ~60 MB heap by 2d). Keep ONE pool and the existing IDW code path;
  bound it by the cap. Make the pool cheap to rebuild by moving work to pack BUILD time: apply
  the HAT gate and land mask offline (packs hold survivors only — removes the per-point
  `nearestPort` + `maskWater` at :2929/:2934) and store precomputed `r0` (the r0 loop is 82% of
  the measured chain: 137 of 168 ms). `buildShade`'s pixel loop is unchanged. `_idwCache` must
  become `poolVersion`-keyed and lose the −24.85° anchor (1c). Scanline mask: pass it only the
  zone features whose bbox intersects the grid rect — an exact pre-filter, cost then tracks the
  view not the corpus. **v16.67 §E answer: canvas rasterisation does NOT become the right call.**
  Its objection to scanline was corpus growth; bbox-scoping the feature list removes that growth
  while keeping the "0 diff or it is a bug" gate. Rasterisation stays the fallback for a single
  view containing an extreme edge count (GBR reef mosaics) — measure before reopening.
- **Import path.** A region = a commit: build pack, add manifest row, push. No field procedure,
  no 25,000-point cap, no force-close ritual.
- **Offline.** This is A's weak point. Viewport-driven fetching works only where there is
  signal — the opposite of where the data is needed. A must therefore ALSO have an explicit
  "Download this region" action, at which point the implicit path is a convenience with its own
  failure states. Panning into an uncached area must show a persistent, specific banner: "Depth
  data for <region> is not on this phone — connect and download", and the zone state from 3.0.2.
  Without it, an uncached region is indistinguishable from "no survey here".
- **Durability on iOS.** Packs in IndexedDB; exempt from the 7-day rule as a home-screen app
  (2c); evictable only whole-origin under storage pressure, i.e. together with the logbook.
  The ritual changes: each pack has a manifest SHA-256, verified on install and re-verified at
  boot (`crypto.subtle.digest`); a failure demotes the pack to "not installed" — visible, and
  never a false claim. Force-close/reopen is no longer needed for public data.
- **Rule 2 fail-safe.** 3.0.2. Extra exposure specific to A: `notloaded` becomes a state the
  user enters by PANNING, so it is common, not exceptional, and a fetch that completes mid-tap
  must not change a card already on screen.
- **Overlap.** 3.0.3 — with one more hazard: under LRU, the pack holding the more protective
  polygon can be evicted while its neighbour stays. Coverage rows make that a `notloaded`
  result rather than a wrong zone, provided eviction updates installed/resident status
  atomically with the feature list. Simplest safe rule: zone packs are never LRU-evicted.
- **Park identity.** 3.0.4, `park` stamped in the zone pack; `PARKS` baked.
- **Privacy.** 3.0.6 — continuous region-grain signal.
- **Migration.** 3.0.8, then per region: when a published pack supersedes a local dataset the
  user is OFFERED removal of the local copy; never automatic. Rollback: the localStorage copy
  until its removal build; packs are re-downloadable.
- **Effort.** ~14 one-variable builds; on-phone gates on 9 (probe, SW, IDB migration, async
  boot, pack install, viewport loader, eviction, backup v3, localStorage removal).

### Option B — IndexedDB migration only; zones stay baked; CSV import stays

**Shape.** `datasets` moves from `woongarra_imported_v2` to an IndexedDB store, one record per
region. Nothing is fetched. Zones, FHA, masks and tides stay in index.html.

- **Capacity.** Storage stops binding (39 GB quota). Next to bind: the single file, at the first
  new marine park (+~0.9 MB per Great-Sandy-sized park, 1b); then residency at ~0.5–1 M points
  (2d); and the import path the whole way.
- **Runtime.** Unchanged — everything resident. Fine to SEQ-complete (175,000 points, 1.4×).
  Boot becomes asynchronous: `datasets` is read synchronously at :2715 and flattened at :2756
  today; with IndexedDB the pool arrives after first paint, so `rebuildImportedFlat()` +
  `buildShade()` must run on arrival and every consumer must tolerate an empty pool at boot.
  That is B's main code risk.
- **Import path.** Still a field procedure: CSV onto the phone, pick a region, import. The
  25,000 cap (:3979) exists because of the storage ceiling and could be raised. Adding a region
  with a new park still needs an index.html build.
- **Offline.** Best of all options: nothing is ever fetched, so nothing can be "not cached".
  A region is on the phone or it was never imported.
- **Durability.** An IndexedDB transaction's `oncomplete` is a real commit signal, unlike the
  in-memory localStorage read-back (:2765-2767). Write → complete → re-read in a NEW
  transaction → compare count and hash. Retires the ritual for imported depths. Whether
  WebKit's default transaction durability is fsync-strict is UNVERIFIED; the boot receipt
  (:2810) is kept, pointed at IndexedDB.
- **Rule 2 fail-safe.** Zones are never unloaded, so `notloaded` cannot occur — but 3.0.1's
  false OUTPARK north of −24.5 remains unless 3.0.2 is built anyway. B does not excuse it.
- **Overlap / park identity.** Unchanged code; 3.0.4 still required before any third park.
- **Privacy.** No new traffic at all.
- **Migration.** 3.0.8 exactly. Smallest migration of any option.
- **Effort.** ~5 builds (probe, copy-to-IDB, read-from-IDB with async boot, backup v3,
  localStorage removal); on-phone gates on all 5.

### Option C — fixed-grid tiles (z/x/y or geohash), lazily fetched and cached

**Shape.** Depth and zone data cut into a fixed grid — e.g. slippy z10 (≈35 × 39 km at −27°) —
one file per tile per layer; a tile manifest is the coverage index.

- **Capacity.** As A. File count is the new pressure: ~260–400 files for QLD, 1,000–1,500
  national (2d), all rewritten on any pipeline change, all carried in git history.
- **Runtime.** The best residency story: bounded, uniform load units; resident = tiles under
  the view; a per-tile index never exceeds a small fixed size. Cross-tile IDW needs neighbour
  tiles resident (120 m reach).
- **Import path.** A commit, as A, plus a tiler in the build chain.
- **Offline.** "Download the tiles in this view" — the same interaction as the existing Esri
  tile saver (:4185-4203), which the user already knows. An uncached tile is a visible square
  gap: honest, but fine-grained enough to be missed at a platform edge.
- **Durability.** As A.
- **Rule 2 fail-safe.** The tile manifest gives the coverage states almost for free: tile
  listed + installed, listed + not installed, not listed. That is C's real attraction.
- **Overlap — and why C is wrong for ZONES.** A zone polygon spans many tiles. Either each tile
  stores every whole polygon touching it — Great Sandy's four types hold 23,980 vertices in 104
  features, and the large MNP/GUZ polygons would be duplicated into dozens of tiles — or
  polygons are clipped to tile edges, which manufactures vertices the legislation does not
  contain and puts a seam through every boundary crossing (3.0.3). Neither is acceptable for
  the one dataset carrying the legal weight. Regions also are not spatially exclusive:
  `sunshine_coast` (topographic) and `maroochy_noosa` (bathymetric) overlap on the ground, and
  `sourceType` and the mask exemption are REGION properties (:1969, :2753). A tile would need
  per-layer or per-point flags to keep "never label topographic data as depth" true.
- **Park identity.** 3.0.4; per-feature, so it survives tiling.
- **Privacy.** 3.0.6 — the finest-grained signal of any option.
- **Migration.** 3.0.8; existing datasets stay as local datasets, untiled.
- **Effort.** ~17 builds plus a tiler; on-phone gates on ~10.

### Option D — explicit region library: static packs, downloaded deliberately, zones resident whenever installed (added)

**Why it is added.** Phase 2d shows viewport-driven loading solves a problem (residency) that
does not exist until ~0.5–1 M points, while 1f and the field case show that fetching on pan is
the wrong trigger for an app used where there is no signal. A's hypothesis bundles two separable
ideas: static packs with a commit as the import path (needed now) and viewport-driven fetching
(not needed, and harmful offline). D takes the first and replaces the second with an explicit
library. It is A's storage and import model with B's offline certainty.

**Shape.**
- A "Regions" panel lists every pack in the manifest with size, date and state: Not downloaded
  / Downloading / On this phone ✓ / Update available / Failed check. Download and Remove are
  explicit buttons. The manifest is refreshed when online; the last-good copy is kept.
- **The two home parks stay BAKED in index.html.** Great Sandy and Moreton Bay zones, the SEQ
  FHA set and their coverage rows remain in the file exactly as now. Home-water zone calls
  never depend on a download, a cache or IndexedDB. Packs carry only ADDITIONAL parks and all
  depth data. Rule-2 regression risk at home is therefore nil by construction.
- **Zone packs: installed ⇒ resident, always.** Loaded from IndexedDB at boot, never
  viewport-scoped, never LRU-evicted. Until the boot load completes, their coverage rows read
  `notloaded` ("loading…"). Cost: a QLD-scale zone corpus resident in memory — acceptable if
  decoded to flat typed arrays; revisit only if a boot-time measurement says otherwise.
- **Depth packs: installed ⇒ resident, until residency binds.** Start with everything installed
  being resident (correct to ~250,000 points). Add viewport-scoped RESIDENCY — from local
  storage, no network — as a later, separately gated build when an installed-set measurement
  shows it is needed. That later step is A's loader with the network removed from the pan path.
- A service worker precaches the app shell (index.html, icon), network-first with cache
  fallback, so a build update still arrives promptly online and a cold launch works offline.

- **Capacity / what binds first.** As A: Pages and IndexedDB never bind; the human pipeline does.
- **Runtime.** Identical to today until the residency build. Pack build-time HAT/mask/r0
  precompute (as A) makes installs cheap and shrinks the per-point resident cost.
- **Import path.** A commit for published regions. The CSV importer stays for private or
  experimental data, writing local datasets.
- **Offline.** Explicit and inspectable before leaving home: the panel says what is on the
  phone. Panning into an area whose pack exists but is not installed shows the persistent
  banner; an area with no pack at all shows nothing for depth and `unassessed` for zones.
- **Durability.** As A (hash-verified at install and at boot). Whole-origin eviction is the
  residual risk; `navigator.storage.persist()` is requested once and its result shown in the
  panel. Ritual retired for packs; unchanged for user data.
- **Rule 2 fail-safe.** 3.0.2. `notloaded` arises only from: not downloaded, failed hash,
  evicted, or boot still loading — never from panning. Fewest paths into the state of any
  network option, and none of them at home.
- **Overlap.** 3.0.3; with zones never evicted, the LRU hazard in A does not exist.
- **Park identity.** 3.0.4.
- **Privacy.** 3.0.6 — one request per deliberate download.
- **Migration.** 3.0.8.
- **Effort.** ~12 builds; on-phone gates on 7.

### Comparison

| | A viewport + packs | B IDB only | C tiles | D explicit library |
|---|---|---|---|---|
| fixes the 5 MiB ceiling | yes | yes | yes | yes |
| region = a commit | yes | no | yes | yes |
| new park without growing index.html | yes | no | yes (badly, for zones) | yes |
| works where there is no signal | only if pre-downloaded | always | only if pre-downloaded | by design |
| ways to reach "zone data not loaded" | panning, eviction, failure | none | panning, eviction, failure | failure or never downloaded |
| rule-2 risk at HOME waters | new (zones leave the file) | none | new | none (home parks stay baked) |
| residency bounded | yes | no | yes (best) | later build, when measured |
| new files / CLAUDE.md invariants touched | yes | no | yes (hundreds of files) | yes |
| builds (on-phone gated) | ~14 (9) | ~5 (5) | ~17 (10) | ~12 (7) |

CHECKPOINT: Phase 3 complete 2026-11-14T03:06Z


## PHASE 4 — RECOMMENDATION AND BUILD SEQUENCE

### 4.1 Recommendation

**Option D, staged — with the rule-2 fail-safe and park identity built FIRST and independently,
B's IndexedDB migration as D's storage step, A's viewport scoping deferred behind a
measurement, and C rejected for zones.**

Why, against the evidence:

1. **The most urgent work is not storage.** The shipped build asserts "Outside the marine park
   boundary" for any tap north of about −24.5 or south of the border (3.0.1), prints rod/hook
   limits keyed on zone type alone (1d #7), and has no FHA lookup (1e). All three are rule
   defects that exist today, need no new architecture, and are prerequisites for every option.
   They go first.
2. **At the only scale with a plan, storage is the single binding ceiling** (2d): SEQ-complete
   is ~175,000 points, 5.18 MB at today's encoding against a ~5 MiB cap, but only ~40 MB of
   heap and a 1.4× load chain. Viewport-driven loading solves a problem that starts at
   roughly 0.5–1 M resident points.
3. **Fetch-on-pan is the wrong trigger for this app.** The field case has no signal (roadmap
   v16.62 §7 rejected Google Drive on exactly this ground). Any design must have an explicit
   download; D makes that the only path, which also removes panning as a way into "zone data
   not loaded" and reduces the location signal to one request per deliberate download.
4. **Home-water zone calls must not acquire new failure modes.** D keeps Great Sandy and
   Moreton Bay baked in index.html. SEQ-complete needs NO zone pack at all: Bribie and the
   northern Gold Coast are inside the baked Moreton Bay MP extent (to −27.93), and the rest of
   the Gold Coast is outside marine-park zoning — a verified-empty coverage row. The first
   zone pack is only needed for the first region north of Baffle Creek.
5. **"A region costs a commit" is the one ceiling B cannot lift** (2d reading 4), and it is the
   one that decides whether "many more areas" is tractable. Static packs deliver it.
6. **C's tile seams cut the legally load-bearing dataset** and its tiles cannot carry
   region-level `sourceType` cleanly where regions overlap (3, Option C). If depth residency
   ever needs a finer unit than a region, tiling DEPTH inside a pack is a later, local decision.

What the recommendation costs: two CLAUDE.md invariants change (3.0.7 — Aaron's edit, by
hand), the repo gains a `regions/` directory and a `sw.js`, and the app gains its first
asynchronous boot path.

### 4.2 Build sequence

Model column follows roadmap :10971 ("Sonnet default; Fable 5 for long autonomous runs /
root-cause work"); Opus is proposed where a build is short but rule-critical. That middle tier
is this spike's suggestion, not a quoted project rule. Every build keeps the standing
discipline: `node --check` both blocks, Leaflet SHA pin, `zoneAt()` + green-zone drag
safeguard intact, build string bumped, push + Pages run confirmed.

**Stage 0 — find out what the phone will do (no app change)**

| # | build | scope / files | vm harness proves | only the phone proves (gate) | STOP conditions | model |
|---|---|---|---|---|---|---|
| T0 | Cold-launch test — NO BUILD | Aaron: open Guya, force-close, flight mode ON, launch from the home-screen icon. Repeat after the phone has been idle overnight | nothing | whether today's app opens with no signal at all | none — record the result either way | — |
| P0 | Storage/offline PROBE | `storage_check.html` + a probe service worker registered ONLY under a sub-scope (`probe/sw.js`, scope `…/Guya_Wamu/probe/`) so it can never control index.html | syntax; that the probe SW's scope string cannot match the app URL | in the HOME-SCREEN container: iOS version; `estimate()`; `persisted()` then `persist()` result; IndexedDB write of a 20 MB blob, read back in a new transaction, and again after force-close (count + SHA-256); Cache API put/match after force-close; SW registers, controls the probe page on 2nd launch, and serves it in flight mode from cold; `crypto.subtle` and `DecompressionStream` present | STOP if the probe SW's scope would cover `index.html`; STOP if any probe write touches a `woongarra_*` key or either existing database | Sonnet |

P0 resolves every device-UNVERIFIED limit in 2c. Its results choose between S1-as-designed and
the fallbacks in Phase 5.

**Stage 1 — rule fixes on the current single file (no storage or network change)**

| # | build | scope / files | vm harness proves | phone gate | STOP conditions | model |
|---|---|---|---|---|---|---|
| R1 | Collapse the OUTPARK copies | index.html: :3044 and :3058 call `zoneCard()` / one shared composer; no wording change | card HTML byte-identical pre/post over a fixed grid of taps (in-zone, out-of-zone, both shading states, FHA tap) | smoke only | any HTML difference | Sonnet |
| R2 | `zoneLookup()` + baked `ZONE_COVERAGE` | index.html: coverage rows for Great Sandy, Moreton Bay and the verified-empty SEQ gaps; all seven 1e sites consume the four states; `unassessed` card. All rows are baked, so `notloaded` is unreachable in this build | `zoneAt()` unchanged on ≥100,000 random points; every point inside coverage renders byte-identical HTML to R1; every point outside renders the `unassessed` card; forced exception → `unassessed` | Hays Inlet (zone), Mooloolaba (outside, assessed), a pan to Agnes Water or Gladstone (unassessed) | STOP if any coverage extent or verified-empty row lacks an official source Aaron has confirmed (rule 5); STOP if any inside-coverage card changes | Opus |
| R3a | Park identity in data | index.html: `park` stamped on all 178 features; baked `PARKS` table; rules sentence built from `PARKS[park].limits[zt]`; no-entry → "limits not confirmed", no figures | geometry arrays hash-identical to pre-build (coordinates untouched); card HTML identical for both existing parks; a synthetic third-park feature renders "not confirmed" with no figures | zone card at Bargara and at Redcliffe reads as before | STOP if any coordinate byte changes; STOP if the two verified figures do not match CLAUDE.md rule 5 exactly | Sonnet |
| R3b | Unknown zone type fails protective | index.html: `STYLES[p.zt]||…` (:1280) and `rank=(i<0?98:i)` (:1335) | all 178 real features unchanged; synthetic unknown type ranks first and renders the restricted wording | none (unreachable with real data) | any change for a real feature | Sonnet |
| R4a | `fhaAt()` + an FHA line on every card | index.html: point lookup, `FHA_COVERAGE`, four FHA states; the FHA tap handler (:1314) builds from the same function | `fhaAt` agrees with a brute-force PIP on ≥100,000 points; FHA-tap card unchanged apart from the documented new line | Hays Inlet with the FHA layer OFF still shows the FHA block; a non-FHA tap says so | STOP if any card implies an FHA is a no-take zone or that fishing is legal (rule 1) | Opus |
| R4b | FHA layer non-interactive | index.html: `interactive:false` on `fhaLayer`, as zones got at E2; FHA block now comes only from the map handler | no FHA canvas hit path remains; depth-pin popups inside an FHA open their own popup | pin inside Hays Inlet FHA opens the pin popup; FHA card still appears on a water tap | loss of the desktop FHA tooltip must be accepted by Aaron first | Sonnet |
| P1 | Tide-port range cap everywhere | index.html: `nearestPort` consumers (:1990, :2929, :2946, :3509, :4133) honour `PORT_MAX_KM` and render "no tide port for this location" instead of a far port | within 200 km of a port every output is byte-identical; beyond it, no tide value is produced | best-bite and a depth read at Redcliffe unchanged | STOP if any in-range output changes; note the HAT gate needs a defined behaviour with no port (proposed: keep the point, mark it un-gated — Aaron's call) | Opus |
| H1 | Region-aware header and safety text | index.html: title "Guya"; subtitle from `zoneLookup(map centre)`; recentre list; crocodile block region-scoped, most cautious when unknown (1d #1-4, #9, #10) | subtitle strings for a fixed list of centres | header reads correctly at Bargara, Hays Inlet, Noosa | STOP if the croc text for any latitude is weaker than today's | Sonnet |

Stage 1 is worth shipping even if nothing after it is ever built.

**Stage 2 — app shell offline (conditional on P0)**

| # | build | scope / files | vm harness proves | phone gate | STOP conditions | model |
|---|---|---|---|---|---|---|
| S1 | Service worker for the shell | new `sw.js` + registration in index.html. Network-first for `index.html` with a short timeout, cache fallback; precache the icon; NEVER intercept `storage_check.html`, a rescue URL, or any cross-origin request; every handler falls through to the network on error; a version constant acts as a kill switch | handler logic under a mocked fetch/caches: online → fresh copy and cache refreshed; offline → cached copy; error → network | flight-mode cold launch opens the app; after the next build is pushed, ONE online relaunch shows the new build string; `storage_check.html` still loads uncontrolled | STOP if P0 found service workers unavailable or non-persistent in the container; STOP if the rescue page is inside the SW's fetch handling | Opus |

**Stage 3 — imported depths out of localStorage (Option B, as D's storage step)**

| # | build | scope / files | vm harness proves | phone gate | STOP conditions | model |
|---|---|---|---|---|---|---|
| M1 | Dual-write | index.html: new IndexedDB database (own name; the photo and tile DBs are not touched), one record per region; every verified localStorage save also writes it; the app still READS localStorage | with fake-indexeddb: records equal `datasets` after each import path (merge, replace, undo, remove, restore) | `storage_check.html` shows per-region counts in IndexedDB equal to localStorage, before and after force-close | STOP on any change to what the app reads; STOP if the photo or tile DB version is touched | Sonnet |
| M2 | Read from IndexedDB, async boot | index.html: boot loads `datasets` from IndexedDB, falls back to localStorage if the store is empty or its counts disagree; `rebuildImportedFlat()` + `buildShade()` run on arrival; `_idwCache` keyed on `poolVersion` | consumers behave with an empty pool then a late pool; fallback path taken on a forced mismatch; shade output identical to M1 for the same data | cold launch: shading appears, counts match; flight mode; force-close ×3 | STOP if any consumer throws or caches an empty pool; STOP if a mismatch is resolved silently in either direction | Fable |
| M3 | Backup version:3 + restore to IndexedDB | index.html: export drops the flat `imported` duplicate and the pretty-printing, carries local datasets and (later) pack ids; import accepts version:2 and version:3 and pre-region files | round-trip v3; a real v2 file and a pre-region file restore to the same points as today; user collections unchanged | export, delete one test region, restore; restore the existing 19.08 MB v2 backup | STOP if any v2 fixture restores differently from the current build | Opus |
| M4 | Retire the localStorage copy | index.html: after a successful IndexedDB read AND a recorded v3 export, stop writing `woongarra_imported_v2` and the rollback slots; move rollback to IndexedDB; remove the key | removal happens only when both preconditions hold; never on a fallback boot | `storage_check.html` section 1 falls by ~3.85 MB; fill-test headroom rises; shading unchanged | STOP unless Aaron confirms a v3 export is saved off the phone; irreversible on-device | Sonnet |

After M4 the logbook has the whole 5 MiB to itself and can no longer be silently starved by
LiDAR (1a).

**Stage 4 — static depth packs, explicit library**

| # | build | scope / files | vm harness proves | phone gate | STOP conditions | model |
|---|---|---|---|---|---|---|
| K1 | Pack builder + first pack (no app change) | `tools/` builder; `regions/manifest.json`; one depth pack. HAT gate, land mask and `r0` precomputed; lossless delta-varint (or integer-column JSON if a binary toolchain is unwanted) | decode(pack) equals the CSV after the app's own normalisation, filtered exactly as `depthSamples()` would; manifest SHA-256 matches | none. Desk check: Pages serves the file — status, bytes, content type, hash | STOP if the class-9 adjacency check (CLAUDE.md data sources) has not been run on a topographic source; STOP on any decode mismatch | Sonnet |
| K2 | Regions panel + explicit download | index.html: manifest fetch (last-good kept), list with states, Download / Remove, hash verify on install and at boot, pack points join the pool; `persist()` requested once and shown | install / verify / corrupt-byte / remove state machine; a pack and a local dataset coexist | download on Wi-Fi at home; flight mode; force-close; pack still listed ✓ and paints; Remove frees it | STOP if a failed hash can leave a pack resident; STOP if a download can run without an explicit tap | Opus |
| K3 | "Not on this phone" states for depth | index.html: banner when the view intersects a manifest region that is not installed; tap-read and Deepest messages distinguish "no survey" from "not downloaded" (:3016, :3076) | message selection over installed / not-installed / no-pack fixtures | pan to a not-downloaded region in flight mode | none beyond wording review | Sonnet |
| K4 | Supersede a local dataset | index.html: when an installed pack covers a local dataset's region, OFFER removal of the local copy | never removes without confirmation; `legacy_unknown` is never offered automatically | remove the local Brisbane River copy after its pack is installed; counts as expected | STOP if `legacy_unknown` can be removed by this path | Sonnet |

**Stage 5 — only when a region needs it**

| # | build | trigger | notes | model |
|---|---|---|---|---|
| Z1a | Zone-pack loader with a TEST pack | before the first region north of Baffle Creek | installed ⇒ resident; coverage rows with `baked:false`; `notloaded` reachable for the first time; `zoneLayer.addData`; reset `_shadeFeats`; bbox pre-filter into `scanlineMask`. Harness: boot-race (tap before load → `notloaded`), remove-pack → `notloaded`, overlap + dedupe + cross-park tie. Phone gate: card before download, after download, after removal, in flight mode. STOP if any path renders OUTPARK inside a not-installed coverage row | Fable |
| Z1b | First real additional park | after Z1a and after that park's limits are verified against official sources (rule 5) | data only; `PARKS` entry starts unconfirmed | Sonnet |
| T1 | Tide tables as packs / annual refresh | before 2027-12-31 regardless | the embedded tables end then (1b) | Sonnet |
| V1 | Viewport-scoped depth residency (local, no network) | when installed points exceed ~250,000 or the perf HUD shows the load chain hurting | A's loader without the network; LRU over installed packs; zones are never evicted | Fable |

**Count.** 21 steps: T0 and P0; eight Stage-1 rule builds that every option needs; twelve that
are D itself (S1, M1–M4, K1–K4, Z1a, Z1b, V1) — the "~12" of Phase 3 — plus T1, which is owed
under any architecture. On-phone gates: P0, R2, R3a, R4a, R4b, P1, H1, S1, M1–M4, K2–K4, Z1a.
Stage 1 and Stage 3 are independent of each other and can interleave with the existing queue.

### 4.3 Effect on the existing backlog

| item | effect |
|---|---|
| IndexedDB migration (Hold) | SUBSUMED — M1–M4. Comes off Hold, as v16.62 §8 argued |
| 19.08 MB backup double-storage (v16.62 §6) | FIXED by M3 |
| Zone cards state rod/hook limits as fact (v16.77.18 backlog e) | ADDRESSED by R3a: figures carry a per-park verification record or are not shown |
| F7 canvas order | FHA-block half closed by R4a; the pin-popup half closed by R4b. Later canvases no longer matter to the card |
| MN v3 (Noosa-OSM clip) | Data work unchanged. DELIVERY changes: ship it as the first pack (K1) instead of a CSV REPLACE, which avoids the ~1,045 KiB transient rollback peak (v16.62 §9 item 6). If MN v3 is wanted before Stage 4 it still fits the current architecture |
| Option 3 coverage-boundary toggle | NOT blocked. Partly overlapped by K3, which answers "why is nothing painted here" for not-downloaded regions. Re-scope after K3; build after M2 so `buildShade` is not reopened twice |
| Gold Coast (#15, parked) | UNBLOCKED after K2 for depth. Needs: a verified-empty coverage row south of the Moreton Bay MP boundary (R2-type data), a Gold Coast tide port, and a land mask — the baked masks stop at −27.35 / −27.66 (:2829-2830) and `maskWater` returns true outside them (:2887), so unmasked topographic data there would paint dry ground. No zone pack needed |
| Bribie | Inside baked Moreton Bay MP; needs only a depth pack and, ideally, Bongaree as its own port |
| #16 Scout | Its "hard dependency on #15" becomes: R2 + P1 for new regions without a new park, Z1 for those with one. Its per-region OSM bundle fits as another pack kind |
| National-scale Hold | Architecture stops being the blocker after V1. Stays on Hold for the reason the Hold note already gives: per-state zoning and FHA sourcing |
| Canvas rasterisation (v16.67 §E) | Stays a fallback. The bbox pre-filter in Z1a answers the corpus-growth objection without giving up the bit-exact gate |
| `storage_check.html` tooling pass (v16.62 §9 item 4) | Fold its three caption/verdict fixes into P0's session only if kept as separate commits; otherwise leave queued |
| Slope-exit gate, chip, placing double, zones-toggle persistence | Unaffected; no shared code beyond the map click handler that R1 touches — sequence R1 after "placing double" or accept a rebase |

CHECKPOINT: Phase 4 complete 2026-11-14T03:08Z


## PHASE 5 — RED TEAM OF THE RECOMMENDATION

### 5.1 Failure modes, ranked by consequence

**Rule 2 — silence or a false "outside the marine park"**

1. **The coverage extents become the new single point of failure.** The fail-safe moves trust
   from legislated polygons to extents this project draws. An extent that is too generous —
   or a "verified-empty" row that is wrong — produces a confident OUTPARK card inside a marine
   park, with a source citation attached. That is worse than today's unsourced one.
   Mitigation: derive park extents mechanically from the official outer boundary and shrink
   them inward; treat every verified-empty row as a rule-5 fact needing an official source
   and a date; default everything else to `unassessed`. R2's STOP condition exists for this.
2. **A caller reads `zoneAt()` directly and renders a claim.** Seven sites exist today and
   four were written as copies; an eighth will be written the same way (Scout is the obvious
   candidate). Mitigation: R1 first; then pin the count and locations of `zoneAt(` call sites
   in the build discipline, the way the Leaflet SHA is pinned.
3. **Boot race (Z1 onward).** A tap lands before zone packs have loaded from IndexedDB. If
   "no features yet" is treated as "loaded, empty", the card says OUTPARK. Mitigation: a row is
   installed only after its features are in the scan list — one atomic step; harness test in Z1a.
4. **Stale zoning.** A zone pack, or the service-worker-cached index.html, keeps serving a
   superseded plan after an amendment, indefinitely offline. Baked zones have the same
   weakness today but are refreshed by every build the phone loads. Mitigation: `checked`
   date printed on every card; network-first shell; an age warning past a threshold.
5. **Partial hits misread.** The `notloaded` card's "At least: <zone>" line is read as the
   answer. Mitigation: wording and layout — unknown state first and larger. Removing the line
   would hide a known no-take zone, which is the worse error.
6. **FHA "none here" overclaims.** `fhaAt` makes a negative statement the app has never made.
   The data is dated Aug 2023. Mitigation: the negative is printed only inside assessed
   coverage and always with the currency date.
7. **Depth-side silence.** A not-downloaded region looks like unsurveyed water until K3 ships.
   Not a zone-rule breach, but it is the same class of misleading silence. K3 must not slip
   behind K2 by more than one build.

**Data loss**

8. **A faulty service worker can make the app unopenable, and on iOS the cure destroys the
   logbook.** A home-screen web app has no "clear cache" control: the user's only reset is to
   delete the icon, which deletes the origin's storage — spots, catches, photos. This is the
   most severe new risk the recommendation introduces. Mitigation, all mandatory in S1:
   network-first; every handler falls through to the network on any error; the worker never
   handles `storage_check.html` or a rescue page; the rescue page can unregister the worker
   and export a backup; a version kill switch. Take a v2 export off the phone before S1.
9. **Migration orphans `legacy_unknown`.** 55,660 points including the only copy of the
   Bargara data, with no source CSV in the repo (2a). Mitigation: M1–M4 copy, never move; M4
   is gated on a v3 export held off the phone; K4 can never offer `legacy_unknown`.
10. **Whole-origin eviction.** WebKit deletes an origin's data as a whole under storage
    pressure (2c). The logbook already lives under this policy; D does not create the exposure,
    but it makes the origin tens of MB larger and the roadmap has no restore drill. Mitigation:
    `persist()` requested and its result shown; export reminders; packs are re-downloadable.
11. **Wrong container.** A pack downloaded in a Safari tab is not in the home-screen app, and
    the tab is subject to the 7-day rule. Mitigation: the Regions panel shows the container
    (the test `storage_check.html` section 0 already does) and refuses to download in a tab.
12. **Backup regression.** M3 changes the only recovery path. A v3 importer that mishandles a
    v2 file strands every existing backup. Mitigation: real v2 fixtures in M3's harness; the
    v2 reader is kept permanently.

**Field usability**

13. **The download is forgotten.** Explicit download trades convenience for certainty; a trip
    to a new region with no pack ends with a banner on a rock platform. The Regions panel
    needs to be visible at a glance.
14. **Asynchronous boot.** Shading appears a beat after the map (M2). On a slow launch that
    reads as "my depths are gone".
15. **More states to explain.** Four zone states, four FHA states and three depth states,
    on a phone, outdoors. Each additional card state is a place for a wrong reading.
16. **Residency arrives sooner than estimated.** The ~250,000-point threshold comes from
    desktop ratios; the phone's heap ceiling is unmeasured. If it is lower, V1 moves up.

**Cost**

17. **Twenty-odd gated builds** at the project's one-feature-per-session pace is months, most
    of it on a failure (false OUTPARK in the far north) that has not yet been observed in use.
18. **Two data paths forever**: local CSV datasets and published packs, each with its own
    import, storage and backup behaviour.
19. **A per-region pipeline** — LAS processing, the class-9 adjacency check, masks, a port —
    is the real cost of each region and no architecture reduces it. "A region costs a commit"
    describes delivery, not production.
20. **CLAUDE.md invariants change** (3.0.7), by hand, by Aaron.

### 5.2 Assumptions that would flip the recommendation — and the cheapest test of each

| assumption | if wrong | cheapest test |
|---|---|---|
| The scale ambition is "many regions, eventually beyond SEQ" (roadmap v16.62 §8) | If it is "finish SEQ and stop" — at most three more regions, no new park — **Option B plus Stage 1 is sufficient**: about 13 builds instead of 21, no new files, no CLAUDE.md change. Stages 2 and 4 are then optional | Ask Aaron. No build |
| A service worker works and persists in Guya's no-manifest home-screen container | S1 is dropped. D still works for packs (IndexedDB needs no worker), but offline cold launch stays unsolved and becomes the app's main field risk | P0; and T0 says whether there is a problem to solve |
| Today's app does NOT reliably cold-launch offline (1f, inferred) | If it does, S1 falls from "largest offline risk" to "nice to have" and can leave the sequence | T0 — five minutes, no build |
| IndexedDB is durable in the container | If it is not, do not move `legacy_unknown` off localStorage; packs remain acceptable because they are recoverable | Existing evidence first: have catch photos (IndexedDB since they shipped) ever gone missing? Then P0 |
| Residency does not bind below ~250,000 points on the phone | V1 becomes part of Stage 4, and A's loader arrives earlier | After K2: install packs to a known total and read the perf HUD already in the app (`perfBegin` :2322) |
| iOS on Aaron's phone is 17 or later | The quota and `persist()` statements in 2c do not apply as written (older WebKit: ~1 GiB then a prompt) | P0 prints the version |
| Explicit download is acceptable to use | If it is not, the answer is A's implicit fetch layered on D — not a different architecture | Use K2 for two trips |
| Extents for "verified outside any marine park" can be sourced officially | If they cannot, those areas stay `unassessed` and Mooloolaba / Maroochy / Noosa lose the OUTPARK card they have today — more honest, less useful | Planning-chat check against official QLD sources before R2 is dispatched |
| The first new region with its own park is far off | If it is next, Z1a/Z1b move ahead of Stage 4 | Ask Aaron which region follows Gold Coast |
| The delta-varint builder is worth a toolchain | If not, integer-column JSON costs 12 B/pt at rest and changes nothing else | Decide at K1; both are measured in 2b |

### 5.3 Everything marked UNVERIFIED in Phases 1–4

1. Whether the current app cold-launches from the home screen with no signal (1f). → T0.
2. Whether a service worker registers, persists and serves a cold offline launch in the
   no-manifest home-screen container (2c). → P0.
3. Whether `navigator.storage.persist()` returns true in that container (2c). → P0.
4. Aaron's iOS version; all "iOS 17+" quota statements are conditional on it (2c). → P0.
5. Whether WebKit's default IndexedDB transaction durability survives an immediate
   force-close (Option B). → P0 / M1 gate.
6. Whether GitHub Pages gzips `application/octet-stream`; undocumented, no such file deployed
   (2b). Made irrelevant by a self-compact pack format.
7. Pages' gzip level — inferred ≈4–5 from one file (2b).
8. The exact iOS version supporting `DecompressionStream` — MDN gives Baseline May 2023 only (2c).
9. The localStorage cap itself: bracketed to [4,995.5, 5,919.6) KiB by roadmap v16.62; 5,120
   KiB is assumed (1a).
10. Stored-pool figures (134,372 points, 3,849.1 KiB, 64,306 surviving) are roadmap figures;
    no phone backup was reachable to re-measure (2a).
11. Coastline lengths in 2d (QLD ≈6,970 km, Australia ≈35,900 km) are from memory, and the ×2
    estuary allowance is a guess; (ii) and (iii) are order-of-magnitude only.
12. The QLD-scale zone-corpus estimate (≈11 MB at current precision, ≈7 MB at 5 dp) is scaled
    from Great Sandy; real GBR polygon counts were not measured (2d).
13. The ~230 B/pt heap figure and every millisecond in 2d are desktop V8; the phone's heap
    ceiling and timings are unmeasured.
14. The ~250,000-point residency threshold follows from 13 and inherits its uncertainty.
15. That the Great Barrier Reef Coast MP begins north of Baffle Creek is taken from CLAUDE.md
    and roadmap :1728, not re-verified against an official source this session; 3.0.1's
    false-OUTPARK finding rests on it. That NSW marine parks lie south of the border is from
    general knowledge.
16. That the state GBR Coast MP and the Commonwealth GBRMP overlap in tidal waters (3.0.3) is
    from general knowledge, not verified.
17. That SEQ-complete needs no zone pack assumes the Gold Coast south of −27.93 is outside
    every marine park (4.1 point 4) — needs the same official check as R2's other rows.
18. The "Opus" tier in 4.2 is this spike's suggestion; the roadmap line found (:10971) names
    only Sonnet as default and Fable for long or root-cause work.
19. Service-worker support in iOS home-screen apps is INFERRED from the Web Push announcement,
    not stated by any page fetched (2c).
20. `idwIndex`'s cell-width shortfall south of −24.85° (1c) is derived arithmetically (117.6 m
    at Redcliffe against a 120 m reach); no missed sample was demonstrated.

CHECKPOINT: Phase 5 complete 2026-11-14T03:09Z

## CLOSE

- Read-only for the spike confirmed: git status clean (0 porcelain lines), `## main...origin/main`
  with no ahead/behind, HEAD = origin/main = 0c8d6ff6e30a18c2ef3169e2060b3de692982c7f — unchanged
  from Phase 0. No tracked file modified. The only repo write this session was Step A's
  authorised push of the pre-existing commit 0c8d6ff.
- data\raw\ not touched. Inputs sampled read-only: four tracked CSVs under data\ (three for
  encodings and scaling, plus maroochy_noosa_bathy_v1.csv for the large-sample row).
- Network: GitHub REST + the live Pages site (Step A and header checks) and documentation pages
  on docs.github.com, webkit.org, developer.mozilla.org and web.dev. No ArcGIS, no ELVIS.
- No roadmap entry written. CLAUDE.md not touched.
- Files written, all under C:\Guya\Guya_Wamu\scratchpad\ : multiregion_spike.md (this file) and
  three helpers — mr_inventory.js, mr_encode.js, mr_scale.js. Sizes and SHA-256 are reported in
  the session's closing message (a file cannot contain its own hash).
- Phase 2 was written in two parts because a usage limit interrupted the session; the
  "PARTIAL" banner in the first part is superseded by "PHASE 2 — COMPLETION".
