"""Reviewer corpus of FP2 round 3 (cases12/13/15/16/17/18), embedded verbatim: every case must read PARTIAL (not scanned) -- or,
for the literal-only comment cases, the exact table set. Generated from the reviewer scratch files; see test_e5_9_footprint_round3.py."""
PARTIAL = {'r12_ca14': 'from consts import Q, QS, D\n'
             'class A:\n'
             "    sql = 'DELETE FROM a'\n"
             '    sql += Q\n'
             '    def go(self, cur):\n'
             '        cur.execute(self.sql)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ca15': 'from consts import Q, QS, D\n'
             'class A:\n'
             "    sql = 'DELETE FROM a'\n"
             '    if QS:\n'
             '        sql = Q\n'
             '    def go(self, cur):\n'
             '        cur.execute(self.sql)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ca3': 'from consts import Q, QS, D\n'
            'class W:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            '    def set(self):\n'
            "        self.__dict__['sql'] = Q\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ca5': 'from consts import Q, QS, D\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'class B(A):\n'
            '    sql = Q\n'
            'B().go(None)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ca9': 'from consts import Q, QS, D\n'
            'class A:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'A.__dict__\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_cp70': 'from consts import Q, QS, D\n'
             'def run(cur):\n'
             "    cur.__getattribute__('execute')(Q)\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_cp74': 'from consts import Q, QS, D\n'
             'def run(cur):\n'
             '    import operator\n'
             "    operator.methodcaller('execute', Q)(cur)\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct10': 'from consts import Q, QS, D\n'
             "QL = ['DELETE FROM a']\n"
             'Q2 = QL\n'
             'Q2.append(Q)\n'
             'def run(cur):\n'
             '    for q in QL:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct13': 'from consts import Q, QS, D\n'
             "QL = ['DELETE FROM a']\n"
             'list(map(QL.append, QS))\n'
             'def run(cur):\n'
             '    for q in QL:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct18': 'from consts import Q, QS, D\n'
             "QL = ['DELETE FROM a']\n"
             'def run(cur):\n'
             '    import operator\n'
             '    operator.setitem(QL, 0, Q)\n'
             '    cur.execute(QL[0])\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct22': 'from consts import Q, QS, D\n'
             "QL = {'k':'DELETE FROM a'}\n"
             'def run(cur):\n'
             "    QL.__setitem__('k', Q)\n"
             "    cur.execute(QL['k'])\n"
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct25': 'from consts import Q, QS, D\n'
             "QL = ['DELETE FROM a']\n"
             'def fill(l, v):\n'
             '    l.append(v)\n'
             'def run(cur):\n'
             '    fill(QL, Q)\n'
             '    for q in QL:\n'
             '        cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct5': 'from consts import Q, QS, D\n'
            "QL = ['DELETE FROM a']\n"
            'QL.__setitem__(0, Q)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct6': 'from consts import Q, QS, D\n'
            "QL = ['DELETE FROM a']\n"
            'QL.__iadd__(QS)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct7': 'from consts import Q, QS, D\n'
            "QL = ['DELETE FROM a']\n"
            'list.append(QL, Q)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct8': 'from consts import Q, QS, D\n'
            "QL = ['DELETE FROM a']\n"
            'ap = QL.append\n'
            'ap(Q)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_ct9': 'from consts import Q, QS, D\n'
            "QL = ['DELETE FROM a']\n"
            'def add(l):\n'
            '    l.append(Q)\n'
            'add(QL)\n'
            'def run(cur):\n'
            '    for q in QL:\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_gl2': 'from consts import Q, QS, D\n'
            "T='DELETE FROM a'\n"
            'import builtins\n'
            'def run(cur):\n'
            "    builtins.globals()['T'] = Q\n"
            '    cur.execute(T)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_gl3': 'from consts import Q, QS, D\n'
            "T='DELETE FROM a'\n"
            'def run(cur):\n'
            '    import sys\n'
            "    sys._getframe().f_globals['T'] = Q\n"
            '    cur.execute(T)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_gl4': 'from consts import Q, QS, D\n'
            "T='DELETE FROM a'\n"
            'def run(cur):\n'
            '    g = globals\n'
            "    g()['T'] = Q\n"
            '    cur.execute(T)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_gl6': 'from consts import Q, QS, D\n'
            "T='DELETE FROM a'\n"
            'import inspect\n'
            'def run(cur):\n'
            "    inspect.currentframe().f_globals['T'] = Q\n"
            '    cur.execute(T)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_gl7': 'from consts import Q, QS, D\n'
            "T='DELETE FROM a'\n"
            'import __main__\n'
            'def run(cur):\n'
            '    __main__.T = Q\n'
            '    cur.execute(T)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_gl8': 'from consts import Q, QS, D\n'
            'import sys\n'
            "T='DELETE FROM a'\n"
            'def run(cur):\n'
            '    me = sys.modules[__name__]\n'
            '    me.T = Q\n'
            '    cur.execute(T)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r12_pd8': 'from consts import Q, QS, D\n'
            "def f(cur, q='DELETE FROM a'):\n"
            '    cur.execute(q)\n'
            'def run(cur):\n'
            '    f(cur)\n'
            "    getattr(__import__('sys').modules[__name__], 'f')(cur, Q)\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r15_dd1': 'from consts import Q, QS\n'
            'class W:\n'
            "    def go(self, cur, q='DELETE FROM a'):\n"
            '        cur.execute(q)\n'
            '    def run(self, cur):\n'
            '        self.go(cur)\n'
            "        getattr(self, 'go')(cur, Q)\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r15_dd18': 'from consts import Q, QS\n'
             'class W:\n'
             '    @classmethod\n'
             "    def go(cls, cur, q='DELETE FROM a'):\n"
             '        cur.execute(q)\n'
             'W.go(None)\n'
             'W.go(None, Q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r15_dd2': 'from consts import Q, QS\n'
            "def f(cur, q='DELETE FROM a'):\n"
            '    cur.execute(q)\n'
            'def run(cur):\n'
            '    f(cur)\n'
            "    globals()['f'](cur, Q)\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r15_dd3': 'from consts import Q, QS\n'
            "def f(cur, q='DELETE FROM a'):\n"
            '    cur.execute(q)\n'
            'def run(cur):\n'
            '    f(cur)\n'
            "    locals()['f'](cur, Q)\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r15_dd4': 'from consts import Q, QS\n'
            "def f(cur, q='DELETE FROM a'):\n"
            '    cur.execute(q)\n'
            'def run(cur):\n'
            '    f(cur)\n'
            "    vars()['f'](cur, Q)\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r15_dd5': 'from consts import Q, QS\n'
            "def f(cur, q='DELETE FROM a'):\n"
            '    cur.execute(q)\n'
            'def run(cur):\n'
            '    f(cur)\n'
            "    globals().get('f')(cur, Q)\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de1': 'from c import deco\n'
            '@deco\n'
            'def get_sql():\n'
            "    return 'DELETE FROM a'\n"
            'def run(cur):\n'
            '    cur.execute(get_sql())\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de2': 'from c import deco\n'
            'class W:\n'
            '    @deco\n'
            '    def sql(self):\n'
            "        return 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql())\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de33': 'from c import Q\n'
             "L = ['DELETE FROM a']\n"
             'def f():\n'
             '    L.__setitem__(0, Q)\n'
             'def run(cur):\n'
             '    cur.execute(L[0])\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de36': 'from c import Q\n'
             'class W:\n'
             "    L = ['DELETE FROM a']\n"
             '    def go(self, cur):\n'
             '        self.L.append(Q)\n'
             '        cur.execute(self.L[0])\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de37': 'from c import Q\n'
             'class W:\n'
             "    L = ['DELETE FROM a']\n"
             '    def go(self, cur):\n'
             '        self.L.append(Q)\n'
             '        for q in self.L:\n'
             '            cur.execute(q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de38': 'from c import Q\n'
             'class W:\n'
             "    L = ['DELETE FROM a']\n"
             '    def go(self, cur):\n'
             '        for q in self.L:\n'
             '            cur.execute(q)\n'
             'def g():\n'
             '    W.L.append(Q)\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de39': 'from c import Q\n'
             'class W:\n'
             "    L = ['DELETE FROM a']\n"
             '    def go(self, cur):\n'
             '        for q in self.L:\n'
             '            cur.execute(q)\n'
             'def g(w):\n'
             '    w.L.extend([Q])\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de40': 'from c import Q\n'
             'class W:\n'
             "    L = ['DELETE FROM a']\n"
             '    def go(self, cur):\n'
             '        for q in self.L:\n'
             '            cur.execute(q)\n'
             'def g(w):\n'
             '    w.L[0] = Q\n'
             'def own(cur):\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de8': 'from c import Q\n'
            'def run(cur):\n'
            '    for q in sum([[Q]], []):\n'
            '        cur.execute(q)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r16_de9': 'from c import QS\n'
            'def run(cur):\n'
            '    cur.execute(sum(QS, ()) )\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r17_vb1': "V='DELETE'\n"
            "F='FROM'\n"
            'def run(cur):\n'
            "    cur.execute(f'{V} {F} a')\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r17_vb9': "V='DELETE'\n"
            "F='FROM'\n"
            "T='a'\n"
            'def run(cur):\n'
            "    cur.execute(' '.join([V, F, T]))\n"
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r18_dc1': 'from dataclasses import dataclass\n'
            'from c import Q\n'
            '@dataclass\n'
            'class Step:\n'
            "    sql: str = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step(sql=Q).go(cur)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r18_dc2': 'from typing import NamedTuple\n'
            'from c import Q\n'
            'class Step(NamedTuple):\n'
            "    sql: str = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step(Q).go(cur)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r18_dc4': 'from c import Q\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def __init__(self, **kw):\n'
            '        self.__dict__.update(kw)\n'
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step(sql=Q).go(cur)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r18_dc5': 'from c import Q\n'
            'import types\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    Step.go(types.SimpleNamespace(sql=Q), cur)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r18_dc6': 'from c import Q\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur, other):\n'
            '    Step.go(other, cur)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r18_dc7': 'from c import Q\n'
            'class Step:\n'
            "    sql = 'DELETE FROM a'\n"
            '    def go(self, cur):\n'
            '        cur.execute(self.sql)\n'
            'def run(cur):\n'
            '    class Sub(Step):\n'
            '        sql = Q\n'
            '    Sub().go(cur)\n'
            'def own(cur):\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r8_globals_alias_upd': "T='a'\n"
                         'g=globals\n'
                         "g()['T']='b'\n"
                         'def run(cur):\n'
                         "    cur.execute(f'DELETE FROM {T}')\n"
                         "    cur.execute('INSERT INTO own VALUES (1)')\n"}

