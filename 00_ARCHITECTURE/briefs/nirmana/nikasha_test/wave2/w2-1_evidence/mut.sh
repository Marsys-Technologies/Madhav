#!/bin/bash
# mut.sh NAME FILE TESTSEL [live]  < spec(OLD\n=====>>>\nNEW) : apply mutation, run TESTSEL, restore, rerun suite.
set -u
S=/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/e1effe6d-cae4-4643-b098-d49444a83a68/scratchpad/w2-1
NAME=$1; F=$2; SEL=$3; MODE=${4:-offline}
cd /Users/Dev/madhav-nikasha
cp "$F" "$S/mut_backup.py"
spec=$(cat)
echo "=== mutation $NAME on $F ($MODE)"
printf '%s\n' "$spec" | python3 $S/sub.py "$F" || { echo "MUTATION NOT APPLIED"; exit 1; }
if [ "$MODE" = live ]; then
  (source $S/../pgenv.sh >/dev/null 2>&1; timeout 300 python3 -m pytest $SEL -q -p no:cacheprovider 2>&1 | grep -E '^(FAILED|ERROR)|passed|failed' | tail -8)
else
  env -u PGHOST -u PGPORT -u PGUSER -u PGDATABASE -u PGPASSWORD timeout 300 python3 -m pytest $SEL -q -p no:cacheprovider 2>&1 | grep -E '^(FAILED|ERROR)|passed|failed' | tail -8
fi
cp "$S/mut_backup.py" "$F"
cmp -s "$S/mut_backup.py" "$F" && echo "--- reverted (byte-identical)"
echo "--- after revert:"
env -u PGHOST -u PGPORT -u PGUSER -u PGDATABASE -u PGPASSWORD timeout 300 python3 -m pytest platform/scripts/governance/__tests__/ -q -p no:cacheprovider -k 'not drift_detector' 2>&1 | tail -1
