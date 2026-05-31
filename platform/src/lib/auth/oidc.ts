import { OAuth2Client } from 'google-auth-library'

const oauthClient = new OAuth2Client()

export async function verifyOidcToken(
  token: string,
  opts: { expectedAudience: string; expectedServiceAccount?: string },
): Promise<{ email: string; sub: string } | null> {
  const ticket = await oauthClient.verifyIdToken({
    idToken: token,
    audience: opts.expectedAudience,
  })
  const payload = ticket.getPayload()
  if (!payload?.email) return null
  if (opts.expectedServiceAccount && payload.email !== opts.expectedServiceAccount) return null
  return { email: payload.email, sub: payload.sub ?? '' }
}
