// Keep the deployed names readable while operators migrate their configuration.
// Prefer the existing binding when both names are set to preserve deployed behavior.
const LEGACY_KEYS = {
  GOOGLE_CLOUD_PROJECT: 'GCP_PROJECT',
  GOOGLE_CLOUD_REGION: 'GCP_REGION',
  GOOGLE_CLOUD_BILLING_PROJECT_ID: 'GCP_BILLING_PROJECT_ID',
  GOOGLE_CLOUD_BILLING_DATASET_ID: 'GCP_BILLING_DATASET_ID',
  GOOGLE_CLOUD_BILLING_TABLE_ID: 'GCP_BILLING_TABLE_ID',
} as const

export function readGoogleCloudEnv(
  name: keyof typeof LEGACY_KEYS,
  env: Readonly<Record<string, string | undefined>> = process.env,
): string | undefined {
  return env[LEGACY_KEYS[name]] ?? env[name]
}
