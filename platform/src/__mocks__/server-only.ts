// Vitest stub for the 'server-only' package.
// server-only throws at import time in browser environments to prevent
// accidental bundling; in vitest (jsdom) we no-op it so pure server
// functions can be unit-tested without a full Next.js runtime.
export {}
