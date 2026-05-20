---
artifact: CLAUDECODE_BRIEF_PHASE_4C_6_S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-6-S2
session_name: 4C-6-S2 — YAML weights config + tunability
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
predecessor: 4C-6-S1
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.4.1 (scoring rubric)
---

# CLAUDECODE_BRIEF — Phase 4C-6-S2
## Auditable YAML weights config + per-event tunability

S1 hard-coded scoring weights in Python. S2 externalises them to a YAML config so weights are auditable + tunable without code changes. Per master plan §4.4.1: "Weights `W_*` are event-specific and read from a YAML config so the rubric is auditable, tunable, and not buried in code."

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f platform/python-sidecar/panchang_engine/muhurat.py
grep -q "score_muhurat" platform/python-sidecar/panchang_engine/muhurat.py
grep -q "DEFAULT_MUHURAT_WEIGHTS" platform/python-sidecar/panchang_engine/shastra_tables.py
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.4.1 (scoring rubric section)
3. `platform/python-sidecar/panchang_engine/muhurat.py` (current weight passing)
4. `platform/python-sidecar/panchang_engine/shastra_tables.py` (DEFAULT_MUHURAT_WEIGHTS)

## §3 — Scope (7 items)

### Item 1 — Author `muhurat_weights.yaml`
Create `platform/python-sidecar/panchang_engine/config/muhurat_weights.yaml`:

```yaml
# Muhurat scoring weights — auditable, per-event tunable
# Edited in this file (NOT in code) so the rubric stays transparent.
#
# Structure:
#   defaults: applied for any event not overridden
#   events: per-event overrides; partial — missing keys inherit from defaults
#
# All weights sum to ~1.0 within positive contributors; avoid_penalty
# remains a separate multiplicative knockout factor.

defaults:
  tithi: 0.20
  nakshatra: 0.30
  vara: 0.10
  yoga: 0.15
  planet: 0.10
  native: 0.10
  avoid_penalty: 1.0  # knockout — full negation when in inauspicious window

events:
  vivah:
    # Marriage prioritises nakshatra (Rohini, Mrigashira, etc. are paramount)
    nakshatra: 0.40
    tithi: 0.20
    vara: 0.05
    yoga: 0.15
    planet: 0.10
    native: 0.10
    avoid_penalty: 1.0

  griha_pravesh:
    # Housewarming weights vara and tithi heavily
    vara: 0.20
    tithi: 0.25
    nakshatra: 0.25
    yoga: 0.10
    planet: 0.10
    native: 0.10
    avoid_penalty: 1.0

  vyapara:
    # Business start: yoga (e.g., Guru Pushya is famously great) + planet (Jupiter strength)
    yoga: 0.25
    planet: 0.15
    nakshatra: 0.25
    tithi: 0.15
    vara: 0.10
    native: 0.10
    avoid_penalty: 1.0

  yatra:
    # Travel: vara matters more (Saturday is bad); nakshatra avoidance is key
    vara: 0.20
    nakshatra: 0.30
    tithi: 0.15
    yoga: 0.15
    planet: 0.10
    native: 0.10
    avoid_penalty: 1.0

  property_purchase:
    # Tripushkar/Dwipushkar are huge for purchases (multiplier yogas)
    yoga: 0.30
    nakshatra: 0.25
    tithi: 0.15
    vara: 0.10
    planet: 0.10
    native: 0.10
    avoid_penalty: 1.0

  mantra_initiation:
    # Spiritual events: native overlay matters more (favourable to native's chart)
    native: 0.20
    nakshatra: 0.30
    yoga: 0.15
    tithi: 0.15
    vara: 0.10
    planet: 0.10
    avoid_penalty: 1.0
```

Cite the rationale for each per-event override in YAML comments.

**AC.4C6S2.1:** YAML file present; all 6 MVP events have full weight sets; values sum check passes.

### Item 2 — Loader
Add `panchang_engine/config_loader.py`:

