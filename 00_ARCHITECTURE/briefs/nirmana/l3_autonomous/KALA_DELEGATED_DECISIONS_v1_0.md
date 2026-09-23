---
artifact: KALA_DELEGATED_DECISIONS
canonical_id: KALA_DELEGATED_DECISIONS
version: "1.0"
status: DECIDED
date: 2026-09-23
decided_by: "L3 Kāla strategic session (madhav-fc), under the native's explicit delegation"
delegation: "The native, 2026-09-23, verbatim: 'Can you take the call on my behalf since you
  understand the system much better than me on the decision that you've consolidated you've you've
  given to me.' Scope: the four consolidated items this session put to the native."
authority_note: >
  These are the AUTHOR'S decisions under delegation, not the native's words. Each states its
  reasoning so any can be reversed by one native line. Nothing here authorizes code, migration,
  build or deployment; two decisions are deliberately NON-ACTIONS and two are staged pending an
  outage.
supersedes: "the four open items in KALA_ELEVATION_BLUEPRINT_v1_0.md addenda"
---

# Kāla — the four delegated decisions

The native delegated four consolidated items to this session. All four are decided below. Two
required a live database that is currently refusing on both endpoints (`127.0.0.1:5433` and
`:5434`); those two are decided **on their merits anyway**, with the query staged, because in both
cases the honest disposition does not depend on the query's result — only the eventual upgrade does.

---

## D-A — The readiness branch: **LEAVE AS-IS. Do not reset, do not force-push.**

**Decision: no action.**

`l3/kala-elevation-readiness` was advanced by this session's accidental push to include 18 Saṅgam
stage-3 commits. Verified before deciding: `c46cd9f0e` is an ancestor (a fast-forward, not a force),
every commit exists on `sangam/stage3` as well, **no open PR** targets the branch, and the sealed
L1 writer's net diff across the whole run is empty. Nothing was lost and nothing is queued to reach
`main`.

**Why not reset.** A reset would be a force-push on a shared ref that another session is actively
committing to, to correct an outcome that is cosmetically wrong and functionally harmless. The
remedy is more dangerous than the defect — the precise trade this campaign has been getting wrong
in the other direction all day. Both the Saṅgam and Kṣetra sessions independently recommend leaving
it, and the eventual PR opens from `sangam/stage3`, which contains the readiness history entirely.

**What IS actioned:** the root cause, which was never the branch. The Saṅgam execution prompt
pointed an executor at a shared checkout; that session has fixed the prompt at source to require
`git worktree add` and to assert worktree and branch as its first action. This session has left the
foreign worktree and works from its own. G15 in the blueprint's gap register is the standing entry.

---

## D-B — The L0 lane: **the work has a holder, not an owner. Recorded as UNOWNED-BY-AUTHORITY.**

**Decision: name the gap rather than fill it, and block the silent assumption.**

"The L0 owner" is cited as the responsible party in at least three artifacts
(`SANGAM_STAGE3_STATE.md` B-5, `D-L0-GG-FOLLOWUP_v1_0.md`, the Saṅgam ruling sheet's F-23/G-8
routing) and is bound to **no session, agent or person anywhere in the repository**. This session
cannot appoint one and will not invent a route — inventing a relay is precisely how a spec lands in
a gap while everyone assumes it was carried.

**The distinction that matters, and it is the decision:** the L0 work now has a **holder** — the
Gochara stream has taken G-9 into its lane and recorded the transit-row repair spec there — but no
**authority**. A holder can stage work; only an authority can apply it to L0 data. So:

1. `KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md` and the F-23/G-8 re-citation stay **staged and unapplied**.
2. No downstream packet may record the L0 fixes as routed-and-therefore-handled. They are routed to
   a holder, which is not the same as owned.
3. The row qualifications that depend on them (`house_vedha` → `applied` on re-citation) stay at
   their current grade until the re-citation actually lands, not from the moment it was specified.

**For the native, the one thing only they can settle:** whether the L0 owner is a session to be
opened, an existing stream given the authority, or the native directly. Until then this is the
single largest unowned surface in the campaign, and it now says so in a durable place.

---

## D-C — The century writer: **do NOT set it inactive. Fix the declaration instead.**

**Decision: reject the action I originally recommended to the native, on new information.**

