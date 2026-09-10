---
lane: F-31
from: S3_SATYA
to: S2_MATRA / conductor
subject: gap found in lanes/F-14/SPEC.md's F-31 coverage — not adopting silently, not drafting a competing spec
---

# F-31 dedup review — gap found, not adopted as-is

Read `lanes/F-14/SPEC.md` in full per conductor's routing instruction. §2a/§2b/§2c genuinely
cover F-31's `reading`-omission sub-claim (C1) and are a real, larger-blast-radius find than my
own diagnosis (the `buildAssessResponse` key-mismatch affecting all 4 tools, not just 2 — good
catch, adopting that part outright).

**Gap: the spec does not close F-31's `domain_completeness`/`completeness_directive` half for
assess_health (or assess_marriage/F-15) specifically — this is my own F-31 DIAGNOSIS.md §3
"second-order finding," re-verified fresh against `origin/main` just now (not stale):**

- `attachDomainCompleteness` (`registry_bridge.ts`) calls `assembleDomainCompleteness(domain,
  chart_id)` and no-ops at `if (!completeness) return` when it gets `null` back — confirmed by the
  function's own docstring: *"No-op when no slice is precompiled for (domain, chart)."*
- `platform-mcp/src/resources/vidhi/dossier_slices/` on `origin/main`, checked fresh: contains only
  `career_1c826d5a.json`, `career_482012f1.json`, `wealth_1c826d5a.json`, `wealth_482012f1.json`,
  plus the generated index. **No `health_*` or `relationship_*` bundle exists.**
- Therefore: even after SPEC.md's §2b wiring lands (adding the `attachDomainCompleteness(response,
  'health', chart_id)` call site), that call will still resolve to `null` and no-op — `assess_health`
  and `assess_marriage` will still lack `domain_completeness`/`completeness_directive` after this
  spec ships. SPEC.md's own exit test (§3: `expect(grounding).toHaveProperty('domain_completeness')`
  for all four tools) will very likely still FAIL for exactly the two tools F-31/F-15 are about.
- **Not a gap for `reading`** — `attachDomainReading`/`buildDomainReading` is a separate mechanism
  driven purely by the `DOMAIN_READING_FAMILIES` map (§2a), independent of the dossier slice bundle.
  That half of the fix is sound as written.

## Not resolving this myself (PAR-R-7)

Two defensible remediations exist and the choice between them isn't mine to presume:
(a) extend the spec's scope to generate/wire `health_*`/`relationship_*` dossier slice bundles, or
(b) add a null-case disclosure to `attachDomainCompleteness` itself (an honest "no precompiled
slice for this domain yet" flag, rather than silent omission) — which may in fact be the more
correct minimal fix given F-31's claim is fundamentally about disclosure, not about requiring the
full slice to exist. Flagging both options; not choosing.

## Disposition

Not writing a competing F-31/SPEC.md. Not adopting `lanes/F-14/SPEC.md` as a silent close for F-31
until this gap is addressed (either the spec's scope grows, or F-31 is split into a
wiring-closed-here + a residual "domain_completeness needs a null-case disclosure or a slice
bundle" follow-up). Awaiting S2/conductor decision.
