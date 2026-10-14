<!-- Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T220409Z-b4-define-kv3-schema-1/DEFINE_KV3-SCHEMA-1.md -->
<!-- Original sha256: 241e9ba26b646d428a4314de155436e1610e18fe119a966d75dab976e4a3d203; date: 2026-10-14 -->
# KV3-SCHEMA-1 — read-only acceptance study

Keys: existing paths/1-based lines; checks proposed.

| Key | Path |
|---|---|
| M | 00_ARCHITECTURE/control/kalayantra/plan_model.json |
| P | 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md |
| O | 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md |
| S | 00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json |
| J | /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T164123Z-b4-packetplan/ITEMS.json |
| OP | /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T164123Z-b4-packetplan/OPEN_POINTS.md |
| R | /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/lane2/B4_RULINGS.md |
| D | /Users/Dev/kalayantra/run/DECISIONS.jsonl |
| C | /Users/Dev/worktrees.noindex/madhav/claude/campaign-coordination/00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md |
| T | platform-mcp/src/tools/retrieval/register_gochara_windows.ts |
| A | platform/scripts/governance/asset_declarations.json |
| V | platform/python-sidecar/brahmagyan/verification_vocab.py |
| F | 00_ARCHITECTURE/briefs/kalayantra/fleet (directory; append suffixes below) |
| H | platform/python-sidecar/tests/l3/kala_db/conftest.py |
| B | /Users/Dev/kalayantra/run/schema/prod_schema.sql |
| W | /Users/Dev/kalayantra/wt/k2/platform/python-sidecar/brahmagyan/l0_gochara_citation_resolution.py |

## 1. WHAT THE ITEM IS

1. Add the stored citation-density tier column to bg_gochara_citation_resolution additively (M:8085,8112).
2. Produce allocated SQL in platform/migrations/ and platform/python-sidecar/tests/l3/kala_db/certification/test_citation_resolution_tier_schema.py (M:8103-8105).
3. Supply K-CERT's prerequisite; K-CERT later changes the served select and proves Dens.served (M:7912,7925-7932; P:735-737).
4. K produces code; Opus schema-prerequisite packet, SS coordination, 24-hour objection fallback to Suvarṇa (M:8116-8118; O:61-67).
5. Depends on B-7 launch acceptance, K0-SV alignment and the recorded tier contract (M:8087-8089,8114).

## 2. DECIDED

col is Q1's future identifier. Use disposable DB; executor supplies production proof (F/cards/KARAKA.md:24). Expand F/placeholders.

| Obligation | Source | Exact measurement | Real input / future fixture |
|---|---|---|---|
| Dual schema, prerequisite kind, Opus | P:538-540; O:61-64; F/schemas/packet.json:141-148 | python3 -B F/kypacket.py check PACKET --repo REPO; python3 -B F/kyroute.py packet --packet PACKET --model MODEL --repo REPO; compare intended_schema to approved contract | Future packet, M, S:617-626, contract |
| Column absent on admitted base; same presence test red before, green after | M:8108 | SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='bg_gochara_citation_resolution' AND column_name=:col; 0 before/1 after; capture actual failing assertion | Owned DB test; admitted table fixture from a hash-valid replacement/restored seed (blocker below) |
| Every existing column/row retained | M:8108; CLAUDE.md:114 | Old catalog unchanged; old nine-column rows EXCEPT ALL post projection, and reverse, empty | Nonempty resolved/unresolved fixture; nine old columns S:617-626 |
| Idempotent migration | M:8109 | Apply SQL twice; success + equal catalog/rows/tier values; error or mutation fails | Future allocated migration, same disposable fixture |
| Unrecorded tiers NULL; no invented values | M:8110; D:146; CLAUDE.md:135,137,141 | SELECT citation_string,chunk_id FROM bg_gochara_citation_resolution WHERE col IS NOT NULL excludes every unevidenced key; resolved→tier mutant fails | Both status labels T:757-758; reason/evidence representation awaits Q2 |
| Additive reader/writer compatibility until K-CERT | M:8113 | Execute unchanged T:799-801 SELECT before/after, compare results; old explicit-column INSERT succeeds; old PK/constraints remain | T:799-815; platform/supabase/migrations/565_bg_gochara_citation_resolution.sql:65-77,97-99; later producer W:179-185 |
| Allocate number at job start; protected classifier/approval; no applied-SQL edits | P:338-342,528,535-543; M:8112; CLAUDE.md:114 | Allocator reservation; actual diff classifier/protected-list pin; ledger SQL digest. Protected: owner approval + workflow outcome | Allocated SQL, slot ledger, platform/scripts/kala_protected_migrations.txt; P:749-756 |
| Independent exact-head + post-deploy squash review; verified application | M:8118,123-124; F/cards/PARIKSAKA.md:21 | Independent head verdict; successful deployed source contains squash; _migrations_applied filename/sha256 + catalog definition match; post_deploy verdict at squash | Head→squash mapping/readback; S:45 ledger |
| Tests/precheck actually run; skipped DB proof insufficient | P:551; F/cards/KARAKA.md:16; H:62-83 | KALA_REQUIRE_DB=1 python3 -B -m pytest OWNED_TEST -q -p no:cacheprovider --basetemp=ABS_JOB_SCRATCH/pytest; guarded DSN supplied by launcher. KY_ITEM=KV3-SCHEMA-1 bash ABS_FLEET/precheck.sh --item | Owned test; H:85-100 cleanup; F/precheck.sh:94-115; .github/workflows/ci.yml:336-341 collection |
| Coordination/fallback and prerequisite availability | O:61-64; M:8087-8089; P:330-335 | Check dated §6 notice/24h response; accepted B-7; K0-SV accepted head/verified squash in base | C:9302 is an earlier request, not the intended contract; M:1245-1286,1894-1946 |

