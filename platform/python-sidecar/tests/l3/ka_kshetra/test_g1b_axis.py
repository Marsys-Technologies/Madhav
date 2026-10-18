"""K4: development-registry dates only; no held-out outcomes consumed."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from services.ka_kshetra.g1_inputs import field_days


def test_registry_development_dates_and_boundary_timezones_share_birth_axis():
    fixture=Path(__file__).parents[1]/'gochara_eval/fixtures/candidate_3_0/event_registry_v2_3.json'
    dates=[row['date'] for row in json.loads(fixture.read_text())['events'] if row['tier']=='dev']
    assert len(dates)>=3
    birth=datetime(1984,2,5,5,13,tzinfo=timezone.utc)
    for date in dates:
        utc=datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        expected=(utc-birth).total_seconds()/86400
        for hours in (-12,5.5,14):
            local=utc.astimezone(timezone(timedelta(hours=hours)))
            assert field_days(local,birth)==expected
        for seconds in (-1,0,1):
            assert field_days(utc+timedelta(seconds=seconds),birth)==pytest.approx(expected+seconds/86400)
    assert field_days(birth,birth)==0.
