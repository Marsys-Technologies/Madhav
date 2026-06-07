---
artifact: CGM_v9_0
document: CGM_v9_0
version: "9.1"
status: CURRENT
supersedes: "CGM_v2_0.md (archived to 99_ARCHIVE/CGM_v2_0.md)"
canonical_id: CGM
layer: L2.5
source: FORENSIC_v8_0 (canonical L1 basis for all position facts)
node_count: 284
edge_count_v2: 339
date: 2026-04-26
session: Madhav_M2A_Exec_5
purpose: >
  Chart Graph Model for Abhisek Mohanty (1984-02-05, 10:43 IST, Bhubaneswar).
  One YAML node block per chart entity. Parsed by rag/chunkers/cgm_node.py.
  Boundary regex: ^node_id:\s*(\S+)\s*$ (MULTILINE). Max 600 tokens per block.
  All position facts cite l1_source pointing to FORENSIC_v8_0 sections.
  KRK nodes carry karaka_system field (8-karaka canonical; 7-karaka alternative retained for PK only).
  DVS and YOG nodes include PLN.* references for P1 layer-separation compliance.
reconciled_edges_manifest: "035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json"
edge_count_reconciled: 22
changelog:
  - "9.1 (2026-05-10, VARGA-ETL-FULL-S1 D13): added 50 DVS nodes for D24/D30/D40/D45/D60
     (10 per varga = lagna + 9 planets), grounded in FORENSIC §3.10–§3.14. Added §6
     DIVISIONAL_TRANSITION edges: 9 edges per §3.15 CSI ledger from PLN.{PLANET} to
     DVS.D9.{PLANET}. node_count 234 → 284. DVS breakdown updated. No prior node mutated."
  - "9.0 amended-in-place (2026-04-26, Madhav_M2A_Exec_6): manifest pointer added
     (reconciled_edges_manifest + edge_count_reconciled: 22); no node content changed; fingerprint rotates."
  - "9.0 (2026-04-26): Full rebuild on FORENSIC_v8_0. GAP.13 resolved: 8-karaka system canonical,
     7-karaka alternative retained on KRK.C7.PUTRA only. KRK count expanded from 16 to 18 (8 C8-Chara
     + 1 C7-alt + 9 Sthira). DVS count adjusted from 80 to 77. Special Lagnas corrected per §12.1
     (Hora→Gemini, Ghati→Sagittarius, Varnada→Cancer, Shree→Libra). All L1 citations verified
     against FORENSIC_v8_0. YOG.CYSS scores from FORENSIC §26."
  - "2.0 (prior): Archived to 99_ARCHIVE/CGM_v2_0.md."
expose_to_chat: true
native_id: "abhisek"
---

# CGM v9.0 — CHART GRAPH MODEL

## §1 Purpose and Structure

The Chart Graph Model (CGM) is the L2.5 Holistic Synthesis layer representation of the natal chart
as a typed, weighted graph. Each node below is a YAML block parsed by `cgm_node.py`. Edges are
computed separately and stored in the RAG vector store.

Node types:
- PLN: Planets (9) — D1 Rashi positions, canonical L1 data
- HSE: Houses (12) — Rashi + Bhavabala + SAV strength metrics
- SGN: Signs (12) — elemental/modal classification, lord pointer
- NAK: Occupied Nakshatras (15) — relevant stellar positions
- YOG: Yoga clusters (19) — verified by FORENSIC §26 + JH
- KRK: Chara + Sthira Karakas (18) — planet-role assignments
- DVS: Divisional chart positions (77) — key varga placements
- DSH: Dasha periods (30) — Vimshottari MD/AD, Yogini, Chara
- SEN: Sensitive points (42) — upagrahas, arudhas, special lagnas, sahams

P1 compliance: All L2.5 nodes must contain at least one entity reference ID matching the
pattern `\b(PLN|HSE|SGN|NAK|KRK|DSH|YGA|LAG|ARD|SAH|BVB|SBL|AVG)\.[A-Z0-9_.]+\b`.

## §3 Node Count Verification

| Type | Count |
|------|-------|
| PLN  | 9     |
| HSE  | 12    |
| SGN  | 12    |
| NAK  | 15    |
| YOG  | 19    |
| KRK  | 18    |
| DVS  | 127   |
| DSH  | 30    |
| SEN  | 42    |
| **TOTAL** | **284** |

DVS breakdown: D9×10 + D10×10 + D12×10 + D7×10 + D2×2 + D3×10 + D4×9 + D16×7 + D20×9 + D24×10 + D30×10 + D40×10 + D45×10 + D60×10 = 127 ✓ (v9.1 adds 50 nodes for D24/D30/D40/D45/D60)
DSH breakdown: VM-MD×9 + VM-AD(Mercury)×9 + Yogini×8 + Chara×4 = 30 ✓
SEN breakdown: UPG×9 + ARD×12 + LAG×8 + SAH×10 + MISC×3 = 42 ✓

## §4 Edge Inventory Reference

Edge data from CGM_v2_0 (339 edges, 15 types) is preserved and will be extended by
Gemini edge-proposal pass (B.3.5 Task 4). Edge types include:
DISP (9), GRAHA_ASPECT (27), BHAV_ASPECT (30), JAIMINI_ASPECT (36), OWNERSHIP (12),
TENANCY (9), EXALT_DEBIL_AFFINITY (18), NAK_LORDSHIP (14), KARAKA_ROLE (16),
YOGA_MEMBERSHIP (60), DASHA_ACTIVATION (30), DIVISIONAL_CONFIRMATION (15),
COMBUST_WAR (0), KAKSHYA_ZONE (8), SAHAM_COMPOSITION (55).

## §5 Key Structural Observations (L2.5 synthesis notes)

These observations are L2.5 notes — they reference node IDs, not raw L1 facts.

- **Mercury 8-system spine**: PLN.MERCURY is KRK.C8.DARA + KRK.STH.AMATYA + vargottama +
  YOG.POINT yogi-planet + DVS.D9.MERCURY kendra + YGA.BUDH_ADITYA + YGA.MERCURY_OPERATIONAL_SPINE.
  Eight independent system designations converge on PLN.MERCURY.
- **Saturn primary deliverer**: PLN.SATURN = KRK.C8.AMATYA + exalted H7 + Shadbala JH rank 1 +
  Ishta 9:1 + PVC POWERFUL. YGA.SATURN_QUADRUPLE encodes this. Also in YGA.SASHA_MPY.
- **Jupiter paradox** (CTR.03): PLN.JUPITER = own-sign H9 (dignified) + Phalita Kashta 48.81 (Phalita-weak).
  KRK.STH.PUTRA + KRK.C8.GNATI + DVS.D9.JUPITER in 12H stellium.
- **H7 structural weakness**: HSE.7 = weakest BVB.JH rank 12 but holds strongest planets
  (exalted Saturn, Mars). Structural paradox for relationship domain.
- **D9 12H stellium**: DVS.D9.MOON + DVS.D9.JUPITER + DVS.D9.RAHU all in D9 12H Gemini.
  Dispositor DVS.D9.MERCURY is vargottama in kendra. YGA.D9_12H_STELLIUM captures this.
- **Gemini H3 nexus**: HSE.3 holds SEN.LAG.HORA + SEN.ARD.UL + SEN.ARD.A11 +
  SEN.SAH.PUNYA + SEN.MISC.AVY_POINT (avayogi) — simultaneous fortune and avayogi pointer.

## §2 Node Catalog

The 234 node blocks follow. Each block begins with a bare `node_id:` line (parsed as block
boundary). All prose sections above do not contain bare `node_id:` lines.

---

node_id: PLN.SUN
node_type: PLN
node_label: Sun
sign: Capricorn
degree: "21°57′35″"
house_rashi: 10
house_chalit: 11
nakshatra: Shravana
pada: 4
abs_long: 291.96
shadbala_jh_rupas: 8.18
shadbala_jh_rank: 2
ikp_net: slightly_malefic
sthira_karaka: ATMA
sthira_karaka_alt: PITRI
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.MOON
node_type: PLN
node_label: Moon
sign: Aquarius
degree: "27°02′48″"
house_rashi: 11
house_chalit: 12
nakshatra: Purva_Bhadrapada
pada: 3
abs_long: 327.05
shadbala_jh_rupas: 6.44
shadbala_jh_rank: 4
ikp_net: slightly_malefic
chara_karaka_c8: ATMA
janma_nakshatra: true
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.MARS
node_type: PLN
node_label: Mars
sign: Libra
degree: "18°31′38″"
house_rashi: 7
house_chalit: 7
nakshatra: Swati
pada: 4
abs_long: 198.53
shadbala_jh_rupas: 5.34
shadbala_jh_rank: 6
ikp_net: slightly_beneficial
chara_karaka_c8: PITRU
chara_karaka_c7: PUTRA
sthira_karaka: BHRATRU
avayogi_planet: true
note: "Exalted sign lord. Co-tenant with PLN.SATURN in H7."
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.MERCURY
node_type: PLN
node_label: Mercury
sign: Capricorn
degree: "00°50′11″"
house_rashi: 10
house_chalit: 10
nakshatra: Uttara_Ashadha
pada: 2
abs_long: 270.84
shadbala_jh_rupas: 6.09
shadbala_jh_rank: 5
ikp_net: malefic
chara_karaka_c8: DARA
sthira_karaka: AMATYA
vargottama: true
yogi_planet: true
pvc_class: POWERFUL
note: "8-system convergence planet. Nearest-cusp planet to H10 cusp (2.14° inside)."
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.JUPITER
node_type: PLN
node_label: Jupiter
sign: Sagittarius
degree: "09°48′28″"
house_rashi: 9
house_chalit: 9
nakshatra: Moola
pada: 3
abs_long: 249.81
shadbala_jh_rupas: 7.68
shadbala_jh_rank: 3
ikp_net: phalita_weak
chara_karaka_c8: GNATI
sthira_karaka: PUTRA
pvc_class: POWERFUL
dignity: own_sign
note: "Own-sign H9. Phalita Kashta 48.81 (1:5 malefic). CTR.03 Jupiter paradox basis."
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.VENUS
node_type: PLN
node_label: Venus
sign: Sagittarius
degree: "19°10′12″"
house_rashi: 9
house_chalit: 9
nakshatra: Purva_Ashadha
pada: 2
abs_long: 259.17
shadbala_jh_rupas: 4.80
shadbala_jh_rank: 7
ikp_net: slightly_malefic
chara_karaka_c8: MATRU
sthira_karaka: DARA
sthira_karaka_alt: VAHANA
note: "Debilitated in D9 Virgo; NBR active via Mercury in D9 kendra."
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.SATURN
node_type: PLN
node_label: Saturn
sign: Libra
degree: "22°27′04″"
house_rashi: 7
house_chalit: 7
nakshatra: Vishakha
pada: 1
abs_long: 202.45
shadbala_jh_rupas: 8.79
shadbala_jh_rank: 1
ikp_net: "9:1_beneficial"
chara_karaka_c8: AMATYA
sthira_karaka: GNATI
pvc_class: POWERFUL
dignity: exalted
note: "Exalted AmK. Primary benefic deliverer. Co-tenant with PLN.MARS in H7."
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.RAHU
node_type: PLN
node_label: Rahu
sign: Taurus
degree: "19°01′47″"
house_rashi: 2
house_chalit: 2
nakshatra: Rohini
pada: 3
abs_long: 49.03
chara_karaka_c8: PUTRA
motion: retrograde
note: "Mean node. In 8-karaka system Rahu = C8.PUTRA. Excluded from 7-karaka system."
l1_source: "FORENSIC_v8_0 §2.1"

node_id: PLN.KETU
node_type: PLN
node_label: Ketu
sign: Scorpio
degree: "19°01′47″"
house_rashi: 8
house_chalit: 8
nakshatra: Jyeshtha
pada: 1
abs_long: 229.03
motion: retrograde
note: "Mean node. Axis with PLN.RAHU. H8 placement."
l1_source: "FORENSIC_v8_0 §2.1"

