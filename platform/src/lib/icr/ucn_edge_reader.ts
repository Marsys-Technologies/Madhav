// UCN edge reader — ICR stream
// ICR-S4: reads UCN_v4_0.md to extract edges referencing a given signal_id (2026-05-21)

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export interface UCNEdgeRef {
  edge_id: string;
  signal_refs: string[];
  confluence_type: string;
}

/**
 * Read UCN_v4_0.md and return all edges whose signal_refs include the given signal_id.
 *
 * UCN_v4_0.md uses a flat narrative format — structured edge blocks are not emitted
 * in machine-parseable form. This reader performs a best-effort scan for lines that
 * contain both an edge-like identifier (e.g. "UCN.E.NNN" or "EDGE.NNN") and the
 * target signal_id.
 *
 * If no structured edge blocks are found the function returns an empty array (valid
 * — Tier 2 is empty for MSR.377 at present).
 */
export function readUCNEdgesForSignal(
  signal_id: string,
  ucn_path?: string,
): UCNEdgeRef[] {
  const resolvedPath =
    ucn_path ??
    resolve(
      process.cwd(),
      '../025_HOLISTIC_SYNTHESIS/UCN_v4_0.md',
    );

  let content: string;
  try {
    content = readFileSync(resolvedPath, 'utf-8');
  } catch {
    // File not found — return empty (tested environment may not have corpus)
    return [];
  }

  const edges: UCNEdgeRef[] = [];
  const lines = content.split('\n');

  // Pattern: a line that mentions the signal_id and contains an edge-like token
  // e.g. "edge_id: UCN.E.042" or "- edge: UCN.E.042  signal_refs: [MSR.377, ...]"
  const edgeIdPattern = /edge_id:\s*([\w.]+)/;
  const signalRefsPattern = /signal_refs:\s*\[([^\]]+)\]/;
  const confluencePattern = /confluence_type:\s*([\w-]+)/;

  let currentEdgeId: string | null = null;
  let currentSignalRefs: string[] = [];
  let currentConfluence: string = 'unspecified';

  function flushEdge() {
    if (currentEdgeId && currentSignalRefs.includes(signal_id)) {
      edges.push({
        edge_id: currentEdgeId,
        signal_refs: currentSignalRefs,
        confluence_type: currentConfluence,
      });
    }
    currentEdgeId = null;
    currentSignalRefs = [];
    currentConfluence = 'unspecified';
  }

  for (const line of lines) {
    const edgeMatch = line.match(edgeIdPattern);
    if (edgeMatch) {
      flushEdge();
      currentEdgeId = edgeMatch[1];
    }

    const refsMatch = line.match(signalRefsPattern);
    if (refsMatch) {
      currentSignalRefs = refsMatch[1]
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
    }

    const confMatch = line.match(confluencePattern);
    if (confMatch) {
      currentConfluence = confMatch[1];
    }
  }
  flushEdge();

  return edges;
}