```python
import yaml
from pathlib import Path
from functools import lru_cache

@lru_cache
def load_muhurat_weights(config_path: Path = None) -> dict:
    """Load weights from YAML. Cached on first read. Pass config_path to override (testing)."""
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "muhurat_weights.yaml"
    raw = yaml.safe_load(config_path.read_text())
    return raw

def get_weights_for_event(event: str, config_path: Path = None) -> dict:
    """Return effective weights for `event`: defaults merged with event overrides."""
    cfg = load_muhurat_weights(config_path)
    weights = dict(cfg["defaults"])
    weights.update(cfg.get("events", {}).get(event, {}))
    return weights
```

**AC.4C6S2.2:** Loader works; `get_weights_for_event("vivah")` returns merged dict; caching verified.

### Item 3 — Wire loader into `muhurat.py`
Update `muhurat.py`'s `score_muhurat` and `find_muhurat`: if `weights` arg is None, load from YAML via `get_weights_for_event(event)`. Explicit weights arg still overrides (for testing).

**AC.4C6S2.3:** `score_muhurat(panchang, "vivah")` now uses YAML-loaded weights by default.

### Item 4 — Remove DEFAULT_MUHURAT_WEIGHTS from `shastra_tables.py`
Now obsolete; YAML is canonical. Delete the Python constant. Update any imports.

**AC.4C6S2.4:** `DEFAULT_MUHURAT_WEIGHTS` no longer in shastra_tables.py; no broken imports.

### Item 5 — Update tests
- `test_muhurat_scoring.py`: ensure tests still pass with YAML-loaded weights (should be identical numerically since YAML defaults match the old constants)
- New `test_config_loader.py`: 6 cases — load_muhurat_weights, get_weights_for_event for each event, cache hits, custom config_path override
- Sanity: scoring outputs for the canonical test cases unchanged within 0.5% (since weights are identical to S1's defaults)

**AC.4C6S2.5:** All tests PASS; numerical regression check confirms scores unchanged.

### Item 6 — Operator documentation
Add a section to `platform/python-sidecar/panchang_engine/README.md`:

```markdown
## Tuning muhurat scoring weights

Weights live in `config/muhurat_weights.yaml`. Edit there to retune scoring
without code changes. The file is parsed at sidecar startup (cached);
restart the sidecar for changes to take effect.

To tune for a specific user complaint ("the scoring overweights nakshatra
for Griha Pravesh"):
1. Edit `config/muhurat_weights.yaml` `events.griha_pravesh.nakshatra`
2. Adjust other weights so they still sum to ~1.0 (within positive
   contributors; avoid_penalty stays at 1.0)
3. Restart sidecar; verify with `find_muhurat("griha_pravesh", ...)` that
   rankings shift as intended

NEVER change the avoid_penalty value — knockout for inauspicious windows
is non-negotiable per master plan §4.4.1.
```

**AC.4C6S2.6:** README updated.

### Item 7 — Close
CURRENT_STATE; SESSION_LOG; brief flip; FINAL_SUMMARY.

**AC.4C6S2.7:** Done.

---

## §5 — Constraints
**may_touch:** `panchang_engine/config/muhurat_weights.yaml` (new); `panchang_engine/config_loader.py` (new); `muhurat.py` (loader wiring only); `shastra_tables.py` (delete DEFAULT_MUHURAT_WEIGHTS); tests; README; governance state files; this brief.
**must_not_touch:** UI; RetrievalTool; engine modules other than muhurat/config_loader/shastra_tables.

## §6 — Close checklist
- [ ] 7 ACs PASS
- [ ] Numerical regression check confirms identical scores
- [ ] README operator docs added
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Weights tuning is operator-level concern; native does not need to write code
- 6 MVP events are the only ones with explicit overrides; new events inherit defaults

## §9 — Canary
Numerical regression: identical scores pre- and post-YAML migration for the 15 test cases from S1. If scores diverge, the YAML defaults don't match the Python constants exactly — find the discrepancy.

*End — 4C-6-S2.*
