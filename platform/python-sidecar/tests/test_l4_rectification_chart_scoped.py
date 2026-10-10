"""
test_l4_rectification_chart_scoped.py -- SS N-384 (PR-S6), item 1.

POST /phala/rectification_framework used to return one person's birth details and a hard-coded
life-event list for EVERY chart_id. It now reads the REQUESTED chart's own data (birth details
from its charts row, events from its own life-event log) through an injected source, and says
not_available when the chart has no events of its own.

No database and no psycopg are needed: the data source is a dependency, replaced by a fake.

The static test at the bottom bans the removed native data WITHOUT re-embedding it: it stores
only sha256 hashes of the banned phrases (token windows of the old module's birth details,
life-event identifiers/descriptions and analysis prose) and slides a window of each phrase
length over every string constant of the module.
"""
from __future__ import annotations

import ast
import hashlib
import re
import sys
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_SIDECAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.phala import l4_rectification as mod  # noqa: E402

MODULE_PATH = _SIDECAR / "brahmagyan" / "phala" / "l4_rectification.py"

CHART_A = "aaaaaaaa-0000-4000-8000-00000000000a"
CHART_B = "bbbbbbbb-0000-4000-8000-00000000000b"
CHART_EMPTY = "cccccccc-0000-4000-8000-00000000000c"
CHART_UNDATED = "dddddddd-0000-4000-8000-00000000000d"
CHART_NOTIME = "eeeeeeee-0000-4000-8000-00000000000e"
CHART_MISSING = "99999999-0000-4000-8000-000000000099"


class FakeSource:
    """Two synthetic charts with different data; nothing here is a real person."""

    def __init__(self) -> None:
        self.birth_calls: list[str] = []
        self.event_calls: list[str] = []
        self._birth = {
            CHART_A: {"birth_date": "2001-03-04", "birth_time": "06:30:00", "birth_lat": 10.0,
                      "birth_lng": 20.0, "birth_place": "Synthetic Alpha", "timezone_id": "UTC"},
            CHART_B: {"birth_date": "1999-09-09", "birth_time": "18:05:00", "birth_lat": -30.0,
                      "birth_lng": 40.0, "birth_place": "Synthetic Beta", "timezone_id": "UTC"},
            CHART_EMPTY: {"birth_date": "1980-01-01", "birth_time": "12:00:00", "birth_lat": 0.0,
                          "birth_lng": 0.0, "birth_place": "Synthetic Gamma", "timezone_id": "UTC"},
            CHART_UNDATED: {"birth_date": "1980-01-02", "birth_time": "12:00:00", "birth_lat": 1.0,
                            "birth_lng": 1.0, "birth_place": "Synthetic Delta", "timezone_id": "UTC"},
            CHART_NOTIME: {"birth_date": "1980-01-03", "birth_time": None, "birth_lat": 2.0,
                           "birth_lng": 2.0, "birth_place": "Synthetic Eps", "timezone_id": "UTC"},
        }
        self._events = {
            CHART_A: [
                {"event_id": "A-2005", "event_date": "2005-05-05", "category": "career", "domain": "d1"},
                {"event_id": "A-2019", "event_date": "2019-12-31", "category": "family", "domain": "d2"},
                {"event_id": "A-2020", "event_date": "2020-01-01", "category": "travel", "domain": "d3"},
                {"event_id": "A-2024", "event_date": "2024-04-04", "category": "career", "domain": "d1"},
                {"event_id": "A-nodate", "event_date": None, "category": "other", "domain": "d9"},
            ],
            CHART_B: [
                {"event_id": "B-2010", "event_date": "2010-10-10", "category": "health", "domain": "d4"},
            ],
            CHART_EMPTY: [],
            CHART_UNDATED: [{"event_id": "U-1", "event_date": None, "category": "x", "domain": "y"}],
            CHART_NOTIME: [
                {"event_id": "N-1", "event_date": "2001-01-01", "category": "x", "domain": "y"},
            ],
        }

    def birth(self, chart_id):
        self.birth_calls.append(chart_id)
        return self._birth.get(chart_id)

    def life_events(self, chart_id):
        self.event_calls.append(chart_id)
        # The real source returns only LIFE_EVENT_COLUMNS; a leaked description would be a bug in it.
        return list(self._events.get(chart_id, []))


