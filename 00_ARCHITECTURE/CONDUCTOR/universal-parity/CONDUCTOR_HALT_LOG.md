# CONDUCTOR_HALT_LOG — Universal Parity Campaign

**Campaign:** Universal Tool & Data Asset Parity (feature/universal-parity)
**Purpose:** Records all conductor halts requiring native approval before proceeding.

A halt is written here when:
- A session's gate_commands fail after 2 retry attempts
- A session's acceptance criteria cannot be verified programmatically
- A schema conflict or architecture decision is encountered that was not anticipated
- A required human-approval checkpoint (HAP) is reached

---

## Open Halts

*(None — campaign not yet started)*

---

## Resolved Halts

*(Populated as halts are cleared)*

---

## Halt Template

```
### HALT-NNN
- **Session:** <session_id>
- **Timestamp:** <ISO date>
- **Reason:** <one-line description>
- **Blocking:** <list of subsequent sessions blocked>
- **Required action:** <what native must do/decide>
- **Resolution:** <filled in when cleared>
- **Resolved timestamp:** <ISO date>
```

---

## Known Required Human-Approval Checkpoints (HAP)

The following are MANDATORY halts baked into the session queue. The conductor will halt at each and require explicit native approval before proceeding:

| HAP ID | After Session | Reason |
|--------|--------------|--------|
| HAP-1 | UDA-Q-S8 | Quality delta implementation verified; gate before manifest changes |
| HAP-2 | UDA-0-S3 | Manifest fully populated; gate before portal+MCP cross-porting begins |
| HAP-3 | UDA-1-S12 | All 12 Class B engines in portal + planner wired; gate before MCP porting |
| HAP-4 | UDA-2-S10 | All 14 portal tools in MCP; gate before normalization pass |
| HAP-5 | UDA-4-S2 | All data assets enriched; gate before test campaign |
| HAP-6 | TEST-4-S1 | Production smoke complete; gate before governance close |
