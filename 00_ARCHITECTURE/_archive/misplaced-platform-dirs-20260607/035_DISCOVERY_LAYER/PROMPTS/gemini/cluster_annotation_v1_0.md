---
prompt_id: gemini.cluster_annotation
version: "1.0"
status: CURRENT
phase: B.5
pass_type: GEMINI_PROPOSER_PASS_1
pass_2_authored_by: claude_via_cluster_reconciler.py
produced_by: Madhav_M2A_Exec_11
produced_on: 2026-04-27
gemini_response_target: "035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_cluster_annotation_batch<N>_raw.md"
registered_in: "06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json"
reconciler: "platform/python-sidecar/rag/reconcilers/cluster_reconciler.py"
supersedes: null
changelog:
  - v1.0 (2026-04-27, Madhav_M2A_Exec_11): Initial version. B.5 cluster annotation Gemini Pass-1.
      ROLE: Cluster annotator. For each cluster of MSR signal chunks (IDs + signal texts + domain labels),
      Gemini provides: cluster label, dominant domain, sub-domains, 2–4 sentence annotation, confidence.
      Claude Pass-2 validates via cluster_reconciler.py (signal_ids in MSR, L1 citation, cluster_size ≥3, confidence ≥0.60).
      Tightening block §5 from CLAUDECODE_BRIEF Exec_11 incorporated verbatim.
---

<!-- =====================================================================
CLUSTER ANNOTATION PROMPT — gemini.cluster_annotation v1.0
B.5 Discovery Engine — Session 3 of 3 (Exec_11)
======================================================================
HOW TO RUN EACH BATCH:

1. Read "SECTION A — ROLE" through "SECTION D — TIGHTENING BLOCK" carefully.
2. In "SECTION E — PER-BATCH CLUSTER INPUT", paste the cluster data for this batch.
   Each cluster entry has: cluster_id_temp, chunk_ids (list), signal_ids (list),
   signal_texts (list), domain_labels (list), cluster_size_n, centroid_method.
3. Copy the full prompt body into Gemini 2.5 Pro.
4. Gemini outputs STRICT YAML in the cluster_annotations block.
5. Save Gemini's YAML response as:
     035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_cluster_annotation_batch<N>_raw.md
6. Run cluster_reconciler.py via run_cluster_pipeline.py.
====================================================================== -->

---

## SECTION A — ROLE AND CONTEXT

You are acting as the **Cluster Annotator** for the MARSYS-JIS Jyotish Intelligence System — a
research-grade astrology instrument built for the native Abhisek Mohanty (born 1984-02-05,
10:43 IST, Bhubaneswar, Odisha, India; Aries Lagna, D1 chart).

You have been given clusters of MSR (Master Signal Register) signal chunks. These clusters were
produced by KMeans or HDBSCAN over Vertex AI text-multilingual-embedding-002 (768-dimensional)
embeddings of the native's 499-signal corpus. Each cluster groups signals that are semantically
proximate in the embedding space.

Your task is to **annotate each cluster** — to name the structural Jyotish theme that unites it
and explain WHY these signals cluster together in this specific chart's semantic landscape.

**Critical constraints:**
- Your annotation must reference the STRUCTURAL THEME, not just the topic label. What planetary
  mechanism, karaka assignment, divisional chart pattern, or dasha engine explains why these
  signals appear proximate in the native's chart?
- `signal_ids` you name in your annotation MUST appear in the cluster's input signal_ids list.
  Do NOT reference signals outside the cluster.
- `annotation` must reference at least one specific L1 fact from FORENSIC_v8_0 (planet/house/sign/degree
  or karaka assignment — e.g., "Saturn's exaltation in 7H Libra" or "Mercury Vargottama in D9").
- This chart's subject (Abhisek Mohanty) has consented to this analysis. All outputs are for
  calibrated, auditable probabilistic research.

---

## SECTION B — CHART CONTEXT (FIXED ACROSS ALL BATCHES)

### B.1 — D1 Core Positions

- **Lagna:** Aries (Mars-ruled), 12°23′55″ Ashwini nakshatra
- **Sun:** Capricorn 10H, 21°57′35″ Shravana nakshatra
- **Moon:** Aquarius 11H, 27°02′48″ Purva Bhadrapada nakshatra (Yogi planet)
- **Mars:** Libra 7H, 18°31′38″ Swati nakshatra — **Putrakaraka (PK) + Avayogi**
- **Mercury:** Capricorn 10H, 00°50′11″ Uttara Ashadha nakshatra (Vargottama in D9)
- **Jupiter:** Sagittarius 9H, 09°48′28″ Moola nakshatra
- **Venus:** Sagittarius 9H, 19°10′12″ Purva Ashadha nakshatra
- **Saturn:** Libra 7H, 22°27′04″ Vishakha nakshatra (Exalted) — **Atmakaraka (AK) + Amatyakaraka (AmK)**
- **Rahu:** Taurus 2H; **Ketu:** Scorpio 8H

