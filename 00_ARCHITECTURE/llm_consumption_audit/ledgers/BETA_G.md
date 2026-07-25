# Lane β.G ledger — Remedies & corpus (EL-51, EL-35, EL-52)

Per charter §10 / M2.10, append-only Native-Proxy ruling log for lane β.G, plus the Verifier-protocol
evidence blocks for each EL id this lane owns.

---

## PROXY-RULED — 2026-07-25 — Worktree/branch setup

**Situation:** This session began in `.worktrees/beta`, which was checked out on
`elev/beta-T-gochara-timing` (lane T's branch), not any lane-G branch — the brief's stated
`elev/beta/G-remedy-corpus` did not exist anywhere (`git branch -a` confirmed). An untracked file,
`platform/scripts/dispatch_elev_beta_t_gochara_resume.py`, was present in the working tree —
leftover lane-T work, outside this lane's file-ownership manifest (`platform/scripts/**` is not
owned by β.G).

**Ruling:** Verified `elev/beta`, `elev/beta-T-gochara-timing`, `origin/elev/beta`, and `main` all
point at the identical commit (`43116c42`) and the working tree was clean before branching — so no
lane-T work existed to lose. Created `elev/beta-G-remedy-corpus` from `elev/beta` in this same
worktree, following the flattened-branch-name convention this stream already established for lanes
D/D2 (`elev/beta-D-writer-integrity`, `elev/beta-D2-saham-bhanga`) to avoid the same `refs/heads/
elev/beta` file/directory git conflict. The stray T-lane script is left untouched, uncommitted, not
staged — commits from this lane will `git add` only files under this lane's explicit ownership
(`platform/python-sidecar/**`, `platform/migrations/**` additive-only, this ledger file), never a
blanket `git add`. PR base will be `elev/beta`, matching precedent. No citation applicable —
engineering/process decision, §10 MAY (merge-order and lock arbitration; ruling on ambiguous
acceptance criteria).

---

## PROXY-RULED — 2026-07-25 — A-5 supersession authorization record

