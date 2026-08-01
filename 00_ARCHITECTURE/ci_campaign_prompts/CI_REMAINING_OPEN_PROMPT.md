# Claude Code task — close everything still open after the TAP-6 remediation (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (open PRs; the queue merges; never commit to
`main`). Standing rules: `00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6`, all nine — the ones that
bite here: (2) n=1 isn't a measurement, (4) a mutation proves nothing until it reaches the code
under test, (5) impossible instructions get recorded not worked around, (9) a detector's
description is not evidence about the code. Assume this brief has a flaw; report it.

Precondition: PR #996 merged and `main`'s TAP-6 run green (0 NEW, 111 tracked / 15 entries). Verify
before starting; if #996 hasn't landed, land it first via the queue.

---

## Item 1 — PR-2: drain the TAP-6 baseline (the main work)

Goal: after this, `tap6_baseline.json` means **only** "register-tracked open defects." Today 7 of
15 entries are adjudicated innocents held by hash collision.

Order by the delivered inventory (drain-per-effort):
1. **`ga_structural_writer.py`** — 81 sites, mechanical, drains 5/15 entries.
2. The seven adjudicated "NOT A VIOLATION" entries — pure conversions:
   `ga_sensitive_degree_writer.py` (3), `bo_pramana_mapa.py` (1), `bo_laksana.py` (1), plus the
   correct-as-is defaults noted in `ga_sensitive_writer.py` / `ga_sade_sati_writer.py`.
3. `ga_vargas_writer.py` (18 sites, 1 entry).

Method per file:
- Convert emit sites to the sanctioned vocabulary in **`brahmagyan/verification_vocab.py`**
  (constants for static tiers like `documented_approximation`/`single`; `two_pass_verdict(...)`
  ONLY where a genuine engine-vs-derived comparison exists). **Do not invent verification** — a
  site that today asserts the literal without a comparison converts to the honest lower tier or,
  if it is a real M-22 defect, stays baselined with its register row and gets reported, not
  silently fixed.
- The baseline notes flag known real-defect residue: `ga_sade_sati_writer.py`'s ~9 default-relying
  rows ("full per-call-site audit out of scope" — now it IS the scope: audit them, classify each),
  and `ga_sensitive_writer.py`'s non-fabricated points. Classify: genuinely-computed → helper;
  upstream-joined/no-comparison → honest tier; real defect → keep entry + register row + report.
- Emissions must be byte-identical for identical inputs **except** where a tier honestly changes
  (assertion → `single`/`documented_approximation`); list every such row-tier change in the PR
  body — that's a data-honesty change Abhisek should see, not a silent one.
- Delete each file's baseline entries as it lands (the ratchet), one PR per file or small group.
- After each PR: run TAP-6 — 0 NEW, entry count strictly decreasing. Mutation-check at least once
  per file that the grep still catches a bare literal there (rule 4: confirm the probe is in the
  scanned path).

End state: baseline entries = open register rows only (target: only genuine M-22 residue, ideally
just the `ga_sade_sati`/`ga_sensitive` rows if they prove defective — or zero).

## Item 2 — arming `two_pass_verified_literal` as a required check: CONDITIONALLY PRE-AUTHORIZED

Abhisek has delegated this decision. It is taken, with a condition that is not optional:

- **Condition:** ≥7 consecutive days of green TAP-6 runs on `main` (scheduled + push), verified
  from run history at execution time — not projected. The gate has never been observed green over
  time; requiring a check with zero green history would violate rule 2.
- **When the condition holds:** add the TAP-6 check (the job carrying `two_pass_verified_literal`)
  to ruleset 20141220's required status checks. Name must be byte-exact. One-toggle rollback:
  remove it from the ruleset. Record in §6.
- **If you are running before the condition holds:** do NOT arm. Instead note the green-streak
  start date in §6 and state in your report the earliest arming date. That is a complete outcome,
  not a failure.
- Never arm while Item 1 has a PR in flight that could change TAP-6's result.

## Item 3 — the two owner secrets: verify, don't set

Check whether `MCP_SMOKE_BEARER_TOKEN` and `TAP7_API_BASE_URL` now exist (`gh secret list`; you
handle names, never values).
- If set: dispatch the unblocked job(s) once each; read results at **step level** (rule 1 —
  `continue-on-error` lies at job level); report what genuinely ran, honest-skip vs pass vs fail.
- If not set: restate exactly — `MCP_SMOKE_BEARER_TOKEN` unblocks `mcp_tool_smoke`;
  `TAP7_API_BASE_URL` unquarantines one TAP-7 gate; no code change needed; owner-only. Do not
  create placeholders.

## Item 4 — housekeeping: archive the campaign prompt files (decided: archive, not delete)

The repo root holds ~10 untracked prompt files: `CI_*.md` (8), `TAP6_M22_REMEDIATION_PROMPT.md`,
`CI_REMAINING_OPEN_PROMPT.md` (this one). They are the campaign's direction record and §6
references their reasoning. In a small PR: `git mv` them to
`00_ARCHITECTURE/ci_campaign_prompts/` with a 5-line README naming the campaign, dates, and
pointing to `CI_EFFICIENCY_AUDIT_v1_0.md §6` as the authoritative record. Do not edit their
contents. If any file is absent (Abhisek may have removed some), archive what exists and say so.

---

## Guardrails
- No silent tier changes: every row whose `verification_pass_status` value changes is listed.
- No baselining of correct code; no detector-dodging rewrites.
- Branch per item; queue merges; one line/toggle to revert each change.
- Secrets: names only, never values.

## Deliverable
Prose. Per file drained: sites converted by kind (helper / honest-tier / left-as-defect+register
row), tier changes listed, TAP-6 counts before/after. The arming outcome (armed with evidence, or
earliest date). The secrets status and any step-level run results. The archive PR. End plainly:
**how many baseline entries remain, are all of them genuine tracked defects now — yes or no — and
what is the single next thing, if anything, that needs a human.**