@pytest.fixture()
def source() -> FakeSource:
    return FakeSource()


@pytest.fixture()
def client(source: FakeSource) -> TestClient:
    app = FastAPI()
    app.include_router(mod.router)
    app.dependency_overrides[mod.get_rectification_source] = lambda: source
    return TestClient(app)


# ---------------------------------------------------------------- behaviour on the requested chart

def test_two_charts_get_their_own_different_data(client: TestClient) -> None:
    a = client.post("/phala/rectification_framework", json={"chart_id": CHART_A}).json()
    b = client.post("/phala/rectification_framework", json={"chart_id": CHART_B}).json()
    assert a["ok"] is True and b["ok"] is True
    assert a["chart_id"] == CHART_A and b["chart_id"] == CHART_B
    assert a["birth"]["birth_date"] == "2001-03-04" and b["birth"]["birth_date"] == "1999-09-09"
    assert a["birth"]["birth_time"] == "06:30:00" and b["birth"]["birth_time"] == "18:05:00"
    a_ids = {e["event_id"] for e in a["training_events"] + a["holdout_events"]}
    b_ids = {e["event_id"] for e in b["training_events"] + b["holdout_events"]}
    assert a_ids == {"A-2005", "A-2019", "A-2020", "A-2024"}
    assert b_ids == {"B-2010"}
    assert a_ids.isdisjoint(b_ids)
    # candidate window comes from each chart's OWN birth time
    assert a["candidate_window"]["candidate_times"][0] == "06:00"
    assert a["candidate_window"]["candidate_times"][-1] == "07:00"
    assert b["candidate_window"]["candidate_times"][0] == "17:35"
    assert "1999-09-09" in b["candidate_window"]["external_computation_spec"]
    assert "2001-03-04" not in b["candidate_window"]["external_computation_spec"]


def test_only_the_requested_chart_is_read(client: TestClient, source: FakeSource) -> None:
    client.post("/phala/rectification_framework", json={"chart_id": CHART_B})
    assert set(source.birth_calls) == {CHART_B}
    assert set(source.event_calls) == {CHART_B}


def test_train_holdout_split_at_cutoff_and_undated_counted(client: TestClient) -> None:
    a = client.post("/phala/rectification_framework", json={"chart_id": CHART_A}).json()
    assert [e["event_id"] for e in a["training_events"]] == ["A-2005", "A-2019"]
    assert [e["event_id"] for e in a["holdout_events"]] == ["A-2020", "A-2024"]
    assert a["training_event_count"] == 2 and a["holdout_event_count"] == 2
    assert a["events_without_date"] == 1
    assert a["train_test_cutoff"] == "2020-01-01"


def test_no_lagna_verdict_is_invented(client: TestClient) -> None:
    a = client.post("/phala/rectification_framework", json={"chart_id": CHART_A}).json()
    assert a["lagna_verdict"] is None
    assert a["lagna_verdict_status"] == "EXTERNAL_COMPUTATION_REQUIRED"
    assert "[EXTERNAL_COMPUTATION_REQUIRED]" in a["candidate_window"]["external_computation_spec"]


def test_event_text_is_never_returned(client: TestClient, source: FakeSource) -> None:
    assert "description" not in mod.LIFE_EVENT_COLUMNS
    source._events[CHART_B][0]["description"] = "PRIVATE-TEXT-SENTINEL"
    b = client.post("/phala/rectification_framework", json={"chart_id": CHART_B}).json()
    assert "PRIVATE-TEXT-SENTINEL" not in repr(b)


def test_chart_without_events_is_not_available(client: TestClient) -> None:
    r = client.post("/phala/rectification_framework", json={"chart_id": CHART_EMPTY})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False and body["not_available"] is True
    assert body["reason"] == "no_life_events_for_chart"
    assert body["chart_id"] == CHART_EMPTY
    assert "training_events" not in body and "birth" not in body


def test_chart_with_only_undated_events_is_not_available(client: TestClient) -> None:
    body = client.post("/phala/rectification_framework", json={"chart_id": CHART_UNDATED}).json()
    assert body["not_available"] is True and body["reason"] == "no_dated_life_events_for_chart"


def test_chart_without_birth_time_gets_no_candidate_window(client: TestClient) -> None:
    body = client.post("/phala/rectification_framework", json={"chart_id": CHART_NOTIME}).json()
    assert body["ok"] is True
    assert body["candidate_window"]["candidate_times"] == []
    assert "no usable birth time" in body["candidate_window"]["external_computation_spec"]


