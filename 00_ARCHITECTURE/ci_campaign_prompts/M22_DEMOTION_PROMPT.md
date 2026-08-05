# Claude Code task — measure, then demote the ~104 unearned `two_pass_verified` sites (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after any queue
ejection — a consumed arm looks like "off"). Standing rules `CI_EFFICIENCY_AUDIT_v1_0.md §6`, all
nine plus the §6.16 sibling: **neither a detector's description nor a baseline adjudication note is
evidence about the code — read the emit site.** Assume this brief has a flaw; record it.

Context: §6.16 found ~104 of 114 `two_pass_verified` emit sites carry the status with no comparison
behind it. Abhisek has accepted the recommendation to **demote to `single`** (F-11 precedent, DVA
Ruling 13), **gated on a measurement stage**. This brief is that two-stage execution. Do the stages
in order; the gate between them is real.

---

## Stage 1 — MEASURE the serve-layer blast radius (no writer changes in this stage)

1. **Enumerate every consumer of `verification_pass_status`** outside the writers: serve layer,
   MCP tools, prompt/synthesis/narration code, SQL views, exporters
   (`platform/src/`, `platform-mcp/src/`, sidecar routers/services, migrations/views). For each:
   does it **filter**, **weight/rank**, **display**, or merely **carry** the field? Quote the line.
2. **Quantify the row delta**: against the live DB (via the existing `PROD_DATABASE_URL` +
   cloud-sql-proxy pattern, read-only queries only), count chart_facts rows per
   (fact_category, chart) whose status would change `two_pass_verified → single` under the
   demotion. Total, and per category.
3. **Derive the output delta**: combining 1+2, state concretely what changes in a served reading —
   which tools' responses, which narration paths, any counts/grades the serve layer computes from
   the field. If a consumer filters on `two_pass_verified`, name the facts that would drop out.
4. **Re-audit the 104 while you're at each site** (rule 9-sibling: don't trust §6.16's count
   either): classify every site — (a) genuinely has an engine-vs-derived comparison → convert to
   `two_pass_verdict(...)` from `brahmagyan/verification_vocab.py`, no demotion; (b) no comparison,
   plain upstream value → demote to `single`; (c) known approximation/fabricated formula → the
   honest tier is `documented_approximation`, not `single`. Report the (a)/(b)/(c) split with
   file:line.

**The gate:** deliver Stage 1 as a report to Abhisek.
- **If (and only if) Stage 1 finds ZERO consumers that filter/weight/display the field** — it is
  carried but never acted on — the demotion has no product-visible effect and **Stage 2 is
  pre-authorized: proceed immediately.** State this finding explicitly with the evidence.
- **If any consumer filters, weights, or displays it: STOP after Stage 1.** Abhisek reads the
  measured delta and gives the go before Stage 2. Do not proceed on projected impact, however
  small it looks.

## Stage 2 — DEMOTE (only per the gate above)

- Execute the (a)/(b)/(c) classification: helper conversions for (a); tier demotions for (b)/(c).
  One PR per writer file or coherent group; queue merges.
- **Every row-tier change listed in the PR body** per file: site, old→new tier, and the (b)/(c)
  rationale line. These are data-honesty changes; none silent.
- Cite F-11 / DVA Ruling 13 and §6.16 in each PR description.
- **Regenerate/backfill semantics:** determine how chart_facts rows pick up new statuses — next
  scheduled rebuild vs. an explicit backfill. Do NOT run destructive rebuilds; if a backfill script
  is needed, write it, test it against one chart, and hand the production invocation to Abhisek
  unless an existing sanctioned rebuild path covers it. Live-DB writes follow the same discipline
  as the D-1.6 era: honest states, never fabricated ones.
- **Complete the drain as you go:** delete each file's `tap6_baseline.json` entries when its sites
  are converted/demoted; TAP-6 must show 0 NEW and a strictly decreasing entry count after every
  PR. Mutation-check once per file that a bare literal still fails (rule 4: confirm the probe is
  scanned).
- End state: baseline entries = genuine open defects only, ideally **zero**; every
  `two_pass_verified` in the estate is produced by `two_pass_verdict(...)` or lives in the
  sanctioned vocab module.

## Invariants across both stages
- TAP-6 stays green on `main` throughout; never a drain PR in flight when the 2026-08-08 arming
  check runs (arming remains conditionally pre-authorized: ≥7 consecutive green days read from run
  history, then add the check to ruleset 20141220; rollback = remove it).
- No invented verification. No baselining of correct code. Secrets: names only, never values
  (`TAP_MCP_SERVER_URL`, `TAP_MCP_SMOKE_BEARER_TOKEN`, `TAP7_API_BASE_URL` remain owner-set; not
  this task's scope).
- Read-only against production except a sanctioned, tested backfill explicitly handed over or
  approved.

## Deliverable
Prose. Stage 1: the consumer table (file:line, filter/weight/display/carry), row delta per
category, the concrete output delta, the (a)/(b)/(c) split, and which gate branch applied. If
Stage 2 ran: PRs landed, tier changes listed, TAP-6 counts before/after, baseline entries
remaining, backfill status. End plainly: **does `verification_pass_status` now tell the truth at
every emit site — yes or no — and what, if anything, still needs a human.**
