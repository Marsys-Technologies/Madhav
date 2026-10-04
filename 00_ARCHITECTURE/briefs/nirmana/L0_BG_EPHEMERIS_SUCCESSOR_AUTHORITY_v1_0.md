---
artifact: L0_BG_EPHEMERIS_SUCCESSOR_AUTHORITY
decision_id: NATIVE-2026-10-04-L0-BG-EPHEMERIS-SUCCESSOR
version: "1.0"
status: SUCCESSOR_ADMISSION_AUTHORIZED
produced_by: Exec Suvarṇa (recording the owner's decision, typed by the owner in the Exec Suvarṇa window)
produced_on: 2026-10-04
---

# L0 analysis-layer successor admission for the bg_ephemeris writer digest change (authority record)

status: SUCCESSOR_ADMISSION_AUTHORIZED

## Authority

Decision made by the owner (the native) personally, typed in the Exec Suvarṇa session window on 2026-10-04, after Strategic Suvarṇa put the request packet to the owner (`/Users/Dev/suvarna-evidence/POST/L0_SUCCESSOR_bg_ephemeris/REQUEST.md`, sections 1-7) and after an independent read-only review of pull request 3015 (`REVIEW_3015.md`, verdict APPROVE WITH NITS, status ACCEPTED for the code change). This record states exactly who decided.

## Decision (verbatim)

> I authorise Exec Suvarna to admit an L0 analysis-layer successor for the bg_ephemeris writer digest change in pull request 3015 (writer digest 0d362cef… to ce6750c1…, L0 inventory 082c4bbe… to 92a746ec…, classification approved_intentional_change), including a new authority record with me as the authority, the matching authority and source-commit entries in the pin generator, binding the standing L0 acceptance artifact as the review artifact, to merge that pull request, and to record this decision; I understand the bg_ephemeris Batch A analysis then needs re-acceptance.

## Scope of this authorisation

Exactly one L0 successor admission over the `bg_ephemeris` writer digest move caused by pull request 3015 (classification `approved_intentional_change`):

- writer digest `0d362cef30e7ad50d73aa41d4a485c7388a4012746210696e0a4ac927565f655` to `ce6750c1dbe4c6bc36db4a7efbd1e74f00e534560a69eb6b673f1f88a99e9c45`;
- L0 slice of the writer inventory `082c4bbe8c374313ef8720e7d75ab6e64ad9fb41d4bee6a3a38fcb616fbd23ec` to `92a746ec446ed44e06cccec168d235f5414c441b080d2cf64469eb32cc127620`;
- no membership change; the other 35 `bg_*` writer digests are byte-identical to the active predecessor pin; `receipt_count` stays 40;
- the change is additive: the INSERT, the ON CONFLICT update and the change guard of `ephemeris_daily` gain `node_mode` and `epoch_convention`, which the compute step already emits and production already holds on every row;
- review artifact bound to the admission: the standing L0 acceptance artifact (`MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE_v1_0.md`);
- consequence accepted by the owner: the `bg_ephemeris` Batch A analysis is not valid at the new generation and needs re-acceptance; Batches B, C and E and the other 39 capsules are unaffected.

It does not authorise any other writer change, any other layer's re-pin, any bg_ephemeris RUN, or any production action.

## Procedure bound to this record

`python -m scripts.generate.nirmana_analysis_layer_pins --admit-successor --layer L0 ... --authority-decision NATIVE-2026-10-04-L0-BG-EPHEMERIS-SUCCESSOR --classification bg_ephemeris=approved_intentional_change`, with the standing L0 acceptance artifact as review artifact; verification with `--check` and `--check --delivery-topology`, judged against a clean-main baseline.

## Authority identity

Immutable approval identity (the tip of pull request 3015 at the moment of the owner's approval, which is also the successor's source commit, so what was approved and what is pinned cannot diverge): `149874958e32c1759563e8475ce15853b0912c0c`
