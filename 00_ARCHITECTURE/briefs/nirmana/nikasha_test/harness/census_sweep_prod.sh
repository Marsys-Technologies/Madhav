#!/usr/bin/env bash
# nikasha-test Phase 2 (T2) — production census sweep, read-only, with runtimes.
set -uo pipefail
cd /Users/Dev/madhav-nikasha
source /Users/Dev/madhav-l3/dbenv.sh
export PGPORT=5433
PY=/opt/homebrew/opt/python@3.13/bin/python3.13
OUT=00_ARCHITECTURE/briefs/nirmana/nikasha_test/census
TS=20260926
RT="$OUT/runtime_sweep_$TS.tsv"
: > "$RT"
for L in L1 L2 L3 L4 L5 all; do
  start=$(date +%s)
  $PY platform/scripts/governance/asset_census.py --layer "$L" --out "$OUT/${L}_prod_${TS}.json" > "$OUT/${L}_prod_${TS}.log" 2>&1
  rc=$?
  end=$(date +%s)
  echo -e "$L\t$((end-start))s\trc=$rc" | tee -a "$RT"
done
echo "[sweep] done" | tee -a "$RT"
