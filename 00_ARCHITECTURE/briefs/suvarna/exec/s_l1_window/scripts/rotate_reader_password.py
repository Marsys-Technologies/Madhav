#!/usr/bin/env python3
"""rotate_reader_password.py --instance NAME [--dry-run]

Rotates the Cloud SQL password of role suvarna_reader WITHOUT argv exposure and WITHOUT ever printing it:
  - the new value is generated in-process (secrets.token_urlsafe) and exists only in this process's memory;
  - it is sent in the BODY of an HTTPS request to the Cloud SQL Admin API (users.update), authenticated with the operator's own
    `gcloud auth print-access-token` (read in-process, never printed) -- NOT on any command line;
  - ~/.config/suvarna/pgenv.sh is rewritten in place (same mode, atomic replace) by replacing the single PGPASSWORD assignment;
  - verification: new login -> current_user + read-only session; the OLD password must be refused. Output = timestamps and PASS/FAIL only.
--dry-run performs only the layout check of pgenv.sh and the token read (no change anywhere).
Status: the REST call itself is UNVERIFIED until its first real use (it is a write); the equivalent gcloud form is
`gcloud sql users set-password suvarna_reader --instance=NAME --prompt-for-password` (reads the value from a TTY, no argv).
"""
import argparse, datetime, json, os, re, secrets, stat, subprocess, sys, time, urllib.request, urllib.error
F = os.path.expanduser('~/.config/suvarna/pgenv.sh'); USER = 'suvarna_reader'; PROJECT = 'madhav-astrology'
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
PAT = re.compile(r'^(\s*(?:export\s+)?PGPASSWORD=)(["\']?)([^"\'\n]*)(["\']?)[ \t]*$', re.M)
def api(method, path, token, body=None):
    r = urllib.request.Request('https://sqladmin.googleapis.com/v1/' + path, method=method, data=None if body is None else json.dumps(body).encode(),
                               headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=60) as f: return json.load(f)
def login(pw=None):
    env = dict(os.environ, PGCONNECT_TIMEOUT='10')
    if pw is not None: env['RB_TEST_PW'] = pw
    cmd = ('source "$HOME/.config/suvarna/pgenv.sh" >/dev/null 2>&1; [ -n "$RB_TEST_PW" ] && export PGPASSWORD="$RB_TEST_PW"; '
           'psql -X -A -t -F "|" -c "select current_user, current_setting(\'transaction_read_only\')"')
    return subprocess.run(['bash', '-c', cmd], env=env, capture_output=True, text=True)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--instance', required=True); ap.add_argument('--dry-run', action='store_true'); a = ap.parse_args()
    src = open(F).read(); ms = PAT.findall(src)
    if len(ms) != 1: sys.exit(now() + ' FAIL layout: PGPASSWORD assignments found = %d; nothing changed' % len(ms))
    print(now() + ' PASS layout: exactly one PGPASSWORD assignment')
    token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()
    print(now() + ' PASS access token read in-process')
    if a.dry_run: print(now() + ' dry-run: nothing changed'); return
    old = ms[0][2]; new = secrets.token_urlsafe(32)
    try:
        op = api('PUT', f'projects/{PROJECT}/instances/{a.instance}/users?name={USER}', token, {'name': USER, 'password': new})
        for _ in range(60):
            if op.get('status') == 'DONE': break
            time.sleep(5); op = api('GET', f'projects/{PROJECT}/operations/{op["name"]}', token)
        if op.get('status') != 'DONE' or op.get('error'): raise RuntimeError('operation not DONE/clean')
    except Exception as e:
        sys.exit(now() + ' FAIL set-password (%s): the old password is still valid unless the operation completed; nothing written locally' % type(e).__name__)
    print(now() + ' PASS set-password operation DONE')
    try:
        mode = stat.S_IMODE(os.stat(F).st_mode); tmp = F + '.new'
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode); os.fchmod(fd, mode)
        with os.fdopen(fd, 'w') as fh: fh.write(PAT.sub(lambda m: m.group(1) + m.group(2) + new + m.group(4), src))
        os.replace(tmp, F)
    except Exception as e:
        sys.exit(now() + ' FAIL file write AFTER set-password (%s): the reader password is now unknown to every helper; repeat this procedure after fixing the file permissions (no data risk: the role is read-only)' % type(e).__name__)
    print(now() + ' PASS credential source rewritten, mode %s preserved' % oct(mode))
    x = login(); print(now() + (' PASS' if x.returncode == 0 and x.stdout.strip() == 'suvarna_reader|on' else ' FAIL') + ' new credential: current_user + read-only session')
    y = login(old); print(now() + (' PASS' if y.returncode != 0 and 'password authentication failed' in y.stderr else ' FAIL') + ' old password no longer logs in')
if __name__ == '__main__': main()
