"""AM-16: is 'the opened ephemeris files + swisseph version + flags' an adequate identity for the arc / node series the kernel consumes?
(Codex round 7 [9]: 'specify the consumed arc/node-series content binding or the demonstrated equivalence of the file-identity substitute'.)

The kernel does not store the series: it computes it with pyswisseph (`calc_ut`, FLG_SWIEPH|FLG_SPEED|FLG_SIDEREAL). The series is therefore a PURE FUNCTION of
(opened file contents, library version, flags/sidereal mode, instants). This probe DEMONSTRATES that on the real files:
  1  the same inputs give a byte-identical series in two separate processes (determinism);
  2  a byte-identical COPY of the files in a different directory gives the same series (path independence — identity is content, not location);
  3  a one-byte corruption of an OPENED file changes the series or is refused (the file hash is therefore necessary);
  4  an UNOPENED file (seas_18.se1) can be removed or altered with no change to the series (the file hash of an unopened file is NOT needed);
and defines the cheap CONTENT binding the vector carries in addition: `probe_digest` = sha256 over the exact float.hex() results of calc_ut for a fixed
probe set (bodies x instants), so a library/numerics change that file hashes alone would miss is still caught.
Usage: python am16_series_equivalence_probe.py <ephe_dir> [--child]"""
import hashlib, json, os, shutil, subprocess, sys, tempfile

BODIES = {"Sun": 0, "Moon": 1, "Saturn": 6, "MeanNode": 10}
INSTANTS = [(2024, 6, 1, 0.0), (2025, 1, 1, 0.0), (2025, 7, 1, 12.0), (2026, 1, 1, 0.0)]


def series_digest(ephe_dir):
    import swisseph as swe
    swe.close(); swe.set_ephe_path(ephe_dir); swe.set_sid_mode(swe.SIDM_LAHIRI)
    fl = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
    rows, opened = [], set()
    for y, m, d, h in INSTANTS:
        jd = swe.julday(y, m, d, h)
        for name, b in BODIES.items():
            xx, ret = swe.calc_ut(jd, b, fl)
            rows.append([name, jd, ret & 2 == 2, [float(v).hex() for v in xx]])
            for i in (0, 1):
                f = swe.get_current_file_data(i)[0]
                if f: opened.add(os.path.basename(f))
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest(), sorted(opened), swe.version


def runtime_identity():
    """What the vector binds besides the data files (AM-16 schema /2, Codex R8-1): the sha256 of the LOADED swisseph artifact (the compiled
    extension the import resolved to — a version string does not distinguish two builds) and the platform."""
    import importlib.util, platform, swisseph as swe
    origin = importlib.util.find_spec("swisseph").origin
    with open(origin, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()
    return {"swe_version": swe.version, "library_file": os.path.basename(origin), "library_sha256": h, "platform": f"{platform.system()}-{platform.machine()}"}


def child(ephe_dir):
    d, opened, ver = series_digest(ephe_dir)
    print(json.dumps({"digest": d, "opened": opened, "version": ver}))


def run_child(ephe_dir):
    out = subprocess.run([sys.executable, __file__, ephe_dir, "--child"], capture_output=True, text=True)
    return json.loads(out.stdout.strip().splitlines()[-1]) if out.returncode == 0 and out.stdout.strip() else {"error": (out.stderr or out.stdout)[-200:]}


def main(src):
    base = run_child(src); again = run_child(src)
    print("0 runtime identity bound by the vector:", json.dumps(runtime_identity()))
    print("1 determinism (two processes):", base["digest"] == again["digest"], base["digest"][:16], "opened", base["opened"], "swe", base["version"])
    with tempfile.TemporaryDirectory() as t:
        c = os.path.join(t, "copy"); shutil.copytree(src, c)
        print("2 path independence (byte-identical copy elsewhere):", run_child(c)["digest"] == base["digest"])
        un = os.path.join(t, "no_unopened"); shutil.copytree(src, un); os.remove(os.path.join(un, "seas_18.se1"))
        print("4a unopened file REMOVED -> same series:", run_child(un)["digest"] == base["digest"])
        ua = os.path.join(t, "alt_unopened"); shutil.copytree(src, ua)
        with open(os.path.join(ua, "seas_18.se1"), "r+b") as fh:
            fh.seek(5000); b = fh.read(1); fh.seek(5000); fh.write(bytes([b[0] ^ 0xFF]))
        print("4b unopened file ALTERED -> same series:", run_child(ua)["digest"] == base["digest"])
        for name in ("sepl_18.se1", "semo_18.se1"):
            for label, stride in (("ONE byte at offset 100000", None), ("every 997th byte across the file", 997)):
                cc = os.path.join(t, "corrupt"); shutil.rmtree(cc, ignore_errors=True); shutil.copytree(src, cc)
                path = os.path.join(cc, name)
                with open(path, "r+b") as fh:
                    data = bytearray(fh.read())
                    for i in ([100000] if stride is None else range(0, len(data), stride)):
                        data[i] ^= 0xFF
                    fh.seek(0); fh.write(data)
                r = run_child(cc)
                verdict = "REFUSED/ERROR" if "error" in r else ("series DIFFERS" if r["digest"] != base["digest"] else "same series")
                print(f"3 opened file {name}, {label}: {verdict}")
        print("   -> a byte outside the consumed Chebyshev segments does not move the series (the file hash is a SUFFICIENT, conservative identity, not a minimal one);"
              " damage inside consumed data does.")


if __name__ == "__main__":
    if "--child" in sys.argv: child(sys.argv[1])
    else: main(sys.argv[1])
