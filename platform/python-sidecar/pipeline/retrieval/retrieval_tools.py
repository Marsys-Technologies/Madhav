"""
pipeline.retrieval.retrieval_tools — Query helpers for panchanga and chart_facts retrieval.
A4-S9: query_panchanga_at_birth — retrieve panchanga chart_facts rows by scope.
"""


def query_panchanga_at_birth(conn, chart_id, ayanamsha_ids=None, scope_filter='all'):
    """
    Query panchanga facts for a chart.
    scope_filter: 'all' | 'core' | 'inauspicious' | 'auspicious' | 'panchaka' | 'astronomical'
    """
    if ayanamsha_ids is None:
        ayanamsha_ids = [
            'lahiri_chitrapaksha', 'true_chitra', 'krishnamurti',
            'raman', 'surya_siddhanta_classical',
        ]

    SCOPE_CATEGORIES = {
        'core': [
            'panchanga_tithi', 'panchanga_vara', 'panchanga_nakshatra_moon',
            'panchanga_yoga', 'panchanga_karana', 'panchanga_hora_birth',
            'panchanga_choghadiya_birth',
        ],
        'inauspicious': [
            'panchanga_rahu_kalam', 'panchanga_yamaganda_kalam', 'panchanga_gulika_kalam',
            'panchanga_durmuhurta', 'panchanga_varjyam', 'panchanga_visha_ghati',
            'panchanga_sashtighati', 'panchanga_yamakantaka', 'panchanga_krakaca',
        ],
        'auspicious': [
            'panchanga_abhijit_muhurta', 'panchanga_brahma_muhurta', 'panchanga_pratah_sandhya',
            'panchanga_madhyahna_sandhya', 'panchanga_sayam_sandhya', 'panchanga_amrit_kaal',
            'panchanga_vijaya_muhurta', 'panchanga_godhuli_muhurta', 'panchanga_nishita_kala',
        ],
        'panchaka': [
            'panchanga_panchaka_classification', 'panchaka_flag', 'bhadra_flag',
            'panchanga_agni_vasa', 'panchanga_disha_shul',
        ],
        'astronomical': [
            'panchanga_astronomical', 'panchanga_sun_moon_dynamics',
        ],
    }

    if scope_filter == 'all':
        category_filter = None  # return all panchanga categories
    else:
        category_filter = SCOPE_CATEGORIES.get(scope_filter, None)

    placeholders_aya = ','.join(['%s'] * len(ayanamsha_ids))

    if category_filter:
        placeholders_cat = ','.join(['%s'] * len(category_filter))
        query = f"""
            SELECT fact_category, fact_subject, fact_key, fact_value_text, fact_value_num,
                   ayanamsha_id, citation_human, verification_pass_status
            FROM chart_facts
            WHERE chart_id = %s
              AND ayanamsha_id IN ({placeholders_aya})
              AND fact_category IN ({placeholders_cat})
            ORDER BY fact_category, ayanamsha_id, fact_subject, fact_key
        """
        params = [chart_id] + ayanamsha_ids + category_filter
    else:
        query = f"""
            SELECT fact_category, fact_subject, fact_key, fact_value_text, fact_value_num,
                   ayanamsha_id, citation_human, verification_pass_status
            FROM chart_facts
            WHERE chart_id = %s
              AND ayanamsha_id IN ({placeholders_aya})
              AND fact_category LIKE 'panchanga_%'
            ORDER BY fact_category, ayanamsha_id, fact_subject, fact_key
        """
        params = [chart_id] + ayanamsha_ids

    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cols = [
            'fact_category', 'fact_subject', 'fact_key', 'fact_value_text', 'fact_value_num',
            'ayanamsha_id', 'citation_human', 'verification_pass_status',
        ]
        return [dict(zip(cols, row)) for row in rows]
    except Exception:
        return []
