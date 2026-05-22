---
artifact: CLAUDECODE_BRIEF_MCPT_V33_S2_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.3-S2
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT
branch: feature/mcpt-depth
depends_on: [v3.3-S1]                                                   # same-WT sequential
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: chart_facts KP cuspal + planet + significator + ruling-planets + upagraha ingestion
source_data: 00_ARCHITECTURE/SOURCE_DATA/jagannatha_hora_exports/
---

# v3.3-S2 — KP + Upagraha Ingestion

You are a Claude Code sub-agent on WT-E. Runs after v3.3-S1. Closes the KP and upagraha depth gaps in `chart_facts`.

Read: `MCP_ARCH §9.2 items 11, 12`; v3.3-S1 brief for the ingestion helper pattern.

## §1 — Scope

Ingest four `chart_facts` category groups:
- **kp_cusp**: 12 cusps × (cusp_lord, star_lord, sub_lord) = 36+ rows
- **kp_planet**: 9 planets × (cusp_lord, star_lord, sub_lord) = 27 rows
- **kp_significator**: per-planet significator hierarchy
- **upagraha**: Gulika, Mandi, Yamaganda, Kala, Maandi positions

## §2 — Source data prerequisite

`00_ARCHITECTURE/SOURCE_DATA/jagannatha_hora_exports/native_chart_full_export.csv` (same as v3.3-S1; reused). If missing, halt.

## §3 — Files in scope

```
platform/scripts/bootstrap/bootstrap_chart_facts_kp.ts                   # new (cusp + planet + significator combined)
platform/scripts/bootstrap/bootstrap_chart_facts_upagraha.ts             # new
platform/test/bootstrap/chart_facts_kp.test.ts
platform/test/bootstrap/chart_facts_upagraha.test.ts
```

Reuses `chart_facts_ingester.ts` helper from v3.3-S1.

## §4 — Files NOT in scope

Same as v3.3-S1.

## §5 — Ingestion specification

KP cuspal rows: subkey format `<house_num>.<role>` (e.g., `1.cusp_lord`, `1.star_lord`, `1.sub_lord`).
KP planet rows: subkey format `<planet>.<role>` (e.g., `Saturn.sub_lord`).
KP significator: subkey format `<planet>.significator_houses` with array value.
Upagraha: subkey = upagraha name (e.g., `Gulika`); value_text = sign+degree+house.

`build_manifests` entries for each ingestion.

## §6 — Acceptance criteria

- **AC.S2.1** — `SELECT count(*) FROM chart_facts WHERE category='kp_cusp'` ≥ 36.
- **AC.S2.2** — `SELECT count(*) FROM chart_facts WHERE category='kp_planet'` ≥ 27.
- **AC.S2.3** — `SELECT count(*) FROM chart_facts WHERE category='kp_significator'` ≥ 9.
- **AC.S2.4** — `SELECT count(*) FROM chart_facts WHERE category='upagraha'` ≥ 5.
- **AC.S2.5** — `build_manifests` entries present.

## §7 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT && \
  test -f platform/scripts/bootstrap/bootstrap_chart_facts_kp.ts && \
  test -f platform/scripts/bootstrap/bootstrap_chart_facts_upagraha.ts && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM chart_facts WHERE category='kp_cusp'" | grep -qE "^\s+[3-9][0-9]+|[1-9][0-9]{2,}" && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM chart_facts WHERE category='upagraha'" | grep -qE "^\s+[5-9]|[1-9][0-9]+"
```

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V33_S2_CLOSE.md`. Body: row counts per category, sample row spot-check.

---

*End of CLAUDECODE_BRIEF_MCPT_V33_S2_v1_0.md.*
