"""SR-DETECTOR-REFS (2): merged pre-build packets are named by squash commit + PR, never by a deleted branch.

Claim: each item below was built in a pre-build PR that is merged on main and whose source branch was deleted, so a
`origin/kalayantra/<id>` ref can never be fetched (`couldn't find remote ref`) and the item read as an error. Its
detector must instead name the packet's squash commit and PR (the J-3b convention), and where git can resolve the
commit its subject must end in that PR number.
"""
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
MODEL = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"

PACKET = {
    "J6M-R1": 3636, "K5-G1b-N1": 3640, "K6-N1": 3635, "K6-N2": 3635, "K6-N3": 3635, "K5G1A-R1": 3605,
    "K5G1A-R2": 3605, "J-4c-pr2907": 3596, "J-4c-pr2953": 3596, "J-4c-pr2988": 3596,
    "J-4c-pr3082": 3596, "J-4c-pr3085": 3596, "J-4c-pr3111": 3596, "J-4c-pr3187": 3604, "J-4c-pr3188": 3604,
}
# K9-23-N2 is not here: its pre-build #3606 only registered the finding, so its detector follows K9-23 itself
# (pinned in governance/__tests__/test_k9_23_n2_custody.py)
# left out of their pre-build (needs migration number): the code is only in the still-open P06 PR #3516
OPEN_P06 = ("J-4c-pr3141", "J-4c-pr3191", "J-4c-pr3193", "J-4c-a55l")


def _items():
    return {i["id"]: i for i in json.loads(MODEL.read_text(encoding="utf-8"))["items"]}


def test_merged_packet_items_name_their_squash_commit_and_pr():
    items = _items()
    for iid, pr in PACKET.items():
        det = items[iid]["detector"]
        assert det["type"] == "branch_merged" and det["packet_pr"] == pr, iid
        assert re.fullmatch(r"[0-9a-f]{40}", det["ref"]), f"{iid}: {det['ref']!r} is not a squash commit"
        probe = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%s", det["ref"]],
                               capture_output=True, text=True)
        if probe.returncode == 0:   # a shallow checkout may not hold the commit; the shape above still holds
            assert probe.stdout.strip().endswith(f"(#{pr})"), f"{iid}: {det['ref']} is not PR #{pr}'s squash commit"


def test_items_left_out_of_their_prebuild_stay_on_the_open_carrying_pr():
    items = _items()
    for iid in OPEN_P06:
        det = items[iid]["detector"]
        assert (det["type"], det["pr"], det["packet_pr"]) == ("pr_merged", 3516, 3516), iid
