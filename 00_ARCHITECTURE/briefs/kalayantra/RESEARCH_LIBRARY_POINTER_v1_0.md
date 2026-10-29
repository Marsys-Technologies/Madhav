---
artifact: RESEARCH_LIBRARY_POINTER_v1_0.md
version: "1.0"
status: ACTIVE
authority: owner, 2026-10-29 ("save it in the appropriate place right now in your project root")
recorded_on: 2026-10-29
changelog:
  - "1.0 (2026-10-29): records where the Rule Book research library lives, what it holds, and how it must be handled."
---

# KĀLA-YANTRA — research library and Rule Book v1 (pointer)

The project has a permanent, organised research library for the doctrine-built Rule Book. **It is kept outside this repository on purpose.** This file says where it is and how to use it. It holds no book text, chart data or life-event data.

## Where

`/Users/Dev/Archives/madhav-research-library/` on the owner's Mac (owner-only folder, about 3 GB). Start at its `README.md`. The library is refreshed by `00_bin/sync_library.sh`; `00_bin/LAST_SYNC.txt` shows when it was last refreshed.

## What it holds

| Section | Contents |
|---|---|
| `01_decisions` | Snapshot of the KĀLA-YANTRA surrogate decision ledger |
| `02_plans` | Rule Book programme, engine plans v0.1–v0.2, `STRUCTURED_APPROACH_v0_1.md` (current plan, Stage 1 awaiting owner approval) |
| `03_reviews` | Outside model reviews (Fable, Grok, Argon, Astra) with the exact briefs |
| `04_audits` | Doctrine inventory; Jupiter–Saturn and Sade Sati provenance audits |
| `07_doctrine_library` | Curated verse/passage bank from the 16-text library (topic-tagged, verse vs commentary, chapter concordance, packs); free Sanskrit texts (13 works); scanned-text OCR |
| `08_panel_harness` | Panel runners, citation verifier, Rule Card format, planted-error set |
| `09_rule_book` | **Rule Book v1, sealed 2026-10-28: 229 rules**, `RULEBOOK_V1_FINAL_CARDS.json` (sha256 `58d15ba811a9533aeab03f4699372cee5957cae42b52785ddbef09aa7b67df0c`), closure note `RULEBOOK_V1_CLOSURE.md`, per-wave records |
| `10_engine` | Engine preparation checks (data coverage; testable-rule census) |

Rule Book v1 facts: 84 rules free of rival versions; 145 in 39 variant-conflict groups (unresolved); planted-error catch 222/225 across all waves. No admissible rules for: parent bereavement, other parent events, spiritual renunciation, relationship beginning.

## Handling rules

1. **Never copy the library, or any part of `07_doctrine_library`, into this repository, a PR, a chat log or a cloud service.** It contains text from purchased editions. Rule Cards from those editions carry fingerprints (sha256), not quotes.
2. The owner's life events are not in the library and must not be added.
3. The library is the only copy of some material (its scratch sources were cleaned). Until an off-Mac backup exists, do not delete or move it.
4. Code that consumes the Rule Book lives in this repository via reviewed PRs (rule-card compiler, L0 rule-book store); the card data itself is loaded from the library at an owner-session compile.
