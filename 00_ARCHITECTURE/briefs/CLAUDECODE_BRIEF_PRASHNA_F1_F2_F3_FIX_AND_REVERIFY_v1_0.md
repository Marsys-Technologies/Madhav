# Prashna — Fix F1/F2/F3, re-cast, re-verify, PR (paste into Claude Code / Antigravity)

**Read CLAUDE.md §C first + memory `feedback-prashna-every-query-design`.** `PRASHNA_VERIFY_v1_0.md` = **FAIL —
not mergeable**. Architecture is sound (ga_positions fixed, real chart cast, namespace-isolated, multi-chart gate
correct, FROZEN contract untouched), but three gaps prevent activation — all invisible to the 22 passing unit
tests. Fix all three, RE-CAST a Prashna chart end-to-end, confirm `ga_prashna_judgment` produces non-zero rows
with a non-None judgment, THEN PR. The cast evidence is the only acceptable proof — NOT "tests pass."

## STANDING RAILS
deterministic horary judgment (rule-based from bg_prashna_rules, never generative); L1-is-authority; FROZEN
orchestrator contract (HALT if a change seems needed); namespace isolation (prashna outputs NEVER touch the
native 482012f1 natal stream); surgical migrations if any (≥ next free); endpoint-verify; never fabricate a
horary answer — validate-and-reject non-Prashna queries.

---

## FIX 1 — F1 (THE BLOCKER): graha-name convention mismatch — fix it ONCE, consistently, not just line 173

**Root cause:** `chart_facts.fact_subject` stores ABBREVIATED tokens (`MOON`, `JUP`, `SAT`, …) but
`bg_prashna_significators` stores FULL names (`'Moon'`, `'Jupiter'`). In `ga_prashna_writer.py`:
- `positions` (lines 126-130) is keyed by the raw `fact_subject` → keys are `MOON/JUP/SAT/…`.
- `querent_planet`/`quesited_planet` (lines 168-169) come from bg_prashna_significators → `'Moon'`/`'Jupiter'`.
- Line 173 `querent_planet not in positions` → `'Moon' not in {MOON,…}` is ALWAYS True → `return None` → 0 rows.

**Do NOT just patch line 173.** The full names are also used downstream — `positions[querent_planet]` (176-177),
`PLANET_DAILY_MOTION.get(querent_planet)` (180-181), and the Lagna lookup `positions.get("Lagna")` (143). If you
normalize in one place but a downstream comparison still uses the raw token, you get partial/wrong significators
— a subtler version of the same bug.

**Correct fix — reconcile on ONE convention at the source.** Normalize the `positions` dict keys to FULL names
at construction (the comprehension at lines 126-130), via an explicit `_ABBREV_TO_FULL` map (MOON→Moon,
SUN→Sun, MAR→Mars, MER→Mercury, JUP→Jupiter, VEN→Venus, SAT→Saturn, RAH→Rahu, KET→Ketu — **VERIFY the exact
abbreviations actually present in chart_facts for this Prashna chart by querying distinct fact_subject**, don't
assume the set). Then every downstream consumer (significator membership test, `PLANET_DAILY_MOTION`, Lagna)
works against one vocabulary. Confirm:
1. **Grep the whole writer for every graha-name comparison/lookup** and confirm each now sees full names
   (no raw `MOON`/`JUP` token leaks past the normalization).
2. **Lagna/Ascendant token (line 143):** confirm what `chart_facts` actually stores for the Ascendant for a
   Prashna chart — is it `LAGNA`/`ASC` (abbrev) or `Lagna`/`Ascendant` (full)? If abbreviated, add it to the
   map so `positions.get("Lagna")`/`get("Ascendant")` resolves. If the Ascendant isn't a `graha_position` row
   at all, `lagna_lon` silently falls back to 0.0 (Aries 0°) — a wrong-but-non-crashing judgment. VERIFY the
   Lagna longitude is real, not the 0.0 fallback.
3. `PLANET_DAILY_MOTION` keys must match the normalized convention (full names). Confirm Rahu/Ketu motion keys
   exist (they're significators for some question classes).

## FIX 2 — F2: spurious `charts` INSERT fails on NOT NULL columns

`cast_prashna_chart()` (`ga_prashna_cast.py:168`) INSERTs into `charts`, which fails on NOT NULL columns
(`name`, `birth_date`, …). The verifier found no FK requires this INSERT. REMOVE it — the Prashna chart_id lives
in `prashna_charts` (its own namespace), and `chart_facts`/`ga_prashna_judgment` key on chart_id without a
`charts` row. **Before removing, grep for any FK or JOIN that expects a `charts` row for the prashna chart_id**
(confirm the verifier's "no FK requires it" against the schema — if some read path DOES join `charts`, the fix
is a minimal NULL-safe insert or a separate prashna-chart registry decision, NOT just deletion → flag it).

## FIX 3 — F3: validation gate misses "What's my Moon sign?"

The gate (`ga_prashna_cast.py` `_LOOKUP_PATTERNS`) rejects "what is" but misses the contraction "what's" → a
factual lookup slips through as a valid Prashna. Add `"what's"` and `"my … sign"` (and consider other common
contractions: `"whats"`, `"what're"`) to `_LOOKUP_PATTERNS`. **Add a test case for each** so the gate's
accept/reject behavior is locked: it must REJECT "What's my Moon sign?" / "what is my lagna" / "whats my rashi"
and ACCEPT a genuine horary question ("Will I get this job?"). Deterministic patterns are the floor; the gate's
job is reject-non-Prashna, so over-rejecting a borderline lookup is safer than under-rejecting.

---

## RE-CAST + RE-VERIFY (the proof — cast evidence, NOT the test count)
After all three fixes, cast a test Prashna chart end-to-end and CONFIRM against the DB:
1. **⭐ `ga_prashna_judgment` produces NON-ZERO rows** for the cast Prashna chart (verifier expects ~10 — record
   the actual count) with a **non-None judgment** (significators resolved, Ithasala/Eesarpha computed,
   fructification populated). This is the "Prashna activated" proof — if still 0, F1 isn't fully fixed; report
   which graha lookup still mismatches.
2. **Lagna is real** (not the 0.0/Aries fallback) — show the lagna longitude + rashi for the cast chart.
3. **F2:** the cast completes WITHOUT the `charts` INSERT error; prashna_charts row present.
4. **F3:** gate REJECTS "What's my Moon sign?" (+ the other contractions) and ACCEPTS a real question — show both.
5. **Namespace isolation still holds** — query 482012f1's chart_facts/judgment, confirm zero prashna rows leaked.
6. 22/22 (+ new F1/F3 tests) green; FROZEN contract untouched.

## PR (with cast evidence in the body)
Open a PR. Body MUST include: the cast's `ga_prashna_judgment` row count + the actual judgment text/significators
produced; the F1 normalization diff (showing it's applied at the source, not just line 173); the F2 resolution;
the F3 gate accept/reject demonstration; namespace-isolation confirmation. Paste the numbers, not "verified".
Update `PRASHNA_VERIFY_v1_0.md` → v2 with the PASS evidence.

**FAIL the re-verify (don't merge) if `ga_prashna_judgment` is still 0 rows or the judgment is None** — that
means Prashna still isn't activated. Report which lookup mismatched. Only a real horary judgment from a cast
chart counts as activation.