node_id: HSE.1
node_type: HSE
node_label: House 1 — Aries (Lagna)
sign: Aries
lord: PLN.MARS
tenants: []
sav: 29
bvb_jh_rupas: 7.00
bvb_jh_rank: 8
arudha: A10
note: "Empty lagna. A10 Arudha Lagna in Aries = H1."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.2
node_type: HSE
node_label: House 2 — Taurus
sign: Taurus
lord: PLN.VENUS
tenants: [PLN.RAHU]
sav: 29
bvb_jh_rupas: 4.83
bvb_jh_rank: 11
arudha_markers: [A6]
note: "Rahu H2. A6 (enemy arudha) co-located with Rahu."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.3
node_type: HSE
node_label: House 3 — Gemini
sign: Gemini
lord: PLN.MERCURY
tenants: []
sav: 28
bvb_jh_rupas: 7.83
bvb_jh_rank: 6
arudha_markers: [A11, UL]
note: "Hora Lagna in Gemini (LAG.HORA). A11 and UL (Upapada) in Gemini."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.4
node_type: HSE
node_label: House 4 — Cancer
sign: Cancer
lord: PLN.MOON
tenants: []
sav: 32
bvb_jh_rupas: 8.80
bvb_jh_rank: 5
arudha_markers: [A2]
note: "Empty H4. Varnada Lagna in Cancer (LAG.VARNADA). A2 in Cancer."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.5
node_type: HSE
node_label: House 5 — Leo
sign: Leo
lord: PLN.SUN
tenants: []
sav: 30
bvb_jh_rupas: 9.64
bvb_jh_rank: 1
note: "Strongest house by JH Bhavabala. Empty but architecturally powerful."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.6
node_type: HSE
node_label: House 6 — Virgo
sign: Virgo
lord: PLN.MERCURY
tenants: []
sav: 26
bvb_jh_rupas: 6.61
bvb_jh_rank: 9
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.7
node_type: HSE
node_label: House 7 — Libra
sign: Libra
lord: PLN.VENUS
tenants: [PLN.SATURN, PLN.MARS]
sav: 33
bvb_jh_rupas: 4.73
bvb_jh_rank: 12
note: "Weakest house by JH Bhavabala. Saturn exalted + Mars conjunction. ATT architecture."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.8
node_type: HSE
node_label: House 8 — Scorpio
sign: Scorpio
lord: PLN.MARS
tenants: [PLN.KETU]
sav: 33
bvb_jh_rupas: 6.06
bvb_jh_rank: 10
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.9
node_type: HSE
node_label: House 9 — Sagittarius
sign: Sagittarius
lord: PLN.JUPITER
tenants: [PLN.JUPITER, PLN.VENUS]
sav: 25
bvb_jh_rupas: 7.77
bvb_jh_rank: 7
note: "Jupiter in own sign H9. Ghati Lagna in Sag (LAG.GHATI)."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.10
node_type: HSE
node_label: House 10 — Capricorn
sign: Capricorn
lord: PLN.SATURN
tenants: [PLN.SUN, PLN.MERCURY]
sav: 26
bvb_jh_rupas: 9.39
bvb_jh_rank: 3
arudha_markers: [AL]
note: "AL (Arudha Lagna) in Capricorn H10. Sun+Mercury stellium."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.11
node_type: HSE
node_label: House 11 — Aquarius
sign: Aquarius
lord: PLN.SATURN
tenants: [PLN.MOON]
sav: 23
bvb_jh_rupas: 9.60
bvb_jh_rank: 2
arudha_markers: [A7]
note: "AK Moon in H11 (Rashi). A7 partner-arudha co-located with Moon."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: HSE.12
node_type: HSE
node_label: House 12 — Pisces
sign: Pisces
lord: PLN.JUPITER
tenants: []
sav: 23
bvb_jh_rupas: 9.28
bvb_jh_rank: 4
note: "Empty H12. Bhava Lagna in Pisces H12 (LAG.BHAVA)."
l1_source: "FORENSIC_v8_0 §2.2 §6.6 §7.2"

node_id: SGN.ARIES
node_type: SGN
node_label: Aries
element: fire
quality: cardinal
lord: PLN.MARS
house: 1
sav: 29
exaltation: PLN.SUN
debilitation: PLN.SATURN
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.TAURUS
node_type: SGN
node_label: Taurus
element: earth
quality: fixed
lord: PLN.VENUS
house: 2
sav: 29
tenants: [PLN.RAHU]
exaltation: PLN.MOON
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.GEMINI
node_type: SGN
node_label: Gemini
element: air
quality: mutable
lord: PLN.MERCURY
house: 3
sav: 28
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.CANCER
node_type: SGN
node_label: Cancer
element: water
quality: cardinal
lord: PLN.MOON
house: 4
sav: 32
exaltation: PLN.JUPITER
debilitation: PLN.MARS
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.LEO
node_type: SGN
node_label: Leo
element: fire
quality: fixed
lord: PLN.SUN
house: 5
sav: 30
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.VIRGO
node_type: SGN
node_label: Virgo
element: earth
quality: mutable
lord: PLN.MERCURY
house: 6
sav: 26
exaltation: PLN.MERCURY
debilitation: PLN.VENUS
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.LIBRA
node_type: SGN
node_label: Libra
element: air
quality: cardinal
lord: PLN.VENUS
house: 7
sav: 33
tenants: [PLN.SATURN, PLN.MARS]
exaltation: PLN.SATURN
debilitation: PLN.SUN
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.SCORPIO
node_type: SGN
node_label: Scorpio
element: water
quality: fixed
lord: PLN.MARS
house: 8
sav: 33
tenants: [PLN.KETU]
debilitation: PLN.MOON
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.SAGITTARIUS
node_type: SGN
node_label: Sagittarius
element: fire
quality: mutable
lord: PLN.JUPITER
house: 9
sav: 25
tenants: [PLN.JUPITER, PLN.VENUS]
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.CAPRICORN
node_type: SGN
node_label: Capricorn
element: earth
quality: cardinal
lord: PLN.SATURN
house: 10
sav: 26
tenants: [PLN.SUN, PLN.MERCURY]
exaltation: PLN.MARS
debilitation: PLN.JUPITER
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.AQUARIUS
node_type: SGN
node_label: Aquarius
element: air
quality: fixed
lord: PLN.SATURN
house: 11
sav: 23
tenants: [PLN.MOON]
l1_source: "FORENSIC_v8_0 §2"

node_id: SGN.PISCES
node_type: SGN
node_label: Pisces
element: water
quality: mutable
lord: PLN.JUPITER
house: 12
sav: 23
exaltation: PLN.VENUS
debilitation: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §2"

node_id: NAK.ASHWINI
node_type: NAK
node_label: Ashwini
lord: PLN.KETU
sign: Aries
pada: 4
occupant: lagna
occupant_degree: "12°23′55″"
note: "Lagna falls in Ashwini P4. Navatara 4=Kshema from Janma."
l1_source: "FORENSIC_v8_0 §1.2 §14"

node_id: NAK.ROHINI
node_type: NAK
node_label: Rohini
lord: PLN.MOON
sign: Taurus
pada: 3
occupant: PLN.RAHU
occupant_degree: "19°01′47″"
note: "Rahu in Rohini P3. Navatara 7=Naidhana from Janma."
l1_source: "FORENSIC_v8_0 §2.1 §14"

node_id: NAK.MRIGASHIRA
node_type: NAK
node_label: Mrigashira
lord: PLN.MARS
sign: Gemini
pada: 3
occupant: LAG.HORA
occupant_detail: "Hora Lagna Gemini 0°39′ (Mrigashira P3)"
upagraha: UPG.DHUMA
upagraha_detail: "Dhuma Gemini 5°17′ (Mrigashira P1)"
avayogi_nakshatra: true
note: "Hora Lagna + Dhuma in this nakshatra. Avayogi planet Mars is the lord."
l1_source: "FORENSIC_v8_0 §11.1 §12.1"

node_id: NAK.PUNARVASU
node_type: NAK
node_label: Punarvasu
lord: PLN.JUPITER
sign: Gemini
note: "SAH.BHRATRU at Gemini 29°46′ (Punarvasu P1). Jupiter lord connects to H9."
l1_source: "FORENSIC_v8_0 §12.2"

node_id: NAK.PURVA_PHALGUNI
node_type: NAK
node_label: Purva Phalguni
lord: PLN.VENUS
sign: Leo
pada: 3
occupant: LAG.VIGHATI
occupant_detail: "Vighati Lagna Leo 20°21′ (Purva Phalguni P3)"
alt_occupant: LAG.PRANAPADA
alt_detail: "Pranapada Leo 20°32′ (Purva Phalguni P3)"
l1_source: "FORENSIC_v8_0 §12.1"

node_id: NAK.UTTARA_PHALGUNI
node_type: NAK
node_label: Uttara Phalguni
lord: PLN.SUN
sign: Leo_Virgo
note: "SAH.LABHA at Virgo 2°23′ (Uttara Phalguni). Multiple Virgo arudhas (A4,A8,A9)."
l1_source: "FORENSIC_v8_0 §12.2 §13"

node_id: NAK.SWATI
node_type: NAK
node_label: Swati
lord: PLN.RAHU
sign: Libra
pada: 4
occupant: PLN.MARS
occupant_degree: "18°31′38″"
alt_occupant: SEN.MISC.BB_NATAL
alt_detail: "Bhrigu Bindu Libra 8°04′ (Swati P1)"
l1_source: "FORENSIC_v8_0 §2.1 §11.2"

node_id: NAK.VISHAKHA
node_type: NAK
node_label: Vishakha
lord: PLN.JUPITER
sign: Libra
pada: 1
occupant: PLN.SATURN
occupant_degree: "22°27′04″"
alt_occupant: LAG.SHREE
alt_detail: "Shree Lagna Libra 23°19′ (Vishakha P1)"
note: "Saturn exalted in Vishakha P1. Shree Lagna co-located."
l1_source: "FORENSIC_v8_0 §2.1 §12.1"

node_id: NAK.JYESHTHA
node_type: NAK
node_label: Jyeshtha
lord: PLN.MERCURY
sign: Scorpio
pada: 1
occupant: PLN.KETU
occupant_degree: "19°01′47″"
alt_occupant: LAG.INDU
alt_detail: "Indu Lagna Scorpio 27°04′ (Jyeshtha P4)"
l1_source: "FORENSIC_v8_0 §2.1 §12.1"

node_id: NAK.MOOLA
node_type: NAK
node_label: Moola
lord: PLN.KETU
sign: Sagittarius
pada: 3
occupant: PLN.JUPITER
occupant_degree: "09°48′28″"
l1_source: "FORENSIC_v8_0 §2.1"

node_id: NAK.PURVA_ASHADHA
node_type: NAK
node_label: Purva Ashadha
lord: PLN.VENUS
sign: Sagittarius
pada: 2
occupant: PLN.VENUS
occupant_degree: "19°10′12″"
alt_occupant: LAG.GHATI
alt_detail: "Ghati Lagna Sagittarius 13°56′ (Purva Ashadha P1)"
upagraha: UPG.UPAKETU
upagraha_detail: "Upaketu Sagittarius 21°57′ (Purva Ashadha P2)"
l1_source: "FORENSIC_v8_0 §2.1 §11.1 §12.1"

node_id: NAK.UTTARA_ASHADHA
node_type: NAK
node_label: Uttara Ashadha
lord: PLN.SUN
sign: Capricorn
pada: 2
occupant: PLN.MERCURY
occupant_degree: "00°50′11″"
note: "Mercury vargottama (Capricorn in both D1 and D9)."
l1_source: "FORENSIC_v8_0 §2.1 §3.5"

node_id: NAK.SHRAVANA
node_type: NAK
node_label: Shravana
lord: PLN.MOON
sign: Capricorn
pada: 4
occupant: PLN.SUN
occupant_degree: "21°57′35″"
l1_source: "FORENSIC_v8_0 §2.1"

node_id: NAK.PURVA_BHADRAPADA
node_type: NAK
node_label: Purva Bhadrapada
lord: PLN.JUPITER
sign: Aquarius
pada: 3
occupant: PLN.MOON
occupant_degree: "27°02′48″"
janma_nakshatra: true
navatara_type: Janma
l1_source: "FORENSIC_v8_0 §2.1 §14"

