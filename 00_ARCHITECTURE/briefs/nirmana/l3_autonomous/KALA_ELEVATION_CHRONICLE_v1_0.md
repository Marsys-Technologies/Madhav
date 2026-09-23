---
artifact: KALA_ELEVATION_CHRONICLE
canonical_id: KALA_ELEVATION_CHRONICLE
version: "1.0"
status: CLOSED_HISTORICAL
date: 2026-09-24
supersedes: "KALA_ELEVATION_BLUEPRINT_v1_0.md §11.1–§11.28 (v1.2 → v3.5), moved here verbatim at blueprint v4.0"
purpose: >
  The chronological record of what the 23–24 September readiness campaign found, retracted and
  corrected, in the order it happened. Read for provenance and for the failure-mode ledger.
  The blueprint carries the CURRENT truth; this carries how it was reached. Nothing here is
  authoritative over the blueprint where they differ — where they differ, the blueprint was
  updated deliberately and this was not.
retained_in_place_per: "ONGOING_HYGIENE_POLICIES_v1_0.md §A (archival retain-in-place)"
---

# Kāla elevation — the chronicle (verbatim §11 of the blueprint, v1.2–v3.5)

*Twenty-eight addenda written across one campaign, each verified or retracted in place. The
consolidated failure-mode ledger is §11.23; the governance finding that outranks the rest is
§11.26's closing paragraph.*

## §11 — Addendum (v1.2, 2026-09-23): the node-convention split, and M-3

Opened by the Saṅgam session's FINAL packet, corrected and extended by the Gochara and Kshetra
sessions, and re-measured independently here. **Two claims in v1.1 of this section were wrong and
are corrected in §11.4.** Everything below is marked verified-here or carried-unverified.

### 11.1 The node convention is split FOUR ways, and the store disagrees with its own contract

| Surface | Convention | Evidence (verified here unless marked) |
|---|---|---|
| **L1 natal facts** (`ga_positions`) | **MEAN** | `pyjhora_adapter/positions.py:21-22` `_USE_TRUE_NODES = False`, "classical convention"; `:61` passes it. Three further declarations reported by the Gochara session (`vargas.py:21,65`; `_jhora.py:23-55` patching `drik.sidereal_longitude` to `MEAN_NODE`) — *carried, not re-verified here*. |
| **L0 `ephemeris_daily`** (`bg_ephemeris`) | **TRUE — under a "mean" contract** | `brahmagyan/l0_ephemeris.py:77` `{"name":"Rahu","swe_id":11}` commented *"Mean North Node"*; `:289` `swe.calc_ut(jd, 11, ...)`; docstring `:8` "Rahu (mean)". **`swe.MEAN_NODE = 10`, `swe.TRUE_NODE = 11`** — so id 11 is TRUE. Empirically decisive: stored tropical longitude matches Swiss TRUE on **5 of 5 sampled dates** (residual ≤ 0.10°) and MEAN on 0 of 5 (off by up to 1.47°). |
| **Transit engine** `pipeline/transit_search.py` | **TRUE** (correctly labelled) | `:10`, `:64` `"Rahu": 11, # swe.TRUE_NODE` |
| **Legacy `brahmagyan/ganita/l1_positions.py`** | **TRUE** | `:128` `("Rahu", swe.TRUE_NODE)`. Importers confirmed: `l1_dashas`, `l1_strength`, `l1_divisionals`, `l1_sensitive_points`, `l1_panchanga_birth`, `graha_sthana_writer`. **Whether each importer's persisted output actually diverges is UNVERIFIED** — a bounded L1 check, not a claim. |

**The store contradicts its own declared contract.** Migration
`624_nirmana_l0_ephemeris_probe_contract.sql:30` pins `"node_mode": "mean"`. The data is true node.
A contract with no detector that can falsify it is an unearned signal (§N.8) — here it stayed green
for a year over data it never checked.

**And the L0 closure receipt records a value the table does not hold.** `DAR_CLOSE_v1_0.md:20`:
*"ephemeris_daily: Rebuilt with MEAN_NODE Rahu/Ketu; Rahu at 1984-02-05 = 49.04° Taurus/Rohiṇī
(FORENSIC-verified delta 0.01°)."* Measured: stored tropical 73.629058 − ayanāṃśa 23.6349 =
**49.9941° sidereal**; Swiss MEAN for that instant = **49.0405°**. The receipt's 49.04 is *exactly*
the mean value — so it describes an intended computation, not the stored result, and its
"FORENSIC-verified" claim was never compared against the table. **Routed to L0's owner as a
receipt-vs-data discrepancy. No L3 session touches L0.**

**It IS visible in a reading, and the figure is measured.** At the birth instant (1984-02-05
05:13 UT, Lahiri, real Swiss — `retflag 258`, no Moshier bit):

| Convention | Sidereal | Rohiṇī pāda | Margin to the 50.0000° boundary |
|---|---|---|---|
| **MEAN** (analytic; what L1 stores) | 49.033044° | **3** | 3492″ |
| **TRUE** (what the store and the scanner carry) | 50.049248° | **4** | 177″ |

A mean-vs-true ruling therefore **moves this native's Rāhu from Rohiṇī pāda 3 to pāda 4** as a
measured fact. The 177″ margin is an order of magnitude above any plausible ephemeris-version
difference, and the mean figure reproduces L1's own served `RAH_MEAN` (49.0330441°) to **0.00″**.
Instant: 1984-02-05 05:13 UT (10:43 IST), `jd 2445735.717361`. A cited number carries its instant.

**And store-is-TRUE is exact, not statistical.** Computed at **noon UT** — the epoch
`l0_ephemeris.py:164,278` actually uses — with `set_ephe_path('/tmp/se1')`, real Swiss reproduces
the stored knot on **5 of 5 dates to 0.00 arcsec at six decimals**, while mean is 317–5380″ away.
There is no residual to caveat.

### 11.2 The ruling needs a paired disposition, not just a convention

"Rule mean node" is **not** a one-line hub repair, because the store itself is true. Whatever is
ruled, the native must also rule *where the repair lands*:

| Option | What it costs |
|---|---|
| **(a) Rebuild `ephemeris_daily` mean-node** | Matches the DAR receipt's own claim; touches a frozen layer and every downstream consumer of the knots. |
| **(b) Keep the knots TRUE; derive mean Rāhu/Ketu analytically at read time** | Cheap, no L0 rebuild, auditable against Swiss — but store and derivation then disagree by ~1° and that must be **declared per row**, never silent. Recommended by the Gochara session (its N-4a) and the Saṅgam session; **I concur.** |
| **(c) A declared mixed-frame contract per consumer** | Most honest about current reality, most surface area to police. |

Whichever is ruled, the paired obligations are: repair migration 624's probe so it *detects* rather
than declares; correct the `l0_ephemeris.py` comment and docstring; and decide the legacy
`l1_positions` chain separately. Riding with it: the **cusp frame** (L1 stores Placidus; the Saṅgam
plan assumed Śrīpati) — which the Kshetra session confirms does not touch Kshetra (whole-sign
arithmetic only, `writer.py:1783`).

### 11.3 M-3 — two producer paths, and E1/E3 is **not** unblocked by either yet

If the native re-affirms June §4.5 (no ephemeris scan inside Saṅgam; Saṅgam consumes pre-computed
directed contact events; `planet` as a list), a directed contact-event producer becomes an upstream
obligation. Two shapes are now on the table:

- **Path A — a bounded amendment to `transit_search.py`** under one named owner (frame/ayanāṃśa/node
  arguments; directed special-aspect search). Faster; **edits a frozen shared hub**.
- **Path B — a new pure module** (`services/gochara_kernel`), proposed in the Gochara brief v1.2:
  emits directed contact episodes natively (t_in / t_exact / t_out, bracket, tolerance, branch, orb
  + orb_source, plus a Search-coverage row per partition), with frame/ayanāṃśa/node as arguments by
  construction. Edits neither `transit_search.py` nor `ka_dasha_kala` (both in its `must_not_touch`).
  Saṅgam E1/E3 would bind to the kernel; Kshetra S0 could adopt it later without a second amendment.

