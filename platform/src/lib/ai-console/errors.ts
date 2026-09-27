import { z } from 'zod'
import { AiRoleSchema, type AiRole } from './types'

export const AI_ERROR_CODES = [
  'AI_DEFAULT_REQUIRED', 'AI_CHOICE_BROKEN', 'AI_CONNECTION_INVALID',
  'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE', 'AI_CLI_NOT_GRANTED',
  'AI_CLI_UNREACHABLE', 'AI_PROVIDER_UNREACHABLE', 'AI_PERMISSION_DENIED',
  'AI_BILLING_UNAVAILABLE', 'AI_RATE_LIMITED', 'AI_CLI_NOT_INSTALLED',
  'AI_CLI_AUTH_UNAVAILABLE', 'AI_CLI_TIMEOUT', 'AI_CLI_OUTPUT_LIMIT', 'AI_EXECUTION_FAILED',
] as const
export const AiErrorCodeSchema = z.enum(AI_ERROR_CODES)
export type AiErrorCode = z.infer<typeof AiErrorCodeSchema>

const PUBLIC_ERRORS: Record<AiErrorCode, { message: string; retryable: boolean }> = {
  AI_DEFAULT_REQUIRED: { message: 'Choose a default in AI Console before continuing.', retryable: false },
  AI_CHOICE_BROKEN: { message: 'The saved AI choice is unavailable. Repair it in AI Console.', retryable: false },
  AI_CONNECTION_INVALID: { message: 'The provider credential was rejected. Replace it and test the connection.', retryable: false },
  AI_MODEL_UNAVAILABLE: { message: 'The selected model is unavailable. Refresh the catalog and update your AI choice.', retryable: false },
  AI_ROLE_INCOMPATIBLE: { message: 'The selected model does not support this role. Update the role in AI Console.', retryable: false },
  AI_CLI_NOT_GRANTED: { message: 'Access to this CLI is not granted. Contact an administrator.', retryable: false },
  AI_CLI_UNREACHABLE: { message: 'The selected CLI could not be reached. Test its connection before trying again.', retryable: true },
  AI_PROVIDER_UNREACHABLE: { message: 'The selected provider could not be reached. Try the same choice again later.', retryable: true },
  AI_PERMISSION_DENIED: { message: 'The provider denied access. Check this connection\'s model permissions.', retryable: false },
  AI_BILLING_UNAVAILABLE: { message: 'Provider billing or credits are unavailable. Check your provider account.', retryable: false },
  AI_RATE_LIMITED: { message: 'The provider rate limit was reached. Try the same choice again later.', retryable: true },
  AI_CLI_NOT_INSTALLED: { message: 'The selected CLI is not installed. Contact an administrator.', retryable: false },
  AI_CLI_AUTH_UNAVAILABLE: { message: 'The selected CLI requires authentication. Contact an administrator.', retryable: false },
  AI_CLI_TIMEOUT: { message: 'The selected CLI exceeded its time limit. Try the same choice again later.', retryable: true },
  AI_CLI_OUTPUT_LIMIT: { message: 'The selected CLI exceeded its output limit. Reduce the request and try again.', retryable: false },
  AI_EXECUTION_FAILED: { message: 'The selected AI could not complete the request. Check the choice in AI Console.', retryable: false },
}

export const PublicAiErrorSchema = z.object({
  code: AiErrorCodeSchema,
  message: z.string(),
  retryable: z.boolean(),
  role: AiRoleSchema.optional(),
}).strict().refine(
  error => error.message === PUBLIC_ERRORS[error.code].message && error.retryable === PUBLIC_ERRORS[error.code].retryable,
  { message: 'Public AI errors must use the fixed message and retry policy for their code.' },
)
export type PublicAiError = z.infer<typeof PublicAiErrorSchema>

function publicError(code: AiErrorCode, role?: AiRole): PublicAiError {
  const safeRole = AiRoleSchema.safeParse(role)
  return { code, ...PUBLIC_ERRORS[code], ...(safeRole.success ? { role: safeRole.data } : {}) }
}

/** No upstream message, cause, response, or credential is accepted or retained. */
export class AiConsoleError extends Error {
  readonly code: AiErrorCode
  readonly role?: AiRole

  constructor(code: AiErrorCode, role?: AiRole) {
    const safeCode = AiErrorCodeSchema.parse(code)
    super(PUBLIC_ERRORS[safeCode].message)
    this.name = 'AiConsoleError'
    this.code = safeCode
    this.role = role === undefined ? undefined : AiRoleSchema.parse(role)
  }

  toJSON(): PublicAiError {
    return publicError(this.code, this.role)
  }
}

export interface AiErrorContext {
  source: 'provider' | 'cli'
  role?: AiRole
}

/** Read only machine discriminators; never inspect or serialize upstream text. */
function discriminator(error: unknown, key: 'status' | 'statusCode' | 'code'): unknown {
  if (typeof error !== 'object' || error === null) return undefined
  try {
    return (error as Record<string, unknown>)[key]
  } catch {
    return undefined
  }
}

export function normalizeAiError(error: unknown, context: AiErrorContext): PublicAiError {
  if (error instanceof AiConsoleError) {
    const code = AiErrorCodeSchema.safeParse(error.code)
    if (code.success) return publicError(code.data, error.role ?? context.role)
  }

  let code: AiErrorCode
  if (context.source === 'cli') {
    switch (discriminator(error, 'code')) {
      case 'ENOENT': code = 'AI_CLI_NOT_INSTALLED'; break
      case 'ETIMEDOUT': code = 'AI_CLI_TIMEOUT'; break
      case 'AUTH_UNAVAILABLE': code = 'AI_CLI_AUTH_UNAVAILABLE'; break
      case 'OUTPUT_LIMIT': code = 'AI_CLI_OUTPUT_LIMIT'; break
      case 'GRANT_REVOKED': code = 'AI_CLI_NOT_GRANTED'; break
      case 'ECONNREFUSED':
      case 'ECONNRESET': code = 'AI_CLI_UNREACHABLE'; break
      default: code = 'AI_EXECUTION_FAILED'
    }
  } else {
    switch (discriminator(error, 'status') ?? discriminator(error, 'statusCode')) {
      case 401: code = 'AI_CONNECTION_INVALID'; break
      case 402: code = 'AI_BILLING_UNAVAILABLE'; break
      case 403: code = 'AI_PERMISSION_DENIED'; break
      case 404: code = 'AI_MODEL_UNAVAILABLE'; break
      case 429: code = 'AI_RATE_LIMITED'; break
      case 408:
      case 500:
      case 502:
      case 503:
      case 504: code = 'AI_PROVIDER_UNREACHABLE'; break
      default: {
        // Unknown failures (including invalid requests and cancellation) do not
        // establish transience. Adapters may raise a typed error for finer cases.
        const networkCode = discriminator(error, 'code')
        code = networkCode === 'ECONNREFUSED' || networkCode === 'ECONNRESET'
          || networkCode === 'ETIMEDOUT' || networkCode === 'EAI_AGAIN'
          ? 'AI_PROVIDER_UNREACHABLE' : 'AI_EXECUTION_FAILED'
      }
    }
  }
  return publicError(code, context.role)
}
