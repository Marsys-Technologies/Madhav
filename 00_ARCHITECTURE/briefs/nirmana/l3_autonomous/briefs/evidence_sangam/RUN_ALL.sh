#!/usr/bin/env bash
# Falsifier runner v2 (RR-01). Each script must exit 0 on its positive run AND exit nonzero under NEG=1
# (its negative control), or the suite FAILS. Writes a NEW timestamped OUTPUT file; never truncates a prior one.
# Read-only otherwise; no DB. Exit status of this runner is the suite verdict.
cd "$(dirname "$0")"
PY=/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python
OUT="OUTPUT_$(date +%FT%H%M%S).txt"; [ -e "$OUT" ] && { echo "refusing to overwrite $OUT"; exit 2; }
fail=0; n=0
while IFS='|' read -r script want_pos want_neg; do
  [[ "$script" =~ ^#|^$ ]] && continue; n=$((n+1))
  [ -f "$script" ] || { echo "MISSING $script" | tee -a "$OUT"; fail=1; continue; }
  $PY -B "$script" >> "$OUT" 2>&1; rc=$?
  NEG=1 $PY -B "$script" > /dev/null 2>&1; nrc=$?
  if [ "$rc" -ne "$want_pos" ]; then echo "SUITE-FAIL positive: $script exit=$rc want=$want_pos" | tee -a "$OUT"; fail=1; fi
  if [ "$nrc" -eq 0 ]; then echo "SUITE-FAIL negative control did not fail: $script" | tee -a "$OUT"; fail=1; fi
  echo "  [$script] positive exit=$rc  negative-control exit=$nrc" >> "$OUT"
done < MANIFEST.txt
echo "scripts run: $n; verdict: $([ $fail -eq 0 ] && echo SUITE-PASS || echo SUITE-FAIL)" | tee -a "$OUT"
echo "wrote $OUT"; exit $fail
