/**
 * ConsumeChat — thin re-export of the V2 chat shell.
 *
 * Pre-§M.16 (closed 2026-05-18) this file was a flag-gated switch between
 * legacy and V2 paths. Post-cutover, V2 is the only path; the legacy file
 * and feature flag are removed. See §M.16 brief for details.
 */

export { ConsumeChatV2 as ConsumeChat, type ConsumeChatProps } from './ConsumeChatV2'
