#!/usr/bin/env python3
"""Offline rollup of the SAVED L2 census under the current inspector's rules (A.L2, INDEX section 1).

Runs asset_census.build_rollup_output (platform/scripts/governance/asset_census.py) over the saved measurements. It mixes old
measurements with new rules: not a re-measure. The saved JSON carries no per-asset `columns`/`asset_kind` facts, so applicability-
dependent criteria read NO_DETECTOR.

Usage: python3 rollup_saved_l2.py <repo-root> [census.json] [output.json]
Default census: layers/census/after_reader_grant/census_L2.json (the one the briefs use).
"""
import json, sys
root = sys.argv[1] if len(sys.argv) > 1 else '.'
cen = sys.argv[2] if len(sys.argv) > 2 else root + '/00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json'
out = sys.argv[3] if len(sys.argv) > 3 else 'rollup_saved_L2.json'
sys.path.insert(0, root + '/platform/scripts/governance')
import asset_census as ac
c = json.load(open(cen))
r = ac.build_rollup_output({'L2': c['L2']}, declarations=ac.load_asset_declarations())
json.dump(r, open(out, 'w'), indent=1)
print('registry_revision', r['rollup']['registry_revision'])
