# WIRE shard-1a4-b12 — FUSED Lane 1a (synthesizability-as-received) + Lane 4 (receipt honesty)

Worker tools: `vector_search`, `yoga_activation_by_dasha`. 100% probed, no skips.
Wire: POST localhost:3000/api/mcp/primitives/<tool>, chart 482012f1-710e-4a25-994a-93821f5871aa.
Cross-validated across TWO queries (`"career and profession yoga"` top_k:5 and `"career and profession"`).

---

## 1. vector_search — channel = reachable-surgical

**Call:** `POST /api/mcp/primitives/vector_search` → `ok:true`, `epistemics.surgical:true`, `confidence_band:"high"`, latency 5–6.5s.

**Envelope:** `result{tool_bundle_id,tool_name,tool_version,invocation_params,results,served_from_cache:false,latency_ms,result_hash:sha256:…,schema_version:1.0}`. Inner `content` JSON: `{search_mode:"hybrid_vector_keyword", query_used, citations[5], rows[5], total:5}`. Each citation: `citation_ref`, `verse_ref`, `verse_text_en`, `verse_text_sa`, `content_summary`, `topics`, `source_citation` (`[HIGH]/[MEDIUM]` tier), `tradition_school`, `vector_score`/`keyword_score`/`combined_score`.

### Synthesizability-as-received = PARTIAL (query-dependent; unreliable on first contact)
- Citation scaffolding IS self-describing and composable: tier + publisher + page (`"[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 | PG403"`, `"[HIGH] BPHS — Trans. R. Santhanam, Ranjan Publications | PG364"`).
- BUT the payload consumers actually cite — `verse_text_en` — is raw OCR sludge, and `content_summary:null`, `topics:[]`, `verse_text_sa:null` across all hits, so the fields that would make it clean-consumable are empty. **[failure_class 6 — UNUSABLE FORM].**
  - Query `"career and profession yoga"` — Sanskrit OCR garble, verbatim (E-6): `"f{fuswi fagorfua: fiwdgerigtn qilril{it l"` / `"6ag:nrrfa:tlil: ttti? a frqhr: RrctilrEn: I"`.
  - Query `"career and profession"` — English INDEX-PAGE OCR, verbatim (E-6): rank1 `phaladeepika:PG403:C2` = `"BROTHERIIOOD\nTo bo devoid\nof good— .\nVI- 08.\nBQDDJIIST…"`; rank2 `phaladeepika:PG445:C1` = `"POURNAMI\n' INDEX\n55\nPUBLIC…POVERTY."`; rank3 = `"INDEX\n13\nBUSINESS\nBKF.AST…"`. Only rank0 `bhrigu_nandi_nadi:PG257:C2` was a clean composable sentence: `"Even Saturn, significator of profession meets Mars in Aquarius first. So the native will be employed in an engineering concern."` (combined 0.452).
- **Ranking surfaces garbage at near-top scores:** the 3 index-page garbage hits scored 0.443–0.449 — within 0.01 of the one clean hit (0.452). A consumer trusting `combined_score` ordering cannot distinguish real verses from alphabetical-index OCR noise. **Retrieval relevance also poor:** "career/profession" queries returned index pages + (prior run) yogas for "barren wife", "leprosy", "loss of eye sight", "imprisonment" — none career-specific. Salvage needs a 2nd tool (`read_classical_text`) or tribal knowledge → PARTIAL not PASS.
- **[failure_class 7 — DROWNED/DUPLICATE, secondary]:** inner `content` emits the same 5-hit array twice under both `citations` and `rows` keys — payload duplicated, doubling envelope size. (Prior run observed the same duplication.)

### Receipt honesty (Lane 4) = HONEST
- `total:5` == `len(citations)` 5 == `len(rows)` 5. `served_from_cache:false`, `result_hash` present, `schema_version:1.0`. Per-hit `vector_score`/`keyword_score`/`combined_score` internally consistent (combined ≈ weighted blend).
- No `truncated` flag asserted and `total:5` honestly equals rows shown at top_k=5 — no counter contradicts payload. **Contrast LCA-7 msr_sql `truncated:False` (dishonest): NOT reproduced here — vector_search is the honest counter-example.**
- Minor caveat (not scored DISHONEST): envelope top-level `citations:[]` is empty while inner `content` carries 5 — a consumer reading the standard envelope `citations` field sees zero. These envelope fields (`citations/plan/predictions_logged/synthesis_audit/suggested_followups/warnings` all empty) are down-pipeline aggregation slots unpopulated in surgical mode (expected), so classified HONEST-with-caveat.

---

## 2. yoga_activation_by_dasha — channel = served-only-by-down-pipeline

**Call:** `POST /api/mcp/primitives/yoga_activation_by_dasha` → `ok:false`, `error.class:"validation"`, verbatim (E-6): `"Tool not in surgical whitelist: yoga_activation_by_dasha"`, remediation `"Use ask_madhav for full-pipeline queries."` (Initial probe returned `rate_limit` 60 RPM; retried past it to the definitive whitelist verdict.)
- Absent from the surgical whitelist; consumable only via full `ask_madhav` pipeline, whose consult path is broken per **LCA-2**. **synthesizability = not-probed** (no surgical channel to grade first-contact form). **receipt_honesty = n/a.**
- **[failure_class 1 — UNREACHABLE via surgical].** NOT DEAD-19 (not registry-missing; a real pipeline tool excluded from surgical), cross-ref LCA-2.

---

## Cross-refs cited (not re-derived)
- LCA-2: full-pipeline consult broken → served-only-by-down-pipeline tools unconsumable.
- LCA-7: msr_sql dishonest `truncated:False` — vector_search receipt is the honest counter-example.