def test_unknown_chart_is_404_not_another_charts_data(client: TestClient) -> None:
    r = client.post("/phala/rectification_framework", json={"chart_id": CHART_MISSING})
    assert r.status_code == 404
    assert "birth" not in r.json()


# ---------------------------------------------------------------- chart_id is required

@pytest.mark.parametrize("payload", [{}, {"chart_id": None}, {"chart_id": ""}, {"chart_id": "not-a-uuid"}])
def test_post_requires_a_valid_chart_id(client: TestClient, payload) -> None:
    assert client.post("/phala/rectification_framework", json=payload).status_code == 422


def test_gate_requires_chart_id(client: TestClient) -> None:
    assert client.get("/phala/rectification_framework/gate").status_code == 422
    assert client.get("/phala/rectification_framework/gate", params={"chart_id": "x"}).status_code == 422


def test_gate_is_computed_on_the_charts_returned_split(client: TestClient) -> None:
    ok = client.get("/phala/rectification_framework/gate", params={"chart_id": CHART_A}).json()
    assert ok["gate_passed"] is True and ok["leakage_violations"] == []
    assert ok["training_event_count"] == 2 and ok["holdout_event_count"] == 2
    empty = client.get("/phala/rectification_framework/gate", params={"chart_id": CHART_EMPTY}).json()
    assert empty["gate_passed"] is None and empty["not_available"] is True
    assert client.get("/phala/rectification_framework/gate", params={"chart_id": CHART_MISSING}).status_code == 404


def test_gate_reads_false_when_the_split_leaks(client: TestClient, monkeypatch) -> None:
    """Earned-signal check: break the split and the gate must say so."""
    def leaky(events, cutoff=mod.TRAIN_TEST_CUTOFF):
        items = [{"event_id": e["event_id"], "event_date": e["event_date"], "category": None, "domain": None}
                 for e in events if e["event_date"]]
        return items, items, 0                                  # everything on both sides
    monkeypatch.setattr(mod, "split_events", leaky)
    g = client.get("/phala/rectification_framework/gate", params={"chart_id": CHART_A}).json()
    assert g["gate_passed"] is False and g["leakage_violations"] and g["train_holdout_event_id_overlap"]


# ---------------------------------------------------------------- the old defect, name-independent

def test_without_a_data_source_no_chart_gets_anyones_data(monkeypatch) -> None:
    """The OLD route answered 200 with embedded birth data for any chart_id and no database.
    Now, with no database configured, the route must not answer 200 at all."""
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        monkeypatch.delenv(key, raising=False)
    app = FastAPI()
    app.include_router(mod.router)
    r = TestClient(app).post("/phala/rectification_framework", json={"chart_id": str(uuid.uuid4())})
    assert r.status_code != 200
    assert r.status_code == 503


# ---------------------------------------------------------------- static ban (hashed)

