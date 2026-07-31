// jsdom-ONLY setup. Loaded by the `jsdom` vitest project (see vitest.config.ts).
// The environment-agnostic half (next/navigation + monitoring-write mocks, needed
// by node-env tests too) lives in ./test-setup.shared.ts and is imported first.
import './test-setup.shared'
import '@testing-library/jest-dom'

// jsdom doesn't implement ResizeObserver or IntersectionObserver — stub them
// globally so components that use them (e.g. ConsumeChat) don't throw.
if (typeof ResizeObserver === 'undefined') {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}
if (typeof IntersectionObserver === 'undefined') {
  global.IntersectionObserver = class IntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    readonly root = null
    readonly rootMargin = ''
    readonly thresholds = []
    takeRecords() { return [] }
  }
}
