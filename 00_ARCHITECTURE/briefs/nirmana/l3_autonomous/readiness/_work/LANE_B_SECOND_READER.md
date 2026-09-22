# LANE B — ADVERSARIAL SECOND READER

Scope: the packets/deliverables the first independent reader did not deep-read —
`KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` (T1), `KALA_BRIEF_CONFORMANCE_v1_0.md` (T4),
`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` (T3), `_work/DOMAIN_D/G/H/I/J.md`, spot-check of
`_work/T5.md` and `_work/T6.md`.

Method: every material claim re-derived at its **authority** (the schema, the zod validator, the
source file, the live production DB) — never by re-running the packet's own query. The two known
errors (F2 ancestor-scope; `server_reconstructed` misread) are treated as calibration and are not
re-reported.

Read-only throughout. No mutation, no build dispatch, no evidence event, no branch, no commit.

---

## 1. VERDICT

**The audit's central arithmetic and its asset-level measurements can be relied on for a GO
decision.** Everything I could re-measure independently reproduced exactly: the `t3` event census,
the 0/22 reading, the 22-active denominator, the canonical-chart row counts, the `asset_throughput`
data-loss signature, and the `ka_gochara` table-identity split. The packets are unusually disciplined
about sampling and about distinguishing what they did and did not establish — Domain I and Domain D
in particular pre-empt the exact overreach I was sent to find.

**Three conclusions cannot be relied on as written.** All three are the same defect family as the
two known errors: a claim measured over the *observed* or *locally-scoped* population and stated as
if it covered the *defined* or *repo-wide* one.

| Cannot be relied on | Why |
|---|---|
| **T4's brief inventory** — "only one native asset brief exists"; "Kshetra and Sangam asset briefs CONFIRMED ABSENT … no file, no draft, no placeholder" | It is a listing of one directory presented as a repo census. **Twelve** per-asset L3 briefs exist elsewhere in the repo, including one for `ka_sangam`. T4's questions 3, 5, 6 and 7 to the native are built on the false premise. |
| **T3 §4.2's stated *reason* for the `CONSUMER_INTEGRATED`/`VALUE_EVALUATED` gap** — "there is no `source_kind` that could carry an operator's attestation … the receipt schema itself does not exist" | `source_kind` has **no** CHECK constraint and **no** enum, at either the DB or the ingress validator. T3 read six observed values as the defined vocabulary. T3's *conclusion* (the gap is real and blocking) survives; its *reason*, and therefore the size of the work to close it, does not. |
| **Domain G finding 5's "strongest evidence"** — that Pūrṇa's served availability logic "directly reads L3's `build_run_assets`/`build_runs` state" | The quoted SQL is a registry-owned `LIMIT 0` **shape probe**, not a served read. It establishes *reference*, not *consumption*. The direction-of-dependency conclusion may survive on the packet's other evidence; this citation does not carry it. |

Two further evidence-grading corrections (MATERIAL, below) narrow but do not overturn their
packets' conclusions.

**Nothing I found changes the headline verdict** (strategy GO-WITH-CONDITIONS; environment GO for
non-mutating work / NO-GO for production builds). Finding B-1 changes the *content of a native
question*; finding B-2 changes the *estimated shape of a named blocking work item*.

---

## 2. FINDINGS

### B-1 — CHANGES-A-DECISION · T4 · Scope error: a directory listing reported as a repo census

**Claim as written** (`KALA_BRIEF_CONFORMANCE_v1_0.md:72-77`):

> **Kshetra and Sangam asset briefs: CONFIRMED ABSENT.** No file matching `*KSHETRA*` or `*SANGAM*`
> exists (only 8 entries total, all listed above, all Gochara-scoped). … Only one native asset brief
> exists to check: `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`.

and question 7 (`:154-157`): "Kshetra and Sangam asset briefs are confirmed absent — **no file, no
draft, no placeholder**."

**What I measured.**

```bash
ls 00_ARCHITECTURE/briefs/ | grep -i "CLAUDECODE_BRIEF_L3"   # → 17
```

Twelve of the seventeen are **per-asset** L3 Kāla briefs:

