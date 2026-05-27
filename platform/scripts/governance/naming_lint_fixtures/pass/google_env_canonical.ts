// PASS fixture: canonical GOOGLE_CLOUD_ prefix + allowed SDK var.
// google_env_prefix rule should produce ZERO violations here.

const projectId = process.env.GOOGLE_CLOUD_PROJECT;
const region = process.env.GOOGLE_CLOUD_REGION;
const credsPath = process.env.GOOGLE_APPLICATION_CREDENTIALS; // allowed exception
const aiKey = process.env.GOOGLE_AI_API_KEY; // allowed exception (SDK var)

export { projectId, region, credsPath, aiKey };
