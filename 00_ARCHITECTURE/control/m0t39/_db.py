import re, pathlib, psycopg, psycopg.rows
ROOT = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
def url():
    return next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
                for l in (ROOT/'platform/.env.local').read_text().splitlines() if l.startswith('DATABASE_URL='))
def conn(autocommit=True):
    c = psycopg.connect(url(), row_factory=psycopg.rows.dict_row, autocommit=autocommit)
    c.execute("SET statement_timeout = '60s'")
    return c
