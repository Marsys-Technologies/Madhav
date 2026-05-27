// FAIL fixture: bare GCP_ prefix + non-canonical GOOGLE_ resource var.
// Expected violations: google_env_prefix on GCP_PROJECT_ID and GOOGLE_PROJECT_ID.

const projectIdLegacy = process.env.GCP_PROJECT_ID; // forbidden prefix
const projectIdAlt = process.env.GOOGLE_PROJECT_ID; // non-canonical

export { projectIdLegacy, projectIdAlt };
