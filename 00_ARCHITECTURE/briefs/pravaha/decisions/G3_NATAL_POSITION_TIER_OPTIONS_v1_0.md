---
artifact: G3_NATAL_POSITION_TIER_OPTIONS_v1_0.md
canonical_id: G3_NATAL_POSITION_TIER_OPTIONS
version: 1.0
status: DRAFT for the owner — an options note; authorises NOTHING
date: 2026-10-04
revised_by: Stream B (Śāstra) 2026-10-04 — tense corrected after SETTLED-1 (the S-L1 rebuild has happened); no option or cost changed
authored_by: Stream C (Kimi) — steward task C48 (gap G3 of REBUILD_AND_UPSTREAM_SEQUENCING_v1_0)
scope: >
  One-page plain-language options note for the one open owner question in
  REBUILD_AND_UPSTREAM_SEQUENCING_v1_0 (§5, G3): the first sealed Gochara generation's
  ten natal longitudes are read from chart_facts at the tier they carry today — 'single',
  i.e. computed once and never cross-checked by a second method. Decision needed before
  the numerical build: accept 'single', or require an independent second derivation first.
---

# G3 — natal positions are single-check values: the two options

## The situation in plain words

A reading's starting point is ten numbers: where the Sun, Moon, five planets, and the
two lunar nodes stood at birth. Today each of those numbers was computed **once**, by
one method, and stored. Nobody has ever computed them a second way and compared. That
is what tier "single" means — not that the number is wrong, but that nothing
independent has confirmed it.

Everything the new Gochara engine concludes about a chart starts from these ten
numbers. If one of them is off, the error does not stay in one place: it moves every
event date derived from that position.

The numbers were rebuilt anyway at SETTLED-1 (2026-10-04: Suvarṇa's S-L1 rebuild, on the
Swiss ephemeris instead of the Moshier fallback). But that rebuild is the **same method
with a better engine** — it fixes a known small bias, it is not an independent check.

## Option A — accept "single" natal positions

Say honestly, in the sealed brief's disclosures, that the natal positions are
single-check values, and proceed.

- **Cost:** almost nothing — a disclosure text change (already planned, bundled with
  Stream A's F-R14-1 change, inside the implementation digest).
- **Risk:** a systematic error in the one computation method would pass silently into
  every sealed reading, with the seal's full authority attached. The known evidence is
  reassuring — the engine swap moves the longitudes by under 1 arc-second and no sign,
  nakshatra, or kakshya cell is closer than 828″ to any stored value — but both engines
  come from the same computation family, so a shared blind spot would not show.
- **What changes for readings:** nothing visible. The disclosure line is the only
  difference.

## Option B — require an independent second derivation before the numerical build

Compute the ten longitudes a second time by a genuinely separate route (different
ephemeris source or an independently written computation), compare, and only then
allow numbers to be switched on. A disagreement beyond tolerance stops the build by
name, like every other refusal in the system.

- **Cost:** a new derivation path to write, review, and maintain forever; a new
  comparison gate in the build; the numerical build waits until both agree. Roughly a
  small asset's worth of work, plus a permanent second ephemeris dependency.
- **Risk:** low residual risk — this is the same two-method standard the daśā rows
  already carry ("two_pass_verified"). The main new risk is operational: two sources
  can disagree for benign reasons (nutation models, delta-T tables), and each
  disagreement needs a ruling.
- **What changes for readings:** nothing the reader can see, except the disclosure can
  say the natal positions are cross-checked. The value is that a whole class of silent,
  self-consistent error becomes impossible rather than merely unlikely.

## What is already true either way

- The daśā timeline the engine also depends on is **already two-pass verified** — only
  the ten natal longitudes are single-check.
- At S-L1 the stored values move by < 1″ and no cell boundary is within 828″ of any
  of them on fixture values (Suvarṇa's addendum and Stream A's analysis; **not** re-measured
  on the real rows in the SETTLED-1 record, which covers the daśā rows), so for
  the **all-NULL proof build** either option is safe — the question binds the build
  where numbers are switched on.
- Whichever option is chosen, the first seal's brief discloses the tier honestly
  (REBUILD_AND_UPSTREAM_SEQUENCING_v1_0 §5, G3 row).

## The question

Before the numerical Gochara build: **accept single-check natal positions (Option A),
or require an independent second derivation first (Option B)?**
