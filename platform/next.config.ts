import type { NextConfig } from "next";

const RETIRED_COCKPIT_SECTIONS = [
  'plan',
  'sessions',
  'registry',
  'interventions',
  'parallel',
  'health',
  'activity',
] as const;

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
      ...RETIRED_COCKPIT_SECTIONS.map((section) => ({
        source: `/cockpit/${section}/:path*`,
        destination: '/cockpit',
        permanent: false,
      })),
      // The former AIOps control routes were retired with their dropped DB
      // tables. Keep old bookmarks and Observatory deep-links operational by
      // sending them to the maintained AIOps observability surface. Temporary
      // redirects let a future Mīmāṃsā rebuild reclaim these paths.
      {
        source: '/aiops',
        destination: '/observatory',
        permanent: false,
      },
      {
        source: '/aiops/:path*',
        destination: '/observatory',
        permanent: false,
      },
    ]
  },
  // SS N-376 / PR-S4: share links are authenticated, convenience links. Keep the
  // rendered conversation out of search indexes and out of Referer headers, and
  // never cache it in a shared cache.
  async headers() {
    return [
      {
        source: '/share/:path*',
        headers: [
          { key: 'X-Robots-Tag', value: 'noindex, nofollow' },
          { key: 'Referrer-Policy', value: 'no-referrer' },
          { key: 'Cache-Control', value: 'private, no-store' },
        ],
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
    "/api/admin/nirmana-elevation/snapshot": [
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
