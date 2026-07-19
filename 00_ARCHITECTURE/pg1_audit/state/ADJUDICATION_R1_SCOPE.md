---
artifact: ADJUDICATION_R1_SCOPE
wave: PG-1 (Paripraśna Grounding Audit)
lane: R-1
adjudicator_seat: Opus (engineering)
charge: ADJUDICATOR_CHARGE_v1_0.md (v1.1)
authored_by: Opus Adjudicator (engineering seat), 2026-07-19
routes_from: PG-1 Phase-1 verifier REJECT of Lane R-1 on scope-warden grounds
status: RULED
---

# Adjudication — R-1 Scope-Warden REJECT (commit `9216bc84`)

## The decision routed to me

The PG-1 Phase-1 verifier REJECTED Lane R-1 with `scope_warden: fail`, on the
ground that commit `9216bc84` ("chore(pg1/R-1)") touches **four** files across
**two** lanes — R-1's own two designated files (`pg1_findings_R-1.jsonl`,
`PG1_LANE_R-1.md`) **and** D-3's two designated files (`pg1_findings_D-3.jsonl`,
`PG1_LANE_D-3.md`) — in one atomic commit. Per CONDUCTOR_PROTOCOL §3(d):
"`git diff --stat` touches only the lane's `may_touch` globs — any stray path is
an automatic REJECTION regardless of code quality."

The question I must rule on: **is scope-warden a per-COMMIT mechanical check or a
per-LANE-CONTENT integrity check** — and, given the answer, what is the root cause
here and the prescribed fix.

## Independent verification I performed (§1.7 / §2 — reproduction, not report-reading)

1. `git show --stat 9216bc84` — confirmed 4 files, `4 files changed, 204
   insertions(+)`, **zero deletions**. Purely additive.
2. `git show 9216bc84 --numstat` — the four files split cleanly along lane lines:
   R-1's `.jsonl` (+11) and `.md` (+106); D-3's `.jsonl` (+4) and `.md` (+83).
   No file is co-authored across lanes.
3. Read **both** jsonl files and **both** lane `.md` files as they exist in the
   commit:
   - `pg1_findings_R-1.jsonl` (11 findings PG1-R1-0001..0011) is entirely
     R-1-domain content: live MCP tool-surface inventory, the 113 (CAPABILITY_
     MANIFEST doc-catalog) vs 119 (platform registry URIs) vs 139 (live MCP tool
     names) reconciliation, and verdicts on assumptions A1/A3/A4/A5/A6/A9/A10.
     `lane` field on every row = `"R-1"`.
   - `PG1_LANE_R-1.md` frontmatter `lane: R-1`; scope section describes the MCP
     capability-inventory charge; explicitly states it wrote "only to
     `pg1_findings_R-1.jsonl` and this state file."
   - `pg1_findings_D-3.jsonl` (4 findings PG1-D3-0001..0004) is entirely D-3-domain
     content: prediction-ledger table existence, `mimamsa_predictions`/`phala_anchors`
     row counts, the two-disjoint-ledger defect, and the critical §7.4 NO-LEAKAGE
     `pg_roles` finding. `lane` field on every row = `"D-3"`.
   - `PG1_LANE_D-3.md` frontmatter `lane: D-3`; scope section is the DB/role audit.

**Conclusion of verification:** R-1's content touches ONLY R-1's two designated
files; D-3's content touches ONLY D-3's two designated files. Neither lane wrote
a single byte into the other's files. This is a **commit-boundary artifact**, not
a **content scope violation**. Root cause: the wave ran all lanes in a SHARED
working tree rather than isolated git worktrees (a conductor-level deviation from
CONDUCTOR_PROTOCOL's implementer role row — "Builds in an isolated worktree" — and
§4 worktree discipline), so two parallel lane agents' `git commit` calls raced and
git combined their staged files into one commit object.

## Ruling

### On the interpretive question (per-commit vs per-lane-content)

**Scope-warden is, by design, a per-LANE-CONTENT integrity check — mechanically
IMPLEMENTED as a per-commit `git diff --stat`.** The rule exists to catch a lane's
*work* reaching into a path it must not write. CONDUCTOR_PROTOCOL's own framing
proves this is the intent: the named structural fix for the whole class is
"tool-access restriction ... should not be granted `Write`/`Edit` access to any
path outside" its globs (§1.1), and the rule is stated in terms of "a lane
implementer touching a path outside its `may_touch`." The concern is *authorship*,
not *commit topology*. `git diff --stat` is merely the cheap mechanical proxy the
protocol chose for "what did this lane write" — a proxy that holds **only when the
commit boundary and the lane-content boundary coincide**, which is exactly the
invariant the isolated-worktree discipline is there to guarantee.

