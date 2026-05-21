/**
 * atomic_apply.ts — ICR-S5
 *
 * Extracted atomic-apply logic for confirm action.
 * Two-step transaction: write corrected MSR → move YAML to RESOLVED.
 * Full rollback if the rename fails (restores original MSR content).
 *
 * Exported as a standalone function so it can be unit-tested without
 * spinning up the Next.js route layer.
 */

import fs from 'fs';
import path from 'path';

/** Minimal fs surface used by atomicApply — injectable for testing */
export interface FsImpl {
  readFileSync: (p: string, enc: 'utf-8') => string;
  writeFileSync: (p: string, data: string, enc: 'utf-8') => void;
  mkdirSync: (p: string, opts: { recursive: boolean }) => void;
  renameSync: (src: string, dest: string) => void;
}

export interface AtomicApplyOptions {
  /** Absolute path to PROPOSED/<patch_file> */
  proposedPath: string;
  /** Absolute path to RESOLVED/ directory */
  resolvedDir: string;
  /** Absolute path to MSR_v3_0.md */
  msrPath: string;
  /**
   * Optional fs implementation — defaults to the real `fs` module.
   * Inject a custom object in unit tests to simulate failures.
   */
  fsImpl?: Partial<FsImpl>;
}

export interface ApplyResult {
  ok: boolean;
  error?: string;
}

/**
 * Parse a single-line quoted YAML field of the form:
 *   field: "value"
 * Returns the unquoted value, or null if not found.
 */
export function parseYamlField(content: string, field: string): string | null {
  // Matches: ^field: "value" (with optional leading whitespace)
  const regex = new RegExp(`^${field}:\\s*"((?:[^"\\\\]|\\\\.)*)"`, 'm');
  const m = content.match(regex);
  return m ? m[1] : null;
}

/**
 * Atomically applies a proposed patch to the MSR file.
 *
 * Steps:
 * 1. Read YAML from proposedPath; parse `before` and `after` fields.
 * 2. Read MSR content (backup).
 * 3. Verify MSR contains the `before` text.
 * 4. Write updated MSR (replace `before` with `after`).
 * 5. Move YAML from PROPOSED/ to RESOLVED/
 *    — if rename fails: restore MSR backup, return { ok: false }.
 * 6. Return { ok: true }.
 */
export function atomicApply(opts: AtomicApplyOptions): ApplyResult {
  const { proposedPath, resolvedDir, msrPath } = opts;

  // Merge real fs with any injected overrides (injection used in tests only)
  const fsi: FsImpl = {
    readFileSync: fs.readFileSync.bind(fs) as FsImpl['readFileSync'],
    writeFileSync: fs.writeFileSync.bind(fs) as FsImpl['writeFileSync'],
    mkdirSync: fs.mkdirSync.bind(fs) as FsImpl['mkdirSync'],
    renameSync: fs.renameSync.bind(fs),
    ...opts.fsImpl,
  };

  // ── Step 1: Read patch YAML ──────────────────────────────────────────────
  let yamlContent: string;
  try {
    yamlContent = fsi.readFileSync(proposedPath, 'utf-8');
  } catch (e) {
    return { ok: false, error: `Cannot read proposed patch: ${e}` };
  }

  const before = parseYamlField(yamlContent, 'before');
  const after = parseYamlField(yamlContent, 'after');

  if (!before || !after) {
    return { ok: false, error: 'YAML missing before/after fields' };
  }

  // ── Step 2: Read MSR (backup) ────────────────────────────────────────────
  let msrContent: string;
  try {
    msrContent = fsi.readFileSync(msrPath, 'utf-8');
  } catch (e) {
    return { ok: false, error: `Cannot read MSR: ${e}` };
  }

  // ── Step 3: Verify before text exists ───────────────────────────────────
  if (!msrContent.includes(before)) {
    return { ok: false, error: `MSR does not contain before text: "${before}"` };
  }

  // ── Step 4: Write updated MSR ────────────────────────────────────────────
  const updatedMsr = msrContent.replace(before, after);
  try {
    fsi.writeFileSync(msrPath, updatedMsr, 'utf-8');
  } catch (e) {
    // MSR write failed — attempt to restore (best-effort; may already be partial)
    try {
      fsi.writeFileSync(msrPath, msrContent, 'utf-8');
    } catch {
      // best-effort
    }
    return { ok: false, error: `Failed to write MSR: ${e}` };
  }

  // ── Step 5: Move YAML PROPOSED → RESOLVED ───────────────────────────────
  const patchFile = path.basename(proposedPath);
  const resolvedPath = path.join(resolvedDir, patchFile);
  try {
    fsi.mkdirSync(resolvedDir, { recursive: true });
    fsi.renameSync(proposedPath, resolvedPath);
  } catch (e) {
    // Rollback: restore original MSR
    try {
      fsi.writeFileSync(msrPath, msrContent, 'utf-8');
    } catch {
      // best-effort rollback
    }
    return { ok: false, error: `Failed to move YAML to RESOLVED (MSR restored): ${e}` };
  }

  return { ok: true };
}