**Path B's own caveat, stated by its author and carried verbatim:** the kernel becomes a shared hub
the moment two assets bind to it — *"the exact property that made `transit_search` hard to change"* —
so it must carry an additive-only signature rule and a versioned contract from day one. And it
**exists only if the native approves that brief's N-5 (served-product owner) and N-7 (persisted
Contact ledger), both unruled**. If N-7 is refused, the obligation reverts to Path A and still needs
an owner. **Therefore E1/E3 must not be recorded as unblocked by a proposal.**

**The owner is the native's to name.** All three sessions have declined to name it between
themselves — correctly. The native rules shape *and* owner together.

**Directed aspects — an earlier item in this section is WITHDRAWN.** v1.2 recorded a
"directed-aspect gap at the engine, unexercised in served data." Re-verified, none of that holds:
`find_aspect_events` computing `(target_longitude_deg + aspect_deg)` (`transit_search.py:320`) is
**correct** — dṛṣṭi is directional, and a symmetric search would be the defect. The Gochara path
already uses the classical per-graha table: `gochara_grammar/primitives.py:342-343` passes
`SPECIAL_DRISHTI_DEG.get(planet, _DEFAULT_DRISHTI_DEG)` into it (Mars `[90,180,210]`, Jupiter/Rāhu/
Ketu `[120,180,240]`, Saturn `[60,180,270]`, everything else `[180]`, BPHS Ch.26 cited at
`:189-196`). And it **is** exercised: `drishti_contact` appears on 379 of 914 served generation-3.0
rows. My "zero rows carry an asymmetric degree" was measuring `activity_terms`, whose keys are
`primitive, transit_planet, target_ref, target_weight, event_datetime_ist, orb_decay, p_i` — the raw
aspect degree is **not a field it has**. Absence in a field that cannot hold the value is not absence
of the value.

**The real defect is a Saṅgam call-site, not a producer gap:** `services/ka_sangam/engine.py:464-466`
passes the symmetric generic set `[0,60,90,120,180]` for the benefics Jupiter and Venus, where
Jupiter's classical dṛṣṭi is `[120,180,240]`. Attributing this to the Gochara producer would send
the fix to the wrong owner. It belongs in Saṅgam's R-series. (Found by the Gochara session; verified
here.)

### 11.4 Corrections to this session's own v1.1

1. **Kshetra is not a `transit_search` position reader.** v1.1 listed three readers. Verified:
   `services/ka_kshetra/stage0_kinematics.py` imports only the `MEAN_MOTIONS` constant (`:746`) for
   dwell normalisation — **zero** scan/search call-sites — and reads all nine bodies from
   `ephemeris_daily` through its own Hermite spline. Correct position readers of `transit_search`:
   **`ka_gochara/service.py` and `ka_sangam/engine.py`**. Kshetra is an `ephemeris_daily` reader —
   which, per §11.1, still makes it **contract-mean / store-true**, so it is affected, just at a
   different repair site. (Raised by the Kshetra session; its own "Kshetra is mean/mean" conclusion
   is withdrawn by the store measurement.)
2. **The "242 rows" figure was wrong.** It summed two generations and two carriers without a
   generation filter. Correct: **232 of 914** at `g3_utkarsha` via `term_breakdown`, **50 of 87** at
   generation 2.0 via `active_sentences`. Raised by the Gochara session; reconciled here.

### 11.5 The shared branch

`l3/kala-elevation-readiness` is by use the shared L3 documentation branch. Committed docs there are
fine, **staged by name only**; uncommitted work belongs in the authoring session's own worktree.
Verified: the Saṅgam commits swept zero foreign files. The Kshetra session's user has since ruled:
both artifacts moved to `/Users/Dev/madhav-l3/kshetra` on `l3/kshetra-elevation`, and the readiness
worktree is clean again.

**One consequence of this session's own error, flagged for anyone citing it.** `origin/main` carries
`briefs/KSHETRA_ELEVATION_BRIEF_v1_0.md` at that session's **stale v1.0**, swept there by this
session's `git add -A` in `bd1a12e03` (PR #2713). It contains three findings its author has since
withdrawn — including the "Kshetra is mean/mean, already conformant" conclusion that §11.1's store
measurement overturns. Until that session's v4.0 lands as an in-place update, **anyone reading that
path on `main` gets the withdrawn version.** Do not cite it. This is why the staged-by-name rule
exists.

### 11.6 Carried but NOT verified by this session

**`bg_cohort` is CONFIRMED, and my earlier denial was my own measurement error.** Re-grepped
without truncation: `@register("bg_cohort")` at `:470`, `("Rahu", swe.TRUE_NODE)` at `:333`, and the
provenance string *"Lahiri ayanamsha; TRUE_NODE Rahu"* at `:159`; 691 lines, byte-identical to
`origin/main`. My v1.2 statement that the file had neither came from a grep I had piped through
`head -5`, which truncated away everything after line 106 — I then published that absence as a
finding against a peer's correct claim. The peer's own correction also stands and *strengthens* the
finding: `bg_cohort` does **not** import `l1_positions` (`:49`, `:105-106` say it independently
reproduces the formulas), so it is a **fifth independent TRUE_NODE declaration**, not a dependent
one. · Per-importer persisted
divergence in the `l1_positions` chain. · The century BUILD-PROTECTED "residue" timeline (error
stamped 2026-08-21 vs migration 588 applied 2026-08-23). · The 1.933° maximum over 1984–2084. · **No natal Rāhu
`longitude_sidereal` fact row exists** for the canonical chart at `lahiri_chitrapaksha` — so L1's
mean convention is confirmed by declaration and by the DAR arithmetic, not by a stored fact.

### 11.7 A gate rule this week produced: a Swiss-vs-kernel comparison is not a detector here

Raised by the Gochara session, and it generalises the §11.1 caveat. This environment ships no `.se1`
files, so `FLG_SWIEPH` silently falls back to Moshier and returns bit-identical values to a Moshier
call. **Any acceptance gate phrased "our kernel agrees with Swiss to N arcseconds" therefore compares
Moshier with Moshier where `.se1` is absent — it cannot fail, and under §N.8 it is not a detector at
all.** Production does carry real Swiss data (`Dockerfile:24`, `Dockerfile.pipeline:17`,
sha256-verified into `/app/ephe`), so the gate is meaningful there and vacuous here.

**Both backend inferences failed here, in opposite directions.** "Two flags return identical values,
therefore Moshier" was right by luck. "No `.se1` found, therefore Moshier" was right by luck too —
the files existed and the path was simply never set. **Only `retflag` survives both**: read it and
test the MOSEPH bit. Provision and checksum your own `.se1` rather than assuming another session's
copy persists — the one on this host sits under `/tmp`, placed by another session, and may not
survive a reboot.

**Measured over the whole domain, so "unbounded Moshier error" is retired — and so are two sparse
samples of it.** Moshier's true-node error against Swiss, computed at **every** noon knot from
1950-01-01 to 2100-12-31 (**n = 55,152**, `retflag` asserted Swiss on every call): **min −58.1″, max
+65.3″, worst 65.3″ on 1972-11-20.** Two earlier sparse estimates both under-reported it in the same
direction — a five-date sample said 18.1″, my sixteen-date decade sample said 32.5″, the truth is
**65.3″**, half as much again as my figure and over three times the other. **Independently reproduced by three
sessions** — measured by the Gochara session, reproduced here and by the Saṅgam session, each to the
arcsecond and the date.

That bound is what separates a reportable figure from an unreportable one, with the real ratios:

| Quantity | Margin | vs the 65.3″ bound |
|---|---|---|
| Natal pāda (birth instant) | 177.3″ | **2.7× safety — reportable even on Moshier** |
| Stored noon knot | 6.3″ | **10.4× over — not reportable on any backend** |

