// PASS fixture — Record<string, string> that is NOT an ayanamsha alias map.
// Scanner must not flag arbitrary string-to-string Records.

const DOMAIN_ALIAS: Record<string, string> = {
  marriage: 'relationship',
  partnership: 'relationship',
  spouse: 'relationship',
}


export function resolveDomain(d: string): string {
  return DOMAIN_ALIAS[d] ?? d
}
