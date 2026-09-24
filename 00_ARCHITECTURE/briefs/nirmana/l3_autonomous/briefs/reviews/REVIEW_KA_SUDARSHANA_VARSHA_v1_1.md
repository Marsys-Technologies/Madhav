---
artifact: KALA_BRIEF_INDEPENDENT_REVIEW
canonical_id: REVIEW_KA_SUDARSHANA_VARSHA
version: "1.1"
status: COMPLETE
date: 2026-09-24
brief_reviewed: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_SUDARSHANA_VARSHA_ELEVATION_BRIEF_v1_0.md (frontmatter version "1.1")
prior_review: REVIEW_KA_SUDARSHANA_VARSHA_v1_0.md (REWORK, 21 findings)
reviewed_on: "worktree /Users/Dev/madhav-l3/layer-briefs, branch l3/kala-layer-briefs, HEAD e82dd34a3; `git diff --stat 3387c9ac3 HEAD` and `9feac52d7 HEAD` on services/ka_sudarshana_varsha/, query_sudarshana_varsha.ts, kala_views/now.ts, services/gochara_v3/, orchestrator/birth_params.py, migrations 521/670 are both empty, so every code citation checked at HEAD holds at the brief's source_revision"
reviewer: "Fable 5.1 review agent, fresh context, read-only; no DB, no git write, no external service; no test run"
method: "REVIEWER_PROMPT_TEMPLATE_v1_0.md followed as written. Each of the 21 v1.0 findings re-verified against v1.1's text at source (§6), not against the brief's own §12. Then a fresh hunt on the six axes named by the caller: the constancy invariant (re-computed read-only over all 1728 natal triples × 120 years), the independence_group shape vs B4, conjuncts (h′)/(i)/(j) against the real charts DDL and its RLS, the omitted-as_of fixture against the actual TS harness (vitest; now.ts→wrapper is HTTP), the sha256 window_id against B3 and the 521 natural key, and the three newly-cited §1 records at their lines."
---

# Review — `KA_SUDARSHANA_VARSHA_ELEVATION_BRIEF` v1.1

## 1. Verdict

**ACCEPT_WITH_CORRECTIONS.** Every v1.0 MAJOR is resolved at source (the constancy invariant is stated exactly and is arithmetically right in every case including the equal-natal-triple one; `now.ts:1643` is now the primary target of an interface packet; `kala_views/**` is fenced; the Relevant-influence and Duplication rows are now consistent with the arithmetic and with the absence of any concurrence consumer), and the recommendation, decisions and target state need no change. What remains is local and correctable without re-argument: the brief's stated reason for putting `moon_fact_id` in `roots[]` is false on this base (tithi-praveśa cites a *different* Moon fact, so fact-id roots would call the two assets independent — the opposite of what the brief intends), the `charts.timezone_id` "already read at `chart_header.ts:78`" claim is wrong (nothing in the TS registry reads `timezone_id`; that line reads `name`), the sha256 id omits `ayanamsha_id` from the natural key, conjunct (h′) needs a join shape that cannot pass vacuously under `charts`' RLS, the Irrelevant-control row is still not executable through the input that exists, the Delivery sentinel is a value the wrapper already serves, and FOUNDATION_SAFETY `:79` is still missing from §1.

## 2. Findings

Severity: `BLOCKER` / `MAJOR` / `MINOR` / `NOTE`. Ids `N-nn` are new in v1.1; carried-over partials are cross-referenced to §6.