2.7× is a real margin but a thin one; state it as 2.7×, not as "well under".

**New rule, earned the same way as the other two: a sparse sample is not a bound.** The node's error
oscillates on timescales shorter than a decade, so decade spacing samples it about as badly as five
dates do. Two sessions each produced a confident bound from a sample and both were wrong in the same
direction; only measuring the full domain settled it. This sits beside *"a date is not an epoch"* and
*"a flag is not a backend"*.

**Consequence for the inherited 0.314″ spline figure:** 65.3″ is two orders of magnitude above it.
If the W2G V3 validation ran without `set_ephe_path`, it compared its spline against a reference
~200× coarser than its own claim, and the figure says nothing about Swiss-grade accuracy. Whether
that runner calls `set_ephe_path` is answerable from source and should be answered before 0.314″
anchors any gate. (Raised by the Gochara session.)

**Rule for every numerical acceptance gate in this campaign:** require `.se1` present, verify
`retflag`, and record the file checksums in the evidence, or the result is `NOT_RUN` — never `PASS`. Any inherited
arcsecond-level parity figure whose run environment is not established is `[UNVERIFIED]` until it is.
This is the same defect class as migration 624's probe (§11.1): a check that cannot return false.

### 11.8 Four measurement errors by this session, and the pattern

Recorded because the pattern matters more than the individual slips. (1) v1.1 listed Kshetra as a
`transit_search` position reader — it imports one constant. (2) v1.1's "242 rows" conflated two
generations and two carriers. (3) v1.2 denied `@register`/`TRUE_NODE` in `bg_cohort` from a grep
truncated by `head -5`. (4) v1.2's directed-aspect gap measured a JSON field that cannot hold the
value. All four are the same failure: **asserting from an incomplete read, then publishing the
absence as evidence.** The three asset sessions caught all four. The countermeasure that actually
worked was not care — it was other sessions re-measuring at the authority and saying so.

### 11.9 RETRACTED IN FULL — there was no session disagreement; the 332″ was my own epoch error

v1.5 recorded that two sessions' node computations diverged by 332 arcsec, called it unexplained,
and reasoned the disagreement might invert the pāda finding. **All of that is withdrawn.** Both
peers independently found the cause; verified here:

- **`l0_ephemeris` stores every knot at NOON UT** (`:164` *"Julian Day Number (noon UT)"*, `:278`
  `swe.julday(..., 12.0)`). I differenced against **midnight**. Midnight − noon for the true node on
  that date is **+332.3″** — precisely the "disagreement" I reported. Both hosts agree bit-for-bit
  at the same epoch.
- **This host *does* carry `.se1`** at `/private/tmp/se1`, and the production resolver
  `brahmagyan.l0_ephemeris._resolve_ephe_path()` returns `/tmp/se1` — its own documented
  development/CI candidate. `swisseph` finds them only after `set_ephe_path()`; without that call
  `FLG_SWIEPH` silently returns `retflag 260` (Moshier bit set), with it `retflag 258` — real Swiss.
  My "Moshier fallback" was true of *my calls*, not of *this host*.

Everything v1.5 derived from the phantom divergence is void: the "(A′) peer-offset" row, the claim
that the pāda finding inverts, and "weak evidence my local node is the outlier." Neither session was
an outlier. **§11.7's rule survives with a better detector:** never infer the backend from flags
matching or from `.se1` appearing absent — **read `retflag` and test the MOSEPH bit**, the only
thing a silent fallback cannot fool.

### 11.10 The epoch convention is undeclared too — the other half of the §N.8 finding

`ephemeris_daily` carries neither the node frame nor the knot epoch on the row. The frame is
declared *wrongly* (migration 624 says `"mean"`; the data is true — §11.1). The epoch is not
declared **at all**. That undeclared epoch fooled two independent sessions on one day, produced a
332″ phantom finding that reached v1.5 of this document, and was caught only because a third session
re-derived it from the builder source.

Both belong in one repair: whatever is ruled on the node, `ephemeris_daily` should carry its
**frame and its epoch, each with a detector behind it**, and migration 624's probe should verify
both against the data rather than assert them. A spline built on the wrong epoch assumption is wrong
by half a day — W2G's own validation note puts that at ~6.6° for the Moon.

**One conflation to drop from every sheet, including this one:** the "0.0059° from the boundary"
figure belongs to the **stored noon knot** — a transit sample on the birth date, not the natal
position. It says nothing about the natal pāda, which comes from L1's birth-instant computation
(§11.1). Two different quantities; only the natal one bears on a reading. (Raised by the Kshetra
session.)

### 11.11 A third undeclared convention: how the ayanāṃśa is applied (14.82″)

Found while reconciling a 15″ spread between sessions that was assumed to be a birth-instant
difference. It is not — it is **method**:

