// FAIL fixture: feature-flag-shaped identifier without MARSYS_FLAG_ prefix.
// Expected violations: marsys_flags on PANEL_MODE_ENABLED + CITATION_GATE_OVERRIDE.

const panel = process.env.PANEL_MODE_ENABLED;
const citation = process.env.CITATION_GATE_OVERRIDE;

export { panel, citation };