branch_merged alone cannot earn done; require M:8118's review/readback (M:8093-8094; CLAUDE.md:141).

S:617-626 and B:9345-9356 have nine columns/no tier. Current dump hash mismatches S:17-19; not an admitted fixture. Receipt is historical, not live/slot proof (S:9-15).

Real fixture sources: platform/supabase/migrations/565_bg_gochara_citation_resolution.sql:65-77 (DDL); platform/supabase/migrations/630_nirmana_l0_wave1_correctness_contract.sql:262-270 (false-resolution repair); platform/supabase/migrations/631_nirmana_l0_gochara_citation_chunk_repair.sql:20-38 (14 historical rows, 1 resolved/13 unresolved, eight-value digest). Existing platform/python-sidecar/services/gochara_v3/mechanisms/tests/test_mr25_citation_verse_refs.py:13-27 is static, insufficient for DDL application/authority.

J:3355-3378 read; absent test is output. R:12 accepts OP:163-175 test policy; no new mandatory feature fields. Checker lacks prerequisite test-blob checks (F/kypacket.py:421-452); green ≠ executed tests. No control-plane fix (R:9).

## 3. UNDECIDED

1. **What exact column name, type, allowed values and constraints must be added?** M:8114 supplies none; O:61-67 changes authorship, not this contract; S:617-626 has no tier. Options: (a) nullable TEXT verification_pass_status, no value default, custodian-approved CHECK subset of V's vocabulary; (b) nullable custom citation-tier domain/name with reviewed density_tier_columns declaration; (c) custodian supplies its own DDL. **(I) INTERPRETATION / recommendation:** (a), ratified subset only. Cost: settle vocabulary; risk: computation tiers may misdescribe passage correspondence. Standard name recognized by platform/scripts/governance/asset_census.py:197; V:40-53,71-107 forbids false verification.

2. **What evidence may populate tiers, and where is the custodian's NULL reason recorded?** M:8110 requires NULL/reason but M:8114 leaves backfill blank; A:2727-2733 says unverified transcription; D:146 forbids resolution→verification. Options: (a) no backfill, all existing rows NULL, reason in pinned contract and column COMMENT; (b) backfill only enumerated keys with recorded row/content and detector bindings; (c) separate reason column for row-specific explanations. **(I) INTERPRETATION / recommendation:** (a), preserve notes. Cost: later population is separate work; risk: common reason may need row detail. W:179-185 deletes/reinserts without tier: future nonnull backfill needs rebuild-survival contract outside M:8103-8105.

