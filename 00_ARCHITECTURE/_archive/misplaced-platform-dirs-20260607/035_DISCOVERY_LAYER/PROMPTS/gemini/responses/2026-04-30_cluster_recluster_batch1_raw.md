---
artifact: 2026-04-30_cluster_recluster_batch1_raw.md
session: M2_B3_CLUSTER_RECLUSTER
pass: 1
actor: gemini-web-2026-04-30
produced_at: 2026-04-30T10:00:00+00:00
purpose: Pass 1 Gemini proposal — initial 25-cluster proposal for MSR_v3_0 re-clustering
input_source: 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json (baseline), 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md (499 signals)
status: ACCEPTED (with Pass 2 revisions — see claude_response_ref)
---

# Pass 1 — Gemini Cluster Proposal (Raw)

## Input brief

Gemini was tasked with proposing a new cluster schema for the 499 MSR_v3_0 signals. The existing CLUSTER_ATLAS_v1_0 had 12 clusters housing approximately 170 signals (34% coverage). The target was:
- 25–35 clusters
- ≥80% coverage
- ≥5 signals per cluster
- ≤30 signals per cluster
- Every domain (career, wealth, spirit, relationships, mind, health, travel, children, parents) in ≥2 clusters as dominant or sub-domain
- Every planet (sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu) centered in ≥1 cluster
- centroid_method: semantic_thematic

## Gemini's Pass 1 Proposal (summary)

Gemini proposed 25 initial clusters organized around the following thematic axes:

**Career axis (7 clusters):**
- Saturn Dual-Karaka Career Authority (CLUS.001) — 20 signals
- Sun 10H Career-Density Stellium (CLUS.002) — 8 signals
- Raja Yoga Authority Combinations (CLUS.005) — 20 signals
- Divisional Chart Portfolio D3-D60 (CLUS.017) — 17 signals
- Arudha Pada Lagna System (CLUS.019) — 18 signals
- Vimshottari Dasha Timing Activations (CLUS.024) — 21 signals
- Transit Activation Register (CLUS.025) — 22 signals

**Intelligence axis (2 clusters):**
- Mercury Vargottama Operational Spine (CLUS.003) — 11 signals
- Saraswati-Budhaditya Intelligence Yoga Stack (CLUS.004) — 11 signals

**Wealth axis (3 clusters):**
- Rahu 2H Wealth Drive (CLUS.006) — 5 signals
- Jupiter-Venus Dharma-Lakshmi Engine (CLUS.007) — 14 signals
- Dhana Yoga Wealth Combinations (CLUS.008) — 7 signals

**Moksha/spirit axis (3 clusters):**
- Ketu 8H Moksha-Occult Mastery (CLUS.009) — 11 signals
- Moon AK Soul-Network Fortune (CLUS.010) — 5 signals
- 12H Foreign-Moksha Architecture (CLUS.011) — 11 signals

**Relationship axis (2 clusters):**
- Mars-Saturn 7H Iron Forge Partnership Paradox (CLUS.012) — 16 signals
- Venus Relationships & Aesthetic Dignity (CLUS.013) — 5 signals

**Jaimini super-cluster (1 cluster, OVERSIZED at initial proposal):**
- Jaimini System (43 signals) — flagged for splitting in Pass 2

**Nakshatra super-cluster (1 cluster, OVERSIZED at initial proposal):**
- Nakshatra Signatures (36 signals) — flagged for splitting in Pass 2

**Sensitive points super-cluster (1 cluster, OVERSIZED at initial proposal):**
- Sensitive Points (38 signals) — flagged for splitting in Pass 2

**Panchang+KP super-cluster (1 cluster, OVERSIZED at initial proposal):**
- Panchang + KP (41 signals) — flagged for splitting in Pass 2

**Convergence catch-all (1 cluster, OVERSIZED at initial proposal):**
- Convergence catch-all (31 signals) — flagged for splitting in Pass 2

**Remaining structural clusters:**
- D9 Navamsa Pattern Register (CLUS.018) — 22 signals
- Health Constitution & Sade Sati Transit (CLUS.020) — 17 signals
- Tajika Annual Chart Pattern Register (CLUS.027) — 13 signals
- Contradiction & Internal Tension Register (CLUS.028) — 11 signals
- Yoga Absence & Near-Miss Register (CLUS.029) — 10 signals

## Pass 1 constraint violations flagged for Pass 2

Gemini's Pass 1 identified the following violations for Claude Pass 2 review and resolution:

1. **CLUS.009 (Ketu) only 2 signals** — type-first routing captured most Ketu signals before content rules
2. **CLUS.012 (Mars-Saturn 7H) only 4 signals** — 'hidden raja yoga' substring was firing CLUS.005 before Mars-Saturn check
3. **CLUS.013 (Venus) only 4 signals** — Venus in spirit-primary signals was falling through to wrong cluster
4. **CLUS.022 (Parents) only 2 signals** — parent signals captured by type rules before content override
5. **Jaimini super-cluster (43 signals) too large** — needs split into karaka hierarchy + Rashi Drishti
6. **Nakshatra super-cluster (36 signals) too large** — needs split into individual signatures + lord chains
7. **Sensitive Points super-cluster (38 signals) too large** — needs split into Arudha Padas + Special Lagnas
8. **Panchang+KP super-cluster (41 signals) too large** — needs split into Panchang + KP separately
9. **Convergence catch-all (31 signals) too large** — needs split into CVG core + meta-convergence/statistics

**Domains not yet covered by ≥2 clusters at Pass 1:** children, parents (each had only 1 cluster)

**Planet centering gaps at Pass 1:** Venus (only 4 signals), Ketu (only 2 signals) — size below minimum

## Pass 1 → Pass 2 handoff

All violations above were handed to Claude Pass 2 for resolution. See `035_DISCOVERY_LAYER/PROMPTS/claude/responses/2026-04-30_cluster_recluster_pass2.md` for the reconciliation record.

Final accepted output: `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_1.json` (34 clusters, 495/499 signals, 99.2% coverage).
