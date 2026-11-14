// Keep the deployed names readable while operators migrate their configuration.
// Prefer the existing binding when both names are set to preserve deployed behavior.
type GoogleCloudEnvName =
  | "GOOGLE_CLOUD_PROJECT"
  | "GOOGLE_CLOUD_REGION"
  | "GOOGLE_CLOUD_BILLING_PROJECT_ID"
  | "GOOGLE_CLOUD_BILLING_DATASET_ID"
  | "GOOGLE_CLOUD_BILLING_TABLE_ID";

export function readGoogleCloudEnv(
  name: GoogleCloudEnvName,
  env: Readonly<Record<string, string | undefined>> = process.env,
): string | undefined {
  return env[name]
}
