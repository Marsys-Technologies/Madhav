import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // GCP SDK packages use dynamic requires internally — exclude from webpack bundle
  // so they're loaded from node_modules at runtime in the standalone container.
  serverExternalPackages: [
    "@google-cloud/tasks",
    "@google-cloud/run",
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
  },
};

export default nextConfig;
