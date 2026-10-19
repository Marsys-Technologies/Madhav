"""Generate FB35_TABLE_v1_2.json from the FB-35 table text of FINAL_BUILD_SCOPE_v1_0.md (version 1.2).

Imports NOTHING from the builder or the verifier: the fixture is the specification-side third term of the FB-38 equality test
(builder == fixture == verifier). Run from this directory:  python3 fixtures/make_fb35_fixture.py
"""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE.parent / "FINAL_BUILD_SCOPE_v1_0.md"
OUT = HERE / "FB35_TABLE_v1_2.json"
NAMES = {"Sun": "sun", "Moon": "moon", "Mars": "mars", "Mercury": "mercury", "Jupiter": "jupiter", "Ketu": "ketu", "Rāhu": "rahu"}


def frame_house(anchor, offset):
    return (anchor + offset - 2) % 12 + 1


def ints(cell):
    return sorted(int(x) for x in re.findall(r"\d+", re.sub(r"\([^)]*\)", "", cell)))


def main():
    text = SPEC.read_text()
    start = text.index("**FB-35 (the table).**")
    rows = [ln for ln in text[start:].splitlines()[1:40] if ln.startswith("| ") and not ln.startswith("| class") and not ln.startswith("|---")]
    table = {}
    for ln in rows:
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        cls = c[0].split(" ")[0]
        core_cell, dvi_cell, sup_cell, kar_cell = c[1:5]
        if cls == "parental_event":
            a, b = (int(x) for x in re.search(r"offsets (\d+), (\d+)", core_cell).groups())
            core = sorted({frame_house(9, a), frame_house(9, b)})
            sup = sorted(int(x) for x in re.search(r"lagna (\d+), (\d+)", sup_cell).groups())
            frame = "bhavat_bhavam:9"
        else:
            core, sup, frame = ints(core_cell), ints(sup_cell), "lagna"
        table[cls] = {
            "core": core, "dvi": [] if dvi_cell == "—" else ints(dvi_cell), "support": sup,
            "noted": sorted(int(x) for x in re.findall(r"\((\d+) noted\)", sup_cell)), "frame": frame,
            "karaka_a": sorted(NAMES[n] for n in re.findall(r"(Sun|Moon|Mars|Mercury|Jupiter|Ketu|Rāhu) K-A", kar_cell)),
            "karaka_b": sorted(NAMES[n] for n in re.findall(r"(Sun|Moon) (?:K-A \+ )?K-B", kar_cell)),
        }
    assert len(table) == 8, sorted(table)
    body = json.dumps({"source": "FINAL_BUILD_SCOPE v1.2 FB-35", "rule_version": "1.2.0", "classes": table}, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    OUT.write_text(body)
    print(hashlib.sha256(body.encode()).hexdigest())


if __name__ == "__main__":
    main()
