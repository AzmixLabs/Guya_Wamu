# Guya — Feature Backlog & Roadmap

Personal / family land-based fishing tool. Single self-contained HTML file, Leaflet,
localStorage + IndexedDB, offline-first, hosted free on GitHub Pages. **Not for commercial
sale** — built for Aaron + family (sisters, nephews) use.

---

## Design rules (carry into every feature)

- **Never assert legality.** Bag/size/protected limits are *personal reference only* — the user
  enters them, the app surfaces official sources + a "verify currency" caveat, and the angler
  (the adult) makes the legality call. This holds for the kids' passport too: it celebrates the
  catch, it never tells a child a fish is legal to keep.
- **Zones only from legislated polygons** (`zoneAt()`). FHA stays a separate informational layer,
  independent of `zoneAt()`.
- **Offline-first.** Stored data shapes migrate, never orphan. Validate every script block with
  `node --check` before shipping. Preserve the green-zone drag safeguard.
- **Safety feeds never imply safety.** "No warning / no report" must never read as "safe."

---

## Phase 1 — keystone + personal features
*Fits the current architecture as-is: local, offline, no backend, $0.*

**Spine (build in this order — each makes the next more useful):**

1. **Auto catch-journal** — the keystone. Log a catch; auto-stamp date, spot, tide state, wind,
   moon phase, PB flag from data the app already computes. Everything below derives from it.
2. **Today's best-bets / spot scores** — extend `scoreSpotsFor` with live tide/wind/time vs each
   spot's recorded best-bite + windWarn + your logged catches. (Spot A 92%, Spot B 74%, …)
3. **Personal pattern surfacing** — plain aggregations over your own log ("bream: run-out, dawn,
   hardbody"). No ML. Call it *your patterns*, not "AI."

**Derived collection / achievement layer (built on the journal):**

4. **Species passport** — regional collections, rare-species flags, "collected X / Y." The
   stickiest idea on the list; ideal for the nephews. Nearly free once the journal exists.
5. **Personal species tally** per region.
6. **Adventure tasks / achievements** — first fish, first bream, 5 species, 20 species in summer
   (as *personal* goals). Badges / certificates UI for the kids' passport.

**Reference / utility layers (independent — slot in anytime):**

7. **POI layers** — boat ramps, kayak launches, jetties, reefs, curated tackle stores.
   (Ramps/kayak are low-relevance to Aaron's own land-based fishing; useful for family.)
8. **Gear tracking** — rods / reels / lures, local CRUD. Ties into the EOFY tackle workbook world.
9. **Navigation** — GPS track breadcrumb + saved routes, stored locally. (Offline basemap cache
   already done.)
10. **Official safety / warning feeds** — BOM warnings, cyclone / storm, fetched via API like
    Open-Meteo, surfaced with source + caveat. Never imply absence = safe.
11. **Closures layer** — official fisheries closures as an informational overlay, same discipline
    as zones / FHA.
12. **One-tap trip bundle** — download spots, depths, zones, FHA, tide tables for a trip in one
    action (Fiji / remote use). Builds on the existing offline cache.

---

## Phase 2 — shared / family
*Forces a light sync layer. Build only when you actually want cross-person sharing.*

> **Architecture note:** localStorage is per-device. Sharing catches/progress between Aaron,
> sisters and nephews needs sync. For ~6 known people use the **lightest** option — a shared
> backup file via iCloud/Drive, or **one** free Supabase table keyed by a family code — **not** a
> full accounts/auth SaaS stack. Keep it a tool, not a product.

- Parent / child accounts (lightweight identity, not full auth)
- Shared catches / catch feed / photo galleries (family-private)
- Family challenges & progress ("20 species in summer" across the family; "catch a fish together")
- Competitions / seasonal events — Brisbane Bream Challenge, Flathead Challenge — as shared
  leaderboards (the *personal* versions of these are Phase 1 goals)
- Angler profiles

---

## Hold / caution (do not build, or build only with care)

- **Crowdsourced croc / shark / bluebottle / stinger sightings** — needs a userbase + moderation,
  and must NEVER imply "no report = safe." Logging your *own* sightings locally is fine; a
  reporting network is not, for a private family tool.
- **AI fish-ID that states legality or eating quality** — don't. Breaks the legality rule; pure
  liability. (Identifying a species for fun is fine; asserting "legal to keep" is not.)
- **Public / stranger social feed, comments, messaging** — not for a private family tool;
  ~80% of the maintenance for ~20% of the value.

---

## Notes on the "game-changer" ideas

- **Predictive Bite Engine** = Phase 1 items 2 + 3. Honest scope: predicts from
  tide/wind/moon/time + your history. Weak until you've logged enough trips. Useful, not an oracle.
- **Global Species Passport** = item 4 with a larger species list. The collection hook is the
  genuinely sticky, family-friendly differentiator.
- **Personal Fishing AI** = item 3 evolved. Start as transparent aggregations; optional later,
  pipe your own log to an LLM for plain-English summaries (needs the API — optional polish, not
  the engine).
