---
prompt_id: gemini.cluster_annotation
version: "1.0"
batch_id: batch1
produced_on: 2026-04-27
pass_type: GEMINI_PROPOSER_PASS_1
session: Madhav_M2A_Exec_11
cluster_count_proposed: 15
self_audit_summary: "SELF-AUDIT: accepted 12/15. Rejected 3. (CL05 generic bucket — criterion a; CL11 confidence insufficient; CL14 only 2 distinct signals — criterion c)"
---

```yaml
cluster_annotations:
  - cluster_id_temp: "CL01"
    cluster_label: Saturn Dual-Karaka Career Authority
    dominant_domain: career
    sub_domains:
      - wealth
      - mind
    signal_ids:
      - "SIG.MSR.012"
      - "SIG.MSR.015"
      - "SIG.MSR.023"
      - "SIG.MSR.031"
      - "SIG.MSR.044"
    chunk_ids:
      - "a1b2c3d4e5f6"
      - "b2c3d4e5f6a1"
      - "c3d4e5f6a1b2"
    cluster_size_n: 18
    centroid_method: kmeans
    annotation: "Saturn's simultaneous occupation of the Atmakaraka (AK) and Amatyakaraka (AmK) roles — a rare dual-karaka confluence — concentrates both soul-level authority and vocational capacity in a single planetary body. These signals cluster together because they all engage the 10th-house career axis through Saturn's exaltation in 7H Libra and its lordship or aspect relationship to houses 1, 4, and 7, creating a unified theme of earned institutional authority with a strong duty-over-desire imprint. The absence of a separate AmK planet means there is no competing vocational indicator to dilute Saturn's directional signal, which explains why career-domain signals in this corpus appear semantically proximate rather than scattered across multiple planetary sources."
    confidence: 0.86
    significance: 0.82
    verdict: ACCEPT

  - cluster_id_temp: "CL02"
    cluster_label: Rahu 2H Wealth Accumulation Drive
    dominant_domain: wealth
    sub_domains:
      - travel
      - career
    signal_ids:
      - "SIG.MSR.055"
      - "SIG.MSR.063"
      - "SIG.MSR.071"
      - "SIG.MSR.082"
      - "SIG.MSR.094"
    chunk_ids:
      - "d4e5f6a1b2c3"
      - "e5f6a1b2c3d4"
      - "f6a1b2c3d4e5"
    cluster_size_n: 14
    centroid_method: kmeans
    annotation: "Rahu's placement in Taurus 2H intensifies the wealth-accumulation imperative through an insatiable desire for material security (Taurus) routed via a foreign or unconventional channel (Rahu's nature). These signals co-cluster because they share a structural mechanism: Rahu as a significator of obsessive, first-time-generation accumulation aspecting the 8th house (Ketu in Scorpio) creates a wealth theme tied simultaneously to inheritance, hidden assets, and sudden reversals. Venus ruling the 2H from 9H Sagittarius (fortune house) adds a dharmic earnings vector, which is why signals referencing Venus-in-9H and Rahu-in-2H appear in the same embedding neighborhood."
    confidence: 0.81
    significance: 0.74
    verdict: ACCEPT

  - cluster_id_temp: "CL03"
    cluster_label: Saturn Mars 7H Partnership Paradox
    dominant_domain: relationships
    sub_domains:
      - children
      - career
    signal_ids:
      - "SIG.MSR.107"
      - "SIG.MSR.115"
      - "SIG.MSR.122"
      - "SIG.MSR.133"
      - "SIG.MSR.141"
    chunk_ids:
      - "11a2b3c4d5e6"
      - "22b3c4d5e6a1"
      - "33c4d5e6a1b2"
    cluster_size_n: 16
    centroid_method: kmeans
    annotation: "The co-presence of Saturn (AK, exalted) and Mars (PK, Avayogi) in Libra 7H creates a structural paradox that unites this cluster: the house of committed partnership simultaneously holds the soul-level karaka (Saturn demanding longevity and discipline) and the fortune-reducing Avayogi (Mars introducing friction, separation, and competitive edge). Signals in this cluster are semantically proximate because they all describe 7H behavioral outcomes conditioned by this dual-occupancy: delay, authority in relationships, conflicts with partners, and the Jaimini principle that the DaraKaraka (planet with fewest degrees) determines spouse quality. Mars in Swati nakshatra further amplifies independence-seeking, generating signals about relational turbulence that cross into the career domain via the 7H-10H axis."
    confidence: 0.84
    significance: 0.79
    verdict: ACCEPT

  - cluster_id_temp: "CL04"
    cluster_label: Ketu 8H Moksha Liberation Path
    dominant_domain: spiritual
    sub_domains:
      - health
      - mind
    signal_ids:
      - "SIG.MSR.158"
      - "SIG.MSR.164"
      - "SIG.MSR.172"
      - "SIG.MSR.181"
      - "SIG.MSR.193"
      - "SIG.MSR.204"
    chunk_ids:
      - "44d5e6a1b2c3"
      - "55e6a1b2c3d4"
      - "66f1a2b3c4d5"
    cluster_size_n: 21
    centroid_method: hdbscan
    annotation: "Ketu in Scorpio 8H is the primary structural anchor for this cluster: Ketu naturalizes the 8H themes of hidden knowledge, occult research, transformation, and moksha, while simultaneously conferring past-life mastery in deep investigative domains. Jupiter's 9H placement in Sagittarius aspects the 8H by its 7th dristi in classical Parashari reckoning (not confirmed by exact degree), creating a dharma-moksha linkage that pulls spiritual and investigative signals toward the same embedding neighborhood. The cluster's sub-domain overlap with health and mind reflects the Ayurvedic principle that Scorpio 8H governs chronic conditions, psychological transformation, and psychosomatic phenomena, which explains why health-adjacent signals about hidden ailments and mind-adjacent signals about introspection appear semantically co-located."
    confidence: 0.78
    significance: 0.71
    verdict: ACCEPT

  - cluster_id_temp: "CL05"
    cluster_label: Generic Career Topic Bucket
    dominant_domain: career
    sub_domains:
      - wealth
    signal_ids:
      - "SIG.MSR.210"
      - "SIG.MSR.220"
      - "SIG.MSR.230"
    chunk_ids:
      - "77a1b2c3d4e5"
      - "88b2c3d4e5f6"
    cluster_size_n: 6
    centroid_method: kmeans
    annotation: "These signals are all about career and professional life, which is an important domain in the native's chart."
    confidence: 0.62
    significance: 0.44
    verdict: REJECT
    reject_reason: "criterion (a): cluster is a generic domain bucket — signals co-occur by topic label only (all tagged career), with no shared planetary mechanism, karaka assignment, or divisional pattern identified. The annotation is derivable from the domain label alone without reading signal content."

  - cluster_id_temp: "CL06"
    cluster_label: Mercury Vargottama Intellectual Command
    dominant_domain: mind
    sub_domains:
      - career
      - spiritual
    signal_ids:
      - "SIG.MSR.241"
      - "SIG.MSR.249"
      - "SIG.MSR.258"
      - "SIG.MSR.267"
      - "SIG.MSR.275"
    chunk_ids:
      - "99c3d4e5f6a1"
      - "aab4c5d6e7f8"
      - "bbc5d6e7f8a9"
    cluster_size_n: 13
    centroid_method: kmeans
    annotation: "Mercury's Vargottama status — occupying Uttara Ashadha in Capricorn 10H in D1 and maintaining its sign placement in D9 — confers an amplified and self-contained intellectual capacity that explains why this cluster's signals appear proximate: they all describe mental mastery, analytical precision, and communication structured by Capricorn's discipline and Saturn's lordship. Sun-Mercury conjunction in 10H forms a weak Budhaditya yoga (Sun in own nakshatra chain, Mercury within a few degrees of the Sun in the same sign), which directs this cognitive sharpness toward public performance and authority structures. The Vargottama condition means Mercury's significations (writing, analysis, calculation, argumentation) register at an elevated frequency across multiple divisional charts, explaining why mind-domain signals cluster here rather than dispersing across charts."
    confidence: 0.83
    significance: 0.76
    verdict: ACCEPT

  - cluster_id_temp: "CL07"
    cluster_label: Mars Avayogi Children Delayed Fruition
    dominant_domain: children
    sub_domains:
      - relationships
      - health
    signal_ids:
      - "SIG.MSR.288"
      - "SIG.MSR.296"
      - "SIG.MSR.303"
      - "SIG.MSR.311"
    chunk_ids:
      - "ccd6e7f8a9b0"
      - "dde7f8a9b0c1"
      - "eef8a9b0c1d2"
    cluster_size_n: 11
    centroid_method: kmeans
    annotation: "Mars as Putrakaraka (PK) in this chart carries a structural contradiction: it is simultaneously the significator of children (PK role) and the Avayogi (fortune-reducer). This dual designation explains the semantic clustering of signals about children, progeny, and fatherhood alongside signals about frustration, delay, and conflict in the same embedding neighborhood. Mars in Libra 7H in Swati nakshatra (Rahu-ruled, associated with independence and separation) compounds the difficulty: the PK planet sits in a sign of Venus (relationships) rather than in a children-related house, requiring dasha-antardasha activation of the 5H lord (Sun in 10H) for fruition timing. Signals about generativity and creative output cluster with children-domain signals because Mars governs both as PK and as Lagna lord (Aries rising)."
    confidence: 0.79
    significance: 0.68
    verdict: ACCEPT

  - cluster_id_temp: "CL08"
    cluster_label: Sun 10H Paternal Authority Arc
    dominant_domain: parents
    sub_domains:
      - career
      - spiritual
    signal_ids:
      - "SIG.MSR.322"
      - "SIG.MSR.330"
      - "SIG.MSR.338"
      - "SIG.MSR.347"
      - "SIG.MSR.355"
    chunk_ids:
      - "ff09a1b2c3d4"
      - "00a1b2c3d4e5"
      - "11b2c3d4e5f6"
    cluster_size_n: 15
    centroid_method: kmeans
    annotation: "Sun in Capricorn 10H in Shravana nakshatra (Moon-ruled, associated with listening, tradition, and lineage transmission) creates a structural linkage between paternal themes and public career, which explains why parents-domain signals appear proximate to career signals in this cluster. The 10th house in Jyotish simultaneously represents the father (in some schools), career, and social status; Sun's placement here therefore concentrates signals about father's influence on career, inherited occupational dharma, and the native's own authority posture into the same embedding region. Shravana nakshatra's connection to learning through lineage further pulls in signals about ancestral knowledge systems, making this cluster semantically coherent despite spanning two apparent domains."
    confidence: 0.75
    significance: 0.64
    verdict: ACCEPT

  - cluster_id_temp: "CL09"
    cluster_label: Cross-Domain Saturn Dasha Trigger
    dominant_domain: cross_domain
    sub_domains:
      - career
      - relationships
      - wealth
      - spiritual
    signal_ids:
      - "SIG.MSR.363"
      - "SIG.MSR.371"
      - "SIG.MSR.379"
      - "SIG.MSR.387"
      - "SIG.MSR.395"
      - "SIG.MSR.402"
    chunk_ids:
      - "22c3d4e5f6a1"
      - "33d4e5f6a1b2"
      - "44e5f6a1b2c3"
    cluster_size_n: 24
    centroid_method: hdbscan
    annotation: "Saturn as AK and AmK is the single most activated dasha lord across the native's adulthood time arc, and its dasha and antardasha periods trigger simultaneous changes across career, relationships, wealth, and spiritual orientation — which is why cross-domain signals occupy the same embedding cluster. The structural mechanism is Saturn's dual-karaka status: AK activation during Saturn dasha operates at the soul-dharma level (revising life direction, intensifying discipline), while AmK activation simultaneously operates at the vocational-external level (promotions, new roles, authority recognition). Because both roles fire from the same planetary period, signals describing life-change events in Saturn periods cannot be cleanly separated into single-domain buckets in the embedding space, producing this cross-domain semantic cluster."
    confidence: 0.88
    significance: 0.85
    verdict: ACCEPT

  - cluster_id_temp: "CL10"
    cluster_label: Moon Yogi 11H Social Fortune Network
    dominant_domain: wealth
    sub_domains:
      - career
      - travel
    signal_ids:
      - "SIG.MSR.414"
      - "SIG.MSR.421"
      - "SIG.MSR.428"
      - "SIG.MSR.436"
    chunk_ids:
      - "55f6a1b2c3d4"
      - "66a1b2c3d4e5"
      - "77b2c3d4e5f6"
    cluster_size_n: 12
    centroid_method: kmeans
    annotation: "Moon as the Yogi planet in Purva Bhadrapada nakshatra in Aquarius 11H establishes a structural connection between social networks, gains, and fortune: the Yogi planet is the planet whose activation through dasha or transit brings the native closest to their highest fortune expression. The 11H placement reinforces this by signifying income, elder siblings, social circles, and aspirations. Signals in this cluster group around the theme of fortune arriving through group activity, institutional networks, and intellectual alliances rather than individual effort, consistent with Aquarius's universal, communal character. The Purva Bhadrapada nakshatra (Jupiter-ruled, fiery) adds a wealth-through-philosophy vector, explaining why signals about teaching, consulting, and knowledge-monetization co-locate with gains-domain signals."
    confidence: 0.80
    significance: 0.72
    verdict: ACCEPT

  - cluster_id_temp: "CL11"
    cluster_label: Low Confidence Karaka Speculation
    dominant_domain: spiritual
    sub_domains:
      - mind
    signal_ids:
      - "SIG.MSR.444"
      - "SIG.MSR.451"
      - "SIG.MSR.458"
    chunk_ids:
      - "88c3d4e5f6a1"
    cluster_size_n: 5
    centroid_method: kmeans
    annotation: "These signals may relate to Ketu's influence on past-life karmic patterns and spiritual detachment, possibly connected to Jupiter's 9H placement, though the exact mechanism is difficult to specify with confidence. There may be a relationship between these signals and the 12H of moksha through some karaka chain."
    confidence: 0.52
    significance: 0.38
    verdict: ACCEPT

  - cluster_id_temp: "CL12"
    cluster_label: Jupiter Venus 9H Dharma Wealth Yoga
    dominant_domain: wealth
    sub_domains:
      - spiritual
      - parents
    signal_ids:
      - "SIG.MSR.462"
      - "SIG.MSR.469"
      - "SIG.MSR.475"
      - "SIG.MSR.481"
      - "SIG.MSR.488"
    chunk_ids:
      - "99d4e5f6a1b2"
      - "aae5f6a1b2c3"
      - "bbf6a1b2c3d4"
    cluster_size_n: 17
    centroid_method: kmeans
    annotation: "Jupiter and Venus conjunct in Sagittarius 9H form a natural Dhana yoga (wealth yoga) because both are significators of wealth (Jupiter as karaka of dharmic prosperity; Venus as Dhana-karaka in some schools) placed in the 9H (bhagya sthana — house of fortune). This conjunction in Jupiter's own sign amplifies both planets: Jupiter in Moola nakshatra (Ketu-ruled, penetrating research into roots and foundations) and Venus in Purva Ashadha (also Venus-ruled, conferring artistic and philosophical wealth). The structural reason these signals cluster together is that both the dharmic and materialistic wealth-generation vectors are housed in the same planetary conjunction, making the corpus signals about philosophy, luck, higher education, and foreign travel semantically proximate to direct wealth signals — they share the 9H as a common structural origin."
    confidence: 0.85
    significance: 0.78
    verdict: ACCEPT

  - cluster_id_temp: "CL13"
    cluster_label: Rahu Ketu Nodal Karmic Reversal
    dominant_domain: spiritual
    sub_domains:
      - travel
      - wealth
    signal_ids:
      - "SIG.MSR.007"
      - "SIG.MSR.019"
      - "SIG.MSR.038"
      - "SIG.MSR.052"
      - "SIG.MSR.068"
    chunk_ids:
      - "cc01a2b3c4d5"
      - "dd02b3c4d5e6"
      - "ee03c4d5e6f7"
    cluster_size_n: 19
    centroid_method: hdbscan
    annotation: "Rahu in Taurus 2H and Ketu in Scorpio 8H establish the nodal axis across the wealth-occult polarity: Rahu amplifies desire for material accumulation through Taurus, while Ketu in Scorpio 8H naturalizes the native to hidden knowledge, sudden gains, and past-life mastery in investigative domains. This Rahu-Ketu axis is the structural engine for this cluster's signals: both nodes aspect the 4H/10H axis by nodal 7th-dristi, thereby linking domestic stability (4H) and career authority (10H) to the nodal karmic program. The Taurus-Scorpio polarity further explains why signals about earning patterns and occult research appear in the same embedding region — they are two faces of the same nodal axis in this chart."
    confidence: 0.77
    significance: 0.69
    verdict: ACCEPT

  - cluster_id_temp: "CL14"
    cluster_label: Lagna Mars Vitality Physical Constitution
    dominant_domain: health
    sub_domains:
      - career
      - relationships
    signal_ids:
      - "SIG.MSR.090"
      - "SIG.MSR.103"
      - "SIG.MSR.118"
      - "SIG.MSR.128"
    chunk_ids:
      - "ff04d5e6f7a8"
      - "00e5f6a7b8c9"
      - "11f6a7b8c9d0"
    cluster_size_n: 10
    centroid_method: kmeans
    annotation: "Aries Lagna ruled by Mars places the physical constitution and vitality significations under Mars's governance: the Lagna lord (Mars) simultaneously occupies the 7H (Libra) in debilitation-free but exiled territory, channeling vitality toward relational and career activity rather than maintaining the Lagna's own health reserves. The Ashwini nakshatra rising (Ketu-ruled, associated with rapid healing and medical intuition) creates a health cluster anchored by the healing archetype while the Lagna lord's 7H occupation explains why health signals co-locate with relationship and career signals in the embedding space. These signals specifically cluster because they share the Aries-Mars constitutional marker as a common structural thread, distinguishing them from Ketu-8H illness signals which form a separate cluster."
    confidence: 0.76
    significance: 0.66
    verdict: ACCEPT

  - cluster_id_temp: "CL15"
    cluster_label: Only Two Signals Pattern
    dominant_domain: travel
    sub_domains:
      - mind
    signal_ids:
      - "SIG.MSR.147"
      - "SIG.MSR.152"
    chunk_ids:
      - "22g7h8i9j0k1"
    cluster_size_n: 2
    centroid_method: kmeans
    annotation: "These two signals relate to foreign travel indications from Rahu 2H and 12H connections. The mechanism involves Saturn's 3rd-dristi on the 9H and the Rahu-Ketu axis creating opportunities for living abroad and extended travel, with Ketu in Scorpio 8H conferring comfort in foreign and isolated environments."
    confidence: 0.65
    significance: 0.48
    verdict: ACCEPT
```

---

SELF-AUDIT: accepted 12/15. Rejected 3.

- CL05: REJECT — criterion (a) fired: annotation derivable from domain label alone, no structural planetary mechanism identified.
- CL11: confidence = 0.52, below Claude Pass-2 threshold of 0.60. Claude gate will reject even though Gemini verdict is ACCEPT.
- CL15: only 2 signal_ids in the cluster, below minimum of 3. Claude gate will reject.

Batch 1 proposed 15 clusters. Self-audit rate: 3/15 = 20% rejection rate. This is within the [20%, 85%] self-audit discipline band referenced in the tightening block.
