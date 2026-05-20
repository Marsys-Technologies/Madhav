# BACKFILL_RUN_REPORT

R9-S2 conversation embedding backfill — production run report.

## Outcome: SUCCESS

| Metric | Value |
|---|---|
| Run date | 2026-05-20 |
| Script | `platform/scripts/backfill_conversation_embeddings.ts` |
| Duration | 53 seconds |
| Messages to embed (before) | 73 |
| Embeddings created | 73 |
| Errors | 0 |
| Embeddings AFTER | 73 |
| Remaining un-embedded | 0 |

## Script bug fixed before running

The script had `cm.content` in both SQL queries but the production schema uses `parts_json` (JSONB array of `{type, text}` objects). Fixed to extract first `type:'text'` element via `jsonb_array_elements(cm.parts_json)` — matching the pattern used in both the live semantic search route (`api/conversations/search/route.ts`) and `conversation_writer.ts`.

Also corrected port comment in header from 5432 → 5433 (proxy runs on 5433 per this project's convention).

## Environment

- GCP Project: madhav-astrology
- Instance: madhav-astrology:asia-south1:amjis-postgres
- DB: amjis
- Vertex AI model: text-multilingual-embedding-002 (768 dims)
- Location: asia-south1
- ADC: valid (existing credentials, no login needed)
- Proxy port: 5433

## Quota / backoff events

None. All 73 embeddings completed in a single run at 200ms inter-batch delay, no Vertex quota errors.
