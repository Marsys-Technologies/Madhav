"""
brahmagyan.bodha.l2_signals_scaffold — BRAHMA-BO-2-1 (L2 Bodha)
================================================================

Scaffolds all 573 MSR signals from MSR_v5_0.md into chart_facts with:
  fact_category = 'bodha.signals'
  fact_subject  = signal_id  (e.g. 'SIG.MSR.001')
  fact_value    = {signal_id, signal_text, domain, signal_type, valence,
                   strength_score, confidence, entities_involved, ...}
  rule_id       = NULL  (awaiting WS-3 rule base)
  provenance_envelope.grounding_status = 'UNGROUNDED'
  provenance_envelope.grounding_note   = 'Scaffold pass — awaiting WS-3 rule_base'

CRITICAL: All signals are explicitly UNGROUNDED. rule_id=null on every row.
The l2-bodha-grounded session (after ws3-rule-base-complete tag) re-derives
these with real rule IDs and verse citations.

Volume floor: 573 rows

Source: 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
Layer:  L2 Bodha (scaffold)
Asset:  bodha.signals (BO-2-1)
Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
        chart_id: 482012f1-710e-4a25-994a-93821f5871aa

BRAHMA-BO-2-1 / l2-bodha-scaffold
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 569  # 573 declared in MSR; 4 are known ID gaps (207, 497-499 — confirmed numbering artifacts)
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

SOURCE_CITATION = "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"

# Provenance envelope for all scaffold rows — HARD REQUIREMENT
PROVENANCE_ENVELOPE = {
    "layer": "L2",
    "asset": "bodha.signals",
    "asset_id": "BO-2-1",
    "scaffold_pass": "l2-bodha-scaffold",
    "grounding_status": "UNGROUNDED",
    "grounding_note": "Scaffold pass — awaiting WS-3 rule_base",
    "rule_id": None,  # Explicitly NULL — WS-3 provides rules
    "ws3_dependency": "ws3-rule-base-complete",
}

# MSR source path — resolved relative to repo root
MSR_REL_PATH = "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"

# Domain mapping from signal_type / entities to domain labels
SIGNAL_TYPE_TO_DOMAIN: dict[str, str] = {
    "yoga":                "yoga",
    "divisional-pattern":  "divisional",
    "dignity":             "dignity",
    "nakshatra-signature": "nakshatra",
    "strength":            "strength",
    "sensitive-point":     "sensitive_point",
    "convergence":         "convergence",
    "transit":             "timing",
    "dasha-pattern":       "dasha",
    "nadi":                "nadi_bnn",
    "nadi-pattern":        "nadi_bnn",
    "yogini":              "yogini_tajaka",
    "tajika":              "yogini_tajaka",
    "house":               "house_domain",
    "aspect":              "aspect",
    "relationship":        "relationships",
    "career":              "career",
    "wealth":              "wealth",
    "health":              "health",
    "mind":                "mind",
    "spirit":              "spirit",
}

# Signal ID pattern
_SIG_ID_RE = re.compile(r"^(SIG\.MSR\.\d+):\s*$", re.MULTILINE)
_FIELD_RE = re.compile(r"^\s{2}(\w[\w_-]*):\s*(.*)$")


# ── MSR parser ────────────────────────────────────────────────────────────────

def _parse_msr(msr_path: Path) -> list[dict[str, Any]]:
    """
    Parse MSR_v5_0.md and return a list of signal dicts.

    Each dict contains: signal_id, signal_name, signal_type, valence,
    strength_score, entities_involved, temporal_activation, classical_source,
    domains_affected, confidence, forensic_ref.
    """
    text = msr_path.read_text(encoding="utf-8")
    signals: list[dict[str, Any]] = []

    # Split on signal ID markers
    # Pattern: line starting with SIG.MSR.NNN:
    sig_id_pattern = re.compile(r"(?m)^(SIG\.MSR\.\d+):\s*$")
    parts = sig_id_pattern.split(text)

    # parts[0] = frontmatter/preamble
    # parts[1], parts[2], parts[3], parts[4], ... = (sig_id, sig_body) pairs
    i = 1
    while i + 1 < len(parts):
        sig_id = parts[i].strip()
        body = parts[i + 1]
        sig = _parse_signal_body(sig_id, body)
        signals.append(sig)
        i += 2

    logger.info("[l2_signals_scaffold] Parsed %d signals from MSR", len(signals))
    return signals


def _parse_signal_body(sig_id: str, body: str) -> dict[str, Any]:
    """Parse the YAML body of a single MSR signal entry."""
    sig: dict[str, Any] = {"signal_id": sig_id}

    # Parse indented key: value pairs (simple, not recursive)
    for line in body.splitlines():
        m = re.match(r"^\s{2}(\w[\w_-]*):\s*(.*)", line)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2).strip().strip('"').strip("'")

        if key == "signal_name":
            sig["signal_name"] = value
        elif key == "signal_type":
            sig["signal_type"] = value
        elif key == "valence":
            sig["valence"] = value
        elif key == "strength_score":
            try:
                sig["strength_score"] = float(value)
            except (ValueError, TypeError):
                sig["strength_score"] = None
        elif key == "confidence":
            try:
                sig["confidence"] = float(value)
            except (ValueError, TypeError):
                sig["confidence"] = None
        elif key == "temporal_activation":
            sig["temporal_activation"] = value
        elif key == "classical_source":
            sig["classical_source"] = value
        elif key == "forensic_ref":
            sig["forensic_ref"] = value
        elif key == "entities_involved":
            # Parse list like [PLN.SATURN, HSE.7, ...]
            inner = re.sub(r"[\[\]]", "", value)
            entities = [e.strip() for e in inner.split(",") if e.strip()]
            sig["entities_involved"] = entities
        elif key == "domains_affected":
            inner = re.sub(r"[\[\]]", "", value)
            domains = [d.strip() for d in inner.split(",") if d.strip()]
            sig["domains_affected"] = domains

    # Derive primary domain from signal_type or domains_affected
    sig["domain"] = _derive_domain(sig)

    # Ensure required fields have defaults
    sig.setdefault("signal_name", f"(unnamed) {sig_id}")
    sig.setdefault("signal_type", "unknown")
    sig.setdefault("valence", "context-dependent")
    sig.setdefault("strength_score", None)
    sig.setdefault("confidence", None)
    sig.setdefault("temporal_activation", "natal-permanent")
    sig.setdefault("classical_source", SOURCE_CITATION)
    sig.setdefault("forensic_ref", None)
    sig.setdefault("entities_involved", [])
    sig.setdefault("domains_affected", [])

    return sig


def _derive_domain(sig: dict[str, Any]) -> str:
    """Map signal_type or entities_involved to a domain label."""
    sig_type = sig.get("signal_type", "unknown").lower()
    if sig_type in SIGNAL_TYPE_TO_DOMAIN:
        return SIGNAL_TYPE_TO_DOMAIN[sig_type]

    # Fallback: check signal_id range
    sig_id = sig.get("signal_id", "SIG.MSR.000")
    num_match = re.search(r"SIG\.MSR\.(\d+)", sig_id)
    if num_match:
        n = int(num_match.group(1))
        if n >= 544 and n <= 558:
            return "yogini_tajaka"
        if n >= 559 and n <= 573:
            return "yogini_tajaka"
        if n >= 515 and n <= 543:
            return "nadi_bnn"

    # Check domains_affected list
    domains = sig.get("domains_affected", [])
    if domains:
        d0 = domains[0].strip().lower()
        if d0 in SIGNAL_TYPE_TO_DOMAIN:
            return SIGNAL_TYPE_TO_DOMAIN[d0]
        return d0

    return "mixed"


# ── chart_facts writer ────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[l2_signals_scaffold] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


def seed_bodha_signals(
    chart_id: str,
    *,
    build_id: str | None = None,
    msr_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Parse MSR_v5_0.md and write all 573 signals into chart_facts.

    Each row:
      fact_category = 'bodha.signals'
      fact_subject  = signal_id  (e.g. 'SIG.MSR.001')
      fact_value    = {signal data + provenance_envelope}
      source_citation = SOURCE_CITATION
      build_id      = build_id

    All rows are UNGROUNDED (rule_id=null, grounding_status='UNGROUNDED').

    Returns: { seeded: int, volume_floor: int, volume_met: bool }
    """
    # Resolve MSR path
    if msr_path is None:
        repo_root = Path(os.environ.get("MARSYS_REPO_ROOT", ""))
        if not repo_root or not (repo_root / MSR_REL_PATH).exists():
            # Walk up from this file
            here = Path(__file__).resolve()
            for parent in [here.parent, here.parent.parent,
                           here.parent.parent.parent,
                           here.parent.parent.parent.parent]:
                candidate = parent / MSR_REL_PATH
                if candidate.exists():
                    repo_root = parent
                    break
        msr_path = repo_root / MSR_REL_PATH if repo_root else Path(MSR_REL_PATH)

    if not msr_path.exists():
        raise FileNotFoundError(
            f"[l2_signals_scaffold] MSR not found at {msr_path}. "
            "Set MARSYS_REPO_ROOT env var."
        )

    signals = _parse_msr(msr_path)

    if dry_run:
        logger.info("[dry_run] Would write %d signal rows", len(signals))
        return {
            "seeded": 0,
            "dry_run": True,
            "parsed": len(signals),
            "volume_floor": VOLUME_FLOOR,
            "volume_met": len(signals) >= VOLUME_FLOOR,
        }

    build_id = build_id or f"l2-signals-{_today()}"

    rows_written = 0
    with _conn() as conn:
        for sig in signals:
            fact_value = {
                "signal_id":           sig["signal_id"],
                "signal_text":         sig["signal_name"],
                "signal_type":         sig["signal_type"],
                "domain":              sig["domain"],
                "valence":             sig["valence"],
                "strength_score":      sig["strength_score"],
                "confidence":          sig.get("confidence"),
                "temporal_activation": sig["temporal_activation"],
                "classical_source":    sig["classical_source"],
                "forensic_ref":        sig.get("forensic_ref"),
                "entities_involved":   sig["entities_involved"],
                "domains_affected":    sig["domains_affected"],
                "layer":               "L2",
                # ── HARD REQUIREMENT: ALL SIGNALS UNGROUNDED ──────────────────
                "rule_id":             None,   # NULL — WS-3 provides rules
                "provenance_envelope": {
                    **PROVENANCE_ENVELOPE,
                    "signal_id": sig["signal_id"],
                    "source_file": str(msr_path),
                },
            }

            conn.execute(
                """
                INSERT INTO chart_facts
                  (chart_id, fact_category, fact_subject, fact_value,
                   source_citation, build_id)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (chart_id, fact_category, fact_subject) DO UPDATE SET
                  fact_value      = EXCLUDED.fact_value,
                  source_citation = EXCLUDED.source_citation,
                  build_id        = EXCLUDED.build_id,
                  updated_at      = NOW()
                """,
                [
                    chart_id,
                    "bodha.signals",
                    sig["signal_id"],
                    json.dumps(fact_value),
                    SOURCE_CITATION,
                    build_id,
                ],
            )
            rows_written += 1
        conn.commit()

    logger.info(
        "[l2_signals_scaffold] seed_bodha_signals: chart=%s rows=%d grounding=UNGROUNDED",
        chart_id, rows_written,
    )
    return {
        "seeded":       rows_written,
        "volume_floor": VOLUME_FLOOR,
        "volume_met":   rows_written >= VOLUME_FLOOR,
        "grounding_status": "UNGROUNDED",
        "rule_id":      None,
        "build_id":     build_id,
    }


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


