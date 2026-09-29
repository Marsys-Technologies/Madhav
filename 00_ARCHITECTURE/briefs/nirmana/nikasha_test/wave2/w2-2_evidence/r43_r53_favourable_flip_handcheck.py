import re, pathlib
SC = pathlib.Path("platform/python-sidecar"); W = SC / "pipeline/orchestrator/writers"
ka = "ka_dasha_kala ka_gochara_resonance ka_kota_chakra ka_kshetra ka_moorti_nirnaya ka_muhurta_seva ka_sudarshana_varsha ka_tithi_pravesha ka_tulana ka_vedha_gochara".split()
files = {a: SC / "services" / a / "writer.py" for a in ka}
files.update(mi_bhara=W / "mi_bhara.py", mi_sankalpa=W / "mi_sankalpa.py", ph_rectification=W / "ph_rectification/__init__.py")
targets = dict(l.split(" | ") for l in open("/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/e1effe6d-cae4-4643-b098-d49444a83a68/scratchpad/w2-2/idem_targets.txt").read().split("\n") if l)
print("R43 contract flips — text-level scan broader than the AST contract_scan (every line of the resolved file):")
for a, f in files.items():
    t = f.read_text()
    calls = [f"{i+1}: {l.strip()}" for i, l in enumerate(t.splitlines()) if re.search(r"\.(commit|close|rollback)\(\)", l) and not l.strip().startswith("#")]
    thr = [f"{i+1}: {l.strip()[:90]}" for i, l in enumerate(t.splitlines()) if "asset_throughput" in l and re.search(r"\b(INSERT|UPDATE|DELETE)\b", l, re.I)]
    print(f"  {a:22s} {f.relative_to(SC)} | commit/close/rollback calls: {calls or 'none'} | asset_throughput writes: {thr or 'none'}")
print("R43 Idem.pattern PASS flips — DELETE targets vs registry target_table:")
for a, tt in sorted(targets.items()):
    t = files[a].read_text()
    dels = sorted(set(re.findall(r"DELETE\s+FROM\s+([A-Za-z_0-9.]+)", t, re.I)))
    print(f"  {a:22s} target={tt:24s} DELETE FROM {dels}  -> {'on target' if tt in dels else 'NOT on target'}")
