import { describe, expect, it } from 'vitest'
import {
  NirmanaEvidenceIngressNotConfiguredError,
  assertNirmanaEvidenceIngressDatabaseUrl,
} from '../evidence-ingress'

describe('Nirmana evidence ingress database credentials', () => {
  it('fails closed when the distinct ingress secret is absent', () => {
    expect(() => assertNirmanaEvidenceIngressDatabaseUrl(undefined, undefined, undefined))
      .toThrow(NirmanaEvidenceIngressNotConfiguredError)
  })

  it('rejects a generic application principal even when passed through the ingress setting', () => {
    expect(() => assertNirmanaEvidenceIngressDatabaseUrl(
      'postgresql://amjis_app:secret@db.example/amjis',
      'postgresql://amjis_app:secret@db.example/amjis',
      'amjis_app',
    )).toThrow(/must authenticate as nirmana_evidence_ingress_writer/i)
  })

  it('accepts only the separately provisioned ingress login', () => {
    expect(assertNirmanaEvidenceIngressDatabaseUrl(
      'postgresql://nirmana_evidence_ingress_writer:secret@db.example/amjis',
      'postgresql://amjis_app:secret@db.example/amjis',
      'amjis_app',
    )).toContain('nirmana_evidence_ingress_writer')
  })
})
