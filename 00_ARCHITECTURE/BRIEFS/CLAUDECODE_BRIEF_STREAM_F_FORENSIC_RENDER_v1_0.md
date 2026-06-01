---
artifact: CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md
brief_id: STREAM_F_FORENSIC_RENDER
version: 1.0
status: ACTIVE — executable
supersedes: STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md (scoping brief — the rows assumption was wrong)
authored_at: 2026-06-01
authored_by: cowork-planner
implementation_surface: Claude Code in Google Antigravity IDE (full autonomy — gcloud + MCPs present)
autonomy: code → commit → merge to main → deploy. No human gate. See RUN_PLAN autonomy charter.
why: >
  forensic_writer.py is a 0-row stub. The render INFRASTRUCTURE already exists and is tested
  (ForensicRenderer orchestrator + 13 section renderers + no_narration_linter + rag_embedder).
  Nothing wires ForensicRenderer into the writer. This brief does that wiring and reconciles
  the pyjhora_adapter chart_output shape with the renderer input contract.
grounded_facts:
  - "build_chart.run_engine_parallel() calls pyjhora_adapter.compute_chart(ayanamsha) → chart_output dict per ayanamsha"
  - "dispatch_asset() calls WRITER_REGISTRY[asset_id](build_id, chart_id, ayanamsha_id, chart_output, conn)"
  - "ForensicRenderer.render(chart_output, chart_id, ayanamsha_id, engine_version='pyjhora/1.0.0', build_id) returns full markdown; lints each section"
  - "13 section renderers exist: planets, houses, upagrahas, sahams, karakas, yogas, panchanga, aspects, strengths, vimsopaka, vargas, dashas, supplementary"
  - "Section renderers consume chart_output via .get('sign'/'degree'/'nakshatra'/'pada'/'retrograde'/'dignity'/'house'/'varga_positions')"
  - "chart_documents table (migration 131): document_type='forensic_render', content_md, content_json, gcs_uri, byte_size, chunk_count, is_embedded; UNIQUE(chart_id, ayanamsha_id, document_type, build_id)"
  - "rag_embedder.embed_chart_document() reads chart_documents content_md, chunks, embeds — runs AFTER forensic render"
