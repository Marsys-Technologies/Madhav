"""Chart timelines for the scorer, from the engine driver run on birth data only.

For one birth: the 0-minute build is scanned over the transit horizon (which contains the daśā horizon);
the -5 and +5 minute builds are scanned over the daśā horizon, daśā units only. A daśā member's day is
NOT_ASSESSED wherever the three builds differ (v1.1 C2). A chart whose lagna sign or Moon nakshatra moves
with the +-5 minutes is excluded (v1.0 7.4 item 4). Horizons follow v1.1 A4: start = later of birth + 12 years
and the family's data start; end = earliest of the recording end proxy and 2036-10-09.

The recording end is a PROXY here (the article retrieval date and the death date are occurrence-side facts the
calibration does not read): ``min(2026-10-29, birth + 95 years, 2036-10-09)``.
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..engine import constants as K
from ..engine.driver import scan
from ..engine.units import sha256_file
from ..scorer import config as C
from ..scorer.model import ChartTimeline, mask_unstable
from .births import BirthRow
from .natal import build_natal

DASHA_DATA_START = date(1950, 1, 1)
TRANSIT_DATA_START = date(1902, 2, 12)
CAP_END = date(2036, 10, 9)
RECORDING_END_PROXY = date(2026, 10, 29)


class InputsBundle:
    """The engine inputs shared by every build (manifest, bundle, sky), loaded once."""

    def __init__(self, manifest_path: str, bundle_path: str, sky_path: str):
        from ..engine.sky import sky_from_fixture

        self.manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        self.bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        self.manifest_sha = sha256_file(Path(manifest_path))
        self.bundle_sha = sha256_file(Path(bundle_path))
        self.sky = sky_from_fixture(json.loads(Path(sky_path).read_text(encoding="utf-8")))
        self.by_plane = {
            pl: {**self.manifest, "units": [u for u in self.manifest["units"] if u["plane"] == pl]} for pl in (C.FAMILY_DASHA, C.FAMILY_TRANSIT)
        }


def _twelfth(d: date) -> date:
    try:
        return d.replace(year=d.year + 12)
    except ValueError:
        return d.replace(year=d.year + 12, day=28)


def _plus_years(d: date, n: int) -> date:
    try:
        return d.replace(year=d.year + n)
    except ValueError:
        return d.replace(year=d.year + n, day=28)


def runs_to_array(runs: Sequence[Sequence[Any]], n: int) -> np.ndarray:
    out = np.zeros(n, dtype=np.int8)
    code = {"T": 1, "F": 0, "N": -1}
    for k, (s, v) in enumerate(runs):
        e = runs[k + 1][0] if k + 1 < len(runs) else n
        out[s:e] = code[v]
    return out


def _scan(inp: InputsBundle, chart, prov, plane: Optional[str], first: date, last: date) -> Mapping[str, Any]:
    man = inp.by_plane[plane] if plane else inp.manifest
    return scan(chart, inp.sky, prov, first, last, inp.bundle, man, manifest_sha256=inp.manifest_sha, bundle_sha256=inp.bundle_sha)


def build_one(b: BirthRow, inp: InputsBundle) -> Dict[str, Any]:
    """Timelines of one birth; ``{"excluded": reason}`` when the chart is out (exclusion 4 or an engine refusal)."""
    from ..engine.dayatom import SolarSunrise
    from ..engine.birthrecord import BirthRecordError

    try:
        charts = {s: build_natal(b, s) for s in (-5, 0, 5)}
        moon_nak = {s: int(c.grahas["chandra"].longitude // (360.0 / 27.0)) for s, c in charts.items()}
        if len({c.lagna_sign for c in charts.values()}) > 1 or len(set(moon_nak.values())) > 1:
            return {"excluded": "EXCL4_LAGNA_OR_NAKSHATRA_MOVES_WITH_5_MINUTES"}
        c0 = charts[0]
        birth_d = c0.birth.birth_date
        h12 = _twelfth(birth_d)
        end = min(RECORDING_END_PROXY, _plus_years(birth_d, 95), CAP_END)
        t_first = max(h12, TRANSIT_DATA_START)
        if end <= t_first:
            return {"excluded": "HORIZON_EMPTY"}
        prov = SolarSunrise(b.lat, b.lon)
        doc0 = _scan(inp, c0, prov, None, t_first, end)
        hi = doc0["horizon_inputs"]
        t_start = max(t_first, date.fromisoformat(hi["transit_first_day"])) if hi["transit_first_day"] else t_first
        d_first_eng = date.fromisoformat(hi["dasha_first_day"]) if hi["dasha_first_day"] else None
        if d_first_eng is None:
            return {"excluded": "NO_DASHA_ROWS"}
        d_start = max(h12, DASHA_DATA_START, d_first_eng)
        if end <= d_start:
            return {"excluded": "DASHA_HORIZON_EMPTY"}
        docs_d = {0: doc0}
        for s in (-5, 5):
            docs_d[s] = _scan(inp, charts[s], prov, C.FAMILY_DASHA, d_start, end)
        out: Dict[str, Any] = {"code": b.code, "birth_ord": birth_d.toordinal(), "surrogate": b.surrogate}
        # transit family
        n_t = (end - t_start).days + 1
        off_t = (t_start - t_first).days
        tstates = {}
        for rid, m in doc0["members"].items():
            if m["plane"] == C.FAMILY_TRANSIT:
                tstates[rid] = runs_to_array(m["runs"], doc0["range"]["days"])[off_t : off_t + n_t].copy()
        out[C.FAMILY_TRANSIT] = {"h_start": t_start.toordinal(), "h_end": end.toordinal(), "states": tstates}
        # dasha family: three builds, unstable days not assessed
        n_d = (end - d_start).days + 1
        off_d = (d_start - t_first).days
        dstates = {}
        unstable = 0
        total = 0
        for rid, m in doc0["members"].items():
            if m["plane"] != C.FAMILY_DASHA:
                continue
            a0 = runs_to_array(m["runs"], doc0["range"]["days"])[off_d : off_d + n_d]
            builds = [a0]
            for s in (-5, 5):
                mm = docs_d[s]["members"].get(rid)
                builds.append(runs_to_array(mm["runs"], docs_d[s]["range"]["days"]) if mm else np.full(n_d, -1, dtype=np.int8))
            masked = mask_unstable(builds)
            unstable += int(((masked == -1) & (a0 != -1)).sum())
            total += n_d
            dstates[rid] = masked
        out[C.FAMILY_DASHA] = {"h_start": d_start.toordinal(), "h_end": end.toordinal(), "states": dstates, "unstable_share": (unstable / total) if total else 0.0}
        out["meta"] = {"readiness": len(doc0["readiness_problems"]), "birth_problems": len(doc0["birth_consistency_problems"])}
        return out
    except BirthRecordError as exc:
        return {"excluded": "ENGINE_" + exc.code}


def save_chart(res: Mapping[str, Any], directory: str) -> None:
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    code = res["code"]
    meta = {"code": code, "birth_ord": res["birth_ord"], "surrogate": res["surrogate"], "meta": res["meta"]}
    for fam in (C.FAMILY_DASHA, C.FAMILY_TRANSIT):
        f = res[fam]
        meta[fam] = {"h_start": f["h_start"], "h_end": f["h_end"], "unstable_share": f.get("unstable_share")}
        np.savez_compressed(d / f"{code}.{fam}.npz", **f["states"])
    p = d / f"{code}.json"
    p.write_text(json.dumps(meta, sort_keys=True))
    os.chmod(p, 0o600)
    for fam in (C.FAMILY_DASHA, C.FAMILY_TRANSIT):
        os.chmod(d / f"{code}.{fam}.npz", 0o600)


def load_timelines(directory: str, codes: Optional[Sequence[str]] = None) -> Dict[str, List[ChartTimeline]]:
    d = Path(directory)
    metas = sorted(d.glob("*.json"))
    out: Dict[str, List[ChartTimeline]] = {C.FAMILY_DASHA: [], C.FAMILY_TRANSIT: []}
    for p in metas:
        meta = json.loads(p.read_text())
        if codes is not None and meta["code"] not in codes:
            continue
        for fam in (C.FAMILY_DASHA, C.FAMILY_TRANSIT):
            z = np.load(d / f"{meta['code']}.{fam}.npz")
            st = {k: z[k] for k in z.files}
            out[fam].append(ChartTimeline(meta["code"], meta["birth_ord"], meta[fam]["h_start"], meta[fam]["h_end"], st))
    return out