I put "set the century writer inactive before any unattended build" to the native four times. I am
reversing it, and the reason is the N-14 ruling that landed after I first raised it.

`ka_gochara_v3_century_materialize` is `is_active = true` and DELETEs `kala_gochara_windows`
generation `3.0` — production — inside its staging transaction, while its registry row declares
only `kala_gochara_windows_v2` and carries `clear_tables = NULL`. That remains true and remains the
hazard.

**But N-14 now requires a same-generation gochara_v3 regeneration** to remove the `w30_modifier`
term from every stored λ, and the ruling explicitly requires it be done "inside a new candidate,
never a patch over live rows." Disabling the century writer would block the exact work the native
just ruled for. **Flipping the toggle treats the symptom and obstructs the remedy.**

**The real defect is not that the writer deletes production. It is that nothing declares that it
does.** An undeclared deletion is invisible to Atlas, to clear-scope reasoning and to every
blast-radius estimate. A declared one is an ordinary, reviewable build step.

**Decided action, staged on the outage:**

1. Add `kala_gochara_windows` to that asset's `clear_tables` so the registry states its true reach.
   Non-destructive, one `UPDATE`, reversible, blocks nobody.
2. Until that lands, **no unattended or overnight build may include this asset.** Attended runs are
   fine — the hazard is silent deletion nobody is watching, not deletion as such.
3. The N-14 regeneration proceeds under its own three conditions, which already forbid patching
   live rows.

```sql
-- staged; run when an endpoint is reachable
UPDATE asset_registry
   SET clear_tables = ARRAY['kala_gochara_windows_v2','kala_gochara_windows']
 WHERE asset_id = 'ka_gochara_v3_century_materialize';
```

---

## D-D — Sade-Sati: **demote the claim, keep the data, stage the real question.**

**Decision: `unqualified` pending a predicate-level check. Not removed, not left narrating.**

4,492 Sade-Sati facts serve on the canonical chart. The corpus holds five rows mentioning it, all in
one MEDIUM-provenance modern text, and four of those five are a twentieth-century author's
bindu-correlation observation across two example charts rather than any classical rule.

**This decision does not depend on the outstanding query, which is why it can be taken now.** Under
F23 a serving factor cannot claim source qualification on a citation that does not exist, whatever a
further search finds later. Under B.10 the rows are not dropped — writers emit, serve-time governs.
Under §N.6 and §N.7 the honest disposition of a claim we cannot ground is a declared gap, never a
confident sentence.

1. Sade-Sati rows carry `source_qualification = 'unsourced'` and serve **flagged**, not silently.
2. No narration layer states a Sade-Sati conclusion with unqualified confidence while that holds.
3. The rows stay. This is a qualification change, not a deletion.

**The question that is actually open, and the one that can upgrade this:** I searched for a **name**,
not a **doctrine**. "Sade-sati" is a late vernacular term — the rows themselves note "elarata" and
the 7½-year "Panoti" framing. Saturn's transit results reckoned from the Moon may well be attested
in the primaries under entirely different wording, inside the gochara chapters we have already been
reading for vedha. **Nobody has asked.** It must be asked by predicate, not by term, or it will
produce exactly the false absence this campaign was made of.

```sql
-- staged; the predicate form, NOT a term search
SELECT text_id, verse_ref, left(content_en, 400)
  FROM classical_text_chunks
 WHERE content_en ILIKE '%saturn%'
   AND (content_en ILIKE '%from the moon%' OR content_en ILIKE '%from the janma%'
        OR content_en ILIKE '%12th%' OR content_en ILIKE '%2nd%')
   AND text_id IN ('bphs','phaladeepika','saravali','brihat_jataka','hora_sara',
                   'jataka_parijata','sarvartha_chintamani','uttara_kalamrita');
```

If that returns a grant, Sade-Sati upgrades to `verse_cited` at page grain and the demotion in (1)
lifts. If it returns nothing, the demotion stands on a real check rather than on a term search.

---

## What this record does not decide

The native's own four-times-raised items are now closed, but three things remain genuinely theirs
and are not delegable by any reading of the delegation: **who the L0 owner is** (D-B), whether the
`PROVISIONAL_INSUFFICIENT_N` evaluation thresholds the Saṅgam stream set under its own delegation
are acceptable, and any disposition that would change what the instrument *tells the native about
their own life* beyond the honest-gap demotions above.
