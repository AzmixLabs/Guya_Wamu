# Guya — Feature Backlog & Roadmap

*v16.77 · 5 Sep 2026 — **F2 PAINT SIDE SHIPPED AND GATED. `buildShade()` NO LONGER PAINTS
LAND. Build `2026.09.05f`.** On-phone gate PASSED at all three benchmark locations,
before/after, with no S3 regression — confirmed by Aaron directly; per-location S3 figures
not transcribed this session. **F2 IS NOW FULLY CLOSED, both sides.***

**1. WHAT SHIPPED — ONE LINE OF CODE.** `index.html:2617`, inserted between the existing
`maskA` gate and the `FD`/`AL`/`ST` write in `buildShade()`'s pass-2a pixel loop:

```js
if(distA>0&&queryOnLand(la,lo)){AL[i0]=0;continue;}
```

`AL[i0]=0;continue;` is byte-for-byte the treatment `:2579` (`!den`) and `:2595`
(`maskA<=0`) already give a no-coverage pixel — `FD`/`ST` left unwritten, pass-2b reaches it
at `a<=0.01` and writes literal alpha 0. **No new rendering path was added.** `queryOnLand()`
reused verbatim rather than calling `maskWater()` at the paint site: it is a pure
`(lat,lng)→boolean` with no read-path state (popup, DOM, closure) and its `catch` fails open,
which is the correct direction here too — a throw paints as before rather than silently
erasing water. Scope confirmed by brace walk, not assumed: `buildShade`, `maskWater`,
`queryOnLand` and `depthSamples` all sit at identical depth, so no IIFE hook was needed.

**2. PLACEMENT WAS THE WHOLE BUILD, AND THE NAIVE ONE FAILS. RECORD THIS NUMBER.** Measured
before touching `buildShade()`, per the brief's stop-and-report condition:

| placement | calls/rebuild | node ms | device est. |
|---|---|---|---|
| top of the pixel loop | 360,000 | 8.0–12.8 | **15.7–25.3 ms — FAILS** |
| painted pixels only (shipped) | 1.4k–55k | 0.05–1.36 | **0.5–2.0 ms — passes** |

**15–25 ms is tens, not a few, against S3 budgets of 151 / 189 / 291 ms.** Had the test gone
in at the top of the loop this build should have stopped and become an F3-style
precomputed-bitmap job. It did not, because the existing transparent path is not at the top of
the loop — it is at the END of the gate chain, and a pixel only needs a land test if it would
otherwise paint. **v16.76.4 §2's "the obvious fix" was right about the mechanism and wrong
about where it goes; the difference between the two placements is an order of magnitude.**

**3. `distA>0` IS A COST GUARD, NOT A BEHAVIOUR RULE — DO NOT TIDY IT AWAY.** `distA===0`
already forces `AL=distA*maskA=0`, so such a pixel is transparent with or without a land test:
the guard changes nothing on screen and only decides who PAYS. It is load-bearing because
`maskA=Math.max(mA,…)` lets every pixel inside a zone polygon past `:2595` even where nothing
is painted; without the guard the test runs across that whole set and the cost collapses back
toward the failing figure in §2. Harness suite 4 proves the guard cannot leave a land pixel
painted. Documented in the code comment for the same reason.

**4. METHODOLOGY — HOW THE DEVICE NUMBERS WERE REACHED OFF-PHONE.** A raw Node figure is not
device-representative (this project's own standing rule), so the S3 loop *shape* was reproduced
at the same scale (64,306-point pool, 120 m bucket index, 3×3 probe + IDW accumulate, 3.24 M
probes) and calibrated against v16.68.2's measured on-device S3: **Bargara 1.98×, Redcliffe
2.23×, Brisbane z10 1.49×**. The painted fraction was BOUNDED, not assumed — a ceiling run
against the real repo CSVs with `okMASK` dropped and no thinning (strictly more samples than
the phone carries) peaks at **15.3% of the grid** (BR dense core, 55,233 px, 1.36 ms node).
Structural ceiling ~31%: `W=max(280,min(600,extM/35))` means the 600² grid exists only at
extents ≥21 km where a pixel is 35 m, and BR's entire ~139 km² painted footprint (~113,000 px)
spans 61 km of longitude and cannot fit one 21 km viewport. Break-even against a 3 ms budget is
~14% of the grid. **Reusable pattern: calibrate the harness against an existing on-device
segment measurement rather than reporting bare Node milliseconds.**

**5. SCALE OF THE DEFECT THIS CLOSES.** At ceiling density, **43–82% of currently-painted
pixels at Redcliffe and Brisbane were on land** — 76% at the BR dense core. Independently
consistent with v16.53's "BR painted footprint is 79.3% certainly-dry (110.5 km²)". The
paint-side defect was not a fringe case; in the river it was most of the painted footprint.

**6. VALIDATION.** Both blocks `node --check` pass. Leaflet block byte-identical —
**147,552 bytes**, SHA-256 `db49d009…641a`, exact match to the `CLAUDE.md` pin. `zoneAt()` and
the green-zone dragend safeguard absent from the diff (the only `zoneAt`/`maskWater` hits are
two lines of the new comment). Diff scope: **24 insertions, 2 deletions, one file** —
`index.html:1052` and `:1091` (build string), `:2596–2617` (21-line comment + 1 code line).
`index.html:2862`, the F2 read-side comment header, keeps its own historical `2026.09.05e` tag
and was deliberately not bumped. **Harness** (`scratchpad/f2_painttest_land.js`, extending
F1's 6,005-pair paint-alpha-purity harness): **78,674 cases across 5 suites, all pass** — land
pixels exactly `+0` alpha by `Object.is` (not `==`), water pixels bit-identical to `2026.09.05e`,
and the original 6,005 F1 pairs re-run clean. Acceptance case reproduced off-phone at
Nudibranch Tip (`-24.9002, 152.4692`, `queryOnLand` true): alpha 1.000 / 0.667 / 0.433 / 0.011
at 30 / 60 / 81 / 119 m → **0.000 at every one**.

**7. ON-PHONE GATE — PASSED.** Acceptance test at Nudibranch Tip with shading ON, before/after,
plus the standard 10-pan timing protocol at Bargara z11, Redcliffe z11 and Brisbane River z10:
**land renders unshaded, water unchanged, no S3 regression at any of the three.** Recorded on
Aaron's direct confirmation — the same standard used for every prior on-device gate in this
project (see v16.76.2 §2). **Per-location S3 numbers were not transcribed into this entry; if a
future build needs them as a baseline, re-measure rather than inferring them from §2's
predictions.**

**8. KNOWN AND INTENDED CONSEQUENCE FOR F3's ZONE FILL.** F3's coverage cells are set only at
`a>=0.05`, so a zone whose only shade was land-overpaint now correctly stops counting as covered
and no longer dims. Different gate, same render loop. Called out in the code comment and checked
at the gate.

**9. NEXT SESSION.** Build **2026.09.05f**, roadmap **v16.77**, repo head is this entry's own
commit. `CLAUDE.md` unchanged. **F2 is fully closed, both sides — do not reopen it.** Next job
is open: the standing backlog items untouched by this arc are **`R1` declared twice
(`buildShade()` and `buildAutoContours()`) still not unified**, **`WOFS_FREQ_MIN`**, and
**`_idwCache` keying** (reversed and reclassified low-priority correctness at v16.68.3). Do not
re-litigate: the placement decision (§2/§3 — the guard stays); `queryOnLand()` over `maskWater()`
at the paint site (§1); the LANDMASK coverage — three baked regions, uncovered north of roughly
lat −26.34, so this gate is a permanent no-op at Mooloolaba/Noosa.

*v16.76.4 · 5 Sep 2026 — **F2 READ-SIDE ON-PHONE GATE PASSED.** F2's read side (tap+hover)
is now fully shipped AND gated — v16.76.3 shipped it harness-verified only; this entry
supersedes its "gate unrun" line. No build, no code, no data change this entry. Build
stays **2026.09.05e**; repo head unchanged at **0d486b0**.*

**1. GATE RESULTS.** Acceptance case (Woongarra Scenic Drive, ~81 m from nearest sounding)
and a second point further along the same road — both read `No data here — this point is
on land.`, zero digits in either response. F1's six checks re-run clean on genuine water
points, wording byte-identical to before this build: Innes Park 10 m → `Est. depth here ≈
5.0 m`; Hervey Bay 20 m → `Est. depth here ≈ 10.4 m`; Hervey Bay offshore → `No survey
data within 120 m here.` Headland remains shaded — expected, paint side untouched (§2).

**2. WHAT'S LEFT — THE PAINT SIDE.** `buildShade()` still colours land pixels out to R1
(120 m) with no land test — the same defect the read side just fixed. Not built here,
deliberately — a perf-sensitive per-pixel change gets its own measurement first. New fact
from the read-side diagnosis, worth carrying forward: `maskWater()` is O(1) per point
after a one-time per-region bitmap decode — a bbox test plus one bit read, no live
geometry, no network — cheap relative to what `buildShade()` already does per pixel
(nearest-neighbour search, IDW, R0/R1 ramps). That lowers the expected cost of the obvious
fix: skip painting (leave transparent) any pixel where the query point is land, the same
treatment already given to no-coverage pixels. Still needs to be MEASURED, not assumed —
a quick before/after pan-timing check is the right size of spike, not a full F3-style
bitmap-precompute investigation, unless measurement says otherwise.

**3. NEXT SESSION.** Build **2026.09.05e** (unchanged), roadmap **v16.76.4**, repo head
**0d486b0** plus this entry's own commit. `CLAUDE.md` unchanged. **Next job: F2's
paint-side land test** — extend `buildShade()`'s per-pixel loop with the same
`queryOnLand()` gate, measure the added per-pan cost before any further optimisation,
on-phone gate before/after. Do not re-litigate: the read-side fix (v16.76.3 shipped, this
entry gated); the LANDMASK coverage — **three baked regions** (`woongarra`, `seq_coast`
— a single box covering both Redcliffe/Moreton and Sunshine Coast/Maroochy/Noosa —
and `brisbane_river`), not four; uncovered north of roughly lat −26.34.

*v16.76.3 · 5 Sep 2026 — **F2 READ SIDE SHIPPED: THE DEPTH READOUT NOW TESTS THE QUERY
POINT FOR LAND. Build `2026.09.05e`, commit `0d486b0`.** Pushed; Pages run `33941861043`
completed/success, live site confirmed serving `2026.09.05e`. **THE ON-PHONE GATE WAS NOT RUN —
pushed at Aaron's explicit instruction ahead of it. This build is HARNESS-VERIFIED ONLY. Do not
read it as verified on device.** The paint side is untouched and is still open.*

**1. THE DEFECT THIS CLOSES, RESTATED FROM v16.75.7.** `maskWater()` had exactly one call site:
`okMASK` inside `depthSamples()`, asked about a stored **sample's** own coordinates. Both observed
defects were on the other axis — the readout reported a nearest sample's value at a **query** point
without ever asking whether that point was land. v16.76.2 §4 gave it a reproduction case: a tap on
Woongarra Scenic Drive at Nudibranch Tip, 81 m from the nearest dries sample, returning
`dries ≈ 1.7 m` **on a sealed road**.

**2. TAP AND HOVER DID NOT SHARE A CODE PATH — TWO EDITS, ONE DEFINITION.** Checked rather than
assumed, because it decided the shape of the fix: the hover has its **own** `mousemove` handler and
**never calls `openDepthRead()`** — it calls `idwDepthAt()` and writes `el.textContent` itself. So
the rule lives in **one shared helper**, `queryOnLand()`, called from both, rather than the hover
growing a second copy — the same pattern build `2026.09.05c` used for `NEAR_HERE`/`NEAR_MAX`.

```js
function queryOnLand(lat,lng){try{return maskWater(lat,lng)===false;}catch(e){return false;}}
```

| site | lines | kind |
|---|---|---|
| `queryOnLand()` + comment, immediately after `maskWater()` | `index.html:2862–2878` | insertion only |
| tap gate, **ahead of `idwDepthAt`** so a land tap does no interpolation at all | `index.html:2974–2987` | insertion only |
| hover gate, first arm of the existing text chain | `index.html:3899–3902` | 1 → 4 lines |

**Water points reach identical code with identical inputs**, so every water-side case is
**byte-identical in wording** to `2026.09.05d`. **Fails open**: any throw is treated as *not* land,
because suppressing a real depth is the worse of the two errors.

**3. TWO DECISIONS TAKEN DELIBERATELY, BOTH APPROVED BEFORE THE CODE WAS WRITTEN.**
   - **D1 — coverage limit, written into the code comment.** `maskWater()` returns `true` wherever it
     has **no data**, so the gate **can never wrongly claim "on land"** but is a **permanent no-op
     north of lat −26.34**, outside the three `LANDMASK` boxes. Bargara/Woongarra, Redcliffe,
     Brisbane River and Mooloolaba–Noosa are covered. A fourth region is a data-pipeline job, not a
     code change.
   - **D2 — a bare map tap on land now opens a popup**, where a bare no-data tap previously opened
     nothing. The gate only ever fires on land, where the alternative is the wrong number this item
     exists to remove, so silence would be the worse answer.

**4. HARD RULE 1 PRESERVED AND ASSERTED, NOT ASSUMED.** A zone tap over land still renders the full
zone card — type, ID, restriction text, "simplified boundary — not authoritative" warning, official
link — with the land message **below** it. **The gate suppresses the NUMBER, never the
classification.** Covered by a harness assertion that the zone land response still contains
`CPZ06` and `not authoritative`, and by a second that it contains no depth value or distance wording.

**5. HARNESSES EXTENDED RATHER THAN LEFT UNTESTED — 21 → 44 ASSERTIONS, ALL PASS.** All three
extract the live lines from `index.html` rather than restating them.

| harness | before | after |
|---|---|---|
| tap — `scratchpad/f1_labeltest.js` | 12/12 | **19/19** |
| hover — `scratchpad/f1_hovertest.js` | 9/9 | **16/16** |
| gate — `scratchpad/f2_gatetest.js` (new) | — | **9/9** |

Worth naming: the gate **structurally precedes `idwDepthAt` and every distance/value branch** in
both paths; the land response contains **no numeric character at all** (regex-asserted, both paths);
**land wins at 5 m**, so distance never overrides the land verdict; a water point never reaches the
land branch; fail-open on a throwing `maskWater`; and D1's no-op north of the boxes returns `false`,
never a false "on land". At the real acceptance coordinates (lat −24.84089) the gate fires at
152.4770/4780/4789 (road side) and stays silent at 152.4790/4800/4830 (water side).

**6. VALIDATION.** Both script blocks `node --check` clean. Leaflet block **byte-identical**,
147,552 bytes, SHA-256 `db49d009…641a`, matching the `CLAUDE.md` pin. **`buildShade()` NOT
TOUCHED** — `git diff | grep -c 'buildShade\|distA\|maskA\|AL[i0]'` = **0**; its cost was not
estimated as a substitute for measuring it, as dispatched. `zoneAt()`, `ORDER` and the green-zone
`dragend` safeguard absent from the diff. **The `okMASK` admission line is unmodified** — the only
`okMASK` in the diff is prose inside the new comment (`grep -c "^[-+].*const okMASK="` = 0), so
sample admission, `_poolCache` and `poolVersion` are unchanged. **Diff: 37 insertions, 3 deletions,
5 hunks**, `index.html` only.

**7. THE PAINT SIDE IS UNTOUCHED AND STILL SHADES THE HEADLAND.** `buildShade()` still paints
anything within 120 m of a pooled sample, land or not. **Expect a land tap to read "on land" over
shaded pixels** — that is the intended intermediate state, not a regression. F2's paint half is a
separate dispatch and the last item in this arc.

**8. ON-PHONE GATE — OUTSTANDING, AND THIS ENTRY DOES NOT CLAIM IT.**
   **8a. Acceptance case.** Tap Woongarra Scenic Drive at Nudibranch Tip, ~81 m from the nearest
   `dries ≈ 1.7 m` sample, on the sealed road, shading ON. **Before** (`2026.09.05d`):
   `Nearest reading · 81 m away` / `dries ≈ 1.7 m`. **After** (`2026.09.05e`):
   `No data here — this point is on land.`, **no numeric value anywhere**. Inside a zone polygon the
   zone card must still appear above that message.
   **8b. F1 regression re-check, all six v16.76 §7 checks** — water-side wording must be
   byte-identical to `2026.09.05d`. Two expected non-regressions, so they are not misread: check 4's
   **on-road tap now reads the land message** (the intended change), and the **headland is still
   shaded** (§7). Hover adds a fifth leg: **over land → `on land — no data`**.

**9. STILL QUEUED.** **This build's on-phone gate (§8)**; **F2 paint side — the last item in the
arc**; hover-bypass fill-opacity bug; `R1` declared twice; `_idwCache` keyed on `n===s.length` not
`poolVersion`; `WOFS_FREQ_MIN` dead; a fourth `LANDMASK` region for the northern no-op (§3 D1);
F4 fan-mode ruler — **spec still owed by Aaron**; F5 score hygiene; F6 hook-definition card —
**still blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a current official QLD source (hard
rule 4)**; export filename UTC dating; NN-guard class audit; `GateRC`/`GateNoosa` frozen; job (b)
"Here" replaces "Coast-wide"; GPS scouting dot.

**10. NEXT SESSION.** Build **2026.09.05e**, roadmap **v16.76.3**, repo head **`0d486b0`**
plus this entry's own commit. `CLAUDE.md` unchanged. **Next job: run §8's gate, then F2's paint
side.** **Do not re-litigate:** D1's coverage limit or D2's popup (§3, both decided before the code
was written); that tap and hover needed two edits (§2, measured); that the headland is still shaded
(§7, by design).

*v16.76.2 · 5 Sep 2026 — **F1'S ON-PHONE GATE FULLY PASSED, ALL SIX §7 CHECKS. F1 IS NOW
FULLY CLOSED.** Also: concrete, reproducible field evidence for F2's land defect, on a
road, no ambiguity. No build, no code, no data change this entry. Build stays
**2026.09.05d**; repo head unchanged at **63a68bf**.*

**1. CHECK 4 CLOSES — WALK-INLAND SERIES, SIX TAPS, Nudibranch Tip.**

| tap | data away | reading |
|---|---|---|
| 1 | 119 m | dries ≈ 1.5 m |
| 2 | 90 m | dries ≈ 0.2 m |
| 3 | <30 m ("here") | dries ≈ 0.8 m |
| 4 | 29 m | depth ≈ 2.4 m |
| 5 | 26 m | depth ≈ 7.2 m |
| 6 | **81 m, ON WOONGARRA SCENIC DRIVE — the road itself** | dries ≈ 1.7 m |

All five water-side readings reconcile exactly against tide +1.7 m (e.g. tap 1: 1.7 − 1.5
= 0.2 m over it now). **Tap 6 is the finding.** Same 1.7 m value as an earlier 58 m-away
tap this session — consistent with one nearest intertidal sample being returned regardless
of the query point's land status, correctly labelled with a climbing, truthful distance.
Doesn't map cleanly onto any of v16.75.1 §12's four original rows (those predate F1's
working guard) — the value pins, but distance correctly climbs rather than being
suppressed. **That is F1 behaving exactly as designed. The value being meaningless on a
road is squarely F2's unbuilt scope, not a check-4 failure or a regression.**

**2. CHECK 6 (DESKTOP HOVER) — PASS**, per Aaron's direct confirmation running the §7
desktop limb (sounding / 40–60 m / in-zone-far-from-data / out-of-zone-far-from-data). No
screenshot on file for this leg — recorded on Aaron's word, the same standard used for
every prior on-device gate in this project.

**3. F1 IS NOW FULLY CLOSED.** Diagnosis (v16.75.4) → characterisation (v16.75.7, which
rewrote what the defect actually was) → fix across three builds (v16.75.8–.10) → gate,
partial (v16.76.1) → gate, complete (this entry). Cite this entry, not v16.76 or v16.76.1,
as F1's final state.

**4. F2 NOW HAS A CONCRETE REPRODUCTION CASE, NOT JUST A CHARACTERISED MECHANISM.**
Nudibranch Tip, Woongarra Scenic Drive, 81 m from the nearest `dries ≈ 1.7 m` sample,
tapped on the road itself: returns a plausible-looking reading with no land test
performed. **Use this exact tap as F2's on-phone acceptance test** — before: reads a
number on the road; after: should read "no data — on land" or equivalent, gated by
`maskWater()` at the query point, not just at sample admission.

**5. NEXT SESSION.** Build **2026.09.05d** (unchanged), roadmap **v16.76.2**, repo head
**63a68bf** plus this entry's own commit. `CLAUDE.md` unchanged. **Next job: F2's
query-point land test — the last item blocking this arc's full close-out.** Do not
re-litigate: F1 (closed, §3); the arithmetic on the five water-side taps (§1, reconciled
with zero residue).

*v16.76.1 · 5 Sep 2026 — **F1 ON-PHONE GATE PARTIALLY RUN. THREE OF SIX §7 CHECKS PASS (1,
2, 3), PLUS CHECK 5 CONFIRMED INCIDENTALLY. CHECKS 4 AND 6 STILL OUTSTANDING — F1 STAYS
CODE-CLOSED, NOT FULLY CLOSED BY THIS ENTRY.** No build, no code, no data change this
entry. Build stays **2026.09.05d**; repo head unchanged at **3e115ed**.*

**1. RESULTS AGAINST v16.76 §7's VERBATIM SPEC, Nudibranch Tip / Innes Park, shading ON —
BY SCREENSHOT, NOT FIELD IMPRESSION.**
   - **Check 1 (headland tap) — PASS.** Headline read `Nearest reading · 58 m away`; value
     still shown (`dries ≈ 1.7 m`, above LAT, exposed now); fine print carried `not
     measured at this point`. Exact match to spec.
   - **Check 2 (known sounding, Innes Park CPZ06) — PASS.** Nearest data 17 m away — inside
     the 30 m `NEAR_HERE` band — headline read `Est. depth here ≈ 4.1 m`, old "here"
     wording preserved. Fine print's `nearest data 17 m away — rough estimate (LAT) · now`
     is the pre-existing disclosure, not a new element — consistent with §4's "byte-
     identical inside 30 m" claim, not a regression.
   - **Check 3 (offshore, Hervey Bay GUZ07) — PASS.** Read `No survey data within 120 m
     here.`, exact match, correctly updated from the pre-arc 150 m wording.
   - **Check 5 (headland still shaded) — CONFIRMED, incidentally, in the check-1
     screenshot.** The coastal fringe at Nudibranch Tip is visibly shaded despite being
     land. Expected per §5 — F1 never touched the paint side; this is F2's open item, not
     a regression.

**2. NOT YET RUN.** Check 4 (the walk-inland table recording both distance and value at
successive taps, per v16.75.1 §12's four-outcome test) and the desktop/hover limb (check
6: sounding / 40–60 m / in-zone-far-from-data / out-of-zone-far-from-data). **The gate is
not closed until these are in — do not read this entry as F1 reaching full closure.**

**3. ZONE-CARD SPOT CHECK, UNSOUGHT, RELEVANT TO HARD RULES 1–2.** Both CPZ06 (Innes Park,
"Conservation Park (yellow)") and GUZ07 (Hervey Bay, "General Use (light blue)") cards,
observed during this pass, state zone type + ID + restriction text, carry the "simplified
boundary — not authoritative, confirm before fishing" warning, and link to the official
source. No legality assertion in either. Recorded as a live confirmation the hard-rule
wording survives in shipped UI, not because anything changed.

**4. NEXT SESSION.** Build **2026.09.05d** (unchanged), roadmap **v16.76.1**, repo head
**3e115ed** plus this entry's own commit. `CLAUDE.md` unchanged. **Next job: finish
§7's gate — checks 4 and 6 — before any further code.** Do not re-litigate checks 1/2/3/5,
settled here by screenshot evidence.

*v16.76 · 5 Sep 2026 — **THE F1 ARC IS CLOSED AS SHIPPED WORK. NO FURTHER F1 CODE IS
PLANNED.** Build **`2026.09.05d`**, repo head **`4c17bbe`** plus this entry's commit. Four builds
and seven roadmap entries in one day. **THE ON-PHONE GATE IS STILL NOT RUN — F1 IS CLOSED ON CODE,
NOT ON VERIFICATION**, and this entry does not claim otherwise. Same posture as v16.75, which also
shipped code with its gate outstanding and said so in its own header.*

**1. WHY THIS IS A VERSION BUMP AND NOT ANOTHER `.x`.** The 5 Sep run closed one defect (F3),
characterised a second to the line (F2), and shipped a third across three builds (F1) — and the
middle one **rewrote what the third defect actually was** before a line of it was written. That is
an arc, not an increment.

**2. THE ARC, IN ORDER.**

| # | entry | what happened | state |
|---|---|---|---|
| F3 | v16.75.2 → .6 | zone fill dimmed on the global shading flag; fixed with a per-polygon coverage bitmap (`2026.09.05a`, `3cc831d`) | **CLOSED — on-phone gate PASSED, all four checks** |
| F2 | v16.75.7 | characterisation spike, read-only | **CHARACTERISED — not fixed, deliberately** |
| F1 | v16.75.8 → .10 | shipped across three builds (`b`, `c`, `d`) | **CODE CLOSED — gate unrun** |

**3. F2 IS THE REASON F1 SHIPPED AS SOMETHING DIFFERENT FROM WHAT WAS LOGGED.** The standing F1
finding (v16.75.1 §12) said the point query had **no maximum-distance guard**. It had one — a bare
150 m at `openDepthRead()`. The field observation was *"data 35 m away"*, and **35 passes 150**, so
the logged fix would have been a no-op against the observed symptom. F2's spike caught that before
any code was written. **This is the single most valuable thing the day produced**, and it came from
a read-only session that was explicitly forbidden to fix anything.

F2 also resolved the standing contradiction: `maskWater()` is a **sample-admission** filter (one
call site, on a stored sample's own coordinates), while both observed defects are **query-side**.
v16.52/53's "wired at five call sites" and F2's "not consulted at either site" were **both true, on
different axes.** Neither record needed correcting.

**4. WHAT F1 ACTUALLY SHIPPED, ACROSS THREE BUILDS.**

| build | commit | change |
|---|---|---|
| `2026.09.05b` | `bed3d37` | `NEAR_MAX` 150→120 (= `R1`, so read extent and paint extent agree); `NEAR_HERE`=30 (= `R0_MIN`); headline carries the distance instead of asserting "here"; value still shown |
| `2026.09.05c` | `3de36ca` | hover joins the tap — constants hoisted to module scope, one definition; hover's own bare 150 **and** its second bare 120 retired; in-zone 120–150 m band stops showing a number |
| `2026.09.05d` | `3c36e29` | map-click gate and slope chain name `NEAR_MAX`; identity swap, no behaviour change |

Net: **two named constants replaced five bare literals across four call sites**, and no bare
distance literal remains on any read path. Readings inside 30 m are worded **byte-identically to
before the arc** — the fix is entirely about what is claimed beyond 30 m.

**5. WHAT F1 DID NOT FIX, STATED SO NOBODY LATER READS "CLOSED" AS "SOLVED".** F1 is **distance-only**.
The readout still has **no land test at the query point**. A sounding 35 m away across a rock
headland and one 35 m away over open water remain indistinguishable — what changed is that neither
is called "here". **The paint side is untouched and still shades the headland out to 120 m.** The
real fix for the land case is F2's query-point land test, still unbuilt: `maskWater()` exists,
already holds correct data at the failing headland (v16.75.7 §8b, coastline resolved at lng
152.4790), and is asked nothing at query time.

**6. THE ARC DID NOT TRIP ITS OWN SEQUENCING WARNING.** v16.75.1 §13 warned an F1 guard would
suppress the headland reading and make F2 harder to detect. **It didn't** — the reading is
relabelled, not suppressed, so the four-outcome walk-inland test (v16.75.1 §12) remains fully
available with both numbers on screen. Sequencing F2 before F1 was correct and the risk it guarded
against did not materialise.

**7. THE ONE OUTSTANDING LIMB — THIS IS WHAT "NOT ON VERIFICATION" MEANS.** F1's on-phone gate
(v16.75.8 §9) is **unrun and now covers three builds**, two of which changed user-visible wording.
Verbatim, at Nudibranch Tip / Innes Park with shading ON:
   (1) tap the headland — headline must read `Nearest reading · N m away`, **never** "Est. height
   here"; the value must still be shown; fine print must carry `not measured at this point`;
   (2) tap directly on a known pin/sounding — must still read `Est. height here`/`Est. depth here`
   with the old wording;
   (3) tap well offshore of any data — `No survey data within 120 m here.` (was 150);
   (4) **record both numbers at every tap walking inland** — §12's table is still live;
   (5) confirm the headland is **still shaded** — expected, §5.
   Desktop limb (hover, `2026.09.05c`): hover over a sounding → wording unchanged; 40–60 m off →
   gains `· N m away`; inside a zone far from data → `no survey data here`; outside a zone far from
   data → tooltip hidden.
**When that gate passes, amend this entry to full closure. Until then F1 is code-complete only.**

**8. VALIDATION ACROSS ALL FOUR BUILDS.** Every build: both script blocks `node --check` clean;
inlined Leaflet block **byte-identical at 147,552 bytes**, SHA-256 `db49d009…641a`, matching the
`CLAUDE.md` pin on every one; `zoneAt()` and the green-zone `dragend` safeguard absent from every
diff; two `<script>` + two `<style>` blocks throughout. Four Pages runs, all completed/success, all
four build strings confirmed live. Behavioural harnesses, all extracting the live lines from
`index.html` rather than restating them: tap **12/12**, hover **9/9**, paint-alpha purity **6,005
pairs**, mask coastline decode, scope/TDZ enumeration. All still pass at head.

**9. HOUSEKEEPING FROM THE ARC, LOGGED NOT FIXED.** `WOFS_FREQ_MIN` (`:2832`) is dead — one
reference, its own declaration, and its "retune here only" comment is false without a re-bake.
`R1` is declared **twice** (`buildShade()` `:2439`, `buildAutoContours()` `:3049`). `_idwCache` is
keyed on `n===s.length`, not `poolVersion`. `NEAR_MAX` and `R1` are numerically equal and
**deliberately separate** — unifying them couples the readout to the renderer, a decision rather
than a tidy-up. Two unrelated things in the file are still called "mask".

**10. STILL QUEUED.** **F1's on-phone gate (§7) — blocking F1's full closure**; F2 query-point land
test (**the real fix for the land case**, read side and paint side, or one shared test);
hover-bypass fill-opacity bug; `R1` declared twice; `_idwCache` keying; `WOFS_FREQ_MIN` removal;
F4 fan-mode ruler — **spec still owed by Aaron, do not reconstruct**; F5 score hygiene; F6
hook-definition card — **still blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a current
official QLD source (hard rule 4)**; export filename UTC dating; NN-guard class audit (line numbers
v16.75.7 §10); `GateRC`/`GateNoosa` frozen; job (b) "Here" replaces "Coast-wide"; GPS scouting dot.

**11. NEXT SESSION.** Build **2026.09.05d**, roadmap **v16.76**, repo head **`4c17bbe`** plus this
entry's commit. `CLAUDE.md` unchanged. **Next job: run §7's gate. Not more code** — four builds have
shipped since the last phone check and three of them are unverified. Then F2's query-point land
test. **Do not re-litigate:** F3 (closed and gated); F2's answer (§3, settled by measurement); the
values 30 and 120 (v16.75.8 §1, both sourced from existing constants); that F1 is distance-only
(§5, by design); that `NEAR_MAX` and `R1` stay separate (§9).

*v16.75.10 · 5 Sep 2026 — **NO BARE DISTANCE LITERAL LEFT ON ANY READ PATH. BUILD
`2026.09.05d`, COMMIT `3c36e29`** on top of `715e6e0` (roadmap v16.75.9). Pushed; Pages run
`33933828183` completed/success, live site confirmed serving `2026.09.05d`. Closes the item
v16.75.9 §5 logged deliberately one build earlier. **Identity swap — no behaviour change at any
distance, in any branch.***

**1. THE CHANGE.** Both sites already held the correct number; what changed is that it now has one
definition instead of three copies.

| site | was | is |
|---|---|---|
| `:1905` slope chain | `r.near<=120` | `r.near<=NEAR_MAX` |
| `:2990` map-click gate | `r.near<=120` | `r.near<=NEAR_MAX` (+ the comment above it, which spelled the number out in prose) |

**`grep -c 'near<=120\|near>120\|near<=150\|near>150'` now returns 0.** The only read-side literal
left is **80 m** — `findDeepest()`'s cutoff and the hover's roughness marker — a genuinely
different threshold, deliberately left alone.

**2. THE FORWARD-REFERENCE QUESTION, VERIFIED RATHER THAN ASSUMED.** The slope-chain reference sits
**~1,050 lines ABOVE** the `const` it now names, and `node --check` cannot see a TDZ error. It is
safe because the reference is inside a `map.on('click')` handler body — evaluated on click, long
after module evaluation, so no TDZ window exists at that point. Checked by harness
(`scratchpad/f1_scopetest.js`), which enumerates every `NEAR_HERE`/`NEAR_MAX` reference, classifies
each as before/after the declaration and code/comment, confirms **the only forward code reference is
`:1907`** and that it is enclosed by the handler at `:1903`, and reproduces the deferred-reference
pattern to show it resolves. The two other apparent "forward" hits are lines inside the hoisted
`/* F1 … */` comment block.

**3. RECORDED IN THE CODE, NOT ACTED ON — `NEAR_MAX` AND `R1` STAY SEPARATE.** They are numerically
equal (both 120) and remain **separate declarations**: one is how far a reading may be reported
from, the other bounds the painted footprint. They agree today; **unifying them would couple the
readout to the renderer — a decision, not a tidy-up**, and it is not this build's to make. Noted in
the same comment: **`R1` itself is declared twice**, in `buildShade()` (`:2439`) and
`buildAutoContours()` (`:3049`). Logged, not touched.

**4. THE THRESHOLD-PROLIFERATION ITEM IS NOW CLOSED ON THE READ SIDE.** Its arc across four
entries: v16.75.7 §11b logged **five** distinct thresholds across six consumers of one pool →
v16.75.8 cut it to four → v16.75.9 to three → this build leaves **two named constants
(`NEAR_HERE`=30, `NEAR_MAX`=120) and one unnamed 80 m** that is a real, separate threshold. **The
paint side is untouched and still carries its own `R1`, twice** (§3).

**5. VALIDATION.** Both script blocks `node --check` clean. Leaflet block **byte-identical**,
147,552 bytes, SHA-256 `db49d009…641a`, matching the `CLAUDE.md` pin. `zoneAt()` and the
green-zone `dragend` safeguard **absent from the diff entirely**. Both behavioural harnesses still
pass unregressed — tap **12/12**, hover **9/9** — which is the check that matters for an identity
swap: the numbers did not move. **Diff: 13 insertions, 6 deletions, 4 hunks.**

**6. NO ON-PHONE GATE OF ITS OWN.** An identity swap has no observable behaviour to gate. It
inherits F1's outstanding gate and adds nothing to it.

**7. FOUR BUILDS HAVE NOW SHIPPED ON 5 SEP AND NONE HAS BEEN GATED ON THE PHONE.**
`2026.09.05a` (F3 zone-fill coverage — gated, PASSED, v16.75.6), then **`b` (F1 readout), `c`
(hover), `d` (literals) — all three ungated.** `b` and `c` both changed user-visible wording; `d`
did not. **This is the largest ungated stack this project has carried**, and it is stacked on the
one limb (the readout) that a phone screenshot verifies fastest. **Recommend running F1's gate
(v16.75.8 §9) before any further code.**

**8. STILL QUEUED.** **F1's on-phone gate (v16.75.8 §9) — unrun, blocking F1's closure, and now
covering three builds**; F2 query-point land test (the real fix for the land case); `R1` declared
twice (§3); hover-bypass fill-opacity bug; F4 fan-mode ruler — spec still owed by Aaron; F5 score
hygiene; F6 hook-definition card — blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a current
official QLD source (hard rule 4); export filename UTC dating; NN-guard class audit (line numbers
v16.75.7 §10, plus `_idwCache`'s `n===s.length` keying); `WOFS_FREQ_MIN` removal;
`GateRC`/`GateNoosa` frozen; job (b) "Here" replaces "Coast-wide"; GPS scouting dot.

**9. NEXT SESSION.** Build **2026.09.05d**, roadmap **v16.75.10**, repo head **`3c36e29`** plus this
entry's commit. `CLAUDE.md` unchanged. **Next job: run F1's on-phone gate (§7) — not more code.**
Then the F2 query-point land test. **Do not re-litigate:** that this build changed no behaviour
(§1, identity swap); the forward reference (§2, verified); keeping `NEAR_MAX` and `R1` separate
(§3, deliberate).

*v16.75.9 · 5 Sep 2026 — **HOVER READOUT BROUGHT INTO LINE. BUILD `2026.09.05c`, COMMIT
`3de36ca`** on top of `05f9857` (roadmap v16.75.8). Pushed; Pages run `33933487527`
completed/success, live site confirmed serving `2026.09.05c`. Closes the item v16.75.8 §10 logged one
build earlier: the desktop hover was still on a bare 150 m after F1 fixed only the tap.*

**1. WHAT WAS ACTUALLY WRONG — WORSE THAN THE ONE NUMBER LOGGED.** v16.75.8 §10 recorded "hover
threshold `:3832` still 150 m". Re-reading it to fix that turned up a **second** bare literal in the
same function: the hover's *visibility* gate held its own `120`, separate from its *text* gate's
`150`. **Two literals for the same question inside one handler, one of them already disagreeing
with the tap it was written to mirror** (the comment above it says "mirrors the depth-shading paint
rule"). The logged item was the smaller half.

**2. THE FIX — ONE DEFINITION, NOT A SECOND COPY.** `NEAR_HERE=30` and `NEAR_MAX=120` are **hoisted
out of `openDepthRead()` to module scope**, so the two readouts share one definition rather than
the hover growing its own pair. Both hover gates now name the constants. The hover's reading gains
the same distance rule as the tap: past `NEAR_HERE` the tooltip states how far the reading actually
came from instead of presenting it as the value under the cursor. The pre-existing `~` roughness
marker (>80 m) is untouched and still trails the line. A stale comment citing a bare 120 was
corrected to name the constant.

**3. BEHAVIOUR CHANGE, PRECISELY — ONE BAND MOVES.**

| context | 0–30 m | 31–120 m | 120–150 m | >150 m |
|---|---|---|---|---|
| inside a zone polygon | unchanged | value **+ `· N m away`** *(new)* | **`no survey data here`** *(was: a number)* | unchanged |
| outside a zone polygon | unchanged | value **+ `· N m away`** *(new)* | tooltip hidden (unchanged) | tooltip hidden (unchanged) |

**The 120–150 m band inside a zone is the actual defect closed**: the renderer paints nothing past
120 m, so the hover was putting a number over unpainted water. **Inside 30 m the tooltip is
byte-identical to before this build.**

**4. VALIDATION.** Both script blocks `node --check` clean. Leaflet block **byte-identical**,
147,552 bytes, SHA-256 `db49d009…641a`, matching the `CLAUDE.md` pin. `zoneAt()` and the
green-zone `dragend` safeguard **absent from the diff entirely**. **No bare 150 threshold remains
on any readout path** (`grep -c 'near>150\|near<=150'` = 0). Two harnesses extract the live lines
from `index.html` and drive them: the tap's **12/12 still pass unregressed after the hoist**, and
the hover's **9/9 pass** across both `inZ` states and both tier boundaries
(`scratchpad/f1_labeltest.js`, `f1_hovertest.js`). **Diff: 27 insertions, 22 deletions, 6 hunks** —
two build strings, the constant block moving up 15 lines (an insertion hunk and a deletion hunk of
the same block, dedented, comment amended), and two hunks in the hover.

**5. THE FOUR-THRESHOLDS ITEM IS NOW A THREE-THRESHOLDS ITEM.** v16.75.7 §11b logged five distinct
distance thresholds across six consumers of one pool; v16.75.8 cut it to four. Remaining: **80 m**
(`findDeepest()`, and the hover's roughness marker), **120 m** (`NEAR_MAX` — tap gate, hover gates,
map-click gate, slope chain, and `R1` itself), **30 m** (`NEAR_HERE`). The map-click gate and the
slope chain still carry their own bare `120` literals rather than naming `NEAR_MAX` — **left
deliberately, not overlooked**: they are different functions and this build was scoped to the
hover. Logged for the sweep.

**6. ON-PHONE GATE — DESKTOP-ONLY LIMB, SO IT IS A DESKTOP CHECK.** The hover-readout does not exist
on the phone (`mousemove`). Verify at a desktop browser with shading ON: (1) hover directly over a
sounding — tooltip wording unchanged from before; (2) hover 40–60 m off — tooltip gains
`· N m away`; (3) hover inside a zone polygon well away from data — `no survey data here` rather
than a number; (4) hover outside any zone well away from data — tooltip hidden. **F1's own phone
gate (v16.75.8 §9) is still unrun and still governs — this entry does not close it.**

**7. STILL QUEUED.** **F1's on-phone gate (v16.75.8 §9) — unrun, blocking F1's closure**; F2
query-point land test (the real fix for the land case — read side and paint side, or one shared
test); bare `120` literals at the map-click gate and slope chain (§5); hover-bypass fill-opacity
bug; F4 fan-mode ruler — spec still owed by Aaron; F5 score hygiene; F6 hook-definition card —
blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a current official QLD source (hard rule 4);
export filename UTC dating; NN-guard class audit (line numbers v16.75.7 §10, plus `_idwCache`'s
`n===s.length` keying); `WOFS_FREQ_MIN` removal; `GateRC`/`GateNoosa` frozen; job (b) "Here"
replaces "Coast-wide"; GPS scouting dot.

**8. NEXT SESSION.** Build **2026.09.05c**, roadmap **v16.75.9**, repo head **`3de36ca`** plus this
entry's commit. `CLAUDE.md` unchanged. **Next job: run F1's on-phone gate (v16.75.8 §9) — three
builds have now shipped on 5 Sep and none of the three has been gated on the phone.** Then the F2
query-point land test. **Do not re-litigate:** the values 30 and 120 (v16.75.8 §1); the hoist
(§2 — one definition is the point); that the 120–150 m in-zone band now reads "no data" (§3, that
is the fix, not a regression).

*v16.75.8 · 5 Sep 2026 — **F1 SHIPPED AS BUILD `2026.09.05b`. ON-PHONE GATE NOT YET RUN —
F1 IS NOT CLOSED.** Commit `bed3d37` on top of `a04e189` (roadmap v16.75.7). Pushed; Pages run
`33933016948` completed/success, live site confirmed serving `2026.09.05b`. Scope was the
readout only, as re-defined by v16.75.7 §7: **retune `:2941`'s threshold and fix the "here" label.**
Not "add a missing guard" — there was never a missing guard.*

**1. THE CHANGE — TWO BARE NUMBERS BECOME TWO NAMED CONSTANTS, NEITHER INVENTED HERE.**

| constant | was | is | where the figure comes from |
|---|---|---|---|
| `NEAR_MAX` | bare `150` | **120** | `buildShade()`'s `R1` — the hard stop past which the shading paints nothing (`distA`), and already the map-click gate's own figure |
| `NEAR_HERE` | *did not exist* | **30** | `R0_MIN` — the tightest per-sample radius `buildShade()` uses, i.e. the radius inside which the file already treats one sounding as representing the point outright (alpha=1) |

**At 150 the readout claimed data in a band where the renderer draws none**, and where the
map-click gate (`≤120`) would not have opened the popup for a bare map tap — three numbers for one
question. Now one. **Paint extent and read extent agree exactly.**

**2. THE LABEL.** The headline now carries the distance itself — `Nearest reading · 35 m away` —
instead of asserting "here" and leaving the correction to 9.5 px of fine print. That headline-wins-
the-reader's-attention disagreement *was* the defect (v16.75.1 §12). **The value is still shown,
unchanged.** Nearest-neighbour returns a real stored reading; suppressing it would throw away the
good offshore data (63 m → +0.1 m, 118 m → 3.9 m, monotonic) that was never the defect. Inside
30 m the wording is **byte-identical to before this build** — close readings did not regress.

**3. A SECOND-PASS REFINEMENT THE HARNESS CAUGHT, NOT THE READING.** First cut left the distance
printed **twice** — headline and fine print — which in a 170 px popup costs a wrapped line. Each
branch now states it exactly once: when `hereOK` the headline says "here" and the fine print carries
the figure (unchanged); when it doesn't, the headline carries the figure and the fine print drops it
for `· not measured at this point`. Worth recording that the *first* version passed `node --check`
and all twelve assertions — it was legible output, not a failing test, that exposed it.

**4. WHAT THE READER NOW SEES, BY DISTANCE** (from the harness, which extracts the live lines):

| nearest sample | headline | fine print |
|---|---|---|
| ≤ 30 m | `Est. height here` / `Est. depth here` | `… · data N m away` (unchanged) |
| 31–120 m | `Nearest reading · N m away` | `… · not measured at this point` (+ `low confidence` past 80 m) |
| > 120 m | *nothing* | `No survey data within 120 m here.` |

**5. THIS DOES NOT HIDE F2's EVIDENCE — THE STATED SEQUENCING RISK IS NOT TRIPPED.** v16.75.1 §13
warned that an F1 guard would suppress the headland reading regardless of whether a land mask is
consulted, making F2 harder to detect. **It doesn't, because the reading is not suppressed** — at
35 m the headland still returns `dries ≈ 1.7 m`, now labelled honestly. The discriminating
walk-inland test (v16.75.1 §12's four-outcome table) **remains fully available**: both numbers are
still on screen at every tap. Sequencing held, and the risk it guarded against did not materialise.

**6. DELIBERATE LIMIT, WRITTEN INTO THE CODE COMMENT SO IT CANNOT BE MISREAD LATER.** This fix is
**distance-only.** The readout still has no land test at the query point (F2, v16.75.7 §1-§6). A
sounding 35 m away across a rock headland and one 35 m away over open water remain
indistinguishable — **what changed is that neither is called "here".** The query-point land test
(`maskWater()` at `:2850`, which already holds correct data at this exact headland — v16.75.7 §8b)
is still unbuilt and still the real fix for the land case.

**7. THE PAINT SIDE IS UNTOUCHED AND STILL PAINTS THE HEADLAND.** `:2579`/`:2592` were out of scope
this build — one variable per build. Shading still covers anything within 120 m of a pooled sample,
rock or not. **Expect the headland to still be shaded on-phone; that is not an F1 regression**, it is
F2's other half, unfixed by design.

**8. VALIDATION.** Both script blocks `node --check` clean. Leaflet block **byte-identical**,
147,552 bytes, SHA-256 `db49d009…641a`, matching the `CLAUDE.md` pin. `zoneAt()` and the
green-zone `dragend` safeguard **absent from the diff entirely** (`git diff | grep -c` = 0).
Harness `scratchpad/f1_labeltest.js` extracts the live constant, guard and label lines from
`index.html` and drives both branches across 0–180 m: **12/12 assertions pass**, both tier
boundaries (30/31, 120/121) exercised. **Diff: 33 insertions, 5 deletions, 4 hunks** — two build
strings and two mid-file hunks in `openDepthRead()`. The two `build 2026.09.05a` strings inside
F3's comments at `:1271`/`:2218` were **deliberately not bumped**: they record when F3 shipped.

**9. ON-PHONE GATE — MANDATORY, NOT YET RUN. F1 STAYS OPEN UNTIL IT IS.** At Nudibranch Tip /
Innes Park, shading ON:
   (1) tap the headland — headline must read `Nearest reading · N m away`, **never** "Est. height
   here"; the value must still be shown; fine print must carry `not measured at this point`;
   (2) tap directly on a known pin/sounding — must still read `Est. height here`/`Est. depth here`
   with the old wording, i.e. close readings did not regress;
   (3) tap well offshore of any data — must read `No survey data within 120 m here.` (was 150);
   (4) **record both numbers at every tap walking inland** — v16.75.1 §12's four-outcome table is
   still live and this build deliberately preserved the evidence for it;
   (5) confirm the headland is **still shaded** — expected, see §7.

**10. STILL QUEUED.** F2 query-point land test (**the real fix for the land case** — `:2941` read
side and `:2592` paint side, or one shared test); hover threshold `:3832` still **150 m**, now
inconsistent with the tap's 120 — **new, logged this build**, small; hover-bypass fill-opacity bug;
F4 fan-mode ruler — spec still owed by Aaron; F5 score hygiene; F6 hook-definition card — blocked
on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a current official QLD source (hard rule 4); export
filename UTC dating; NN-guard class audit (line numbers in v16.75.7 §10, plus `_idwCache`'s
`n===s.length` keying); five-thresholds item (v16.75.7 §11b — **now four**: 80/120/120/150);
`WOFS_FREQ_MIN` removal; `GateRC`/`GateNoosa` frozen; job (b) "Here" replaces "Coast-wide"; GPS
scouting dot.

**11. NEXT SESSION.** Build **2026.09.05b**, roadmap **v16.75.8**, repo head **`bed3d37`** plus this
entry's commit. `CLAUDE.md` unchanged. **Next job: run §9's on-phone gate before anything else — F1
is shipped, not closed.** Then the F2 query-point land test. **Do not re-litigate:** the choice of
30 and 120 (§1, both sourced from existing constants); showing the value rather than suppressing it
(§2); that the paint still covers the headland (§7, by design).

*v16.75.7 · 5 Sep 2026 — **F2 CHARACTERISED. THE CONTRADICTION RESOLVES AS: BOTH RECORDS
ARE TRUE, ON DIFFERENT AXES.** Read-only spike, Sonnet dispatch. No build, no code, no data change.
Build stays **2026.09.05a**; repo head **`7e88991`** — correcting v16.75.6 §5, which recorded
`3cc831d` because it was written before its own commit landed. `index.html` is byte-identical to
`3cc831d` (`git diff --stat 3cc831d..HEAD -- index.html` empty), so the audited code state is the
intended one. Full write-up: `scratchpad/f2_characterisation.md`.*

**1. THE ANSWER — THE MASK IS NOT ABSENT, AND IT IS NOT DEFEATED.** Not by the HAT gate, not by the
R0/R1 ramp, not by a stale cache key, not by an early short-circuit. It is **present, correctly
wired, carrying correct data at the exact failing headland, and structurally incapable of gating
either site**, because **`maskWater()` is a SAMPLE-ADMISSION filter and both defects are
QUERY-SIDE.** It is only ever asked about a stored sample's own coordinates — never about the point
the user tapped or the pixel being painted.

**2. DOWN TO THE LINE.** `maskWater()` declared `index.html:2850`; **exactly one call site,
`:2889`** (inside `okMASK`); `okMASK` itself **exactly one call site, `:2894`** — the `imported[]`
loop inside `depthSamples()`. Its arguments there are `imported[i][0], imported[i][1]`: **the
sample's** lat/lng. `idwDepthAt(lat,lng)` (`:2929`) and `buildShade()`'s pixel loop
(`:2570`-`:2594`) both hold a query coordinate and **neither passes it to `maskWater()`.**
Whole-file reference count for `maskWater`: **2** — its declaration and that one call.

**3. SO BOTH RECORDS STAND.** v16.52/53 ("wired, additive to the HAT gate, reaching five call sites
via the shared pool, memoised on `poolVersion`") is **accurate as written — for sample admission.**
The standing F2 finding ("exists and is not consulted at either site") is **accurate in effect —
for query gating.** The file has no line doing what F2 assumed was missing, and no line doing what
a reader of v16.52 would assume was present. Neither entry needs correcting; they were describing
different axes and nobody had said so.

**4. THE FIVE CALL SITES SHARE THE MASK ONLY BY SHARING THE POOL — THERE IS NO PER-SITE MASK CODE.**
`buildShade()` `:2419`; tap-to-read `:2940`→`:2929`→`:2919`; `findDeepest()` `:2975`→ same;
`buildAutoContours()` `:3004`; desktop hover `:3828`→ same. (Sixth consumer: the slope-chain tool,
`:1905`.) Inside `depthSamples()`: `:2892` own pins and `:2893` own contours are `okHAT` only —
**never mask-tested at all, by construction, not by configuration**; only `:2894` imported points
are, and only when not exempt.

**5. `REGION_MASK_EXEMPT` IS A RED HERRING AT THIS HEADLAND.** `:2725` =
`{woongarra:1, maroochy_noosa:1}`, but v16.55 already recorded there is **no `woongarra`-tagged
dataset on device** — all Bargara-area data sits in `legacy_unknown` (55,660 pt), which is **not**
exempt. Bargara imports **are** mask-tested, and they passed. Do not re-open the exemption list as
a suspect.

**6. SAME ROOT CAUSE, TWO ENFORCEMENT POINTS — ONE MECHANISM, NOT ONE DIFF.** Both the headland
readout and the headland paint come from **a query gate deciding on distance alone, with no land
test at the query point.** But that decision is made at two independent lines in two independent
functions with two thresholds already in place: **`:2941`** (`if(!r||r.near>150)`, the readout's
entire gate) and **`:2579`/`:2592`** (`distA`/`maskA`, hard stop `R1=120 m`). One *mechanism*
serves both; one *diff* does not. Stated the F3 way: this is not "the code branch differs" — it is
`:2941` and `:2592` each independently deciding on `near` alone, while the only land evidence in
the file sits at `:2889` gating a different quantity entirely.

**7. F1's PREMISE IS WRONG AT HEAD AND MUST BE CORRECTED BEFORE IT IS FIXED.** v16.75.1 §12 records
"point query has no maximum-distance guard". **It has one.** `openDepthRead()` `:2941` carries a
**150 m** guard with the copy *"No survey data within 150 m here."*; the desktop hover carries the
same threshold at `:3832`. The field observation was *"data 35 m away"* — **35 m passes a 150 m
guard.** F1's fix shape is therefore **retune the existing threshold and fix the "here" label**,
not "add a missing guard". Adding a guard that already exists would be a no-op against the observed
symptom. This is the single most load-bearing correction in this entry.

**8. FALSIFIABLE CHECKS — BOTH RUN, BOTH PASS, ZERO RESIDUE.**
   (a) *Prediction: the paint alpha is a pure function of distance; the zone mask term `mA` can
   never change a pixel.* Transcribed `:2579`/`:2592`/`:2593`/`:2594` 1:1 and swept **6,005
   `(near, r0)` pairs** (near 0-300 m at 0.25 m, r0 ∈ {30,45,60,75,90}) at `mA=0` vs `mA=1` —
   **identical at every distance.** Anything within **120 m** of a pooled sample paints, land or
   not. The file's own comment at `:2586`-`:2588` argues this from two endpoints; this confirms it
   across the whole domain. Harness: `scratchpad/f2_painttest.js`.
   (b) *Prediction: the mask holds CORRECT land data at the headland and is simply never asked.*
   Extracted `LANDMASK`/`lmBits()`/`maskWater()` verbatim and scanned `maskWater(−24.84089, lo)`
   across the woongarra box (grid 1113×1187, cells ~30.0 m × ~27.2 m): coastline resolved at
   **lng 152.4790**, headland side **land**, seaward **water**, plus two correctly-identified
   inland water bodies. **The mask would have answered correctly had anything asked it.** Harness:
   `scratchpad/f2_masktest.js`.

**9. WHAT THE FILE CANNOT DECIDE — NEEDS THE PHONE, NOT A GUESS.** Which pooled sample sits 35 m
from the headland has two candidate origins: **(i)** an own pin or hand-drawn contour, never
mask-tested (`:2892`/`:2893`), so present regardless of the mask working perfectly; or **(ii)** a
`legacy_unknown` import that legitimately **passed** the mask — e.g. a genuine sounding 35 m
offshore in real water. **Case (ii) requires no mask defect whatsoever**, which is exactly why F2
had to be characterised before F1's guard hid the evidence. Discriminating them needs the
Imported-depths panel region labels plus whether a pin sits near the rock. **Neither origin changes
the root-cause answer** — both produce the same query-side failure through the same two lines.

**10. NN-GUARD-CLASS AUDIT ITEMS RE-LOCATED BY CONTENT — ALL THREE DELTAS RECONCILE TO F3'S HUNKS
WITH ZERO RESIDUE.** `_sampleIndexCache` `:2148`→**`:2155`** (+7, the `:1271` hunk's 1→8 lines);
`distA` `:2523`→**`:2579`** (+56 = 7+45+4); `_idwCache` `:2851`→**`:2918`** (+67 = 7+45+4+5+1+5).
No line moved for any reason other than F3's six insertions. Guard status, **observed not fixed**:
`_sampleIndexCache` is `poolVersion`-keyed and sound; **`_idwCache` is keyed on `n===s.length`
only (`:2924`), not `poolVersion`** — a pool edit preserving the sample count returns a stale index
(the file flags this as deferred at `:2920`-`:2923`; **not** the F2 mechanism, since `buildShade()`
nulls it every rebuild at `:2398`); `distA` has a hard `R1=120 m` stop, so paint *is*
distance-guarded — the gap is that the guard has no land term.

**11. NEW FINDINGS, LOGGED NOT FIXED.**
   (a) **`WOFS_FREQ_MIN` (`:2832`) is dead** — exactly one reference in the file, its own
   declaration. The 0.2 threshold was baked offline by `tools/landmask_build.py`; at runtime the
   bitmap is binary and `maskWater()` only tests a bit. Its comment *"retune here only"* is **false
   as written** — retuning changes nothing without a re-bake.
   (b) **Five different distance thresholds across six consumers of one pool:** `:1905` `≤120`;
   `:2941` `>150`; `:2962` `≤120`; `:2977` `>80`; `:3831`/`:3832` `≤120`/`>150`. Worth an item in
   its own right.
   (c) **Two different things in this file are called "mask".** `shadeMaskFeats()`/`inWaterFast()`/
   `scanlineMask()` (`:1992`/`:2000`/`:2058`) read `ZONES.features` — "inside a legislated
   polygon". `maskWater()`/`LANDMASK` is the OSM/DEA land/water mask. **Only one of them knows
   anything about land**, and the naming collision is how F2's finding and v16.52's record could
   both be recorded in good faith and appear to contradict.

**12. SEQUENCING CONFIRMED BY CONSTRUCTION, NOT MERELY PLAUSIBLE.** v16.75.1 §13's warning holds:
F1's fix touches `:2941`; the headland paint is decided at `:2579`/`:2592` with a 120 m stop.
Tightening `:2941` below 35 m removes the headland *reading* and leaves the headland *paint*
untouched — the app would paint over the rock while saying "no survey data here" at the same pixel,
exactly the end state §13 predicted. **Both lines must move together, or be re-expressed once and
shared.** The natural shared form is a query-point land test: `maskWater()` already exists at
`:2850`, already holds correct data at the failing headland (§8b), and is currently asked nothing
at query time. **That is a fix proposal, not a fix — nothing was implemented.**

**13. SCOPE DISCIPLINE HELD.** `zoneAt()`, `ORDER`, the green-zone `dragend` safeguard and the five
hard rules were not read as part of this and are untouched. Nothing here asserts or bears on
legality — cosmetic paint/read gating only. **F1 was not fixed.** File state confirmed before and
after: tree clean, both script blocks `node --check` clean, Leaflet block 147,552 bytes /
SHA-256 `db49d009…641a` matching the `CLAUDE.md` pin, 2 `<script>` + 2 `<style>` blocks.

**14. STILL QUEUED — F2 characterisation removed, F1 re-scoped by §7.** F1 point-query guard
(**now: retune `:2941`'s 150 m threshold + fix the "here" label, and move `:2592` with it — not
"add a missing guard"**); hover-bypass fill-opacity bug (re-locate by content, F3 shifted it — low
priority); F4 fan-mode ruler — spec still owed by Aaron; F5 score hygiene; F6 hook-definition card
— still blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a current official QLD source (hard
rule 4); export filename UTC dating; NN-guard class audit (**line numbers refreshed in §10 — use
those**, plus the `_idwCache` keying item); the five-thresholds item (§11b); `WOFS_FREQ_MIN`
removal (§11a); `GateRC`/`GateNoosa` frozen; job (b) "Here" replaces "Coast-wide"; GPS scouting
dot (v16.75.2 §12).

**15. NEXT SESSION.** Build **2026.09.05a**, roadmap **v16.75.7**, repo head **this entry's
commit**. `CLAUDE.md` unchanged. **Next job: F1 — but read §6, §7 and §12 first; the dispatch that
produced §12's warning assumed a guard that does not need adding.** Decide up front whether F1
ships as the two-line pair (`:2941` + `:2592`) or as a shared query-point land test, and gate it
on-phone at the same headland. **Do not re-litigate:** whether the mask is wired (§1-§3, settled);
the exemption list as a suspect (§5, cleared); whether the zone mask affects paint (§8a, measured).

*v16.75.6 · 5 Sep 2026 — **F3 CLOSED. ON-PHONE GATE PASSED, ALL FOUR CHECKS.** No build, no code,
no data change this entry. Build stays **2026.09.05a**; repo head unchanged at `3cc831d`.*

**1. GATE RESULTS, against v16.75.5 §6's stated expectations:**
   (1) far zone, no coverage — **PASS**, rendered identically with shading on vs off, as predicted;
   (2) Innes Park/Barolin Rock, real coverage — **PASS**, fill dimmed to the faint wash, outline
       stayed fully legible;
   (3) partial-polygon boundary — **not observed as a problem**, consistent with the disclosed
       bbox-granularity trade-off (v16.75.5 §3);
   (4) pan/`moveend` perf watch — **no hitch felt**, consistent with the change-gated restyle
       costing nothing on pans that don't cross a coverage boundary.

**2. F3 IS NOW FULLY CLOSED — DIAGNOSIS (v16.75.2), CHARACTERISATION (v16.75.2/.3),
FIX (v16.75.5), VERIFICATION (this entry).** From measurement to shipped, verified fix in five
roadmap entries, zero re-diagnosis, zero rebuild. Cite this entry, not any earlier one, as F3's
final state.

**3. STANDING OPERATIONAL RULE RETIRED: "READ ZONING WITH SHADING OFF" NO LONGER APPLIES.**
Zone fill now reads correctly with shading on. Covers Bargara 10–13 September without a
workaround.

**4. STILL QUEUED — carry list refreshed, F3 removed.** Hover-bypass fill-opacity bug
(`index.html:1281` pre-fix line numbers — **re-verify against current file, F3's edits shifted
lines below :1271**; low priority, still unfixed, still separate from F3); F2 land mask; F1
point-query distance guard (never before F2); F4 fan-mode ruler — spec still owed by Aaron; F5
score hygiene; F6 hook-definition card — still blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6
against a current official QLD source (hard rule 4); export filename UTC dating — still open;
NN-guard class audit (`_sampleIndexCache`, `_idwCache`, `distA` — **line numbers stale since F3,
re-locate by content**); `GateRC`/`GateNoosa` frozen; job (b) "Here" replaces "Coast-wide"; GPS
scouting dot (v16.75.2 §12).

**5. NEXT SESSION.** Build **2026.09.05a**, roadmap **v16.75.6**, repo head **`3cc831d`**
(unchanged). `CLAUDE.md` unchanged. **Next job: F2 land mask characterisation, then F1's guard —
never F1 first** (standing sequencing, v16.75.1 §13). **Do not re-litigate:** F3's mechanism,
fix, or gate (§1-§2, closed); the bbox-granularity trade-off (permanent, not a bug); the
shading-off rule is gone, don't reinstate it without a new measured reason.

*v16.75.5 · 5 Sep 2026 — **F3 FIX SHIPPED. ON-PHONE GATE NOT YET RUN — F3 IS NOT CLOSED.** Build
**2026.09.05a**, commit `3cc831d` on top of `7b9db91` (roadmap v16.75.3 sync commit). Pushed,
Pages run completed/success (run `33925599989`), live site confirmed serving `2026.09.05a`.*

**1. THE CHANGE — one gate, two conditions, not a straight swap.** `index.html:1271`, before:
`const fo=_shadeFade?Math.min(s.fillOp,0.06):s.fillOp;`. After:
`const fo=(_shadeFade&&f._shFade)?Math.min(s.fillOp,0.06):s.fillOp;`. **Note this differs from
what was dispatched** (a straight replacement of the global flag) **in a way that's an
improvement, not a deviation to flag as risk:** `_shadeFade` stays the master switch — shading
off still short-circuits with zero bbox tests — and `f._shFade`, a new per-feature flag, adds the
coverage test only when shading is actually on. Clamp value `0.06` and stroke opacity `0.95`
untouched, as scoped.

**2. MECHANISM.** `buildShade()` now retains `_shadeCov` — a 64×64 byte bitmap over the same
lat/lng rect as the image overlay (row 0 = north, matching the paint loop's own `y`). Filled
inside the existing paint loop at negligible marginal cost (one multiply/truncate/add/byte-store
per pixel, in a loop already doing more per pixel than that) — a cell is set at `AL>=0.05`,
deliberately above the paint loop's own `0.01` cutoff so barely-visible edge alpha doesn't count
as coverage. Published only after the overlay swap, so a mid-rebuild throw can't leave stale
coverage; every overlay-removal path nulls it, the rebuild-threw catch path leaves it alone
(previous overlay still showing = previous coverage still true). `applyZoneFade()` walks all 180
zone layers, tests each one's cached `getBounds()` against the bitmap via `zoneCovered()` — O(1)
reject on bbox-disjoint, early-exit scan otherwise — and restyles **only when a flag actually
changed**, so a pan with no coverage change costs 180 bbox tests and zero canvas redraws.

**3. GRANULARITY — disclosed before the build, not discovered after.** The test is per-polygon
**bounding box**, not point-in-polygon: a half-painted zone dims whole, and a concave zone whose
bbox catches paint outside its own boundary also dims. Accepted trade-off — the goal was "don't
dim zones nothing is painted on," not exactness, and the bitmap cell size stays well under
R1=120m so a genuinely painted zone can't be missed by the coarser test.

**4. DIFF SCOPE — `index.html` only, 75 insertions / 8 deletions, 11 hunks.** 3 insertion-only
(new `_shadeCov`/`zoneCovered()`/`applyZoneFade()` block, +45 lines at old `:2210`; the per-pixel
cell write, +1 line at old `:2565`; publish call, +5 lines at old `:2595`). 8 mid-file
replacements (2 build strings; the clamp gate `:1271`, 1→8 lines; `buildShade()`'s head `:2347`,
1→5 lines, retiring the old global restyle; 3 early-return lines `:2356/:2364/:2379`; the paint
loop head `:2562`, 1→6 lines for the bitmap alloc).

**5. VALIDATION — all four standard CLAUDE.md checks plus a new harness, all PASS.**
`node --check` both script blocks; exactly 2 `<script>`/2 `<style>` blocks confirmed (structure
invariant intact); Leaflet block byte-identical, 147,552 bytes, SHA-256 matches the CLAUDE.md pin
exactly; `zoneAt()` (`:1332`) and the green-zone drag safeguard (`:1583-1585`) present and
untouched by any hunk; build string read from the file and bumped (verified no prior `2026.09.*`
shipped). **New: a coverage-mapping harness** (`scratchpad/f3_covtest.js`) pulled `zoneCovered()`
**verbatim** from the file, drove 7 cases (painted quadrant, 3 unpainted quadrants, far-away
reject, whole-rect bbox catch, `_shadeCov===null`) — **7/7 pass**, confirming the fill loop's and
the test's row orientation actually agree (a real risk for a bitmap indexed independently of the
paint loop). Encoding via a Node UTF-8 script, no BOM, no round-trip through PowerShell 5.1's
`Get-Content`/`Set-Content`. `scratchpad/` gitignored throughout, no stray writes.

**6. ON-PHONE GATE — MANDATORY, NOT YET RUN. This is what keeps F3 open.** Four checks, stated
with their expected result so any surprise is legible as a surprise:
   (1) a zone far from any imported soundings renders at normal (shading-off) opacity even with
       shading ON — **expected PASS**, this is the whole point of the fix;
   (2) a zone with real shade over it still dims as before, stroke unchanged — **expected PASS**;
   (3) a shaded/unshaded boundary within the SAME polygon shows no visible difference — **NOT a
       regression to report if seen; this is the disclosed bbox-granularity trade-off from §3**;
   (4) **watch item, not a pass/fail:** pan repeatedly with shading on, check for a new hitch at
       `moveend`. Restyle is change-gated so most pans should cost nothing new; a zone crossing
       the painted footprint's edge costs one coalesced redraw. Given this app's documented
       history of desktop-fine/phone-slow shading surprises, this is worth watching even though
       nothing in the design predicts a regression. If a hitch appears, the fix point is the gate
       in `applyZoneFade()`, not the bitmap itself.

**7. STANDING OPERATIONAL RULE, UNCHANGED UNTIL THE GATE ABOVE PASSES: READ ZONING WITH SHADING
OFF.** Bargara is 10–13 September — close. Running the on-phone gate soon is worth doing precisely
so this constraint can be retired before the trip, not to rush the build itself (the build already
shipped through the normal diagnose-then-implement path, nothing here compresses that).

**8. STILL QUEUED — carry list refreshed.** **F3 on-phone gate (§6, NEXT — do this before
anything else touches shading or zones)**; hover-bypass fill-opacity bug (`:1281`, low, still
separate from F3, still unfixed); F2 land mask; F1 point-query distance guard (never before F2);
F4 fan-mode ruler — spec still owed by Aaron; F5 score hygiene; F6 hook-definition card — still
blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a current official QLD source (hard rule 4);
export filename UTC dating — still open; NN-guard class audit (`_sampleIndexCache` :2148,
`_idwCache` :2851, `distA` :2523 — **note: F3's edits shifted line numbers again, re-verify these
against the current file before citing them**); `GateRC`/`GateNoosa` frozen; job (b) "Here"
replaces "Coast-wide"; GPS scouting dot (v16.75.2 §12).

**9. NEXT SESSION.** Build **2026.09.05a**, roadmap **v16.75.5**, repo head **`3cc831d`**.
`CLAUDE.md` unchanged. **Next job: run the §6 on-phone gate, report all four results explicitly
(including the watch item), then close F3 with a short confirmation entry** — not a re-diagnosis,
not a rebuild, just the verification the fix has been waiting on. **Do not re-litigate:** the
gate's bbox-vs-point-in-polygon trade-off (§3, deliberate); the `_shadeFade && f._shFade`
two-condition shape (§1, an improvement on the dispatch, not a deviation to worry about); the
diff scope and validation (§4-§5, measured, not asserted).

*v16.75.4 · 4 Sep 2026 — **F3 ROOT CAUSE FULLY CHARACTERISED, DOWN TO THE LINE. NO FIX WRITTEN.**
Read-only Claude Code spike (Sonnet), no edits to tracked files, no commit. Build stays
**2026.08.30a**; repo head unchanged at `b49ff94`. Supersedes v16.75.2's "code branch" framing
with the exact mechanism.*

**1. THE ANSWER.** Fill and stroke were never "composited differently" — they never share an
alpha to begin with. `index.html:1271` — `const fo=_shadeFade?Math.min(s.fillOp,0.06):s.fillOp;`
— clamps fill alpha to a variable gated on the global `_shadeFade` boolean. `index.html:1272`
emits the style object with `fillOpacity:fo, opacity:0.95` — fill gets the variable, stroke gets
a hardcoded literal, same call. Leaflet's inlined `_fillStroke` (`:1209-1214`) reads the two
fields into `globalAlpha` in two independent canvas passes. No shared alpha, group node, or
parent opacity would make stroke follow fill.

**2. STYLES TABLE (`:1222-1225`) — shading-off `fillOp` per zone: MNP 0.30, CPZ 0.22, HPZ 0.18,
GUZ 0.14.** Stroke `opacity` is the literal `0.95`, uniform, for all four, always — confirmed by
a full sweep of every `setStyle`/`resetStyle`/`styleFor`/`zoneLayer` site in app code (5 total):
none writes `opacity`.

**3. NO GATE, ANYWHERE, EVER CONSULTS SHADE COVERAGE.** `_shadeFade` is written in exactly one
place (`:2347`, `_shadeFade=shadeOn`) — a direct copy of the global flag. `styleFor(f)` receives
only the GeoJSON feature; it never sees the overlay's bounds, existence, or per-pixel alpha
array. A zone 100 km from the nearest sounding dims identically to one under the densest part of
the overlay. This is the exact mechanism behind the n=611,979 zero-coverage population in
v16.75.2.

**4. THREE FILL-OPACITY CODE PATHS, NOT ONE.** B1 = the clamp (`:1271`, the cause). B2 = hover
emphasis (`:1281`) — **reads `STYLES[...].fillOp` raw, bypassing `_shadeFade` and `styleFor`
entirely**; while shading is ON, hovering a zone jumps fill from 0.06 to `fillOp+0.12` — *above*
the shading-off baseline (GUZ 0.26, MNP 0.42). Logged as a secondary defect, no fix proposed.
B3 = hover release (`:1282`, `resetStyle` → re-runs `styleFor` → correctly inherits B1; not a
defect).

**5. SHADE OVERLAY PHYSICALLY CANNOT COMPOSITE OVER THE ZONE FILL — CONFIRMED FROM
CONSTRUCTION, NOT JUST PIXELS.** Overlay pane `shadePane`, zIndex **350** (`:1934`); zone canvas
is Leaflet's default `overlayPane`, zIndex **400** (no `pane` option at `:1277`). 350 < 400 —
overlay sits strictly beneath the zones regardless of DOM add order. `shadeOp` default 0.75,
clamped [0.25,1]. ImageData alpha is per-pixel, `Math.round(a*235)`, hard 0 below coverage 0.01
(`:2564-2565,2585`) — zero-coverage pixels get exactly zero overlay alpha, not a faint one.

**6. RECONCILES ARITHMETICALLY, NO RESIDUE.** `0.06/fillOp` predicts MNP 20.0% / CPZ 27.3% /
HPZ 33.3% / GUZ 42.9%. v16.75.2's blended 41.7% over a GUZ-dominated 611,979-pixel region backs
out to an area-weighted mean `fillOp` ≈ 0.144 — ≈93-94% GUZ composition, plausible for that view.
**Falsifiable check, NOT YET RUN:** re-measure retention segmented by zone type; line 1271
predicts exactly those four ratios with zero distance-from-sounding dependence. Any zone-
invariant ratio or distance dependence would falsify this diagnosis.

**7. CLEANEST REPRO — ZERO SHADE PIXELS ANYWHERE, ZONES STILL DIM.** `_shadeFade=shadeOn`
(`:2347`) sits above every bail-out in `buildShade()` (`:2356,2364,2379`). Switching shading ON
with <3 soundings: alert fires, function returns at `:2364` having built no overlay at all —
zones still dim to 0.06. Removes compositing from the explanation entirely; isolates `:1271` as
sole cause.

**8. SCOPE HELD.** `zoneAt()` and the green-zone drag safeguard were not read or touched. No
tracked file modified; tree clean at HEAD `b49ff94` throughout. Full report:
`C:\Guya\Guya_Wamu\scratchpad\f3_characterisation.md`, 340 lines.

**9. THE FIX ITSELF IS STILL UNWRITTEN — NEXT F3 DISPATCH, SEPARATE SESSION (diagnose-before-
patch).** Per v16.75.2 §6, gating the clamp on actual shade coverage rather than the global flag
is "the highest-value single edit F3 has, and it costs nothing" — now locatable precisely at
`index.html:1271`. Also carry the §4 hover-bypass defect into the same or a following fix pass;
it is cheap and adjacent but is a **different bug** (reads `STYLES` raw instead of `_shadeFade`-
gated `styleFor`) and must not be silently folded into the F3 commit without saying so.

**10. STILL QUEUED — carry list refreshed.** **F3 fix (§9, NEXT — gate `index.html:1271` on
coverage, not the global flag; separate on-phone gate before/after per standing discipline)**;
hover-bypass fill-opacity bug (§4, low, adjacent to F3 but distinct); F2 land mask; F1 point-
query distance guard (never before F2); F4 fan-mode ruler — spec still owed by Aaron; F5 score
hygiene; F6 hook-definition card — still blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a
current official QLD source (hard rule 4); export filename UTC dating — still open; NN-guard
class audit (`_sampleIndexCache` :2148, `_idwCache` :2851, `distA` :2523); `GateRC`/`GateNoosa`
frozen; job (b) "Here" replaces "Coast-wide"; GPS scouting dot (v16.75.2 §12).

**11. STANDING OPERATIONAL RULE, UNCHANGED: READ ZONING WITH SHADING OFF.** Bargara is 10–13
September. The mechanism is now fully known but **no fix has shipped** — this rule stays in
force until a build closes it, not until the diagnosis does.

**12. NEXT SESSION.** Build **2026.08.30a** (unchanged — this entry ships no code), roadmap
**v16.75.4**, repo head **`b49ff94`** (unchanged). `CLAUDE.md` unchanged. **Next job: F3 fix** —
gate `index.html:1271`'s clamp on per-polygon shade coverage instead of the global `_shadeFade`
flag, as a standalone dispatch with its own diagnose-stated-hypothesis, `node --check`, Leaflet-
hash and on-phone gate. **Do not re-litigate:** the root-cause mechanism (§1-§7, measured and
characterised, not hypothesised); the hover-bypass bug is real but separate (§4); the overlay
cannot composite over the fill regardless of pane order (§5).

*v16.75.3 · 4 Sep 2026 — **MACHINE MOVE COMPLETE AND VERIFIED BYTE-FOR-BYTE. CARRY ITEM (iv)
CLOSED.** No app code, no data, no schema change. Build stays **2026.08.30a**. Head is **`b49ff94`**,
preceded by `543db29` (data/audit), `c2b262d` (.gitattributes) and `2f930dd` (v16.75.2). Three Pages
runs green. Build workflows now live on the laptop; the desktop is retired to archive duty.*

**1. THE NEW MACHINE.** Repo root **`C:\Guya\Guya_Wamu`**, scratchpad
**`C:\Guya\Guya_Wamu\scratchpad`** — state that path **absolutely** in every dispatch (v16.75.1 §s1).
Toolchain: **pwsh 7.6.5**, Git 2.55.0, **Node 24.20.0** (current line, not LTS — recorded so any
future `node --check` oddity is attributable), AMD64. Claude Code installed via npm; **npm 12 blocks
postinstall scripts by default**, so the package needs
`npm install -g --allow-scripts=@anthropic-ai/claude-code` — the one-shot form, never
`npm config set allow-scripts --location=user`, which is the same shape as a session-wide edit grant
and is declined for the same reason.

**2. THE CLONE VERIFIED CLEAN ON THE FIRST ATTEMPT.** Fresh `git clone`, never a directory copy.
Head `543db29`; `git diff --stat` **empty**; `index.html` **4197 lines** and SHA-256
**`BF738E0D9CD4FC70A94F4EDD477175F4CFDC43190A019CCBAD09A7EE7D801288`** — identical to the desktop,
byte for byte; build string `2026.08.30a` present at **both** `:1052` and `:1091`; **23** files under
`data/audit`. **The hash match across two machines is the whole proof** — it is the only check that
would have caught a line-ending conversion, and `git diff` cannot, because it normalises on the way
back.

**3. `.gitattributes` COMMITTED (`c2b262d`), AND IT CAUGHT SOMETHING ON ITS FIRST USE.**
`core.autocrlf` was set **repo-locally** to `input` and **repo-local config does not survive a
clone** — a fresh clone on Windows inherits the system default `true`, checks out CRLF, breaks the
hash check, and shows **nothing** in `git diff`. That is a failure with no visible cause. Pinned with
`* text=auto eol=lf`. On the very next commit it flagged two CRLF files
(`moreton_manifest.json`, `moreton_hyb_manifest.json`) written that way by the original pipeline.
**Written via `[System.IO.File]::WriteAllText` with a BOM-less `UTF8Encoding`** — see §5.

**4. `data/audit/` CREATED (`543db29`) — 23 files, 4.37 MiB, 6,022 insertions. A DELIBERATE
REVERSAL, STATED IN THE OPEN.** v16.18–v16.24 designated these "gitignored scratch". That was correct
while they were mid-process working files; it stopped being correct when the drop-mask shipped.
**They are now the sole evidentiary basis for 40,747 points dropped across BR/SC and 6,861 cells
across Moreton, and they existed in exactly one place, on one disk, in a directory labelled
disposable.** Promoted: `audit_results.json` (2,268 entries), `audit_results.pre_dedupe.bak.json`
(2,282), `audit_results.pre_gap.bak.json` (1,375), `hybrid_mask_cells.json` + `hybrid_manifest.json`
(1,184 tiles each), `audit_manifest.json`, Moreton's own audit (193 tiles, renamed
**`moreton_audit_results.json`** — three files shared that name at different depths), Moreton's mask
+ two manifests, and **13 pipeline scripts** under `data/audit/tools/`.

**Entry counts were reconciled against the roadmap BEFORE promotion, not after:** 1,375 + 907 =
2,282; 2,282 − **14** byte-identical duplicates (v16.23) = 2,268; Moreton 193 (v16.28's
`audit_class2.py` run, PID 1514). **Every figure closed with no unexplained residue.** The scripts
went with them deliberately — the roadmap leans on their exact behaviour repeatedly
(`audit_class2.py` "reused unmodified", `process_tiles.py`'s two approved deviations documented line
by line), and without them the recorded figures can be trusted but not reproduced.

**Explicitly NOT the v16.48 failure mode.** That sweep committed
`guya_species_qld_v3.md` against two on-record "project knowledge only, never the repo" notes and
nobody noticed for nine days. This reverses a standing decision **on purpose, with the reasoning
recorded in the same commit**. The distinction is the record, not the action.

**5. STANDING RULE — POWERSHELL 5.1 ENCODING. This is a data-corruption hazard, not a nuisance.**
Windows PowerShell 5.1 reads as cp1252 by default (observed: `.gitignore` rendering an em-dash as
`â€"`) and its `-Encoding UTF8` **writes a BOM**. Two distinct failures follow:
- **`Set-Content -Encoding UTF8 .gitattributes` would have produced a BOM'd file that git's attribute
  parser does not strip** — the first pattern reads `\ufeff* text=auto` and matches nothing. A
  `.gitattributes` that is committed, looks correct in every editor, and does **absolutely nothing**.
- **`(Get-Content .\index.html) | Set-Content .\index.html` would mangle every em-dash in the app's
  visible UI copy** ("lights the seabed from the NW — drop-offs and gutter walls"). `node --check`
  passes. The build-string check passes. Mojibake ships to the phone.
**Never round-trip a repo file through `Get-Content`/`Set-Content`/`Out-File` under 5.1.** Use
`[System.IO.File]::WriteAllText(path, text, (New-Object System.Text.UTF8Encoding $false))`, or
PowerShell 7. **This machine standardises on pwsh.** Now recorded in `CLAUDE.md` at `b49ff94`.

**6. CARRY ITEM (iv) IS CLOSED (`b49ff94`).** Validation check 2 said *"Confirm the inlined Leaflet
block is byte-identical"* — **byte-identical to what?** No reference value was given; the digest
lived only in this file, nine times. Unsatisfiable from `CLAUDE.md` alone, exactly as v16.74 §5
recorded, and it bites hardest on a fresh clone. `CLAUDE.md` now carries the reference adjacent to
the check: body-only SHA-256
**`db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`**, `<script>`/`</script>` tags
excluded, **147,552 bytes**.

**Claude Code recomputed the digest from `index.html` at HEAD before writing it, rather than
accepting the dispatched constant** — the right instinct, and the standing skepticism rule applied to
a value handed to it by the dispatch. It also recorded the **with-tags** digest
`156fc90aa436d569480491a5009458ac1375630726e3fe096059305f6565fc58` (147,569 bytes) for
disambiguation, and confirmed the span has no boundary ambiguity: `<script>` is immediately followed
by `/* @preserve` with no newline, and `</script>` immediately follows `leaflet.js.map`. **The byte
count was added beyond the dispatch text, declared as a deviation** — a second independent tripwire
on the same span, checkable without running a hash. Accepted.

**7. THE PIN NOW EXISTS IN TWO PLACES, AND THAT IS A FORK WAITING TO HAPPEN.** `CLAUDE.md` (one
occurrence, **operative**) and `GUYA_ROADMAP.md` (nine, **historical record**). A Leaflet version bump
would have to update ten sites or check 2 starts failing against a stale reference. **Standing: on any
future Leaflet upgrade, `CLAUDE.md` is the single source of truth and roadmap occurrences get
`[SUPERSEDED]` tags, not edits.** No upgrade is planned, so this is not urgent — it is exactly the
kind of thing that stays invisible until it fails.

**8. DISPATCH FAULT, RECORDED — THE PLANNING CHAT'S, NOT THE MODEL'S.** The first laptop dispatch
stated it *"closes carry item (iv)"* **and** forbade touching `GUYA_ROADMAP.md`. Both instructions
correct in isolation, incompatible together: the edit shipped while the roadmap still showed the item
open, so the two files disagreed about its state until this entry. **Claude Code caught it and
flagged it unprompted.** The standing rule already says red-team a dispatch before sending; this
sharpens it — **check a dispatch against itself for internal contradictions, not only for whether
what it asks is correct.** Two individually-correct instructions can be jointly unsatisfiable, and
that is invisible when each is read on its own.

**9. `data/raw/` — 217.1 GiB, 265 files — MOVED TO `D:\Guya_raw_archive\`. NOT DELETED.** Still
gitignored, out of the repo path. Breakdown: Sunshine-Coast 119.6 GiB / 17 files, Brisbane-River 90.6
/ 3, `_inventory` 4.6 / 128, Bathymetric-LiDAR-SC 2.1 / 45, Gold-Coast 0.2 / 1, three spike dirs ~0 /
67. **By the letter of the disposal rule the SC/BR bulk (96.8%) is disposable** — the
class-9-adjacency audit, the drop-mask, the v2 CSVs and the confirmed on-device REPLACE all completed
(v16.17–v16.28, field-verified v16.52). **Kept anyway**, because a future SC/BR **v3 re-export** is
the recorded vehicle for the Option 3 STRICT-AND land mask, and ELVIS is order-and-email-link only
with 48-hour expiry — a multi-day manual slog to reclaim disk on a machine that is not going
anywhere. `Bathymetric-LiDAR-Sunshine-Coast` (the 2011 Fugro LADS green-laser survey) and
`_landmask_spike` (OSM tiles, the MN v3 clip input) are small and irreplaceable in practice.

**10. THE DESKTOP.** Retired at head `543db29`, tree clean, nothing stashed, nothing unpushed.
The rename to a STALE name **failed on a file lock and was abandoned as not worth chasing** — a
`STALE-DO-NOT-USE.txt` marker serves the same purpose and is what a future Claude Code session
opening that directory would actually see. **The protection was never the folder name**: everything
is at `origin/main`, the laptop clone is verified byte-identical, and the raw data is already moved
out. **Two live clones is how the v16.57/58 three-way fork happened** — that risk is closed by the
desktop no longer being used, not by its name.

**11. STILL QUEUED — carry list refreshed.** F3 fix (v16.75.2 §11 characterisation dispatch first,
**FIRST**, artefact to `C:\Guya\Guya_Wamu\scratchpad\`); F2 land mask; F1 point-query distance guard
(**never before F2**); F4 fan-mode ruler — **spec still owed by Aaron, do not reconstruct**; F5 score
hygiene; F6 hook-definition card — **still blocked on verifying CPZ 2/2 and GUZ+HPZ 3/6 against a
current official QLD source** (hard rule 4); export filename UTC dating — one export between 00:00
and 10:00 AEST, read the **offered** filename before renaming (**still open — the 4 Sep export was
sent by email, which can rename the attachment, so it does not settle this**); NN-guard class audit
(`_sampleIndexCache` :2148, `_idwCache` :2851, `distA` :2523); `Cap*` spot deletion — **DONE 4 Sep,
export taken first**; `GateRC`/`GateNoosa` frozen; job (b) "Here" replaces "Coast-wide"; GPS scouting
dot (v16.75.2 §12). **Removed from the list: the Leaflet pin (§6).** Line numbers unchanged —
`index.html` 4197 lines, everything at or after 3440 shifted +1 (v16.75 §6).

**12. STANDING OPERATIONAL RULE, UNCHANGED: READ ZONING WITH SHADING OFF.** Bargara is 10–13
September. F3's fix is not needed before the trip and must not be rushed to meet it.

*v16.75.2 · 4 Sep 2026 — **F3 IS CLOSED. VERIFIED AND CHARACTERISED BY PIXEL MEASUREMENT OF A
COMPLETE 2×2, NOT BY FIELD IMPRESSION.** No build, no code, no data, no schema change. Build stays
**2026.08.30a**; repo head is v16.75.1's commit plus this entry's own. The recorded root cause in
v16.75.1 §11 is **wrong and is superseded here**. Also carried in: a **retracted mitigation** this
planning chat proposed and then disproved (§7), **two wasted screenshot batches** and what went
wrong in each (§10), a **new backlog item** (§12), and the **machine move** (§13).*

**1. THE MEASUREMENT.** Four frames at z14 over Innes Park / Barolin Rock, one view, toggling only
Marine-park zones and Depth shading (slider fixed at 80%). Cells: **D** zones off / shade off ·
**A** zones on / shade off · **C** zones off / shade on · **B** zones on / shade on. Analysis by
PIL/numpy on the raw screenshots — no eyeballing, every figure reproducible from the four files.

| quantity | value |
|---|---|
| zone fill, shading OFF (`A−D`) | **21.73 luma** |
| zone fill, shading ON where shade paints (`B−C`) | **4.43 luma** |
| net retention where shade paints | **0.144** (n = 309,600) |
| **retention where shade paints NOTHING** | **0.417** (n = 611,979) |
| orange stroke core, shading OFF | `[198.7, 136.4, 30.3]` |
| orange stroke core, shading ON | `[198.2, 136.3, 30.6]` |
| zone-fill area at this view that is actually shaded | **29.0%** |

**4.43 luma out of 255 is 1.7% of full scale.** The field report "the fill is not visible" is
correct. "The fill is gone" would not have been.

**2. REGISTRATION — THE ONE FRAME THAT NEARLY COST THE SET.** Frame D was captured after an
unnoticed pan: **−144 px in y, −18 px in x** relative to the other three. Recovered by
cross-correlating an inland land patch and translating; after the shift the inland control reads
**mean |A−D| = 0.000, p99 = 0.0** — exact pixel identity, not approximate. **A pure translation is
recoverable; a zoom change would not have been.** Standing: a 2×2 is only a 2×2 if all four cells
share a view, and the cheapest way to prove that is an inland control block that contains neither
zones nor shading. Report its mean absolute difference before reporting anything else.

**3. THE DOMINANT EFFECT IS A CODE BRANCH, NOT COMPOSITING.** This is the finding. Over **611,979
pixels that carry zone fill and have ZERO shade painted on them**, the fill still drops to **41.7%**
of its shading-off strength the moment the shading flag is set. Compositing cannot do that — there
is nothing there to composite. **Something in the code reduces zone FILL opacity on the global
shading flag, independent of whether any shade covers the polygon.**

**4. THE BRANCH TARGETS FILL ONLY — THE STROKE IS UNTOUCHED.** Orange stroke cores over unshaded
water match across the toggle to within **0.5 / 255** (`[198.7,136.4,30.3]` → `[198.2,136.3,30.6]`).
So this is not a layer-wide opacity change and not a pane or z-order effect: a raster overlay cannot
sit above a polygon's fill and below its stroke, and an opacity change on the layer would dim both.
**Fill and stroke are being treated differently by code.** That is a much narrower thing to go
looking for than "layer-order or opacity".

**5. THE SECOND EFFECT IS REAL BUT SECONDARY.** Where the shade overlay does paint, the
already-reduced fill is then composited underneath it, taking **0.417 → 0.144 net**. Implied overlay
alpha rises with sounding density — conflated alpha **0.742** at weak shade (6–15 luma), **0.806**
(15–30), **0.835** (30–60), **0.946** at dense shade (60+) — consistent with an ImageData whose
per-pixel alpha tracks data coverage, multiplied by the slider. Backing out the code branch gives an
overlay term of roughly **1 − 0.144/0.417 ≈ 0.655** at the median.

**6. 71% OF THE DIMMING IS FREE DAMAGE.** Only **29.0%** of the visible zone-fill area at this view
has any shade over it. The remaining **71%** is dimmed to 42% to protect depth colours that are not
being painted there. **Gating the reduction on actual shade coverage rather than the global flag is
a strict improvement with no trade-off against depth readability** — it is the highest-value single
edit F3 has, and it costs nothing.

**7. [RETRACTED] THE OPACITY SLIDER IS NOT A MITIGATION.** This chat proposed dropping shading
opacity to 20–25% as a field workaround that would preserve the depth picture, and then disproved
it. At 25% the overlay term relaxes to roughly 0.795, but **the 41.7% code branch still applies**,
so predicted retention is ≈ **0.33** — about 7 luma, still not readable. The branch caps the slider.
An earlier attempt to test this at z11 was worthless for a second reason: the slider change altered
only **23,885 pixels**, all inside a narrow coastal band at x 1298–1938, because the shaded strip was
a sliver of that frame. **A mitigation must be tested at a view where the affected area dominates.**

**8. OPERATIONAL RULE, STANDING UNTIL F3 SHIPS: READ ZONING WITH SHADING OFF.** Not "at low
opacity" — off. This covers the Bargara trip 10–13 September without a build, and it is the reason
F3 does not need to be rushed into a pre-trip patch. **Do not let the trip date set the build
cadence**; one variable per build survives contact with a deadline only if the deadline has a
non-code answer, and here it does.

**9. [SUPERSEDED] v16.75.1 §11's ROOT CAUSE.** "Layer-order or opacity" is wrong on both limbs.
Occlusion is excluded outright by §1 and §4. "Opacity" is right only in the narrow sense that a
fill-opacity value is being changed — by code, deliberately, on a flag, not as a compositing
consequence. §11's symptom description stands; its cause sentence does not. Tagged inline at §11 of
that entry so a top-to-bottom read cannot pick it up as current.

**10. PROCESS — TWO BATCHES BURNED BEFORE THE SET LANDED, FOR TWO DIFFERENT REASONS.** Worth
recording because neither was a model or a device fault.
- **Batch 1 (3 frames) was internally valid but incomplete** — it had zones-on/shade-off,
  zones-on/shade-on and zones-off/shade-on, and no zones-off/shade-off. Three quarters of a square
  measures nothing cleanly. The retention figure derived from it (0.42) happened to be nearly right
  but for the wrong reason, and was reported at the time as suspect. **A ratio whose denominator
  mixes two variables is not a retention figure even when the number comes out plausible.**
- **Batch 2 (3 frames) was taken at a different map view** and could not be crossed with batch 1 —
  8769↔8771 differed over **37.2%** of map pixels by >40. Nobody moved the map deliberately; it moved
  between sessions and nothing in the protocol checked.
- **Both failures were specification failures, not execution failures.** The first protocol asked
  for observations rather than a closed design; the second asked for the missing cell without
  restating the fixed-view precondition. **When a measurement needs N cells, dispatch all N in one
  list with the invariant stated at the top, not the cells that are missing from the last attempt.**

**11. NEXT JOB — READ-ONLY CHARACTERISATION SPIKE.** Claude Code, Sonnet, no edits, no commit.
Diagnose before patch; the fix is not to be written in the same dispatch. Required output, verbatim
with absolute `file:line`: (a) the zone layer's base fill style; (b) every code path that alters
zone fill opacity or fill style, and what each is gated on; (c) whether any such gate consults shade
COVERAGE at the polygon or only the global shading flag; (d) the zone stroke style and whether any
path touches it; (e) the shade overlay's construction — pane, `zIndex`, add order relative to the
zone layer, `opacity` option, and whether its ImageData alpha is per-pixel. Artefact path stated
**absolutely** against the new repo root (v16.75.1 §s1), byte size reported back. **Then F2
characterisation, THEN F1's guard — never F1 first (v16.75.1 §13).**

**12. NEW BACKLOG ITEM — GPS "YOU ARE HERE" SCOUTING DOT. [unspecced]** Raised this session. A live
position marker for scouting, so a spot can be marked relative to where the angler is standing.
Constraints, non-negotiable and to be written into the spec before any build: **check what
`EMERGENCY — POSITION` already does first** — part of this may exist; the panel also carries
`WALK TRACKER (GPS · OPT-IN)`, so a live dot **subscribes to that existing `watchPosition`
consumer** rather than opening a second one; **render the accuracy circle, never a bare dot** —
phone GNSS on a headland with cliff multipath runs ±10–15 m, worse than the geometry being read
against; **no "your zone: X" readout may attach to the dot** (hard rules 1–3 — a blue dot beside an
orange line is precisely the UI that invites a legality call the app must not make); position stays
in memory, never stored, never exported; marking goes through the existing `addPt`, not a new
persistence path; explicit on/off with auto-stop for battery. **Sequenced behind F3, F2 and F1.**

**13. MACHINE MOVE.** Code workflows move off `D:\Claude Code` after this session. **Clone fresh
from `AzmixLabs/Guya_Wamu`; do not copy the working directory across** — a directory copy carries
gitignored raw data, stale scratchpad artefacts and any uncommitted state. `CLAUDE.md` and
`.claude/settings.json` are committed and arrive with the clone. Before migrating, confirm
`git status --porcelain`, `git stash list` and `git log origin/main..HEAD` are all **empty**; work
stranded on the old machine is invisible from the new one and from every chat. Check `data/raw/` —
it is gitignored and will not travel, and raw LiDAR is disposable **only** once its processed CSV has
passed the class-9-adjacency/density check, not merely "imported and rendered". **If the new machine
is not Windows, `CLAUDE.md`'s PowerShell-only command rules are actively wrong there and need their
own one-variable build.** Record the new absolute repo and scratchpad paths and use them in every
dispatch from the next session on.

**14. STILL QUEUED — unchanged unless noted.** **F3 fix (§11 dispatch first, FIRST)**; F2 land mask
on depth readout and shade paint; F1 point-query distance guard (never before F2); F4 fan-mode
ruler — **spec still owed by Aaron, do not reconstruct**; F5 score hygiene (`liveWindDir` TTL,
`recBandKm` default 0); F6 hook-definition card — **still blocked on verifying CPZ 2/2 and GUZ+HPZ
3/6 against a current official QLD source** (hard rule 4); export filename UTC dating — one export
between 00:00 and 10:00 AEST, read the **offered** filename before renaming; **Leaflet SHA-256 pin
still absent from `CLAUDE.md`** (v16.74 §5) [CLOSED — v16.75.3 §6, commit `b49ff94`; the pin is now
in `CLAUDE.md` adjacent to validation check 2. Ignore this item on a top-to-bottom pass.] — this
bites harder on a fresh clone, where the
validation list instructs a check against a pin the file does not contain; NN-guard class audit
(`_sampleIndexCache` :2148, `_idwCache` :2851, `distA` :2523, all unchecked); `Cap*` spot deletion
(7 spots) — **unblocked, export first**; `GateRC`/`GateNoosa` frozen; job (b) "Here" replaces
"Coast-wide"; GPS scouting dot (§12). **Line numbers: `index.html` is 4197 lines after build
2026.08.30a and everything at or after 3440 shifted +1 — any dispatch quoting a pre-build number
past 3439 is stale (v16.75 §6).**

*v16.75.1 · 31 Aug 2026 — **THE PANEL-OPEN GATE IS CLOSED. FIVE LIMBS, FIVE PASSES, BUILD
2026.08.30a CONFIRMED IN THE FIELD AT BOTH BUILD-STRING SITES.** No build, no code, no data, no
schema change. Build stays **2026.08.30a**; repo head is `4531b38` plus this entry's own commit.
Also carried in: **two corrections to committed entries** (§5, §7), a **process failure in this
planning chat** that a limb caught (§8), and the **29 Aug field-review backlog F1–F6** (§11–§16),
with **F3 promoted ahead of F1 on safety grounds.***

**1. THE GATE, AS OBSERVED ON DEVICE.**

| limb | map at | action | `TIDES ·` | first high | verdict |
|---|---|---|---|---|---|
| baseline | Redcliffe | expand best-bite section | `BRISBANE BAR` | 11:26 2.14 m | — |
| **L2** | Noosa | collapse section, pan, expand | `NOOSA HEAD` | 09:48 1.76 m | **PASS** |
| **L1** | Redcliffe | collapse whole panel, pan, expand | `BRISBANE BAR` | 11:26 2.14 m | **PASS** |
| **L3** | Noosa | collapse+expand **Map layers** | `BRISBANE BAR` — unchanged | 11:26 2.14 m | **PASS** |
| **L4** | Noosa | pan only, touched nothing | `BRISBANE BAR` — unchanged | 11:26 2.14 m | **PASS** |
| **L5** | Redcliffe | force-close, reopen | `BRISBANE BAR` | 11:26 2.14 m | **PASS** |

Reference states, both read off device: **Redcliffe / Brisbane Bar** 05:28 0.38 · 11:26 2.14 · 17:33
0.51 · 23:27 2.20, sunset 17:34, moonset 07:26. **Noosa / Noosa Head** 03:42 0.35 · 09:48 1.76 ·
15:45 0.49 · 21:53 1.80, sunset 17:35, moonset 07:27.

**2. THE STRONGEST OBSERVABLE WAS NOT THE PORT LABEL — IT WAS A ONE-MINUTE ASTRONOMY SHIFT.**
Sunset moved 17:34 → 17:35 and moonset 07:26 → 07:27 between the Redcliffe and Noosa reads, and the
bite windows moved with them (moonset window 06:56–07:56 → 06:57–07:57). **A port name is a selected
label and could in principle arrive from some other path; the astronomy cannot.** A one-minute delta
means `compute(ymd,lat,lng)` re-ran with different coordinates, so `ANCHOR()` genuinely moved.
**Standing, and cheaper than it looks: where a panel derives several values from one anchor, gate on
the DERIVED QUANTITY that no other code path could produce, not on the identifier.** This is the
same principle as v16.73.2 §4 (measured quantity over selected label), one step further on.

**3. L3 AND L4 ARE THE DISCRIMINATING PAIR AND THE ONLY REASON THIS GATE MEANS ANYTHING.** L1, L2
and L5 pass **identically** whether the `#bb-out` structural guard discriminates or fires on every
section toggle. Only L3 separates those. And only L4 establishes that the recompute is attributable
to the open event rather than to some unrelated re-render — without it, an incidental re-render from
any cause would have made L1 and L2 pass while nothing was actually hooked. **Both negative limbs
pass by NOT updating: the panel reads a value that contradicts the map, and that contradiction is
the evidence.**

**4. L4 ALSO CONFIRMS THE ACCEPTED LIMITATION IN THE FIELD.** Panning with the panel open leaves the
panel stale. This is the cost of choosing panel-open over `moveend` and the decision stands
(v16.72.1 §1, twice retracted) — but it is now **observed behaviour, not an inference**. On desktop
the panel is a persistent sidebar and may never close, so it can stay stale indefinitely; on mobile
the 1615/1843/1894 forced collapses at ≤600 px make the collapse-pan-expand cycle the normal path.
**Not a defect. Do not re-open it as one.**

**5. CORRECTION TO v16.74.1 §11 — THE FOOTER CHECK WAS NEVER RUN.** §11 records the two-site
build-string field check as closed for `2026.08.24a`. It was not. The planning chat asked whether
header **and** footer both read the build string and accepted "yes"; the footer is at
`index.html:1091`, inside the **Fishing spots & catches** block, which was collapsed, and it was
later established on device that it had not been seen. **A single "yes" to a two-part question is
one answer, not two, and it was recorded as two.** The claim in §11 is withdrawn. v16.73.1 §5 was
never run either, so `2026.08.21a` and `2026.08.24a` both shipped without this check.

**6. THE CHECK IS NOW GENUINELY CLOSED, FOR `2026.08.30a`.** Header reads `BUILD 2026.08.30A`
(`:1052`, uppercased by the `.sub` line's CSS); spots-block footer reads `build 2026.08.30a`
(`:1091`, lowercase as authored), under "Logging as Me". **The case difference is presentational and
is NOT a defect** — `panelopen_diff_U0.txt` shows both hunks carrying the identical lowercase token
in the source. Recorded so a future check does not flag the mismatch. Practical note for scoping any
future run: both sites live in the same deployed file, so a correct header read already proves the
deployed file is the built file; the footer limb adds very little, which is exactly why it should
never have been recorded as evidence it did not supply.

**7. SUPERSEDES v16.75 §13 — THE GATE SPEC WENT FROM THREE LIMBS TO FIVE.** §13 was written by
Claude Code alongside the build it validates, and specified three limbs: whole-panel, section, and a
negative control on a different section. **A self-written test protocol receives the same red-team
as any patch.** Two additions were made before the run: the pan-without-opening limb (L4), which
§13's set omitted and which is the attributability check; and the boot limb (L5), covering Phase 1
§7C's ordering concern. §13's own negative control was a genuine addition the planning chat had not
specified and is retained as L3. **The five-limb set in §1 is the record; §13's three-limb list is
superseded.**

**8. PROCESS FAILURE IN THE PLANNING CHAT, CAUGHT BY A LIMB.** On the report "expanding and
collapsing map layers does change it", the planning chat declared L3 FAILED and began diagnosing a
propagation defect in site 2 — **before asking what had changed.** The screenshots showed the
`TIDES ·` heading and all four tide values unmoved; what changed was Map layers' own toggle list
rendering and the sections below it shifting up. **L3 had passed.** This is precisely the
two-outcome reading of a many-outcome observation that the same chat had flagged three messages
earlier in F1's test design (§12), applied to itself and missed. **Standing: when a field report says
"it changed", establish WHAT changed before classifying the result. A verdict issued ahead of the
observation is a guess wearing a verdict's clothes.**

**9. L5 AS RUN WAS BETTER THAN L5 AS SPECIFIED.** The planning chat said a retry with the panel
pre-set to Noosa "would test nothing", because the app always boots at Redcliffe (`#home` hard-codes
`map.setView([-27.2275,153.0950],12)`) and the expected and stale values would coincide. **Wrong.**
Aaron set the panel to `NOOSA HEAD`, force-closed, reopened, and got `BRISBANE BAR` — which
distinguishes *boot render ran fresh against the current map centre* from *boot restored the last
displayed value*. Phase 1 §4 predicted no persistence of computed values; this observed it. **A
limb whose two outcomes coincide under one hypothesis may still separate two OTHER hypotheses.**

**10. SITE 2's DELIBERATE OVERSHOOT IS BENIGN IN THE FIELD.** v16.75 §10 recorded that a whole-panel
expand fires `render()` even when the best-bite `.blk` is itself collapsed. No lag, no error and no
visible artefact was observed across the run. Remains accepted and unguarded.

---

**BACKLOG — 29 AUG FIELD-REVIEW SESSION (planning only, no build).** Six items, recorded here for
the first time. **Sequencing changed from the field notes: F3 goes first.**

**11. F3 — DEPTH SHADING OBSCURES THE MARINE-PARK ZONE FILL. [needs verify] PROMOTED TO FIRST.**
[SUPERSEDED — v16.75.2 §§1–6. VERIFIED by measurement 4 Sep 2026. The cause sentence below
("Layer-order or opacity") is WRONG: occlusion is excluded, and the dominant effect is a code branch
that reduces fill opacity to 41.7% on the global shading flag. Symptom description stands; cause
does not. Do not read the cause as current.]
Shading OFF: CPZ06 fill renders as a visible wash inside the boundary. Shading ON: the fill is not
visible and only the orange boundary line survives. Layer-order or opacity. **This is the only item
on the list that degrades a SAFETY cue, and it does so specifically in the mode used for planning
casts** — hard rules 1–3 exist to surface zone information, and shading quietly removes it. Elevated
further by the Hoffmans Rocks finding: there is a live green-zone boundary immediately north of a
spot in active use. **"Needs verify" is not a reason to sequence it later** — the verification is a
shading toggle on a known zone edge, cheaper than F1's walking test, and if it confirms, everything
else waits.

**12. F1 — POINT QUERY HAS NO MAXIMUM-DISTANCE GUARD. [confirmed defect]** "Est. height here"
returned `dries ≈ 1.7 m · exposed now · data 35 m away` on a 10–15 m headland at Nudibranch Park
that the tide never reaches. The nearest stored value is returned and labelled as the value AT the
query point. **Same class as `nearestPort()`'s `let best=PORTS[0], bd=Infinity` — a "present but
meaningless" third state.** Offshore readings are unaffected and internally consistent (63 m → +0.1 m,
118 m → 3.9 m, 180 m → 5.6 m; monotonic). Also a computation/label disagreement: the headline says
"here", the fine print says 35 m away, and the headline wins the reader's attention.

**THE DISCRIMINATING TEST HAS FOUR OUTCOMES, NOT TWO.** The field notes framed it as two. Record
BOTH numbers at every tap walking inland and read the pair afterwards; **do not classify into a
bucket in the field** — a test that can only return one of two answers will return one of them
whatever is true:

| height | "data N m away" | reading |
|---|---|---|
| pins ~1.7 | climbs | F1 as stated — no distance guard |
| varies | stays small | land points in the store — datum/classification, **worse** |
| pins ~1.7 | stays small | nearby points all carrying the same value — a flat fill in the store |
| varies | climbs | sparse nearest-neighbour behaving correctly — **no defect** |

Wording correction for the eventual fix: nearest-neighbour does not *extrapolate*, it returns the
nearest stored value unchanged. "Pins near 1.7 m" is exactly correct NN behaviour at distance.
**The defect is the absent guard and the "here" label, not the arithmetic.** Fix shape, post-test,
one variable: a distance guard returning "no data here" rather than a number, mirroring
`portInRange()`.

**13. F2 — NO LAND MASK ON THE DEPTH READOUT OR THE SHADE PAINT. AND IT MUST BE CHARACTERISED
BEFORE F1 IS FIXED.** Shading paints over the same headland in the same frame as F1. The readout and
the renderer are separate call sites and a shared root cause is **UNVERIFIED**. The OSM/DEA
STRICT-AND mask exists and is not consulted at either site. **The interaction the field notes did
not capture: an F1 distance guard suppresses the headland reading REGARDLESS of whether a land mask
is ever consulted — so shipping F1 first makes F2 harder to detect, not easier, and leaves the app
painting over land while reporting "no data here" at the same point.** Sequence F2's characterisation
spike before F1's fix. If they share a call path, one fix serves both; if not, that is known before
the guard hides the evidence.

**14. NEW — THE NEAREST-NEIGHBOUR-WITHOUT-A-GUARD PATTERN IS A CLASS, AND IT HAS NEVER BEEN
AUDITED.** Three instances now: `nearestPort()` (v16.74 §9), `portInRange()` — which fixed it at
**one call site only**, leaving the display path open (v16.74 §10) — and now the point query (§12).
v16.74.1 §14 adds that the haversine itself is implemented twice. **Add an audit item: sweep every
nearest-neighbour or proximity lookup in the file for a maximum-distance guard.** `_sampleIndexCache`
(`:2148`), `_idwCache` (`:2851`) and `distA` (`:2523`) all surfaced in the Phase 1 sweeps and none
has been checked. **Fixing instances one at a time as the field finds them is how this reached
three.**

**15. F6 — ZONE RULE CARD, HOOK DEFINITION. [new] BLOCKED ON VERIFICATION, NOT ON BUILD.** Spot
popups surface zone type + ID + "verify rules yourself" but not the hook definition — the rule most
likely to be got wrong in the field, and got wrong twice in the 29 Aug session. Candidate: a static
reference card under the zone line — CPZ 2 rods/2 hooks, GUZ+HPZ 3/6, gang ≤6 = 1 hook, lure ≤3
hooks = 1 hook, bait jig ≤6 hooks size 1–12 = 1 hook, with the QPWS FAQ link. **STATIC TEXT ONLY,
never computed, never presented as a legality call** — that framing is right and respects hard rule 1.
**But hard rule 4 marks the recorded rod/hook limits as UNCONFIRMED, and a reference card is read as
authoritative precisely because it is a card.** Displaying unverified limits is worse than displaying
none: the user stops checking. **Verify CPZ 2/2 and GUZ+HPZ 3/6 against a current official QLD source
BEFORE the card is built.** If they do not verify, the card degrades to a link plus a "check before
you fish" line, which is still an improvement on nothing. That the numbers were got wrong twice in
one session is evidence both that the card is needed and that they are easy to get wrong.

**16. F5 AND F4.**
- **F5 — SCORE HYGIENE. Operational, no code change.** `liveWindDir` never expires (v16.71 §8);
  `recBandKm` defaults to 0, i.e. no distance cap. Both silently degrade ranking away from home water.
- **F4 — RULER, FAN MODE. [enhancement] SPEC UNSPECIFIED.** The field notes read "[spec below]" with
  nothing below them. **Recorded as a placeholder deliberately rather than reconstructed** — a spec
  written from chat recollection is what the standing rules forbid, and a plausible-looking wrong
  spec is worse than an honest gap. Aaron to supply.

**17. RETRACTED FROM THE 29 AUG NOTES — MEASURE-TOOL LABEL/TOTAL DISCREPANCY (logged 28 Aug). NO
DEFECT.** Vertex labels are cumulative, not per-segment; 77/143/211/381 was a closed loop totalling
381. **Kept with its reasoning rather than deleted, so it is not re-raised.** Worth noting the shape:
this is a computation/label disagreement — the same class as v16.74.1 §13 — but it resolved the
other way round, with the label correct and the expectation wrong.

**18. NEW OBSERVATION, UNVERIFIED, LOW — THE SPECIES FILTER IS RENDERING SPOT NOTES AS CHIPS.** Under
FILTER BY SPECIES, entries appear reading "— geometry warning pin; fish from the frontage pin S of
here.", "Beachworms + pippis at low on the open sand…", and several Cool:/Warm: species-hint lines,
alongside the expected `Catch1`–`Catch4` chips. These read like spot notes and species-hint text
landing in a UI slot meant for short labels. **May be intended. Not investigated, not in the F1–F6
set, recorded so it is not lost.**

**19. HOUSEKEEPING.** Device shows **Show spots 29**, matching the round-2 capgate export's
`spots=29` exactly — so the spot store has survived five days and many force-closes, which also
retires v16.74.1 §17's durability residual for the spots themselves. Seven `Cap*` spots and the
frozen `GateRC` (3 catches) / `GateNoosa` (1 catch) remain. **Delete the `Cap*` set only after this
entry is committed** — `CapKeppel` and `CapCairns` are the only field evidence the 200 km cap fires.
Export first. Scratchpad note: the 30 Aug build session wrote its artefacts to a **session temp
directory**, not `D:\Claude Code\scratchpad\`, after a bash heredoc failure forced a fallback to the
file-write tool; `panelopen_edit.js` exists in both locations, same byte count, five minutes apart.
**A fallback that preserves the content can still break the location, and a terminal condition that
checks the repo is clean will not notice.** All artefacts recovered. **Standing: state artefact paths
ABSOLUTELY in dispatches, never as bare `scratchpad\`.**

**20. STILL QUEUED — unchanged unless noted.** **F3 zone-fill occlusion (§11, FIRST)**; F2
characterisation spike then F1 guard (§12–§13); NN-guard class audit (§14, NEW); F6 blocked on rule
verification (§15); F5 operational (§16); F4 awaiting spec (§16); `CLAUDE.md` Leaflet pin + method
(v16.74 §5 — still open; the 30 Aug build's digest check was satisfiable only because the ROADMAP
carries the pin `CLAUDE.md` requires); display-path remoteness (v16.74 §10, with a confirmed route
to siting a Fiji limb via the ESRI global base map, v16.74.1 §16); haversine implemented twice
(v16.74.1 §14); export filename UTC dating (v16.74.1 §8 — **still needs the one-line confirmation**:
export once between 00:00 and 10:00 AEST and read the offered filename BEFORE renaming);
spot-id variable length (v16.74.1 §9, low); `buildPlan()`'s identical `ANCHOR()` defect (v16.75 §9 —
and its no-throttle exemption does NOT transfer, it fetches Open-Meteo); v16.71.1 §5 overlay clip;
`storage_check.html` tooling pass; MN v3 (#15) Noosa-OSM fetch + Noosa tide-port wiring; SC `okHAT`
boundary inclusivity; `FLATS_BOUNDS` 3-dp precision; `env.tide`/`env.moon` frame mismatch (v16.72.3
§7); bite-time graph scrub (v16.73.2 §7, blocked behind the frame mismatch).

**21. NEXT SESSION.** Build **2026.08.30a** (unchanged — this entry ships no code), roadmap
**v16.75.1**, repo head `4531b38` plus this entry's own commit. `CLAUDE.md` unchanged. **The
panel-open gate is CLOSED (§1). Next job: F3 verification** — a read-only on-phone toggle on a known
zone edge, not a build, nothing dispatched before it returns. Then job (b), "Here" replaces
"Coast-wide". **Do not re-litigate:** everything in v16.73's, v16.73.1's, v16.73.2's, v16.74's,
v16.74.1's and v16.75's lists, plus — the panel-open gate is closed and is not to be re-run (§1);
panning with the panel open leaves it stale and that is accepted, not a defect (§4); site 2's
overshoot is accepted and unguarded (§10); site 3 detects the block structurally and must not be
changed to match on label text (v16.75 §13); the measure-tool discrepancy is retracted (§17).

---
*v16.75 · 30 Aug 2026 — **JOB (a) SHIPPED: THE BEST-BITE PANEL NOW RECOMPUTES WHEN IT BECOMES
VISIBLE. Build 2026.08.30a.** Repo head `4f1e0f7` plus this build's commits. Three sites, one
variable, `+212` bytes, five hunks. Explicitly **not** on `moveend` (v16.72.1 §1, twice retracted).
The on-phone gate is **NOT RUN** — this entry ships code only.*

**1. WHAT SHIPPED.** Phase 1 (`scratchpad/panelopen_phase1.txt`) established that the panel is stale
not because a cache went stale but because a fresh computation never happens: `ANCHOR()` and
`curPort()` are pure and are read at the instant `render()` runs, and nothing re-runs `render()`
after a pan. The fix is therefore a re-run, not an invalidation. Three sites:

- **`index.html:3440` — NEW LINE, `window.bbRender=render;`** beside the existing
  `window.bbRefreshSpots=populate;` at `:3439`, which is the pattern one line away. This is the
  second app hook across the best-bite IIFE boundary (3313–3629). It binds the **first** `render()`
  (`:3394`); the unrelated badges `render()` at `:4152` is in a different IIFE and is not exposed.
- **`index.html:1318`** — inside `setCollapsed`, after the existing `classList.toggle` and
  `textContent` statements: `if(!c&&typeof window.bbRender==='function')window.bbRender();`.
  Expand direction only. Guarded in the style of `:1830`.
- **`index.html:3938`** (was `:3937`) — inside the `.lbl` click handler, after the existing toggle
  **and** after the `localStorage` write:
  `if(blk.querySelector('#bb-out')&&!blk.classList.contains('collapsed')&&typeof window.bbRender==='function')window.bbRender();`
- **`index.html:1052` and `:1091`** — build string `2026.08.24a` → `2026.08.30a`, both sites.

**2. BOTH OPEN MECHANISMS ARE HOOKED, WHICH WAS THE POINT.** Phase 1 §7A: the whole-panel collapse
(`:1318`) and the per-section collapse (`:3938`) are independent, and hooking one leaves the other
desynchronised. §7B is why the whole-panel arm is the load-bearing one in the field: `Best bite
times` is in `KEEP_OPEN` (`:3932`), so the section starts open and its `.lbl` click can only fire
after the user has first collapsed it — whereas `1615/1843/1894` force `setCollapsed(true)` at
≤600 px, so on the phone the user is *made* to re-expand. A section-only fix would have shipped
nothing for the common case.

**3. THE SECTION IS DETECTED STRUCTURALLY, NOT BY ITS LABEL.** `blk.querySelector('#bb-out')`, not a
match on the string `'Best bite times'` — that string is display copy and a future rename must not
silently kill the recompute. `querySelector` on an element searches its descendants only, so it is
correctly scoped without `:scope`. Note the deliberate asymmetry: the collapse IIFE's own state key
`k` **is** the label text (`:3934`), because that is the existing persisted `localStorage` schema and
changing it would orphan `woongarra_collapsed_v2`. Structural detection sits alongside it rather than
replacing it.

**4. BOTH CALL SITES TOLERATE `window.bbRender` BEING UNDEFINED, AND THAT IS NOT DEFENSIVE PADDING.**
Phase 1 §7C flagged boot order and it is real: `setCollapsed` is defined at `:1318`, the hook is not
assigned until `:3440`, and the collapse IIFE at `:3931` applies its classes only after the best-bite
IIFE has already run its own `render()` at `:3628`. Any expand that fires inside that window is a
no-op instead of a `TypeError`.

**5. NOTHING WAS THROTTLED, DEBOUNCED OR CACHED, ON PURPOSE.** Phase 1 §4 found no memo anywhere on
the render path (`compute()` at `:3334` rebuilds all 289 samples unconditionally; the eight
cache-ish variables in the file all belong to the depth/shading/zone pipelines) and §5 found zero
`fetch` on it. So there is nothing to invalidate and no rate to limit. The cost of a recompute is
pure CPU. **This does NOT carry over to `buildPlan()`** — see §9.

**6. VALIDATION, DESK-SIDE.** The four `CLAUDE.md` checks, run on the shipped file:

| check | result |
|---|---|
| `node --check` block 1 (inlined Leaflet, `:1209–1214`, 147,552 B) | PASS |
| `node --check` block 2 (app, `:1215–4194`, 2,135,293 B) | PASS |
| Leaflet block byte-identical vs the pre-edit backup | `cmp` identical; sha256 `db49d009…f4e5641a` both sides |
| `zoneAt()` (`:1325`) + green-zone drag safeguard (`:1578`) | both unmoved, unmodified, no hunk within them |

`zoneAt()` was read back in full: `ORDER=["MNP","CPZ","HPZ","GUZ"]` at `:1227`, `rank<bi` lowering
only, `return best` at the end — most-protective-on-overlap, not first-match, intact. Blocks were
located structurally (two `<script>`, two `</script>` confirmed), not by remembered line numbers.

**7. THE DELTA WAS PREDICTED BEFORE THE WRITE AND RECONCILED AFTER.** `+212 B` predicted, `+212 B`
measured (2,352,268 → 2,352,480); the edit script asserted the two against each other and would have
thrown before writing. Arms off the line text on disk: site 1 `+26` (25 chars + its own LF), site 2
`+61`, site 3 `+125`, build string `+0` (11 chars → 11, both sites). Cross-checked against line
lengths read back: `:1318` 151→212, `:3937` 183→308. `git diff --numstat` = `5 4` — four lines
modified in place plus one inserted. **Hunk count measured off `git diff -U0`, not inferred from the
site count: 5, not 3**, because the build string is its own hunk at each of its two sites; only
`@@ -3439,0 +3440 @@` is an insertion. File is LF-only with no trailing newline; confirmed 0 CR
before and after.

**8. LINE-NUMBER SHIFT MAP.** One region moved, by `+1`, because site 1 is the only insertion.
Lines 1–3439 unshifted (`:1052`, `:1091`, `:1318` were edited in place); `:3440` is new; old
3440–4196 → 3441–4197. Landmarks: `window.bbRefreshSpots` 3439→3439, `todayAEST` 3440→3441,
`onchange=render` 3441/3442→3442/3443, `shiftDay` 3445→3446, boot `render()` 3627→3628, IIFE close
3628→3629, collapse IIFE 3930→3931, `.lbl` handler 3937→3938, badges `render()` 4151→4152,
`</script>` 4193→4194. **Every Phase 1 number at or after 3440 is now off by one.**

**9. `buildPlan()` WAS LEFT ALONE AND THE DEBT IS RESTATED, NOT CLOSED.** `:3575` (was `:3574`) has
the identical desynchronisation defect — it resolves `ANCHOR()` at click time only — and it was out
of scope here. It is **not** a candidate for the same one-line treatment: it fetches Open-Meteo, so
§5's no-throttle conclusion does not transfer. Any future panel-open recompute extended to that block
needs its own rate decision first.

**10. RECORDED AS A DECISION, NOT AN OVERSIGHT: SITE 2 OVERSHOOTS.** A whole-panel expand fires
`render()` even when the best-bite `.blk` is itself still collapsed, writing `#bb-out` into a hidden
node. Cost is one `compute()` and no network. Guarding it would duplicate site 3's predicate and
create a second thing to keep in sync, to save work only for a user who has explicitly collapsed a
`KEEP_OPEN` section. Left in.

**11. NO jsdom STEP; BOTH ARMS WERE EXERCISED ANOTHER WAY.** The two guard expressions were
**extracted by regex from the file on disk** — not retyped — and run against stub objects: 8/8 pass,
covering fire-on-expand, silent-on-collapse, fire on the bb block when it opens, silent on the bb
block when it closes, silent on a non-bb block in both directions, and no-throw with `bbRender`
undefined on both arms. Both branches of both guards are therefore exercised desk-side. Script:
`scratchpad/panelopen_branch_probe.js`; full evidence `scratchpad/panelopen_build_report.txt`.
**This is desk-side only and is not a substitute for the on-phone gate.**

**12. HARNESS NOTE, WORTH CARRYING.** Two attempts to write the build report via a bash quoted
heredoc failed identically with a shell parse error at the same offset, with no file produced; the
repo was verified unaffected each time before retrying, and the report was written with the file-write
tool instead. Heredocs are not reliable for large report payloads in this harness — write the file
directly.

**13. ON-PHONE GATE FOR `2026.08.30a` — NOT RUN, AND IT NEEDS BOTH ARMS.** Force-close/reopen the
home-screen app; confirm `2026.08.30a` in **both** the header and the spots-block footer. Then:
**(i) whole-panel arm** — with the panel expanded, note the port name printed in the Tides heading;
collapse the panel with the `–` button, pan the map far enough to change the nearest port (Redcliffe
↔ Bargara is the reliable pair), expand again, and confirm the Tides heading now names the **new**
port. **(ii) section arm** — with the panel already open, collapse just the `Best bite times`
section by its label, pan to change the nearest port, re-open that section only, and confirm the same.
**(iii) negative control** — collapse and re-open a *different* section (e.g. `Map layers`) after a
pan and confirm the best-bite output does **not** change; that is what distinguishes site 3's
structural predicate from an always-true one. A run that only exercises (i) is a **null result** for
site 3 — record it as one (v16.74.1 §5).

**14. NEXT SESSION.** Build **2026.08.30a**, roadmap **v16.75**, repo head `4f1e0f7` plus this
build's commits. `CLAUDE.md` unchanged. **Next job: run the §13 gate** (all three limbs, or say
plainly which were skipped), then **(b) "Here" replaces "Coast-wide"**. Pending cleanup carried:
`buildPlan()` `ANCHOR()` desync (§9, now with a rate decision attached); display path still out of
range (v16.74 §10); everything in v16.74.1 §19's list. **Do not re-litigate:** recompute is on panel
open, **not** `moveend` (v16.72.1 §1, twice retracted, and this build did not add a single map
listener); the 200 km cap gate is closed and is not to be re-run (v16.74.1 §1); the field bracket is
not to be tightened (v16.74.1 §15); site 3 detects the block structurally and must not be changed to
match on label text (§3).

---
*v16.74.1 · 25 Aug 2026 — **THE 200 km CAP'S ON-PHONE GATE IS CLOSED. ALL FIVE LIMBS PASS AND BOTH
BRANCHES ARE EXERCISED IN THE FIELD.** No build, no code, no data, no schema change. Build stays
**2026.08.24a**; repo head is `c83854a` plus this entry's own commit. Evidence: three `version:2`
exports inspected off-device across two rounds — round 1 proved only the pass-through path and is
recorded as a **null result**, round 2 closed the gate. Also: the desk-side boundary measured off
the shipped file before the phone was touched (§7), a fourth transport failure in a NEW direction
(§12), and two new defects in the export/id layer (§8, §9). **`env.tide` remoteness is confirmed in
the field and the queue is unblocked.***

**1. THE GATE, VERBATIM FROM THE EXPORTS.**

| limb | dist km | resolved port | `Object.keys(env)` | verdict |
|---|---|---|---|---|
| `CapCairns` | **1,117.64** | Burnett Heads | `["moon"]` — **no `tide` key** | PASS |
| `CapKeppel` | **243.10** | Burnett Heads | `["moon"]` — **no `tide` key** | PASS |
| `CapCurtis` | **160.37** | Burnett Heads | `["tide","moon"]`, `ht 1.04 falling` | PASS |
| `CapB1` | **13.49** | Mooloolaba | `["tide","moon"]`, `ht 0.6 falling` | PASS |
| `CapC` | **3.76** | Mooloolaba | `["tide","moon"]`, `ht 0.6 falling` | PASS |

`tide:null` and `tide:{}` have **zero occurrences** across all five catches. The build reuses the
existing omission semantics with no schema change, exactly as v16.74 §1 claimed. `port` on the
in-range side is `"Mooloolaba"` and `"Burnett Heads"` — spot-coordinate-derived, not map-centre-derived,
corroborating v16.72.3 §3 for a third time.

**2. FOUR CANDIDATE DEFECTS EXCLUDED BY OBSERVATION, NOT INFERENCE.** A dead predicate or an
always-true predicate stamps Keppel and Cairns — neither is stamped. A cap of 0, or any cap below
160.37 km, strips Curtis, B1 and C — none is stripped. A broken `dayTideSampler` fails the in-range
side — it does not. Deletion of `env` at the omission site takes `moon` with it — `moon` survives on
both omitting catches. **This is the property v16.73.1 demanded and round 1 could not supply: every
passing observable is not the same string.**

**3. THE `ht` CONSISTENCY CHECK PASSES, AND IT COST NOTHING.** `CapB1` at `23:47` and `CapC` at
`23:49`, two minutes apart, both resolving Mooloolaba: `ht 0.6`, `state "falling"`, identical. No
second table is being reached. **Recorded as a reusable technique: two limbs at the same port a few
minutes apart give a table-identity check with no external tide source and no extra dispatch** —
strictly better than "`ht` plausible against the published table for that instant", which requires a
source the gate does not carry.

**4. BURNETT HEADS WAS EXERCISED ON BOTH SIDES OF THE BOUNDARY — UNPLANNED.** The gate was designed
entirely against Brisbane Bar. The re-siting forced by §6 moved every new limb north, so the
predicate is now confirmed in-range at Curtis and out-of-range at Keppel and Cairns against a
**second port**. **Standing lesson, third instance after v16.73.2 §4: a constraint that forces a
protocol off its designed path has repeatedly produced a stronger gate than the design.** Record the
accident; do not pretend it was the plan.

**5. ROUND 1 IS A NULL RESULT AND IS KEPT AS ONE.** The first pass logged catches on `CapB1`
(13.49 km) and `CapC` (3.76 km) only. `CapA` and `CapB2` were created but carry **zero catches**, and
all four round-1 spots resolve `portInRange=true`. **That export evidences the pass-through path
alone — precisely what a completely dead cap also produces.** It was reported as a null result rather
than as a clean run, and the distinction is the entire value of the round. Round-1 artefacts:
`woongarra-backup-2026-08-24 pre cap.json` (20,012,001 B) and
`woongarra-backup-2026-08-24capgate.json` (20,014,212 B); spots 22 → 26; delta **2,211 B** across 4
spots + 2 catches ≈ 368 B/record, which agrees with the catch count and not with four.

**6. THE ROUND-1 MISPLACEMENT WAS A DISPATCH-LANGUAGE DEFECT, NOT A USER ERROR, AND NOT AN APP
DEFECT.** The planning chat wrote "exact placement doesn't matter" (true — the export carries the
pin's real coordinates and the distance is recomputed from those) alongside "drop the pin there".
Together those read as *anywhere*. They meant *anywhere within ~20 km of the stated coordinate*.
Distance to the nearest port is the predicate's only input, so the pin's location **is** the test
input. **Standing rule: when a dispatch says a tolerance is loose, it must state the tolerance.**
The two candidate explanations — misplacement versus coordinate clamping in the app — were
distinguished by one field: `CapA` at `153.117150` is a QLD longitude, so the pins went where they
were put. Ruling out the app defect mattered more than the gate, since coordinate integrity
underwrites every distance-derived behaviour in the file.

**7. THE BOUNDARY WAS MEASURED OFF THE SHIPPED FILE BEFORE THE PHONE WAS TOUCHED.** A read-only
harness at `scratchpad\capgate_sites.js` lifted `PORTS`, `nearestPort`, `portInRange` and the
function-local `hv` arrow **verbatim** from `index.html` — the `hv` slice verified as a genuine
substring by `.Contains()`, not retyped. Sweep along `lng 153.40`, `lat −27.40 → −30.00` at 0.005°:
**521 rows, 351 true, 170 false, exactly one flip, `Brisbane Bar` the only port seen** — so the
boundary is a single distance crossing, not a port-handover artefact. Last true `−29.150` at
**199.6059 km**; first false `−29.155` at **200.1582 km**. **`PORT_MAX_KM` is where it claims to be,
measured on disk.**

*Independently reproduced in the planning chat from the same lifted formula: Redcliffe →
Brisbane Bar **15.62 km**, character-identical to the harness, from a copy that travelled a
different path.*

**8. NEW DEFECT — EXPORT FILENAMES APPEAR TO BE UTC-DATED, NOT LOCAL. NEEDS ONE-LINE CONFIRMATION.**
The round-2 export was written at `2026-08-24T14:09:27.774Z` = **00:09:27 AEST on 25 August**, and
its filename stem reads `woongarra-backup-2026-08-24`. Round 1 exported at `13:49:42.526Z` = 23:49
AEST 24 Aug, where UTC and local agree and the stem is uninformative. **Caveat, and it is why this is
not yet asserted: Aaron hand-suffixed both files, so the stem's date cannot be proven to be the app's
rather than typed.** Confirm by exporting once between 00:00 and 10:00 AEST and reading the offered
filename before renaming. **If confirmed, it amplifies the v16.73.2 §6 collision hazard rather than
repeating it** — every export in the 00:00–10:00 AEST window carries the *previous* day's date, so a
late-night and a next-morning export collide by construction, and no amount of care about
same-day exports prevents it.

**9. NEW DEFECT, LOW — SPOT IDS ARE VARIABLE-LENGTH.** `index.html:1611` builds ids as
`'s'+Date.now()+Math.floor(Math.random()*999)`. The random tail is **not zero-padded**, so ids run
15–17 characters: `s178757909871556` (tail `56`), `s178758041951444` (tail `44`),
`s1787579039491992` (tail `992`). Harmless today because the epoch is a fixed 13 digits and every
decode in use takes a **prefix**. **Any future parse using a fixed offset from the END of the id will
break, silently and only sometimes.** The epochs in this entry are trustworthy because Claude Code
read `1611` to confirm the format instead of assuming a 13-digit decode — the right instinct, and the
reason the defect was found at all.

**10. THE MIDNIGHT STRADDLE HAPPENED, AND KEEPING BOTH WINDOWS LIVE IS WHAT SAVED IT.** Round-1 spots
were created 23:43:59–23:45:26 AEST on 24 Aug; round-2 spots 00:05:21–00:06:59 AEST on **25 Aug**
(`1,787,580,321,915` / `…358,968` / `…419,514`, all inside the 25 Aug window
`1,787,580,000,000 – 1,787,666,400,000`). A single 24 Aug bound — the obvious reading of v16.73.2 §1 —
would have **rejected three valid records**. **Extension to that rule: when a gate is run near a day
boundary, both adjacent windows stay live until the records are read.** A recomputed bound is not
sufficient if the recomputation assumes one day.

**11. THE TWO-SITE BUILD-STRING FIELD CHECK IS CLOSED.** Header **and** footer both read
`2026.08.24a` on the phone. Open since v16.73.1 §5 and never run for `2026.08.21a`. Deployment
confirmed first, as required: Pages Actions runs succeeded for `82571ac` (47 s) and `c83854a` (41 s),
the latter carrying the live `https://azmixlabs.github.io/Guya_Wamu/` URL on its deploy job.

**12. TRANSPORT — A FOURTH FAILURE, IN A NEW DIRECTION, PLUS TWO OF A FIFTH KIND.**

- **INBOUND truncation, first observed instance.** A dispatch carrying ten candidate coordinate rows
  arrived with **one**. The loss was **mid-prompt**, not a tail cut — STEP 4 and the terminal
  conditions after the candidate block both arrived intact, so it was not self-announcing. Standing
  rule (2) routes long *outputs* to `scratchpad\`; **nothing protected the outbound leg of a
  dispatch.** Detected only because Claude Code reported the received count instead of proceeding
  with what it had.
- **Non-arrival, twice.** `capgate_sites.txt` and `capgate_results.txt` were both reported attached
  by Claude Code and neither crossed into the planning chat. **Strictly better than truncation — a
  missing file is visible, a truncated one is not.** Both were eventually attached by Aaron directly
  from `scratchpad\`.

**STANDING, NEW — three rules from the above:**
1. **A dispatch that transports a fixed list carries that list's length, and the prompt requires the
   received count to be reported back before the list is used.** This does **not** conflict with
   v16.74 §14's rule against stating an expected match count: that rule governs *discovery*, where a
   stated count stops the search early. A supplied list is not a discovery — its length is transport
   metadata, not a finding. **The two must not be conflated.**
2. **Better still, do not transport the list.** Round 2's prompt had the harness *generate* its
   candidates from a rule (a swept meridian). A generated list cannot truncate in transit and
   produced a stronger measurement than the transported one would have — §7's single-crossing proof
   was a by-product.
3. **An attach is confirmed on the receiving end, not asserted on the sending end.** Dispatches now
   require the artefact's byte size to be stated back so arrival can be distinguished from a claim.

**13. A DISPATCH THAT CARRIES BOTH A COMPUTATION AND A LABEL FOR IT CONTAINS TWO THINGS THAT CAN
DISAGREE.** The round-1 sweep prompt labelled `crossing − 0.20°` as "inside, with margin". Latitudes
are negative and grow more negative southward, so `− 0.20°` is *further* from the port — outside. The
planning chat had it backwards. **Claude Code computed exactly what was specified, then flagged the
label as inverted rather than silently swapping to the evidently-intended meaning.** A silent swap
would have produced a correct-looking table untraceable to a defective prompt, and the prompt would
have been reused. **Standing: execute the computation, flag the label, never reconcile them
silently.**

**14. NEW, QUEUED — THE HAVERSINE IS IMPLEMENTED TWICE, AND v16.74 §9 DOES NOT COVER IT.** §9 records
that the tide path *resolves* `nearestPort` twice. This is a different and slightly worse thing:
`nearestPort`'s function-local `hv` arrow (`index.html:3310`) and `portInRange`'s bare inline
expression (`:3311`) are **two independent copies of the distance formula**, not a call site and a
caller. Verified algebraically identical today — same `R=6371`, same half-angle terms, same
`cos(ll.lat)·cos(p.lat)` pairing, same `Math.min(1,…)` domain clamp, same argument order once
`hv(cl.lat,cl.lng,p.lat,p.lng)` binds. **But an edit to one leaves the other untouched**, after which
`portInRange` could admit or reject a point that `nearestPort`'s own distance disagrees about. §9's
"the two cannot disagree" reasoning covers the resolved **port**, not the **distance**. Also
confirmed while extracting: there is **no geodesic helper function anywhere in the file** — a
declaration-anchored sweep for `dist|haversine|equirect|km|bearing` returned six hits, none of them a
distance helper (`angDist` :1478 compass-bearing, `distA` :2523 proximity score, `okMASK` :2822,
`PORT_MAX_KM` :3311, `recBandKm` :3450 UI cap, `distTxt` :3517 drive-time formatter).

**15. THE FIELD BRACKET IS LOOSER THAN DESIGNED, AND THAT IS FINE FOR A STATED REASON.** Pins landed
off-nominal — Curtis at 160.37 km against a 179 km target, Keppel at 243.10 km against 229.75 km — so
the **field** bracket is cap ∈ (160.37, 243.10), which still admits 175 or 225 as hypothetical values.
**Precision comes from §7's harness, which read the shipped file and put the boundary inside
0.55 km of 200; the phone's job is to confirm the harness describes the real container, and it does.**
For the property that actually protects field data, v16.74 §9's floor is 126.28 km and every value
the field bracket admits clears it. **Do not re-run the gate to tighten the bracket** — a tighter
field bracket would add nothing the harness has not already measured more precisely.

**16. BASE MAP — ESRI SATELLITE AND STREET BOTH RENDER GLOBALLY; THE QLD AERIAL IS CLIPPED.** The
default aerial layer (`State of Queensland (Dept of Resources)`) has no imagery outside QLD, which is
why a Fiji limb could not be sited by eye. The label layer was global throughout (OpenStreetMap /
CARTO), and the map stays georeferenced over blank tiles — **absent imagery never blocked pin
placement, it only made it blind.** `CapFiji` was therefore dropped from this gate and Cairns
(1,117.64 km) exercised the same false branch. **This unblocks §10's display-path gate, which
genuinely does need a Fiji spot**: switch BASE MAP to ESRI before siting it.

**17. RESIDUALS, NEITHER BLOCKING.**

- **Durability of the three round-2 catches is unproven.** Logged 00:07–00:09, exported 00:09:27 —
  whether a force-close intervened is not recoverable from the file. `CapB1` and `CapC` **are**
  proven durable: they were written before round 1's confirmed force-close and are present in round
  2's separately-sessioned export. Per v16.73.2 §5, an export reads localStorage's in-memory view, so
  a same-session export is evidence of **shape**, never of **disk**. This closes for free the next
  time the app is opened and re-exported; it does not warrant its own session.
- **`CapA` and `CapB2` carry no catches at all** and are inert spots at 13.33 km and 11.42 km.

**18. HOUSEKEEPING.** Seven `Cap*` spots now on the device, plus the frozen `GateRC` (3 catches) and
`GateNoosa` (1 catch) from the (c) gate. **Delete the `Cap*` set only after this entry is committed**
— `CapKeppel` and `CapCairns` are the only field evidence that the cap fires. Export first. Round-2
artefact: `woongarra-backup-2026-08-24 cap cairns.json` (20,016,446 B); spots 26 → 29; delta
**2,234 B** across 3 spots + 3 catches. Harness artefacts `capgate_sites.js` (136,996 B),
`capgate_report.js` and both results files are in `scratchpad\`, gitignored at `.gitignore:18`.

**19. STILL QUEUED — unchanged unless noted.** `CLAUDE.md` pin + method (v16.74 §5, own build);
display-path remoteness (v16.74 §10 — now with a confirmed route to siting a Fiji limb, §16);
**haversine implemented twice (§14, NEW)**; export filename UTC dating (§8, NEW, needs the one-line
confirmation first); spot-id variable length (§9, NEW, low); v16.71.1 §5 overlay clip (carried, still
unfolded); `storage_check.html` tooling pass; MN v3 (#15) Noosa-OSM fetch + Noosa tide-port wiring;
SC `okHAT` boundary inclusivity; `FLATS_BOUNDS` 3-dp precision; `env.tide`/`env.moon` frame mismatch
(v16.72.3 §7); bite-time graph scrub (v16.73.2 §7, blocked behind the frame mismatch).

**20. NEXT SESSION.** Build **2026.08.24a** (unchanged — this entry ships no code), roadmap
**v16.74.1**, repo head `c83854a` plus this entry's own commit. `CLAUDE.md` unchanged. **The gate is
CLOSED (§1). Next job: (a) recompute on PANEL OPEN** — a build, so it claims the clean integer
**v16.75** and a fresh build string. Then (b) "Here" replaces "Coast-wide". **Do not re-litigate:**
everything in v16.73's, v16.73.1's, v16.73.2's and v16.74's lists, plus — the cap gate is closed and
is not to be re-run (§1); the field bracket is not to be tightened (§15); recompute is on PANEL OPEN,
not `moveend` (v16.72.1 §1); the display path remains deliberately out of scope for the cap build
(v16.74 §10).

---

*v16.74 · 24 Aug 2026 — **BUILD 2026.08.24a SHIPPED: THE 200 km TIDE-PERSISTENCE CAP.** Repo head
`82571ac` plus this entry's own commit; pre-build head `7c4a111`, pre-build `index.html` blob
`5385f5b9b1929aaeaeab2fb4082050deef8a5647`. One variable: `env.tide` is omitted when the nearest
port is further than 200 km. **No schema change** — it reuses the existing omission semantics.
**The on-phone gate has NOT been run; it is the next job and nothing may be dispatched before it.**
Also: a repo incident that removed this file for three days (§7), and a validation-source
contradiction that has been live since v16.73.1 (§5).*

**1. THE CHANGE — three sites, four hunks, measured not inferred.**

- **`index.html:3311`, NEW** — `const PORT_MAX_KM=200;function portInRange(ll){…}`, one physical
  line, column 0, inserted immediately after `nearestPort` at `3310` and **sibling to it** — top
  level of the second `<script>` block, *outside* the best-bite IIFE opening at `3313`. Visible to
  `stampEnv` by closure; no IIFE-boundary hook needed.
- **`index.html:3622`** (was `3621`) — `&&portInRange(ll)` appended as the **last** conjunct of the
  existing `if(...)`, after both `Number.isFinite` checks. **`3623`, the `env.tide=` write, was not
  touched.**
- **`index.html:1052` and `:1091`** — build string `2026.08.21a` → `2026.08.24a`, both sites.

`git diff --numstat` **4 3**; hunk count **4**, counted off `git diff -U0` and each header read
back, not inferred from the site list. Three in-place rewrites (3 added + 3 removed) plus one pure
insertion (`@@ -3310,0 +3311 @@`, 1 added + 0 removed) reconciles to 4/3 exactly.

**2. LAST-CONJUNCT PLACEMENT IS LOAD-BEARING, NOT STYLISTIC.** `portInRange` dereferences `ll.lat`
and `ll.lng` directly, while `nearestPort` also accepts the **array** form
(`Array.isArray(centre)?{lat:centre[0],lng:centre[1]}`). Placed anywhere before the two
`Number.isFinite` checks, an array or a non-finite `ll` would reach the predicate. Short-circuit
guarantees an object with numeric coordinates before it runs. **Recorded because a future
reformatting of that line could reorder the conjuncts and silently remove the guarantee.**

**3. THE 321-BYTE RECONCILIATION, AND WHY THE TOTAL IS UNIQUELY PINNING.** 2,351,947 →
2,352,268 = **+321**, predicted before the write and measured after. Arms derived from line text on
disk: declaration **303** (pure ASCII, chars = bytes) + **1** LF separator + **17** for
`&&portInRange(ll)` (`&&` 2 + `portInRange` 11 + `(` 1 + `ll` 2 + `)` 1). Build-string arms
contribute **0** — same-length by construction. Lines 4,195 → 4,196; trailing byte still `62` (`>`),
no EOF newline introduced.

**The arms cannot trade off.** The dispatch specified `&& portInRange(ll)`; the build shipped
`&&portInRange(ll)`, matching the four existing conjuncts on the same line. Spaced variants total
322 or 323. **So 321 pins the declaration to full length AND the conjunct to exactly that text** —
a stronger property than a matching total usually carries, and the opposite of the v16.73.1 §2
same-length blind spot.

**4. THE BUILD-STRING BUMP WAS READ BACK INDEPENDENTLY, AS §2 OF v16.73.1 REQUIRES.** The byte
delta is blind to a half-bump. Whole-file token counts after the edit: **`2026.08.21a` = 0**,
**`2026.08.24a` = 2**. Also `portInRange` 2 (1 decl + 1 call), `PORT_MAX_KM` 2, `nearestPort` 11
(was 10; the +1 is the new call inside `portInRange`), **`curPort` 5, unchanged**.

**5. THE LEAFLET PIN IS NOT IN `CLAUDE.md`, AND THAT MAKES A STANDING RULE UNSATISFIABLE.**

The first pass at check 2 hashed lines 1209–1214 **including the `<script>` tags**, pre and post,
and confirmed they matched *each other*. That is not the check: it proves the block did not change
during the session, and compares nothing to the pin. **A self-comparison is not a pin comparison.**
Re-run body-only against the recorded value: **`db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`,
character-identical.** The tags-included form `156fc90a…` also matches a value recorded at
`GUYA_ROADMAP.md:2367`, so both forms are pinned and the first pass measured something real — just
not the specified thing.

**Root cause, and it is not the operator's.** `CLAUDE.md` (6,780 bytes) holds the *requirement* and
**zero hex runs, zero digest/hash/sha256 mentions**. The pin lives in this file, nine occurrences,
with `GUYA_ROADMAP.md:1618` naming the body-only method. v16.73.1 §7 made it standing that
**validation steps come from `CLAUDE.md` read at the time, never from a handoff or a chat's
recollection.** For this check that rule is **unsatisfiable** — reading `CLAUDE.md` yields a check
with no value and no method, so the value must come from somewhere else, which is precisely the
sourcing §7 forbids. That is how the check drifted to a self-comparison.

**ACTION, own build, not this one: write the pin and the body-only method into `CLAUDE.md`.** Until
then §7 has a hole with a known shape. *Standing lesson: a rule that says "get it from file X" must
be checked against file X actually containing it. An unsatisfiable rule does not fail loudly — it
gets satisfied from memory and looks like compliance.*

**6. THE PHASE-1 CHARACTERISATION CORRECTED v16.73 §8's BLAST RADIUS.** §8 enumerates six
`nearestPort` call sites and that list is **complete and current**. But `stampEnv` does not call
`nearestPort` — it calls **`curPort(ll)`**, whose own four call sites §8 never enumerates:
`tideTable` (3351), `ANCHOR` (3352), best-bite render (3397), and **`stampEnv`'s tide branch
(3622)**. Ten sites total. **Exactly one reaches persistence — `3622`** — and six of the other nine
already tolerate null. Had Phase 2 been dispatched against §8's list alone, the patch site would
have been reasoned about through the wrong function.

**7. LINE NUMBERS AT AND AFTER 3311 HAVE SHIFTED +1.** The insert displaces everything below it.
Post-build: `curPort` **3350**, `tideTable` **3351**, `ANCHOR` **3352**, best-bite render **3397**,
`stampEnv` assignment **3621**, tide branch **3622**, `env.tide=` write **3623**, `curP` **3965**.
Unchanged (above the insert): `stampEnv` forward declaration 1466, persistence site 1796/1798,
`zoneAt` 1325, drag safeguard 1576–1578, `flatsBand` 1977, `okHAT` 2817, `tideHeightNow` 2834,
`nearestPort` 3310. **Any dispatch quoting a pre-build line number at or past 3311 is stale.**

**8. THE FOUR `CLAUDE.md` CHECKS — PASS, none self-reported.** `node --check` on both extracted
blocks: **PASS / PASS** under node v24.18.0, with `block2.js` confirmed to contain exactly one
`function portInRange` (so the new code is inside the block that was checked). Leaflet body-only
digest character-identical to the pin (§5). `zoneAt()` intact **on the merits** — ranks every
containing polygon and keeps the winner via `rank<bi`, early return reserved for rank 0, with
`ORDER=["MNP","CPZ","HPZ","GUZ"]` at `1227`; most-protective-on-overlap holds. Drag safeguard intact
at `1576`–`1578` — re-runs `zoneAt()` on the dropped coordinates and fires the deferred no-take
alert. **None of the four sits in any diff hunk**, verified against the measured hunk list.

**Independent corroboration across sessions:** post-edit app-block body = **2,134,764 characters**,
against v16.73.1 §4's pre-edit **2,134,443** plus this build's **321**. Difference from expected:
**0**. Two measurements, three days and two sessions apart, reconciling through the byte delta.
(Block1 = 147,552 bytes, matching v16.73.1 §4 exactly; Leaflet is pure ASCII so bytes = chars.)

**9. BEHAVIOURAL NOTES ON THE SHIPPED CODE — recorded, none blocking.**

- The tide path now resolves `nearestPort` **twice** per stamp: once in `portInRange(ll)`, once via
  `curPort(ll)`. Pure function over a 4-entry `const`, so cost is nil and the two cannot disagree —
  **but if `nearestPort` is ever made stateful or memoised, this doubles the coupling.**
- `if(!p)return false` is **dead today** — Phase 1 established `nearestPort` never returns null
  (both exits yield a `PORTS[]` element). Defensive only, and it fails **closed**: an unresolvable
  port omits the stamp rather than inventing one.
- `env.moon` is untouched, so a Fiji catch still gets moon data. Correct — moon phase is not
  port-derived.
- Boundary is **inclusive** (`<=PORT_MAX_KM`): exactly 200.000 km still stamps. Against the measured
  floor of 126.28 km and Fiji at 2,649.71 km, immaterial.
- **Nothing is back-filled.** A previously-stamped out-of-range catch keeps its wrong port until a
  separate, explicitly authorised pass addresses it. No migration, no schema change.
- Pre-edit backup held outside the repo at `…\Temp\claude\…\scratchpad\index.html.pre2026.08.24a.bak`.

**10. NEW, OPEN — THE DISPLAY PATH STILL LIES OUT OF RANGE. Same field deadline.** The cap guards
persistence only. `flatsBand` (1977), `okHAT` (2817), `tideHeightNow` (2834) and `curP` (3965) all
resolve a port at any distance. **At Tokoriki the app will show a tide readout interpolated from
Noosa Head's table and gate depth shading on Noosa's HAT, while correctly refusing to stamp tide on
the catches logged beside it.** The asymmetry is deliberate and defensible — persisted wrong data is
permanent, a display is transient, and one variable per build — **but it is a decision, not an
oversight, and it must not be discovered in Fiji in October.** A field user reading `tide 1.4 m
rising` on Tokoriki has no way to know it is nonsense. Scope when reached: these are display paths
where a null breaks rendering, so the fix is a *readout suppression*, not a null return.

**11. REPO INCIDENT — `2e16a5c` REMOVED THIS FILE FROM THE REPO AND NOBODY NOTICED FOR THREE DAYS.**

The v16.73.1 commit is `GUYA_ROADMAP.md | 7796 deletions(-)`, **zero insertions** — a pushed
`git rm --cached`, not an entry addition, under a commit message describing an entry addition. The
working-tree file survived untracked and kept accumulating, so no content was lost; `origin/main`
simply carried **no roadmap at all** from 21 to 24 Aug. Restored at `7c4a111` as a fresh add
(`create mode 100644`, 8,003 insertions).

**Lineage proven byte-exact before the restore**, by git's own hashing rather than a text
comparison: stripping the two new entries from the restored file reproduced
`870bddb:GUYA_ROADMAP.md` = **`d46721a1446eb3834e277dee61d3981a933fc9de`** (632,849 bytes, matching
v16.73.1 §5's independently recorded figure). Nothing drifted in the three untracked days.

**THE SESSION-CLOSE CHECK COULD NOT HAVE CAUGHT THIS, AND STILL CANNOT.** "`git status` clean and up
to date with `origin/main`" **passed on 21 Aug** — it had to, because the deletion was committed and
pushed. A clean status proves the working tree matches HEAD; it says nothing about whether HEAD
contains the file. **NEW MANDATORY SESSION-CLOSE CHECK, alongside `git status`:**

    git ls-tree -r HEAD --name-only | Select-String 'ROADMAP'

It must return `GUYA_ROADMAP.md`. *Standing lesson: a check cannot detect its own subject going
missing. Existence in HEAD was assumed by the entire authority model and never once verified.*

**12. v16.73.2 §9 CORRECTED — its repo-head claim points at the deletion.** As committed it reads
"repo head is v16.73.1's commit plus this entry's own". v16.73.1's commit is `2e16a5c`, which
removed the file. **The correct pre-build head is `7c4a111`.** Not amended in place — the commit is
pushed and gets a correcting entry, not a rewrite. *Fourth consecutive arc in which a self-written
planning artefact carried a defect into the repo.*

**13. THE TRANSCRIPT IS A LOSSY CHANNEL — CHARACTERISATION OUTPUT GOES TO A FILE.** Phase 1's answers
reached the planning chat truncated **twice, differently**, with a `√ Update installed · Restart to
update` status line overwriting the pane; two copy attempts of the same completed run produced
different text. Recovered by having the session write its answers to `scratchpad/` (gitignored) and
attaching the file. Compare v16.72.3 §1 (dropped characters, mangled integrity rows) and v16.73.1 §3
(console-width truncation showing that a site contains *a* build string but not *which*). **Third
distinct instance.** **STANDING: any Claude Code output longer than a few lines is written to
`scratchpad/` and attached, never pasted.** The transcript has no integrity check and its corruption
is undetectable from inside the receiving chat.

**14. TWO DISPATCH-PROMPT DEFECTS, both caught by Claude Code rather than by review.**

- **A discovery prompt must not state an expected match count.** Phase 1 said "single match
  expected" for `stampEnv`. There are two — a forward declaration at `1466` and the assignment at
  `3620`. A search told what to expect stops looking once it finds it, converting a measurement into
  a confirmation. Had it stopped at the first match, it would have characterised `let stampEnv=null`
  as the function body.
- **A build dispatch adapted from a read-only characterisation inherits its terminal conditions,
  and they are wrong.** Phase 2 carried over "`git status` must be clean when you finish", which no
  build editing a tracked file can satisfy. Flagged rather than silently resolved. Correct wording
  for a build: *nothing staged, nothing committed, no untracked files.*

**15. THE ON-PHONE GATE — NOT RUN. THIS IS THE NEXT JOB.** No in-app readout of `env.tide.port`
exists, so as with (c) and (d) this **cannot be gated on the phone alone** — it needs a `version:2`
export inspected off-device. Confirm a Pages Actions run completed and `2026.08.24a` reads live in
the app before starting; a push is not a deployment.

**SETUP.** Force-close/reopen the home-screen app; confirm `2026.08.24a`. Export a `version:2`
backup before logging anything. Three spots, reached by panning the map — no travel required.

- **LIMB A — THE CAP FIRES.** Spot at Tokoriki (≈ −17.62, 177.05), ≈2,650 km from Noosa Head. Log a
  catch. **PASS** = **no `tide` key at all** — not `null`, not `{}` — with `moon` present.
- **LIMB B — THE DISCRIMINATING ONE.** Spot near Point Danger (≈ −28.17, 153.55), ≈97 km from
  Brisbane Bar. Log a catch. **PASS** = `tide` **present**, `port:"Brisbane Bar"`, `ht` plausible
  against the Brisbane Bar table for that instant. **This limb is what stops a cap that is too
  tight, and a cap set to 0 passes LIMB A perfectly.** It protects real Gold Coast field data —
  §9's hard floor of 126.28 km exists for exactly this failure.
- **LIMB C — CONTROL.** Redcliffe spot, unchanged behaviour: `tide` present,
  `port:"Brisbane Bar"`.

A and B are **mutually discriminating**: a broken `dayTideSampler` fails both, a dead predicate
fails A, an always-true predicate fails B. Force-close, reopen, export, inspect off-device. **Parse
the export, never print it** — a `version:2` export carries base64 photos and is megabyte-scale.
**Epoch/date bounds must be recomputed for the day the gate actually runs** (v16.73.2 §1: a computed
bound carries the date it was computed for, and a stale bound fails open).

**16. STILL QUEUED — unchanged unless noted.** `CLAUDE.md` pin + method (§5, NEW, own build);
display-path remoteness (§10, NEW); v16.71.1 §5 overlay clip (carried, still unfolded);
`storage_check.html` tooling pass; MN v3 (#15) Noosa-OSM fetch + Noosa tide-port wiring; SC `okHAT`
boundary inclusivity; `FLATS_BOUNDS` 3-dp precision; `env.tide`/`env.moon` frame mismatch
(v16.72.3 §7 — now with a downstream dependent, the bite-time graph scrub at v16.73.2 §7); bite-time
graph scrub (v16.73.2 §7).

**17. NEXT SESSION.** Build **2026.08.24a**, roadmap **v16.74**, repo head `82571ac` plus this
entry's own commit. `CLAUDE.md` unchanged — but see §5, it is now known to be incomplete. **Next
job: the ON-PHONE GATE (§15). It is not a build, and nothing may be dispatched before it passes.**
After it: (a) recompute on PANEL OPEN; then (b) "Here" replaces "Coast-wide". **Do not
re-litigate:** everything in v16.73's, v16.73.1's and v16.73.2's lists, plus — the cap is built and
sited at the persistence site (§1); the display path is deliberately out of scope for this build
(§10); the (c) gate is closed and is not to be re-run.

---

*v16.73.2 · 24 Aug 2026 — **THE (c) ON-PHONE GATE IS CLOSED. ALL FOUR LIMBS PASS.** No build, no
code, no data, no schema change. Build stays **2026.08.21a**; repo head is v16.73.1's commit plus
this entry's own. Evidence: `woongarra-backup-2026-08-24.json`, a `version:2` export taken
`2026-08-24T08:12:10.264Z` (18:12:10 AEST), inspected off-device. **`env.wind` provenance is
confirmed in the field and the queue is unblocked.***

**1. THE GATE RAN THREE DAYS LATE, AND §6's EPOCH BOUNDS DID NOT TRAVEL.** v16.73.1 §6 computed
`at` bounds for 21 Aug. The session ran 24 Aug, so those bounds were void on arrival — recomputed
before any limb was read: 2026-01-01T00:00Z = 1,767,225,600 s; 24 Aug is day 236, so 235 elapsed
days × 86,400 = 20,304,000 s → **1,787,529,600,000 ms** at 2026-08-24T00:00Z; AEST is UTC+10, so
any `at` logged 24 Aug local falls in **1,787,493,600,000 – 1,787,580,000,000**. Both observed
values land inside. **Standing lesson: a computed bound carries the date it was computed for.** A
gate that slips its day silently loses its sanity check unless the bound is re-derived, and a stale
bound fails open — it accepts everything in the wrong day just as readily.

**2. THE SESSION TIMELINE RECONSTRUCTS FROM THE EXPORT ALONE.** Spot ids encode creation epoch:
`GateRC` `s1787558111506579` → **17:55:11**, `GateNoosa` `s1787558177541549` → **17:56:17**, both
before the 17:57:23 fetch. `GateRC` at −27.23297, 153.118207; `GateNoosa` at −26.408168, 153.115311.
Aaron's contemporaneous written notes were 17:57 / 18:03 / 18:09. The file corroborates the first
and third; the second is unexplained and **provably benign** (§5).

**3. THE FOUR LIMBS, VERBATIM FROM THE EXPORT.**

- **LIMB 1 — PASS, and the §6 ambiguity never arose.** Catch 1, `time` `18:02`:
  `wind={dir:98,kn:6,port:"Noosa Head",at:1787558243369}`, `tide={state:"rising",ht:2.05,
  port:"Brisbane Bar"}`. **Two provenance strings on one record that disagree** — the observable the
  §1-rejected mirror of (d) cannot produce. §6's discriminator resolves it further rather than being
  needed: `at` = **17:57:23.369 AEST**, matching the recorded button press, *not* the 18:02 log. No
  silent re-fetch across the pan, and `liveWindPort` survived the ~110 km move exactly as the Phase 1
  characterisation predicted.
- **LIMB 2 — PASS, both conditions evaluable.** Catch 2, `time` `18:08`, carries
  `at:1787558243369` — **identical to catch 1 to the millisecond** — with `dir`/`kn` also identical
  at 98/6. The two `time` values differ (`18:02` vs `18:08`), so §6's degradation-to-one-condition
  hazard did not materialise; the 5-minute spacing was sufficient against minute-granular `time`.
  `Date.now()` is at the fetch site, not the stamp site.
- **LIMB 3 — PASS.** Catch 3, `time` `18:09`: `wind={dir:73,kn:5,port:"Brisbane Bar",
  at:1787558946241}` = **18:09:06.241 AEST**, matching the recorded press and strictly greater than
  limb 1's. `wind.port === tide.port === "Brisbane Bar"`.
- **LIMB 4 — PASS.** Catch 4, `time` `18:10`: `env` keys are exactly `["moon","tide"]`. **No `wind`
  key at all** — not `null`, not `{}` — while `tide` and `moon` survive, confirming `1798` does not
  delete `env`. The spot was reached by tapping its pin rather than panning; §11's own note
  ("no tap-the-pin discipline is needed here") holds, and no limb depended on map centre.

**4. TWO UNPLANNED CONTROL LIMBS, NEITHER DESIGNED IN.** Both are free stuck-result discriminators,
which is precisely the property the gate-design rule demands and which no limb above was written to
supply.

- **Limb 3's `dir`/`kn` changed** — 98/6 → 73/5. A cached replay of limb 1's response would have
  returned 98/6 again. The values moving proves the second fetch reached Open-Meteo rather than
  re-serving a stale scalar. Limb 3 was scoped as a control for `port`; it turns out to control for
  fetch-liveness too.
- **Limb 4's `tide.port` reads `"Noosa Head"`** on a spot at −26.408, while all three `GateRC`
  records read `"Brisbane Bar"` at −27.233. Tide-port resolution following **spot** coordinates —
  established by harness at v16.72.3 §3 — is now corroborated by execution in the field, on a
  record logged for an unrelated purpose.

*Standing lesson, extending v16.72.3 §3: the harness-stub finding generalises past harnesses. A
limb whose observable is a **measured quantity** rather than a **selected label** controls for
staleness for free, because a stuck value is detectable where a stuck string is not.*

**5. TWO RESIDUALS, NEITHER BLOCKING.**

- **The 18:03 note is unexplained but cannot have been a fetch.** Catch 2's `at` is still
  1787558243369, so nothing wrote between 17:57:23 and 18:09:06. Whatever happened at 18:03 — a
  failed press, a mis-noted pan — left no trace in the persisted state and cannot have influenced
  any limb. Recorded so a later reader does not mistake a three-note log for a three-fetch session.
- **Catch 4's durability is unproven, its shape is not.** Catches 1–3 were written before limb 4's
  force-close and are present after it, so they have crossed a restart and are disk-durable.
  Catch 4 was logged 18:10 and exported 18:12; whether the step-16 force-close intervened is not
  recoverable from the file. The limb's PASS rests on `env` shape, which the export shows
  regardless. **Note the asymmetry: an export reads localStorage's in-memory view, so a same-session
  export can never be evidence of disk persistence** — only a restart between write and read can.
  That is the iOS async-flush rule stated from the export side, where it had not been written down.

**6. EXPORT NAMING IS A COLLISION HAZARD.** `woongarra-backup-2026-08-24.json` is date-only, one
day distant from `woongarra-backup-2026-08-19.json`, the §7/§4 evidence artefact. Two exports on a
single day silently overwrite. **Adopt a suffix on any export retained as evidence** (purpose or
time), and treat the bare date form as scratch. Not actioned; recorded as a standing hazard.

**7. NEW BACKLOG ITEM — BITE-TIME GRAPH SCRUB.** Requested this session: drag along the best-bite
curve and read the **exact time at an arbitrary point**, not only at labelled peaks/endpoints. Not
scoped — two questions decide the shape, and neither is answered: (i) touch-drag on the existing
canvas versus a rendered cursor line with its own hit-testing; (ii) what time resolution the readout
displays. **(ii) is not cosmetic** — a minute-resolution readout would surface the
`env.tide`/`env.moon` frame mismatch (v16.72.3 §7) in the UI for the first time, so that item likely
has to close before this one ships, or the graph will display the mismatch to the field user.
Queued, not sequenced.

**8. HOUSEKEEPING.** The four gate records and their two spots (`GateRC` `s1787558111506579`,
`GateNoosa` `s1787558177541549`) are **UNFROZEN** — the gate they protected has closed.
`woongarra-backup-2026-08-24.json` joins `woongarra-backup-2026-08-19.json` as a permanent evidence
artefact: **do not overwrite either.** `Test`/`Test02` deletion confirmed executed — neither appears
in the export.

**9. NEXT SESSION.** Build **2026.08.21a**, roadmap **v16.73.2**, repo head v16.73.1's commit plus
this entry's own. `index.html` unchanged; `CLAUDE.md` unchanged. **The (c) gate is CLOSED and the
queue is unblocked. Next job: the `nearestPort()` distance cap, 200 km, AT THE PERSISTENCE SITE and
never inside `nearestPort()` (v16.73 §8/§9) — it is a build and needs its own on-phone gate.** Then
(a) recompute on PANEL OPEN; then (b) "Here" replaces "Coast-wide". **Do not re-litigate:**
everything in v16.73's and v16.73.1's lists, plus — the (c) gate is closed on all four limbs (§3)
and is not to be re-run. **Still queued, unchanged:** v16.71.1 §5 overlay clip (carried, still
unfolded); `storage_check.html` tooling pass; MN v3 (#15) Noosa-OSM fetch + Noosa tide-port wiring;
SC `okHAT` boundary inclusivity; `FLATS_BOUNDS` 3-dp precision; `env.tide`/`env.moon` frame mismatch
(v16.72.3 §7, now with a downstream dependent — §7 above).

---

*v16.73.1 · 21 Aug 2026 — **VALIDATION CLOSED ON BUILD 2026.08.21a. NO BUILD, NO CODE, NO DATA,
NO SCHEMA CHANGE.** Build stays **2026.08.21a**; repo head `870bddb` plus this entry's own commit.
The (c) ON-PHONE GATE (v16.73 §11) is still **NOT RUN** and remains the next job.*

**1. THE §10 RESIDUAL IS CLOSED.** v16.73 §10 flagged that the `var w` collision check at
`index.html:1797` searched lines 1789–1800 while `var` hoists to the whole enclosing function.
`openCatchSheet` was located by declaration (single match, line **1775**) and its extent bounded by
brace-depth to **1820**; the sweep ran 1775–1840 (function extent plus 20 lines of deliberate
margin, since over-sweeping is free and under-sweeping is the original defect). **Exactly one
`\bw\b` hit in that range: line 1797 itself.** No collision. Closed.

**2. THE 177-BYTE RECONCILIATION, COMPUTED NOT ASSERTED.** File delta 177 = 34 + 86 + 57 across the
three whole-line splices, each arm derived from the line text on disk:

- `1417` new 71 (`let ` 4 + `liveWindDir=null,` 17 + `liveWindKn=null,` 16 + `liveWindPort=null,` 18
  + `liveWindAt=null;` 16) − old 37 = **+34**
- `1797` new 220 − old 134 = **+86** (the delta is `if(liveWindPort!=null)w.port=liveWindPort;` 42 +
  `if(liveWindAt!=null)w.at=liveWindAt;` 36, plus the `var w=` / `o.env.wind=w;` indirection 8)
- `1856` appended `liveWindPort=(_wp&&_wp.name)||null;` 35 + `liveWindAt=Date.now();` 22 = **+57**

Both build sites were spliced same-length by construction, so **the byte delta is blind to a
half-bump** — it reads 177 whether the bump landed on both sites, one, or neither. Read back
independently (§3). Recorded so the method's blind spot is not rediscovered.

**3. BUILD STRING CONFIRMED AT BOTH SITES.** `index.html:1052` and `:1091` both read
`2026.08.21a`, extracted by regex from the line text rather than eyeballed — the first
`Select-String` attempt returned both lines **truncated by console width**, which shows a site
contains *a* build string but not *which*. v16.73 §5's two-site rule now has its first verified
non-drift.

**4. VALIDATION COMPLETE AGAINST `CLAUDE.md`'s FOUR CHECKS — all verbatim, none self-reported.**

- `node --check` on both extracted script blocks: **exit 0** and **exit 0**.
- Inlined Leaflet byte-identical: computed digest
  `db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`, character-identical to the
  pin. Two `<script>` blocks found, matching the architecture invariant — bodies 147,552 and
  2,134,443 chars, separated by a single LF (so the working tree is LF and the `core.autocrlf`
  CRLF hazard did not apply).
- `zoneAt()` intact **on the merits, not merely present**: `index.html:1325` scans every feature and
  keeps the best rank (`rank<bi`), never first-match; `bi=99` initial vs `rank=98` for an unknown
  `zt` means an unrecognised zone still outranks "no zone"; and the `rank===0` early return is safe
  because **`index.html:1227` is `const ORDER=["MNP","CPZ","HPZ","GUZ"]`** — index 0 is MNP, so
  nothing can outrank it. Most-protective-on-overlap holds.
- Green-zone drag safeguard intact **and stronger than the UI copy claims**: `1576` persists the
  dropped coordinates, **`1577` re-runs `zoneAt()` on them** and refreshes via
  `renderSpots()` + `openPopup()`, and `1578` fires a deferred blocking alert *only* when the new
  zone is no-take. The `setTimeout(…,60)` defers the alert until after the popup paints. The alert
  surfaces zone name + ID and says to confirm before fishing — no legality assertion, hard rule 1
  holds. Non-no-take zone changes do not alert but are **not silent**: the re-render carries the
  fresh `zoneAt()` result. That is the design, not a gap.

**5. THERE IS NO "jsdom BOOT TEST" AND THERE NEVER WAS.** A jsdom boot check was asserted as a
validation step during this session. It is not in `CLAUDE.md`, not in this roadmap (**0 occurrences
across 632,849 bytes / 7,796 lines**), and not installable state in the repo — no `package.json`,
no `.js` files, no global `node_modules`. It came from a chat's working context, not from a file.
`CLAUDE.md`'s post-edit list is the four checks in §4 and nothing else. **Do not add jsdom**: a
desktop Node/vm harness is not device-representative for a persistence-shape change, which is
precisely why the on-phone gate exists.

**6. §11 GATE AMENDMENTS — three, fold in before the phone session, not during it.**

- **Limb 1's failure mode is not diagnostic as written.** Both ports reading `"Brisbane Bar"` has
  two causes: the mirror defect §1 rejected, *or* a silent wind re-fetch after the pan — in which
  case `"Brisbane Bar"` is **correct** provenance and the gate would fail a working build.
  **Record the wall-clock second of the Noosa button press before panning.** Limb 1's `at` ≈ that
  instant ⇒ genuine mirror defect. `at` ≈ the log time ⇒ re-fetch, inconclusive, no build fault.
- **Limb 2 inherits the same ambiguity in reverse.** A differing `at` is specified as proof that
  `Date.now()` landed at the stamp site, but an intervening re-fetch produces the same observable.
  Discriminator: a stamp-site defect makes `at` ≈ each record's **own** `time` for *both* records;
  a re-fetch gives both a single new `at` matching neither. Also: `time` is a wall-clock string —
  **confirm the two records' `time` values actually differ** before accepting the limb, or the
  second condition is unevaluable and the limb silently degrades to a one-condition check.
- **The epoch sanity check has ~11.6-day resolution as written.** `1.787×10¹²` to `1.788×10¹²`
  spans 1×10⁹ ms = 11.57 days, so it cannot detect a day-scale error. Computed bounds instead:
  2026-01-01T00:00Z = 1,767,225,600 s; 21 Aug is day 233, so 232 elapsed days × 86,400 =
  20,044,800 s → 1,787,270,400,000 ms at 2026-08-21T00:00Z. AEST is UTC+10, so any `at` logged on
  21 Aug local must fall in **1,787,234,400,000 – 1,787,320,800,000**.

**7. STANDING, NEW — two.**

- **Validation steps come from `CLAUDE.md`, read at the time, not from a handoff or a prior chat's
  recollection.** The existing rule is that a chat's claim never outranks a file; §5 is that same
  failure in a new place — a *checklist item* sourced from a chat. A step nobody can find in a file
  is not a step.
- **On a file carrying megabyte-scale data blobs, a regex hit is not evidence about code, and a
  matched line must never be printed whole.** `MNP.*CPZ.*HPZ.*GUZ` matched the baked ZONES GeoJSON
  (lines 1219/1227/1276 are zone data, hundreds of KB each) and `ORDER\s*=` matched `border=` inside
  minified Leaflet. Printing one blew a transcript to ~3,000 lines and answered nothing. Require a
  declaration keyword in the pattern and slice every hit (`Substring(0, min(200, len))`).

**8. NEXT SESSION.** Build **2026.08.21a**, roadmap **v16.73.1**, repo head `870bddb` plus this
entry's own commit. `index.html` unchanged by this entry; `CLAUDE.md` unchanged. **Next job: the (c)
ON-PHONE GATE (v16.73 §11 as amended by §6 above). It is not a build, and nothing may be dispatched
before it passes.** After it: the `nearestPort()` distance cap at 200 km, at the persistence site
(v16.73 §8/§9); then (a) recompute on PANEL OPEN; then (b) "Here" replaces "Coast-wide". **Do not
re-litigate:** everything in v16.73's do-not-re-litigate list, plus — §10 is closed (§1); there is
no jsdom step (§5).

---

*v16.73 · 21 Aug 2026 — **JOB (c) SHIPPED: `env.wind` NOW CARRIES PROVENANCE. Build 2026.08.21a.**
Repo head `5ec347b`; roadmap head at build time `06a4c3c` (v16.72.3). This build **changes the
persisted catch record shape** — `env.wind` gains optional `port` and `at`. One variable: additive
provenance only, no change to WHEN wind is written. **The on-phone gate has NOT been run — it is the
next job and nothing may be dispatched before it.***

**1. (c) IS NOT A MIRROR OF (d) — the handoff instruction was wrong and was corrected before
dispatch.** v16.72.2's NEXT SESSION said "mirroring (d) exactly". A literal mirror would write
`port: nearestPort(spotCoords).name`, stamping the port nearest the CATCH onto a wind value fetched
for a different port — replacing honest silence (`{dir,kn}`, no provenance) with a confident wrong
answer on a persisted field. Same failure shape as the `FLATS_BOUNDS` key-miss. **Phase 1 found the
fetch is better than assumed:** `index.html:1854` sends `_wp.lat`/`_wp.lng` — the PORT's own
coordinates, resolved from `nearestPort(map.getCenter())` at `index.html:1853`. So `env.wind.port`
is not an approximation of where the wind came from, it **is** the fetch coordinate. Stronger
provenance than `env.tide.port`, which names a table rather than a measurement point.

**2. TTL-AS-OMISSION WAS DROPPED. The raw fetch instant is stored instead.** The tide guard omits
because a wrong `ht` has no field that could rescue it. Wind is not that: `{dir,kn,port,at}` is
self-describing at any age, so a reader can compute staleness and decide. Omitting on age would
destroy a real observation to prevent a misreading that provenance already prevents. **`at` is
`Date.now()` at fetch time — an absolute UTC instant, frame-free by construction, which sidesteps
the v16.72.3 §7 tide/moon frame mismatch rather than inheriting it.**

**3. THE CHANGE — three lines plus the build string.**

- `index.html:1417` — `let liveWindDir=null,liveWindKn=null,liveWindPort=null,liveWindAt=null;`
- `index.html:1856` — `liveWindPort=(_wp&&_wp.name)||null;liveWindAt=Date.now();` appended before
  `renderSpots()`, in the same statement run as the two existing assignments, so the four scalars
  are never observable in a mixed state where `dir` is fresh and `port` is stale.
- `index.html:1797` — `port` and `at` written CONDITIONALLY onto a local `w`, so a null is never
  persisted for either. **Absent means unknown, exactly as `env.tide.port`.** The pre-existing
  `kn:null` asymmetry (`dir` unconditional, `kn` independently null-checked) is preserved
  byte-for-byte — recorded, deliberately out of scope, do not "fix" it in a later build without
  its own variable.
- No read site changed: `1489` (catch row), `1798` (delete-if-empty), `3488` (`scoreSpotsFor`),
  `3607` (`windRows` filter) all byte-identical.

`stampEnv`, `nearestPort`, `curPort` and `PORTS` re-hashed against the values recorded in the
previous two sessions: untouched. Wind remains stamped OUTSIDE `stampEnv` — `index.html:3606`
states the reason in the file: there is no historical wind table to reconstruct from. The fetch
FAILURE path (`index.html:1857-1864`) assigns to none of the four scalars — `1863` writes only
`o.innerHTML` — so on a failed fetch all four retain their prior values, which is the pre-existing
behaviour of the two existing ones, unchanged.

**4. VALIDATION — BYTE ARITHMETIC BOUNDS THE CHANGE COMPLETELY.** 2,351,947 − 2,351,770 = **+177**,
reconciling exactly against the three line deltas: (71−37) + (220−134) + (138−81) = 34 + 86 + 57 =
177. All added characters are ASCII, so char delta = byte delta; **the total matching to the byte
means no other line changed length**, and LINES unchanged at 4,195 excludes an added line. With 5
MEASURED `@@` headers at the 5 expected locations, a same-length edit elsewhere is also excluded.
Leaflet block hash exact (`db49d009…5641a`, 147,552 bytes), both script blocks `node --check` exit
0, exactly 2 `<script>` blocks, `zoneAt()` still ranking by `ORDER` with the early return only at
`rank===0` (most-protective on overlap, not first-match), green-zone drag safeguard intact at
`1576-1578`. `git diff --numstat` 5/5. **Standing method, promoted: a byte-delta reconciliation
against per-line character deltas is strictly stronger than a hunk count — it excludes same-length
edits elsewhere in the file, which a hunk count alone does not.**

**5. STANDING FACT — THE BUILD STRING IS AT TWO SITES, NOT ONE.** `index.html:1052` (header) and
`index.html:1091` (footer). Both read `2026.08.16a` before this build, so they have never drifted.
The dispatch said "the line found in P3", singular; Claude Code bumped both and flagged the
deviation, correctly. **Every future dispatch must name BOTH sites** — a half-bump ships a header
and footer disagreeing about the build, and "confirm the build string in-panel" is the first step of
every on-phone gate. Five other `2026.08.NNa` matches (`2000`, `2219`, `2227`, `2415`, `2965`) are
historical references in comment prose and must stay untouched.

**6. NEW — `at` CAN PRECEDE ITS OWN CATCH, BY YEARS.** `date`/`time` are user-editable form fields;
a backdated catch (as the 2025-09-23 EXIF record was) gets TODAY's wind stamped on it, so
`catchTime − at` goes hugely negative. The behaviour is pre-existing and unchanged by (c); what
changed is that it is now **detectable**, which is (c)'s own argument in miniature. **Any consumer
of `at` must treat it as describing the WIND OBSERVATION, never the catch.** `at` is UTC-absolute
while `date`/`time` are wall-clock strings — not the same clock, never to be subtracted naively.

**7. v16.72.3 §6 CORRECTED — WRONG PORT NAMED.** §6 said a Fiji catch stamps
`port:"Burnett Heads"`. **It resolves to Noosa Head at 2,649.71 km**; Burnett Heads is 2,670.84 km.
The substance stands — a Fiji catch stamps a QLD port and a QLD tide height — but a gate written
against "expect Burnett Heads" would fail for the wrong reason and read as a code defect. Root
cause: the port name was asserted from reasoning ("northernmost port, so closest to Fiji") rather
than computed. **Fiji is east, not north.** v16.72.3 §3's separate claim — that a `{0,0}` harness
stub resolves to Burnett Heads — is unaffected and correct. Tagged inline at §6. **Third
consecutive arc in which a self-written planning artefact carried a defect into the repo; the new
failure mode is unverified NUMBERS inside an otherwise red-teamed entry. Numbers get computed, not
asserted.**

**8. v16.72.3 §6 UNDER-SPECIFIED — THE CAP MUST NOT LIVE INSIDE `nearestPort()`.** Two call sites
swallow a null return and substitute `PORTS[0]`: `index.html:1853`
(`nearestPort(map.getCenter())||PORTS[0]`) and `index.html:3349` (`curPort()`'s
`catch(e){return PORTS[0]}`). A guard returning null from `nearestPort()` would therefore make a
Fiji session fetch wind at **Burnett Heads' coordinates** and stamp **Burnett's tide table** —
replacing a wrong-by-20 km answer with a wrong-by-2,670 km one, silently. Worse than the defect.
Four further call sites (`1977` `flatsBand`, `2817` `okHAT`, `2834` `tideHeightNow`, `3964` `curP`)
are render/query paths where a null breaks display rather than protecting data. **The cap belongs
at the PERSISTENCE site — a separate predicate consulted by `stampEnv`'s tide branch, never a
change to the shared resolver.** And once wind carries provenance (§1), the distance problem is a
**tide-path problem only**: a Fiji wind record reads honestly as "Noosa Head wind, timestamped",
while a Fiji tide record reads as authoritative nonsense. Tagged inline at §6.

**9. CAP VALUE DECIDED: 200 km.** Working, from Phase 1's coastline sweep (lat −24.0 to −28.5, 0.1°
steps, coastline longitude interpolated piecewise-linearly through the four `PORTS` entries):

- Largest sampled coast-to-nearest-port distance **126.28 km** — but at the sweep boundary lat
  −28.5, roughly 35 km into NSW past Point Danger. Artificial: the value increases monotonically
  toward the limit, so it is set by where the sweep was told to stop, not by port geometry.
- Real southern limit, Point Danger (−28.17, 153.55) → Brisbane Bar ≈ **97 km**.
- Largest genuine INTERIOR maximum **93.17 km** at lat −25.6 — the Noosa Head / Burnett Heads
  handover near Rainbow Beach / Double Island Point. Second interior maximum 35.29 km at lat −27.0,
  the Brisbane Bar / Mooloolaba handover.
- Fiji **2,649.71 km**.

200 km gives 1.6× headroom over the largest measured value including the artificial boundary case,
2.1× over the real-world worst, and sits 13× below Fiji. Anything from ~150 to ~500 km separates the
two populations cleanly — there is no tuning risk here. **HARD FLOOR: the cap must exceed 126.28
km**, or a legitimate Gold Coast catch loses its tide stamp — a "fix" that deletes real field data.
Port-to-port separations for reference (km): Burnett–Brisbane 299.56, Burnett–Mooloolaba 225.32,
Burnett–Noosa 193.08, Brisbane–Noosa 109.60, Brisbane–Mooloolaba 76.15, Mooloolaba–Noosa 33.45.

**10. RESIDUAL, LOW.** The `var w` collision check at `index.html:1797` searched lines 1789–1800,
but `var` hoists to the whole enclosing function (`openCatchSheet`, per the hunk header). Contained
in fact — `1798`–`1800` do not reference `w` — but the search window was narrower than the scope it
needed to cover. Close whenever convenient with a 1770–1805 sweep for `\bw\b`.

**11. THE ON-PHONE GATE — NOT RUN. THIS IS THE NEXT JOB.** There is no in-app readout of `port` or
`at` (`index.html:1489` renders `dir` and `kn` only), so like (d) this **cannot be gated on the
phone alone** — it requires a `version:2` export inspected off-device. That is a consequence of the
one-variable rule, not an oversight, and it must not be discovered halfway through a gate session.

**SETUP.** Force-close/reopen the home-screen app; confirm `2026.08.21a` in BOTH the header and the
footer (§5 — first field check of the two-site bump). Export a `version:2` backup **before logging
anything**. Create two fresh test spots, one at Redcliffe and one at Noosa.

- **LIMB 1 — THE DISCRIMINATING ONE.** Centre the map on Noosa, press the wind button, confirm the
  label reads `Checking live wind at Noosa Head…`. **Pan to Redcliffe WITHOUT pressing the button
  again.** Log a catch at the Redcliffe spot. **PASS** = `env.wind.port === "Noosa Head"` AND
  `env.tide.port === "Brisbane Bar"` — **two provenance strings on one record that must DISAGREE.**
  The naive mirror of (d) rejected in §1 would put "Brisbane Bar" in both. Also field-tests that
  `liveWindPort` survives a ~110 km pan, as the Phase 1 characterisation predicted.
- **LIMB 2 — `at` IS FETCH TIME, NOT STAMP TIME.** Without re-fetching, log a second catch at the
  same Redcliffe spot a minute or two later. **PASS** = `at` **identical to the millisecond** across
  both records while their `time` fields differ. A difference means `Date.now()` landed at the stamp
  site — a real defect that no other limb detects.
- **LIMB 3 — CONTROL.** Press the wind button with the map at Redcliffe, confirm the label reads
  `Brisbane Bar`, log a third catch there. **PASS** = `wind.port === tide.port === "Brisbane Bar"`
  and `at` strictly greater than limb 1's.
- **LIMB 4 — ABSENT MEANS UNKNOWN.** Force-close and reopen (all four scalars reset to null at
  `1417`). Without touching the wind button, log a catch at the Noosa spot. **PASS** = **no `wind`
  key at all** — not `null`, not `{}`. `env` survives with tide and moon, so `1798` will not delete
  it.

Then force-close, reopen, export `version:2`, move it off-device, and inspect all four records.
Sanity-check `at` as a plausible epoch-ms value for 21 Aug 2026 (≈1.787×10¹²), not merely present
and equal. **No tap-the-pin discipline is needed here** — that rule serves gates requiring spot ≠
map centre, and no limb above depends on where the map is.

**12. HOUSEKEEPING.** `Test` (`s1787143687537239`) and `Test02` (`s1787143995330639`) and their five
catches are **unfrozen** (v16.72.3 §8) and may be deleted before the gate — export first, and keep
`woongarra-backup-2026-08-19.json` untouched as the §7/§4 evidence artefact. **The four NEW gate
records and their two spots are frozen until the (c) gate closes.**

**13. STILL QUEUED — unchanged.** v16.71.1 §5 overlay clip (carried, promoted, still unfolded; it
did not ride with v16.72 and did not ride with (c)). `storage_check.html` tooling pass: single sized
probe, not the KiB-granular binary search; `navigator.storage.estimate()` reports the StorageManager
origin quota and does not bound localStorage. MN v3 (#15): 3a OSM-only fetch → 3b clip and
**measure**, import nothing → sized probe → decide. SC `okHAT` boundary inclusivity (464 rows at
exactly −2.24 m + 51 at −2.81 m = 515). `FLATS_BOUNDS` quoted to 3 dp against a method with ±1–2 mm
jitter. `nearestPort()` distance cap (§8/§9) — decided, not built, needs its own gate.
`env.tide`/`env.moon` frame mismatch (v16.72.3 §7).

**NEXT SESSION.** Build **2026.08.21a**, roadmap **v16.73**, repo head `5ec347b` plus this entry's
own commit. `CLAUDE.md` unchanged — no re-upload needed. **Next job: the (c) ON-PHONE GATE (§11). It
is not a build, and nothing may be dispatched before it passes.** After it: the `nearestPort()`
distance cap at 200 km, at the persistence site (§8/§9); then (a) recompute on PANEL OPEN; then (b)
"Here" replaces "Coast-wide". **Do not re-litigate:** recompute is on PANEL OPEN, not `moveend`
(v16.72.1 §1); the C3 arc is closed (v16.70.1); the 600×600 grid cap stays; "Coast-wide pins the
anchor" is false (v16.71.1 §6); `env.tide.port` is never back-filled (v16.72.2 §3); `ht`/`port`
provenance is settled (v16.72.3 §1); (c) is NOT a mirror of (d) (§1); the cap does not go inside
`nearestPort()` (§8).

---

*v16.72.3 · 21 Aug 2026 — **THE §7 RESIDUAL IS CLOSED — PASS.** No build, no code, no data, no
schema change. Build stays **2026.08.16a**; repo head `bbc5e22` plus this entry's own commit.
Read-only characterisation plus an extracted-code harness, run against `index.html` at blob
`2068474366c9a6522b563756154577b714e3b7c4` (working tree = committed blob, verified). Housekeeping
unfreezes. Two new findings, neither of which rides with job (c).*

**1. THE INVARIANT HOLDS — `ht` AND `port` COME FROM THE SAME TABLE.** `curPort()` resolves twice
per `stampEnv` call: indirectly via `dayTideSampler`→`tideTable()`→`curPort(ll)`
(`index.html:3621`→`3352`→`3350`), which chooses the table that produces `ht`; and directly at
`index.html:3621` (`const _p=curPort(ll)`), which produces the `port` string. Both receive the same
`ll` object, `stampEnv` gates the whole tide branch on `Number.isFinite` coords so the
`ll||map.getCenter()` arm at `index.html:3349` is never taken, and `nearestPort()`
(`index.html:3310`) is a pure function of `(ll, PORTS)` — fixed haversine over a module-level
constant, no time or state input. Same input, same output. **The 23:21 field record's
`ht: 1.35` reproduces exactly from the Brisbane Bar table and its `port` reads `"Brisbane Bar"`.**

**REPRODUCED BY HAND from the raw table rows, not taken from the harness.** Cosine interpolation
(`index.html:3358`), `p.v+(n.v−p.v)(1−cos πf)/2`, bracketing across `dayTideSampler`'s ±1-day
window (`index.html:3354`) — the 19 Aug stamps all fall past that day's last event, so the
bracketing pair spans into 20 Aug:

- Brisbane Bar, p = 19 Aug 20:25 L 0.97 (h 20.4167), n = 20 Aug 01:51 H 1.64 (h 25.85), span
  5.4333 h. **23:21** (h 23.35): f = 2.9333/5.4333 = 0.53988, πf = 97.18°, w = 0.56249 →
  0.97 + 0.67×0.56249 = 1.34687 → **1.35** ✓. **23:04** (h 23.0667): f = 2.65/5.4333 = 0.48773,
  πf = 87.79°, w = 0.48072 → 0.97 + 0.67×0.48072 = 1.29208 → **1.29** ✓
- Mooloolaba, p = 19:10 L 0.82, n = 20 Aug 00:22 H 1.19, span 5.2 h. **23:21**:
  f = 4.1833/5.2 = 0.80449, πf = 144.81°, w = 0.90858 → 0.82 + 0.37×0.90858 = 1.15617 → **1.16** ✓
- Noosa Head, p = 18:59 L 0.93, n = 20 Aug 00:18 H 1.33, span 5.3167 h. **22:53** (h 22.8833):
  f = 3.9/5.3167 = 0.73354, πf = 132.04°, w = 0.83495 → 0.93 + 0.40×0.83495 = 1.26398 → **1.26** ✓

Four of the twelve harness cells reproduce from the table rows independently. The harness was not
taken on trust — which mattered, because the returning transcript again dropped characters (the P3
integrity rows for `3247` and `3305` arrived mangled and `3257`'s hash truncated). Standing lesson:
**where a transcript is the channel, arithmetic that can be re-derived from short quoted rows is a
better instrument than a hash table that only the sender can check.**

**2. FOUR-WAY DISCRIMINATION, not the two-way the check was designed for.** `stampEnv` called at
2026-08-19 23:21 with each port's own `PORTS` coordinates returns **1.95 / 1.35 / 1.16 / 1.30**
(Burnett Heads / Brisbane Bar / Mooloolaba / Noosa Head). The recorded 1.35 is unique. Nearest
competitor is Noosa Head at 1.30 — **0.05 m = 5× the 2 dp persisted resolution**; the attested map
centre, Mooloolaba, is **0.19 m = 19×**. The separation was computed and declared before the match
was interpreted, per the v16.72.2 §2 precision rule, and the matrix is non-degenerate.

**3. THE STRONGEST LIMB WAS UNPLANNED — the stub became the control.** The harness runs under Node
with `globalThis.map` stubbed to `{getCenter(){return{lat:0,lng:0}}}`. Had either resolution taken
the `map.getCenter()` arm, all twelve cells would have returned **Burnett Heads** — nearest of the
four to the equator. All twelve returned the forced port, and `ht` varied across all four. **Both
resolutions demonstrably follow `ll`, by execution rather than by reading the source.** Standing
lesson, promoted: **a harness stub chosen to be IMPLAUSIBLE rather than neutral converts itself
into a control limb for free.** A stub at Redcliffe would have proven nothing.

**4. §7 DOES NOT INHERIT §1's UNTESTABLE LINK.** v16.72.2 §1's map-centre claim rests on the
wind-check label read in the field, which no export records and none ever will. §7 does not depend
on it: `ht` and `port` are shown mutually consistent **regardless of where the map was**. Had the
centre been Redcliffe rather than Mooloolaba, the §7 conclusion is unchanged. **The residual closes
strictly harder than the gate it was residual to.**

**5. `Test02` IS NOT EVIDENCE FOR THIS — and the checks as written did not catch that.** At 22:53
Brisbane Bar and Noosa Head both return **1.26**, identical at 2 dp. The `Test02` record therefore
discriminates only against Burnett Heads (1.87) and Mooloolaba (1.12), never against Brisbane Bar.
**§7 closes on the 23:21 record alone** — precisely the record the housekeeping freeze protected.
Flagged by Claude Code unprompted; the dispatch's C2 limb would have been read as corroboration it
cannot supply.

> **CORRECTED 21 Aug 2026 — see v16.73 §7 and §8.** Two defects in §6 below. (i) The port is
> **Noosa Head** (2,649.71 km), not Burnett Heads (2,670.84 km) — Fiji is east, not north; the
> substance stands, only the name was wrong. (ii) "Build the guard after (c)" is under-specified:
> the cap must NOT go inside `nearestPort()` — two call sites swallow a null into `PORTS[0]` and
> would silently make it worse. Cap value decided: **200 km, at the persistence site** (v16.73 §9).

**6. NEW, OPEN — `nearestPort()` HAS NO MAXIMUM-DISTANCE GUARD.** `index.html:3310` is
`let best=PORTS[0],bd=Infinity` over four QLD ports: it always returns one, at any distance. A catch
logged in **Fiji (Sheraton Tokoriki, Oct–Nov 2026)** stamps `port:"Burnett Heads"` and interpolates
a Burnett-table height — persisted wrong data of exactly the class job (d) just fixed. `stampEnv`'s
guard omits tide only on non-finite coordinates, never on remoteness. **It creates a third state —
PRESENT BUT MEANINGLESS — that job (c)'s "absent means unknown" semantics do not cover, and
`env.wind.port` will inherit the same unbounded resolver.** Decision: **fix the cap value during
(c)'s Phase 1 characterisation so (c)'s documented semantics are right from the start; build the
guard after (c), as its own one-variable build with its own gate.** It does not ride with (c).
Field deadline is the Fiji trip.

**7. NEW — `env.tide` IS DEVICE-WALL-CLOCK FRAMED WHILE `env.moon` IS HARD-AEST.** The tide path
never forms an instant: `parseHM` (`index.html:3332`) returns a bare float, table times become
`off*24+HH+MM/60` (`index.html:3355`), and nothing in the code asserts or converts a zone — while
`index.html:3623` calls `moonIllum(aestDate(...))` with a hardcoded −10 h (`index.html:3330`). **Two
frames on one record.** Correct on a Brisbane-set phone and only on a Brisbane-set phone; on a
Fiji-set phone (UTC+12) the tide stamp shifts two hours and the moon stamp does not. Compounds with
§6 on the same trip. Documented, not scheduled. Related, same read: `new Date(base)` +
`setDate(base.getDate()+off)` (`index.html:3354`) is a local-calendar day step — safe in QLD (no
DST), not safe in a DST locale, where the ±1-day neighbours shift an hour against the `off*24`
constant.

**8. HOUSEKEEPING UNFROZEN.** Test spots `Test` (`s1787143687537239`) and `Test02`
(`s1787143995330639`) and their five catches may now be deleted. The evidence is already durable
off-device in `woongarra-backup-2026-08-19.json` (21,811,399 bytes), which carries all five `env`
blocks including the 23:21 invariant record and the 2025-09-23 guard record. **File that export
permanently as the §7/§4 evidence artefact — do not overwrite it, do not let a routine export cycle
consume the filename.** Take a fresh `version:2` export after the deletion as the working backup,
and force-close/reopen before trusting it (iOS async flush).

**9. STILL QUEUED — unchanged.** v16.71.1 §5 overlay clip (carried, promoted, still unfolded; it did
not ride with v16.72 and does not ride with job (c)). `storage_check.html` tooling pass: single
sized probe, not the KiB-granular binary search; `navigator.storage.estimate()` reports the
StorageManager origin quota and does not bound localStorage. MN v3 (#15): 3a OSM-only fetch → 3b
clip and **measure**, import nothing → sized probe → decide. SC `okHAT` boundary inclusivity (464
rows at exactly −2.24 m + 51 at −2.81 m = 515). `FLATS_BOUNDS` quoted to 3 dp against a method with
±1–2 mm jitter.

**NEXT SESSION.** Build **2026.08.16a**, roadmap **v16.72.3**, repo head `bbc5e22` plus this entry's
own commit. `CLAUDE.md` unchanged — no re-upload needed. **The §7 residual is CLOSED (§1). Next job:
(c) `env.wind.port` + TTL at `index.html:1797`, mirroring (d) exactly** — a string sibling of `dir`
and `kn`, absent means unknown, no back-fill, Phase 1 read-only characterisation before any patch,
and its own on-phone gate designed against v16.72.2 §5, §6 and §8. **Phase 1 must also settle the
`nearestPort()` distance cap value (§6)**, though the guard itself is a later build. Then (a)
recompute on PANEL OPEN; then (b) "Here" replaces "Coast-wide". **Do not re-litigate:** recompute is
on PANEL OPEN, not `moveend` (v16.72.1 §1); the C3 arc is closed (v16.70.1); the 600×600 grid cap
stays; "Coast-wide pins the anchor" is false (v16.71.1 §6); `env.tide.port` is never back-filled
(v16.72.2 §3); and `ht`/`port` provenance is settled — do not re-open §7.

---

*v16.72.2 · 19 Aug 2026 — **THE v16.72 ON-PHONE GATE PASSED.** No build, no code, no data, no
schema change. Build stays **2026.08.16a**; repo head `02091fe` plus the v16.72.1 entry's own
commit. The gate ran off-device against a `version:2` export, exactly as v16.72.1 §3 warned it would
have to. The result below was read out of the export file, not accepted from a report. Three
structural findings, one open residual, and three defects in the gate protocol itself.*

**1. GATE RESULT — PASS, verified from the file.** Export `woongarra-backup-2026-08-19.json`,
21,811,399 bytes, `"version":2`, `"exported":"2026-08-19T13:22:18.904Z"`, 22 spots, 134,372 imported
depth points, **5 catch records**. Every `env` in the file, unedited:

- `Nudibranch Tip` (−24.84089) · 2023-12-27 08:27 — `env` is `null`.
- `Test` (−27.23753) · 2025-09-23 13:26 — `moon` + `wind` present, **no `tide` key**.
- `Test` (−27.23753) · 2026-08-19 23:04 — `tide: {ht:1.29, port:"Brisbane Bar", state:"rising"}`.
- `Test` (−27.23753) · 2026-08-19 23:21 — `tide: {ht:1.35, port:"Brisbane Bar", state:"rising"}`.
- `Test02` (−26.38157) · 2026-08-19 22:53 — `tide: {ht:1.26, port:"Noosa Head", state:"rising"}`.

**Both limbs of the crossed test are satisfied.** The 23:21 catch sits at a −27.238 spot and records
`"Brisbane Bar"` while the map centre was at Mooloolaba — **excludes map-centre resolution**.
`Test02` at −26.382 records `"Noosa Head"` — **excludes a hardcoded or stuck result**, which the
protocol as originally written could not have detected (§8). The field is written, it carries the
spot's own port, and it varies with the spot. **The v16.72 invariant holds in the field: `stampEnv`
resolves from the catch's own coordinates, never the map centre.**

**THE ONE UNTESTABLE LINK, recorded rather than glossed.** Nothing in the export records where the
map was. That the 23:21 stamp occurred with the centre at Mooloolaba rests on the wind-check label
read before and after logging, reported as confirmed. The file cannot corroborate it, and no export
ever will. Any future gate on a centre-versus-spot question inherits this: the centre is
screenshot evidence, never file evidence.

**2. THE GUARD IS DEMONSTRATED — on a path no test was designed for.** The 2025-09-23 catch was
stamped by v16.72 code at a spot with perfectly good coordinates, but its date falls outside the
loaded tables. `tideTable()` returned null, no sampler was built, and the record carries `moon` and
`wind` with **no `tide` key and no fallback value of any kind**. That is the v16.72 §4 guard
behaving correctly — omission rather than a wrong number — on an out-of-range *date* rather than
the bad-*coordinate* path it was written for. Two failure routes, one correct outcome. This record
was originally logged in error (a photo-EXIF date), which is how a path nobody scoped got covered.

**3. NO BACK-FILL — confirmed positively, not on trust.** The one legacy catch predating v16.72
carries `env: null` outright. It has not acquired a `port`, or an `env`. v16.72 shipped with no
migration and the absent-means-unknown rule held across a real export/reopen cycle. The standing
instruction stands: **do not back-fill `env.tide.port`.**

**4. JOB (c)'s DEFECT IS VISIBLE IN THE FIELD DATA.** Every `env.wind` in the export is exactly
`{dir, kn}` — no port, no timestamp, no TTL. v16.72.1 §4 promoted job (c) on a code reading; this
is the same conclusion from persisted records. The promotion is now evidence-backed.

**5. STRUCTURAL — OPENING A SPOT FROM THE SPOT MENU RE-CENTRES THE MAP ONTO IT.** Confirmed on
device: tapping a spot in the list pans the map to that spot before anything else happens. There is
**no route to an off-screen spot that leaves the viewport where it was**, and a spot created from
the map lands at the map centre by construction. Two consequences, both durable: (a) a freshly
created spot can never serve as a centre-versus-spot discriminator; (b) any future gate needing
spot ≠ centre must tap the pin **directly on the map**, at a zoom that holds both the pin and the
intended centre. Three catches were burnt as null tests before this was understood.

**6. STRUCTURAL — THE WIND-CHECK PORT LABEL IS TRANSIENT, AND IT IS VALID.** The label at
`index.html:1853` (`Checking live wind at <port>…`) appears only during the fetch and is replaced by
a result that names no port. It is the **only** user-visible readout of `curPort()`, and capturing
it requires screenshotting mid-fetch. Fragile, and worth knowing before designing a gate around it.
It was verified to track the live map centre this session: Noosa centre → `Noosa Head`, Redcliffe
centre → `Brisbane Bar`. v16.72.1 §2's choice of observable therefore holds. Had it turned out to
be cached or anchored, every "confirm the resolution with the wind-check button" step in the
protocol would have been unfounded — that was the worse branch and it is excluded.

> **CLOSED 21 Aug 2026 — see v16.72.3 §1: PASS.** The residual below is retired: `ht` and `port`
> came from the same table, verified by execution and reproduced by hand. The proposed close has
> been executed. Do not re-run it.

**7. RESIDUAL, OPEN — THE HEIGHT'S PROVENANCE IS NOT VERIFIED.** v16.72.1 §5 records that
`curPort(ll)` resolves **twice per stamp**: once directly for the recorded `port` string
(`index.html:3622`), once transitively via `dayTideSampler`→`tideTable()` for the height. **The gate
verified the string. It did not verify that `ht` came from that same port's table.** The numbers
cannot settle it either — 1.26 → 1.29 → 1.35 across 22:53 → 23:04 → 23:21 is +0.03 m over 11 min
(0.0027 m/min) then +0.06 m over 17 min (0.0035 m/min), a smooth rising curve running straight
through a Noosa Head → Brisbane Bar change. Plausible for two SEQ ports at a similar phase, but it
means **the §3 "secondary numeric check" discriminated nothing at 2 dp**; the categorical port
string carried this gate alone, exactly as the §2 precision rule predicted it would have to.
**Proposed close — read-only, off-phone, Sonnet, one file, no edits:** read the Brisbane Bar and
Mooloolaba tables from `index.html`, interpolate both at 2026-08-19 23:21, and check 1.35 against
each. Matching Brisbane Bar and not Mooloolaba retires the residual. Not a build; may run before or
after job (c).

**8. THREE DEFECTS IN v16.72.1 §3's OWN GATE PROTOCOL — recorded because protocols get reused.**
- **Every expected-PASS value was the same string.** §3 asked for `"Brisbane Bar"` from catch 1 and
  the identical port from catch 2. That set excludes centre-resolution but **passes cleanly on a
  hardcoded or stuck resolution**. The fix was one extra catch in the mirror direction, expected to
  read a *different* port. A gate whose every passing observable is one value is not a gate.
- **Nothing confirmed the centre at the instant of the stamp.** §3 checked the wind label before
  logging and never after. Given §5, that gap is not hypothetical — it is exactly the failure that
  voided three catches. Re-read the observable *after* the action, not only before.
- **§3 step 6 mis-specified its own expectation.** It treated "arrived via `importBackup`" as a
  proxy for non-finite coordinates. It is not: most imported spots carry good coordinates and
  produce an entirely normal record. The step was dropped. Coordinate finiteness is checked in the
  export, not predicted from a spot's provenance.

*Standing lesson, and the third arc running on the same root: v16.71's entry carried 505-for-464,
v16.72's carried a retracted design, and v16.72.1's carried a gate that could pass on a stuck
value. Self-written planning output gets the same verbatim red-team as Claude Code output — and
that now demonstrably extends to **test protocols**, not just entries and code.*

**9. STILL QUEUED — unchanged.** v16.71.1 §5 overlay clip (carried, promoted, still unfolded; it did
not ride with v16.72 and does not ride with job (c)). `storage_check.html` tooling pass: single
sized probe, not the KiB-granular binary search; `navigator.storage.estimate()` reports the
StorageManager origin quota and does not bound localStorage. MN v3 (#15): 3a OSM-only fetch → 3b
clip and **measure**, import nothing → sized probe → decide. SC `okHAT` boundary inclusivity (464
rows at exactly −2.24 m + 51 at −2.81 m = 515). `FLATS_BOUNDS` quoted to 3 dp against a method with
±1–2 mm jitter.

**HOUSEKEEPING.** The three test spots and five test catches (`Test` `s1787143687537239`, `Test02`
`s1787143995330639`) remain on the device. Delete after the §7 residual closes — not before, since
the 23:21 record is the only field evidence of the invariant, and the 2025-09-23 record is the only
field evidence of the guard. Export first.

**NEXT SESSION.** Build **2026.08.16a**, roadmap **v16.72.2**, repo head `02091fe` plus the v16.72.1
and this entry's commits. `CLAUDE.md` unchanged — no re-upload needed. **The v16.72 gate is CLOSED
(§1). Next job: (c) `env.wind.port` + TTL at `index.html:1797`, mirroring (d) exactly** — a string
sibling of `dir` and `kn`, absent means unknown, no back-fill, Phase 1 read-only characterisation
before any patch, and its own on-phone gate designed against §5, §6 and §8 above. Then (a) recompute
on PANEL OPEN; then (b) "Here" replaces "Coast-wide". **Do not re-litigate:** recompute is on PANEL
OPEN, not `moveend` (v16.72.1 §1); the C3 arc is closed (v16.70.1); the 600×600 grid cap stays;
"Coast-wide pins the anchor" is false (v16.71.1 §6); `env.tide.port` is never back-filled (§3).

---

*v16.72.1 · 19 Aug 2026 — planning only, no build, no code. Build stays **2026.08.16a**, repo head
`02091fe`. **The v16.72 code is accepted; the v16.72 ENTRY is not.** Three defects in the
self-written entry corrected, four claims tagged inline so a top-to-bottom reader cannot act on
them, and the next job re-sequenced: **the on-phone gate for v16.72 comes before any further
build.** Also corrects v16.71.1 §8. No code, no data, no schema change.*

**1. v16.72 REINSTATED A DECIDED DESIGN — `moveend` IS RETRACTED, AGAIN.** v16.72 §7 and its
NEXT-SESSION pending item (ii) both frame the missing best-bite recompute as an absent `moveend`
listener — item (ii) verbatim: "no `moveend` trigger exists, so a pan silently desynchronises the
panel from its port". **v16.71.1 §11 decided the opposite four days earlier: recompute on PANEL
OPEN, not `moveend`** — deliberately, because the panel is already a considered action, it sidesteps
the debounce question rather than inheriting it, and it avoids a network call per pan. As committed,
v16.72 hands the next chat an actionable instruction to build the thing that was decided against.
Both occurrences tagged inline. **The item is "no recompute on panel open", and it is job (a).**

*Standing lesson, now twice-proven (v16.71.1 §3 predicted it): a self-written roadmap entry is
Claude Code output like any other and gets the same verbatim red-team. v16.71 shipped un-reviewed
and carried 505-for-464 into the repo; v16.72 shipped un-reviewed and carried a retracted design
back into the repo. Two consecutive arcs, same root cause, different symptom.*

**2. v16.72 §6's "six hunks" COUNTS CHANGE SITES, NOT GIT HUNKS — UNMEASURED AS COMMITTED.** The
entry lists six change *sites* and labels the total "six hunks". Those are different quantities:
git merges hunks whose context windows overlap, and `:3349-3350` and `:3352` are two lines apart, so
at the default three lines of context they collapse into a single hunk spanning roughly
`:3346-3355`. On that reasoning the real count is **five**, not six. **Measured directly against the
commit: 5 hunks, measured 19 Aug.** Hunk count and location is a standing ship gate — a figure
that is inferred from a site list rather than measured will not reconcile against a real
`git diff` on the next verification pass, and reconciliation failures are how a good gate gets
quietly abandoned. §6 tagged inline.

**3. THE ON-PHONE GATE FOR v16.72 IS THE NEXT JOB — NOT JOB (c).** v16.72's NEXT-SESSION note
sequences job (c) directly after a **persisted-schema change** with no gate in between. The standing
rule is unambiguous: build it, confirm it on the phone, and only then start the next build. Pushing
to Pages is how the build reaches the phone; it is not the gate. Tagged inline.

**PROTOCOL.** (1) Force-close/reopen the home-screen app; confirm `2026.08.16a` in-panel. (2) Export
a `version:2` backup **before logging anything** — pre-change snapshot. (3) Centre the map on Noosa,
north of the ≈ −26.53 bisector, and confirm the resolution with the wind-check button label
(`Checking live wind at Noosa Head…`, `index.html:1853`) — the categorical observable v16.71.1 §2
identified after the 1-dp tide readout failed to discriminate. (4) Log a catch at a **Redcliffe**
spot, date and time inside the 2026–27 tables. (5) Log a second catch at the **same spot** with the
map re-centred on Redcliffe — the control. (6) If any spot arrived via `importBackup` rather than
the map, log a third catch there. (7) Force-close and reopen — iOS flushes localStorage
asynchronously and a same-session read-back proves nothing. (8) Export `version:2`, move it
off-device, inspect the new catches' `env`.

**PASS** = catch 1 reads `env.tide.port === "Brisbane Bar"`, and catch 2 reads the identical port
**and** `ht` (proving the resolution follows the spot rather than a hardcoded result). **FAIL,
parameter not threaded** = `"Noosa Head"`. **FAIL, guard misfired or field not written** = `port`
absent with `moon` present. Catch 3 with no `tide` key is **expected** if that spot's coordinates are
non-numeric, and confirms the §4 guard in the field. Secondary numeric check, now usable for the
first time: `env.tide.ht` persists at 2 dp (`Math.round(ht*100)/100`), finer than the 1-dp UI that
could not separate 1.279 from 1.139 at v16.71 — cross-check catch 1's height against the Noosa table
for the same instant; they must differ.

**CONSTRAINT, recorded because it shapes the gate:** display was deliberately untouched, so **there
is no in-app readout of `env.tide.port`**. This build cannot be gated on the phone alone; it
requires an export inspected off-device. That is a consequence of the one-variable rule, not an
oversight, but it must not be discovered halfway through a gate session.

**4. v16.71.1 §8 CORRECTED — `stampEnv` WAS NOT THE ONLY PERSISTED-DATA DEFECT.** §8 called it
"unlike everything else here… **persisted wrong data**, not a stale display". That is wrong.
`env.wind` at `index.html:1797` is the same class on the same record, written one line later:
`liveWindDir` persisted with no port provenance, no timestamp and no TTL. v16.72 correctly promoted
job (c) on exactly this basis — the promotion stands, the sequencing does not (see §3). **Sequence
after the gate passes: (c) `env.wind.port` + TTL, mirroring (d) exactly — a string sibling of `dir`
and `kn`, absent means unknown, no back-fill; then (a) recompute on PANEL OPEN; then (b) "Here"
replaces "Coast-wide".** v16.72 §4's nesting rationale already reserves the collision-free slot.

**5. ACCEPTED RISKS FROM v16.72 — logged, not rebuilt.**
- **`curPort(ll)` resolves twice per stamp** — once transitively via `dayTideSampler`→`tideTable`,
  once directly for `_p` at `:3622`. Deterministic and synchronous, so the two cannot diverge, and
  the unguarded `_p.name` is safe for the reason given (a sampler exists only if `tideTable(ll)` was
  non-null, which requires `curPort(ll)` non-null). But **the recorded port is resolved
  independently of the table that produced the height, rather than returned by it.** Correct today.
  Do not make `nearestPort` stateful or memoised without revisiting this coupling.
- **Catches at imported spots with non-numeric coordinates now silently get no tide fields.** The
  `Number.isFinite` guard is correct and load-bearing — `importBackup` (`:3116`) merges `d.spots` on
  an `s&&s.id` check with no coordinate validation, so string and non-finite coordinates are
  genuinely reachable. Omission is the right failure (no data beats wrong data, per the
  classifier-fault precedent), but there is **no user-facing signal**. Recorded so it is not later
  reported as a regression.

**6. STANDING RULES ADDED THIS ARC.**
- **A STOP condition is written against BEHAVIOUR, not signature or arity.** The Phase 1 dispatch
  said "stop if the fix requires changing `tideTable()`'s signature **or** behaviour at any call
  site other than `stampEnv`'s". The arity limb fired on a change with **zero** behavioural blast
  radius — an additive optional trailing parameter that collapses to the existing expression at all
  six untouched call sites — and would have parked a safe build. A stop condition that trips on a
  safe change costs as much as one that misses an unsafe change.
- **A single-line grep cannot establish the ABSENCE of a phrase in a hard-wrapped file.**
  `grep -i "not yet wired" CLAUDE.md` returned nothing this session while the phrase was present at
  lines 70–71, split across the wrap. Same class as the `Measure-Object -Line` rule. To prove a
  phrase absent, normalise the whitespace first or search a distinctive single word.

**7. SYNC VERIFIED — NO FORK.** The repo copy at `02091fe` was checked against the
project-knowledge copy at v16.71.1 before this entry was written: stripping the v16.72 entry
(lines 3–88) leaves a body **byte-identical** across 7,163 lines, `diff` empty. Repo = project
knowledge + the v16.72 entry, exactly as the one-direction rule requires. Base file for this entry:
589,795 bytes, 7,251 lines.

**8. STILL QUEUED — unchanged, restated so this entry is self-contained.** v16.71.1 §5 overlay clip
(carried, promoted, still unfolded — it does **not** ride with a persisted-schema build and did not
ride with v16.72). `storage_check.html` tooling pass: the correct gate is a **single sized probe**,
not the KiB-granular binary search; `navigator.storage.estimate()` reports the StorageManager origin
quota and does not bound localStorage. MN v3 (#15): 3a OSM-only fetch → 3b clip and **measure**,
import nothing → sized probe → decide. SC `okHAT` boundary inclusivity (464 rows at exactly −2.24 m
+ 51 at −2.81 m = 515). `FLATS_BOUNDS` quoted to 3 dp against a method with ±1–2 mm jitter.

**NEXT SESSION.** Build **2026.08.16a**, roadmap **v16.72.1**, repo head `02091fe` plus this entry's
own commit. `CLAUDE.md` unchanged this session — no re-upload needed. **Next job: the v16.72
ON-PHONE GATE (§3). It is not a build, and nothing may be dispatched before it passes.** After it:
job (c), then (a), then (b) — §4. **Do not re-litigate:** recompute is on PANEL OPEN, not `moveend`
(§1); the C3 arc is closed (v16.70.1); the 600×600 grid cap stays untouched; "Coast-wide pins the
anchor" is false (v16.71.1 §6). **Do NOT back-fill `env.tide.port` on legacy records** — absent
means unknown and must stay that way.

---

*v16.72 · 16 Aug 2026 — **STAMPENV NOW RESOLVES TIDE FROM THE CATCH'S SPOT, NOT THE MAP CENTRE.
Build 2026.08.16a.** Repo head `7def0f3` (the v16.71.1 entry) at session start. Best-bite job (d).
This build **changes the persisted catch record shape** — `env.tide` gains a `port` string. Phase 1
was a read-only characterisation; Phase 2 is this patch. One variable: an optional trailing `ll`
threaded down four functions.*

**1. THE DEFECT.** `stampEnv(dateStr,timeStr)` took no coordinate. It resolved its tide table
through `dayTideSampler` → `tideTable()` → `curPort()` → `nearestPort(map.getCenter())`. So a catch
logged at Bargara while the map happened to sit over Noosa was persisted with **Noosa Head's tide
height and state**, written to `localStorage` via `saveSpots()` (index.html:1800) with no marker
saying which table produced it. A plausible wrong number in a right-looking field, unrecoverable
after the fact. Wrong values, not missing ones — the reason this outranked the other best-bite items.

**2. PRE-FLIGHT, ALL FOUR CLEAR.** (P1) `dayTideSampler` **memoises nothing** — it rebuilds `evs`
and returns a fresh closure on every call, so a threaded coordinate cannot hit a cached wrong-port
sampler. The STOP condition did not fire. (P2) `stampEnv` has exactly three sites: declaration
`:1466`, assignment `:3620`, **one call `:1796`**. No catch-edit, import or re-stamp path calls it —
`importBackup` (`:3111`) merges whole spot objects and never re-stamps. The STOP condition did not
fire. (P3) `nearestPort(centre)` accepts **either** `[lat,lng]` (via `Array.isArray`) **or**
`{lat,lng}`; `null`/`undefined`/`{}` fall to `cl.lat==null` → `PORTS[0]`. Object shape chosen, to
match what `map.getCenter()` already hands it. (P4) **Spots CAN be created outside `openSpotSheet`**
— `importBackup` at `:3116` merges `d.spots` on an `s&&s.id` check alone, with **no lat/lng
validation**, and `loadSpots` (`:1414`) rehydrates whatever localStorage holds. Non-finite or
string coordinates are therefore reachable. **The guard in item 4 is load-bearing, not defensive
decoration.**

**3. WHAT SHIPPED — five lines, additive optional parameter, no existing site touched.**
`curPort(ll)` `:3349` → `nearestPort(ll||map.getCenter())`, both pre-existing fallback and `catch`
paths byte-unchanged. `tideTable(ll)` `:3350` → passes through. `dayTideSampler(ymd,ll)` `:3352` →
passes through, with the dual meaning commented in place: spot-scoped when `ll` is supplied,
map-centre when omitted. `stampEnv(dateStr,timeStr,ll)` `:3620-3622`. Caller `:1796` →
`stampEnv(o.date,o.time,{lat:s.lat,lng:s.lng})`; `s` was already in scope from `:1775` and its
coordinate already used two lines later at `:1800` for `zoneAt`. **The six call sites that pass
nothing — `:3351` `ANCHOR`, `:3366` `tideCurveSVG`, `:3396` `render`, `:3485` `scoreSpotsFor`,
`:3563` `planFor`, `:3599` analytics — are absent from the diff and keep map-centre behaviour.**

**4. PROVENANCE AND GUARD.** `env.tide.port` is a **string**, the resolved port's `name`, written
only when `env.tide` is written. Nested under `tide`, not top-level, because `moonIllum` (`:3325`)
takes no coordinate — the moon fields are location-independent and a top-level `port` would falsely
claim to scope them. Guard: `ll&&Number.isFinite(ll.lat)&&Number.isFinite(ll.lng)` — `Number.isFinite`,
not global `isFinite`, so string coordinates from a hand-edited backup are rejected rather than
coerced. On failure **no tide fields are written at all and there is no map-centre fallback**.
Omission reproduces the record shape of the pre-existing blank-date path (`:3621` → `:1798` deletes
an empty `env`), so **no new record shape is introduced by the failure case**.

**5. MIGRATION — none, deliberately.** Legacy catches carry `env.tide` with no `port`. **Absent
means UNKNOWN, never assume-correct.** No back-fill pass was written and none should be: the map
centre at the time those catches were logged is not recoverable, so any back-fill would be a guess
persisted as fact. Analytics (`:3599`) already falls back to re-deriving tide stage from date/time
for older entries and is unaffected — it reads `state`, never `port`.

**6. VERIFICATION — executed, not predicted.** `node --check` PASS on both extracted script blocks.
Inlined Leaflet block body-only SHA-256 `db49d009…5641a` — **unchanged**, 147,552 chars, confirmed
against the recorded baseline. `zoneAt()` (`:1325`, most-protective `ORDER` rank with the
`rank===0` early return) and the green-zone `dragend` safeguard (`:1576-1578`) absent from the diff
and re-read present in the file. All five edited lines re-read from disk and quoted — every one is a
long single line, and `node --check` would have passed a mangled property name, so `port:_p.name`,
`Number.isFinite`, and `{lat:s.lat,lng:s.lng}` were each eyeballed in the file rather than trusted
from the edit. Behavioural harness over the **real patched source lines** with the map parked on
Noosa throughout and four distinguishable stub tables: existing no-`ll` sites still resolve Noosa
(`ht 6.00`, `ANCHOR [-26.3833,153.0917]`); the four spot cases resolve **Burnett Heads / Brisbane
Bar / Mooloolaba / Noosa Head** correctly and independently of the map; all eight bad-coordinate
cases (omitted, null, NaN, Infinity, string, empty object, missing key) wrote **no tide fields**;
`typeof env.tide.port === 'string'`; `env.moon` keys remain `["name","illum"]` with no port.
`git diff --numstat` = `9 9 index.html` — six hunks
`[UNVERIFIED — see v16.72.1 §2: this counts change SITES, not git hunks]`: `:1052` and `:1091`
build string, `:1796`,
`:3349-3350`, `:3352`, `:3620-3622`. index.html 2,351,226 → 2,351,770 bytes (+544), line count
4,195 unchanged. Both `<style>` blocks absent from the diff.

**7. NOT DONE, ON PURPOSE.** Display is untouched — no popup, header or panel change; this is a
persisted-data build only. `env.wind` at `:1797` still stamps `liveWindDir` with no port provenance
and no staleness check: **that is job (c) and was not touched.** The three other best-bite defects
from the v16.71.1 spike remain open: missing recompute on `moveend`
`[CORRECTED — see v16.72.1 §1: the decision is PANEL OPEN, not `moveend`]`, the unscoped
coast-wide spot list, and stale `liveWindDir` persisting across regions for the whole session.

**NEXT SESSION.** Build **2026.08.16a**, head = this commit. Catches now record which tide table
produced their height. **Recommended next job: best-bite job (c) — `liveWindDir` staleness**
`[SUPERSEDED — see v16.72.1 §3: the ON-PHONE GATE for this build comes first]`, the
same class of defect as this one and the last unfixed source of wrong persisted data: `:1797` stamps
a wind reading that may have been fetched at a different port an unbounded time earlier, with no TTL
and no origin recorded. Pending cleanup, in priority order: (i) job (c) as above; (ii) the missing
best-bite recompute — no `moveend` trigger exists, so a pan silently desynchronises the panel from
its port `[CORRECTED — see v16.72.1 §1: recompute is on PANEL OPEN; `moveend` was decided
against]`; (iii) the unscoped spot list in `scoreSpotsFor` (`:3483`), which scores every saved spot
against a single port's astronomy. **Do NOT back-fill `env.tide.port` on legacy records** — absent
means unknown and must stay that way.

---

*v16.71.1 · 15 Aug 2026 — planning only, no build, no code. Build stays **2026.08.15a**, repo head
`ba17a68`. **THE v16.71 ON-PHONE GATE PASSED**, and a read-only spike into best-bite found that the
anchor was never the defect — **the recompute is.** Also corrects a transcription error committed
inside v16.71 §7. The next build is a best-bite scoping/staleness fix, not a tide job.*

**1. ON-PHONE GATE — PASS. `pool 64308`, THE PREDICTED DIRECTION.** Noosa centre, build string
confirmed live as `2026.08.15A` on the home-screen container. `pool 64308` read **identically at
z11.0 and z12.0**, against the pre-build Redcliffe z11 baseline of **64306** (v16.70 §6) — **+2, a
rise.** v16.71 predicted the change could only rise or hold, because 2.37 m is strictly looser than
2.24 m and no point can be removed by a looser gate. It rose. **+2 is the expected magnitude, not a
disappointment:** Maroochy/Noosa is genuine bathymetry, so almost nothing sits in the 13 cm band
between −2.24 and −2.37, and the SC contribution was 7 rows pre-thin. **Identical at two zooms
establishes that `pool` is store-wide, not viewport-scoped** — a fact not previously recorded, and
one that makes any single-centre `pool` reading valid for the whole store. Left open: a Redcliffe
z11 reading on this build. If it also reads 64308, +2 is the entire effect and the gate closes.

**2. THE TIDE READOUT DID NOT DISCRIMINATE, AND THE SCREENSHOTS COULD NOT CLOSE THAT.** The Noosa
tap showed `tide +1.2`. The off-phone probe (v16.71 §5) gave Noosa 1.2793 m and Mooloolaba 1.1391 m
at the same instant; at the one decimal place the UI renders, those round to 1.3 and 1.1, and the
displayed **1.2 sits between them**. It is consistent with the new port but proves nothing.
**Standing lesson: a gate observable must have more precision than the difference it is asked to
detect.** The discriminating observable was the wind-check button label (`Checking live wind at
Noosa Head…`, `index.html:1853`), which is unambiguous and was not captured. Use it next time.

**3. CORRECTION TO v16.71 §7 — THE FIGURE IS 464, NOT 505.** As committed, §7 reads "505 rows at
exactly −2.24 m and 51 at exactly −2.81 m" for a stated total of 515. **505 + 51 = 556.** The
correct figure is **464**: 464 + 51 = 515 ✓, and 7 of those 464 clearing the looser 2.37 m threshold
is exactly the measured 515 → 508 drop. 464 was the figure derived in the preceding session; 505 was
a transcription error in the closing summary that propagated into the committed entry. **The rest of
§7 stands.** *Standing lesson: a self-written roadmap entry is Claude Code output like any other and
gets the same verbatim red-team. This one shipped un-reviewed and carried a wrong number into a
pending-cleanup item, where it would have been trusted rather than re-derived.*

**4. NOOSA IS THE SLOWEST CENTRE YET RECORDED — AND IT STRENGTHENS v16.70.1.** On-phone, build
2026.08.15a: **z11 comp 174.5 med / 236.0 max; z12 comp 239.5 med / 311.0 max** (z12 total 596.5 /
666.0, S3 81.5 / 153.0). Against Redcliffe's 156.5 / 200.0 (v16.70 §6). **This does not reopen the
350 ms debounce — it closes it harder.** v16.68.1 §H's eligibility condition (compute under ~200 ms)
failed at Redcliffe by 0 ms on the max; at Noosa z12 it fails by **111 ms, 55% over**, at a real
fishing centre. v16.70.1's DECIDED-NO stands on stronger evidence than when it was written. `T1-T0`
held at 351.5–353.5 med, confirming the debounce constant is invariant across centres.

**5. §9b IS NO LONGER COSMETIC — IT ATE A DIAGNOSTIC UNDER REAL USE.** The v16.63 scale box clipped
`six H⋯` in both overlay screenshots at Noosa. `pool` survived; the cache-state indicator did not.
v16.70 §9b was rated "not worth a build alone" on the assumption nothing depended on reading that
line. **The on-phone gate depended on reading that line.** Promote it from cosmetic to a real
carried defect and fold it into the next build. Workarounds that worked in the field: landscape
rotation, and stepping one zoom level (the Leaflet scale bar changes width with zoom, moving the
overlap).

**6. BEST-BITE SPIKE — THE PREMISE WAS WRONG. `ANCHOR()` ALREADY FOLLOWS THE MAP CENTRE.** The
planning chat's diagnosis — that "Coast-wide" pins the anchor to Woongarra — is **FALSE and is
retracted.** Executed, not read (`index.html:3349-3351`):
`ANCHOR()` → `curPort()` → `nearestPort(map.getCenter())`, returning the nearest `PORTS[]` entry's
coordinate. At the app's init centre it is **Brisbane Bar**, not Woongarra. `PORTS[0]` (Burnett
Heads) is reached only on the `cl.lat==null` path or the `catch`; it is the **fallback, not the
default**. The `[-27.3667,153.1667]` literal at the tail of `:3351` is Brisbane Bar and is
unreachable while `PORTS` exists. **There is no hardcoded Woongarra coordinate in this path.**
"Coast-wide" is `<option value="">` (`:1061`, re-emitted `:3435`) whose only consumer is `:3397`
(`const sp=$('bb-spot').value?…:null;`) — the tide-preference note. **It never reaches the anchor.**

**7. WHAT THE DEFECT ACTUALLY IS — THREE SEPARATE THINGS, NONE OF THEM THE ANCHOR.**
- **(a) NOTHING RECOMPUTES ON PAN.** `render()` fires on page load (`:3626`), date change (`:3440`),
  spot-selector change (`:3441`) and `shiftDay()` (`:3444`). **There is no `moveend` listener in the
  best-bite IIFE** — the file's only `moveend` is the depth-shade debounce at `:3693`. So panning
  silently changes what `ANCHOR()`/`curPort()` *would* return while the displayed astronomy, tide
  table, port name (`:3428`) and rankings **stay at the old port** until the user next touches a
  control. This is the real bug and it is invisible.
- **(b) THE SPOT LIST IS UNSCOPED BY DESIGN.** `scoreSpotsFor()` (`:3483`) takes the whole store with
  no geographic predicate. `rankSpots()` filters by species (default: empty set, no filter), then by
  `recBandKm` — **default 0 = no distance cap** (`:3449`, `data-km="0"` on `rng-on` at `:1072`) —
  then `.slice(0,5)`. So Woongarra spots ranked at a Noosa map centre is **correct behaviour for the
  default**, not a fault. It is also useless. Scope origin is `recOrigin()` (`:3450-3451`) = **raw
  map centre**, a *different* variable from the anchor's snapped port coordinate; the two always
  diverge by the centre-to-port offset, and diverge in kind when one-shot GPS origin is on.
- **(c) THE HEADER IS A FIXED STRING AND CONTRADICTS BOTH.** `index.html:1052` hardcodes
  `<h1>Woongarra Coast</h1>` / `Great Sandy MP`. **Nothing writes to it** — the only code touching
  `#phead` is the collapse toggle (`:1320`) and a read-only build-string scrape (`:2263`). At the
  app's own default centre it is already wrong, sitting above a Brisbane Bar resolution.

**8. TWO DEFECTS THE SPIKE FOUND THAT NOBODY ASKED ABOUT — BOTH WORSE THAN THE HEADER.**
- **`liveWindDir` NEVER EXPIRES.** Declared `:1417`, written at exactly one site (`:1856`, the
  `#sp-wind` handler). **No TTL, no timestamp, no staleness check, no in-flight dedupe.** It is set
  once per button press and persists for the whole page session at whatever port it was fetched for.
  Pan Bargara → Noosa and every subsequent `scoreSpotsFor()` still scores against **Bargara's wind**,
  with no indication it is stale or from the wrong region — feeding pin recolouring (`:1493`), spot
  popups (`:1503-1505`), the list warning badge (`:1584`), the score term (`:3498`) and the catch env
  stamp (`:1797`). `buildPlan()` (`:3577`) fetches fresh per press and never writes to it.
- **`stampEnv` PERSISTS A MAP-CENTRE-DERIVED TIDE ONTO A CATCH RECORD.** `:3620-3622` writes tide
  state and height onto every newly logged catch via `tideTable()` → `nearestPort(map.getCenter())`.
  **The catch's own coordinates are not used.** Log a Bargara catch while the map sits at Noosa and
  the record permanently carries Noosa's tide. Unlike everything else here this is **persisted wrong
  data, not a stale display**, and it is silently wrong in the logbook forever.

**9. THE IIFE BOUNDARY IS INTACT AND IS NOT AN OBSTACLE.** IIFE opens `:3313`, closes `:3627`;
nothing on `window`; exactly two outward hooks (`window.bbRefreshSpots=populate` `:3438`, and
`stampEnv=function…` `:3620` assigned to the outer `let` at `:1466`). **Inward needs no hook at
all:** `const map` is declared at `:1228`, top-level in the same script block *before* `:3313`, so it
is already in the IIFE's lexical scope and is used inside three times (`:3349`, `:3451`, `:3510`).
**"Anchor on map centre" is a one-line edit inside `ANCHOR()`, and wiring a `moveend` recompute is
in-scope today** — no boundary crossing, contrary to the concern that prompted the question.

**10. THERE IS NO ACTIVE-REGION CONCEPT.** No `activeRegion` variable exists. `REGION_SOURCE` /
`REGION_MASK_EXEMPT` / `regionLabel()` / `#imp-region` are the depth-import **dataset tagging**
system and have no bearing on tides, astronomy or best-bite — do not conflate them. The de facto
region is `nearestPort(map.getCenter())`, **re-derived independently at three call sites** (`:3349`
`curPort()`, `:1853` `_wp`, `:3964` `curP()`), set by any `setView`/drag/pinch/zoom-to-spot
(`:1317`, `:1366`, `:1382`, `:1395`, `:1591`, `:1614`, `:3201`), with **no change event, no
invalidation, no re-render and no UI naming it.**

**11. DESIGN DECISION — "HERE" REPLACES "COAST-WIDE"; ANCHOR AND SCOPE COME APART.** Agreed in
planning: the selector currently does two jobs and they separate. **Anchor** = the coordinate feeding
astronomy/tide/wind. **Scope** = which spots appear. Default both to the live map centre, labelled
**"Here"** rather than "Coast-wide" (which reads as a region name once regions are real); an
explicitly picked spot overrides both. **Recompute on PANEL OPEN, not on `moveend`** — the panel is
already a deliberate action, it sidesteps the debounce question entirely rather than inheriting it,
and it avoids a network call per pan. Map centre is also the correct default on privacy grounds
(hard rule 6 already names it as the no-GPS path). NOT dispatched here.

**NEXT-SESSION NOTE:** build **2026.08.15a**, roadmap **v16.71.1**, repo head `ba17a68` plus this
entry's own commit. `CLAUDE.md`'s "not yet wired into the app" sentence corrected in the same commit
— it must land on **both** surfaces (repo + project knowledge) or it forks. **Next job: the
best-bite scoping/staleness build (§11), one variable at a time** — recommended order (a) recompute
on panel open, (b) "Here" default + scope, (c) `liveWindDir` TTL, (d) `stampEnv` to use the catch's
own coordinates. §8's two defects are the highest-severity items found this arc and (d) is the only
one that corrupts stored data. **Carried:** §5's overlay clip, now promoted. **Do not re-litigate:**
the C3 arc is closed (v16.70.1), and §6 retires the "Coast-wide pins the anchor" theory permanently.
**Still queued from v16.70.1:** the `storage_check.html` tooling pass — `navigator.storage.estimate()`
reports the StorageManager origin quota (39,321.6 MB observed) and **does not bound localStorage**
(observed usage 2.27 MB against a localStorage key-sum of ~4.9 MB — arithmetically impossible unless
excluded). The correct gate is a **single sized probe** at `(measured bytes + rollback snapshot +
10%)`, not the queued KiB-granular binary search, which would drive a container holding real data to
its ceiling. MN v3 sequencing is unchanged: 3a OSM-only fetch → 3b clip and **measure**, import
nothing → sized probe → decide.

*v16.71 — 15 Aug 2026 — **NOOSA HEAD WIRED AS THE FOURTH TIDE PORT. Build 2026.08.15a.**
Repo head `844c889` (the v16.70.1 entry) at session start. Closes the Noosa tide-port item that has
been carried as a fast-follow since v16.5. One build, three intended effects, all three measured
off-phone against the edited file rather than predicted.*

**1. WHAT SHIPPED.** `NOOSA_TIDES_2026` + `NOOSA_TIDES_2027` embedded in the v16.42
Brisbane/Mooloolaba shape exactly (two year consts, then
`Object.assign(NOOSA_TIDES_2026,NOOSA_TIDES_2027);/* one lookup spans 2026-2027 */`), 730 date keys
2026-01-01 → 2027-12-31, **0 overlapping keys between the two consts** so the merge overwrites
nothing. `PORTS[]` gains a fourth entry, **APPENDED not inserted** — `PORTS[0]` is still Burnett
Heads, which is what `nearestPort()` returns when `cl.lat==null`. `FLATS_BOUNDS` gains
`'Noosa Head':[0.917,1.373]`. `hat:2.37` = the two-year embedded max (2026 max 2.36, 2027 max 2.37).

**2. THE HAT SITS IN THE CONSERVATIVE DIRECTION, LIKE ALL THREE EXISTING PORTS.** Checked against
MSQ's **Semidiurnal Tidal Planes 2025**, tidal datum epoch 2010–2029 (newer than the 2020 edition
v16.44.1 used, and on the epoch that edition flagged as superseding it). Published Noosa Head
**HAT 2.35 m**; embedded max **2.37 m** → **+0.02 m above**. Full set on the 2025 edition:
Bundaberg (Burnett Heads) 3.68 vs 3.70 (+0.02), Brisbane Bar 2.78 vs 2.81 (+0.03), Mooloolaba 2.21
vs 2.24 (+0.03), Noosa Head 2.35 vs 2.37 (+0.02). **All four above published HAT, consistent to the
centimetre.** Note the 2025 edition moves the two figures v16.44.1 recorded off the 2020 edition
(Burnett 3.67→3.68, Brisbane Bar 2.73→2.78) — both still below the embedded values, so v16.44.1's
conclusion survives the epoch change. Noosa Head MSL is **1.15 m** on the same table.

**3. THE FLATS-BAND METHOD WAS RE-PROVEN FIRST, AND IT MISSES MOOLOOLABA BY 0.677 mm.** Before
computing anything for Noosa, v16.50's `FLATS_BOUNDS` derivation was re-run: `tideHeightNow()`
extracted VERBATIM and driven in a Node vm (never reimplemented — the whole validity of the method
rests on it not being a rival tide model), 1-minute steps, nulls dropped, 1/3 and 2/3 quantiles.
**The span is the 2026 calendar year, NOT the full 730-day table** — the 730-day span reproduces
none of the three. On the 2026 span: **Brisbane Bar [1.002, 1.653] EXACT, Burnett Heads
[1.407, 2.176] EXACT, Mooloolaba [0.774, 1.234] against the shipped [0.775, 1.234]** — raw
H1 = 0.774323, short by 0.000677 m. **This is not a quantile-definition artefact:** ten estimators
(floor/ceil/round/+1/n-1/n+1 index forms, R6 and R7 linear interpolation, and a 1 mm cumulative
histogram) all return 0.774, and the index ranges required to hit 0.775 and 1.234 simultaneously
have an empty intersection. **It is not input drift either:** `MOOLOOLABA_TIDES_2026`,
`BRISBANE_TIDES_2026`, `BURNETT_TIDES_2026`, `tideHeightNow()` and `FLATS_BOUNDS` are all
byte-identical between `9fe0a9d` (v16.50) and HEAD. The gap is inside v16.50's own arithmetic.

**4. THE REAL LESSON: THIS METHOD DOES NOT SUPPORT 3 dp.** A ±48 h phase scan of the 365-day window
moves every port by 1–2 mm (Brisbane 1.002–1.003 / 1.652–1.653; Mooloolaba 0.774–0.776; Burnett
1.406–1.409 / 2.175–2.177). **The shipped constants are quoted one to two digits finer than the
method's own jitter.** That is a standing property of all four entries now, not a Noosa defect.
Noosa's value is stable across every window tried (H1 0.917–0.922, H2 1.373–1.378), and the 2026-span
figure was taken because that is the span that reproduces two of three controls exactly.
**External cross-check:** computed midpoint (0.917+1.373)/2 = **1.145 m** vs MSQ's published
Noosa Head **MSL 1.15 m**. **The existing three values were deliberately NOT re-derived** — changing
them would move rendered output for Brisbane River and Sunshine Coast for no gain.

**5. OFF-PHONE VERIFICATION, RUN AGAINST THE EDITED FILE.** `nearestPort()`, `okHAT()`,
`flatsBand()`, `flatsColor()` and `FLATS_BOUNDS` extracted VERBATIM from the edited `index.html`
and driven in a Node vm. Over `data/sunshine_coast_flats_v1.csv` (57,565 rows):
**2,451 rows re-resolve Mooloolaba → Noosa Head** (the only transition that occurs), **55,114
unchanged**. Band histogram for the 2,451 re-banded rows, BEFORE (Mooloolaba bounds) → AFTER
(Noosa bounds): band 0 **1,624 → 1,358 (-266)**, band 1 **750 → 858 (+108)**, band 2
**77 → 235 (+158)**, band 3 **0 → 0**. The 55,114 unchanged rows are **BIT-IDENTICAL**
(39,952 / 12,105 / 3,057 / 0 before and after). Over `data/brisbane_river_flats_v1.csv` (68,591
rows): **0 rows resolve to Noosa Head**, histogram bit-identical. `okHAT` drops on the SC set fall
**515 → 508** — the 7 rows sitting exactly at −2.24 m inside the Noosa catchment now clear the
looser 2.37 m threshold. Probe resolutions at 2026-08-15 12:00 AEST: Bargara → Burnett Heads
(2.3343 m), Redcliffe → Brisbane Bar (2.0154 m), Maroochydore → Mooloolaba (1.1391 m),
Noosa → Noosa Head (1.2793 m). All four tables span 730 keys, 2026-01-01 → 2027-12-31.

**6. THE GEOMETRIC COUNT AND THE POST-DROP SURVIVOR COUNT ARE DIFFERENT NUMBERS — v16.50 CONFLATED
THEM AND SHIPPED THE WRONG ONE.** On the live `sunshine_coast_flats_v1.csv` the two coincide at
2,451 **only because that file was already HAT-filtered when it was generated** (deepest value
−2.81 m, every Noosa-catchment row shallower than −2.37 m). On the pre-drop source
`sunshine_coast_intertidal_ground_v2.csv` (168,461 rows) they diverge fourfold: **10,499 geometric,
2,632 post-drop survivors at hat=2.37**. **Never quote one as the other.** The Mooloolaba/Noosa
haversine bisector sits at **lat ≈ −26.53** (−26.5375 at lng 153.040 to −26.5272 at lng 153.195),
well inside the SC dataset's latitude range of −27.0773 … −26.3643 — which reaches 2.11 km NORTH of
Noosa Head itself, so this is a genuine split and not an edge artefact. It also agrees with the
−26.533° bucket boundary already recorded for the AHD→LAT conversion.

**7. PRE-EXISTING, NOT INTRODUCED HERE: 515 ROWS IN THE LIVE SC SET FAIL TODAY'S `okHAT`.**
`sunshine_coast_flats_v1.csv` contains 464 rows at exactly −2.24 m and 51 at exactly −2.81 m. The
CSV generator kept `depth == -hat`; `okHAT` uses strict `d > -hat` and drops it. A boundary-
inclusivity mismatch between the generator and the app, pre-dating this build (it is why the drop
count is 515 before and 508 after, not 0). **Not fixed here — out of scope for this build.**
Worth a decision next time the SC set is regenerated: align the generator to strict `>`, or leave it.

**8. GATES.** `node --check` exit 0 on both script blocks. Leaflet inner-content SHA-256
`db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`, 147,552 bytes, 0 CRLF —
unchanged. `zoneAt()`, `ORDER`, the green-zone `dragend` safeguard, `spotsUnlocked` and both
`<style>` blocks absent from the diff and present in the file. `git diff --numstat` = `38 4
index.html` — four hunks, nothing else touched. index.html 2,284,040 → 2,351,226 bytes (+67,186,
+65.6 KB). CLAUDE.md NOT edited — its "not yet wired into the app" sentence (lines 72–74) is now
stale, and **Aaron must apply that correction to BOTH the repo copy and project knowledge**;
editing the repo copy alone forks them.

**NEXT SESSION.** Build **2026.08.15a**, head = this commit. Noosa Head is live as
`PORTS[3]`/`FLATS_BOUNDS['Noosa Head']`. **Recommended next job: the on-phone acceptance tap at
Noosa** — confirm a Noosa-area tap reads the Noosa Head table and that flats shading in the
Noosa catchment shifts as item 5 predicts (band 0 down 266, band 2 up 158 on the SC set). Pending
cleanup, in priority order: (i) the CLAUDE.md sentence at lines 72–74 on both surfaces;
(ii) the 515-row `okHAT` boundary mismatch in item 7; (iii) the 3-dp-vs-1-mm-jitter question in
item 4 — decide whether `FLATS_BOUNDS` should be quoted to 2 dp, which would be a rendering change
and needs its own build. **Do NOT re-derive the existing three `FLATS_BOUNDS` entries to close the
Mooloolaba 0.677 mm gap** — it is understood, recorded, and not worth moving shipped output for.

---


*v16.70.1 · 14 Aug 2026 — planning only, no build, no code. Build stays **2026.08.14a**. Repo head
`851a51c` (the v16.70 entry) at session start. **THE 350 ms `moveend` DEBOUNCE IS RATED AND CLOSED
AS A DECIDED NON-CHANGE.** It has been carried as "deferred, then eligible, then rate it" since
v16.68.1 §H across five entries. This entry ends that. It is NOT deferred, NOT parked and NOT
awaiting a number — it is decided, with one narrow reopening condition in §6. The C3 optimisation
arc closes with it.*

**1. THE ELIGIBILITY TEST WAS RUN ON THE WRONG STATISTIC AT EVERY STEP, AND ON THE RIGHT ONE IT
FAILS.** v16.68.1 §H's condition — compute under ~200 ms — exists to bound HOW LONG THE MAIN THREAD
IS BLOCKED when a rebuild collides with a gesture. That is a worst-case property. It has been
evaluated against the MEDIAN every time: v16.69.2 §8 ("118.0 / 123.0 / 129.5 … with margin"), and
v16.70 §9a, which surfaced the thinner margin and then still concluded "still eligible" off 156.5.
**Redcliffe's compute MAX is 200.0** (v16.70 §6). The condition reads "under ~200 ms." 200.0 is not
under 200. The median understates by 43.5 ms here, and the 11 Aug arm-B maxes that banked the
original "with margin" claim were never recorded at all. **On its own condition, applied to the
statistic the condition is about, the debounce is NOT eligible. §9a's "still eligible" is
SUPERSEDED.**

**2. THE BLOCKING OBJECTION IS ARCHITECTURALLY UNFIXABLE — SO IT CAN NEVER GRADUATE.** "No in-flight
guard exists to absorb the extra overlap" has been carried since v16.68.1 §H as though it were a
precondition a later build could satisfy. It is not. `buildShade()` is synchronous end to end,
S1–S5 including the `cv.toDataURL()` encode (v16.65 §2). **Synchronous work cannot be guarded** —
once the timer callback enters, no touch event is serviced until it returns; there is nothing to
cancel and nothing to interrupt. The debounce reset IS the guard, and it covers only the
pending-but-not-started case. The started-and-running case would require slicing the pixel loop
across rAF with abort checks — a rewrite an order of magnitude larger than C3b, which is already
parked. **An item gated on a condition that no small build can ever meet is not deferred, it is
refused. Say so once and stop re-listing it.**

**3. THE COLLISION WINDOW DOES NOT WIDEN — IT RELOCATES. THE REBUILD COUNT IS THE REAL COST.**
"Cutting it moves jank closer to the finger" is directionally right and mechanically vague, and the
vagueness has let it be re-argued three times. Precisely: the window in which a new gesture lands on
a RUNNING rebuild is `compute` ms wide and starts `D` ms after the previous `moveend`. **Width is
independent of D.** At D=350 the window is gaps ∈ [350, 506.5]; at D=150 it is [150, 306.5] — the
same 156.5 ms width, relocated. **The current setting is not collision-free either**, which no
earlier entry states.

The real cost of shortening is second-order: **coalescing collapses.** A five-gesture exploration
burst at 250 ms spacing is **one** rebuild at D=350 and **five** at D=150, four of them landing
mid-burst. That is a 5× increase in main-thread blocking, concentrated on the pattern that dominates
real use of this app — panning a stretch of coast hunting structure — while the benefit lands on the
single-settled-pan case, which is rarer.

**4. IT REMOVES NO WORK, AND THE VISIBLE DEFECT IT WOULD FIX IS SMALLER THAN THE TOTALS COLUMN
IMPLIES.** Reconciling v16.70 §6's Redcliffe reading against v16.66 §4 (`T1-T0` 351.0–353.5 median,
`T3-T2` 2.0–13.5 median): 351 + 156.5 + ~2.5 = **510.0**. **The debounce is 68.8% of user-visible
latency and 0% of the work.**

```
D=350 (current)   total 510   —              work removed 0
D=200             total ~359  −151  (−30%)   work removed 0
D=150             total ~309  −201  (−39%)   work removed 0
```

A −39% headline with zero milliseconds of compute removed is exactly the shape v16.66 §8 was written
about. The counter — "perceived latency IS the metric, so it is not gaming" — has force only if the
perceived cost is real, and here it largely is not: **the previous overlay is geo-anchored and stays
on screen for the whole 510 ms.** The visible defect is a newly-revealed viewport edge unshaded for
about half a second, not a blank map. Not worth a 5× rebuild-count increase.

**5. THE DEBOUNCE WAS NEVER A PERFORMANCE ITEM — THAT IS THE ROOT ERROR.** It is a UX tuning
constant that got recruited into an optimisation arc and then rated in that arc's currency (compute
medians against a threshold). **General lesson: rating a latency-tuning constant against a
work-reduction metric is a category error, and it produced four entries of "eligible but untouched"
without ever asking what the constant is for.** The honest successor to the complaint the debounce
appeared to answer is a **coarse-then-refine pass** (render ~150² immediately, refine to 600²) —
which changes output pixels transiently, needs its own bit-exact story, and is a real build. It is
NOT dispatched here and is recorded only so the next session does not reach for the debounce again.

**6. REOPENING CONDITION — ONE, AND IT IS NOT CHEAP.** Reopen only if an on-phone instrumentation
pass records the **distribution of inter-`moveend` gaps in real field use** and shows the mass above
~500 ms, i.e. that bursts are rarer than §3 assumes. That measurement does not exist, costs an
instrumentation build plus an on-phone run, and would be spent on a change that removes no work.
**Do not reopen on a subjective "feels slow" report** — route that to §5's coarse-then-refine
instead.

**NEXT-SESSION NOTE:** build **2026.08.14a**, roadmap **v16.70.1**, repo head `851a51c` plus this
entry's own commit. No code shipped this session. **The C3 arc is CLOSED: C3a shipped and gated
(v16.70), C3b PARKED (v16.69.2 §9), the 350 ms debounce DECIDED-NO (this entry).** The 600×600 grid
cap stays UNTOUCHED — it changes output pixels. Do not dispatch the bare `_idwCache` `poolVersion`
re-key (v16.68.3 §2 — a no-op while `buildShade()` nulls the cache on its first line). **The only
carried code item is v16.70 §9b** — the v16.63 scale box now clips `pool 64306 z11.0 six HIT idw
MISS`, which carries both cache-state indicators; fold into the next build that does not depend on
reading the overlay, still not worth a build alone. **Next job: region work — MN v3 Noosa-OSM fetch
and Noosa tide-port wiring (#15).** Noosa Head is a Standard Port (MSQ 2024 Semidiurnal Tidal
Planes), own harmonic prediction, no offset math, not yet wired.

*v16.70 · 14 Aug 2026 — **C3a DEAD-ARM CLEANUP SHIPPED AND ON-PHONE GATED. The numeric bucket key is
now the sole path and the measured saving is in normal use for the first time.** Build
**2026.08.14a**, repo head `851a51c`. Repo head before this build was `69bfc56` (the v16.69.2
entry). The `'str'` arm, `sIdxMode`, `#six-mode-toggle`, `_pf.sixMode` and the `key <mode>` footer
row are all deleted. **C3a is CLOSED.***

**1. WHY THIS COMMIT WAS NOT HYGIENE.** `let sIdxMode='str'` was a plain global with no persistence
— it reset to `'str'` on every launch, so the STRING key was the shipped default and every pan
between 11 and 14 Aug paid the full arm-A cost. v16.69.2's measurement proved the saving; this
commit is what delivers it. **Standing lesson: a diagnostic A/B toggle whose default is the OLD arm
leaves the win unshipped. The cleanup commit is the delivery, and it inherits the on-phone gate, not
the previous build.**

**2. BRANCH IDENTITY — THE PRIMARY RISK, PROVED FROM OUTSIDE THE FILE.** Deleting the wrong arm
passes `node --check`, the Leaflet hash, the diff-scope grep and a review read — the same
valid-JavaScript-wrong-meaning class as v16.65 §5's `subdaxZoom`. The gate harness eval'd HEAD's
real `buildSampleIndex` and asserted `buildSampleIndex(pts,cellLa,cellLo,undefined).mode === 'str'`,
independently confirming which arm was the default before deleting it rather than trusting a read of
the source. **PROMOTE TO STANDING: when a commit's correctness rests on which of two arms is live,
prove it by EXECUTING the pre-edit code, not by reading it.**

**3. THE CACHE-GUARD HAZARD — CAUGHT IN PLANNING, HANDLED IN THE SAME EDIT.** `mode` was removed
from the returned and cached objects and the `.mode===sIdxMode` term removed from all THREE guards
in the same edits: `pooledSampleIndex()` (`:2160`), its perf mirror (`:2440`), `idwIndex()`
(`:2850`). A surviving `.mode` term against an object that no longer carries `mode` reads
`undefined`, is false forever, and misses on EVERY rebuild — **slower than the arm it replaced, and
invisible to every static gate.** Observable only as `six MISS` on-phone. It read `six HIT`.

**4. GATES.** Bit-exact: **961 probe cells, 0 mismatches** (bucket store, r0, shade
`{num,den,near,nearD,nearR0,nearST}`, contour `{F,OK}`, tap depth, plus a 405-cell exhaustive
`bkAt` sweep, each via both an inline-mirror and a real-`bkAt` probe). **Plus a SPAN GATE — all
three hot-site bodies byte-identical to HEAD's arm B after removing exactly one indent level**,
which is the check that guarantees no accumulator was orphaned in the unwrap and is stronger than
value comparison alone. `node --check` both blocks exit 0. Leaflet inner-content SHA-256
`db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`, 147,552 bytes, 0 CRLF,
byte-identical to HEAD's block. `zoneAt`/`ORDER`/`dragend`/`spotsUnlocked`/both `<style>` blocks
absent from the diff and confirmed still present in the file. 18 hunks, +78/−154. Harness:
`D:\Claude Code\scratchpad\c3a_cleanup_bitexact.js`. **Note the corpus CHANGED** — 961 cells here
against `c3a_bitexact.js`'s 74 query points. Strictly larger, but the two are NOT one continuous
chain of evidence and must not be cited as such.

**5. `core.autocrlf` FIXED — the open minor item from v16.69.2 is closed.** Set to `input` on this
machine. `git ls-files --eol index.html` read `i/lf w/lf attr/` before and after, working tree
stayed clean, no renormalisation and no line-ending change. The `.gitattributes` option
(`* text=auto eol=lf`) was REJECTED — more durable, but it risks a whole-repo renormalisation commit
and would have broken one-variable-per-build on this diff.

**6. ON-PHONE GATE — PASS. Redcliffe z11, `2026.08.14a`, force-close/reopen confirmed.**

| | arm A (11 Aug) | arm B (11 Aug) | 14 Aug post-cleanup |
|---|---|---|---|
| S3 med/max | 195.5/242.0 · 174.0/228.0 | 84.0/112.0 | **119.0/163.0** |
| comp | 236.0 | 118.0 | **156.5** (max 200.0) |
| total | 599.0 | 471.0 | **510.0** |
| S2 | 24.0 | 24.0 | 25.0 |

`skip 0`, `sh 600²=360k`, `ct —`, `pool 64306`, `six HIT`, `idw MISS`, `n=10/10`. Segments reconcile
exactly: 0.5 + 25.0 + 119.0 + 1.0 + 8.0 + 3.0 = 156.5 = comp. **Toggle gone from the panel, `key
<mode>` row gone from the footer, and shading redrawing — 10 rebuilds at `skip 0` is the check that
a surviving `sIdxMode` reference is not throwing behind v16.68.1 §4's silent `catch(e){}`, which
would have presented as a stale overlay and no error of any kind.**

**7. THE PREDICTION MISSED, AND THE PREDICTION WAS AT FAULT.** The planning chat predicted S3
70–115 ms, derived from arm B's 84.0 ± the **21.5 ms INTRA-session** drift (v16.69.2 §2). Wrong
constant: this is a CROSS-session, CROSS-BUILD reading, where the applicable figure is v16.68.2 §5's
**±119 ms** — the exact confound v16.69.1 §2 warned against importing into an arm-B comparison. The
band should have been far wider and was therefore a weak test. 119.0 sits nowhere near the
160–200 ms falsifier and 55.0 ms below even the lower arm-A reading. **STANDING RULE: a
post-cleanup gate is a CROSS-SESSION reading. Bound it with the cross-session drift figure, or state
plainly that it is a BRANCH-IDENTITY check and not a magnitude measurement.**

**8. IS +35.0 ms A REGRESSION? BEST READING NO — BUT IT IS NO LONGER MEASURABLE.** No mechanism
exists in the diff: the §4 span gate proved the loop bodies byte-identical to arm B. S2 moved
+1.0 (+4%) while S3 moved +35.0 (+42%), and S3-specific movement is the documented signature of
v16.68.2 §5's effect rather than of a code change. The centre also differs from 11 Aug's pan set
(v16.69.2 §6: a named location is not a centre). **The honest claim is "arm-B territory, ~66 ms
below the arm-A mean at this centre" — NOT "the 100.75 ms saving was realised."** With the toggle
deleted this can never be paired again; that was the accepted price, recorded at v16.69.2 §12.

**9. TWO ITEMS THIS READING GENERATES.**

**9a. THE DEBOUNCE ELIGIBILITY MARGIN IS THINNER THAN RECORDED.** v16.68.1 §H's condition (compute
under ~200 ms) is banked in this file against arm B's 118.0 / 123.0 / 129.5. Redcliffe now reads
**156.5 median, 200.0 max — the max sits exactly on the threshold.** Still eligible; **rate the
350 ms `moveend` debounce against 156.5, not 118.0.**

**9b. §11b DID NOT SELF-FIX — IT MOVED ONTO A WORSE LINE.** Deleting the `key <mode>` row shifted
the footer up one row, so the v16.63 scale box now clips **`pool 64306 z11.0 six HIT idw MISS`**
instead. That line carries BOTH cache-state indicators; `key <mode>` was retired diagnostic chrome.
**The clip now costs more than it did.** The planning chat deferred §11b partly on the theory that
the deletion would relieve it — that theory was wrong, and is recorded as wrong. Fold it into the
next build that does not depend on reading the overlay; still not worth a build alone.

**NEXT-SESSION NOTE:** build **2026.08.14a**, roadmap **v16.70**, repo head `851a51c` plus this
entry's own commit. **C3a is CLOSED — shipped, gated, and in normal use.** Next job: **rate the
350 ms `moveend` debounce as its own change (v16.69.2 §8)**, against §9a's 156.5 ms and not this
file's older 118.0. Eligibility is NOT a decision — the debounce stays UNTOUCHED until rated against
its own reasoning (351 ms is idle main thread; cutting it moves jank closer to the finger; no
in-flight guard exists to absorb the extra overlap; and improving T1−T0 games the totals column
without removing work, v16.66 §8). **C3b stays PARKED (v16.69.2 §9).** Do not dispatch the bare
`_idwCache` `poolVersion` re-key (v16.68.3 §2 — a no-op while `buildShade()` nulls the cache on its
first line). The 600×600 grid cap stays UNTOUCHED — it changes output pixels. Carry §9b's overlay
position into whichever build comes next.*

*v16.69.2 · 11 Aug 2026 — **ON-PHONE A/B RUN COMPLETE. C3a MEASURED AND CONFIRMED — S3 down 54–76%,
C1 down 64% at Bargara, compute under 200 ms at every location for the first time.** No build, no
code. Build stays **2026.08.11a**. Repo head `7c0ae14` (the v16.69.1 entry) at session start.
**BOTH PREDICTIONS FALSIFIED — the string key cost roughly 2× what §3 estimated, and its cost is
geography-DEPENDENT. C3b is PARKED, not dispatched; the 350 ms `moveend` debounce is now the larger
lever and is ELIGIBLE for the first time.***

**1. RESULTS.** Force-close/reopen confirmed, `2026.08.11a` in-panel, shading + auto contours +
rebuild timing all ON. `pool 64306`, `six HIT`, `idw MISS`, `skip 0` in every reading; `ct —` at
both Moreton locations (C2 early-out still firing). Every batch ran the v16.69.1 §2 protocol: flip →
window clears → 11 pans → screenshot at `n=10/10` with the `key <mode>` footer in frame.

| location | arm | S3 med/max | C1 | C2 | CT | RESID | comp | total | grid |
|---|---|---|---|---|---|---|---|---|---|
| Redcliffe z11 | A1 `str` | 195.5/242.0 | 0.0 | 0.0 | 2.0 | 3.0 | 236.0 | 599.0 | sh 600²=360k · ct — |
| Redcliffe z11 | B `num` | **84.0**/112.0 | 0.0 | 0.0 | 2.0 | 3.0 | 118.0 | 471.0 | sh 600²=360k · ct — |
| Redcliffe z11 | A2 `str` | 174.0/228.0 | 0.0 | 0.0 | 2.0 | 3.0 | 209.0 | 565.5 | sh 600²=360k · ct — |
| Brisbane z10 | A `str` | 310.0/337.0 | 0.0 | 0.0 | 3.0 | 3.5 | 347.5 | 705.0 | sh 600²=360k · ct — |
| Brisbane z10 | B `num` | **86.0**/137.0 | 0.0 | 0.0 | 2.0 | 3.0 | 123.0 | 474.0 | sh 600²=360k · ct — |
| Bargara z11 | A `str` | 181.0/288.0 | 143.5 | 9.0 | 152.5 | 152.5 | 350.0 | 714.5 | sh 600²=360k · ct 360²=130k |
| Bargara z11 | B `num` | **43.5**/54.0 | **51.5** | 20.5 | 72.0 | 72.5 | 129.5 | 483.5 | sh 600²=360k · ct 360²=130k |

**2. P3 PASSES — THE APPARATUS IS SOUND, AND INTRA-SESSION DRIFT IS REAL BUT SMALL.** Redcliffe's
repeat arm A returned to **174.0** against A1's 195.5 — arm-A territory, nowhere near arm B's 84.0.
**Drift of 21.5 ms with nothing changed, so the honest Redcliffe saving is a RANGE: 90.0–111.5 ms
(100.75 against the A mean of 184.75).** This is the intra-session component of v16.68.2 §5's
±119 ms effect, and it is small enough that a ~100 ms delta survives it intact. **A single A/B pair
could not have distinguished a real saving from drift. The A→B→A arm is why the toggle was shipped
instead of two alternating builds, and it earned its cost.**

**3. P1 FALSIFIED — AND SO WAS ITS STATED ALTERNATIVE.** The absolute saving is NOT constant
(100.75 / 224.0 / 137.5), so key cost is not geography-independent as predicted. But the saving does
not track S3 proportionally either (54.5% / 72.3% / 76.0%), so v16.69.1 §3's stated falsifier — "the
residual is inner-loop work, not key churn" — is not what happened. Both branches of the prediction
are wrong. **Implied unit cost against the 15–40 ns/key estimate:**

| location | segment | probes/rebuild | Δ ms | implied ns/key |
|---|---|---|---|---|
| Redcliffe z11 | S3 | 3.24 M | 100.75 | 31 |
| Bargara z11 | S3 | 3.24 M | 137.5 | 42 |
| Brisbane z10 | S3 | 3.24 M | 224.0 | 69 |
| Bargara z11 | C1 | 1.166 M | 92.0 | 79 |

**31–79 ns, a 2.5× spread, against an estimated 15–40 ns.** Probe counts are CEILINGS — masked
pixels may short-circuit before probing — so the true ns/key is somewhat higher still. **Best
available model, stated as a HYPOTHESIS and not a finding: string-key cost scales with the number of
DISTINCT keys resident in the hash table (more distinct buckets at wide zoom ⇒ larger table ⇒ worse
locality) rather than with probe count alone. Consistent with Brisbane z10 being the worst case. Not
proven, and not worth a build to chase.**

**4. CORRECTION TO AN INTERIM READING MADE DURING THE RUN.** After Brisbane, arm-B S3 read 84.0 and
86.0 and was called flat, with the entire Redcliffe/Brisbane S3 gap attributed to key churn.
**Bargara's arm-B S3 is 43.5 — half that. Inner-loop work DOES vary with geography, just far less
than key cost did.** Recorded because the two-point version was stated confidently mid-run and is
wrong. Three points were needed; two were not enough.

**5. P2 FALSIFIED IN MAGNITUDE — C1 SAVED 92.0 ms AGAINST A PREDICTED 17–47.** The contour half of
C3a is worth roughly double the estimate, in the same direction as the S3 miss and by the same
mechanism (§3). Bargara remains the only location where this term is measurable at all — everywhere
else C2's early-out means `ct —` and C1 reads 0.0.

**6. BARGARA IS DIRECTIONAL, NOT RIGOROUS — CITE REDCLIFFE AS THE CONTROLLED PAIR.** The two Bargara
arms sat at visibly different map centres (arm A on Innes Park, arm B on the Burnett mouth).
**`C2` rising 9.0 → 20.5 is the tell — different contour geometry in view, on a segment C3a does not
touch.** Deltas of 137.5 and 92.0 cannot be flipped by that, but the Bargara pair does not meet the
same-centre standard v16.68.2 §5 set and must not be cited as though it does. **PROTOCOL LESSON:
"same centre" needs an explicit no-pan-between-arms step, not merely the same named location.
Panning to reach `n=10/10` moves the centre by design.**

**7. P4 DOES NOT FIRE — THE RESULT IS NOT CONTAINER-BOUND.** v16.69 §2a framed a saving near the
49 ms low end as evidence the sparse integer-keyed object was sitting in dictionary-mode elements
rather than the array fast path, which would have pointed at C3b. **The saving landed at or above
the TOP of the 49–130 ms range at every location.** Whatever container the engine chose, it is not
the limiting factor, and §2a's escape hatch is not needed.

**8. COMPUTE IS UNDER 200 ms EVERYWHERE — THE DEBOUNCE IS ELIGIBLE FOR THE FIRST TIME.**
236.0 / 347.5 / 350.0 → **118.0 / 123.0 / 129.5.** v16.68.1 §H deferred the 350 ms `moveend`
debounce until compute was under ~200 ms; that condition is now met at all three locations with
margin. **This is ELIGIBILITY, NOT A DECISION. The debounce STAYS UNTOUCHED until it is rated as its
own change against its own reasoning: the 351 ms is idle main thread, so cutting it moves jank
closer to the finger rather than removing it; there is no in-flight guard to absorb the extra
overlap; and improving `T1-T0` moves the totals column without removing a millisecond of work, which
is the shape of a metric being gamed (v16.66 §8).**

**9. C3b IS PARKED, NOT DISPATCHED.** v16.68.3 §7a made C3b dispatch-gated on these numbers. **The
gate returns PARK.** C3b removes what remains of hashing inside an arm-B S3 of 43.5–86.0 ms, so its
ceiling is a fraction of that — against a rewrite of `buildSampleIndex()` reaching three callers on
two anchors, plus v16.69 §8a's `NJ = -Infinity` allocation hazard and §7a's national-extent CSR
ceiling (~8.63e8 entries, ~3.45 GB). **The 350 ms debounce is the larger lever by an order of
magnitude.** C3b is not closed; it sits behind the debounce and behind any future need.

**10. CLEVELAND z11 DELIBERATELY NOT RUN.** Three locations, one controlled A→B→A pair, and
consistent direction and magnitude across all three. A fourth corroborating Moreton point adds
nothing the Redcliffe pair does not already carry. **Recorded as a judgement, not an omission** —
v16.69.1 §2 named Cleveland as the only droppable batch and it was dropped for that reason.

**11. TWO PROTOCOL DEFECTS IN v16.69.1 §2, BOTH IN THE PLANNING TEXT, RECORDED SO THEY DO NOT
RECUR.**

**11a. THE PRE-FLIGHT CHECK AS WRITTEN WAS IMPOSSIBLE.** §2 said to flip once and confirm the
`key <mode>` footer CHANGES *before any gestures*. The footer reads off `sIx.mode` — the returned
index object, deliberately, per v16.69 §5c — so at `n=0/10` no rebuild has occurred, there is no
object to read, and the footer correctly shows nothing. The first flip therefore looked like a dead
toggle and nearly triggered an abort. **What actually proves the flip fired is the PERF WINDOW
CLEARING (§5d): `n` resets to 0/10 and every row returns to `—`, and no other control in the app
does that.** **STANDING RULE: when a toggle's indicator is DERIVED FROM MEASURED OUTPUT, the
pre-flight check must be the SIDE EFFECT of flipping, never the indicator itself — the indicator
cannot exist until the thing being measured has run at least once.**

**11b. THE OVERLAY'S BOTTOM ROWS ARE CLIPPED BY THE v16.63 SCALE BOX.** The `5 km`/`10 km` scale and
the `z11.0` zoom readout, both moved to bottom-right by v16.63, overlap the left edge of the
overlay's last two lines. `key <mode>`, `n`, `skip`, `pre` and `noload` all remained legible and
**no CSS build was needed or taken.** v16.65 recorded the overlay's position as reasoned from the
CSS/DOM layout and never confirmed against a real narrow viewport; this is that gap surfacing.
**Fold the overlay position into the dead-arm cleanup commit if it is cheap in the same diff; do not
spend a build on it alone.**

**12. WHAT THE TOGGLE DESIGN BOUGHT, FOR THE RECORD.** Three locations, seven arms and a repeat-A
drift check ran in a single session with no force-close, no Pages round-trip and no container-state
change between arms. The alternating-builds alternative (v16.68.3 §5's rejected option) would have
required a deploy and a force-close between every arm, and could not have produced §2's drift
measurement at all. **The dead branch it leaves behind is the price, and the cleanup commit is the
next job.**

**NEXT-SESSION NOTE:** build **2026.08.11a**, roadmap **v16.69.2**, repo head is this entry's own
commit. No code shipped this session. **C3a is MEASURED and CONFIRMED — S3 −54% to −76%, C1 −64% at
Bargara, compute under 200 ms at all three locations.** Next job: **the DEAD-ARM CLEANUP COMMIT** —
delete the `'str'` branch and the `#six-mode-toggle`, carrying v16.69 §8b (deleting the toggle
removes ONE of two copies of the perf-window clearing statement; that commit must confirm the perf
toggle's own copy survives intact as the sole remaining one, and must not leave the perf toggle
without its clear) and optionally §11b's overlay position. After that: **rate the 350 ms `moveend`
debounce as its own change (§8)** — now eligible for the first time, still UNTOUCHED until rated.
**C3b is PARKED (§9).** Do not dispatch the bare `_idwCache` `poolVersion` re-key (v16.68.3 §2 — a
no-op while `buildShade()` nulls the cache on its first line). The 600×600 grid cap stays UNTOUCHED
— it changes output pixels and is a visual-quality decision, not a bit-exact optimisation.

*v16.69.1 · 11 Aug 2026 — planning only, no build, no code. Build stays **2026.08.11a**. Repo head
`82df814` (the v16.69 §8 additions) at session start. **This entry exists to fix the on-phone
protocol BEFORE it is run, not after.** v16.69 §7's protocol is sound but incomplete in four ways
that would each cost a re-run, and it carries no prediction for the contour half of C3a. It is
SUPERSEDED by §2 below. Also records two open verifications and one sync state. **Nothing here is a
measurement — C3a's saving remains UNMEASURED.***

**1. WHY §7 NEEDED AMENDING — four gaps, each of which invalidates a run rather than degrading it.**

  1. **No pre-flight check that the toggle is live.** The two arms are bit-exact by design, so a
     toggle that is wired but never actually read yields two identical arms and a null result that
     is indistinguishable from "C3a doesn't help". §5c wired the `key <mode>` footer off `sIx.mode`
     precisely so the arm is provable from the image — but §7 never says to CONFIRM THE FOOTER MOVES
     before spending 70+ gestures.
  2. **No within-session drift check.** The whole reason C3a shipped a toggle rather than two
     alternating builds (v16.68.3 §5) was to hold everything constant except the key scheme. That
     buys nothing unless one location runs **A → B → A** and the second A is compared to the first.
     v16.68.2 §5 measured S3 moving up to 119 ms between builds that touched nothing in S3; if that
     effect is intra-session rather than inter-session, a paired A/B is compromised too, and the
     repeat-A is the only thing that would reveal it.
  3. **No stated invalidator.** The headline prediction holds only at equal pixel count, so the
     shade W×H must READ 600×600 on both compared screenshots. And Redcliffe reported `skip 10` in
     v16.68.2 §9, cause unidentified — a non-zero `skip` means the median rests on fewer rebuilds
     than the protocol assumes.
  4. **No prediction for the contour half.** C3a removes ~1.166 M keys per rebuild from the C1
     field loop as well as ~3.24 M from S3, and Bargara is the ONLY location where contours still
     build post-C2. §7 predicted S3 and left C1 unpredicted, which makes the Bargara result
     unfalsifiable.

**2. THE PROTOCOL — SUPERSEDES v16.69 §7. Run this, not that.**
**RUN COMPLETE — SUPERSEDED by v16.69.2. This protocol was executed on 11 Aug 2026; results, falsified predictions and two defects in this protocol are in v16.69.2 §§1–11. Retained for the record.**


**PRE-FLIGHT (do not skip — this is gap 1).** Force-close and reopen the home-screen app. Confirm
`2026.08.11a` in the panel header. Enable depth shading, auto contours and the rebuild-timing
overlay. **Then flip `#six-mode-toggle` ONCE and confirm the `key <mode>` footer line CHANGES.**
If the footer does not move, ABORT — the checkbox is dead and every subsequent number is worthless.

**PER BATCH.** Flip → the perf window clears (§5d) → pan **11 times** → screenshot at `n=10/10`
with the `key <mode>` footer visible in frame. Eleven, not ten: the first gesture after a flip
rebuilds the index and must roll out of the window before the screenshot.

| # | location / zoom | arms | what it is for | droppable |
|---|---|---|---|---|
| 1 | Redcliffe z11 | **A → B → A** | headline + the within-session drift check (gap 2) | no |
| 2 | Brisbane z10 | A → B | the equal-absolute-saving prediction (P1) | no |
| 3 | Bargara z11 | A → B | the ONLY place C1 is measurable (P2) | no |
| 4 | Cleveland z11 | A → B | third Moreton point, corroborates P1 | **yes** |

Seven screenshots / 77 gestures required; nine / 99 with Cleveland. **If fatigue sets in, drop
Cleveland — nothing else.** The repeat-A at Redcliffe is not optional; it is the only check on the
apparatus itself.

**INVALIDATORS (gap 3).** Confirm the shade grid reads **600×600** on both the Redcliffe and
Brisbane screenshots — the P1 prediction is void at unequal pixel count. Record `skip` on every
reading; a non-zero value on either arm means that median rests on fewer rebuilds than assumed and
must be reported, not smoothed over.

**DO NOT USE v16.68.2's TABLE AS THE ARM-A BASELINE.** v16.69 §7 says to run at the same
locations/zooms as v16.68.2 "for direct comparability", which is true as a bonus and dangerous as a
method. The arm-A baseline is the arm-A screenshot from THIS session at THIS centre. Comparing an
arm-B reading against v16.68.2's numbers reintroduces the exact ±119 ms cross-session confound the
toggle was built to eliminate (v16.68.2 §5).

**3. PREDICTIONS, RECORDED BEFORE THE RUN.**

- **P1 — S3, the headline.** String-key cost is proportional to pixel count and INDEPENDENT of
  bucket occupancy, so at equal W×H the ABSOLUTE saving (arm A minus arm B, on S3) should be
  near-identical at Redcliffe and Brisbane despite their ~100 ms S3 gap (189.5 vs 291.0 in
  v16.68.2). A saving that instead tracks S3 PROPORTIONALLY falsifies the model: the residual is
  inner-loop work, not key churn. Unchanged from v16.69 §7; restated so the set is in one place.
- **P2 — C1 at Bargara, new.** 360×360 × 9 = 1,166,400 keys per contour rebuild; at 15–40 ns per
  concat+hash that is **17–47 ms** off a measured C1 of 117.0 (v16.68.2). Bargara is the only
  location where this term exists at all — everywhere else C2's early-out means C1 reads `0.0` and
  the contour half of C3a is structurally unmeasurable.
- **P3 — the repeat A.** Redcliffe's second arm-A median should return to within the noise of the
  first. If it does not, intra-session drift is real, and that is a finding about the MEASUREMENT
  APPARATUS that outranks the C3a result — do not report a saving derived from a compromised pair.
- **P4 — how to read a small number.** Per §2a, a sparse integer-keyed object sits in the engine's
  dictionary-mode elements, not the array fast path, so a saving at the LOW end of the 49–130 ms
  estimate is **CONTAINER-BOUND and points at C3b as the lever** — it is NOT "C3 doesn't help" and
  is NOT grounds to re-open C3a.

**4. TWO OPEN VERIFICATIONS.**

**4a. ORIGIN-VARIABLE SCOPE — one grep, before the run.** The three hot probe sites use three
**DONE — PASSED. Three `const` declarations, one per hot site (`:2508`, `:2547`, `:3089`), each destructured from `sIx`; buckets `_ixo`/`_ixoS`/`_ixoC` from `sIx.ix` at `:2506`/`:2545`/`:3087`, same object, same scope. No module-level declaration. Run unblocked.**

distinct bucket variables (`_ixo`, `_ixoS`, `_ixoC`) but a SINGLE shared set of origin names
(`_iLo`/`_iHi`/`_jLo`/`_jHi`/`_NJ`). If those are per-function locals there is nothing to see. If
any is module-level, that is precisely the §4 origin-purity hazard — one function's origin surviving
into another function's probe, with a different bucket store — and it bites only with the toggle ON,
i.e. during the run itself. Check:
`Select-String -Path .\index.html -Pattern '(let|const|var)\s+_iLo' | Select-Object LineNumber,Line`
Expected: one declaration inside each function that probes. **A single top-level declaration is the
finding, and it blocks the run.** Note this is a scope check only; `bkAt()`'s cold path already
reads origin, bounds and buckets off the one object `C` and is structurally correct by construction.

**4b. PROJECT-KNOWLEDGE SYNC.** The project-knowledge mirror was verified at **v16.68.2** at the top
of the session that produced v16.68.3 — it is now three entries stale (v16.68.3, v16.69, v16.69.1).
Re-upload the committed repo copy to project knowledge after this entry lands. Repo → PK, one
direction, per the standing rule. A chat opening on the stale mirror would read the entire C3a arc
as not having happened and could not detect that from inside.

**5. STANDING RULE PROMOTED FROM GAP 1.** An A/B toggle between two arms that are bit-exact by
design has the same observability problem as an early-out sharing a return path (v16.68.2 §2): a
dead toggle and a zero saving produce the same screenshot. **Any bit-exact A/B must ship an arm
indicator read off the same object the measured code reads, and the protocol must confirm the
indicator MOVES before the run begins.** The indicator was built correctly here; the protocol simply
did not use it.

**NEXT-SESSION NOTE:** build **2026.08.11a**, roadmap **v16.69.1**, repo head is this entry's own
commit. No code shipped. **Next job: the ON-PHONE A/B RUN per §2 above — not a build.** Do the §4a
scope check first; it blocks the run. C3a's saving is UNMEASURED and the 49–130 ms figure is
arithmetic, not a measurement, and may be zero. After the run, in order: the dead-arm cleanup commit
(delete the `'str'` branch and the toggle, carrying v16.69 §8b's duplicated perf-window clear —
confirm the perf toggle's own copy survives as the sole remaining one), then C3b dispatch-gated on
the numbers per v16.68.3 §7a. Do not start C3b before the numbers exist. Do not dispatch the bare
`_idwCache` `poolVersion` re-key (v16.68.3 §2 — it is a no-op while `buildShade()` nulls the cache
on its first line; the mode term added to its guard is a separate change and already shipped). The
350 ms `moveend` debounce and the 600×600 grid cap both stay UNTOUCHED.

*v16.69 · 11 Aug 2026 — C3a SHIPPED: numeric bucket key for `buildSampleIndex()`, diagnostic A/B
toggle, off-phone verification complete. Build **2026.08.11a**. Repo head before this build was
`aa87b6b` (the v16.68.3 planning entry). **ON-PHONE PERF RUN NOT YET DONE. C3a's SAVING IS
UNMEASURED — NOTHING IN THIS ENTRY MAY BE READ AS VALIDATED.** What is proven here is SAFETY only
(arm A byte-identical to shipped, arm B bit-exact against arm A, both off-phone). Whether C3a is
worth anything is an open question until §7's protocol runs on the device; §5's estimate of
49–130 ms is arithmetic, not a measurement, and may turn out to be zero.*

**1. WHAT SHIPPED.** `buildSampleIndex(pts,cellLa,cellLo,mode)` now takes a `mode` ('str'
default/arm A = shipped string key, unchanged formula; 'num' = arm B, new) and returns
`{ix,mode,iLo,jLo,iHi,jHi,NJ}` instead of a bare bucket object — origin travels WITH the buckets,
computed from `pts` itself on every call (not from `ptsBounds()`/`bb`), per v16.68.3 §2b/§6d. A new
`bkAt(C,i2,j2)` helper does the bounds-test-before-key-formation lookup (§3/§6c) for the two COLD
sites. All FIVE probe sites changed: `pooledSampleIndex()`, the r0 precompute, the shade pixel
loop, `buildAutoContours()`'s field loop (HOT, mode hoisted once above the loop, two full loop
bodies per v16.68.3 §5a), and `idwIndex()`/`idwDepthAt()`, `impIndex()`/`impAt()` (COLD, per-probe
branch via `bkAt()`, allowed per §5a). A new checkbox `#six-mode-toggle` ("🔢 Numeric bucket key
(diagnostic, C3a)") sits under the existing perf-toggle; flipping it sets the global `sIdxMode` and
clears the perf window (§5d) via the same clear the perf-toggle itself performs. The perf overlay
now prints `key <mode>` in its footer, read off the SAME object (`sIx.mode`, captured as
`_pf.sixMode`) every probe site reads mode from — not off the checkbox (§5c). Both cache guards
enumerated in v16.68.3 §5b now check mode alongside their existing key: `_sampleIndexCache.mode`
alongside `poolVersion` (`pooledSampleIndex`), `_idwCache.mode` alongside `n===s.length`
(`idwIndex`, scope-fenced — the `n===s.length`→`poolVersion` re-key stays OUT of scope per
v16.68.3's scope fence). `impIndex()` builds fresh every call — confirmed still no cache, nothing
to guard. Container stays a plain object in BOTH arms (§2a) — Map/dense-array is explicitly C3b,
not this build.

**2. CONTAINER CHOICE AND ITS CEILING — STATED BEFORE THE NUMBERS (§2a).** The saving is
container-bound, not key-bound: a max key of ~1.89 M at the current pool against a few thousand
occupied cells is very sparse for a plain object, so V8/JSC puts it in dictionary-mode elements
(numeric hashing, no string concat, no allocation) — a real win over the string arm, but NOT the
dense-array/CSR fast path C3b would give. A saving that lands at the LOW end of the estimate (49–130
ms per v16.68.3 §4) should read as "container-bound — C3b is the next lever," not as "C3 doesn't
help." This framing is recorded here BEFORE the on-phone numbers exist, per the spec's requirement.

**3. WHAT EACH CALLER PASSES TO `buildSampleIndex()` — VERIFIED FROM THE FILE (§2b).**
- `pooledSampleIndex()` — passes `buildShade()`'s/`buildAutoContours()`'s `pts`, which is
  `depthSamples()`, the SAME array `ptsBounds()` bounds. Consistent.
- `idwIndex()` — `const s=depthSamples();` then passes `s`. Same array. Consistent.
- `impIndex()` — builds a FRESH array from `imported`, NOT `depthSamples()`. Confirmed: under the
  OLD (pre-C3a) design, a `ptsBounds()`/`bb`-derived origin here would have been silently wrong,
  because `depthSamples()` is mask-filtered and the pool bbox can be TIGHTER than `imported`'s own
  extent — samples outside that tighter window would have been dropped at construction with no
  error. **This is the confirmed bug the §2b amendment prevents**, not merely a footnote: C3a's
  spec (compute bounds from `pts` itself, inside `buildSampleIndex()`, every call) sidesteps it
  structurally rather than requiring `impIndex()` to be specially handled.

**4. ARM A BYTE COMPARISON AGAINST HEAD (`aa87b6b`) — §6.** SPAN DEFINITION: opens at
`for(let m=0;m<bk.length;m++){` / `for(let k=0;k<bk.length;k++){` immediately after
`if(!bk)continue;`; closes at the matching `}` that terminates THAT loop (brace-depth-counted, not
textual), excluding the bucket-lookup statement and the i2/j2 loop headers above it (permitted to
change — arm A's enclosing loop sources `ix` off `sIx.ix` now, a differently-shaped object). Ran
programmatically (not by eye) via a Node harness that brace-matches the span out of both HEAD and
the working tree and does a strict string `===`:
  - r0 precompute (`:2427` pre-edit): 167 bytes, IDENTICAL.
  - shade pixel loop (`:2448` pre-edit): 238 bytes, IDENTICAL.
  - `buildAutoContours` field loop (`:2950` pre-edit): 206 bytes, IDENTICAL.
All three: **byte-for-byte identical, including leading whitespace** — arm A's else-branch bodies
were deliberately left at the PRE-C3a original indentation (not re-flowed to the new if/else
nesting level) specifically so this comparison is literal, not "equivalent modulo whitespace."
Harness: `D:\Claude Code\scratchpad\c3a_span_compare.js`.

**5. BIT-EXACTNESS — §7.** Geometric, not compositional, per the spec's own framing (a bijective
re-map has no firing condition, so the v16.68.1 §B representative-pool rule doesn't apply — what
matters is the bounds domain, not pool composition). A Node harness extracts the REAL, shipped
`buildSampleIndex()`/`bkAt()` verbatim (brace-matched extraction + `eval`, not retyped) from
`index.html` and runs them against a small synthetic pool (26 points, southern-hemisphere
magnitude lat/lng, four deliberate bbox corners + one isolated point):
  - **(a) key-formation domain, exhaustive** over `[iLo-2..iHi+2]×[jLo-2..jHi+2]` (189 in-window +
    136 out-of-window cells at this pool's scale): all in-window keys distinct (injectivity), all
    out-of-window probes skip (`bkAt`→`undefined`). **Constructed row-wrap case**, per §3/§7a: a
    dedicated 4-corner pool puts a real sample at `(iLo,jHi)`; querying `(iLo+1,jLo-1)` — which
    WITHOUT bounds-test-before-key-formation would compute `key=(1)*NJ+(-1)=NJ-1`, IDENTICAL to
    `(iLo,jHi)`'s correct key — is confirmed to skip (`undefined`), not alias into that occupied
    bucket. `cj-1` at `jLo` and `cj+1` at `jHi` explicitly checked for every row `i2∈[iLo,iHi]`.
  - **(b) end-to-end value compare, arm A vs arm B**, per site, over 74 query points (interior grid
    + boundary-hugging + near-isolated-point + far-outside-pool):
    - `:2427` r0 array — 26/26 samples bit-identical.
    - `:2448` shade pixel loop — compared the full `{num,den,near,nearD,nearR0,nearST}` tuple that
      the (unchanged, byte-proven-identical) downstream code turns into the alpha/ImageData buffer
      — 74/74 identical.
    - `:2950` `buildAutoContours` F field — compared `{F,OK}` per query, 74/74 identical; the level
      set is a deterministic, mode-independent function of `F`/`OK` once built (no `sIx` reference
      anywhere in the marching-squares code), so identical `F`/`OK` implies an identical level set
      without re-running marching squares under both arms.
    - `:2789`/`:3595` `idwDepthAt`/`impAt` returned depth — both share one accumulation shape
      (fixed, non-pool-anchored `cellLa`/`cellLo`), tested together, 74/74 identical.
  - **0 failures across every check.** Harness:
    `D:\Claude Code\scratchpad\c3a_bitexact.js`.

**6. §8 CHECKLIST — ALL VERIFIED.**
  - `node --check` on both extracted script blocks: PASS (Leaflet block 147,552 bytes; app block).
  - Leaflet inner-content SHA-256: `db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`
    — MATCHES the required value, both before and after the indentation fix that made the arm-A
    spans byte-identical (re-verified after the final edit, diff against the first extraction was
    empty).
  - Diff-grepped absent: `zoneAt(`, `spotsUnlocked`, `notake:true` (ORDER-array/zone-order
    literal) — 0 matches in the `+`/`-` diff. Manually confirmed still PRESENT and untouched in the
    file: `zoneAt()` (:1327, unchanged), `const ORDER=["MNP","CPZ","HPZ","GUZ"];` (:1229,
    unchanged), the green-zone `dragend` safeguard + `spotsUnlocked` (:1576-1580, unchanged — all
    three sit well outside every diff hunk). Both `<style>` blocks (Leaflet :17-683, app :686-1028)
    untouched — every diff hunk touching the panel HTML sits at :1049-1168 (build string + the new
    checkbox), well below the style blocks' line range.
  - Build string bumped in both locations (`:1052`, `:1091` pre-edit) to **2026.08.11a** — read
    from the file (was `2026.08.09c`), checked against git log and roadmap history for
    `2026.08.1[01]` (no match — today is the first build of 11 Aug, so `a` is correct, not a
    collision).
  - `git diff` reviewed hunk-by-hunk before commit — matches intended scope exactly, nothing
    outside it.

**7. §5 — THE ON-PHONE RUN IS NOT DONE. PROTOCOL AND PREDICTION FOR AARON TO RUN.**
**SUPERSEDED by v16.69.1 §2 — that protocol adds a pre-flight toggle check, an A→B→A drift arm, stated invalidators and a C1 prediction. Run v16.69.1 §2, not this. Retained for the record.**

Fixed map centre, overlay ON, flip the `#six-mode-toggle` checkbox every 10 gestures. Force-close/
reopen the app first; confirm build `2026.08.11a` in-panel before starting. **Flipping clears the
perf window (§5d)** — protocol per gesture batch: flip → window clears → pan 11 times → screenshot
at `n=10/10` (by then the window holds gestures 2–11 and the index-rebuild gesture has rolled out
of it). Screenshot must show the `key <mode>` footer line so the arm that produced the numbers is
provable from the image itself, not asserted. Run at the same locations/zooms as v16.68.2's table
(Redcliffe z11, Brisbane z10, Cleveland z11, Bargara z11) for direct comparability.
**PREDICTION, RECORDED BEFORE THE RUN:** string-key cost is proportional to pixel count and
INDEPENDENT of bucket occupancy, so at equal W×H the ABSOLUTE saving (arm A minus arm B, on S3)
should be near-identical at Redcliffe and Brisbane despite their ~100 ms S3 gap (v16.68.2 measured
189.5 vs 291.0 ms). A saving that instead tracks S3 PROPORTIONALLY falsifies the model and means
the residual is inner-loop work, not key churn. This build did NOT run that comparison — it only
proves arm A is byte-identical to shipped and arm B is bit-exact against arm A off-phone.

**8. TWO ITEMS CARRIED FORWARD — ONE AGAINST C3b, ONE AGAINST THE CLEANUP COMMIT.**

**8a. `NJ = -Infinity` ON AN EMPTY POOL — HARMLESS FOR C3a, A LIVE HAZARD FOR C3b.** With
`pts.length === 0` the min/max scan leaves `iLo=+Infinity, iHi=-Infinity, jLo=+Infinity,
jHi=-Infinity`, so `NJ = jHi-jLo+1 = -Infinity`. **This is NOT a C3a defect** and needs no fix in
this build: the insert loop never runs (so no `NaN` key is ever written), and every probe is
rejected by the bounds test before key formation — `i2 < +Infinity` is true for all finite `i2`, so
`bkAt()` returns `undefined` unconditionally. Verified directly on the shipped code: empty pool
returns `undefined` at both `(0,0)` and `(1e6,1e6)`; a single-point pool gives `NJ=1`, its own cell
occupied, and all four neighbours skipping. **RECORD IT AGAINST C3b.** C3b's CSR design sizes a
row-pointer array at `NI*NJ+1`; on an empty pool that becomes an allocation on `-Infinity`, which
THROWS rather than degrading quietly. C3a's sparse plain object tolerates a nonsense `NJ` because
nothing indexes with it; a flat array does not. **C3b must clamp or early-return on an empty/
degenerate pool before sizing anything.** This is exactly the class of thing that is invisible until
the container changes — the reason it is written down now rather than found during C3b.

**8b. THE §5d DEVIATION IS ACCEPTED AND BELONGS TO THE DEAD-ARM CLEANUP COMMIT.** v16.68.3 §5d
specified "reuse the same clearing path the perf toggle already performs — do not reimplement." The
shipped `#six-mode-toggle` handler instead **copies the five clearing assignments inline**
(`perfSamples=[];perfSkips=0;perfPre=0;perfNoLoad=0;perfT0=null;`) rather than calling a shared
function. Correct today and identical in effect, so it is ACCEPTED as shipped — but it is a
duplicated statement that can drift if the perf-window bookkeeping ever changes. **NAMED HERE SO IT
IS NOT ORPHANED WHEN THE TOGGLE IS DELETED:** the dead-arm cleanup commit removes the `#six-mode-
toggle` handler, which removes one of the two copies. That commit must confirm the perf-toggle's own
copy survives intact and is the sole remaining one — the cleanup must not delete the wrong copy, and
must not leave the perf toggle without its clear.

**NEXT-SESSION NOTE:** build **2026.08.11a**, roadmap **v16.69**, repo head is this entry's own
commit. Code shipped and off-phone-verified; **on-phone A/B perf run per §5/§7 above is the next
job** — not a new build. After that run: if C3a lands at the low end of the 49–130 ms estimate
(§2a's container-bound framing), that is expected and NOT a reason to re-open C3a; the next lever
is C3b (CSR flat arrays) dispatch-gated on this run's numbers per v16.68.3 §7a. Do not start C3b
before the on-phone numbers exist. A follow-up commit should delete the dead arm (the 'str' branch
and the toggle) once the A/B comparison is done and arm B is confirmed safe to ship as the only
path — not yet, since the on-phone run hasn't happened. **That cleanup commit also carries §8b's
duplicated perf-window clear** (delete the toggle's copy, confirm the perf-toggle's own copy
survives as the sole remaining one).

*v16.68.3 · 11 Aug 2026 — planning only, no build, no code. Build stays **2026.08.09c**.
Repo head `efe3862` at session start (the v16.68.2 entry). **RATING OF `_idwCache` AGAINST C3
COMPLETE — the v16.68.2 §10 recommendation is REVERSED.** §§1–5, 8 are the planning session's
own text. **§6 was written in planning and is WRONG by two orders of magnitude; the derivation
that corrects it (§§6a–6d) was done by Claude Code against `index.html`, and §6's original
figures are left in place struck through.** This is the entry the "DERIVE FROM THE FILE, do not
inherit from planning" instruction was written for, and it is the reason the C3a build did not
ship a broken key.*

**1. CORRECTION TO v16.68.2 §10 — `_idwCache` CANNOT PAY INTO S3.** §10 read `idw MISS` on every
pan as the IDW structure rebuilding every pan with the cost landing in S3. v16.65's own
instrumentation note states the opposite and is authoritative: `buildShade()` nulls `_idwCache` on
its first line and never repopulates it; only `idwIndex()` (tap-to-read) does. MISS on every pan is
the PREDICTED reading for a clean pan protocol — a HIT would have meant a contaminated gesture.
Nothing repopulates it during a pan, so there is no per-pan cost to remove. **Expected S3 saving:
zero.** §10 also inverted the `six HIT` comparison, which measures a different cache on a different
path.

**2. THE PROPOSED EDIT IS A NO-OP AS SCOPED.** Re-keying `s.length` → `poolVersion` changes nothing
while `buildShade()` unconditionally nulls the cache first. A real fix must also remove the nulling,
which touches tap-to-read and `impIndex()` (the Navionics-comparison path v16.59 deliberately fenced
off). **Recorded so a future session does not dispatch the bare re-key.**

**3. `_idwCache` RECLASSIFIED, NOT CLOSED.** Stays on OPEN/LOW PRIORITY, moved from "perf / S3" to
"correctness / tap path": the `s.length` key can collide across two equal-length pools and serve a
stale index to tap-to-read. Small, real, not a pan cost.

**4. C3 IS THE NEXT DISPATCH.** `sIx[i2+':'+j2]` = 3.24 M concat+hash per shade rebuild at the
600×600 cap (360,000 px × 9), plus 1.17 M in C1 at 360×360 where contours still build (post-C2,
Bargara only). At 15–40 ns per concat+hash on JSC that is **49–130 ms**, the right order to be the
dominant remaining S3 term (measured S3 189.5 / 291.0 / 173.5 / 151.5). Estimate with arithmetic
exposed, not a measurement.

**5. GATE — IN-BUILD TOGGLE, NOT ALTERNATING BUILDS.** The v16.68.2 §5 binding (S3 moved up to
119 ms between builds touching nothing in S3) is satisfied more cleanly by shipping both key schemes
behind a diagnostic toggle, default OFF, flipped every 10 gestures at a fixed map centre — same
build, same session, same viewport, same pool. Alternating builds requires a Pages round-trip and
force-close between arms and still spans container state. Same precedent as the perf overlay. Dead
branch removed in a follow-up commit. **PREDICT THE SEGMENT:** string cost is ∝ pixel count and
independent of bucket occupancy, so at equal W×H the ABSOLUTE saving should be near-identical at
Redcliffe and Brisbane despite their ~100 ms S3 gap. A saving that tracks S3 proportionally
falsifies the model and means the residual is inner-loop work, not key churn.

**6. THE ONE REAL BUG RISK — NEGATIVE CELL INDICES.** `-3:5` is a unique string key;
`i2*STRIDE+j2` is NOT injective for negative i2/j2, and the 3×3 probe reaches outside the grid on
any viewport extending past the pool bbox. Silent collision, wrong bucket, no error. **The hazard is
real and correctly identified; the remedy and the sizing below are both wrong.**
~~Spec as `((i2+BIAS)<<SHIFT)|(j2+BIAS)` with a runtime guard asserting `j2+BIAS` is inside
`[0,1<<SHIFT)`. Indicative sizing (pool lat span 2.90° at cellLa≈0.001078° → ~2,690 cells):
SHIFT=12, BIAS=512, max key ≈13.1 M, a small int in the engine fast path.~~ **SUPERSEDED by §6a.
The sizing was derived from the pool's cell SPAN (~2,690); `buildSampleIndex()` (`index.html:2098`)
keys on ABSOLUTE floor-indices, which are ~23k–25.6k (lat) and ~125k–126k (lng). `(i2+512)` stays
negative for every point in the pool and `(j2+512)` overruns a 12-bit field ~30×, smearing into the
i2 field. Not an edge case — broken for every point. Additionally the `assert`-style guard is the
wrong shape; see §6c.**

**6a. DERIVED SIZING — FROM THE FILE, NOT FROM PLANNING.** Read off `index.html` at head `efe3862`:

| quantity | source | value |
|---|---|---|
| `cellLa = 120/mLat`, `mLat=111320` | `:2394`, `:2330` | 1.077973e-3° |
| `i2 = floor(lat/cellLa)`, lat −24.7475…−27.642694 | `:2098` | **−25,644 … −22,958** (2,687 cells) |
| `mLngMin = 111320·cos(27.642694°)` | `:2391` | 98,622.7 |
| `cellLo = 120/mLngMin` | `:2394` | 1.216766e-3° |
| `j2 = floor(lng/cellLo)`, lng 152.47…153.324175 | `:2098` | **125,307 … 126,009** (703 cells) |

Lat/lng extents: repo CSVs give −27.642694…−25.894569 / 152.736646…153.324175; Bargara's
−24.7475 / ~152.47 arrives via imported datasets, matching the on-phone range in the v16.60 comment
at `:2377`. **`i2` needs 15 bits plus sign, `j2` needs 17 — so no packing of the ABSOLUTE indices
fits the fast path (§6b).** The key must be ORIGIN-RELATIVE, anchored on the pool bbox `bb` already
cached by `ptsBounds()` (`:2148`):

```
iLo = floor(bb.minLa/cellLa)              jLo = floor(bb.minLo/cellLo)
iHi = floor(bb.maxLa/cellLa)              jHi = floor(bb.maxLo/cellLo)
NJ  = jHi - jLo + 1                       ≈ 703   (runtime-derived — see below)
key = (i2-iLo)*NJ + (j2-jLo)              max ≈ 2686*703 + 702 = 1,888,960
```

≈1.89 M: a small int and a valid array index. Injective iff `(j2-jLo) ∈ [0,NJ)`, which §6c enforces.

**FORWARD CHECK AT NATIONAL SCALE — the design does not need revisiting for the expansion queue.**
Working shown: over lng 113–154, lat −10…−44, `mLngMin = 111320·cos(44°) = 80,077`,
`cellLo = 120/80077 = 1.49856e-3°`, `NJ ≈ 41/1.49856e-3 ≈ 27,359`, `NI ≈ 34/1.077973e-3 ≈ 31,540`,
`max key ≈ 31,540 × 27,359 ≈ 8.63e8` — still comfortably under 2³² (4.29e9). **`NJ` is
runtime-derived from `bb` on every build; 703 is illustrative of the current pool only and must
never be hard-coded.**

**6b. THE TRAP §6 DID NOT REACH — KEYS ≥ 2³² ARE STRINGIFIED ANYWAY.** A plain JS object keeps a
numeric property in indexed/element storage only for `0 ≤ k < 2³²−1`; past that the engine converts
the key to a string. Any injective packing of the absolute indices lands ≳6.7e9, so "just use a
bigger BIAS" **reintroduces the exact concat-and-hash cost C3 exists to remove, while looking like a
fix** — and would have measured as a null result with no visible defect to explain it. The saving is
contingent on the key staying under 2³², not merely on it being a number. **General lesson: for a
JS-object key, "numeric" is not the property that buys the fast path — "numeric AND a valid array
index" is.**

**6c. ROW-WRAP ALIASING — THE SILENT FAILURE MODE. The bounds test must PRECEDE key formation.**
"Out-of-window is a skip, bit-identical to the string version's `undefined` miss" holds only in that
order. Formed first, `j2-jLo = -1` yields `(i2-iLo)*NJ - 1` — a VALID key belonging to the previous
row's LAST cell. That is a wrong-bucket **HIT**, not a miss: no error, no `continue`, real samples
returned from a cell one row up and ~700 cells away, firing at exactly the `ci-1` pool-edge case the
3×3 probe reaches on every viewport touching the bbox edge. **Spec: test `i2` against `[iLo,iHi]`
and `j2` against `[jLo,jHi]` INDEPENDENTLY, and `continue` BEFORE computing `key`.** With that
ordering the skip is bit-exact by construction — every sample lies inside the window by definition
of `bb`, so an out-of-window cell provably holds no sample, and the string version would have missed
there too. This also subsumes the negative-index hazard §6 raised, without a fallible assert. **A
guard that asserts is the wrong shape here; the correct shape is a bounds test that skips.**

**6d. ORIGIN PURITY — VERIFIED FROM THE FILE, NOT INHERITED FROM v16.59.** `_sampleIndexCache` is
`poolVersion`-keyed, so an index built with one origin and probed with another is a silent
wrong-bucket read for **every pan in that `poolVersion`** — the worst failure shape available here.
Both preconditions checked directly against `index.html` at `efe3862`:

- `ptsBounds()` (`:2148–2156`) caches on `poolVersion` **in its own body**
  (`_boundsVersion===poolVersion&&_boundsCache`) and computes min/max over all of `pts` with no
  viewport term. **Confirmed.**
- `bb` is `const` in BOTH builders — `:2312` (`buildShade`) and `:2864` (`buildAutoContours`) — each
  assigned only from `ptsBounds(pts)` and never reassigned anywhere in the app script (checked by
  grep for `bb =`; only those two sites plus the v16.60 comment at `:2102`). The ±30% viewport
  clipping at `:2313–2324` and `:2865–2877` writes to separate `let minLa/maxLa/minLo/maxLo` copies,
  leaving `bb` pure. **Confirmed: `bb` is the pool bbox, not viewport-clipped render bounds.**

**ENFORCE STRUCTURALLY: every probe site reads `NJ`/`iLo`/`jLo` off the SAME object it reads the
buckets off. Never a module-level copy, never a second call to re-derive them.**

**7. STAGED: C3a THEN, ONLY IF WARRANTED, C3b.** C3a = numeric key only — a bijective re-map of the
same (i2,j2), bit-exact by construction. ~~`pooledSampleIndex()`/`idwIndex()`/`impIndex()` all
unaffected.~~ **SUPERSEDED: not achievable. The origin must travel WITH the index (§6d), so
`buildSampleIndex()`'s RETURN SHAPE changes (`{ix,iLo,jLo,iHi,jHi,NJ}`) and five probe sites change
with it: `:2427` (r0 precompute), `:2448` (shade pixel loop), `:2950` (`buildAutoContours`), `:2789`
(`idwIndex` read), `:3595` (`impIndex` read).** Threading the origin ON the returned object is the
MITIGATION for the v16.59 multi-anchor hazard, not a re-exposure of it — a caller cannot pair one
index with another's origin unless it mixes objects, which §6d forbids. But the blast radius is
larger than planned, and `impIndex()` is back in scope: **bit-exactness must now be proven for the
`idwIndex()` and `impIndex()` probe paths, not only the shade loop. The Navionics-comparison tool
has no gate of its own.** C3b = CSR flat arrays (removes hashing entirely, not just the concat) is a
rewrite of `buildSampleIndex()`, which three callers reach with different `cellLo` anchors —
dispatch only if C3a lands at the low end of the estimate.

**7a. STAGING HOLDS BUT IS WEAKENED.** C3a now changes the return shape and all five probe sites, so
C3b is a smaller MARGINAL step than planned — the interface churn C3b was going to pay for is paid
by C3a. C3a still leaves bucket CONSTRUCTION and the container type unchanged; C3b changes both plus
memory layout. **Measure C3a first regardless.** One asymmetry to record now: C3a's key scales to
national extent (§6a), but C3b's CSR row-pointer array is sized `NI×NJ+1`, which is ~1.89 M entries
(~7.6 MB Int32) at the current pool and **~8.63e8 entries (~3.45 GB) at national extent — not
viable.** C3b would need a hashed or per-row-compressed origin if the pool ever widens. C3a carries
no such ceiling.

**8. FLAGGED, NOT QUEUED.** C3 removes a constant from a 360,000-iteration loop; it likely will not
bring Brisbane z10 (compute 326.5) under the ~200 ms threshold on its own. The next lever after it
is the 600×600 grid cap (`:2328`), which changes output pixels — a visual-quality decision, not a
bit-exact optimisation. Recorded so the endpoint is not oversold. The 350 ms `moveend` debounce stays
UNTOUCHED.

**NEXT-SESSION NOTE:** build **2026.08.09c**, roadmap **v16.68.3**, repo head `efe3862` before this
entry's own commit. No code shipped. Decided: **C3a is the dispatch, `_idwCache` reversed and
reclassified to low-priority correctness.** Next job: **the C3a build** — origin-relative key per
§6a, bounds-test-before-key per §6c, origin threaded on the returned object per §6d, toggle-gated
A/B per §5, bit-exactness proven off-phone across ALL FIVE probe sites including `impIndex()` per
§7, perf gate on-phone at one fixed centre. Do not dispatch the bare `_idwCache` re-key (§2). Do not
inherit §6's struck-through sizing.

*v16.68.2 · 9 Aug 2026 — ON-PHONE RUN FOR `2026.08.09c` COMPLETE. **C2 EARLY-OUT CONFIRMED FIRING
ON-DEVICE; §B RETIRED.** Planning/measurement only, no build, no code. Build stays **2026.08.09c**.
Repo head `b3a5195` (the v16.68.1 entry, pushed; project-knowledge copy verified byte-identical by
SHA-256 `e8080540…80ef6b`). Supersedes three predictions in v16.68.1 §G.*

**1. RESULTS.** Force-close/reopen confirmed, `2026.08.09c` in-panel, overlay ON, depth shading +
auto contours + rebuild timing all ON. `pool 64306`, `six HIT`, `idw MISS`, `pre 0` in all five.

| reading | n | idle | comp | paint | total | S2 | S3 | S5 | RESID | C1 | C2 | CT | `ct` grid | skip |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Redcliffe z11 | 10/10 | 351.0 | 224.5 | 2.0 | 582.0 | 24.0 | 189.5 | 8.0 | 2.0 | **0.0** | 0.0 | 2.0 | **—** | 10 |
| Brisbane z10 | 8/10 | 351.0 | 326.5 | 6.5 | 689.5 | 24.0 | 291.0 | 5.0 | 3.0 | **0.0** | 0.0 | 2.0 | **—** | 0 |
| Cleveland z11 | 10/10 | 351.0 | 208.5 | 2.0 | 563.5 | 23.0 | 173.5 | 6.0 | 2.0 | **0.0** | 0.0 | 1.0 | **—** | 0 |
| Bargara z11 | 10/10 | 351.0 | 290.5 | 12.0 | 653.5 | 4.0 | 151.5 | 5.0 | 126.0 | 117.0 | 8.0 | 126.0 | 360×360=130k | 0 |
| Brisbane z10 TRANSIT | 9/10 | 351.0 | 498.0 | 11.0 | 860.0 | 6.0 | 321.0 | 8.0 | 180.0 | 166.0 | 21.0 | 180.0 | — | 0 |

**2. THE DECIDER IS `ct —`, NOT `C1 0.0`.** §G warned that `0.0` is the return path. It is also the
reading produced by the PRE-EXISTING empty-levels return, which returns before `_cm1` is assigned by
the same mechanism — so `C1 0.0` alone cannot distinguish the new early-out from the old behaviour,
and v16.66 §1 already recorded `C1 0.0` at all three Moreton locations. **What distinguishes them is
the grid line.** Pre-edit the field loop ran to completion, so `ct W×H=Nk` was populated. It now
reads `ct —` at Redcliffe, Brisbane and Cleveland while Bargara still reads `ct 360×360=130k`. The
field build is being skipped, not merely producing no levels. **Record this as the general lesson: an
early-out that shares a return path with existing behaviour needs a side-channel to be observable at
all. Design the instrumentation with the optimisation.**

**3. §B IS RETIRED. `legacy_unknown` carries no `d > 0` in these viewports.** The 20,533-point
unaudited block was the one thing that could have stopped the early-out firing on the phone's
64,306-point pool when it fired on the gate's 52,929-point corpus. It fires. No audit is needed and
the planned `version:2`-export depth-sign check is CANCELLED. **The standing rule promoted in §B
stands unchanged and was vindicated** — the gate genuinely could not have settled this, and the
on-phone run was the right deliverable.

**4. THE FULL SAVING WAS REALISED. Net totals moved less because S2 and S3 drifted between pan
sets.** Reconciled against the v16.66 §1 baseline table (`:454-461` pre-insert), medians throughout:

```
loc        ΔS2      ΔS3   ΔRESID      sum    Δcomp    slack
Bri     -342.5     18.0   -184.5   -509.0   -511.0     -2.0
Red     -480.0     38.5   -128.5   -570.0   -584.0    -14.0
Bar     -101.0   -119.0      0.0   -220.0   -220.8     -0.8
Cle     -515.5   -107.5   -137.5   -760.5   -748.0    +12.5
```

**ΔRESID is the C2 early-out's whole contribution, and at each location it equals that location's
baseline C1 to within 2 ms** — Brisbane −184.5 against C1 186.5, Redcliffe −128.5 against 130.0,
Cleveland −137.5 against 138.5 (n=6 baseline, corroborating only). **At Bargara ΔRESID is exactly
0.0**, which is the early-out correctly not firing where contours draw. ΔS2 is v16.67.1's scanline
mask, already banked. Slack is the residue of summing medians of different distributions and is
≤15 ms everywhere.

**§G's "total ~540" at Redcliffe was therefore a bad predictor of a correct change** — it assumed
every other segment held constant across pan sets, and S3 alone moved 38.5 ms. **Predict the segment
the change touches, not the total.**

**5. NEW AND UNRESOLVED — S3 IS NOT STABLE ACROSS NOMINALLY IDENTICAL READINGS, AND THIS IS A GATE
PROBLEM FOR C3.** S3 at the same location and zoom, across builds that touched nothing in S3:
Bargara z11 **268.0 / 273.0 → 151.5** (−119.0, −44%); Cleveland z11 **281.0 → 173.5**; Redcliffe z11
**151.0 → 189.5**; Brisbane z10 **273.0 → 291.0**. Not monotonic, so not drift.

Two candidates are excluded by recorded evidence: the mask set is unchanged (v16.67.1's gate, 0
disagreeing pixels over 28,804,800), and `idw MISS` on every pan is not new — v16.66 §1 recorded it
in all seven readings. That leaves **viewport composition** (water fraction and local bucket
occupancy under the 600×600 grid), consistent with v16.66 §3's finding that sparse local buckets make
the IDW loop cheaper, but **NOT ESTABLISHED**.

**Consequence, binding on the next build: C3's benefit lands in S3, so a C3 gate that compares S3
between two pan sets can be swamped by a ±119 ms viewport effect.** C3 must be measured as a paired
A/B — same device, same session, same map centre, alternating builds — or by a segment-level counter
(transient allocations per pan) rather than by wall-clock S3 across sessions.

**6. CORRECTION TO §G — the pool scan lands in `CT`, not `RESID`.** §G predicted a small `RESID`
shift. `RESID(+CT)` is a superset of `CT`, and at every firing location the two are equal to within
1.0 (Redcliffe 2.0/2.0, Brisbane 3.0/2.0, Cleveland 2.0/1.0), as they are at Bargara where it does
not fire (126.0/126.0). **The early-out's own cost is therefore directly measured at 1–2 ms rather
than inferred.** Better than predicted; record the measured figure, not the estimate.

**7. CORRECTION TO §G — THE BARGARA → MORETON VISIBLE-BREAK CHECK IS UNOBSERVABLE BY CONSTRUCTION.**
It was run (Bargara z11 → Brisbane z10) and showed no stranded contours, but the test cannot fail.
Leaflet polylines are geographic: a layer stranded at Bargara sits ~300 km north of a Moreton
viewport and is off-screen whether or not the teardown ran. The general case is worse — **any
viewport that triggers the early-out has no contourable sample in bbox+pad, so it also excludes the
footprint of any geometry that could have stranded.** There is no pan between these regions that puts
stale contours inside the new viewport.

**The teardown is established by the six-exit-path byte comparison in v16.68 (`:2859, :2863, :2878,
:2942, :2967, :2971`, all ending in the identical
`{if(autoCtLayer){map.removeLayer(autoCtLayer);autoCtLayer=null;}return;}`), which is a stronger
proof than any pan and was already done.** The pan is corroborating, not the gate. **Lesson: before
nominating an on-device check as "the one visible break", verify the failure it targets would
actually be visible.**

**8. THE TRANSIT READING IS NOT A LOCATION MEASUREMENT — do not cite row 5 as Brisbane z10.** It is a
9-sample median spanning the pan from Bargara, crossing the Maroochy/Noosa corpus (max-d 3.53–42.48
m), where full contour fields are legitimately built at z10 viewport size. `C2 21.0 med / 46.0 max`
is the fingerprint: at least half the window created a contour layer. It is useful only as
confirmation that the rebuild path stays live across the transit and that layers are created and torn
down repeatedly, rather than the early-out wedging the function into a permanent no-op. Its `C1
166.0` does not contradict the clean Brisbane z10 row.

**9. TWO PROTOCOL DEFECTS, RECORDED AND DELIBERATELY NOT CHASED.** Brisbane z10 ran **n=8/10**, two
short of spec. Redcliffe z11 reported **`skip 10`** against `skip 0` in every other reading — ten
suppressed rebuilds, on the location carrying the headline result, cause unidentified (repeat pans
landing on an unchanged viewport is the benign explanation, untested). Neither can flip a verdict
resting on `ct —` plus a ±2 ms ΔRESID reconciliation, and Cleveland z11 at n=10/10 corroborates
Redcliffe independently. **Judgement: not worth a re-run. Recorded so a future session does not read
the numbers as clean.**

**10. NEXT: C3 NUMERIC BUCKET KEYS, UNCHANGED — and `_idwCache` PROMOTED TO SIT ALONGSIDE IT.** S3 is
now 84% of compute at Redcliffe (189.5/224.5), 89% at Brisbane (291.0/326.5) and 52% at Bargara
(151.5/290.5, with C1's 117.0 taking most of the rest). C3 is aimed correctly.

**`idw MISS` appears on every pan in all five readings.** The known `_idwCache` keyed on `s.length`
rather than `poolVersion` (long-standing low-priority backlog item) means the IDW structure is
rebuilt every single pan, and that cost lands in S3 — the same segment C3 targets. It is a smaller
edit than C3 and shares its measurement problem. **Re-rate it against C3 before dispatching either;
do not leave it at low priority.** Compare `six HIT` on the same line, which is the cache behaving.

**The 350 ms `moveend` debounce stays UNTOUCHED.** Compute medians are 224.5 / 326.5 / 208.5 / 290.5
— no location is under the ~200 ms threshold. Reasoning in v16.68.1 §H is unchanged.

**NEXT-SESSION NOTE:** build **2026.08.09c**, roadmap **v16.68.2**, repo head `b3a5195` at time of
writing (the v16.68.2 commit and its Pages run are UNAPPLIED/UNCONFIRMED unless Aaron says
otherwise). No code shipped this session. **The C2 early-out is confirmed firing on-device and §B is
retired** — the decider is `ct —` replacing `ct 360×360=130k`, not `C1 0.0`, which the pre-existing
empty-levels return produces by the same mechanism. Next job: **Step C3, numeric bucket keys** — but
**re-rate `_idwCache` (`s.length` vs `poolVersion`) against it first** (§10). **Binding on whichever
ships: S3 moved up to 119 ms between builds that touched nothing in S3 (§5), so C3 cannot be measured
by comparing S3 across pan sets — paired A/B at the same map centre, or an allocation counter.** The
Bargara → Moreton visible-break check is unobservable by construction and is not to be re-specified
(§7). The 350 ms `moveend` debounce stays UNTOUCHED.

---

*v16.68.1 · 9 Aug 2026 — C2 CONTOUR EARLY-OUT SHIPPED (+ dead `inWaterFast()` term deleted;
v16.68.1 adds the planning review, one caveat, three corrections to earlier entries). Build
bumped to **2026.08.09c**. Repo head `b0ddab9` at session start. Closes v16.66 §7 item 3. Two
changes, both in `buildAutoContours()`, both bit-exact by construction.*

**1. EARLY-OUT (`index.html:2889-2943`).** Skips the whole field build — the W×H IDW lookup loop,
`smoothField()`, and both typed-array allocations — when no contour level can exist. Placed after
`mLngMin` (which the pad needs) and before the `F`/`OK` allocation at `:2944`.

**The precondition is MAX-DEPTH, not "no samples in bbox".** v16.66 §7 item 3 proposed the bbox
test; it would never have fired at Redcliffe. Moreton contributes **9,228 mask-surviving samples**
to the 64,306-point pool, centred on Redcliffe — the viewport is full of samples. What is actually
true is that **every one of them is above LAT**: `data/moreton_bay_flats_v1.csv` (33,751 rows) runs
min -2.81 / **max -0.30, zero rows deeper than 0**. Same for both Sunshine Coast CSVs (max -0.10);
`brisbane_river_*` max 0.19 with 2 rows of 257,778 — which is why Brisbane z10 also read `C2 = 0.0`.
The bbox-membership test is KEPT as the free first filter, but max-d is what decides.

**Soundness (one-way, cannot suppress a contour that would have drawn):** the field is `num/den`
with weights `1/(dist²+1) > 0`, i.e. a convex combination of contributing sample depths, so
`mxD <= max(d)`. `v0` is floored at 0 (`:2969`), so `max(d) <= 0` ⇒ `mxD <= 0` ⇒ empty `levels` ⇒
the existing empty-levels return. It deliberately does NOT catch the "data exists but no level
crossed" case (`mnD > 0` with `v0` past `mxD`), which stays on the full path exactly as before.

**Pad = 240 m, exactly the 3×3 bucket probe's reach, not a safety guess.** A sample in cell `ci±1`
is at most TWO cell widths away on that axis; `cellLa = 120/mLat` and `cellLo = 120/mLngMin`, so two
cells is `240/mLat` and `240/mLngMin` degrees — computed from the same constants the buckets are
built from.

**Exit path is the existing teardown, verified byte-for-byte.** All six returns in
`buildAutoContours()` (`:2859, :2863, :2878, :2942, :2967, :2971`) end in the identical string
`{if(autoCtLayer){map.removeLayer(autoCtLayer);autoCtLayer=null;}return;}`. This was the one way the
build could visibly break — a pan from Bargara into Moreton stranding its contour layer on screen.

**2. DEAD `inWaterFast()` TERM DELETED (`index.html:2961`).** Was
`(den&&near<=R1&&(inWaterFast(feats,la,lo)||near<=R1))`; `near<=R1` was already required by the `&&`
to its left, so the OR was `(X||true)` for any X — the call ran and its result was discarded. Now
`(den&&near<=R1)`. `const feats=shadeMaskFeats()` became dead and was removed with it.
**`inWaterFast()` live call sites 4 → 3** (`:2820` tap-to-read, `:2840` deep-scan, `:3643` zone
readout); the function itself is byte-identical to HEAD. The stale claim in `scanlineMask()`'s
header naming four callers (`:1999-2003`) was amended — the only comment touched outside the edited
region, and `scanlineMask()`'s executable code is byte-identical.

**GATE — behavioural, PASS.** Harness `c2_gate.js` (11,946 bytes) at
`C:\Users\Az\AppData\Local\Temp\claude\D--Claude-Code\28754a1b-d748-4589-b1ee-605576418e89\scratchpad\`.
Baseline extracted programmatically via `git show b0ddab9:index.html` (`extract_baseline.ps1`),
never retyped; all app logic under test is SLICED VERBATIM from both files.

- **26 boxes** over a combined 52,929-point pool (Moreton 33,751 + MN 19,178, one pool spanning both
  regions as in the real app). **13 fired** (all Moreton/Redcliffe-like, max-d -0.30 to -0.84;
  pre-edit drew 0 polylines in every one). **13 did not fire** (all Maroochy/Noosa-like, max-d 3.53
  to 42.48, 15–43 polylines each) — **F, OK, levels and polyline geometry all bit-identical to
  pre-edit. 0 failures.**
- **The deletion was tested ADVERSARIALLY, not with a constant stub.** Pre-edit was run three times
  per box with `inWaterFast` forced always-true / always-false / deterministic pseudo-random — 52
  comparisons, all agreeing with each other and with post-edit. A stub returning `false` would have
  passed vacuously and proved nothing.
- **Pad honesty (`pad_check.js`, 5,780 bytes):** re-running all 26 boxes with `padM` substituted to
  0 changed **no** verdict. The pad is NOT exercised by the real corpus — the ±30% viewport
  expansion was doing the work I had attributed to it. It is conservative insurance justified by the
  reach argument, not a practically-triggered mechanism, and should be described that way.
- **`pad_boundary.js` (6,599 bytes)** walks a controlled probe across the reach with a sparse bed:
  cutover is exactly between **240 m (does not fire) and 250 m (fires)**, matching the two-cell
  reach. Caveat recorded: pre-edit drew nothing at every offset (a single dominating sample gives a
  locally constant field, so no level is crossed), so this locates the boundary but does not
  demonstrate the pad rescuing real geometry — consistent with `pad_check`'s 0/26.

**Build discipline:** `node --check` both blocks **exit=0 before AND after the bump** (block 2 is
byte-identical across the bump at 2,061,276 bytes, proving the bump touched only HTML outside the
script blocks). Leaflet body-only SHA-256 `db49d009…5641a` MATCH. Both `<style>` blocks
byte-identical to HEAD. `pir()`, `pip()`, `zoneAt()`, `ORDER`, `inWaterFast()`, `scanlineMask()`
code, the green-zone `dragend` safeguard and `spotsUnlocked` all byte-identical to HEAD by direct
string comparison. Diff scope: 6 hunks, +72/−10, at `:1052`, `:1091`, `:1999-2003`, `:2882`,
`:2889-2944`, `:2953-2961`. Step B overlay stays in, default OFF.

---

**v16.68.1 PLANNING REVIEW OF THE v16.68 BUILD — accepted, with one material caveat and three
corrections to earlier entries.**

**A. THE SAFETY ARGUMENT IS SOUND, checked independently rather than accepted.** The field is a
convex combination of contributing sample depths (weights `1/(dist²+1) > 0`), so `mxD <= max(d)`;
`v0` is floored at 0; therefore `max(d) <= 0` implies empty `levels` implies the pre-existing
return. One-way — it cannot remove geometry that would have drawn. The six-exit-path teardown
comparison closes the one way this build could have visibly broken. **The adversarial test of the
dead-term deletion is the right method and should be the pattern**: pre-edit was run with
`inWaterFast` forced always-true, always-false, and deterministic pseudo-random, 52 comparisons all
agreeing. A constant `false` stub would have passed vacuously and proved nothing.

**B. THE GATE PROVES SAFETY, NOT BENEFIT. The harness pool is not the runtime pool.** The gate ran
a 52,929-point pool = raw `moreton_bay_flats_v1.csv` (33,751) + MN (19,178). The pool that exists on
the phone is 64,306 with a *different composition*: legacy_unknown 20,533 + BR 9,420 + SC 5,947 +
Moreton **9,228 post-mask survivors** + MN 19,178. So the gate used the pre-mask Moreton file rather
than the survivors, and omitted legacy_unknown, BR and SC entirely. **legacy_unknown is unaudited for
depth sign.** If any point inside the Redcliffe box carries `d > 0` — a manually logged spot depth
would do it — the early-out does not fire and the ~130 ms saving evaporates. The change stays *safe*
either way; what is unproven is that it *fires*.

**Strong counter-evidence, explicitly not proof:** v16.66 §1 recorded `C2 = 0.0` at Redcliffe,
Cleveland and Brisbane, i.e. `levels` was empty. `levels` is empty iff `v0 >= mxD`, and with
`v0 = max(0, ceil(mnD/stepL)*stepL)` the ordinary route is `mxD <= 0` — exactly the early-out's
precondition. But a second route exists: `mnD > 0` with `v0` rounding up past `mxD` (e.g.
`mnD = 0.1`, `mxD = 0.4`, `stepL = 0.5` gives `v0 = 0.5 > 0.4`), which v16.68 deliberately does NOT
catch. So `C2 = 0` makes firing very likely without establishing it. **The on-phone run is the
decider, and a non-firing result is the §B case, not a defect — report the number, do not patch.**

**STANDING RULE PROMOTED: a gate that measures WHETHER an optimisation fires must use a corpus
matching the runtime pool's composition; a gate that measures only whether a change is SAFE may use
any corpus.** This session's gate was built to the second standard and read as though it met the
first.

**C. THE COMMENT AMENDMENT OUTSIDE THE EDITED REGION (`:1999-2003`) IS APPROVED.**
`scanlineMask()`'s header asserted `inWaterFast()` "keeps all four of its other callers …
`buildAutoContours()`' field loop …", which edit 2 made false. Shipping it would have told the next
session that the contour loop still calls `inWaterFast()` — the precise error this entry corrects in
§E. The test for future builds is narrow: **amend an out-of-region comment only when this diff makes
it assert something false about the code.** Not a general licence to tidy comments.

**D. PAD HONESTY — accepted as written, and do not upgrade the claim later.** `padM=240` is exactly
the 3×3 probe's two-cell reach, computed from the same `mLat`/`mLngMin` the buckets use. But
`pad_check.js` re-ran all 26 boxes at `padM=0` and changed **no verdict** — the ±30% viewport
expansion was doing the work. `pad_boundary.js` locates the cutover exactly between 240 m (does not
fire) and 250 m (fires), with the caveat that pre-edit drew nothing at any offset, so it locates the
boundary without demonstrating the pad rescuing real geometry. **Conservative insurance, correct and
near-free, not a practically-triggered mechanism.** Keep it; describe it that way.

**E. THREE CORRECTIONS TO EARLIER ENTRIES. All three are marked SUPERSEDED in place; this is the
authoritative statement.**

1. **v16.66 §7 item 3's precondition is FALSE.** "Skip the field build when the viewport contains no
   contourable samples" would never have fired at Redcliffe — Moreton contributes 9,228
   mask-surviving samples centred there. Had it been built as specified it would have shipped,
   gated, measured zero, and cost a full cycle. Superseded by the max-depth precondition.
2. **v16.67.1 §J item 1 is WRONG.** It claimed `buildAutoContours()`'s field loop "still runs the
   per-pixel `inWaterFast()` path" and might outrank C3. It never ran unconditionally — the call sat
   behind `den && near<=R1 &&` — and its result was discarded, because `near<=R1` was already true
   at that point, making the OR `(X||true)`. The correct action was deletion, done in v16.68. It
   never competed with C3.
3. **"C1 idx/field" UNDERCOUNTS ITS OWN SPAN.** Per the in-file comment, C1 = bucket index build +
   field loop + `smoothField`. The index half is `poolVersion`-cached and read `six HIT` in all
   seven v16.66 readings, so it costs ~0 — the label points at the wrong half. C1 was always the
   field loop plus `smoothField`. Read the C1 row that way in every prior entry.

**F. NEW FAILURE CLASS — a comment can record intent the code no longer implements.** The deleted
`NOTE` at the field loop explained, *accurately*, why `inWaterFast()` could never be the deciding
branch there. The comment was true; the call it described was dead compute. Reading a comment as
justification for code is not the same as verifying the code does anything. Where a comment explains
why a term cannot matter, check whether the term is still evaluated.

**G. ON-PHONE PROTOCOL FOR BUILD `2026.08.09c` — RUN 9 Aug 2026; RESULTS IN v16.68.2 §1.
Retained as written; three of its predictions are SUPERSEDED there (§4, §6, §7).** Force-close and
reopen, confirm `2026.08.09c` in-panel, overlay ON, 10 pans each at `n=10/10`:

| location / zoom | baseline (2026.08.09b or v16.66) | expected |
|---|---|---|
| Redcliffe z11 | C1 130.0, CT 130.0, total 670.0 | C1 → 0.0, CT → 0.0, total ~540 |
| Brisbane z10 | C1 186.5, CT 187.5 | C1 → 0.0, CT → 0.0 |
| Bargara z11 | C1 122.0, C2 8.5, CT 130.5 | unchanged, contours still drawn |

**When the early-out fires, `C1` and `CT` read `0.0` because the function returns before `_cm1` is
assigned — that is the return path, not a measurement.** Do not read `0.0` as the field build having
become infinitely fast. **The ~1 ms pool scan is now paid on every pan including Bargara, where it
never fires, and lands in `RESID` rather than `C1`** — a small RESID shift is expected and is not a
new mystery. **SUPERSEDED (v16.68.2 §6): the scan lands in `CT`, not `RESID`, and is
therefore directly measured at 1–2 ms rather than inferred.**

**THE ONE VISIBLE BREAK TO CHECK: pan Bargara → Moreton and confirm the contour layer DROPS rather
than stranding on screen.** Also confirm contours still draw normally at Bargara.
**SUPERSEDED (v16.68.2 §7): this check is unobservable by construction — any viewport triggering the
early-out also excludes the footprint of the geometry that could strand. The teardown is established
by the six-exit-path byte comparison above.**

**H. SEQUENCE UNCHANGED: C3 numeric bucket keys next, then the debounce.** `sIx[i2+':'+j2]`
allocates 9 transient strings per pixel in both the S3 and C1 loops — 1,166,400 per pan in the
contour loop alone at 360×360. Geography-independent, which is why it could never have explained the
gap, and now the largest remaining term. **The 350 ms `moveend` debounce stays UNTOUCHED** until
compute is under ~200 ms: the 351 ms is idle main thread, cutting it moves jank closer to the finger
rather than removing it, there is no in-flight guard to absorb the extra overlap, and it has no
dependency so it will never get harder. Improving `T1-T0` is the fastest way to move the totals
column without touching a millisecond of work — the shape of a metric being gamed, which this
project has already paid for once (v16.66 §8).


**NEXT-SESSION NOTE — SUPERSEDED by v16.68.2; retained for the record.** build **2026.08.09c**,
roadmap **v16.68.1**, repo head `fb27f98` at time of
writing (the v16.68.1 commit and its Pages run are UNAPPLIED/UNCONFIRMED unless Aaron says
otherwise). Shipped: C2 contour early-out + dead `inWaterFast()` term removed, both gated bit-exact
off-phone. **The on-phone run is the deliverable and has NOT happened** — protocol and expected
values in §G above. Two things to read carefully: `C1`/`CT` reading `0.0` is the return path, not a
measurement; and **if C1 is NOT ~0 at Redcliffe the early-out is not firing, which is the §B
runtime-pool case and not a defect — report the number, do not patch.** Confirm by panning Bargara →
Moreton that the contour layer drops rather than stranding. Next job after that: **Step C3, numeric
bucket keys** (§H). The 350 ms `moveend` debounce stays UNTOUCHED and deferred until compute is
under ~200 ms, then rated as its own change.

---

*v16.67.1 · 9 Aug 2026 — C1 SCANLINE WATER MASK SHIPPED (+ session record, gate re-derivation,
standing rules). Build bumped to **2026.08.09b**. Repo head `dcbc673` at session start. Closes v16.66 §7's C1 slot. **Canvas rasterisation is DROPPED to
fallback and was never implemented.**

**What shipped (`index.html:1992-2094` new, `index.html:2355` call site):** `scanlineMask()`
replaces the per-pixel `inWaterFast()` ray-cast in `buildShade()`'s pass-1 mask loop — and only
there. For a fixed row, `pir()`'s intercept term `(xj-xi)*(y-yi)/(yj-yi)+xi` does not depend on
`x`, so it is computed once per edge per row and every pixel is classified by the parity of the
intercepts strictly greater than its longitude.

**`pir()` and `pip()` are byte-identical to HEAD and are not called from the new code** — verified
by direct line comparison, not by diff inspection. `zoneAt()`, `ORDER` and `inWaterFast()` are
likewise byte-identical. The zone hard rule is untouched.

**`inWaterFast()` reference audit before the edit: 9 textual references — 1 declaration, 3 in
comments, 5 real call sites.** Only the `buildShade` mask loop changed. The other four keep the
per-pixel path unchanged: tap-to-read depth gate (`:2714` pre-edit), deep-scan loop (`:2734`),
`buildAutoContours()`'s field loop (`:2795` — C2, deliberately out of scope), zone readout
(`:3477`).

**GATE — 0 disagreeing pixels on every box.** The FINAL IN-FILE implementation was lifted back out
of `index.html` after the edit and diffed against the original per-pixel implementation:

- **144 boxes, 28,804,800 pixels compared, TOTAL DISAGREEING PIXELS: 0. Per-box worst case: 0.**
- W at **280 / 400 / 600** (47 / 49 / 48 boxes) — the whole clamp range, not 600 only.
- Targeted: CPZ21 Great Sandy Strait (149 rings), GUZ02 and MNP23 Peel Island (both
  MultiPolygons), HPZ02 Moreton Island to Broadwater (23 rings, blanketing bbox) — each at four
  aspect ratios × three W.
- 48 pseudo-random boxes spanning both regions, aspect 0.4–2.6, span 0.01–0.71°.
- Degenerate: 33 boxes 100% land, 3 boxes 100% water, open-ocean boxes east of every ring, and
  boxes north/south of the corpus's latitude extent (-27.9333..-24.4983) plus boxes straddling
  that edge so some rows intersect no edges at all and some do.

**Why it is exact, recorded so it is not re-litigated:** same expression, same operand order, same
`(yi>y)!=(yj>y)` guard, strict `<` preserved by advancing while `T[p] <= lo`. Nothing rearranged,
no cross-product form, no epsilon. Sorting cannot perturb the result — parity of a multiset is
order-independent and no float is accumulated. Two shortcuts, both exact and both consequences of
scanline order rather than added heuristics (**neither is the inner-ring bbox reject, which is not
in this build**): a ring with no crossing on a row produces no intercepts and could never toggle
`pir()`; and the per-pixel longitude test is dropped because the guard forces the interpolation
factor into [0,1], so every intercept lies inside the ring's own x-range — left of it all
intercepts exceed `lo` and a closed ring always has an even crossing count, right of it the count
is 0. The per-row latitude reject is kept.

**Allocation audit (measured, constraint 4):** 6 typed-array allocations on the first rebuild in a
page's life, then **2 per rebuild steady-state** — the mask (which the old loop also allocated)
plus the shared longitude table — and still 2 after a W change. Per-ring-per-row allocation was
specifically avoided: CPZ21 would have been 600 × 148 = 88,800 arrays per rebuild, i.e. v16.61's
GC-churn candidate re-entering by the back door.

**NO on-phone number yet, and the harness ms figures are NOT projections.** Per v16.66's own Item
1(c) the off-phone harness is uncalibrated — it disagreed with the phone by 3.14× at Bargara and
1.73× at Redcliffe on the same aspect, and the water-fraction hypothesis was falsified (water
pixels cost ~2× land pixels, so a water-heavier real box is dearer, not cheaper). The harness's
23.4×/41.0× and its 2.98×→1.70× ratio collapse are within-harness comparisons only. **The on-phone
gate produces the real number.** The 0-diff gate, by contrast, is exact and engine-independent.

**NEXT JOB — on-phone gate.** Panel → "⏱ Rebuild timing (diagnostic)" (still default OFF,
untouched by this build). Depth shading AND auto contours ON. **CORRECTED PROTOCOL — see §I
below; the z14 pairs originally written here have NO v16.66 baseline and cannot be compared.**
10 pans each at **Bargara z11 / Redcliffe z11 / Bargara z10 / Brisbane z10** — four screenshots
at `n=10/10`. **Read S2 specifically** against 105.0 / 504.0 / 205.5 / 366.5 ms medians. Also
confirm visually that the shading footprint is unchanged at a coastline — the gate is bit-exact
off-phone, but nothing has run on-device.

**Open, carried forward:** the `:2417` vs `:2251` half-pixel inconsistency between how the mask
samples (pixel centres on the bounds, `(W-1)` denominators) and how `L.imageOverlay` stretches the
image (pixel edges on the bounds) — pre-existing, deliberately untouched, logged separately.
~~`buildAutoContours()`'s field loop still runs the per-pixel path and is the obvious C2
candidate~~ — **SUPERSEDED by v16.68.1 §E2: that call was conditional and its result discarded;
the correct action was deletion, done in v16.68.**

---

**v16.67.1 SESSION RECORD — the reasoning that produced C1, recorded because three hypotheses were
killed on the way and none of them should be reopened.**

**A. STEP B2 (S2a/S2b SPLIT) — CANCELLED BEFORE BUILD. Do not re-scope it.** v16.66 §7 item 1 made
C1 conditional on splitting S2 to check whether `shadeMaskFeats()` was a large slice of the 504 ms.
A read of the file answered it without a build: `_shadeFeats` has exactly **four textual
references** in `index.html` — `let _shadeFeats=null` (`:1977`), the guard
`if(_shadeFeats)return _shadeFeats` (`:1979`), the assignment (`:1980`), the return (`:1984`).
**No reset path anywhere.** It is a permanent singleton built once per page life, so S2a would have
read `0.0` on every gesture of the protocol. Its one-off construction is attributed to C1's span in
any case, because the `buildAutoContours()` call site (`:2194`) runs before `buildShade()`'s S2
span. `poolVersion` would have been the WRONG cache key here — it tracks points/contours/imported,
none of which `shadeMaskFeats()` reads; keying on it would force a pointless rebuild after every
depth import. The B2 precondition was satisfied by evidence, not bypassed.

**B. THE 16.2x VERTEX RATIO WAS WRONG. The real figure is 3.87x.** The first harness counted
vertices by walking every bbox-surviving feature's rings without replicating the code's
short-circuits — `inWaterFast()` returns on the first accepting feature (`:1988-1989`) and `pip()`
skips inner rings unless the point is inside the outer (`:1324`). Those were **upper bounds on
work, not work done**. Instrumenting the actual control flow gives 58.4 verts/px at Bargara vs
226.3 at Redcliffe. **STANDING RULE: an instrumented counter must replicate every short-circuit in
the path it measures, or it reports a bound and not a measurement.** This is the second harness in
three sessions to make this class of error; dispatch prompts must say so explicitly.

**C. THE INNER-RING HYPOTHESIS IS FALSIFIED — the gap lives in the OUTER rings.** `pip()` applies
no bbox reject to inner rings, and the corpus looked like the perfect victim (CPZ21 149 rings,
GUZ01 34, HPZ02 23). Measured, inner rings are only **14.6% (Bargara) / 16.8% (Redcliffe)** of
scanned vertices. The geographic ratio is outer-ring: 188.3 vs 49.9 verts/px, 3.77x, essentially
the whole 3.87x total. The inner scans are near-pure waste (18 hole hits across 316,855
inside-outer tests at Bargara, **zero** at Redcliffe) but there is no money in them. HPZ02 is the
instructive case: 0 pixels inside its outer ring in the Redcliffe viewport despite a bbox that
blankets it — 3,037 vertices, holes never reached. That is a coarse-bbox failure and it is an
outer-ring problem.

**D. THE INNER-RING BBOX REJECT WAS BUILT, MEASURED, AND NOT SHIPPED.** Bit-exact (0/360,000 both
viewports), 1.45x at Bargara and 1.13x at Redcliffe — it **widens** the geographic ratio 1.82x ->
2.35x, optimising the arm that was already fine. It is also superseded: scanline removes the
per-pixel path entirely, leaving `zoneAt()` (one call per tap) as its only surviving beneficiary.
**Not to be revived.** A per-polygon outer-ring bbox reject on top was also tried and is slightly
WORSE (Bargara 194.6 vs 189.3 ms) — for the 176 single-polygon features the polygon bbox is the
feature bbox just tested. Dead end, recorded so nobody retries it.

**E. CANVAS RASTERISATION — DROPPED TO FALLBACK, NEVER IMPLEMENTED.** It was v16.66 §7 item 2 and
it was the plan until scanline measured. Canvas cannot be bit-exact by construction: it needs a
coastline threshold decision on antialiased edge pixels, per-polygon `evenodd` fills to preserve
union semantics (a single-path fill was measured to drop water the current code paints — Bargara
9 px, Great Sandy 7, Hays 2 — caused by cross-feature hole punch-through across 385 of 15,753 bbox
pairs), and an exact `(W-1)` + half-pixel transform. Scanline delivers the same complexity-class
change with a gate of **0 diff or it is a bug**. The scaling objection is real and is accepted, not
dismissed: scanline is O(rows x candidate edges) and degrades as the corpus grows where canvas
would not. **Revisit at the multi-region architecture spike (§7 item 7)**, which changes the
data-loading model anyway. Canvas stays on file as the fallback the bbox reject used to be.

**F. THE OFF-PHONE HARNESS IS UNCALIBRATED. Its ratios transfer; its milliseconds do not.** Against
the v16.66 on-phone medians the harness was 2.62x SLOWER at Bargara and at PARITY at Redcliffe. An
engine difference scales both arms alike, so this is workload, not JSC — "JSC amplifies it" is
withdrawn. Aspect was a genuine harness defect (it used a square 0.25 deg box; `buildShade()`
builds a square W x H grid over a non-square degree box — pool bbox padded 35% at `:2209-2210`,
intersected with the viewport expanded 30% per side at `:2215-2218`, `extM` taking `Math.max` of
the two extents at `:2222`, `H=W` at `:2223`, ~1.59:1 in practice). **Correcting it made the
absolute fit worse** — 3.14x and 1.73x, harness now slower on both arms. The water-fraction
hypothesis was tested and falsified in the direction that hurts: water pixels cost ~2x land pixels
(a land pixel is usually rejected by the feature bbox outright), so a water-heavier real box is
dearer, not cheaper. Best remaining candidate is **pool-bbox clipping** (`:2217-2218`), unmodelled
and asymmetric by construction — Bargara's pool is a narrow coastal strip, Redcliffe's fills the
bay — with the over-modelled arm being Bargara, which fits. Also live: guessed pan centres, and the
fact that a phone median over 10 varying boxes is not comparable to one fixed box. `W` is saturated
at 600 on both arms so the overlay yields only extM >= 21 km, a lower bound, not the box. **The
on-phone gate is the calibration.**

**G. GATE RE-DERIVED FROM A CLEAN BASELINE — and the first gate HAD drifted.** The shipped gate's
baseline was partly hand-made: `pir`/`pip`/`inWaterFast` were extracted, but `shadeMaskFeats` was
**hand-written** and the pre-edit mask loop was **retyped**. Re-running against the authentic
function failed instantly — the hand-written copy had invented `zid`/`name` fields the real
`shadeMaskFeats()` does not return (it returns `{polys,minx,miny,maxx,maxy}` only). Benign in
effect (the geometry never reads those fields) but proof that a retyped copy diverges silently.
Re-derivation: baseline extracted programmatically from `head_prev.html`
(`git show d903ba8~1:index.html`, SHA-256 `2A3A986E…1BC87C3`, 2,267,215 B, verified identical to
the blob), candidate extracted from the shipped `index.html`, harness written to a real file at
`D:\Claude Code\scratchpad\c1_gate.js` (12,913 B).

- **168 boxes, 32,702,400 pixels, TOTAL DISAGREEING PIXELS: 0. Per-box worst case: 0.**
- W 280/400/600 at 61/53/54 boxes; 72 random boxes across two seeds (24 never previously run).
- **`ZONES` asserted IDENTICAL across both files, with the harness halting on mismatch** — the
  shipped gate never checked this, and a differing corpus would have reported a hollow zero.
- `MNP23` occurs at ZONES indices **[101, 165]** (Garrys Anchorage AND Peel Island, the
  MultiPolygon). Both covered; a naive single-match selector covers only one.
- Degenerate: 46 boxes 100% land, 4 boxes 100% water, open-ocean east of every ring, north and
  south of the corpus latitude extent (-27.9333..-24.4983), and straddle boxes on those edges where
  some rows intersect no edges and some do.

**This validates the ARITHMETIC, not the INTEGRATION.** It proves `scanlineMask()` returns an
identical mask for any box. It does not exercise the `buildShade()` call site, `mAt`, or anything
downstream, and nothing has run on a device.

**H. STANDING RULES PROMOTED FROM THIS SESSION.**

1. **A gate's baseline must be extracted programmatically from a file on disk** — never retyped,
   never hand-written, never pasted from a transcript. Where a gate compares two implementations,
   the shared input corpus must be asserted identical across both sources, with the harness HALTING
   on mismatch rather than reporting a pass.
2. **A harness whose output gates a ship must be written to a real file, and its ABSOLUTE PATH
   reported.** Claude Code's session scratchpad is
   `%LOCALAPPDATA%\Temp\claude\<slug>\<session>\scratchpad`, NOT repo-relative — a repo-relative
   `Get-ChildItem` produces a false negative and cost this session a round trip. `scratchpad/` is
   now gitignored in-repo (`.gitignore:18`, commit `590824c`) for harnesses written there
   deliberately.
3. **Leaflet SHA-256 span is PINNED: BODY ONLY, excluding the `<script>`/`</script>` tags, expected
   `db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`.** The tags-included span is
   `156fc90aa436d569480491a5009458ac1375630726e3fe096059305f6565fc58`. Two sessions hashing
   different spans of identical bytes would report a false corruption alarm.
4. **Instrumented counters must replicate the measured path's short-circuits** (see §B).

**I. CORRECTED ON-PHONE PROTOCOL — the NEXT JOB paragraph above originally specified z14 and that
was wrong.** v16.66's protocol ran z11/z10, so **no z14 baseline exists and none can now be
captured** — the pre-C1 code is shipped over. Treat the z14 data point as a permanent loss; it was
worth ~87 ms extrapolated and was already flagged marginal in v16.66 §6. Run instead, 10 pans each,
`n=10/10`, four screenshots, reading **S2**:

| location / zoom | v16.66 S2 baseline (median ms) |
|---|---|
| Bargara z11 | 105.0 |
| Redcliffe z11 | 504.0 |
| Bargara z10 | 205.5 (mean of 216.5 / 194.5) |
| Brisbane z10 | 366.5 |

(Cleveland z11 538.5 is n=6 and stays corroborating-only.) Plus a visual coastline check — nothing
has run on-device. Watch whether **S3 becomes the top segment** and whether the Redcliffe/Bargara
ratio **inverts**; an inversion is the confirmation, not a regression.

**J. DEFERRED OPTIMISATIONS, logged not scoped. None to be built before the on-phone number
exists.**

1. **SUPERSEDED — WRONG, see v16.68.1 §E2.** The call was never unconditional (it sat behind
   `den && near<=R1 &&`) and its result was discarded, because `near<=R1` was already true there,
   making the OR `(X||true)`. Deletion was the correct action and shipped in v16.68; it never
   competed with C3. Original text kept below for the record. ~~**`buildAutoContours()`'s field
   loop still runs the per-pixel `inWaterFast()` path**~~ over the
   360x360 contour grid (129,600 px) against the same outer rings. Post-edit call site `:2898`. The
   same scanline transformation applies. On the Redcliffe arm this is plausibly worth more than C3
   numeric bucket keys — C1's span measured 118–191 ms per pan. **Re-sequence §7 to put this ahead
   of C3** if the on-phone S2 result confirms the shade-side win.
2. **`scanlineMask()`'s x loop runs all W pixels per polygon per row**, even where the polygon's
   intercepts span a narrow longitude range. Bounding the walk to [first intercept, last intercept]
   would cut the residual per-pixel term.
3. **`slFit()`'s corpus scan (~34k iterations) runs every rebuild** and could be hoisted into
   `_shadeFeats` alongside the feature bboxes.
4. Buffer sizing in `scanlineMask()` is EXACT with zero slack (`_slT` is sized to max
   `sum(ring.length)` per polygon; each ring yields at most one intercept per edge). Correct, but
   any future change to ring storage has no headroom to absorb — re-check `slFit()` if that
   changes.
5. `slSort()` insertion sort cannot regress on this corpus: break-even against the loop it replaces
   needs ~1,595 crossings on a single row of HPZ02's 2,119-vertex outer ring, i.e. 797 water/land
   alternations across one horizontal line. Geometrically impossible here. The "typically 2
   intercepts" claim is not load-bearing.

**K. PROCESS NOTE — Claude Code self-authored the v16.67 roadmap entry unprompted.** The dispatch
did not ask for it. Content is accurate and it correctly kept the uncalibrated harness figures out
as projections, but rev D puts roadmap deltas in the planning chat, and this bypassed that. Named
so it does not become habit. Related and unresolved: the `.gitignore` commit printed "Enumerating
objects: 214" for a one-line change — a hook or mid-commit repack. Harmless here (the push moved 3
objects / 355 B) but worth identifying before it appears during a build commit.

**NEXT-SESSION NOTE:** build **2026.08.09b**, committed on top of `dcbc673` (`d903ba8` = C1 build +
v16.67 entry; `590824c` = `.gitignore scratchpad/`). Shipped: C1 scanline water mask, gated at
**0 disagreeing pixels across 168 boxes / 32,702,400 px** from a programmatically-extracted pre-C1
baseline (§G supersedes the 144-box / 28,804,800-px figure recorded before the re-derivation).
Recommended next job: **run the on-phone protocol in §I and read S2 — no further optimisation until
that number exists.** Pending cleanup: confirm the Pages run for `d903ba8`, commit and push this
v16.67.1 entry, confirm its Pages run, and re-upload the committed file to project knowledge. `mA`
remains dead code by instruction (v16.66 §7 item 5).

---

*v16.66 · 9 Aug 2026 — **STEP B NUMBERS LANDED. THE GAP IS SOLVED.** Planning/analysis only, no
build, no code. Build stays **2026.08.09a**. Repo head `6762ffc` (v16.65 build + roadmap) at session
start. Seven on-phone screenshots from the 2026.08.09a instrumentation overlay. **v16.61 candidate
(a) — per-pixel `inWaterFast()` polygon complexity — is CONFIRMED as the entire geographic gap.
Candidate (b) — local IDW bucket occupancy — is FALSIFIED, and moves in the wrong direction.**

**1. THE MEASUREMENT. Seven readings, median ms, transcribed from the overlay.**

Six at `n=10/10`; one (Cleveland z11) at `n=6/10` and therefore corroborating only, not load-bearing.
Protocol ran at z11/z10 rather than the specified z14/z11 — see §5. `sh 600×600=360k` and
`ct 360×360=130k` in **all seven**, so shade grid size is constant and cannot explain any variance.
`pool 64306`, `six HIT`, `idw MISS`, `skip 0`, `pre 0` in all seven — no cache or edge-case confound.

| reading | n | idle | comp | paint | total | S2 | S3 | S5 | RESID | C1 | C2 | CT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bargara z11 (img1) | 10 | 351.0 | 509.0 | 2.0 | 865.5 | **105.0** | 268.0 | 8.0 | 124.5 | 118.0 | 9.0 | 124.0 |
| Bargara z11 (img4) | 10 | 351.0 | 513.5 | 3.5 | 868.0 | **105.0** | 273.0 | 8.0 | 127.5 | 119.5 | 8.5 | 127.0 |
| Bargara z10 (img6) | 10 | 351.0 | 764.0 | 2.0 | 1118.0 | **216.5** | 276.5 | 6.0 | 196.0 | 191.0 | 6.5 | 195.0 |
| Bargara z10 (img7) | 10 | 351.0 | 677.0 | 2.5 | 1034.0 | **194.5** | 286.5 | 6.0 | 191.5 | 183.0 | 7.0 | 190.5 |
| Redcliffe z11 (img5) | 10 | 351.5 | 808.5 | 3.5 | 1167.5 | **504.0** | 151.0 | 6.0 | 130.5 | 130.0 | 0.0 | 130.0 |
| Cleveland z11 (img3) | 6 | 353.5 | 956.5 | 13.5 | 1324.0 | **538.5** | 281.0 | 9.0 | 139.5 | 138.5 | 0.0 | 139.0 |
| Brisbane z10 (img2) | 10 | 351.0 | 837.5 | 3.0 | 1203.5 | **366.5** | 273.0 | 6.0 | 187.5 | 186.5 | 0.0 | 187.5 |

S1 is 0.0 in all seven (max 1.0–3.0) and S4 is 1.0–1.5. Both are noise; neither is ever worth
another look. `enc` is 4.5–5.0 of S5's 6.0–9.0 — the synchronous `toDataURL()` PNG encode is real
but trivial, and is now closed as a suspect.

**2. S2 IS THE GAP. Like-for-like at z11, Bargara (mean of two runs) vs Redcliffe:**

```
  S2 mask    105.0 -> 504.0   delta +399.0   ratio 4.80x
  S3 idw     270.5 -> 151.0   delta -119.5   ratio 0.56x
  S5 paint     8.0 ->   6.0   delta   -2.0
  CT total   125.5 -> 130.0   delta   +4.5
  ------------------------------------------------------
  T2-T1      511.2 -> 808.5   delta +297.2
  sum of segment deltas = +282.0  (15.2 ms apart; medians drawn from different gesture sets)
```

**S2's delta alone (+399.0) EXCEEDS the entire compute gap (+297.2)** — S3 runs the other way and
partially cancels it. Same finding at z10, Bargara (mean of two) vs Brisbane: S2 205.5 -> 366.5
(+161.0, 1.78x) against a compute delta of +117.0, with S3 flat at 281.5 -> 273.0 (-8.5).

S2 as a share of compute: **Bargara 20.4–28.7%, Moreton 43.8–62.3%.** The mask pass is a fifth of
the work on the reference coast and up to five-eighths of it in Moreton Bay. That is the whole story.

**3. CANDIDATE (b) IS FALSIFIED — do not reopen it.** S3 across all seven: Bargara 268.0 / 273.0 /
276.5 / 286.5; Moreton 151.0 / 273.0 / 281.0. The ranges fully overlap and the **fastest S3 in the
entire set is Moreton's** (151.0, Redcliffe z11). Sparse local buckets make the IDW loop cheaper,
not dearer, so bucket occupancy cannot generate a gap in the observed direction under any reading.
The v16.61 §1 candidate list is now closed: (a) confirmed, (b) dead, (c) GC churn untested but
demoted — it is geography-independent by construction and there is no longer an unexplained
geographic residue for it to account for.

**4. TWO HYPOTHESES THIS SESSION KILLED, INCLUDING ONE OF THIS CHAT'S OWN.**

- **T3 paint is not the problem.** `T3-T2` is 2.0–13.5 ms median, 11.0–29.0 max. The v16.65-era
  argument that asynchronous PNG decode might sit wholly outside S1–S5 and explain the visible
  absence was wrong. It cost two boundary marks to falsify and was worth it — the alternative was
  carrying it as a live unknown into the fix.
- **There is no hidden term.** `RESID - CT` = **+0.0 to +1.0 ms in all seven readings**. The
  segmentation accounts for essentially 100% of `T2-T1`. Any future claim that "something else" is
  costing time in the shade rebuild has to explain how it hides inside a 1 ms residual.

Also settled: `T1-T0` is 351.0–353.5 median (max 351.0–386.0) in every reading. The 350 ms trailing
debounce is exact and invariant. The three-timestamp split (v16.65 §2) earned its keep by proving
the idle term is not a variable — every ms of the 865–1324 ms user-visible total above 351 is
compute.

**5. NEW FINDING, UNSOUGHT: `C2 = 0.0` AT EVERY MORETON READING.** The marching-squares/polyline/
layer-add stage produces literally zero geometry in Moreton Bay (correct — the Option 3 STRICT-AND
mask leaves no depth samples over that water), yet `C1` still spends **130.0 / 138.5 / 186.5 ms**
per pan building a 130k-cell field for it. At Bargara, where contours are real, C2 is 6.5–9.0 and
the work is earned. This is a pure-waste term available **only in the slow arm**, i.e. it improves
the gap as well as the absolute. Requires a cheap, correct precondition — "no samples in the
contour viewport bbox", not "C2 was 0 last time"; C2 can legitimately be 0 when data exists but no
level is crossed, and an early-out keyed on that would silently drop real contours.

**6. PROTOCOL DEVIATIONS — recorded, neither invalidating.**

- **z11/z10 was run, not the specified z14/z11.** The finding generalises regardless: S2 and S3 are
  both linear in W·H, so at any grid size the *ratio* between them is preserved. But the tight-zoom
  regime is now genuinely unmeasured. At z14 the shade grid is `clamp(280,600,extM/35)` = 280×280 =
  78,400 px, i.e. 4.59x fewer pixels, extrapolating to S2 ≈ 22.9 ms (Bargara) vs ≈ 109.8 ms
  (Moreton) — an **~87 ms absolute gap, which is marginal as a subjective full point**. Either the
  tight-zoom rating was less reliable than v16.61 assumed, or a second mechanism operates there.
  Capture one z14 pair opportunistically; not a blocker for Step C.
- **Cleveland z11 (img3) is `n=6/10`.** Consistent with Redcliffe z11 and therefore corroborating,
  but it must not be quoted as a primary figure.

**7. STEP C — THE FIX. Ordered, one variable per build.**

**Projected end state at z11** (S2 -> ~10 ms via rasterisation; Moreton CT -> ~0 via early-out):

```
  Bargara    comp  509.0 ->  414.0    total   865.5 ->  ~767 ms
  Redcliffe  comp  808.5 ->  184.5    total  1167.5 ->  ~540 ms
```

The gap does not close — **it inverts**, and S3 (268–286 ms at Bargara, untouched by any of this)
becomes the new ceiling. Plan for that; do not treat an inverted gap as a regression.

1. **STEP B2 — SPLIT S2. Instrumentation only, two marks, Sonnet. DO THIS FIRST.** The S2 span as
   built includes `shadeMaskFeats()` as well as the pixel loop. If feature assembly is a large slice
   of the 504 ms, canvas rasterisation buys far less than projected and a cycle has been spent on
   output-critical code. The evidence favours the pixel loop dominating — Moreton S2 *fell* 504.0
   (z11) -> 366.5 (z10) despite more polygons entering view, which is a per-pixel signature, not a
   feature-count one — but that is inference, not measurement, and the mask is the one component
   whose breakage is not cosmetic. Split into **S2a (`shadeMaskFeats()`)** and **S2b (pixel loop)**,
   then a 20-gesture run: Bargara z11 and Redcliffe z11 only. Cheap insurance, not a coin flip.
2. **STEP C1 — RASTERISE THE MASK.** Replace the 360,000-iteration JS point-in-polygon loop with a
   native canvas fill: draw the mask polygons into an offscreen 600×600 context, `getImageData`
   once, threshold to the existing binary `mask` array. The browser rasteriser is native code doing
   in single-digit ms what the JS loop does in 105–538. **Output-identity risk is real and must be
   gated:** polygon antialiasing at edges means the thresholded result can differ by a pixel or two
   from the PIP result. Verify by diffing the `mask` arrays for both geographies before trusting it,
   and treat any edge disagreement as a decision to make deliberately, not a rounding detail.
   Conditional on B2 showing S2b dominant.
3. **STEP C2 — CONTOUR EARLY-OUT** (§5). **SHIPPED v16.68 — but the precondition stated here is
   FALSE and was corrected before build; see v16.68.1 §E1.** ~~Skip the field build when the
   viewport contains no contourable samples~~ — Redcliffe is full of samples (9,228 mask-surviving
   Moreton points); the working precondition is **max sample depth ≤ 0 over the padded box**.
   ~130–187 ms per pan in Moreton, ~0 at Bargara.
4. **STEP C3 — NUMERIC BUCKET KEYS.** v16.65's optimisation candidate 2: `sIx[i2+':'+j2]` allocates
   a transient string per bucket probe, 9 per pixel, in both the S3 and C1 loops. Geography-
   independent, so it could never have explained the gap — but after C1/C2 it is the largest
   remaining term (S3 268–286 ms at Bargara). Deferred to last precisely because it is the one item
   whose benefit does not depend on the others.
5. **Dead `mA` removal** (v16.65 candidate 1) stays unactioned. It is real but small, and it touches
   the alpha path. Not worth a build of its own; fold into C3 only if C3 already opens that loop.

**8. STANDING ADDITION — SUBJECTIVE RATING IS RETIRED FOR THIS CLASS OF PROBLEM.** The /5 pan-
smoothness scale saturated twice (v16.61, v16.64) and produced one actively misleading reading (the
confounded 2.8/2.8 in v16.64 §1). A single instrumented build resolved in one on-phone run what four
sessions of rating could not. **Where a symptom has a plausible per-stage decomposition, instrument
before rating.** The overlay from 2026.08.09a stays in the build and is the tool for it.

**NEXT-SESSION NOTE:** build **2026.08.09a**, repo head `6762ffc` at session start, roadmap
**v16.66** UNAPPLIED at time of writing. Nothing shipped this session — analysis only. Decided:
S2 is the gap (4.80x at z11), candidate (b) falsified, paint and hidden-residual hypotheses both
killed, contour build is pure waste in Moreton. Next job: **Step B2, the S2a/S2b split** (§7 item 1)
— instrumentation only, Sonnet, then a 20-gesture run at Bargara z11 + Redcliffe z11. Do not build
the rasterisation fix before that split reports. Pending cleanup: commit and push this roadmap entry
on its own before any build commit, and confirm the Pages run.

---

*v16.65 · 9 Aug 2026 — STEP B MEASUREMENT BUILD SHIPPED (instrumentation only, no behaviour
change). Build bumped to **2026.08.09a**. Repo head `6e85fc7` at session start. This is §7 item 2
of v16.64 below, as amended. **THE NUMBERS DO NOT EXIST YET — nothing has been measured. This build
only makes measurement possible; the on-phone run is the deliverable and it is the next job.**

**What shipped (`index.html`, one new block + fourteen boundary marks):**

- **Timestamps.** `T0` last `moveend` before the 350 ms trailing debounce elapsed · `T1`
  `buildShade()` entry · `T2` code-level swap complete · `T3` `imageOverlay` `'load'` — the PNG
  actually decoded and painted. Overlay reports T1−T0, T2−T1, **T3−T2**, T3−T0. T3−T2 has never
  been measured before and is carried as a first-class row, not a footnote.
- **Segments.** `buildShade()`: S1 samples+bounds+index, S2 mask pass, S3 IDW pixel loop, S4
  `smoothField`, S5 canvas paint **including `cv.toDataURL()`**, plus a sub-row `of which enc` —
  the synchronous PNG encode of W·H px alone, split out because it had never once been measured.
  `buildAutoContours()`: C1 index+field, C2 marching-squares+polyline+layer-add, CT total (timed
  at the **call site**, so it covers that function's own early returns).
- **Per gesture:** shade W/H/W·H, contour W/H/W·H, `depthSamples().length`, `map.getZoom()` to 1 dp,
  and two cache states (`six`, `idw` — see the correction below).
- **Aggregation:** rolling window of the last 10 gestures, **median and max** per segment, with a
  live `n=k/10` so a screenshot taken early is self-evidently incomplete. Median/max/window/
  double-commit behaviour was exercised headlessly against the block lifted verbatim from the
  file (odd-n, even-n, oldest-drop, duplicate-commit) before commit.
- **Overlay:** `#perf-box`, top-right at `top:150px` (clears the zoom control in both the desktop
  and the `max-width:600px` layout; nowhere near the bottom-right scale bar / zoom readout /
  attribution that v16.63 settled). Monospace, tabular figures, 1 dp, 19 compact rows.
  `pointer-events:none`; the only interactive control is the `#perf-toggle` checkbox in the panel.
  Prints the build string, **read from the panel header** rather than duplicated — a third copy
  would be a third thing to drift.
- **Gating.** Collection and display share one flag, default OFF. With it off `perfBegin()` returns
  `null` on its first line and `perfT0` is never set: no clock read, no record allocated, no DOM
  node. **In-memory only — nothing is written to localStorage** (headroom is 1,024–2,047 KiB).

**Discipline held:** not one `performance.now()` sits inside a per-pixel or per-cell loop body
(all 17 call sites audited; S3 alone runs to 360,000 iterations, so a mark in there would have been
the largest thing measured). No change to grid sizing, sample selection, alpha curve, contour
interval, layer ordering, or v16.62's add-before-remove swap order. The overlay's own DOM write
happens in `perfCommit()`, reached from the `'load'` handler or the flush task — after T3, outside
every timed span. Leaflet block and first `<style>` block byte-identical
(sha256 `156fc90a…6565fc58` and `fa8029b4…60c019e4`, unchanged); both script blocks `node --check`
exit 0. `zoneAt()` most-protective ordering and the green-zone drag safeguard verified intact.

**One deliberate code move:** `cv.toDataURL()` was hoisted out of the `L.imageOverlay(...)` argument
list into `const _url` so the encode could get its own boundary mark. Identical value, identical
evaluation order — it was already the first argument evaluated.

**CORRECTION TO THE BRIEF — `_idwCache` is not the cache that governs S1.** The brief asked for
`_idwCache` HIT/MISS on the grounds that its `s.length` key can collide and make S1 spuriously
fast. That key weakness is real (it stays on the low-priority list), **but `_idwCache` is not on
buildShade's path at all**: `buildShade()` nulls it on its own first line and never repopulates it
— only `idwIndex()` (tap-to-read) does. The index S1 actually pays for or skips is
`pooledSampleIndex()`'s `poolVersion`-keyed `_sampleIndexCache`. Both are therefore reported:
**`six`** is the governing one, read at its call site immediately *before* the call (reading it
after would make every gesture a HIT), and **`idw`** is `_idwCache`'s state at T1 as asked. On a
pure pan sequence `idw` should read MISS every time; if it ever reads HIT, something called
`idwIndex()` mid-protocol and that gesture is not a clean pan.

**Two honest caveats on how to read the overlay:**

- **S1 is split, not contiguous.** "samples + bounds + index build" straddles the mask pass in the
  existing code order (samples/bounds/canvas → mask → `pooledSampleIndex` + r0 precompute), so it
  is measured as two spans and summed. Segments were fitted to the code; the code was not reordered
  to fit the segments. S1a also carries the canvas/`ImageData` allocation (600×600 `ImageData` is
  1.44 MB) and S1b also carries the r0 precompute (itself cached on `_r0Version`, so ≈0 on a pan
  that didn't change the pool — a non-zero S1b means that cache missed).
- **`RESID(+CT)` includes the whole nested contour build.** `buildAutoContours()`'s call site sits
  *above* the S1 start mark, so S1–S5 exclude CT entirely and CT falls wholly inside
  `RESID = (T2−T1) − (S1+S2+S3+S4+S5)`. Subtract CT from RESID for the genuinely unaccounted time.
  **A large residual is a finding, not an instrumentation bug** — do not re-cut the segments to
  shrink it.

**Edge cases instrumented rather than swallowed:** a gesture whose `imageOverlay` had already
loaded by bind time records T3−T2 = 0 and increments `pre`; one where no `load` ever arrives is
committed at 0 after 2 s and increments `noload`; one that never reached the swap (shade off,
`pts<3`, degenerate clip, throw) is excluded from the medians and increments `skip`. All three
counters are on screen, so no sample is silently dropped and a screenshot shows if any fired.

**Three optimisation candidates spotted while instrumenting. Code left alone, as instructed —
these are Step C material and must not be touched before the numbers land:**

1. **`mA` in the IDW pixel loop is dead weight.** The existing v16.47 comment already says so: the
   9-tap mask average can no longer change the painted result (`distA` zeroes `AL` when
   `near ≥ R1`, and `near < R1` forces `maskA = 1`). That is ~9 array reads + 9 adds per pixel,
   ~3.2 M redundant ops per 600×600 rebuild.
2. **String-keyed bucket lookup.** `sIx[i2+':'+j2]` builds a fresh string key per bucket probe — 9
   per pixel, in *both* the S3 loop and the C1 loop. At 360,000 px that is ~3.2 M transient string
   allocations per shade rebuild. Prime candidate for v16.61's GC-churn hypothesis (c), and it is
   geography-independent, so on its own it still cannot explain the Bargara/Brisbane gap.
3. **S2's per-pixel `inWaterFast()`** is exactly v16.61 candidate (a) — the one that *is*
   geography-dependent (Moreton's polygon complexity vs Woongarra's). S2 is now measured directly,
   so this hypothesis is finally falsifiable rather than argued.

**NEXT JOB — run the protocol, do not patch anything first.** Panel → tick "⏱ Rebuild timing
(diagnostic)" (ticking it ON clears the window, so `n` restarts at 0/10). Depth shading AND auto
contours both ON. Then: 10 pans at Bargara z14, 10 at Bargara z11, 10 at Redcliffe/Hays z14, 10 at
Redcliffe/Hays z11 — **four screenshots, forty gestures**, each screenshot taken only at `n=10/10`.
Collapse the panel before screenshotting (an expanded panel covers the overlay, same as it already
covers the zoom control). Portrait only — 19 rows at `top:150px` will clip in landscape on a short
viewport.

**Not verified on-device this session** (no phone access): the overlay's real position and that it
fits an iPhone screenshot uncropped are reasoned from the CSS/DOM layout, not confirmed against an
actual narrow-viewport screenshot. If it clips, lower `top:150px` before running the protocol —
that is a one-line CSS change, not a re-measure.

**NEXT-SESSION NOTE:** build **2026.08.09a**, committed on top of `6e85fc7`. Shipped: Step B `performance.now()`
instrumentation (T0–T3, S1–S5+enc, C1/C2/CT, median+max over the last 10 gestures, on-screen
overlay default OFF, in-memory only). Recommended next job: **run the forty-gesture on-phone
protocol above and paste the four screenshots — no code changes until those numbers exist.** Then
§7 item 3 (jitter fix), scoped by what the numbers actually say. Pending cleanup: none from this
build; the three optimisation candidates above are deliberately unactioned.

---

*v16.64 · 9 Aug 2026 — planning only, no build, no code. Build stays **2026.08.07a**. Repo head
`40835f6` at session start; roadmap version verified by direct `project_knowledge_search` at the
top of the session (found v16.61 on project knowledge, v16.62/v16.63 committed by the build
sessions in between — PK was four days stale, see the repo-hygiene note below). **v16.62 and
v16.63 both GATED ON-PHONE AND CLOSED. The gate result REOPENS the geographic asymmetry that
v16.61 §1 raised and that this session's own earlier re-gate appeared to falsify.**

---

**1. ON-PHONE GATE ON v16.62 (atomic overlay swap) — PASS. Item closed.**

Build `2026.08.06a`, both layers ON. No blanking at either location at any zoom tested; toggle-off
still immediate, so the rewritten `!shadeOn`/`!autoCtOn` branches did not regress. Subjective /5
against the pre-fix v16.60 baseline, at ~1–2 km scale:

| location | v16.60 | v16.62 | Δ |
|---|---|---|---|
| Bargara | 2.8 | ~3.8 | **+1.0** |
| Brisbane/Hays | 2.8 | 3.0 | +0.2 |

**Wide-zoom rows completed** (z11 or lower — shade pinned at its 600×600 cap, 360,000 px; contours
at 360×360): Bargara 3.5–4, Brisbane/Hays 2.5–3, **NO BLANKING at either**. Worst-case rebuild
confirmed gap-free. 4.6× the pixel work vs the tight-zoom rows moved neither score materially,
while the ~1-point Bargara/Brisbane gap persisted at both zooms. **Do not read that as evidence
against the per-pixel candidates** — a subjective /5 saturates, and flat scores across 4.6× pixels
are equally consistent with both locations already sitting past the annoyance threshold. The
rating scale has reached its resolution limit; that is the argument for measurement, not against
the hypotheses.

**THE EARLIER FALSIFICATION WAS CONFOUNDED, NOT WRONG.** Earlier the same session, a re-gate with
zoom held constant returned 2.8/2.8 (both-off 4.5/4.5, depths-only 3.5/3.5) and was read as
falsifying the Bargara-vs-Brisbane difference outright. It does not. The blanking was a large
**geography-independent** cost sitting on top of both locations, and it dominated hard enough to
flatten them to an identical score. Remove it and Bargara gains a full point while Brisbane barely
moves. **v16.61 §1's candidates (a) per-pixel `inWaterFast()` scaling with Moreton's polygon
complexity and (b) local IDW bucket occupancy are back on the table as the live hypotheses.**
Candidate (c) `smoothField` GC churn is unchanged in status — geography-independent, so it can
never explain the gap on its own.

**Standing lesson:** a controlled comparison is only valid once the *dominant* confounder is
removed. Controlling zoom was necessary but not sufficient — a second, larger confounder sat
underneath it and inverted the conclusion. Before treating any future A/B as decisive, ask what
else is common to both arms and larger than the effect being measured.

**Additional signal, not yet explained:** Bargara degrades noticeably from ~1–2 km scale to z11;
Brisbane does not. If pixel count (280²→600², ~4.6×) were the sole driver both should degrade
together. Brisbane appears already saturated at the tighter zoom by something not pixel-scaled.
Do not theorise further — this is exactly what Step B measures.

---

**2. HOW THE DIAGNOSIS WAS REACHED (two read-only steps, no code changed).**

Recorded because the *route* matters more than the answer: v16.61 §1 nominated three compute-cost
candidates and the real defect was none of them.

- **Step A** — `buildShade()` is bound to `moveend` with a 350 ms trailing debounce
  (`index.html:3198-3200`), NOT a raw `move` binding. It therefore provably does not run during
  the drag at all, ruling out per-frame rebuild as the mechanism. `buildAutoContours()` has no
  separate map binding; it is invoked inside `buildShade()` and rides the same trigger.
  `pooledSampleIndex()` is a genuine cache hit on the nested call, so the bucket index is built
  once per gesture, not twice.
- **Step A2** — neither overlay repositions per-frame during a pan either; both ride the shared
  `mapPane` CSS transform. Only Leaflet's own `Canvas._update` fires on `moveend` to resize and
  redraw existing contour paths, independent of our debounce. **The actual defect:** both
  functions removed the existing overlay/layer at the START of every rebuild, before the
  replacement existed — a destroy-then-rebuild gap, ~187 lines of compute wide in `buildShade()`,
  with no `try`/`catch` around the intervening span.
- **The user-visible symptom was never "jitter."** Drag was smooth; both overlays went ABSENT for
  ~1–2 s after each pan settled. 350 ms of that was the debounce, the rest real rebuild time.
  Every candidate in v16.61 §1 was an answer to "why is each frame slow" — the wrong question.

**Process note:** the phone report that produced this was one question — "is it jittery while your
finger is down, or is there a hitch after it settles?" That single discriminator was worth more
than the entire three-candidate compute analysis it replaced.

---

**3. CORRECTION TO v16.61 §1 — TWO GRIDS, NOT ONE.**

§1 attributed `W`/`H` = `clamp(110,360,extM/60)` to the mask pass and quoted "up to 360×360 =
129,600 point-in-polygon tests per pan". **That is `buildAutoContours()`'s grid.** `buildShade()`
sizes itself independently:

- `buildShade()`: `Math.max(280,Math.min(600,Math.round(extM/35)))` → **78,400 – 360,000 px**
- `buildAutoContours()`: `Math.max(110,Math.min(360,Math.round(extM/60)))` → 12,100 – 129,600 px

Shade's grid is up to 2.8× larger, and its floor (78,400 px) is 6.5× the contour floor. **Any
figure in §1 derived from the 110–360 grid for shading work is wrong.**

**Per-pan typed-array allocation volume** (from Step A4's inventory of 11 W×H-sized allocations —
7 in `buildShade`: ImageData, mask, FD, AL, ST, 2× `smoothField` swap buffers; 4 in
`buildAutoContours`: F, OK, 2× `smoothField`):

- At the floor (shade 280², contours 110²): 1,724,800 B + 157,300 B ≈ **1.88 MB per pan**
- At the cap (shade 600², contours 360²): 7,920,000 B + 1,684,800 B ≈ **9.6 MB per pan**

---

**4. ACCEPTED RISK INTRODUCED BY v16.62 — observability regression, logged not fixed.**

Both rebuild paths now sit inside a silent `catch(e){}`. A throw mid-rebuild leaves the stale
overlay displayed with no signal of any kind. This app has form here: **v16.38's
`Math.max.apply` RangeError at the iOS JSC argument ceiling, which desktop never reproduced.** If
pool growth re-triggers that class, shading will silently stop updating rather than failing
visibly. **Not a field-safety issue** — `imageOverlay` is bounds-anchored, so a stale overlay
cannot display depths at the wrong coordinates. A future build should surface the catch via
`console.warn` plus the existing `#imp-save-err` banner slot. Low priority, but do not let it
become invisible.

**Expected, not a bug:** `autoCtRenderer` is a single persistent `L.canvas` reused across
rebuilds, so during the swap window both the new and the old layer group are attached to it.
Momentarily doubled or thicker contour lines are the correct trade for not blanking — do not
report that as a regression.

---

**5. ON-PHONE GATE ON v16.63 (map control layout) — PASS. Item closed.**

Build `2026.08.07a` confirmed in-panel after force-close/reopen. Scale **number** readable (not
just the unit); zoom readout visible in `z12.0` format and updating on pinch; attribution still
showing OpenStreetMap + CARTO + State of Queensland; place-name labels still rendering. **No
collision with the attribution strip in the bottom-right corner** — the reasoned-not-verified
corner choice held. The `voyager_only_labels` tileLayer line was independently verified from the
file (`subdomains:'abcd'`, `pane:'labels'`, `maxZoom:21` all present) after a suspected truncation
in the session transcript.

**METHOD NOTE — a verification gap in the standing build discipline.** The suspected corruption
was `{subdaxZoom:21,…}` in place of `{subdomains:'abcd',pane:'labels',maxZoom:21,…}`. That is
**valid JavaScript** — a wrong property name, not a syntax error — so `node --check` would have
passed a broken file, as would the Leaflet hash check and the diff-scope check. **Add to dispatch
prompts: after editing any long single line, re-read it from the file and quote it, not from the
edit output.** Transcript paste is not file content.

---

**6. REPO HYGIENE — v16.61 sat UNCOMMITTED for four days.**

`d8e6248` swept in the v16.61 entry, which had been written to the repo working tree on 2 Aug and
never committed. For four days the repo read v16.60 while project knowledge carried v16.61 — a
reader checking repo head would have concluded PK had forked *ahead* of the authoritative copy,
which is the exact undetectable-from-inside-a-chat failure the one-direction sync rule exists to
prevent. Verified before pushing: `v16.61` occurrence count is 0 at `c1684fd` and 8 at `d8e6248`;
412 changed lines − 48 for the v16.62 entry = 364 ≈ the v16.61 entry. Now closed.

**Standing rule, promoted from this incident: WRITING A ROADMAP ENTRY IS NOT COMMITTING IT.** A
session that ends without `git status` clean has not closed. Check for an uncommitted roadmap
before every push, not only when a hygiene sweep is running.

---

**7. NEXT — supersedes v16.61's list.**

1. **DONE** — v16.62 and v16.63 both gated on-phone and closed (§1, §5 above).
2. **BUILT — shipped as build `2026.08.09a` (v16.65 at the top of this file). NOT YET RUN: the
   forty-gesture on-phone protocol below is now the next job, and no patch may precede it.**
   Original scoping, kept for the record:
   **STEP B MEASUREMENT BUILD — the next job. Sonnet. Diagnose before patch.** Now correctly
   scoped and genuinely warranted: subjective rating has saturated twice and cannot resolve the
   ~1-point gap. Instrument with `performance.now()` — `buildShade()`: S1 samples+bounds+index,
   S2 mask pass, S3 IDW pixel loop, S4 `smoothField`, **S5 canvas paint including
   `cv.toDataURL()`** (a synchronous PNG encode of W×H px, never once measured, kept as its own
   number); `buildAutoContours()`: C1 index+field, C2 marching-squares+polyline+layer-add, CT
   total. Also capture shade W/H/W·H, contour W/H/W·H, `depthSamples()` length, `map.getZoom()`
   to 1 dp (v16.63's readout makes this exact), and wall time from `moveend` to swap complete.
   **Rolling window of the last 10 gestures, reporting MEDIAN and MAX per segment — jitter is
   variance, not mean.** On-screen overlay (iOS standalone has no console), toggleable, **default
   OFF**. Output pixels must be byte-identical to `2026.08.07a`. On-phone protocol: overlay ON,
   10 pans at Bargara z14 + 10 at z11, 10 at Redcliffe/Hays z14 + 10 at z11 — four screenshots,
   forty gestures.
3. **Jitter fix, scoped by what (2) measures. Not before.** (2)'s instrumentation now exists but
   has produced no numbers yet — this item stays blocked until the four screenshots land.
4. `storage_check.html` tooling pass, batch three: section 1 reload hint after a section 6 delete;
   section 3 caption corrected to say it does NOT bound localStorage; stale 5.34 MB VERDICT panel
   removed. Unchanged, independent of the render work.
5. Option 3 coverage-boundary toggle, opt-in default OFF, edge-detection of the painted alpha
   buffer. Unchanged.
6. MN v3 Noosa-OSM fetch → clip, plus Noosa tide-port wiring (BoM TP021). Independent.
   **TRANSIENT COST:** the REPLACE path writes a ~553.6 KiB rollback snapshot before committing,
   so peak demand ≈1,045 KiB against 1,024–2,047 KiB free — fits now, did not before the v16.61
   rollback-key delete. The ~491 KiB projection is geometric; measure the real clipped count
   first.
7. Multi-region architecture spike — gates Gold Coast, national scale, and item 16. Named starting
   hypothesis: static region files on GitHub Pages + IndexedDB cache + viewport-driven loading.
   IndexedDB migration comes OFF Hold as the gate, not an optimisation.

**OPEN, LOW PRIORITY (unchanged from v16.61):** lat/lng readout on the depth-tap popup; backup
file is 19.08 MB for 3.85 MB of unique data (pretty-printed, points stored twice); `legacy_unknown`'s
mask drops >half a below-datum population — worth one look before treating it as clean. **Added
this session:** surface the v16.62 silent `catch(e){}` (§4); `_idwCache` is keyed on `s.length`
rather than `poolVersion`.

---

*v16.63 · 7 Aug 2026 — MAP CONTROL LAYOUT SHIPPED (cosmetic only). Build bumped to
**2026.08.07a**. Repo head `d8e6248` at session start.

**Problem:** the scale control (bottom-left) was clipped by the screen edge on narrow (~390px)
iPhone viewports — only the "km" unit was visible, not the number, which breaks the on-phone gate
protocol since it depends on reading zoom/scale accurately. Root cause of the left-edge clipping
itself was not chased down (out of scope for a cosmetic, one-variable build); the fix relocates the
control rather than diagnosing why bottom-left clips.

**What shipped (`index.html:1208-1218`):**
- Scale control moved `bottomleft` → `bottomright` — the only corner with no competing UI: `.panel`
  occupies topleft, the zoom control occupies topright (pushed down 64px on narrow screens per the
  existing `max-width:600px` rule to clear the header), bottomright previously held only the
  attribution strip.
- New zoom-level readout appended directly into the scale control's own container via
  `L.DomUtil.create('div','leaflet-control-scale-line', scaleCtl.getContainer())` — reuses the
  scale text's own CSS class verbatim (same border/padding/background/font, so same visual weight
  by construction, zero new CSS), reads `z<zoom to 1 decimal>`, set on load and updated on
  `map.on('zoomend', …)` only, matching the spec exactly (no extra `'zoom'`/animation binding).
- Attribution compacted via `map.attributionControl.setPrefix(false)` — confirmed against the
  inlined `_update()` source that this only omits the "Leaflet" credit link (a falsy-prefix check,
  `this.options.prefix&&i.push(...)`); the per-layer `attribution:` strings are joined independently
  and untouched. **Attribution text remaining on screen: "Labels © OpenStreetMap, © CARTO" (from
  the always-on CARTO labels layer) + "Aerial imagery © State of Queensland (Dept of Resources)"
  (default QLD aerial base) + whichever of "© OpenStreetMap contributors" / "Imagery © Esri, Maxar,
  Earthstar Geographics · cached offline" if the user has switched base layer to OSM/satellite.**
  OSM, CARTO and State of Queensland attributions confirmed present in every base-layer state; only
  "Leaflet" was removed.
- Zoom control (topright) untouched, still present.

**Not verified on-device this session** (no phone access) — the corner choice is reasoned from the
CSS/DOM layout (documented above), not confirmed against an actual narrow-viewport screenshot.
**Next job:** on-phone gate — confirm the full scale number is visible bottom-right, the zoom
readout reads correctly and updates on pinch/double-tap zoom, and attribution still shows the three
required credits with the current base layer. If v16.62's atomic-swap fix hasn't been gated yet
either, both can be checked in the same session.

---

*v16.62 · 6 Aug 2026 — ATOMIC OVERLAY SWAP SHIPPED. Build bumped to **2026.08.06a**. Repo head
`c1684fd` at session start.

**Diagnosis this session (stated as settled by Aaron before the build, superseding v16.61 §1):**
an on-phone re-gate with zoom held constant found NO Bargara-vs-Brisbane difference (both-off
4.5/4.5, depths-only 3.5/3.5, both-on 2.8/2.8 subjective /5) — falsifying v16.61's polygon-
complexity and local-bucket-occupancy candidates as the differentiator, and the rating scaling
with the *number* of visible overlays rather than geography. Drag itself was confirmed smooth; the
complaint is **both overlays going ABSENT for ~1-2s after each pan settles**. Two read-only steps
(Step A / Step A2, this session, no code changed) narrowed the cause before any fix was written:

- `moveend` + 350ms debounce was already confirmed (not a raw `move` binding), ruling out
  per-frame rebuild during the drag itself.
- Leaflet's own `ImageOverlay`/`Canvas` renderer classes (inlined, byte-identical, unedited) don't
  reposition per-frame during a pan either — both ride the shared `mapPane` CSS transform; only
  `Canvas._update` fires on `moveend` to resize/redraw existing paths, independent of our own
  debounce.
- Step A2 confirmed the actual defect: `buildShade()` (`index.html:2034`, pre-fix) and
  `buildAutoContours()` (`index.html:2547`, pre-fix) both **removed the existing overlay/layer at
  the START of every rebuild**, before the replacement was ready — a genuine destroy-then-rebuild
  gap, not a compute-cost problem. This is a DIFFERENT root cause than v16.61 §1's three
  compute-cost candidates (mask pass / IDW bucket occupancy / `smoothField` GC churn) — those were
  never confirmed or denied by a compute measurement in this session; the originally-sequenced
  Step B `performance.now()` instrumentation build (§9 item 2 below) was **not run**. If the
  absent-overlay symptom is gone after this build but jitter/lag persists, Step B's segment timing
  is still the owed next diagnostic — this build did not do compute profiling.

**What shipped:** `buildShade()` and `buildAutoContours()` now build the replacement overlay/layer
into a local variable, add it to the map, and only then remove the previous one — old content stays
visible for the entire rebuild instead of a bare gap. Both wrapped in try/catch so a thrown
exception mid-rebuild leaves the prior overlay in place rather than leaving the map bare. Explicit
toggle-off (`shadeOn`/`autoCtOn` false) and the "genuinely nothing to show for this view" branches
(pts<3, degenerate viewport-clip, `mxD<=mnD`, empty `levels`) still clear immediately — final-state
pixels for those branches are unchanged from before, only the successful-rebuild path's ordering
changed. No debounce/W-H-sizing/`pooledSampleIndex`/`smoothField`/pixel-output change — confirmed
by diff scope (index.html:2034-2228, 2556-2638 only) and Leaflet-block byte-identity
(sha256 `db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`, unchanged).

**Next job:** on-phone gate this build — confirm the ~1-2s absent-overlay window is gone (old
overlay visibly persists through the ~350ms debounce + rebuild, then swaps in one step). If jitter
or lag still shows up as a *feel*, not an absence, resume §9 item 2 (the originally-sequenced
`performance.now()` instrumentation of `buildShade()`'s bounds/mask/IDW/`smoothField` segments,
extended per v16.61's correction to also cover `buildAutoContours()`) — that measurement was never
run this session and remains the way to settle whether v16.61 §1's compute-cost candidates matter
at all once the ordering bug is out of the way.

---

*v16.61 · 2 Aug 2026 — planning + on-device measurement. No build, no code. Build stays
**2026.08.02a**. Repo head `c1684fd` at session start; roadmap version verified by direct
`project_knowledge_search` before this entry was written (found v16.59 on project knowledge,
v16.60 committed by the build session in between). **Storage ceiling measured for the first time.
Rollback keys deleted. Storage prune CANCELLED. Item 13 closed. On-phone gate on v16.60: PARTIAL
PASS — pan jitter remains, and its geography identifies the residual.**

---

**1. ON-PHONE GATE ON v16.60 — PARTIAL PASS. "Still feels a little jittery, more noticeable
around Brisbane than Bargara."**

The cache did its job: the O(n) index rebuild that scaled with the full pool is gone. What
remains does NOT scale with pool size — and the geography proves it. Bargara and Brisbane draw
from the same 64,306-point pool, so anything scaling with the pool would feel identical at both.
It doesn't. The residual is therefore **viewport-local work**, and there are three candidates,
all inside `buildShade()`'s per-pan path:

- **(a) The mask pass — `inWaterFast(feats,la,lo)` per pixel.** `W`/`H` are `Math.max(110,
  Math.min(360, Math.round(extM/60)))`, so up to 360×360 = **129,600 point-in-polygon tests per
  pan**. Cost scales with *polygon complexity*, and Moreton Bay's OSM water geometry (Hays Inlet,
  Pine River, Bramble Bay, the river channel, islands) is vastly more intricate than Bargara's
  open coast. **Strongest fit for the Brisbane-vs-Bargara asymmetry.**
- **(b) The IDW pixel loop — 3×3 bucket scan per pixel.** Cost ∝ *local* bucket occupancy. Global
  mean occupancy is 1.135 (measured, v16.60 Step B), but that average is over the whole pool bbox
  including empty ocean; local occupancy around Brisbane is far higher than around Bargara.
  **Second-strongest fit.**
- **(c) `smoothField()` allocation churn.** It allocates `new Float32Array(W*H)` on each
  ping-pong swap — ~518 KB per allocation at 360×360, several per pan. GC pressure produces
  *hitches* rather than uniform slowness, which is what "jittery" describes. **Not
  geography-dependent, so it can't explain the asymmetry on its own — but it may be what makes
  the residual feel like jitter rather than lag.**

**Architecturally this is the right shape and it matters for multi-region (#15):** none of
(a)/(b)/(c) grows with the *number* of regions. They grow with local density and local geometry
complexity. Adding Gold Coast or Hervey Bay does not make Bargara slower. The pool-scaling
problem is genuinely solved.

**NEXT BUILD IS A MEASUREMENT BUILD, NOT A FIX.** Diagnose before patch. Instrument `buildShade()`
with `performance.now()` around four segments — bounds/index (expected ~0 now the caches are in),
mask pass, IDW pixel loop, `smoothField` — and surface the four numbers plus `W`, `H` and pixel
count. One pan at Bargara, one at Brisbane, both reported. Writing an optimisation before that
would be guessing between three plausible causes.

**Unseparated variable:** the gate report did not state whether auto-contours was ON or OFF.
`buildAutoContours()` chains from `buildShade()` and runs its own full pixel loop plus its own
`smoothField` — if it was ON, roughly half the observed cost may be that second path. **Re-test
with it explicitly OFF, then explicitly ON, before the measurement build.**

**Also unconfirmed:** Aaron did not report seeing build string `2026.08.02a` in the panel. The
gate result is being recorded on the assumption the new build was live. Confirm on the next
phone session.

---

**2. STORAGE — THE CEILING IS MEASURED. FIRST REAL BOUND IN THE PROJECT'S HISTORY.**

**Sequence run this session:** `storage_check.html` on the phone (home-screen container,
confirmed by its own section 0) → fill-test → guarded rollback-key delete tooling built and
shipped → deletes executed → fill-test re-run.

**Reading 1 (pre-delete):** 20 keys, 4,995.5 KiB. Fill-test **0.0 MB**. Container at ceiling.

**The quota trap — do not repeat this mistake.** `navigator.storage.estimate()` reported
**usage 2.27 MB of quota 39,321.6 MB**. That 39.3 GB figure is the **StorageManager origin
quota** — disk-derived, governing IndexedDB and the Cache API. **localStorage on WebKit has a
separate per-origin ceiling that StorageManager does not report.** Recording "quota = 39.3 GB"
would read as "storage is a non-issue" and is the exact wrong inference. Section 3 is also
internally incoherent: its caption claims the estimate reads *higher* than section 1 because it
covers localStorage + IndexedDB, but it reads 2.27 MB against section 1's 4.88 MB — **lower**,
and that is before ~1 MB of photo data. Section 3 cannot be used as a localStorage measurement.
**Fix the caption on the next tooling pass.**

**Section 1 IS accurate — verified independently.** Serialising the `datasets` object exactly as
the app stores it gives **3,849.69 KiB** against section 1's reported **3,849.7 KiB**. Exact to
0.01 KiB. Everything below rests on that.

**The fill-test's 1 MiB granularity — v16.60's claim corrected.** The test builds
`chunk = new Array(MB+1).join('x')` with `MB = 1024*1024`, appends whole chunks, and never
retries smaller after a failure; `achieved = filled.length/MB` displayed `.toFixed(1)`. So its
**display floor is 1 MiB**. "0.0 MB" means *headroom < 1,024 KiB* and nothing more precise.
v16.60's "GENUINE zero, not a rounding artefact" is wrong and is tagged superseded in that entry.

**Cap bracket — the first real bound:**

```
pre-delete  usage 4,995.5 KiB, first 1 MiB append failed
              → cap < 4,995.5 + 1,024 = 6,019.5 KiB
            current contents obviously fit
              → cap >= 4,995.5 KiB
post-delete usage 3,871.6 KiB, fill-test returned 1.0 MB
              → cap >= 3,871.6 + 1,024 = 4,895.6 KiB
              → cap <  3,871.6 + 2,048 = 5,919.6 KiB
            ─────────────────────────────────────────
            cap in [4,995.5 , 5,919.6) KiB
```

**5,120 KiB (5 MiB) is the only round figure in that window** and is the conventional WebKit
per-origin localStorage ceiling. Plan against it; do not record it as measured. **The ~4.75 MB
cap figure carried since v16.35 is SUPERSEDED** — the container sat at 4.88 MB without failing.

A precise cap needs a KiB-granular binary search after the coarse 1 MiB pass. Worth adding to
`storage_check.html` on a later tooling pass; not worth a build on its own.

---

**3. ROLLBACK-KEY DELETE — SHIPPED AND EXECUTED. 1,123.9 KiB FREED, NON-DESTRUCTIVELY.**

`storage_check.html` had no path to delete these keys (its section 5 targets only legacy
`woongarra_imported_v1`, confirmed absent since v16.55), and Safari remote inspection is not
available from Windows. New **section 6** built and shipped in commit `7db40e8` — no
`index.html` change, no build-string bump, tool rev stamp `2026.08.02a` in the heading.

Enumerates keys prefixed `woongarra_imported_rollback_v2:` (colon required), one delete button
per key behind a `confirm()`, no delete-all, prefix re-verified immediately before every
`removeItem` plus an explicit protected-key assertion, re-enumerates from live localStorage after
each delete.

Deleted on-device, smallest-first so a fault would surface on a 0.4 KiB key rather than a
602 KiB one:

| key | KiB |
|---|---:|
| `:brisbane_river` | 602.3 |
| `:sunshine_coast` | 519.3 |
| `:smoke_test` | 0.6 |
| `:smoketest` | 0.6 |
| `:smoke02` | 0.5 |
| `:smoke` | 0.4 |
| `:moreton_bay` | 0.1 |
| `:custom` | 0.1 |
| **total** | **1,123.9** |

4,995.5 − 1,123.9 = **3,871.6 KiB**, 12 keys. Fill-test 0.0 → **1.0 MB**. Four of the eight were
leftover smoke-test debris from earlier tooling runs.

**Tooling wart found:** section 1 renders once at page load and does NOT re-render after a
section 6 delete, so it keeps showing pre-delete totals while section 6 correctly shows "None
found". Section 5 at least prints "(Reload this page to refresh section 1.)"; section 6 doesn't.
This nearly produced a wrong conclusion on-device. **Add the reload hint on the next tooling
pass.**

**Second wart:** the VERDICT panel tests against a **full-res Sunshine Coast import at 5.34 MB**
— a v16.28-era scenario superseded by the v2 drop-mask CSVs and the Option 3 mask. Nothing in the
current sequence needs 5.34 MB. It is a stale hardcoded threshold that would push a future
session into thinning something that doesn't need thinning. **Remove it on the next tooling
pass.** Ignore it until then.

---

**4. STORAGE PRUNE — CANCELLED. The destructive option frees LESS than the free one.**

Measured from the verified 2 Aug backup, at real serialised bytes-per-point:

| dataset | stored | survives mask | dead | B/pt | stored KiB | **dead KiB** |
|---|---:|---:|---:|---:|---:|---:|
| `legacy_unknown` | 55,660 | 20,533 | 35,127 | 28.92 | 1,571.8 | 992.0 |
| `brisbane_river` | 21,126 | 9,420 | 11,706 | 29.66 | 611.8 | 339.0 |
| `sunshine_coast` | 17,806 | 5,947 | 11,859 | 29.64 | 515.4 | 343.2 |
| `maroochy_noosa` | 19,178 | 19,178 | 0 | 29.56 | 553.6 | 0.0 |
| `moreton_bay` | 20,602 | 9,228 | 11,374 | 29.65 | 596.4 | 329.3 |
| **total** | **134,372** | **64,306** | **70,066** | | **3,849.1** | **2,003.5** |

Stored total and the 64,306 runtime pool both reconcile exactly to prior figures. **Measured
bytes-per-point is 29.6, not the 27.91 carried since v16.47.4** — that figure was MN-specific and
excluded the datasets-object wrapper.

**The prune's saving was overstated by roughly half.** The roadmap treated "≈1.87 MB of dead
localStorage" as the payoff. That is the *total* dead weight. The prune as specified only reaches
BR/SC/Moreton:

```
BR + SC + Moreton dead = 339.0 + 343.2 + 329.3 = 1,011.5 KiB   ← reachable by REPLACE
legacy_unknown dead    =                          992.0 KiB   ← no source CSV, unreachable
                                                 ──────────
total dead                                       2,003.5 KiB
```

| | frees | destructive | build | re-import |
|---|---:|---|---|---|
| Rollback-key delete | **1,123.9 KiB** | no | no | no |
| BR/SC/Moreton REPLACE | 1,011.5 KiB | **yes** | yes | yes |

**The non-destructive option freed more than the destructive one would have, and it is already
done.** No case survives for the prune. **CANCELLED — do not reopen without a new measured
justification.**

**Opportunity the backup unlocks, if headroom is ever needed again:** `legacy_unknown`'s points
now exist off-device for the first time. They could be run through the HAT+mask pipeline offline
and re-imported as a masked CSV, converting that 992.0 KiB from unreachable to reachable. Only
worth doing if a future measurement says it's needed.

---

**5. `legacy_unknown` — OPEN QUESTION FROM v16.56 CLOSED. It is not Bargara data.**

v16.56 asked why the blob loses ~63.1% to HAT+mask when it is "real Bargara bathymetric LiDAR by
original description, which should mostly sit below HAT and survive." The backup answers it.

```
Bargara/Woongarra (lat > -25.5)   10,452   18.8%
SEQ               (lat <= -25.5)  45,208   81.2%
```

**Four fifths of the blob is SEQ** — Sunshine Coast, Moreton and Brisbane River latitudes. The
original description is wrong. v16.56's alternative hypothesis (untagged BR/SC-area data mixed
in, which is exactly what HAT+mask are built to strip) is **confirmed on geography**. The 63.1%
loss rate is expected behaviour, not an anomaly.

**Second signature, unexpected:** the two halves have opposite depth profiles. The Bargara
fraction is **71.4% above datum, up to +15.92 m** — topographic ground elevation, not bathymetry.
The SEQ fraction is uniformly below datum (max +0.19 m). So even the Bargara portion of the "real
bathymetric LiDAR" blob mostly isn't bathymetry.

**Loss apportionment:** the SEQ half is entirely below datum and therefore cannot be touched by
the HAT gate. So at minimum 35,127 − 10,452 = **24,675 points, ≥70% of the loss, comes from the
mask dropping SEQ legacy points** — i.e. the mask is dropping over half of a below-datum
population. Not a blocker, but **do not treat `legacy_unknown` as clean data** without looking at
this once.

---

**6. BACKUP VERIFIED — and it is ~5× larger than it needs to be.**

`woongarra-backup-2026-08-02.json`, `version: 2`, exported `2026-08-02T04:23:49Z`. Carries 20
spots, all 5 datasets summing to 134,372 points, 1 photo (1.08 MB), profiles. Reconciles exactly
to section 1. **Sound safety net** — it is what made the rollback-key delete a zero-risk
operation.

**Inefficiency, low priority:** the file is 19.08 MB for 3.85 MB of unique point data. It is
pretty-printed (indent 2) and stores the points **twice** — an 8.11 MB flat `imported` array and
a 10.80 MB `datasets` object holding the same 134,372 points. Compact separators plus dropping
the redundant array would take it to ~4 MB. Matters only because restore is whole-store-scoped
and parses the lot on an iPhone.

---

**7. GOOGLE DRIVE AS A STORAGE BACKEND — EVALUATED AND REJECTED. Do not reopen.**

Free in dollar terms (Drive API costs nothing; files count against the personal 15 GB quota), but
wrong for this app on four counts:

- **Offline-first dies.** Guya's value is working on a rock platform with no signal. Drive needs
  a network round-trip and a live token.
- **OAuth friction.** An app in Testing status is capped at 100 test users and its refresh tokens
  expire after **7 days** — so weekly re-authentication, forever. Production status gives
  indefinite tokens but requires Google's application verification, including a security audit
  for sensitive scopes. A verification process for a personal fishing app.
- **iOS standalone-mode redirect hazard.** A home-screen web app that kicks out to an OAuth
  consent screen typically returns into Safari — the wrong storage container.
- **Hard rule 5.** Photos and personal data stay on-device. A depth-only split is defensible but
  needs an explicit decision, not a quiet consequence.

**The better answer, and the named starting hypothesis for the multi-region architecture spike:
static region files on GitHub Pages + IndexedDB cache + viewport-driven loading.** No auth,
`git commit` as the import path, Cache API for real offline, $0, and no privacy exposure at all
because the only thing moving off-device is public LiDAR already published in the repo. Capacity:
Pages' ~1 GB soft repo limit ÷ 29.6 B/pt ≈ **36.3 million points**, ~270× the current whole pool,
before gzip. It also retires the manual per-region import ritual — every future region costs a
commit instead of a field procedure, which is what makes "eventually a lot of regions" tractable.

---

**8. MULTI-REGION (#15) NOW HAS A HARD CEILING — three of them, binding at different points.**

Aaron flagged intent to map many more areas. On the current architecture that is not reachable:

- **Storage.** ~1.0–2.0 MB free in a ~5 MiB container ÷ 29.6 B/pt ≈ **35,000–70,000 more points,
  total, ever.** Two or three more SEQ regions at current density and headroom is gone again —
  with no rollback keys left to delete. The national-scale item (QLD-wide + NT, WA, partial NSW)
  is off by two orders of magnitude.
- **Runtime.** v16.60's cache removes the per-pan index rebuild, but the pool is still fully
  resident and fully in scope for every operation touching it. Fine at 64,306. Not fine at
  500,000.
- **Import path.** 25,000 points per CSV parse, manual, one region at a time, each followed by a
  force-close/reopen verification ritual. Tolerable for five regions; unworkable for fifty.

Fixing storage alone buys ~10× and leaves the other two. **The IndexedDB migration (currently on
Hold, deferred at v16.38 as "not urgent enough to block re-establishing SC/Maroochy-Noosa") should
come off Hold and be sequenced as the GATE on multi-region expansion, not as an optimisation.**
That deferral was correct then; the zero-headroom event is the signal it no longer is. Gold Coast
and every region after it sit behind the spike. MN v3 and Noosa are sized to fit on the current
architecture and can still proceed — they are the last things that will.

Note also that IndexedDB brings a durability win independent of capacity: transaction commit is a
genuine signal, which would retire the force-close/reopen ritual for everything except
user-created data.

---

**9. NEXT SEQUENCE (supersedes the v16.58 sequence and v16.60's restatement of it):**

1. **Re-gate v16.60 with auto-contours explicitly OFF, then explicitly ON**, and confirm build
   string `2026.08.02a` in the panel. Separates the two pixel-loop paths. No build.
2. **Measurement build** — `performance.now()` instrumentation of `buildShade()`'s four segments
   (bounds/index, mask pass, IDW loop, `smoothField`) plus `W`/`H`/pixel count, reported for one
   Bargara pan and one Brisbane pan. Sonnet. Diagnose before patch.
3. **Jitter fix**, scoped by what (2) measures. Not before.
4. **`storage_check.html` tooling pass** (cheap, batch three fixes): section 1 reload hint after
   section 6 deletes; section 3 caption corrected to say it does NOT bound localStorage; stale
   5.34 MB VERDICT panel removed. Optionally add the KiB-granular binary search for a precise cap.
5. **Option 3 coverage-boundary toggle** — opt-in, default OFF.
6. **MN v3 Noosa-OSM fetch → clip, and Noosa tide wiring** — independent of 1–5. **Transient cost
   note:** MN v3 nets ≈ −63 KiB at rest (553.6 out, ~491 in), but the REPLACE path writes a
   rollback snapshot of `maroochy_noosa` BEFORE committing, so peak demand is ~1,045 KiB against
   1,024–2,047 KiB free. It fits now; it did NOT fit before the rollback delete. **Do not
   re-derive "MN v3 is free" and dispatch it against a full container.** The ~491 KiB projection
   is geometric, not measured — measure the real clipped count before dispatching.
7. **Multi-region architecture spike** (see §8) — gates Gold Coast, national scale, and #16.

---

**10. PROCESS NOTES FROM THIS SESSION.**

- **Claude Code's inference needs checking against its own evidence, even when the evidence is
  correct and verbatim.** The fill-test diagnostic reported the 1 MiB chunk mechanism accurately
  and then concluded the opposite of what it implies. Twice this session it *also* stopped
  correctly rather than papering over a problem (the viewport-dependency finding that reshaped
  v16.60; a self-flagged comparison-direction bug in the Step B harness). The pattern is: trust
  the evidence it gathers, red-team the conclusions it draws from it.
- **A commit message is a label, not a file.** Verify roadmap version by reading the file
  (`Select-String -Path .\GUYA_ROADMAP.md -Pattern '^\*v16\.' | Select-Object -First 1`), not
  by trusting `git log`.
- **PowerShell has no `grep`/`head`/`tail`/`wc`.** Use `Select-String`, `Select-Object
  -First/-Last`, `Measure-Object -Line`. Write dispatch commands in PowerShell form.
- **`Select-String` prints nothing on no-match** — empty output is a valid negative result, not a
  failed command.
- **Never delete and re-add the home-screen icon to bust a cache.** It destroys the container and
  every point in it. Restore is whole-store-scoped and needs headroom that may not exist.
- **Never open a `?v=` cache-bust URL in Safari to test.** Separate container; it shows an empty
  store that means nothing.
- Pages Actions runs for `dff2999`, `7db40e8`, `5d99dcc` and `c1684fd` were **not** confirmed —
  `gh` is unavailable in the Claude Code environment. Check
  `https://github.com/AzmixLabs/Guya_Wamu/actions` directly. A push is not a deployment.*

---

*v16.60 · 2 Aug 2026 — poolVersion-keyed memoisation of ptsBounds()/buildSampleIndex(), on-phone
sequence item (2). Build bumped to **2026.08.02a**. Repo head `5d99dcc` (tooling commit `7db40e8`
before it: storage_check.html rollback-key delete + the item-13 hygiene commit `dff2999`, all v16.59
follow-through, no index.html changes in that pair).

**What shipped:** `buildShade()` and `buildAutoContours()` rebuilt a fresh O(n) bucket index over
the FULL point pool on every map pan (`map.on('moveend', …)`, 350ms debounce) — cost scaled with
pool size (64,306-pt real runtime pool), not viewport. A naive poolVersion-only cache around
`buildSampleIndex()` was blocked by a real finding: `cellLo` (bucket cell width) was derived from
the VIEWPORT's own `midLa`, which changes every pan independently of `poolVersion` — caching would
have served a stale index built at the wrong cell size. Root-caused and fixed at the source instead
of working around it: `cellLo` now derives from `mLngMin` (the pool bbox's most-negative latitude,
i.e. its smallest possible `mLng`), making it a pure function of the pool alone — structurally
`>= R1=120m` everywhere in the pool, for any pool, no re-verification needed as regions are added.
`cellLa` needed no change (`mLat=111320` is a bare constant, never viewport-dependent). This wasn't
purely a latent-bug fix bundled in for its own sake: the OLD viewport-anchored scheme, measured via
a harness that slices the real `buildSampleIndex()`/lookup loop into a Node `vm` context (synthetic
pool spanning the real -24.7475..-27.6428 on-phone span), missed a genuinely-within-120m sample on
2/385 eligible spread queries and 2/8 targeted boundary cases — always at the southern (Moreton
Bay/Redcliffe) extreme, under BOTH narrow zoom centred on the pool AND wide zoom, not only a
wide-zoom edge case. The new scheme: zero misses, confirmed twice — once against a hand-derived S3
formula (pre-implementation proof), once (Step C2) re-sliced from the actually-edited file, byte-
identical results both times. `poolVersion`-keyed caches then added: `ptsBounds()` caches inside
its own body (its only two callers always pass the same `depthSamples()`-cached array, confirmed
no other caller exists); `buildSampleIndex()` is cached via a `pooledSampleIndex()` WRAPPER at
`buildShade`'s/`buildAutoContours`'s call sites only, deliberately NOT inside `buildSampleIndex()`
itself — `idwIndex()`/`impIndex()` (the Navionics-comparison tool) also call `buildSampleIndex()`
directly with a different, fixed (-24.85°-anchored) `cellLo` that a body-level poolVersion-only
cache would have silently corrupted (whichever caller ran first in a given `poolVersion` would hand
its own index to every other caller). `idwIndex`/`_idwCache` and `impIndex` left untouched, exactly
as scoped. `R0_local`/`R0_MIN`/`R0_MAX`/`R1`/HAT gate/`okHAT`/`okMASK`/`REGION_MASK_EXEMPT`/
`WOFS_FREQ_MIN`/`zoneAt()`/`ORDER`/green-zone dragend safeguard/`spotsUnlocked`/both `<style>`
blocks/inlined Leaflet block: untouched, confirmed absent from the diff. `git diff --stat`: 1 file
(`index.html`), 89 insertions / 19 deletions, fully scoped to the cache/cellLo change plus the two
build-string lines. Verified: `node --check` both script blocks (exit 0, before and after the
build-string bump); Leaflet SHA-256 unchanged (`db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a`);
both `<style>` blocks byte-identical to the pre-session HEAD by direct string comparison. Pushed
(`7db40e8..5d99dcc`); `gh` unavailable in this environment, so the Pages Actions run itself was NOT
confirmed here — check `https://github.com/AzmixLabs/Guya_Wamu/actions` directly. Not claimed:
on-phone "feels faster" — that's Aaron's gate, not measured here.

**Next session:** on-phone gate this build (confirm shading/contours still render correctly panning
across Bargara↔Redcliffe, and that pan responsiveness actually improved) before touching sequence
items (3)/(4). If the gate passes, next up per the still-unchanged v16.58 sequence: (2 done) → (3)
storage prune — REPLACE BR/SC/Moreton with mask-surviving points only, after a `storage_check.html`
run that records an actual **quota** figure and not just usage (NOTE: storage_check.html's own
Step 1 diagnostic this session found "0.0 MB" fill-test headroom is GENUINE zero, not a rounding
artefact — the quota ceiling is real and current); (4) Option 3 coverage-boundary toggle,
edge-detect implementation, opt-in and default OFF; (5) MN v3 Noosa-OSM fetch → MN v3 clip, plus
Noosa tide-port wiring. The v16.58 process fix (route planning-deltas to the repo copy first) is
STILL not actioned — still requires an edit to this project's own custom instructions, which only
Aaron can make.*

> **[THREE CORRECTIONS TO THE PARAGRAPH ABOVE — see v16.61, 2 Aug 2026.]**
> (1) **The "GENUINE zero, not a rounding artefact" claim is WRONG.** The fill-test writes a flat
> 1 MiB chunk and never retries smaller, so its display floor *is* 1 MiB — "0.0 MB" means
> "headroom < 1,024 KiB" and cannot mean anything more precise. The diagnostic reported the
> mechanism correctly and then drew the opposite inference from it.
> (2) **The storage prune is CANCELLED**, not pending. Its reachable saving was measured at
> 1,011.5 KiB — less than the 1,123.9 KiB freed non-destructively by the rollback-key delete.
> (3) **The v16.58 process fix IS actioned** — project instructions rev D (31 Jul) carry the
> one-direction repo→project-knowledge sync rule. Not an open task.*

---

*v16.59 · 31 Jul 2026 — housekeeping + one correction. No build, no code, no data. Build stays
**2026.07.30a**. Repo clean at `28c3fff` (v16.58); project knowledge confirmed at v16.58 by direct
search before this entry was written, so v16.58 is the verified common base on both surfaces — the
fork v16.58 resolved has not reopened.

**Two stale-tracking loose ends closed — but one of them did NOT close the way it was reported,
and the difference matters.**

- **`guya_species_qld_v3.md` — open item 13 CLOSED as a tracking item, but the standing note that
  contradicts it is only now being tagged.** The file is tracked and committed. It did not sit out
  of the repo and then get deliberately admitted: it was swept in by **v16.48's STEP 0 REPO
  HYGIENE** (22 Jul), which committed it alongside the pending roadmap edit and described it as
  benign species-passport seed data, read in full before committing, unrelated to that build. True
  as far as it goes — but it treated a **deliberate exclusion as accidental cruft.** Two places on
  record say the opposite: the standing **Species seed** note immediately above the `## Design
  rules` divider ("kept in project knowledge (private), not the repo. Repo stays just the shipped
  `index.html`"), and the earlier baked-data commit entry, which lists the file under
  **Deliberately left out** — "by design — project knowledge only, never the repo." So the correct
  status is not "no action needed." It is: **a design decision was silently reversed, and the
  roadmap still asserted the pre-reversal position in a live, untagged section.** That Species-seed
  note is now tagged `[SUPERSEDED — see v16.59]` in place — the same treatment v16.58 gave
  v16.53's two stale claims, for the same reason: so a top-to-bottom Claude Code pass can't read it
  as current.
  **Left to Aaron, deliberately not decided here — whether the file should stay in the repo.**
  The content is benign, but the original note's parenthetical was "project knowledge
  (**private**)", which reads as a visibility decision rather than a tidiness one. If
  `AzmixLabs/Guya_Wamu` is public (it serves GitHub Pages; **not verified in this chat — the API
  check was rate-limited, so this is an open question, not a finding**), the sweep made the seed
  list public. Resolve one of two ways: accept it as a change and delete the superseded note, or
  `git rm --cached` it and add it to `.gitignore` so the next hygiene sweep can't re-commit it.
  Doing neither leaves a third independently-drifting copy of a project-knowledge file — the same
  multi-surface divergence class as the v16.58 sync incident, just with a smaller file.

- **Two contaminated pre-drop-mask CSVs re-deleted from the working tree.**
  `brisbane_river_intertidal_ground_v1` and `sunshine_coast_intertidal_ground_v1` resurfaced
  untracked; confirmed byte-identical to the v1 files already formally removed from the repo
  (classifier-fault contaminated, superseded by the v2 CSVs at `ef9385d`). Re-deleted, `git status`
  clean. **No new information** — same files, not a fresh export, so nothing about the mask or the
  v2/v3 lineage changes. Worth one line only because they came back once and can come back again:
  they are **not gitignored**, so anything that re-materialises them (an old export script re-run,
  a restore from a scratch folder) leaves them one careless `git add -A` from re-entering the repo.
  Cheap prophylactic if it recurs: add `*_intertidal_ground_v1.csv` to `.gitignore`.

**Unchanged and still open — the v16.58 process fix has NOT been actioned.** Route planning deltas
to the repo copy first, commit, then re-upload to project knowledge: one direction, one
authoritative copy. It requires an edit to this project's own custom instructions, which only Aaron
can make. Until it exists, every full-file handoff — including this one — depends on the manual
"delete old, upload new" step that already failed once at v16.57.

**Next build session — sequence unchanged from v16.58**, restated only so this entry is
self-contained: (1) `poolVersion`-keyed cache on `ptsBounds()`/`buildSampleIndex()`, on its own,
on-phone gate; (2) storage prune — REPLACE BR/SC/Moreton with mask-surviving points only, after a
`storage_check.html` run that records an actual **quota** figure and not just usage; (3) Option 3
coverage-boundary toggle, edge-detect implementation, opt-in and default OFF; (4) MN v3 Noosa-OSM
fetch → MN v3 clip, plus Noosa tide-port wiring — order-agnostic between themselves, independent
of 1–3.*

---


*v16.58 · 31 Jul 2026 — planning chat, no build. **SYNC INCIDENT, resolved.** A separate planning
chat, opened from this chat's handoff prompt, found project knowledge stuck at v16.55 with no
v16.56/v16.57 — the full v16.57 file this chat produced and presented was never actually re-
uploaded to project knowledge (a file-swap failure, not a delta-application failure: the download
was generated and offered, but the "delete old, upload new" step didn't happen). That chat also
found the **repo** stuck at v16.53 (`a3bb30d`), meaning the build-authoritative copy still carries
both of v16.53's two highest-prominence errors as unmarked fact. Both quotes it flagged checked out
verbatim against the real file — **both now tagged inline, in place, so Claude Code can't read them
as current on a top-to-bottom pass:** the 51.7%/177,898→85,894 headline (`[SUPERSEDED — see
v16.56]`) and the "MN v3 clip... OSM polygons... now exist" NEXT JOB line (`[CORRECTED — see
v16.54]`). **Action: re-download THIS file (v16.58) and use it for both the project-knowledge
re-upload and the repo overwrite** — it descends cleanly from the real v16.55 base, verified
insertions-only, no mid-file hunks, matching the diff gate the other chat correctly insisted on
before any overwrite.

**Corrections accepted from that chat's review, applied here:**

- **Option 2 (cosmetic edge softening) dropped from the pending-decision list.** A linear alpha
  falloff between R0 and R1 already exists (`distA = near<=R0 ? 1 : (near>=R1 ? 0 :
  1-(near-R0)/(R1-R0))`, per that chat's citation of `index.html:2014`, v16.47.x) — R0 was
  deliberately raised (30→35→56 in the MN work) specifically to close visible gaps, so "soften the
  edge" now would mean either changing the curve shape or lowering R0, i.e. partially reversing a
  three-sub-version-old decision and reopening the hole-rate v16.47.4 measured. Not verified against
  the live `index.html` in this chat (no repo access here) but consistent with everything on record;
  Claude Code should confirm the current curve at build time and stop here if it disagrees.
- **Option 3 pinned to a specific implementation, not left for Claude Code to pick:** edge-detect
  the painted alpha buffer and stroke the boundary of what's actually painted (interior holes
  included) — not a convex hull (implies coverage over gaps) or a concave/alpha-hull (fiddly,
  introduces a tuning parameter). Tautologically correct, O(pixels) not O(points). **Ship as an
  opt-in layer toggle, default OFF** — the default path stays lean; this is chrome for interrogating
  a specific blob, not always-on cost.
- **Bundling rejected — build the perf cache alone, gate it on-phone, decide the blob display
  after.** Two reasons: mixing a pixel-paint-loop change into the same build as the perf fix would
  make an on-phone "still feels laggy" report unattributable to either change (same one-variable
  discipline the r0 harness artefact already taught this project); and Option 3 wasn't build-ready
  as originally stated (three implementations with very different honesty profiles) until pinned
  above.
- **Storage note corrected — it was one figure in two units, not two figures.** "4995.5 KB / 4.88
  MB" is the same usage number (4995.5 ÷ 1024 = 4.878), not usage-vs-quota. **No actual quota
  figure has ever been recorded** — next `storage_check.html` run should capture it explicitly, not
  just usage, especially now that usage is confirmed non-trivial.
- **MN v3's storage-note direction was backwards — corrected.** v16.47's own entry mandates REPLACE
  on `maroochy_noosa`: ~535 KB of existing 19,178-pt data comes OUT before the new ~491 KB clip goes
  in. Net effect is **≈ −44 KB, not +491 KB** as the v16.55 backlog note carried it forward. The
  clip is a storage *saving*, not a cost, at the projected (≤60k-pt, native-25m) branch size.

**Checked, not accepted as stated:** the claimed self-contradiction in the MN v3 grid-ladder entry
("check quota first" for the 60k–150k branch vs "quota risk is negligible" in the same entry) does
NOT hold up against the actual text — they apply to different branches (the 40m-thin contingency
vs the currently-projected ≤60k/native-25m case), not a flat contradiction. That said, the
practical concern underneath it is real and this chat isn't dismissing it: the same entry admits
the real clipped count could land 2–3× over the geometric estimate (which is exactly what would
push it into the 60k–150k branch), and today's storage findings (below) mean "negligible" deserves
re-checking against an actual measured quota, not the projected best case, regardless of which
branch it lands in.

**Open, not resolved — flagged rather than asserted:** the 64,306 real-runtime-pool figure DOES
reconcile exactly to a per-dataset breakdown (it was computed that way in v16.56, from the start:
legacy_unknown 20,533 + BR 9,420 + SC 5,947 + MN 19,178 + Moreton 9,228 = 64,306) — the other chat
flagged it as unreconciled only because it never received the real v16.56/57 file, not because the
arithmetic was actually missing. But the number underneath — `legacy_unknown` losing ~63.1% (55,660
→ 20,533) to HAT+mask — is a fair question to leave open rather than wave through: it's real
Bargara bathymetric LiDAR by original description, which should mostly sit below HAT and survive.
Plausible explanation: `legacy_unknown` is a pre-region-tagging blob that also contains untagged
BR/SC-area data (v16.24.2), and BR/SC's known contamination — classifier-fault topographic returns
mislabelled as depth — is exactly the population HAT+mask are supposed to strip. Plausible, not
confirmed; no per-subregion breakdown of the blob exists to settle it either way.

**New backlog item, sequenced behind the cache build and the reconciliation above, ahead of MN
v3:** a one-time storage prune — REPLACE each of BR/SC/Moreton with mask-surviving points only.
134,372 stored vs 64,306 real runtime pool = 70,066 points that never render, ≈1.87 MB of dead
localStorage (≈38% of current usage) — pruning it both resolves the quota risk outright and halves
the baseline pan-rebuild N before the `poolVersion` cache even ships. Risk: bakes in a mask that's
already had one measurement error; mitigated by the v3 CSVs still being on disk for re-import if a
third error surfaces. **Separately worth a look, not yet investigated:** the `storage_check.html`
key list shows `brisbane_river`/`sunshine_coast` **rollback** backup keys (kept for "Undo last
replace/merge/remove") totalling over 1.1 MB between them — additional reclaimable headroom if
those backups are past their useful window, unconfirmed.

**Process-fix suggestion, not actioned — needs Aaron, not Claude:** route planning deltas to the
repo copy first, commit, then re-upload to project knowledge — one direction, one authoritative
copy, retiring this whole failure class. This is a change to this project's own custom
instructions, which only Aaron can edit (via Settings) — this chat can draft the exact wording if
wanted, but can't apply it.

**Confirmed sequence for the next build session, once Aaron says go:**
1. Cache: `poolVersion`-keyed memoisation of `ptsBounds()`/`buildSampleIndex()`, same pattern as
   `_r0Cache`/`_idwCache`. On-phone gate: full-pool wide pan, auto-contours off — expect near-zero
   on repeat rebuilds.
2. Storage prune (BR/SC/Moreton REPLACE with mask-surviving points only) — new item, see above.
3. Option 3 coverage-boundary toggle (edge-detect implementation, opt-in, default off) — build once
   1–2 are shipped and stable, kept out of the perf-measurement build for the one-variable reason
   above.
4. MN v3 Noosa-OSM fetch, then MN v3 clip; Noosa tide-port wiring — unchanged, order-agnostic
   between the two, both independent of 1–3.*

---


*v16.57 · 31 Jul 2026 — planning chat, no build. Tasks 3 and 4 dispatched same session as Task
1/2 (v16.56), results at `data/raw/_landmask_validation/task{3,4}_results.md`.

**Task 3 — corrects v16.56's "2× `buildSampleIndex()` per pan" framing.** The `:2505` call isn't
inside `buildShade()` — it's inside `buildAutoContours()`, which `buildShade()` only invokes when
BOTH `shadeOn` AND `autoCtOn` are true (both default false). Real baseline cost (shading on,
auto-contours off — the default, almost certainly Aaron's normal config): full-pool pan ≈ 0.79 +
49.3 ≈ **~50ms** (not ~100ms), single-region pan ≈ 0.05 + 4.83 ≈ **~5ms** (not ~10ms) — using
v16.56's own per-call timings, corrected for the single real call. The ~10x scaling ratio holds;
the absolute figures don't. When auto-contours IS on, the double call is confirmed real and pure
redundant work (identical inputs, no order-dependent side effects) — but the already-queued
`poolVersion`-keyed cache subsumes this automatically (second call becomes a cache hit), so no
separate dedupe patch is needed; one fix covers both cases.

**Task 4 — "circle blob" density investigation, river-mouth/mangrove-terrain hypothesis
REFUTED.** R0 is per-sample adaptive (30–90m), hard cutoff at R1=120m — no fill attempted past
that, by design. >90% of points merge into continuous coverage even at the tightest radius; the
sparse tail causing visible gaps is ~1–9% of points. BR is structurally sparser overall than
Moreton (median 3 vs 9 pts/250m cell) — but BR's DENSE cells are 4x more likely to fall inside
HPZ02 (Port of Brisbane, the zone in Aaron's screenshot) than sparse ones — that area is one of
BR's better-surveyed patches, not worse; BR's sparse coverage skews upstream instead. Separately:
Moreton's dataset doesn't geographically reach HPZ02 at all — the blob in Aaron's screenshot is BR
data rendering under a Moreton Bay Marine Park zone label (independent overlays, expected).
Conclusion: ordinary patchy LiDAR flight-line coverage, not a systematic terrain-class artefact —
doesn't justify a general R1 increase. A 250m grid can't rule out a genuinely sparse patch at the
exact screenshotted coordinate though; pinning that down needs the lat/lng-readout backlog item or
a manual coordinate check.

**Aaron's "make it uniform" request reframed as three options, decision pending:**
1. Raise R1 to bridge gaps further — **rejected**: paints extent the survey doesn't support,
   conflicts with the "no data beats wrong data" principle the class-9-adjacency check already
   settled the other way.
2. Cosmetic-only edge softening (gradient falloff instead of a hard circle boundary) — same real
   extent, less visually jarring.
3. Surface the real coverage boundary explicitly, using Task 4's NN-gap percentiles — the safe
   version of Aaron's earlier "5m offshore, water begins here" idea: a boundary showing where the
   *surveyed extent* ends, not a depth or water-onset claim.

Recommended: (3), optionally layered with (2). **NEXT:** Aaron decides which option(s) to build;
build session then covers the `poolVersion` cache (fixes the baseline pan-lag and subsumes the
conditional double-call) plus whichever blob-display option is chosen. MN v3 Noosa-OSM fetch and
Noosa tide-port wiring remain queued, unaffected, order-agnostic.*

---


*v16.56 · 31 Jul 2026 — planning chat, no build. Tasks 1 and 2 from v16.55 completed via Claude
Code, results written to `data/raw/_landmask_validation/task{1,2}_results.md`.

**Task 1 — real Option 3 mask table, supersedes v16.53's headline:**

| Dataset | Stored | HAT-surviving | Mask-surviving | Removed (of HAT-surviving) |
|---|---|---|---|---|
| BR | 21,126 | 20,970 | 9,420 | 55.08% |
| SC | 17,806 | 17,561 | 5,947 | 66.14% |
| Moreton | 20,602 | 20,353 | 9,228 | 54.66% |

v16.53's claimed HAT-surviving figures (68,246/57,050/33,424) exceed the real stored counts for
all three — structurally impossible, confirms the v16.55 wrong-dataset diagnosis (harness ran
against pre-thin v3 CSV exports, not on-device data). **The removal RATE was correct all along**
(55.08/66.14/54.66% real vs 52.5/67.0/53.7% claimed) — only the absolute population was wrong, by
roughly 3x on BR/SC and 3.6x on Moreton (real mask-surviving counts run about a third of what
v16.53 implied).

**Minor inconsistency caught in task1_results.md, logged not re-run:** its method section
describes `legacy_unknown` as "exempt by REGION_MASK_EXEMPT, out of scope per spec," grouping it
with `woongarra`. That's not accurate — `REGION_MASK_EXEMPT` keys are only `woongarra` and
`maroochy_noosa`; `legacy_unknown`'s region tag doesn't match either, so it IS mask-filtered, same
as BR/SC/Moreton (confirmed independently and correctly in Task 2's own method section, which
computed its real post-filter N as 20,533). Doesn't affect Task 1's reported BR/SC/Moreton numbers
— it just wasn't asked to measure legacy_unknown — but the stated justification for skipping it is
wrong and shouldn't be reused as a reference next time legacy_unknown needs measuring.

Real total runtime pool, all 5 datasets combined post-HAT+mask (using Task 2's correct
legacy_unknown figure): legacy_unknown 20,533 + BR 9,420 + SC 5,947 + MN 19,178 (HAT-only,
mask-exempt, passes at 100%) + Moreton 9,228 = **64,306**, down from 134,372 stored — ~48% overall
survival.

**Raised, then resolved same session: does `WOFS_FREQ_MIN=0.2` still match the accuracy bar now
the true (smaller) surviving population is visible?** Resolved as NOT an open decision — the
density Aaron reviewed and accepted in v16.55's item-3 visual check (residual blobs = legitimate
canal/lake water agreeing under both OSM and WOfS, not under- or over-removal) was already
produced by these exact real numbers; nothing rendered on-device has changed between "before this
diagnostic" and "after." No threshold change queued.

**Task 2 — pan-lag timing measured, both passes agree on pool-size-not-viewport scaling** (~7x N →
~8.3–8.5x `buildSampleIndex()` time, stored-count pass and real-post-filter pass consistent). Real
per-pan cost estimated at the time: full-pool pan ≈78–100ms, single-region pan ≈9–10ms — **NOTE:
this estimate double-counts a call and is corrected downward in v16.57**, see below. Caveat stood
from the start: Node/V8 desktop timings, not iOS JSC — relative scaling expected to transfer,
absolute ms unconfirmed on-device. Not built this session, measurement only —
`poolVersion`-keyed caching (same pattern as `_r0Cache`/`_idwCache`) is the indicated fix, pending
Task 3's follow-up.

**NEXT:** Task 3 (confirm whether `buildShade()`'s two `buildSampleIndex()` calls share identical
inputs) and Task 4 (investigate a "circle blob" density pattern Aaron flagged at Port of Brisbane
on desktop) dispatched same session — see v16.57. MN v3 Noosa-OSM fetch and Noosa tide-port
wiring remain queued, unaffected, order-agnostic.*

---


*v16.55 · 31 Jul 2026 — planning chat, no build. Build stays `2026.07.30a`. ON-PHONE CHECK for the
Option 3 mask (per the v16.53 checklist) reviewed against 18 screenshots. **Items 2 and 4 PASS,
closed.** MN unchanged: exactly 19,178pt in the Imported-depths panel, matching the v16.34 export
size — exempt by construction (`okMASK` never calls `maskWater()` for `maroochy_noosa`), confirmed
live. Legacy Bargara/Woongarra depths intact: Innes Park / Nudibranch Tip taps (CPZ06, Great Sandy
MP) both returned live depths (≈5.2–5.7 m across two taps at different tide states). Panel confirms
there is NO separate `woongarra`-tagged dataset — all Bargara-area data sits inside "Restored
backup (pre-region-tagging)" (`legacy_unknown`, 55,660pt, unchanged). **The `woongarra` mask box
(`−24.98..−24.66, 152.30..152.60`) therefore has zero dataset customers by construction** — the
only points ever mask-tested inside that bbox belong to something other than the exempt
`woongarra`/`maroochy_noosa` regions, and the only candidate present is `legacy_unknown`, which
passed. Not urgent to remove; logged for awareness.

**MAJOR — v16.53's measured mask-effect figures were validated against the wrong dataset, need
re-measurement.** Real on-device stored counts, read directly off the Imported-depths panel (sum
matches the app's own "134372 points loaded across all regions" label exactly): legacy_unknown
55,660 / Brisbane River 21,126 / Sunshine Coast 17,806 / Maroochy·Noosa 19,178 / Moreton
Bay·Redcliffe 20,602. v16.53's "HAT-surviving pre-mask" figures (BR 68,246 / SC 57,050 / Moreton
33,424) each EXCEED these totals — structurally impossible, since a HAT-surviving subset can't
outnumber the full stored pool it's drawn from. Most likely root cause, matching the same bug class
the r0 session already caught once (144,474-vs-113,557, harness omitting the app's 25k-per-CSV-parse
auto-thin loop): the v16.53 validation harness almost certainly ran against the pre-thin v3 CSV
export files, which do match the 68,591/57,565/33,751-point sizes logged at v16.52 import time — not
against on-device storage after the app's per-parse cap thinned BR/SC/Moreton further on import.
Maroochy/Noosa was unaffected because its bake-time export was already pre-thinned to 19,178 (under
the 25k cap), so CSV size and on-device size happen to coincide there. **The 51.7% removal / 0.87%
false-paint / +93.7 kB headline from v16.53 is therefore unverified against real stored data —
re-run the harness against the actual 21,126/17,806/20,602-point datasets before citing those
figures again.**

**Item 5 (pan feel-check): FAIL, new finding.** Real, reported lag on a wide-zoom pan spanning
Brisbane River → Bargara. Not expected — the mask runs on pool rebuild only, never per-frame, so
it's unlikely to be the direct cause; prime suspect is the pre-flagged v16.51 backlog item (c):
`ptsBounds(pts)` and `buildSampleIndex()`/`sIx` inside `buildShade()` still run O(n) over the full
pool on every call, uncached on `poolVersion` — and the pool is now larger post-flats-layer and
post-mask than when that item was logged as "not queued, Aaron reports panning acceptable." Open
scoping question before dispatch: is a LOCAL single-region pan (e.g. around Redcliffe) still fine,
or is it slow everywhere now — determines whether this is the bounds/index full-scan theory or
something else.

**Item 3 (visual scan): qualitative pass, with one refinement and one new finding.** Most of the
"random inland blobs" Aaron flagged are canal estates and permanent lakes (Twin Waters/Bli Bli
corridor, Minyama) — genuinely wet under BOTH OSM and WOfS, so STRICT-AND is correctly painting
them; this is not mask residual, since the two sources agree there (unlike the golf-lake/canal-
estate disagreement case the v16.43 spike used to justify AND over either source alone — here both
sources are simply right). Separately: **Edgewater Village Lake** (near Bli Bli/David Low Way)
shows a HAT-based tidal-exposure tag ("dries earliest") despite appearing, from the imagery, to be
a landlocked residential/ornamental lake with no visible tidal channel to Petrie Creek. If
unconnected, this is a scope gap in the flats-layer HAT-banding logic — it labels any water body the
mask passes as tidally exposed, without checking tidal connectivity — not a land/water mask defect,
since the lake is genuinely wet and correctly painted. Can't confirm connectivity from imagery
alone; needs the lat/lng-readout backlog item below or a manual coordinate check. Low priority —
cosmetic mislabel, no legality/safety assertion involved.

**Confirmed clean:** `woongarra_imported_v1` and `woongarra_imported_rollback_v1` both absent from
`storage_check.html` — the v16.51/v16.52 cleanups held. **New backlog, low priority:** lat/lng
readout on the depth-tap popup (Aaron's request — makes future on-phone checks reportable with
coordinates instead of screenshots, would also resolve the Edgewater Village Lake question
directly); storage headroom — `storage_check.html` now reports 4995.5 KB / 4.88 MB across 20 keys,
entering the same range that caused the v16.35 quota-exceeded incident — recheck before the MN v3
clip (+~491 kB projected) or the Noosa OSM-only fetch land.*

---


*v16.54 · 30 Jul 2026 — planning chat, no build. Reviewed the Option 3 build (v16.53): build is
sound — measured figures reconcile arithmetically (177,898→85,894 = 51.7% removal checks out;
+93.7 kB matches the 2,149,778→2,245,730 byte delta; per-dataset percentages all correct), two
real bugs were caught and fixed mid-build rather than shipped, and residual/caveat framing is
honest throughout. **ONE CORRECTION to v16.53's "NEXT JOB" claim, applied here before it gets
cited as fact:**

**MN v3 clip does NOT yet have full OSM coverage — v16.53 overstated readiness.** MN is EXEMPT
from Option 3's mask (`REGION_MASK_EXEMPT={woongarra:1,maroochy_noosa:1}`), so `okMASK` returns
`true` for it without ever calling `maskWater()` — meaning no OSM tiles were fetched for MN's own
footprint. The `seq_coast` box built for SC/Moreton (`−27.35..−26.34`) only reaches as far north
as Bli Bli/Maroochydore; MN's full extent runs to `−25.89` (Noosa). So
`data/raw/_landmask_spike/tiles/` has OSM coverage for roughly the SOUTHERN HALF of Maroochy/Noosa
(where it overlaps `seq_coast`), not the Noosa half. **MN v3 clip needs a supplementary OSM-only
fetch (`~−26.34..−25.89`, reuse `tools/landmask_fetch.py`'s OSM path, no WOfS/mask-build needed)
for the Noosa gap before it can assume full coverage** — correct MN v3 prerequisite: confirm/
extend OSM coverage first, don't assume v16.53's tiles are sufficient as-is.

Noosa tide-port wiring is unaffected by this (mechanical, BoM TP021, no OSM dependency) and can
proceed independently, in either order.*

---


*v16.53 · 30 Jul 2026 — **OPTION 3 STRICT-AND LAND/WATER MASK SHIPPED (runtime path). Build
`2026.07.30a`.** Closes the v16.47.3 authorisation. A sample now counts as paint/read evidence only
where OSM water polygons AND DEA WOfS frequency ≥ `WOFS_FREQ_MIN` (0.2) BOTH call it water —
additive to the v16.44 HAT gate and the v16.25 R0/R1 ramp, neither of which was touched.

**HEADLINE, read this before opening the app: the mask removes 51.7% of the HAT-surviving pool**
**[SUPERSEDED — see v16.56 for real figures: BR/SC/Moreton mask-surviving 9,420/5,947/9,228, real
runtime pool 64,306. The 51.7% REMOVAL RATE below is still correct; the ABSOLUTE counts are not —
this harness measured pre-thin CSV exports, not on-device data.]**
(177,898 → 85,894 across the repo-visible on-device datasets). Per-dataset: BR flats 68,246 → 32,426
(−52.5%), SC flats 57,050 → 18,807 (−67.0%), Moreton flats 33,424 → 15,483 (−53.7%), MN v2 19,178 →
19,178 (−0%, exempt). This is the intended effect — that population is the sub-HAT "messy tier"
Option A knowingly kept painting — but **expect visibly less flats paint on BR/SC/Moreton**, not a
subtle change. Consistent with the spike: strict-AND retains only ~30% of the messy tier (measured
28.16% here vs the spike's 30%).

**Wired as ONE conjunct in `depthSamples()`, not five call-site edits** (Aaron's call after Step 0
recon). The v16.44 HAT gate was already a single pool filter, and all five v16.25 gate call sites
draw from that pool — `buildShade()` (`index.html:2007`), tap-to-read (`:2442-2443` handler →
`openDepthRead()` `:2425`), `findDeepest()` (`:2454`, inner probe `:2460`), `buildAutoContours()`
(`:2485`), desktop hover-readout (`:3189`) — all via `depthSamples()` directly or through
`idwDepthAt()` (`:2414`) → `idwIndex()` (`:2409`). The slope-chain tool (`:1868`) inherits it for free
exactly as it already inherits okHAT. One conjunct reaches all of them by construction, inherits
`_poolCache`'s `poolVersion` memoisation with no new cache machinery, and makes "can only remove
evidence" structural rather than five things to verify. Lines touched (and ONLY these):
`REGION_MASK_EXEMPT`/`importedEx` `:2215-2216`, `rebuildImportedFlat()` `:2217`,
`LANDMASK`+`lmBits()`+`maskWater()` `:2289-2377`, `depthSamples()`'s `okMASK` declaration `:2379` and
its single use `:2384`. Build string `:1033` + `:1072`.

**`source_type` could NOT carry the bathymetric exemption — this was a real trap.** `REGION_SOURCE`
maps `legacy_unknown:'bathymetric'`, and `depthSamples()` hardcodes `st:'bathymetric'` for own pins
and contours, so `'bathymetric'` is simultaneously the genuine-sounding tag AND the untagged default.
A literal `st!=='bathymetric'` skip would have exempted the 55,660-pt legacy blob — the one dataset
this was made runtime to reach. Exemption is therefore keyed on REGION: `REGION_MASK_EXEMPT=
{woongarra:1,maroochy_noosa:1}`, plus own pins/hand contours (deliberately: deleting depths Aaron
placed himself because a 30 m raster disagrees would be wrong). `'sonar'` does not exist anywhere in
the codebase — only `bathymetric`/`topographic`.

**Measured figures, from the ACTUAL SHIPPED JS decoder** (a Node harness loading the real `LANDMASK`
block + `lmBits()` + `maskWater()` out of `index.html`, not the offline Python — the two agreed on
**0 / 13,231** points):
  - **dry→water (false paint): 32/3,684 = 0.87%** (spike 0.79%)
  - **wet→water (coverage kept): 7,940/7,981 = 99.49%** (spike 99.74%)
  - messy→water: 426/1,513 = 28.16% (spike 30%)
  - Fidelity vs the spike's per-point vector verdicts: 97.78% agreement (292 disagreements of 13,178)
  - All 4 named dry probes → land ✓ (Twin Waters GC, Sunshine Motorway, Bli Bli, Maroochydore CBD)
  - **All 9 v16.41 stale-popup offshore locations → water ✓** (coverage preserved where it matters)
  - Maroochy Wetland Sanctuary 36-pt defect grid: **35 land / 1 water** — defect class suppressed,
    beating the spike's OSM 31 / WOfS 34. The single water cell is the grid centre, which the spike
    also scored water (its own probe: OSM `water(poly)`, WOfS 0.98) — matched behaviour, not a regression.
  - **Real payload: +93.7 kB (0.092 MB)** — `index.html` 2,149,778 → 2,245,730 B. Comfortably inside
    the 0.3–0.8 MB budget, so no resolution coarsening was needed (per-region boxes alone did it).
  - Perf: RLE decode 9 ms cold (once), 159,907 `maskWater()` calls in 12 ms (0.08 µs/pt), 907 kB
    bitmap RAM. Runs on pool rebuild only — never per frame, never per pixel.

**Known accepted residual, and it is INERT:** the "Maroochy River mouth channel" probe
(−26.6555, 153.099) reads land where water is expected — the spike scored it identically (OSM `land`,
WOfS 0.0031), so it is inherited, not new. It is not an MN point (nearest MN sounding 167 m away), so
the bathymetric exemption does not cover it; the 110 `sunshine_coast` samples within 150 m are all
`d ≤ −2.24` and **already excluded by the v16.44 HAT gate**, so the mask removes 0 additional samples
there. Logged and not chased further, per instruction.

**Structural no-regression: PASS.** HAT+mask pool ⊆ HAT pool for every dataset, 0 violations — the
mask is a pure conjunct after the HAT test, so nothing excluded can reappear. Caveat stated honestly:
this holds for paint *extent*; interpolated *values* (`FD`) inside the surviving extent do shift as
dry-land contributors drop out of the IDW — that is the intended improvement, not a no-op.

**Two build defects found and fixed during the run — both would have silently shipped a wrong mask:**
  1. `overpass.osm.ch` is a **Switzerland-only** Overpass instance that answers Australian bboxes with
     HTTP 200 + zero elements. It silently wiped central Brisbane and Mooloolaba/Maroochy in the first
     full fetch. Removed; an empty result now requires either a second mirror's agreement or an
     independent WOfS open-water confirmation before being accepted.
  2. The ocean flood-fill **leaked**: seeding from wet box-edge cells let inland dams on the land side
     seed the fill, and land is one connected region, so 99.8%/93.2%/99.3% of each box filled as
     "ocean" — collapsing STRICT-AND onto WOfS-alone (2.04% false paint) and discarding the OSM half
     entirely. Replaced with OSM's actual coastline-direction invariant (land on left, sea on right;
     `cross = dx*vy − dy*vx < 0` ⇒ seaward), which is purely local and so immune to ways clipped at
     box edges. Also switched polygon rasterisation to `all_touched=False`: dilation was inflating
     false paint to 1.28%.

**Tooling now lives in the repo, deliberately:** `tools/landmask_fetch.py`, `tools/landmask_build.py`,
`tools/landmask_validate.py`. The v16.43 spike's `score_landmask.py`/`cohorts.js` were lost with the
session scratchpad because `data/raw/` is gitignored — the raw pulls and `score_results.json` survived
(all 13,178 labelled cohort points + 17 probes, which is what made this validation possible at all).
Do not put build scripts under `data/raw/` again. Long-run discipline: progress per tile with flush,
atomic checkpoint (tmp + `os.replace`) after every tile, resume verified by a real restart, smoke
tested before the full run; 15 tiles, 1,607 s, pids 12796 (smoke) / 16160 / 240 / final run 3.

**Mask geometry:** three boxes, not one — woongarra (−24.98..−24.66, 152.30..152.60), seq_coast
(−27.35..−26.34, 153.02..153.22; SC+Moreton merged, their union is smaller than two separate boxes),
brisbane_river (−27.66..−27.27, 152.72..153.34). 0.54 deg² total vs 3.1 deg² for one combined box.
Outside every box `maskWater()` returns **true (pass)** — load-bearing: MN reaches north to −25.89,
past every box, and a future region must not silently go unpainted.

**ON-PHONE CHECK FOR AARON (build `2026.07.30a`):**
  1. **Should NO LONGER paint:** Sunshine Motorway golf course / Twin Waters GC (≈ −26.627, 153.083),
     Bli Bli suburb, Maroochydore CBD, Brighton-side suburban pockets. Tap → expect no depth read.
  2. **Should STILL paint:** all 9 v16.41 stale-popup offshore spots (e.g. −26.71118, 153.14156;
     −26.3636, 153.09836) — these validated as water. Maroochy/Noosa soundings must be COMPLETELY
     unchanged (region-exempt) — this is the fastest single check that the exemption is working.
  3. **Expect a big visible reduction** in BR/SC/Moreton flats paint (~52–67%). Confirm it looks like
     dry-pocket removal, not holes punched in genuine channels/mudflats.
  4. **Legacy Woongarra depths — the one thing not verifiable offline.** The 55,660-pt legacy blob is
     `legacy_unknown`, which is NOT exempt, and it is presumed to span Bargara/BR/SC. It is phone-only
     and not in the repo (`quota_test_dummy_backup.json` is a 398k synthetic fixture, not it), so it
     could not be scored. **Check Bargara/Woongarra rock-ledge depths still read.** If Woongarra
     depths have thinned, add `legacy_unknown:1` to `REGION_MASK_EXEMPT`.
  5. Feel-check panning at Redcliffe and Maroochydore for any new slowdown — none expected (mask runs
     on pool rebuild only), so any lag is a real finding worth reporting.

**NEXT JOB:** MN v3 clip (≤200 m / native 25 m) — it wanted Option 3's OSM polygons, which now exist
in `data/raw/_landmask_spike/tiles/`. **[CORRECTED — see v16.54: this OSM coverage only reaches the
SOUTHERN half of Maroochy/Noosa. The Noosa half needs a supplementary OSM-only fetch first — do not
assume these tiles are sufficient as-is.]** Then Noosa tide-port wiring (mechanical, BoM TP021). **New
low-priority backlog item (not in scope, logged so it isn't lost): `_idwCache` (`index.html:2408`,
invalidation check `:2410`)
keys on `s.length`, not `poolVersion`** — a pool change that happens to preserve length would not
invalidate the read index. Pre-existing, untouched by this build, but the mask changes pool length so
it sits adjacent. Also still open: Redcliffe 2021 Hydrographic Survey extents inspection.*

---

*v16.52 · 29 Jul 2026 — planning chat, no build. FIELD VERIFICATION CLOSES v16.51's NEXT JOB: all
three flats-layer imports (BR REPLACE 68,591 pts, SC REPLACE 57,565 pts, Moreton MERGE 33,751 pts)
confirmed correct on-device — depths read OK, persisted through force-close/reopen (iOS
async-flush check passed). Legacy `woongarra_imported_v1` guarded delete button exercised — ~519 KB
reclaimed, closes the item open since v16.49.6. Version:2 backup exported post-import per standing
habit. Flats-layer arc (Phase A+B BR/SC + Phase A Moreton) is now fully shipped AND field-verified —
nothing pending on it. Build stays `2026.07.27a`; no code shipped this chat.

**NEXT JOB, build prompt drafted this session, ready to dispatch: Option 3 (STRICT-AND land/water
mask, runtime path, authorised v16.47.3).** Unblocked now the flats layer is done (per the
flats-before-mask reorder logged mid-arc). Full build prompt handed to Aaron for Claude Code; key
requirements captured here so this entry stands alone if the prompt itself isn't kept:
  - Spec unchanged from the v16.43 spike / v16.47.3 authorisation: a sample counts as
    paintable/readable water only if OSM water polygons AND DEA WOfS (frequency ≥ 0.2, named
    tunable constant) both agree it is water. Expect ~0.79% false-paint / 99.74% wet-coverage kept
    — measure against the real shipped code, don't assume the spike's number transfers unchanged.
  - Runtime, not bake-time — the only way to reach the untagged legacy 55,660-pt blob (phone
    localStorage only, not in the repo, cannot be re-exported).
  - Cache the OSM+WOfS verdict **per sample, keyed on `poolVersion`** — same pattern as the
    `.r0`/`_r0Cache` memoisation — so this doesn't reopen the per-pan performance cost the
    r0/pool-cache arc just closed. Evaluated once per unique point on import/replace/clear, not
    per render frame.
  - Wire in as an ADDITIONAL required condition at all FIVE `v16.25` gate call sites
    (`buildShade()`, tap-to-read, `findDeepest()`, `buildAutoContours()`, desktop hover-readout) —
    additive to the existing HAT gate (v16.44) and R0/R1 distance ramp, never a replacement.
  - Reuse the v16.43 spike's proven OSM/WOfS sourcing+scoring code (`data/raw/_landmask_spike/`)
    rather than re-deriving from scratch.
  - Never touches `zoneAt()`, zone determination, or any legality assertion — cosmetic paint/read
    gate only.
  - Data budget: +0.3–0.8 MB on the single file, combined bbox = the four current regions
    (Woongarra/Bargara, Moreton Bay/Redcliffe/Bribie/Pumicestone, Sunshine Coast/Maroochy/Noosa,
    Brisbane River) — report the real payload size, don't assume it lands in-budget.
  - Re-validate on the real shipped runtime code (not just trust the offline spike): the same
    13,178 pilot points, all named dry probes, all 9 stale-popup locations, the Maroochy Wetland
    Sanctuary 36-pt defect grid — AND confirm genuine bathymetric soundings (MN, Woongarra) are not
    false-negatived by the mask, since those datasets weren't the spike's main focus.
  - Standard discipline: both script blocks `node --check`; Leaflet block byte-identical;
    `zoneAt()`/dragend safeguard confirmed absent from the diff by `grep`, not eyeballed; build
    string bumped; `git status` clean at close. Apply LONG-RUN DISCIPLINE (progress/checkpoint/
    resume, PID reported) if the OSM/WOfS fetch+processing exceeds ~100 files or ~10 minutes.

MN v3 clip (≤200 m/native 25 m) sits behind this build (needs Option 3's OSM polygons); Noosa
tide-port wiring (mechanical, BoM TP021, independent of the above) sits behind that. Backlog aside,
cheap, no urgency: Redcliffe 2021 Hydrographic Survey extents inspection (item a).*

---

*v16.51 · 28 Jul 2026 — MORETON BAY / REDCLIFFE PHASE A COMPLETE. Data only — **no `index.html`
change, build stays `2026.07.27a`**; the v16.50 renderer already handles `moreton_bay` and its
`source_type` was wired then. One new CSV ready for Aaron's phone-side import.

**`data/moreton_bay_flats_v1.csv` — import as MERGE into "Moreton Bay / Redcliffe"** (new region, so
MERGE is correct here; BR/SC needed REPLACE only because they had mislabelled "depth" data to
displace). **33,751 points, 0.95 MB.** Device auto-thin (`MAXP=25000`) applies as usual.

**This delivery is markedly more fault-affected than BR/SC — the class-9-adjacency check earned its
keep here.** Full audit over all 193 tiles (`audit_class2.py`, reused unmodified, PID 1514, ~8 min):
- **149 of 193 tiles HIT (77%)**, 38 `clean_by_absence` (no class-9 points at all), 6 `clean`.
- **6,365 flagged cells, 3.978 km²** of misclassified water surface, max density 4,797 ground points
  in a single 25 m cell.
- Mask re-scan (`hybrid_mask.py`, PID 1239, 353 s) dumped every flagged cell key: **6,365 cells,
  0 count mismatches** against the audit — clean cross-validation, same as BR/SC.
- Flagged points were **dropped, never reclassified**. 6,861 of 88,768 extracted cells removed
  (7.73%).

**Pipeline (extract → mask → band → CSV), faithful to BR/SC with two approved deviations:**
- class-2 ground only, elevation clipped −3.0..+5.0 m AHD, 25 m cells, rank priority (2018 rank 1
  beats 2014 rank 2; equal rank pools z and takes the median) — identical to `process_tiles.py`.
- **Deviation 1:** outer zip resolved from `tile['src']` instead of the hardcoded `SUNSHINE_DIR`.
  No behaviour change for the 184 Sunshine-Coast-bundle tiles; without it the 9 Brisbane-River-bundle
  tiles fail outright.
- **Deviation 2:** AHD→LAT offset taken from the manifest's **per-tile** `offset` (184 tiles at 1.26
  Beachmere, 9 at 1.32 Brisbane Bar), not `export_csv.py`'s latitude-bucket function — that function
  buckets every Moreton tile to 1.26 and was built for the SC/Noosa delivery. Same "per-group, not
  blanket" principle as Brisbane River's Brisbane Bar/Bremer split.
- Banding uses **per-point `nearestPort()`** against the `FLATS_BOUNDS` already shipped in
  `index.html` — no new tide computation. Port split of the written points: **Mooloolaba 24,025 /
  Brisbane Bar 9,726**, confirming a region-wide port would have been wrong for 71% of this region.

**Moreton's own figures, computed fresh against this delivery (NOT carried over from BR/SC):**
| Metric | Moreton Bay / Redcliffe |
|---|---|
| cells extracted | 88,768 |
| dropped by flagged-cell mask | 6,861 (7.73%) |
| post-mask points | 81,907 |
| **dropped above HAT** | **48,156 (58.8% of post-mask)** |
| **written** | **33,751** (0.95 MB) |
| **below LAT** | **0** |
| gold / amber / teal / blue | **22,357 / 9,489 / 1,905 / 0** |
Above-HAT at 58.8% is lower than BR (63.7%) and SC (65.8%) — this delivery sits closer to the
intertidal zone. Band 4 (blue) is again **empty**, consistent with NIR's inability to see underwater;
that is now 3 regions running (BR 2, SC 0, Moreton 0) and should be treated as the expected result.

**JS/Python cross-check performed again, and it caught something again.** First pass disagreed by
3 points (teal↔amber). Cause: the build script banded on the **unrounded** depth while the CSV ships
values rounded to 2 dp — and 247 points sit within 6 mm of Mooloolaba's 0.775 m boundary. Re-banding
in Python **from the written CSV** reproduces `flatsBand()` exactly (22,357 / 9,489 / 1,905 / 0, and
0 rows above HAT). The CSV was never wrong — only the first summary was. **Lesson worth keeping:
band counts must be computed from the rounded values that actually ship, since that is all the
renderer ever sees.** Do not skip this cross-check; it has now found a real discrepancy on 2 of 3
regions.

**NEXT JOB:** import the three CSVs on-device and eyeball the flats layer in the field — that is the
first real visual confirmation the 4-band scheme reads correctly at the map scale Aaron actually
uses. Everything upstream is now shipped and verified. **Also still open:** the v16.49.6 guarded
legacy-`woongarra_imported_v1` delete button was never exercised (~519 KB legacy key possibly still
on-phone; cheap, one-tap, no urgency). Bundle-accurate raw-directory renaming remains deliberately
unscheduled (see v16.50).*

---

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
`Moreton_Bay_2018_LGA`), MGA56 E505000–519000 / N6976000–7021000, spread across five `DATA_*.zip`
archives (110.6 GB total). *(Corrected: these are legitimate multi-region ELVIS order bundles, NOT
Moreton-specific deliveries misfiled under the wrong directory — the earlier "misfiled" claim was
wrong. Moreton tiles are a minority slice of each: 9 of 819 tiles in `DATA_2047341.zip` (the rest is
625 Brisbane + 185 Ipswich), 17 of 74, 47 of 92, 85 of 152, 138 of 150. `audit_class2.py` selects
tiles by manifest (`AUDIT_MANIFEST`), not by directory, so no move was needed or performed.)*
**Rename investigated and REJECTED:** manifest `src` paths are hardcoded absolute
(`D:/Claude Code/data/raw/Brisbane-River`, `.../Sunshine-Coast`) across all 1,375 entries, so moving
the zips would orphan every manifest entry and fail every tile. If bundle-accurate directory naming
is wanted later for human readability, that is a separate deliberate job (rename dirs + regenerate
manifests to match) — not a Moreton prerequisite, not scheduled.
This delivery has **never** had the class-9-adjacency density check (v16.17–v16.18)
run on it — mandatory, drop flagged points, never reclassify. **Smoke test passed** (4 tiles spanning
3 different bundles including the 64 GB one): 3 HIT / 1 `clean_by_absence`, same misclassified-water
signature as BR/SC (e.g. class-2 median −0.56 m against class-9 median −0.70 m in the same 25 m cell,
1,428 ground points) — the fault is confirmed present in this delivery, though affected areas per
tile are small (0.001–0.023 km²). >100 tiles and multi-hour, so LONG-RUN
DISCIPLINE is confirmed required: smoke test on a small subset first, progress print every N tiles
with flush, atomic checkpoint every N, resume-from-checkpoint, real PID reported. Reuse the exact
banding + renderer logic already proven here — **per-point `nearestPort()`, NOT a region-wide port**:
Moreton tiles span lat −27.335..−26.928 and split **122 Mooloolaba / 71 Brisbane Bar**, so a
region-wide "Brisbane Bar throughout" would repeat the Sunshine Coast bug at 63% instead of 14.6%.
Output: one new-region **MERGE** CSV (`moreton_bay`, source_type already wired).

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
13. **RESOLVED (v16.61) — `git rm --cached` + `.gitignore`, committed `dff2999` (2 Aug 2026).**
   History: raised v16.26 as an untracked file of undecided origin; swept into the repo by
   **v16.48's STEP 0 repo-hygiene sweep** against a standing "project knowledge only, never the
   repo" note; reopened as a decision at v16.59. Aaron's call was to untrack it. `.gitignore` now
   carries both `guya_species_qld_v3.md` and `*_intertidal_ground_v1.csv` (the latter pre-empts
   re-entry of the two contaminated v1 CSVs, which have already resurfaced once). File remains on
   disk, untracked, 10,790 bytes. **This is an ANTI-DRIFT fix, not a privacy fix** — `git rm
   --cached` leaves the file in git history and the repo is public (it serves Pages). History was
   deliberately NOT rewritten: the content is benign species-passport seed data and a rewrite
   isn't warranted. Do not re-file this as a privacy remediation. CLOSED.
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

**Species seed:** `guya_species_qld_v3.md` — kept in project knowledge (private), not the repo. Repo stays just the shipped `index.html`. **[SUPERSEDED — see v16.59. The file WAS committed to the repo by v16.48's STEP 0 repo-hygiene sweep on 22 Jul 2026 and is tracked there now. The sentence above describes the pre-reversal intent, not current state. Whether it stays in the repo is an open decision for Aaron — do not act on this line as written.]**

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
