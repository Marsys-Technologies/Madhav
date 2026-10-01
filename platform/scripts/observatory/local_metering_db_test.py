"""Disposable local verification. Never reads production database configuration."""
import os, pathlib, shutil, socket, subprocess, tempfile
platform = pathlib.Path(__file__).resolve().parents[2]
root = pathlib.Path(tempfile.mkdtemp(prefix="madhav-metering-db-"))
pg_bin = pathlib.Path(os.environ.get("AI_METERING_PG_BIN", "/opt/homebrew/bin"))
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
started = False
try:
    subprocess.run([str(pg_bin / "initdb"), "-D", str(root / "data"), "-A", "trust", "-U", "metering_test"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(pg_bin / "pg_ctl"), "-D", str(root / "data"), "-l", str(root / "postgres.log"), "-o", f"-h 127.0.0.1 -p {port} -k {root}", "-w", "start"], check=True)
    started = True
    env = dict(os.environ, AI_METERING_TEST_DATABASE_URL=f"postgresql://metering_test@127.0.0.1:{port}/postgres")
    result = subprocess.run([str(platform / "node_modules/.bin/vitest"), "run",
                             "src/lib/metering/__tests__/ledger.integration.test.ts"], cwd=platform, env=env)
    raise SystemExit(result.returncode)
finally:
    if started:
        subprocess.run([str(pg_bin / "pg_ctl"), "-D", str(root / "data"), "-m", "fast", "-w", "stop"], check=True)
    shutil.rmtree(root)
