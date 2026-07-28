/**
 * Paripraśna canonical message-parts store — PB-2 (SMṚTI) lane M-1 public API.
 *
 * The canonical, kind-typed persistence layer for pariprashna turns. Replaces
 * the opaque conversation_messages.parts_json blob for the /api/pariprashna
 * route (wiring happens in lane M-2, not here). Backed by migration 467.
 *
 *   Schema/validation (isomorphic — safe on client & server):
 *     MESSAGE_PART_KINDS, MessagePartKindSchema, per-kind body schemas,
 *     parsePartContent, CanonicalMessageSchema, MessagePartInputSchema,
 *     CANONICAL_SCHEMA_VERSION, and the row types.
 *
 *   Serializer (isomorphic, pure, deterministic):
 *     serializeCanonical / serializeCanonicalObject / canonicalizeValue —
 *     the shared serialization PB-2 lane M-2's byte-equality gate consumes.
 *
 *   DAL (server-only — pulls in the pg pool; NOT re-exported here to keep this
 *   barrel isomorphic/client-safe):
 *     writeTurn        → import from '@/lib/pariprashna/store/writer'
 *     readTurnParts    → import from '@/lib/pariprashna/store/reader'
 *     readCanonicalMessage → import from '@/lib/pariprashna/store/reader'
 *   Those modules carry `server-only`; importing them from this barrel would
 *   drag the pg pool into client bundles, so they are intentionally left out.
 */

export * from './schema'
export * from './serialize'
