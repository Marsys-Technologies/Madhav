#!/usr/bin/env bash
# probe/ask.sh — thin wrapper around ask.ts. See ask.ts's own header for the
# full credential-seam design (Step 1) and what this actually does (Step 2).
#
# One-time setup: none required in the common case — ask.ts fetches
# FIREBASE_ADMIN_CREDENTIALS and NEXT_PUBLIC_FIREBASE_API_KEY from Secret
# Manager itself if they aren't already in your shell's environment (needs
# the same `gcloud auth` this whole session already uses).
#
# Optional, for the harness-origin DB tag (Step 4, guard 2) to actually run
# rather than skip: a cloud-sql-proxy tunnel to amjis-postgres on 127.0.0.1:5433 —
#   cloud-sql-proxy --port 5433 madhav-astrology:asia-south1:amjis-postgres &
# Without it, the turn still completes normally; only the DB tag is skipped
# (ask.ts reports this on stderr, non-fatal).
#
# Usage:
#   ./ask.sh "What does this period ask of my career?"
#   ./ask.sh "..." --conversation-id <uuid>
#   ./ask.sh "..." --chart-id <uuid>          # explicit override — see ask.ts's guard
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # repo root
exec npx tsx platform/scripts/probe/ask.ts "$@"
