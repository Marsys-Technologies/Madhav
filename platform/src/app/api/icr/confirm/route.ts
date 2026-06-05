/**
 * POST /api/icr/confirm
 * Confirm, reject, or escalate a proposed conflict patch.
 *
 * Body: { patch_file: string, action: 'confirm' | 'reject' | 'escalate', reason?: string }
 *
 * ICR-S5 (2026-05-21)
 */

import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { atomicApply } from '@/lib/icr/atomic_apply';

// ── Path helpers ──────────────────────────────────────────────────────────────
// process.cwd() = platform/ in Next.js API routes.
//
// NOTE: intentionally lazy getters (functions) rather than module-level constants.
// A module-level `path.join(process.cwd(), '..')` causes Turbopack to create a
// DirAssetReference for the parent directory, which contains python-sidecar/venv/
// with a broken symlink (→ python3.13) that triggers a fatal Turbopack panic.
function getRepoRoot(): string { return path.join(process.cwd(), '..'); }
function getConflictPatchesDir(): string { return path.join(getRepoRoot(), '00_ARCHITECTURE', 'CONFLICT_PATCHES'); }
function getProposedDir(): string { return path.join(getConflictPatchesDir(), 'PROPOSED'); }
function getResolvedDir(): string { return path.join(getConflictPatchesDir(), 'RESOLVED'); }
function getRejectedDir(): string { return path.join(getConflictPatchesDir(), 'REJECTED'); }
function getL1ReviewDir(): string { return path.join(getConflictPatchesDir(), 'L1_REVIEW'); }
function getMsrPath(): string { return path.join(getRepoRoot(), '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md'); }
function getDisagreementRegisterPath(): string {
  return path.join(getRepoRoot(), '00_ARCHITECTURE', 'DISAGREEMENT_REGISTER_v1_0.md');
}

// ── Path-traversal validation ─────────────────────────────────────────────────

/**
 * Returns null if patch_file is safe (bare filename, no path separators or dots).
 * Returns an error string if it looks dangerous.
 */
function validatePatchFile(patchFile: string): string | null {
  if (
    patchFile.includes('/') ||
    patchFile.includes('\\') ||
    patchFile.includes('..')
  ) {
    return 'patch_file must be a bare filename with no path separators';
  }
  if (!patchFile.endsWith('.yaml') && !patchFile.endsWith('.yml')) {
    return 'patch_file must be a .yaml or .yml file';
  }
  return null;
}

// ── Handlers ──────────────────────────────────────────────────────────────────

async function handleConfirm(patchFile: string): Promise<NextResponse> {
  const proposedDir = getProposedDir();
  const proposedPath = path.join(proposedDir, patchFile);

  // Double-check resolved path stays within PROPOSED/
  if (!proposedPath.startsWith(proposedDir + path.sep) && proposedPath !== proposedDir) {
    return NextResponse.json({ error: 'invalid patch_file (path escape)' }, { status: 400 });
  }

  const result = atomicApply({
    proposedPath,
    resolvedDir: getResolvedDir(),
    msrPath: getMsrPath(),
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 500 });
  }

  return NextResponse.json({ ok: true, resolved: patchFile });
}

async function handleReject(patchFile: string, reason?: string): Promise<NextResponse> {
  const proposedDir = getProposedDir();
  const proposedPath = path.join(proposedDir, patchFile);

  if (!proposedPath.startsWith(proposedDir + path.sep) && proposedPath !== proposedDir) {
    return NextResponse.json({ error: 'invalid patch_file (path escape)' }, { status: 400 });
  }

  let yamlContent: string;
  try {
    yamlContent = fs.readFileSync(proposedPath, 'utf-8');
  } catch (e) {
    return NextResponse.json({ error: `Cannot read proposed patch: ${e}` }, { status: 500 });
  }

  // Append reject_reason line
  const rejectedContent = reason
    ? `${yamlContent.trimEnd()}\nreject_reason: "${reason}"\n`
    : `${yamlContent.trimEnd()}\nreject_reason: "<none provided>"\n`;

  try {
    const rejectedDir = getRejectedDir();
    fs.mkdirSync(rejectedDir, { recursive: true });
    const rejectedPath = path.join(rejectedDir, patchFile);
    fs.writeFileSync(rejectedPath, rejectedContent, 'utf-8');
    fs.rmSync(proposedPath);
  } catch (e) {
    return NextResponse.json({ error: `Failed to reject patch: ${e}` }, { status: 500 });
  }

  return NextResponse.json({ ok: true, rejected: patchFile });
}

async function handleEscalate(patchFile: string, reason?: string): Promise<NextResponse> {
  const proposedDir = getProposedDir();
  const proposedPath = path.join(proposedDir, patchFile);

  if (!proposedPath.startsWith(proposedDir + path.sep) && proposedPath !== proposedDir) {
    return NextResponse.json({ error: 'invalid patch_file (path escape)' }, { status: 400 });
  }

  try {
    const l1ReviewDir = getL1ReviewDir();
    fs.mkdirSync(l1ReviewDir, { recursive: true });
    const l1Path = path.join(l1ReviewDir, patchFile);
    fs.renameSync(proposedPath, l1Path);
  } catch (e) {
    return NextResponse.json({ error: `Failed to escalate patch: ${e}` }, { status: 500 });
  }

  // Append stub entry to DISAGREEMENT_REGISTER
  const isoDate = new Date().toISOString().slice(0, 10);
  const stub = `\n## [AUTO] Escalated: ${patchFile} (${isoDate})\nStatus: ESCALATED_TO_L1_REVIEW\nArtifact: 00_ARCHITECTURE/CONFLICT_PATCHES/L1_REVIEW/${patchFile}\nReason: ${reason ?? '<none provided>'}\n`;

  try {
    fs.appendFileSync(getDisagreementRegisterPath(), stub, 'utf-8');
  } catch {
    // Non-fatal — log the escalation even if DISAGREEMENT_REGISTER append fails
    // (the file may not exist in test environments)
  }

  return NextResponse.json({ ok: true, escalated: patchFile });
}

// ── Route handler ─────────────────────────────────────────────────────────────

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: { patch_file?: unknown; action?: unknown; reason?: unknown };
  try {
    body = (await request.json()) as {
      patch_file?: unknown;
      action?: unknown;
      reason?: unknown;
    };
  } catch {
    return NextResponse.json({ error: 'invalid JSON body' }, { status: 400 });
  }

  const { patch_file, action, reason } = body;

  if (typeof patch_file !== 'string' || !patch_file) {
    return NextResponse.json({ error: 'patch_file is required (string)' }, { status: 400 });
  }

  if (
    typeof action !== 'string' ||
    !['confirm', 'reject', 'escalate'].includes(action)
  ) {
    return NextResponse.json(
      { error: 'action must be one of: confirm, reject, escalate' },
      { status: 400 },
    );
  }

  // ── Path-traversal check ──────────────────────────────────────────────────
  const validationError = validatePatchFile(patch_file);
  if (validationError) {
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  const reasonStr = typeof reason === 'string' ? reason : undefined;

  switch (action as 'confirm' | 'reject' | 'escalate') {
    case 'confirm':
      return handleConfirm(patch_file);
    case 'reject':
      return handleReject(patch_file, reasonStr);
    case 'escalate':
      return handleEscalate(patch_file, reasonStr);
  }
}
