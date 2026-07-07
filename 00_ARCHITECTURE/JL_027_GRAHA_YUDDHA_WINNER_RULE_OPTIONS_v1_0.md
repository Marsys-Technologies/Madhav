---
canonical_id: JL_027_GRAHA_YUDDHA_WINNER_RULE_OPTIONS
version: 1.0
status: SURFACED-FOR-RULING — awaiting native / Ācārya-Pratinidhi decision (gates W3/W4)
created: 2026-07-07
author: Claude Code (BA-R4-WRAP W2.3) — research surface for the JL-027 native ruling
program: CLAUDECODE_BRIEF_BA_R4_WRAP_v1_0.md §W2.3; closes JL-027 in BA_JUDGMENT_LEDGER_v1_0.md before W3
governs: ga_structural_writer._build_graha_yuddha_rows (winner rule) + downstream graha_yuddha readers
doctrine: CANONICAL-OR-FLOOR — a CITED classical method is adopted (with derivation ledger); if none is
  ratified/citable by W2 close, FLOOR to winner=NULL + reason='no_ratified_classical_rule'. The current
  lower-longitude proxy is NOT eligible under any circumstances.
citation_honesty: >
  Rule SUBSTANCE below is grounded in accessible translations/secondary sources (cited). Exact chapter/
  verse NUMBERS are given where a source states them but are FLAGGED as needing verification against a
  critical edition before they enter a derivation ledger — I did not collate a primary Sanskrit critical
  text this session. Do not treat any verse number here as ledger-final until §5 verification is done.
---

# JL-027 — Graha Yuddha (planetary war) winner rule: options for ruling

## 1. The defect being ruled (what currently ships)

`ga_structural_writer._build_graha_yuddha_rows` (platform/python-sidecar/ga_writers/ga_structural_writer.py
~L4815) computes, for two classical grahas within **orb ≤ 1.0°** in the same sign:

```
Lower absolute longitude = winner; higher longitude = loser.
# code comment: "(classical rule: closer to 0° of sign)"   ← THIS LABEL IS FALSE
```

- The "closer to 0° of the sign wins" claim is **not** attested in any classical graha-yuddha text I can
  find. It is a computational convenience.
- The JL-026 audit further found the (now-removed) ga_condition writer used the **opposite** proxy
  (higher longitude wins) — two contradictory uncited rules, one silently clobbering the other until R2.1.
- Under canonical-or-floor this proxy is **ineligible**: it cannot be ratified, only replaced or floored.

## 2. Option A — Northern-latitude rule (Parāśara / mainstream Jyotiṣa)  ◀ recommended if data available

**Rule.** Among the five tārā-grahas (Maṅgala, Budha, Guru, Śukra, Śani — never Sun/Moon/Rāhu/Ketu), the
**victor is the planet further to the NORTH** (greater north celestial/ecliptic latitude). When both are
north, greater north latitude wins; when both south, the *less* southern wins; when split, the northern
one wins. **Śukra (Venus) is held to win regardless of direction**, by its exceptional brilliance.

**Source (substance verified; verse # to be confirmed §5):**
- *Bṛhat Parāśara Horā Śāstra* — graha-yuddha treatment: "Venus is the conqueror whether in North or
  South; among the other four the one in the North is the conqueror, that in the South is defeated."
  (JL-027 ledger cites "BPHS ch.3"; **chapter number varies by edition — FLAG for §5**.)
- *Bṛhat Saṃhitā* (Varāhamihira), **Grahayuddhādhyāya, ch. 17** — the northern/brighter planet is
  victor (jayin); the rough, discoloured, or southern planet is overcome.

**Computation cost (B.10).** Requires each graha's **ecliptic latitude** at the yuddha epoch — NOT in L1
today (L1 stores longitude/sign/house/dignity). → `[EXTERNAL_COMPUTATION_REQUIRED]` Swiss Ephemeris
latitude per graha at chart epoch; a new L1 latitude fact + a derivation-ledger entry. Deterministic,
re-derivable, no fabrication.

## 3. Option B — Brightness / disc rule (Sūrya Siddhānta, ch. 7)

**Rule.** In *apasavya* yuddha (planets within ~1°), "the planet that is obscure, small and gloomy is
conquered; the rough, discoloured or southern is overcome; **the conqueror is the planet whose disc is
brighter and larger, north or south**." Venus usually wins by brilliance.

**Source (substance verified; verse # to be confirmed §5):**
- *Sūrya Siddhānta* **ch. 7 (Grahayuddha / grahayuti)** — four yuddha types (Ullekha, Bheda,
  Aṃśuvimarda, Apasavya) and the brighter-larger-disc victor rule. (Burgess tr. places this ~VII.18–24;
  **exact verse numbers FLAG for §5**.)

**Computation cost (B.10).** Requires apparent **magnitude/angular-diameter** of each graha at epoch —
also not in L1, and heavier than latitude (needs a brightness/phase model). More faithful to the
astronomical origin but more external machinery. → `[EXTERNAL_COMPUTATION_REQUIRED]`, larger than A.

## 4. Option C — FLOOR (default if A/B not ratified+computable by W2 close)

Per canonical-or-floor and the brief's guardrail: set **`winner = NULL`, `loser = NULL`,
`reason = 'no_ratified_classical_rule'`** on all `graha_yuddha` winner/loser rows (keep `orb_deg` — it is
a true computed fact). `judgment_flags` marks graha_yuddha **provisional / non-load-bearing**. The native
chart at W4 then never consumes an uncited winner. This is the safe, honest default and is what W3/W4 will
carry unless the native ratifies A or B.

**Explicitly forbidden:** shipping the lower-longitude (or higher-longitude) proxy as if it were a winner.

## 5. Verification owed before any citation enters a derivation ledger

Before Option A or B is *implemented* (not merely ruled), confirm against a critical edition:
- BPHS: exact chapter/verse of the graha-yuddha winner śloka (the ledger's "ch.3" is unverified).
- Bṛhat Saṃhitā ch. 17: the jayin/parājita verse numbers.
- Sūrya Siddhānta ch. 7: the apasavya + brighter-disc verse numbers (Burgess numbering).
Uncited-but-substantively-known is fine for *surfacing this decision*; it is NOT fine for a shipped
`DERIVATION_LEDGER` entry (B.3).

## 6. Recommendation

1. **Ratify Option A (northern-latitude)** — it is the mainstream Parāśari rule and the project is
   Parāśara-based; it is the lightest external computation (one latitude fact).
2. Gate its *implementation* on: (a) §5 citation verified, (b) Swiss Ephemeris latitude computed + stored
   as an L1 fact with a derivation ledger. If both land before W2 close → implement for W3/W4.
3. If either is not ready by W2 close → **ship Option C (FLOOR)**. Do not slip W3 waiting on ephemeris
   plumbing; the floor is a correct, honest state and JL-027 still CLOSES (ruled = "A, floored pending
   data").

## 7. Sources (secondary/translation — for substance, not ledger-final verse numbers)
- Bṛhat Saṃhitā ch. 17 (grahayuddha), wisdomlib (fetch blocked 403 this session; listed for §5).
- "Judging the Effects of Graha Yuddha", pdfcoffee / Scribd (Surya Siddhānta yuddha types + victor rule).
- indianastrologysoftware.com — Samaagama / Graha Yuddha (northern-latitude winner rule).
- vedicastrology.wikidot.com — Planetary War (tārā-graha eligibility; Venus-always-wins).
- Ernst Wilhelm, *Planetary War* (astrology-videos.com) — latitude-based winner exposition.
