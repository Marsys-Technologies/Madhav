# F-63 SPEC (TIER3-EXPERIENCE) — panchanga special-yoga combination_name always "unknown"

Stream S4 VĀCA · Stage S SPEC, per Stage-D DIAGNOSIS.md (verdict: OPEN-mechanism-found).

## NEEDS-LEASE flag (read first — ESCALATE-TO-CONDUCTOR)

**The fix's files are not in S4's `OWNS` list.** Per `LEASES.json`, `platform/python-sidecar/
ga_writers/**` is explicitly owned by **S6_ADHARA**, not S4_VACA. F-63's mechanism is entirely in
`ga_panchanga_writer.py` (an `ga_writers/**` file) plus its paired test in
`platform/python-sidecar/tests/test_ga4_writer.py` (the test suite for that same writer, naturally
associated with the same owning stream). Neither file appears anywhere in S4's `owns` block.

Per the plan's lease-conflict-resolution rule quoted in `LEASES.json`'s own `_meta.rule` ("A lane
whose mechanism lives outside its stream's lease posts PAR-F-63-NEEDS-LEASE and does not edit;
conductor re-leases or routes the spec to the owning stream") and PAR-R-7 (this class of call is a
conductor routing decision, not a code judgment call this lane should make silently): **this SPEC
is diagnose/spec-only. S4 does not build F-63.** The precedent pattern is identical to F-78, F-08,
F-117, F-125, and F-45/F-38 already recorded in `LEASES.json`/`BOARD.md` — a stream diagnoses and
specs a finding whose mechanism sits in another stream's owned files, then routes the completed
spec to the owning stream's builder once the spec is VERIFIED-COMPLETE.

**Recommended disposition: route to S6_ADHARA.** S6 already owns both touched files outright
(`ga_writers/**` covers `ga_panchanga_writer.py`; the paired writer test naturally follows the
same lease). This SPEC.md is written in full so S6's builder can proceed directly once the
conductor confirms the route — no re-diagnosis needed on S6's side.

Posting `PAR-F-63-NEEDS-LEASE` to the conductor is the action this SPEC recommends; it is not
self-executed here.

## Root-cause statement

`_emit_special_yoga_combinations` in `ga_panchanga_writer.py:1060` reads a detected special-yoga
result dict under the keys `"name"` and `"yoga_name"`, but `special_yogas.py`'s `_yoga_dict()`
helper (lines 68-77) — the sole producer used by all 9 `detect_*` functions — only ever populates
the key `"yoga"`, so the `.get("name", yoga_dict.get("yoga_name", "unknown"))` chain falls through
to the literal string `"unknown"` unconditionally, every time, for every special-yoga type, on
every chart where any of the 9 classical combinations fire.

## Files to change

Both files below are **S6_ADHARA's lease**, not S4's. Listed here for spec completeness; S4 does
not touch them.

1. **`platform/python-sidecar/ga_writers/ga_panchanga_writer.py:1060`** — one-line consumer-side
   key fix. Current:
   ```python
   yname = yoga_dict.get("name", yoga_dict.get("yoga_name", "unknown"))
   ```
   Change to read the key the producer actually emits, and per §N.7 item 6 ("an honest null beats
   an invented judgment"), change the terminal fallback from the string `"unknown"` to `None`
   rather than preserving a fabricated-looking default:
   ```python
   yname = yoga_dict.get("yoga")
   ```
   Downstream use of `yname` at lines 1063 (`subj = f"YOGA_{yname.upper()...}"`) and 1066-1069
   (`value_text=yname`, citation string) must handle the `None` case explicitly — if `yoga_dict`
   ever legitimately lacks a `"yoga"` key (should not happen given `_yoga_dict()` is the sole
   producer, but defensively), skip emitting that row rather than emitting a `YOGA_NONE` subject or
   a `None`-as-text value. This is a builder-level implementation decision within the one-line fix's
   spirit, not a scope expansion: guard with `if not yname: continue` before line 1063, matching the
   "row genuinely absent" idempotency pattern already used elsewhere in this writer (compare the
   `if not yogas: yogas = []` empty-list guard immediately above at lines 1055-1057).

2. **`platform/python-sidecar/tests/test_ga4_writer.py:176-178`** — the test fixture invents a dict
   shape the real producer never emits (`{"name": ..., "yoga_name": ...}`), which is exactly why
   this bug shipped green (§N.8 Earned-Signal Principle: a passing test with no detector behind the
   real production key shape). Current:
   ```python
   pi.special_yogas_instant = [
       {"name": "Sarvartha Siddhi Yoga", "yoga_name": "Sarvartha Siddhi Yoga"}
   ]
   ```
   Change to the real producer's dict shape (matching `_yoga_dict()`'s five keys exactly):
   ```python
   pi.special_yogas_instant = [
       {"yoga": "Sarvartha Siddhi Yoga", "start_utc": <utc-datetime>,
        "end_utc": <utc-datetime>, "strength": "strong", "stars": 5}
   ]
   ```
   (Exact `start_utc`/`end_utc`/`strength`/`stars` values are the builder's choice within the
   fixture — any well-formed values matching `_yoga_dict()`'s signature satisfy the shape
   correction; the load-bearing part is the key `"yoga"`, not `"name"`/`"yoga_name"`.)

