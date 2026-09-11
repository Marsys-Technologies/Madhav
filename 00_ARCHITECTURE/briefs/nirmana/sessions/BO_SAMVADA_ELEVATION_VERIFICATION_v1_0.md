---
artifact: BO_SAMVADA_ELEVATION_VERIFICATION_v1_0.md
canonical_id: NIRMANA_L2_BO_SAMVADA_ELEVATION_VERIFICATION
version: "1.0"
status: VERIFIED_AND_FROZEN
campaign_id: nirmana-elevation
definition_revision: t2-2026-09-10-057e53eb
asset_id: bo_samvada
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
produced_on: 2026-09-11
---

# `bo_samvada` independent verification

## Verdict

**PASS.** The production result is independently accepted and frozen. The verifier did not
reuse the executor identity and did not infer acceptance from CI, deployment, or run status.

## Release and execution proof

| Proof | Observed result |
|---|---|
| Correct implementation | PR #2591, commit `22df08aaa1f4d408c4475d50312b87b7ce89a71b` |
| Registry migration | `1029_nirmana_l2_bo_samvada_integrity_scope.sql` applied in production |
| Campaign rebuild | `5b06c25b-36ad-44d4-87c2-e0f12edea263`, completed `2026-09-11T10:40:21.699636Z` |
| Run plan digest | `b4f9d69b7c26ea5af599e077cfae77cd4507904df64f3788e7602155a9065497` |
| Asset state | `complete` |
| Provenance | `proven`, `nirmana-provenance-receipt-v2` |
| Output digest | `da7b0ba829b037e4fe599f6f8cae3c8e9ba0c3775e4636322dfb9c9f22345db9` |
| Accepted rebuild event | `1e7b98d7-3e28-4488-b1c4-e22c3bdeb3c7` |
| Independent integrity event | `3e050251-d49e-42aa-841c-b0338c532e20` |
| Freeze event | `87dc6768-47bc-462b-9d56-82b1f7b1260d` |

## Independent checks

- The canonical chart produces exactly five rows, one for each canonical ayanamsha.
- Each current row has at most five `top_convergence_domains` entries; production currently
  returns five on all five ayanamshas.
- Domain eligibility is limited to `static_natal` convergence rows. Ordering is total and
  deterministic: score descending with nulls last, convergence count descending with nulls
  last, then domain ascending.
- `weakest_graha` is independently re-derived from the minimum non-null L1 Shadbala rupa fact,
  with fact-subject ordering as the deterministic tie break. Production currently returns
  `Venus` for all five canonical ayanamshas.
- `top_priority_class` is separately derived from remedy priority rank; production currently
  returns `critical` for all five ayanamshas. The two concepts are not conflated.
- Signal, yoga and dosha counts agree with distinct canonical upstream signal rows.
- Column shape and chart/ayanamsha coverage match the registered contract.
- `CREATE OR REPLACE VIEW` preserves the shared relation; the accepted writer contains no
  `DROP VIEW` path.
- `digest_at` changes at query time because this is a view. It is not represented as the
  upstream computation timestamp; campaign run and provenance receipts are used for freshness.
- `query_ucd` is the registered canonical consumer and enforces chart identity; orientation
  degrades explicitly when the capability fails rather than returning a fabricated full result.

The authoritative production integrity detector returned true and was server-reconstructed as
the verifier. Its result digest is
`145af74fad9a3f6d7ef5d8816007780a11327bce71876ea5e8859fddb512adeb`.

## Scope and limitations

This verification accepts the campaign chart named by the frozen definition. It also relies on
the all-chart `bo_samvada` registry detector because the asset is a shared view and its DDL is not
chart-local. The later L2 layer-wide W5 scope ruling is recorded in the L2 close report; it does
not narrow this asset's stronger all-chart integrity contract.

No live-tracker display state is used as certification evidence.
