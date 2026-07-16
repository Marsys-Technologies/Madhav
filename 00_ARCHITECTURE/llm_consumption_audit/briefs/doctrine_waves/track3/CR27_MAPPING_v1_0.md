---
artifact: TRACK3_CR27_MAPPING
type: SOURCE DRAFT (required input per BRIEF_D2.md §F1 Lane V-1 — CR-27 improvisation corpus)
version: 1.0
status: DRAFT
---

# CR-27 improvisation corpus → floor-item prevention map

**Source:** `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` §A row CR-27 (status LOGGED) —
four logged Class-9 instances in one row, named a–d here for per-item tracking — plus
§G.0's six-conclusion table and the CR-36 buried-evidence specimen (§E).

Every instance below is prevented by a floor item; none is left "out-of-contract" —
DONE-CHECK per BRIEF_D2.md §F1 Lane V-1: "Each logged improvisation must be prevented by a
floor item or explicitly noted as out-of-contract." Asserted by
`platform/src/lib/vidhi/__tests__/floor_coverage.test.ts`.

| id | CR-27 instance (verbatim from register) | prevented by | mechanism |
|---|---|---|---|
| CR-27a | "4-call diff reading answered a fresh-reading question" | `dasha_spine_lord_capability` (present on `wealth_deepdive`, `panoramic_breadth`, `general_synthesis` floors) | A compiled floor always includes the current dasha spine, forcing a fresh-state read regardless of how the question was framed — closes the diff-vs-fresh ambiguity at the floor level, not by relying on the LLM to notice. |
| CR-27b | "supply-shaped evidence plans twice" | `intervention_synthesis`, `remedy_scan` (present on every deepdive floor's machine band) | The floor mandates a leverage-ranked / capability-joined remedy read rather than letting the LLM improvise a plan from whatever it happened to retrieve — supply no longer shapes the plan because the plan-shaping primitive is itself contractual. |
| CR-27c | "chain missed until native pointed" | `mechanism_read`, `dhana_yoga_scan`, `wealth_loss_mechanism_scan` (present on `wealth_deepdive`, `career_deepdive`, `panoramic_breadth` floors) | `mechanism_read` explicitly serves named chain/circuit motifs (CR-24 known_gap notwithstanding — the primitive's PRESENCE on the floor is what prevents the omission; the known_gap flags the underlying serving defect for remediation, not the floor's completeness). |
| CR-27d | "nakshatra layer omitted from financial synthesis" | `nakshatra_semantics` (present on `wealth_deepdive`, `career_deepdive`, `panoramic_breadth` floors) | Nakshatra semantics are now a non-skippable floor item for every domain that had this omission — the LLM no longer has to "remember" to volunteer it. |
| CR-36 | "assess_wealth composite top-10 buried decisive wealth evidence" — vargottama Mercury (MD lord), Rahu exalted H2, Moon H11 (2/11 axis), KP star-lord chains | `varga_ratification`, `karaka_condition`, `kp_cusp_sublord_read`, `dasha_spine_lord_capability` (all present on `wealth_deepdive`'s acharya floor + machine band) | The specimen's four buried facts map directly onto four floor primitives: vargottama/varga-collapse → `varga_ratification`; karaka placement (Rahu/Moon axis) → `karaka_condition`; KP star-lord chain → `kp_cusp_sublord_read`; MD-lord-is-2L → `dasha_spine_lord_capability`. A compiled `wealth_deepdive` contract cannot omit any of the four without an explicit `dark` entry on its completeness receipt. |

**Note on "prevention" semantics.** A floor item being present does not itself GUARANTEE
the underlying data is well-served — several floor items above carry a `known_gap` (e.g.
`mechanism_read` → CR-24, `dhana_yoga_scan` → CR-56). What the floor prevents is the
*omission from the contract*: the compiled contract always asks for the primitive, and the
completeness receipt (`completeness_receipt_template.dark`) always surfaces the known gap
explicitly rather than the LLM silently failing to think of it. This is the distinction the
design doc draws between "sufficiency" (server-owned, measurable) and "the LLM's ability to
ignore what the system ranked" (§G.1) — the floor makes the ASK non-skippable even where the
SERVE is still a register-tracked gap.
