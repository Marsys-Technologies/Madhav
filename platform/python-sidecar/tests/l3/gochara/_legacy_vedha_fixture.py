"""Historical DATE-row fixture for P06 legacy reader/storage contracts.

Archived from accepted P06 b99032fdb's rolling writer. This TEST-ONLY builder
uses live pure/fetch helpers, including the P06 provenance fingerprint; it is
never registered or called by production dispatch. KA-3a deliberately replaced
that dispatch with candidate-only storage, so legacy oracles must explicitly
construct historical rows instead of activating a production fallback.
"""
from services.ka_vedha_gochara import writer
from services.gochara_kernel.node_series_digest import node_series_identity
from services.gochara_kernel.l1_identity import l1_operand_identity
from services.ka_vedha_gochara.writer import (
    ALL_GRAHAS,
    C,
    CANONICAL_AYANAMSHA,
    FORMULA_VERSION,
    HORIZON_BACK_DAYS,
    HORIZON_FORWARD_DAYS,
    HOUSE_VEDHA,
    L1_OPERANDS,
    LATTA,
    NAKSHATRAS,
    NAK_SIZE_DEG,
    SARVATOBHADRA,
    SARVATOBHADRA_CITATION,
    SIGN_SIZE_DEG,
    WriterResult,
    _DELETE_SQL,
    _INSERT_SQL,
    _build_house_vedha_intervals,
    _config_horizon_date,
    _fetch_daily_sidereal_by_body,
    _fetch_janma_moon,
    _fetch_latta_rules,
    _fetch_malefic_scale,
    _fetch_retrograde_dates,
    _fetch_school_tagged_vedha_pair,
    _fetch_vedha_rules,
    _has_complete_daily_series,
    _house_vedha_detail,
    _vedha_independence_group,
    _vedha_pairs_from_db,
    corpus_verifiable_for,
    date,
    detect_sign_runs,
    exception_for_pair,
    house_from_moon,
    house_vedha_uncited_extension,
    is_mutual_exclusion,
    json,
    latta_nakshatra_idx,
    logger,
    opposite_nakshatra_id,
    overlap_window,
    sign_from_house,
    source_qualification_for,
    timedelta,
    upstream_fingerprint,
)


