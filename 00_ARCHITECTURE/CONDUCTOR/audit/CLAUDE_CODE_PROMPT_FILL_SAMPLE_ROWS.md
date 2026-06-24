---
artifact: CLAUDE_CODE_PROMPT_FILL_SAMPLE_ROWS.md
canonical_id: CLAUDE_CODE_PROMPT_FILL_SAMPLE_ROWS
version: 1.0
status: READY — fills the 2 real sample rows per asset into PLAIN_LANGUAGE_INSTRUMENT_MAP. Read-only DB. NO SEAL.
authored_by: Cowork 2026-06-22
companion_to: PLAIN_LANGUAGE_INSTRUMENT_MAP_v1_0.md
---

# Claude Code Prompt — Fill the Real Sample Rows

> Paste §PROMPT to Claude Code in Antigravity. It queries the live DB for 2 REAL representative rows per
> asset and fills the [SAMPLE] placeholders in PLAIN_LANGUAGE_INSTRUMENT_MAP. Read-only; no fixes, no seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Fill the real sample rows in
`00_ARCHITECTURE/PLAIN_LANGUAGE_INSTRUMENT_MAP.md`. For EACH asset listed there (L0–L4, ~69 assets), it has
two `[SAMPLE — to be filled]` placeholders. Replace them with 2 REAL representative rows from the live DB
for the native chart `482012f1-710e-4a25-994a-93821f5871aa`. **Read-only — query only, change no data, fix
no bug, seal nothing.**

**Rails:** read-only DB via the Cloud SQL proxy; this is a presentation task, not an audit — but if you
happen to notice an obvious anomaly while sampling (e.g. a column that's all one value), note it in a
"NOTICED WHILE SAMPLING" appendix — do NOT act on it. Gemini/DeepSeek if any summarization needed.

**For each asset:**
1. Find its `target_table` + `count_sql` from `platform/scripts/seed/asset_registry_seed.ts` (or the
   registry API). That's the table to sample.
2. Pull 2 rows that are REPRESENTATIVE + HUMAN-LEGIBLE for the native:
   - Prefer rows that best ILLUSTRATE what the asset does (the strongest/clearest signal, a recognizable
     example) — not the first 2 by id. If the asset has categories, pick 2 DIFFERENT categories so the two
     samples show range, not duplication.
   - For global/reference assets (L0 bg_* with no chart_id), pull 2 representative reference rows.
   - For service assets with no persisted table (e.g. ka_gochara/bg_*_engine), instead show 2 example
     OUTPUTS of calling the service for the native (a sample of what it returns), labelled "service output".
3. **Render each sample row in PLAIN, HUMAN-READABLE form** — not raw JSON dumps. Translate the key columns
   into a short readable line a non-technical person understands. Example for ga_positions:
   `Sample 1: Sun — in Capricorn, 9th house, 22°14′ (its own measured natal position)` rather than a raw
   tuple. Keep it to the few columns that convey what the asset produces; drop internal ids/timestamps
   unless they're the point. If a JSONB column holds the meaning, summarize its key fields in words.
4. Replace the asset's two `[SAMPLE]` placeholders with these 2 readable lines. Keep everything else in the
   file (the descriptions, structure) EXACTLY as-is — you are only filling placeholders.

**Coverage:** every asset in the map must end with 2 real samples. If an asset's table is EMPTY for the
native (e.g. ga_prashna = 0 rows, correctly), write `Sample: (no rows — [reason, e.g. horary-only, not
applicable to a birth-chart native])` instead of inventing data. If a table is empty because of a known
bug (ph_pratikara/ph_sankrama pending the convergence fix; ka_sangam pre-fix), note `(currently affected
by the in-flight convergence fix — sample pending rebuild)`.

**Output:** the updated PLAIN_LANGUAGE_INSTRUMENT_MAP.md with all [SAMPLE] placeholders filled with real,
human-readable rows; flip its frontmatter `status` to `CURRENT`. Plus a short report: which assets had
empty/NA samples + why, and any "NOTICED WHILE SAMPLING" anomalies (noted, not acted on). Do NOT seal.

---
*End. Fill 2 real, human-readable representative rows per asset from the live DB into the plain-language
map. Read-only, presentation-only, no fixes, no seal. Empty tables get an honest "(no rows — reason)".*