node_id: NAK.PUSHYA
node_type: NAK
node_label: Pushya
lord: PLN.SATURN
sign: Cancer
pada: 3
occupant: LAG.VARNADA
occupant_detail: "Varnada Lagna Cancer 12°25′ (Pushya P3)"
alt_occupant: LAG.BHAVA
alt_detail_2: "Bhava Lagna Pisces 26°13′ Revati — not this nak but Varnada here"
note: "Varnada Lagna in Pushya. Multiple Cancer sahams cluster here."
l1_source: "FORENSIC_v8_0 §12.1 §12.2"

node_id: YGA.SASHA_MPY
node_type: YOG
node_label: Sasha Mahapurusha Yoga
yoga_class: Pancha_Mahapurusha
strength: verified_JH
members: [PLN.SATURN]
mechanism: "Saturn exalted in own/exaltation sign in kendra (H7 from Lagna)"
domain: character_status_longevity
cyss_note: "Pancha Mahapurusha — not scored in CYSS system"
l1_source: "FORENSIC_v8_0 §26"

node_id: YGA.SARASWATI
node_type: YOG
node_label: Saraswati Yoga
yoga_class: Named_compound
strength: verified_JH
members: [PLN.JUPITER, PLN.VENUS, PLN.MERCURY]
cyss: 91
mechanism: "Jupiter + Venus + Mercury in kendra/kona/2H; Mercury vargottama amplifies"
domain: intelligence_arts_learning
l1_source: "FORENSIC_v8_0 §26"

node_id: YGA.LAKSHMI
node_type: YOG
node_label: Lakshmi Yoga
yoga_class: Named_compound
strength: verified_JH
members: [PLN.VENUS, PLN.JUPITER]
cyss: 77
mechanism: "9L Venus strong + Lagna lord Mars dignified; Lakshmi domain"
domain: wealth_prosperity
l1_source: "FORENSIC_v8_0 §26"

node_id: YGA.HIDDEN_RAJA
node_type: YOG
node_label: Hidden Raja Yoga
yoga_class: Raja
strength: partial
members: [PLN.SATURN, PLN.JUPITER, PLN.MERCURY]
mechanism: "Trikona/kendra lord exchange and mutual support; not immediately obvious"
domain: power_authority_delayed
l1_source: "FORENSIC_v8_0 §26"

node_id: YGA.ANAPHA
node_type: YOG
node_label: Anapha Yoga
yoga_class: Chandra_yoga
strength: verified_JH
members: [PLN.SATURN]
mechanism: "Saturn in 12th from Moon (H7=12th from H11 Moon — Rashi count)"
domain: comforts_dignity_character
note: "Reinforces Saturn as primary deliverer from Moon's perspective."
l1_source: "FORENSIC_v8_0 §26"

node_id: YGA.BUDH_ADITYA
node_type: YOG
node_label: Budha-Aditya Yoga
yoga_class: Named_simple
strength: verified_JH
members: [PLN.MERCURY, PLN.SUN]
mechanism: "Mercury and Sun conjunct in Capricorn H10; not combust (21° separation)"
domain: intelligence_skill_career
l1_source: "FORENSIC_v8_0 §26 §11.4"

node_id: YGA.NBRY_VENUS
node_type: YOG
node_label: Neecha Bhanga Raja Yoga — Venus
yoga_class: NBR
strength: active_D9
members: [PLN.VENUS, PLN.MERCURY]
mechanism: "Venus debilitated in D9 Virgo; Mercury (dispositor) in D9 kendra (Capricorn 7th from Cancer D9 Lagna)"
domain: marriage_refinement_cancelled_fall
l1_source: "FORENSIC_v8_0 §3.5.1"

node_id: YGA.NBRY_SATURN
node_type: YOG
node_label: Neecha Bhanga Raja Yoga — Saturn
yoga_class: NBR
strength: active_D9
members: [PLN.SATURN, PLN.SUN]
mechanism: "Saturn debilitated in D9 Aries; exaltation ruler Sun in Cancer (D9 Lagna kendra)"
domain: service_discipline_cancelled_fall
l1_source: "FORENSIC_v8_0 §3.5.1"

node_id: YGA.D9_12H_STELLIUM
node_type: YOG
node_label: D9 12th House Stellium
yoga_class: Divisional_configuration
strength: verified
members: [PLN.MOON, PLN.JUPITER, PLN.RAHU]
mechanism: "Moon + Jupiter + Rahu in D9 12th (Gemini); dispositor Mercury vargottama in D9 kendra"
domain: foreign_spiritual_subconscious_pattern
l1_source: "FORENSIC_v8_0 §3.5.2"

node_id: YGA.GEMINI_3H_NEXUS
node_type: YOG
node_label: Gemini 3H Nexus
yoga_class: Multi_marker_cluster
strength: verified
members: [PLN.MERCURY]
cluster_items: [LAG.HORA, ARD.UL, ARD.A11, SAH.PUNYA]
mechanism: "Gemini H3: Hora Lagna + UL + A11 + Punya Saham all co-located; lord Mercury is Yogi planet"
domain: skills_effort_networks_fortune
l1_source: "FORENSIC_v8_0 §12.1 §12.2 §13"

node_id: YGA.MERCURY_OPERATIONAL_SPINE
node_type: YOG
node_label: Mercury Operational Spine
yoga_class: System_convergence
strength: verified
members: [PLN.MERCURY]
convergence_systems: [chara_dara, sthira_amatya, vargottama, yogi_planet, yoga_lord_panchang, budh_aditya, D9_kendra, pvc_powerful]
count: 8
mechanism: "Mercury = 8 independent system designations creating a dominant operational axis"
domain: intelligence_systems_instrument_delivery
l1_source: "FORENSIC_v8_0 §2.1 §3.5 §10.1 §10.3 §11.3 §15.1 §6.8"

node_id: YGA.JUPITER_9L_DHARMA_WEALTH
node_type: YOG
node_label: Jupiter 9L Dharma-Wealth Nexus
yoga_class: House_lord_strength
strength: verified
members: [PLN.JUPITER, PLN.VENUS]
mechanism: "Jupiter in own-sign H9 with Venus; 9L and 9H stellium creates Dharma-Wealth axis"
domain: dharma_fortune_knowledge_expansion
l1_source: "FORENSIC_v8_0 §2.1 §6.7"

node_id: YGA.MOON_AK_FOREIGN_CHAIN
node_type: YOG
node_label: Moon AK Foreign Chain
yoga_class: Karaka_house_linkage
strength: verified
members: [PLN.MOON, PLN.JUPITER]
mechanism: "Moon AK in H11 (Rashi) / H12 (Chalit); Jupiter rules H12 and is in H9; D9 12H stellium includes Moon; multiple foreign-domain indicators"
domain: foreign_residence_gains_moksha_path
l1_source: "FORENSIC_v8_0 §2.1 §3.5.2 §10.3"

node_id: YGA.10H_CAREER_DENSITY
node_type: YOG
node_label: 10H Career Density
yoga_class: Multi_occupant_kendra
strength: verified
members: [PLN.SUN, PLN.MERCURY]
mechanism: "Sun + Mercury in H10 Capricorn; AL in H10; KP significators for H10 include Mercury,Venus,Mars,Ketu,Sun,Saturn"
domain: career_public_status_authority
l1_source: "FORENSIC_v8_0 §2.1 §4.3 §13"

node_id: YGA.SATURN_QUADRUPLE
node_type: YOG
node_label: Saturn Quadruple Architecture
yoga_class: Planet_multi_role
strength: verified
members: [PLN.SATURN]
roles: [exalted_H7, AmK_chara, Shadbala_JH_rank1, Ishta_9to1, POWERFUL_PVC]
count: 5
mechanism: "Saturn holds 5 simultaneous high-strength designations; primary deliverer status"
domain: discipline_authority_longevity_delivery
l1_source: "FORENSIC_v8_0 §6.2 §6.7 §6.8 §10.3"

node_id: YGA.JUPITER_9H_NEAR_MPY
node_type: YOG
node_label: Jupiter 9H Near-Mahapurusha Pattern
yoga_class: Dignified_angular_approach
strength: partial
members: [PLN.JUPITER]
mechanism: "Jupiter in own-sign 9H (trikona, near-kendra); Hamsa MPY conditions partially met but H9 is not a kendra"
domain: wisdom_guru_dharma_near_royal
l1_source: "FORENSIC_v8_0 §2.1 §6.7"

node_id: YGA.ARIES_LIBRA_AXIS
node_type: YOG
node_label: Aries-Libra Axis Configuration
yoga_class: Opposition_axis
strength: verified
members: [PLN.MARS, PLN.SATURN]
mechanism: "Lagna=Aries (lord Mars in H7 Libra); Saturn exalted H7; A10 in Aries H1; mutual aspect Lagna-H7"
domain: self_vs_partner_axis_delayed_marriage_strength
l1_source: "FORENSIC_v8_0 §2.1 §13"

node_id: YGA.RAHU_JAIMINI_QUADRUPLE
node_type: YOG
node_label: Rahu Jaimini Quadruple
yoga_class: Jaimini_multi_indicator
strength: verified
members: [PLN.RAHU]
roles: [C8_PUTRA_8karaka, H2_Taurus, A6_co_location, Rohini_P3]
mechanism: "Rahu in H2 = Jaimini-powerful placement; multiple concurrent Jaimini indicators"
domain: foreign_material_accumulation_unusual_gains
l1_source: "FORENSIC_v8_0 §2.1 §10.3 §13"

node_id: YGA.TRIPLE_EXALTED_NODAL
node_type: YOG
node_label: Triple Exalted Nodal Configuration
yoga_class: Exaltation_cluster
strength: verified
members: [PLN.SATURN, PLN.RAHU, PLN.MARS]
mechanism: "Saturn exalted H7; Rahu in Taurus (exaltation sign for Rahu); Mars in Libra (exaltation sign for Saturn, lord of Mars's exaltation is Saturn)"
domain: multi_domain_strength_via_nodal_axis
l1_source: "FORENSIC_v8_0 §2.1"

node_id: KRK.C8.ATMA
node_type: KRK
node_label: Atmakaraka (8-karaka)
karaka_system: 8-karaka
karaka_role: ATMA
planet: PLN.MOON
degree_in_sign: "27°02′"
l1_source: "FORENSIC_v8_0 §10.1 §10.3"

node_id: KRK.C8.AMATYA
node_type: KRK
node_label: Amatya Karaka (8-karaka)
karaka_system: 8-karaka
karaka_role: AMATYA
planet: PLN.SATURN
degree_in_sign: "22°27′"
l1_source: "FORENSIC_v8_0 §10.1 §10.3"

node_id: KRK.C8.BHRATRU
node_type: KRK
node_label: Bhratru Karaka (8-karaka)
karaka_system: 8-karaka
karaka_role: BHRATRU
planet: PLN.SUN
degree_in_sign: "21°57′"
l1_source: "FORENSIC_v8_0 §10.1 §10.3"

node_id: KRK.C8.MATRU
node_type: KRK
node_label: Matru Karaka (8-karaka)
karaka_system: 8-karaka
karaka_role: MATRU
planet: PLN.VENUS
degree_in_sign: "19°10′"
l1_source: "FORENSIC_v8_0 §10.1 §10.3"

node_id: KRK.C8.PUTRA
node_type: KRK
node_label: Putra Karaka (8-karaka)
karaka_system: 8-karaka
karaka_role: PUTRA
planet: PLN.RAHU
degree_in_sign: "19°01′"
note: "Rahu included in 8-karaka; displaces Mars from PK. GAP.13 resolved."
l1_source: "FORENSIC_v8_0 §10.3"

node_id: KRK.C8.PITRU
node_type: KRK
node_label: Pitru Karaka (8-karaka)
karaka_system: 8-karaka
karaka_role: PITRU
planet: PLN.MARS
degree_in_sign: "18°31′"
note: "New in 8-karaka system. Mars = C8.PITRU (not PK as in 7-karaka). GAP.13 resolved."
l1_source: "FORENSIC_v8_0 §10.3"

