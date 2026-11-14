import { describe, expect, it } from 'vitest'
import { readGoogleCloudEnv } from '@/lib/config/google_cloud_env'

const aliasPairs = [
  ['GOOGLE_CLOUD_PROJECT', 'GCP_PROJECT'],
  ['GOOGLE_CLOUD_REGION', 'GCP_REGION'],
  ['GOOGLE_CLOUD_BILLING_PROJECT_ID', 'GCP_BILLING_PROJECT_ID'],
  ['GOOGLE_CLOUD_BILLING_DATASET_ID', 'GCP_BILLING_DATASET_ID'],
  ['GOOGLE_CLOUD_BILLING_TABLE_ID', 'GCP_BILLING_TABLE_ID'],
] as const

const resolutionCases = [
  ['both undefined', undefined, undefined, undefined],
  ['canonical only', undefined, 'canonical', 'canonical'],
  ['legacy only', 'legacy', undefined, 'legacy'],
  ['equal bindings', 'same', 'same', 'same'],
  ['conflicting bindings', 'legacy', 'canonical', 'legacy'],
  ['empty legacy with canonical', '', 'canonical', ''],
  ['legacy with empty canonical', 'legacy', '', 'legacy'],
  ['both empty', '', '', ''],
  ['empty canonical only', undefined, '', ''],
  ['empty legacy only', '', undefined, ''],
] as const

describe.each(aliasPairs)('readGoogleCloudEnv %s', (canonical, legacy) => {
  it('distinguishes absent bindings from empty values', () => {
    expect(readGoogleCloudEnv(canonical, {})).toBeUndefined();
    expect(readGoogleCloudEnv(canonical, { [canonical]: '' })).toBe('');
    expect(readGoogleCloudEnv(canonical, { [legacy]: '' })).toBeUndefined();
  })

  it.each(resolutionCases.map(([name, legacyValue, canonicalValue]) => [name, legacyValue, canonicalValue, canonicalValue] as const))('%s', (_name, legacyValue, canonicalValue, expected) => {
    expect(readGoogleCloudEnv(canonical, {
      [legacy]: legacyValue,
      [canonical]: canonicalValue,
    })).toBe(expected)
  })
})


describe.each(aliasPairs)('canonical translation %s', (canonical, legacy) => {
  it.each(resolutionCases)('%s retains the previous effective input', (_name, legacyValue, canonicalValue, expected) => {
    const before: Record<string, string | undefined> = { [legacy]: legacyValue, [canonical]: canonicalValue };
    const translated = { ...before };
    const effective = before[legacy] ?? before[canonical];
    delete translated[legacy];
    if (effective === undefined) delete translated[canonical];
    else translated[canonical] = effective;
    expect(readGoogleCloudEnv(canonical, translated)).toBe(expected);
    expect(Object.prototype.hasOwnProperty.call(translated, legacy)).toBe(false);
    expect(Object.prototype.hasOwnProperty.call(translated, canonical)).toBe(effective !== undefined);
  });

  it('reads the default environment at the existing call time', () => {
    const oldCanonical = process.env[canonical];
    const oldLegacy = process.env[legacy];
    try {
      process.env[legacy] = 'retired-input';
      process.env[canonical] = 'first-canonical';
      expect(readGoogleCloudEnv(canonical)).toBe('first-canonical');
      process.env[canonical] = 'second-canonical';
      expect(readGoogleCloudEnv(canonical)).toBe('second-canonical');
    } finally {
      if (oldCanonical === undefined) delete process.env[canonical];
      else process.env[canonical] = oldCanonical;
      if (oldLegacy === undefined) delete process.env[legacy];
      else process.env[legacy] = oldLegacy;
    }
  });
});
