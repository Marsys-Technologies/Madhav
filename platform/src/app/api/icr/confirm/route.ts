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

// ── Path constants ────────────────────────────────────────────────────────────
// process.cwd() = platform/ in Next.js API routes
const REPO_ROOT = path.join(process.cwd(), '..');
const CONFLICT_PATCHES_DIR = path.join(REPO_ROOT, '00_ARCHITECTURE', 'CONFLICT_PATCHES');
const PROPOSED_DIR = path.join(CONFLICT_PATCHES_DIR, 'PROPOSED');
const RESOLVED_DIR = path.join(CONFLICT_PATCHES_DIR, 'RESOLVED');
const REJECTED_DIR = path.join(CONFLICT_PATCHES_DIR, 'REJECTED');
const L1_REVIEW_DIR = path.join(CONFLICT_PATCHES_DIR, 'L1_REVIEW');

const MSR_PATH = path.join(REPO_ROOT, '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md');
const DISAGREEMENT_REGISTER_PATH = path.join(
  REPO_ROOT,
  '00_ARCHITECTURE',
  'DISAGREEMENT_REGISTER_v1_0.md',
);

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
  const proposedPath = path.join(PROPOSED_DIR, patchFile);

  // Double-check resolved path stays within PROPOSED/
  if (!proposedPath.startsWith(PROPOSED_DIR + path.sep) && proposedPath !== PROPOSED_DIR) {
    return NextResponse.json({ error: 'invalid patch_file (path escape)' }, { status: 400 });
  }

  const result = atomicApply({
    proposedPath,
    resolvedDir: RESOLVED_DIR,
    msrPath: MSR_PATH,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 500 });
  }

  return NextResponse.json({ ok: true, resolved: patchFile });
}

async function handleReject(patchFile: string, reason?: string): Promise<NextResponse> {
  const proposedPath = path.join(PROPOSED_DIR, patchFile);

  if (!proposedPath.startsWith(PROPOSED_DIR + path.sep) && proposedPath !== PROPOSED_DIR) {
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
    fs.mkdirSync(REJECTED_DIR, { recursive: true });
    const rejectedPath = path.join(REJECTED_DIR, patchFile);
    fs.writeFileSync(rejectedPath, rejectedContent, 'utf-8');
    fs.rmSync(proposedPath);
  } catch (e) {
    return NextResponse.json({ error: `Failed to reject patch: ${e}` }, { status: 500 });
  }

  return NextResponse.json({ ok: true, rejected: patchFile });
}

async function handleEscalate(patchFile: string, reason?: string): Promise<NextResponse> {
  const proposedPath = path.join(PROPOSED_DIR, patchFile);

  if (!proposedPath.startsWith(PROPOSED_DIR + path.sep) && proposedPath !== PROPOSED_DIR) {
    return NextResponse.json({ error: 'invalid patch_file (path escape)' }, { status: 400 });
  }

  try {
    fs.mkdirSync(L1_REVIEW_DIR, { recursive: true });
    const l1Path = path.join(L1_REVIEW_DIR, patchFile);
    fs.renameSync(proposedPath, l1Path);
  } catch (e) {
    return NextResponse.json({ error: `Failed to escalate patch: ${e}` }, { status: 500 });
  }

  // Append stub entry to DISAGREEMENT_REGISTER
  const isoDate = new Date().toISOString().slice(0, 10);
  const stub = `\n## [AUTO] Escalated: ${patchFile} (${isoDate})\nStatus: ESCALATED_TO_L1_REVIEW\nArtifact: 00_ARCHITECTURE/CONFLICT_PATCHES/L1_REVIEW/${patchFile}\nReason: ${reason ?? '<none provided>'}\n`;

  try {
    fs.appendFileSync(DISAGREEMENT_REGISTER_PATH, stub, 'utf-8');
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
