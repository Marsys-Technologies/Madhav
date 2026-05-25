---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-0-S1: Manifest Audit + Deduplicate CAPABILITY_MANIFEST.json"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_0_S1
version: 1.0
status: CURRENT
phase: UDA-0
session_id: UDA-0-S1
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-0-S1 — Manifest: Audit + Deduplicate CAPABILITY_MANIFEST.json

## 1. Context

`00_ARCHITECTURE/CAPABILITY_MANIFEST.json` is the project's single source of truth for all
canonical artifacts. Before populating it with all portal and MCP tools, this session audits
the existing manifest for:

1. **Duplicate `canonical_id` values** — must be zero
2. **Entries without required fields** (`canonical_id`, `path`, `status`, `version`)
3. **Stale or incorrect paths** (files that no longer exist at declared paths)
4. **Tool entries** — count how many retrieval tool entries currently exist per channel

The session writes a human-readable audit report and leaves the manifest clean (no duplicates).

---

## 2. Scope

**may_touch:**
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (dedup only — remove exact duplicate entries)
- `eval-results/UDA_0_S1_MANIFEST_AUDIT.md` (create)

**must_not_touch:**
- Any files under `platform/` or `platform-mcp/`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.0_1.1: No duplicate `canonical_id` values in manifest after this session
- [ ] AC.0_1.2: `eval-results/UDA_0_S1_MANIFEST_AUDIT.md` exists with full audit report
- [ ] AC.0_1.3: Audit report includes: total entry count, duplicate count (pre/post), missing-field entries, stale-path entries, current tool entry counts per channel
- [ ] AC.0_1.4: `cd platform && npx tsc --noEmit` passes with 0 errors (no code changes expected; verify manifest is still valid JSON)
- [ ] AC.0_1.5: Commit message contains `UDA-0-S1`

---

## 4. Step-by-Step Execution

### Step 1 — Count and list all entries

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  console.log('total entries:', m.entries.length);
  const byType = {};
  m.entries.forEach(e => { byType[e.type] = (byType[e.type]||0)+1; });
  console.log('by type:', JSON.stringify(byType, null, 2));
"
```

### Step 2 — Detect duplicates

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const ids = m.entries.map(e => e.canonical_id);
  const seen = new Set(); const dupes = [];
  ids.forEach(id => { if (seen.has(id)) dupes.push(id); else seen.add(id); });
  console.log('duplicate canonical_ids:', dupes.length ? dupes.join(', ') : 'NONE');
"
```

### Step 3 — Detect missing-field entries

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const REQUIRED = ['canonical_id', 'status', 'version'];
  const bad = m.entries.filter(e => REQUIRED.some(f => !e[f]));
  console.log('entries missing required fields:', bad.length);
  bad.slice(0,10).forEach(e => console.log(' -', e.canonical_id || '(no id)', JSON.stringify(Object.keys(e))));
"
```

### Step 4 — Detect stale paths

```bash
node -e "
  const fs = require('fs');
  const m = JSON.parse(fs.readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const stale = m.entries.filter(e => e.path && !fs.existsSync(e.path));
  console.log('stale paths:', stale.length);
  stale.slice(0,10).forEach(e => console.log(' -', e.canonical_id, '->', e.path));
"
```

### Step 5 — Count tool entries per channel

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const portal = m.entries.filter(e => e.channel === 'portal' && e.type === 'retrieval_tool');
  const mcp = m.entries.filter(e => e.channel === 'mcp' && e.type === 'retrieval_tool');
  const noChannel = m.entries.filter(e => e.type === 'retrieval_tool' && !e.channel);
  console.log('portal retrieval_tools:', portal.length);
  console.log('mcp retrieval_tools:', mcp.length);
  console.log('retrieval_tools missing channel:', noChannel.length);
"
```

### Step 6 — Remove duplicates from manifest

If duplicates were found in Step 2:
```bash
node -e "
  const fs = require('fs');
  const m = JSON.parse(fs.readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const seen = new Set();
  m.entries = m.entries.filter(e => {
    if (seen.has(e.canonical_id)) return false;
    seen.add(e.canonical_id);
    return true;
  });
  fs.writeFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json', JSON.stringify(m, null, 2) + '\n');
  console.log('deduped. new count:', m.entries.length);
"
```

If no duplicates, skip this step.

### Step 7 — Write audit report

Write `eval-results/UDA_0_S1_MANIFEST_AUDIT.md` with:
- Summary table: total entries, pre-dedup duplicates, post-dedup count, missing-field count, stale-path count
- Per-channel tool counts
- List of any stale paths found (or "none")
- List of any missing-field entries (or "none")
- Conclusion: manifest is clean and ready for UDA-0-S2 population

### Step 8 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json eval-results/UDA_0_S1_MANIFEST_AUDIT.md
git commit -m "audit(UDA-0-S1): CAPABILITY_MANIFEST dedup + audit report

Pre: <N> entries, <D> duplicates. Post: <N-D> entries, 0 duplicates.
Stale paths: <S>. Missing-field entries: <M>.
Portal tools registered: <P>. MCP tools registered: <C>."
```

---

## 5. Gate Commands

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const ids = m.entries.map(e => e.canonical_id);
  const dupes = ids.filter((id,i) => ids.indexOf(id) !== i);
  if (dupes.length > 0) { console.error('GATE_UDA_0_S1_DUPES: FAIL — ' + dupes); process.exit(1); }
  console.log('GATE_UDA_0_S1_DUPES: PASS');
"

test -f eval-results/UDA_0_S1_MANIFEST_AUDIT.md && echo 'GATE_UDA_0_S1_AUDIT: PASS'

git log --oneline -3 | grep -q 'UDA-0-S1' && echo 'GATE_UDA_0_S1_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_0_S1_v1_0.md*
