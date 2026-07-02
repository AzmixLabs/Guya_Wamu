# Guya — Feature Backlog & Roadmap
*v16 · 28 Jun 2026*

Personal / family land-based fishing **+ nature field-log** tool. Single self-contained HTML
file, Leaflet, localStorage + IndexedDB, offline-first, hosted free on GitHub Pages.
**Not for commercial sale** — built for Aaron + family (sisters, nephews, daughter).

**Current build:** 2026.06.28b *(Badges / achievements shipped — see changelog v16)*
**Next build:** `2026.06.NNa` — **open.** Item 6 (Badges) is now SHIPPED, so the queue's strong picks are: **Region 2b (Sunshine Coast)** — the next region, where depth actually works (real 5 m Maroochy/Noosa bathy-LiDAR), but still **blocked on external data egress** (LAT tide tables + FHA polygons + LiDAR are unreachable in-sandbox → **local-build handoff, not an inline build**); **DEA Intertidal exposure layer (item 14b)** — qualified GO, gated on a manual DEA-Maps confidence check over Hays Inlet / Bramble Bay / Pumicestone first; or **profile-aware patterns / views (4c+)** — fully local, no egress, builds on the avatars already stamped. The cleanest *inline* next job is 14b (after the manual check) or 4c+; 2b needs a data run first. **Badges shipped (v16 / 2026.06.28b):** 18 badges computed entirely from the stamped catch log (counts, distinct-species, released, distinct-spots, PB, moon-phase, spring-tide, all-tide-phases, four-seasons, + secret Grand Slam / Dawn Patrol / Night Shift); per-angler filter; offline canvas PNG certificates; zero egress, no IndexedDB writes, catch-log only. **The Bargara-anchored astronomy / wind remnants were CLEARED (v15 / 2026.06.28a):** best-bite sun/moon, both wind buttons, and the spot wind-check all follow the nearest tide port (`nearestPort(map.getCenter())`); and the live-wind button's latent `ReferenceError` (it called the best-bite IIFE's private `curPort()`/`tideTable()` from a sibling scope and silently fell to "No signal" even online) is fixed in the same pass. **Region 2a is COMPLETE at v14 / 2026.06.27a:** Brisbane Bar 2026 tides + 74-zone Moreton Bay park + `PORTS`/`nearestPort` + most-protective `zoneAt()` (MNP > CPZ > HPZ > GUZ) + region-aware popups + Redcliffe default view. **Still pending for home water:** 2027 Brisbane Bar tides (needed before the 2027 season, not blocking 2026); FHA + depth for Moreton accrete later as the rest of #15.
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
    - **Data-prep workbench:** **QGIS** turns the official source into app-ready GeoJSON — download the
      **QSpatial** 2019 zoning + FHA (SHP / FGDB), clip to the home extent, reproject **GDA94 → WGS84**,
      **simplify vertices** (keep the single-file size sane), export GeoJSON for `zoneAt()`. QSpatial =
      the zone / FHA source. The **GA portal / GA online tools** are discovery + coarse open-coast
      bathy only (AusBathyTopo) — no help inside the bay.
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
