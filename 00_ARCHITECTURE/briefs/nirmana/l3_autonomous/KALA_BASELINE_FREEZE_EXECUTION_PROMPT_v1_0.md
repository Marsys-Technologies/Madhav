---
artifact: KALA_BASELINE_FREEZE_EXECUTION_PROMPT
canonical_id: KALA_BASELINE_FREEZE_EXECUTION_PROMPT
version: "1.0"
status: AUTHORIZED
date: 2026-09-24
authorized_by: "Native, 2026-09-24, verbatim: 'For the residual other than point two, I will go with your recommendation, whatever you suggest.' — recommendation E1 of KALA_BLUEPRINT_REVIEW_v1_0.md, decided as KALA_DELEGATED_DECISIONS D-J"
scope: "Freeze KALA_BASELINE_v1_0.md. Read-only against serving. No code, no migration, no build."
---

# BASELINE FREEZE SESSION — execution prompt

Paste everything below the line into a fresh Claude Code session.

---

You are the **baseline freeze session**. You produce one artifact, `KALA_BASELINE_v1_0.md`, and you
change nothing else. You are not an L3 stream and you write no code.

## 0. First action

```
git worktree add /Users/Dev/madhav-l3/baseline -b l3/baseline-freeze origin/main
cd /Users/Dev/madhav-l3/baseline
git rev-parse --show-toplevel && git rev-parse --abbrev-ref HEAD
```
Print both. If the toplevel is not `/Users/Dev/madhav-l3/baseline` or the branch is not
`l3/baseline-freeze`, stop and report. Re-assert before every commit. Never enter any other
worktree under `/Users/Dev/madhav-l3/` or `/Users/Dev/madhav-l0/`.

## 1. Read first (all paths from repo root, verified to resolve)

- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` — the thirteen consumer questions L3-Q01–Q13.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ELEVATION_BLUEPRINT_v1_0.md` §1 and §8.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_BLUEPRINT_REVIEW_v1_0.md` §3 M1 and §4 E1.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ACCEPTANCE_RECORD_CONTRACT_v1_0.md` — what
  your artifact will later be compared against.

## 2. What you produce

`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_BASELINE_v1_0.md`, status `FROZEN`, containing:

1. **The thirteen questions**, verbatim from their source, each with the exact serving call(s)
   that answer it today (tool name + arguments), the **verbatim response** (trimmed only with an
   explicit `[… N bytes omitted]` marker), and the response's own `coverage`, `qualification` and
   `dissent` fields quoted as served, including when they are empty.
2. **The three proving cases** from Product §14, run the same way.
3. **One ordinary period** — a dated window with no major transit, chosen and justified in the
   artifact, run the same way. This is the control the product's own §9 needs and has never had.
4. For every run: the chart id (`482012f1-710e-4a25-994a-93821f5871aa` unless the question names
   another), the served generation / authority pointer as returned, the timestamp, and the
   `result_hash` the tool emits.
5. A closing section **"What this baseline cannot show"**: every question whose answer was empty,
   errored, or served with a `not built` marker, stated as such. An honest empty is a result.

## 3. Hard rules

- **Read-only.** You call serving tools. You run no writer, apply no migration, open no build.
- **Verbatim over summary.** A paraphrased answer cannot be diffed after the next wave. Quote.
- **Every number carries its instant and its source.** A longitude without its epoch and
  ayanāṃśa method is not a fact (blueprint §11.10–§11.12 in the chronicle).
- **Absence is a served empty, quoted** — never "no result found" in your own words.
- **Assert the post-condition of every edit**, never the exit code. A `str.replace` that matched
  nothing still writes the file.
- **Do not interpret.** If a served answer looks wrong, record it exactly and add one line under
  "What this baseline cannot show." Judging it is the elevation's job, not the baseline's.

## 4. Close

Commit the single artifact, open a PR from `l3/baseline-freeze` to `main`, and name an
independent reviewer who is not the Saṅgam, Kṣetra or Gochara stream. The reviewer's only question
is: *can every quoted response be re-run from what is written here?* If any cannot, the baseline is
not frozen.
