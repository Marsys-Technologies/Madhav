---
artifact: KALA_DELEGATED_DECISIONS
canonical_id: KALA_DELEGATED_DECISIONS
version: "1.1"
status: DECIDED  # D-C WITHDRAWN and replaced at v1.1 — it contradicted N-6a
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

**Note added at v1.1:** the Saṅgam session has adopted this distinction verbatim and its B-5 now
reads `UNOWNED-BY-AUTHORITY` rather than naming "the L0 owner", on the ground that the latter names
a lane, not a person. The Gochara brief implements it independently: §8.4 applies the G-9 row
repairs to a disposable database only, and §5.1 stamps `house_vedha corpus_verifiable = true` only
once the re-citation is on the row.

**For the native, the one thing only they can settle:** whether the L0 owner is a session to be
opened, an existing stream given the authority, or the native directly. Until then this is the
single largest unowned surface in the campaign, and it now says so in a durable place.

---

## D-C — **WITHDRAWN AT v1.1. My reversal was wrong; the original recommendation was already a native ruling.**

**What v1.0 decided:** do NOT set the century writer inactive, because N-14's regeneration needs it;
declare `clear_tables` instead and bar the asset from unattended builds.

**Why that was wrong.** The Gochara session refused it and I verified its grounds at source in
`GOCHARA_RULING_SHEET_v1_0.md` on `origin/l3/gochara-elevation`. Three rulings I had not read
decide this, and two of them decide it against me:

| ruling | what it says |
|---|---|
| **N-5** | `ka_gochara` owns the served product and writes a NEW generation into `kala_gochara_windows`; **"the century writer donates its engine and stays held."** |
| **N-6a** | **RULED: century `is_active=false` at runbook step 3**, reversible at WP10, nothing deleted; the registry declares its production write (F-30) at step 5. |
| **N-10** | the publication generation is `'4.0'`; `'3.0'` is the rollback surface. |

So the regeneration is `ka_gochara` writing `'4.0'`. It never needs the century writer to run.
`'3.0'` is never regenerated — the "never a patch over live rows" condition I leaned on is a
**prohibition on touching `'3.0'`**, which is the opposite of what I read it to mean. And
`is_active=false` was **already ruled by the native at N-6a**, at a named runbook step, reversible,
with nothing deleted.

**So my four-times-raised original recommendation was correct, the native had already ruled it, and
I reversed it into a weaker procedural form.** "No unattended build may include the asset" is a
convention someone must remember; `is_active=false` at step 3 is structural. I replaced a ruled
structural guard with an unruled procedural one, on a premise the ruling set excludes.

**How I got it wrong — the same mechanism, third time today.** I drew a consequence from N-14, the
one ruling I had read, without reading N-5, N-6 or N-6a beside it. I checked *a* ruling, not the
*ruling set*. Yesterday's forms of this were checking a ref instead of a file, a directory instead
of a table, and one page instead of a chapter.

**What stands, and it is the part that was mine:** the diagnosis. The registry declares only
`kala_gochara_windows_v2` while the writer DELETEs `kala_gochara_windows` generation `'3.0'`, and
`clear_tables` is NULL, so the production write is invisible to Atlas and to every blast-radius
estimate. That is F-30 and the Gochara session has adopted it as registry work at runbook step 5.
The Gochara session's own summary is the fair one: my diagnosis was right and stays right; only the
inference that the writer must remain dispatchable was wrong.

**Decided at v1.1:** N-6a governs. The century writer goes `is_active=false` at runbook step 3,
reversible at WP10, nothing deleted; `clear_tables` is declared at step 5. This session's D-C adds
nothing and is withdrawn rather than reconciled, because a decision that merely re-states a native
ruling in weaker words is worse than no decision — it gives an executor two records that disagree.

```sql
-- v1.0 staged this as the whole remedy; at v1.1 it is step 5 of N-6a's runbook, not a substitute
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
