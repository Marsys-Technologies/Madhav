"""
Empirical PyJHora API discovery — native chart 1984-02-05 10:43 IST Bhubaneswar.
Run with QT_QPA_PLATFORM=offscreen to avoid PyQt6 headless crash.
NOT a test. Throwaway. Drives encoding of the typed adapter.
"""
from __future__ import annotations
import json

# Lazy / direct-submodule import strategy — never `import jhora` (GUI paths).
from jhora.panchanga import drik
from jhora import utils, const
from jhora.horoscope.chart import charts

LAT, LON, TZ = 20.2961, 85.8245, 5.5
Y, M, D = 1984, 2, 5
HH, MM, SS = 10, 43, 0


def main():
    place = drik.Place("Bhubaneswar", LAT, LON, TZ)
    dob = drik.Date(Y, M, D)
    tob = (HH, MM, SS)
    jd = utils.julian_day_number(dob, tob)
    print("jd (julian_day_number):", jd)

    # default ayanamsa
    drik.set_ayanamsa_mode("LAHIRI")
    print("ayanamsa value:", drik.get_ayanamsa_value(jd))

    # rasi chart D1
    rc = charts.rasi_chart(jd, place)
    print("\n=== rasi_chart (D1) ===")
    print("len:", len(rc))
    for row in rc:
        print(repr(row))

    # nakshatra / tithi / yoga / karana / vaara
    print("\n=== panchanga ===")
    print("nakshatra:", drik.nakshatra(jd, place))
    print("tithi:", drik.tithi(jd, place))
    print("yogam:", drik.yogam(jd, place))
    print("karana:", drik.karana(jd, place))
    print("vaara:", drik.vaara(jd, place))
    print("lunar_phase:", drik.lunar_phase(jd))

    # nakshatra_pada helper on moon longitude
    moon_row = rc[2]  # [planet_id, (rasi, long)]
    print("\nmoon_row:", moon_row)
    moon_full_long = moon_row[1][0] * 30 + moon_row[1][1]
    print("moon full long:", moon_full_long)
    print("nakshatra_pada(moon):", drik.nakshatra_pada(moon_full_long))

    # navamsa D9
    print("\n=== navamsa (D9) via charts.divisional_chart ===")
    try:
        d9 = charts.divisional_chart(jd, place, divisional_chart_factor=9)
        print("d9 len:", len(d9))
        for row in d9:
            print(repr(row))
    except Exception as e:
        print("divisional_chart err:", repr(e))

    # retrograde
    print("\n=== retrograde ===")
    print("planets_in_retrograde:", drik.planets_in_retrograde(jd, place))

    # vimshottari dasha
    print("\n=== vimshottari dasha ===")
    try:
        from jhora.horoscope.dhasa.graha import vimsottari
        vd = vimsottari.get_vimsottari_dhasa_bhukthi(jd, place)
        print("type:", type(vd))
        print("first 3:", vd[:3] if isinstance(vd, list) else vd)
    except Exception as e:
        print("vimsottari err:", repr(e))
        import traceback; traceback.print_exc()

    # ascendant detail
    print("\n=== ascendant ===")
    print("ascendant:", drik.ascendant(jd, place))


if __name__ == "__main__":
    main()
