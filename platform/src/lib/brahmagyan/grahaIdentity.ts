/**
 * Client-safe Graha identity and vocabulary owned by Brahmagyan.
 * Derived from the immutable L0 semantic release shared with the data plane.
 */
import semanticReleaseJson from "../../../python-sidecar/brahmagyan/l0_semantic_release_v1.json";

/** Thrown by `grahaCodeOf` (and, more broadly, by address_resolver.ts's own
 *  DB-touching resolution functions — it is the one shared address-resolution
 *  error type for the whole module, defined here because this is where the
 *  first/simplest throw site, `grahaCodeOf`, lives). No I/O; a plain `Error`
 *  subclass is pure. */
export class AddressResolutionError extends Error {}

export class AmbiguousAddressResolutionError extends AddressResolutionError {}

type ReleasedGrahaIdentity = {
  entity_id: string;
  identity_id: string;
  canonical_subject_code: string;
  canonical_label: string;
  script_labels: Record<string, string>;
  physical_variant_id: string | null;
  legacy_default: boolean;
  roles: string[];
  aliases: string[];
};

type SemanticRelease = {
  semantic_release_id: string;
  content_sha256: string;
  normalization: string;
  ambiguous_aliases: Record<string, string[]>;
  entities: ReleasedGrahaIdentity[];
};

const semanticRelease = semanticReleaseJson as SemanticRelease;
export const L0_SEMANTIC_RELEASE_ID = semanticRelease.semantic_release_id;
export const L0_SEMANTIC_RELEASE_DIGEST = semanticRelease.content_sha256;

function normalizeReleasedAlias(value: string): string {
  return value.normalize("NFC").trim().toLocaleLowerCase("en-US");
}

const RELEASED_IDENTITY_BY_ID = new Map(
  semanticRelease.entities.map(
    (entity) => [entity.identity_id, entity] as const,
  ),
);

const RELEASED_ALIAS_TO_ID = new Map<string, string>();
for (const entity of semanticRelease.entities) {
  for (const alias of entity.aliases) {
    const key = normalizeReleasedAlias(alias);
    const prior = RELEASED_ALIAS_TO_ID.get(key);
    if (prior && prior !== entity.identity_id) {
      throw new Error(`L0 semantic release alias collision: ${alias}`);
    }
    RELEASED_ALIAS_TO_ID.set(key, entity.identity_id);
  }
}

/** Strict identity adapter derived from the immutable L0 semantic release. */
export function grahaIdentityOf(
  input: string,
): Readonly<ReleasedGrahaIdentity> {
  const key = normalizeReleasedAlias(input);
  const ambiguous = semanticRelease.ambiguous_aliases[key];
  if (ambiguous) {
    throw new AmbiguousAddressResolutionError(
      `Ambiguous graha "${input}" — choose one of ${ambiguous.join(", ")}.`,
    );
  }
  const identityId = RELEASED_ALIAS_TO_ID.get(key);
  const identity = identityId
    ? RELEASED_IDENTITY_BY_ID.get(identityId)
    : undefined;
  if (!identity) {
    throw new AddressResolutionError(
      `Unknown graha "${input}" — not in L0 semantic release.`,
    );
  }
  return identity;
}

/** graha_position / karaka_chara_position fact_subject code ↔ classical graha name. */
export const GRAHA_CODE_TO_NAME: Record<string, string> = {
  ...Object.fromEntries(
    semanticRelease.entities
      .filter((entity) => entity.roles.includes("graha"))
      .map((entity) => [entity.canonical_subject_code, entity.canonical_label]),
  ),
};

/** Normalize a graha name/alias/code (English, Sanskrit, or 2-letter shorthand) to its
 *  canonical fact_subject code (e.g. "Saturn" | "shani" | "SAT" -> "SAT"). Throws
 *  `AddressResolutionError` on an unrecognized name (B.10 — no silent fallback). */
export function grahaCodeOf(input: string): string {
  return grahaIdentityOf(input).canonical_subject_code;
}
