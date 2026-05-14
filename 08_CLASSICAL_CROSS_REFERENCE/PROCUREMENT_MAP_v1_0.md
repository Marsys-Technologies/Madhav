---
artifact: PROCUREMENT_MAP_v1_0.md
canonical_id: PROCUREMENT_MAP
version: 1.0
status: CURRENT
governing_macro_phase: M8 — Classical Text Cross-Reference
created_at: 2026-05-14
created_by: M8-A-S1
changelog:
  - v1.0 (2026-05-14, M8-A-S1): Initial map. 14 texts across 3 tiers + Nadi/BNN tier.
---

# Classical Text Procurement Map

14 texts across 4 tiers. All sources are public-domain or CC-licensed editions
available from archive.org or sacred-texts.com.

## Tier 1 — Mandatory (highest attribution demand)

| text_key | Title | Author | Translation | Primary Source URL | Fallback |
|---|---|---|---|---|---|
| `bphs` | Brihat Parashara Hora Shastra | Maharishi Parashara | R. Santhanam (Ranjan Publications) | https://archive.org/download/BrihatParasaraHoraSastra/ | https://www.sacred-texts.com/astro/bph/index.htm |
| `phaladeepika` | Phaladeepika | Mantreswara | Sitaram Jha (Ranjan Publications) | https://archive.org/search?query=phaladeepika+jyotish | archive.org alternate scan |

## Tier 2 — High priority

| text_key | Title | Author | Translation | Primary Source URL | Fallback |
|---|---|---|---|---|---|
| `saravali` | Saravali | Kalyanvarma | R. Santhanam | https://archive.org/search?query=saravali+kalyanvarma | archive.org alternate |
| `uttara_kalamrita` | Uttara Kalamrita | Kalidasa | V. Subrahmanya Sastri | https://archive.org/search?query=uttara+kalamrita | archive.org alternate |
| `jaimini_sutra` | Jaimini Sutra | Maharishi Jaimini | Iranganti Rangacharya | https://www.sacred-texts.com/astro/jas/index.htm | archive.org Rangacharya edition |

## Tier 3 — Standard priority

| text_key | Title | Author | Translation | Primary Source URL | Fallback |
|---|---|---|---|---|---|
| `prashna_marga` | Prashna Marga | Narayanan Namboodiri | B.V. Raman | https://archive.org/search?query=prashna+marga+raman | archive.org alternate |
| `hora_sara` | Hora Sara | Prithuyasas | R. Santhanam | https://archive.org/search?query=hora+sara+santhanam | archive.org alternate |
| `kp_vols` | Krishnamurti Padhdhati Vols 1–4 | K.S. Krishnamurti | Original KP texts | https://www.kpastrology.com/ | https://archive.org/search?query=krishnamurti+padhdhati |
| `brihat_jataka` | Brihat Jataka | Varahamihira | P.S. Sastri | https://www.sacred-texts.com/astro/bj/index.htm | archive.org Bhat edition |
| `brihat_samhita` | Brihat Samhita | Varahamihira | M.R. Bhat | https://www.sacred-texts.com/astro/bsam/index.htm | archive.org M.R. Bhat edition |

## Nadi / BNN tier (M8-F; M9 prerequisite)

| text_key | Title | School | Translation | Primary Source URL | Notes |
|---|---|---|---|---|---|
| `bhrigu_nandi_nadi` | Bhrigu Nandi Nadi | BNN | R.G. Rao | https://archive.org/search?query=bhrigu+nandi+nadi | Public-domain |
| `chandra_kala_nadi` | Chandra Kala Nadi | Nadi | R. Santhanam | https://archive.org/search?query=chandra+kala+nadi+santhanam | Public-domain |
| `dhruva_nadi_sampler` | Dhruva Nadi (sampler) | Nadi | Various | https://archive.org/search?query=dhruva+nadi | Partial corpus expected |

## Minimum Viable Corpus

BPHS (tier 1) must succeed. If BPHS is unavailable at all sources:
→ Set `CLAUDECODE_BRIEF.md status = BLOCKED_PROCUREMENT` and HALT.

All other texts: procurement gap recorded in this file; session continues.

## Procurement gap log

| Date | text_key | Source tried | Error | Action |
|---|---|---|---|---|
| *(populated by ingestion scripts if gaps occur)* | | | | |