Here that invariant was broken upstream (shared worktree), so the per-commit proxy
diverged from the per-content truth it stands in for and produced a **false
positive** relative to the rule's intent.

### On the verdict (§1.7 — I may not convert a REJECT to an ACCEPT)

Per ADJUDICATOR_CHARGE §1.7 / §2, I **do not** overturn the verifier's REJECT, and
I have no authority to flip R-1 to ACCEPT. The verifier applied the mechanical
`git diff --stat` check correctly against commit `9216bc84`; on the letter of the
mechanical proxy, the REJECT is not wrong. What I rule is on **root cause and the
fix for the next attempt**: the REJECT reflects a **commit-hygiene defect, not a
content scope violation** — R-1's audit content is clean and (per the verifier's
own diagnosis) independently reproduced and accurate.

### Prescribed fix (for the next verification attempt)

Purely a commit-hygiene repair; **zero content change**:

- The conductor re-commits so that the commit boundary aligns with the lane-content
  boundary — i.e. **R-1's two files (`pg1_findings_R-1.jsonl`, `PG1_LANE_R-1.md`)
  land in their own dedicated `chore(pg1/R-1)` commit that touches ONLY those two
  paths**, and D-3's two files in their own dedicated `chore(pg1/D-3)` commit.
  Concretely: split `9216bc84` into two per-lane commits (e.g. soft-reset the
  combined commit and re-commit each lane's two files separately), preserving the
  identical file contents already verified above.
- Then re-run the Phase-1 scope-warden on R-1's dedicated commit. Because the four
  files are already additive-only and cleanly separable by lane (verified via
  `--numstat`), the split is guaranteed to yield a `git diff --stat` that touches
  exactly R-1's two `may_touch` paths — scope-warden then passes on the content
  that was already accepted on the merits.

Note: D-3 was already dispositioned ACCEPT by the verifier with the commit-provenance
anomaly flagged for the close report; the split also gives D-3 a clean dedicated
commit, closing that flagged anomaly symmetrically.

### Attempt-counter ruling (my call, with reasoning)

**This re-commit-and-re-verify does NOT burn one of R-1's 3 verification attempts.**
Reasoning: the 3-attempt counter (§2.3) bounds how many times a lane may re-submit
**corrected substantive content** after a content rejection — it is a guard against
unbounded re-work of the *audit itself*. R-1's audit content required **no
correction**; it was already independently reproduced and confirmed accurate by the
verifier. The defect being repaired is a conductor-level process deviation (shared
worktree causing a commit race) over which the R-1 lane agent had no control, and
the repair changes not one byte of R-1's deliverables. Charging an attempt would
penalize the lane for the conductor's worktree deviation and would misuse the
counter as a process-hygiene tax rather than a re-work bound. Therefore the
mechanical re-commit is **attempt-neutral**: it is the same accepted content
re-presented under a correct commit boundary, not a second attempt at the work.
(Had the REJECT been for a genuine content defect — cross-lane contamination or a
write into a forbidden path — a corrected re-submission WOULD burn an attempt.)

## Falsifier (what would change this ruling)

- **On root cause / content-cleanliness:** if inspection showed R-1's designated
  files actually contained D-3-relevant material (or vice versa), i.e. genuine
  cross-lane content contamination — or if either lane's files contained an edit to
  a truly forbidden path (`platform/src/**`, `platform-mcp/src/**`, migrations,
  infra, workflows, `CLAUDE.md`, or another wave's brief) — then this would be a
  **substantive** content scope violation, the REJECT would stand on the merits, and
  a corrected re-submission **would** burn an attempt. (Verified NOT the case: all
  four files are lane-pure and confined to `00_ARCHITECTURE/pg1_audit/**`.)
- **On the fix / attempt-neutrality:** if the four files could not be cleanly
  isolated into per-lane commits without a content edit (e.g. genuinely entangled
  hunks), the "zero content change" premise would fail and the split would itself
  become a content operation requiring fresh verification — changing both the
  prescribed mechanism and the attempt-neutral call. (Verified NOT the case:
  `--numstat` shows four whole, additive, separable files.)

---
*Ruling authority: ADJUDICATOR_CHARGE §1.7 (never REJECT→ACCEPT; may authorize the
next attempt) + §2 (record decision, rule/reason, evidence, falsifier). I did not
adjudicate any PARK-class item or the scientific-integrity gate (§4). I did not
modify any lane's files or VERIFICATION_RECEIPTS.md — the conductor reconciles.*