| Getting sidereal from Swiss | MEAN at 05:13 UT | vs L1's stored `RAH_MEAN` |
|---|---|---|
| `tropical − get_ayanamsa_ut()` (manual subtraction) | 49.028927° | **off by 14.82″** |
| `FLG_SIDEREAL` (Swiss's own transform) | **49.033044°** | **0.00″** |

**The gap is nutation in longitude, exactly.** Nutation at that instant is **−14.82″**, and the
method gap is **−14.82″** — identical to two decimals. `get_ayanamsa_ut()` returns the *mean*
ayanāṃśa; `FLG_SIDEREAL` applies the *apparent* one, which includes nutation. So the three sessions'
figures were never three measurements — they were **one value under two conventions**, and the
convention split we spent the day documenting reproduced itself inside our own instruments. Both
conventions put Rāhu in pāda 4 (177″ and 162″ margins), so the conclusion is convention-independent.
(Closed by the Gochara session; verified here.)

**L1's stored fact is the arbiter, and it validates `FLG_SIDEREAL`.** My manual subtraction — used
for every sidereal figure this session published before v1.7 — is the one that disagrees with what
L1 actually serves. Both natal figures in §11.1 are corrected accordingly (mean 49.028927 →
49.033044; true 50.045130 → 50.049248; margin 163″ → 177″). The pāda conclusion is unchanged; the
method finding is the durable part.

So three conventions govern a single longitude and **none is recoverable from the data**: the node
frame (declared *wrongly* — §11.1), the epoch (declared correctly in code, never in the row —
§11.10), and now the ayanāṃśa application method (declared nowhere, worth 15″, and silently
divergent between two correct-looking call shapes). Each cost a session an error today.

### 11.12 §11.10 refined, and the fix is smaller than it looks

The Kshetra session's correction, adopted: *"declares neither"* was slightly too strong. Precisely —
**the node frame is declared wrongly in two places** (`624:30` `node_mode="mean"`;
`l0_ephemeris.py:77` comment "Mean North Node"), while **the epoch is declared correctly in exactly
one place a consumer never reads** (`l0_ephemeris.py:164,278`). A reader of `ephemeris_daily` can
recover neither: its columns are `id, date, body, ayanamsha_id, tropical_longitude, latitude,
speed_dps, is_retrograde, sign_number, degree_in_sign, nakshatra_number, source_citation,
computed_at`. `date` carries no time-of-day; `source_citation` is the constant string
*"pyswisseph + Swiss Ephemeris .se1"*.

**And the fix is not new machinery — it is this table's own established pattern.** The row already
carries `ayanamsha_id` (value: `tropical`) precisely to declare a frame. `node_mode`,
`epoch_convention` and the ayanāṃśa application method belong beside it, each with a detector, rather
than in a probe contract that asserts without measuring. §11.10 therefore reads as *"extend the
row's existing frame declaration to the three frames it omits"*, not *"add declaration machinery"* —
which should make it considerably easier to land. (Framing by the Kshetra session.)

**And the consumer cost, in one sentence** (madhav-d9's, adopted): because L1 stores no `RAH_TRUE`,
the true natal value is computed at read time and stored nowhere — so any consumer wanting it
recomputes it and silently inherits its caller's epoch, backend and ayanāṃśa method. Today that is
three ways to be wrong, none of them visible in the data.

### 11.13 The knot and the instant fall on opposite sides of the boundary

Measured on Swiss, the sharpest form of the whole episode: the **stored noon knot** for the birth
date is TRUE 49.998247° → **pāda 3**, while the **birth instant** is 50.049248° → **pāda 4**. Same
body, same day, same backend — opposite sides of a classical boundary, 6″ and 177″ from it
respectively.

That is the argument for a design rule the Gochara family had already reached independently: **solve
at the instant; a stored knot is an interpolation input, never an answer.** It is also why the
knife-edge finding must not be cited against the natal figure (§11.10): the knot's 6″ margin is
smaller than any backend's error, while the instant's 177″ margin is five times larger than the
measured 32.5″ worst case. One is reportable, the other never will be.

### 11.14 Three defects from the Kshetra packet — verified here, one of them governance-level

**(a) A wrong classical citation, carrying an acceptance stamp.** `MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md:207`
states the source-qualified reference is *"the BPHS Ch.29 Sun third-from-Moon favourable transit and
paired ninth-house Vedha case."* Checked in the corpus: **BPHS Volume 1 Chapter 29 is titled
"Bhava Padas"** (`00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt`),
and the whole of Volume 1 contains **2** occurrences of "gochara". There is no gochara chapter there.
Line 39 of that same record lists *"source-qualified Vedha case"* as **INDEPENDENTLY ACCEPTED**.

So a citation naming the wrong text carries an acceptance stamp in a W0 record that the whole
campaign treats as settled. The admitted chain is `bg_phaladeepika_vedha` — **Phaladīpikā** PG353,
ADJUDICATION-11 — a different work entirely. This is the source-qualification discipline failing at
the one place it is supposed to be strongest, and it propagated: the Kshetra session inherited the
phrase verbatim into two documents before catching it. **Routed to the W0 record's owner.** No L3
session edits an accepted W0 record.

**(b) A coverage gap that declares a table absent while it holds live rows.** `stage1_symbolization.py`'s
`latta_coverage()` returns `"not_in_corpus"` with *"No classical latta-kick rule table found in this
codebase."* Live: **`bg_phaladeepika_latta` holds 8 rows.** An unearned signal in the *opposite*
direction from the usual — declaring absence where there is presence — and it suppresses a source
the layer has already admitted. Fix belongs with the comment's owner; the coverage detector should
query rather than assert (the §11.12 pattern again).

**(c) The stored field is chart-wide; its contract says route-scoped.** Verified: `layer0.py:200-201`
states plainly *"Store ALL chart-level vighna instances. Per-class SM-R-7 filtering is Layer 1's
responsibility"*, and the SM-R-7 filter lives in `layer1.py` — a projection that never writes
`kala_field`. The field path passes `obstructions=self.envelopes.obstructions_at(t)` unfiltered
(`stage4_field.py:866-873`), and the null path does the same. So field and null are **mutually
consistent and chart-wide**, and the documented route-scoped contract is what no stored row honours.

Note what the Kshetra session did *not* claim: its reviewer inferred a further consequence — that
`null_p` is biased low by a field/null split — and that session **rejected it** after checking the
fourth site, because there is no split. Contract ≠ behaviour, not field ≠ null. Rejecting a
reviewer's consequence while accepting the finding is the right discipline and worth recording as
such. The native's decision is which semantics governs, gated on a byte-equality test
`field ≡ null ≡ projection` before any `null_p` is served.

### 11.15 The citation strike propagates: the layer has no corpus-verifiable vedha source

Consequence of §11.14(a), raised by the Kshetra session, cross-checked by the Gochara session,
measured independently here against `bg_transit_rules` where `vedha_house IS NOT NULL`:

| Citation | Rules |
|---|---|
| `BPHS Ch.29 (Gochara Phala — Transit Results)` | **39** |
| `Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)` | **2** |

BPHS Volume 1 Chapter 29 is *Bhāva Padas* (§11.14a) — so **39 of 41 vedha rules, 95% of the set,
cite a gochara chapter that does not exist.** The remaining 2 name the right work; the admitted
corpus holds `BPHS · Jaimini_Sutram · KP · KP_Reader` and **no Phaladīpikā** (0 matches under
`SOURCE_DATA`). So after the strike **zero vedha rules are corpus-verifiable.**

Two consequences the native should see plainly:

1. **`FOUNDATION_SAFETY §5:207-209`'s claim does not hold as written.** It names "the existing
   source-qualified ordinary reference" and the thing it names is the wrong chapter. That record's
   41 passing tests (`test_ka_vedha_gochara*.py`) prove geometry and interval behaviour — which is
   **computational correctness, not source qualification** (F24 keeps those tiers separate). A
   correction note belongs on that record; no L3 session edits it silently.
2. **The layer currently has no source-qualified ordinary reference at all.** Not just vedha:
   `ka_tithi_pravesha`'s own citation reads `not_in_corpus`, and Sarvatobhadra is an acknowledged
   approximation. So D4 (tithi-praveśa qualification) is not one asset's paperwork — it is the path
   to the layer's **first** honest source-qualified reference, which changes its priority.

**The three streams have already converged on the mechanism**, which is why this needs ruling once
rather than three times. The producer stamps every `ka_vedha_gochara` row with
`source_qualification ∈ {verse_cited, algorithmic_approximation, unsourced}`, `precision_regime ∈
{date_grain, instant_grain}` and **`corpus_verifiable`** (is the cited text actually in the admitted
corpus). Consumer admission is then uniform and mechanical: **F06 `applied` iff `corpus_verifiable`
AND the Vedha geometry conjuncts pass; otherwise `unqualified`.** Today that admits nothing —
house-vedha, sarvatobhadra and laṭṭā all enter unqualified in all three consumers — and the policy
lifts row by row as the stamp flips, with no plan needing re-ruling. This also corrects an
inconsistency the Gochara session caught in Kshetra's earlier draft, where house-vedha was applied
and laṭṭā unqualified on one stated ground.

**The fix is a corpus/L0 decision, not an L3 one** (Gochara's G-9): admit Phaladīpikā — and
Sārāvalī / Jātaka Pārijāta if the non-vedha rows citing them are to stay verse-cited — or re-grade
every gochara-vedha row uniformly as *cited-outside-admitted-corpus*. Routed to the corpus owner.

### 11.16 `set -e` is not a detector either — recorded against this session's own rails

The Kshetra session reported that a commit chain pushed a file whose frontmatter did not parse,
because `set -e` did not halt the chain. That is worth recording here rather than in one packet,
because **this session has been running the same shape all day**: a heredoc Python step that
validates or rewrites an artifact, followed by `git add`/`commit`/`push` in the same compound
command. `set -e` does not abort when the failing command sits inside a pipeline, a command
substitution, or a construct the shell treats as tested — so a validation step can fail silently and
the commit still lands.

It is the §11.1 pattern one layer down, in our own tooling: **a check that cannot fail the thing it
guards is not a detector.** Migration 624 asserted a node frame it never measured; a `set -e` chain
asserts a validation it does not enforce. Verification steps should assert explicitly and gate the
commit on their own exit status, not lean on shell semantics.

Concrete instance found while checking PR #2722: one file, `KIMI_K3_REVIEW_KSHETRA_v1_0.md`, was
missing frontmatter entirely rather than carrying a broken block — see §11.17 for the retraction of
my first diagnosis of it. Both files now carry real byte-0 frontmatter (`29bddaa2b`), and that
session's commit chain now runs its parse gate as its own step with an explicit `|| exit 1` rather
than trusting `set -e`.

### 11.17 The governance frontmatter gate is blind in scope — and my first diagnosis of PR #2722 was wrong

Two findings here, one of which is a retraction of my own.

**RETRACTED — the ScannerError I reported was mine, not the gate's.** I told the Kshetra session its
file failed to parse at "frontmatter line 5, column 4," a `**bold**` prose line inside the fences.
That was an artifact of my own checker, which split on the first `---` *anywhere* in the file. The
real file, at `c83309a00`, had **no frontmatter block at all** — it opened with `#`. My splitter had
seized on an interior horizontal rule and called the prose beneath it a frontmatter block. The gate's
own `_FRONTMATTER_RE` is used with `.match()`, which is anchored at byte 0, so it would have read
that file as *missing* frontmatter, a different violation class from the one I named. The Kshetra
session caught this and was right. Both files now carry real byte-0 frontmatter at `29bddaa2b`.

**Rule earned, alongside "a date is not an epoch" / "a flag is not a backend" / "a sparse sample is
not a bound": a naive parser is not the gate.** When reporting what a gate will do, run the gate's
own matcher, not a reimplementation of it. Mine differed from the real one in exactly the way that
produced a confident, specific, wrong line number — the most credible-looking kind of error.

**STANDS — scope.** Independently measured and unaffected by the above: expanding all eleven
class/glob pairs in `schemas/artifact_schemas.yaml` against the repo matches **zero files under
`00_ARCHITECTURE/briefs/`**. The class that would cover us, `architecture_governance`, globs
`00_ARCHITECTURE/*.md` — single-level, does not descend. Every artifact this campaign has produced
is ungoverned. The Kshetra session reached the same conclusion independently and noted that Saṅgam's
two identically-shaped Kimi files are already on `main` unchallenged, which corroborates it.

**STANDS, as a constructed finding — the gate does not fail on a malformed block it *does* reach.**
For a file that is in scope and does open with `---` at byte 0, a `yaml.safe_load` failure raises no
violation: `validate_frontmatter_for_class` sets a `__loose_yaml__` marker and falls back to a
line-start regex scan for the required keys at severity `LOW`. I tested this with a constructed
byte-0 block containing broken interior YAML: all three required keys were still found by the regex,
so the file produced **zero violations, exit 0**. Even a `LOW` returns exit 3, the band
`ONGOING_HYGIENE_POLICIES` keeps a `known_residuals` whitelist for. This was never PR #2722's
situation — it is a latent hole, found while chasing a defect that turned out to be mine.

**Net, for W0.** A clean CI run on a briefs-tree artifact is not evidence its frontmatter is
well-formed; nothing looked. Two small fixes belong in W0: extend the campaign-artifact class to
`briefs/**`, and make a YAML parse failure a violation in its own right instead of a silent
downgrade to a regex scan. The second matters more — widening the reach of a gate that cannot fail
only spreads a green light nothing earned. That is §N.8 read against our own tooling: *what code
path would have to run, and fail, for this signal to correctly read false?*

### 11.18 The ephemeris backend is process-global and unowned — G4 retracted, replaced by something worse

**RETRACTION of G4.** I recorded that this host has no `.se1` files and that every local benchmark
therefore ran on Moshier. That is wrong as of 2026-09-22 17:20. All five files — `sepl_18.se1`,
`semo_18.se1`, `seas_18.se1`, `sefstars.txt`, `seleapsec.txt` — are at `/private/tmp/se1`, and the
*production* resolver `brahmagyan.l0_ephemeris._resolve_ephe_path()` returns `/tmp/se1`, its own
third candidate. The Saṅgam session established this; I reproduced it directly rather than accept it.

With the path set I reproduce, at L1's own birth instant (jd 2445735.717361 = 1984-02-05 05:13 UT =
10:43 IST), `retflag` carrying the SWIEPH bit and no Moshier bit:

| quantity | sidereal Lahiri |
|---|---|
| TRUE node | 50.049248° → Rohiṇī pāda 4 |
| MEAN node | 49.033044° → Rohiṇī pāda 3 |

Both figures match the Saṅgam sheet to six decimals, and the MEAN value matches L1's stored
`RAH_MEAN` fact, which is what pins the instant.

**What replaces G4 is sharper.** The files being present does not mean a computation uses them.
`swe.set_ephe_path` sets *process-global* state, and the components disagree about who owns it:

- **The 0.314″ figure's actual origin is `services/w2g_validations/v3_spline_accuracy.py`** (the
  Gochara session located it precisely; I had said "w2g", which is the consumer, not the producer).
  It imports `serialized_swiss_state` at line 42, decorates `_swe_longitude` at 111, and calls with
  `swe.FLG_SWIEPH | swe.FLG_SPEED` at 118 — **and never calls `set_ephe_path` at all.** Requesting
  the SWIEPH flag does not load the files; `calc_ut` falls back silently.
- **The mechanism is sharper than "nobody sets it": a lock is not a configuration.**
  `serialized_swiss_state` (`panchang_engine/swiss_state.py`) takes `SWISS_STATE_LOCK` and calls the
  function. That is all it does. A decorated function is *serialized*, not *configured* — and the
  decorator's presence reads, at a glance, like the Swiss state has been handled. `transit_search.py`
  is decorated **and** sets the path at 249-250, so the contact path is genuinely configured; the
  spline validator is decorated and is not. Same decorator, opposite guarantees.
- `ka_gochara_v3_century_materialize.py` imports `swisseph` directly at line 2022 and **never sets
  it**.
- `panchang_engine/__init__.py` calls `swe.set_ephe_path(None)` **four** times, and
  `l0_ephemeris.py` twice more, each forcing Moshier. (I first reported two, from a grep I had piped
  through `head`. There are **23** non-test `set_ephe_path` call sites in the sidecar. Truncating my
  own greps is now the single most frequent mechanism behind my errors this session — see §11.8.)
- `bg_cohort.py`, `bg_sky_calendar.py`, `transit_search.py`, `routers/pyhora.py` and
  `service_probes.py` each set it themselves.

So the backend a given computation receives depends on which unrelated component last touched a
global in that process. `bg_sky_calendar.py:234` documents the trap in its own docstring: setting
the path does not fail when files are missing, and `calc_ut` falls back silently.

**This closes the question the Gochara session routed to me.** It asked whether the V3 runner sets
the path, because if the 0.314″ validation ran without it, it compared a spline against a reference
two orders of magnitude coarser than its own claim — the Moshier true-node error is bounded at
65.3″ over the full 1950–2100 domain, roughly 200× the 0.314″ figure. **Answer: neither the V3
runner nor w2g sets it.** The figure cannot anchor any gate until its owner asserts its own
`retflag` on every call. This is §N.8 again: a precision claim with no detector for the backend that
produced it.

**One caution for whoever picks this up.** The string `0.314` appears in this corpus as two
unrelated quantities: the w2g worst-case spline error in **arcseconds**, and a CPU sample of
0.314605 **seconds** in the W0 benchmark baseline. Same digits, different units, different subject.
That is the "a filename is not a table" family, which the Gochara session and its reviewer both hit
independently this week.

### 11.19 The century hold is procedural only, and the registry understates the blast radius

The Gochara session reported that the held century writer is still registered and active and deletes
production in the same transaction as its staging write. I verified it, and the live registry makes
it worse than reported.

Source: `ka_gochara_v3_century_materialize.py` carries `@register(ASSET_ID)` at line 1717. In one
`conn` — the orchestrator's transaction, which a writer must never commit or close — it executes
two deletes back to back: `DELETE FROM kala_gochara_windows_v2` (staging, generation `g3_utkarsha`)
at line 2247, then `DELETE FROM kala_gochara_windows … generation = '3.0'` (**production**) at line
2257.

Live registry, read just now:

| asset_id | is_active | target_table | clear_tables |
|---|---|---|---|
| `ka_gochara_v3_century_materialize` | **true** | `kala_gochara_windows_v2` | NULL |
| `ka_gochara` | true | `kala_gochara_windows` | NULL |

Two things follow that the source alone does not show. First, the asset **declares only the staging
table**, so every registry-driven view of what it touches — the Atlas display, any clear-scope
reasoning, any blast-radius estimate — omits the production table it deletes from. Second,
`clear_tables` is NULL, so there is no second declaration to catch it. The asset's declared reach
understates its real reach by exactly one production table, and that table is `ka_gochara`'s own
declared target. Two active assets write the same production table; one declares it, one does not.

The "hold" on the century writer is a note in a document. Nothing in code, registry or database
prevents it running and wiping production generation `3.0` for a chart. It is G19, and it blocks
unattended build until the native sets it inactive.

### 11.20 M-1 through M-7 are now recorded in writing

The gap I escalated is closed, by the Saṅgam session and correctly. `SANGAM_RULING_SHEET_v1_0.md`
is on this branch at `101046052`, status `RULED`, with the rulings verbatim, attribution to the
native by name, and a timestamp of 2026-09-23T02:42:50+05:30. I confirmed the file and read the
block rather than accept the report.

Two qualifications, both of which that session stated **on the sheet itself** rather than leaving
me to find:

1. The seven lines are character-for-character its own *example* answer lines, which the native
   adopted by pasting them back. That is recorded as what happened, not dressed up as independent
   drafting. A reader should weigh it accordingly, and the session says any line meant differently
   is corrected on request.
2. M-6's minimum-n is a literal unfilled placeholder, `<your number>`, recorded as **OPEN**, not
   closed. A placeholder cannot be a ruling. The E6 evaluation gate stays shut until the native
   supplies the number.

**The one ruling that changes chart facts is M-1: node = mean.** Read against §11.1 and §11.18 that
is a decision with teeth, not a formality. `ephemeris_daily` stores the **true** node under a
contract declaring mean; L1 serves `RAH_MEAN` and no `RAH_TRUE`; and at this native's birth instant
the two frames fall on **opposite sides of a pāda boundary** — true 50.049° is Rohiṇī pāda 4, mean
49.033° is pāda 3. Ruling "mean" makes pāda 3 the answer and makes the stored knots a derivation
input rather than a servable value. It does not by itself repair the undeclared contract on
`ephemeris_daily`, which remains the §N.8 finding of §11.1.

### 11.21 The citation strike was wrong where it mattered — Phaladīpikā IS in the corpus

**This retracts the central claim of §11.15 and it bears directly on ruling 8, which the native has
already ruled. It should be read before stage 3 proceeds.**

**What I published.** That the admitted corpus is (BPHS, Jaimini_Sutram, KP, KP_Reader); that 39 of
41 vedha rules cite "BPHS Ch.29" which is actually *Bhāva Padas*; that the remaining 2 cite
Phaladīpikā, "which is not in the admitted corpus"; and therefore that **zero vedha rules are
corpus-verifiable**. The Gochara session reached a compatible conclusion, and ruling 8 turns on it.

**What is true, read from the live corpus table rather than from a file listing:**

| text_id | chunks | rows containing "vedha" |
|---|---|---|
| `phaladeepika` | 564 | **17** |
| `bphs` | 1459 | 2 |
| `hora_sara` | 460 | 0 |
| `saravali` | 471 | 0 |
| `brihat_jataka` | 607 | 0 |

The served corpus holds **fifteen populated texts**, not four. Phaladīpikā is one of them, and it is
the single **richest** source of vedha material in the entire corpus. The doctrine itself is there,
in Adhyāya XXVI: the Sun's vedha pairs at `PG322:C1` (auspicious in the 11th, 3rd, 10th, 6th,
provided the corresponding 5th, 9th, 4th and 12th are unmarred, Saturn excepted), Mercury's at
`PG323:C1`, and the laṭṭā rules at `PG339:C1` (the 9th from Rāhu, the 22nd from the Moon). That is
precisely the material the 41 rules need.

