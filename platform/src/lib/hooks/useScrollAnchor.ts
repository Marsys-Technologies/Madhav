/**
 * Re-export of the consolidated scroll-anchor hook used by the consume chat.
 *
 * CO.6: surfaced here so the lifecycle-slot architecture (flag-ON path)
 * can import from the same lib/hooks namespace as useChatLifecycle and
 * useSidebarState.
 *
 * Behavior (ChatGPT-style):
 *   - Auto-scroll to bottom when new content arrives AND user is within
 *     `thresholdPx` of the bottom.
 *   - If user has scrolled up (> thresholdPx), do NOT auto-scroll.
 *   - On new user message submit, always call scrollToBottom explicitly.
 */
export { useScrollAnchor } from '@/hooks/useScrollAnchor'
export type { } from '@/hooks/useScrollAnchor'
