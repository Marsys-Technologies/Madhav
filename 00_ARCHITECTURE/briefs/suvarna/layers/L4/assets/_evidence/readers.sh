#!/bin/bash
# usage: readers.sh <table|asset_id>  -> non-test, non-generated files under platform/src platform-mcp/src platform/python-sidecar that name it (whole word)
cd /Users/Dev/suvarna-al4
grep -rlw "$1" platform/src platform-mcp/src platform/python-sidecar 2>/dev/null --include='*.ts' --include='*.tsx' --include='*.py' | grep -v -E "test|/generated/|__tests__|\.d\.ts|/node_modules/|/migrations/" | sort