**Where my error came from.** `Jaimini_Sutram` and `KP_Reader` are **directory names** under
`00_ARCHITECTURE/SOURCE_DATA/classical_texts/`. I read a source-data folder listing and published it
as the admitted corpus. It is the same family as every other error I have made today, and it now has
its own line: **a source directory is not the corpus.** Note also that `jaimini_sutram` exists as a
text_id with `chunk_count: 0` — admitted in name, empty in substance, which is a separate §N.8
finding worth its own row.

**What survives, and it still matters.** The BPHS Ch.29 mis-citation is real: 39 rules cite a
chapter that is *Bhāva Padas*, and BPHS itself carries only 2 vedha rows. So the rules do cite the
wrong text. But the conclusion inverts. It is **not** "nothing is verifiable, admit nothing." It is
**"the citations point at the wrong source, and the right source is in the corpus."** Those call for
opposite remedies: the first would have us drop or permanently flag 41 rules; the second is a
re-citation against Phaladīpikā Adhyāya XXVI, after which they are verifiable.

**One honest limit on the remedy.** Phaladīpikā's chunks are heavily OCR-degraded and their
`verse_ref` is **page-based** (`PG322:C1`), not chapter-and-śloka. So a citation of the form
"Phaladīpikā 23.11" — which the Saṅgam ruling sheet's M-2 relies on — cannot be resolved against
this corpus as written. Precise verse citation needs either a chapter/śloka index or a
page-anchored convention. Hard to cite precisely is a real cost; it is not the same as absent.

