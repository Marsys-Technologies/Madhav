import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const migration = readFileSync(
  resolve(__dirname, '../../supabase/migrations/1158_ai_console_configuration_types.sql'),
  'utf8',
)

describe('AI Console migration 1158', () => {
  it('completes table DDL before updating rows with FK trigger events', () => {
    const firstClassification = migration.indexOf('UPDATE ai_custom_configurations c SET configuration_kind')
    expect(firstClassification).toBeGreaterThan(
      migration.lastIndexOf('ALTER TABLE ai_custom_configurations'),
    )
    expect(firstClassification).toBeGreaterThan(
      migration.indexOf('CREATE TRIGGER ai_configuration_scope_update'),
    )
    expect(migration).toContain("configuration_kind = 'custom_api', version = version + 1")
    expect(migration).toContain("configuration_kind = 'custom_cli', version = version + 1")
  })
})
