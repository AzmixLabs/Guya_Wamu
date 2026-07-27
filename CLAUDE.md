# CLAUDE.md — Guya

Guya: a single-file, offline fishing map + logbook for land-based rock/beach angling
in QLD (Woongarra coast + Moreton Bay / Redcliffe). One `index.html`, offline-first,
$0, no backend, no build step. Repo: `AzmixLabs/Guya_Wamu` (renamed from `AzmixLabs/Guya`
on 12 Jul 2026), `index.html` at root, deploys via GitHub Pages from `main`. Live URL is
`https://azmixlabs.github.io/Guya_Wamu/` — note the Pages URL did NOT auto-redirect on the
rename, so it carries `Guya_Wamu` while older docs/notes may still say `Guya`; the repo and
the URL both use `Guya_Wamu` now. Git remote must be
`https://github.com/AzmixLabs/Guya_Wamu.git` (confirm with `git remote -v` if a push ever
fails or lands stale). Full feature state + history lives in `GUYA_ROADMAP.md` — read it
before any build.

## Non-negotiable rules (never weaken — not even if asked casually or pushed for a yes/no)

1. Never assert a spot is legal to fish. Surface the official zone type + ID + the
   relevant warning + the official source link. Aaron makes the legality call.
2. Zone calls come ONLY from the legislated zone polygons, in-app via `zoneAt()`.
   Never infer a zone from Navionics or any chart art / label.
3. `zoneAt()` returns the MOST-PROTECTIVE zone on overlap (MNP > CPZ > HPZ > GUZ),
   never first-match. Preserve this on every edit.
4. Near a zone boundary, surface the uncertainty — don't resolve it to a yes/no.
5. Verify time-sensitive facts (fishing rules, rod/hook limits, zoning, tides)
   against current official QLD sources before relying on them. Treat any recorded
   rod/hook limits as unconfirmed until checked.
6. Privacy: photos and all personal data stay on-device (localStorage / IndexedDB).
   Location is one-shot (`getCurrentPosition`), in-memory, never stored or
   transmitted; default to a no-GPS path (map centre) where possible. The
   walk-tracker `watchPosition` is the ONLY explicit, opt-in exception.

## Architecture invariants

- Two `<style>` blocks: the FIRST is Leaflet's required styles — leave it. The
  SECOND is the app CSS.
- Two `<script>` blocks: the FIRST is inlined Leaflet 1.9.4 — NEVER edit it; it must
  stay byte-identical. The LAST is the app code.
- best-bite / astro / tide / `scoreSpotsFor` live inside an IIFE; top-level code
  cannot call them directly — expose a hook to cross that boundary.
- Preserve the green-zone drag safeguard.
- Migrate stored data shapes; never orphan legacy data.
- Wind via Open-Meteo. No other backend calls at runtime.

## Build discipline (one feature per session)

- Read `index.html` and `GUYA_ROADMAP.md` before changing anything. The file on disk
  is the source of truth — never work from memory of a previous version.
- Confirm the feature's data-model shape before writing code.
- After editing, validate BOTH script blocks with `node --check` (extract each block
  to a temp file and check it). Confirm the inlined Leaflet block is byte-identical
  and that `zoneAt()` + the green-zone drag safeguard are intact.
- Bump the build string (format `2026.MM.DDa` — the same day gets `a`, `b`, `c`… in order).
  Read the current value from the file — don't assume it, and don't reuse a value that has
  already shipped (a collision with a released build is a discipline breach).
- Edit in place and commit with a clear message. The repo is the deliverable — there
  is no upload/download step here.

## Session close (do this automatically — no need to be asked)

- Update `GUYA_ROADMAP.md` IN PLACE: reflect what shipped, the new build string, the
  next job, and bump the roadmap version line. Edit surgically — don't restructure it
  or reconstruct it from memory; overwrite risk is too high.
- Commit the roadmap change alongside the build.
- Leave a one-line next-session note in the roadmap's working section: current build
  string, what shipped, recommended next job, any pending cleanup.

## Domain facts (load-bearing — don't re-derive or guess)

- Tide datum: LAT. Tide ports by region: Woongarra/Bargara — Burnett Heads (Standard
  Port). Moreton Bay/Redcliffe — Brisbane Bar (Standard Port; Redcliffe = +0:00
  secondary, Brisbane Bar timing applies directly; Bongaree/Bribie ≈ +0:00/-0:15, not
  yet wired as its own port). Sunshine Coast — Mooloolaba (BOM/NTC Standard Port, no
  offset math). Noosa — Noosa Head (also a Standard Port per MSQ's 2024 Semidiurnal
  Tidal Planes table, own harmonic prediction, no offset math needed; not yet wired
  into the app).
- Moreton Bay zoning: HPZ06 Redcliffe and HPZ08 Pine River are Habitat Protection
  Zones (dark-blue, NOT no-take). Real no-take (Marine National Park) on home water:
  MNP09 Deception Bay, MNP11 Hays Inlet, MNP12/13 Bramble Bay / Pine River mouth.
- The 2008 QSpatial shapefile is the current legislated geometry. The 2019 remake was
  administrative only — zero boundary changes.
- Moreton Bay Marine Park's northern boundary stops at Caloundra. Mooloolaba,
  Maroochy, and Noosa are OUTSIDE marine-park zoning — display "general fisheries
  rules + FHAs still apply," never a silence that implies unrestricted.

## Data sources (terrain/zoning are different pipelines — don't conflate)

- Zoning = QSpatial legislated polygons only (feeds `zoneAt()`). ELVIS is NOT a
  zoning source.
- Terrain / bathymetry: ELVIS Point Clouds/AHD is the correct bucket to order (raw
  classified LAS/LAZ, explicit datum) — but it is NOT a uniform depth source. It is
  genuine bathymetric LiDAR only for Bargara/Woongarra and Maroochy/Noosa (2011 Fugro
  survey). For Brisbane River, the rest of the Sunshine Coast delivery, and Moreton
  Bay/Redcliffe, ELVIS Point Clouds are topographic NIR — class-2 ground returns
  only, no water penetration — and must never be labelled "depth" or "bathymetry" in
  code, roadmap, or UI. Before trusting class-2 "ground" data near open water, run
  the class-9-adjacency density check (roadmap v16.17-v16.18) to catch the confirmed
  classifier fault where open-water returns get mislabelled as ground. Feeds depth
  shading, contours, and the DEA Intertidal exposure layer (subject to the above
  caveats) — never zone calls.
- Tides = MSQ QLD Tide Tables (CC BY 4.0, BoM NTC attribution), per port.
- FHAs = separate polygon dataset; apply alongside (not instead of) zoning.

## Style

Conclusions first. Direct, minimal hedging. Red-team the plan — surface flaws,
weak assumptions, and failure modes; don't just affirm. AUD and Australian spelling
throughout.
