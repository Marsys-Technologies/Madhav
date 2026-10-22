Vendored COPIES of the merged repository tools, used only by the harness tests (the real runs call the tools in the repository checkout):
  trial_ready.py, git_env_scrub.py          origin/main platform/scripts/governance/   (#3856)
  equivalence_record.py, equivalence_requalification.json   origin/main 00_ARCHITECTURE/briefs/kalayantra/fleet/   (#3855)
taken at origin/main 3978c18ec19aa7bdda680f71bb7b80c209c650fe. Set KY_TOOLS_DIR to a directory holding newer copies to test against them.
  rolling_trial.sh                          a COPY of the cockpit's fast/rolling_trial.sh (taken 2026-10-22; not a repository tool): test_t1b_fix.py runs the report-reading program inside it against the
                                            harness's own report so a renamed key cannot silently page the rolling trial as NOT_RUN.  Refresh it when the cockpit script changes.
