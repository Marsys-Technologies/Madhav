# Repository bootstrap

Before any substantive work, read `../CLAUDE.md` in full and follow its
mandatory-reading sequence and the common session-open protocol. The root
`../AGENTS.md` is the equivalent bootstrap loader. Then apply the platform
rules below.


<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

---

# Locked UI design decisions (Consume module)

These three behaviors were silently reverted in commits `a37ede8` (parking bundle, 2026-05-01) and `eb427e3` ("four post-redesign tweaks", 2026-05-01) after the Portal Redesign workstream closed (PORTAL_REDESIGN_TRACKER ARCHIVED v1.0.12, 2026-04-30). They were restored 2026-05-02 by native direction. The PORTAL_REDESIGN_TRACKER is sealed and cannot record this; this section is the durable lock surface for the platform repo.

Any change to one of these three lines must be raised with the native first. The table records the active V2 source anchors and their historical counterparts.

| # | Decision | Active source | Anchor and verification |
|---|---|---|---|
| 1 | Left sidebar is **auto-collapsible**, default collapsed (`useState(true)`). The hover strip on the left edge expands it. Do not flip the default to `false`. | `src/components/consume/ConsumeChatV2.tsx` | `sidebarCollapsed = useState(true)` and the left glass rail's `onMouseEnter={handleStripEnter}`. Historical anchor `desktopSidebarCollapsed` in `ConsumeChat.tsx`, now the V2 re-export. |
| 2 | The Trace button (**super_admin**; the new pipeline is the only supported path after Phase 11B) lives in the **top-right header**, **not** in the input toolbar above the composer. Do not move it back into the bottom toolbar. | `src/components/consume/ConsumeChatV2.tsx` | Right-side header action `v2-trace-btn`, gated by `audienceTier === 'super_admin'`. Phase 11B (2026-05-11, commit `0fd18c1`) retired the `pipelineEnabled` prop/conditional with the legacy pipeline; rollback is a source revert, not a flag flip. See `FEATURE_FLAG_STATUS.md` → Removed. Historical anchor: `ChatShell.headerActions` in `ConsumeChat.tsx`. |
| 3 | The composer textarea is **fixed-size** (plain `<textarea rows={3}>` with `overflow-y-auto`). Do not reintroduce `react-textarea-autosize`, `minRows`/`maxRows`, or CSS `field-sizing: content`. Long prompts scroll inside the fixed box. | `src/components/consume/ConsumeChatV2.tsx` | `ComposerPrimitive.Input` with `rows={3}`, `resize-none`, and `overflow-y-auto`. Historical anchor `src/components/chat/Composer.tsx` textarea. These are source settings. Rendered fixed sizing and scrolling remain unverified. |

If a future redesign reopens any of these three decisions, the right sequence is: (a) raise it with the native, (b) author a new versioned design-decisions artifact under `00_ARCHITECTURE/` (the redesign tracker is archived and will not be reopened), (c) update this section to point at the new artifact, (d) only then change the code.
