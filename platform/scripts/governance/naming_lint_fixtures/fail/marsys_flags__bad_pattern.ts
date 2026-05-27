// FAIL fixture: MARSYS_FLAG_ literal that does NOT match the required pattern.
// MARSYS_FLAG_lowercase fails the [A-Z0-9]+ class.
// Expected violation: marsys_flags rule on MARSYS_FLAG_lowercase_bad.

// Use a synthetic invalid literal — lowercase chars break the canonical pattern.
const bad = "MARSYS_FLAG_lowercasebad";

export { bad };