Recorded here for lane-local completeness (canonical record is `~/elev-v2-shared/proxy/beta.md`
"[STREAM-CONDUCTOR] Session-scope autonomy authorization" entry, independently re-checked against
the live file before this lane proceeded): the A-5 "remedy accept-as-dark" supersession is exercised
under charter §10's MAY-list, which names it explicitly by ID
("superseding CURRENT_STATE A-5 (remedy accept-as-dark -> beta.G repair)"), verified directly against
the primary charter text (`ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §10), not taken on trust from any
relayed paraphrase. This is disclosed and provisional (PROXY-RULED, open for morning ratification),
not a claim of native ratification. The hard, non-negotiable constraint carried into this lane's
work: the gemstone contraindication verdict may ship `VERIFIED-CLOSED` only with a real, checkable
citation from this project's own classical-text corpus (`ref_rules_search` / `ref_classical_
citation_get` / `ref_doshas_get`); absent that, the honest disposition is `PARKED-HONEST`, not a
forced close.

---

## G0 live reproduction — 2026-07-25

**`ref_remedies_chart_get(affliction="Venus", top_k=50)`** against the canonical chart returned
`returned_count: 25` — this is almost certainly where the register's "catalog of 25" figure comes
from (a live row count for one affliction keyword), not 25 distinct remedy *classes*. Cross-checked
against `l0_remedy_corpus.py`'s `VALID_REMEDY_TYPES` (12 types: mantra, yantra, gemstone, charity,
vrata, puja, japa, homa, tantric, ayurvedic, vastu, behavioral) and the YAML corpus (10 distinct
`category:` values) — no 25-class enumeration exists anywhere in the codebase. **Correction to the
brief's framing, logged honestly rather than silently implemented against a number that isn't real.**

**More serious finding: `ref_remedies_chart_get` is not actually chart-scoped.** Its tool schema
takes no `chart_id` parameter at all; per source (`platform/src/lib/retrieval/registry/layers/
register_d7_channel.ts:1362-1452`, found via code investigation, NOT edited — outside this lane's
file ownership), it is `scope: 'global'`, a single `WHERE planet ILIKE $1 OR domain ILIKE $1` keyword
match with a flat `ORDER BY confidence DESC, cost_tier ASC LIMIT $2`, no per-class fan-out, no
per-class inclusion/exclusion accounting, and `chart_id` (when passed at all) is documented in-code
as being used for provenance logging only, never for filtering. This is the real EL-51 root cause:
a tool named "chart_get" that silently ignores the chart.

**File-ownership conflict — must be disclosed, not silently worked around.** This lane's ownership is
`platform/python-sidecar/**` + `platform/migrations/**` (additive) + this ledger only.
`register_d7_channel.ts` is under `platform/src/lib/retrieval/registry/**` — explicitly listed as
**never touch** in this lane's brief. **The actual fix for "chart-scoped engine ignores chart_id and
has no per-class accounting" requires a file this lane is not permitted to edit.** This is not a
PARKED-HONEST finding about the astrology (the classical grounding work is going fine) — it's a
scope/ownership finding about the engineering task itself, and it needs a decision from whoever owns
that path, not a unilateral lane-G workaround (e.g. editing outside ownership, which would itself
violate the file-ownership discipline this campaign runs on).

**What IS in-scope and being pursued:** the `bodha_remedies_get` (L2 Bodha) path is genuinely
chart-scoped (SQL keyed on `chart_id`, confirmed live — 9 resonances + 27 prescriptions returned for
the canonical chart, all real rows) and is backed by Python writers under this lane's ownership.
`associated_doshas_array` and `estimated_cost_inr_range_jsonb` are confirmed live-NULL DB-wide (own
live call, matches the code's documented `DATA_GAP_NOTE`) — a `bo_upaya`-writer population gap, which
IS a python-sidecar writer fix, in scope.

**EL-52 named example reproduced live, verbatim.** Row `sweep_venus_japa_1b8a46b9` from the same
`ref_remedies_chart_get` call: `source_citation: "[HIGH] BPHS — Trans. R. Santhanam, Ranjan
Publications (archive.org: BPHSEnglish) | PG581"`, prescription_text:
`".Chapter 47\n3Tr?Ctrqqqad\nEI€TITfEfrffTq I\n589\n...88-8g.SimilararetheeffectsofVenusinhissub.
periods.\nIf Venus belord of the 2nd or the 7th(two maraka houses)' there\nwill'be during his Dasa,
physical pains and troubles' To get\nalleviation from those troubles the native should"` — this is
the exact garbled text named in the register. Assessment: the garbled segment
(`3Tr?Ctrqqqad EI€TITfEfrffTq`, `?6{ler qfilqfa llqqll`, `qr aqrcti qt( |`) is an OCR-mangled attempt
at a Devanagari verse — **not recoverable from this OCR output; flagged low-confidence, not
reconstructed.** The trailing English is legible with only word-boundary loss (a mechanical OCR
defect, not missing/altered characters): `"88-89. Similar are the effects of Venus in his
sub-periods. If Venus be lord of the 2nd or the 7th (two maraka houses), there will be during his
Dasa, physical pains and troubles. To get alleviation from those troubles the native should..."` —
de-spacing this is safe (no characters invented, no words guessed) and it directly corroborates the
maraka rule via a second citation (BPHS Ch.47, PG581) beyond Ch.44.

## Maraka-lordship rule — citation grounding (safety-critical piece)

**Source: BPHS Chapter 44 "Maraka (Killer) Planets"**, `[HIGH]` confidence, Trans. R. Santhanam,
Ranjan Publications, corpus chunks `bphs_pg0439_c01` through `bphs_pg0443_c01` (verified live via
`ref_rules_search(keyword="maraka")`).

Rule as stated in the primary text: "the 3rd and 8th are the two houses of longevity. The houses
related to death are the 12th from each of these, i.e. the 2nd and 7th are Maraka houses... The
lords of the 2nd and the 7th, malefics in the 2nd and the 7th and malefics accompanying the 2nd and
7th lords are all known as Marakas" (`bphs_pg0439_c01`). Strength ordering, same source
(`bphs_pg0440_c02`): primary marakas = lords/occupants of 2nd, 3rd, 7th, 8th, 12th (2nd ranked
strongest); second-grade = lords/occupants of 6th, 11th; least-marakas = lords/occupants of 1st, 4th,
5th, 9th, 10th (can still act as marakas under specific conjunct/aspect conditions per slokas 15-21,
not modeled in this pass — scoped to the primary 2nd/7th-lordship rule only, disclosed as a scope
limit, not silently generalized).

This matches this lane's brief's own stated hypothesis almost exactly ("a maraka is typically the
lord of the 2nd or 7th house from lagna, or a planet closely associated with those lords") and is
independently corroborated by the BPHS Ch.47 passage above (Venus named as maraka specifically via
2nd/7th lordship). **Verdict: real, citable, HIGH-confidence grounding exists. The A-5 "no
fabrication-free repair possible" prior finding does NOT hold for the core 2nd/7th-lordship rule** —
this is the fresh-eyes repair the charter's supersession asked for. Scope note: the fuller rule
(malefic occupants, conjunct/aspecting planets, Rahu/Ketu-as-maraka per `bphs_pg0443_c01`) is
documented above but not yet implemented in code — v1 of the deterministic verdict should implement
the 2nd/7th-lordship core (unambiguous, directly cited) and disclose the occupant/conjunction
extensions as a named follow-up rather than silently baking in an under-verified fuller rule.

## EL-51/EL-35/EL-52 evidence blocks — pending, filled in as work completes below.
