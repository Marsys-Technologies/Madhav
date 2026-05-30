/**
 * tailwind.config.ts — MARSYS-JIS Tailwind v4 compatibility shim
 *
 * This project uses Tailwind CSS v4 where configuration is CSS-first:
 * all theme tokens (brand colors, fonts) are declared in
 * src/app/globals.css under the @theme inline block.
 *
 * This file exists for tooling compatibility (IDEs, type-checking, storybook)
 * and documents the design-system contract. It is NOT the active config
 * source — globals.css @theme is the source of truth for v4.
 *
 * Brand token reference (obsidian+gold palette):
 *   bg-brand-bg       #08070a  — deepest background
 *   bg-brand-surface  #0d0c10  — surface / card
 *   border-brand-border #1a1820 — default border
 *   text-brand-gold-1  #d4a648 — base gold
 *   text-brand-gold-2  #e8c878 — lighter gold
 *   text-brand-gold-3  #f8e6a8 — highlight gold
 *   text-brand-gold-4  #c4932a — dark gold / pressed
 *   text-brand-text-1  #f5f0e8 — primary text (warm white)
 *   text-brand-text-2  #c8bfb0 — secondary text
 *   text-brand-text-3  #8a8070 — tertiary / muted
 *   text-brand-text-4  #5a5550 — disabled
 *   text-brand-ok      #4a8c5c — success green
 *   text-brand-warn    #c8842a — warning amber
 *   text-brand-err     #9c3a2a — error red
 *
 * Font families (CSS custom properties set by next/font in layout.tsx):
 *   font-serif  → var(--font-serif)  → Cormorant Garamond
 *   font-sans   → var(--font-sans)   → Inter
 *   font-mono   → var(--font-mono)   → system monospace
 */

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/**/*.{ts,tsx}',
    './src/app/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          bg:       '#08070a',
          surface:  '#0d0c10',
          border:   '#1a1820',
          'gold-1': '#d4a648',
          'gold-2': '#e8c878',
          'gold-3': '#f8e6a8',
          'gold-4': '#c4932a',
          'text-1': '#f5f0e8',
          'text-2': '#c8bfb0',
          'text-3': '#8a8070',
          'text-4': '#5a5550',
          ok:       '#4a8c5c',
          warn:     '#c8842a',
          err:      '#9c3a2a',
        },
      },
      fontFamily: {
        serif: ['var(--font-serif)', 'Georgia', 'serif'],
        sans:  ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono:  ['var(--font-mono)', 'monospace'],
      },
    },
  },
  plugins: [],
}

export default config