COMMENT_PARTIAL = {'r13_cm1': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"INSERT INTO c VALUES (\'--\'); DELETE FROM {T}")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm2': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"INSERT INTO c VALUES (\'/*\'); DELETE FROM {T}")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm29': 'def run(cur, t):\n'
             '    cur.execute(f"INSERT INTO a VALUES (\'--\'); INSERT INTO {t} VALUES (1)")\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm3': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"DELETE FROM {T}")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm30': 'def run(cur, t):\n'
             '    cur.execute("SELECT \'--\' ; INSERT INTO" + " " + t)\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm31': 'def run(cur, t):\n'
             "    cur.execute('INSERT INTO ' + t + ' /* ' + 'x */ VALUES (1)')\n"
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm32': "T = 'a'\n"
             'if 1:\n'
             "    T = 'b'\n"
             'def run(cur, t):\n'
             '    cur.execute(f"INSERT INTO a -- c\\n VALUES (1); DELETE FROM {T}")\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm33': "T = 'a'\n"
             'if 1:\n'
             "    T = 'b'\n"
             'def run(cur, t):\n'
             '    cur.execute(f"INSERT INTO a VALUES (\'--\')\\n; DELETE FROM {T}")\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm34': "T = 'a'\n"
             'if 1:\n'
             "    T = 'b'\n"
             'def run(cur, t):\n'
             '    cur.execute(f"SELECT \'--\' -- x\\n; DELETE FROM {T}")\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm35': "T = 'a'\n"
             'if 1:\n'
             "    T = 'b'\n"
             'def run(cur, t):\n'
             '    cur.execute(f"SELECT \'/*\' ; DELETE FROM {T} /* x */")\n'
             "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm4': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"SELECT \'--\'; DELETE FROM {T}")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm5': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"SELECT 1 /* "\n'
            '      f"DELETE FROM {T}")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm6': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"SELECT \'/*\'; UPDATE {T} SET x=1")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm7': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"SELECT \'--\'; TRUNCATE {T}, c")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm8': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"SELECT \'--\'; COPY {T} FROM STDIN")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n",
 'r13_cm9': "T = 'a'\n"
            'if 1:\n'
            "    T = 'b'\n"
            'def run(cur, t):\n'
            '    cur.execute(f"SELECT \'--\'; INSERT INTO {T} VALUES (1)")\n'
            "    cur.execute('INSERT INTO own VALUES (1)')\n"}