may_touch:
  - platform/python-sidecar/pipeline/writers/forensic_writer.py
  - platform/python-sidecar/pipeline/writers/__init__.py            (register in WRITER_REGISTRY)
  - platform/python-sidecar/pipeline/render/_chart_output_adapter.py (CREATE — shape shim, if needed)
  - platform/python-sidecar/pipeline/render/*.py                     (ONLY if a renderer has a real bug; prefer fixing the shim)
  - platform/python-sidecar/pipeline/__tests__/test_forensic_writer.py
  - platform/python-sidecar/pipeline/render/__tests__/                (extend, do not weaken)
  - 00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml                (add forensic_render doc-count expectation)
must_not_touch:
  - platform/python-sidecar/pyjhora_adapter/   (engine — read its output, don't change it)
  - platform/supabase/migrations/ , platform/migrations/   (131 already exists; no schema change)
  - src/   (frontend)
  - the OTHER streams' file scope (see RUN_PLAN parallel-safety matrix)
hard_bans:
  - No Anthropic models.
  - No JH-parity / FORENSIC-v8.0 value oracle. v8.0 is the SECTION SCHEMA only.
  - Do NOT weaken or skip the no_narration_linter. Facts-only is the prime directive.
  - Do NOT rewrite the tested section renderers to fix a shape mismatch — fix it in the input shim.
prime_directive: only computed facts. no narrative, no opinion, no judgement.
---

# Stream F — wire the forensic renderer

## 1 · What exists vs what's missing

EXISTS (tested, on main): `pipeline/render/base_renderer.py` (`ForensicRenderer` with
`register_section()` + `render()`), 13 section renderers, `pipeline/linters/no_narration_linter.py`,
`pipeline/writers/rag_embedder.py`. The forensic *facts* already live in `chart_facts`
(`pratyaksha`, ~2717 rows).

MISSING: `forensic_writer.write()` is a stub returning 0. It must instantiate
`ForensicRenderer`, register the 13 sections in FORENSIC v8.0 order, call `.render(chart_output, …)`,
and persist the markdown to `chart_documents`. And the `chart_output` shape that
`pyjhora_adapter.compute_chart()` emits must match what the renderers `.get(...)`.

## 2 · The work (two sub-sessions)

### S4a — wire + shape-reconcile + persist

1. **Discover the shape gap first (empirical).** In a scratch test, call
   `pyjhora_adapter.compute_chart('lahiri', <native jd>)` and dump the `chart_output` keys.
   Compare against what each section renderer `.get(...)`s (grep the renderers for `.get(`).
   Record the delta. This is the load-bearing discovery — do it before writing the writer.
2. **Build the input shim** `render/_chart_output_adapter.py`: a typed mapping from the
   `pyjhora_adapter.compute_chart()` output to the dict shape the renderers expect (e.g.
   `longitude_arcsec`→`degree` as `Decimal` degrees, 2-letter `sign` codes→full sign names,
   `nakshatra_pada`→`pada`, assemble `varga_positions`). One mapping function per renderer
   input, or one composite `to_render_input(chart_output) -> dict`. **Fix shape here, never
   in the tested renderers.** If a renderer genuinely has a bug (not a shape mismatch),
   fix it and strengthen its test.
3. **Wire `forensic_writer.write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra=None)`:**
   - `render_input = to_render_input(chart_output)`
   - instantiate `ForensicRenderer`; `register_section()` for all 13 renderers in §-order
     (Identity/Planets → Houses → Upagrahas → Sahams → Karakas → Yogas → Panchanga →
     Aspects → Strengths → Vimsopaka → Vargas → Dashas → Supplementary; align to FORENSIC
     v8.0 §1–§27 grouping).
   - `md = renderer.render(render_input, chart_id, ayanamsha_id, engine_version='pyjhora/1.0.0', build_id=build_id)`
   - lint the assembled doc (render() already lints per-section; assert no `NarrationViolation`).
   - **upsert to `chart_documents`** (document_type `'forensic_render'`): `content_md=md`,
     `content_json` = the structured section payloads, `byte_size=len(md.encode())`,
     `chunk_count=NULL` (rag_embedder fills it), `is_embedded=false`, optional `gcs_uri`.
     Use the `UNIQUE(chart_id, ayanamsha_id, document_type, build_id)` constraint with
     `ON CONFLICT … DO UPDATE`. **Idempotency guard checks `chart_documents`** (the actual
     write target — [[idempotency-guard-checks-write-target]]).
   - return `rows_written = 1` per ayanamsha (one document).
4. **Register** `forensic_writer.write` in `WRITER_REGISTRY['A2_forensic_render']` so
   `dispatch_asset` stops returning the stub 0.
5. Update `test_forensic_writer.py`: it currently asserts the stub returns 0 — flip it to
   assert a non-empty `content_md` is written and `rows_written==1`. Add a narration-lint
   assertion on the output.

### S4b — integration + RAG verify

6. Integration test (DB-backed or mocked conn): run a native-chart build path for one
   ayanamsha; assert exactly one `chart_documents` row of type `forensic_render` with
   non-empty `content_md`, linter clean, and that all 13 section anchors are present.
7. Confirm `rag_embedder.embed_chart_document()` picks up the new `is_embedded=false` row
   and produces `rag_chunks` with `source_type='forensic_render'` (mock Vertex AI in test).
8. Add `forensic_render` to `EXPECTED_ROW_COUNTS.yaml` as a `chart_documents` expectation
   (1 doc per chart × ayanamsha × build) so Pariksha's row-count battery covers it.

## 3 · Acceptance criteria

1. `pytest platform/python-sidecar/` green (writer + render + integration).
2. `forensic_writer` writes 1 `chart_documents` row per ayanamsha with non-empty `content_md`.
3. No-narration linter passes on the rendered document (no forbidden verbs).
4. All 13 section anchors present in the rendered markdown.
5. `rag_embedder` consumes the rendered doc → `rag_chunks(source_type='forensic_render')`.
6. Determinism: re-render same `(chart_id, ayanamsha_id)` → byte-identical `content_md`
   (excluding `rendered_at`).
7. Section renderers UNMODIFIED except for genuine bugs (shape handled in the shim).
8. `EXPECTED_ROW_COUNTS.yaml` updated; Pariksha forensic_render row-count GREEN.

## 4 · Out of scope

- New section renderers beyond the 13 (if FORENSIC v8.0 has a section with no renderer,
  add a TODO placeholder section + a follow-up note; do not block the wiring on it).
- Schema migrations (131 exists).
- The forensic *facts* in `chart_facts` (already populated; this is the render only).
- JH/FORENSIC-v8.0 value parity (banned).

## 5 · Failure modes

- **chart_output shape doesn't match renderers.** Expected — that's S4a step 1. Shim it.
- **A renderer raises on missing data.** `render()` already catches per-section and emits a
  `_[Render error]_` placeholder so the build continues — but a placeholder is a FAIL for
  AC4. Fix the shim to supply the field, or fix the renderer's `.get(...)` default.
- **Devanagari leaking from pyjhora_adapter.** Normalise to IAST in the shim (the adapter
  already normalises per the engine brief; double-check).
- **Linter false-positive on a legit fact verb.** Tune the linter's pattern with a test,
  do not disable it.

---

*End of CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md*
