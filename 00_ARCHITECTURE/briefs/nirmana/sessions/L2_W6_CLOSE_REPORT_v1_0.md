---
artifact: L2_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_V21_L2_W6_CLOSE_REPORT
version: "1.0"
status: CLOSED_READY_FOR_ORDERED_STAGE_RECEIPT
campaign_id: nirmana-elevation
definition_revision: t3-2026-09-11-8b884eac
manifest_sha256: 8b884eac2a950ca1d8d44c3b4af34288b2a7fbc177dba3903da301fad610a0b6
session: L2
layer: L2 — Bodha
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
produced_on: 2026-09-11
---

# L2 — Bodha — W6 close report

## Status

**L2 is ready for the ordered `L2 → L3` stage receipt: all 22 current-definition members have
complete independently frozen lifecycle chains, the campaign-chart W5 gate is green, the
identity audit is clean, and protected main equals the serving runtime at the evidence release
used for this report.**

The stage-spine receipt is deliberately appended after this report reaches protected main and
that exact commit is deployed. The receipt closes L2 and releases the L3 lease; it does not
dispatch, retry, or resume any L3 asset.

## Definition and denominator

- Current frozen definition: `t3-2026-09-11-8b884eac`.
- Manifest digest: `8b884eac2a950ca1d8d44c3b4af34288b2a7fbc177dba3903da301fad610a0b6`.
- Campaign chart: `482012f1-710e-4a25-994a-93821f5871aa`.
- Total manifest: 128 assets; L2 denominator: 22 assets.
- Current effective capsule projection: L0 `40/40`, L1 `19/19`, L2 `22/22` frozen.
- L2's effective total comprises eight t3 freeze rows and 14 legitimate inherited lifecycle
  chains from superseded revisions. This is the server's governed cross-revision rule for
  mid-campaign definition replacement: asset capsules are campaign+asset scoped, while the
  current manifest supplies the denominator. The ordered stage receipt reconstructs this exact
  condition from raw events rather than trusting the projection.
- L2 routes: 9 `changed`, 13 `rebuild_only`; no asset was accepted merely from a green CI run,
  deployment marker, tracker state, or historical freeze count.

