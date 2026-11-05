"""DDL-derived stand-in for the catalog (offline harness only; the live census reads information_schema).
Best effort over platform/migrations + platform/supabase/migrations: CREATE TABLE columns, ALTER ... ADD COLUMN,
ALTER COLUMN SET/DROP DEFAULT. Renames, drops and type changes are NOT followed."""
import re, glob, collections

REPO = "platform"   # overridden by offline_narr_null_L1.py (ddl_c.REPO = <repo>/platform)
KW = {"primary", "foreign", "unique", "check", "constraint", "exclude", "like"}
_END = re.compile(r"\s+(?:NOT\s+NULL|NULL|PRIMARY|REFERENCES|CHECK|UNIQUE|GENERATED|COLLATE|CONSTRAINT)\b", re.I)


def split_top(s):
    out, d, cur, q = [], 0, "", None
    for ch in s:
        if q:
            cur += ch
            q = None if ch == q else q
            continue
        if ch in "'\"":
            q = ch; cur += ch; continue
        d += ch == "("; d -= ch == ")"
        if ch == "," and d == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def coldef(p):
    w = p.strip().split(None, 1)
    col = w[0].strip('"')
    rest = w[1] if len(w) > 1 else ""
    dm = re.search(r"\bDEFAULT\s+(.+)", rest, re.I | re.S)
    default = None
    if dm:
        default = _END.split(dm.group(1))[0].strip()
    typ = re.split(r"\s+(?:NOT|NULL|DEFAULT|PRIMARY|REFERENCES|CHECK|UNIQUE|GENERATED|COLLATE)\b", rest, flags=re.I)[0].strip().lower()
    return col, typ, default


def build():
    cols = collections.defaultdict(dict)
    files = sorted(glob.glob(f"{REPO}/migrations/*.sql") + glob.glob(f"{REPO}/supabase/migrations/*.sql"))
    for f in files:
        t = open(f, encoding="utf-8", errors="replace").read()
        t = re.sub(r"/\*.*?\*/", "", re.sub(r"--[^\n]*", "", t), flags=re.S)
        for m in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?\"?([a-z_0-9]+)\"?\s*\(", t, re.I):
            i = m.end(); d = 1; j = i
            while j < len(t) and d > 0:
                d += (t[j] == "(") - (t[j] == ")"); j += 1
            for part in split_top(t[i:j - 1]):
                if part.strip() and part.split()[0].lower() not in KW:
                    c, ty, df = coldef(part)
                    cols[m.group(1)][c] = (ty, df)
        for m in re.finditer(r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?:public\.)?\"?([a-z_0-9]+)\"?\s+([^;]*);", t, re.I | re.S):
            for a in split_top(m.group(2)):
                am = re.match(r"\s*ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?(.*)", a, re.I | re.S)
                if am:
                    c, ty, df = coldef(am.group(1)); cols[m.group(1)][c] = (ty, df)
                sm = re.match(r"\s*ALTER\s+COLUMN\s+\"?(\w+)\"?\s+SET\s+DEFAULT\s+(.+)", a, re.I | re.S)
                if sm and sm.group(1) in cols[m.group(1)]:
                    cols[m.group(1)][sm.group(1)] = (cols[m.group(1)][sm.group(1)][0], sm.group(2).strip())
                dm = re.match(r"\s*ALTER\s+COLUMN\s+\"?(\w+)\"?\s+DROP\s+DEFAULT", a, re.I)
                if dm and dm.group(1) in cols[m.group(1)]:
                    cols[m.group(1)][dm.group(1)] = (cols[m.group(1)][dm.group(1)][0], None)
    return cols
