---
artifact: D_E022_PINS_READMISSION_AUTHORITY
version: 1.0
status: PINS_READMISSION_AUTHORIZED
date: 2026-09-29
decision: D-E022
campaign: pravaha
item: A0.3
---

# D-E022 — Nirmāṇa analysis-layer pins re-admission authority (PR #2731 merge)

## The decision, verbatim

From `/Users/Dev/pravaha/run/EVENTS.jsonl`, 2026-09-29T10:25:04+00:00, actor `steward`:

> {"kind":"decision","actor":"steward","decision":"D-E022","state":"decided","detail":"Native, 2026-09-29: 'Accept all recommendations.' — pins re-admission at the #2731 merge is authorised, per MERGE_HYGIENE_12_10c_RUNBOOK","ts":"2026-09-29T10:25:04+00:00"}

The native's words, 2026-09-29: **"Accept all recommendations."** — recorded as D-E022.

## Scope of the authority granted

This authority is narrow. It authorises exactly one operation: fail-closed
successor admission (`nirmana_analysis_layer_pins.py --admit-successor`) for the
two stale analysis layers detected on PR #2731 after the origin/main merge
(merge commit `8eeeb6e2a`), per `MERGE_HYGIENE_12_10c_RUNBOOK.md` step 2 and
ESCALATIONS.md E-022:

- **L1** (`ga_` prefix): successor over the G-10/M-6 changeset delta.
- **L3** (`ka_` prefix): successor over the lane's gochara writer changeset delta.

It does **not** grant a general re-pin capability, does not touch any other
layer, and does not authorise membership changes (none occurred — the changed
set is digest drift on existing writers only).

## Why the pins went stale

The merge of `origin/main` (`55ec5e3555a8bf2b4a3ed4f42397f03a56396b2d`) into the
lane brought the lane's writer-source edits and main's writer-source edits into
one tree. The committed pins still name the pre-merge aggregate digests
(`93de3b2c…` L1, `dfcf30d8b3d2…` L3); the merged tree derives `b3674dfb…` (L1)
and `64ca6e06c175…` (L3). This is detector-correct staleness: the data (writer
sources) moved; the receipt did not. Per ADK-0026 the receipt is re-admitted,
not the detector weakened.

## Per-asset delta classification

Computed by comparing each writer's provenance closure
(`asset_runner._writer_source_paths` + transitive local-import closure) between
`55ec5e3555a8bf2b4a3ed4f42397f03a56396b2d` and the merge HEAD.

### L1 (6 changed assets)

| Asset | Classification | Cause |
|---|---|---|
| `ga_strength` | `approved_intentional_change` | own writer `ga_writers/ga_strength_writer.py` edited on the lane |
| `ga_sensitive` | `approved_intentional_change` | own writer `ga_writers/ga_sensitive_writer.py` edited on the lane |
| `ga_ayurdaya` | `derived_import_change` | imports `ga_strength_writer.py`; no own-module edit |
| `ga_sensitive_degree` | `derived_import_change` | imports `ga_strength_writer.py`; no own-module edit |
| `ga_structural` | `derived_import_change` | imports `ga_strength_writer.py`; no own-module edit |
| `ga_yoga` | `derived_import_change` | imports `ga_strength_writer.py`; no own-module edit |

### L3 (7 changed assets)

| Asset | Classification | Cause |
|---|---|---|
| `ka_gochara` | `derived_import_change` | `gochara_grammar/*`, `gochara_intensity/enrichment.py` imports moved; no own-module edit |
| `ka_sangam` | `derived_import_change` | `gochara_kernel/*`, `ka_gochara/service.py` imports moved; no own-module edit |
| `ka_gochara_resonance` | `approved_intentional_and_derived_import_change` | own `ka_gochara_resonance/writer.py` edited; `gochara_grammar/derived_points.py` import moved |
| `ka_gochara_v3_century_materialize` | `approved_intentional_and_derived_import_change` | own writer edited; `gochara_kernel/*`, `gochara_v3/*`, `gochara_grammar/*`, `gochara_intensity/*` imports moved |
| `ka_kshetra` | `approved_intentional_and_derived_import_change` | own `ka_kshetra/writer.py` edited; `stage4_field.py` import moved |
| `ka_moorti_nirnaya` | `approved_intentional_and_derived_import_change` | own writer + `logic.py` edited; `gochara_kernel/*` imports moved |
| `ka_vedha_gochara` | `approved_intentional_and_derived_import_change` | own writer + `logic.py` edited; `gochara_kernel/*`, `gochara_grammar/*` imports moved |

## Authority identity

The immutable approval identity for this authority is the commit that first
introduced this document: `442f1ed955a701008b2a975c7df80d543fbbc67a`
