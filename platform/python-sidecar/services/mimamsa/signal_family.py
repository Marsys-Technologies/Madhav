"""Signal family classification shared by Mīmāṃsā writers."""


def signal_family_key(sig: dict) -> str | None:
    """
    Map a bodha_msr_signals row to its mimamsa_signal_families family_id.

    The multipliers dict is keyed by target_ref = family_id (e.g. "fam_yoga"),
    NOT by the signal UUID.  This function derives the correct family key from
    the signal's classification attributes so the signal overlay loop can find
    the matching multiplier.

    Mapping (precedence order):
      signal_type_class == "yoga"                   → fam_yoga
      source_subsystem == "yoga"                    → fam_yoga
      source_subsystem == "strength_ashtakavarga"   → fam_ashtakavarga
      source_subsystem == "dasha"                   → fam_dasha_period
      source_subsystem == "varga"                   → fam_divisional
      source_subsystem in ("structural", "nakshatra",
                           "sensitive", "panchanga") → fam_graha_natal
      source_l1_asset == "ga_positions"             → fam_graha_natal
      signal_type_class in ("dignity", "strength",
                            "position", "magnitude") → fam_graha_natal
      signal_type_class == "configuration"          → fam_msr_signal
      (fallback)                                    → fam_msr_signal
    """
    cls = sig.get("signal_type_class", "") or ""
    subsystem = sig.get("source_subsystem", "") or ""
    asset = sig.get("source_l1_asset", "") or ""

    if cls == "yoga" or subsystem == "yoga":
        return "fam_yoga"
    if subsystem == "strength_ashtakavarga":
        return "fam_ashtakavarga"
    if subsystem == "dasha":
        return "fam_dasha_period"
    if subsystem == "varga":
        return "fam_divisional"
    if subsystem in ("structural", "nakshatra", "sensitive", "panchanga"):
        return "fam_graha_natal"
    if subsystem in ("tajaka", "sade_sati"):
        return "fam_transit"
    if "positions" in asset:
        return "fam_graha_natal"
    if cls in ("dignity", "strength", "position", "magnitude"):
        return "fam_graha_natal"
    # configuration / composite / unknown → generic MSR signal family
    return "fam_msr_signal"
