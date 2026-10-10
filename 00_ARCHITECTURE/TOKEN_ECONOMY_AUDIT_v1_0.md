---
artifact: TOKEN_ECONOMY_AUDIT_v1_0.md
status: DRAFT — PENDING NATIVE REVIEW
version: 1.0
authored_by: Claude Code (Opus 5.5), token-economy audit session, worktree audit/token-economy
authored_on: 2026-10-11
audience: native (Abhisek Mohanty); campaign conductors (KĀLA-YANTRA, Suvarṇa, Pravāha) as secondary readers
disposition: >
  Phase A findings report of the token-economy campaign. Read-only audit — nothing
  in code, config, settings, fleets or production was changed. Companion:
  00_ARCHITECTURE/TOKEN_ECONOMY_PLAN_v1_0.md (the plan, gated on native approval).
evidence_base:
  - ~/.claude/projects/**/*.jsonl (2,742 Madhav-related transcripts incl. subagents)
  - ~/.codex/sessions/**/rollout-*.jsonl (6,516 scanned; 5,431 Madhav-related)
  - /Users/Dev/kalayantra/logs/<lane>.<cycle>.log (4,082 KĀLA-YANTRA cycle logs)
  - git branch campaign/nirmana-autonomous (spend_meter.py, PRICING.json, CAMPAIGN_STATE.json)
  - repo origin/main @ af9e6b8c6 (runtime call sites, MCP serve layer, settings, prompts)