## Exit test

A corrected assertion in `test_ga4_writer.py` (in the existing test that consumes the
`special_yogas_instant` fixture — Stage B locates the exact test function name; the fixture edit
above is the input, this is the assertion that must accompany it) asserting that the emitted
`panchanga_special_yoga_combinations` / `combination_name` row's `value_text` resolves to the real
classical name (`"Sarvartha Siddhi Yoga"` for the fixture above), **not** the literal string
`"unknown"`.

- **Fails today:** with the current buggy key-read (`.get("name", yoga_dict.get("yoga_name",
  "unknown"))`) against the *current* (also-buggy) fixture, the test currently passes green by
  accident (fixture and bug are shape-matched to each other, not to production). Once the fixture
  is corrected to the real producer shape (Files-to-change item 2) but *before* the writer fix
  (item 1) lands, the test must fail — `yname` resolves to `"unknown"` because the corrected
  fixture no longer has `"name"`/`"yoga_name"` keys. This fixture-first/writer-second sequencing is
  the concrete demonstration that the new fixture actually exercises the real bug.
- **Passes after the fix:** with both the fixture correction and the one-line writer fix
  (`.get("yoga")`) applied, `yname == "Sarvartha Siddhi Yoga"` and the emitted `combination_name`
  row carries that string, not `"unknown"`.
- Command: `pytest platform/python-sidecar/tests/test_ga4_writer.py -k special_yoga -v` (or the
  specific test function name Stage B identifies covering the `special_yogas_instant` fixture;
  DIAGNOSIS.md did not name the exact test function, only the fixture lines — Stage B confirms the
  enclosing `def test_...` on read).

## Sibling sites covered

