---
artifact: SUVARNA_NATIVE_SETUP
canonical_id: SUVARNA_NATIVE_SETUP
version: "1.0"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-30
produced_in: session "Strategic Suvarṇa"
companion_of: "SUVARNA_CAMPAIGN_PLAN_v1_5.md §5.0b (launch readiness); SUVARNA_AUTONOMY_CHARTER_v1_0.md v1.5 §4, §13"
governed_by: "N-28 (the native performs only what only the native can physically do), N-25/N-25a/N-25b, N-23, N-29, N-31, N-34–N-38 (Strategic Suvarṇa rulings in plan v1.5 §8)"
changelog:
  - "1.0 (2026-09-30, plan set v1.5): first issue. The complete ordered list of the native's physical acts (NS.1–NS.10 before N-1; NP.1 after E7.1), each with the exact commands and the check the swarm runs afterwards. Everything else is done by Strategic Suvarṇa or the swarm (N-28)."
---

# Suvarṇa — the native's setup

**What this is.** The only things you have to do yourself. Everything not on this page is decided by Strategic Suvarṇa
(SS) or done by the swarm (N-28). You do not review, approve or supervise anything else. You may stop everything at any
time with the native hold (§3).

**How to use it.** Open Terminal as your own account (`Dev`, an administrator). Do the steps in order; each takes a few
minutes. Commands that start with `sudo` ask for your password. When a step says *SS does*, you do nothing: Strategic
Suvarṇa does it. After the last step, tell Strategic Suvarṇa "setup done"; it runs every check below in one go
(`python3 -m suvarna_tracker.native_setup_verify`, CODE-57, run as the swarm user, which writes
`$SUVARNA_HOME/evidence/launch/NS_VERIFY.json`) and tells you what, if anything, failed and exactly how to fix it.

**What you will need:** your Mac password; about 45 minutes; a second email address for the swarm's GitHub account;
your Claude subscription login; your GitHub login (org owner of `Marsys-Technologies`).

---

## §1 · Before N-1, in this order

### NS.0 · SS prepares (you do nothing)

