---
artifact: L0_FINDINGS_ADDENDUM
version: "1.0"
status: "LIVING; findings recorded as given; items marked (R) are provisional until the J1 independent review"
produced_by: exec-suvarna
produced_on: 2026-10-02
scope: "docs only; later L0 findings go in this same file"
---

# L0 Brahmagyan findings addendum

## F-L0-01 · The stored Rahu/Ketu daily series is the TRUE node; the house convention is MEAN (R)

Rulings: SS N-68 (house convention stays MEAN, N-57; a MEAN Rahu/Ketu series is ADDED alongside the labelled TRUE one, additive rows with `node_mode='mean'`, TRUE kept as the named variant; every reader pins `node_mode`), N-69 (node standard = MEAN confirmed), N-70 (L0 pin: same-PR transparent re-pin). J1 by name: "node convention in L0 ephemeris".

Finding (measured): `ephemeris_daily` (asset `bg_ephemeris`) stores Rahu as `SE_TRUE_NODE` (`swe_id 11`) and Ketu as TRUE Rahu + 180°, labelled `node_mode='true'`, `epoch_convention='noon_ut'`, `ayanamsha_id='tropical'` on every row, 91,676 rows per body, 1900-01-01..2150-12-31 (`brahmagyan/l0_ephemeris.py:8-15,65-67,96-97,306-314`). The house standard is MEAN node; the gochara kernel pins MEAN (`services/gochara_kernel/knots.py:37-48`). The stored series equals `SE_TRUE_NODE` exactly (0.0000 difference on 14 sampled dates against real Swiss .se1). The two disagree by up to 0.73° (2026-11-18..30, Lahiri sidereal level 300°), and the crossing of sidereal 300° differs by about 10.25 days (TRUE JD 2461370.25, MEAN JD 2461380.5), which made `ka_moorti_nirnaya` raise "Rahu: separation root at 300.0000° lost its bracket" (run b5f5e32d, 2026-10-01).

Effect: a documented deviation from the house standard for every consumer of `ephemeris_daily` Rahu/Ketu that assumes MEAN (the reader census lists 40 readers: 15 Pravāha's, the rest L0 routes and served tools; no L1 writer or L1 service reads the table). Design and rollout: `00_ARCHITECTURE/briefs/suvarna/exec/node_series/DESIGN_L0_MEAN_NODE_SERIES_v1_0.md` (PR #2874). Migrations 1227 (new key), 1228 (integrity contract + digest spec), 1250 (drop the old key) (renumbered 2026-10-02; formerly 1225/1226/1227) are intent only until the owner lifts the migration hold.

## F-L0-02 · The synthetic cohort uses a different node frame from native charts

`pipeline/orchestrator/writers/bg_cohort.py:333` pins `swe.TRUE_NODE`, declared in its own `SAMPLING_METHOD_VERSION = "uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v2"` (:156-159): a documented, versioned frame, but different from native charts (MEAN). `ka_kshetra`'s rarity factor (`services/ka_kshetra/cohort_client.py` `cohort_base_rate()`) compares a native feature against cohort base rates, so for features involving Rahu/Ketu (sign, nakshatra, degree band) the base rate comes from a frame that differs by up to about 1.5°. Bounded and second-order at sign level; none for features that do not involve the nodes. Not needed for S7 (SS). `bg_cohort` is L0, lit (last built 2026-09-07), guarded to Linux/x86_64. Action: a mean-node `..._v3` sampling version post-J1 with the L0 node work (it moves `bg_cohort`'s digest and the L0 pin and needs a cohort rebuild). Disclose meanwhile: "rarity for node-involving features is computed against a TRUE-node cohort".

## F-L0-03 · The Jaimini karaka reference rows carry the old ranks (no reader)

`brahmagyan/l0_reference.py:558-575` (`reference_karakas`, "Chara Jaimini (8)") lists atmakaraka..darakaraka at ranks 1-7 and `strikaraka` as rank 8 ("Co-spouse Significator"; "8-karaka scheme; not used when Rahu excluded") with NO `pitrikaraka`; `brahmagyan/l0_ontology.py:365-373` mirrors the canonical ids. The 8-scheme (BPHS 32.13-17, sourced_ocr_unverified, J1 print-edition check pending) is ATMA, AMATYA, BHRATRI, MATRI, PITRI, PUTRA, GNATI, DARA. Readers: none by SELECT in the sidecar or the TS tiers (the L0 writer inserts, `l0_ontology` mirrors ids, one comment in `bo_pratijna_karyatva.py:251`, the ownership-preflight table list); no L1 or L2 reader takes karaka role names from those rows. Not traced: generic L0 reference tools that serve rows by table name. Disposition (SS): fixed with the L0 node work after J1 (an L0 digest move is not worth it now).
