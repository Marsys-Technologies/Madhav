/**
 * GET /api/icr/patches
 * Lists and parses YAML files from PROPOSED/, RESOLVED/, REJECTED/ subdirs of
 * 00_ARCHITECTURE/CONFLICT_PATCHES/. Returns full PatchSummary objects.
 *
 * ICR-S5 (2026-05-21) — extended in PERF-S5 to return structured PatchSummary[]
 */

import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// In Next.js API routes, process.cwd() resolves to the `platform/` directory.
// Go up one level to reach the repo root.
//
// NOTE: intentionally a lazy getter (function) rather than a module-level constant.
// A module-level `path.join(process.cwd(), '..')` causes Turbopack to create a
// DirAssetReference for the parent directory, which contains python-sidecar/venv/
// with a broken symlink (→ python3.13) that triggers a fatal Turbopack panic.
function getConflictPatchesDir(): string {
  return path.join(process.cwd(), '..', '00_ARCHITECTURE', 'CONFLICT_PATCHES');
}

export interface PatchSummary {
  filename: string;
  conflict_id: string;
  signal_ids_affected: string[];
  patch_description: string;
  authored_on: string;
  before: string;
  after: string;
  status: string;
}

/**
 * Parse a YAML string into a PatchSummary using simple line-by-line parsing
 * (no external YAML library — same approach as atomic_apply.ts).
 */
function parseYaml(content: string, filename: string, fallbackStatus: string): PatchSummary {
  const lines = content.split('\n');

  function scalarField(key: string): string {
    for (const line of lines) {
      const match = line.match(new RegExp(`^${key}:\\s*(.+)$`));
      if (match) {
        // Strip surrounding quotes if present
        return match[1].replace(/^["']|["']$/g, '').trim();
      }
    }
    return '';
  }

  function listField(key: string): string[] {
    const result: string[] = [];
    let inList = false;
    for (const line of lines) {
      if (line.match(new RegExp(`^${key}:\\s*$`))) {
        inList = true;
        continue;
      }
      if (inList) {
        const item = line.match(/^\s+-\s+(.+)$/);
        if (item) {
          result.push(item[1].replace(/^["']|["']$/g, '').trim());
        } else if (line.match(/^\S/)) {
          // New top-level key — end of list
          break;
        }
      }
    }
    return result;
  }

  return {
    filename,
    conflict_id: scalarField('conflict_id'),
    signal_ids_affected: listField('signal_ids_affected'),
    patch_description: scalarField('patch_description'),
    authored_on: scalarField('authored_on'),
    before: scalarField('before'),
    after: scalarField('after'),
    status: scalarField('status') || fallbackStatus,
  };
}

function listAndParseYamls(subdir: string, fallbackStatus: string): PatchSummary[] {
  const dirPath = path.join(getConflictPatchesDir(), subdir);
  let files: string[] = [];
  try {
    files = fs
      .readdirSync(dirPath)
      .filter((f) => f.endsWith('.yaml') || f.endsWith('.yml'));
  } catch {
    // Directory may not exist yet — return empty array
    return [];
  }

  return files.map((filename) => {
    try {
      const content = fs.readFileSync(path.join(dirPath, filename), 'utf-8');
      return parseYaml(content, filename, fallbackStatus);
    } catch {
      // If file can't be read, return a minimal record
      return {
        filename,
        conflict_id: filename,
        signal_ids_affected: [],
        patch_description: '(unreadable)',
        authored_on: '',
        before: '',
        after: '',
        status: fallbackStatus,
      };
    }
  });
}

export async function GET() {
  const proposed = listAndParseYamls('PROPOSED', 'PROPOSED');
  const resolved = listAndParseYamls('RESOLVED', 'RESOLVED');
  const rejected = listAndParseYamls('REJECTED', 'REJECTED');

  return NextResponse.json({ proposed, resolved, rejected });
}
