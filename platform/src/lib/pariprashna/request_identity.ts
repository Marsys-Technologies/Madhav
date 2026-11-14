import 'server-only'
import { v5 as uuidv5, validate as validUuid, NIL, MAX } from 'uuid'

// Dedicated, stable namespace for the owner/chart-scoped request contract.
const REQUEST_NAMESPACE = 'a36d924a-ef35-5b07-a462-836f1263db5d'

export function isClientRequestId(value: unknown): value is string {
  return typeof value === 'string' && validUuid(value) && value !== NIL && value.toLowerCase() !== MAX
}

/** Call only with a verified uid; chart authorization is mandatory before binding/execution/readback. */
export function deriveClientRequestTurnId(verifiedUid: string, chartId: string, clientRequestId: string): string {
  return uuidv5(JSON.stringify([verifiedUid, chartId.toLowerCase(), clientRequestId.toLowerCase()]), REQUEST_NAMESPACE)
}
