---
artifact: SUVARNA_NATIVE_SETUP
canonical_id: SUVARNA_NATIVE_SETUP
version: "1.1"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-30
produced_in: session "Strategic Suvarṇa"
companion_of: "SUVARNA_CAMPAIGN_PLAN_v1_5.md §5.0b (launch readiness); SUVARNA_AUTONOMY_CHARTER_v1_0.md v1.5 §4, §13"
governed_by: "N-28 (the native performs only what only the native can physically do), N-25/N-25a/N-25b, N-23, N-29, N-31, N-34–N-38 (Strategic Suvarṇa rulings in plan v1.5 §8)"
changelog:
  - "1.1 (2026-09-30): rewritten as a one-page guide for a non-technical reader. NS.1–NS.4 and
    NS.8–NS.9 are now one script — `platform/scripts/governance/suvarna_tracker/runtime/native_setup.sh`
    — run twice (`--check` then `sudo bash native_setup.sh --apply`) instead of typed one at a time.
    NS.5 (GitHub bot token) and NS.7 (Claude token) are the same script's `--github-token` and
    `--claude-token` interactive helpers: numbered browser clicks, then one command each. The
    detailed per-step reference (what each step changes on disk, and the exact checks the swarm
    runs afterwards) moves to the Appendix for reviewers; the main body is now five steps. §3 (the
    native's veto) is unchanged and stays prominent. No governing rule (N-25 family, N-28, N-36–38)
    changed — this is a packaging change only, reviewed and tested in dry-run/syntax mode
    (`platform/scripts/governance/suvarna_tracker/tests/test_native_setup.py`, 20/20 passing) before
    the native ever runs it for real."
  - "1.0 (2026-09-30, plan set v1.5): first issue. The complete ordered list of the native's physical acts (NS.1–NS.10 before N-1; NP.1 after E7.1), each with the exact commands and the check the swarm runs afterwards. Everything else is done by Strategic Suvarṇa or the swarm (N-28)."
---

# Suvarṇa — the native's setup

**What this is, in five lines.** The Suvarṇa swarm needs its own macOS account, separate from
yours, so it can build and test things without ever touching your files or credentials. This page
walks you through creating that account and its guardrails. It is the only thing you have to do
yourself — everything else is decided by Strategic Suvarṇa (SS) or done by the swarm itself. You
do not review, approve, or supervise anything beyond what is on this page. You can stop everything,
at any time, with the veto in §3 below.

**What you will need:** your Mac password; about 20 minutes; a second email address (for the
swarm's own GitHub account); your Claude subscription login; your GitHub login (you must be the
owner of the `Marsys-Technologies` org).

---

## §3 · Your veto, at any time

This works before, during, and after every step below — keep it in mind, not just at the end.

To stop everything new at once (running items finish; no build, merge, or dispatch starts):

```
python3 -m suvarna_tracker.hold --set --native --reason "<why>"      # from /Users/Dev/suvarna/control/platform/scripts/governance
```

Or just tell Strategic Suvarṇa **"hold"** — it sets this for you; you do not need to type anything.
Only you can clear a hold you set: `python3 -m suvarna_tracker.hold --clear <hold id> --native`. The
dashboard shows every hold and every SS decision; you can veto any decision just by saying so to SS,
which records your words.

---

## The five steps

Do these in order, in the Terminal app (⌘-Space, type "Terminal", press Enter). Everything you type
below is one line, copy-pasted as a whole. Lines starting with `sudo` will ask for your Mac
password once per step, not once per line.

### Step 1 — Run the check

```
cd /Users/Dev/suvarna/control/platform/scripts/governance/suvarna_tracker/runtime
bash native_setup.sh --check
```

This only looks — it changes nothing. It tells you what is already set up and what Step 2 is about
to do. If SS told you `NS.0` is done (it prepares the ground before you start), you're clear to
continue.

### Step 2 — Run the setup

```
sudo bash native_setup.sh --apply
```

Type your password when asked. This one command does everything that used to be nine separate
steps: it creates the swarm's own macOS account (a standard account, not an administrator), a
second, locked-down account that alone can start a build, locks your own credential files so the
swarm account can never read them, sets up the shared folders, installs the always-on services (if
they're ready — it skips them with a clear message otherwise, and that's fine), and keeps the Mac
awake on power while the campaign runs. Every part of it is safe to run again — if a part is already
done, it says so and moves on. If anything fails partway, it stops immediately, tells you in plain
language what failed, and gives you the exact command to undo everything it did. Tell Strategic
Suvarṇa if that happens.

### Step 3 — The swarm's own GitHub account

The swarm needs its own GitHub identity so its commits are never mistaken for yours, and so it can
never touch anything with your own access.

1. Open a **private/incognito browser window** and go to github.com.
2. Sign up for a **new** GitHub account for the swarm — for example `marsys-suvarna-bot` — using a
   **second email address** (a `+suvarna` alias of your own email works, e.g.
   `mail.abhisek.mohanty+suvarna@gmail.com`). Turn on **two-factor authentication** for it.
3. Back in your own (main) browser: go to the Madhav repository on GitHub → **Settings → Collaborators**
   → add `marsys-suvarna-bot` with **Write** access (not Maintain, not Admin). Then, in the bot's
   private window, accept the invitation email.
4. Still in the bot's private window: **Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token.** Fill in:
   - Resource owner: `Marsys-Technologies`
   - Repository access: **Only select repositories** → `Madhav`
   - Expiration: 90 days
   - Permissions: **Contents** (Read and write), **Pull requests** (Read and write), **Metadata**
     (Read), **Commit statuses** (Read), **Checks** (Read), **Actions** (Read). Leave everything
     else as **No access**.
5. Click **Generate token** and **copy it** — GitHub will not show it to you again.

Now, back in Terminal:

```
sudo bash native_setup.sh --github-token
```

Paste the token when it asks (it will not appear on screen — that's normal, just paste and press
Enter). The script hands the token to the swarm's account and checks that it worked.

### Step 4 — The Claude token

The swarm runs on your Claude subscription for now, using its own copy of Claude Code so it never
touches your own login session.

```
sudo bash native_setup.sh --claude-token
```

Follow the instructions it prints: it opens a login link — sign in with your own Claude subscription
account — and then prints a token in the Terminal window. Copy that token, then paste it back in
when the script asks for it (again, it will not appear on screen). The script checks that it worked
with a harmless test message.

### Step 5 — Tell Strategic Suvarṇa

Once Steps 1–4 are done, tell Strategic Suvarṇa **"setup done"**. It runs every check in one go
(writing `$SUVARNA_HOME/evidence/launch/NS_VERIFY.json` — you can also produce this yourself any
time with `sudo bash native_setup.sh --verify`) and tells you exactly what, if anything, still needs
attention, in plain language, with the exact fix.

After that, SS will let you know when the final plan set is reconciled and every launch check is
green — at that point, and only then, it asks you to say **"go"** (or "no"). That's the only
approval you give (this is `NS.10` / `N-1` — see the Appendix).

---

## Appendix — detailed reference (for reviewers; not required reading to complete setup)

This appendix explains, step by step, exactly what changes on disk and how the swarm verifies it —
the same content as v1.0 of this document, reorganized to sit behind the five steps above rather
than in front of them. Nothing in this appendix requires you to type anything the five steps above
did not already cover; it exists so a reviewer (human or agent) can audit the setup without
re-deriving it from the script's source.

### How the script maps to the old step numbers

| Old step | What it covers | New home |
|---|---|---|
| NS.0 | SS prepares the ground (worktrees, control checkout, settings file) — you do nothing | unchanged; SS tells you when Step 1 can start |
| NS.1 | Swarm macOS user + campaign group | `native_setup.sh --apply` |
| NS.2 | Build broker account + its one sudoers rule | `native_setup.sh --apply` |
| NS.3 | Lock your own credential-like files | `native_setup.sh --apply` |
| NS.4 | Campaign folder ownership/ACLs | `native_setup.sh --apply` |
| NS.5 | GitHub bot account + token | Step 3 (browser clicks) + `native_setup.sh --github-token` |
| NS.6 | Branch protection path guard | unchanged; SS walks you through the one-time ruleset click when its control PR lands |
| NS.7 | Claude token for the swarm | Step 4 (browser link) + `native_setup.sh --claude-token` |
| NS.8 | Install the always-on services | `native_setup.sh --apply` (skips cleanly if the service files aren't generated yet) |
| NS.9 | Power + software-update settings | `native_setup.sh --apply` |
| NS.10 | Say "go" | unchanged — Step 5 above, done in the Strategic Suvarṇa session, not Terminal |

### NS.1 — the swarm's macOS user and campaign group (N-25)

Creates a standard (non-administrator) account named `suvarna`, hidden from the login window, with
a random password the script generates and stores only in the System keychain item
`"suvarna-swarm-user"` — nobody, including you, needs to type or read it day to day. Creates a group
`suvarna-campaign` containing both `suvarna` and `Dev` (you).

**The swarm verifies:** `id suvarna` lists `suvarna-campaign`; `suvarna` is not in the `admin`
group; `Dev` is a member of `suvarna-campaign`.

### NS.2 — the build broker account and its one sudo rule (N-36)

Creates a role account `_suvarnabuild` (uid chosen automatically from the first free id between 300
and 399) that alone can run the build broker — a program that checks the hold, the scope, and the
running commit before any build starts. The one sudoers rule that lets `suvarna` invoke this,
exactly this program and nothing else, is written to a temporary file, checked with `visudo -cf`,
and only installed to `/etc/sudoers.d/suvarna-build` (mode 440) if that check passes. If it fails,
nothing is installed and you're told plainly what to report back to SS.

**The swarm verifies:** as `suvarna`, `sudo -n -l` lists exactly that one command; the broker's own
folder is unreadable to the swarm account.

### NS.3 — locking your own credential-like files (N-29 priority 1)

Scans under `/Users/Dev` (not deeper than 8 folders, skipping `node_modules` and `.git`) for files
that look like credentials — `.env` files, `dbenv*.sh`/`pgenv*.sh`, `*key*.pem`, `auth.json`,
`hosts.yml`, `credentials*.json`, `*service-account*.json` — excluding anything named `*.example`,
`*.sample` or `*.template`. Anything found readable by anyone other than you has its permissions
tightened (`chmod go-rwx`) so only you can read it. **File contents are never read or printed** —
only the path of each file that was changed. This typically touches about 20 files and takes two or
three minutes. This is a one-way tightening: `--undo` (see below) does not loosen these files back
up, because re-exposing a credential is never a safe "undo."

**The swarm verifies:** every path on its watch list is unreadable to `suvarna`; it repeats this
check every five minutes for as long as the campaign runs, and a newly-readable secret blocks
dispatch immediately.

### NS.4 — campaign folder ownership (N-37)

Creates (if not already present) `hq`, `trunk`, `lanes`, `evidence`, `run`, `.repo`,
`authority`, `config`, `control` under `$SUVARNA_HOME` (default `/Users/Dev/suvarna`). The swarm
owns and can freely use the first group; you own the second group, which the swarm can read but
never change. Moves the decisions log into `authority/` if it's still sitting in the swarm's working
folder (harmless to skip if it's already been moved, or was never there). Prepares
`authority/HOLDS.jsonl` (append-only — the swarm can add a hold but never rewrite or delete one) and
`authority/HOLD_CLEARS.jsonl`. Gives the swarm its own copy of the read-only database login, in its
own home folder, mode 600 — your own copy is untouched and still unreadable to the swarm.

**The swarm verifies:** appending a test hold succeeds and is later cleared by SS; truncating,
renaming, or writing the decisions log fails with a permission error; the read-only login logs in
successfully as `suvarna_reader`.

### NS.8 — the always-on services (N-34)

Installs the tracker, the Monitor (with its watchdog), and the two Conductor runners as macOS
LaunchDaemons under the `suvarna` account, so they restart automatically and nobody has to re-arm
them by hand. **This step only runs for a service whose plist file already exists** in the control
checkout — SS generates those files first; if one isn't ready yet, the script skips it with a clear
message rather than failing. The two runners start idle and do nothing until Step 5's "go" (`N-1`)
is recorded.

**The swarm verifies:** each installed service shows `state = running`; a local health check answers
`"ok": true`.

### NS.9 — power and software-update settings (once, for the campaign)

Keeps the Mac from sleeping while on power, turns on auto-restart after a power loss, and pauses
fully-automatic macOS updates and forced update-restarts for the duration of the campaign (you can
still update manually any time).

**The swarm verifies:** the sleep, auto-restart, and update settings all read back as expected.

### NP.1 — provisioning the build identity (after N-1, only when SS asks)

This needs an administrator database login, which only you hold, so it stays a separate one-off
script SS hands you on the day (dry run first, then `--apply` with the dry run's plan hash) — not
part of `native_setup.sh`. Full detail: the builder account (role `guest`, status `active`), its
grants (the canonical chart `build` grant and the global-L0 grant, N-31), its secret written to
`/Users/Dev/suvarna/broker/builder.env` (owned by `_suvarnabuild`, mode 600), and a non-secret
provisioning record at `$SUVARNA_HOME/run/builder_identity.json`.

**The swarm verifies:** the Monitor's `builder_scope` check reads `ok` through the broker's
authenticated preflight.

### `--undo`: reversing the setup

```
sudo bash native_setup.sh --undo
```

Removes the always-on services, the sudoers rule, the `_suvarnabuild` account, and the `suvarna`
account and `suvarna-campaign` group, and returns folder ownership to you. **It never deletes a data
folder** — only ownership and access rules change back. It also never re-loosens the credential
files NS.3 locked (see above) — that tightening is intentionally permanent. If any single step can't
fully undo (for example, an account already removed by hand), it says so and continues with the
rest rather than stopping.

### `--verify`: the swarm's own report card

```
sudo bash native_setup.sh --verify
```

Runs every check listed above in one pass and writes a flat PASS/FAIL map to
`$SUVARNA_HOME/evidence/launch/NS_VERIFY.json`. This is the same thing Strategic Suvarṇa runs when
you tell it "setup done" (Step 5) — running it yourself just lets you see the same report without
waiting.

### What else could ever need you

- **Rotating or revoking a credential** (the reader login, the builder, the bot's token when it
  expires after 90 days, the Claude token): SS tells you which, and gives you the exact command.
- **A scope or end-state change** (for example certifying a second chart, or adding or removing
  assets from the 127): SS brings it to you with a recommendation.
- **The API key at G2** (N-23): if SS's measured data says the runner should move off your
  subscription, it asks you to create a key and gives you the command to hand it to the swarm user.

### Safety notes for reviewers

- The script refuses to run `--apply`/`--undo`/`--verify` unless invoked with `sudo` by an account
  that is an actual administrator on the Mac (checked via `SUDO_USER`'s group membership), and
  unless `$SUVARNA_HOME` already exists (i.e., unless SS has completed NS.0).
- Every mutating step checks its own current state first and reports "already done" rather than
  repeating an action — verified in `test_native_setup.py` by asserting a second `--apply` run
  issues zero commands.
- A failure at any step halts immediately, before the next step runs, and prints the exact `--undo`
  command — verified by injecting a simulated failure mid-run and asserting nothing after that point
  was touched.
- The sudoers rule is always syntax-checked (`visudo -cf`) before it is installed, never after —
  verified by asserting the log order and by injecting a simulated validation failure and confirming
  nothing was installed.
- No password or token is ever written to a log, a command line the script itself constructs, or
  printed to the screen; both are piped over `stdin` to the real commands that need them, and the
  test suite asserts a planted fake secret never appears in the script's own output or logs.
- The one part of this that cannot be fully hidden even in principle: macOS's own `security
  add-generic-password` command takes the password as a command-line argument to the `security`
  binary itself (there is no `stdin` form for this call) — visible only to `root`, and only for the
  instant that one call runs. The generated password is otherwise never printed, logged, or written
  to a file this script controls.
