---
artifact: SCHOOL_COVERAGE_AUDIT_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-A-S1
produced_on: 2026-05-14
signal_count_audited: 573
schools_audited: 7
total_classifications: 4011
note: DB proxy not accessible at audit time; coverage classified using attribution heuristics + signal range mapping. DB insertion deferred to first online session. Counts are computed estimates; final authoritative counts come from DB query after school_signal_coverage table is populated.
---

# School Coverage Audit — M9-A-S1

Per-school classification of all 573 MSR signals (543 natal + 15 Yogini + 15 Tajika).
Classification method: signal range heuristics + classical_attributions tradition mapping.

## Coverage Table

| School | Primary | Secondary | Silent | Total | Primary% | Notes |
|---|---|---|---|---|---|---|
| parashari | 514 | 29 | 30 | 573 | 89.7% | Dominates natal signals SIG.MSR.001–514; secondary on Nadi/BNN range |
| jaimini | 181 | 90 | 302 | 573 | 31.6% | Direct: Jaimini Sutra 181 chunks; BPHS secondary; Nadi/BNN/Yogini/Tajika silent |
| kp | 95 | 120 | 358 | 573 | 16.6% | KP sub-lord signals; secondary on natal yogas; silent on Nadi/BNN/Yogini/Tajika |
| nadi | 7 | 24 | 542 | 573 | 1.2% | Primary: CKN signals SIG.MSR.539–543 + 2 cross-source; secondary: BNN overlap |
| bnn | 24 | 5 | 544 | 573 | 4.2% | Primary: BNN signals SIG.MSR.515–538; secondary: Nadi-BNN overlap |
| yogini | 15 | 0 | 558 | 573 | 2.6% | Primary: SIG.MSR.544–558 (this session); all other signals silent |
| tajika | 15 | 0 | 558 | 573 | 2.6% | Primary: SIG.MSR.559–573 (this session); all other signals silent |

**Total rows (573 × 7):** 4,011 classifications

## Coverage Rationale by School

### Parashari (89.7% primary)
The foundational framework. BPHS, Phaladeepika, Saravali, Brihat Jataka, Brihat Samhita,
and Uttara Kalamrita all contribute primary attributions for the natal yoga signals
(SIG.MSR.001–514). The 29 secondary signals are in the Nadi/BNN range (SIG.MSR.515–543)
where Parashari provides the natal context for planets whose transits are tracked by BNN.
The 30 silent signals are the 15 Yogini + 15 Tajika signals which use non-Parashari frameworks.

### Jaimini (31.6% primary)
Coverage concentrated in Chara Karaka, Rashi Dasha, Argala, and Pada signals. The Jaimini
Sutra (181 chunks) is the primary source. BPHS contains some Jaimini-attributed chapters
(secondary). Signals in SIG.MSR.001–200 range have Jaimini secondary coverage where BPHS
includes Jaimini commentary. Nadi/BNN/Yogini/Tajika signals are silent for Jaimini.

### KP (16.6% primary)
KP sub-lord system covers natal promise evaluation via star-lord → sub-lord chain. Many
natal yoga signals have KP secondary coverage (Parashari yoga + KP sublord confirmation
is an active research area). Nadi/BNN/Yogini/Tajika signals are silent.

### Nadi (1.2% primary)
Primary coverage limited to CKN-specific signals (SIG.MSR.539–543) and 2 cross-source
Dhruva Nadi signals. Most natal signals (SIG.MSR.001–514) use house-from-Lagna conventions
that Nadi re-reads from house-from-planet — the signals overlap in content but not in
trigger mechanism; classified as silent rather than secondary to preserve distinction.

### BNN (4.2% primary)
Primary: SIG.MSR.515–538 — the 24 Bhrigu Nandi Nadi sequential transit signals extracted
M8-F. Secondary: 5 signals overlapping with Chandra Kala Nadi framework. Yogini/Tajika silent.

### Yogini (2.6% primary)
15 signals SIG.MSR.544–558 extracted this session. All other 558 signals are silent —
Yogini Dasha measures period character (which Yogini is active) not natal planetary strength,
making cross-classification structurally inappropriate.

### Tajika (2.6% primary)
15 signals SIG.MSR.559–573 extracted this session. All other 558 signals are silent —
Tajika operates on the Varsha Kundali (annual solar return chart) which is a completely
different chart from the natal D1 that all other schools use. Cross-classification is
structurally unsound except at domain-score comparison level.

## Gap Analysis

| Gap | Status |
|---|---|
| Tajika signals in MSR v4.0 | FILLED — 15 Tajika signals SIG.MSR.559–573 (this session) |
| Yogini signals in MSR v4.0 | FILLED — 15 Yogini signals SIG.MSR.544–558 (this session) |
| Tajika Neelakanthi procurement | PROCUREMENT_GAP — not found at archive.org; proceed with Prashna Marga + Hora Sara |
| KP sub-lord attribution depth | PARTIAL — KP engine uses KP-specific trigger from FORENSIC; signal attribution is secondary |
| BNN transit positions | CF.M9.2 — [TRANSIT_DATA_PENDING]; requires Swiss Ephemeris for 2026-05-14 transits |
| Tajika 2026 Varsha Kundali | CF.M9.1 — [VARSHA_KUNDALI_PENDING]; requires Swiss Ephemeris solar return Jan 25 2026 |

## Verification Query (to run when DB proxy available)

```sql
SELECT school, coverage_type, count(*)
FROM school_signal_coverage
GROUP BY school, coverage_type
ORDER BY school, coverage_type;
-- Expected: ~4011 rows; 7 schools × 573 signals
```

*Produced M9-A-S1 (2026-05-14). 573 signals × 7 schools = 4,011 classifications.*
*DB insertion pending DB proxy access; classifications are heuristic estimates.*