*SS does:* stops the tracker supervisor and Monitor that today run as you from its own worktree; pushes `suvarna/hq`
and `suvarna/trunk` to `origin`; removes the three worktrees in `/Users/Dev/suvarna/{hq,trunk,lanes/*}` (they belong to
your main checkout's repository, which the swarm user must not write); creates the native-owned control checkout
`/Users/Dev/suvarna/control` at the pinned control release (N-37); writes the settings file into `/Users/Dev/suvarna/config/`.
SS tells you when NS.1 can start.

### NS.1 · Create the swarm's macOS user and the campaign group (N-25)

```
sudo sysadminctl -addUser suvarna -fullName "Suvarna swarm" -shell /bin/zsh -home /Users/suvarna -password -
sudo createhomedir -c -u suvarna
sudo dscl . create /Users/suvarna IsHidden 1
sudo dseditgroup -o create -r "Suvarna campaign" suvarna-campaign
sudo dseditgroup -o edit -a Dev -t user suvarna-campaign
sudo dseditgroup -o edit -a suvarna -t user suvarna-campaign
```

`-password -` asks you to type a password for the new user; choose any strong one and keep it in your password manager
(nobody needs it day to day). The user is a standard user, not an administrator.

**Check (swarm):** `id suvarna` lists `suvarna-campaign`; `dseditgroup -o checkmember -m suvarna admin` answers *no*;
`dseditgroup -o checkmember -m Dev suvarna-campaign` answers *yes*.

### NS.2 · Create the build broker's account and its one sudo rule (N-36)

The builder credential will belong to this account, so no swarm process can read it. The swarm may run exactly one
program as this account: the broker, which checks the hold, the scope and the running commit before any build.

```
dscl . -list /Users UniqueID | awk '$2==350'        # must print nothing; if it prints a line, use another number in 300–399 below
sudo sysadminctl -addUser _suvarnabuild -fullName "Suvarna build broker" -UID 350 -roleAccount -shell /usr/bin/false
sudo mkdir -p /Users/Dev/suvarna/broker
sudo chown _suvarnabuild /Users/Dev/suvarna/broker
sudo chmod 700 /Users/Dev/suvarna/broker
echo 'suvarna ALL=(_suvarnabuild) NOPASSWD: /opt/homebrew/bin/python3 /Users/Dev/suvarna/control/platform/scripts/governance/suvarna_tracker/broker.py *' | sudo tee /etc/sudoers.d/suvarna-build >/dev/null
sudo chmod 440 /etc/sudoers.d/suvarna-build
sudo visudo -cf /etc/sudoers.d/suvarna-build        # must say "parsed OK"
```

(`/opt/homebrew/bin/python3` is Python 3.14, owned by you and not writable by the swarm; the macOS `/usr/bin/python3` is
3.9, too old for the tracker code.)

**Check (swarm):** as `suvarna`, `sudo -n -l` lists exactly that one command; `test ! -r /Users/Dev/suvarna/broker`
succeeds (the folder is unreadable to the swarm).

### NS.3 · Lock your own credential files (N-29 priority 1)

Your account holds logins the swarm must never read. This makes every credential-like file under your home readable by
you only (it changes permissions, not contents; nothing of yours stops working):

```
chmod 700 ~/.config/gh ~/.config/madhav-admin ~/.claude
find /Users/Dev -maxdepth 8 -not -path '*/node_modules/*' -not -path '*/.git/*' \
  \( -name '.env' -o -name '.env.*' -o -name 'dbenv*.sh' -o -name 'pgenv*.sh' -o -name '*key*.pem' \
     -o -name 'auth.json' -o -name 'hosts.yml' -o -name 'credentials*.json' -o -name '*service-account*.json' \) \
  ! -name '*.example' ! -name '*.sample' ! -name '*.template' ! -name '*.example.*' \
  -perm -o=r -print -exec chmod go-rwx {} +
```

It prints each file it fixes (about 20 today, measured 2026-09-30; `dbenv.sh` and `dbenv_builder.sh` were already fixed
by N-25a). It can take two or three minutes.

**Check (swarm):** as `suvarna`, every path in the Monitor's isolation probe list (`~Dev/.config/{gh,madhav-admin}`,
`~Dev/.codex/auth.json`, `/Users/Dev/madhav-l3/dbenv*.sh`, every `platform/.env*` under `/Users/Dev`) is unreadable,
and the same `find` (run as `suvarna`, with `-readable` instead of `-perm -o=r`) prints nothing. The Monitor repeats
this probe every five minutes after launch; a new readable secret blocks dispatch (CODE-38).

### NS.4 · Give the campaign folders their owners (N-37)

After NS.0 and NS.1. The swarm owns its working folders; you own the authority and control folders, which the swarm
can read but never change.

```
cd /Users/Dev/suvarna
sudo mkdir -p hq trunk lanes evidence run .repo authority config control
sudo mv run/DECISIONS.jsonl run/DECISIONS.jsonl.lock authority/
sudo chown -R suvarna:suvarna-campaign hq trunk lanes evidence run .repo
sudo chmod 2775 hq trunk lanes evidence run .repo
sudo chmod -R +a "group:suvarna-campaign allow list,search,add_file,add_subdirectory,delete_child,read,write,append,execute,readattr,writeattr,readextattr,writeextattr,readsecurity,file_inherit,directory_inherit" hq trunk lanes evidence run .repo
sudo chown -R Dev:staff authority config control
sudo chmod 755 authority config control
sudo touch authority/HOLDS.jsonl authority/HOLD_CLEARS.jsonl
sudo chown Dev:suvarna-campaign authority/HOLDS.jsonl
sudo chmod 664 authority/HOLDS.jsonl
sudo chflags uappnd authority/HOLDS.jsonl
sudo chown Dev:staff authority/HOLD_CLEARS.jsonl
sudo chmod 644 authority/HOLD_CLEARS.jsonl
sudo -u suvarna mkdir -p -m 700 /Users/suvarna/.config/suvarna/bin
sudo install -o suvarna -g staff -m 600 /Users/Dev/.config/suvarna/pgenv.sh /Users/suvarna/.config/suvarna/pgenv.sh
```

What this gives: the swarm can append a hold to `authority/HOLDS.jsonl` but can never rewrite, truncate or delete it
(N-35); it can read the decisions log but not write, replace or rename it (N-37); the read-only database login moves to
the swarm's own home (you keep your copy, unreadable to the swarm).

