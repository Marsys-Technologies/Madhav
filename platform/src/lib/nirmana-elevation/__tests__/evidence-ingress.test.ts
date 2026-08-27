import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  NirmanaEvidenceIngressNotConfiguredError,
  assertNirmanaEvidenceIngressDatabaseUrl,
  assertNirmanaEvidenceIngressDatabaseUser,
} from '../evidence-ingress'
import {
  NirmanaCampaignControlWriterNotConfiguredError,
  assertNirmanaCampaignControlDatabaseUrl,
  assertNirmanaCampaignControlDatabaseUser,
} from '../campaign-control-writer'

describe('Nirmana evidence ingress database credentials', () => {
  it('fails closed when the distinct ingress secret is absent', () => {
    expect(() => assertNirmanaEvidenceIngressDatabaseUrl(undefined, undefined, undefined))
      .toThrow(NirmanaEvidenceIngressNotConfiguredError)
  })

  it('rejects a generic application principal even when passed through the ingress setting', () => {
    expect(() => assertNirmanaEvidenceIngressDatabaseUrl(
      'postgresql://amjis_app@db.example/amjis',
      'postgresql://amjis_app@db.example/amjis',
      'amjis_app',
    )).toThrow(/must authenticate as nirmana_evidence_ingress_writer/i)
  })

  it('accepts only the separately provisioned ingress login', () => {
    expect(assertNirmanaEvidenceIngressDatabaseUrl(
      'postgresql://nirmana_evidence_ingress_writer@db.example/amjis',
      'postgresql://amjis_app@db.example/amjis',
      'amjis_app',
    )).toContain('nirmana_evidence_ingress_writer')
  })

  it('accepts the Cloud SQL connector credential only for the distinct ingress login', () => {
    expect(assertNirmanaEvidenceIngressDatabaseUser(
      'nirmana_evidence_ingress_writer', 'test-credential', 'amjis_app',
    )).toEqual({ user: 'nirmana_evidence_ingress_writer', credential: 'test-credential' })
    expect(() => assertNirmanaEvidenceIngressDatabaseUser('amjis_app', 'test-credential', 'amjis_app'))
      .toThrow(NirmanaEvidenceIngressNotConfiguredError)
  })
})

describe('Nirmana campaign control writer database credentials', () => {
  it('fails closed rather than using generic application credentials', () => {
    expect(() => assertNirmanaCampaignControlDatabaseUrl(undefined, undefined, undefined))
      .toThrow(NirmanaCampaignControlWriterNotConfiguredError)
    expect(() => assertNirmanaCampaignControlDatabaseUrl(
      'postgresql://amjis_app@db.example/amjis',
      'postgresql://amjis_app@db.example/amjis',
      'amjis_app',
    )).toThrow(/must authenticate as nirmana_campaign_control_writer/i)
  })

  it('accepts only a separately provisioned control writer login', () => {
    expect(assertNirmanaCampaignControlDatabaseUrl(
      'postgresql://nirmana_campaign_control_writer@db.example/amjis',
      'postgresql://amjis_app@db.example/amjis',
      'amjis_app',
    )).toContain('nirmana_campaign_control_writer')
    expect(assertNirmanaCampaignControlDatabaseUser(
      'nirmana_campaign_control_writer', 'test-credential', 'amjis_app',
    )).toEqual({ user: 'nirmana_campaign_control_writer', credential: 'test-credential' })
  })

  it('requires the dedicated control secret in the serving revision without exposing migration credentials', () => {
    const deployWorkflow = readFileSync(resolve(__dirname, '../../../../../.github/workflows/deploy.yml'), 'utf8')
    const webDeployment = deployWorkflow.slice(deployWorkflow.indexOf('  deploy-web:'))
    expect(webDeployment).toContain('NIRMANA_CAMPAIGN_CONTROL_DB_USER=nirmana_campaign_control_writer')
    expect(webDeployment).toContain('NIRMANA_CAMPAIGN_CONTROL_DB_PASSWORD=nirmana-campaign-control-db-password:latest')
    expect(webDeployment).not.toContain('NIRMANA_MIGRATOR_DATABASE_URL')
    expect(webDeployment).not.toContain('NIRMANA_EVIDENCE_LEGACY_OWNER_DATABASE_URL')
  })
})