def build_legacy_vedha(ctx) -> WriterResult:
    conn = ctx.db_conn
    chart_id = ctx.config["chart_id"]

    if ctx.dry_run:
        logger.info("[ka_vedha_gochara] dry_run=True — skipping")
        return WriterResult(asset_id="ka_vedha_gochara", rows_inserted=0, notes="dry_run=True")

    janma = _fetch_janma_moon(conn, chart_id)
    if janma is None:
        return WriterResult(
            asset_id="ka_vedha_gochara", rows_inserted=0,
            notes="no natal MOON longitude_sidereal fact — run ga_positions first",
        )
    janma_moon_sign_idx, janma_moon_nak_idx, janma_fact_id = janma

    vedha_rules = _fetch_vedha_rules(conn)
    if not vedha_rules:
        return WriterResult(
            asset_id="ka_vedha_gochara", rows_inserted=0,
            notes="bg_transit_rules has no vedha-checkable (favourable + vedha_house) "
                  "rows — run bg_transit_rules (L0 seed) first",
        )

    # ADJUDICATION-11 Part 4: the two cited-reference tables. Neither being
    # empty is fatal to the whole writer — house_vedha/sarvatobhadra still
    # serve honestly; only the malefic-count grading / latta kind are
    # skipped, each with its own coverage note (never silently degraded).
    malefic_scale = _fetch_malefic_scale(conn)
    latta_rules = _fetch_latta_rules(conn)

    today = date.today()
    # WP9 5.3 (F-11): the caller may pass the REQUESTED horizon explicitly
    # (ctx.config['horizon_start'] / ['horizon_end'], date or ISO string);
    # the ±60/+400 d build window is only the default, never silently
    # treated as the requested coverage.
    horizon_start = _config_horizon_date(ctx.config.get("horizon_start")) or (
        today - timedelta(days=HORIZON_BACK_DAYS)
    )
    horizon_end = _config_horizon_date(ctx.config.get("horizon_end")) or (
        today + timedelta(days=HORIZON_FORWARD_DAYS)
    )

    offset = writer._compute_ayanamsha_offset(today)
    daily_by_body = _fetch_daily_sidereal_by_body(conn, horizon_start, horizon_end, offset, ALL_GRAHAS)
    if not any(daily_by_body.values()):
        return WriterResult(
            asset_id="ka_vedha_gochara", rows_inserted=0,
            notes=f"no ephemeris_daily rows for horizon {horizon_start}..{horizon_end} — "
                  "run bg_ephemeris first",
        )
    incomplete_grahas = [
        graha for graha in ALL_GRAHAS
        if not _has_complete_daily_series(
            daily_by_body.get(graha) or [], horizon_start, horizon_end,
        )
    ]
    if incomplete_grahas:
        return WriterResult(
            asset_id="ka_vedha_gochara",
            rows_inserted=0,
            notes=(
                "incomplete daily ephemeris coverage for " + ",".join(incomplete_grahas)
                + "; prior partition preserved"
            ),
        )

    # §12.9: digest of exactly the reference rows this build consumes, stamped on
    # every house_vedha row so a later re-citation upstream is DETECTABLE.
    # Step 3 §4: the fingerprint also carries the consumed node-series identity
    # (L0-owned node_series_digest_v1), the consumed L1 natal-operand identity and
    # this writer's formula_version — an L1 rebuild, a series change or a version
    # bump alone makes older rows stale. Computed only after every graceful
    # refusal above — an absent node series RAISES here, and that raise must
    # not pre-empt the coverage refusal (spec §7 test 6: no write, no TRUE
    # fallback).
    upstream_fp = upstream_fingerprint(
        vedha_rules, malefic_scale,
        node_series=node_series_identity(conn),
        l1=l1_operand_identity(conn, chart_id, CANONICAL_AYANAMSHA, L1_OPERANDS),
        formula_version=FORMULA_VERSION,
    )

    # Per-graha sign runs and nakshatra runs, computed once and reused by
    # both vedha_kind branches below (no repeat ephemeris derivation).
    retro_dates = _fetch_retrograde_dates(conn, horizon_start, horizon_end, ALL_GRAHAS)
    sign_runs_by_graha: dict[str, list[dict]] = {}
    nak_runs_by_graha: dict[str, list[dict]] = {}
    for graha in ALL_GRAHAS:
        daily = daily_by_body.get(graha) or []
        if not daily:
            continue
        daily_sign = [(d, int(lon // SIGN_SIZE_DEG) % 12) for d, lon in daily]
        daily_nak = [(d, int(lon // NAK_SIZE_DEG) % 27) for d, lon in daily]
        sign_runs_by_graha[graha] = detect_sign_runs(
            daily_sign, horizon_start=horizon_start, horizon_end=horizon_end,
        )
        nak_runs_by_graha[graha] = detect_sign_runs(
            daily_nak, horizon_start=horizon_start, horizon_end=horizon_end,
        )

    # Vedha-target nakshatra: the SBC vedha nakshatra of the janma nakshatra.
    # ADJUDICATION-11 Part 2: THREE tiers, tried in order, each already
    # wired so a future populated source activates with zero code change:
    #   1. bg_sarvatobhadra_grid (school-tagged, migration 529) — the
    #      ruling's own affirmed "DB-sourced-grid-first path".
    #   2. l1_sarvatobhadra_vedha (migration _archive/140, the original
    #      fallback sarvatobhadra.py::find_sarvatobhadra_vedha_states uses).
    #   3. The disclosed algorithmic opposition approximation.
    # As of this writing BOTH DB tables are confirmed empty (see logic.py's
    # R-19 section), so grid_basis='algorithmic_approximation' and
    # grid_school_tag=None on every sarvatobhadra row — machine-readable,
    # per ADJUDICATION-11 Part 3, never prose-only. (opposite_nakshatra_id
    # / _vedha_pairs_from_db / the grid table are all 1-based; convert
    # both ways.)
    grid_school_tag: str | None = None
    grid_pair = _fetch_school_tagged_vedha_pair(conn, janma_moon_nak_idx + 1)
    if grid_pair is not None:
        vedha_nak_idx_1based, grid_school_tag = grid_pair
        grid_basis = "db_sourced_grid"
    else:
        vedha_nak_idx_1based = _vedha_pairs_from_db(conn, janma_moon_nak_idx + 1)
        if vedha_nak_idx_1based is not None:
            grid_basis = "db_sourced_grid"
        else:
            vedha_nak_idx_1based = opposite_nakshatra_id(janma_moon_nak_idx + 1)
            grid_basis = "algorithmic_approximation"
    vedha_nak_idx = vedha_nak_idx_1based - 1

    all_rows: list[dict] = []
    # M-8 (a) coverage: one record per house_vedha transit whose ONLY
    # vedha-house occupancy was by the mutual-exclusion partner — no row
    # is emitted for these (the exception nullifies the vedha itself);
    # the record is what "searched, exception_applied" means for them.
    m8_exceptions: list[dict] = []

    # ── house_vedha ────────────────────────────────────────────────────
    for graha, runs in sign_runs_by_graha.items():
        graha_lower = graha.lower()
        for run in runs:
            house = house_from_moon(run["sign_idx"], janma_moon_sign_idx)
            rule = vedha_rules.get((graha_lower, house))
            if rule is None:
                continue  # not a vedha-checkable transit — out of scope (logic.py)

            vedha_house = int(rule["vedha_house"])
            vedha_sign_idx = sign_from_house(janma_moon_sign_idx, vedha_house)

            # Collect EVERY overlapping occupant; each becomes its own
            # interval relation below (N4: no first-only, no simultaneity
            # collapse).
            occupants: list[tuple[str, dict]] = []
            for other_graha, other_runs in sign_runs_by_graha.items():
                if other_graha == graha:
                    continue
                for other_run in other_runs:
                    if other_run["sign_idx"] != vedha_sign_idx:
                        continue
                    ov = overlap_window(
                        run["start_date"], run["end_date"],
                        other_run["start_date"], other_run["end_date"],
                    )
                    if ov is None:
                        continue
                    occupants.append((other_graha, ov))

            # M-8 evaluation order — exceptions FIRST, then vipareeta.
            # (a) Mutual exclusions (Sun↔Saturn, Moon↔Mercury; Phaladīpikā
            # PG322:C1 / PG323:C1): occupancy of the vedha house by the
            # excluded partner produces NO interval, and never counts
            # toward the malefic census either.
            effective = [(g, ov) for g, ov in occupants if not is_mutual_exclusion(graha, g)]
            excepted = [g for g, _ov in occupants if is_mutual_exclusion(graha, g)]
            if occupants and not effective:
                m8_exceptions.append({
                    "graha": graha,
                    "primary_house": house,
                    "vedha_house": vedha_house,
                    "excluded_obstructors": sorted(set(excepted)),
                    "exception": sorted({
                        exception_for_pair(graha, g) for g in excepted}),
                    "window_start": run["start_date"].isoformat(),
                    "window_end": run["end_date"].isoformat(),
                    "searched": True,
                    "exception_applied": True,
                })
                continue  # no vedha row — the exception nullifies this vedha

            # T0-8: per-obstructor interval relations; vipareeta carved as
            # sub-intervals; per-interval intensity qualifier + group.
            intervals = _build_house_vedha_intervals(
                graha=graha,
                run=run,
                vedha_sign_idx=vedha_sign_idx,
                effective=effective,
                sign_runs_by_graha=sign_runs_by_graha,
                retro_dates=retro_dates,
            )

            uncited = house_vedha_uncited_extension(rule.get("classical_citation"))

            all_rows.append({
                "chart_id": chart_id,
                "ayanamsha_id": CANONICAL_AYANAMSHA,
                "vedha_kind": HOUSE_VEDHA,
                "graha": graha,
                "window_start": run["start_date"],
                "window_end": run["end_date"],
                "start_truncated": run["start_truncated"],
                "end_truncated": run["end_truncated"],
                "janma_reference_fact_id": janma_fact_id,
                "classical_citation": rule.get("classical_citation") or C.PHALADEEPIKA_VEDHA_26,
                # §12.10b / §N.7 item 6: derived from the rule's OWN citation.
                # bg_transit_rules now carries rows declared UNSOURCED (the
                # Rāhu/Ketu house-transit rules); a literal False here stamped
                # them as cited. A missing citation also counts as uncited —
                # the column fallback above satisfies the schema, it does not
                # make the row cited.
                "uncited_extension": uncited,
                # Constraint kala_vedha_gochara_grid_fields_scope: grid_basis/
                # grid_school_tag must be NULL for non-sarvatobhadra rows.
                "grid_basis": None,
                "grid_school_tag": None,
                # WP9 overlay stamps (migration 1082). house_vedha restates a
                # bg_transit_rules row; every stamp below derives from THAT
                # row's own classical_citation (logic.py), not from a constant.
                # Date-grain until kernel ingress instants land.
                "source_qualification": source_qualification_for(
                    HOUSE_VEDHA, None,
                    classical_citation=rule.get("classical_citation"),
                ),
                "precision_regime": "date_grain",
                "corpus_verifiable": corpus_verifiable_for(
                    HOUSE_VEDHA,
                    classical_citation=rule.get("classical_citation"),
                    graha=rule.get("graha"),
                    primary_house=rule.get("primary_house"),
                    vedha_house=rule.get("vedha_house"),
                ),
                "detail": _house_vedha_detail(
                    upstream_fp=upstream_fp,
                    graha=graha,
                    run=run,
                    house=house,
                    vedha_house=vedha_house,
                    vedha_sign_idx=vedha_sign_idx,
                    rule=rule,
                    uncited=uncited,
                    intervals=intervals,
                    excepted=excepted,
                    horizon_start=horizon_start,
                    horizon_end=horizon_end,
                ),
                "formula_version": FORMULA_VERSION,
            })

    # ── sarvatobhadra (R-19; see logic.py for the full honesty disclosure) ──
    # ADJUDICATION-11 Part 3: uncited_extension reflects grid_basis — False
    # (a real, cited source) only when a school-tagged/DB-sourced pair was
    # actually found; True (the current, only-populated state) for the
    # algorithmic approximation. grid_basis/grid_school_tag are
    # machine-readable data fields (never prose-only), so a caller/census
    # can exclude these rows from a "cited" count without parsing text.
    sarvatobhadra_uncited = grid_basis == "algorithmic_approximation"
    r19_disclosure_text = (
        "no SBC grid in the ingested corpus (8 term hits, all "
        "index/OCR/passing-mention); grid geometry varies by tradition; "
        "served value is an algorithmic approximation, not a transcribed "
        "grid."
    ) if sarvatobhadra_uncited else None
    for graha, runs in nak_runs_by_graha.items():
        for run in runs:
            if run["sign_idx"] != vedha_nak_idx:  # field is generically named; holds nak_idx here
                continue
            all_rows.append({
                "chart_id": chart_id,
                "ayanamsha_id": CANONICAL_AYANAMSHA,
                "vedha_kind": SARVATOBHADRA,
                "graha": graha,
                "window_start": run["start_date"],
                "window_end": run["end_date"],
                "start_truncated": run["start_truncated"],
                "end_truncated": run["end_truncated"],
                "janma_reference_fact_id": janma_fact_id,
                "classical_citation": SARVATOBHADRA_CITATION,
                "uncited_extension": sarvatobhadra_uncited,
                # Constraint kala_vedha_gochara_grid_fields_scope: grid_basis
                # must be NOT NULL for sarvatobhadra rows; grid_school_tag
                # is NULL when no school-tagged source was found (the current,
                # only-populated state for the algorithmic approximation).
                "grid_basis": grid_basis,
                "grid_school_tag": grid_school_tag,
                # WP9 overlay stamps (migration 1082): qualification mirrors
                # grid_basis exactly (algorithmic approximation ⟺ the R-19
                # approximation serves the pairing); not corpus-verifiable
                # while that approximation is what is served.
                "source_qualification": source_qualification_for(SARVATOBHADRA, grid_basis),
                "precision_regime": "date_grain",
                "corpus_verifiable": corpus_verifiable_for(SARVATOBHADRA, grid_basis=grid_basis),
                "detail": {
                    "target_nakshatra_idx": janma_moon_nak_idx,
                    "target_nakshatra_name": NAKSHATRAS[janma_moon_nak_idx],
                    "vedha_nakshatra_idx": vedha_nak_idx,
                    "vedha_nakshatra_name": NAKSHATRAS[vedha_nak_idx],
                    "independence_group": _vedha_independence_group(
                        body=graha,
                        relation="sarvatobhadra_vedha",
                        target_deg=vedha_nak_idx * NAK_SIZE_DEG,
                        window_start=run["start_date"],
                    ),
                    "grid_basis": grid_basis,
                    "grid_school_tag": grid_school_tag,
                    "cancellation_effect": (
                        f"While {graha} dwells in {NAKSHATRAS[vedha_nak_idx]} "
                        f"(vedha to the janma nakshatra {NAKSHATRAS[janma_moon_nak_idx]}), "
                        "primary gochara results are classically held to be obstructed."
                    ),
                    "r19_disclosure": r19_disclosure_text,
                },
                "formula_version": FORMULA_VERSION,
            })

    # ── latta (ADJUDICATION-11 Part 4; Phaladeepika PG338-339, REAL,
    # cited; uncited_extension=False) — Ketu is absent from
    # bg_phaladeepika_latta (its own counting rule was not found in the
    # retrieved passage; see brahmagyan/l0_phaladeepika_vedha.py), so
    # `latta_rules.get(graha)` naturally skips it, never guessed.
    for graha, runs in nak_runs_by_graha.items():
        rule = latta_rules.get(graha)
        if rule is None:
            continue  # Ketu, or bg_phaladeepika_latta not yet seeded — honest skip
        for run in runs:
            latta_nak_idx = latta_nakshatra_idx(
                run["sign_idx"], int(rule["count_from_graha"]), str(rule["direction"]),
            )
            if latta_nak_idx != janma_moon_nak_idx:
                continue  # affliction fires only when the Latta point IS the janma nakshatra
            all_rows.append({
                "chart_id": chart_id,
                "ayanamsha_id": CANONICAL_AYANAMSHA,
                "vedha_kind": LATTA,
                "graha": graha,
                "window_start": run["start_date"],
                "window_end": run["end_date"],
                "start_truncated": run["start_truncated"],
                "end_truncated": run["end_truncated"],
                "janma_reference_fact_id": janma_fact_id,
                "classical_citation": rule["source_citation"],
                "uncited_extension": False,
                # Constraint kala_vedha_gochara_grid_fields_scope: grid_basis/
                # grid_school_tag must be NULL for non-sarvatobhadra rows.
                "grid_basis": None,
                "grid_school_tag": None,
                # WP9 overlay stamps (migration 1082): latta restates
                # bg_phaladeepika_latta verbatim (Phaladīpikā PG338-339,
                # REAL cited) — verse-cited and corpus-verifiable today.
                "source_qualification": source_qualification_for(LATTA, None),
                "precision_regime": "date_grain",
                "corpus_verifiable": corpus_verifiable_for(LATTA),
                "detail": {
                    "count_from_graha": int(rule["count_from_graha"]),
                    "direction": rule["direction"],
                    "latta_nakshatra_idx": latta_nak_idx,
                    "latta_nakshatra_name": NAKSHATRAS[latta_nak_idx],
                    "independence_group": _vedha_independence_group(
                        body=graha,
                        relation="latta",
                        target_deg=latta_nak_idx * NAK_SIZE_DEG,
                        window_start=run["start_date"],
                    ),
                    "janma_nakshatra_idx": janma_moon_nak_idx,
                    "janma_nakshatra_name": NAKSHATRAS[janma_moon_nak_idx],
                    "effect_description": rule["effect_description"],
                    "affliction_condition": rule["affliction_condition"],
                },
                "formula_version": FORMULA_VERSION,
            })

    if not all_rows:
        return WriterResult(
            asset_id="ka_vedha_gochara", rows_inserted=0,
            notes="no vedha-checkable house transit and no sarvatobhadra-vedha-nakshatra "
                  f"dwelling found in horizon {horizon_start}..{horizon_end};"
                  f"m8_exceptions={len(m8_exceptions)};"
                  f"m8_exception_windows={json.dumps(m8_exceptions)}",
        )

    # Idempotency: per-chart delete-then-insert (§N.3)
    with conn.cursor() as cur:
        cur.execute(_DELETE_SQL, (chart_id,))

    for row in all_rows:
        row["detail"] = json.dumps(row["detail"])

    with conn.cursor() as cur:
        cur.executemany(_INSERT_SQL, all_rows)

    house_count = sum(1 for r in all_rows if r["vedha_kind"] == HOUSE_VEDHA)
    sbc_count = sum(1 for r in all_rows if r["vedha_kind"] == SARVATOBHADRA)
    latta_count = sum(1 for r in all_rows if r["vedha_kind"] == LATTA)
    logger.info(
        "[ka_vedha_gochara] %d rows (%d house_vedha, %d sarvatobhadra, %d latta) for "
        "chart %s; sbc_grid_basis=%s; m8_exceptions=%d",
        len(all_rows), house_count, sbc_count, latta_count, chart_id, grid_basis,
        len(m8_exceptions),
    )
    return WriterResult(
        asset_id="ka_vedha_gochara", rows_inserted=len(all_rows),
        notes=f"house_vedha={house_count};sarvatobhadra={sbc_count};latta={latta_count};"
              f"grid_basis={grid_basis};m8_exceptions={len(m8_exceptions)};"
              f"m8_exception_windows={json.dumps(m8_exceptions)};"
              f"horizon={horizon_start}..{horizon_end}",
    )
