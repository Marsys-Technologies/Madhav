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

// These names identify the exact bundled bytes. Use a new name if bytes change.
const ROOT_FONT_FILES = [
  '024ead497118aa23-s.woff2',
  '19cfc7226ec3afaa-s.woff2',
  '21350d82a1f187e9-s.woff2',
  '393d45a2251e223a-s.woff2',
  '48410f3df60da620-s.woff2',
  '558ca1a6aa3cb55e-s.woff2',
  '64d784ea54a4acde-s.woff2',
  '6d831b18ae5b01dc-s.woff2',
  '7b89a4fd5e90ede0-s.woff2',
  '8715d2ed531152f4-s.woff2',
  '8e9860b6e62d6359-s.woff2',
  'ac0e76ddaeeb7981-s.woff2',
  'ba9851c3c22cd980-s.woff2',
  'c48b38fe8bb532f3-s.woff2',
  'c5fe6dc8356a8c31-s.woff2',
  'df0a9ae256c0569c-s.woff2',
  'e18f83c737786aa7-s.woff2',
  'e4af272ccee01ff0-s.p.woff2',
  'e74f24ed7f0e4323-s.woff2',
  'ea896c3885e026c1-s.woff2',
  'edc640959b0c7826-s.woff2',
  'fd3893c623c32b6d-s.woff2',
  'ff71da380fbe67dd-s.woff2',
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
      { source: '/audit', destination: '/admin/administration-log', permanent: false },
      { source: '/performance', destination: '/admin/foundation', permanent: false },
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
      ...ROOT_FONT_FILES.map((filename) => ({
        source: `/brand/fonts/root/${filename}`,
        headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }],
      })),
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