node_id: KRK.C8.GNATI
node_type: KRK
node_label: Gnati Karaka (8-karaka)
karaka_system: 8-karaka
karaka_role: GNATI
planet: PLN.JUPITER
degree_in_sign: "09°48′"
l1_source: "FORENSIC_v8_0 §10.1 §10.3"

node_id: KRK.C8.DARA
node_type: KRK
node_label: Dara Karaka (8-karaka)
karaka_system: 8-karaka
karaka_role: DARA
planet: PLN.MERCURY
degree_in_sign: "00°50′"
note: "Lowest degree planet in 8-karaka. Mercury = DK."
l1_source: "FORENSIC_v8_0 §10.1 §10.3"

node_id: KRK.C7.PUTRA
node_type: KRK
node_label: Putra Karaka (7-karaka alternative)
karaka_system: 7-karaka-alternative
karaka_role: PUTRA
planet: PLN.MARS
degree_in_sign: "18°31′"
note: "Retained per GAP.13 resolution. In 7-karaka Mars = PK. This node is the 7-karaka alternative; canonical is KRK.C8.PUTRA=Rahu."
l1_source: "FORENSIC_v8_0 §10.1"

node_id: KRK.STH.ATMA
node_type: KRK
node_label: Sthira Atma Karaka
karaka_system: sthira
karaka_role: ATMA
planet: PLN.SUN
domain: soul_vitality
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.AMATYA
node_type: KRK
node_label: Sthira Amatya Karaka
karaka_system: sthira
karaka_role: AMATYA
planet: PLN.MERCURY
domain: intelligence_minister
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.BHRATRU
node_type: KRK
node_label: Sthira Bhratru Karaka
karaka_system: sthira
karaka_role: BHRATRU
planet: PLN.MARS
domain: brothers_courage
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.MATRU
node_type: KRK
node_label: Sthira Matru Karaka
karaka_system: sthira
karaka_role: MATRU
planet: PLN.MOON
domain: mother_nourishment
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.PUTRA
node_type: KRK
node_label: Sthira Putra Karaka
karaka_system: sthira
karaka_role: PUTRA
planet: PLN.JUPITER
domain: children_teacher
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.DARA
node_type: KRK
node_label: Sthira Dara Karaka
karaka_system: sthira
karaka_role: DARA
planet: PLN.VENUS
domain: spouse_pleasure
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.GNATI
node_type: KRK
node_label: Sthira Gnati Karaka
karaka_system: sthira
karaka_role: GNATI
planet: PLN.SATURN
domain: illness_enemies_cousins
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.PITRI
node_type: KRK
node_label: Sthira Pitri Karaka
karaka_system: sthira
karaka_role: PITRI
planet: PLN.SUN
domain: father_ancestors
note: "Same planet as KRK.STH.ATMA but different karaka role."
l1_source: "FORENSIC_v8_0 §10.2"

node_id: KRK.STH.VAHANA
node_type: KRK
node_label: Sthira Vahana Karaka
karaka_system: sthira
karaka_role: VAHANA
planet: PLN.VENUS
domain: vehicles_comforts
note: "Same planet as KRK.STH.DARA but different karaka role."
l1_source: "FORENSIC_v8_0 §10.2"

node_id: DVS.D9.LAGNA
node_type: DVS
node_label: D9 Lagna — Cancer
varga: D9
position_type: lagna
sign: Cancer
vargottama: false
planet: lagna_point
note: "D9 Lagna Cancer. D9 Lagna lord PLN.MOON in D9 12th (Gemini) — 12H stellium."
l1_source: "FORENSIC_v8_0 §3.5"

node_id: DVS.D9.SUN
node_type: DVS
node_label: D9 Sun — Cancer
varga: D9
planet: PLN.SUN
sign: Cancer
vargottama: false
l1_source: "FORENSIC_v8_0 §3.5"

node_id: DVS.D9.MOON
node_type: DVS
node_label: D9 Moon — Gemini (12H)
varga: D9
planet: PLN.MOON
sign: Gemini
house_from_d9_lagna: 12
vargottama: false
note: "In D9 12H stellium with PLN.JUPITER and PLN.RAHU."
l1_source: "FORENSIC_v8_0 §3.5 §3.5.2"

node_id: DVS.D9.MARS
node_type: DVS
node_label: D9 Mars — Pisces
varga: D9
planet: PLN.MARS
sign: Pisces
vargottama: false
l1_source: "FORENSIC_v8_0 §3.5"

node_id: DVS.D9.MERCURY
node_type: DVS
node_label: D9 Mercury — Capricorn (vargottama)
varga: D9
planet: PLN.MERCURY
sign: Capricorn
vargottama: true
house_from_d9_lagna: 7
note: "Vargottama. Kendra from D9 Lagna. Dispositor for D9 12H stellium and NBR yogas."
l1_source: "FORENSIC_v8_0 §3.5 §3.5.1 §3.5.2"

node_id: DVS.D9.JUPITER
node_type: DVS
node_label: D9 Jupiter — Gemini (12H)
varga: D9
planet: PLN.JUPITER
sign: Gemini
house_from_d9_lagna: 12
vargottama: false
note: "In D9 12H stellium. D9 position differs from D1 dignified placement."
l1_source: "FORENSIC_v8_0 §3.5 §3.5.2"

node_id: DVS.D9.VENUS
node_type: DVS
node_label: D9 Venus — Virgo (debilitated, NBR)
varga: D9
planet: PLN.VENUS
sign: Virgo
vargottama: false
dignity: debilitated
nbr: true
note: "Neecha Bhanga active. Dispositor PLN.MERCURY in D9 kendra (H7 Capricorn)."
l1_source: "FORENSIC_v8_0 §3.5.1"

node_id: DVS.D9.SATURN
node_type: DVS
node_label: D9 Saturn — Aries (debilitated, NBR)
varga: D9
planet: PLN.SATURN
sign: Aries
vargottama: false
dignity: debilitated
nbr: true
note: "Neecha Bhanga active. Exaltation ruler PLN.SUN in Cancer = D9 Lagna (kendra)."
l1_source: "FORENSIC_v8_0 §3.5.1"

node_id: DVS.D9.RAHU
node_type: DVS
node_label: D9 Rahu — Gemini (12H)
varga: D9
planet: PLN.RAHU
sign: Gemini
house_from_d9_lagna: 12
vargottama: false
note: "In D9 12H stellium with PLN.MOON and PLN.JUPITER."
l1_source: "FORENSIC_v8_0 §3.5 §3.5.2"

node_id: DVS.D9.KETU
node_type: DVS
node_label: D9 Ketu — Sagittarius
varga: D9
planet: PLN.KETU
sign: Sagittarius
vargottama: false
l1_source: "FORENSIC_v8_0 §3.5"

node_id: DVS.D10.LAGNA
node_type: DVS
node_label: D10 Lagna — Leo
varga: D10
position_type: lagna
sign: Leo
house: 1
lagna_lord: PLN.SUN
note: "D10 AL (Arudha in Dashamsha) = Sagittarius. PLN.SUN is lagna lord."
l1_source: "FORENSIC_v8_0 §3.6 §13"

node_id: DVS.D10.SUN
node_type: DVS
node_label: D10 Sun — Aries H9
varga: D10
planet: PLN.SUN
sign: Aries
house_from_d10_lagna: 9
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.MOON
node_type: DVS
node_label: D10 Moon — Scorpio H4
varga: D10
planet: PLN.MOON
sign: Scorpio
house_from_d10_lagna: 4
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.MARS
node_type: DVS
node_label: D10 Mars — Aries H9
varga: D10
planet: PLN.MARS
sign: Aries
house_from_d10_lagna: 9
note: "Co-located with PLN.SUN in D10 H9."
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.MERCURY
node_type: DVS
node_label: D10 Mercury — Virgo H2
varga: D10
planet: PLN.MERCURY
sign: Virgo
house_from_d10_lagna: 2
note: "Mercury in own sign Virgo in D10 H2."
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.JUPITER
node_type: DVS
node_label: D10 Jupiter — Pisces H8
varga: D10
planet: PLN.JUPITER
sign: Pisces
house_from_d10_lagna: 8
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.VENUS
node_type: DVS
node_label: D10 Venus — Gemini H11
varga: D10
planet: PLN.VENUS
sign: Gemini
house_from_d10_lagna: 11
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.SATURN
node_type: DVS
node_label: D10 Saturn — Taurus H10
varga: D10
planet: PLN.SATURN
sign: Taurus
house_from_d10_lagna: 10
note: "Saturn in D10 H10 (10th lord position) — strong career indicator."
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.RAHU
node_type: DVS
node_label: D10 Rahu — Cancer H12
varga: D10
planet: PLN.RAHU
sign: Cancer
house_from_d10_lagna: 12
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D10.KETU
node_type: DVS
node_label: D10 Ketu — Capricorn H6
varga: D10
planet: PLN.KETU
sign: Capricorn
house_from_d10_lagna: 6
l1_source: "FORENSIC_v8_0 §3.6"

node_id: DVS.D12.LAGNA
node_type: DVS
node_label: D12 Lagna — Leo
varga: D12
position_type: lagna
sign: Leo
lagna_lord: PLN.SUN
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.SUN
node_type: DVS
node_label: D12 Sun — Virgo
varga: D12
planet: PLN.SUN
sign: Virgo
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.MOON
node_type: DVS
node_label: D12 Moon — Scorpio
varga: D12
planet: PLN.MOON
sign: Scorpio
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.MARS
node_type: DVS
node_label: D12 Mars — Cancer
varga: D12
planet: PLN.MARS
sign: Cancer
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.MERCURY
node_type: DVS
node_label: D12 Mercury — Aries
varga: D12
planet: PLN.MERCURY
sign: Aries
note: "Co-located with PLN.JUPITER in D12 Aries."
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.JUPITER
node_type: DVS
node_label: D12 Jupiter — Aries
varga: D12
planet: PLN.JUPITER
sign: Aries
note: "Co-located with PLN.MERCURY in D12 Aries."
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.VENUS
node_type: DVS
node_label: D12 Venus — Libra
varga: D12
planet: PLN.VENUS
sign: Libra
note: "Venus in own sign Libra in D12."
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.SATURN
node_type: DVS
node_label: D12 Saturn — Gemini
varga: D12
planet: PLN.SATURN
sign: Gemini
note: "Co-located with PLN.KETU in D12 Gemini."
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.RAHU
node_type: DVS
node_label: D12 Rahu — Sagittarius
varga: D12
planet: PLN.RAHU
sign: Sagittarius
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D12.KETU
node_type: DVS
node_label: D12 Ketu — Gemini
varga: D12
planet: PLN.KETU
sign: Gemini
note: "Co-located with PLN.SATURN in D12 Gemini."
l1_source: "FORENSIC_v8_0 §3.7"

node_id: DVS.D7.LAGNA
node_type: DVS
node_label: D7 Lagna — Cancer
varga: D7
position_type: lagna
sign: Cancer
tenant: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.SUN
node_type: DVS
node_label: D7 Sun — Sagittarius H6
varga: D7
planet: PLN.SUN
sign: Sagittarius
house_from_d7_lagna: 6
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.MOON
node_type: DVS
node_label: D7 Moon — Leo H2
varga: D7
planet: PLN.MOON
sign: Leo
house_from_d7_lagna: 2
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.MARS
node_type: DVS
node_label: D7 Mars — Aquarius H8
varga: D7
planet: PLN.MARS
sign: Aquarius
house_from_d7_lagna: 8
note: "Co-located with PLN.JUPITER in D7 H8."
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.MERCURY
node_type: DVS
node_label: D7 Mercury — Cancer H1
varga: D7
planet: PLN.MERCURY
sign: Cancer
house_from_d7_lagna: 1
note: "Mercury in D7 lagna sign; co-location with D7 Lagna marker."
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.JUPITER
node_type: DVS
node_label: D7 Jupiter — Aquarius H8
varga: D7
planet: PLN.JUPITER
sign: Aquarius
house_from_d7_lagna: 8
note: "Co-located with PLN.MARS in D7 H8."
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.VENUS
node_type: DVS
node_label: D7 Venus — Aries H10
varga: D7
planet: PLN.VENUS
sign: Aries
house_from_d7_lagna: 10
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.SATURN
node_type: DVS
node_label: D7 Saturn — Pisces H9
varga: D7
planet: PLN.SATURN
sign: Pisces
house_from_d7_lagna: 9
note: "Co-located with PLN.RAHU in D7 H9."
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.RAHU
node_type: DVS
node_label: D7 Rahu — Pisces H9
varga: D7
planet: PLN.RAHU
sign: Pisces
house_from_d7_lagna: 9
note: "Co-located with PLN.SATURN in D7 H9."
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D7.KETU
node_type: DVS
node_label: D7 Ketu — Virgo H3
varga: D7
planet: PLN.KETU
sign: Virgo
house_from_d7_lagna: 3
l1_source: "FORENSIC_v8_0 §3.4"