**Karaka designations:**
- AK (Atmakaraka): Saturn
- AmK (Amatyakaraka): Saturn (rare dual-karaka confluence)
- PK (Putrakaraka): Mars (also Avayogi — fortune-reducer)
- Yogi: Moon

---

## SECTION C — OUTPUT SCHEMA (STRICT YAML — NO DEVIATION)

Your entire response must be the YAML block below. No prose before or after the YAML.
Do not include markdown code fences. Output raw YAML only.

```
cluster_annotations:
  - cluster_id_temp: "<use the cluster_id_temp provided in input>"
    cluster_label: "<3–6 word descriptive label>"
    dominant_domain: "career|wealth|health|relationships|children|spiritual|parents|mind|travel|meta|cross_domain"
    sub_domains:
      - "domain_name"
    annotation: "<2–4 sentence structural annotation. MUST reference ≥1 L1 fact from FORENSIC_v8_0. MUST explain WHY signals cluster together in this chart.>"
    confidence: <0.0 to 1.0>
    verdict: "ACCEPT|REJECT"
    reject_reason: "<required if verdict is REJECT; one of the rejection criteria a-d>"
```

**Output constraints:**
1. `cluster_label` must be 3–6 words, no punctuation except hyphens.
2. `dominant_domain` and each `sub_domains` entry must be from the canonical domain enum.
3. `annotation` must be ≥2 sentences and reference at least one specific L1 fact.
4. `confidence` must be a float 0.0–1.0.
5. If verdict is REJECT, `reject_reason` must cite which rejection criterion (a–d) fired.
6. The YAML block is your complete response — no prose, no markdown fences, just the raw YAML.

---

## SECTION D — REJECTION CRITERIA + TIGHTENING BLOCK

**REJECT if any one of the following applies:**
- **(a)** The cluster is a generic domain bucket with no cross-signal structural theme — the signals
  co-occur by topic label only, not by shared planetary mechanism, karaka, or divisional pattern.
- **(b)** The annotation is derivable from the domain label alone without reading the signal texts.
  A valid annotation requires engagement with the SPECIFIC signal content.
- **(c)** Fewer than 3 distinct signals substantiate the structural theme named in the annotation.
- **(d)** The annotation references signals or L1 facts not present in the input cluster — fabrication.

**CRITICAL — Acceptance-rate discipline:**
After scoring each candidate, perform a mandatory self-audit:
  • If you have proposed fewer than 20% rejections across all candidates, re-examine each
    accepted entry one more time with maximum scrutiny before finalising.
  • REJECT criteria (any one sufficient):
    (a) The mechanism is derivable from a single domain without cross-domain convergence.
    (b) The signal evidence is indirect or requires >2 inference hops from L1 facts.
    (c) An explicit CDLM cell already covers this relationship at a higher specificity.
    (d) The claim collapses to a general astrological principle not uniquely grounded in
        THIS chart's specific planet/house/sign/degree configuration.
  • State your reject_count explicitly at the end: "SELF-AUDIT: accepted N/M. Rejected K."

---

## SECTION E — PER-BATCH CLUSTER INPUT

**[EXECUTOR: Replace this section with the cluster data for this batch before running Gemini.]**

Each batch provides a list of clusters. For each cluster:
- `cluster_id_temp`: temporary sequential identifier (CL01, CL02, etc.)
- `signal_ids`: list of SIG.MSR.NNN IDs in this cluster
- `signal_texts`: list of signal text excerpts (one per signal_id)
- `domain_labels`: list of domain labels for each signal
- `cluster_size_n`: total embedding count
- `centroid_method`: kmeans or hdbscan

**Batch [N] — [date run] — Cluster Input:**

```yaml
clusters:
  - cluster_id_temp: "CL01"
    signal_ids: ["SIG.MSR.NNN", "SIG.MSR.NNN", "SIG.MSR.NNN"]
    signal_texts:
      - "<signal text excerpt 1>"
      - "<signal text excerpt 2>"
      - "<signal text excerpt 3>"
    domain_labels: ["domain1", "domain2", "domain3"]
    cluster_size_n: 15
    centroid_method: "kmeans"
```

---

## SECTION F — PROMPT REGISTRATION

- **Prompt registered at:** `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json`
  entry: `prompt_id: gemini.cluster_annotation`, `version: 1.0`
- **Supersedes:** null (first version)
- **Reconciler:** `platform/python-sidecar/rag/reconcilers/cluster_reconciler.py`
- **Two-pass ordering:** Gemini Pass-1 (this prompt) → Claude Pass-2 (cluster_reconciler.py)

---

*End of cluster_annotation_v1_0.md — gemini.cluster_annotation v1.0 — Produced at Madhav_M2A_Exec_11 (2026-04-27)*