**And the retrieval layer cannot be trusted for absence claims.** Two measured demonstrations:
`find_verses_about` returned **zero** results for a Phaladīpikā gochara/vedha topic that has 17
matching rows in the table; and a Rāhu/Ketu aspect query returned five rows, **all** from a
MEDIUM-provenance grey-upload nadi text, three of them near-identical table headers, with nothing
from BPHS, Hora Sāra, Phaladīpikā or Bṛhat Jātaka. The Saṅgam session was right to report its
node-aspect finding as "unverified so far" rather than "absent," and this is the concrete
counterexample that justifies the caution. **A hybrid search returning nothing is not evidence of
absence in this corpus.** Absence claims must be made against the table, with a `count(*)`, not
against the search tool.

**Consequence for ruling 8.** The native ruled on a premise that two sessions supplied and that was
wrong in its central term. The ruling may still be the right call on other grounds, but it should be
re-put with the corrected premise while the sheet is reversible. I am not asking for it to be
reversed; I am saying it should not stand on a fact I got wrong.

### 11.22 "No node dṛṣṭi" is a formula change, not a record trim — and the engine is not the one named

M-1's closing clause, "no graha-dṛṣṭi for Rāhu/Ketu," reads like a scoping decision about which rows
ship. It is not. The Gochara session flagged this and I verified it, with one correction: the code
is in **`services/gochara_v3/engine.py`**, not `services/ka_sangam/engine.py`. Two files named
`engine.py`; the finding is right and the address was wrong. That is the "a filename is not a table"
family again, and it caught a session that had just caught three of mine — which is the argument for
the rule rather than against anyone.

Verified at `services/gochara_v3/engine.py`:

- `_W30_NODAL_DRISHTI_ENABLED: bool = True` at line 107. **Live, not dormant.**
- Line 628: `_w30.compute(context, t_jd, swe=swe, enabled=_W30_NODAL_DRISHTI_ENABLED)`.
- Line 632: `raw_lambda = promise * permission * activity * tara_modifier * w30_modifier * quality_gates`.
- Lines 668 and 778 emit `w30_modifier` into the stored output.

So `w30_modifier` is a **live multiplicative factor in the served λ**. Setting the toggle to False
does not remove records; it changes the formula, and every stored λ computed with the factor becomes
incomparable to every λ computed without it. The codebase already says so in its own comment at line
132: removing the term "automatically invalidates every stored" score.

**Two things follow for the native's ruling.** First, if "no node dṛṣṭi" extends to this mechanism,
it implies a full gochara_v3 rebuild, and that cost belongs in the ruling rather than being
discovered afterwards. Second, the mechanism is declared a **CANDIDATE** in its own module docstring
(`w30_nodal_drishti.py:4`) while running enabled in the served path — a candidate that is live is
not a candidate, and that gap deserves its own line whatever the node ruling says.

