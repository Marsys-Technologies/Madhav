# Claude Code task — close the TAP-6 blind spot, then re-census (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after a queue
ejection — a consumed arm reads as "off"). Standing rules `CI_EFFICIENCY_AUDIT_v1_0.md §6`, all
nine plus the §6.16 sibling: **neither a detector's description nor a baseline note is evidence
about the code.** Assume this brief has a flaw; record it rather than working around it.

**Scope discipline — this task changes NO writer emit site, NO row, NO tier.** It fixes a detector
and produces a number. The demotion decision is Abhisek's and is explicitly out of scope. If you
find yourself editing a writer's `verification_pass_status`, stop — that's the next task, not this
one.

## Why

Stage 1 measured that `ga_dashas_writer.py` passes the literal **positionally** —
`None, None, "two_pass_verified", ref, human,` — invisible to TAP-6's
`/(=|:)\s*['"]two_pass_verified['"]/` and to §6.16's census. It feeds `chart_dashas`:
**1,358,993** two-pass rows, 4× the entire `chart_facts` population. So **a green TAP-6 is not
evidence the estate is clean**, and §6.16's "104 sites" is a floor, not a count.

Consequence already recorded: **TAP-6 arming is BLOCKED** until this lands — arming a detector with
a known blind spot manufactures the exact false confidence this campaign exists to remove. The
7-consecutive-green-days condition remains necessary but is no longer sufficient.

## Step 1 — Characterise the blind spot before widening the net

Do not just broaden the regex and re-run. First establish, with evidence, **every syntactic form**
in which a verification-status literal reaches an emit site across `platform/python-sidecar`
(and `.ts` — the scanner walks `.py` + `.ts`). Known forms so far: keyword/dict assignment
(`=` / `:`, currently caught) and bare positional argument (missed). Look for at least:
- positional args in calls and tuple/list literals;
- default parameter values (`def _make_row(..., verif="two_pass_verified")`) — note the baseline
  already quarantines shared-default declarations, so confirm how these are currently classified;
- dict/tuple construction without a colon adjacency (e.g. built then `.append(...)`);
- f-string / concatenation / `.format()` construction, and any indirection through a constant or
  alias that is not the sanctioned `brahmagyan/verification_vocab.py`.

Report the taxonomy with file:line examples. **A form you cannot enumerate you cannot claim to
detect** — if some construction defeats static grep entirely (e.g. a value assembled at runtime),
say so explicitly rather than implying full coverage.

## Step 2 — Widen the detector honestly

Amend `platform/scripts/audit/tap/tap6_method_grep.ts`:
- Extend `two_pass_verified_literal` (or add a sibling pattern — your call, justify it) to catch the
  enumerated forms. Keep the sanctioned-module exemption for
  `brahmagyan/verification_vocab.py` exactly as #996 established it.
- **Rewrite the pattern `description` to state precisely what it now measures and what it does
  not** — including any form from Step 1 that remains undetectable. §6.16's lesson is that a
  description claiming more than the regex measures is itself the defect.
- Verify BOTH directions (rule 4, and confirm each probe is in a scanned path):
  (i) a probe in each newly-covered form → exit 1, named;
  (ii) the sanctioned module still exempt → no false positive;
  (iii) removing the exemption → exit 1 naming `verification_vocab.py`.

## Step 3 — Re-census, and make the new hits honest without hiding them

Widening will surface many previously-invisible hits (~28 in `ga_dashas_writer.py` alone, likely
more). **These are not new defects — they are newly visible ones.** Handle them as the ratchet
intends:
- Baseline every newly-surfaced hit with `register_row: "M-22"` and a note that states plainly:
  *surfaced by the 2026-08-01 detector widening; unearned status pending the demotion decision;
  NOT adjudicated as correct.* Do **not** write "NOT A VIOLATION" for anything you have not read
  and verified — that annotation is what misled three prior passes (§6.16).
- Where you *can* cheaply determine earned vs unearned by reading the site, record which in the
  note. Explicitly flag `ga_dashas_writer.py`'s `_verify_vimshottari` case: real verification
  wrapped in `if chart_id == CANONICAL_CHART_ID`, so the native chart earns its status and every
  other chart does not — a per-chart split, not a uniform verdict.
- Result must be TAP-6 **exit 0 with an honest baseline**, not green-by-narrowing. If the only way
  to green is to weaken the pattern, stop and report.

Deliver the **true census**: total emit sites by file and by syntactic form; the earned /
unearned / undetermined split; and the corrected row-count exposure per table (`chart_facts`
352,485 known; `chart_dashas` 1,358,993 known — confirm read-only against the live DB via the
existing `PROD_DATABASE_URL` + cloud-sql-proxy pattern, and check whether `chart_divisionals` or
any other table carries the field too — Stage 1 did not enumerate those).

## Step 4 — Record

Update `CI_EFFICIENCY_AUDIT_v1_0.md §6` with a new subsection: the blind spot, the taxonomy, the
corrected census, and the arming block with its new precondition (positional/all-forms coverage +
clean re-census, **in addition to** ≥7 consecutive green days). Correct §6.16's "104 sites" in
place — do not leave the old number standing beside the new one (the campaign has hit doc-drift
twice; this is the third opportunity).

## Guardrails
- No writer changes, no tier changes, no backfill, no row writes. Read-only against production.
- No "NOT A VIOLATION" annotations without having read the site.
- Do not arm TAP-6 as a required check in this task under any circumstances.
- Branch, PR, queue merges; one line to revert the pattern change.

## Deliverable
Prose. The syntactic taxonomy with examples and any form that defeats static detection; the
detector diff and the three-way verification result; the true census (sites by file/form, earned /
unearned / undetermined, row exposure per table); what §6 now records. End plainly: **is TAP-6 now
able to see every form of this literal that static analysis can reach — yes or no — and what is the
corrected total the demotion decision should be made against.**
