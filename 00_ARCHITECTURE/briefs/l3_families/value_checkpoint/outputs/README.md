# VC-2 outputs — intentionally empty

No VC-2 arm output exists. The generator (`platform/scripts/value_checkpoint/vc2_run.py --mode real`) refuses
to write here until the freeze order of `KSHETRA_ABLATION_PREREGISTRATION_v1_1.md` §2 is satisfied: an accepted
full-G1 baseline receipt, the external binding receipt (seven identities, hashes equal to the raw files and to
the landed commit) and a consenting, evaluation-eligible population with six provenanced class identities.
Any file here other than this README before then invalidates the run (preregistration.json `freeze.preexisting_outputs`).

Rehearsal output (`--mode rehearsal`) is refused under this directory by construction.
