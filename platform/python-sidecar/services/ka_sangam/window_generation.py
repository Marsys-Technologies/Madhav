"""Saṅgam window composition with caller-owned service and compatibility bindings."""
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from services.ka_sangam.engine import EnrichmentContext, NativeChartContext
    from services.ka_dasha_kala.service import KaDashaKalaService
    from services.ka_gochara.service import KaGocharaService
    from services.ka_muhurta_seva.service import KaMuhurtaSevaService


class WindowBindings(Protocol):
    """Fixed point-of-use bindings supplied by the registered compatibility facade."""

    @property
    def mode_a_search(self) -> Callable[..., list[dict[str, Any]]]: ...

    @property
    def mode_b_sweep(self) -> Callable[..., list[dict[str, Any]]]: ...

    @property
    def mode_c_subsystem_period(self) -> Callable[..., list[dict[str, Any]]]: ...

    @property
    def mode_d_av_bindhu(self) -> Callable[..., list[dict[str, Any]]]: ...

    @property
    def _date_to_jd(self) -> Callable[[date], float]: ...

    @property
    def _mode_d_carrier_index(self) -> Callable[[Sequence[dict[str, Any]]], int | None]: ...

    @property
    def _resolved_target_longitude(self) -> Callable[[dict[str, Any]], float | None]: ...

    @property
    def _target_blank_note(self) -> Callable[[list[dict[str, Any]]], str]: ...

    @property
    def apply_trigger_suppression(self) -> Callable[..., list[dict[str, Any]]]: ...

    @property
    def _SIGN_NAME_TO_IDX(self) -> Mapping[str, int]: ...

    @property
    def SIGNAL_UNRESOLVED(self) -> str: ...

    @property
    def TARGET_UNRESOLVED(self) -> str: ...

    @property
    def logger(self) -> logging.Logger: ...


