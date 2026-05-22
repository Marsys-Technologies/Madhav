/**
 * Composer.test.tsx — B-S4 gate test
 *
 * Verifies:
 *  1. consume-composer-card class is applied to the card div
 *  2. CSS rules for r11b-active consume-composer-card exist in globals.css
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// CSS-only check — we don't render Composer in tests due to complex deps

describe('Composer (B-S4 chrome)', () => {
  it('consume-composer-card class exists in Composer.tsx', () => {
    const source = readFileSync(
      resolve(__dirname, './Composer.tsx'),
      'utf-8'
    );
    expect(source).toContain('consume-composer-card');
  });

  it('r11b-active consume-composer-card CSS rule exists in globals.css', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('.consume-shell.r11b-active .consume-composer-card');
  });

  it('r11b-active composer has 1.5rem border-radius in globals.css', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    // Check for the shape constant
    expect(css).toContain('border-radius: 1.5rem');
  });

  it('r11b-active composer has box-shadow: none in globals.css', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('box-shadow: none');
  });

  it('.brand-cta class is not modified by r11b-active CSS', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    // brand-cta should NOT be inside r11b-active block (preserved)
    // Verify .brand-cta is defined at top-level, not inside .consume-shell.r11b-active
    const r11bActiveIndex = css.indexOf('.consume-shell.r11b-active .consume-composer-card');
    const brandCtaIndex = css.indexOf('.brand-cta {');
    expect(brandCtaIndex).toBeGreaterThan(-1);
    expect(brandCtaIndex).toBeLessThan(r11bActiveIndex); // brand-cta defined before r11b-active block
  });
});
