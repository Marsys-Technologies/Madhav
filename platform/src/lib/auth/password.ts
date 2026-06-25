import 'server-only'

export function validatePassword(pw: string): string | null {
  if (typeof pw !== 'string' || pw.length < 8) {
    return 'Password must be at least 8 characters.'
  }
  if (pw.length > 128) return 'Password is too long.'
  return null
}