def generate_windows(
    pred_dicts: Sequence[dict[str, Any]],
    horizon_start: date,
    horizon_end: date,
    dasha_kala_service: KaDashaKalaService,
    gochara_service: KaGocharaService,
    chart_id: str,
    native_ctx: NativeChartContext,
    keepalive: Callable[[], None] | None = None,
    enrichment_context: EnrichmentContext | None = None,
    muhurta_service: KaMuhurtaSevaService | None = None,
    mode_d: bool = True,
    *,
    bindings: WindowBindings,
    publish_target_blanks: Callable[[list[dict[str, Any]]], None],
) -> list[dict[str, Any]]:
    """Run Mode A + Mode B (or Mode C for SUBSYSTEM) for every predicate.

        SUBSYSTEM predicates are routed to mode_c_subsystem_period (sign-ingress
        trigger) instead of the aspect-based Mode A/B engine.
        keepalive: optional callable to prevent idle-in-transaction timeout.
        enrichment_context: EnrichmentContext for U3 current scoring.
        muhurta_service: KaMuhurtaSevaService for panchanga_quality + tara_bala.
        native_ctx: CR-87 — THIS chart's resolved NativeChartContext (janma
          nakshatra, Moon sign, location). Never another chart's values.
        B4-src: stamps primary_domain onto every window dict produced.
        mode_d: whether this call carries the (predicate-agnostic) Mode D set. It rides the first predicate of the
          call that has a signal; the lifetime tier calls once per predicate and passes True for ONE of them only.
        """
    horizon_start_jd = bindings._date_to_jd(horizon_start)
    horizon_end_jd   = bindings._date_to_jd(horizon_end)
    all_windows: list[dict] = []
    blanks: list[dict] = []
    publish_target_blanks(blanks)        # read by the substeps for their notes; one list per call
    # Mode D is sign-level: it is computed once per call, on the first predicate that can be attributed to a signal and reaches the Mode D step.
    mode_d_idx = bindings._mode_d_carrier_index(pred_dicts) if mode_d else None
    mode_d_pred = pred_dicts[mode_d_idx] if mode_d_idx is not None else None

    def _mode_d_windows(pred_dict: dict, primary_domain) -> list[dict]:
        try:
            windows = bindings.mode_d_av_bindhu(
                predicate=pred_dict,
                horizon_start_jd=horizon_start_jd,
                horizon_end_jd=horizon_end_jd,
                gochara_service=gochara_service,
                enrichment_context=enrichment_context,
            )
        except Exception as exc:
            bindings.logger.warning("ka_sangam: Mode D failed for signal %s: %s", pred_dict.get('signal_id'), exc)
            return []
        for w in windows:
            w['primary_domain'] = primary_domain
        return windows

    for pred_dict in pred_dicts:
        sig_id    = pred_dict.get('signal_id')
        sig_class = (pred_dict.get('signature_class') or '').upper()
        # B4-src: primary domain from MSR signal (carried through plan_substeps)
        primary_domain = pred_dict.get('primary_domain')

        if not sig_id:
            blanks.append({'signal_id': None, 'reason': bindings.SIGNAL_UNRESOLVED})
            bindings.logger.info("ka_sangam: predicate blank (%s): no signal_id, nothing attributable to compute", bindings.SIGNAL_UNRESOLVED)
            if keepalive:
                keepalive()
            continue

        # Route SUBSYSTEM predicates to Mode C (period-based ingress trigger)
        if 'SUBSYSTEM' in sig_class:
            try:
                new_windows = bindings.mode_c_subsystem_period(
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    gochara_service=gochara_service,
                    moon_sign=native_ctx.moon_sign,
                    enrichment_context=enrichment_context,
                )
                for w in new_windows:
                    w['primary_domain'] = primary_domain
                all_windows.extend(new_windows)
            except Exception as exc:
                bindings.logger.warning("ka_sangam: Mode C failed for signal %s: %s", sig_id, exc)
            if keepalive:
                keepalive()
            continue

        # D-3 T-6: target_lon feeds TRIGGER's mechanism_lon/target_lon below —
        # same longitude mode_a_search/mode_b_sweep already scan against.
        target_lon = bindings._resolved_target_longitude(pred_dict)
        if target_lon is None:
            # Named blank (SR-K9B-TRIAGE): nothing to scan against, nothing invented. services/ka_sangam/engine.py mode_a_search / mode_b_sweep
            # return no window for a null target on their own; this only stops the float() of None above them. Mode D is sign-level and reads no
            # target, so it still runs for the first predicate of the call exactly as before.
            blanks.append({'signal_id': sig_id, 'reason': bindings.TARGET_UNRESOLVED})
            bindings.logger.info("ka_sangam: signal %s blank (%s): no target longitude", sig_id, bindings.TARGET_UNRESOLVED)
            if keepalive:
                keepalive()
            if pred_dict is mode_d_pred:
                all_windows.extend(_mode_d_windows(pred_dict, primary_domain))
                if keepalive:
                    keepalive()
            continue
        moon_sign_idx = bindings._SIGN_NAME_TO_IDX.get(native_ctx.moon_sign)
        vedha_rules = (enrichment_context.vedha_rules if enrichment_context else None) or None

        try:
            new_windows_a = bindings.mode_a_search(
                predicate=pred_dict,
                horizon_start_jd=horizon_start_jd,
                horizon_end_jd=horizon_end_jd,
                dasha_kala_service=dasha_kala_service,
                gochara_service=gochara_service,
                muhurta_service=muhurta_service,
                chart_id=chart_id,
                janma_nakshatra_idx=native_ctx.janma_nakshatra_idx,
                enrichment_context=enrichment_context,
                native_location=native_ctx.location,
                moon_sign=native_ctx.moon_sign,  # CR-102 fix (T-6): correct house-from-Moon vedha frame
            )
            # D-3 T-6: TRIGGER suppressive term at the ADMITTED 0.2/0.2 weights
            # (wave/D-3/ADMIT, receipted ACCEPT) — see apply_trigger_suppression docstring.
            new_windows_a = bindings.apply_trigger_suppression(
                new_windows_a, chart_id=chart_id, target_lon=target_lon,
                gochara_service=gochara_service, vedha_rules=vedha_rules,
                moon_sign_idx=moon_sign_idx,
            )
            for w in new_windows_a:
                w['primary_domain'] = primary_domain
            all_windows.extend(new_windows_a)
        except Exception as exc:
            bindings.logger.warning("ka_sangam: Mode A failed for signal %s: %s", sig_id, exc)
        if keepalive:
            keepalive()
        try:
            new_windows_b = bindings.mode_b_sweep(
                signal_id=sig_id,
                predicate=pred_dict,
                horizon_start_jd=horizon_start_jd,
                horizon_end_jd=horizon_end_jd,
                gochara_service=gochara_service,
                janma_nakshatra_idx=native_ctx.janma_nakshatra_idx,
                magnitude_threshold=0.3,
                enrichment_context=enrichment_context,
                muhurta_service=muhurta_service,
                native_location=native_ctx.location,
                moon_sign=native_ctx.moon_sign,  # CR-102 fix (T-6): correct house-from-Moon vedha frame
            )
            new_windows_b = bindings.apply_trigger_suppression(
                new_windows_b, chart_id=chart_id, target_lon=target_lon,
                gochara_service=gochara_service, vedha_rules=vedha_rules,
                moon_sign_idx=moon_sign_idx,
            )
            for w in new_windows_b:
                w['primary_domain'] = primary_domain
            all_windows.extend(new_windows_b)
        except Exception as exc:
            bindings.logger.warning("ka_sangam: Mode B failed for signal %s: %s", sig_id, exc)
        if keepalive:
            keepalive()

        # O7: Mode D — SAV-bindhu activation windows for strong signs
        # Only run for the first attributable predicate per horizon call to avoid duplicate windows.
        # Mode D is sign-level and predicate-agnostic; running it for every predicate
        # produces N×K duplicate windows with different signal_ids that bypass the dedup
        # key check (which includes signal_id).
        if pred_dict is mode_d_pred:
            all_windows.extend(_mode_d_windows(pred_dict, primary_domain))
            if keepalive:
                keepalive()
    if blanks:      # the orchestrator does not persist WriterResult.notes (FROZEN contract), so the count is also in the run log
        bindings.logger.info("ka_sangam: %d of %d predicates in this call are blank: %s", len(blanks), len(pred_dicts), bindings._target_blank_note(blanks))
    return all_windows
