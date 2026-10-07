#!/usr/bin/env bash
# Run by the steward (owner of those events); Stream B may not post updates on A-owned rows.
export PRAVAHA_STREAM=A
P=/Users/Dev/pravaha/bin/pravaha
$P done A5.5a --as steward --evidence 'PRs 2961, 2963, 2981 merged 2026-10-03' --detail 'window prerequisites merged'
$P done A5.5b --as steward --evidence 'decisions/PROTECTED_WINDOW_CLOSE_20261004.md; roles read back 2026-10-04' --detail 'verifier identity, secret container, two roles created and read back'
$P done A5.5c --as steward --evidence 'gate gochara-seal restricted to main; live proof passed 2026-10-04' --detail 'approval gate created and proven'
$P done A5.5d --as steward --evidence 'decisions/DASHA_REPIN_SETTLED1_20261004.md' --detail 'dasha pin at SETTLED-1 build 75524b3e, reviewed'
$P done A5.5e --as steward --evidence '/Users/Dev/pravaha/run/sitting-20261004; decisions/PROTECTED_WINDOW_CLOSE_20261004.md' --detail 'train merged, window applied 2026-10-04 11:50-11:51Z, qualified twice'
