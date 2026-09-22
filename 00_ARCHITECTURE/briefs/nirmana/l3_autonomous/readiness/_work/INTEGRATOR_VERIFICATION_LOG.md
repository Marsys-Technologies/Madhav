---
artifact: KALA_READINESS_INTEGRATOR_VERIFICATION_LOG
version: "1.0"
status: LIVING — appended as lanes land
date: 2026-09-22
scope: >
  The integrating session's OWN re-measurement of lane claims that would change a decision.
  Lane reports are evidence, not verdicts. Per CLAUDE.md §N.8, a claim is verified at its
  authority (code/schema/live DB), never by re-running the lane's own query.
---

# Integrator verification log

## CONFIRMED — Lane B: 12 per-asset L3 briefs exist; the audit's inventory was wrong

The readiness audit (T4) stated Kshetra and Sangam briefs were "CONFIRMED ABSENT — no file, no
draft, no placeholder." Re-measured at the authority: `ls 00_ARCHITECTURE/briefs/` returns **17**
`CLAUDECODE_BRIEF_L3_*` files, **12 per-asset**, including
`CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md` — 170 lines, `status: AUTHORED`, and its `brief_for:`
line is explicitly tagged **`[ELEVATE]`**. Its §0 describes elevating "the registered `ka_sangam`
(today a thin 'dasha-transit convergence windows') into the full rigor-scored engine", and it
already names the independence discount for correlated evidence and the
generator→narrow→ephemeris-last efficiency spine.

Tag census across the 12: `[ELEVATE]` ×2 (`KA_SANGAM`, `KA_VIGHNAKARA`), `[NEW]` ×4
(`KA_BHAVISHYA_LEKHA`, `KA_JIVANA_PARVA`, `KA_KALA_DARSHANA`, `KA_TULANA`), untagged ×6.

**Governance standing (the nuance Lane B did not resolve):** all 12 are dated **2026-06-21** and
name `parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v0_10.md`, which exists but is a
DIFFERENT campaign plan from the current L3 Kāla Strategy/Execution Brief. So they are
substantively rich and governance-stale: **reconcile, do not re-author.**
**`ka_kshetra` has no brief — that absence is real** (`ls | grep -i kshetra` → none).

## CORRECTED — Lane E: `transit_contribution` is not dead; it is dead in ONE scope

Lane E reported "`transit_contribution = 0.0` on every row group — its source table is empty",
concluding the served activation waveform is merely "a binary lord-domain lookup × promise grade."
**That is not what the data shows.** `transit_contribution` is not a table column at all — it is a
key inside the `components` jsonb. Measured live over all 92,412 canonical-chart rows:

| term | min | max | mean |
|---|---|---|---|
| `dasha_contribution` | 0.15 | 1.00 | 0.653 |
| `promise_contribution` | 0.00 | 0.88 | 0.478 |
| `transit_contribution` | 0.00 | 1.00 | **0.249** |

`activation` itself takes 808 distinct values over [0.033, 0.957] — not degenerate.

**The honest finding, by scope:**

| `scope_kind` | rows | rows with zero transit term | mean transit term |
|---|---|---|---|
| `domain` | 43,488 | 39,552 (**90.9%**) | 0.041 |
| `event_class` | 48,924 | 16,578 (33.9%) | 0.434 |

So for **domain-scoped** waveforms — 47% of the asset's output — the transit term contributes
nothing in 91% of rows, and those waveforms are in practice dasha × promise only. For
`event_class` scope the transit term is live and material. Lane E's conclusion holds for one
scope and is false as a blanket claim. Carry the scoped version forward; discard the blanket one.

## CONFIRMED AND BROADER — Lane E: `dissent: []` is hardcoded across the served surface