Per DIAGNOSIS.md's sibling census (searched all of `platform/python-sidecar` for `.get(...,
"unknown")` / `.get(..., "unmapped")` / bare `= "unknown"` patterns, ~25 hits manually inspected
for the "fallback keys structurally never match the named producer" pattern):

- `bo_pratijna.py:307`, `mi_darshana.py:158`, `bo_cgm_paths.py:163` — inspected and ruled **not**
  the same defect class: in all three, the key read (`dignity_state`, `domain`, `node_subject`)
  genuinely appears in the producing dict/row in the normal case, so `"unknown"` there is a
  legitimate defensive default for a field that can be legitimately absent.
- No other instance found where a `.get()` fallback chain reads keys the named producer never
  emits. **`ga_panchanga_writer.py:1060` is confirmed the only instance of the
  "guaranteed-always-unknown" key-mismatch pattern in this codebase**, and `special_yogas.py`'s
  `_yoga_dict()` has exactly one consumer, so there is no second call site to check independently.
- **Sibling count: 0 additional instances; 1 total (this finding).** No further sites in scope for
  this spec.

## Recurrence guard

The corrected exit test (fixture matches production shape, asserts a real name not `"unknown"`) is
the concrete guard for this specific defect. Beyond that minimal fix, a real structural guard is
feasible and recommended (larger than this lane's minimal scope — noted as a recommendation, not
required for this lane's exit):

- Define a `TypedDict` (e.g. `SpecialYogaResult`) in `special_yogas.py` describing the five keys
  `_yoga_dict()` returns (`yoga: str`, `start_utc: datetime`, `end_utc: datetime`, `strength: str`,
  `stars: int`), and annotate `_yoga_dict()`'s return type and `PanchangaInstant.special_yogas_instant`
  (wherever that attribute is typed) as `list[SpecialYogaResult]`. A future producer/consumer key
  drift would then surface as a static-type error (mypy/pyright, if either runs in this codebase's
  CI) at the `.get("name", ...)`-style call site, rather than silently falling through to a
  string-literal default at runtime. This is the direct structural analogue of what a dataclass or
  TypedDict already buys elsewhere in this codebase; whether to adopt it here is a call for S6
  (the owning stream) to make at build time, not a blocking requirement of this spec.

## Dependencies and rollback

- **ND-PARISESA-1 rebuild dependency (binding).** The code fix (writer one-line key fix + test
  fixture correction) and its own unit test are **not blocked** by ND-PARISESA-1 — they can land via
  the normal Stage B → VERIFIER → INTEGRATOR merge cadence like any other lane. What **is** gated:
  the live reproduce_cmd for this finding (`ganita_chart_facts_get` against chart
  `482012f1-710e-4a25-994a-93821f5871aa`, category `panchanga`, showing the
  `panchanga_special_yoga_combinations` / `combination_name` row resolve to `"Panchaka"` — or
  whatever the writer's fixed string form is, e.g. `"panchaka"` per `_yoga_dict()`'s `name`
  parameter as passed by `detect_panchaka` — instead of the literal `"unknown"`) **stays PENDING**
  until (a) native permission is granted, relayed through the conductor, per
  `00_ARCHITECTURE/briefs/parisesa/NATIVE_DIRECTIVE_NO_REBUILD_WITHOUT_PERMISSION.md` (ND-PARISESA-1,
  binding, issued 2026-08-16), and (b) `ga_panchanga_writer` (or the relevant L1 rebuild scope
  covering it) actually re-runs against chart `482012f1` so the fix manifests in live
  `chart_facts` data. Until then, Stage V for this lane reports the code-level fix as landed and
  its unit test as passing, and explicitly reports the live-probe verification as PENDING-ON-
  NATIVE-PERMISSION — never silently marked verified from the unit test alone, and never skipped
  without being named.
- **S6 lease question (primary open item):** see NEEDS-LEASE section above. This is the item this
  spec cannot resolve itself; it is presented to the conductor as `PAR-F-63-NEEDS-LEASE`, recommending
  route-to-S6, per the F-78/F-08/F-117/F-125 precedent already recorded in `LEASES.json`.
- **Rollback:** two small, independent, additive-safe changes (one `.get()` key fix + a fallback
  default change from `"unknown"` string to `None` with a guard; one test-fixture dict-shape
  correction). No schema change, no migration. A `git revert` of the one commit (once built)
  fully restores the current (buggy but stable) behavior with no data loss — the pre-fix state
  simply resumes writing `combination_name = "unknown"` for firing special yogas, exactly as it
  does today, until a corrected rebuild is manually triggered again.

## Sub-claim coverage table (from DIAGNOSIS.md's claim decomposition)

| DIAGNOSIS.md sub-claim | Spec element that closes it |
|---|---|
| (a) a detector recognized SOME special combination is active — TRUE, and stronger than the original finding stated (Panchaka Dosha specifically fires for the native's chart) | No spec action needed — detector logic (`special_yogas.py`) is correct and untouched; root-cause statement records this |
| (b) "it could not resolve WHICH one" — FALSE as literally stated; real mechanism is a dict-key mismatch, not an unresolved lookup | Root-cause statement + Files-to-change item 1 (the `.get("yoga")` fix restores the already-known name, no lookup table needed) |
| (c) served the literal string `"unknown"` instead of the real classical name or an honest null — TRUE, confirmed to file:line | Files-to-change item 1 (fix reads the right key; fallback becomes `None` per §N.7 item 6, not a re-fabricated string) |
| (d) conditional (chart-specific), not a universal placeholder — TRUE, confirmed structurally (comparison chart 1c826d5a emits zero rows in this category because no special yoga fires there) | No spec action needed — the emission-only-when-`special_yogas_instant`-non-empty gate (lines 1055-1057) is correct and untouched; only the row-content bug is in scope |
| Contributing factor: test fixture masks the bug (§N.8 Earned-Signal-class defect) | Files-to-change item 2 + Exit test's fixture-first/writer-second sequencing requirement, which concretely proves the corrected fixture exercises the real bug |
| Sibling census: 0 additional instances of the same defect class | Sibling sites covered section, restated from DIAGNOSIS.md, no new sites in scope |
| Blast radius: `bo_laksana.py` tags this L1 category `["spirituality","character"]` for L2 birth-moment signals; no confirmed hardcoded narration template quoting `"unknown"` found yet | Out of scope for this spec (no S4-owned narration file confirmed to consume this value) — flagged as a plausible but unconfirmed downstream leak in DIAGNOSIS.md, not actioned here; would need its own finding/lane if a consuming narration template is later confirmed |
| Blast radius: no overlap with `ekv/b-01-dignity-oracle-fix` branch | No spec action needed — confirmed disjoint file sets, no coordination required |

## Verdict

Stage S complete. **NEEDS-LEASE — routes to S6_ADHARA for build**, per `LEASES.json`'s
`ga_writers/**` ownership and the standing lease-conflict-resolution rule. Stage B does not start
in S4; this SPEC.md is handed to the conductor as `PAR-F-63-NEEDS-LEASE` for routing. Once routed
and built, Stage V's live-probe verification stays PENDING on ND-PARISESA-1 native rebuild
permission — the code fix and its unit test are not gated by that directive, only the live
`chart_facts` manifestation is.