The second line moves the decisions log out of the swarm's working folder before that folder changes owner. The swarm
makes its own clone in `.repo` and its worktrees `hq` and `trunk` itself (first runner start, NS.8); nothing of that
needs you.

**Check (swarm):** as `suvarna`: appending a test hold line to `authority/HOLDS.jsonl` succeeds and is then cleared
by SS; truncating it, renaming it or writing `authority/DECISIONS.jsonl` fails with "Operation not permitted" or
"Permission denied"; `authority/`, `config/`, `control/` are not writable; `~/.config/suvarna/pgenv.sh` is mode 600,
owned by `suvarna`, and logs in as `suvarna_reader`.

### NS.5 · The swarm's own GitHub account and token (N-25, N-38)

1. In a private browser window, create a GitHub account for the swarm, e.g. **`marsys-suvarna-bot`**, with a second
   email address (a `+suvarna` alias of yours works). Turn on two-factor authentication for it.
2. As yourself (org owner), give it **Write** on the repository (not Maintain, not Admin):
   `gh api -X PUT repos/Marsys-Technologies/Madhav/collaborators/marsys-suvarna-bot -f permission=push`
   then accept the invitation in the bot's browser window.
3. As the bot: Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate:
   resource owner **Marsys-Technologies**; repository access **Only select repositories → Madhav**; expiry 90 days;
   permissions: **Contents: Read and write · Pull requests: Read and write · Metadata: Read · Commit statuses: Read ·
   Checks: Read · Actions: Read**; everything else **No access** (in particular Administration, Workflows, Secrets). If the
   org requires approval of fine-grained tokens, approve it as yourself (Org settings → Personal access tokens → Pending).
4. Hand the token to the swarm user only (paste it, then press Enter and Ctrl-D; it is never written to a file you keep):
   ```
   sudo -iu suvarna gh auth login --hostname github.com --git-protocol https --with-token
   sudo -iu suvarna gh auth setup-git
   sudo -iu suvarna git config --global user.name "Suvarna swarm"
   sudo -iu suvarna git config --global user.email "marsys-suvarna-bot@users.noreply.github.com"
   ```

**Check (swarm):** `gh auth status` as `suvarna` shows `marsys-suvarna-bot`; the repository's permissions for it read
`push: true, maintain: false, admin: false`; the LG.5 drill (plan §5.0b) proves a direct push to `main` is refused, a
merge of a throwaway PR with a failing required check is refused, a green throwaway PR merges through the merge queue
only via `merge_gate`, and a ruleset edit is refused.

### NS.6 · Branch protection: add the path guard to `main`'s required checks (N-25b, N-38)

`main` is already protected by the org ruleset **"main protection (org migration, merge queue)"** (id 20141220,
measured 2026-09-30): four required checks, pull requests with 0 required approvals, a squash merge queue, no bypass
actors. After SS's control PR E0.2 (the CI job `Suvarṇa path guard`) is merged, add that job to the required checks:

GitHub → Marsys-Technologies/Madhav → Settings → Rules → Rulesets → *main protection (org migration, merge queue)* →
**Require status checks to pass** → Add checks → type `Suvarṇa path guard` → select it → **Save changes**. Leave
everything else as it is (no bypass actors; required approvals stay 0, N-25b).

Then confirm who can merge (Write or higher) — you, the bot, and existing automation only:
`gh api 'repos/Marsys-Technologies/Madhav/collaborators?affiliation=all&per_page=100' --jq '.[] | select(.permissions.push) | .login'`
SS reads the list; if it shows anyone unexpected, SS asks you to remove that person's access (one command it gives you).

**Check (swarm):** `main_protected` (v2 spec, CODE-40) reads done: the required checks include `Suvarṇa path guard`,
no bypass actor, required approvals 0, merge queue on, the bot is not Admin/Maintain.

### NS.7 · Claude login for the swarm user (N-23)

The swarm runs on your Claude subscription until G2 (N-23). It gets its own copy of Claude Code, pinned to the version
the settings were tested against (2.1.239, runtime document §7), and, because system services cannot use a Keychain
login, a long-lived token:

```
sudo -iu suvarna sh -c 'curl -fsSL https://claude.ai/install.sh | bash -s 2.1.239'
sudo -iu suvarna /Users/suvarna/.local/bin/claude setup-token
```

