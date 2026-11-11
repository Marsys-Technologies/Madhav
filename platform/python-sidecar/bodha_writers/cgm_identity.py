"""Shared CGM subject and configuration identity for Bodha writers."""

from __future__ import annotations

import re

from brahmagyan.graha_vocabulary import to_title


# L1 fact_subject codes map to canonical CGM graha names.
SUBJECT_TO_GRAHA: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}

YOGA_NODE_CLASSES = ("yoga", "dosha")


def _yoga_config_name(cfg: dict, signal_type_id: str | None) -> str | None:
    """Human name of a yoga/dosha signal (the label the node is titled by). None when the
    configuration names it nowhere and the signal carries no type id (an honest null, never a
    blank label)."""
    for k in ("fact_value_text", "yoga_name", "dosha_name", "name", "label"):
        v = cfg.get(k)
        if v and isinstance(v, str) and v.strip():
            return v.strip()
    return signal_type_id


def yoga_node_subject(sig_class: str, cfg: dict, signal_type_id: str) -> str:
    """Stable node_subject key for a yoga/dosha configuration node.

    Same derivation used by bo_bimba (node creation) and bo_karanajala
    (membership-edge wiring) so both resolve to the same node. Namespaced by
    class to avoid a yoga and a dosha of the same name colliding on the
    (node_type, node_subject) uniqueness key.
    """
    name = _yoga_config_name(cfg, signal_type_id)
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "unnamed"
    return f"{sig_class}:{slug}"
