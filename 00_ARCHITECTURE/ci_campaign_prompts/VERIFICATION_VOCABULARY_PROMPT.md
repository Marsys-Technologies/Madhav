# Claude Code task — settle the verification tier vocabulary, then drain the data residue (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after a queue
ejection — a consumed arm reads as "off"). Standing rules `CI_EFFICIENCY_AUDIT_v1_0.md §6`, all
nine plus the §6.16 sibling. Assume this brief has a flaw; record it rather than working around it.

**Scope boundary — this task does NOT demote the 392,001 unearned rows.** That decision is
Abhisek's and is still open. This task makes the vocabulary coherent so the demotion, if approved,
lands somewhere readable. If you find yourself changing an unearned site's tier, stop.

## Why this is first

Landing 392k demoted rows onto today's vocabulary would make it less legible, not more. Measured
state of `chart_facts`:
- `single_pass` (32,614) **and** `single` (6,611) coexist as distinct strings for what is plausibly
  one concept.
- **`PASS` (5,428) survives from F-11** — the writer was fixed 2026-07-30, the data was never
  drained. Third instance in this campaign of *fix the code, leave the data lying*.
- `documented_approximation` (970) in live use.
- `chart_facts` has **no live CHECK** (migration-134's is archived, not on the running DB).
- `chart_dashas` / `chart_divisionals` **do** have CHECKs allowing only
  `{two_pass_verified, classical_match, divergent_flagged, single}` — `documented_approximation`
  would be **rejected** there.

## Step 1 — Establish ground truth (read-only, before proposing anything)

Against the live DB via the existing `PROD_DATABASE_URL` + cloud-sql-proxy pattern, **read-only**:
1. **Every distinct value** of `verification_pass_status`, with row counts, **per table** — not just
   `chart_facts`. Enumerate which tables carry the column at all (Stage 1 only checked some;
   `chart_divisionals` surfaced late).
2. **Every live CHECK constraint** on the column, per table, quoted from the running DB (not from
   migration files — the archived-134 discrepancy proves those disagree).
3. **Every producer**: which writer emits which value into which table (the widened TAP-6 census
   from #1012 is your starting list, not your final one).
4. **Every consumer** and how it treats each value — extend Stage 1's table
   (`envelope.ts:1617-21`, `:72-75`, `:819-24`, `register_p1_ganita.ts:715,1098`,
   `generated/envelope.ts:1611`, `209_ga5_..._mv.sql:144`, `bo_pramana_mapa.py:144,149`,
   `gates.py:151`). Critically: **what does each consumer do with a value it does not recognise?**
   Count it as unverified, crash, or ignore? That determines whether adding a tier is safe.

Report this as a matrix before proposing a vocabulary. If (1) or (2) contradicts anything above,
say so — the numbers in this brief are Stage-1 measurements and may have moved.

## Step 2 — Propose the vocabulary (proposal only; Abhisek approves before Step 3)

Design the smallest coherent set. The known requirement, from the underclaim risk:

> A deterministic, single-pass computation (e.g. an ephemeris-derived position never independently
> re-derived) is **epistemically different** from an unverified candidate or an approximation.
> Today's ladder is binary — `two_pass_verified|pass` counts as verified, everything else reads as
> "not confirmations". Demoting 392k deterministic facts into that bucket would trade an overclaim
> for an **underclaim**.

So the proposal must say, for each tier: its exact string, what claim it makes, what evidence
justifies it, and which producer sets it. Cover at minimum: cross-verified by independent
re-derivation; deterministic single-pass computation; documented approximation; divergent/flagged;
unverified. **Reuse existing strings wherever they already mean the right thing** — a new
synonym is the disease, not the cure (`verification_vocab.py` exists because this field once had
six definitions).

Then state the migration cost honestly:
- Which tiers require a **CHECK constraint migration** on which tables (`chart_dashas` /
  `chart_divisionals` are constrained; `chart_facts` is not — decide whether it *should* be, and
  say why).
- What the **grade ladder** (`envelope.ts:72-75`) and the **warranty sentence**
  (`envelope.ts:819-24`) should say about each tier, in the sentence's actual voice. A
  deterministic-single-pass fact should not be described to a user as "not a confirmation"; write
  the replacement wording. Include the codegen mirror (`generated/envelope.ts`) and remember
  `codegen:check` enforces parity.
- Whether `209_ga5_..._mv.sql:144`'s `MIN()` aggregate still behaves sensibly under the new
  vocabulary — alphabetic `MIN` over a changed value set may silently reorder.

**STOP after Step 2. Deliver the proposal and wait.** This changes what the product claims about
its own facts; it is not an executor's call.

## Step 3 — Execute (only after Abhisek approves the vocabulary)

Order matters:
1. **Constants + producers**: the approved strings live in `brahmagyan/verification_vocab.py`
   (the single source of truth, per #996). Writers reference constants, never literals.
2. **CHECK migrations** where required, before any data movement that would violate them.
3. **Serve layer**: grade ladder + warranty wording + codegen mirror, together, so the displayed
   claim never disagrees with the stored value. Verify `codegen:check` passes.
4. **Data drain** — the part F-11 skipped. Normalise `PASS` → its approved equivalent, and reconcile
   `single_pass` vs `single`. Write the backfill, **test it against one chart**, show the
   before/after counts, and hand the production invocation to Abhisek unless an existing sanctioned
   rebuild path covers it. No destructive rebuilds. Honest states only.
5. Re-run TAP-6 (0 NEW, entries not increased) and confirm no consumer regressed.

## Guardrails
- The 392,001 unearned rows keep their current tier in this task. Vocabulary only.
- No new synonym for an existing meaning.
- Read-only against production except a tested, approved/handed-over backfill.
- Secrets: names only (`TAP_MCP_SERVER_URL`, `TAP_MCP_SMOKE_BEARER_TOKEN`, `TAP7_API_BASE_URL`
  remain unset and out of scope).
- Do not arm TAP-6 as a required check (needs ≥7 green days; earliest 2026-08-08).

## Deliverable
Prose. Step 1's matrix (values × tables × counts, live CHECKs quoted, producers, consumers +
unknown-value behaviour). Step 2's proposed vocabulary with per-tier claim/evidence/producer, the
migration cost, and the **rewritten warranty sentence wording**. If Step 3 ran: what landed, the
backfill's tested before/after counts, and TAP-6 after. End plainly: **is `verification_pass_status`
now a coherent vocabulary with no orphaned values in the data — yes or no — and is the estate ready
for the demotion decision to be executed against it.**
