"""ka_temporal — shared L3 predicate→date resolution helpers (WP-2.1).

Public surface (consumed by ka_kalasutra, ka_vighnakara, and — after the WP-2.1
merge — the WP-2.3-temporal CGM-edge lane for `active_dasha_periods_jsonb`):

    from services.ka_temporal import (
        DashaPeriod,
        ActivationWindows,
        normalize_graha,
        load_dasha_timeline,
        resolve_activation_windows,
    )

See `date_resolver.py` for the full contract + signatures.
"""
from services.ka_temporal.date_resolver import (
    DashaPeriod,
    ActivationWindows,
    normalize_graha,
    sign_lord,
    extract_lords_from_config,
    extract_lords_from_text,
    lord_from_house_varga,
    load_dasha_timeline,
    resolve_birth_date,
    resolve_activation_windows,
)

__all__ = [
    "DashaPeriod",
    "ActivationWindows",
    "normalize_graha",
    "sign_lord",
    "extract_lords_from_config",
    "extract_lords_from_text",
    "lord_from_house_varga",
    "load_dasha_timeline",
    "resolve_birth_date",
    "resolve_activation_windows",
]
