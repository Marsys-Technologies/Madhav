---
artifact: PARIPRASHNA_ID_RECONCILIATION
version: 1.0
status: PROPOSED — read-only forensics + design, produced by lane A6
  (Structural Engineer, Pariprashna Experience Assurance v3 autonomous
  overnight closeout). A6 holds NO tracker write access by charter; every
  `correction_recorded` event below is a proposal for the Native Surrogate
  to review and submit, not an executed action. Nothing in this document has
  been written to the live tracker.
date: 2026-08-29
authoritative_side: claude
role: >
  Forensic census of every finding-id collision/anomaly across the live
  Pariprashna v3 tracker (`/api/projection`, GET-only) and its supporting
  documents, cross-checked against `EDIR_V3_REGISTER_v1_0.md`, the six
  streams' result packets, `rejected_events`, and merged-PR titles on GitHub.
  Proposes the going-forward id convention `S{N}-V3-E-NNN` and gives the
  exact `correction_recorded` events needed to annotate each historical
  collision, with a role-model finding that changes who can submit them.
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/control.py
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/EVENT_SCHEMA_v1_0.json
method:
  tool: "curl -s http://127.0.0.1:8787/api/projection | python3 -m json.tool (GET only, no writes)"
  cross_checks:
    - EDIR_V3_REGISTER_v1_0.md full read (2603 lines)
    - "STREAM_S2_RESULT_PACKET_v1_0.md, STREAM_RESULT_PACKET_S1_v1_0.md, S3_RESULT_PACKET_v1_0.md, S5_LIVE_REPROOF_CHECKPOINT_v1_0.md, S5_CONVERGENCE_HANDOFF_v1_0.md"
    - "tracker rejected_events (154 total; 3 FINDING_ID_CONFLICT)"
    - "tracker/control.py source read (ROLE_EVENTS, correction_recorded validation, projection-apply logic)"
    - "gh pr view 1612 / 1619 / 1646 (merged-PR titles, read-only)"
changelog:
  - "1.0 (2026-08-29): initial forensic census + convention design + correction
    event proposals, lane A6."
---

# Pariprashna V3 — Finding-ID Reconciliation

## 0. Headline finding: the plan to submit as the Native Surrogate will be rejected

Before the collision list: the tracker's own role model (`control.py`
`ROLE_EVENTS`) restricts `correction_recorded` to the **`STREAM_LEAD`** role:

```python
ROLE_EVENTS = {
    "STREAM_LEAD": {..., "correction_recorded"},
    "NATIVE_SURROGATE": {"decision_recorded", "finding_triaged",
                          "remediation_approved", "improvement_parked"},
    ...
}
```

`submit()` enforces this at `control.py:424-426`:
`if event_type not in ROLE_EVENTS.get(role, set()): raise RejectedEvent("ROLE_FORBIDDEN", ...)`.
Role is resolved per-`actor_id` from a pre-provisioned actors table
(`actor_role()`, `control.py:361`), not declared at submission time — a
Surrogate-authenticated request for `event_type: "correction_recorded"` will
be rejected with `ROLE_FORBIDDEN` regardless of payload correctness.

**Practical consequence:** every `correction_recorded` event below must be
submitted under the `actor_id` of the finding's **owning stream's lead**
(`lead-s2`, `lead-s3`, or `lead-s4` as applicable), not under a
`NATIVE_SURROGATE`-role identity. If the Surrogate is the one operating the
submission tooling, this requires either (a) routing the submission through
each stream lead's own credential, or (b) a deliberate, recorded governance
exception before any of these are emitted. I have set `actor_id` on each
proposed event below to the correct stream lead for this reason — do not
resubmit under a surrogate identity expecting it to pass.

A second limitation, also read directly from the projector
(`control.py:1081-1087`): `correction_recorded`'s projection-apply logic
currently does something only when the corrected event was a `work_started`
event carrying a session `ceiling` (`session_id = started_sessions.get(...)`).
For any other corrected event type — including every `finding_discovered`
event this document targets — the event is accepted and durably logged in
the audit trail, but **produces no visible change** in `/api/projection`'s
`findings` array, and is not even surfaced in the dashboard's `decisions`
panel (that panel only renders `decision_recorded` / `remediation_approved`
/ `improvement_parked`, per `control.py:1119`). Emitting the events below
is the correct, honest audit-trail action per the tracker's own
`correction_recorded` design, and per §N.7/§N.8 doctrine (an honest,
evidenced annotation beats no annotation) — but it will **not** rename,
merge, or hide a finding on the live dashboard. If the campaign wants a
finding_id to visibly change, that requires a tracker code change (a new
event type, e.g. `finding_relabeled`, with real projector support) — flagged
as a recommendation in §5, not something this lane implements.

---

## 1. Forensic method

Read-only only, per charter:

1. `GET /api/projection` — full canonical state: 71 `findings`, 20
   `remediations`, 36 `verifications`, 26 `decisions`, 154 `rejected_events`.
