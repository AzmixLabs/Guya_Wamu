# Guya — Feature Backlog & Roadmap
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
~13.6 km² / 192 in v16.18) — the SC 2022/2014/2008 + Noosa groups add 110 artifact-scale tiles
/ +6.69 km²; the 2009 vintages add ZERO at artifact scale (effectively clean — the fault is
post-2009 only). Current build remains 2026.07.05a. Both the Brisbane River and Sunshine Coast
CSVs — each already phone-imported via MERGE (see v16.22 correction) — remain unsafe to trust
as-is; the drop-mask re-export (item 2) is now fully scoped and unblocked. See changelog v16.21.*

Personal / family land-based fishing **+ nature field-log** tool. Single self-contained HTML
file, Leaflet, localStorage + IndexedDB, offline-first, hosted free on GitHub Pages.
**Not for commercial sale** — built for Aaron + family (sisters, nephews, daughter).

**Current build:** 2026.07.05a *(2b wiring: zoning/FHA/tides — see changelog v16.19. Priority list below synced to that build in v16.20 — no code shipped in v16.20. `storage_check.html` diagnostic page + its temporary in-app link, from v16.7, are still present and still flagged for removal.)*

**Next-session note (10 Jul 2026):** build 2026.07.05a unchanged; v16.21 closed the depth-audit
gap (diagnostic only — new headline: 302 tiles / 20.3 km² at artifact scale, per-tile results in
`data/raw/_inventory/audit_results.json`). Recommended next job: **item 2 — drop-mask re-export
design** (now unblocked, scope final). Pending cleanup: `storage_check.html` + its in-app link
(v16.7); `data/raw/_inventory/gap_checkpoint.json` is completed-run scratch, safe to delete.

**Next session — priority order:**
1. **Close the depth-data audit gap — DONE (v16.21).** All 544 remaining SC/Noosa tiles audited
   (556 total incl. the 12 v16.18 spot samples; count corrected from "652" in v16.22)
   by class-9-adjacency (SunshineCoast_2008 carries class 9 after all, so no fallback needed) and
   all three 2009-vintage groups (363 unique tiles) by the density-only secondary test. Zero read
   errors. Artifact-scale total revised 192 tiles / 13.6 km² → **302 tiles / 20.3 km²**; the 2009
   vintages contributed zero. Per-tile results merged append-only into
   `data/raw/_inventory/audit_results.json`. See changelog v16.21.
2. **Design + build the drop-mask re-export**, once item 1 closes the scope. Per-cell density
   threshold derived from `data/raw/_inventory/audit_results.json` (already has the per-cell
   counts). Drop flagged points rather than reclassify — geometry alone can't tell a real drying
   flat from mislabelled water at the same elevation (see v16.18 qualification 3). Applies to:
   Brisbane_2014/2019, Redland_2014/2022, Pine River strays, SC MoretonBay_2014/2018, plus the
   110 artifact-scale tiles v16.21 added across Sunshine_Coast_2022/2014/2008 + Noosa_2022/2015
   (2009 vintages: zero at artifact scale, no mask needed).
3. **Re-export both CSVs**; validate against known controls — Brighton, Sandgate, Shorncliffe,
   Redland bayside, Deception Bay/Beachmere, Golden Beach/Pumicestone, Currimundi (all surfaced
   during the v16.18 audit) — confirm artifact zones read "no data," and spot-check that real
   flats nearby weren't wholesale gutted by the drop-mask.
4. **Re-import — REPLACE required for BOTH regions, not a fresh first import for Brisbane
   River.** Brisbane River and Sunshine Coast phone data are both already imported (both via
   MERGE) and both confirmed to carry the classifier-fault artifact. Neither can be corrected by
   another MERGE — MERGE cannot remove points already present. Flag explicitly when run; a first
   for this app's import history on both fronts.
5. **Small, independent fix — no dependency on the above:** add the missing "low confidence" tag
   to the "dries" popup branch past 80 m (the depth-popup branch already has it) — found
   incidentally during the v16.17 diagnostic.
6. `git remote -v` check — DONE (v16.19): still points at `AzmixLabs/Guya.git`, unchanged
   despite the repeated "repository moved to Guya_Wamu" notice. **What's left is a decision, not
   a check:** confirm on github.com whether the repo was actually renamed server-side, then
   either rename the local remote to match or confirm nothing changed — once, deliberately —
   rather than letting the notice fire a third time on an unverified redirect (the same class of
   risk already flagged for the phone's home-screen icon in v16.7/v16.15).
7. Confirm `fishhabitat_bundaberg_region.geojson` — RESOLVED (v16.19): confirmed byte-identical
   to the already-shipped Woongarra FHA store. It's that store's raw source file, not an
   unrelated file. No action needed.
8. 2b wiring build (zoning/FHA/tides) — SHIPPED (v16.19, build 2026.07.05a).
9. **New (surfaced by v16.19):** FHA data (35 features, merged into the store) has no rendered
   map layer or point-in-polygon lookup — same gap as the pre-existing Woongarra FHA entries,
   just newly visible now that Maroochy/Noosa are in the same store. Independent, no dependency
   on the depth-audit work.
10. Noosa Head tide port — ready-whenever fast-follow. Own Standard Port, no offset math needed
    (confirmed v16.5, re-confirmed v16.19) — same pattern as Redcliffe following Brisbane Bar in
    2a. Cheap, not urgent.
11. Gold Coast stays parked.

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

> **Home-water depth reality (SE QLD / Moreton Bay), confirmed 19 Jun 2026:** beyond the open coast
> this is a physics + coverage gap, not a missing download. Turbid water defeats laser bathymetry — a
> satellite-laser (ICESat-2) study found >half of Moreton Bay too sediment-laden to read — so the
> clear-water LiDAR that gave Woongarra its shading can't be replicated up the Pine / Brisbane / Hays
> Inlet. National open bathy (GA AusBathyTopo, 250 m) is coarse open-coast only; the one all-QLD-
> estuary composite (CSIRO 5 m) fills gaps with **modelled** creek depth → out by the no-chart-art
> rule; hydro charts are channel-centric + copyright. Realistic home-water depth = (a) **your own
> sonar → GPX** (works in mud; already supported); (b) real 5 m bathy-LiDAR exists for the **Sunshine
> Coast** Maroochy/Noosa estuaries (data.qld.gov.au) if you extend north; (c) otherwise **no depth
> layer** — spots / tides / zones / FHA / patterns all work without it. Don't bake modelled bathymetry.

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
