// PASS fixture: canonical MARSYS_FLAG_ prefix on all feature flags.
// marsys_flags rule should produce ZERO violations here.

const obs = process.env.MARSYS_FLAG_OBSERVATORY_ENABLED;
const r10 = process.env.MARSYS_FLAG_R10_EDIT_WHILE_STREAMING;
const r11 = process.env.MARSYS_FLAG_R11V2_USE_ADAPTERS;

export { obs, r10, r11 };
