// FAIL fixture — raw enum array joined directly into a narrative _thesis field.
// Defect (F-132): window.signature_classes.join('/') produces raw internal tokens
// like 'CLASSIFY_RESIDUAL/DIGNITY/YOGA/SUBSYSTEM' in reading.thesis.

interface Window {
  signature_classes?: string[]
  strength: number
}

function buildReading(windows: Window[]) {
  const top = windows[0]
  // BAD: raw enum join into _thesis text
  const thesis = `strongest active window: ${(top?.signature_classes ?? []).join('/')} at strength ${top?.strength}`
  return { reading: { thesis } }
}