Lane E named `priority.ts:280,316`, `story.ts:609`, `explain.ts:302`. Re-measured: the hardcoded
empty-dissent assertion appears in **seven** served `kala_views` tools —
`explain.ts:302`, `now.ts:1312`, `priority.ts:280` and `:316`, `story.ts:609`, `ritual.ts:637`,
`upaya.ts:265`. `ahead.ts` carries the documented fix and states the defect plainly at `:1705`
("F-110: `dissent: []` was hardcoded") and `:1157` ("the empty array `dissent: []` … asserts that
no dissent exists"). This is a §N.8 unearned signal at the serving boundary, repeated seven times,
and it bears directly on the product's promise of inspectable disagreement.

## CONFIRMED — Lane D: four Kāla assets are in `error` state right now

Live `asset_throughput`, canonical chart: `ka_kshetra` (`worker_crash: OperationalError: the
connection is lost`, 1,183,134 rows claimed), `ka_avadhi` (`post-write integrity check failed`),
`ka_gochara_v3_century_materialize` (`BUILD-PROTECTED`, guard working as designed),
`ka_gochara_sweep` (`no writer registered`, retired identity). Diagnosis of the first:
`LANE_A2_KSHETRA_CRASH_DIAGNOSIS.md`.

## CORRECTED (downgraded) — Lane F: the `ka_graha_sancara` ayanāṃśa gate is latent, not live

Lane F reported "a hard equality gate in `ka_graha_sancara` (the foundational ephemeris service)
that would reject the canonical `lahiri_chitrapaksha` string outright." The gate is real —
`services/ka_graha_sancara/engine.py:306` (`if ayanamsha != "lahiri": raise`) and `:376`
(`if ayanamsha not in SUPPORTED_AYANAMSHAS`, a set of engine-level names:
`{lahiri, raman, kp, krishnamurti, yukteshwar, surya_siddhanta}`).

**But it is not a present-tense defect, and the framing matters.** The codebase carries a
documented two-name convention, stated explicitly by a writer that handles it correctly
(`services/ka_tithi_pravesha/writer.py:61-62`):

```
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"    # the DB / chart_facts id
ENGINE_AYANAMSHA    = "lahiri"                 # pyjhora_adapter's own id for the SAME ayanamsha
```

Measured: every call site into the sancara engine passes the engine-level literal `'lahiri'`
(`services/ka_graha_sancara/__init__.py:9`, `writers/ka_graha_sancara.py:122,178,234`) or an
already-validated parameter. Every external importer takes only constants — `NAKSHATRAS`, `SIGNS`,
`ALL_GRAHAS`, `NAK_SIZE_DEG` — never the ayanāṃśa-taking functions
(`ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_kota_chakra`, `ka_vedha_gochara`).
Search scope: `platform/python-sidecar/services/` and `pipeline/`. **No live caller can trip the
gate.**

**The real, smaller finding:** there is no translation layer between the canonical DB
`ayanamsha_id` vocabulary and the engine vocabulary — correctness depends on each writer author
knowing the convention and hardcoding the right literal. `ka_tithi_pravesha` documents it;
the engine does not enforce or translate it. Any future caller that reads `ayanamsha_id` from
`chart_facts` and passes it straight into the engine fails at `:376`. That is a genuine hazard
for an elevation campaign that will edit these writers, and the fix is cheap (a shared
`to_engine_ayanamsha()` mapping, or accepting both spellings at the boundary). Record it as a
**latent hazard with a cheap guard**, not as a blocker — and note that the separately-confirmed
`?? 'lahiri'` default in `call_service_wrappers.ts:328` IS a live defect of this same family,
already fixed in the unmerged PR #2695.

**Classification note.** This is the third instance in this exercise of the F2 error shape — a
correct observation reported in the wrong frame (Lane B found two in the audit; I have now found
one each in Lanes E and F). The pattern is consistent enough to name: **a lane verifies that a
mechanism exists and can fail, then reports it as failing, without measuring whether any live
caller reaches it.** The consolidated package must state, for every hazard it carries, whether a
live path reaches it today.

## CONFIRMED — Lane C F1: a LIVE path deletes the protected Gochara capital

This one passes the live-path test that the three corrections above failed. Every link
re-measured at its authority:

| # | Link | Evidence |
|---|---|---|
| 1 | The Clear route loads the registry **unfiltered** | `platform/src/app/api/cockpit/clear/route.ts:114-117` — `SELECT … FROM asset_registry ORDER BY layer, sort_order`. No `WHERE is_active`. |
| 2 | Scope filtering does not restore it | `platform/src/lib/cockpit/clearScopeFilter.ts` — the `layer` branch returns `r.layer === scopeTarget && allowedScopes.includes(r.scope)`. `is_active` appears nowhere in the file. |
| 3 | The retired asset is in scope and points at live capital | live `asset_registry`: `ka_gochara_sweep` — `is_active=false`, `layer=kala`, `scope=per_chart`, `target_table=kala_gochara_windows`. |
| 4 | **So does the ACTIVE asset** | `ka_gochara` — `is_active=true`, `target_table=kala_gochara_windows`, while its `count_sql` reads `kala_gochara_windows_v2 … generation='2.0'` and its writer (`ka_gochara.py:120,336,362`) writes `_v2`. The active row's `target_table` points at a table its writer never touches. |
| 5 | The protection table is empty | live: `SELECT count(*) FROM build_protected_assets` → **0**. `route.ts:122` is the only protection lookup and it returns nothing, for every chart. |
| 6 | The fallback reaches a DELETE | `route.ts:186-187` — `isClearable = deleteSql != null \|\| asset.target_table != null`. The route's own authz test docstring (`__tests__/route.authz.test.ts:14`) states the effect: "`DELETE FROM <target_table> WHERE chart_id=$1` across every build-derived" table — and its fixture at `:68` is literally `target_table: 'kala_gochara_windows'`. |
| 7 | No database-level guard exists | positive control, live: non-internal triggers on ANY `kala_%` table → **0**. The guard a code comment attributes to migration 540 is not present (migration 588 dropped it). |
| 8 | Rows at risk | `kala_gochara_windows` → **40,117 rows**. |

**Conclusion.** A layer-scoped Clear on `kala` issues `DELETE FROM kala_gochara_windows WHERE
chart_id=$1`, and nothing in code, registry or database prevents it. Because link 4 shows the
ACTIVE asset carries the same `target_table`, **filtering out retired assets would not save these
rows** — the registry's own `target_table` is wrong for `ka_gochara` and that is the deeper fault.

This is the single most consequential finding of the readiness exercise: the native's Gochara v0.3
plan treats this capital as protected, and it is not. Severity: **BLOCKS-CAMPAIGN** for any work
that touches the Gochara family, and a standing hazard for the cockpit regardless of the campaign.
Remediation is cheap and belongs BEFORE any Gochara work: correct `ka_gochara.target_table` to
`kala_gochara_windows_v2`, add `is_active` to the clear route's registry query, and populate
`build_protected_assets` (or restore a database-level guard) so the protection is not merely a
comment.


## RETRACTED — "none of the accepted L3 source is on main" (fourth instance of the ancestry trap)

Stated in the strategic session on 2026-09-22 from `git merge-base --is-ancestor` alone: six accepted
L3 commits "exist but are not ancestors of `origin/main`". True as ancestry, **false as content**,
because `main` squash-merges. Re-measured by diffing the files each commit touched against `main`:
`3f109869d` IDENTICAL (7 files), `a3e518864` IDENTICAL (3), `87cc8c9baf` IDENTICAL (3),
`47131772b` one file differs — `ka_yojaka.py`, 789 lines in the commit vs 1,026 on `main`, because
`main` carries the *later* accepted DP-SD-019 Yojaka repair. Whole-sidecar diff between `main` and
`codex/madhav-data-plane-execution` is 7 files / 789 deletions, all tests and a grant migration that
`main` removed — `main` is ahead. `DHARA_SWEEP_SEMANTIC_VERSION = '1.2'` at `dhara_sweep.py:52` on
`main`; my earlier proxy strings (`writer.py`, the word "midpoint") were simply the wrong markers.

This is the same error the conductor disproved on 2026-09-20 ("stranded work", 874/874 lines present
via PR #2607) and that the kickoff prompt itself warns against ("verify content, not commit
ancestry"). Rule, restated for the fourth time: **a claim that work is missing from `main` is made
only by content diff of the touched files, never by SHA ancestry.**