3. **What exact density mapping does K-CERT consume, and who records it within the separate scopes?** M:8114 leaves mapping blank; T:1504-1517 layers window calibration_state; A:2681-2778 has no citation density_tier_columns; C:9302 requests mapping. Options: (a) custodian contract defines stored tier→verification/confidence/unknown, leaving TS/declaration/census implementation to separately owned consumers; (b) broaden this item with reviewed model/write-set changes. **(I) INTERPRETATION / recommendation:** (a), NULL unknown; positive claims need detector evidence (CLAUDE.md:141; V:40-46). Cost: later consumer work; risk: structural PASS mistaken for verified content. Scanner recognition exists (platform/scripts/governance/asset_census.py:197,1383-1438); asset mapping does not. K-CERT owns census PASS (M:7931-7932).

4. **Which verified schema/readback receipt must consumers receive?** P:539-540 requires it; M:8103-8105 owns SQL/test only. S:16-36 binds seed files, not deployment/row preservation. F/kypacket.py:401-413 only resolves ID; shared template awaits pilot (R:13). Options: (a) existing schema/ledger/registry export plus independent deployment/migration and old-row comparison evidence; (b) separate typed prerequisite receipt/admission contract. **(I) INTERPRETATION / recommendation:** (a), cockpit freezes fields/producer/location/ownership. Cost: real readback/export; risk: schema digest mistaken for data preservation.

## 4. BLOCKED BY

- **Drafting:** missing Q1-Q3 contract/coordination: M:8114, D:146 insufficient_evidence, C:9302 request. Authorship exception supplies no semantics (O:61-67); R:15 holds custody-unsettled packets.
- **Hash-valid admitted seed, before fixture/admission:** fresh SHA-256 measurement of S's seed_directory files (S:14,17-27) found prod_schema.sql recorded a9d843652016dd15d6193a147ae2d02b348099687d5681e460266d75f4507bd1, observed f82aa93c60c397eb3e44c5317a1721bfa75db6a9fd32c551b5c5f89796804120. migrations_applied_data.sql also mismatches; asset_registry_data.sql matches. Restore receipt-bound bytes or admit a newly measured receipt; never rewrite a hash to pretend acceptance.
- **Admission/run:** ls found /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json absent. Required P:587-599; post-ruling drafts allowed, no fake pins (R:14).
- **Dependency proof before run:** M:8087-8089 edges remain. Historical B-7 acceptance exists (/Users/Dev/kalayantra/run/LAUNCH_ACCEPTED.json:3-5); K0-SV agreement still requires reviewed/merged PR (00_ARCHITECTURE/briefs/l3_families/contracts/DASHA_TABLE_CONTRACT_v1_0.md:4,90). Neither alone proves final v3 acceptance/base containment (P:595-599,330-335); do not label them missing.
- **Final packet:** Q4/shared template pending (R:13); deployed output follows implementation, not a missing source.

## 5. BUILD SHAPE

**(I) INTERPRETATION / sizing:** SQL ~30-80 lines; owned test ~250-400, inline faithful fixture (M:8103-8105), 10-15 cases covering table checks/mutants above. Comparator inside test; optional proposed F/accept/citation_resolution_schema.py (~150-250) needs extra scope. J-0c's offline pattern cannot measure DDL (F/accept/j0_disposition.py:2; F/tests/test_accept_j0_disposition.py:45-56).

Reuse accepted installed kypacket.py (F/kypacket.py:8-48) and local_db.sh (F/local_db.sh:6-24,35-46); H:62-100 fixture/skip-fails. Authoring offline; execution needs loopback PostgreSQL, psycopg, DB/migration process tools (F/precheck.sh:110-115). No item-test external network; full CI downloads ephemeris (.github/workflows/ci.yml:323-341). Executor supplies production evidence.

**(I) INTERPRETATION — preservation:** compare all nine values including timestamp/note, stronger than old integrity seal; no writer rebuild in this check (M:8108,8113; S:617-626). Study created no DB/copy/repository change; job report/result retained for cockpit.

## 6. READINESS

BLOCKED — Q1-Q3 recorded contract/SS coordination, Q4 receipt contract, mismatching seed; release receipt and current dependency-base proof before admission/run. Study complete; no acceptance claimed.
