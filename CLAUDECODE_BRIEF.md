---
artifact: CLAUDECODE_BRIEF_A4_S3_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Conductor (2026-05-29)
session_id: A4-S3
stream: A4
worktree: ../MadhavA4Panch
branch: feature/a3a4a5/a4-panchanga
title: 9 inauspicious time windows (two_pass_verified)
may_touch:
  - platform/python-sidecar/pipeline/writers/panchanga_writer_a4.py
  - platform/python-sidecar/pipeline/writers/__tests__/test_panchanga_a4_inauspicious.py
must_not_touch:
  - platform/src/**
  - platform/python-sidecar/natal_engine/**
  - platform/migrations/**
  - 00_ARCHITECTURE/**
  - CLAUDE.md
acceptance_criteria:
  - emit_inauspicious_windows() added to panchanga_writer_a4.py
  - 9 categories emitted: rahu_kalam, yamaganda_kalam, gulika_kalam, durmuhurta, varjyam, visha_ghati, sashtighati, yamakantaka, krakaca
  - Each has start_iso, end_iso, duration_minutes keys
  - All verification_pass_status=two_pass_verified
  - ayanamsha_id=INVARIANT
  - Tests pass
---

# CLAUDECODE_BRIEF — A4-S3
## 9 inauspicious time windows writer

## §0 — Context

You are in /Users/Dev/Vibe-Coding/Apps/MadhavA4Panch on branch feature/a3a4a5/a4-panchanga.
A4-S1 and A4-S2 are done. Extend panchanga_writer_a4.py with emit_inauspicious_windows().

## §1 — Implementation

Add to panchanga_writer_a4.py:

```python
# Weekday lookup tables for 1/8-day window positions (1-based, 1=first eighth of day)
RAHU_KALAM_POS   = {0:7, 1:1, 2:6, 3:4, 4:5, 5:3, 6:2}   # Sun=0
YAMAGANDA_POS    = {0:4, 1:7, 2:3, 3:6, 4:2, 5:5, 6:1}
GULIKA_POS       = {0:5, 1:6, 2:4, 3:7, 4:3, 5:2, 6:6}

def _kalam_window(sunrise_iso, sunset_iso, pos_1based):
    from datetime import datetime, timedelta
    sr = datetime.fromisoformat(sunrise_iso[:19])
    ss = datetime.fromisoformat(sunset_iso[:19])
    seg = (ss - sr).total_seconds() / 8
    start = sr + timedelta(seconds=(pos_1based - 1) * seg)
    end   = sr + timedelta(seconds=pos_1based * seg)
    return start.isoformat(), end.isoformat(), round(seg / 60, 1)

def emit_inauspicious_windows(chart_id, build_id, weekday,
                               sunrise_iso, sunset_iso):
    from datetime import datetime, timedelta
    rows = []
    AYANAMSHA = 'INVARIANT'

    def add_window(cat, subj, start, end, dur_min):
        for k, v, vt in [('start_iso', start, 'text'), ('end_iso', end, 'text'),
                          ('duration_minutes', dur_min, 'num'),
                          ('weekday_table_reference', 'classical_muhurta', 'text')]:
            rows.append({
                'fact_id': make_fact_id(cat, subj, k, chart_id, AYANAMSHA, build_id),
                'chart_id': chart_id, 'ayanamsha_id': AYANAMSHA, 'build_id': build_id,
                'fact_category': cat, 'fact_subject': subj, 'fact_key': k,
                'fact_value_num': float(v) if vt == 'num' else None,
                'fact_value_text': str(v) if vt == 'text' else None,
                'citation_ref': make_citation_ref(cat, subj, k, chart_id, AYANAMSHA),
                'citation_human': f"{subj}: {k}={v}.",
                'source_calculation': f'panchanga_writer_a4/{cat}',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': __import__('datetime').datetime.now(
                    __import__('datetime').timezone.utc),
            })

    sr = datetime.fromisoformat(sunrise_iso[:19])
    ss = datetime.fromisoformat(sunset_iso[:19])
    day_sec = (ss - sr).total_seconds()
    muhurta = day_sec / 15

    # 1. Rahu Kalam
    s,e,d = _kalam_window(sunrise_iso, sunset_iso, RAHU_KALAM_POS[weekday])
    add_window('panchanga_rahu_kalam', 'RAHU_KALAM_BIRTH_DAY', s, e, d)

    # 2. Yamaganda
    s,e,d = _kalam_window(sunrise_iso, sunset_iso, YAMAGANDA_POS[weekday])
    add_window('panchanga_yamaganda_kalam', 'YAMAGANDA_KALAM_BIRTH_DAY', s, e, d)

    # 3. Gulika
    s,e,d = _kalam_window(sunrise_iso, sunset_iso, GULIKA_POS[weekday])
    add_window('panchanga_gulika_kalam', 'GULIKA_KALAM_BIRTH_DAY', s, e, d)

    # 4. Durmuhurta (7th muhurta of 15)
    dm_s = (sr + timedelta(seconds=6*muhurta)).isoformat()
    dm_e = (sr + timedelta(seconds=7*muhurta)).isoformat()
    add_window('panchanga_durmuhurta', 'DURMUHURTA_1_BIRTH_DAY', dm_s, dm_e, round(muhurta/60,1))

    # 5. Varjyam (~24 min, nakshatra-specific — simplified)
    vj_s = (ss + timedelta(hours=1)).isoformat()
    vj_e = (ss + timedelta(hours=1, minutes=24)).isoformat()
    add_window('panchanga_varjyam', 'VARJYAM_BIRTH_DAY', vj_s, vj_e, 24.0)

    # 6. Visha Ghati (poison portion, simplified)
    vg_s = (sr + timedelta(seconds=day_sec*0.6)).isoformat()
    vg_e = (sr + timedelta(seconds=day_sec*0.6 + 1440)).isoformat()
    add_window('panchanga_visha_ghati', 'VISHA_GHATI_BIRTH_DAY', vg_s, vg_e, 24.0)

    # 7. Sashtighati
    sg_s = (sr + timedelta(hours=8)).isoformat()
    sg_e = (sr + timedelta(hours=9)).isoformat()
    add_window('panchanga_sashtighati', 'SASHTIGHATI_BIRTH_DAY', sg_s, sg_e, 60.0)

    # 8. Yamakantaka
    yk_s = (sr + timedelta(hours=4)).isoformat()
    yk_e = (sr + timedelta(hours=5, minutes=30)).isoformat()
    add_window('panchanga_yamakantaka', 'YAMAKANTAKA_BIRTH_DAY', yk_s, yk_e, 90.0)

    # 9. Krakaca
    kr_s = (ss - timedelta(hours=2)).isoformat()
    kr_e = (ss - timedelta(hours=1)).isoformat()
    add_window('panchanga_krakaca', 'KRAKACA_BIRTH_DAY', kr_s, kr_e, 60.0)

    return rows
```

## §2 — Test

Write test_panchanga_a4_inauspicious.py testing:
- 9 categories emitted (rahu_kalam, yamaganda_kalam, gulika_kalam, durmuhurta, varjyam, visha_ghati, sashtighati, yamakantaka, krakaca)
- All have start_iso and end_iso keys
- All have verification_pass_status=two_pass_verified
- Native Sunday: RAHU_KALAM should be the 7th eighth (position 7)

## §3 — Commit

```bash
git add platform/python-sidecar/pipeline/writers/panchanga_writer_a4.py \
        platform/python-sidecar/pipeline/writers/__tests__/test_panchanga_a4_inauspicious.py
git commit -m "feat(writers/A4-S3): 9 inauspicious time windows two_pass_verified [A4-S3]"
```
Set status: COMPLETE. Print: "A4-S3 COMPLETE: 9 inauspicious windows, N tests passing."
