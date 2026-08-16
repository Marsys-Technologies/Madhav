// PASS fixture — narrative text uses a glossed label, not raw enum/token.

const WINDOW_CLASS_GLOSS: Record<string, string> = {
  'CLASSIFY_RESIDUAL': 'residual activation',
  'DIGNITY': 'dignity activation',
  'YOGA': 'yoga activation',
  'SUBSYSTEM': 'subsystem window',
}

interface Window {
  signature_classes?: string[]
  strength: number
}

function glossClass(c: string): string {
  return WINDOW_CLASS_GLOSS[c] ?? c.toLowerCase().replace(/_/g, ' ')
}

function buildReading(windows: Window[]) {
  const top = windows[0]
  // GOOD: glossed label, not raw enum join
  const label = (top?.signature_classes ?? []).map(glossClass).join(' + ') || 'activation window'
  const thesis = `strongest ${label} at strength ${top?.strength}`
  return { reading: { thesis } }
}
