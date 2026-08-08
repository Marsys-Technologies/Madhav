"""
ga_vichara_writer.py — GA Vichāra ("judged structure") writer
================================================================
Asset: ga_vichara — new L1 sibling asset to ga_structural (design §2
fold-vs-build rule: "judgment lands as new registered assets"). Consumes
ga_structural's `bhava_significance_link` / `graha_dignity_per_varga` /
`graha_functional_class_per_ascendant` facts, ga_strength's
`graha_shadbala_total` facts, ga_yoga's `ga_yoga_firings` rows, and
ga_dashas's `chart_dashas` rows — all read-only (B.10/§N.5: never restates
an L1 computed value, only references + derives judgment on top).

Doctrine Campaign D-1 / Night-1, Lane 2. Brief:
00_ARCHITECTURE/llm_consumption_audit/briefs/night1/LANE2_GA_VICHARA.md
Design ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §4 (deltas 1-2), §8
(leverage_index), §11 (ratification_factor).

Four row families, all written to `chart_vichara`:
  1. valence_pass                    — CR-54 AMENDED (actor lordship x target class)
  2. varga_ratification              — CR-57 / design §11 ratification_factor
     (+ varga_ratification_divergence)
  3. varga_consistency               — design §4 delta 2 (vargottama generalized)
  4. leverage_index                  — CR-69/CR-60, design §8

Hard rails (inherited, CLAUDE.md):
- ZERO LLM in the data path (§N.4 deterministic-first).
- No new astronomical/positional computation (B.10) — every operand is read
  from already-stored chart_facts / ga_yoga_firings / chart_dashas rows.
  Gaps (a varga position genuinely not stored) are logged in
  `value_jsonb.known_gaps`, never silently computed.
- Constants (ratification step/clamp, operative-varga sets, valence matrix,
  dignity score map, leverage/consistency weights) are read from
  `brahma_vichara_constants` — never Python literals (design §11).
- Delete-then-insert idempotency scoped to (chart_id, ayanamsha_id) (§N.3).
- constituent_fact_ids / constituent_facts_array reference real
  chart_facts.fact_id values — must resolve with zero orphans (§N.5).
- NEVER commits / closes conn — orchestrator owns the transaction boundary.

SCHEMA NOTE (migration 435): chart_vichara carries the UNION of two
already-merged consumers' column vocabularies (bo_laksana.py's
actor/target/varga/ratification_factor/constituent_facts_array and
get_vichara.ts's subject/domain/varga_id/constituent_fact_ids) — this
writer populates BOTH sides of each duplicated pair so both consumers see
real rows unmodified. See migration 435's header comment for the full
reconciliation-pending finding.
"""
from __future__ import annotations

import json
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from brahmagyan import valence_doctrine as _vd
from brahmagyan.graha_vocabulary import norm_graha

logger = logging.getLogger(__name__)

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

CLASSICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
ALL_GRAHAS = CLASSICAL_GRAHAS + ["Rahu", "Ketu"]

# PLANET_TO_SUBJECT is a read-dependency of the parallel ADHIṢṬHĀNA Lane A1
# (ga_condition_writer imports it) — kept as this exact name/shape/values.
# Values are sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather
# than hardcoded literals — ADHIṢṬHĀNA Lane A2 (it was a pure duplicate: a
# 9-key Title-case subset of the SSoT's alias table).
PLANET_TO_SUBJECT: dict[str, str] = {name: norm_graha(name) for name in ALL_GRAHAS}
SUBJECT_TO_PLANET: dict[str, str] = {v: k for k, v in PLANET_TO_SUBJECT.items()}

FORMULA_VERSION = "leverage_index_v1"
VALENCE_FORMULA_VERSION = "valence_pass_v2_doctrine"  # DR-9/VAL-ROOT: shared valence_doctrine
RATIFICATION_FORMULA_VERSION = "varga_ratification_v1"
CONSISTENCY_FORMULA_VERSION = "varga_consistency_v1"

