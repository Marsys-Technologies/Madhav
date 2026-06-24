---
artifact: CLAUDE_CODE_PROMPT_L2_CDLM_VOCAB_FIX.md
canonical_id: CLAUDE_CODE_PROMPT_L2_CDLM_VOCAB_FIX
version: 1.0
status: READY — native-authorized L2 reopen: fix the CDLM domain vocabulary at source (bo_sangati writer + data) + rebuild ph_sankrama. NO SEAL.
authored_by: Cowork 2026-06-22
native_decision: "Fix at L2 — data + writer, version-bump L2, rebuild. The durable fix (not a read-time shim)."
---

# Claude Code Prompt — L2 CDLM Domain-Vocabulary Fix (NO SEAL)

> Native AUTHORIZED reopening sealed L2 Bodha for this surgical vocabulary fix. Paste §PROMPT to Claude
> Code in Antigravity. **DO NOT SEAL** L4 or L2 — report back.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav, main). The native has AUTHORIZED a
surgical reopen of sealed L2 Bodha to fix a foundational domain-vocabulary defect, then rebuild ph_sankrama.
**DO NOT seal** L4 or L2 (no DRAFT→CURRENT beyond what's needed, no L4_PHALA_CLOSE, no CURRENT_STATE flip
to CLOSED). Report back.

**The defect (diagnosed + code-located):** `bodha_cdlm_cells` stores NON-CANONICAL domain labels. The
SOURCE is `pipeline/orchestrator/writers/bo_sangati.py` line 42:
`KNOWN_DOMAINS = ["career", "wealth", "health", "relationship", "spirituality", "character", "general"]`.
The M9 canonical domains (per `09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md`) + the L4 vocabulary
(`services/ph_phaladesa/engine.py:50 _ALL_DOMAINS = career, financial, health, relationship, spiritual,
psychological, transition`) use DIFFERENT labels. The mismatches that strand CDLM rows from phala_anchors:
- `spirituality` → should be **`spiritual`** (7 anchors × 5 domain_row + 20 domain_col rows currently dark)
- `character` → should be **`psychological`** (15 domain_row + 5 domain_col rows stranded)
- `wealth` → should be **`financial`** (25 domain_col rows; latent — no financial anchors in THIS chart yet)
A data-only UPDATE would be re-broken on the next bo_sangati rebuild. **Fix BOTH the writer AND the data.**

**Rails:** Frozen contract; anti-drift; L-is-authority; N4; canonical chart 482012f1 never mutated;
Gemini/DeepSeek only; verify against live prod data. This reopens L2 — stay surgical; touch ONLY the
vocabulary, nothing else in the L2 build.

---

### STEP 0 — Confirm the blast radius before changing anything (the fragmentation is wider than CDLM)
The diagnostic found MULTIPLE writers with divergent domain vocabularies. Map them first so the fix is
coherent, not whack-a-mole:
```
grep -rnE "spirituality|'character'|\"character\"|'wealth'|\"wealth\"|KNOWN_DOMAINS|_ALL_DOMAINS|_DOMAINS *=" \
  platform/python-sidecar --include="*.py" | grep -v __pycache__ | grep -viE "test_"
```
Known offenders: `bo_sangati.py` (KNOWN_DOMAINS — the CDLM source), `bo_drishti.py` (lines 39–49:
wealth/character/spirituality), `ka_bhavishya_lekha.py` (finance/education/general). Authoritative target
vocabulary = the M9 canonical five + the L4 set: **career, financial, health, relationship, spiritual,
psychological** (+ `general`/`transition` as the explicit catch-alls where a writer needs one).
**Decide + report:** is the right fix (a) just `bo_sangati` + its data (minimal, unblocks ph_sankrama), or
(b) also align `bo_drishti` and surface the `ka_bhavishya_lekha` variant? Recommend; do the minimal coherent
set for THIS task (bo_sangati + data), and FLAG the others as follow-ups rather than silently leaving
fragmentation. Do NOT expand scope beyond what's needed to make ph_sankrama correct + durable without
native sign-off on the wider cleanup.