Follow the browser link, sign in with your subscription account, and paste the token it prints into:

```
sudo -iu suvarna sh -c 'umask 077; cat > ~/.config/suvarna/claude_oauth.env'
```

Type `CLAUDE_CODE_OAUTH_TOKEN=` followed by the token, press Enter, then Ctrl-D.

**Check (swarm):** the runner starts one no-op pass (`claude -p "reply OK" --settings /Users/Dev/suvarna/config/claude-settings.json --permission-mode dontAsk`) as `suvarna` and gets `OK`; the file is mode 600, owned by `suvarna`.

### NS.8 · Install the always-on services (N-34)

The tracker, the Monitor (with the watchdog) and the two Conductor runners run as the `suvarna` user as system services,
so they survive restarts and need no one to re-arm them. SS generates the service files into the control checkout first.

```
sudo install -o root -g wheel -m 644 /Users/Dev/suvarna/control/platform/scripts/governance/suvarna_tracker/runtime/launchd/com.marsys.suvarna.*.plist /Library/LaunchDaemons/
for s in tracker monitor runner.engine runner.exec; do sudo launchctl bootstrap system /Library/LaunchDaemons/com.marsys.suvarna.$s.plist; done
```

The two runners start **idle**: they do nothing until N-1 is recorded (ENGINE-EARLY-START).

*SS does:* installs its own decision runtime as a user agent of your account (`~/Library/LaunchAgents/com.marsys.suvarna.strategic.plist`, no `sudo`; L.18).

**Check (swarm):** `launchctl print system/com.marsys.suvarna.monitor` shows `state = running` (same for the tracker and
both runners); `curl -s http://127.0.0.1:8765/api/health` answers `"ok": true`; the Monitor reads every stage-S1 check
`ok` (CODE-38).

### NS.9 · Power and updates (once, for the campaign)

Keep the Mac on AC power with the lid open. Then:

```
sudo pmset -c sleep 0 disksleep 0
sudo pmset -a autorestart 1
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false
sudo defaults write /Library/Preferences/com.apple.commerce AutoUpdateRestartRequired -bool false
```

**Check (swarm):** `pmset -g custom` shows `sleep 0` under AC Power; `pmset -g` shows `autorestart 1`;
`defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates` prints `0`.

### NS.10 · Say "go" (N-1)

When SS tells you the final plan set is reconciled (after both independent reviews, N-30) and every launch check is
green, say **"go"** (or "no") in the Strategic Suvarṇa session. SS records N-1 with your words. That is the only
approval you give.

---

## §2 · After N-1 (only when SS asks)

### NP.1 · Provision the build identity (E7.2), once, after the E7.1 change is deployed

This needs an administrator database login, which only you hold. Track E prepares a one-shot script (like the D6 reader
script you ran on 2026-09-29) that creates the builder account (role `guest`, status `active`), its grants (the
canonical chart `build` grant and the global-L0 grant, N-31), writes its secret to `/Users/Dev/suvarna/broker/builder.env`
(owned by `_suvarnabuild`, mode 600) and the non-secret provisioning record to `$SUVARNA_HOME/run/builder_identity.json`.
SS gives you the exact command on the day (a dry run first, then `--apply` with the dry run's plan hash).

**Check (swarm):** the Monitor's `builder_scope` check reads `ok` through the broker's authenticated preflight.

### What else could ever need you

- **Rotating or revoking a credential** (the reader login, the builder, the bot's token when it expires after 90 days,
  the Claude token): SS tells you which, and gives you the command.
- **A scope or end-state change** (for example certifying a second chart, or adding or removing assets from the 127):
  SS brings it to you with a recommendation.
- **The API key at G2** (N-23): if SS's measured data says the runner should move off your subscription, it asks you to
  create a key and gives you the command to hand it to the swarm user.

## §3 · Your veto, at any time

To stop everything new at once (running items finish; no build, merge or dispatch starts):

```
python3 -m suvarna_tracker.hold --set --native --reason "<why>"      # from /Users/Dev/suvarna/control/platform/scripts/governance
```

(Or tell Strategic Suvarṇa "hold" — it sets it for you.) Only you can clear a hold you set:
`python3 -m suvarna_tracker.hold --clear <hold id> --native`. The dashboard shows every hold and every SS decision; you
can veto any decision by saying so to SS, which records your words.
