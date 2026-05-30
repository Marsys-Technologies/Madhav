import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // GCP SDK packages use dynamic requires internally — exclude from webpack bundle
  // so they're loaded from node_modules at runtime in the standalone container.
  serverExternalPackages: [
    "@google-cloud/tasks",
    "@google-cloud/run",
  ],
};

export default nextConfig;
