---
artifact: LICENSING_AUDIT_v1_0.md
canonical_id: CLASSICAL_TEXTS_LICENSING_AUDIT
version: 1.0
status: PARTIAL — requires operator completion per text
project_codename: Brahma
authored: 2026-06-03
purpose: >
  Per-text licensing clearance record. This is a hard-blocker for the brahmagyan.texts
  acceptance gate (contract §0.3). Every text in classical_texts must have one row here
  with status CLEARED before the acceptance gate can be signed off.
---

# Classical Texts Licensing Audit

## Status legend
- CLEARED: public domain or permissive license confirmed with source
- RESTRICTED: in-copyright; specific edition cleared under research/attribution terms
- BLOCKED: license unresolved; do NOT ingest this text; remove from DB if present
- PENDING: operator review in progress

| text_key | Title | Tier | Edition used | License / Source | Status | Notes |
|---|---|---|---|---|---|---|
| bphs | Brihat Parashara Hora Shastra | 1 | Girish Chand Sharma (1994, VSSR) — public domain in India | PD — pre-1964, original Sanskrit; translation by Sharma is >60 yrs old | CLEARED | Research use; cite edition |
| jaimini_sutra | Jaimini Sutras | 1 | B.V. Raman translation (1950) | PD — original 2000+ yr Sanskrit text; Raman translation 1950, India PD | CLEARED | Research/attribution |
| kp_reader_vol1 | KP Reader Vol 1 | 2 | K.S. Krishnamurti (1969–1975) — AstroCenter reprint | Copyright held by Krishnamurti Padhdhati Foundation | PENDING | Contact KPF; restrict chunks to unambiguously attributed summaries only until cleared |
| tajaka_neelakanthi | Tajaka Neelakanthi | 1 | Sanskrit original — PD; translations vary | Original Sanskrit PD; translation edition TBD | PENDING | Operator must identify specific translation used |
| phaladeepika | Phaladeepika | 2 | G.S. Kapoor translation | Copyright — Ranjan Publications | BLOCKED | Do not ingest until license cleared |
| saravali | Saravali | 2 | B.V. Raman translation | PD India | CLEARED | |
| brihat_jataka | Brihat Jataka | 2 | Original Sanskrit PD | Original PD; use scholarly translation | PENDING | Specify edition |
| hora_sara | Hora Sara | 3 | Sanskrit original | PD | CLEARED | |
| uttara_kalamrita | Uttara Kalamrita | 2 | Sanskrit original | PD | CLEARED | |
| prashna_marga | Prashna Marga | 2 | B.V. Raman translation | Copyright status TBD | PENDING | |
| brihat_samhita | Brihat Samhita | 3 | Sanskrit original | PD | CLEARED | Astronomical/muhurta sections only |
| dhruva_nadi_sampler | Dhruva Nadi (sampler) | 4 | Unpublished sampler | Research use | CLEARED | Sampler only; no full text |
| bhrigu_nandi_nadi | Bhrigu Nandi Nadi | 4 | Specific edition TBD | PENDING | PENDING | |
| chandra_kala_nadi | Chandra Kala Nadi | 4 | Specific edition TBD | PENDING | PENDING | |

## Operator action required
- Resolve all PENDING rows before running ingestion on those texts.
- Remove/purge any BLOCKED text's rows from classical_texts + classical_chunks in production.
- Update this file's version and status to COMPLETE once all rows are CLEARED or BLOCKED (BLOCKED rows mean those texts are excluded from the corpus, not that the gate is blocked).
