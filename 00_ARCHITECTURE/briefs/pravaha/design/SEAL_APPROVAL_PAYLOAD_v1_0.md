---
artifact: SEAL_APPROVAL_PAYLOAD
version: "1.0"
status: "PROPOSAL for Codex round 12 (answers R11-3, workflow/runbook side). Stream A builds the job-side functions; the schema below is to be agreed with Stream A through the steward before code. Authorises nothing."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0
---

# The seal approval payload — what is approved, hashed, recomputed and receipted

## 1. The defect this answers (R11-3)
v1.2 of the runbook let the verifier's `--report-only` step produce a "brief" and let the sealer re-check "the gate". Codex found: (i) `--report-only` **skips** the gate (`gate_all = [] if report_only`) while labelling `gate_source` as the combined function; (ii) the runbook required the **raw SQL function** to return zero on a **candidate** row, which contradicts the (correctly disclosed) need for the candidate adapter; (iii) **recomputing a gate result is not recomputing what was approved** — two different valid candidates can both give `[]`; (iv) the promised approver login / run id are **not columns** of the generation-seal table.

## 2. The approval payload (canonical JSON; its sha256 is THE brief digest)
Schema `seal_approval_payload/1`, produced by the verifier identity (new `--brief` mode of the verification job — **not** `--report-only`), every field computed from the database by the same code the seal uses:

| field | content |
|---|---|
| `schema` | `"seal_approval_payload/1"` |
| `chart_id`, `generation`, `manifest` | `{manifest_id, status:"candidate", horizon, convention_id, input_generation_vector_digest}` |
| `result_policy` | the manifest's policy id (`all_null_candidate/1`) |
| `candidate_gate` | `{source:"candidate_adapter/1 over ka_gochara_candidate_gate_violations", violations:[]}` — **evaluated by the candidate adapter** (the raw function is evaluated by the seal itself, on the published row, see §3), and `violations` MUST be empty for a brief to be produced at all |
| `classes[]` | per event class: `inventory_digest`, `ledger_digest`, and per included grain `{path_id, rule_version, status:"VERIFIED", windows_content_digest, expected_windows_digest, derivation_inputs_digest, verified_at, verifier_policy_version, runner:{commit, implementation_digest}}` — read from the **persisted attestations**, not re-derived |
| `generation_output_identity` | **one digest over ALL output of the generation** — every record, prerequisite, contact, window, member link, path pin and inventory header, in canonical order, **including held/superseded-version rows** (R11-1: it must not be possible for an output outside the included grains to exist without changing this digest) |
| `code` | the verification job's `DEPLOY_SHA` and implementation digest (must equal the manifest's pin), the sealing workflow's commit |
| `ledger` | for each of 1204, 1206, 1232, 1233, 1240, 1241: `{filename, sha256, applied_at}` from the migration ledger |
| `disclosures` | the ids and versions of the disclosures that attach to the generation (all-NULL policy, certification limits, retained-attestation behaviour) |
| `seal_is_not_a_flip` | the literal sentence |

## 3. The flow (and exactly what each step is allowed to claim)
1. **Brief** (verifier identity, read-only): evaluate the candidate adapter, read the persisted attestations, compute the payload, write it as a workflow artifact with its sha256. **Refuses to produce a brief if any violation exists.** (Stream A: a real `--brief` mode; `--report-only` stays a report.)
2. **Display** the artifact (the steward, on the owner's authority per his direct ruling) before the approval gate.
3. **Approval** (the `gochara-seal` environment): the approver supplies **the brief digest** (the sha256) as part of the approval comment; the digest is the thing approved.
4. **Seal** (sealer identity), **one transaction**: take the **seal locks** (chart, then global — the order the builder uses) → **recompute the payload** with the same code → if its sha256 ≠ the approved digest, **refuse** (a changed candidate whose gate is still empty invalidates the old approval) → publish the candidate (`ledger.publish`) → run the **authoritative SQL seal** (`ka_gochara_seal_generation`, whose triggers run the combined gate **on the published row**) → write the **approval receipt** → commit. A failure anywhere rolls the whole transaction back: nothing is half-published.
5. **Claim wording** (squarely): the brief is **not** an independent human check (native ruling #2); what it guarantees is (a) the candidate adapter found no violation, (b) every grain is `VERIFIED` by the separate job under a runner pinned to the manifest, (c) the **exact output** that was shown is the output that is sealed, (d) the authoritative SQL checks passed on the published row.

## 4. The approval receipt — storage (DECISION NEEDED; I recommend R2 for this milestone)
The runbook promised "approver login and run id are recorded on the seal row"; the seal table has no such columns. Options:
- **R1 — a DB receipt:** a new append-only table `ka_gochara_seal_approval(chart_id, generation, brief_digest, approver_login, approved_by_note, run_id, run_attempt, approved_at)` with a FK to the seal row, insertable only by the sealer, in the same transaction as the seal. Durable and DB-enforced. **Cost:** it creates a table in the protected `public` schema, so it is a **protected-window migration** (a new file in the window list, the rehearsal re-run, Codex review) and needs a sealer INSERT grant in 1241.
- **R2 — a durable repository receipt:** the sealing job writes `brief.json`, its sha256, the approval record (login, run id, attempt, timestamp, comment) and the seal's manifest id to a **receipt file committed to `main` by pull request** (`00_ARCHITECTURE/briefs/pravaha/receipts/SEAL_RECEIPT_<chart>_<generation>.md`), linked to the seal by `manifest_id`/digest. Durable and auditable (git history), **not DB-enforced**. No migration.
I recommend **R2 for the all-NULL milestone** (nothing is served; the seal is not a flip) and **R1 together with numeric activation**; the claim then says "a durable receipt linked to the seal", not "recorded on the seal row".

## 5. Narrow read grants this needs (1241 v4 — to be written AFTER Stream A's `--brief` exists, so each is proven necessary the same way as the others)
Expected: the verifier's SELECT on whatever the generation-wide output identity reads that it does not already hold (the held/superseded-version rows are in the tables it already reads); **column-level SELECT `(filename, sha256, applied_at)` on the migration ledger table** for the `ledger` field. No write grant. If the brief needs more, the necessity test names it.

## 6. Open points for Stream A (through the steward)
(1) the `--brief` mode and the candidate-adapter call; (2) the `generation_output_identity` function (SQL or Python, one canonical implementation shared by brief and sealer); (3) the sealer-side recompute under the seal locks, in the publishing transaction; (4) R11-1's generation-wide output checks produce the same "no output outside the permitted grains" fact the identity digest relies on.
