import { memo } from 'react'

/**
 * The user's own question, settled at submit — optimistic and
 * client-authoritative (§5.3 `submitted`: "the user's text repainting when
 * the server echoes it" must never happen; client text IS the display).
 * Memoized like a `FrozenBlock` since it never changes after the turn
 * opens.
 */
function UserBlockImpl({ text }: { text: string }) {
  return (
    <div className="flex justify-end my-6">
      <p
        className="pp-prose italic text-right"
        style={{ maxWidth: '78%', opacity: 0.92, fontSize: 19 }}
      >
        <span aria-hidden>&ldquo;</span>
        {text}
        <span aria-hidden>&rdquo;</span>
      </p>
    </div>
  )
}

export const UserBlock = memo(UserBlockImpl)
