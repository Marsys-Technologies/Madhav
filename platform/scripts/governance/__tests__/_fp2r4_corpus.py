"""Reviewer corpus of FP2 round 4 (cases19-34), embedded verbatim and generated from the reviewer scratch files.
PARTIAL: every case must read not-scanned. HIDDEN: the statement is read (the `hidden` table is found) or not scanned.
SETS: controls that keep exactly their tables. Cases that stay scanned with an unknowable truth are documented in the README
(VACUUM FULL, an imported delegate called instead of the in-file class, COPY ... TO export, benign mutations of copies)."""
PARTIAL = {'r22_alter_do': 'def run(cur):\n'
                 "    cur.execute('DO $$ BEGIN ALTER /*x*/ TABLE hidden ADD COLUMN b int; END $$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_alter_func': 'def run(cur):\n'
                   "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN ALTER /*x*/ TABLE hidden ADD COLUMN b int; END $$ "
                   "LANGUAGE plpgsql')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_alter_tag': 'def run(cur):\n'
                  "    cur.execute('DO $t$ BEGIN ALTER /*x*/ TABLE hidden ADD COLUMN b int; END $t$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_alter_top': 'def run(cur):\n'
                  "    cur.execute('ALTER /*x*/ TABLE hidden ADD COLUMN b int')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create2_do': 'def run(cur):\n'
                   "    cur.execute('DO $$ BEGIN CREATE TEMP /*x*/ TABLE hidden (a int); END $$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create2_func': 'def run(cur):\n'
                     "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN CREATE TEMP /*x*/ TABLE hidden (a int); END $$ "
                     "LANGUAGE plpgsql')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create2_tag': 'def run(cur):\n'
                    "    cur.execute('DO $t$ BEGIN CREATE TEMP /*x*/ TABLE hidden (a int); END $t$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create2_top': 'def run(cur):\n'
                    "    cur.execute('CREATE TEMP /*x*/ TABLE hidden (a int)')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create_do': 'def run(cur):\n'
                  "    cur.execute('DO $$ BEGIN CREATE /*x*/ TABLE hidden (a int); END $$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create_func': 'def run(cur):\n'
                    "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN CREATE /*x*/ TABLE hidden (a int); END $$ LANGUAGE "
                    "plpgsql')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create_tag': 'def run(cur):\n'
                   "    cur.execute('DO $t$ BEGIN CREATE /*x*/ TABLE hidden (a int); END $t$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_create_top': 'def run(cur):\n'
                   "    cur.execute('CREATE /*x*/ TABLE hidden (a int)')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas2_do': 'def run(cur):\n'
                     "    cur.execute('DO $$ BEGIN CREATE /*x*/ TABLE hidden AS SELECT 1; END $$')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas2_func': 'def run(cur):\n'
                       "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN CREATE /*x*/ TABLE hidden AS SELECT 1; END $$ "
                       "LANGUAGE plpgsql')\n"
                       'def own(cur):\n'
                       "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas2_tag': 'def run(cur):\n'
                      "    cur.execute('DO $t$ BEGIN CREATE /*x*/ TABLE hidden AS SELECT 1; END $t$')\n"
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas2_top': 'def run(cur):\n'
                      "    cur.execute('CREATE /*x*/ TABLE hidden AS SELECT 1')\n"
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas_do': 'def run(cur):\n'
                    "    cur.execute('DO $$ BEGIN CREATE TABLE hidden /*x*/ AS SELECT 1; END $$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas_func': 'def run(cur):\n'
                      "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN CREATE TABLE hidden /*x*/ AS SELECT 1; END $$ "
                      "LANGUAGE plpgsql')\n"
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas_tag': 'def run(cur):\n'
                     "    cur.execute('DO $t$ BEGIN CREATE TABLE hidden /*x*/ AS SELECT 1; END $t$')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_createas_top': 'def run(cur):\n'
                     "    cur.execute('CREATE TABLE hidden /*x*/ AS SELECT 1')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_drop_do': 'def run(cur):\n'
                "    cur.execute('DO $$ BEGIN DROP /*x*/ TABLE hidden; END $$')\n"
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_drop_func': 'def run(cur):\n'
                  "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN DROP /*x*/ TABLE hidden; END $$ LANGUAGE plpgsql')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_drop_tag': 'def run(cur):\n'
                 "    cur.execute('DO $t$ BEGIN DROP /*x*/ TABLE hidden; END $t$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_drop_top': 'def run(cur):\n'
                 "    cur.execute('DROP /*x*/ TABLE hidden')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_dropsch_do': 'def run(cur):\n'
                   "    cur.execute('DO $$ BEGIN DROP /*x*/ SCHEMA hidden CASCADE; END $$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_dropsch_func': 'def run(cur):\n'
                     "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN DROP /*x*/ SCHEMA hidden CASCADE; END $$ LANGUAGE "
                     "plpgsql')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_dropsch_tag': 'def run(cur):\n'
                    "    cur.execute('DO $t$ BEGIN DROP /*x*/ SCHEMA hidden CASCADE; END $t$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_dropsch_top': 'def run(cur):\n'
                    "    cur.execute('DROP /*x*/ SCHEMA hidden CASCADE')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_merge_do': 'def run(cur):\n'
                 "    cur.execute('DO $$ BEGIN MERGE /*x*/ INTO hidden USING s ON true WHEN MATCHED THEN DELETE; END $$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_merge_func': 'def run(cur):\n'
                   "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN MERGE /*x*/ INTO hidden USING s ON true WHEN MATCHED "
                   "THEN DELETE; END $$ LANGUAGE plpgsql')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_merge_tag': 'def run(cur):\n'
                  "    cur.execute('DO $t$ BEGIN MERGE /*x*/ INTO hidden USING s ON true WHEN MATCHED THEN DELETE; END $t$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_merge_top': 'def run(cur):\n'
                  "    cur.execute('MERGE /*x*/ INTO hidden USING s ON true WHEN MATCHED THEN DELETE')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh2_do': 'def run(cur):\n'
                    "    cur.execute('DO $$ BEGIN REFRESH MATERIALIZED /*x*/ VIEW hidden; END $$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh2_func': 'def run(cur):\n'
                      "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN REFRESH MATERIALIZED /*x*/ VIEW hidden; END $$ "
                      "LANGUAGE plpgsql')\n"
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh2_tag': 'def run(cur):\n'
                     "    cur.execute('DO $t$ BEGIN REFRESH MATERIALIZED /*x*/ VIEW hidden; END $t$')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh2_top': 'def run(cur):\n'
                     "    cur.execute('REFRESH MATERIALIZED /*x*/ VIEW hidden')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh_do': 'def run(cur):\n'
                   "    cur.execute('DO $$ BEGIN REFRESH /*x*/ MATERIALIZED VIEW hidden; END $$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh_func': 'def run(cur):\n'
                     "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN REFRESH /*x*/ MATERIALIZED VIEW hidden; END $$ "
                     "LANGUAGE plpgsql')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh_tag': 'def run(cur):\n'
                    "    cur.execute('DO $t$ BEGIN REFRESH /*x*/ MATERIALIZED VIEW hidden; END $t$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_refresh_top': 'def run(cur):\n'
                    "    cur.execute('REFRESH /*x*/ MATERIALIZED VIEW hidden')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto2_do': 'def run(cur):\n'
                    "    cur.execute('DO $$ BEGIN SELECT 1 /*x*/ INTO hidden; END $$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto2_func': 'def run(cur):\n'
                      "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN SELECT 1 /*x*/ INTO hidden; END $$ LANGUAGE "
                      "plpgsql')\n"
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto2_tag': 'def run(cur):\n'
                     "    cur.execute('DO $t$ BEGIN SELECT 1 /*x*/ INTO hidden; END $t$')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto2_top': 'def run(cur):\n'
                     "    cur.execute('SELECT 1 /*x*/ INTO hidden')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto_do': 'def run(cur):\n'
                   "    cur.execute('DO $$ BEGIN SELECT 1 INTO /*x*/ hidden; END $$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto_func': 'def run(cur):\n'
                     "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN SELECT 1 INTO /*x*/ hidden; END $$ LANGUAGE plpgsql')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto_tag': 'def run(cur):\n'
                    "    cur.execute('DO $t$ BEGIN SELECT 1 INTO /*x*/ hidden; END $t$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r22_selinto_top': 'def run(cur):\n'
                    "    cur.execute('SELECT 1 INTO /*x*/ hidden')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_alias1': 'from c import imported, X\n'
               "QL = ['DELETE FROM a']\n"
               'R = QL\n'
               'R.append(X)\n'
               'def run(cur):\n'
               '    for q in QL:\n'
               '        cur.execute(q)\n'
               'def own(cur):\n'
               "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_alias2': 'from c import imported, X\n'
               "QL = ['DELETE FROM a']\n"
               'R = QL\n'
               "R.append('DELETE FROM b')\n"
               'def run(cur):\n'
               '    for q in QL:\n'
               '        cur.execute(q)\n'
               'def own(cur):\n'
               "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_alias3': 'from c import imported, X\n'
               "QL = ['DELETE FROM a']\n"
               'R, S = QL, 1\n'
               'R.append(X)\n'
               'def run(cur):\n'
               '    for q in QL:\n'
               '        cur.execute(q)\n'
               'def own(cur):\n'
               "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_alias4': 'from c import imported, X\n'
               "QL = ['DELETE FROM a']\n"
               'R = S = QL\n'
               'R.append(X)\n'
               'def run(cur):\n'
               '    for q in QL:\n'
               '        cur.execute(q)\n'
               'def own(cur):\n'
               "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_alias_walrus': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     '(R := QL).append(X)\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_append_f': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 "QL.append(f'DELETE FROM {X}')\n"
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_attr_container': 'from c import imported, X\n'
                       "QL = ['DELETE FROM a']\n"
                       'class H:\n'
                       "    q = ['DELETE FROM a']\n"
                       'H.q.append(X)\n'
                       'def run(cur):\n'
                       '    for q in H.q:\n'
                       '        cur.execute(q)\n'
                       'def own(cur):\n'
                       "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_attr_container2': 'from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        'class H:\n'
                        "    q = ['DELETE FROM a']\n"
                        'R = H.q\n'
                        'R.append(X)\n'
                        'def run(cur):\n'
                        '    for q in H.q:\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_attr_container3': 'from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        'class H:\n'
                        '    pass\n'
                        "H.q = ['DELETE FROM a']\n"
                        'H.q.append(X)\n'
                        'def run(cur):\n'
                        '    for q in H.q:\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_bound_method': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'f = QL.append\n'
                     'f(X)\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_bound_method2': 'from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      "getattr(QL, 'append')(X)\n"
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_chain': 'from c import imported, X\n'
              "QL = ['DELETE FROM a']\n"
              'import itertools\n'
              'for x in itertools.chain(QL, imported):\n'
              '    QL.append(x)\n'
              'def run(cur):\n'
              '    for q in QL:\n'
              '        cur.execute(q)\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_clear_then': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'QL.clear()\n'
                   'QL.extend(imported)\n'
                   'def run(cur):\n'
                   '    for q in QL:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_closure': 'from c import imported, X\n'
                "QL = ['DELETE FROM a']\n"
                'def f():\n'
                '    QL.append(X)\n'
                'f()\n'
                'def run(cur):\n'
                '    for q in QL:\n'
                '        cur.execute(q)\n'
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_closure_nested': 'from c import imported, X\n'
                       "QL = ['DELETE FROM a']\n"
                       'def f():\n'
                       '    def g():\n'
                       '        QL.append(X)\n'
                       '    g()\n'
                       'f()\n'
                       'def run(cur):\n'
                       '    for q in QL:\n'
                       '        cur.execute(q)\n'
                       'def own(cur):\n'
                       "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_comp_iter': 'from c import imported, X\n'
                  "QL = ['DELETE FROM a']\n"
                  '[QL.append(x) for x in [X]]\n'
                  'def run(cur):\n'
                  '    for q in QL:\n'
                  '        cur.execute(q)\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_copy_copy': 'from c import imported, X\n'
                  "QL = ['DELETE FROM a']\n"
                  'import copy\n'
                  'R = copy.copy(QL)\n'
                  'R.append(X)\n'
                  'QL = R\n'
                  'def run(cur):\n'
                  '    for q in QL:\n'
                  '        cur.execute(q)\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_default_arg': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    'def f(l=QL):\n'
                    '    l.append(X)\n'
                    'f()\n'
                    'def run(cur):\n'
                    '    for q in QL:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_default_arg_kw': 'from c import imported, X\n'
                       "QL = ['DELETE FROM a']\n"
                       'def f(*, l=QL):\n'
                       '    l.append(X)\n'
                       'f()\n'
                       'def run(cur):\n'
                       '    for q in QL:\n'
                       '        cur.execute(q)\n'
                       'def own(cur):\n'
                       "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_del_item': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 'del QL[0]\n'
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dict_alias': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   "T = {'k': QL}\n"
                   "T['k'].append(X)\n"
                   'def run(cur):\n'
                   '    for q in QL:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dict_comp': 'from c import imported, X\n'
                  "QL = ['DELETE FROM a']\n"
                  'D = {k: k for k in QL}\n'
                  "D['x'] = X\n"
                  'def run(cur):\n'
                  '    for q in D:\n'
                  '        cur.execute(q)\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dict_of_list': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     "N = {'k': ['DELETE FROM a']}\n"
                     "N['k'].append(X)\n"
                     'def run(cur):\n'
                     "    for q in N['k']:\n"
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dict_setdefault': 'from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        "D = {'q': 'DELETE FROM a'}\n"
                        "D.setdefault('z', X)\n"
                        'def run(cur):\n'
                        '    for q in D.values():\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dict_store': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   "D = {'q': 'DELETE FROM a'}\n"
                   "D['z'] = X\n"
                   'def run(cur):\n'
                   '    for q in D.values():\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dict_update': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    "D = {'q': 'DELETE FROM a'}\n"
                    'D.update(imported)\n'
                    'def run(cur):\n'
                    '    for q in D.values():\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dunder_iadd': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    'QL.__iadd__(imported)\n'
                    'def run(cur):\n'
                    '    for q in QL:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_dunder_setitem': 'from c import imported, X\n'
                       "QL = ['DELETE FROM a']\n"
                       'QL.__setitem__(0, X)\n'
                       'def run(cur):\n'
                       '    for q in QL:\n'
                       '        cur.execute(q)\n'
                       'def own(cur):\n'
                       "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_exec_in_other_fn_mut': 'from c import imported, X\n'
                             "QL = ['DELETE FROM a']\n"
                             'def helper(cur, q):\n'
                             '    cur.execute(q)\n'
                             'QL.append(X)\n'
                             'def run(cur):\n'
                             '    for q in QL:\n'
                             '        helper(cur, q)\n'
                             'def own(cur):\n'
                             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_exec_mut': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 "exec('QL.append(X)')\n"
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_extend_imported': 'from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        'QL.extend(imported)\n'
                        'def run(cur):\n'
                        '    for q in QL:\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_for_alias': 'from c import imported, X\n'
                  "QL = ['DELETE FROM a']\n"
                  'for R in [QL]:\n'
                  '    R.append(X)\n'
                  'def run(cur):\n'
                  '    for q in QL:\n'
                  '        cur.execute(q)\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_for_alias2': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'for R in (QL, QL):\n'
                   '    R.append(X)\n'
                   'def run(cur):\n'
                   '    for q in QL:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_genexp': 'from c import imported, X\n'
               "QL = ['DELETE FROM a']\n"
               'list(QL.append(x) for x in [X])\n'
               'def run(cur):\n'
               '    for q in QL:\n'
               '        cur.execute(q)\n'
               'def own(cur):\n'
               "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_global_stmt': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    'def f():\n'
                    '    global QL\n'
                    '    QL = [X]\n'
                    'f()\n'
                    'def run(cur):\n'
                    '    for q in QL:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_global_stmt2': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'def f():\n'
                     '    global QL\n'
                     '    QL = QL + [X]\n'
                     'f()\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_globals_mut': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    "globals()['QL'].append(X)\n"
                    'def run(cur):\n'
                    '    for q in QL:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_globals_mut2': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'g = globals()\n'
                     "g['QL'].append(X)\n"
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_iadd_imported': 'from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      'QL += imported\n'
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_ifexp_alias': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    'R = QL if X else []\n'
                    'R.append(X)\n'
                    'def run(cur):\n'
                    '    for q in QL:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_insert_method': 'from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      'QL.insert(0, X)\n'
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_item_assign': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    'QL[0] = X\n'
                    'def run(cur):\n'
                    '    for q in QL:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_lambda_cap': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'g = lambda: QL.append(X)\n'
                   'g()\n'
                   'def run(cur):\n'
                   '    for q in QL:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_lambda_def': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'g = lambda l=QL: l.append(X)\n'
                   'g()\n'
                   'def run(cur):\n'
                   '    for q in QL:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_list_alias': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'T = [QL]\n'
                   'T[0].append(X)\n'
                   'def run(cur):\n'
                   '    for q in QL:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_list_comp_alias': 'from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        'L2 = [q for q in QL]\n'
                        'L2.append(X)\n'
                        'def run(cur):\n'
                        '    for q in L2:\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_list_copy': 'from c import imported, X\n'
                  "QL = ['DELETE FROM a']\n"
                  'R = list(QL)\n'
                  'R.append(X)\n'
                  'QL = R\n'
                  'def run(cur):\n'
                  '    for q in QL:\n'
                  '        cur.execute(q)\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_list_copy2': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'R = list(QL)\n'
                   'R.append(X)\n'
                   'def run(cur):\n'
                   '    for q in R:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_list_plus': 'from c import imported, X\n'
                  "QL = ['DELETE FROM a']\n"
                  'L2 = QL + [X]\n'
                  'def run(cur):\n'
                  '    for q in L2:\n'
                  '        cur.execute(q)\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_list_times': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'L2 = QL * 2\n'
                   'L2.append(X)\n'
                   'def run(cur):\n'
                   '    for q in L2:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_map_call': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 'list(map(lambda x: QL.append(x), [X]))\n'
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_method_via_type': 'from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        'list.append(QL, X)\n'
                        'def run(cur):\n'
                        '    for q in QL:\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_method_via_type2': 'from c import imported, X\n'
                         "QL = ['DELETE FROM a']\n"
                         'list.extend(QL, imported)\n'
                         'def run(cur):\n'
                         '    for q in QL:\n'
                         '        cur.execute(q)\n'
                         'def own(cur):\n'
                         "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_nested_list': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    "N = [['DELETE FROM a']]\n"
                    'N[0].append(X)\n'
                    'def run(cur):\n'
                    '    for q in N[0]:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_nested_list2': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     "N = [['DELETE FROM a']]\n"
                     'for l in N:\n'
                     '    l.append(X)\n'
                     'def run(cur):\n'
                     '    for q in N[0]:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_nonlocal': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 'def f():\n'
                 '    z = []\n'
                 '    def g():\n'
                 '        nonlocal z\n'
                 '        z.append(X)\n'
                 '    g()\n'
                 '    QL.extend(z)\n'
                 'f()\n'
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_operator_iadd': 'from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      'import operator\n'
                      'operator.iadd(QL, imported)\n'
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_operator_setitem': 'from c import imported, X\n'
                         "QL = ['DELETE FROM a']\n"
                         'import operator\n'
                         'operator.setitem(QL, 0, X)\n'
                         'def run(cur):\n'
                         '    for q in QL:\n'
                         '        cur.execute(q)\n'
                         'def own(cur):\n'
                         "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_or_alias': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 'R = QL or []\n'
                 'R.append(X)\n'
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_param': 'from c import imported, X\n'
              "QL = ['DELETE FROM a']\n"
              'def add(l):\n'
              '    l.append(X)\n'
              'add(QL)\n'
              'def run(cur):\n'
              '    for q in QL:\n'
              '        cur.execute(q)\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_param_kw': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 'def add(l):\n'
                 '    l.append(X)\n'
                 'add(l=QL)\n'
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_partial': 'from c import imported, X\n'
                "QL = ['DELETE FROM a']\n"
                'import functools\n'
                'f = functools.partial(QL.append, X)\n'
                'f()\n'
                'def run(cur):\n'
                '    for q in QL:\n'
                '        cur.execute(q)\n'
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_rebind_after': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'QL = [X]\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_rebind_tuple': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'QL, Z = [X], 1\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_reduce': 'from c import imported, X\n'
               "QL = ['DELETE FROM a']\n"
               'import functools\n'
               'functools.reduce(lambda a, b: a.append(b), imported, QL)\n'
               'def run(cur):\n'
               '    for q in QL:\n'
               '        cur.execute(q)\n'
               'def own(cur):\n'
               "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_ret_container': 'from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      'def get():\n'
                      '    return QL\n'
                      'get().append(X)\n'
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_ret_container2': 'from c import imported, X\n'
                       "QL = ['DELETE FROM a']\n"
                       'def get():\n'
                       '    return QL\n'
                       'R = get()\n'
                       'R.append(X)\n'
                       'def run(cur):\n'
                       '    for q in QL:\n'
                       '        cur.execute(q)\n'
                       'def own(cur):\n'
                       "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_self_container': 'from c import imported, X\n'
                       "QL = ['DELETE FROM a']\n"
                       'class H:\n'
                       '    def __init__(self):\n'
                       "        self.q = ['DELETE FROM a']\n"
                       '    def add(self):\n'
                       '        self.q.append(X)\n'
                       '    def go(self, cur):\n'
                       '        for q in self.q:\n'
                       '            cur.execute(q)\n'
                       'h = H()\n'
                       'h.add()\n'
                       'def run(cur):\n'
                       '    h.go(cur)\n'
                       'def own(cur):\n'
                       "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_self_container_alias': 'from c import imported, X\n'
                             "QL = ['DELETE FROM a']\n"
                             'class H:\n'
                             '    def __init__(self):\n'
                             "        self.q = ['DELETE FROM a']\n"
                             '    def go(self, cur):\n'
                             '        r = self.q\n'
                             '        r.append(X)\n'
                             '        for q in self.q:\n'
                             '            cur.execute(q)\n'
                             'h = H()\n'
                             'def run(cur):\n'
                             '    h.go(cur)\n'
                             'def own(cur):\n'
                             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_setattr_call': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     "setattr(__import__('sys').modules[__name__], 'QL', [X])\n"
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_setitem_via_slice_del': 'from c import imported, X\n'
                              "QL = ['DELETE FROM a']\n"
                              'del QL[:]\n'
                              'QL.append(X)\n'
                              'def run(cur):\n'
                              '    for q in QL:\n'
                              '        cur.execute(q)\n'
                              'def own(cur):\n'
                              "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_slice_assign': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'QL[0:1] = imported\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_slice_assign2': 'from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      'QL[:] = X\n'
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_slice_copy': 'from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   'L2 = QL[:]\n'
                   'L2.append(X)\n'
                   'def run(cur):\n'
                   '    for q in L2:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_sorted_copy': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    'L2 = sorted(QL)\n'
                    'L2.append(X)\n'
                    'def run(cur):\n'
                    '    for q in L2:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_tuple_alias': 'from c import imported, X\n'
                    "QL = ['DELETE FROM a']\n"
                    'T = (QL,)\n'
                    'T[0].append(X)\n'
                    'def run(cur):\n'
                    '    for q in QL:\n'
                    '        cur.execute(q)\n'
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_vars_obj': 'from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 'import types\n'
                 'ns = types.SimpleNamespace(q=QL)\n'
                 'ns.q.append(X)\n'
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_while_mutate': 'from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'while len(QL) < 3:\n'
                     '    QL.append(X)\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_with_as': 'from c import imported, X\n'
                "QL = ['DELETE FROM a']\n"
                'import contextlib\n'
                'with contextlib.nullcontext(QL) as R:\n'
                '    R.append(X)\n'
                'def run(cur):\n'
                '    for q in QL:\n'
                '        cur.execute(q)\n'
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r23_yield_container': 'from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        'def get():\n'
                        '    yield QL\n'
                        'for R in get():\n'
                        '    R.append(X)\n'
                        'def run(cur):\n'
                        '    for q in QL:\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g1': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           "globals()['QL'].append(X)\n"
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g10': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import sys\n'
            'sys.modules[__name__].QL.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g11': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "globals().setdefault('QL', [X]).append(X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g12': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            '[*globals().values()][0].append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g13': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'for v in globals().values():\n'
            '    if isinstance(v, list):\n'
            '        v.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g14': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "next(v for k, v in globals().items() if k == 'QL').append(X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g15': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "globals().pop('QL').append(X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g16': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "x = globals()['QL']\n"
            'x.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g17': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "globals().__getitem__('QL').append(X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g18': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "__builtins__.__dict__['globals']()['QL'].append(X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g2': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           "globals()['QL'].extend(imported)\n"
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g3': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           "vars()['QL'].append(X)\n"
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g4': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           "globals().get('QL').append(X)\n"
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g5': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           "globals()['QL'] += imported\n"
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g6': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           "globals()['QL'][0] = X\n"
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g7': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'def f():\n'
           "    locals()['QL'].append(X)\n"
           'f()\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g8': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'globals().update(QL=[X])\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r24_g9': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           "globals()['QL'] = [X]\n"
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r1': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'if X:\n'
           '    QL = imported\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r10': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'try:\n'
            '    pass\n'
            'except Exception as QL:\n'
            '    pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r11': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'match X:\n'
            '    case QL:\n'
            '        pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r12': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'class QL:\n'
            '    pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r13': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'from c import QL\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r14': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL = [*QL, *imported]\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r15': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL = QL + imported\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r16': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL = sorted(imported)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r17': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL = QL.copy()\n'
            'QL.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r18': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL = list(QL)\n'
            'QL.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r19': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'def f(QL):\n'
            '    QL.append(X)\n'
            'f(QL)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r2': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'try:\n'
           '    QL = imported\n'
           'except Exception:\n'
           '    pass\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r21': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'def f():\n'
            '    QL.append(X)\n'
            'f()\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r22': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'class K:\n'
            '    QL.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r23': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'class K:\n'
            '    q = QL\n'
            'K.q.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r24': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'class K:\n'
            '    q = QL\n'
            '    q.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r25': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'class K:\n'
            '    def m(self):\n'
            '        QL.append(X)\n'
            'K().m()\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r26': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'def f():\n'
            '    global QL\n'
            '    QL.append(X)\n'
            'f()\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r27': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            '[QL.append(X) for _ in range(1)]\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r28': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            '(lambda: QL.append(X))()\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r29': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL.append(X) if X else None\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r3': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'for QL in imported:\n'
           '    pass\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r30': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import atexit\n'
            'atexit.register(QL.append, X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r31': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import threading\n'
            'threading.Thread(target=QL.append, args=(X,)).start()\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r32': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'T = [QL.append]\n'
            'T[0](X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r33': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "T = {'f': QL.append}\n"
            "T['f'](X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r34': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'def deco(f):\n'
            '    QL.append(X)\n'
            '    return f\n'
            '@deco\n'
            'def g():\n'
            '    pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r35': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            '@QL.append\n'
            'def g():\n'
            '    pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r36': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'class M(type):\n'
            '    def __new__(m, n, b, d):\n'
            '        QL.append(X)\n'
            '        return super().__new__(m, n, b, d)\n'
            'class K(metaclass=M):\n'
            '    pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r37': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL.extend(x for x in imported)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r38': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL.extend(map(str, imported))\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r39': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL.append(X); QL.extend([])\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r4': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'with X as QL:\n'
           '    pass\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r40': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL += (X,)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r41': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL[len(QL):] = imported\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r43': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'type(QL).append(QL, X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r44': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL.__class__.append(QL, X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r45': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "getattr(QL, 'ap' + 'pend')(X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r46': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "QL.__getattribute__('append')(X)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r47': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            "m = 'append'\n"
            'getattr(QL, m)(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r48': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'from operator import methodcaller\n'
            "methodcaller('append', X)(QL)\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r49': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import builtins\n'
            'builtins.list.append(QL, X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r5': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'import QL\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r50': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'iter_ = iter(QL)\n'
            'QL.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r51': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'id_ = id(QL)\n'
            'import ctypes\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r52': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import gc\n'
            'for o in gc.get_objects():\n'
            '    pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r53': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import gc\n'
            'for o in gc.get_referrers(QL):\n'
            '    pass\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r54': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import weakref\n'
            'r = weakref.proxy(QL)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r55': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'import copy\n'
            'R = copy.deepcopy(QL)\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in R:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r59': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'R = reversed(QL)\n'
            'QL.append(X)\n'
            'def run(cur):\n'
            '    for q in R:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r6': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'def QL():\n'
           '    pass\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r60': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'R = QL.__iter__()\n'
            'QL.append(X)\n'
            'def run(cur):\n'
            '    for q in R:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r7': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           '(QL := imported)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r8': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'del QL\n'
           'QL = imported\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r25_r9': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'QL: list = imported\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k1': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'Step.sql = X\n'
           'def run(cur):\n'
           '    Step().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k10': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    class Sub(Step):\n'
            '        sql = X\n'
            '    Sub().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k11': 'from c import imported, X\n'
            'def deco(c):\n'
            '    c.sql = X\n'
            '    return c\n'
            '@deco\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k12': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def deco(c):\n'
            '    c.sql = X\n'
            '    return c\n'
            'Step = deco(Step)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k13': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    sql = X\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k14': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    if X:\n'
            '        sql = imported\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k15': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    sql += imported\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k16': 'from c import imported, X\n'
            'class Step:\n'
            "    sql: str = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k18': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def __init_subclass__(cls, **kw):\n'
            '        cls.sql = X\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'class S2(Step):\n'
            '    pass\n'
            'def run(cur):\n'
            '    S2().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k19': 'from c import imported, X\n'
            'from enum import Enum\n'
            'class Step(Enum):\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step.sql.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k2': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           "Step.sql = 'DELETE FROM b'\n"
           'def run(cur):\n'
           '    Step().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k20': 'from c import imported, X\n'
            'from typing import Protocol\n'
            'class Step(Protocol):\n'
            "    sql: str = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'class Impl(Step):\n'
            '    sql = X\n'
            'def run(cur):\n'
            '    Impl().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k21': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'class Other:\n'
            '    def run(self, cur):\n'
            '        Step.sql = X\n'
            '        Step().go(cur)\n'
            'def run(cur):\n'
            '    Other().run(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k22': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(type(self).sql)\n'
            'class S2(Step):\n'
            '    sql = X\n'
            'def run(cur):\n'
            '    S2().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k23': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.__class__.sql)\n'
            'def run(cur):\n'
            '    s = Step()\n'
            "    s.__class__ = type('S', (Step,), {'sql': X})\n"
            '    s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k24': 'from c import imported, X\n'
            'class Base:\n'
            "    sql = 'DELETE FROM a'\n"
            'class Step(Base):\n'
            '    def go(self, cur):\n'
            '        cur.execute(super().sql)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k25': 'from c import imported, X\n'
            'class Mixin:\n'
            "    sql = 'DELETE FROM a'\n"
            'class Step(Mixin):\n'
            '    sql = X\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k26': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step(sql=X).go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k27': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def __init__(self, sql=None):\n'
            '        if sql: self.sql = sql\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step(X).go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k28': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur, o):\n'
            '    Step.go(o, cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k29': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur, o):\n'
            '    s = Step()\n'
            "    s.__setattr__('sql', X)\n"
            '    s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k3': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           "setattr(Step, 'sql', X)\n"
           'def run(cur):\n'
           '    Step().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k30': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur, o):\n'
            '    s = Step()\n'
            "    vars(s)['sql'] = X\n"
            '    s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k31': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    s = Step()\n'
            '    s.sql, z = X, 1\n'
            '    s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k32': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    s = Step()\n'
            '    for s.sql in [X]:\n'
            '        s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k33': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    s = Step()\n'
            '    with X as s.sql:\n'
            '        s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k35': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    s = Step()\n'
            '    s.sql += X\n'
            '    s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k36': 'from c import imported, X\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    s = Step()\n'
            '    s.sql = X\n'
            '    s.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k37': 'from c import imported, X\n'
            'class Step:\n'
            '    class Inner:\n'
            "        sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.Inner.sql)\n'
            'def run(cur):\n'
            '    Step.Inner.sql = X\n'
            '    Step().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k39': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            'class B:\n'
            '    def go(self, cur):\n'
            '        cur.execute(A.sql)\n'
            'A.sql = X\n'
            'def run(cur):\n'
            '    B().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k4': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'def run(cur):\n'
           '    s = Step()\n'
           '    s.sql = X\n'
           '    s.go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k42': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            'B = A\n'
            'B.sql = X\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k43': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            'B = A\n'
            'def f(c):\n'
            '    c.sql = X\n'
            'f(B)\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k44': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            'def f(c):\n'
            '    c.sql = X\n'
            'f(A)\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k45': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            'for c in [A]:\n'
            '    c.sql = X\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k46': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "d = {'k': A}\n"
            "d['k'].sql = X\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k47': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    @staticmethod\n'
            '    def s(c):\n'
            '        c.sql = X\n'
            'A.s(A)\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k48': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    @classmethod\n'
            '    def set(cls):\n'
            '        cls.sql = X\n'
            'A.set()\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k49': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def set(self):\n'
            '        type(self).sql = X\n'
            'A().set()\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k5': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'def run(cur):\n'
           '    s = Step()\n'
           "    setattr(s, 'sql', X)\n"
           '    s.go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k50': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def set(self):\n'
            '        self.__class__.sql = X\n'
            'A().set()\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k51': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def set(self):\n'
            '        A.sql = X\n'
            'A().set()\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k52': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            'import sys\n'
            'sys.modules[__name__].A.sql = X\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k53': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            'A.__dict__\n'
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k54': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "A.__setattr__(A, 'sql', X)\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k55': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "type.__setattr__(A, 'sql', X)\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k56': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "A.__dict__.update({'sql': X})\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k57': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "vars(A)['sql'] = X\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k58': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "globals()['A'].sql = X\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k59': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "exec('A.sql = X')\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k6': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'def run(cur):\n'
           '    s = Step()\n'
           "    s.__dict__['sql'] = X\n"
           '    s.go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k60': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            "A = type('A', (), {'sql': X})\n"
            'def run(cur):\n'
            '    cur.execute(A.sql)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k61': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def __getattribute__(self, n):\n'
            '        return X\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k63': 'from c import imported, X\n'
            'class A:\n'
            '    sql = property(lambda s: X)\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k64': 'from c import imported, X\n'
            'class A:\n'
            '    @property\n'
            '    def sql(self):\n'
            '        return X\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k65': 'from c import imported, X\n'
            'class D:\n'
            '    def __get__(self, o, t):\n'
            '        return X\n'
            'class A:\n'
            '    sql = D()\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k66': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'class B(A):\n'
            '    pass\n'
            'def run(cur):\n'
            '    B().go(cur)\n'
            'B.sql = X\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k67': 'from c import imported, X\n'
            'from dataclasses import dataclass\n'
            '@dataclass\n'
            'class A:\n'
            "    sql: str = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A(X).go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k68': 'from c import imported, X\n'
            'from dataclasses import dataclass\n'
            '@dataclass\n'
            'class A:\n'
            "    sql: str = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k69': 'from c import imported, X\n'
            'from typing import NamedTuple\n'
            'class A(NamedTuple):\n'
            "    sql: str = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k7': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'def run(cur):\n'
           '    Step.__dict__\n'
           '    Step().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k70': 'from c import imported, X\n'
            'from typing import TypedDict\n'
            'class A(TypedDict):\n'
            '    sql: str\n'
            'def run(cur):\n'
            "    cur.execute(A(sql=X)['sql'])\n"
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k72': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    a = A()\n'
            '    b = a\n'
            '    b.sql = X\n'
            '    a.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k73': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def mk():\n'
            '    return A()\n'
            'def run(cur):\n'
            '    a = mk()\n'
            '    a.sql = X\n'
            '    a.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k74': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur, objs):\n'
            '    for a in objs:\n'
            '        a.sql = X\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k75': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur, a):\n'
            '    a.sql = X\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k76': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur, a):\n'
            '    a.sql = X\n'
            '    a.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k77': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'x = A()\n'
            'x.sql = X\n'
            'def run(cur):\n'
            '    x.go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k78': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            "    A.go(type('Z', (), {'sql': X})(), cur)\n"
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k8': 'from c import imported, X\n'
           'class Sub:\n'
           '    pass\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'class Sub2(Step):\n'
           '    sql = X\n'
           'def run(cur):\n'
           '    Sub2().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k80': 'from c import imported, X\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A.go(lambda: 0, cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r26_k9': 'from c import imported, X\n'
           'class Step:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           "Sub = type('Sub', (Step,), {'sql': X})\n"
           'def run(cur):\n'
           '    Sub().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q1': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'A = imported\n'
           'def run(cur):\n'
           '    cur.execute(A.sql)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q10': 'from c import imported, X, Other\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def f():\n'
            '    global A\n'
            '    A = Other\n'
            'f()\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q11': 'from c import imported, X, Other\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'class A:\n'
            '    sql = X\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q16': 'from c import imported, X, Other\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    A = Other\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q17': 'from c import imported, X, Other\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    import c as A\n'
            '    A().go(cur)\n'
            '\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q2': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'A = Other\n'
           'def run(cur):\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q3': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'if X:\n'
           '    A = Other\n'
           'def run(cur):\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q4': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'from c import A\n'
           'def run(cur):\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q5': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'def A():\n'
           '    pass\n'
           'def run(cur):\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q6': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           "A = type('A', (), {'sql': X})\n"
           'def run(cur):\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q7': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'def run(cur):\n'
           '    global A\n'
           '    A = Other\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q8': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'def run(cur, A):\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r27_q9': 'from c import imported, X, Other\n'
           'class A:\n'
           "    sql = 'DELETE FROM a'\n"
           '    def go(self, cur):\n'
           '        cur.execute(self.sql)\n'
           'for A in [Other]:\n'
           '    pass\n'
           'def run(cur):\n'
           '    A().go(cur)\n'
           '\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m1': 'from c import imported, X\n'
           'def make():\n'
           "    return ['DELETE FROM a']\n"
           'QL = make()\n'
           'R = QL\n'
           'R.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m10': 'from c import imported, X\n'
            "QL = ['DELETE FROM a'].copy()\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m11': 'from c import imported, X\n'
            'import copy\n'
            "QL = copy.copy(['DELETE FROM a'])\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m12': 'from c import imported, X\n'
            'import copy\n'
            "QL = copy.deepcopy(['DELETE FROM a'])\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m14': 'from c import imported, X\n'
            "QL = ['DELETE FROM a'] + []\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m15': 'from c import imported, X\n'
            "QL = {'DELETE FROM a': 1}.keys()\n"
            'R = QL\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m16': 'from c import imported, X\n'
            "QL = list({'DELETE FROM a': 1})\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m17': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            'QL = D.values()\n'
            "D['z'] = X\n"
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m18': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            'E = D\n'
            "E['z'] = X\n"
            'def run(cur):\n'
            '    for q in D.values():\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m19': 'from c import imported, X\n'
            'def make():\n'
            "    return {'k': 'DELETE FROM a'}\n"
            'D = make()\n'
            'E = D\n'
            "E['z'] = X\n"
            'def run(cur):\n'
            '    for q in D.values():\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m2': 'from c import imported, X\n'
           "QL = ['DELETE FROM a'][:]\n"
           'R = QL\n'
           'R.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m20': 'from c import imported, X\n'
            'from collections import deque\n'
            "QL = deque(['DELETE FROM a'])\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m21': 'from c import imported, X\n'
            'from collections import defaultdict\n'
            'D = defaultdict(list)\n'
            "D['k'].append(X)\n"
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m22': 'from c import imported, X\n'
            'import itertools\n'
            "QL = list(itertools.chain(['DELETE FROM a']))\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m23': 'from c import imported, X\n'
            "QL = [x for x in ['DELETE FROM a']]\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m25': 'from c import imported, X\n'
            'class H:\n'
            '    q = make()\n'
            'def make():\n'
            "    return ['DELETE FROM a']\n"
            'H.q.append(X)\n'
            'def run(cur):\n'
            '    for q in H.q:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m26': 'from c import imported, X\n'
            'def make():\n'
            "    q = ['DELETE FROM a']\n"
            '    return q\n'
            'QL = make()\n'
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m27': 'from c import imported, X\n'
            'def make():\n'
            "    q = ['DELETE FROM a']\n"
            '    q.append(X)\n'
            '    return q\n'
            'QL = make()\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m28': 'from c import imported, X\n'
            'def make(l):\n'
            '    return l\n'
            "QL = make(['DELETE FROM a'])\n"
            'R = QL\n'
            'R.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m29': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = QL or []\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m3': 'from c import imported, X\n'
           "QL = (lambda: ['DELETE FROM a'])()\n"
           'R = QL\n'
           'R.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m30': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = (QL)\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m31': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = (QL, 1)[0]\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m32': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = [QL][0]\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m33': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = {0: QL}[0]\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m34': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = next(iter([QL]))\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m35': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = (lambda l: l)(QL)\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m36': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = max([QL], key=len)\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m37': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = QL if X else QL\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m38': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = X or QL\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m39': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = QL.__iter__\n'
            'QL2\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m4': 'from c import imported, X\n'
           "QL = ['DELETE FROM a'] if X else ['DELETE FROM b']\n"
           'R = QL\n'
           'R.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m40': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            '(QL2 := QL).append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m42': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'for QL2 in (QL,):\n'
            '    QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m43': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'with open(X) as f:\n'
            '    pass\n'
            'QL2, = (QL,)\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m44': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2, QL3 = QL, QL\n'
            'QL2.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m45': 'from c import imported, X\n'
            "QL = ['DELETE FROM a']\n"
            'QL2 = QL3 = QL\n'
            'QL3.append(X)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m5': 'from c import imported, X\n'
           'def make():\n'
           "    return ['DELETE FROM a']\n"
           'QL = make()\n'
           'def f(l):\n'
           '    l.append(X)\n'
           'f(QL)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m6': 'from c import imported, X\n'
           'def make():\n'
           "    return ['DELETE FROM a']\n"
           'QL = make()\n'
           'QL.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m7': 'from c import imported, X\n'
           'def make():\n'
           "    return ['DELETE FROM a']\n"
           'QL = make()\n'
           'class K:\n'
           '    q = QL\n'
           'K.q.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m8': 'from c import imported, X\n'
           "QL = [*['DELETE FROM a']]\n"
           'R = QL\n'
           'R.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r28_m9': 'from c import imported, X\n'
           "QL = ['DELETE FROM a']\n"
           'R = QL\n'
           'R.append(X)\n'
           'def run(cur):\n'
           '    for q in QL:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t1': 'from c import imported, X\n'
           "T = (['DELETE FROM a'],)\n"
           'L = T[0]\n'
           'L.append(X)\n'
           'def run(cur):\n'
           '    for q in T[0]:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t10': 'from c import imported, X\n'
            "d = dict(q=['DELETE FROM a'])\n"
            "d['q'].append(X)\n"
            'def run(cur):\n'
            "    for q in d['q']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t11': 'from c import imported, X\n'
            "d = dict(q=('DELETE FROM a',))\n"
            "d['q'] = d['q'] + (X,)\n"
            'def run(cur):\n'
            "    for q in d['q']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t2': 'from c import imported, X\n'
           "T = (['DELETE FROM a'],)\n"
           'T[0].append(X)\n'
           'def run(cur):\n'
           '    for q in T[0]:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t3': 'from c import imported, X\n'
           "T = (['DELETE FROM a'],)\n"
           'for l in T:\n'
           '    l.append(X)\n'
           'def run(cur):\n'
           '    for q in T[0]:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t4': 'from c import imported, X\n'
           "T = (['DELETE FROM a'],)\n"
           'def f(l):\n'
           '    l.append(X)\n'
           'f(T[0])\n'
           'def run(cur):\n'
           '    for q in T[0]:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t5': 'from c import imported, X\n'
           "T = [['DELETE FROM a']]\n"
           'L = T[0]\n'
           'L.append(X)\n'
           'def run(cur):\n'
           '    for q in T[0]:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t6': 'from c import imported, X\n'
           "L0 = ['DELETE FROM a']\n"
           'T = (L0,)\n'
           'L0.append(X)\n'
           'def run(cur):\n'
           '    for q in T[0]:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t7': 'from c import imported, X\n'
           "L0 = ['DELETE FROM a']\n"
           'T = (L0,)\n'
           'L0.append(X)\n'
           'def run(cur):\n'
           '    for q in T[0]:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t8': 'from c import imported, X\n'
           'from dataclasses import dataclass, field\n'
           '@dataclass\n'
           'class K:\n'
           "    q: list = field(default_factory=lambda: ['DELETE FROM a'])\n"
           'k = K()\n'
           'k.q.append(X)\n'
           'def run(cur):\n'
           '    for q in k.q:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r29_t9': 'from c import imported, X\n'
           'import types\n'
           "ns = types.SimpleNamespace(q=['DELETE FROM a'])\n"
           'ns.q.append(X)\n'
           'def run(cur):\n'
           '    for q in ns.q:\n'
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s1': "V='DELETE'\n"
           "F='FROM'\n"
           'def run(cur):\n'
           "    cur.execute(f'{V} {F} hidden')\n"
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s13': 'def run(cur):\n'
            "    v = 'DELETE'\n"
            "    cur.execute(f'{v} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s14': 'def run(cur):\n'
            "    v, f = 'DELETE', 'FROM'\n"
            "    cur.execute(f'{v} {f} hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s15': "VERBS = ['DELETE', 'INSERT']\n"
            'def run(cur):\n'
            '    for v in VERBS:\n'
            "        cur.execute(f'{v} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s16': "VERBS = {'d': 'DELETE'}\n"
            'def run(cur):\n'
            '    cur.execute(f"{VERBS[\'d\']} FROM hidden")\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s17': 'class K:\n'
            "    v = 'DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'{K.v} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s18': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'''\n"
            '    {V}\n'
            "    FROM hidden''')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s19': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'/* c */ {V} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s2': "V='DELETE'\n"
           "F='FROM'\n"
           'def run(cur):\n'
           "    cur.execute(' '.join([V, F, 'hidden']))\n"
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s20': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'-- c\\n{V} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s21': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'SELECT 1; {V} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s22': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'SELECT 1;{V}\\nFROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s25': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'BEGIN; {V} FROM hidden; COMMIT')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s28': "V='INSERT'\n"
            'def run(cur):\n'
            "    cur.execute(f'{V}\\nINTO hidden VALUES (1)')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s29': "V='UPDATE'\n"
            'def run(cur):\n'
            "    cur.execute(f'{V} hidden SET a=1')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s3': "V='DELETE'\n"
           "F='FROM'\n"
           'def run(cur):\n'
           "    cur.execute('%s %s hidden' % (V, F))\n"
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s30': "V='TRUNCATE'\ndef run(cur):\n    cur.execute(f'{V} hidden')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s31': "V='COPY'\n"
            'def run(cur):\n'
            "    cur.execute(f'{V} hidden FROM stdin')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s4': "V='DELETE'\n"
           "F='FROM'\n"
           'def run(cur):\n'
           "    cur.execute('{} {} hidden'.format(V, F))\n"
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s5': "V='DELETE'\n"
           "F='FROM'\n"
           'def run(cur):\n'
           "    cur.execute(V + ' ' + F + ' hidden')\n"
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s6': "V='DELETE FROM'\ndef run(cur):\n    cur.execute(V + ' hidden')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s7': "V='DELETE FROM'\ndef run(cur):\n    cur.execute(f'{V} hidden')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s8': "V='DELETE FROM'\n"
           'def run(cur):\n'
           "    cur.execute(V + ' ' + 'hidden')\n"
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s9': "V='DELETE'\ndef run(cur):\n    cur.execute(V + ' FROM hidden')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r31_f8': 'Q2 = "\'; REFRESH /*x*/ MATERIALIZED VIEW hidden"\n'
           'def run(cur, v):\n'
           '    cur.execute(v + Q2)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r31_f9': 'Q2 = "\'; MERGE /*x*/ INTO hidden USING s ON true WHEN MATCHED THEN DELETE"\n'
           'def run(cur, v):\n'
           '    cur.execute(v + Q2)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g1': 'def run(cur):\n    cur.execute("UPDATE %s SET a = \'--\'")\ndef own(cur):\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
 'r32_g10': 'def run(cur):\n'
            "    cur.execute('UPDATE a /* x */ SET b = 1; UPDATE %s SET c = 2')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g11': "def run(cur):\n    cur.execute('TRUNCATE a -- x\\n, %s')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g12': "def run(cur):\n    cur.execute('TRUNCATE a /* x */, %s')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g13': "def run(cur):\n    cur.execute('TRUNCATE /* x */ a, %s')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g14': 'def run(cur):\n'
            "    cur.execute('COPY a FROM stdin; COPY %s FROM stdin -- x')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g2': "def run(cur):\n    cur.execute('UPDATE %s SET a = 1 /* c */')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g3': 'def run(cur):\n    cur.execute("UPDATE %s SET a = \'/*\' ")\ndef own(cur):\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
 'r32_g4': 'def run(cur):\n    cur.execute("COPY %s FROM \'--\'")\ndef own(cur):\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
 'r32_g5': "def run(cur):\n    cur.execute('TRUNCATE %s -- c')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g6': 'def run(cur):\n'
           '    cur.execute("INSERT INTO %s VALUES (\'--\')")\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g7': 'def run(cur):\n'
           '    cur.execute("DELETE FROM %s WHERE a = \'--\'")\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r32_g8': 'def run(cur):\n    cur.execute("UPDATE {t} SET a = \'--\'")\ndef own(cur):\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
 'r32_g9': 'def run(cur):\n'
           '    cur.execute("UPDATE a SET b = 1; UPDATE %s SET c = \'--\'")\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d1': 'from c import imported, X\n'
           'D = {}\n'
           "D.setdefault('k', []).append(X)\n"
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d10': 'from c import imported, X\n'
            'D = {}\n'
            "D.update({'k': X})\n"
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d11': 'from c import imported, X\n'
            'D = {}\n'
            'D.update(k=X)\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d12': 'from c import imported, X\n'
            'D = dict(k=X)\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d13': 'from c import imported, X\n'
            'D = {**imported}\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d14': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a', **imported}\n"
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d15': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            'D |= imported\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d16': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            'D.update(imported)\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d17': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            "D = {**D, 'k': X}\n"
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d18': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            'for k in imported:\n'
            '    D[k] = X\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d19': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            'D = dict(D, k=X)\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d2': 'from c import imported, X\n'
           'D = {}\n'
           "D['k'] = []\n"
           "D['k'].append(X)\n"
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d20': 'from c import imported, X\n'
            "D = {'k': 'DELETE FROM a'}\n"
            'D = {k: v for k, v in imported.items()}\n'
            'def run(cur):\n'
            "    for q in D['k']:\n"
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d3': 'from c import imported, X\n'
           'D = {}\n'
           "D['k'] = ['DELETE FROM a']\n"
           "D['k'].append(X)\n"
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d4': 'from c import imported, X\n'
           'D = {}\n'
           "D['k'] = []\n"
           "D.get('k').append(X)\n"
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d5': 'from c import imported, X\n'
           "D = {'k': []}\n"
           "D['k'].append(X)\n"
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d6': 'from c import imported, X\n'
           'D = {}\n'
           "D['k'] = ()\n"
           "D['k'] += (X,)\n"
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d7': 'from c import imported, X\n'
           'D = {}\n'
           "l = D.setdefault('k', [])\n"
           'l.append(X)\n'
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d8': 'from c import imported, X\n'
           'D = {}\n'
           "D['k'] = ['DELETE FROM a']\n"
           'for v in D.values():\n'
           '    v.append(X)\n'
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r33_d9': 'from c import imported, X\n'
           "D = {'k': 'DELETE FROM a'}\n"
           "D['k'] += X\n"
           'def run(cur):\n'
           "    for q in D['k']:\n"
           '        cur.execute(q)\n'
           'def own(cur):\n'
           "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r34_rcv1': 'from c import imported, X\n'
             "QL = ['DELETE FROM a']\n"
             'QL.__init__(imported)\n'
             'def run(cur):\n'
             '    for q in QL:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n"}

