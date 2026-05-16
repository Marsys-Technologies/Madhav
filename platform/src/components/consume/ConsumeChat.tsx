/**
 * ConsumeChat — thin flag switch between legacy and V2 paths.
 *
 * Flag-off (MARSYS_FLAG_CHAT_V2_ENABLED=false, default):
 *   renders ConsumeChatLegacy — byte-identical to pre-α7 production behavior.
 *
 * Flag-on:
 *   renders ConsumeChatV2 — assistant-ui Thread shell (β phase populates full UX).
 *
 * All consumers import from this file; neither Legacy nor V2 is imported directly.
 */

import { ConsumeChatLegacy, type ConsumeChatProps } from './ConsumeChatLegacy'
import { ConsumeChatV2 } from './ConsumeChatV2'

export type { ConsumeChatProps }

interface SwitchProps extends ConsumeChatProps {
  /** Wire MARSYS_FLAG_CHAT_V2_ENABLED here (read by server pages via configService). */
  chatV2Enabled?: boolean
}

export function ConsumeChat({ chatV2Enabled, ...props }: SwitchProps) {
  if (chatV2Enabled) {
    return <ConsumeChatV2 {...props} />
  }
  return <ConsumeChatLegacy {...props} />
}