`CLAUDECODE_BRIEF_L3_KA_BHAVISHYA_LEKHA_v1_0.md`, `…_KA_DASHA_KALA_…`, `…_KA_GOCHARA_…`,
`…_KA_GRAHA_SANCARA_…`, `…_KA_JIVANA_PARVA_…`, `…_KA_KALASUTRA_…`, `…_KA_KALA_DARSHANA_…`,
`…_KA_MUHURTA_SEVA_…`, **`…_KA_SANGAM_…`**, `…_KA_TULANA_…`, `…_KA_VIGHNAKARA_…`, `…_KA_YOJAKA_…`
(the remaining five are L3-wide: K0 service-asset-type, buildpath code fix, closeout cleanup, final
close, remediation).

`00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md` frontmatter, read directly:

```yaml
brief_for: ka_sangam — Saṅgam / THE CONVERGENCE ENGINE + its output (L3 Kāla; THE VALUABLE CORE) [ELEVATE]
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
swarm_coordination:
  wave: K4
  blocked_by: [ka_graha_sancara, ka_dasha_kala, ka_gochara, ka_muhurta_seva, ka_yojaka]
  blocks: [ka_vighnakara, ka_kala_darshana, ka_tulana, ka_bhavishya_lekha]
  may_touch: [...]
```

That is an asset-scoped execution brief with a wave, a dependency set, and a `may_touch` scope.
Also present and not seen by T4: `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_DP019_KSHETRA_GATE_ACCEPTANCE_v1_0.md`
(`status: SOURCE_PACKET_ACCEPTED`, `strategy_decision: DP-SD-019`) — in the **`nirmana/`** directory,
i.e. the same document family whose contracts T4 is measuring conformance against.

**Correction.** T4's contract-*conformance* verdict is probably unaffected: these briefs are from the
earlier Cowork/`L3_KALA_CAMPAIGN_PLAN` arc (`authored_by: Cowork 2026-06-21`), and none uses the
asset/interface-brief-contract's required header keys. But T4's *inventory* claim is wrong, and the
inventory is what the native's questions rest on. Rewritten honestly:

> Twelve per-asset L3 briefs exist under `00_ARCHITECTURE/briefs/`, authored under a prior campaign
> and none conformant to the asset/interface-brief contract's header. `ka_sangam` has one;
> `ka_kshetra` does not. The question for the native is whether these are superseded, or are to be
> re-headed to the contract — not whether asset briefs exist.

**Caveat on my own scope:** I read only `CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md`'s frontmatter and the
two Kshetra-named documents' heads. I did **not** establish whether a later ruling formally
supersedes the `CLAUDECODE_BRIEF_L3_*` family. That is the next question, not a claim I make here.

**Why the spot-check missed it:** T4's `method` block says the conductor independently verified "the
Gochara review verdict … via direct grep." The verification targeted the one claim that was already
right. The absence claim — the load-bearing one — was re-read at the same directory the subagent
used.

---

### B-2 — CHANGES-A-DECISION · T3 · Vocabulary misread: observed values read as the defined vocabulary

**Claim as written** (`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md:280-285`):

> Every existing event's `source_kind` is one of `git_commit`, `build_run`, `campaign_authorization`,
> `server_reconstructed`, `governed_catalogue`, `native_ruling` — all producer-side or
> campaign-internal. **There is no `source_kind` that could carry an operator's attestation, so the
> gap cannot be closed by reusing an existing type with different content; the receipt schema itself
> does not exist.**

and `:301-303`: "This gap is structural, not a backlog item."

**What I measured — at the schema, then at the ingress validator.**

DB authority (live):

```sql
SELECT column_name, data_type FROM information_schema.columns
 WHERE table_schema='nirmana_evidence' AND table_name='nirmana_elevation_campaign_events';
-- event_type | text        (nullable NO)
-- source_kind| text        (nullable NO)

SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
 WHERE conrelid='nirmana_evidence.nirmana_elevation_campaign_events'::regclass;
-- _pkey                  PRIMARY KEY (event_id)
-- _definition_fk         FOREIGN KEY (campaign_id, definition_revision) REFERENCES …
-- _idempotency_unique    UNIQUE (campaign_id, definition_revision, idempotency_key)
```

**There is no CHECK constraint on `event_type` or `source_kind`.** Both are open `text`.

The trigger the campaign relies on (`nirmana_elevation_guard_server_reconstructed_insert`, body read
from `pg_proc`) does not enumerate either — it *partitions* on one value:

```
IF NEW.source_kind = 'server_reconstructed' THEN
  IF session_user <> 'nirmana_evidence_ingress_writer' THEN RAISE EXCEPTION 'server evidence requires ingress writer'; END IF;
ELSIF session_user <> 'nirmana_campaign_control_writer' THEN RAISE EXCEPTION 'non-server evidence requires control writer'; END IF;
```