2. Every `finding.id` string in the live tracker checked for exact-string
   duplicates → **zero** (the tracker enforces global `finding_id` uniqueness
   at `finding_discovered` time — see §2.4). The "collisions" that exist are
   therefore either (a) already resolved by an ad hoc `S{N}-` prefix adopted
   under duress by S4/S6, or (b) numeric-only collisions across *different*
   strings that a human skimming a table can still misread as the same
   finding, or (c) stale/broken cross-references between the tracker and
   `EDIR_V3_REGISTER_v1_0.md`.
3. Every candidate cross-checked against `EDIR_V3_REGISTER_v1_0.md`'s own
   prose — the register already self-documents several of these collisions
   in detail (it is a genuinely well-kept audit trail); I treat that prose as
   corroborating evidence, not as ground truth on its own, and independently
   verified the tracker-side state and, where possible, the merged PR
   history on GitHub (`gh pr view`, read-only).
4. `rejected_events` filtered for `FINDING_ID_CONFLICT` — 3 hits, giving a
   precise timeline of who collided with whom and when (§2.4).

---

## 2. Findings census and disposition

### 2.1 Full live census (71 findings, 0 raw string collisions)

By stream: S1 (1: `S1-F-001`), S2 (9: `V3-E-013,014,015,021,023,024,030,031`
+ `V3-E-024-fixed`), S3 (5: `V3-E-012,016,032,033` + `S3-V3-E-001`), S4 (44:
`S4-V3-E-012`…`S4-V3-E-055`, self-prefixed throughout), S5 (10:
`V3-E-007,010,011,017,018,019,020,022` + `E-001` + none unprefixed
colliding), S6 (1: `S6-V3-E-003`), P1 (1: `P1-F-004`). Full id/severity/
status table below.

| id | stream | severity | status |
|---|---|---|---|
| P1-F-004 | P1 | HIGH | TRIAGED |
| S1-F-001 | S1 | HIGH | TRIAGED |
| V3-E-012 | S3 | MEDIUM | TRIAGED |
| V3-E-013 | S2 | CRITICAL | OPEN |
| V3-E-014 | S2 | MEDIUM | OPEN |
| V3-E-015 | S2 | MEDIUM | OPEN |
| V3-E-016 | S3 | CRITICAL | TRIAGED |
| V3-E-017…V3-E-020, V3-E-022, E-001, V3-E-007, V3-E-010, V3-E-011 | S5 | mixed | TRIAGED/OPEN |
| V3-E-021, V3-E-023 | S2 | HIGH/MEDIUM | OPEN |
| V3-E-024 | S2 | CRITICAL | OPEN |
| **V3-E-024-fixed** | S2 | CRITICAL | OPEN |
| V3-E-030, V3-E-031 | S2 | MEDIUM/LOW | TRIAGED/OPEN |
| V3-E-032, V3-E-033, S3-V3-E-001 | S3 | CRITICAL/MEDIUM/CRITICAL | TRIAGED |
| V3-E-060…V3-E-062 | S2 | mixed | OPEN |
| S4-V3-E-012…S4-V3-E-055 (44 findings) | S4 | mixed | TRIAGED |
| S6-V3-E-003 | S6 | HIGH | OPEN |

(Full per-finding evidence pulled from the live projection; abbreviated here
for length — every id above is verifiable via `GET /api/projection` today.)

### 2.2 Confirmed, well-documented, no action needed

