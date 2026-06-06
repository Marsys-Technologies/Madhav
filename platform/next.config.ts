import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // GCP SDK packages use dynamic requires internally — exclude from webpack bundle
  // so they're loaded from node_modules at runtime in the standalone container.
  serverExternalPackages: [
    "@google-cloud/tasks",
    "@google-cloud/run",
    "@google-cloud/pubsub",
  ],
  // Include GCP proto/data files that Next.js file tracing misses in standalone mode.
  outputFileTracingIncludes: {
    "/api/build/*": [
      "./node_modules/@google-cloud/tasks/**",
      "./node_modules/@google-cloud/run/**",
      "./node_modules/google-gax/**",
      "./node_modules/@grpc/**",
      "./node_modules/grpc-js/**",
    ],
    "/api/cockpit/sse": [
      "./node_modules/@google-cloud/pubsub/**",
      "./node_modules/google-gax/**",
      "./node_modules/@grpc/**",
    ],
    "/api/cockpit/watchdog": [
      "./node_modules/@google-cloud/pubsub/**",
    ],
  },
  // Set Turbopack root to the filesystem root so that symlinks in
  // python-sidecar/venv/bin/ (which point to /opt/homebrew/...) are not
  // considered "outside the filesystem root" by Turbopack's path validator.
  // Without this, Turbopack panics when it encounters the venv's python3.13
  // symlink (→ /opt/homebrew/Cellar/...) during module graph construction.
  // This only affects local dev/build; in production the venv is not present.
  turbopack: {
    root: "/",
  },
};

export default nextConfig;