node_id: DVS.D2.LAGNA
node_type: DVS
node_label: D2 Lagna Hora — Leo (Sun's hora)
varga: D2
position_type: lagna_hora
sign: Leo
hora_ruler: PLN.SUN
tenants_d2: [PLN.JUPITER, PLN.KETU, PLN.SUN, PLN.RAHU]
note: "Aries lagna (odd sign) falls in Leo hora. D2 Leo hora carries Jupiter, Ketu, Sun, Rahu."
l1_source: "FORENSIC_v8_0 §3.1"

node_id: DVS.D2.MOON
node_type: DVS
node_label: D2 Moon Hora — Cancer (Moon's hora)
varga: D2
position_type: moon_hora
sign: Cancer
hora_ruler: PLN.MOON
tenants_d2: [PLN.MOON, PLN.MARS, PLN.VENUS, PLN.SATURN, PLN.MERCURY]
note: "Moon in Cancer hora along with Mars, Venus, Saturn, Mercury."
l1_source: "FORENSIC_v8_0 §3.1"

node_id: DVS.D3.LAGNA
node_type: DVS
node_label: D3 Lagna — Leo
varga: D3
position_type: lagna
sign: Leo
tenant: PLN.VENUS
house: 1
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.SUN
node_type: DVS
node_label: D3 Sun — Virgo H2
varga: D3
planet: PLN.SUN
sign: Virgo
house_from_d3_lagna: 2
note: "Co-located with PLN.RAHU in D3 Virgo."
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.MOON
node_type: DVS
node_label: D3 Moon — Scorpio H4
varga: D3
planet: PLN.MOON
sign: Scorpio
house_from_d3_lagna: 4
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.MARS
node_type: DVS
node_label: D3 Mars — Gemini H11
varga: D3
planet: PLN.MARS
sign: Gemini
house_from_d3_lagna: 11
note: "Co-located with PLN.SATURN in D3 Gemini H11."
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.MERCURY
node_type: DVS
node_label: D3 Mercury — Capricorn H6
varga: D3
planet: PLN.MERCURY
sign: Capricorn
house_from_d3_lagna: 6
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.JUPITER
node_type: DVS
node_label: D3 Jupiter — Aries H9
varga: D3
planet: PLN.JUPITER
sign: Aries
house_from_d3_lagna: 9
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.VENUS
node_type: DVS
node_label: D3 Venus — Leo H1
varga: D3
planet: PLN.VENUS
sign: Leo
house_from_d3_lagna: 1
note: "Venus in D3 lagna sign Leo. Co-location with DVS.D3.LAGNA marker."
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.SATURN
node_type: DVS
node_label: D3 Saturn — Gemini H11
varga: D3
planet: PLN.SATURN
sign: Gemini
house_from_d3_lagna: 11
note: "Co-located with PLN.MARS in D3 Gemini H11."
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.RAHU
node_type: DVS
node_label: D3 Rahu — Virgo H2
varga: D3
planet: PLN.RAHU
sign: Virgo
house_from_d3_lagna: 2
note: "Co-located with PLN.SUN in D3 Virgo."
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D3.KETU
node_type: DVS
node_label: D3 Ketu — Pisces H8
varga: D3
planet: PLN.KETU
sign: Pisces
house_from_d3_lagna: 8
l1_source: "FORENSIC_v8_0 §3.2"

node_id: DVS.D4.LAGNA
node_type: DVS
node_label: D4 Lagna — Cancer
varga: D4
position_type: lagna
sign: Cancer
tenant: PLN.SUN
house: 1
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.SUN
node_type: DVS
node_label: D4 Sun — Cancer H1
varga: D4
planet: PLN.SUN
sign: Cancer
house_from_d4_lagna: 1
note: "PLN.SUN in D4 lagna sign Cancer. Co-location with DVS.D4.LAGNA."
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.MOON
node_type: DVS
node_label: D4 Moon — Scorpio H5
varga: D4
planet: PLN.MOON
sign: Scorpio
house_from_d4_lagna: 5
note: "Co-located with PLN.RAHU in D4 Scorpio."
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.MARS
node_type: DVS
node_label: D4 Mars — Aries H10
varga: D4
planet: PLN.MARS
sign: Aries
house_from_d4_lagna: 10
note: "Co-located with PLN.SATURN in D4 Aries H10."
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.MERCURY
node_type: DVS
node_label: D4 Mercury — Capricorn H7
varga: D4
planet: PLN.MERCURY
sign: Capricorn
house_from_d4_lagna: 7
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.JUPITER
node_type: DVS
node_label: D4 Jupiter — Pisces H9
varga: D4
planet: PLN.JUPITER
sign: Pisces
house_from_d4_lagna: 9
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.VENUS
node_type: DVS
node_label: D4 Venus — Gemini H12
varga: D4
planet: PLN.VENUS
sign: Gemini
house_from_d4_lagna: 12
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.SATURN
node_type: DVS
node_label: D4 Saturn — Aries H10
varga: D4
planet: PLN.SATURN
sign: Aries
house_from_d4_lagna: 10
note: "Co-located with PLN.MARS in D4 Aries H10."
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D4.RAHU_KETU
node_type: DVS
node_label: D4 Rahu-Ketu axis
varga: D4
planet: PLN.RAHU
planet_ketu: PLN.KETU
rahu_sign: Scorpio
ketu_sign: Taurus
rahu_house_from_d4_lagna: 5
ketu_house_from_d4_lagna: 11
note: "Rahu in D4 Scorpio H5 (with Moon). Ketu in D4 Taurus H11. Combined axis node."
l1_source: "FORENSIC_v8_0 §3.3"

node_id: DVS.D16.LAGNA
node_type: DVS
node_label: D16 Lagna — Leo (Moon+Mars co-tenants)
varga: D16
position_type: lagna
sign: Leo
tenants: [PLN.MOON, PLN.MARS]
l1_source: "FORENSIC_v8_0 §3.8"

node_id: DVS.D16.MERCURY
node_type: DVS
node_label: D16 Mercury — Taurus
varga: D16
planet: PLN.MERCURY
sign: Taurus
note: "Co-located with PLN.JUPITER in D16 Taurus."
l1_source: "FORENSIC_v8_0 §3.8"

node_id: DVS.D16.JUPITER
node_type: DVS
node_label: D16 Jupiter — Taurus
varga: D16
planet: PLN.JUPITER
sign: Taurus
note: "Co-located with PLN.MERCURY in D16 Taurus."
l1_source: "FORENSIC_v8_0 §3.8"

node_id: DVS.D16.SATURN
node_type: DVS
node_label: D16 Saturn — Virgo
varga: D16
planet: PLN.SATURN
sign: Virgo
l1_source: "FORENSIC_v8_0 §3.8"

node_id: DVS.D16.VENUS
node_type: DVS
node_label: D16 Venus — Capricorn
varga: D16
planet: PLN.VENUS
sign: Capricorn
l1_source: "FORENSIC_v8_0 §3.8"

node_id: DVS.D16.SUN
node_type: DVS
node_label: D16 Sun — Sagittarius
varga: D16
planet: PLN.SUN
sign: Sagittarius
l1_source: "FORENSIC_v8_0 §3.8"

node_id: DVS.D16.RAHU_KETU
node_type: DVS
node_label: D16 Rahu-Ketu — Gemini (combined)
varga: D16
planet: PLN.RAHU
planet_ketu: PLN.KETU
rahu_sign: Gemini
ketu_sign: Gemini
note: "Both Rahu and Ketu in D16 Gemini — combined axis node."
l1_source: "FORENSIC_v8_0 §3.8"

node_id: DVS.D20.LAGNA
node_type: DVS
node_label: D20 Lagna — Scorpio (Jupiter co-tenant)
varga: D20
position_type: lagna
sign: Scorpio
tenant: PLN.JUPITER
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.JUPITER
node_type: DVS
node_label: D20 Jupiter — Scorpio H1
varga: D20
planet: PLN.JUPITER
sign: Scorpio
house_from_d20_lagna: 1
note: "PLN.JUPITER in D20 lagna sign Scorpio. Own-sign dispositor (Scorpio's alternate lord)."
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.SATURN
node_type: DVS
node_label: D20 Saturn — Sagittarius H2
varga: D20
planet: PLN.SATURN
sign: Sagittarius
house_from_d20_lagna: 2
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.MARS
node_type: DVS
node_label: D20 Mars — Capricorn H3
varga: D20
planet: PLN.MARS
sign: Capricorn
house_from_d20_lagna: 3
note: "Co-located with PLN.RAHU in D20 Capricorn."
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.RAHU
node_type: DVS
node_label: D20 Rahu — Capricorn H3
varga: D20
planet: PLN.RAHU
sign: Capricorn
house_from_d20_lagna: 3
note: "Co-located with PLN.MARS in D20 Capricorn."
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.SUN
node_type: DVS
node_label: D20 Sun — Pisces H5
varga: D20
planet: PLN.SUN
sign: Pisces
house_from_d20_lagna: 5
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.MERCURY
node_type: DVS
node_label: D20 Mercury — Gemini H8
varga: D20
planet: PLN.MERCURY
sign: Gemini
house_from_d20_lagna: 8
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.KETU
node_type: DVS
node_label: D20 Ketu — Cancer H9
varga: D20
planet: PLN.KETU
sign: Cancer
house_from_d20_lagna: 9
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DVS.D20.MOON_VENUS
node_type: DVS
node_label: D20 Moon+Venus — Leo H10 (combined)
varga: D20
planet: PLN.MOON
planet_alt: PLN.VENUS
sign: Leo
house_from_d20_lagna: 10
note: "Moon and Venus co-located in D20 Leo H10. Combined node."
l1_source: "FORENSIC_v8_0 §3.9"

node_id: DSH.VM.MD.JUPITER
node_type: DSH
node_label: Vimshottari MD — Jupiter
dasha_system: vimshottari_mahadasha
planet: PLN.JUPITER
start: "1984-02-05"
end: "1991-08-21"
duration_years: 7
status: completed
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.SATURN
node_type: DSH
node_label: Vimshottari MD — Saturn
dasha_system: vimshottari_mahadasha
planet: PLN.SATURN
start: "1991-08-21"
end: "2010-08-21"
duration_years: 19
status: completed
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.MERCURY
node_type: DSH
node_label: Vimshottari MD — Mercury (current)
dasha_system: vimshottari_mahadasha
planet: PLN.MERCURY
start: "2010-08-21"
end: "2027-08-21"
duration_years: 17
status: active
current_ad: PLN.SATURN
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.KETU
node_type: DSH
node_label: Vimshottari MD — Ketu
dasha_system: vimshottari_mahadasha
planet: PLN.KETU
start: "2027-08-21"
end: "2034-08-21"
duration_years: 7
status: upcoming
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.VENUS
node_type: DSH
node_label: Vimshottari MD — Venus
dasha_system: vimshottari_mahadasha
planet: PLN.VENUS
start: "2034-08-21"
end: "2054-08-21"
duration_years: 20
status: upcoming
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.SUN
node_type: DSH
node_label: Vimshottari MD — Sun
dasha_system: vimshottari_mahadasha
planet: PLN.SUN
start: "2054-08-21"
end: "2060-08-21"
duration_years: 6
status: future
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.MOON
node_type: DSH
node_label: Vimshottari MD — Moon
dasha_system: vimshottari_mahadasha
planet: PLN.MOON
start: "2060-08-21"
end: "2070-08-21"
duration_years: 10
status: future
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.MARS
node_type: DSH
node_label: Vimshottari MD — Mars
dasha_system: vimshottari_mahadasha
planet: PLN.MARS
start: "2070-08-21"
end: "2077-08-21"
duration_years: 7
status: future
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.MD.RAHU
node_type: DSH
node_label: Vimshottari MD — Rahu
dasha_system: vimshottari_mahadasha
planet: PLN.RAHU
start: "2077-08-21"
end: "2095-08-21"
duration_years: 18
status: future
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_MERC
node_type: DSH
node_label: Mercury MD — Mercury AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.MERCURY
start: "2010-08-21"
end: "2013-01-18"
status: completed
dsh_id: DSH.V.015
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_KETU
node_type: DSH
node_label: Mercury MD — Ketu AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.KETU
start: "2013-01-18"
end: "2014-01-15"
status: completed
dsh_id: DSH.V.016
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_VENUS
node_type: DSH
node_label: Mercury MD — Venus AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.VENUS
start: "2014-01-15"
end: "2016-11-15"
status: completed
dsh_id: DSH.V.017
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_SUN
node_type: DSH
node_label: Mercury MD — Sun AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.SUN
start: "2016-11-15"
end: "2017-09-21"
status: completed
dsh_id: DSH.V.018
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_MOON
node_type: DSH
node_label: Mercury MD — Moon AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.MOON
start: "2017-09-21"
end: "2019-02-21"
status: completed
dsh_id: DSH.V.019
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_MARS
node_type: DSH
node_label: Mercury MD — Mars AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.MARS
start: "2019-02-21"
end: "2020-02-18"
status: completed
dsh_id: DSH.V.020
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_RAHU
node_type: DSH
node_label: Mercury MD — Rahu AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.RAHU
start: "2020-02-18"
end: "2022-09-06"
status: completed
dsh_id: DSH.V.021
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_JUPITER
node_type: DSH
node_label: Mercury MD — Jupiter AD
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.JUPITER
start: "2022-09-06"
end: "2024-12-12"
status: completed
dsh_id: DSH.V.022
l1_source: "FORENSIC_v8_0 §5.1"

node_id: DSH.VM.AD.MERC_SATURN
node_type: DSH
node_label: Mercury MD — Saturn AD (current)
dasha_system: vimshottari_antardasha
md_planet: PLN.MERCURY
ad_planet: PLN.SATURN
start: "2024-12-12"
end: "2027-08-21"
status: active
dsh_id: DSH.V.023
l1_source: "FORENSIC_v8_0 §5.1 §1.2"

node_id: DSH.YOG.BHRAMARI
node_type: DSH
node_label: Yogini — Bhramari (Mars)
dasha_system: yogini
yogini: Bhramari
planet: PLN.MARS
start: "1984-02-05"
end: "1985-12-22"
duration_years: 4
cycle: 1_partial
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.YOG.BHADRIKA
node_type: DSH
node_label: Yogini — Bhadrika (Mercury)
dasha_system: yogini
yogini: Bhadrika
planet: PLN.MERCURY
start: "1985-12-22"
end: "1990-12-22"
duration_years: 5
cycle: 1
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.YOG.ULKA
node_type: DSH
node_label: Yogini — Ulka (Saturn)
dasha_system: yogini
yogini: Ulka
planet: PLN.SATURN
start: "1990-12-22"
end: "1996-12-22"
duration_years: 6
cycle: 1
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.YOG.SIDDHA
node_type: DSH
node_label: Yogini — Siddha (Venus)
dasha_system: yogini
yogini: Siddha
planet: PLN.VENUS
start: "1996-12-22"
end: "2003-12-22"
duration_years: 7
cycle: 1
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.YOG.SANKATA
node_type: DSH
node_label: Yogini — Sankata (Rahu)
dasha_system: yogini
yogini: Sankata
planet: PLN.RAHU
start: "2003-12-22"
end: "2011-12-22"
duration_years: 8
cycle: 1
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.YOG.MANGALA
node_type: DSH
node_label: Yogini — Mangala (Moon)
dasha_system: yogini
yogini: Mangala
planet: PLN.MOON
start: "2011-12-22"
end: "2012-12-22"
duration_years: 1
cycle: 1
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.YOG.PINGALA
node_type: DSH
node_label: Yogini — Pingala (Sun)
dasha_system: yogini
yogini: Pingala
planet: PLN.SUN
start: "2012-12-22"
end: "2014-12-22"
duration_years: 2
cycle: 1
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.YOG.DHANYA
node_type: DSH
node_label: Yogini — Dhanya (Jupiter)
dasha_system: yogini
yogini: Dhanya
planet: PLN.JUPITER
start: "2014-12-22"
end: "2017-12-22"
duration_years: 3
cycle: 1
status: completed
l1_source: "FORENSIC_v8_0 §5.2"

node_id: DSH.CHA.VIRGO
node_type: DSH
node_label: Jaimini Chara MD — Virgo
dasha_system: jaimini_chara
md_sign: Virgo
start: "2016-02-05"
end: "2024-02-05"
duration_years: 8
status: completed
note: "Virgo MD (9 years per Jaimini calc). Key period: multiple LEL events; Mercury MD overlap."
l1_source: "FORENSIC_v8_0 §5.3"

node_id: DSH.CHA.LIBRA
node_type: DSH
node_label: Jaimini Chara MD — Libra
dasha_system: jaimini_chara
md_sign: Libra
start: "2024-02-05"
end: "2026-02-05"
duration_years: 2
status: completed
note: "Libra MD (2 years). Saturn+Mars tenanted sign activated as MD."
l1_source: "FORENSIC_v8_0 §5.3"

node_id: DSH.CHA.SCORPIO
node_type: DSH
node_label: Jaimini Chara MD — Scorpio (current)
dasha_system: jaimini_chara
md_sign: Scorpio
start: "2026-02-05"
end: "2036-03-05"
duration_years: 10
status: active
note: "Current Chara MD. Ketu-tenanted sign. PLN.KETU in Scorpio D1."
l1_source: "FORENSIC_v8_0 §5.3"

node_id: DSH.CHA.SAGITTARIUS
node_type: DSH
node_label: Jaimini Chara MD — Sagittarius
dasha_system: jaimini_chara
md_sign: Sagittarius
start: "2036-03-05"
end: "~2048"
duration_years: 12
status: upcoming
note: "Next Chara MD. Jupiter-Venus tenanted sign. PLN.JUPITER own-sign H9."
l1_source: "FORENSIC_v8_0 §5.3"

node_id: SEN.UPG.GULIKA
node_type: SEN
node_label: Gulika
sen_class: upagraha
upagraha_type: time_based
sign: Gemini
degree: "13°57′"
nakshatra: Ardra
house: 3
house_lord: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.MANDI
node_type: SEN
node_label: Mandi
sen_class: upagraha
upagraha_type: time_based
sign: Cancer
degree: "14°13′"
nakshatra: Pushya
house: 4
house_lord: PLN.MOON
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.YAMAGHANTAKA
node_type: SEN
node_label: Yamaghantaka
sen_class: upagraha
upagraha_type: time_based
sign: Taurus
degree: "01°54′"
nakshatra: Krittika
house: 2
planet_ref: PLN.RAHU
note: "In H2 Taurus — same house as PLN.RAHU."
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.ARDHAPRAHARA
node_type: SEN
node_label: Ardhaprahara
sen_class: upagraha
upagraha_type: time_based
sign: Aries
degree: "10°52′"
nakshatra: Ashwini
house: 1
planet_ref: PLN.MARS
note: "In H1 Aries lagna sign — near lagna marker."
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.DHUMA
node_type: SEN
node_label: Dhuma
sen_class: upagraha
upagraha_type: sun_based
sign: Gemini
degree: "05°17′"
nakshatra: Mrigashira
house: 3
planet_ref: PLN.SUN
note: "Co-located with LAG.HORA in Gemini H3."
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.VYATIPATA
node_type: SEN
node_label: Vyatipata
sen_class: upagraha
upagraha_type: sun_based
sign: Capricorn
degree: "24°42′"
nakshatra: Dhanishtha
house: 10
planet_ref: PLN.SUN
note: "In H10 Capricorn — career house cluster."
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.PARIVESHA
node_type: SEN
node_label: Parivesha
sen_class: upagraha
upagraha_type: sun_based
sign: Cancer
degree: "24°42′"
nakshatra: Ashlesha
house: 4
planet_ref: PLN.SUN
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.INDRACHAPA
node_type: SEN
node_label: Indrachapa
sen_class: upagraha
upagraha_type: sun_based
sign: Sagittarius
degree: "05°17′"
nakshatra: Moola
house: 9
planet_ref: PLN.SUN
note: "In H9 Sagittarius — same house as PLN.JUPITER and PLN.VENUS."
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.UPG.UPAKETU
node_type: SEN
node_label: Upaketu
sen_class: upagraha
upagraha_type: sun_based
sign: Sagittarius
degree: "21°57′"
nakshatra: Purva_Ashadha
pada: 2
house: 9
planet_ref: PLN.SUN
note: "Upaketu at same degree as PLN.SUN in D1. In Purva Ashadha P2 with PLN.VENUS."
l1_source: "FORENSIC_v8_0 §11.1"

node_id: SEN.ARD.AL
node_type: SEN
node_label: Arudha Lagna (AL)
sen_class: arudha
arudha_type: AL
sign: Capricorn
house: 10
tenants: [PLN.SUN, PLN.MERCURY]
note: "AL in H10 Capricorn co-located with Sun+Mercury. Exception applied: Mars in H7 Libra triggers jump."
l1_source: "FORENSIC_v8_0 §13.1"

node_id: SEN.ARD.A2
node_type: SEN
node_label: A2 — Dhana Arudha
sen_class: arudha
arudha_type: A2
sign: Cancer
house: 4
l1_source: "FORENSIC_v8_0 §13.1"

node_id: SEN.ARD.A3
node_type: SEN
node_label: A3 Arudha
sen_class: arudha
arudha_type: A3
sign: Leo
house: 5
planet_ref: PLN.SUN
l1_source: "FORENSIC_v8_0 §13.2"

node_id: SEN.ARD.A4
node_type: SEN
node_label: A4 Arudha
sen_class: arudha
arudha_type: A4
sign: Virgo
house: 6
planet_ref: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §13.2"

node_id: SEN.ARD.A5
node_type: SEN
node_label: A5 Arudha
sen_class: arudha
arudha_type: A5
sign: Gemini
house: 3
note: "A5 in Gemini H3 — co-located with UL and A11."
l1_source: "FORENSIC_v8_0 §13.2"

node_id: SEN.ARD.A6
node_type: SEN
node_label: A6 — Enemy Arudha
sen_class: arudha
arudha_type: A6
sign: Taurus
house: 2
planet_ref: PLN.RAHU
note: "A6 co-located with PLN.RAHU in H2 Taurus."
l1_source: "FORENSIC_v8_0 §13.1"

node_id: SEN.ARD.A7
node_type: SEN
node_label: A7 — Partner Arudha
sen_class: arudha
arudha_type: A7
sign: Aquarius
house: 11
planet_ref: PLN.MOON
note: "A7 co-located with PLN.MOON (AK) in H11 Aquarius."
l1_source: "FORENSIC_v8_0 §13.1"

node_id: SEN.ARD.A8
node_type: SEN
node_label: A8 Arudha
sen_class: arudha
arudha_type: A8
sign: Virgo
house: 6
planet_ref: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §13.2"

node_id: SEN.ARD.A9
node_type: SEN
node_label: A9 Arudha
sen_class: arudha
arudha_type: A9
sign: Virgo
house: 6
planet_ref: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §13.2"

node_id: SEN.ARD.A10
node_type: SEN
node_label: A10 — Karma Arudha
sen_class: arudha
arudha_type: A10
sign: Aries
house: 1
note: "A10 in H1 Aries lagna. Exception applied twice in derivation."
l1_source: "FORENSIC_v8_0 §13.1"

node_id: SEN.ARD.A11
node_type: SEN
node_label: A11 — Financial Arudha
sen_class: arudha
arudha_type: A11
sign: Gemini
house: 3
note: "A11 in Gemini H3 with UL and A5."
l1_source: "FORENSIC_v8_0 §13.1 §13.2"

node_id: SEN.ARD.UL
node_type: SEN
node_label: UL — Upapada Lagna (Spouse)
sen_class: arudha
arudha_type: UL
sign: Gemini
house: 3
planet_ref: PLN.MERCURY
note: "UL in Gemini H3. Derivation involves H12 lord Jupiter in Sagittarius with exception jump."
l1_source: "FORENSIC_v8_0 §13.1"

node_id: SEN.LAG.BHAVA
node_type: SEN
node_label: Bhava Lagna
sen_class: special_lagna
lagna_type: Bhava
sign: Pisces
degree: "26°13′27″"
nakshatra: Revati
pada: 3
house: 12
engine: JH_authoritative
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.LAG.HORA
node_type: SEN
node_label: Hora Lagna
sen_class: special_lagna
lagna_type: Hora
sign: Gemini
degree: "00°39′07.90″"
nakshatra: Mrigashira
pada: 3
house: 3
engine: JH_authoritative
note: "v8.0 correction. Previous v6.0 value (Libra 10°11') was erroneous."
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.LAG.GHATI
node_type: SEN
node_label: Ghati Lagna
sen_class: special_lagna
lagna_type: Ghati
sign: Sagittarius
degree: "13°56′07.87″"
nakshatra: Purva_Ashadha
pada: 1
house: 9
engine: JH_authoritative
note: "v8.0 correction. Previous v6.0 value (Scorpio 6°53') was erroneous."
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.LAG.INDU
node_type: SEN
node_label: Indu Lagna
sen_class: special_lagna
lagna_type: Indu
sign: Scorpio
degree: "27°04′14.11″"
nakshatra: Jyeshtha
pada: 4
house: 8
engine: JH_authoritative
planet_ref: PLN.KETU
note: "Indu Lagna in Jyeshtha P4, same sign as PLN.KETU."
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.LAG.SHREE
node_type: SEN
node_label: Shree Lagna
sen_class: special_lagna
lagna_type: Shree
sign: Libra
degree: "23°19′42.57″"
nakshatra: Vishakha
pada: 1
house: 7
engine: JH_authoritative
planet_ref: PLN.SATURN
note: "v8.0 correction. Shree Lagna joins Saturn+Mars in H7 Libra Vishakha P1."
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.LAG.VARNADA
node_type: SEN
node_label: Varnada Lagna
sen_class: special_lagna
lagna_type: Varnada
sign: Cancer
degree: "12°25′21.62″"
nakshatra: Pushya
pada: 3
house: 4
engine: JH_authoritative
note: "v8.0 correction. Previous v6.0 value (Scorpio 12°23') was erroneous."
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.LAG.PRANAPADA
node_type: SEN
node_label: Pranapada Lagna
sen_class: special_lagna
lagna_type: Pranapada
sign: Leo
degree: "20°32′01.21″"
nakshatra: Purva_Phalguni
pada: 3
house: 5
engine: JH_authoritative
note: "New in v8.0. Not in v6.0."
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.LAG.VIGHATI
node_type: SEN
node_label: Vighati Lagna
sen_class: special_lagna
lagna_type: Vighati
sign: Leo
degree: "20°21′07.75″"
nakshatra: Purva_Phalguni
pada: 3
house: 5
engine: JH_authoritative
note: "New in v8.0. Co-located with Pranapada in Leo Purva Phalguni P3."
l1_source: "FORENSIC_v8_0 §12.1"

node_id: SEN.SAH.PUNYA
node_type: SEN
node_label: Saham Punya — Fortune
sen_class: saham
saham_type: Punya
sign: Gemini
degree: "17°30′54″"
nakshatra: Ardra
house: 3
planet_ref: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.RAJYA
node_type: SEN
node_label: Saham Rajya — Authority
sen_class: saham
saham_type: Rajya
sign: Capricorn
degree: "12°53′31″"
nakshatra: Shravana
house: 10
planet_ref: PLN.SUN
note: "Co-located with SAH.PITRU in Capricorn H10."
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.KARMA
node_type: SEN
node_label: Saham Karma — Profession
sen_class: saham
saham_type: Karma
sign: Aquarius
degree: "00°06′11″"
nakshatra: Dhanishtha
house: 11
planet_ref: PLN.SATURN
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.LABHA
node_type: SEN
node_label: Saham Labha — Gains
sen_class: saham
saham_type: Labha
sign: Virgo
degree: "02°23′51″"
nakshatra: Uttara_Phalguni
house: 6
planet_ref: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.VIVAHA
node_type: SEN
node_label: Saham Vivaha — Marriage
sen_class: saham
saham_type: Vivaha
sign: Cancer
degree: "09°09′47″"
nakshatra: Pushya
house: 4
planet_ref: PLN.MOON
note: "v8.0 correction. Previous v6.0 value (Gemini) was erroneous."
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.PUTRA
node_type: SEN
node_label: Saham Putra — Children
sen_class: saham
saham_type: Putra
sign: Capricorn
degree: "25°09′18″"
nakshatra: Dhanishtha
house: 10
planet_ref: PLN.SATURN
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.PITRI
node_type: SEN
node_label: Saham Pitru — Father
sen_class: saham
saham_type: Pitri
sign: Capricorn
degree: "12°53′31″"
nakshatra: Shravana
house: 10
planet_ref: PLN.SUN
note: "Co-located with SAH.RAJYA in Capricorn H10."
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.MATRI
node_type: SEN
node_label: Saham Matru — Mother
sen_class: saham
saham_type: Matri
sign: Cancer
degree: "20°18′18″"
nakshatra: Ashlesha
house: 4
planet_ref: PLN.MOON
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.VYAPARA
node_type: SEN
node_label: Saham Vyapara — Business
sen_class: saham
saham_type: Vyapara
sign: Aries
degree: "08°30′35″"
nakshatra: Ashwini
house: 1
planet_ref: PLN.MARS
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.SAH.PARADESA
node_type: SEN
node_label: Saham Paradesa — Foreign Lands
sen_class: saham
saham_type: Paradesa
sign: Taurus
degree: "15°02′32″"
nakshatra: Rohini
house: 2
planet_ref: PLN.RAHU
note: "Paradesa Saham in H2 Taurus — same sign as PLN.RAHU. Strong foreign-lands indicator."
l1_source: "FORENSIC_v8_0 §12.2"

node_id: SEN.MISC.BB_NATAL
node_type: SEN
node_label: Bhrigu Bindu (Destiny Point)
sen_class: misc_sensitive
point_type: bhrigu_bindu
sign: Libra
degree: "08°03′34.51″"
nakshatra: Swati
pada: 1
house: 7
formula: "(Moon_abs + Rahu_abs) / 2 mod 360"
planet_ref: PLN.MARS
note: "Bhrigu Bindu in Swati P1 H7 Libra — same nakshatra as PLN.MARS."
l1_source: "FORENSIC_v8_0 §11.2"

node_id: SEN.MISC.YOG_POINT
node_type: SEN
node_label: Yogi Point
sen_class: misc_sensitive
point_type: yogi_point
sign: Pisces
degree: "22°20′"
nakshatra: Revati
house: 12
yogi_planet: PLN.MERCURY
formula: "Sun_abs + Moon_abs + 93°20′ mod 360"
l1_source: "FORENSIC_v8_0 §11.3"

node_id: SEN.MISC.AVY_POINT
node_type: SEN
node_label: Avayogi Point
sen_class: misc_sensitive
point_type: avayogi_point
sign: Gemini
nakshatra: Mrigashira
house: 3
avayogi_planet: PLN.MARS
formula: "6th nakshatra from Yogi nakshatra (Revati)"
note: "Avayogi planet PLN.MARS. Mrigashira is also the nakshatra of LAG.HORA."
l1_source: "FORENSIC_v8_0 §11.3"
# --- v9.1 additions (VARGA-ETL-FULL-S1 D13) — 50 DVS nodes for D24/D30/D40/D45/D60 ---

node_id: DVS.D24.LAGNA
node_type: DVS
node_label: D24 Lagna — Taurus
varga: D24
position_type: lagna
sign: Taurus
lagna_lord: PLN.VENUS
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.SUN
node_type: DVS
node_label: D24 Sun — Sagittarius H8
varga: D24
planet: PLN.SUN
sign: Sagittarius
house_from_d24_lagna: 8
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.MOON
node_type: DVS
node_label: D24 Moon — Taurus H1 (exalted, lagna)
varga: D24
planet: PLN.MOON
sign: Taurus
house_from_d24_lagna: 1
dignity: exalted
note: "Moon exalted at D24 Lagna — emotional/intuitive anchor of the education varga."
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.MARS
node_type: DVS
node_label: D24 Mars — Libra H6
varga: D24
planet: PLN.MARS
sign: Libra
house_from_d24_lagna: 6
dignity: enemy
note: "In Libra (enemy sign — Venus-ruled, śatru-kṣetra; Mars debilitates in Cancer not Libra) joined Rahu and Ketu in D24 6H. Corrected 2026-05-27."
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.MERCURY
node_type: DVS
node_label: D24 Mercury — Cancer H3
varga: D24
planet: PLN.MERCURY
sign: Cancer
house_from_d24_lagna: 3
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.JUPITER
node_type: DVS
node_label: D24 Jupiter — Pisces H11 (own sign)
varga: D24
planet: PLN.JUPITER
sign: Pisces
house_from_d24_lagna: 11
dignity: own_sign
note: "Jupiter own-sign in 11H of the education varga — wisdom-yielding-gains signature."
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.VENUS
node_type: DVS
node_label: D24 Venus — Scorpio H7
varga: D24
planet: PLN.VENUS
sign: Scorpio
house_from_d24_lagna: 7
dignity: debilitated
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.SATURN
node_type: DVS
node_label: D24 Saturn — Capricorn H9 (own sign)
varga: D24
planet: PLN.SATURN
sign: Capricorn
house_from_d24_lagna: 9
dignity: own_sign
note: "Saturn own-sign in D24 9H — disciplined knowledge-acquisition in the dharma house of education varga."
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.RAHU
node_type: DVS
node_label: D24 Rahu — Libra H6
varga: D24
planet: PLN.RAHU
sign: Libra
house_from_d24_lagna: 6
note: "Joined Mars and Ketu in D24 6H."
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D24.KETU
node_type: DVS
node_label: D24 Ketu — Libra H6
varga: D24
planet: PLN.KETU
sign: Libra
house_from_d24_lagna: 6
l1_source: "FORENSIC_v8_0 §3.10"

node_id: DVS.D30.LAGNA
node_type: DVS
node_label: D30 Lagna — Capricorn
varga: D30
position_type: lagna
sign: Capricorn
lagna_lord: PLN.SATURN
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.SUN
node_type: DVS
node_label: D30 Sun — Capricorn H1 (lagna)
varga: D30
planet: PLN.SUN
sign: Capricorn
house_from_d30_lagna: 1
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.MOON
node_type: DVS
node_label: D30 Moon — Libra H10
varga: D30
planet: PLN.MOON
sign: Libra
house_from_d30_lagna: 10
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.MARS
node_type: DVS
node_label: D30 Mars — Gemini H6
varga: D30
planet: PLN.MARS
sign: Gemini
house_from_d30_lagna: 6
note: "In D30 6H Gemini triple-stellium with Saturn and Venus — disease/effort concentration."
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.MERCURY
node_type: DVS
node_label: D30 Mercury — Taurus H5
varga: D30
planet: PLN.MERCURY
sign: Taurus
house_from_d30_lagna: 5
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.JUPITER
node_type: DVS
node_label: D30 Jupiter — Aquarius H2
varga: D30
planet: PLN.JUPITER
sign: Aquarius
house_from_d30_lagna: 2
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.VENUS
node_type: DVS
node_label: D30 Venus — Gemini H6
varga: D30
planet: PLN.VENUS
sign: Gemini
house_from_d30_lagna: 6
note: "In D30 6H triple-stellium — health/aesthetic-system vulnerability marker."
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.SATURN
node_type: DVS
node_label: D30 Saturn — Gemini H6
varga: D30
planet: PLN.SATURN
sign: Gemini
house_from_d30_lagna: 6
note: "Anchors the D30 6H triple-stellium; replicates D1 Saturn-Mars ATT tension into disease varga."
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.RAHU
node_type: DVS
node_label: D30 Rahu — Pisces H3
varga: D30
planet: PLN.RAHU
sign: Pisces
house_from_d30_lagna: 3
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D30.KETU
node_type: DVS
node_label: D30 Ketu — Pisces H3
varga: D30
planet: PLN.KETU
sign: Pisces
house_from_d30_lagna: 3
l1_source: "FORENSIC_v8_0 §3.11"

node_id: DVS.D40.LAGNA
node_type: DVS
node_label: D40 Lagna — Virgo
varga: D40
position_type: lagna
sign: Virgo
lagna_lord: PLN.MERCURY
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.SUN
node_type: DVS
node_label: D40 Sun — Pisces H7
varga: D40
planet: PLN.SUN
sign: Pisces
house_from_d40_lagna: 7
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.MOON
node_type: DVS
node_label: D40 Moon — Aries H8
varga: D40
planet: PLN.MOON
sign: Aries
house_from_d40_lagna: 8
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.MARS
node_type: DVS
node_label: D40 Mars — Aries H8 (own sign)
varga: D40
planet: PLN.MARS
sign: Aries
house_from_d40_lagna: 8
dignity: own_sign
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.MERCURY
node_type: DVS
node_label: D40 Mercury — Scorpio H3
varga: D40
planet: PLN.MERCURY
sign: Scorpio
house_from_d40_lagna: 3
note: "Joined Rahu and Ketu in D40 3H."
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.JUPITER
node_type: DVS
node_label: D40 Jupiter — Taurus H9
varga: D40
planet: PLN.JUPITER
sign: Taurus
house_from_d40_lagna: 9
note: "Jupiter + Venus conjunct in D40 9H — maternal-line auspiciousness signature."
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.VENUS
node_type: DVS
node_label: D40 Venus — Taurus H9 (own sign)
varga: D40
planet: PLN.VENUS
sign: Taurus
house_from_d40_lagna: 9
dignity: own_sign
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.SATURN
node_type: DVS
node_label: D40 Saturn — Virgo H1 (lagna)
varga: D40
planet: PLN.SATURN
sign: Virgo
house_from_d40_lagna: 1
note: "Saturn at D40 Lagna — disciplined channel for auspiciousness varga."
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.RAHU
node_type: DVS
node_label: D40 Rahu — Scorpio H3
varga: D40
planet: PLN.RAHU
sign: Scorpio
house_from_d40_lagna: 3
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D40.KETU
node_type: DVS
node_label: D40 Ketu — Scorpio H3
varga: D40
planet: PLN.KETU
sign: Scorpio
house_from_d40_lagna: 3
l1_source: "FORENSIC_v8_0 §3.12"

node_id: DVS.D45.LAGNA
node_type: DVS
node_label: D45 Lagna — Libra
varga: D45
position_type: lagna
sign: Libra
lagna_lord: PLN.VENUS
note: "FORENSIC notes placeholder Neptune body at D45 Lagna; classical reading uses sign only."
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.SUN
node_type: DVS
node_label: D45 Sun — Sagittarius H3
varga: D45
planet: PLN.SUN
sign: Sagittarius
house_from_d45_lagna: 3
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.MOON
node_type: DVS
node_label: D45 Moon — Sagittarius H3
varga: D45
planet: PLN.MOON
sign: Sagittarius
house_from_d45_lagna: 3
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.MARS
node_type: DVS
node_label: D45 Mars — Cancer H10 (debilitated)
varga: D45
planet: PLN.MARS
sign: Cancer
house_from_d45_lagna: 10
dignity: debilitated
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.MERCURY
node_type: DVS
node_label: D45 Mercury — Taurus H8
varga: D45
planet: PLN.MERCURY
sign: Taurus
house_from_d45_lagna: 8
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.JUPITER
node_type: DVS
node_label: D45 Jupiter — Aquarius H5
varga: D45
planet: PLN.JUPITER
sign: Aquarius
house_from_d45_lagna: 5
note: "Jupiter in D45 5H (purva-punya chamber of spiritual-purity varga)."
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.VENUS
node_type: DVS
node_label: D45 Venus — Aries H7
varga: D45
planet: PLN.VENUS
sign: Aries
house_from_d45_lagna: 7
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.SATURN
node_type: DVS
node_label: D45 Saturn — Capricorn H4 (own sign)
varga: D45
planet: PLN.SATURN
sign: Capricorn
house_from_d45_lagna: 4
dignity: own_sign
note: "Saturn own-sign in D45 4H — stable inner foundation in purity varga."
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.RAHU
node_type: DVS
node_label: D45 Rahu — Sagittarius H3
varga: D45
planet: PLN.RAHU
sign: Sagittarius
house_from_d45_lagna: 3
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D45.KETU
node_type: DVS
node_label: D45 Ketu — Sagittarius H3
varga: D45
planet: PLN.KETU
sign: Sagittarius
house_from_d45_lagna: 3
l1_source: "FORENSIC_v8_0 §3.13"

node_id: DVS.D60.LAGNA
node_type: DVS
node_label: D60 Lagna — Gemini
varga: D60
position_type: lagna
sign: Gemini
lagna_lord: PLN.MERCURY
note: "Mercury-sign lagna in D60 mirrors D1 Mercury-spine across past-karma varga."
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.SUN
node_type: DVS
node_label: D60 Sun — Leo H3 (own sign)
varga: D60
planet: PLN.SUN
sign: Leo
house_from_d60_lagna: 3
dignity: own_sign
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.MOON
node_type: DVS
node_label: D60 Moon — Leo H3
varga: D60
planet: PLN.MOON
sign: Leo
house_from_d60_lagna: 3
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.MARS
node_type: DVS
node_label: D60 Mars — Scorpio H6 (own sign)
varga: D60
planet: PLN.MARS
sign: Scorpio
house_from_d60_lagna: 6
dignity: own_sign
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.MERCURY
node_type: DVS
node_label: D60 Mercury — Aquarius H9
varga: D60
planet: PLN.MERCURY
sign: Aquarius
house_from_d60_lagna: 9
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.JUPITER
node_type: DVS
node_label: D60 Jupiter — Cancer H2 (exalted)
varga: D60
planet: PLN.JUPITER
sign: Cancer
house_from_d60_lagna: 2
dignity: exalted
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.VENUS
node_type: DVS
node_label: D60 Venus — Aquarius H9
varga: D60
planet: PLN.VENUS
sign: Aquarius
house_from_d60_lagna: 9
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.SATURN
node_type: DVS
node_label: D60 Saturn — Gemini H1 (lagna)
varga: D60
planet: PLN.SATURN
sign: Gemini
house_from_d60_lagna: 1
note: "Saturn at D60 Lagna — past-karma chart anchored by Saturn in Mercury-sign; mirrors D1 Mercury-spine."
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.RAHU
node_type: DVS
node_label: D60 Rahu — Cancer H2
varga: D60
planet: PLN.RAHU
sign: Cancer
house_from_d60_lagna: 2
l1_source: "FORENSIC_v8_0 §3.14"

node_id: DVS.D60.KETU
node_type: DVS
node_label: D60 Ketu — Capricorn H8
varga: D60
planet: PLN.KETU
sign: Capricorn
house_from_d60_lagna: 8
note: "Moksha-karaka in D60 8H — past-life renunciative trajectory in transformation chamber of past-karma varga."
l1_source: "FORENSIC_v8_0 §3.14"

# end_node_blocks: CGM_v9_1 — 284 nodes total (v9.0 234 + v9.1 50 DVS D24/D30/D40/D45/D60)

## §6 — DIVISIONAL_TRANSITION Edges (v9.1 — VARGA-ETL-FULL-S1 D13)

Nine edges sourced from FORENSIC §3.15 CSI ledger. Each edge connects a D1 planet
node to its D9 placement node and carries the dignity-shift across the navamsha
transition. These edges are the structural correspondents of SIG.MSR.500–502 and the
§3.15 cross-varga dignity matrix. Edge type extends the existing edge inventory
beyond the 15 DIVISIONAL_CONFIRMATION edges noted in §4.

```yaml
edges:
  - edge_id: EDGE.DT.SUN
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.SUN
    to: DVS.D9.SUN
    properties:
      d1_sign: Capricorn
      d9_sign: Cancer
      dignity_shift: "neutral → neutral (sign change, opposite axis)"
    l1_source: "FORENSIC_v8_0 §3.15 CSI.SUN"

  - edge_id: EDGE.DT.MOON
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.MOON
    to: DVS.D9.MOON
    properties:
      d1_sign: Aquarius
      d9_sign: Gemini
      dignity_shift: "neutral → neutral (sign change; D9 placement is in 12H stellium)"
    l1_source: "FORENSIC_v8_0 §3.15 CSI.MOON, §3.5.2"

  - edge_id: EDGE.DT.MARS
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.MARS
    to: DVS.D9.MARS
    properties:
      d1_sign: Libra
      d9_sign: Pisces
      dignity_shift: "enemy → neutral (D1 Libra is Mars enemy sign — Venus-owned, śatru-kṣetra; D9 Pisces is neutral)"
    l1_source: "FORENSIC_v8_0 §3.15 CSI.MARS"

  - edge_id: EDGE.DT.MERCURY
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.MERCURY
    to: DVS.D9.MERCURY
    properties:
      d1_sign: Capricorn
      d9_sign: Capricorn
      dignity_shift: "vargottama (D1 = D9 sign — sole vargottama planet)"
      vargottama: true
    l1_source: "FORENSIC_v8_0 §3.15 CSI.MERCURY, §3.5.2"

  - edge_id: EDGE.DT.JUPITER
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.JUPITER
    to: DVS.D9.JUPITER
    properties:
      d1_sign: Sagittarius
      d9_sign: Gemini
      dignity_shift: "own_sign → neutral (loss of dignity; D9 placement is in 12H stellium)"
    l1_source: "FORENSIC_v8_0 §3.15 CSI.JUPITER, §3.5.2"

  - edge_id: EDGE.DT.VENUS
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.VENUS
    to: DVS.D9.VENUS
    properties:
      d1_sign: Sagittarius
      d9_sign: Virgo
      dignity_shift: "neutral → debilitated (NBRY active via vargottama Mercury in D9 Kendra)"
      nbr: true
    l1_source: "FORENSIC_v8_0 §3.15 CSI.VENUS, §3.5.1"

  - edge_id: EDGE.DT.SATURN
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.SATURN
    to: DVS.D9.SATURN
    properties:
      d1_sign: Libra
      d9_sign: Aries
      dignity_shift: "exalted → debilitated (NBRY active via Sun in D9 Lagna Cancer Kendra)"
      nbr: true
    l1_source: "FORENSIC_v8_0 §3.15 CSI.SATURN, §3.5.1"

  - edge_id: EDGE.DT.RAHU
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.RAHU
    to: DVS.D9.RAHU
    properties:
      d1_sign: Taurus
      d9_sign: Gemini
      dignity_shift: "neutral → neutral (D9 placement is in 12H stellium)"
    l1_source: "FORENSIC_v8_0 §3.15 CSI.RAHU, §3.5.2"

  - edge_id: EDGE.DT.KETU
    edge_type: DIVISIONAL_TRANSITION
    from: PLN.KETU
    to: DVS.D9.KETU
    properties:
      d1_sign: Scorpio
      d9_sign: Sagittarius
      dignity_shift: "neutral → neutral"
    l1_source: "FORENSIC_v8_0 §3.15 CSI.KETU"
```

Edge inventory update (extends §4): DIVISIONAL_CONFIRMATION (15, prior) +
DIVISIONAL_TRANSITION (9, new v9.1) = 24 divisional-class edges total.