_TOKEN = re.compile(r"[a-z0-9:.\-+/_]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _digest(tokens: list[str]) -> str:
    return hashlib.sha256(" ".join(tokens).encode()).hexdigest()


# (token_count, sha256 of the space-joined lowercase tokens). Each entry is a phrase removed
# from the module: the old birth date / time / place / coordinates, the old life-event ids and
# descriptions, and the old per-event signal and analysis prose. Hashes only.
BANNED_PHRASES: tuple[tuple[int, str], ...] = (
    (1, "065f8984149bbf31140d7229a8087a6646a6ccd0e9c3431151d59155ca46ee4a"),
    (1, "0c0cc602699c5d4056d7e1b54018f3d2c6060005239c7da3af5d94b2333ab2ec"),
    (1, "0c3ab06c988e9192a49a74c28393fa9038670728397e16f3b8438d455454a6ce"),
    (1, "1620943a500eb1e833f6536ae79d3c19f9bf1d71e41a0417ac94d12ef35dbca9"),
    (1, "1a4796ec8ed584c7889350c5cc71ef1073ade45daf111d6d7970d192a5987c24"),
    (1, "23f0e8955cf90aaf226f5d86e61008636b1c1d418b02b468fe48c80da8b6111f"),
    (1, "2ae5032713f42e95a79009e29692d81b0f3a83909a6ddfabc815658454fdb52e"),
    (1, "2f3f572388ef33638d8e2ef9e62507d6300a1c9bbaa18fadec2964ae2e196e1a"),
    (1, "2f617913c0b4b45465dccd25fcc8618693590a4d557dab5049f7836eb0d1a96b"),
    (1, "30757d3fc1d703549d8a0e7ae9dbccb5f550a2bd70a268f0528e44052d942595"),
    (1, "32bb19e16e5a2943967c00d40e9f4e8d366ff6a77e421112d6280a50a6735fec"),
    (1, "44727aeb0c07b963c7337a939629d612209faac4069a9ce20ed7a1f21b3b4fb9"),
    (1, "47b1ad52b73365a36253491a40243e73db573fac7df97b62692bb05d412d17fc"),
    (1, "4ac58704a6c64b000ede6fe5ba267a7c4335a654cd24956712a1a8f954d31f9e"),
    (1, "58b8dc0bc077628741cb469381a78c0fe779d536405b38e2fa4831e96dadb8db"),
    (1, "5acd7c28c324c6319820f17dc097496040505236c8c3e3ae17f2029077d64a43"),
    (1, "5db0ceff2d331fe78257e78adad7e389ce92b228389f8a69756f814b229f9e55"),
    (1, "5f2c1b320524139d92130562d50eabbf4fde0fc6bb1ba2745aa4cbe93d7446f9"),
    (1, "612764a80564c1ee040e5b05364938becefab4332438e22722d0ad0d7c9dec5a"),
    (1, "6394142a26cfc17c5b5353dcc8366e88ce96926be64d311254e14022a90c6f56"),
    (1, "63e105d870fce2f99872f7d4a8f8b9255159866493dbe0c1a8f436353fbc33d8"),
    (1, "69167baec1b9fd0c3c82d24989cf1a9c9ca9d5193230ca3d233dc81c67f726bf"),
    (1, "6f1c96fe3e491603e8d67934fa2d38bc11840023e3f660771bcd9e64714cda3c"),
    (1, "752073b6714ce8b4728c16532997248c913a3f246f6a3f1891b0c30b15da7488"),
    (1, "75c9e2017c2afd41500ef15aea2fea67b9826c0b91abe2f9454cee92cc583d23"),
    (1, "7d0c9364398f9178ff1d9d6370e75ab57c2acb897912ad6e0fe79218031e9529"),
    (1, "7e95507ec4d67336dc5cdaea65b71dad229efa712d11dace69df7c0c890b6624"),
    (1, "9ac5552d355b9a56b9e815f2a3092c4638d960d0d42d8b1d2447aa9a11851a1e"),
    (1, "a5aab18328a69a790ebc3dcd54edb88aae6ce1715b13cdc2b36cde337c0e4b40"),
    (1, "a984aaf419da112f876e2875a99af6175cc6a147c69de0ccd7c06ec23d295774"),
    (1, "aecb12c0863e8b86391481bc9714fd47c827b0fd83cd54c999248a81c6b85125"),
    (1, "b18e701e2f2ceebb25f714af2942fc885f7dea1981aae471f1fc0b3f25c7e162"),
    (1, "b7064fa7f52a7585301d004e8138deb7f43f8021d93335a232747e49f47b4011"),
    (1, "bf63cba25676fcc7984714d18d29bc0babd95daeff6db862a0b06ecdcd455619"),
    (1, "c19fce37e1e619196503317ccddc7455814ce522ffe487e29714d9fdba9074a8"),
    (1, "c428917cdcb9209fb11706a8650d95c17e668d4e60e4d32d8e93ccb4059c7b5d"),
    (1, "ce364003f7b42f9d04b385518af8903b4fa4ad183d2606131e250fb33ff6562a"),
    (1, "d40136af57272949ad710491503c647e89a4a165a458227edd508aa058dc0b36"),
    (1, "d850e1d259fd4bac5465db78d4f15d805a02de2bac233a2a19d15217eaeb614e"),
    (1, "d92c4ccbfee4c7d7541899f5620b0136edbaed362d2d4a1668aff49af1ede178"),
    (1, "ddc68e93e6b1d4bdfd6458dc4184f4817429fbc08c62f9676954fff1dd483b78"),
    (1, "dff675a5cb032308e4f07ab766acffd3b6e3bf81e6770ac916e111a3961114c8"),
    (1, "e174f107de941f8a347b0fdf0b355d6c2463dfa784ac4de05e65a9e0ddbc1d08"),
    (1, "e7ba672c7c51c0ee3e47057cb0a101669a4ca3e1233ef3128e01623db92de293"),
    (1, "e84c6e8c162b37373d9066cb9c9108d61e1b242d4ab4f75d17269043bc662c75"),
    (1, "eff9f60c76768004c4b0d9ccc8d6de9b5c400562d6deb681f2ad25ee347ac2f3"),
    (1, "fc005964d215553cf287927eac8c3a644c5535fa53006d2ffd140cc5040ce00c"),
    (2, "bf01a7bd599456742dd93939b76ba2f0f28be0609512843c5bdf15ee7fbb37d3"),
    (4, "a2bf98c140deae411726ba4a76698be200aab7ce492fdafdc0d738fb0b15d45d"),
    (4, "bb1d2ea4f618e12435eeca7ff7493ca8e4d461802ec62eb26570178f1a4fc1c2"),
    (5, "364ef12900bce69b6847c25e91a98bc65cab1960ff8b467f44b3bb71247a6771"),
    (5, "48fca0e85bc5a8a7ad9e81dc34c145dbf5b9d14f4bad26561c4b050aaaf7cddd"),
    (5, "901eec529b5330aa94ebc2e091ac436c960c8fd03fad28c497f879e275687874"),
    (6, "32560a0b3a9b6d9f4166b1985be5f31acee91faba864be72f59d5b702d7fdc36"),
    (6, "3ab086ccb30fcc40bafbc300739478744725ea72dd81ccb6ed058f0cfc069358"),
    (6, "3d1aae43df9d3bba1cd3e989b67393c05d8c7ce27b6890f0f746aeda0c58468f"),
    (6, "45d6a4838d80f43d775a40ad2d223845f7474129d1bd8b7d3115f50b18bd3096"),
    (6, "5b564954bf6c007e2d565c0421cd1997935a7da042657cd6ba781bcb7bc0a6a2"),
    (6, "5d51f38f635ca4f1b9e99e83f3e84eb658e3d00e471bba941410259f1b6039ff"),
    (6, "6b4945245b7fb6e0393335196b39cb69d69095ed1c7dc03b0cc5356e8982a6f0"),
    (6, "84ea881e55b382e9d20879ceddcb33e9314f0667ee09e0c431c21ab094a8fd57"),
    (6, "87cefad23beee0d77f3b030bc06c2879b07c28b397d023e65614228d746e4d27"),
    (6, "bd65a1432b1ac877c2bb796c7697b8fadea75ad9f290e3fe87f41620fa9a165f"),
    (7, "14e6540f1a9e06832d46db87141b145b7f30caf4ed70c48807dfe3e3efc017d3"),
    (7, "14f8abab2c26dac963a8d18baf270779e61cdcb0189222c6b841723149420533"),
    (7, "1d49872fd25d7d42cc139f56ec7d95784311c48fdeeb757fb039f6756af4632c"),
    (7, "216385edc74e84362565966f1aca222104aab7571db2161d6622b408e50be83f"),
    (7, "4202dad0fc10b27c757651f8e5548b6c34a1bd6e3fb6ca3e1f94cd0a6b212ffe"),
    (7, "4307ad726f56700c4e2936e7beab58d7862c3ad35756075e90b4ecb2042cb028"),
    (7, "46c1a1f01967c40d830a600064073a09b90584e3099eb6885dd99c90157d83d9"),
    (7, "bee58466b563f83ae6630b3ae0fee78909177f10101c6c4749a85225753c2a65"),
    (7, "cb616645425ad4269211195425b46451a1e2a8c83317901a9dc66321b8ac21e0"),
    (7, "e7416a86749a4fcdb2838706f45bddeaaf132e614457eb8674a404ad6159789f"),
    (8, "12b5cbc83a2d7607f892c64dc0f556274cd598709e6af02e0b2807e083500595"),
    (8, "1483d4a3b3ea9336b04170028366419b2e5519fa86302f1cef0d22af9c0b9d04"),
    (8, "20451cfd356e5c9fab5de1f9eba42d4acdcb628bcd820f88d3085d529c41bb2a"),
    (8, "4d93e2c624bcba8e7a69ac99eca74c10a0992c856b273942883acef6160982cb"),
    (8, "54d288a8c8a6f6a27a89d2cb32a60bd22ab92c65328803b1caa927fa68a52ae2"),
    (8, "5bba3d1e8ccc08855adadbddfec582ba46d86c8dabf9ebd19db4c8790f7b0f67"),
    (8, "64f611faaa792378d2bb5c1075b25129bee1d31efb0e25c7d0aa9ab251c3d673"),
    (8, "65d844441849234debc4cca2cdb9a194c545a411382d4b1c656e9fbcef150f89"),
    (8, "6f5d18936a6b0af885881b6cbb7f3652859890db5ff15fb4d290c48fd625acd0"),
    (8, "7f4c668e9721af7435feb9548681df70f8f88c359e494e984450c767599ef50e"),
    (8, "f2abc89f9a091f8b98fd2d94ab00de29dfc2f4da8f054b6694760fc9319078a5"),
    (9, "15f39a293253569b825ecf74aee73314a10243ee55d2bb54034b02b7ebff3ab7"),
    (9, "452b40d943d1bd0e409e4c07b0a10f098a60013c560e835c23e0d8f29fee12ce"),
    (9, "65ebacddac1521f30d3151c0c373b2e9a0a7dd857eb91d2d4178782a9017d1bd"),
    (9, "84663151f5681104b739134bfb339b8d89180aa4bbf0fd14b09fc31c8105b4f8"),
    (9, "9c5f1e0d76a639fe50de474723e76b084c8388e34175badc5a4996c62d5b7893"),
    (9, "d08d25199ffb3cc328d10be2faf9afbbce0fff1f487b10e081055009421a913e"),
    (9, "e87c334eb718c2c7efac3279d741fba8557a8f0df74b89cf0211f3b1e708cd3d"),
    (10, "3e34e33535805d9c952d6b24a2fe1cf5ec0fe20069cd992bcb2e5ff50a86db58"),
    (10, "4952a3cc7cce6e6c5f461fbfdc566bdb67e642808ae55573ea912c1528a4d756"),
    (10, "4f385bd076392044006886072f89a201d3e1c8771bea7a4b3df8e3d928478cde"),
    (10, "7ec2a38b09fc7af55ca21a9e6e10f6c929fcd827d1cfd17609c3d5b21f34fa54"),
    (10, "ad60ea21092213f46637da5c7035fe4c9b5296c12359b974379c55824f7fd200"),
    (10, "b0449fa98646d19bef79f036a74083bd95f2a3498fd1ae648c748a8e7e3e550f"),
    (10, "e0e06c4e5c16670072f88a0e44115a4ad76873aec590138a97de64c53a6971cb"),
    (10, "fbed6d69e53625c56c8ac613160ace74d3f811ad726c0ce5ce201bc25cc48d15"),
    (11, "00458c3d730add311f4694fd0e5699bd8b782c33d201a41e6c6512ea74af21c2"),
    (11, "348fadd054ba89fb1e6cf9604be5c931fddb7fbf8aa2477f4e575bca30da9501"),
    (11, "8798d05667c623cd064cfafd62684e105a31d6c7131494ce177145e2df34bc1c"),
    (14, "98409933e22ce39430daa049010012f234a20ec5c129ffe178b54a8a87448082"),
    (17, "a25161775aeb51889b8031dfcc6556b2860a0454fa4b491de0876046bb659ad0"),
    (22, "f010789d886f0f58b71c13f7605f172c48ac1bf899b96e8383b533fba28e1882"),
    (23, "be87ab09f0962124aa1ee225cb450c940132462b56a803bc0613d31df10df1ca"),
    (25, "a461aa5b68a6d13bc829b379f5443a6243cb7e4f30f8400b2ffb79eb44d87175"),
    (27, "44351dbffe32abffe1cada1e512d155ba1ebfa825cc119d63f1d9c22e457dd4e"),
    (29, "3e1ed5bf62282cd10d6560b1b3e4c15c67bf29961dbe651500a54c9f915a42fb"),
    (31, "fc25ad34a632bf858a838451c26092cec1c8d61d682d25c5c1015b9ba82ee594"),
    (32, "14391b02e551ca40cd99faa21079da93cd9fa5afe3b942949785b78daa89eda8"),
    (36, "7823c6e52291253e590247cb559092066525a0999f4e0d6610d509796b1c7111"),
    (38, "2185d091f0d18929301d50c7fa3b9768ca963baf605fa211a59de546c067d281"),
    (40, "1cca0b664633e4a35fef47be3e11530235d01982be4e37b8545c4bccf215e923"),
    (41, "b4f8b45cf989c1f850237e5208d70a52a690a15f58c70c0a5ae24aeacd1486d1"),
    (41, "b99ad3d60450e13c66a6647837182c8d43cb83e3535202cb0680b5ab77cf34fb"),
    (42, "24f75a411fffd05e7dc3d97d817163c3096fcb500f3dfd12e44887a997ff59c8"),
    (45, "15e9f9c2d2f7eb7fc9d2c91fd14222f39e125bd718ff20d623353ef0deb6d6b2"),
    (46, "7a0f1780cc4a49db9b6a987b68dcb3b85f4e0030412eb07c34c4f8e5de79613e"),
    (48, "015fbbc20989fbb68e3b36357ca1ae6466b87ad53fbb32a775d021d18a04dda7"),
    (49, "84a239e437b5df260ac26d0b0b15bf81bb80a3e888944f968afc4b9e0f8db9dc"),
    (52, "f71b8429686db2a2a2bc0e0b4b089b6500b8830d411a77e35e44dda9c92752a5"),
    (55, "e99b7dd4312426a883e1068b0ef19d10af2628cfdb29f4b17cd541e9413754e6"),
    (56, "fa427f3188d8e347671a5b0a267829bddb1e0c6b96457e5ad5123f2fc53fa4cf"),
    (57, "113a6fccf090335f6b032f76ee9232cf42ac8d4bc19fb967ce2802c29ff07e21"),
    (58, "891eb90d485c29b2f9fd14b7e346e8d6648adf4804bec3bdb8e6c282d22b448a"),
    (59, "48818e6838ca57ad82b04e6e0ea5a29dd8c5d27e061b7918faf60ff3ab4cec22"),
    (59, "a23ce320a263912bd36cf0c35b9ad0a74140777c9c22328ff25cccb0857ba5eb"),
    (61, "3eda555fd05a3560a38583475f0e6707677970b7a4c439d5d791de42eb399088"),
    (63, "4aaa6b452831d687c66b1fb11eca8ebcfb279f3e2f339510c68a58e4766e0804"),
    (94, "78ae2f84a6346e6be883d835cea1ad7cb42f5923f4a354b25ebae4459bb2ec65"),
    (94, "ade2b55b8f1084f40968e5dcabca04797910fe9a847be2eb95654159ae422c30"),
)


def _string_constants(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def test_ban_list_is_not_vacuous() -> None:
    assert len(BANNED_PHRASES) > 100
    assert len({h for _, h in BANNED_PHRASES}) > 100
    assert all(len(h) == 64 for _, h in BANNED_PHRASES)


def _hits(constants: list[str], phrases=BANNED_PHRASES) -> list[str]:
    by_len: dict[int, set[str]] = {}
    for n, h in phrases:
        by_len.setdefault(n, set()).add(h)
    found = []
    for const in constants:
        toks = _tokens(const)
        for n, hashes in by_len.items():
            for i in range(0, len(toks) - n + 1):
                if _digest(toks[i:i + n]) in hashes:
                    found.append(" ".join(toks[i:i + n])[:40])
    return found


def test_module_embeds_no_native_birth_data_or_life_events() -> None:
    hits = _hits(_string_constants(MODULE_PATH))
    assert hits == [], f"removed native data is back in {MODULE_PATH.name}: {len(hits)} phrase(s)"


def test_module_has_no_chart_id_default() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    uuid_re = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
    assert not [c for c in _string_constants(MODULE_PATH) if uuid_re.search(c)]
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "NATIVE_CHART_ID"]


def test_ban_scanner_catches_a_planted_phrase() -> None:
    """Prove the detector can read false: a synthetic phrase hashed the same way is found inside
    a longer constant, and a near-miss is not."""
    phrase = "synthetic planted phrase of five"
    toks = _tokens(phrase)
    phrases = ((len(toks), _digest(toks)),)
    assert _hits(["prefix words " + phrase + " and a suffix"], phrases)
    assert not _hits(["synthetic planted phrase of six"], phrases)