`platform/scripts/nirmana/README.md:82-84` states the design intent explicitly: "The required
identity is derived from the submitted `source_kind`, **never from a hardcoded** [list]" — the
absence of an enum is deliberate.

The **actual** gate is one file up the stack,
`platform/src/lib/nirmana-elevation/evidence-command.ts:50-63`:

```ts
event_type: z.enum([
  'asset_analysis_accepted','optimization_verdict_accepted','implementation_accepted',
  'accepted_rebuild_observed','integrity_verified','asset_frozen','probe_accepted',
  'static_accepted','source_accepted','empty_accepted','retired_with_disposition','producer_covered',
]),
…
source_kind: z.string().min(1).max(128),          // ← line 68: OPEN
```

**Correction.** The barrier is a **closed `z.enum` on `event_type` in one TypeScript validator**, not
a schema. `source_kind` is open text at every layer. Closing the `CONSUMER_INTEGRATED` /
`VALUE_EVALUATED` gap therefore requires: (a) one new member in that `z.enum` plus its
`superRefine` payload/`source_ref` contract (the file already carries twelve such per-type contracts
to copy), and (b) the hard part — designing the attestation semantics and the detector that could
make the receipt read *false*. **No migration is required. No new `source_kind` vocabulary is
required.**

T3's conclusion — the gap is real, no existing type is admissible, `Accepted N/22` is honestly 0/22
— **stands unchanged and I confirm it**. What changes is the native's picture of the work: "design a
receipt schema that does not exist in any form" reads as a schema-design project; the true shape is
a validator extension plus a detector-design decision. Given T3 is the packet that establishes the
gap as a named blocker, the misestimate is decision-relevant.

---

### B-3 — MATERIAL · Domain G · `LIMIT 0` probe presented as a live runtime read

**Claim as written** (`_work/DOMAIN_G.md:192-208`), under the heading "**The live runtime dependency
(the strongest evidence)**":

> This is compiled into the served availability-contract query for two Pūrṇa-consumed descriptors and
> **directly reads L3's `build_run_assets`/`build_runs` state** keyed on a `ka_*` asset id.

**What I measured** (`platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts`).
The packet's own quotation contains the refutation — it ends `… DESC LIMIT 0`, which returns no rows.
Confirmed verbatim in source at the cited location, and every CTE in the contract is `LIMIT 0`:

```
), build_observation AS (
  SELECT br.id::text AS build_id, br.state AS build_state, bra.state AS asset_state
    FROM build_run_assets bra JOIN build_runs br ON br.id = bra.run_id
   WHERE br.chart_id = $1::uuid AND bra.asset_id = 'ka_bhavishya_lekha'
   ORDER BY COALESCE(bra.ended_at, br.ended_at, br.created_at) DESC LIMIT 0
) SELECT 1 FROM handler_page CROSS JOIN families CROSS JOIN source_classification CROSS JOIN build_observation
```

The file's own docstring (`:11-16`) defines what this field is:

> **Registry-owned, read-only probe for a handler's actual source query.** … SQL remains source-owned
> here so an untrusted snapshot cannot inject a query into the overlay loader.

and a sibling contract's inline comment states the mechanism outright: "`LIMIT 0` validates the exact
[shape]". The *served* handler is named separately in `source_refs`
(`platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts:74-137 | :209-371`).

**Correction.** Against the six-way distinction: this establishes that Pūrṇa's availability contract
**references** a `ka_*` asset id and the L3 build tables — i.e. `present`. It does not establish
`consumed`, and certainly not `effect_traceable` or `served`. Domain G's *conclusion* (Pūrṇa depends
on L3, not the reverse) may well hold — it also rests on `editorial.ts:113-115` and on the execution
plan's own prose — but the item it labels "the strongest evidence" is the weakest of the three.
**I did not locate an execution site for this `sql` field** beyond the generated census artifact, so
I cannot say whether the probe is run against production at all; I can only say the query as written
cannot return a row.

---

### B-4 — MATERIAL · T3 §2 / §4.4 · Lane D dismissed as CI-sourced when it also carries a deployed-revision receipt

**Claim as written** (`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md:178` and `:310-316`):