| id | severity | brief's claim (section) | found at source | proposed correction |
|---|---|---|---|---|
| N-01 | **MAJOR** | §4.3: *"the `moon_fact_id` in `roots[]` is what makes this asset non-independent of `ka_tithi_pravesha` for a consumer of both"*; §7 Duplication: `roots[]` *"contains the real `moon_fact_id`"*. | This asset's `moon_fact_id` is the `graha_position / sign / MOON` fact (`writer.py:46-51`). `ka_tithi_pravesha` cites the `graha_position / longitude_sidereal / MOON` fact (`services/ka_tithi_pravesha/writer.py:19-20`, SQL `:73-76`, carried as its own `moon_fact_id` `:86,:273`). These are two distinct `chart_facts.fact_id`s for one body. Blueprint Q3 (`KALA_ELEVATION_BLUEPRINT_v1_0.md:668`) defines independence as *disjoint `roots[]`*, so fact-id-level roots would declare sudarśana and tithi-praveśa **independent** — the exact over-count SC-4 exists to prevent. The brief's rationale is therefore false on this base, and the chosen root identity does not do the job it is given. | Either (a) define the root identity at the body/subject level — e.g. the `chart_facts` `(chart_id, fact_subject, ayanamsha_id)` tuple or a declared string such as `L1:MOON@lahiri_chitrapaksha` — and put *that* in `roots[]` beside (not instead of) the three fact ids, or (b) keep fact-id roots and state plainly that they detect same-fact reuse only. Either way this is a **binding-wide B4 question** (root granularity), raised to the binding owner alongside the B1 one, not solved asset-locally. |
| N-02 | MINOR | §4.6: *"`charts.timezone_id`, which the TS registry already reads — `chart_header.ts:78`"*; §11.4 repeats *"already read by the TS registry"*. | No file under `platform/src/lib/retrieval` contains the string `timezone_id` (grep, `--include='*.ts'`, excluding tests: zero hits). `platform/src/lib/retrieval/chart_header.ts:78` (note: not under `registry/`) is `SELECT name FROM charts WHERE chart_id = $1 OR id = $1`. The registry's two `charts` reads are `get_tajik.ts:187` and `get_graha_yuddha.ts:148`, both `SELECT birth_date::text … WHERE id = $1`. The column does exist (`platform/migrations/001_baseline.sql:159 timezone_id TEXT`; COMMENT `0001_brahma_baseline.sql:1614`), and it is reachable through the same `query` client the wrapper already uses — so the IP is feasible — but the sentence is a false code claim, inherited from v1.0 §4's loose wording ("reads from `charts` at `chart_header.ts:78`"), which named the table, not the column. | Replace with: *"column exists (`001_baseline.sql:159`); the registry already reads `charts` through the same client (`chart_header.ts:78` for `name`, `get_tajik.ts:187` for `birth_date`) but nothing reads `timezone_id` yet — the IP adds the first read."* Fix the path. |
| N-03 | MINOR | §4.3 `roots:[<birth-date anchor>, …]`; §4.9 (h′) *"the only external anchor"*. | The anchor has no identity string anywhere in the brief, so conjunct (i) ("vocabulary-valid values") cannot check it and a consumer cannot compare it. Under Q3 disjointness (`:668`) a birth-date root is shared by every birth-anchored current (`ka_dasha_kala`, `ka_tithi_pravesha`, `ka_jivana_parva`, `ka_avadhi`, …), which makes this asset non-independent of nearly the whole layer — a consequence that may well be the honest one, but the brief neither names it nor names the anchor. (v1.0 F-02 proposed the anchor; the consequence is mine to have stated then.) | Name the anchor id (e.g. `charts.birth_date@<chart_id>` or `L1:BIRTH_INSTANT`) and state the disjointness consequence in one sentence; or move the anchor out of `roots[]` into the group's `basis` detail and keep `roots[]` to L1 facts. Fold into the N-01 B4 question. |
| N-04 | MINOR | §4.8: `id = sha256(chart_id, varsha_year, FORMULA_VERSION)`. | B3 (`KALA_SYNERGY_BINDING_v1_0.md:52`): *"content-addressed sha256 over the natural key + method version"*. The natural key is `UNIQUE (chart_id, ayanamsha_id, varsha_year)` (`521_kala_sudarshana_varsha.sql:54-55`; the writer's `ON CONFLICT` at `writer.py:70` matches). `ayanamsha_id` is omitted, so two ayanāṃśa wheels for one chart would collide. Today only `lahiri_chitrapaksha` is written (`writer.py:44`), which is why this is MINOR, not MAJOR. | `sha256(chart_id, ayanamsha_id, varsha_year, FORMULA_VERSION)`. `generation = FORMULA_VERSION` outside the PK is declared honestly and may stand as the alias mapping. |
| N-05 | MINOR | §4.9 / §7 Positive: (h′) *"`min(window_start) = charts.birth_date`"* as a new conjunct in a successor `integrity_check_sql`. | Column and anchor are real: `charts.birth_date DATE NOT NULL` (`001_baseline.sql:139`), PK `id` (`:135`) with a mirror `chart_id UUID UNIQUE` (`:153`) — the brief does not say which column it joins on. `charts` has RLS enabled (`:178`) with `chart_service_policy` permitting rows only when `app.principal_id` is unset/empty (`:180-185`), plus owner/grant policies (`:187-215`); `kala_sudarshana_varsha` has no RLS (grep: none). 670's (a)–(h) are all self-joins or joins to `chart_facts`/`reference_signs`; (h′) would be the first conjunct touching a principal-scoped table. An `INNER JOIN charts` written like (h) (`670:1310-1316`) would drop every chart the executing session cannot see and pass **vacuously** — the §N.8 defect class. Grant is also live: `1070_…grants.sql:72` grants SELECT on `charts` to `data_plane_builder`, but the pool role that `nirmana-elevation/monitor.ts:516-581` runs under is not established here, and the L2 campaign's own last two cycles were spent on exactly this class (migrations 934/935, "integrity_verified 500"). **Can it go red?** Yes — a wheel built from a wrong `datetime_iso`, or a rectified `charts.birth_date` with no rebuild, makes it FALSE; that is the detector F-10 asked for. | Write (h′) as `NOT EXISTS (SELECT 1 FROM (SELECT chart_id, min(window_start) AS anchor FROM kala_sudarshana_varsha GROUP BY chart_id) k LEFT JOIN charts c ON c.id = k.chart_id WHERE c.id IS NULL OR c.birth_date <> k.anchor)` — an unresolvable anchor is red, not invisible; name the join column; add to §11 that the executor role's SELECT on `charts` under RLS is unverified and must be proved in the successor migration's own verification step (§N.4 "surgical migrations, verified"). |
| N-06 | MINOR | Header `may_touch`: DDL *"ONLY if §10.2 chooses columns over JSONB"*; §5: *"optionally one additive DDL"*; §4.9 (i) *"every row carries the stamps"*. | §10.2's two options are *"additive `qualification` JSONB column vs per-chart meta table"*. Both are DDL (`ALTER TABLE … ADD COLUMN` or `CREATE TABLE`); `kala_sudarshana_varsha` has no JSONB column today (`521:32-57`). So the DDL migration is not optional under either ruling, and conjunct (i)'s SQL (which table/column it reads) cannot be written until §10.2 is ruled — the successor registry migration is sequenced *after* the DDL, and after the ruling. | `may_touch`: "one additive DDL migration (JSONB column or meta table — §10.2 decides which, not whether)"; §5: "one DDL then one successor registry migration"; (i)/(j) marked *shape pending §10.2*. |
| N-07 | MINOR | §7 Irrelevant control `[S]`: *"two `as_of` inputs resolving to the same chart-zone date → identical `is_current` row … wrapper test"*. | `as_of` is a `YYYY-MM-DD` string on both surfaces (`query_sudarshana_varsha.ts:46,:71`; `now.ts:2201-2205` regex). Two *inputs* that resolve to one chart-zone date are the same string; the only path where two different inputs resolve to one date is the **omitted-`as_of` default** under two wall clocks. As written the row is still not executable (v1.0 F-05's point, half-applied). | Restate: `as_of` omitted; wall clock at `2026-02-04T18:30:00Z` and at `2026-02-05T10:00:00Z` (both 2026-02-05 in Asia/Kolkata; the second is also 2026-02-05 UTC) → identical `is_current` row and identical echoed date; fails when the rows differ. That is the genuine zone-invariance control; the Boundary row is the zone-sensitivity case. |
| N-08 | MINOR | §7 Boundary `[S]`: *"wall clock faked to `2026-02-04T18:30:00Z` … year 43 … `18:29:59Z` → 42; today's code answers 42 at both — wrapper + MCP test"*. | Arithmetic re-checked: `18:30:00Z` = 2026-02-05 00:00 IST → year 43 (`relativedelta(2026-02-05, 1984-02-05).years + 1`); `18:29:59Z` = 23:59:59 IST 02-04 → 42; today's UTC slice gives 2026-02-04 → 42 at both. **Feasible in the harness:** both packages are vitest (`platform-mcp/package.json:14`, `platform/package.json:11`) and `vi.useFakeTimers()`/`vi.setSystemTime()` is already used in `platform-mcp/src/lib/__tests__/job_registry.test.ts`. **But** `now.ts` reaches the wrapper only over HTTP (`now.ts:128-144` `fetch(${PLATFORM_URL}/api/retrieval/capability)`), and every existing `kala_now_get` test stubs `fetch` (`kala_now_get_kota_sudarshana_w3.test.ts:63,:98`). So an MCP-side fake clock can prove only *what `now.ts` sends or omits and how it reads the echoed date*; the chart-zone **resolution** is provable only on the platform side — a wrapper unit test with a mocked `query` returning `timezone_id`, or a real-DB test in the `platform/tests/integration/*.db.test.ts` family. The row names both tests but not which assertion lives where. | Split the row's evidence path: MCP `[S]` — under the faked clock `now.ts` omits `as_of` (or passes the chart-zone date, per the IP's chosen design) and surfaces the echoed date; platform `[S]/[I]` — the wrapper resolves the omitted default via `charts.timezone_id` and returns year 43 / 42 at the two clocks. Note that the IP has a design choice the brief should name: `now.ts` cannot know the chart's zone before its first fetch, so either it omits `as_of` and reads the wrapper's echo, or it fetches the zone first (one extra round-trip shared by all ten items at `:1645-1681`). |
| N-09 | MINOR | §7 Delivery `[S]`: sentinel = *"`independence_group[0].roots` containing the real `moon_fact_id` (a per-row value the wrapper cannot synthesise)"*. | `moon_fact_id` is already a served column on every row (`query_sudarshana_varsha.ts:87`; also `source_query_availability.ts:2952`). A Pūrṇa implementation could build `roots[]` in TS from the served columns without ever reading the persisted stamp, and the test would pass — so it is not *"a decisive non-default sentinel"* only in the new field (contract `:112`; blueprint §12.3 `:767-771`). v1.0 F-07's alternative (a fixture-seeded `completeness_state` on one year) survives that objection; the `group_id` (once N-03 gives it a value) is another value only the stamp carries. | Sentinel = `independence_group[0].group_id` (stamp-only) **or** `completeness_state='unexplored'` seeded on one `varsha_year` in the fixture; assert it in `kala_now_get.sudarshana_varsha` and the saved reading. |
| N-10 | MINOR | §7 Negative `[S]`: *"`as_of` before birth via `kala_now_get` → `current: null` with honest-empty coverage"*. | Today `now.ts:482` returns `{ reachable: true, current: null }` and nothing else; no `coverage` object exists on item 17 (`:483-494` copies seven fields). The coverage half of the expectation is an IP deliverable (B5 emission at serving is Pūrṇa's), so the row as written fails today on coverage, not on the fabricated-year invariant it names. | Split: today's detector = `current: null` (passes now; fails when a year is returned); post-IP detector = the honest-empty `coverage` object; mark the second *"detector exists once the SC-1/B5 packet lands"* as the brief already does for the served-count test. |
| N-11 | NOTE | §1 row *"W0 field register (`:35,:215-218`)"*; §2.3 live-path *"the UTC `as_of` default is live on both served paths"*. | Register rows verified (`:35` identity row 16; `:215-233` are the asset's 19 partitions, all naming *"`query_sudarshana_varsha`; gochara-v3 annual stack"* as receivers — stale for the second, as the brief says). Third `as_of` convention found: `source_query_availability.ts:2953` computes `is_current` with `CURRENT_DATE` (the **DB session's** zone, a third convention) — `LIMIT 0`, so nothing is served from it; the live-path statement is correct for served rows. | One line in §2.3: the census SQL carries a third (DB-session) `as_of` convention; unserved, not in the IP, recorded. |
| N-12 | NOTE | §4.4 / §10.1: *"carries `time_basis=null` with the amendment id as a transitional state"*. | No amendment id is assigned or requested anywhere in the brief. `KALA_SYNERGY_AMENDMENTS_v1_0.md:38` carries only the `precision_regime → claim_grain` rename; no DATE-grain `time_basis` value exists in any brief on this base (grep `date_grain_local_midnight` across `l3_autonomous/briefs/*.md`: only reviews mention it). The amendment is genuinely new and genuinely generic (the kota/moorti/avadhi reviews raise the same gap). | §10.1: request an amendment id from the binding owner (e.g. `SA-B1-date-grain`) and cite it in the null's reason string. |
| N-13 | NOTE | §1 (guide §1 item 5) — the three added records. | CURRENT_STATE `:130` verified verbatim (*"no L3 input; annual evidence \| preserve; receiving operator owed"*). Field register verified (N-11). **FOUNDATION_SAFETY `:79`** (`…W0_FOUNDATION_SAFETY_v1_0.md:77-82`: the frozen first physical row frontier names `ka_sudarshana_varsha`; *"eligibility, not build authority"*) is still absent from §1, so F-18 is PARTIAL. | Add the row: *"frontier-eligible, not build-authorized — consistent with `target_state_data_plane: PRODUCER_READY`"*. |
| N-14 | NOTE | Header: `interface_packet_targets_not_may_touch` (new field); `must_not_touch` *"applied migrations 1033–1070"*. | Guide §2 gives the header *"verbatim fields"*; the new field is not one of them, though it carries the F-03/F-04 intent cleanly. `platform/migrations/` now holds `1071_kala_convergence_target_provenance.sql` and `1072_kala_convergence_episodes.sql` (Saṅgam's, not this asset's) — the guide's range is stale on this base. | Keep the field but say it is an addition to the template (or fold its content into §5 fences); write the fence as *"applied migrations ≥ 1033"*. |
| N-15 | NOTE | Citation residue after F-19. | `STRATEGY:65` for Q05's proof → the Q05 row is `:66` (`:65` is Q04). `now.ts:483` for `current: null` → `:482`. `670 :1252-1254` for the (c) comment → the quoted sentence spans `:1251-1252` (`:1254` is the `AND NOT EXISTS`). `writer.py:44-52` → the SQL is `:46-52` (`:44` is `CANONICAL_AYANAMSHA`). `chart_header.ts` → `platform/src/lib/retrieval/chart_header.ts` (no `registry/`). `670:1221-1318` is fine (`:1221` comment, `:1222` `UPDATE`, `:1318` `$ck$`). | Fix five line refs and one path. |
| N-16 | NOTE | §0 / §4.2 / §7 Invariant: the constancy statement. | **Exactly right.** With one offset `k=(N−1) mod 12` (`logic.py:74`) added to each natal index (`:110-112`), `(j+k) ≡ (c+k) ≡ (s+k) (mod 12)` ⇔ `j = c = s` on `0..11`, independent of `N`. Re-computed read-only: 1728 triples × 120 years → 0 triples change state; the 12 equal triples are `true` in all 120 rows, the 1716 unequal ones `false` in all 120. The equal-triple case is physically possible (Lagna, Moon and Sun in one sign) and the brief handles it (§7 Relevant-influence *"from an equal-triple fixture, all 120 flip"*). The row-level form additionally rests on 670 (g) (one natal triple per chart, `:1299-1306`) and (c) (`:1254-1259`) — both cited. No correction. | — |
| N-17 | NOTE | §2.3 / §4.10: w27c *"dangling declaration"*, shape mismatch, registry contradiction. | All verified: `w27_annual_stack.py:31` declares `context.sudarshana_rows`; `:15` the module itself says *"NOT wired into engine.py — that wiring is Wave 4 work"*; `compute_sudarshana` `:436-448` reads `{graha, house_number, window_start_iso, window_end_iso}`; `_SD_HOUSE_MODIFIERS` `:102-115`; `context.py` `ClassContext` has no `sudarshana` field (grep: none); `engine.py` has no `w27`/`annual_stack`/`sudarshana` reference; `w27c_sudarshana.yaml:15 admission_state: candidate` vs `mechanism_register.yaml:237 admitted`; both `citation_status: cited` / *"BPHS Sudarśana Cakra chapter"* (yaml `:5-6`; register `:242-244`). The brief could cite `:15` as the mechanism's own admission that it is unwired. | Optional: cite `w27_annual_stack.py:13-16`. |

## 3. Citations verified

All read with `sed -n` / `awk` / `grep -n` at HEAD e82dd34a3 (identical to 3387c9ac3 and 9feac52d7 for every code file below).

| citation (as in brief v1.1) | resolves | note |
|---|---|---|
| `logic.py:8-19` namesake ruling | yes | |
| `logic.py:41-46` "not a true … solar-return instant" | yes | |
| `logic.py:57` `DEFAULT_MAX_VARSHA_YEAR = 120` | yes | |
| `logic.py:60-66` `varsha_year_for_date` raises | yes | no production caller (writer imports `:35-39` only) |
| `logic.py:69-74` offset | yes | `:74` `(varsha_year - 1) % 12` |
| `logic.py:77-80` `progressed_sign_index` | yes | |
| `logic.py:83-91` `varsha_window` | yes | |
| `logic.py:110-112`, `:117` | yes | `jl == cl == sl` |
| `writer.py:44-52` natal SQL | partly | SQL `:46-52`; `:44` is the ayanāṃśa constant (N-15) |
| `writer.py:54`, `:184` DELETE; `:57-70` INSERT; `:70` ON CONFLICT | yes | |
| `writer.py:81-95` fetch / honest None | yes | |
| `writer.py:98-113`, `:111` `raw[:10]` | yes | |
| `writer.py:130-142` refusals | yes | |
| `writer.py:148-172`, `:168-170` fact ids | yes | |
| `writer.py:184-187` | yes | |
| `platform/supabase/migrations/521_…:32-57`, `:52`, `:53`, `:54-55`, `:66-67` | yes | path prefix now present |
| `platform/migrations/670_…:1221-1318` (a)–(h) | yes | `:1222` UPDATE … `:1318` `$ck$` |
| `670 :1252-1254` (c) comment | partly | sentence spans `:1251-1252` (N-15) |
| `670` (h) `min(window_start)` anchor | yes (`:1307-1316`) | |
| `query_sudarshana_varsha.ts:26`, `:38-39`, `:46`, `:71`, `:87`, `:88` | yes | `:87` serves `moon_fact_id` (N-09) |
| `now.ts:469-495` item 17; `:474-478` explicit `as_of` | yes | |
| `now.ts:483` `current: null` | partly (`:482`) | N-15 |
| `now.ts:1643` default; `:1645-1681` shared by every item | yes | |
| `now.ts:2201-2205` regex | yes | |
| `now.ts:128-144` `callRegistryCapability` = HTTP fetch | read here | bears on N-08 |
| `birth_params.py:96`, `:99`, `:106`, `:109` | yes | naive local; zone separate |
| `tests/l3/test_ka_sudarshana_varsha.py:115-117`, `:124-134` | yes | |
| `tests/l3/test_ka_sudarshana_varsha_writer.py:45` | yes | |
| `w27_annual_stack.py:10,31,75,82`, `:436-460`, `:102-115` | yes | plus `:13-16` "NOT wired" |
| `gochara_v3/context.py:114-186` no `sudarshana_rows` | yes (grep: none) | |
| `gochara_v3/engine.py` never invokes w27 | yes (grep: none) | |
| `w27c_sudarshana.yaml:15` candidate; `mechanism_register.yaml:237` admitted; `:242-244` citation | yes | |
| `source_query_availability.ts:2944-2961` | yes | `:2953` uses `CURRENT_DATE` (N-11) |
| `asset_registry_seed.ts:2498-2514` | yes (`platform/scripts/seed/…`) | `estimated_seconds: null`, not cited by brief |
| `chart_header.ts:78` reads `charts.timezone_id` | **no** | `platform/src/lib/retrieval/chart_header.ts:78` reads `name`; no registry file reads `timezone_id` (N-02) |
| `charts.birth_date` (for (h′)) | exists — `platform/migrations/001_baseline.sql:139` | PK `id` `:135`; mirror `chart_id` `:153`; `timezone_id` `:159`; RLS `:178-215` (N-05) |
| `KALA_SYNERGY_BINDING_v1_0.md:27`, `:30-32`, `:44`, `:52-54`, `:64` | yes | |
| `KALA_ELEVATION_BLUEPRINT_v1_0.md:285`, `:324`, `:396`, `:667`, `:668`, `:759`, `:906` | yes | `:906` still `precision_regime` (stale, as brief notes) |
| Blueprint §12.2 (`:751-763`) has no `as_of`/SC-1 packet | yes | IP-1…IP-9 only; the brief's "NEW" is accurate |
| `…STRATEGY_v1_0.md:65` Q05 proof | **no** — `:66` | `:65` is Q04 (N-15) |
| `…STRATEGY_v1_0.md:91` Clock interval; `:280` A10 | yes | |
| `…CONTRIBUTION_REGISTER_v2_0.md:145` | yes | |
| `…CURRENT_STATE_AND_DISPOSITION_v1_0.md:130` | yes, verbatim | |
| `…W0_FIELD_CONTRACT_REGISTER_v1_0.md:35`, `:215-218` | yes | asset's partitions run `:215-233` |
| `…W0_FOUNDATION_SAFETY_v1_0.md:79` | exists; **not cited by the brief** | N-13 |
| `…ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT_v1_0.md:112` Delivery | yes | |
| `KALA_SYNERGY_AMENDMENTS_v1_0.md` DATE-grain `time_basis` | absent (`:38` rename only) | N-12 |
| `KALA_BASELINE_v1_0.md` | does not exist | as brief states |
| `KALA_PHASE2_DECISIONS_v1_0.md` | does not exist | not cited by brief; noted for completeness |
| `platform-mcp` / `platform` test runner = vitest; fake timers in use | yes (`package.json:14` / `:11`; `platform-mcp/src/lib/__tests__/job_registry.test.ts`) | N-08 |
| `platform/tests/integration/*.db.test.ts` real-DB family | exists | host for a platform-side `[I]` fixture |

## 4. What I could not verify

- Any live database state: the 670 contract's production result, the 120-row count, `asset_throughput`, whether `charts.birth_date` for the canonical chart equals `min(window_start)` today — no DB access (brief marks these [A]; consistent).
- The DB role under which `nirmana-elevation/monitor.ts` executes `integrity_check_sql` in production, and therefore whether that role has SELECT on `public.charts` and whether `app.principal_id` is set in that session (bears on N-05; the L2 campaign's migrations 934/935 show this class is live).
- Node/ICU IANA-zone formatting on the deployed runtime (brief §11.4 — same limitation).
- Whether `ga_positions` regenerates `chart_facts.fact_id` deterministically (brief §11.5 — same limitation).
- Whether the L0 corpus holds a verse-grain Sudarśana-cakra source (no DB).
- No test was run; the harness capabilities (vitest fake timers, HTTP-only path from `now.ts`) were read, not exercised.
- Gochara branches other than this base.

## 5. Conformance to the binding

- **B1:** `inclusivity='closed_open'`, `claim_grain='date_grain'` conformant. `time_basis=null` pending a generic amendment — B1 says *declared on every row* (`:30-31`); the transitional null is defensible under §N.7 item 6 only once the amendment has an id (N-12). `window_basis`/`approximates` are declared asset-local aliases — permitted.
- **B2:** one `source_qualification` per row (the rule's) — conformant; `epistemic_class`, `completeness_state='applied'` conformant; `corpus_verifiable` is not mentioned (B2 `:45` names it on the producer row) — add it (`false` until DP02 lands).
- **B3:** `window_ref = {asset_id, generation, id}` conformant in shape; `id` omits `ayanamsha_id` from the natural key (N-04); `generation` outside the PK is declared as an alias — acceptable.
- **B4:** array shape, `family`, `roots[]`, `members[]`, `basis:'declared_lineage'`, `declared_current_count` — names conformant. `group_id` has no value (N-03). Root *identity* is under-specified for the purpose B4 serves (N-01) — a binding-wide question, not a naming defect.
- **B5:** all seven `coverage` keys present; the empty-result coverage on the served path is an IP deliverable (N-10).
- **No field named outside the B1–B7 vocabulary.** Asset-local additions (`convergence_basis`, `window_basis`, `approximates`) are declared as such in §7 — conformant under the alias rule.

## 6. Disposition of the v1.0 findings against v1.1

| v1.0 id | v1.1 status | where verified |
|---|---|---|
| F-01 | **RESOLVED** | §0, §2.4, §3, §4.2, §7 Invariant; 670 (c) cited as prior record; constancy re-computed (N-16) |
| F-02 | **PARTIAL** | array shape, `roots[]`, `family`, `basis`, groups-not-facts all adopted (§4.3); but `group_id` unvalued and the `moon_fact_id` rationale false at fact-id granularity (N-01, N-03) |
| F-03 | **RESOLVED** | §2.3, §4.6, header `interface_packet_targets`; `now.ts:1643`/`:474-478` verified |
| F-04 | **RESOLVED** | `kala_views/**` in `must_not_touch`; `now.ts` no longer in `may_touch` (N-14 notes the non-template header field) |
| F-05 | **PARTIAL** | Boundary row is the omitted-default fixture and is feasible (N-08); Irrelevant-control row still not executable as written (N-07) |
| F-06 | **RESOLVED** | §4.13, §7 Duplication, "detector exists once IP-5/SC-6 lands" |
| F-07 | **PARTIAL** | sentinel changed, but to a value the wrapper already serves (`query:87`) (N-09) |
| F-08 | **RESOLVED** | §7 Relevant-influence consistent with the arithmetic (N-16) |
| F-09 | **RESOLVED** | one generic amendment, §4.4/§10.1; id still to be assigned (N-12, NOTE) |
| F-10 | **RESOLVED** | `birth_params.py` verified in header/§1/§2.2; (h′) proposed — join shape and RLS to fix (N-05) |
| F-11 | **RESOLVED** | §2.3, §4.10, §10.3–10.4; yaml/register lines verified (N-17) |
| F-12 | **RESOLVED** | live path targeted; coverage half of the expectation is conditional (N-10) |
| F-13 | **RESOLVED** | (i)/(j) in a successor migration, 670 never edited; DDL sequencing to fix (N-06) |
| F-14 | **RESOLVED** | §7 Value pending the freeze; `KALA_BASELINE_v1_0.md` still absent |
| F-15 | **RESOLVED** | §4.1 Q05 partial/conditional; line ref is `:66` not `:65` (N-15) |
| F-16 | **RESOLVED** | one `source_qualification`; `window_basis`/`approximates` asset-local |
| F-17 | **PARTIAL** | sha256 declared but omits `ayanamsha_id` (N-04) |
| F-18 | **PARTIAL** | CURRENT_STATE `:130` and field register added; latent-value (a)–(d) and knowledge-time pin added; FOUNDATION_SAFETY `:79` still absent (N-13) |
| F-19 | **PARTIAL** | most refs re-pinned and migration paths prefixed; residue in N-15; `chart_header.ts` path and content wrong (N-02) |
| F-20 | **RESOLVED** | `target_state_data_plane: PRODUCER_READY`; conditions in §9 |
| F-21 | **RESOLVED** | §7 Revision states the determinism question; §11.5 |

Resolved 15 · Partial 6 · Unresolved 0.