method_note: >
  All usage figures come from token_baseline.py (committed in Phase B as
  scripts/token_economy/token_baseline.py; Phase-A copy at
  /Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/token_baseline.py),
  run 2026-10-10T20:00Z. Days are UTC. Claude rows are de-duplicated globally on
  (message.id, requestId) keeping the per-class max. Sizes marked "tik" use tiktoken
  cl100k_base as a stand-in tokenizer (Claude's tokenizer is not installed); "EST"
  means chars/4. Estimates are labelled as such and give their basis.
---

# Token Economy Audit — Madhav / MARSYS-JIS

## 0. Summary

1. **Volume.** In the 30 days 2026-09-11 → 10-10, Madhav work consumed **63.2 B tokens**
   (four classes in §2 B-1), **96.7 % of them cache reads**. Claude carried 51.0 B (81 %),
   Codex 12.1 B (19 %).
2. **Where it goes.** Interactive Claude sessions and their subagents are 58.5 B of the
   63.2 B (93 %) over 30 days. Three Suvarṇa coordinator sessions alone account for
   33.9 B (54 %). The KĀLA-YANTRA fleet only started on 2026-10-06; since 10-07 it
   has been 18–34 % of daily volume (§2 B-12).
3. **Why it is so large.** Context per Claude API call: median 250,926 tokens, p90
   724,964. Every call re-reads its whole context. Main-thread calls average ≈ 557 K
   context tokens and subagent calls ≈ 256 K (derived in F-1). Fixed start-up context
   (system prompt, tools, skills list, CLAUDE.md, first prompt) is ≈ 62 K for a
   general-purpose subagent and ≈ 91.5 K for a main session. Re-reading it accounts
   for 24 % of subagent and 16 % of main-session context tokens.
4. **The fleet.** About half of KĀLA-YANTRA's gross tokens go to cycles that find no work.
   Only 171 of 2,554 builder cycles made an edit.
5. **The existing spend meter is NOT trustworthy.** It overcounts 1.5–2.4× by
   class, misses whole folder families, has no Codex or KĀLA-YANTRA reader, and its
   running ceiling check is an LLM prompt (§3).
6. **Local-builder premise.** The machine is an **Apple M5 Pro with 64 GB**, not the
   M5 Max with 128 GB the plan assumes. No local model is downloaded. The fleet
   supervisor cannot launch a local agent today (§7).
7. **Product runtime** runs mainly on Gemini, billed per use and outside the
   subscriptions. The Claude-path adapter ignores its cache configuration, the Gemini
   explicit cache is hard-disabled, and several cache and reasoning telemetry columns
   are written as constant 0 (§6).

## 1. The token unit

The same day of usage has been quoted as 4.4 M, 31.8 M and 1.195 B tokens. Those
figures differ only because each counts different usage classes. This audit always
reports four classes plus their sum:

| class | Claude source field | Codex source field |
|---|---|---|
| input | `usage.input_tokens` (uncached) | `input_tokens − cached_input_tokens` |
| output | `usage.output_tokens` | `output_tokens` (includes reasoning; reasoning shown separately) |
| cache_creation | `usage.cache_creation_input_tokens` | `cache_write_input_tokens` (0 in every observed rollout) |
| cache_read | `usage.cache_read_input_tokens` | `cached_input_tokens` |

**Codex "tokens used" footer.** The number Codex prints at the end of each run is
uncached input plus output only. The four-class gross is ≈ 7.5× larger on the fleet
(3,990 logs joined to rollouts, workflow sweep `agg.py`). Footer figures are labelled
"footer" wherever they appear.

**Subscription quota is not tokens.** How Claude Max weights each class against its
limits is **NOT MEASURED**: there is no local record of it. Codex reports its own
quota: the weekly window was **33 % used** at the last rollout, and the credit balance
was 59,046.75 (rollout `rate_limits`, 2026-10-10). The workflow sweep observed the
balance fall from 62,500 to 59,047 over 10-06 → 10-10.

## 2. Baseline (four classes, every figure from token_baseline.py)

Commands: `token_baseline.py --since 2026-09-11 --until 2026-10-10 --waste` (30 d) and
`--since 2026-10-04 --until 2026-10-10 --waste` (7 d).

**Retention limit.** Claude Code keeps transcripts for 30 days (`cleanupPeriodDays` is
unset in `~/.claude/settings.json`). The earliest Claude record is 2026-09-11, so
there is no Claude history before that. Codex history goes back further.

**B-1. Grand totals**

| window | input | output | cache_creation | cache_read | total |
|---|--:|--:|--:|--:|--:|
| 30 d (2026-09-11 → 10-10) | 576,048,096 | 197,122,496 | 1,331,704,650 | 61,100,470,850 | 63,205,346,092 |
| 7 d (2026-10-04 → 10-10) | 360,928,035 | 75,177,546 | 589,462,720 | 23,384,920,567 | 24,410,488,868 |

cache_read share: 30 d 96.7%, 7 d 95.8%. Output share: 30 d 0.31%, 7 d 0.31%. Codex reasoning tokens (a subset of output): 30 d 13,574,894.

**B-2. By provider (30 d)**

| provider | input | output | cache_creation | cache_read | total |
|---|--:|--:|--:|--:|--:|
| claude | 427,634 | 153,351,463 | 1,329,078,796 | 49,526,109,714 | 51,008,967,607 |
| codex | 575,606,408 | 43,170,038 | 0 | 11,526,829,184 | 12,145,605,630 |
| claude(fleet-stream-json) | 14,054 | 600,995 | 2,625,854 | 47,531,952 | 50,772,855 |

**B-3. By ISO week (30-d window; W37 holds only 09-11 → 09-13)**

| week | input | output | cache_creation | cache_read | total |
|---|--:|--:|--:|--:|--:|
| 2026-W37 | 82,140,529 | 10,221,477 | 44,416,413 | 2,906,876,725 | 3,043,655,144 |
| 2026-W38 | 40,477,067 | 3,356,152 | 7,071,479 | 1,551,478,410 | 1,602,383,108 |
| 2026-W39 | 51,170,145 | 26,383,390 | 140,745,013 | 8,456,483,006 | 8,674,781,554 |
| 2026-W40 | 47,201,853 | 87,971,756 | 598,278,724 | 27,629,772,000 | 28,363,224,333 |
| 2026-W41 | 355,058,502 | 69,189,721 | 541,193,021 | 20,555,860,709 | 21,521,301,953 |

**B-4. By day (last 10 days)**

| day (UTC) | input | output | cache_creation | cache_read | total |
|---|--:|--:|--:|--:|--:|
| 2026-10-01 | 3,701,283 | 17,706,998 | 121,683,409 | 5,790,744,444 | 5,933,836,134 |
| 2026-10-02 | 5,334,233 | 24,001,036 | 157,746,326 | 7,945,775,060 | 8,132,856,655 |
| 2026-10-03 | 13,750,423 | 22,839,863 | 184,019,425 | 6,928,937,659 | 7,149,547,370 |
| 2026-10-04 | 5,856,805 | 5,985,552 | 48,262,825 | 2,828,241,486 | 2,888,346,668 |
| 2026-10-05 | 15,486,254 | 17,315,793 | 165,351,322 | 6,282,506,398 | 6,480,659,767 |
| 2026-10-06 | 19,907,557 | 8,118,262 | 69,757,291 | 2,405,415,404 | 2,503,198,514 |
| 2026-10-07 | 102,242,158 | 13,211,348 | 115,934,166 | 3,557,136,383 | 3,788,524,055 |
| 2026-10-08 | 89,450,857 | 8,843,170 | 78,772,179 | 2,461,396,955 | 2,638,463,161 |
| 2026-10-09 | 82,740,813 | 10,546,948 | 69,608,406 | 3,024,066,934 | 3,186,963,101 |
| 2026-10-10 | 45,230,863 | 11,154,200 | 41,769,657 | 2,825,338,635 | 2,923,493,355 |

**B-5. By model (30 d, top 14)**

| model (effort) | input | output | cache_creation | cache_read | total |
|---|--:|--:|--:|--:|--:|
| claude-sonnet-5-5 | 220,032 | 104,636,462 | 960,194,284 | 34,523,431,197 | 35,588,481,975 |
| claude-opus-5-5 | 46,816 | 18,125,223 | 134,590,551 | 8,016,659,346 | 8,169,421,936 |
| gpt-6.1-sol (high) | 242,936,600 | 17,734,354 | 0 | 4,167,288,576 | 4,427,959,530 |
| claude-sonnet-5 | 22,908 | 10,716,264 | 65,371,178 | 3,823,411,813 | 3,899,522,163 |
| gpt-5.6-sol (high) | 62,010,045 | 5,464,965 | 0 | 2,093,343,744 | 2,160,818,754 |
| claude-fable-5-1 | 142,161 | 14,233,583 | 120,528,949 | 1,745,944,564 | 1,880,849,257 |
| gpt-5.6-terra (high) | 39,822,060 | 4,272,326 | 0 | 1,771,724,160 | 1,815,818,546 |
| gpt-6-sol (high) | 66,723,812 | 4,847,876 | 0 | 1,677,039,232 | 1,748,610,920 |
| claude-opus-5 | 9,440 | 6,211,759 | 50,347,262 | 1,462,310,443 | 1,518,878,904 |
| gpt-5.6-terra (medium) | 76,410,081 | 4,185,077 | 0 | 629,349,632 | 709,944,790 |
| gpt-6-astra (max) | 36,848,018 | 3,477,049 | 0 | 615,985,792 | 656,310,859 |
| gpt-6-astra (xhigh) | 33,500,099 | 2,464,538 | 0 | 388,357,888 | 424,322,525 |
| gpt-6-astra (high) | 6,811,958 | 393,054 | 0 | 81,285,248 | 88,490,260 |
| gpt-6-astra (ultra) | 2,541,338 | 169,982 | 0 | 48,114,048 | 50,825,368 |

**B-6. By role (30 d)**

| role | input | output | cache_creation | cache_read | total |
|---|--:|--:|--:|--:|--:|
| interactive | 246,764,475 | 69,942,205 | 271,254,831 | 31,439,062,933 | 32,027,024,444 |
| subagent | 280,620 | 102,582,618 | 1,033,870,150 | 25,335,619,395 | 26,472,352,783 |
| KARAKA | 175,338,213 | 10,834,419 | 873,326 | 1,711,904,730 | 1,898,950,688 |
| interactive(kalayantra-root) | 13,515 | 3,016,838 | 23,299,564 | 984,732,480 | 1,011,062,397 |
| PARIKSAKA | 94,695,590 | 6,227,887 | 1,752,528 | 843,300,054 | 945,976,059 |
| SUTRADHARA | 22,621,531 | 2,551,906 | 0 | 481,779,840 | 506,953,277 |
| ADHIKARIN | 35,432,291 | 1,789,522 | 0 | 268,080,896 | 305,302,709 |
| interactive(kalayantra-campaign) | 901,861 | 177,101 | 654,251 | 35,990,522 | 37,723,735 |

**B-7. By workspace / campaign (30 d, top 15)**

| workspace | input | output | cache_creation | cache_read | total |
|---|--:|--:|--:|--:|--:|
| shared-checkout | 80,076,727 | 58,431,363 | 339,157,819 | 24,448,915,489 | 24,926,581,398 |
| codex-wt/a4d5 | 54,329,284 | 5,357,417 | 0 | 2,120,759,808 | 2,180,446,509 |
| /Users/Dev/pravaha/run | 11,203 | 2,780,186 | 16,573,841 | 1,997,396,789 | 2,016,762,019 |
| codex-wt/purna-followup-v1 | 7,644 | 3,332,219 | 18,929,440 | 1,764,996,418 | 1,787,265,721 |
| /Users/Dev/suvarna-exec | 13,756 | 6,108,745 | 39,550,104 | 1,615,824,702 | 1,661,497,307 |
| /Users/Dev/suvarna-integ | 9,874 | 3,091,848 | 80,522,700 | 1,080,560,186 | 1,164,184,608 |
| codex-wt/a4c6 | 30,740,364 | 1,778,777 | 0 | 988,723,712 | 1,021,242,853 |
| kalayantra/root | 13,515 | 3,016,838 | 23,299,564 | 984,732,480 | 1,011,062,397 |
| madhav-nikasha | 440,426 | 3,187,022 | 25,196,539 | 959,905,855 | 988,729,842 |
| codex-wt/jataka-chart-workspace | 4,202 | 1,602,726 | 5,072,995 | 973,289,888 | 979,969,811 |
| /Users/Dev/suvarna-engine-lane-final2 | 5,622 | 2,616,225 | 33,963,962 | 935,144,707 | 971,730,516 |
| /Users/Dev/suvarna-engine-lane-denssrv | 3,234 | 1,720,450 | 24,721,321 | 768,310,372 | 794,755,377 |
| /Users/Dev/suvarna-engine-lane-stack-pr | 4,010 | 1,499,577 | 22,377,961 | 736,749,970 | 760,631,518 |
| claude-scratchpad | 32,990,272 | 3,228,141 | 705,371 | 556,449,241 | 593,373,025 |
| /Users/Dev/suvarna-engine-lane-resid | 2,552 | 1,275,195 | 39,283,223 | 546,019,014 | 586,579,984 |

**B-8. Top 10 sessions (30 d)**

| session | input | output | cache_creation | cache_read | total | note |
|---|--:|--:|--:|--:|--:|---|
| claude:8201ea38-2c77-469c-afac-0d364a9fae85 | 130,354 | 56,613,280 | 465,572,021 | 17,400,492,689 | 17,922,808,344 | shared-checkout; turns=1521; API calls=64338; subagent transcripts=640; first day 2026-09-27 |
| claude:b2d50a3a-3080-4e49-a7c6-2a07e6e6a39a | 63,706 | 32,855,015 | 448,570,588 | 10,783,733,911 | 11,265,223,220 | shared-checkout; turns=692; API calls=31730; subagent transcripts=311; first day 2026-10-01 |
| claude:e1effe6d-cae4-4643-b098-d49444a83a68 | 32,562 | 13,018,234 | 100,553,821 | 4,591,704,863 | 4,705,309,480 | shared-checkout; turns=492; API calls=12133; subagent transcripts=103; first day 2026-09-25 |
| claude:b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095 | 13,568 | 8,059,438 | 19,602,401 | 3,347,155,714 | 3,374,831,121 | shared-checkout; turns=12; API calls=6788; subagent transcripts=7; first day 2026-10-01 |
| claude:aff8845d-ece4-488f-ad50-c6d79df07b47 | 11,024 | 6,343,489 | 17,352,351 | 2,726,329,287 | 2,750,036,151 | shared-checkout; turns=21; API calls=5514; subagent transcripts=2; first day 2026-10-01 |
| codex:01a09ba9-3320-7b13-aae1-a212d02ab44e | 49,571,261 | 4,834,280 | 0 | 1,965,865,472 | 2,020,271,013 | codex-wt/a4d5; turns=None; API calls=None; subagent transcripts=0; first day 2026-09-13 |
| claude:8ce6ffaa-67aa-41a8-a3dd-cd26ebae1545 | 11,593 | 2,789,114 | 16,905,093 | 1,988,301,156 | 2,008,006,956 | /Users/Dev/pravaha/run; turns=1035; API calls=3903; subagent transcripts=4; first day 2026-09-28 |
| codex:01a0df60-601e-74f0-925a-ca0e755f690c | 36,287,003 | 3,970,809 | 0 | 1,775,700,352 | 1,815,958,164 | shared-checkout; turns=None; API calls=None; subagent transcripts=0; first day 2026-09-26 |
| claude:187da22f-dfbc-4545-a93d-21eabb271410 | 7,118 | 2,908,729 | 12,396,033 | 1,577,858,897 | 1,593,170,777 | codex-wt/purna-followup-v1; turns=34; API calls=3546; subagent transcripts=25; first day 2026-09-27 |
| claude:96e50445-aaec-49c3-b206-308252214a42 | 16,005 | 3,721,316 | 29,410,377 | 1,167,062,984 | 1,200,210,682 | kalayantra/root; turns=236; API calls=4392; subagent transcripts=51; first day 2026-10-06 |

**B-9. Shape (30 d, Claude, de-duplicated API calls)**

- Human turns per session: {'n': 236, 'p50': 1, 'p90': 12, 'max': 1521} (n counts main transcripts; headless/resumed transcripts have 0-1 turns).
- Context per API call (input + cache_creation + cache_read): {p50: 250,926, p90: 724,964, p99: 940,341, mean: 333,018} over 152,711 calls.
- Output per API call: p50 483, p90 2127.

**B-10. KĀLA-YANTRA cycle logs, 2026-10-06 → 10-10 (Codex exec footer; see unit note)**

| role | cycles | IDLE-OK cycles | footer 'tokens used' | of which idle | idle share | models (cycle count) |
|---|--:|--:|--:|--:|--:|---|
| ADHIKARIN | 343 | 257 | 29,423,373 | 20,798,776 | 71% | gpt-6.1-sol (high): 267, gpt-6-astra (xhigh): 76 |
| KARAKA | 2585 | 1321 | 179,969,612 | 85,726,274 | 48% | gpt-6.1-sol (high): 1300, gpt-5.6-terra (medium): 1197, claude-opus-5-5 (?): 27, gpt-6-sol (high): 60, claude-sonnet-4-6 (?): 1 |
| PARIKSAKA | 955 | 663 | 84,957,077 | 55,557,958 | 65% | gpt-6.1-sol (high): 794, gpt-6-astra (xhigh): 140, claude-fable-5-1 (?): 21 |
| SUTRADHARA | 199 | 17 | 18,869,826 | 1,580,440 | 8% | gpt-6-sol (high): 199 |

**B-11. Tool-result volume by tool (all retained Claude transcripts ≈ 30 d)**

| tool | results | chars | est tokens (chars/4) | largest (chars) |
|---|--:|--:|--:|--:|
| Bash | 146,458 | 366,496,582 | 91,624,145 | 29,885 |
| Read | 6,665 | 97,099,384 | 24,274,846 | 165,693 |
| mcp__postgres__query | 1,952 | 2,778,375 | 694,593 | 47,033 |
| mcp__marsys-jis-direct__search_classical_texts | 148 | 2,720,873 | 680,218 | 48,585 |
| Agent | 1,497 | 1,971,159 | 492,789 | 44,666 |
| SendMessage | 6,096 | 1,948,386 | 487,096 | 682 |
| Write | 3,753 | 759,856 | 189,964 | 529 |
| Edit | 2,772 | 643,062 | 160,765 | 129,814 |
| Monitor | 1,862 | 605,990 | 151,497 | 1,578 |
| mcp__marsys-jis-direct__read_classical_text | 41 | 569,508 | 142,377 | 49,979 |
| mcp__marsys-jis-direct__read_chapter | 241 | 511,212 | 127,803 | 4,300 |
| mcp__plugin_chrome-devtools-mcp_chrome-devtools__take_screenshot | 6 | 508,210 | 127,052 | 160,888 |

Redundant re-reads: 1,653 of 6,642 Read calls (25%) were repeat reads of a file already read in the same transcript (415 transcripts). Compactions: 119 events in 36 transcripts.

**B-12. Fleet share of daily volume.** Source: Codex rollouts with cwd under
`/Users/Dev/kalayantra/wt/*`, against the B-4 daily totals (script `role_day.py`).

| day | all Madhav | KĀLA-YANTRA fleet (gross, 4 classes) | share |
|---|--:|--:|--:|
| 10-06 | 2,503,198,514 | 143,423,471 | 6 % |
| 10-07 | 3,788,524,055 | 1,288,602,916 | 34 % |
| 10-08 | 2,638,463,161 | 846,885,917 | 32 % |
| 10-09 | 3,186,963,101 | 804,281,962 | 25 % |
| 10-10 | 2,923,493,355 | 523,950,230 | 18 % |

**B-13. Relative weight (estimate).** Raw tokens over-weight cache reads, so the
classes were also weighted by Anthropic list-price ratios against base input: cache
read 0.1×, cache write 1.25×, output 5×. These ratios are used **only to rank where
cost sits**. They are not a quota measurement.
- Claude (30 d): cache_read 67 %, cache_creation 23 %, output 10 %, input ≈ 0 %.
- Codex (30 d): cache_read 59 %, input 30 %, output 11 %.
- Fleet lanes: uncached input is 44–50 % of the weight for KĀRAKA, PARĪKṢAKA and
  ADHIKĀRIN. That is the cost of starting every cycle as a fresh process.

## 3. Is the spend meter trustworthy? — **NO**

The meter is `00_ARCHITECTURE/autonomy/bin/spend_meter.py`. Only one version exists
(commit 29cfdfbc2, 2026-08-23), it lives only on `campaign/nirmana-autonomous`, and it
is not on main. It always appends to `SPEND.jsonl` (`:212-213`) and has no read-only
mode, so its file discovery was re-run separately, read-only.

| check | result | evidence |
|---|---|---|
| four classes parsed | top level yes. The 5-minute and 1-hour cache-write split is ignored, and PRICING.json has one `cache_creation` rate although the two are priced differently. | `:24-29, 173-176`. Its files hold 834 M 1-hour and 1.94 B 5-minute writes. |
| de-duplication | **none**. Overcount by class: input 2.36×, output 1.50×, cache_creation 2.03×, cache_read 1.93×. | `scan_file :85-92`. Example: `aff8845d…jsonl` has 10,421 usage lines but 5,419 unique keys. |
| dedup subtlety | Repeated lines are **not** identical: the first line of 79,478 of 154,950 groups carries a partial output count. Keeping the first line undercounts output (61.3 M against the true 155.0 M). Keep the per-class max. 3,755 keys appear in more than one file (resumed sessions), so dedup must be global. | probe scripts; the baseline script implements both |
| subagents | `subagents/*.jsonl` yes. **557 workflow-agent files are missed**: they sit one level deeper than its globs. | `:45` |
| windowing | The earlier `campaign_started_ts` defect is fixed (`nirmana-up.sh:40-51`). But it windows **per file by first timestamp**, so resumed sessions are dropped or mis-windowed. | `:161-165` |
| ceiling check | Preflight now parses integer ceilings, at launch only. `tokens_per_rung` is not measured. **While running, the ceiling is enforced only by an LLM prompt.** | `preflight.sh ~123-127, ~159`; `prompts/monitor.md:78-90` |
| coverage | The case-sensitive `*Madhav*` glob misses `-Users-Dev-nirmana-s-*` (the fleet's own run, 675 files) and `-Users-Dev-madhav-l3-*`. Missed volume: 10.2 M output and 1.12 B cache read. It also over-includes the native's interactive sessions. | `:39` |
| Codex / KĀLA-YANTRA | **not covered**. KĀLA-YANTRA has no spend meter at all. Its Claude lanes run with `--no-session-persistence`, so no transcript exists to meter. | `claude_cycle.py:13`; `kalayantra_fleet.sh:156-157` (backs off only on a quota error) |

**§N.8 consequence.** No code path computes the in-run ceiling, so any "within
ceiling" status it reports is **null, not green**. The baseline script replaces the
meter for measurement (plan item W0-1).

## 4. Findings, ranked by token impact

Impact is expressed against the 30-day baseline unless a different window is stated.

### F-1 Long-lived interactive coordinator sessions (largest lever) — 30 d ≈ 33.9 B in the top 3 sessions

| session | role / workspace | span | turns | API calls | subagent transcripts | total tokens | subagent share |
|---|---|---|--:|--:|--:|--:|--:|
| 8201ea38 | Suvarṇa exec (shared checkout → suvarna-exec) | 09-27 → 10-10 | 1,521 | 64,338 | 640 | 17.9 B | 76 % |
| b2d50a3a | Suvarṇa engine (5 lanes) | 10-01 → 10-10 | 692 | 31,730 | 311 | 11.2 B | 76 % |
| e1effe6d | Suvarṇa plan (governance scripts) | 09-25 → 10-10 | 492 | 12,133 | 103 | 4.7 B | 39 % |

Sources: B-8 and `top_sessions.py`. The models are Sonnet 5.5 for the first two and
Opus 5.5 for the third. Subagent types were mainly `general-purpose`, then
`code-reviewer`.

- **Main-thread calls average ≈ 557 K context tokens.** Main context tokens were
  27.2 B over 48,825 main calls (152,711 de-duplicated calls minus 103,886 subagent
  calls). Sources: `main_first.py`, `subagent_profile.py`.
- **Context never resets.** Coordinators run for 10–16 days. Compaction happened only
  119 times in 36 transcripts (B-11), so the context fills to the 1 M window and
  stays near it.
- **Subagents are long too:** `general-purpose` median 59 calls, p90 169; peak context
  median 233 K, p90 496 K. That is 1,068 runs and 24.7 B context tokens in 30 days.
- **Lever:** cap session lifetime and size. Hand off to a fresh session at a context
  threshold, and keep subagent tasks smaller. This is a working-practice change,
  routed as an owner decision.

### F-2 Fixed start-up context re-read on every call — ≈ 10.9 B / 30 d

These are measured lower bounds: calls × first-call context. The first-call figure
includes the opening task prompt.

| scope | first-call context | standing reads | share of context tokens |
|---|---|--:|--:|
| subagents (1,915 runs, 103,886 calls) | p50 62,522 (`general-purpose`), 29,783 (`Explore`) | 6,479,383,850 | 24.3 % |
| main sessions (233) | p10 / p50 / p90 77,461 / 91,506 / 92,534 | ≈ 4.4 B (16.2 % of 27,224,811,807) | 16.2 % |

What the start-up context contains (context sweep):

| component | size | finding |
|---|---|---|
| MARSYS MCP tool names, **two copies** | 131 tools each, 4.4 k tik | A deny entry is meant to drop the claude.ai copy, but it is misspelled (`"claude.ai Marsys JIS"` vs the actual name `"claude.ai MARSYS-JIS"`), so both copies load. |
| skills list | ~190 entries, EST 6–9 k | Most come from claude.ai plugins unrelated to Madhav (small-business 48, zoominfo ~32, marketing, data, enterprise-search, zapier). |
| other MCP names and instructions | ~1.4 k names + ~1.5 k Shopify instructions (EST) | Shopify, Playwright, Wispr, Drive and Calendar are unused in Madhav. |
| root `CLAUDE.md` | 3,641 tik | Already slim. Only §C, §D and §N.6–N.8 (~1.5 k) are reference material. |
| user `CLAUDE.md` + output style | 572 + 230 tik | needed |

- **Interactive vs headless.** An interactive Madhav first call is 47.3 k–77 k tokens
  (October). A headless fleet Claude first call is 20.3–22.1 k
  (`--setting-sources local --strict-mcp-config`, logs). That gap is **30–60 k extra
  tokens per turn**.
- **Latent risk.** Deferred tool loading is on by default but not pinned in any
  setting. If it were ever off, MARSYS tool definitions would add **138–210 k tokens
  per turn** for both copies (34,631 tik for 66 registry tools ≈ 525 per tool, from
  `mcp_surface_profiles.generated.json`).
- **Subagent definitions.** None of the four repo subagents set `model:` or `tools:`,
  so every one inherits the session model and the full tool list.

### F-3 KĀLA-YANTRA cycles that find no work — ≈ 1.25 B gross idle + 0.77 B polling, in 5 days

The fleet started 10-06 and ran 4,079 cycles through 10-10: 365 M footer, 3,130 M gross
(2,815 M cached input, 18.2 M output). Source: workflow sweep `agg.py`.

| role | cycles | found no work | median footer per cycle | idle share of gross |
|---|--:|--:|--:|--:|
| builders | 2,582 | 51 % | 64 K | 35 % (640 M of 1,805 M) |
| verifiers | 955 | 72 % | 88 K | 57 % (434 M of 760 M) |
| ADHIKĀRIN | 343 | 75 % | 84 K | 69 % (158 M of 230 M) |
| conductor lane | 199 | 8 % | 91 K | 6 % (19 M of 334 M) |

- **Polling disguised as work.** A further 1,099 builder cycles only renewed a claim or
  noted "waiting for review/CI". They did not print IDLE-OK, so they re-ran after 60 s
  instead of 600 s: **766 M gross**.
- **Very little building.** Only 171 of 2,554 builder cycles edited anything; 109–119
  committed and 25 opened a PR. The median cycle lasts about 2 minutes, not the
  "one item, up to 3 h" the design assumes.
- **Idle cycles are not cheap.** A no-work cycle costs 63–83 K footer, or 420–605 K gross.
- **On 10-09,** the only complete typical day, 801 M gross was spent, 61 % of it in
  no-work cycles.
- **After the hold.** Cycling continued after `HOLD_MERGES` was set at 2026-10-10 09:02Z.
- **Cadence** (`kalayantra_fleet.sh:33-41`): builders wait 60 s, control lanes 300 s,
  an idle lane 600 s, and the whole fleet 1,800 s after a quota error. Caps are 1,600
  builder and 600 control cycles a day.

### F-4 Fleet start-up and document re-reads — EST ≈ 0.1–0.2 B gross per day

- **Codex memory block.** Each cycle starts with ~25 K of fixed context, re-sent on
  every turn (median 9–19 turns per cycle). The largest piece is the Codex "Memory"
  block, ~8.7 K, which comes from `memories = true` in the base Codex config; the
  fleet profile does not switch it off. It also led agents to search a 270 KB
  `MEMORY.md` in 3,584 of 4,079 cycles.
- **Whole-document reads.** The 70 KB / 18,580 tik campaign charter was read in 3,106
  cycles, often whole. The velocity amendment (3,165 tik) was read in 2,623 cycles,
  and `CLAUDE.md` in 2,513, although the cycle prompt says CLAUDE.md does not govern
  the fleet.
- **Root `AGENTS.md`** (115 tik) tells Codex to "read CLAUDE.md in full".
- **Estimate of document re-reads:** ≈ 12 M footer tokens a day. Basis: 10-09 cycle
  counts × first-read events × file sizes. This is a lower bound, because later turns
  re-send what was read.

### F-5 Briefs are pointers; executors explore — unquantified, structurally large

- **No brief is self-contained.** None of 8 sampled KĀLA-YANTRA briefs carried a
  runnable test command, a signature, a code excerpt or inline ruling text. Their
  "spec" is section references into the 115 KB PLAN and 84 KB ALGO documents.
- **Exploration before editing.** Builders run a median of 14 commands (p90 43)
  before their first edit.
- **Verifiers read whole files, not the diff:** `cat` 733 times against `git diff` 38.
- **Rework rate.** `KARAKA.md` records that 77 % of 126 rework events were preventable,
  even with frontier builders. 17 of 37 accepted items needed more than one verdict
  (`EVENTS.jsonl`).

### F-6 Conflict recovery — ≈ 197 M gross / 5 days

- Real git conflicts appeared in 88 builder cycles, at ≈ 2.2 M gross each (≈ 4× a
  normal cycle).
- 131 merges from main ran, against 1 rebase.
- A recurring cause is generated census files: for example, PR #3426 got a "generated
  census conflict with main", per the sutradhara.12 and v1.335 logs.

### F-7 Tool-output volume inside sessions — 30 d ≈ 89 M EST tokens of Bash output, re-read on later calls

- **Bash output** was 354.9 M chars over 140,067 results; Read output was 80.9 M chars
  (B-11). Each result stays in context and is re-read on every later call, so its true
  cost multiplies with session length (F-1).
- **Repeat reads.** 1,653 of 6,642 Read calls (25 %) re-read a file already read in the
  same transcript.
- **Logs in the shared checkout.** The PostToolUse type-check hook runs `tsc` in the
  shared checkout, not the worktree. Its output is small (≤ ~200 tok EST), but it does
  not reflect the edited worktree.

### F-8 Paid production smoke on every deploy — product API spend; cost NOT MEASURED

- `pariprashna-post-deploy-smoke.yml` runs one paid production retrieval-and-synthesis
  turn after every successful deploy, including PR-triggered ones: 42 runs in 11
  hours, 14 of them failed, so up to ~90 paid turns a day.
- No other CI job calls a model. Flake reruns were 1 in 200 runs (`gh run list`
  metadata).

### F-9 Product runtime — input-heavy, no caching (§6)

### F-10 Measurement gaps — enabler for everything else

- The spend meter is untrustworthy (§3).
- Transcript retention is 30 days.
- KĀLA-YANTRA Claude lanes leave no transcript.
- Product telemetry writes constant zeros (§6).
- No MCP response sizes are stored.

## 5. Workflow and campaign mechanics (§3.3 detail)

**Roster: configured vs the owner targets.** Sources: `~/.config/kalayantra/fleet.env`,
`kalayantra_fleet.sh:33-58`, and the header of each cycle log.

| role | runs now | owner target | gap |
|---|---|---|---|
| SŪTRADHĀRA (conductor) | Codex gpt-6-sol high, 199 cycles. Since 10-08 the native's interactive session has acted as conductor. | Opus 5.5 high | vendor |
| ADHIKĀRIN | gpt-6-astra xhigh (76 cycles) → gpt-6.1-sol high (267) | Opus 5.5 high | vendor; 75 % idle |
| KĀRAKA k1–k8 | gpt-5.6-terra medium 1,197; gpt-6.1-sol high 1,297; gpt-6-sol 60; claude-opus-5-5 27 | local Qwen | **No local agent type exists**: the supervisor can only launch `codex` or `claude`. |
| PARĪKṢAKA v1–v3 | gpt-6-astra xhigh 140 → gpt-6.1-sol high 794; claude-fable-5-1 21 | frontier only | meets |
| PRAHARĪ (monitor) | Already a script: the bash supervisor checks every 60 s, `sweep_loop.sh` every 600 s, the executor every 30 s. | deterministic script | **meets.** Nirmāṇa ran it as Sonnet on a 60 s loop. |
| LEKHAKA (scribe) | absent; the conductor writes the digest | small local / Haiku | not present |
| Planner / brief author | the native's interactive sessions | Opus 5.5 xhigh | — |

**Other mechanics:**
- **Claude path cost.** The Claude lane (`claude_cycle.py`) passes no effort flag.
  Its last 49 cycles cost $78 in total by `total_cost_usd` (builders $0.50, verifiers
  $3.05 per cycle).
- **Every cycle is a fresh `codex exec`** with no resume. There were 13 compactions
  across 4,353 sessions.
- **A cheaper model edited more often.** gpt-5.6-terra at medium used about the same
  tokens per cycle as gpt-6.1-sol at high, and edited in 8.7 % of cycles against 3.2 %.
- **Codex outside the fleet, 30 d:** 523 other Madhav sessions used 8,469 M input
  (8,224 M cached) and 22.1 M output. Two interactive Codex sessions ran 2,779 and
  2,606 turns, with 410 M and 396 M input respectively.
- **Claude handing work to Codex:** 123 Claude sessions sent work to Codex at max
  effort, adding 564 M input.
- **Codex configuration:** root `AGENTS.md` and `platform/AGENTS.md` exist. The fleet
  generates a Codex profile (`make_codex_profile.sh`) that turns off every MCP server
  and plugin, but **not memories**.

## 6. Product runtime (§3.4 detail — every lever needs proof the output is unchanged)

**Default stack: Gemini** (`registry.ts:872`). Synthesis runs on gemini-3.1-pro-preview
and the fast planner on gemini-3.7-flash. Gemini 3.x is sent `thinking_level 'high'`
unless reasoning is turned off (`registry.ts:306,330`; `adapter_gemini.ts:62-64`).
Production model overrides held in the database are NOT MEASURED.

| call site | input size | caching | other |
|---|---|---|---|
| Planner, `pipeline_planner.ts:483/515` (repair `:757/773`), every consult and Paripraśna turn | system prompt 107,143 chars ≈ 26.8 k; user payload ≈ 30–39 k EST (32 capabilities by default, 48 max: `planner_projection.ts:133-135`). Multi-school queries repeat that payload in 2 example turns, ≈ 3× (`:190-230`). | none set; Gemini implicit only | Repair re-sends everything. Telemetry saves cache and reasoning as 0 (`:660-666`). |
| Consult synthesis, `run_adapter_dispatch.ts:652-679` + `agentic_loop.ts` | CGM always loaded, 79,040 B ≈ 19.8 k (`bundle_hydrator.ts:35`), plus UCN 49.6 k / LEL 36.6 k / CDLM 22.2 k / RM 11.8 k on demand. No byte cap. Up to 8 tool rounds, each re-sending the full context (`agentic_loop.ts:27, 386-389`). Tool results uncapped (`mcp_tool_executor.ts:62-67`). | Anthropic: `chat()` ignores the cache config (`anthropic/adapter.ts:93-128`). Gemini explicit cache hard-disabled (`if (false && …)`, `:514`). | max output = provider default |
| Consult history | Compression is on (`feature_flags.ts:482`, `deploy.yml:1491`): it replays up to ~32 k (`history_compression.ts:6`) and overrides the planner's 2-pair window (`consult/route.ts:1223-1245`). The summariser is hard-coded to Haiku 4.5 (`:67`). | — | finding F2-runtime |
| Paripraśna synthesis, `synthesis_stage.ts:520-560, 832` | CGM + durable summary + evidence; last 4 messages; loop of 8, or 16 in deep-dive | none | — |
| MCP `prashna_ask` synthesis, `prashna_ask_synthesis.ts:478` | evidence up to 320,000 chars ≈ 80 k (`:201-202`) | none | — |
| Continue route, `consult/continue/route.ts:211` | replays the whole conversation (`:92`) | none | — |
| Admin build chat, `chat/build/route.ts:112` | Sonnet 4.6 hard-coded, max output 16,384, full replay | call-level `cacheControl`; whether it takes effect is unverified | — |
| AI CLI bridge (`server.mjs`) and `cli-executor.ts` | fresh CLI process per call; the README measured 13,330 input tokens for a 1-token probe | none | **Bills the subscription** (claude.ai login required, `server.mjs:152`) |
| Build pipeline writers | embeddings only (`bg_texts.py:139`, `bo_samskara.py:118`) | — | deterministic-first is upheld |

**MCP serve layer:**
- **Budget is soft.** Default 40 KB; per-tool limits of 8–55 KB; maximum 64 KB
  (`registry_bridge.ts:293, 476, 491`). After full trimming, an oversize response is
  flagged `budget_exceeded_after_trim` and sent anyway (`response_budget.ts:425-512`).
- **`density_contract` is not enforced.** It is declared on 185 capabilities, but the
  trimmer never reads it.
- **Paging and projection are sparse:** `limit` on 82 of 178 tools, `cursor` on 2,
  `fields` on 3.
- **Duplicate output.** Any response of 50,000 bytes or less is sent twice, as
  structured content and as text (`registry_bridge.ts:1931-1966`; 127 call sites).
- **Full tool profile:** 178 tools, 244,827 B ≈ 61 k EST, not lazily loaded for
  API-key callers (`mcp_profile.ts:87`).
- **Largest captured responses** (`evals/omega7/harness_runs*`, July, pre-cap):
  assess_career 307,338 B, assess_wealth 280,076, ganita_chart_facts_get 155,090,
  ganita_structural_get 117,402. These must be re-measured on current main.

**Telemetry:**
- `llm_usage_events` (`001_baseline.sql:742`) and the `ai_metering_*` ledger (`1202`)
  have cache columns.
- The planner, title and tool-loop telemetry write constant 0 for cache and reasoning.
  The cache-metrics logging functions have no callers, and the MCP route logs
  `token_estimate: 0`.
- Pricing rows disagree: claude-opus-4-7 is priced 15/75 in `seed_v1.ts:122` and
  migration 583, but the `registry.ts:1222` comment says 5/25.
- **Actual production spend is NOT MEASURED.** No database or production reads were made.

**Correctness finding F1-runtime (not a token item; route to the owner).** Consult
synthesis appears **not** to receive the tool results the planner already fetched. The
system prompt is built from the bundle only (`run_adapter_dispatch.ts:458-493`), which
contradicts the comment at `consult/route.ts:1338`. Confirm with one traced request
body.

## 7. Local-builder readiness (§3.5 detail)

**Hardware and installed tools (verified):**
- **Hardware:** Apple M5 Pro, 64 GB (`sysctl hw.memsize` = 68719476736; `system_profiler`
  Mac17,9).
- **Installed:** Ollama 0.40.2, listening on 127.0.0.1:11434 with **zero models**.
  Its app binary exposes `/v1/messages`, `/v1/chat/completions` and `/v1/responses`;
  none were exercised. Codex CLI 0.162.0-alpha.17.2 has `--oss --local-provider ollama`.
  Claude Code 2.1.239.
- **Absent:** mlx_lm, LM Studio, llama.cpp CLI, litellm, claude-code-router, opencode,
  aider, and any Qwen weights. The model name "Qwen3.8-27B" could not be verified.

**Capacity (estimate).** A 27B model at 8-bit needs ≈ 27–30 GB for its weights, and
macOS gives the GPU ≈ 43–48 GB by default. That fits **one** 8-bit builder with a
moderate context. Two builders would need 4–6-bit weights. Measure before committing.

**Task classes:**
- Of the last 150 merged PRs (10-05 → 10-10), ≈ 27 % (~40) are genuinely
  local-suitable: small library-plus-test packets, text fixes and null-handling fixes.
  72 are frontier by path rule and 19 are docs only. Source: `classify.py`.
- Of KĀLA-YANTRA's K items: 39 local, 34 frontier, and 12 writer or additive-migration
  items.

**Frontier-by-rule globs** (proposed; the plan, W2-3, carries the full list):
- Gaṇita computation core: `python-sidecar/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**`,
  `orchestrator/writers/ga_*.py`, `services/{kala_core/sky,gochara_kernel}/**`,
  `**/*ephemeris*`, and any importer of swisseph or jhora (74 files).
- Migrations: `platform/migrations/*.sql` (612), `platform/supabase/migrations/*.sql`,
  `scripts/migrate.ts`.
- FROZEN orchestrator files, per `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md:40-56`.
- `'lit'` predicate sites: `asset_runner.py:546,853,920`; `src/app/api/cockpit/*`.
- `verification_pass_status` writers: 126 files, so match on diff content as well as
  path.
- Security and auth: `src/proxy.ts`, `src/lib/{auth,security,share,limits,mcp}/**`,
  `src/app/api/{auth,admin,db}/**`, `.github/workflows/**`, `infra/**`.
- Governance detectors: `platform/scripts/governance/**` (§N.8).

**Failure risks, ranked:**
1. Memory headroom on 64 GB.
2. Frameworks newer than the model's training: Next.js 16.2.4 with `src/proxy.ts`,
   React 19.2, Vitest 4, Zod 4, ai SDK 6, Tailwind 4, Python 3.13.
3. Project rules enforced by CI that a model won't guess (§N, verification
   vocabulary constants, `_idempotency.py`, writer digests, migration numbering).
4. No code map: `FILE_INDEX_v1_0.md` is closed and does not index code.
5. Repo size: 15,506 tracked files, ≈ 869 K lines of Python and 771 K of TS/TSX.
6. Database-backed tests: up to 440 of 1,233 Python and 128 of 1,871 TS test files
   need a database. They run against the local PG16 container, but CI uses PG 15.18.
7. Brief oracles are prose, not tests.
8. 52 % of builder cycles are idle; that is a scheduling cost, not a model cost.

## 8. NOT MEASURED (and why)

- **Claude Max quota weighting per class:** no local record exists.
- **Claude Max 5-hour and weekly usage %:** not exposed in transcripts.
- **Production LLM spend and cache-hit rates:** no database or production reads, by
  rule.
- **Per-turn cost of the paid deploy smoke:** needs the production metering ledger.
- **Claude history before 2026-09-11:** transcripts are pruned after 30 days.
- **Claude-path fleet lanes' tokens other than stream-json `result` events:** 98 logs
  contain a result; the rest are Codex.
- **Whether MCP clients read both copies of duplicated output:** client-side.
- **Local-model throughput and quality:** no model installed.

## 9. Changelog

- v1.0 (2026-10-11): initial Phase-A audit.
