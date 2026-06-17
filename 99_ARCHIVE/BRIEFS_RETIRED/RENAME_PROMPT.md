RENAME: MARSYS-JIS → MARSYS-JIS
============================

PRE-FLIGHT (run in terminal before starting):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  mv CLAUDECODE_BRIEF.md CLAUDECODE_BRIEF.md.hold

POST-SESSION (run in terminal after Claude Code confirms RENAME COMPLETE):
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  mv CLAUDECODE_BRIEF.md.hold CLAUDECODE_BRIEF.md

---

OBJECTIVE
---------
Rename the project from "MARSYS-JIS" to "MARSYS-JIS" throughout all text,
documentation, and source files. This is a pure text search-and-replace
with two targeted extras (a file rename and a localStorage key fix).

WHAT TO CHANGE:
  "MARSYS-JIS"  → "MARSYS-JIS"     (the main project name, ~150 files)
  "MARSYS_JIS"  → "MARSYS_JIS"     (underscore variant in filenames + code)

WHAT NOT TO CHANGE (GCP infrastructure slugs — leave exactly as-is):
  amjis-postgres       (Cloud SQL instance)
  amjis-web            (Cloud Run service)
  amjis-sidecar        (Cloud Run service)
  amjis_app            (database user)
  amjis-db-password    (Secret Manager)
  amjis-voyage-api-key (Secret Manager)
  DB_NAME=amjis        (.env.rag)
  asia-south1-docker.pkg.dev/madhav-astrology/amjis/...  (Artifact Registry)

The uppercase-hyphenated forms ("MARSYS-JIS", "MARSYS_JIS") are safe to replace
globally — they will never accidentally match the lowercase GCP slugs
("amjis", "amjis_app", etc.).

---

STEP 1: BULK TEXT REPLACEMENT
-------------------------------
Run this from the project root. It replaces the two case variants across
all tracked text files, excluding build artifacts and version control:

  find . -type f \( \
    -name "*.md" -o -name "*.ts" -o -name "*.tsx" -o -name "*.py" \
    -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh"  \
    -o -name "*.json" -o -name "*.txt" -o -name "*.toml" \
  \) \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/.next/*" \
  -not -path "*/dist/*" \
  -not -path "*/.turbo/*" \
  | xargs sed -i \
      -e 's/MARSYS-JIS/MARSYS-JIS/g' \
      -e 's/MARSYS_JIS/MARSYS_JIS/g'

After running, confirm the GCP slugs are untouched:
  grep -n "amjis" .env.rag platform/cloudbuild.yaml platform/scripts/start_db_proxy.sh

All lines returned should still say "amjis" (lowercase, no change). If
any show "MARSYS_JIS" or "marsys-jis" instead, something went wrong —
revert with git and re-run more carefully.

Confirm the rename worked:
  grep -c "MARSYS-JIS" CLAUDE.md
  grep -c "MARSYS-JIS" CLAUDE.md
First number should be well above zero. Second should be zero.

---

STEP 2: FIX THE LOCALSTORAGE KEY IN useChatPreferences.ts
-----------------------------------------------------------
The file platform/src/hooks/useChatPreferences.ts uses the string
"amjis:consume-prefs:" as a browser localStorage key. This is a product
string (not a GCP resource name) and should change.

In that file, replace:
  amjis:consume-prefs:
with:
  marsys-jis:consume-prefs:

Do this with a targeted sed:
  sed -i 's|amjis:consume-prefs:|marsys-jis:consume-prefs:|g' \
    platform/src/hooks/useChatPreferences.ts

Verify:
  grep "consume-prefs" platform/src/hooks/useChatPreferences.ts
Should show: marsys-jis:consume-prefs:${chartId}

NOTE: Changing this key means existing users will lose their saved chat
preferences (font size, model choice, etc.) — they are trivially
re-settable, so this is acceptable.

---

STEP 3: RENAME THE BOOTSTRAP HANDOFF FILE
------------------------------------------
One file is named with the old project name and must be renamed:

  git mv MARSYS_JIS_BOOTSTRAP_HANDOFF.md MARSYS_JIS_BOOTSTRAP_HANDOFF.md

Then check if any files reference the old filename and update them:
  grep -r "MARSYS_JIS_BOOTSTRAP_HANDOFF" --include="*.md" -l .

For each file found, replace:
  MARSYS_JIS_BOOTSTRAP_HANDOFF.md  →  MARSYS_JIS_BOOTSTRAP_HANDOFF.md

CLAUDE.md §C item 11 mentions this file — confirm it is updated.

---

STEP 4: VERIFY NOTHING IS BROKEN
----------------------------------
Check there are zero remaining MARSYS-JIS occurrences in source files:
  grep -r "MARSYS-JIS\|MARSYS_JIS" \
    --include="*.md" --include="*.ts" --include="*.tsx" \
    --include="*.py" --include="*.yaml" --include="*.sh" \
    --exclude-dir="{node_modules,.git,.next,dist}" \
    . 2>/dev/null | grep -v "Binary"

Expected result: zero lines. If any appear, fix them before committing.

Run a quick TypeScript compile check:
  cd platform && npx tsc --noEmit 2>&1 | tail -10

Expected: clean (no errors introduced by the rename).

---

STEP 5: COMMIT
---------------
  git add -A
  git commit -m "chore: rename MARSYS-JIS → MARSYS-JIS throughout codebase

  Project renamed from MARSYS-JIS (Abhisek Mohanty Jyotish Intelligence System)
  to MARSYS-JIS (MARSYS Jyotish Intelligence System).

  Changes:
  - ~150 files: MARSYS-JIS → MARSYS-JIS (all docs, governance, source files)
  - MARSYS_JIS_BOOTSTRAP_HANDOFF.md → MARSYS_JIS_BOOTSTRAP_HANDOFF.md
  - useChatPreferences.ts: localStorage key amjis: → marsys-jis:

  GCP resource slugs unchanged (amjis-postgres, amjis-web, amjis_app,
  amjis-db-password, etc.) — infrastructure rename deferred per
  architectural decision (GCP names are internal, not user-visible)."

Print RENAME COMPLETE with:
  - Total files changed (from git diff --stat)
  - Confirmation that zero MARSYS-JIS occurrences remain
  - Confirmation that GCP slugs are intact
