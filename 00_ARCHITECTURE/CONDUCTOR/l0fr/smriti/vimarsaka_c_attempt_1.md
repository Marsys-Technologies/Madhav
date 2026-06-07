---
gate: vimarsaka_c
attempt: 1
sample_size: 50
texts_sampled: [bphs, phaladeepika, jataka_parijata]
checks_total: 250
checks_passed: 242
pass_rate_pct: 96.80
breakdown:
  verse_ref_valid: 50/50
  length_in_range: 48/50
  citation_non_null: 50/50
  starts_properly: 44/50
  sha256_valid: 50/50
failing_chunks:
  - chunk_id: jataka_parijata_ch010_v0179
    text_id: jataka_parijata
    verse_ref: CH10:V179
    failures:
      - "length_out_of_range: 2003 (threshold: 2000)"
      - "bad_start: starts with OCR artifact 'tnfra.' — mid-sentence continuation"
  - chunk_id: bphs_ch077_v0013
    text_id: bphs
    verse_ref: CH77:V13
    failures:
      - "bad_start: 'indifferent or neutral) in tha' — mid-sentence continuation"
  - chunk_id: bphs_ch004_v0007
    text_id: bphs
    verse_ref: CH4:V7
    failures:
      - "bad_start: '— If the Adhana Lagna is a noc' — em-dash continuation fragment"
  - chunk_id: jataka_parijata_ch009_v0045
    text_id: jataka_parijata
    verse_ref: CH9:V45
    failures:
      - "bad_start: 'rrrsjTPt (Gandanta)' — OCR artifact leading chars"
  - chunk_id: bphs_ch041_v0013
    text_id: bphs
    verse_ref: CH41:V13
    failures:
      - "bad_start: 'deserve an answer at all and i' — mid-sentence continuation"
  - chunk_id: bphs_ch078_v0008
    text_id: bphs
    verse_ref: CH78:V8
    failures:
      - "bad_start: 'ire timid at one time and cour' — mid-sentence continuation"
  - chunk_id: jataka_parijata_ch010_v0097
    text_id: jataka_parijata
    verse_ref: CH10:V97
    failures:
      - "length_out_of_range: 2011 (threshold: 2000)"
decision: APPROVE
reasoning: >
  Structural-only review per deterministic-first principle (no LLM semantic scoring).
  50 random chunks sampled across bphs (1723 total), phaladeepika (179 total), jataka_parijata
  (741 total). 250 structural checks executed (5 per chunk). 242/250 passed = 96.80% pass
  rate, comfortably above the 85% APPROVE threshold.

  All 50 chunks passed verse_ref_valid (pattern CH\d+:\d+ or CH\d+ confirmed) and
  citation_non_null and sha256_valid. 48/50 passed length_in_range — 2 Jataka Parijata
  chunks marginally exceed the 2000-char ceiling (2003 and 2011 chars) due to multi-verse
  spans. 44/50 passed starts_properly — 6 chunks begin mid-sentence, consistent with the
  OCR-sourced text and multi-verse chunking strategy noted in stream_C_phase1_complete.md.

  Failure pattern is non-systemic: mid-sentence starts are a known OCR artefact from
  djvu/plain-text extraction (noted in Phase 1 report: "parked quality" chunks). The 3.2%
  failure rate does not indicate a systematic chunker defect.

  Stream C may proceed to texts 4-15. Stream D is unblocked.
next_action: >
  Update state.yaml: streams.C.status = midway_approved; gates.vimarsaka_c.status = midway_pass.
  Unblock Stream D. Stream C continues to Phase 2 (texts 4-15).
  Non-blocking feedback for Stream C: consider a post-ingestion trim pass for mid-sentence
  chunk starts and overlong chunks (>2000 chars) — but these do NOT block Phase 2 ingestion.
authored_by: Vimarśaka-C (autonomous)
authored_at: "2026-06-07"
---