> **BARRED from per-asset Deployed** on two counts: lane-scoped not asset-scoped; **evidenced by
> `ci_run_id` — exactly the excluded class**. … `{"lane_id":"D","main_sha":"…","ci_run_id":"…","serving_sha":"…"}`

**What I measured** (live):

```sql
SELECT jsonb_object_keys(evidence_payload) FROM nirmana_evidence.nirmana_elevation_campaign_events
 WHERE event_type='foundation_lane_accepted'
   AND definition_revision='t3-2026-09-11-8b884eac' AND entity_id='D';
-- lane_id · main_sha · ci_run_id · serving_sha · schema_version · manifest_sha256 · serving_revision

SELECT evidence_payload->>'serving_revision', evidence_payload->>'ci_run_id' FROM … same rows;
-- amjis-web-02256-cv4 | 34625204534
```

The payload carries `serving_revision = amjis-web-02256-cv4` — a real Cloud Run revision id — which
T3's own key list omits. §8's exclusion is "may not be **claimed from** CI, PR, local run or
dashboard"; a payload that additionally carries an actual deployed revision is not claiming *from*
CI merely because a `ci_run_id` field sits beside it. The §8 gate text for that rung asks for
"authorized actual revision/environment" — which `serving_revision`/`serving_sha` is the shape of.

**Correction.** One of T3's two stated grounds for barring lane D falls. **The other ground —
lane-scoped, not asset-scoped, and no per-asset migration/rollback limb — survives and is sufficient
to carry the conclusion.** So `DEPLOYED_ACCEPTED` remains a real per-asset gap; it is a *grain* gap,
not a *provenance-class* gap. That distinction matters for how the receipt is designed: the existing
lane-D minting path already produces admissible deploy provenance and can be re-grained, rather than
needing a new evidence class.

---

### B-5 — MATERIAL · T5 Tension 1 · The seed *file* is not the live *registry*; the disagreement is six-way

