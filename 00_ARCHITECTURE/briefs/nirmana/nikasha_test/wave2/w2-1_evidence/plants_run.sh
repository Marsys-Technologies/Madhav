#!/bin/bash
# T1 planted suite, W2-1 re-run: sandbox DB only; code plants mutate a scratch worktree only.
S=/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/e1effe6d-cae4-4643-b098-d49444a83a68/scratchpad/w2-1
PY=/opt/homebrew/opt/python@3.13/bin/python3.13
unset PGPASSWORD PGSSLMODE PGSERVICE DATABASE_URL
export PGHOST=/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/nikasha_test/.sandbox PGPORT=54329 PGUSER=sandbox PGDATABASE=nikasha_sandbox PGOPTIONS=
for v in ${@:-head base}; do
  if [ $v = head ]; then W=$S/wt_plant; else W=$S/wt_9baaa; fi
  O=$S/plants_$v; mkdir -p $O/plants
  echo "##### $v ($(git -C $W rev-parse --short HEAD)) $(date +%T)"
  echo "sandbox read_only: $(psql -tAX -c 'SHOW default_transaction_read_only') db=$(psql -tAX -c 'select current_database()')"
  for L in L0 L3 L4; do
    (cd $W && timeout 300 $PY platform/scripts/governance/asset_census.py --layer $L --out $O/baseline_$L.json | grep -E 'FAIL [0-9]+ ·|UNKNOWN')
  done
  W2_PLANT_ROOT=$W W2_PLANT_OUT=$O timeout 1800 $PY $S/plant_w2.py run > $O/plant_run.log 2>&1
  echo "plant rc=$?"
  git -C $W status --short | head -5
done
echo DONE
