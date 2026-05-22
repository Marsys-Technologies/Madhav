/**
 * MarkdownContent.test.tsx — B-S6 gate test
 *
 * Verifies:
 *  1. markdown-content class applied to root div
 *  2. r11b-active markdown CSS rules exist in globals.css
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('MarkdownContent (B-S6 typescale)', () => {
  it('markdown-content class exists in MarkdownContent.tsx', () => {
    const source = readFileSync(
      resolve(__dirname, './MarkdownContent.tsx'),
      'utf-8'
    );
    expect(source).toContain('markdown-content');
  });

  it('r11b-active markdown CSS rules exist in globals.css', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('.consume-shell.r11b-active .markdown-content');
  });

  it('body typescale: 1rem font-size, 1.65 line-height', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('font-size: 1rem');
    expect(css).toContain('line-height: 1.65');
  });

  it('h1 typescale: 1.75rem font-size, weight 600', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('font-size: 1.75rem');
    expect(css).toContain('font-weight: 600');
  });

  it('code blocks: 14px (0.875rem) mono', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('font-size: 0.875rem');
  });

  it('code bg uses var(--card) — existing token, not new cream value', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    // Should use var(--card) for code background
    expect(css).toContain('background: var(--card)');
    // Should NOT introduce claude-cream bg values
    expect(css).not.toContain('rgb(248, 246, 240)');
    expect(css).not.toContain('#f8f6f0');
  });
});