**Claim as written** (`_work/T5.md`, sources block and Tension 1 surface #2):

> **SEED** = `platform/scripts/seed/asset_registry_seed.ts` (**the live, currently-maintained seed**)
> … `asset_registry_seed.ts:2123` `target_table: 'kala_gochara_windows'`; `:2124` `count_sql: "SELECT
> COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='3.0'"`

**What I measured.** The seed file (current line numbers 2124/2125, one line off T5's citation) says
exactly that. The **deployed `asset_registry` row** does not:

```sql
SELECT asset_id, target_table, count_sql FROM asset_registry
 WHERE asset_id IN ('ka_gochara','ka_gochara_sweep','ka_gochara_v3_century_materialize');
-- ka_gochara                        | kala_gochara_windows    | SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation='2.0'
-- ka_gochara_sweep                  | kala_gochara_windows    | … kala_gochara_windows … generation='v1'
-- ka_gochara_v3_century_materialize | kala_gochara_windows_v2 | … kala_gochara_windows_v2 … generation LIKE 'g3_%'
```

The live `ka_gochara` row is **internally inconsistent** (`target_table` → `kala_gochara_windows`,
`count_sql` → `kala_gochara_windows_v2`) and **disagrees with the seed file it is supposed to be
generated from**. Live row counts for the canonical chart:

```sql
kala_gochara_windows    generation '3.0'         →   914
kala_gochara_windows    generation 'v1'          → 16297
kala_gochara_windows_v2 generation '2.0'         →    87
kala_gochara_windows_v2 generation 'g3_utkarsha' →   914
```

and `asset_throughput` for the same chart gives `ka_gochara.rows_written = 87`,
`ka_gochara_v3_century_materialize.rows_written = 914` — so the live `count_sql` (87) currently
matches the writer, while the seed file's `count_sql` (914) would have attributed the century
materialiser's output to `ka_gochara`. The seed's own comment at `:2108-2112` warns about a third
combination ("`kala_gochara_windows_v2` for `generation='3.0'`, a combination that table never
carries").

**Correction.** T5's Tension 1 is real and if anything understated, but one of its five "governing
surfaces" is a **file**, not production, and the file and production disagree. Any readiness signal,
cockpit count, or `count_sql`-driven gate drawn from "the seed" must be re-read from
`asset_registry` itself. Whether the divergence is intentional (a pending re-seed) or drift **I could
not determine** — I did not trace which migration or seed run last wrote that row.

---

### B-6 — MINOR · Traceability matrix · Cross-cluster synthesis understates its own evidence

**Claim as written** (`KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md:675-682`):

> a cluster of Spine/Kshetra assets — `ka_sangam`, `ka_kalasutra`, `ka_vighnakara`,
> `ka_kala_darshana`, `ka_bhavishya_lekha` — all show live or near-live consumer wiring pointed at
> tables holding zero rows … while `asset_throughput` independently shows **two of them**
> (`ka_sangam`, `ka_kalasutra`) *did* write substantial row counts … before going `stale` with no
> recorded error.

**What I measured** (live, canonical chart): **all five**, not two, show the signature.

| asset | rows_written | state | error? | last_built_at | table rows now |
|---|---:|---|---|---|---:|
| `ka_kalasutra` | 335,403 | stale | none | 2026-08-13 | `kala_activation` = 0 |
| `ka_sangam` | 14,868 | stale | none | 2026-08-13 | `kala_convergence` = 0 |
| `ka_kala_darshana` | 750 | stale | none | 2026-08-13 | `kala_darshana` = 0 |
| `ka_vighnakara` | 536 | stale | none | 2026-08-13 | `kala_obstruction` = 0 |
| `ka_bhavishya_lekha` | 100 | stale | none | 2026-08-13 | `kala_bhavishya` = 0 |

The understatement is in the matrix only; `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s E-3 row gets
it right (names all five tables behind the `ON DELETE CASCADE` from `kala_*.signal_id` →
`bodha_msr_signals.signal_id`, migration 403). Worth correcting so the matrix is not read as a
narrower finding than the audit's own.

---

### B-7 — MINOR · T5 citation drift

`_work/T5.md` cites `asset_registry_seed.ts:2123` for `target_table` and `:2124` for `count_sql`;
current `main` has these at `:2124` and `:2125`. One line. Noted only because T5's own Tension 9 is
"REG's cited line ranges have drifted from the code they cite" — the packet is subject to the defect
it documents.

---

## 3. LOAD-BEARING CLAIMS I CONFIRMED

Each re-derived at the authority, not by re-running the packet's query.

**T3 §1 — the event census and the 0/22 reading. Exact, to the row.**
```sql
SELECT definition_revision, definition_status FROM nirmana_evidence.nirmana_elevation_campaign_definitions;
-- t0 ×3 superseded · t1 superseded · t2 superseded · t3-2026-09-11-8b884eac FROZEN
SELECT count(*) … WHERE definition_revision='t3-…' AND entity_id LIKE 'ka\_%';   -- 0
SELECT count(*) … WHERE definition_revision='t3-…' AND layer='L3';               -- 0
SELECT count(DISTINCT event_type), max(recorded_at) FROM …;                      -- 17 | 2026-09-11 17:25:50+00
```
The `t3` layer/type breakdown reproduces T3's eleven-row table line for line (L2 ×7 types over 8
entities, plus the four campaign-scoped types). `t3` is still the frozen definition — **not stale.**

**No post-audit drift in the evidence ledger.** The ledger's newest row is 2026-09-11 17:25 UTC. A
sibling checkout carries commits narrating "L2 cycle #80/#81/#82 … FROZEN / submitted and verified",
which would look like un-recorded activity; `git log --date=iso` dates them **2026-09-09**, i.e.
before the ledger's last write. No anomaly. Flagged because it is the shape of thing that would
falsify T3's headline, and it does not.

**The 22-active denominator.** `asset_registry` holds 23 `ka_*` rows; exactly one
(`ka_gochara_sweep`) has `is_active = false`, `data_disposition = RETAINED_AS_CAPITAL`,
`superseded_by = ka_gochara`. 22 active + 1 protected-retired — as every packet assumes.

**Traceability matrix row counts (canonical chart), exact:** `kala_kota_chakra` 585 ·
`kala_moorti_nirnaya` 71 · `kala_sudarshana_varsha` 120 · `gochara_resonance_map` 765 · `kala_field`
8,570,075 ("~8.6M") · and all five of `kala_convergence` / `kala_activation` / `kala_obstruction` /
`kala_darshana` / `kala_bhavishya` = **0**. The matrix's dominant pattern is real and live.

**Domain D check 3 — the generation substrate is unexercised. Exact.**
`l1_data_plane_generation_heads` 0 · `l2_data_plane_generation_heads` 0 ·
`l1_data_plane_generations` 0 · `data_plane_l2_producer_generations` 0. Still four zeros today.

**T4 §10 — the exit-gate vocabulary mismatch is real.**
`MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT_v1_0.md:143-147` defines `PRODUCER_READY`,
`INTEGRATED`, `DEPLOYED_OPERATIONALLY_ACCEPTED`, `CONSUMER_VALUE_DEMONSTRATED`,
`EMPIRICALLY_EVALUATED`. `MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md:91` declares
`delivery_target: "LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED +
VALUE_EVALUATED"`. Two disjoint vocabularies, as T4 says.

**T5 Tension 1's code citations.** `writers/ka_gochara.py:120` is exactly
`TABLE = "kala_gochara_windows_v2"`. The live four-way generation split in the two tables (above)
confirms the structural disagreement is not documentary only.

**F1 is genuinely fixed on this branch** — `grep -c definition_revision`: `egate.sql` = 4,
`capsule_audit.sql` = 7. The audit's own stale-note and its cycle-8 supersession are both accurate.

**Domain I does not overreach, and neither does the deliverable that consumes it.** The packet states
"15 of 137 (≈11%), and 15 of 1059 (≈1.4%)", says the sample was "deliberately non-random" and
"not representative", and adds an explicit "what this domain does NOT establish" paragraph.
`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md:1001-1003` carries that caveat verbatim into the verdict
section and phrases the GO line as "Domain I found **0 of 15 sampled** branches genuinely
undelivered." **No sampling-as-census defect found.** This is the single cleanest packet in my scope.

**Domain D and T6 likewise self-limit correctly.** Domain D names both the evidence that would have
flipped it to READY and to NOT READY and reports neither was found — the §N.8 discipline applied to
its own verdict. T6 reports "zero code hits" for F15/F16 purpose codes and knowledge-time, then
separately grades the one real detector it did find (`test_ka_jivana_parva_circularity_guard.py`) and
explicitly labels it "a proxy, not the real target" covering 1 of ~21 writers. Both are honest about
scope without my needing to correct them.

---

## 4. COULD NOT VERIFY

Stated as scope limits, not as implicit passes.

- **Domain D checks 2 and 4** (the `session_user <> 'data_plane_builder'` / `data_plane_migrator`
  guards and the rollback/resume trace in migrations 1035/1036). I did not re-read those migration
  files; only check 3's live row counts were re-measured. The guard quotes are unverified by me.
- **Domain H's seven import tables.** I did not re-grep any of the hub importer sets, the
  `_local_import_files` closure, or the `provenance_inventory.py` / `runner.py` consumers. Domain H's
  blast-radius and "no code-digest → data-staleness bridge" conclusions are unaudited by this pass.
- **Domain G findings 1–4** (Pūrṇa territory, the lease table's stale `ACTIVE` rows, the shared-surface
  partition, the `L3-REQ`/`PA-REQ` interlock). I did not fetch `origin/campaign-coordination`, so the
  six-stale-`ACTIVE`-rows finding is neither confirmed nor refuted by me. Only finding 5's evidence
  was re-graded (B-3).
- **Domain J entirely.** Its `.claude/settings.local.json` and `dbenv.sh` observations are about
  `/Users/Dev/madhav-l3/audit`, a different worktree from mine; I did not read either file. Its DR /
  PITR findings rest on document status fields I did not re-read.
- **Whether the twelve `CLAUDECODE_BRIEF_L3_KA_*` briefs are formally superseded** (B-1). I read one
  frontmatter. If a later ruling retires that family, T4's *practical* conclusion may be closer to
  right than its *stated* one — but the stated one is still a directory listing sold as a census.
- **Whether the `ka_gochara` seed-file/live-registry divergence is intentional** (B-5). I did not
  trace the last writer of that `asset_registry` row.
- **Whether the `source_query_availability.ts` probe SQL is executed against production at all**
  (B-3). I found no execution site outside the generated census artifact; that establishes my search
  scope, not absence.
- **T1's per-asset "receiving operator today" gradings.** I re-measured the row counts underneath
  them but did not re-trace a single consumer path. The matrix's own confidence labels
  (high/medium/low, `COULD NOT VERIFY`) are carried forward unaudited.

---

*Lane B second reader, 2026-09-22. Read-only. 8 findings; 3 change a decision or a work estimate,
4 are evidence-grading corrections that narrow without overturning, 1 is cosmetic. Nine load-bearing
claims independently reproduced at the authority.*