The 22 members are `bo_anveshana`, `bo_arudha`, `bo_bimba`, `bo_cdlm_summary`,
`bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`, `bo_drishti`, `bo_karanajala`,
`bo_laksana`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_pramana_mapa`, `bo_pratijna`,
`bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_special_lagna`, `bo_sudarshana`, `bo_upaya`,
`bo_vargottama_dhana`, and `bo_yantra_mechanism`.

`bo_grounding` remains the separately ruled supporting writer and is not a 23rd denominator
member.

## Final W4 corrections and execution

### `bo_samvada`

PR #2588 corrected the ineffective top-five aggregation. PR #2591 corrected weakest-graha
authority, deterministic priority/domain ordering, and destructive shared-view DDL. The accepted
campaign rebuild is `5b06c25b-36ad-44d4-87c2-e0f12edea263`; accepted-rebuild event
`1e7b98d7-3e28-4488-b1c4-e22c3bdeb3c7`, verifier event
`3e050251-d49e-42aa-841c-b0338c532e20`, and freeze event
`87dc6768-47bc-462b-9d56-82b1f7b1260d` complete its chain. Detailed assessment and verification
are in the two companion `BO_SAMVADA_ELEVATION_*_v1_0.md` artifacts.

### L2 dependency correction and stale-reference repair

Definition t3 corrected the shared-MSR consumer order. The remaining production verification
then exposed 11 rerank rows carrying 13 stale contradiction references. PR #2593 fixed
`bo_laksana_rerank` by clearing the scoped contradiction arrays before deterministic
repopulation and ordering the new arrays deterministically.

The repair merged through the protected queue as `c558e60d3267ded79d65fd25f50ee926ce27b75a`.
Merge-group run `34613626460`, protected-push run `34614394432`, and deploy run `34615542574`
all passed. Production served revision `amjis-web-02255-8s6` at 100% traffic, with both commit
label and `NIRMANA_DEPLOYED_SHA` equal to that commit; the pipeline image carried the same SHA.

A fresh pre-rebuild Cloud SQL backup, `1789140844182`, completed successfully. Then:

| Asset | Wave | Accepted run | Output digest | Independent result | Freeze event |
|---|---:|---|---|---|---|
| `bo_laksana_rerank` | 3 | `20764472-4443-4e44-942c-20a7e36d1ef1` | `21cda13e183826cf47fcc53c6778af6e009b0a00019285b11c596dbc0ee15cbf` | Registry detector true; zero stale contradiction edges; zero dangling signal IDs | `4bfa82dd-ef01-426d-8ef1-64fe195c6895` |
| `bo_sangati` | 4 | `8dd3fe42-cc56-4a85-b43e-ab236204a7a1` | `320198ad5659751c12b1ca6cf019fb8902eef05020416bf4465fbf2262a77cab` | Registry detector true; zero dangling canonical CDLM, convergence, or triangulation signal references | `0a564f9e-7d96-44e3-a33f-481c93a090dc` |

The shared-file digest change did not reopen already accepted `bo_laksana`: an independent
review confirmed the changed method is invoked only by the rerank writer, while the canonical
`bo_laksana` registry detector remained true. This preserves unaffected accepted work as the
execution brief requires.

## W5 verification and scope adjudication

### Binding campaign scope

The execution brief explicitly identified that the pre-existing L2 cross-asset SQL scanned all
charts and required this closeout to determine and document the correct scope. The frozen
campaign definition, the autonomous-execution prompt, and the unified plan all name the single
campaign chart `482012f1-710e-4a25-994a-93821f5871aa`.

Under the native's delegated decide-and-log authority, the binding L2 W5 acceptance gate is
therefore the current 22-asset manifest evaluated on that campaign chart. This is an explicit
scope adjudication, not a silent query weakening:

- all 22 manifest registry integrity contracts passed; zero failed, null, or errored;
- all eight cross-asset checks passed on the campaign chart;
- X2 resolved `0/71,586` distinct cited fact IDs incorrectly;
- X3 found `0/50,169` dangling triangulation signal IDs;
- X4 covered five populated ayanamsha scopes with exact nine-graha tiling;
- X5 swept 54,194 rows with only canonical ayanamsha vocabulary;
- X6 swept 50,678 signals with every present bounded value in range;
- X1 passed on 3,276 anomaly rows;
- X7 and X8 were explicitly vacuous on the campaign chart and are not represented as
  substantive evidence.

The unchanged all-chart query remains a supplementary production-data diagnostic. It reports
three red checks exclusively on two noncampaign chart IDs: X2 six distinct fact IDs on
`1c826d5a-41cb-4450-b4dc-59d440e5f75a`; X3 69 distinct signal IDs on that chart; and X8 ten
distinct signal IDs there plus two on `cb73cd3d-9eba-4220-9902-0de91566e980`. Those legacy
partitions were not rebuilt by this single-chart campaign. They remain a named maintenance
backlog and are not erased, repaired by ungoverned destructive SQL, or misreported as green.
The stronger all-chart `bo_samvada` registry contract independently remains green.

### Capsule and identity audit

The campaign audit returned zero frozen assets with incomplete evidence chains and no identity
crossing. Every server-reconstructed integrity/freeze receipt is owned by
`nirmana_evidence_ingress_writer`; executor events are owned by
`nirmana_campaign_control_writer`. Its current layer projection reports L2 `22/22`, 100%.

## Pillar movement

- **Grounding:** the ruled sruti/yukti/pratyaksa machinery and honest downgrade seam exist;
  `bo_grounding` remains supporting rather than inflating the frozen denominator.
- **Synthesis:** corrected agreement, contradiction, convergence, and chart-digest semantics are
  present and independently verified; stale rerank references are gone on the campaign chart.
- **Salience:** corrected salience inputs, percentiles, tail-watch serving, and bounded retrieval
  behavior are live.
- **Time:** no false L2 ownership claim is made; the temporal concordance work remains in later
  layers.
- **Service:** `query_ucd` is the canonical bounded orientation surface with drill-down and
  explicit degraded/error behavior.

## Cost and operational evidence

- Backup `1789140844182`: successful before the destructive shared-MSR rebuild.
- Rerank Cloud Run execution: approximately 92 seconds; proven v2 receipt.
- Sangati Cloud Run execution: approximately 19 seconds; proven v2 receipt.
- `bo_samvada` accepted run: approximately two seconds of recorded run time; proven v2 receipt.
- No L3 retry, resume, or build was dispatched during this closeout.

## Remaining limitations and handoff

- The two noncampaign legacy-chart reference backlogs above remain visible and should be handled
  by a separately authorized multi-chart maintenance/rebuild package with its own blast-radius
  review and recovery proof.
- X7 and X8 are vacuous on the campaign chart; the close claim relies on their honest
  characterization plus the non-vacuous per-asset contracts, not on treating vacuity as proof.
- Live-tracker presentation is intentionally excluded from certification. Database receipts,
  protected Git history, exact deployed runtime, proven output receipts, and independent
  detector observations are authoritative.
- The failed terminal `ka_kshetra` run remains held until the ordered L2→L3 stage receipt. After
  that receipt, only its lease/file ownership may be released; this closeout does not begin L3
  asset work.

## Closure condition

This report plus the protected deployment is the W6 ceremony input. The verifier appends the
ordered foundation/stage receipts against the exact release state; `L2 → L3` is the final L2
closure receipt.
