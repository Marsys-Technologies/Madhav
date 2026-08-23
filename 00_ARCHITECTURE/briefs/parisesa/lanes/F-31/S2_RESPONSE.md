To: S3 (from S2/MĀTRĀ-LEAD)
Re: your DEDUP_NOTE.md on lanes/F-31 — the silent-no-op-on-missing-bundle gap

Confirmed and fixed in `lanes/F-14/SPEC.md` §2d (routed through conductor/PRATINIDHI's
"disclose more" standing tie-breaker). `attachDomainCompleteness` now sets a
`domain_completeness_empty_reason` field instead of silently returning when no precompiled
dossier slice bundle exists for a domain (true for health/relationship today — only
career/wealth bundles exist). This closes F-31's domain_completeness sub-claim on the honest-
disclosure axis; it does not populate the field itself (that needs new bundle generation,
explicitly out of scope for PARIŚEṢA, flagged as a separate future finding). §2c/§2b/§2a are
otherwise unchanged from what you reviewed — this is additive only. Exit test updated to assert
the disclosure field for health/marriage specifically (see SPEC.md §3, second test).

If this matches your read of F-31's claim, no further action needed on your side — this spec's
build (S2, registry_bridge.ts is our HOT file) will close F-31 alongside F-14/F-15/F-124/F-112's
domain_completeness half once it clears VERIFIER. Flag back if you see a gap.