- **`V3-E-016` (S3, CRITICAL) vs `S4-V3-E-016` (S4, MEDIUM)** — genuinely
  distinct findings that independently drew the same number. S3's is a
  deployed-web-door hallucination defect (`validation_stage.ts`, the
  native's real chart facts leaking into a synthetic-chart answer). S4's is
  about `register_leak_lint.ts:80` (internal register-id leakage into reader
  prose) — an unrelated concern. `EDIR_V3_REGISTER_v1_0.md:1166-1176`
  already documents this disposition explicitly and correctly ("a pure ID
  collision… not a duplicate finding or a severity-disagreement on the same
  defect"). Both ids are already collision-free strings in the tracker.
  **Disposition: two distinct findings, correctly separate. No merge.**
  Recommend only a cosmetic rename to the new convention (§4) plus an
  explicit cross-link annotation (§3, CORR-1/CORR-2) so a future reader
  never conflates "016" across streams again.

- **Historical `E-001` / draft-`V3-E-021` collision (S5 vs S2)** — already
  fully resolved in `EDIR_V3_REGISTER_v1_0.md:779-790`. S5's finding is
  correctly tracker-registered as bare `E-001` (continuity with the
  pre-v3, still-open historical PPR-26 item); S2's unrelated `V3-E-021`
  (composer "Deep dive" depth override silently ignored) is the genuine
  tracker occupant of that number. No live collision exists. No action.

- **S1's document-only `V3-E-012`/`V3-E-013`** — never tracker-registered
  (S1's finding intake was `FINDING_FREEZE`-rejected after `S1-F-001`'s
  remediation plan froze it — confirmed: no `S1-…` finding beyond
  `S1-F-001` appears in the live `findings` array). S1 already renamed its
  own document headings to `S1-V3-E-012`/`S1-V3-E-013` at its 2026-08-29
  convergence checkpoint. Since these were never tracker ids, **no tracker
  correction is needed or possible** — there is no `finding_discovered`
  event to correct. Informational only.

### 2.3 Confirmed anomaly — `V3-E-024-fixed` is a data-entry duplicate, not a second finding

`V3-E-024` (S2, CRITICAL, OPEN) is the real, well-documented finding: a
clarification-only turn's server stream never emits `turn.commit`, so the
reducer's `turn.close` handler never settles the turn — composer locked
121+ seconds observed, no recovery path. `EDIR_V3_REGISTER_v1_0.md:1774-1871`
documents it FIXED and independently verified, in merged PR #1612 (commit
`41bc1f3d1`, confirmed via `git`/`gh pr view 1612` — MERGED
2026-08-28T02:08:10Z, part of the same 6-commit PR that also carries the
`V3-E-013`/`V3-E-030` fix, see §2.4).

`V3-E-024-fixed` (S2, CRITICAL, OPEN) is a **separate `finding_discovered`
event**, filed under the literal string id `"V3-E-024-fixed"`, whose only
evidence beyond the shared doc anchor `#V3-E-024` is `commit
repo://41bc1f3d1` — **the exact same commit** already cited as `V3-E-024`'s
fix. There is no `remediation_implemented` or `verification_accepted`
tracker event for either id (`GET /api/projection`'s `remediations` and
`verifications` arrays contain zero entries whose `finding_id` is
`V3-E-024` or `V3-E-024-fixed`; the only `*-024`-shaped remediation/
verification pair in the tracker belongs to the unrelated `S4-V3-E-024`).

**Determination: `V3-E-024-fixed` is not a second real finding.** It is a
mis-typed attempt to record that `V3-E-024` had been fixed — the correct
event type for that action is `remediation_implemented` (referencing
`finding_id: "V3-E-024"`), not a new `finding_discovered`. Whoever filed it
most likely typed the id as shorthand for "V3-E-024, now fixed" rather than
intending a second defect. The "-fixed" suffix is not a real finding
qualifier anywhere else in this campaign's id space.

**Disposition: VOID the duplicate via a `correction_recorded` annotation
(CORR-7, §3), and separately emit the real missing state-repair events**
(`remediation_implemented` + `verification_accepted` for `finding_id:
"V3-E-024"`, citing PR #1612 / commit `41bc1f3d1`) so the tracker's
`remediations`/`verifications` arrays actually reflect what
`EDIR_V3_REGISTER_v1_0.md` already claims in prose. These two events are
**not** `correction_recorded` — they are ordinary `STREAM_LEAD` events, and
I list their exact payloads in §3.2 as a companion action, since a
correction-only fix would leave the substantive gap (no remediation/
verification record for a CRITICAL, user-facing, already-merged fix)
unaddressed.

### 2.4 Newly discovered anomaly — tracker `V3-E-013` is a stale/renumbered anchor, and both `V3-E-012` and `V3-E-013` have a live, undocumented S4 numeric echo

This one is **not in the task brief's known list** — found via the
`rejected_events` audit trail, which the brief did not point me at.

`rejected_events` contains exactly 3 `FINDING_ID_CONFLICT` rejections:

| received_at | actor | attempted finding_id | outcome |
|---|---|---|---|
| 2026-08-27T23:54:37Z | `lead-s2` | `V3-E-012` | rejected (S3 already held it) → S2 re-filed as `V3-E-021` |
| 2026-08-27T23:55:57Z | `lead-s3` | `V3-E-013` | rejected (S2 already held it) → S3's attempt does not appear under any surviving id; likely absorbed into `V3-E-016`/`V3-E-032`/`V3-E-033` |
| 2026-08-28T00:42:35Z | `lead-s4` | `V3-E-012` | rejected (S3 already held it) → S4 re-filed as `S4-V3-E-012` |

This independently *proves*, from the tracker's own append-only audit log
(not from anyone's narrative), that `S4-V3-E-012` began life as S4's own
attempt at the bare id `V3-E-012` — S4 believed it had its own, unrelated
"012" finding, got rejected, and refiled with the `S4-` prefix. This is
strong corroborating evidence (independent of `EDIR_V3_REGISTER_v1_0.md`'s
own narrative) that `V3-E-012` (S3) and `S4-V3-E-012` are two genuinely
different findings that coincidentally chose the same number — the same
pattern already confirmed for `V3-E-016`/`S4-V3-E-016` (§2.2).

But `S4-V3-E-012`'s *content* has never been independently confirmed in
writing: **S4 has not yet published a stream result packet in this
directory** (no `S4_RESULT_PACKET*.md`/`STREAM_S4_RESULT_PACKET*.md` exists
at the time of this forensic pass), so there is no S4-authored prose
describing what `S4-V3-E-012` (evidence:
`platform-mcp/src/tools/register_prashna_ask.ts:198-206`) or `S4-V3-E-013`
(evidence: `platform/src/lib/pariprashna/pipeline/prashna_ask_synthesis.ts:
285-294`) actually are. **I am not asserting they are distinct from
`V3-E-012`(S3)/`V3-E-013`(tracker) on faith — the rejected-event log proves
S4 tried and failed to claim the bare numbers, which is consistent with
either "genuinely distinct finding" or "S4 re-derived a related finding
about the same underlying defect independently." Given different evidence
files, different severities (HIGH vs MEDIUM for the 012 pair; CRITICAL vs
CRITICAL for the 013 pair — the 013 pair's severity match is the one weak
point in the "clearly distinct" read) and no written S4 rationale to
resolve it, this is an honest open question, not a ruling.**

Separately — and this is the real anomaly of this pair — the live tracker
finding literally called `V3-E-013` (S2, CRITICAL, OPEN, evidence: doc
anchor `EDIR_V3_REGISTER_v1_0.md#V3-E-013` + `commit repo://c06d19486`) does
**not** correspond to any heading currently titled `V3-E-013` in
`EDIR_V3_REGISTER_v1_0.md` — no such heading exists (confirmed by direct
grep of the current file). The commit it cites, `c06d19486`, is the fix
commit for the section now titled **`V3-E-030`** ("The settle announcement
claimed 'Grounded' for a turn whose own receipt recorded
`hallucination_count: 4`…", `EDIR_V3_REGISTER_v1_0.md:1548-1618`).
Independently confirmed via GitHub: the merged PR carrying that commit is
**PR #1612**, titled *"fix(pariprashna): settle announcement discloses
grade, never a bare confident count (S2 / V3-E-013)"* (`gh pr view 1612`,
MERGED 2026-08-28T02:08:10Z) — the PR title itself still says `V3-E-013`,
matching the tracker's permanent `finding_id`, even though the markdown
register's heading was later renumbered to `V3-E-030` during a
same-branch merge-conflict cleanup. `EDIR_V3_REGISTER_v1_0.md:2303-2305`
confirms this in its own closing trailer: *"V3-E-030 FIXED by S2…
(renumbered from a draft V3-E-013 on S2's own branch after this merge
revealed S1 had independently claimed that id on main…)"*.

**Disposition: `V3-E-013` is NOT a duplicate-id collision in the tracker**
— it remains the sole, globally-unique, correctly-registered `finding_id`
for this defect, and no rename is structurally required. It **is** a stale
cross-reference: the tracker's permanent `finding_id` and the merged PR
title both say `V3-E-013`; the living document heading says `V3-E-030`.
Anyone resolving `EDIR_V3_REGISTER_v1_0.md#V3-E-013` today gets a 404
anchor. **Fix belongs to S2** (document-territory, per this campaign's own
established discipline of never fixing across a territory boundary) — I am
not editing `EDIR_V3_REGISTER_v1_0.md` myself; I am filing the referral
(CORR-5, §3) and recommending S2 add a one-line "aka tracker id `V3-E-013`"
note to the `V3-E-030` heading, or an anchor alias, whichever S2 prefers.

### 2.5 Informational-only anomalies (no tracker action possible or warranted)

- **`S5-V3-E-024`** (`S5_LIVE_REPROOF_CHECKPOINT_v1_0.md:238`, "`/api/assets/
  [chart_id]/[asset_key]` is dead code") numerically echoes S2's
  tracker-registered `V3-E-024`, but was never itself tracker-registered —
  `S5_LIVE_REPROOF_CHECKPOINT_v1_0.md:395` confirms it is blocked by
  `FINDING_FREEZE`, document-only, same pattern as S1's frozen intake. No
  live collision exists; no correction event is possible (no
  `finding_discovered` event exists for it to correct). Flagged purely so
  the new convention (§4) prevents this from ever reaching the tracker as a
  live collision once S5's freeze lifts.
- **`S6-V3-E-003`**'s evidence cites anchor `EDIR_V3_REGISTER_v1_0.md#S6-V3-
  E-003`, which does not exist in the current document (no `### S6-…`
  heading anywhere in the register — S6, like S4, has not yet published
  narrative documentation). Not a collision; a documentation-debt gap.
  Flagged for S6's own stream lead, not actionable by this lane.
- **`V3-E-032`'s `root_cause_group: "V3-E-016"`** is intentional grouping
  (V3-E-032 corroborates V3-E-016 at corpus scale), not a collision —
  confirmed by both findings' own prose. No action.

---

## 3. Exact `correction_recorded` events proposed

All payloads below are schema-valid against `EVENT_SCHEMA_v1_0.json`
(`actor_id`, `idempotency_key`, `event_type`, `payload` required;
`payload.corrects_event_id` + `payload.reason` required by
`control.py`'s `correction_recorded` validation). **`corrects_event_id`
is left as an explicit resolution instruction, not a fabricated UUID** — the
live, read-only `/api/projection` surface does not expose raw `event_id`s
for `finding_discovered` events (only `/api/rejected` and a handful of
inline citations in `EDIR_V3_REGISTER_v1_0.md` do, e.g. `V3-E-032`'s
`ef457619-…`), and no GET endpoint lists the full event ledger. Per B.10 /
§N.7 item 6 doctrine (an honest null beats an invented value), I am not
guessing a UUID. The Surrogate (or the relevant stream lead, who does have
legitimate access to the tracker's internal event log / SQLite via the
tracker's own tooling — never by hand-editing the file, per CLAUDE.md's "do
not touch the SQLite file directly" rule that binds this lane too) should
resolve each `corrects_event_id` from the identifying details given, then
submit.

**Role note (repeats §0): `actor_id` on every event below is a stream
lead, not a surrogate identity — `correction_recorded` is `STREAM_LEAD`-
only.**

### 3.1 Corrections (7)

**CORR-1 — annotate S3's `V3-E-016`**
```json
{
  "actor_id": "lead-s3",
  "idempotency_key": "a6-corr-1-v3e016-s3-crosslink",
  "event_type": "correction_recorded",
  "stream_id": "S3",
  "payload": {
    "corrects_event_id": "<RESOLVE: finding_discovered event for finding_id=V3-E-016, stream_id=S3, actor lead-s3, severity CRITICAL, filed 2026-08-28 stream-open>",
    "reason": "Disambiguation, not a defect correction: this finding_id numerically collides with the unrelated S4-owned finding S4-V3-E-016 (register_leak_lint.ts, MEDIUM). Confirmed distinct defects by independent evidence review (validation_stage.ts hallucination-disclosure gap vs. internal-register-id leakage into reader prose) -- see EDIR_V3_REGISTER_v1_0.md:1166-1176 and ID_RECONCILIATION_v1_0.md section 2.2. Going forward this finding's canonical alias under the S{N}-V3-E-NNN convention is S3-V3-E-016. No content, severity, or status change.",
    "canonical_alias": "S3-V3-E-016",
    "distinct_from": ["S4-V3-E-016"]
  },
  "evidence": [
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-016"},
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/ID_RECONCILIATION_v1_0.md"}
  ]
}
```

**CORR-2 — annotate S4's `S4-V3-E-016`**
```json
{
  "actor_id": "lead-s4",
  "idempotency_key": "a6-corr-2-s4v3e016-crosslink",
  "event_type": "correction_recorded",
  "stream_id": "S4",
  "payload": {
    "corrects_event_id": "<RESOLVE: finding_discovered event for finding_id=S4-V3-E-016, stream_id=S4, actor lead-s4, severity MEDIUM>",
    "reason": "Disambiguation, not a defect correction: this finding_id numerically echoes the unrelated S3-owned finding V3-E-016 (deployed-door real-chart-fact hallucination, CRITICAL). Confirmed distinct defects -- see EDIR_V3_REGISTER_v1_0.md:1166-1176 and ID_RECONCILIATION_v1_0.md section 2.2. Canonical alias under the S{N}-V3-E-NNN convention is unchanged (S4-V3-E-016, already correctly prefixed). No content, severity, or status change.",
    "canonical_alias": "S4-V3-E-016",
    "distinct_from": ["S3-V3-E-016 (tracker id V3-E-016)"]
  },
  "evidence": [
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-016"},
    {"kind": "code", "uri": "repo://platform/src/lib/pariprashna/citations/register_leak_lint.ts"}
  ]
}
```

**CORR-3 — annotate S3's `V3-E-012`**
```json
{
  "actor_id": "lead-s3",
  "idempotency_key": "a6-corr-3-v3e012-s3-openquestion",
  "event_type": "correction_recorded",
  "stream_id": "S3",
  "payload": {
    "corrects_event_id": "<RESOLVE: finding_discovered event for finding_id=V3-E-012, stream_id=S3, actor lead-s3, severity MEDIUM>",
    "reason": "This finding_id numerically echoes S4-V3-E-012 (HIGH, register_prashna_ask.ts:198-206). rejected_events confirms S4 independently attempted the bare id V3-E-012 at 2026-08-28T00:42:35Z and was rejected FINDING_ID_CONFLICT, then refiled as S4-V3-E-012 -- proving S4 believed this was its own, separate finding, not proof the underlying defects are unrelated. No S4-authored stream result packet exists yet to confirm the content independently. Recorded as an OPEN DISAMBIGUATION QUESTION, not a ruling: pending S4's written finding rationale. Canonical alias under the S{N}-V3-E-NNN convention is S3-V3-E-012 regardless of the outcome of that question -- this note does not change severity, status, or content. Note also this finding is documented CLOSED-AS-RULED in EDIR_V3_REGISTER_v1_0.md:1007-1024 (native decision_recorded 99421811-e13d-4b19-88f4-2cc16d7af220) but the tracker's own finding status still reads TRIAGED, not any closed state -- flagged separately as a status-sync gap, not fixed by this correction (finding_triaged is a NATIVE_SURROGATE event, out of this lane's and this event's scope).",
    "canonical_alias": "S3-V3-E-012",
    "open_question": "identity vs S4-V3-E-012, pending S4 written confirmation"
  },
  "evidence": [
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-012"},
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/ID_RECONCILIATION_v1_0.md"}
  ]
}
```

**CORR-4 — annotate S4's `S4-V3-E-012`**
```json
{
  "actor_id": "lead-s4",
  "idempotency_key": "a6-corr-4-s4v3e012-openquestion",
  "event_type": "correction_recorded",
  "stream_id": "S4",
  "payload": {
    "corrects_event_id": "<RESOLVE: finding_discovered event for finding_id=S4-V3-E-012, stream_id=S4, actor lead-s4, severity HIGH, resubmitted after a FINDING_ID_CONFLICT rejection on bare V3-E-012 at 2026-08-28T00:42:35Z>",
    "reason": "Mirrors CORR-3: this finding_id numerically echoes S3's V3-E-012 (MEDIUM, quality-corpus real-chart-grounding process finding, CLOSED-AS-RULED). Evidence files differ (register_prashna_ask.ts:198-206 vs fixtures.ts/types.ts) and severities differ (HIGH vs MEDIUM), which weighs toward distinct findings, but no S4-authored written rationale exists yet to confirm independently. Recorded as an OPEN DISAMBIGUATION QUESTION pending S4's own stream result packet. Canonical alias under the S{N}-V3-E-NNN convention is unchanged (S4-V3-E-012, already correctly prefixed).",
    "canonical_alias": "S4-V3-E-012",
    "open_question": "identity vs S3's V3-E-012 (tracker id V3-E-012), pending S4 written confirmation"
  },
  "evidence": [
    {"kind": "code", "uri": "repo://platform-mcp/src/tools/register_prashna_ask.ts"},
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-012"}
  ]
}
```

**CORR-5 — annotate S2's `V3-E-013`, flag stale doc anchor + open question vs S4-V3-E-013**
```json
{
  "actor_id": "lead-s2",
  "idempotency_key": "a6-corr-5-v3e013-stale-anchor",
  "event_type": "correction_recorded",
  "stream_id": "S2",
  "payload": {
    "corrects_event_id": "<RESOLVE: finding_discovered event for finding_id=V3-E-013, stream_id=S2, actor lead-s2, severity CRITICAL, evidence cites commit c06d19486>",
    "reason": "Stale evidence anchor, not a duplicate-id collision: this finding's evidence cites EDIR_V3_REGISTER_v1_0.md#V3-E-013, a heading that no longer exists in the current document. The document's own closing trailer (EDIR_V3_REGISTER_v1_0.md:2303-2305) confirms this content was renumbered to V3-E-030 during a same-branch merge-conflict cleanup after S1 independently claimed V3-E-013 as a document-only draft. The merged fix PR (github.com/Marsys-Technologies/Madhav/pull/1612, MERGED 2026-08-28T02:08:10Z) is titled '...(S2 / V3-E-013)', matching this tracker finding_id -- confirming this tracker id and that PR both correctly refer to the settle-announcement grade-disclosure defect now narrated under the V3-E-030 heading. This finding_id remains globally unique and valid; no rename is required. Recommend S2 (document-owning stream) add a cross-reference note at the V3-E-030 heading pointing back to tracker id V3-E-013, or an anchor alias -- referred, not fixed cross-territory, per this campaign's own discipline. Separately: this finding_id numerically echoes S4-V3-E-013 (CRITICAL, prashna_ask_synthesis.ts:285-294); rejected_events shows lead-s3 (not S4) attempted and lost the bare V3-E-013 id at 2026-08-27T23:55:57Z, so S4's S4-V3-E-013 was filed pre-emptively prefixed and never collided at the raw-id level -- but its relationship in content to this finding is an OPEN QUESTION pending S4's own written result packet. Canonical alias under the S{N}-V3-E-NNN convention is S2-V3-E-013 (with the caveat that the living narrative for this defect is the V3-E-030 heading).",
    "canonical_alias": "S2-V3-E-013",
    "stale_doc_anchor": "EDIR_V3_REGISTER_v1_0.md#V3-E-013 -> living content is at #V3-E-030",
    "open_question": "content relationship to S4-V3-E-013, pending S4 written confirmation"
  },
  "evidence": [
    {"kind": "pull_request", "uri": "https://github.com/Marsys-Technologies/Madhav/pull/1612"},
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-030"},
    {"kind": "commit", "uri": "repo://c06d19486"}
  ]
}
```

**CORR-6 — annotate S4's `S4-V3-E-013`**
```json
{
  "actor_id": "lead-s4",
  "idempotency_key": "a6-corr-6-s4v3e013-openquestion",
  "event_type": "correction_recorded",
  "stream_id": "S4",
  "payload": {
    "corrects_event_id": "<RESOLVE: finding_discovered event for finding_id=S4-V3-E-013, stream_id=S4, actor lead-s4, severity CRITICAL>",
    "reason": "Mirrors CORR-5: this finding_id numerically echoes the tracker's V3-E-013 (S2, CRITICAL, whose living narrative is EDIR_V3_REGISTER_v1_0.md#V3-E-030). Same severity tier on both (CRITICAL) is the one signal that does not clearly separate them -- unlike the V3-E-012/S4-V3-E-012 pair, where severities differ. No S4-authored written rationale exists yet. Recorded as an OPEN DISAMBIGUATION QUESTION pending S4's own stream result packet; not ruled either way by this correction. Canonical alias unchanged (S4-V3-E-013, already correctly prefixed).",
    "canonical_alias": "S4-V3-E-013",
    "open_question": "identity vs S2's V3-E-013 / EDIR V3-E-030, pending S4 written confirmation"
  },
  "evidence": [
    {"kind": "code", "uri": "repo://platform/src/lib/pariprashna/pipeline/prashna_ask_synthesis.ts"},
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-013"}
  ]
}
```

**CORR-7 — void the `V3-E-024-fixed` duplicate**
```json
{
  "actor_id": "lead-s2",
  "idempotency_key": "a6-corr-7-v3e024fixed-void",
  "event_type": "correction_recorded",
  "stream_id": "S2",
  "payload": {
    "corrects_event_id": "<RESOLVE: finding_discovered event for finding_id=V3-E-024-fixed, stream_id=S2, evidence cites commit 41bc1f3d1>",
    "reason": "This finding_id is a data-entry duplicate of finding_id V3-E-024, not a second real defect. Its only distinguishing evidence (commit 41bc1f3d1) is the exact same commit already cited by V3-E-024 -- confirmed part of merged PR #1612 (MERGED 2026-08-28T02:08:10Z), which STREAM_S2_RESULT_PACKET_v1_0.md line 76 lists among that PR's six commits, and which fixes V3-E-024's turn.close/reducer defect per EDIR_V3_REGISTER_v1_0.md:1824-1868. No remediation_implemented or verification_accepted tracker event exists for either V3-E-024 or V3-E-024-fixed despite EDIR_V3_REGISTER_v1_0.md claiming FIXED and independently verified -- this finding_discovered event appears to have been an attempted (and mistyped) way of recording that fix, using the wrong event type. VOID: this finding_id should never be treated as a live, distinct defect going forward, must not be re-derived under the new convention, and carries no independent triage/remediation/verification obligation. The real remediation and verification records for V3-E-024 are proposed separately as ordinary STREAM_LEAD events (see ID_RECONCILIATION_v1_0.md section 3.2), not as part of this correction.",
    "voided_duplicate_of": "V3-E-024",
    "canonical_alias_for_V3-E-024": "S2-V3-E-024"
  },
  "evidence": [
    {"kind": "pull_request", "uri": "https://github.com/Marsys-Technologies/Madhav/pull/1612"},
    {"kind": "commit", "uri": "repo://41bc1f3d1"},
    {"kind": "doc", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-024"}
  ]
}
```

### 3.2 Companion events (not `correction_recorded` — the actual state repair for V3-E-024)

These are ordinary `STREAM_LEAD` events (`remediation_implemented`,
then, once independently re-verified, `verification_accepted` by an
`INDEPENDENT_VERIFIER`-role actor). I list them because CORR-7 alone would
leave the substantive gap open: the tracker would still show `V3-E-024` as
`OPEN` with zero remediation/verification records, contradicting the
register's own "FIXED and independently verified" claim.

```json
{
  "actor_id": "lead-s2",
  "idempotency_key": "a6-companion-1-v3e024-remediation",
  "event_type": "remediation_implemented",
  "stream_id": "S2",
  "payload": {
    "remediation_id": "S2-REM-024",
    "finding_id": "V3-E-024"
  },
  "evidence": [
    {"kind": "pull_request", "uri": "https://github.com/Marsys-Technologies/Madhav/pull/1612"},
    {"kind": "commit", "uri": "repo://41bc1f3d1"}
  ]
}
```

A follow-on `verification_accepted` event (role `INDEPENDENT_VERIFIER`,
referencing `remediation_id: "S2-REM-024"`) should be submitted by whichever
actor performed the "3rd verifier pass" `EDIR_V3_REGISTER_v1_0.md:1850-1868`
describes, under their own tracker identity — not fabricated here, since I
cannot verify who that was beyond the register's own prose, and inventing an
actor_id for a verification event would itself be a §N.7/§N.8 violation
(a verification claim needs a real verifier behind it).

---

## 4. Going-forward convention: `S{N}-V3-E-NNN`

**Rule.** Every new finding, from this point forward, is filed with its
owning stream as an explicit prefix: `S1-V3-E-NNN` … `S6-V3-E-NNN` (and, by
extension, `P1-...`/`P2-...` phase-scoped ids keep their existing
`P{N}-`-prefixed pattern, which already never collided). The historical
legacy-EDIR numbering (`E-001`…`E-122`, imported by reference in
`EDIR_V3_REGISTER_v1_0.md §0`) is a separate, closed namespace; a stream that
re-opens a historical `E-NNN` item as a live v3 tracker finding (as S5 did
for `E-001`, preserving PPR-26 continuity deliberately) should register it
stream-prefixed too — `S5-E-001` — rather than bare, even though the
tracker's `finding_discovered` validation does not itself require a `V3-E-`
substring in the id (confirmed: `control.py:595` only checks the id is a
non-empty string with a valid severity and stream; nothing enforces the
`V3-E-NNN` shape).

**Why this works with the tracker as built, no code change required.**
`finding_discovered`'s validation already enforces **global** uniqueness
across the whole tracker (`control.py:597`, no stream filter on the
existing-id check) — this is exactly the mechanism that produced every
prefix-workaround documented in §2 (S4's systematic `S4-V3-E-*` numbering,
S1's `S1-V3-E-012/013` post hoc rename, S6's `S6-V3-E-003`). The
`S{N}-V3-E-NNN` convention simply makes deliberate, campaign-wide, what
individual streams already backed into independently under pressure. No
stream needs to coordinate a shared counter with any other stream once
every id carries its own stream's prefix — the collision surface shrinks to
"can one stream's own lead accidentally reuse one of its own numbers",
which is a much smaller, single-actor problem the existing global-uniqueness
check already guards against for free.

**What does NOT need to happen under this convention:** no historical
finding_id needs to be renamed in the live tracker (the mechanism to do
that safely does not exist yet — see §0's `finding_relabeled` recommendation
below); every `correction_recorded` event in §3 documents a **canonical
alias** for future citation, it does not attempt an in-place rename.

---

## 5. Recommendation (non-blocking, out of this lane's write scope)

The tracker has no event type or projector logic to actually rename, merge,
or split a `finding_id` once minted — `correction_recorded`'s only real
projector effect today is the `work_started`/session-`ceiling` case. Given
this campaign has now hit the same wall twice (S1's document-only rename,
and this lane's tracker-side corrections), a small, additive
`finding_relabeled` event type (STREAM_LEAD-emittable, validated the same
way `correction_recorded` is, with real `findings[fid]` projector support
to set a `canonical_alias` field the dashboard renders next to the raw id)
would close this gap properly. Flagged for the Programme Integrator; not
implemented by this lane (no tracker write access, and a schema/projector
change is exactly the kind of "if a writer seems to need a contract change
→ STOP and raise it" situation CLAUDE.md §N.2 describes for the orchestrator,
applied here to the tracker's own frozen-ish event contract).

---

## 6. Summary table — every anomaly found and its disposition

| Anomaly | In original brief? | Live tracker collision? | Disposition |
|---|---|---|---|
| `V3-E-016` (S3) vs `S4-V3-E-016` | Yes | No (already prefixed) | Distinct, confirmed. Cross-link only (CORR-1/2). |
| `V3-E-012` (S3) vs `S4-V3-E-012` | Yes (as "V3-E-012 history") | No (already prefixed) | Likely distinct, **not independently confirmed** — S4 has no written packet yet. Open question flagged (CORR-3/4). |
| `V3-E-024-fixed` | Yes | No (never a real second finding) | Data-entry duplicate. VOID (CORR-7) + missing remediation/verification events supplied (§3.2). |
| tracker `V3-E-013` stale doc anchor (→ EDIR `V3-E-030`) | **No — found via `rejected_events` + `gh pr view`** | No | Not a collision; broken cross-reference. Referred to S2 (CORR-5). |
| `V3-E-013` (S2) vs `S4-V3-E-013` | No | No (already prefixed) | Open question, weaker separation signal (same severity) — flagged (CORR-5/6). |
| `S5-V3-E-024` vs `V3-E-024` (S2) | No | No (S5's is `FINDING_FREEZE`-blocked, never registered) | Informational only; no tracker action possible. |
| `S6-V3-E-003` dangling doc anchor | No | No | Documentation debt, referred to S6. |
| `E-001` / draft-`V3-E-021` (S5 vs S2) | No | No — already resolved in doc | Historical, closed. No action. |
| S1 document-only `V3-E-012`/`013` | Implicitly (background) | No — never tracker-registered | Historical, closed by S1 itself. No action. |
| `V3-E-032` `root_cause_group: V3-E-016` | No | N/A | Intentional grouping, not a collision. |

**Bottom line: the live tracker currently has zero raw `finding_id` string
collisions.** Every apparent collision either (a) is a numeric-only echo
between two already-distinct string ids that a human reader can still
misattribute, (b) was a document-only draft that never reached the tracker,
or (c) is the one genuine data-entry duplicate (`V3-E-024-fixed`). The
`S{N}-V3-E-NNN` convention is designed to keep it that way permanently, at
zero tracker-code cost.
