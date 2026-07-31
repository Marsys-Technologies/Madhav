---
canonical_id: PB_SCHEMA_HASH_PIN
version: 1.0
status: CURRENT
lane: SAMAPTI B-PB-SCHEMA-PIN
implements: SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §8.5
closes: REPORT_PB-3.md §G item 1 (residual gap)
date: 2026-07-30
---

# PB_SCHEMA_HASH_PIN — the real schema hash pin for `mimamsa_predictions`

## The gap this closes

`MEMO_PB-3_0.md` (item 3) ruled `mimamsa_predictions` **"hash-pinned at
BIND"** — its schema plus the live row count recorded before PB-3's lanes
opened, to be re-verified unchanged at gate close. `REPORT_PB-3.md` §G item 1
found that this demanded schema *hash* pin never actually existed:

> "the brief's demanded schema *hash* pin never existed — only a prose
> row-count; no future wave has anything but this report's recorded
> fingerprint (`b730b9f3…`) to compare against."

In other words: a sentence saying "286 rows, matches the BIND pin" was
written down, plus one opaque fingerprint string with no query, no script,
and no committed baseline behind it. Nothing could re-derive `b730b9f3…`, and
nothing could tell a future session whether a schema change had happened.
That is not a pin — it's an assertion.

This lane establishes the real thing.

## What was built

| File | Purpose |
|---|---|
| `platform/scripts/governance/schema_pin_mimamsa_predictions.py` | The reproducible hash computation + comparator. `--self-test` (DB-free, CI-safe), `--verify` (live-DB, compares against the baseline), `--print-canonical` (regenerate). |
| `platform/scripts/governance/MIMAMSA_PREDICTIONS_SCHEMA_PIN.json` | The committed baseline: the hash, the exact canonical text it was computed from, the row count at pin time (informational only), and re-derivation instructions. |

## What the hash covers, and what it deliberately does not

**Covers** every DDL-relevant fact about the table, each section internally
ordered deterministically so re-running the same query always produces the
same text:

- every column — `column_name`, `udt_name` (exact type, not the coarser
  `data_type`), `is_nullable`, `column_default` — ordered by
  `ordinal_position`
- every constraint — `conname`, `contype`, `pg_get_constraintdef(oid)` —
  ordered by `conname`
- every index — `indexname`, `indexdef` — ordered by `indexname`

These are concatenated into one string (`TABLE|...` header, then one
`COL|...` / `CON|...` / `IDX|...` line each) and SHA-256'd.

**Does not cover row count.** `MEMO_PB-3_0.md` is explicit that
`mimamsa_predictions`' row count is *expected* to move via legitimate L5
STRUCTURAL-mode rebuilds (`mi_bhavisya.py`'s DELETE-then-INSERT idempotency
pattern, CLAUDE.md §N.3). Folding the count into the hash would turn every
routine rebuild into a false "schema drift" alarm. Row count is tracked
alongside the hash as informational context, reported by `--verify` but never
part of the pass/fail verdict.

## The baseline, as actually established (2026-07-30)

Verified read-only against production Postgres (`amjis`, `PostgreSQL 15.17`)
via the postgres MCP tool — no row inserted, no schema mutated, SELECT-only
throughout, matching the same anti-gaming standard `REPORT_PB-3.md` itself
was held to.

```
schema_hash_sha256: 72733fc6b8ea188ab5b12b679f28fcac9435835ab26a3cdefa7848a6f00fe8a4
row_count_at_pin:   286   (matches REPORT_PB-3.md's 286-row BIND figure exactly — no drift since PB-3 closed)
```

The exact canonical text this hash was computed from — and the three raw
queries (`information_schema.columns`, `pg_constraint` via
`pg_get_constraintdef`, `pg_indexes`) that produced it — are recorded
verbatim in `MIMAMSA_PREDICTIONS_SCHEMA_PIN.json`.

**Both `--self-test`'s can-fail proof and a live simulated-drift run were
performed before this baseline was committed:**

1. `python3 platform/scripts/governance/schema_pin_mimamsa_predictions.py --self-test`
   exits 0 and, internally, proves the hash function is (a) deterministic —
   identical input hashes identically twice — and (b) sensitive to drift —
   mutating a fixture column's nullability, a fixture constraint definition,
   and a fixture index definition each independently changes the hash.
2. The live canonicalization path (`build_canonical_text` + `compute_hash`,
   fed the actual rows returned by the three live queries above) was checked
   against the manually-derived hash and matched byte-for-byte. It was then
   exercised end-to-end through `_verify()` twice: once against the real
   baseline (PASS, exit 0) and once with one live column's type mutated from
   `uuid` to `text` (DRIFT correctly detected, exit 1) — the fail-then-pass
   standard `REPORT_PB-3.md` itself established as house style, applied here
   to the tool that replaces its own gap.

## How a future session re-derives and compares this pin

```bash
# 1. Point at the production database (same convention as
#    msr_referential_integrity.py — DATABASE_URL, psycopg3 or psycopg2 fallback).
export DATABASE_URL="postgresql://<user>:<pass>@<host>:<port>/amjis"

# 2. Compare live schema against the committed baseline:
python3 platform/scripts/governance/schema_pin_mimamsa_predictions.py --verify
# exit 0  -> live schema matches MIMAMSA_PREDICTIONS_SCHEMA_PIN.json. No drift.
# exit 1  -> DRIFT. The live hash differs from the baseline — a real schema
#            change happened to mimamsa_predictions since 2026-07-30. Route to
#            DVA/native: was this change ruled? If yes, regenerate the
#            baseline (step 3) as part of that same ruling. If no, this is a
#            live finding — investigate before touching the file.
# exit 2  -> environment error (no DATABASE_URL, driver missing, table absent).

# 3. To regenerate the baseline after a DELIBERATE, ruled schema change:
python3 platform/scripts/governance/schema_pin_mimamsa_predictions.py --print-canonical
# Paste the printed canonical text and sha256 into
# MIMAMSA_PREDICTIONS_SCHEMA_PIN.json's canonical_text / schema_hash_sha256
# fields, update pinned_at / pinned_by, and record the ruling that authorized
# the change in this file's changelog.

# 4. CI-safe check (no DB required) — proves the tool itself still works:
python3 platform/scripts/governance/schema_pin_mimamsa_predictions.py --self-test
```

No prior artifact gave a future session anything to run. This one does.

## Disposition

`REPORT_PB-3.md` §G item 1's gap ("the brief's demanded schema hash pin never
existed") is closed by this lane. `REPORT_PB-3.md` itself is left unmodified
— it is a sealed, `CLOSED`-status report and its own historical text (the
prose row-count, the `b730b9f3…` fingerprint) is accurate as a record of what
existed *at PB-3's close*; this document and the two files above are the
correction that gives the *next* wave something real to check drift against,
per `SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §8.5`'s framing ("Establish the pin
properly now so the next wave has a real baseline").

*End PB_SCHEMA_HASH_PIN v1.0.*