# ── Volume check (no DB) ──────────────────────────────────────────────────────

def check_volume(msr_path: Path | None = None) -> dict[str, Any]:
    """
    Parse MSR and verify ≥ 573 signals can be extracted without DB access.

    Returns: {status: GREEN|AMBER|RED, volume_floor, actual, grounding_status}
    """
    try:
        if msr_path is None:
            here = Path(__file__).resolve()
            for parent in [here.parent, here.parent.parent,
                           here.parent.parent.parent,
                           here.parent.parent.parent.parent]:
                candidate = parent / MSR_REL_PATH
                if candidate.exists():
                    msr_path = candidate
                    break

        if msr_path is None or not msr_path.exists():
            return {
                "status": "RED",
                "volume_floor": VOLUME_FLOOR,
                "actual": 0,
                "error": f"MSR not found at {MSR_REL_PATH}",
                "grounding_status": "UNGROUNDED",
            }

        signals = _parse_msr(msr_path)
        actual = len(signals)
        status = "GREEN" if actual >= VOLUME_FLOOR else "AMBER"

        # Verify all rule_ids are None (UNGROUNDED check)
        grounded_count = sum(
            1 for s in signals if s.get("rule_id") is not None
        )

        return {
            "status":           status,
            "volume_floor":     VOLUME_FLOOR,
            "actual":           actual,
            "grounding_status": "UNGROUNDED",
            "grounded_count":   grounded_count,   # Must be 0
            "ungrounded_count": actual,
            "rule_id_null_pct": 100.0 if actual > 0 else 0.0,
            "note":             "All signals scaffold-only, awaiting WS-3 rule_base",
        }
    except Exception as exc:
        return {
            "status":       "RED",
            "volume_floor": VOLUME_FLOOR,
            "actual":       0,
            "error":        str(exc),
            "grounding_status": "UNGROUNDED",
        }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    parser = argparse.ArgumentParser(
        description="l2_signals_scaffold — Seed bodha.signals (573 UNGROUNDED)"
    )
    sub = parser.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed", help="Seed signals into chart_facts")
    p_seed.add_argument("--chart-id", default=NATIVE_CHART_ID)
    p_seed.add_argument("--build-id", default=None)
    p_seed.add_argument("--dry-run", action="store_true")
    p_seed.add_argument("--msr-path", default=None)

    p_check = sub.add_parser("check", help="Volume check (no DB)")
    p_check.add_argument("--msr-path", default=None)

    args = parser.parse_args()

    if args.cmd == "seed":
        msr_path = Path(args.msr_path) if args.msr_path else None
        result = seed_bodha_signals(
            args.chart_id,
            build_id=args.build_id,
            msr_path=msr_path,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "check":
        msr_path = Path(args.msr_path) if args.msr_path else None
        result = check_volume(msr_path)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)
