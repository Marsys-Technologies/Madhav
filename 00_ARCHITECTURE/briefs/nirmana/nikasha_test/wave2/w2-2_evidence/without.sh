#!/bin/bash
# without.sh NAME REV TESTSEL [live] : run TESTSEL with asset_census.py at REV (the code before the row), restore, cmp.
set -u
S=/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/e1effe6d-cae4-4643-b098-d49444a83a68/scratchpad/w2-2
NAME=$1; REV=$2; SEL=$3; MODE=${4:-offline}
F=platform/scripts/governance/asset_census.py
cd /Users/Dev/madhav-nikasha
cp "$F" "$S/without_backup.py"
git show "$REV:$F" > "$F"
echo "=== without-the-change $NAME: asset_census.py at $REV ($MODE)"
if [ "$MODE" = live ]; then
  (source $S/../pgenv.sh >/dev/null 2>&1; timeout 300 python3 -m pytest $SEL -q -p no:cacheprovider 2>&1 | grep -E '^(FAILED|ERROR)|passed|failed' | tail -12)
else
  env -u PGHOST -u PGPORT -u PGUSER -u PGDATABASE -u PGPASSWORD timeout 300 python3 -m pytest $SEL -q -p no:cacheprovider 2>&1 | grep -E '^(FAILED|ERROR)|passed|failed' | tail -12
fi
cp "$S/without_backup.py" "$F"
cmp -s "$S/without_backup.py" "$F" && echo "--- restored (byte-identical)"