### STEP 1 — Fix the WRITER (bo_sangati.py) so rebuilds emit canonical labels
In `pipeline/orchestrator/writers/bo_sangati.py` line ~42, change `KNOWN_DOMAINS` to the canonical
vocabulary: `spirituality→spiritual`, `character→psychological`, `wealth→financial`. Keep `general` if the
writer genuinely needs a catch-all (confirm whether it maps anchors there). Trace every downstream use of
`KNOWN_DOMAINS` in bo_sangati (the `combinations`, the contradiction-domain fetch, the cell-pair loop) to
ensure the rename is consistent and nothing else hardcodes the old strings. If the domain values flow from
upstream signal metadata (not just this constant), confirm where the signal `domain` field gets its value
and that it too yields canonical labels.

### STEP 2 — Fix the DATA (surgical migration on bodha_cdlm_cells)
Add a migration (next free number after L4's 341 — confirm prod max first) that UPDATEs existing rows:
```
UPDATE bodha_cdlm_cells SET domain_row = 'spiritual'     WHERE domain_row = 'spirituality';
UPDATE bodha_cdlm_cells SET domain_col = 'spiritual'     WHERE domain_col = 'spirituality';
UPDATE bodha_cdlm_cells SET domain_row = 'psychological' WHERE domain_row = 'character';
UPDATE bodha_cdlm_cells SET domain_col = 'psychological' WHERE domain_col = 'character';
UPDATE bodha_cdlm_cells SET domain_col = 'financial'     WHERE domain_col = 'wealth';
-- (domain_row='wealth' too if any exist — check first)
```
Data-only (no schema change). Idempotent. Confirm post-update: `SELECT DISTINCT domain_row, domain_col FROM
bodha_cdlm_cells WHERE chart_id='482012f1-...'` shows only canonical labels.

### STEP 3 — Version-bump L2 (it was sealed)
Update the L2 Bodha close artifact + CAPABILITY_MANIFEST: record the vocabulary correction as a
version bump (e.g. bo_sangati writer vN+1 + a changelog line "domain vocabulary aligned to M9 canonical:
spirituality→spiritual, character→psychological, wealth→financial"). Do NOT re-seal L2 from scratch — this
is a surgical correction with an audit-trail bump. Note it in DISAGREEMENT_REGISTER if appropriate.

### STEP 4 — Rebuild ph_sankrama (and re-verify the CDLM consumers)
Rebuild ph_sankrama for the native (orchestrator/cockpit Build, not a direct-runner bypass — so
asset_throughput reflects real counts this time):
```
# orchestrator path
PYTHONPATH=. python -m pipeline.orchestrator.run --chart-id 482012f1-... --asset ph_sankrama
```
Verify: phala_sankrama now includes spiritual spillover rows (the 7 spiritual anchors × 5 CDLM rows should
now match); the graph is broader than career-only. Career will still lead (207 genuine anchors) — that's
correct, not a defect. Report the new domain breakdown.
**Also re-verify OTHER CDLM consumers weren't relying on the old labels:** grep for any code matching
`domain_row == 'spirituality'` / `'character'` / `'wealth'` (esp. in retrieval, whole-chart-read, any
ph_/mi_ consumer). If found, they were ALSO silently mismatching — fix or flag.

### STEP 5 — asset_throughput reconciliation (the earlier caveat)
The prior ph_pratikara + ph_sankrama builds used a direct runner that bypassed the orchestrator, so
`asset_throughput.rows_written` still shows 0 for them despite real table rows. Trigger a
cockpit/orchestrator build for ph_pratikara + ph_sankrama so asset_throughput reflects true counts and the
cockpit shows them lit-with-rows. Confirm all 9 ph_ show correct rows_written in asset_throughput.

### REPORT — NO SEAL
Report: Step 0 blast-radius map + scope recommendation; the bo_sangati writer diff; the migration; the L2
version bump; the rebuilt ph_sankrama domain breakdown (esp. new spiritual rows); any other consumers found
relying on old labels; the asset_throughput reconciliation result (all 9 ph_ with real rows_written). State
explicitly whether anything still blocks the L4 seal. Do NOT seal L4 or L2. Then STOP for native direction.

---
*End. Fix the CDLM vocabulary at SOURCE — bo_sangati.py KNOWN_DOMAINS (line 42) + a data migration on
bodha_cdlm_cells — align to the M9 canonical (spiritual/psychological/financial), version-bump L2, rebuild
ph_sankrama via the orchestrator, reconcile asset_throughput. Flag the wider bo_drishti/ka_bhavishya
fragmentation as follow-up. NO SEAL.*
