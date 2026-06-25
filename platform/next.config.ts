import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        child_process: false,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
  async redirects() {
    return [
      {
        source: '/clients/:id/build',
        destination: '/clients/:id/nirmana',
        permanent: true,
      },
      {
        source: '/clients/:id/build/:conversationId',
        destination: '/clients/:id/nirmana/:conversationId',
        permanent: true,
      },
    ]
  },
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
};

export default nextConfig;