**One thing here is genuinely well-built, and it is worth saying.** `scoring_signature.py` exists
specifically to detect toggle and constant changes in these mechanisms and to invalidate stored
scores when they move. Unlike most of what §N.8 has turned up this session, this signal has a real
detector behind it. It is the model the rest of the layer should copy.

### 11.23 The rule ledger, consolidated

Six instances of one failure mode, found in a single day across four sessions. Each is the same
move: reading something adjacent to the thing being described, then publishing the result with more
precision than the method earned.

| rule | what was mistaken for what | whose |
|---|---|---|
| a date is not an epoch | midnight differenced against noon-UT knots | mine |
| a flag is not a backend | `FLG_SWIEPH` requested without the files loaded | shared |
| a sparse sample is not a bound | 16 dates reported as a 150-year bound (32.5″ vs the true 65.3″) | mine |
| a filename is not a table | `gochara_*` basenames; two files named `engine.py` | Gochara's, and its reviewer's |
| a naive parser is not the gate | my splitter vs the gate's byte-0 `.match()` | mine |
| **a source directory is not the corpus** | `SOURCE_DATA/classical_texts/` folders read as the admitted corpus | **mine, then inherited by two other sessions** |
| a lock is not a configuration | `serialized_swiss_state` read as having handled Swiss state | shared |

The last one in the table is the one that did the most damage, because it was not caught by
disagreement: three sessions held it simultaneously, and it took reading the corpus table directly
to break it. **Convergence between sessions is not independent confirmation when the sessions share
a premise.** That is the governance lesson of this day, and it is worth more than any individual
finding above.

A recurring mechanism worth naming separately: three of my errors trace to piping a `grep` through
`head`, which silently truncated the evidence I then reasoned from. The fix is procedural, not
intellectual — count first, then read.

### 11.24 The wrong corpus list is in production code, with a verification claim behind it — and the Sarvatobhadra grid was there all along

Two findings, and the second one recovers an asset we had written off.

**The error was not only mine. It is hardcoded, and it is asserted as verified.**
`platform/python-sidecar/services/ka_vedha_gochara/logic.py` states in its own docstring:

> "The ingested classical-text corpus (`00_ARCHITECTURE/SOURCE_DATA/classical_texts/`) was checked
> this session: it holds BPHS, Jaimini Sutram, KP, and KP_Reader material only — NO Muhurta
> Chintamani or Jyotish Sara Sangraha text … Tier (i) (ingested-corpus citation) is therefore
> UNAVAILABLE for this specific table, **confirmed by direct search, not assumed**."

Every load-bearing part of that is false, and the parenthetical is the whole defect: it equates the
**ingested corpus** with a **source-data folder**. Measured against the live table:

| the docstring's claim | the table |
|---|---|
| corpus holds four texts | **15 populated texts** |
| no Muhurta Chintamani | `muhurta_chintamani`, **274 chunks** |
| `kp` / `kp_reader` are corpus texts | **zero** such text_ids exist |
| tier (i) unavailable for SBC | **false — see below** |

This is §N.8 in its purest form, and worse than the usual case because the signal *says* it has a
detector. "Confirmed by direct search, not assumed" is exactly the sentence that stops the next
reader checking. I did not check it. Two other sessions did not check it. The claim propagated from
a docstring into three independent analyses and into a native ruling within one day. **A verification
claim in prose is not a detector; it is a sentence.** The Saṅgam session found the same list copied
into a migration.

**And the Sarvatobhadra chakra is in the corpus.** The docstring's conclusion sent us to write the
asset off as unsourceable, and it worried at length about having to fabricate a grid layout from
memory because regional traditions disagree. That worry is unnecessary:

- `phaladeepika:PG345:C1` — *"I shall now describe the (Sarvatobhadrachakra) which has become
  famous"*, followed by a grid with `NORTH` and nakshatra cells.
- `phaladeepika:PG332:C1` — **NOT a second SBC page. Corrected below (§11.25).** It is the
  28-asterism *ring* chakra belonging to the Sun-vedha rule at śl. 26-27 — a different instrument
  that happens to share the Kṛttikā start.

Same Adhyāya XXVI as the vedha rules and the laṭṭā rules. There are **ten** rows corpus-wide matching
`sarvato`; nobody had looked, because a docstring said not to.

**My first OCR caveat here was itself over-stated, and I am correcting it (see §11.25).** I wrote
that the pages are severely degraded and need a re-OCR against source images. That is true of
**`PG345:C1` alone**, which is the diagram page — a figure, so of course it OCRs as scattered
tokens. I generalized from it to the whole span without reading the rest. The Saṅgam session read
further and was right: **`PG346:C1`–`PG352:C1` is a complete primary construction in legible
prose**, ~1,400 characters per page, and I have now read all eight.

**The governance point, which outlives all of this.** Three sessions converged on a wrong answer
because all three inherited it from the same docstring. Convergence is not confirmation when the
premise is shared. The only thing that broke it was reading the table with `count(*)`. Whenever an
artifact claims a corpus fact — present, absent, admitted, unqualified — the check is a query
against `classical_text_chunks`, not a search tool and not another document's assurance.

### 11.25 The Sarvatobhadra construction is complete and legible — G10 re-graded again, to buildable

I read `PG345:C1`–`PG352:C1` in full rather than infer from the first page. The construction is
there, in prose, and the degraded diagram page is not needed to build it:

- **`PG346:C1`** — the grid, stated as an instruction: *"Draw ten lines vertically and another ten
  lines crosswise over the same. You will have 81 squares. Write in the regular order the 16 vowels
  from onwards in the corner squares commencing…"* This is the 9×9 layout the
  `ka_vedha_gochara` docstring said could not be recovered without fabricating one.
- **`PG347:C1`** — weekday/tithi groups; the malefic set (Saturn, Sun, Rāhu, Ketu, Mars), Mercury
  conditionally malefic in malefic association, the waning Moon likewise.
- **`PG348:C1`** — the motion-dependent vedha direction rule: *"In the case of Rahu and Ketu, which
  are always retrograde, the Vedha will be on the right, and in the case of the Sun and the Moon
  which move direct … the Vedha will be on the left."*
- **`PG349:C1`** — the five-fold effect scale: agitation, fear, loss, disease, death.
- **`PG350:C1`–`PG351:C1`** — effects by motion, own-weekday vedha, directional/quarter effects.
- **`PG352:C1`** — the sensitive-star set: Janmabha/Janmarkṣa, the 10th as Karmabha, the 19th, etc.

**So G10 moves a second time: from "unsourceable" to "OCR-blocked" to buildable.** The SBC grid
tables are empty because nobody populated them, not because no source exists. That is now an
ordinary build task against a cited primary, and the checkable partition invariant the docstring
proposed can be applied to a transcription rather than to an invention.

**My own error here is the sparse-sample rule again**, one day after I named it. I read the first
page of an eight-page span, found it illegible, and published a caveat about the span. The Saṅgam
session read the rest. **A sparse sample is not a bound, and page one is not a chapter.**

**A fifth correction of mine, and the most dangerous one had it shipped.** I described `PG332:C1`
as "a second grid page" of the Sarvatobhadra chakra. It is not. The Saṅgam session placed it
correctly and I verified the placement: `PG331:C1` is śloka 24 (Rāhu's transit effects through the
12th from the Janmarāśi) and `PG333:C1` is śloka 27 (the three asterisms, Janmanakṣatra, the Sun
associated with a malefic). PG332 sits between them, so it is the **28-asterism ring chakra for the
Sun-vedha rule at śl. 26-27**. The Sarvatobhadra proper is śloka **48**, at PG345-346. Both use a
Kṛttikā start, which is exactly what makes the confusion plausible and the consequence severe: **a
transcriber handed "PG332 and PG345 are the two grid pages" would have spliced two different
instruments into one table** and produced a chakra that exists in no text. This is the worst error I
made today, because unlike the others it would have survived into data rather than into prose.