COMMENT_SETS = {'r13_cm10': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (\'--\'); INSERT INTO b VALUES (1)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm11': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (\'/*\'); INSERT INTO b VALUES (1)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm12': ('def run(cur, t):\n    cur.execute("SELECT \'--\'; UPDATE b SET x=1")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
              ['b', 'own']),
 'r13_cm13': ('def run(cur, t):\n    cur.execute("SELECT $$--$$; DELETE FROM b")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
              ['b', 'own']),
 'r13_cm14': ('def run(cur, t):\n'
              '    cur.execute("/* /* nested */ INSERT INTO a VALUES (1) */ INSERT INTO b VALUES (1)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm15': ('def run(cur, t):\n    cur.execute("INSERT /* c */ INTO a VALUES (1)")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
              ['a', 'own']),
 'r13_cm16': ('def run(cur, t):\n    cur.execute("DEL/**/ETE FROM a")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n', ['own']),
 'r13_cm17': ('def run(cur, t):\n    cur.execute("INSERT INTO a VALUES (1) --")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
              ['a', 'own']),
 'r13_cm18': ('def run(cur, t):\n    cur.execute("INSERT INTO a VALUES (1) /*")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
              ['a', 'own']),
 'r13_cm19': ('def run(cur, t):\n'
              '    cur.execute("E\'\\\\\'\' ; INSERT INTO a VALUES (1)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'own']),
 'r13_cm20': ('def run(cur, t):\n'
              '    cur.execute("SELECT E\'\\\\\'--\'; INSERT INTO a VALUES (1)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'own']),
 'r13_cm21': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (1);--\\nINSERT INTO b VALUES (2)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm22': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (1);--\\r\\nINSERT INTO b VALUES (2)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm23': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (1);--\\rINSERT INTO b VALUES (2)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm24': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (1);--\\x0bINSERT INTO b VALUES (2)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm25': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (1);--\\u2028INSERT INTO b VALUES (2)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm26': ('def run(cur, t):\n'
              '    cur.execute("INSERT INTO a VALUES (1);*/ INSERT INTO b VALUES (2)")\n'
              "    cur.execute('INSERT INTO own VALUES (1)')\n",
              ['a', 'b', 'own']),
 'r13_cm27': ('def run(cur, t):\n    cur.execute("/* c */ */ INSERT INTO b VALUES (2)")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
              ['b', 'own']),
 'r13_cm28': ('def run(cur, t):\n    cur.execute("SELECT 1 -/* x */- 2; DELETE FROM b")\n    cur.execute(\'INSERT INTO own VALUES (1)\')\n',
              ['b', 'own'])}
