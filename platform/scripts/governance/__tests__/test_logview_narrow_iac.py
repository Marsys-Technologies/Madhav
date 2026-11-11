"""LOGVIEW-NARROW-IAC oracles (SR-LOGVIEW-NARROW, SR-LOGVIEW-NARROW-KEEP; root CLAUDE.md §N.8).

Condition (b) of SR-LOGVIEW-NARROW: no workflow-run code reads Cloud Logging as github-actions@
outside a narrow log view. The first failure was invisible to a grep of .github/workflows because
the read sat in a TypeScript script a workflow runs, so the detector scans workflows AND scripts.
Text-level checks only: no terraform, no gcloud, no network. Sources: Google Cloud Logging docs
"Configure log views on a log bucket" (basic filter = SOURCE / resource.type / LOG_ID joined by AND;
single-view access = viewAccessor with a resource.name IAM condition) and the Terraform resources
named in infra/iam/main.tf.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TF = (ROOT / 'infra/iam/main.tf').read_text()
PREFLIGHT = (ROOT / 'platform/scripts/data-plane-cutover-preflight.ts').read_text()
VIEW, BUCKET, LOCATION = 'cloudsql_restore_audit', '_Required', 'global'


def block(text, header):
    """The brace-balanced body of the first block that starts with `header` (quotes in HCL strings are escaped)."""
    start = text.index(header)
    depth, i = 0, text.index('{', start)
    for j in range(i, len(text)):
        depth += {'{': 1, '}': -1}.get(text[j], 0)
        if depth == 0:
            return text[start:j + 1]
    raise AssertionError('unbalanced block ' + header)


def logging_reads_without_view(source, kind):
    """Every Cloud Logging read in `source` whose command carries no --view=. kind: 'sh' (yml/sh) or 'ts'."""
    bad = []
    if kind == 'sh':
        joined = re.sub(r'\\\n', ' ', source)
        for m in re.finditer(r'gcloud\s+(?:beta\s+)?logging\s+read\b[^\n]*', joined):
            if '--view=' not in m.group(0):
                bad.append(m.group(0)[:120])
    else:
        for m in re.finditer(r"'logging'\s*,\s*'read'", source):
            tail = source[m.start():]
            command = tail[:re.search(r'\]\s*[,)\n]', tail).end()]      # the argv array this read sits in
            if '--view=' not in command:
                bad.append(command[:120])
    return bad


# C1 — the detector itself can read false (N.8): a project-wide read is flagged, a view read is not.
def test_detector_flags_a_read_without_a_view():
    assert logging_reads_without_view('gcloud logging read "x" --project p --limit=1', 'sh')
    assert logging_reads_without_view('gcloud logging read "x" \\\n  --project p --bucket=_Default --view=v', 'sh') == []
    assert logging_reads_without_view("execFileSync('gcloud', ['logging', 'read', f, '--project', p])", 'ts')
    assert logging_reads_without_view("['logging', 'read', f, `--view=${v}`])", 'ts') == []


# C2 — repo-wide: no GCP-authenticated workflow or workflow-run script reads logs without a view.
def test_no_workflow_or_workflow_script_reads_logs_project_wide():
    offenders = []
    for path in sorted((ROOT / '.github/workflows').glob('*.yml')):
        offenders += [(str(path.relative_to(ROOT)), r) for r in logging_reads_without_view(path.read_text(), 'sh')]
    for path in sorted((ROOT / 'platform/scripts').rglob('*')):
        if path.suffix in ('.ts', '.sh') and 'node_modules' not in path.parts:
            offenders += [(str(path.relative_to(ROOT)), r)
                          for r in logging_reads_without_view(path.read_text(), 'sh' if path.suffix == '.sh' else 'ts')]
    assert offenders == []


# C3 — the cutover preflight reads the audit log through exactly the view Terraform declares.
def test_preflight_view_matches_terraform_view():
    consts = re.search(r"CLOUDSQL_RESTORE_AUDIT_LOG_VIEW = \{\s*bucket: '([^']+)', location: '([^']+)', view: '([^']+)',?\s*\} as const", PREFLIGHT)
    assert consts and consts.groups() == (BUCKET, LOCATION, VIEW)
    view = block(TF, 'resource "google_logging_log_view" "cloudsql_restore_audit"')
    assert f'name        = "{VIEW}"' in view
    assert f'buckets/{BUCKET}"' in view and f'locations/{LOCATION}/' in view
    helper = block(PREFLIGHT, 'export function cloudSqlRestoreAuditReadArgs')
    assert '`--bucket=${bucket}`, `--location=${location}`, `--view=${view}`' in helper
    assert 'cloudSqlRestoreAuditReadArgs(project, receipt.restoreOperationId)' in PREFLIGHT


# C4 — the view shows only Cloud SQL Admin Activity entries (basic filter: AND only, no OR).
def test_view_filter_admits_only_cloudsql_admin_activity():
    filt = re.search(r'filter\s*=\s*"((?:[^"\\]|\\.)*)"', block(TF, 'resource "google_logging_log_view" "cloudsql_restore_audit"')).group(1)
    clauses = [c.strip() for c in filt.split(' AND ')]
    assert clauses == [r'SOURCE(\"projects/${var.gcp_project}\")',
                       r'resource.type = \"cloudsql_database\"',
                       r'LOG_ID(\"cloudaudit.googleapis.com/activity\")']
    assert ' OR ' not in filt


# C5 — viewAccessor is bound only with a condition naming that one view; never unconditionally.
def test_view_accessor_binding_is_conditioned_to_the_one_view():
    members = re.findall(r'resource "google_project_iam_member" "[^"]+" \{', TF)
    accessor_blocks = [block(TF, h) for h in members if 'roles/logging.viewAccessor' in block(TF, h)]
    assert len(accessor_blocks) == 1
    b = accessor_blocks[0]
    assert 'serviceAccount:github-actions@${var.gcp_project}.iam.gserviceaccount.com' in b
    assert r'resource.name == \"projects/${var.gcp_project}/locations/global/buckets/_Required/views/cloudsql_restore_audit\"' in b


# C6 — the config-reader role that replaces the viewer's plan-time reads carries no log-entry read.
def test_config_reader_role_cannot_read_log_entries():
    role = block(TF, 'resource "google_project_iam_custom_role" "logging_config_reader"')
    perms = re.findall(r'"(logging\.[A-Za-z.]+)"', role)
    assert perms and all(re.fullmatch(r'logging\.(buckets|exclusions|views)\.(get|list)', p) for p in perms)


# C7 — merging changes nothing: the legacy viewer is kept by default, behind a flag, without a destroy-recreate.
def test_legacy_viewer_is_kept_by_default_and_removable_by_flag():
    var = block(TF, 'variable "retain_project_wide_logging_viewer"')
    assert 'default     = true' in var and 'type        = bool' in var
    legacy = block(TF, 'resource "google_project_iam_member" "github_actions_logging_viewer"')
    assert 'count   = var.retain_project_wide_logging_viewer ? 1 : 0' in legacy and 'roles/logging.viewer' in legacy
    moved = block(TF, 'moved')
    assert 'from = google_project_iam_member.github_actions_logging_viewer\n' in moved
    assert 'to   = google_project_iam_member.github_actions_logging_viewer[0]' in moved
    assert TF.count('"roles/logging.viewer"') == 1