**Two refinements adopted from the other sessions, both table-verified by them:**

1. Adhyāya XXVI carries **two distinct 1-5 vedha-count scales**, at `PG349` and `PG353`.
   `bg_vedha_malefic_scale` cites the PG353 one and should say which it cites — two scales in one
   chapter is precisely where an unpinned citation drifts.
2. The retrieval layer ranked the load-bearing Adhyāya XXVI chunk **7th of 12** on a vedha query,
   behind nāḍī and muhūrta noise. So a `top_k=5` search "proves" absence of the very text that
   answers the question. That is the mechanism behind every absence error in this chain.

### 11.26 W0 task: re-audit every corpus-absence claim in the codebase

Every "no source in the corpus" claim any of us relied on was made against a **directory listing**,
not the table, and the three that have been checked are all false: Phaladīpikā is admitted; the SBC
is sourced; `kp`/`kp_reader` do not exist as texts at all. The claims live in production code and
migrations, not only in our documents — `ka_vedha_gochara/logic.py`, and (per the Saṅgam and Kṣetra
sessions) migrations 526 and 528.

**Re-opened pending a `count(*)`, none of them yet checked:** Kota, kakṣyā, muntha, sade-sati
("KP Reader only" — and KP is not in the corpus), the sandhi band, and the tithi-praveśa
`not_in_corpus` disposition. Each may well survive the check. None of them has had one.

**The method rule, which all four sessions converged on independently and which belongs in doctrine
rather than in four packets:** an absence claim about the corpus is made by a `count(*)` against
`classical_text_chunks` naming the predicate. Never a directory listing. Never a search tool, whose
ranking demonstrably buries the answer. And never another artifact's assurance that it already
checked — "confirmed by direct search, not assumed" was the sentence that propagated this error into
three analyses and a native ruling inside one day.

**The governance finding this day produced, which outranks any individual defect above.** The first
statement was: convergence between independent sessions is not independent confirmation when they
inherit a shared premise. The Saṅgam session sharpened it against this day's own record, and its
version is the one that should stand:

> Four sessions checked each other. I checked their claims, they checked mine, and two more checked
> both. All four were still wrong together for a day — because every check ran against *another
> session* and the shared premise, never against the object. **Mutual checking among sessions that
> share a premise is agreement, not verification.** Only a query against the object broke it, and
> the moment one session ran one, the whole chain corrected itself in under two hours.

**The operational form, for any independent reviewer:** a peer's confirmation counts for nothing the
reviewer has not itself queried. The reviewer's own `count(*)`, or its own read of the file, is the
detector. *"Session X also found this"* is evidence only that session X read the same sentence.

This is §N.8 turned on our own review process: **what would have to be true for cross-session
agreement to correctly read false?** Nothing, as long as the sessions are talking to each other. So
the signal is null, and the count is the detector. I am proposing this for doctrine rather than
leaving it in four packets, because it is the one finding today that generalizes past Kāla.

### 11.27 Sade-Sati: 4,492 served facts, zero primary attestation

The Gochara session ran the `count(*)` rule against its own remaining absence claims rather than
leave them, which is the right instinct and produced the most serious finding of the day. I verified
it and the severity holds.

| quantity | measured |
|---|---|
| Sade-Sati facts on the canonical chart | **4,492** |
| corpus rows mentioning it, any spelling | **5** |
| of those, in a primary text | **0** |
| Kota chakra rows, corpus-wide | **0** |
| kakṣyā rows (none in BPHS proper) | 14 |

All five rows are in `nadi_navamsa_patel`, the MEDIUM-provenance grey upload that our retrieval layer
has been over-ranking all day. Worse, of the five, only `PG1334:C1` states the doctrine at all
(*"the transit of Saturn through the 12th, 1st and 2nd houses from the Moon"*). The other four are a
modern author's **empirical observation** correlating outcomes with bindu counts across two example
charts. That is a twentieth-century claim about charts, not a classical rule.

So a serving factor that consumes 4,492 facts for this native rests on one paragraph in one
medium-provenance modern text. Under F23 that cannot reach `DATA_ACCEPTED` on its current citation,
and under §N.7's honest-null discipline it should not be narrating with unqualified confidence in
the meantime.

**The caveat that keeps this from becoming a fifth over-claim, and it is important.** I searched for
a **name**, not a **doctrine**. "Sade-sati" is a late vernacular term — the rows themselves note the
southern "elarata" and the popular "7½-year Panoti" framing. Saturn's transit results reckoned from
the Moon may well be attested in the primaries under entirely different wording, inside the gochara
chapters we have already been reading. **What is established is that the name and its 7½-year
framing have no primary attestation. Whether the underlying transit doctrine does is a separate
question that nobody has asked.** Asking it is a bounded task and it belongs in the W0 re-audit of
§11.26 — and it must be asked by predicate, not by term, or it will produce exactly the class of
false absence this whole chain was made of.

**Kota chakra is the counter-example worth noting**: zero rows corpus-wide, established the way the
rule requires. That is a real absence, honestly reached, and it supports keeping Kota at
proposed-use rather than promoting it. The rule does not only demote things.

### 11.28 Saṅgam closed — and the one disclosure in it that should not close quietly

Saṅgam is CLOSED at `3f62f3468`. Sheet CLOSED, plan v1.0 `APPROVED_FOR_EXECUTION_STAGE_3`, brief
v1.5. For the L3 row and CURRENT_STATE.

**The delegation is recorded the way the earlier episode was not, and that is worth marking.** When
M-1…M-7 were first reported to me as ruled, nothing in the repository recorded them and I refused
the report. The close does it properly: `delegation_recorded` carries a timestamp
(2026-09-23T03:39:33+05:30) and names the delegated scope; the delegation is quoted verbatim in the
CLOSE block; and D-1…D-8 are marked, typographically and in the frontmatter, as **the author's
decisions under delegation, not the native's words**, each with reasoning so any can be reversed in
one line. That is the correct shape for a session deciding under delegation, and it is a direct
improvement on the same day's earlier practice.

**The limit that remains, stated plainly.** I can verify that the sheet *records* a delegation. I
cannot verify the delegation itself — no session can verify a claim about what the native said
outside the repository. Everything a session can do here has been done; the last step is the
native's alone. This is the standing residue of §11.23: a peer's account of an off-repository
exchange is not something a peer can confirm.

**D-8 is the disclosure that matters, and it nearly closed quietly.** The sheet states that **plan
v0.4 — the text v1.0 is built from — has never been reviewed by anyone.** v0.1 returned REWORK on 19
findings and v0.3 on 10; v0.4 is the text that answered the second round, and no reviewer has seen
it. Rather than let an `APPROVED_FOR_EXECUTION` label paper over that, the session made the third
Astra review a **stage-3 entry gate**: it runs before any code is written, by the independent
reviewer, and is explicitly not discharged by the author. That is the right call, and it is §N.8
applied to an approval label — *what would have to run and fail for "approved" to correctly read
false?* Until that review runs, the honest answer was "nothing," and now it is the gate.

**D-1 deserves note for the same reason.** The E6 evaluation gate is set at n=30 per
`(domain × route × method_version)` and n=100 for a pooled instrument-level claim, with
`method_version` never pooled and anything short reporting `PROVISIONAL_INSUFFICIENT_N` **with its
actual n**. The numbers are stated as functions of the measured base rate and recompute at equal
power if it moves off 0.20. That is a threshold with a detector behind it rather than a convention,
which is the distinction this whole campaign has been about.

**D-7** adopts the successor condition: the legacy scan is withdrawn only when the R-5 preservation
manifest shows every dependent claim has an authorized successor — a state, not a date.

**What Saṅgam still depends on, all owned elsewhere:** the Gochara N-7 ruling (gates E1/E3), the
`ephemeris_daily` undeclared-contract finding (§11.1), and the house-vedha re-citation under
F-23/G-8.
