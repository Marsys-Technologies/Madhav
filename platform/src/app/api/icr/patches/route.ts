/**
 * GET /api/icr/patches
 * Lists YAML filenames from PROPOSED/, RESOLVED/, REJECTED/ subdirs of
 * 00_ARCHITECTURE/CONFLICT_PATCHES/.
 *
 * ICR-S5 (2026-05-21)
 */

import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// In Next.js API routes, process.cwd() resolves to the `platform/` directory.
// Go up one level to reach the repo root.
const CONFLICT_PATCHES_DIR = path.join(
  process.cwd(),
  '..',
  '00_ARCHITECTURE',
  'CONFLICT_PATCHES',
);

function listYamls(subdir: string): string[] {
  const dirPath = path.join(CONFLICT_PATCHES_DIR, subdir);
  try {
    return fs
      .readdirSync(dirPath)
      .filter((f) => f.endsWith('.yaml') || f.endsWith('.yml'));
  } catch {
    // Directory may not exist yet — return empty array
    return [];
  }
}

export async function GET() {
  const proposed = listYamls('PROPOSED');
  const resolved = listYamls('RESOLVED');
  const rejected = listYamls('REJECTED');

  return NextResponse.json({ proposed, resolved, rejected });
}