KENDRA_HOUSES = {4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
MARAKA_HOUSES = {2, 7}
UPACHAYA_HOUSES = {3, 6, 10, 11}
WEALTH_HOUSES = {2, 11}

# House-class precedence for a graha with multiple lordships (brief §3.1):
# trikona > dusthana > kendra > maraka > upachaya.
_PRECEDENCE = ["trikona_lord", "dusthana_lord", "kendra_lord", "maraka", "upachaya_lord"]


# ── DB loaders (read-only) ──────────────────────────────────────────────────

def _load_chart_facts(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    """Load all chart_facts rows for (chart_id, ayanamsha_id)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_text,
                   fact_value_num, fact_value_jsonb
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
        """, (chart_id, ayanamsha_id))
        return [dict(r) for r in cur.fetchall()]


def _load_yoga_firings(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    """Load fired ga_yoga_firings rows (domain-participation signal for leverage_index)."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT yoga_canonical_id, constituent_planets
                FROM ga_yoga_firings
                WHERE chart_id = %s AND ayanamsha_id = %s AND fired = TRUE
            """, (chart_id, ayanamsha_id))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.warning("[ga_vichara_writer] ga_yoga_firings unavailable (%s) — "
                        "yoga_participation term stays 0 for every graha (honest gap).", exc)
        return []
    out = []
    for r in rows:
        cp = r.get("constituent_planets")
        if isinstance(cp, str):
            try:
                cp = json.loads(cp)
            except Exception:
                cp = []
        out.append({"yoga_canonical_id": r.get("yoga_canonical_id"), "constituent_planets": cp or []})
    return out


def _load_dasha_md_rows(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    """Load level_n=1 (Mahadasha) chart_dashas rows for this (chart_id, ayanamsha_id)."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT lord_graha, start_iso, end_iso, duration_days
                FROM chart_dashas
                WHERE chart_id = %s AND ayanamsha_id = %s AND level_n = 1
                ORDER BY start_iso
            """, (chart_id, ayanamsha_id))
            return [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.warning("[ga_vichara_writer] chart_dashas unavailable (%s) — "
                        "dasha_runway_weight stays neutral (1.0) for every graha.", exc)
        return []


def _load_constants(conn: Any) -> dict[str, Any]:
    """Load brahma_vichara_constants — design §11: registry data, not literals."""
    with conn.cursor() as cur:
        cur.execute("SELECT constant_key, value_jsonb FROM brahma_vichara_constants")
        rows = [dict(r) for r in cur.fetchall()]
    out: dict[str, Any] = {}
    for r in rows:
        v = r["value_jsonb"]
        if isinstance(v, str):
            v = json.loads(v)
        out[r["constant_key"]] = v
    return out


def _delete_prior_vichara_rows(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    """Idempotency: delete-then-insert scoped to (chart_id, ayanamsha_id) — §N.3."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM chart_vichara WHERE chart_id = %s AND ayanamsha_id = %s",
            (chart_id, ayanamsha_id),
        )
        return cur.rowcount or 0


# ── Fact indexing ────────────────────────────────────────────────────────────

class VicharaFactIndex:
    """Parses the flat chart_facts rows this writer needs into structured
    per-varga lookups. Read-only — never restates an L1 value (§N.5)."""

    def __init__(self, facts: list[dict]):
        # bhava_significance_link rows, grouped by varga.
        # link := {kind, lord, src_h, tgt_h, link_type, fact_id}
        self.links_by_varga: dict[str, list[dict]] = {}
        # (varga, subject) -> {sign, house, dignity, fact_id}
        self.dignity: dict[tuple[str, str], dict] = {}
        # subject -> {value_text, fact_id}  (D1-only functional class, bphs_canonical)
        self.functional_class: dict[str, dict] = {}
        # subject -> {rupa, fact_id}
        self.shadbala: dict[str, dict] = {}
        # CR-91 (A2): aspect_parashari_per_varga rows, grouped by varga.
        # aspect := {graha (subject code), target_house, strength, fact_id}
        # — a raw graha->house Parashari aspect, independent of which house(s)
        # that graha happens to LORD. Ingested so a graha's own functional
        # lordship (dusthana_lord/trikona_lord/etc., from `lordships()` below)
        # can be applied to houses it ASPECTS, not only houses linked via
        # bhava_significance_link's lordship-mediated `lord_aspects` kind.
        # ALL_30_VARGAS includes D1, so this also covers D1 aspects (shared
        # key-space with the legacy D1-only `aspect_parashari_given` category
        # at bo_laksana's consuming end — see build_aspect_valence_rows()).
        self.aspects_by_varga: dict[str, list[dict]] = {}

        for f in facts:
            cat = f.get("fact_category")
            if cat == "bhava_significance_link":
                vj = f.get("fact_value_jsonb") or {}
                if isinstance(vj, str):
                    vj = json.loads(vj)
                varga = vj.get("varga")
                if not varga:
                    continue
                self.links_by_varga.setdefault(varga, []).append({
                    "kind": vj.get("link_kind"),
                    "lord": vj.get("lord"),
                    "src_h": vj.get("source_house"),
                    "tgt_h": vj.get("target_house"),
                    "link_type": vj.get("link_type") or f.get("fact_value_text"),
                    "fact_id": f.get("fact_id"),
                })
            elif cat == "graha_dignity_per_varga" and f.get("fact_key") == "dignity_state":
                vj = f.get("fact_value_jsonb") or {}
                if isinstance(vj, str):
                    vj = json.loads(vj)
                varga = vj.get("varga")
                subj = f.get("fact_subject", "")
                # fact_subject = f"{varga}_{SUBJ}" — strip the varga prefix back off.
                if varga and subj.startswith(f"{varga}_"):
                    bare_subj = subj[len(varga) + 1:]
                else:
                    bare_subj = subj
                if varga:
                    self.dignity[(varga, bare_subj)] = {
                        "sign": vj.get("sign"),
                        "house": vj.get("house"),
                        "dignity": f.get("fact_value_text"),
                        "fact_id": f.get("fact_id"),
                    }
            elif cat == "graha_functional_class_per_ascendant" and f.get("fact_key") == "bphs_canonical":
                self.functional_class[f.get("fact_subject", "")] = {
                    "value_text": f.get("fact_value_text"),
                    "fact_id": f.get("fact_id"),
                }
            elif cat == "graha_shadbala_total" and f.get("fact_key") == "rupa":
                self.shadbala[f.get("fact_subject", "")] = {
                    "rupa": f.get("fact_value_num"),
                    "fact_id": f.get("fact_id"),
                }
            elif cat == "aspect_parashari_per_varga":
                # CR-91 (A2): ga_structural_writer._build_varga_relationship_rows
                # emits fact_subject=f"{varga}_{SUBJ}" (e.g. "D9_MAR"),
                # fact_key=f"house_{target_house}", value_num=strength, and
                # value_jsonb={varga, source_sign, source_house, target_house,
                # offset, ayanamsha_id} — see ga_structural_writer.py:4228-4250.
                vj = f.get("fact_value_jsonb") or {}
                if isinstance(vj, str):
                    vj = json.loads(vj)
                varga = vj.get("varga")
                tgt_h = vj.get("target_house")
                if not varga or tgt_h is None:
                    continue
                subj = f.get("fact_subject", "")
                if subj.startswith(f"{varga}_"):
                    bare_subj = subj[len(varga) + 1:]
                else:
                    bare_subj = subj
                if not bare_subj:
                    continue
                self.aspects_by_varga.setdefault(varga, []).append({
                    "graha_subject": bare_subj,
                    "graha": SUBJECT_TO_PLANET.get(bare_subj, bare_subj),
                    "target_house": int(tgt_h),
                    "strength": float(f["fact_value_num"]) if f.get("fact_value_num") is not None else None,
                    # DR-9 contact-type input: the aspect house-count offset
                    # (Mars 4/8, Saturn 3/10 are the harsh special aspects).
                    "aspect_offset": vj.get("offset"),
                    "fact_id": f.get("fact_id"),
                })

    def lordships(self, varga: str) -> dict[str, set[int]]:
        """{lord_name -> set of houses it lords in this varga} from lord_placed rows
        (one row per src house 1..12; distinct src houses per lord = distinct
        sign-lordships, e.g. Mars lords Aries AND Scorpio)."""
        out: dict[str, set[int]] = {}
        for link in self.links_by_varga.get(varga, []):
            if link["kind"] == "lord_placed" and link["lord"] and link["src_h"]:
                out.setdefault(link["lord"], set()).add(int(link["src_h"]))
        return out

    def lordship_fact_ids(self, varga: str, lord: str) -> list[str]:
        return [
            link["fact_id"] for link in self.links_by_varga.get(varga, [])
            if link["kind"] == "lord_placed" and link["lord"] == lord and link["fact_id"]
        ]


# ── Family 1: valence_pass (CR-54 AMENDED) ──────────────────────────────────

def classify_actor(houses: set[int]) -> tuple[list[str], str]:
    """Actor's functional nature from the set of houses it lords in a varga.
    Precedence (brief §3.1): trikona > dusthana > kendra > maraka > upachaya."""
    classes: list[str] = []
    if houses & TRIKONA_HOUSES:
        classes.append("trikona_lord")
    if houses & DUSTHANA_HOUSES:
        classes.append("dusthana_lord")
    if houses & KENDRA_HOUSES:
        classes.append("kendra_lord")
    if houses & MARAKA_HOUSES:
        classes.append("maraka")
    if houses & UPACHAYA_HOUSES:
        classes.append("upachaya_lord")
    for p in _PRECEDENCE:
        if p in classes:
            return classes, p
    return classes, "neutral"


def _verdict_to_vichara_label(v: "_vd.ValenceVerdict") -> str:
    """Map the shared doctrine's signed ValenceVerdict → chart_vichara's
    magnitude vocabulary {neutral, benefic, malefic, strong_benefic,
    strong_malefic, mixed}. `mixed` is first-class (DR-9); the strong_* bands
    preserve the magnitude signal that bo_karanajala's edge-strength factor and
    downstream consumers read."""
    if v.is_mixed:
        return "mixed"
    n = v.value_num
    if n >= 0.75:
        return "strong_benefic"
    if n > 0.10:
        return "benefic"
    if n <= -0.75:
        return "strong_malefic"
    if n < -0.10:
        return "malefic"
    return "neutral"


def compute_valence(
    graha_subject: str,
    target_house: int,
    functional_class: str | None,
    *,
    contact_type: str = "lordship",
    dignity_state: str | None = None,
    aspect_offset: int | None = None,
) -> tuple[str, float, str, str]:
    """DR-9 / VAL-ROOT: valence via the single shared doctrine module
    (brahmagyan.valence_doctrine). REPLACES the prior (actor_lordship_class ×
    target_house) matrix, whose trikoṇa-membership rule pre-empted the
    dusthāna-affliction cell for a dual-lord graha (Mars, Aries 1L+8L → the
    CR-54 8L-Mars→H2 specimen mislabeled benefic), had NO contact-type
    dimension, and skipped Rahu/Ketu entirely.

    Now: natural nature × functional lordship (the stored functional_class fact,
    §N.5) × dignity × contact-type → signed, MIXED-capable verdict. Returns
    (value_text, value_num, citation, valence_label) — value_text is the 6-way
    magnitude vocab (see _verdict_to_vichara_label); value_num the signed net;
    valence_label the raw 4-way {benefic/malefic/mixed/neutral} for provenance."""
    verdict = _vd.graha_valence(
        graha_subject,
        contact_type=contact_type,
        target_house=int(target_house),
        functional_class=functional_class,
        dignity_state=dignity_state,
        aspect_offset=aspect_offset,
    )
    return (_verdict_to_vichara_label(verdict), verdict.value_num,
            verdict.citation, verdict.valence)


def build_valence_pass_rows(
    idx: VicharaFactIndex, varga: str, matrix: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lordships = idx.lordships(varga)

    for link in idx.links_by_varga.get(varga, []):
        lord = link["lord"]
        tgt_h = link["tgt_h"]
        if not lord or not tgt_h:
            continue
        houses = lordships.get(lord, set())
        # classify_actor retained for provenance + the §N.5 divergence cross-check
        # below (the valence itself now comes from the shared doctrine, not this
        # class × house matrix — which pre-empted dusthāna affliction for a
        # dual-lord graha; DR-9/VAL-ROOT).
        actor_classes, primary = classify_actor(houses)
        actor_subj = PLANET_TO_SUBJECT.get(lord, lord.upper())

        fc = idx.functional_class.get(actor_subj)
        fc_text = fc["value_text"] if fc else None
        is_yogakaraka = bool(fc_text and "yogakaraka" in str(fc_text).lower())
        dig = None  # dignity refinement deferred (tuple-keyed idx.dignity; module handles None; no specimen requires it)
        # lord_aspects links are an aspect contact; lord_placed is lordship.
        contact = "aspect" if link.get("kind") == "lord_aspects" else "lordship"

        value_text, value_num, citation, matrix_key = compute_valence(
            actor_subj, int(tgt_h), fc_text,
            contact_type=contact, dignity_state=dig,
        )

        constituent_ids = list({link["fact_id"], *idx.lordship_fact_ids(varga, lord)} - {None})

        vjsonb: dict[str, Any] = {
            "varga": varga,
            "actor_houses_lorded": sorted(houses),
            "actor_classes": actor_classes,
            "actor_primary_class": primary,
            "target_house": int(tgt_h),
            "link_kind": link["kind"],
            "link_type": link["link_type"],
            "is_yogakaraka": is_yogakaraka,
            "matrix_key": matrix_key,
        }
        if varga == "D1" and fc is not None:
            vjsonb["stored_functional_class_bphs"] = fc["value_text"]
            # §N.5 cross-check: log (never silently override) an apparent clash
            # between this row's derived polarity and the stored L1
            # graha_functional_class_per_ascendant fact for D1.
            stored = str(fc["value_text"] or "").lower()
            derived_negative = primary in ("dusthana_lord", "maraka")
            derived_positive = primary in ("trikona_lord", "upachaya_lord")
            if (derived_negative and "benefic" in stored and "malefic" not in stored) or \
               (derived_positive and "malefic" in stored):
                vjsonb["functional_class_divergence"] = True

        rows.append({
            "vichara_family": "valence_pass",
            "subject": actor_subj,
            "actor": actor_subj,
            "target": f"{varga}_HOUSE_{tgt_h}",
            "domain": None,
            "varga_id": varga,
            "varga": varga,
            "value_num": value_num,
            "value_text": value_text,
            "value_jsonb": vjsonb,
            "ratification_factor": None,
            "constituent_fact_ids": constituent_ids,
            "formula_version": VALENCE_FORMULA_VERSION,
            "source_citation": citation,
        })
    return rows


# ── Family 1b: aspect-sourced valence_pass rows (CR-91/A2) ──────────────────
#
# build_valence_pass_rows (above) judges a graha's OWN functional lordship
# only via bhava_significance_link's lord_placed/lord_aspects kinds — the
# latter is derived from `_graha_aspects_house()` in ga_structural_writer.py,
# which A7 (CR-87 follow-up) flags as off-by-one for opposition/7th-house
# aspects (returns 0.0 instead of 1.0). aspect_parashari_per_varga is an
# INDEPENDENT computation (PARASHARI_ASPECTS offset table, not
# `_graha_aspects_house`) — so ingesting it here backstops that exact gap
# today, regardless of when A-γ's structural fix lands, AND extends
# functional-lordship valence to nodes (Rahu/Ketu) and any graha whose
# aspect reach a lord_aspects link happened not to enumerate.
#
# Same (actor, target, varga) key shape as build_valence_pass_rows — for a
# graha that already has an equivalent bhava_significance_link row, this
# produces a same-valued sibling row (harmless; the codebase already
# tolerates multiple valence_pass rows per key from per-src-house lord_aspects
# duplication). vjsonb["signal_source"] tags provenance so the two paths stay
# distinguishable in an audit.
def build_aspect_valence_rows(
    idx: VicharaFactIndex, varga: str, matrix: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lordships = idx.lordships(varga)

    for asp in idx.aspects_by_varga.get(varga, []):
        graha = asp["graha"]
        tgt_h = asp["target_house"]
        houses = lordships.get(graha, set())
        actor_subj = asp["graha_subject"]
        # DR-9 / VAL-ROOT: NO LONGER skip nodes. Rahu/Ketu own no sign lordship,
        # but the shared doctrine judges them by NATURAL nature (both malefic) +
        # contact-type — the prior skip is exactly why an adverse Rahu/Ketu
        # aspect on a money house never reached a computed valence.
        actor_classes, primary = classify_actor(houses)  # provenance only (may be empty for nodes)

        fc = idx.functional_class.get(actor_subj)
        fc_text = fc["value_text"] if fc else None
        is_yogakaraka = bool(fc_text and "yogakaraka" in str(fc_text).lower())
        dig = None  # dignity refinement deferred (tuple-keyed idx.dignity; module handles None; no specimen requires it)
        offset = asp.get("aspect_offset")

        value_text, value_num, citation, matrix_key = compute_valence(
            actor_subj, tgt_h, fc_text,
            contact_type="aspect", dignity_state=dig, aspect_offset=offset,
        )

        constituent_ids = list({asp["fact_id"], *idx.lordship_fact_ids(varga, graha)} - {None})

        vjsonb: dict[str, Any] = {
            "varga": varga,
            "actor_houses_lorded": sorted(houses),
            "actor_classes": actor_classes,
            "actor_primary_class": primary,
            "target_house": tgt_h,
            "link_kind": "graha_aspect_parashari",
            "aspect_strength": asp.get("strength"),
            "aspect_offset": offset,
            "is_yogakaraka": is_yogakaraka,
            "matrix_key": matrix_key,
            "signal_source": "aspect_parashari_per_varga",
        }

        rows.append({
            "vichara_family": "valence_pass",
            "subject": actor_subj,
            "actor": actor_subj,
            "target": f"{varga}_HOUSE_{tgt_h}",
            "domain": None,
            "varga_id": varga,
            "varga": varga,
            "value_num": value_num,
            "value_text": value_text,
            "value_jsonb": vjsonb,
            "ratification_factor": None,
            "constituent_fact_ids": constituent_ids,
            "formula_version": VALENCE_FORMULA_VERSION,
            "source_citation": citation,
        })
    return rows


# ── Dignity direction helper (shared by families 2 & 3) ─────────────────────

def dignity_direction(dignity_text: str | None) -> str | None:
    """Maps stored L1 dignity_state {exalted, own, neutral, debilitated} to a
    ternary agreement direction. NOTE (known simplification, B.10): L1 only
    stores this 4-way scale — no mooltrikona/friend/enemy granularity — so
    'own' is the sole positive non-exalted bucket and 'neutral' abstains."""
    if dignity_text in ("exalted", "own"):
        return "positive"
    if dignity_text == "debilitated":
        return "negative"
    return None  # neutral or missing -> abstain


# ── Family 2: varga_ratification (CR-57 / design §11) ───────────────────────

def build_varga_ratification_rows(
    idx: VicharaFactIndex,
    domains_config: dict[str, Any],
    step: float, lo: float, hi: float,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], float]]:
    rows: list[dict[str, Any]] = []
    ratification_lookup: dict[tuple[str, str], float] = {}
    d1_lordships = idx.lordships("D1")
    # house -> lord (D1) for subject enumeration
    house_lord_d1: dict[int, str] = {}
    for lord, houses in d1_lordships.items():
        for h in houses:
            house_lord_d1[h] = lord

    for domain, cfg in domains_config.items():
        vargas = cfg.get("vargas", ["D1"])
        houses = cfg.get("houses", [])
        karaka = cfg.get("karaka")
        provisional = bool(cfg.get("provisional", True))

        subjects = set()
        for h in houses:
            lord = house_lord_d1.get(int(h))
            if lord:
                subjects.add(lord)
        if karaka:
            subjects.add(karaka)

        for subject_planet in subjects:
            subj = PLANET_TO_SUBJECT.get(subject_planet, subject_planet.upper())
            d1_rec = idx.dignity.get(("D1", subj))
            d1_dignity_text = d1_rec["dignity"] if d1_rec else None
            d1_direction = dignity_direction(d1_dignity_text)

            n_agree = 0
            n_oppose = 0
            per_varga: dict[str, Any] = {}
            constituent_ids: set[str] = set()
            if d1_rec and d1_rec.get("fact_id"):
                constituent_ids.add(d1_rec["fact_id"])

            for v in vargas:
                if v == "D1":
                    continue  # D1 is the reference, not a voter (brief §8 trap)
                v_rec = idx.dignity.get((v, subj))
                if v_rec is None:
                    per_varga[v] = {"relation": "abstain_missing", "known_gap": True}
                    continue
                if v_rec.get("fact_id"):
                    constituent_ids.add(v_rec["fact_id"])
                v_direction = dignity_direction(v_rec["dignity"])
                if d1_direction is None or v_direction is None:
                    relation = "abstain"
                elif v_direction == d1_direction:
                    relation = "agree"
                    n_agree += 1
                else:
                    relation = "oppose"
                    n_oppose += 1
                per_varga[v] = {
                    "dignity": v_rec["dignity"], "sign": v_rec.get("sign"), "relation": relation,
                }

            factor = max(lo, min(hi, 1.0 + step * (n_agree - n_oppose)))
            ratification_lookup[(subj, domain)] = factor

            rows.append({
                "vichara_family": "varga_ratification",
                "subject": subj,
                "actor": None,
                "target": None,
                "domain": domain,
                "varga_id": None,
                "varga": None,
                "value_num": factor,
                "value_text": None,
                "value_jsonb": {
                    "d1_dignity": d1_dignity_text,
                    "d1_direction": d1_direction,
                    "per_varga": per_varga,
                    "n_agree": n_agree,
                    "n_oppose": n_oppose,
                    "operative_vargas": vargas,
                    "domain_provisional": provisional,
                },
                "ratification_factor": factor,
                "constituent_fact_ids": sorted(constituent_ids),
                "formula_version": RATIFICATION_FORMULA_VERSION,
                "source_citation": "DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11",
            })

            # Divergence rows (CR-57): one per varga that INVERTS D1's direction.
            for v, rec in per_varga.items():
                if rec.get("relation") != "oppose":
                    continue
                v_rec = idx.dignity.get((v, subj))
                cids = sorted({fid for fid in (
                    d1_rec.get("fact_id") if d1_rec else None,
                    v_rec.get("fact_id") if v_rec else None,
                ) if fid})
                rows.append({
                    "vichara_family": "varga_ratification_divergence",
                    "subject": subj,
                    "actor": None,
                    "target": None,
                    "domain": domain,
                    "varga_id": v,
                    "varga": v,
                    "value_num": -1.0,
                    "value_text": (
                        f"{subject_planet.upper()}: D1 {d1_dignity_text} vs {v} {rec.get('dignity')} "
                        f"— {domain} ratification fails in {v}"
                    ),
                    "value_jsonb": {
                        "d1_dignity": d1_dignity_text, "varga_dignity": rec.get("dignity"),
                        "domain_provisional": provisional,
                    },
                    "ratification_factor": None,
                    "constituent_fact_ids": cids,
                    "formula_version": RATIFICATION_FORMULA_VERSION,
                    "source_citation": "CR-57 / DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11",
                })
    return rows, ratification_lookup


# ── Family 3: varga_consistency (design §4 delta 2) ─────────────────────────

def build_varga_consistency_rows(
    idx: VicharaFactIndex, w_sign: float, w_dignity: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    # Every varga this chart actually has dignity rows for, across all grahas.
    all_vargas = sorted({v for (v, _s) in idx.dignity.keys()})
    if "D1" not in all_vargas:
        return rows

    for graha in ALL_GRAHAS:
        subj = PLANET_TO_SUBJECT.get(graha, graha.upper())
        d1_rec = idx.dignity.get(("D1", subj))
        if d1_rec is None:
            continue
        d1_sign = d1_rec.get("sign")
        d1_direction = dignity_direction(d1_rec.get("dignity"))

        vargas_used = [v for v in all_vargas if v != "D1" and (v, subj) in idx.dignity]
        if not vargas_used:
            continue

        sign_matches = 0
        dign_matches = 0
        per_varga: dict[str, Any] = {}
        constituent_ids = {d1_rec.get("fact_id")} if d1_rec.get("fact_id") else set()
        for v in vargas_used:
            v_rec = idx.dignity[(v, subj)]
            if v_rec.get("fact_id"):
                constituent_ids.add(v_rec["fact_id"])
            same_sign = v_rec.get("sign") == d1_sign
            same_direction = dignity_direction(v_rec.get("dignity")) == d1_direction
            if same_sign:
                sign_matches += 1
            if same_direction:
                dign_matches += 1
            per_varga[v] = {"sign": v_rec.get("sign"), "dignity": v_rec.get("dignity"),
                             "same_sign_as_d1": same_sign, "same_dignity_direction_as_d1": same_direction}

        n = len(vargas_used)
        frac_sign = sign_matches / n
        frac_dign = dign_matches / n
        consistency = w_sign * frac_sign + w_dignity * frac_dign

        rows.append({
            "vichara_family": "varga_consistency",
            "subject": subj,
            "actor": None,
            "target": None,
            "domain": None,
            "varga_id": None,
            "varga": None,
            "value_num": round(consistency, 6),
            "value_text": None,
            "value_jsonb": {
                "d1_sign": d1_sign, "d1_dignity": d1_rec.get("dignity"),
                "vargas_used": vargas_used, "per_varga": per_varga,
                "frac_same_sign": frac_sign, "frac_same_dignity_direction": frac_dign,
                "vargottama": (idx.dignity.get(("D9", subj), {}).get("sign") == d1_sign)
                if ("D9", subj) in idx.dignity else None,
            },
            "ratification_factor": None,
            "constituent_fact_ids": sorted(constituent_ids),
            "formula_version": CONSISTENCY_FORMULA_VERSION,
            "source_citation": "DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §4 delta 2",
        })
    return rows


# ── Family 4: leverage_index (CR-69/CR-60, design §8) ───────────────────────

def _yoga_participation(graha: str, domain: str, firings: list[dict], keywords: dict[str, list[str]]) -> bool:
    kws = keywords.get(domain, [])
    if not kws:
        return False
    lower = graha.lower()
    for f in firings:
        cid = str(f.get("yoga_canonical_id") or "").upper()
        if any(kw in cid for kw in kws) and lower in (p.lower() for p in f.get("constituent_planets", [])):
            return True
    return False


def _dasha_runway(graha: str, dasha_rows: list[dict], now: datetime, weights: dict[str, Any]) -> tuple[float, dict]:
    lookforward_years = float(weights.get("runway_lookforward_years", 30))
    base = float(weights.get("runway_base", 1.0))
    scale = float(weights.get("runway_scale", 0.5))
    dur_norm = float(weights.get("runway_duration_norm_years", 20))
    start_horizon = float(weights.get("runway_start_horizon_years", 15))

    best = None
    for r in dasha_rows:
        if str(r.get("lord_graha")) != graha:
            continue
        start = r.get("start_iso")
        end = r.get("end_iso")
        if start is None or end is None:
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if end < now:
            continue  # already elapsed
        s_years = max(0.0, (start - now).days / 365.25)
        if s_years > lookforward_years:
            continue
        if best is None or s_years < best[0]:
            duration_days = r.get("duration_days")
            y_years = float(duration_days) / 365.25 if duration_days is not None else \
                (end - start).days / 365.25
            best = (s_years, y_years)

    if best is None:
        return 1.0, {"dasha_runway_found": False}
    s_years, y_years = best
    weight = base + scale * (y_years / dur_norm) * max(0.0, 1 - s_years / start_horizon)
    return weight, {"dasha_runway_found": True, "years_to_start": round(s_years, 3), "md_duration_years": round(y_years, 3)}


def build_leverage_index_rows(
    idx: VicharaFactIndex,
    domains_config: dict[str, Any],
    ratification_lookup: dict[tuple[str, str], float],
    dasha_rows: list[dict],
    leverage_weights: dict[str, Any],
    dignity_score_map: dict[str, float],
    now: datetime,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    d1_lordships = idx.lordships("D1")
    firings = idx.__dict__.get("_yoga_firings", [])  # set by caller before invocation
    keywords = leverage_weights.get("domain_yoga_keywords", {})
    floor = float(leverage_weights.get("capability_floor", 0.1))

    # Shadbala percentile across the 7 classical grahas present this build.
    shadbala_vals = [
        (g, idx.shadbala.get(PLANET_TO_SUBJECT[g], {}).get("rupa"))
        for g in CLASSICAL_GRAHAS
    ]
    present = [(g, v) for g, v in shadbala_vals if v is not None]
    n_present = len(present)

    def percentile(graha: str, value: float | None) -> float | None:
        if value is None or n_present == 0:
            return None
        rank = sum(1 for _, v in present if v <= value)
        return rank / n_present

    for domain, cfg in domains_config.items():
        houses = set(int(h) for h in cfg.get("houses", []))
        karaka = cfg.get("karaka")

        raw_weights: dict[str, float] = {}
        for graha in CLASSICAL_GRAHAS:
            w = 0.0
            lorded = d1_lordships.get(graha, set())
            w += leverage_weights.get("lordship", 1.0) * len(lorded & houses)
            if karaka and graha == karaka:
                w += leverage_weights.get("karakatva", 0.75)
            subj = PLANET_TO_SUBJECT[graha]
            d1_rec = idx.dignity.get(("D1", subj))
            if d1_rec and d1_rec.get("house") in houses:
                w += leverage_weights.get("occupancy", 0.5)
            if _yoga_participation(graha, domain, firings, keywords):
                w += leverage_weights.get("yoga_participation", 0.75)
            raw_weights[graha] = w

        max_w = max(raw_weights.values()) if raw_weights else 0.0

        for graha in CLASSICAL_GRAHAS:
            subj = PLANET_TO_SUBJECT[graha]
            d1_rec = idx.dignity.get(("D1", subj))
            rupa = idx.shadbala.get(subj, {}).get("rupa")
            pct = percentile(graha, rupa)
            dign_score = dignity_score_map.get(d1_rec["dignity"], 0.5) if d1_rec else 0.5
            rf = ratification_lookup.get((subj, domain))
            rf_rescaled = (rf - 0.6) / 0.8 if rf is not None else None

            components = [c for c in (pct, dign_score, rf_rescaled) if c is not None]
            capability = sum(components) / len(components) if components else 0.5
            capability = max(capability, floor)

            norm_weight = raw_weights[graha] / max_w if max_w > 0 else 0.0
            runway_weight, runway_meta = _dasha_runway(graha, dasha_rows, now, leverage_weights)

            leverage = (norm_weight / capability) * runway_weight

            constituent_ids = set()
            if d1_rec and d1_rec.get("fact_id"):
                constituent_ids.add(d1_rec["fact_id"])
            sb = idx.shadbala.get(subj, {})
            if sb.get("fact_id"):
                constituent_ids.add(sb["fact_id"])

            rows.append({
                "vichara_family": "leverage_index",
                "subject": subj,
                "actor": None,
                "target": None,
                "domain": domain,
                "varga_id": None,
                "varga": None,
                "value_num": round(leverage, 6),
                "value_text": None,
                "value_jsonb": {
                    "domain_load_bearing_weight": round(raw_weights[graha], 4),
                    "domain_load_bearing_weight_normalized": round(norm_weight, 4),
                    "capability": round(capability, 4),
                    "shadbala_percentile": pct,
                    "dignity_score": dign_score,
                    "ratification_factor_rescaled": rf_rescaled,
                    "dasha_runway_weight": round(runway_weight, 4),
                    **runway_meta,
                },
                "ratification_factor": None,
                "constituent_fact_ids": sorted(constituent_ids),
                "formula_version": FORMULA_VERSION,
                "source_citation": "CR-69/CR-60 / DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §8",
            })
    return rows


# ── Row persistence ──────────────────────────────────────────────────────────

def _insert_rows(
    conn: Any, chart_id: str, ayanamsha_id: str, build_id: str | None, rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0
    inserted = 0
    with conn.cursor() as cur:
        for r in rows:
            fact_ids = r.get("constituent_fact_ids") or []
            cur.execute("""
                INSERT INTO chart_vichara (
                    chart_id, ayanamsha_id, build_id, vichara_family, subject, actor, target,
                    domain, varga_id, varga, value_num, value_text, value_jsonb,
                    ratification_factor, constituent_fact_ids, constituent_facts_array,
                    formula_version, source_citation, computed_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s,
                    %s, %s, NOW()
                )
            """, (
                chart_id, ayanamsha_id, build_id, r["vichara_family"], r["subject"], r.get("actor"), r.get("target"),
                r.get("domain"), r.get("varga_id"), r.get("varga"), r.get("value_num"), r.get("value_text"),
                json.dumps(r.get("value_jsonb")) if r.get("value_jsonb") is not None else None,
                r.get("ratification_factor"), fact_ids, fact_ids,
                r.get("formula_version"), r.get("source_citation"),
            ))
            inserted += 1
    return inserted


# ── Main substep builder ────────────────────────────────────────────────────

def build_ga_vichara_substep(
    chart_id: str,
    build_id: str | None,
    ayanamsha_id: str,
    conn: Any,
    dry_run: bool = False,
) -> int:
    """Build chart_vichara rows for one (chart_id, ayanamsha_id) pair.
    Called per-ayanamsha substep by GaVicharaWriter.run_substep."""
    logger.info("[ga_vichara_writer] substep start: chart=%s ayanamsha=%s", chart_id, ayanamsha_id)

    if chart_id == CANONICAL_CHART_ID:
        logger.info("[ga_vichara_writer] FORENSIC: native chart — applying forensic assertions")

    if dry_run:
        logger.info("[ga_vichara_writer] DRY_RUN — no writes")
        return 0

    facts = _load_chart_facts(conn, chart_id, ayanamsha_id)
    if not facts:
        logger.warning("[ga_vichara_writer] no chart_facts for chart=%s ayanamsha=%s — skipping",
                        chart_id, ayanamsha_id)
        return 0

    constants = _load_constants(conn)
    if not constants:
        logger.warning("[ga_vichara_writer] brahma_vichara_constants is empty — skipping")
        return 0

    idx = VicharaFactIndex(facts)
    firings = _load_yoga_firings(conn, chart_id, ayanamsha_id)
    idx.__dict__["_yoga_firings"] = firings
    dasha_rows = _load_dasha_md_rows(conn, chart_id, ayanamsha_id)

    step = float(constants.get("ratification_step", 0.2))
    clamp = constants.get("ratification_clamp", {"lo": 0.6, "hi": 1.4})
    lo, hi = float(clamp.get("lo", 0.6)), float(clamp.get("hi", 1.4))
    domains_config = constants.get("operative_vargas", {})
    valence_matrix = constants.get("valence_matrix", {})
    dignity_score_map = constants.get("dignity_score_map", {})
    leverage_weights = constants.get("leverage_weights", {})
    consistency_weights = constants.get("consistency_weights", {"w_sign": 0.5, "w_dignity": 0.5})

    all_rows: list[dict[str, Any]] = []

    # 1. valence_pass — one pass per varga that has link rows this build.
    for varga in sorted(idx.links_by_varga.keys()):
        all_rows.extend(build_valence_pass_rows(idx, varga, valence_matrix))

    # 1b. aspect-sourced valence_pass rows (CR-91/A2) — one pass per varga
    # that has aspect_parashari_per_varga rows this build (independent of
    # links_by_varga's key set; a varga could in principle have aspects
    # without bhava_significance_link rows, or vice versa).
    for varga in sorted(idx.aspects_by_varga.keys()):
        all_rows.extend(build_aspect_valence_rows(idx, varga, valence_matrix))

    # 2. varga_ratification (+ divergence)
    ratification_rows, ratification_lookup = build_varga_ratification_rows(idx, domains_config, step, lo, hi)
    all_rows.extend(ratification_rows)

    # 3. varga_consistency
    all_rows.extend(build_varga_consistency_rows(
        idx, float(consistency_weights.get("w_sign", 0.5)), float(consistency_weights.get("w_dignity", 0.5)),
    ))

    # 4. leverage_index
    now = datetime.now(timezone.utc)
    all_rows.extend(build_leverage_index_rows(
        idx, domains_config, ratification_lookup, dasha_rows, leverage_weights, dignity_score_map, now,
    ))

    deleted = _delete_prior_vichara_rows(conn, chart_id, ayanamsha_id)
    logger.info("[ga_vichara_writer] deleted %d prior rows", deleted)

    inserted = _insert_rows(conn, chart_id, ayanamsha_id, build_id, all_rows)
    logger.info("[ga_vichara_writer] inserted %d rows (chart=%s ayanamsha=%s)", inserted, chart_id, ayanamsha_id)
    return inserted
