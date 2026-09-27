"""R-5 contact identity + R-3 convention frame — PRODUCTION.

Ported from the disposable harness (`evidence_sangam/r5_harness/r5_identity.py`,
design D-R5-1), which qualified this identity against seven §6.3 attack scenarios
(empty rebuild, moved date, split, merge, ambiguous match, interrupted/resumed,
content swap) in Phase 1.  Only the identity functions are ported: the manifest,
replay and comparison machinery stays in the harness, where it belongs.

Why this module exists (synergy audit #6/#10): `contact_uuid` is DEFINED OVER
R-3's six-component frame vector.  Until this file, that vector was emitted
nowhere in the engine or the writer, so R-5's identity could not be computed in
production at all — the reason it lived and died in the harness while the
production key stayed a BIGSERIAL reissued on every rebuild.

The frame is emitted HONESTLY, including where a component is not yet asserted.
A frame that claims `swieph` without reading a return flag would be worse than
one that says `unasserted` — §N.8: a value with no detector behind it is null.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Optional

# Same namespace as the harness: identities computed there and here must agree,
# or Phase 1's qualification does not transfer to production.
R5_NAMESPACE = uuid.UUID("7b2e1c4a-9f3d-4e8b-9a1c-5d6e7f809102")

# ── R-3 convention frame, per component, with its evidence ───────────────────
# ayanamsa_application: transit_search.py:264 passes swe.FLG_SIDEREAL | FLG_SPEED
AYANAMSA_APPLICATION = 'apparent_flg_sidereal'
# epoch_convention: the Saṅgam scan calls swe.calc_ut at the event jd directly
# (transit_search._calc_ut_cached) — it does NOT interpolate ephemeris_daily's
# noon-UT knots. Naming it distinguishes this frame from the knot-spline kernel
# the Gochara stream is building, which is a genuinely different epoch treatment.
EPOCH_CONVENTION = 'direct_swe_calc_ut'
# node_convention: transit_search.py:10,64 scan swe.TRUE_NODE for Rāhu.
# The native's M-1 ruled MEAN. This value is therefore deliberately the HONEST
# one, not the ruled one: it records what the scanner actually did, which is how
# the M-1/scanner mismatch (RRV-16, synergy audit #8) becomes visible in data
# rather than a stamp someone must remember to apply. It changes to 'mean' when
# the N-7 producer replaces the scan — not before.
NODE_CONVENTION_SCANNER = 'true_node'
# ephemeris_backend: R-4 requires this ASSERTED PER CALL from Swiss's return
# flag. `_calc_ut_cached` discards result[1], so nothing asserts it today.
# 'unasserted' is the honest value and is itself the open R-4 detector gap.
EPHEMERIS_BACKEND_UNASSERTED = 'unasserted'
# house_frame: M-1 ruled Placidus-as-stored, but ka_sangam reads no cusp/house
# system at all, so nothing here may claim one.
HOUSE_FRAME_UNAVAILABLE = 'unavailable'


def frame_vector(ayanamsha_id: Optional[str],
                 ephemeris_backend: str = EPHEMERIS_BACKEND_UNASSERTED,
                 epoch_convention: str = EPOCH_CONVENTION,
                 ayanamsa_application: str = AYANAMSA_APPLICATION,
                 node_convention: str = NODE_CONVENTION_SCANNER,
                 house_frame: str = HOUSE_FRAME_UNAVAILABLE) -> tuple:
    """R-3 convention vector — six components; two frames never coalesce."""
    return (ayanamsha_id, ephemeris_backend, epoch_convention,
            ayanamsa_application, node_convention, house_frame)


def frame_dict(fv: tuple) -> dict:
    """The frame as named data, for the row's `convention_frame` column."""
    keys = ('ayanamsha_id', 'ephemeris_backend', 'epoch_convention',
            'ayanamsa_application', 'node_convention', 'house_frame')
    return dict(zip(keys, fv))


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def contact_uuid(chart_id, method_contract_version, graha, target_fact_id,
                 directed_angle_deg, frame_vector6, orb_deg, contact_kind) -> str:
    """D-R5-1 contact identity.

    Deliberately EXCLUDES peak_date, interval endpoints and orb shoulders: those
    are algorithm-versioned CONTENT, not identity. That exclusion is what let the
    harness's "moved date" attack keep a stable id while the content version
    incremented — the property that makes a window citable across a rebuild.
    """
    payload = {
        "chart_id": chart_id,
        "method_contract_version": method_contract_version,
        "graha": graha,
        "target_fact_id": target_fact_id,
        "directed_angle_deg": directed_angle_deg,
        "frame_vector": list(frame_vector6),
        "orb_deg": orb_deg,
        "contact_kind": contact_kind,
    }
    return str(uuid.uuid5(R5_NAMESPACE, canonical_json(payload)))


def independence_group(signal_id, graha, target_fact_id) -> str:
    """Witness-independence key (synergy audit #5).

    Two rows sharing this key rest on the SAME root testimony — the same MSR
    signal, the same graha, the same natal target — and must not be counted as
    independent witnesses of each other. This is the grouping `independent_
    current_count` needs to be interpretable across rows: ICC discounts
    correlated CURRENTS within one row; this key exposes correlation BETWEEN
    rows, which nothing did before.

    Definition recorded here because it is new: a 16-hex digest over the three
    root fields, stable across rebuilds (no surrogate ids, no timestamps).
    """
    payload = canonical_json({
        "signal_id": str(signal_id) if signal_id is not None else None,
        "graha": graha,
        "target_fact_id": target_fact_id,
    })
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