HIDDEN = {'r30_s23': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'WITH x AS (SELECT 1) {V} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s24': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'EXPLAIN ANALYZE {V} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s26': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'DO $$ BEGIN {V} FROM hidden; END $$')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s27': "V='DELETE'\n"
            'def run(cur):\n'
            "    cur.execute(f'PREPARE p AS {V} FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s32': "V='DEL'\n"
            'def run(cur):\n'
            "    cur.execute(f'{V}ETE FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s33': "V='DEL'\n"
            'def run(cur):\n'
            "    cur.execute(V + 'ETE FROM hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s34': 'def run(cur):\n'
            "    cur.execute('de' + 'lete'.upper() + ' from hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s35': 'def run(cur):\n'
            "    cur.execute('DELETE   FROM'.replace('  ', ' ') + ' hidden')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r30_s37': 'def run(cur):\n'
            "    cur.execute('DELETE FROM xx'.replace('xx', 'hidden'))\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n"}

SETS = {'r19_s_a': ('def run(cur):\n'
             '    cur.execute("SELECT \'--\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_a1': ('def run(cur):\n'
              '    cur.execute("SELECT E\'\\\\\'\' ; DELETE FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_b': ('def run(cur):\n'
             '    cur.execute("SELECT E\'\\\\\\\\\'--\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_b1': ('def run(cur):\n'
              '    cur.execute("SELECT E\'\\\\\\\\\'\' ; DELETE FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_c': ('def run(cur):\n'
             '    cur.execute("SELECT E\'it\'\'s --\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_c1': ('def run(cur):\n'
              '    cur.execute("SELECT e\'\\\\\'--\' ; DELETE FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_d': ('def run(cur):\n'
             "    cur.execute('SELECT $a$ -- $b$ x $b$ $a$; DELETE FROM hidden')\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_d1': ('def run(cur):\n'
              '    cur.execute("SELECT U&\'\\\\0027--\'; DELETE FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_e': ('def run(cur):\n'
             '    cur.execute(\'SELECT "a--b"; DELETE FROM hidden\')\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_e1': ('def run(cur):\n'
              "    cur.execute('SELECT 1 -- x\\rDELETE FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_f': ('def run(cur):\n'
             '    cur.execute("SELECT \'/*\'; DELETE FROM hidden; SELECT \'*/\'")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_f1': ('def run(cur):\n'
              "    cur.execute('SELECT $1; DELETE FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_g': ('def run(cur):\n'
             '    cur.execute("SELECT 1 /* \' */; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_g1': ('def run(cur):\n'
              "    cur.execute('SELECT $1$2; DELETE FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_h': ('def run(cur):\n'
             '    cur.execute("SELECT 1 -- \'\\n; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_h1': ('def run(cur):\n'
              '    cur.execute("SELECT \'$$\'; DELETE FROM hidden; SELECT \'$$\'")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_i': ('def run(cur):\n'
             "    cur.execute('SELECT 1 -- $$\\n; DELETE FROM hidden')\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_i1': ('def run(cur):\n'
              '    cur.execute("SELECT $$ \' $$, \' ; DELETE FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r19_s_j': ('def run(cur):\n'
             '    cur.execute("SELECT \'\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_k': ('def run(cur):\n'
             '    cur.execute("SELECT E\'\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_l': ('def run(cur):\n'
             '    cur.execute("SELECT E\'\\\\\\\\\\\\\\\\\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_m': ('def run(cur):\n'
             '    cur.execute("SELECT \'\\\\\\\\\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_n': ('def run(cur):\n'
             '    cur.execute("SELECT x\'--\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_p': ('def run(cur):\n'
             "    cur.execute('SELECT 1;--\\nDELETE FROM hidden')\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_q': ('def run(cur):\n'
             "    cur.execute('SELECT a$b$ ; DELETE FROM hidden')\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_r': ('def run(cur):\n'
             "    cur.execute('SELECT a$b$ -- \\n; DELETE FROM hidden; SELECT $b$')\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_u': ('def run(cur):\n'
             "    cur.execute('SELECT 1 /* /* */ */ ; DELETE FROM hidden')\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_v': ('def run(cur):\n'
             '    cur.execute("SELECT \'/*\' , \'*/\'; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_w': ('def run(cur):\n'
             '    cur.execute("SELECT \'--\' /* \' */ ; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_x': ('def run(cur):\n'
             '    cur.execute(\'SELECT "--" "\\\'" ; DELETE FROM hidden\')\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_y': ('def run(cur):\n'
             "    cur.execute('SELECT $$--$$; DELETE FROM hidden')\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r19_s_z': ('def run(cur):\n'
             '    cur.execute("SELECT $x$ \' $x$; DELETE FROM hidden")\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r20_u0_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; DELETE FROM /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; DELETE FROM /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; DELETE FROM /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; DELETE FROM /*x*/ hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; DELETE FROM /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; DELETE FROM /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; DELETE FROM /*x*/ hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u0_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; DELETE /*x*/ FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; DELETE /*x*/ FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; DELETE /*x*/ FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; DELETE /*x*/ FROM hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; DELETE /*x*/ FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; DELETE /*x*/ FROM hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; DELETE /*x*/ FROM hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u1_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; DELETE FROM hidden /*x*/")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; DELETE FROM hidden /*x*/")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; DELETE FROM hidden /*x*/')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; DELETE FROM hidden /*x*/")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; DELETE FROM hidden /*x*/')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; DELETE FROM hidden /*x*/')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; DELETE FROM hidden /*x*/\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; DELETE FROM hidden /*x*/")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; DELETE FROM hidden /*x*/")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; DELETE FROM hidden /*x*/\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; DELETE FROM hidden /*x*/')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; DELETE FROM hidden /*x*/')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u2_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; DELETE FROM hidden /*x*/')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; INSERT /*x*/ INTO hidden VALUES (1)")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; INSERT /*x*/ INTO hidden VALUES (1)")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; INSERT /*x*/ INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; INSERT /*x*/ INTO hidden VALUES (1)")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; INSERT /*x*/ INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; INSERT /*x*/ INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; INSERT /*x*/ INTO hidden VALUES (1)\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; INSERT /*x*/ INTO hidden VALUES (1)")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; INSERT /*x*/ INTO hidden VALUES (1)")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; INSERT /*x*/ INTO hidden VALUES (1)\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; INSERT /*x*/ INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; INSERT /*x*/ INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u3_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; INSERT /*x*/ INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; UPDATE /*x*/ hidden SET a=1")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; UPDATE /*x*/ hidden SET a=1")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; UPDATE /*x*/ hidden SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; UPDATE /*x*/ hidden SET a=1")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; UPDATE /*x*/ hidden SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; UPDATE /*x*/ hidden SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; UPDATE /*x*/ hidden SET a=1\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; UPDATE /*x*/ hidden SET a=1")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; UPDATE /*x*/ hidden SET a=1")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; UPDATE /*x*/ hidden SET a=1\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; UPDATE /*x*/ hidden SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; UPDATE /*x*/ hidden SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u4_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; UPDATE /*x*/ hidden SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; TRUNCATE /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; TRUNCATE /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; TRUNCATE /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; TRUNCATE /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; TRUNCATE /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; TRUNCATE /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; TRUNCATE /*x*/ hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; TRUNCATE /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; TRUNCATE /*x*/ hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; TRUNCATE /*x*/ hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; TRUNCATE /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; TRUNCATE /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u5_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; TRUNCATE /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; COPY /*x*/ hidden FROM stdin")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; COPY /*x*/ hidden FROM stdin")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; COPY /*x*/ hidden FROM stdin')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; COPY /*x*/ hidden FROM stdin")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; COPY /*x*/ hidden FROM stdin')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; COPY /*x*/ hidden FROM stdin')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; COPY /*x*/ hidden FROM stdin\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; COPY /*x*/ hidden FROM stdin")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; COPY /*x*/ hidden FROM stdin")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; COPY /*x*/ hidden FROM stdin\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; COPY /*x*/ hidden FROM stdin')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; COPY /*x*/ hidden FROM stdin')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u6_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; COPY /*x*/ hidden FROM stdin')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_a': ('def run(cur):\n'
              '    cur.execute("SELECT $é$ \' $é$; DELETE FROM --x\\n hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_b': ('def run(cur):\n'
              '    cur.execute("SELECT a$b$ \' ; DELETE FROM --x\\n hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_c': ('def run(cur):\n'
              "    cur.execute('SELECT 1; DELETE FROM --x\\n hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_d': ('def run(cur):\n'
              '    cur.execute("SELECT \'x\'; DELETE FROM --x\\n hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_e': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ -- $é$; DELETE FROM --x\\n hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_f': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ -- $b$\\n; DELETE FROM --x\\n hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 /* "*/; DELETE FROM --x\\n hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'\\\\\'; DELETE FROM --x\\n hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_i': ('def run(cur):\n'
              '    cur.execute("SELECT E\'x\\\\\'; DELETE FROM --x\\n hidden")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_j': ('def run(cur):\n'
              '    cur.execute(\'SELECT "; DELETE FROM --x\\n hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_k': ('def run(cur):\n'
              "    cur.execute('SELECT $; DELETE FROM --x\\n hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_l': ('def run(cur):\n'
              "    cur.execute('SELECT $tag$ $; DELETE FROM --x\\n hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r20_u7_m': ('def run(cur):\n'
              "    cur.execute('SELECT $é$; DELETE FROM --x\\n hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_a': ('def run(cur):\n'
              "    cur.execute('DO $$ BEGIN DELETE /*x*/ FROM hidden; END $$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_b': ('def run(cur):\n'
              "    cur.execute('DO $x$ BEGIN DELETE /*x*/ FROM hidden; END $x$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_c': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ ; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_d': ('def run(cur):\n'
              "    cur.execute('SELECT a$$ ; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_e': ('def run(cur):\n'
              "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN DELETE /*x*/ FROM hidden; END $$ LANGUAGE plpgsql')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_f': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ x $é$; DELETE /*x*/ FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 AS "a""b"; DELETE /*x*/ FROM hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'$$\'; DELETE /*x*/ FROM hidden; SELECT \'$$\'")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v0_i': ('def run(cur):\n'
              '    cur.execute("DO $$ BEGIN EXECUTE \'DELETE /*x*/ FROM hidden\'; END $$")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_a': ('def run(cur):\n'
              "    cur.execute('DO $$ BEGIN DELETE FROM /*x*/ hidden; END $$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_b': ('def run(cur):\n'
              "    cur.execute('DO $x$ BEGIN DELETE FROM /*x*/ hidden; END $x$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_c': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ ; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_d': ('def run(cur):\n'
              "    cur.execute('SELECT a$$ ; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_e': ('def run(cur):\n'
              "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN DELETE FROM /*x*/ hidden; END $$ LANGUAGE plpgsql')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_f': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ x $é$; DELETE FROM /*x*/ hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 AS "a""b"; DELETE FROM /*x*/ hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'$$\'; DELETE FROM /*x*/ hidden; SELECT \'$$\'")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v1_i': ('def run(cur):\n'
              '    cur.execute("DO $$ BEGIN EXECUTE \'DELETE FROM /*x*/ hidden\'; END $$")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_a': ('def run(cur):\n'
              "    cur.execute('DO $$ BEGIN INSERT --x\\n INTO hidden VALUES (1); END $$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_b': ('def run(cur):\n'
              "    cur.execute('DO $x$ BEGIN INSERT --x\\n INTO hidden VALUES (1); END $x$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_c': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ ; INSERT --x\\n INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_d': ('def run(cur):\n'
              "    cur.execute('SELECT a$$ ; INSERT --x\\n INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_e': ('def run(cur):\n'
              "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN INSERT --x\\n INTO hidden VALUES (1); END $$ LANGUAGE "
              "plpgsql')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_f': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ x $é$; INSERT --x\\n INTO hidden VALUES (1)')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 AS "a""b"; INSERT --x\\n INTO hidden VALUES (1)\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'$$\'; INSERT --x\\n INTO hidden VALUES (1); SELECT \'$$\'")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v2_i': ('def run(cur):\n'
              '    cur.execute("DO $$ BEGIN EXECUTE \'INSERT --x\\n INTO hidden VALUES (1)\'; END $$")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_a': ('def run(cur):\n'
              "    cur.execute('DO $$ BEGIN UPDATE hidden /*x*/ SET a=1; END $$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_b': ('def run(cur):\n'
              "    cur.execute('DO $x$ BEGIN UPDATE hidden /*x*/ SET a=1; END $x$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_c': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ ; UPDATE hidden /*x*/ SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_d': ('def run(cur):\n'
              "    cur.execute('SELECT a$$ ; UPDATE hidden /*x*/ SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_e': ('def run(cur):\n'
              "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN UPDATE hidden /*x*/ SET a=1; END $$ LANGUAGE plpgsql')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_f': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ x $é$; UPDATE hidden /*x*/ SET a=1')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 AS "a""b"; UPDATE hidden /*x*/ SET a=1\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'$$\'; UPDATE hidden /*x*/ SET a=1; SELECT \'$$\'")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v3_i': ('def run(cur):\n'
              '    cur.execute("DO $$ BEGIN EXECUTE \'UPDATE hidden /*x*/ SET a=1\'; END $$")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_a': ('def run(cur):\n'
              "    cur.execute('DO $$ BEGIN DELETE FROM hidden; END $$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_b': ('def run(cur):\n'
              "    cur.execute('DO $x$ BEGIN DELETE FROM hidden; END $x$')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_c': ('def run(cur):\n'
              "    cur.execute('SELECT a$b$ ; DELETE FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_d': ('def run(cur):\n'
              "    cur.execute('SELECT a$$ ; DELETE FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_e': ('def run(cur):\n'
              "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN DELETE FROM hidden; END $$ LANGUAGE plpgsql')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_f': ('def run(cur):\n'
              "    cur.execute('SELECT $é$ x $é$; DELETE FROM hidden')\n"
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_g': ('def run(cur):\n'
              '    cur.execute(\'SELECT 1 AS "a""b"; DELETE FROM hidden\')\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_h': ('def run(cur):\n'
              '    cur.execute("SELECT \'$$\'; DELETE FROM hidden; SELECT \'$$\'")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r21_v4_i': ('def run(cur):\n'
              '    cur.execute("DO $$ BEGIN EXECUTE \'DELETE FROM hidden\'; END $$")\n'
              'def own(cur):\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['public.hidden', 'public.own']),
 'r22_copy2_do': ('def run(cur):\n'
                  "    cur.execute('DO $$ BEGIN COPY hidden FROM /*x*/ stdin; END $$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_copy2_func': ('def run(cur):\n'
                    "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN COPY hidden FROM /*x*/ stdin; END $$ LANGUAGE "
                    "plpgsql')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
                    ['public.hidden', 'public.own']),
 'r22_copy2_tag': ('def run(cur):\n'
                   "    cur.execute('DO $t$ BEGIN COPY hidden FROM /*x*/ stdin; END $t$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_copy2_top': ('def run(cur):\n'
                   "    cur.execute('COPY hidden FROM /*x*/ stdin')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_copy_do': ('def run(cur):\n'
                 "    cur.execute('DO $$ BEGIN COPY hidden /*x*/ FROM stdin; END $$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_copy_func': ('def run(cur):\n'
                   "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN COPY hidden /*x*/ FROM stdin; END $$ LANGUAGE plpgsql')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_copy_tag': ('def run(cur):\n'
                  "    cur.execute('DO $t$ BEGIN COPY hidden /*x*/ FROM stdin; END $t$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_copy_top': ('def run(cur):\n'
                  "    cur.execute('COPY hidden /*x*/ FROM stdin')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_cte2_do': ('def run(cur):\n'
                 "    cur.execute('DO $$ BEGIN WITH /*x*/ d AS (DELETE FROM hidden RETURNING *) SELECT 1; END $$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_cte2_func': ('def run(cur):\n'
                   "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN WITH /*x*/ d AS (DELETE FROM hidden RETURNING *) SELECT "
                   "1; END $$ LANGUAGE plpgsql')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_cte2_tag': ('def run(cur):\n'
                  "    cur.execute('DO $t$ BEGIN WITH /*x*/ d AS (DELETE FROM hidden RETURNING *) SELECT 1; END $t$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_cte2_top': ('def run(cur):\n'
                  "    cur.execute('WITH /*x*/ d AS (DELETE FROM hidden RETURNING *) SELECT 1')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_cte_do': ('def run(cur):\n'
                "    cur.execute('DO $$ BEGIN WITH d AS (DELETE /*x*/ FROM hidden RETURNING *) SELECT * FROM d; END $$')\n"
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
                ['public.hidden', 'public.own']),
 'r22_cte_func': ('def run(cur):\n'
                  "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN WITH d AS (DELETE /*x*/ FROM hidden RETURNING *) SELECT * "
                  "FROM d; END $$ LANGUAGE plpgsql')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_cte_tag': ('def run(cur):\n'
                 "    cur.execute('DO $t$ BEGIN WITH d AS (DELETE /*x*/ FROM hidden RETURNING *) SELECT * FROM d; END $t$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_cte_top': ('def run(cur):\n'
                 "    cur.execute('WITH d AS (DELETE /*x*/ FROM hidden RETURNING *) SELECT * FROM d')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_del_do': ('def run(cur):\n'
                "    cur.execute('DO $$ BEGIN DELETE /*x*/ FROM hidden; END $$')\n"
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
                ['public.hidden', 'public.own']),
 'r22_del_func': ('def run(cur):\n'
                  "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN DELETE /*x*/ FROM hidden; END $$ LANGUAGE plpgsql')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_del_tag': ('def run(cur):\n'
                 "    cur.execute('DO $t$ BEGIN DELETE /*x*/ FROM hidden; END $t$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_del_top': ('def run(cur):\n'
                 "    cur.execute('DELETE /*x*/ FROM hidden')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_ins_do': ('def run(cur):\n'
                "    cur.execute('DO $$ BEGIN INSERT /*x*/ INTO hidden VALUES (1); END $$')\n"
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
                ['public.hidden', 'public.own']),
 'r22_ins_func': ('def run(cur):\n'
                  "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN INSERT /*x*/ INTO hidden VALUES (1); END $$ LANGUAGE "
                  "plpgsql')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_ins_tag': ('def run(cur):\n'
                 "    cur.execute('DO $t$ BEGIN INSERT /*x*/ INTO hidden VALUES (1); END $t$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_ins_top': ('def run(cur):\n'
                 "    cur.execute('INSERT /*x*/ INTO hidden VALUES (1)')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_trunc2_do': ('def run(cur):\n'
                   "    cur.execute('DO $$ BEGIN TRUNCATE TABLE /*x*/ ONLY hidden; END $$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_trunc2_func': ('def run(cur):\n'
                     "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN TRUNCATE TABLE /*x*/ ONLY hidden; END $$ LANGUAGE "
                     "plpgsql')\n"
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
                     ['public.hidden', 'public.own']),
 'r22_trunc2_tag': ('def run(cur):\n'
                    "    cur.execute('DO $t$ BEGIN TRUNCATE TABLE /*x*/ ONLY hidden; END $t$')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
                    ['public.hidden', 'public.own']),
 'r22_trunc2_top': ('def run(cur):\n'
                    "    cur.execute('TRUNCATE TABLE /*x*/ ONLY hidden')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
                    ['public.hidden', 'public.own']),
 'r22_trunc_do': ('def run(cur):\n'
                  "    cur.execute('DO $$ BEGIN TRUNCATE /*x*/ TABLE hidden; END $$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_trunc_func': ('def run(cur):\n'
                    "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN TRUNCATE /*x*/ TABLE hidden; END $$ LANGUAGE plpgsql')\n"
                    'def own(cur):\n'
                    "    cur.execute('INSERT INTO own VALUES (1)')\n",
                    ['public.hidden', 'public.own']),
 'r22_trunc_tag': ('def run(cur):\n'
                   "    cur.execute('DO $t$ BEGIN TRUNCATE /*x*/ TABLE hidden; END $t$')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_trunc_top': ('def run(cur):\n'
                   "    cur.execute('TRUNCATE /*x*/ TABLE hidden')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_upd2_do': ('def run(cur):\n'
                 "    cur.execute('DO $$ BEGIN UPDATE hidden AS /*x*/ h SET a=1; END $$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_upd2_func': ('def run(cur):\n'
                   "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN UPDATE hidden AS /*x*/ h SET a=1; END $$ LANGUAGE "
                   "plpgsql')\n"
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.hidden', 'public.own']),
 'r22_upd2_tag': ('def run(cur):\n'
                  "    cur.execute('DO $t$ BEGIN UPDATE hidden AS /*x*/ h SET a=1; END $t$')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_upd2_top': ('def run(cur):\n'
                  "    cur.execute('UPDATE hidden AS /*x*/ h SET a=1')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_upd_do': ('def run(cur):\n'
                "    cur.execute('DO $$ BEGIN UPDATE ONLY /*x*/ hidden SET a=1; END $$')\n"
                'def own(cur):\n'
                "    cur.execute('INSERT INTO own VALUES (1)')\n",
                ['public.hidden', 'public.own']),
 'r22_upd_func': ('def run(cur):\n'
                  "    cur.execute('CREATE FUNCTION f() RETURNS void AS $$ BEGIN UPDATE ONLY /*x*/ hidden SET a=1; END $$ LANGUAGE "
                  "plpgsql')\n"
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.hidden', 'public.own']),
 'r22_upd_tag': ('def run(cur):\n'
                 "    cur.execute('DO $t$ BEGIN UPDATE ONLY /*x*/ hidden SET a=1; END $t$')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r22_upd_top': ('def run(cur):\n'
                 "    cur.execute('UPDATE ONLY /*x*/ hidden SET a=1')\n"
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.hidden', 'public.own']),
 'r23_ctl_append_lit': ('from c import imported, X\n'
                        "QL = ['DELETE FROM a']\n"
                        "QL.append('DELETE FROM b')\n"
                        'def run(cur):\n'
                        '    for q in QL:\n'
                        '        cur.execute(q)\n'
                        'def own(cur):\n'
                        "    cur.execute('INSERT INTO own VALUES (1)')\n",
                        ['public.a', 'public.b', 'public.own']),
 'r23_ctl_iadd_lit': ('from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      "QL += ['DELETE FROM b']\n"
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
                      ['public.a', 'public.b', 'public.own']),
 'r23_ctl_plain': ('from c import imported, X\n'
                   "QL = ['DELETE FROM a']\n"
                   '\n'
                   'def run(cur):\n'
                   '    for q in QL:\n'
                   '        cur.execute(q)\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.a', 'public.own']),
 'r23_exec_in_other_fn': ('from c import imported, X\n'
                          "QL = ['DELETE FROM a']\n"
                          'def helper(cur, q):\n'
                          '    cur.execute(q)\n'
                          '\n'
                          'def run(cur):\n'
                          '    for q in QL:\n'
                          '        helper(cur, q)\n'
                          'def own(cur):\n'
                          "    cur.execute('INSERT INTO own VALUES (1)')\n",
                          ['public.a', 'public.own']),
 'r23_join_use': ('from c import imported, X\n'
                  "QL = ['DELETE FROM a']\n"
                  "S = '; '.join(QL)\n"
                  'def run(cur):\n'
                  '    cur.execute(S)\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.a', 'public.own']),
 'r23_pop_in_place': ('from c import imported, X\n'
                      "QL = ['DELETE FROM a']\n"
                      'QL.pop()\n'
                      'def run(cur):\n'
                      '    for q in QL:\n'
                      '        cur.execute(q)\n'
                      'def own(cur):\n'
                      "    cur.execute('INSERT INTO own VALUES (1)')\n",
                      ['public.a', 'public.own']),
 'r23_reverse_in_place': ('from c import imported, X\n'
                          "QL = ['DELETE FROM a']\n"
                          'QL.reverse()\n'
                          'def run(cur):\n'
                          '    for q in QL:\n'
                          '        cur.execute(q)\n'
                          'def own(cur):\n'
                          "    cur.execute('INSERT INTO own VALUES (1)')\n",
                          ['public.a', 'public.own']),
 'r23_self_extend': ('from c import imported, X\n'
                     "QL = ['DELETE FROM a']\n"
                     'QL.extend(QL)\n'
                     'def run(cur):\n'
                     '    for q in QL:\n'
                     '        cur.execute(q)\n'
                     'def own(cur):\n'
                     "    cur.execute('INSERT INTO own VALUES (1)')\n",
                     ['public.a', 'public.own']),
 'r23_sorted_in_place': ('from c import imported, X\n'
                         "QL = ['DELETE FROM a']\n"
                         'QL.sort()\n'
                         'def run(cur):\n'
                         '    for q in QL:\n'
                         '        cur.execute(q)\n'
                         'def own(cur):\n'
                         "    cur.execute('INSERT INTO own VALUES (1)')\n",
                         ['public.a', 'public.own']),
 'r23_zip_use': ('from c import imported, X\n'
                 "QL = ['DELETE FROM a']\n"
                 'for a, b in zip(QL, QL):\n'
                 '    pass\n'
                 'def run(cur):\n'
                 '    for q in QL:\n'
                 '        cur.execute(q)\n'
                 'def own(cur):\n'
                 "    cur.execute('INSERT INTO own VALUES (1)')\n",
                 ['public.a', 'public.own']),
 'r25_r58': ('from c import imported, X\n'
             "QL = ['DELETE FROM a']\n"
             'R = iter(QL)\n'
             'def run(cur):\n'
             '    for q in R:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r26_k40': ('from c import imported, X\n'
             'class A:\n'
             "    sql = 'DELETE FROM a'\n"
             'class B:\n'
             '    def go(self, cur):\n'
             '        cur.execute(A.sql)\n'
             'def run(cur):\n'
             '    B().go(cur)\n'
             '\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r26_k41': ('from c import imported, X\n'
             'class A:\n'
             "    sql = 'DELETE FROM a'\n"
             'class B:\n'
             '    sql = A.sql\n'
             '    def go(self, cur):\n'
             '        cur.execute(self.sql)\n'
             'def run(cur):\n'
             '    B().go(cur)\n'
             '\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r26_k62': ('from c import imported, X\n'
             'class A:\n'
             "    sql = 'DELETE FROM a'\n"
             '    def __getattr__(self, n):\n'
             '        return X\n'
             '    def go(self, cur):\n'
             '        cur.execute(self.sql)\n'
             'def run(cur):\n'
             '    A().go(cur)\n'
             '\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r26_k71': ('from c import imported, X\n'
             'class A(object):\n'
             "    sql = 'DELETE FROM a'\n"
             '    def go(self, cur):\n'
             '        cur.execute(self.sql)\n'
             'def run(cur):\n'
             '    A().go(cur)\n'
             '\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r26_k_ctl': ('from c import imported, X\n'
               'class Step:\n'
               "    sql = 'DELETE FROM a'\n"
               '    def go(self, cur):\n'
               '        cur.execute(self.sql)\n'
               'def run(cur):\n'
               '    Step().go(cur)\n'
               '\n'
               'def own(cur):\n'
               "    cur.execute('INSERT INTO own VALUES (1)')\n",
               ['public.a', 'public.own']),
 'r26_k_ctl_cls': ('from c import imported, X\n'
                   'class Step:\n'
                   "    sql = 'DELETE FROM a'\n"
                   'def run(cur):\n'
                   '    cur.execute(Step.sql)\n'
                   '\n'
                   'def own(cur):\n'
                   "    cur.execute('INSERT INTO own VALUES (1)')\n",
                   ['public.a', 'public.own']),
 'r26_k_ctl_cm': ('from c import imported, X\n'
                  'class Step:\n'
                  "    sql = 'DELETE FROM a'\n"
                  '    @classmethod\n'
                  '    def go(cls, cur):\n'
                  '        cur.execute(cls.sql)\n'
                  'def run(cur):\n'
                  '    Step.go(cur)\n'
                  '\n'
                  'def own(cur):\n'
                  "    cur.execute('INSERT INTO own VALUES (1)')\n",
                  ['public.a', 'public.own']),
 'r27_q13': ('from c import imported, X, Other\n'
             'class A:\n'
             "    sql = 'DELETE FROM a'\n"
             '    def go(self, cur):\n'
             '        cur.execute(self.sql)\n'
             'B = A\n'
             'def run(cur):\n'
             '    B().go(cur)\n'
             '\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r28_m13': ('from c import imported, X\n'
             "QL = tuple(['DELETE FROM a'])\n"
             'R = QL\n'
             'def run(cur):\n'
             '    for q in QL:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r28_m24': ('from c import imported, X\n'
             "QL = ('DELETE FROM a',)\n"
             'R = list(QL)\n'
             'R.append(X)\n'
             'def run(cur):\n'
             '    for q in QL:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r28_m41': ('from c import imported, X\n'
             "QL = ['DELETE FROM a']\n"
             'QL2 = QL[:]\n'
             'QL2.append(X)\n'
             'def run(cur):\n'
             '    for q in QL:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.a', 'public.own']),
 'r30_s10': ("V='hidden'\n"
             'def run(cur):\n'
             "    cur.execute('DELETE FROM ' + V)\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r30_s11': ("def run(cur):\n    cur.execute('DE' + 'LETE FROM hidden')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r30_s12': ("def run(cur):\n    cur.execute('DELETE'' FROM hidden')\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own']),
 'r30_s36': ("def run(cur):\n    cur.execute('DELETE FROM hidden'.upper())\ndef own(cur):\n    cur.execute('INSERT INTO own VALUES (1)')\n",
             ['public.hidden', 'public.own'])}
