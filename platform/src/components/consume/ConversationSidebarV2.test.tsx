/**
 * ConversationSidebarV2.test.tsx — B-S5 gate test
 *
 * Verifies:
 *  1. conversation-list-item class in ConversationSidebarV2.tsx
 *  2. r11b-active conversation-list-item CSS rule in globals.css
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('ConversationSidebarV2 (B-S5 sidebar chrome)', () => {
  it('conversation-list-item class exists in ConversationSidebarV2.tsx', () => {
    const source = readFileSync(
      resolve(__dirname, './ConversationSidebarV2.tsx'),
      'utf-8'
    );
    expect(source).toContain('conversation-list-item');
  });

  it('r11b-active conversation CSS rule exists in globals.css', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('.consume-shell.r11b-active .conversation-list-item');
  });

  it('conversation item has 8px 12px padding in globals.css', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('padding: 8px 12px');
  });

  it('conversation item has 8px border-radius in globals.css', () => {
    const css = readFileSync(
      resolve(__dirname, '../../app/globals.css'),
      'utf-8'
    );
    expect(css).toContain('border-radius: 8px');
  });
});
