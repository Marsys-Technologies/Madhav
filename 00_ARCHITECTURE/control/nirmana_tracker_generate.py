#!/usr/bin/env python3
"""Nirmana campaign tracker: real-time reliability dashboard.

Queries every source fresh on each run — the live Postgres asset_registry,
the fleet's own state files (CAMPAIGN_STATE.json, DECISIONS.jsonl,
VERDICTS.jsonl, HEARTBEAT.jsonl, SPEND.jsonl), the mailbox, and the live
tmux session — and renders one self-contained HTML file. Never caches
across runs, never estimates a number a source doesn't provide, and
surfaces its own data-quality findings instead of hiding them
(CLAUDE.md Sec N.8 Earned-Signal Principle). Re-run any time:

    python3 00_ARCHITECTURE/control/nirmana_tracker_generate.py

Writes 00_ARCHITECTURE/control/nirmana_tracker.html (overwritten each run).
"""
import datetime
import html as html_lib
import json
import pathlib
import re
import subprocess

import psycopg

ROOT = pathlib.Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "00_ARCHITECTURE/autonomy/state"
MAILBOX_DIR = ROOT / "00_ARCHITECTURE/autonomy/mailbox"
OUT_PATH = ROOT / "00_ARCHITECTURE/control/nirmana_tracker.html"
TMUX_SESSION = "nirmana"

LAYER_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5"]
LAYER_PREFIX = {
    "L0": ("bg_", "brahmagyan"),
    "L1": ("ga_", "ganita"),
    "L2": ("bo_", "bodha"),
    "L3": ("ka_", "kala"),
    "L4": ("ph_", "phala"),
    "L5": ("mi_", "mimamsa"),
}
LADDER = ["Intake", "Conform", "Optimize", "Repair", "Verify", "Freeze"]


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_ts(ts):
    if not ts:
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_str(ts, ref):
    dt = parse_ts(ts)
    if dt is None:
        return None, "unknown"
    secs = (ref - dt).total_seconds()
    if secs < 0:
        return secs, "in the future (clock skew?)"
    if secs < 90:
        return secs, f"{int(secs)}s ago"
    if secs < 3600:
        return secs, f"{int(secs / 60)}m ago"
    if secs < 86400:
        return secs, f"{secs / 3600:.1f}h ago"
    return secs, f"{secs / 86400:.1f}d ago"


def load_json(path):
    try:
        return json.loads(path.read_text()), None
    except Exception as e:
        return None, str(e)


def load_jsonl(path):
    rows, errs = [], []
    if not path.exists():
        return rows, [f"missing: {path}"]
    for i, line in enumerate(path.read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            errs.append(f"line {i}: {e}")
    return rows, errs


def esc(x):
    return html_lib.escape(str(x)) if x is not None else ""


def db_url():
    env_path = ROOT / "platform/.env.local"
    for line in env_path.read_text().splitlines():
        m = re.match(r"^\s*DATABASE_URL\s*=\s*(.+)$", line)
        if m:
            return m.group(1).strip().strip("\"'")
    raise RuntimeError("DATABASE_URL not found in platform/.env.local")


def fetch_asset_registry():
    """Returns (rows, error). rows is a list of dicts, empty on failure —
    the caller must render an honest failure state, never a fabricated one."""
    try:
        url = db_url()
        with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True, connect_timeout=8) as conn:
            c = conn.cursor()
            c.execute("SET statement_timeout = '15s'")
            c.execute(
                """SELECT asset_id, catalog_status, asset_kind, target_floor,
                          integrity_check_sql IS NOT NULL AS has_integrity_check,
                          layer, layer_name, layer_index, has_writer, is_active
                   FROM asset_registry ORDER BY asset_id"""
            )
            return c.fetchall(), None
    except Exception as e:
        return [], str(e)


def layer_of(asset_id):
    for code, (prefix, _name) in LAYER_PREFIX.items():
        if asset_id.startswith(prefix):
            return code
    return None


def tmux_windows(session):
    try:
        out = subprocess.run(
            ["tmux", "list-windows", "-t", session, "-F", "#{window_index}\t#{window_name}\t#{window_active}"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode != 0:
            return None, out.stderr.strip() or "tmux returned non-zero (session likely not running)"
        wins = []
        for line in out.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                wins.append({"index": parts[0], "name": parts[1], "active": parts[2] == "1"})
        return wins, None
    except FileNotFoundError:
        return None, "tmux not installed on this host"
    except Exception as e:
        return None, str(e)


def mailbox_scan():
    out = {}
    if not MAILBOX_DIR.exists():
        return out
    for d in sorted(MAILBOX_DIR.iterdir()):
        if not d.is_dir():
            continue
        files = sorted((f.name for f in d.iterdir() if f.is_file()), reverse=True)
        out[d.name] = {"count": len(files), "recent": files[:5]}
    return out


def status_pill_class(status):
    s = (status or "").lower()
    if s in ("complete", "closed", "current", "healthy", "pass"):
        return "pill-good"
    if s in ("in_progress", "running", "working", "awaiting_verification", "awaiting_verification_priority"):
        return "pill-active"
    if s in ("blocked_by_design", "blocked", "fail", "critical", "stuck"):
        return "pill-critical"
    if s in ("not_open", "not_started", "asked", "draft"):
        return "pill-neutral"
    return "pill-neutral"


def main():
    ref = now_utc()
    gen_ts = ref.strftime("%Y-%m-%d %H:%M:%S UTC")

    campaign_state, cs_err = load_json(STATE_DIR / "CAMPAIGN_STATE.json")
    decisions, dec_err = load_jsonl(STATE_DIR / "DECISIONS.jsonl")
    verdicts, ver_err = load_jsonl(STATE_DIR / "VERDICTS.jsonl")
    heartbeats, hb_err = load_jsonl(STATE_DIR / "HEARTBEAT.jsonl")
    spends, sp_err = load_jsonl(STATE_DIR / "SPEND.jsonl")
    mailbox = mailbox_scan()
    tmux_wins, tmux_err = tmux_windows(TMUX_SESSION)
    reg_rows, reg_err = fetch_asset_registry()

    # ---- derived: fleet liveness ----
    last_hb = heartbeats[-1] if heartbeats else None
    hb_age_s, hb_age_txt = (age_str(last_hb["ts"], ref) if last_hb else (None, "no heartbeat data"))
    per_agent = {}
    for h in heartbeats:
        a = h.get("agent", "?")
        if a not in per_agent or (h.get("ts") or "") > (per_agent[a].get("ts") or ""):
            per_agent[a] = h
    agent_rows = sorted(per_agent.values(), key=lambda h: h.get("ts") or "", reverse=True)

    last_spend = spends[-1] if spends else None
    sp_age_s, sp_age_txt = (age_str(last_spend["ts"], ref) if last_spend else (None, "no spend data"))

    fleet_alive = bool(tmux_wins) and tmux_err is None
    hb_recent = hb_age_s is not None and hb_age_s < 600

    # ---- derived: per-layer live registry health ----
    layer_health = {code: {"n": 0, "current": 0, "draft": 0, "retired": 0, "has_integrity": 0,
                            "has_floor": 0, "inactive": 0} for code in LAYER_ORDER}
    unassigned_assets = []
    inconsistent_layer_field = 0
    for r in reg_rows:
        code = layer_of(r["asset_id"])
        if code is None:
            unassigned_assets.append(r["asset_id"])
            continue
        h = layer_health[code]
        h["n"] += 1
        st = (r.get("catalog_status") or "").upper()
        if st == "CURRENT":
            h["current"] += 1
        elif st == "DRAFT":
            h["draft"] += 1
        elif st == "RETIRED":
            h["retired"] += 1
        if r.get("has_integrity_check"):
            h["has_integrity"] += 1
        if r.get("target_floor") is not None:
            h["has_floor"] += 1
        if r.get("is_active") is False:
            h["inactive"] += 1
        expect_idx = code
        li = (r.get("layer_index") or "")
        ln = r.get("layer_name")
        if ln is None or li not in (expect_idx, expect_idx.lstrip("L")):
            inconsistent_layer_field += 1

    total_integrity = sum(h["has_integrity"] for h in layer_health.values())
    total_assets_live = sum(h["n"] for h in layer_health.values())

    # ---- CAMPAIGN_STATE derived ----
    rungs = (campaign_state or {}).get("rungs", {})
    m_track = (campaign_state or {}).get("m_track", {})
    ceilings = (campaign_state or {}).get("ceilings", {})
    open_threads = (campaign_state or {}).get("open_threads", [])
    cs_ts = (campaign_state or {}).get("last_updated_ts")
    cs_age_s, cs_age_txt = age_str(cs_ts, ref) if cs_ts else (None, "unknown")

    thread_state_counts = {}
    for t in open_threads:
        s = t.get("state", "unknown")
        thread_state_counts[s] = thread_state_counts.get(s, 0) + 1

    # ---- spend vs ceilings ----
    out_tok = ((last_spend or {}).get("totals") or {}).get("output_tokens")
    out_ceil = ceilings.get("output_tokens_campaign")
    out_pct = (out_tok / out_ceil * 100) if (out_tok is not None and out_ceil) else None
    all_tok = ((last_spend or {}).get("totals") or {}).get("tokens_all")
    all_ceil = ceilings.get("tokens_campaign")
    all_pct = (all_tok / all_ceil * 100) if (all_tok is not None and all_ceil) else None
    cost_usd = (last_spend or {}).get("cost_usd")
    pricing_note = (last_spend or {}).get("note", "")

    # ================= render =================
    def rung_card(code):
        rung_key = "R" + code[1:]
        rung = rungs.get(rung_key, {})
        status = rung.get("status", "unknown")
        domain = rung.get("domain", "—")
        plan_assets = rung.get("assets")
        prefix, sname = LAYER_PREFIX[code]
        h = layer_health[code]
        carry = rung.get("stage2_carry_forward")
        mismatch = ""
        if plan_assets is not None and plan_assets != h["n"]:
            mismatch = (f'<div class="flag">plan says {plan_assets} assets, live registry has {h["n"]} '
                        f'under prefix <code>{esc(prefix)}</code> — needs reconciliation</div>')
        carry_html = ""
        if carry:
            rows = "".join(
                f'<tr><td><code>{esc(a.get("asset"))}</code></td><td class="num">{esc(a.get("timeout_h"))}h</td>'
                f'<td class="num">{esc(a.get("measured_worst_h"))}h</td>'
                f'<td class="num">{esc(a.get("ratio"))}×</td><td>{esc(a.get("tier"))}</td></tr>'
                for a in carry.get("assets", [])
            )
            carry_html = f'''
              <details class="carry">
                <summary>{len(carry.get("assets", []))} pre-measured defect(s) staged for this rung's Conform stage</summary>
                <p class="carry-source">{esc(carry.get("source"))}</p>
                <p>{esc(carry.get("finding"))}</p>
                <div class="tbl-wrap"><table class="mini">
                  <thead><tr><th>asset</th><th>timeout</th><th>measured worst</th><th>ratio</th><th>tier</th></tr></thead>
                  <tbody>{rows}</tbody>
                </table></div>
              </details>'''
        ladder_html = "".join(
            f'<span class="rung-step off" title="not started">{s}</span>' for s in LADDER
        )
        return f'''
        <article class="rung-card">
          <div class="rung-head">
            <span class="rung-code">{rung_key}</span>
            <span class="layer-name">{esc(sname.capitalize())}</span>
            <span class="pill {status_pill_class(status)}">{esc(status)}</span>
          </div>
          <div class="rung-ladder">{ladder_html}</div>
          <dl class="rung-stats">
            <div><dt>domain</dt><dd>{esc(domain)}</dd></div>
            <div><dt>assets (live)</dt><dd class="num">{h["n"]}</dd></div>
            <div><dt>CURRENT / DRAFT / RETIRED</dt><dd class="num">{h["current"]} / {h["draft"]} / {h["retired"]}</dd></div>
            <div><dt>earned integrity check</dt><dd class="num">{h["has_integrity"]} / {h["n"]}</dd></div>
            <div><dt>target floor set</dt><dd class="num">{h["has_floor"]} / {h["n"]}</dd></div>
          </dl>
          {mismatch}
          {carry_html}
        </article>'''

    rung_cards = "".join(rung_card(c) for c in LAYER_ORDER)

    m0 = m_track.get("M0", {})
    m_rows = "".join(
        f'<tr><td><code>{esc(k)}</code></td><td><span class="pill {status_pill_class(v.get("status"))}">{esc(v.get("status"))}</span></td>'
        f'<td>{esc(v.get("note", ""))[:220]}{"…" if len(v.get("note","")) > 220 else ""}</td></tr>'
        for k, v in m_track.items()
    )

    thread_rows = "".join(
        f'<tr><td><code>{esc(t.get("id"))}</code></td>'
        f'<td><span class="pill {status_pill_class(t.get("state"))}">{esc(t.get("state"))}</span></td>'
        f'<td>{esc(t.get("owner"))}</td><td>{esc(t.get("what"))}</td></tr>'
        for t in open_threads
    )

    def decision_block(d, kind):
        rid = esc(d.get("id"))
        subj = esc(d.get("subject") or d.get("claim") or "")
        body_field = "ruling" if kind == "decision" else "verdict"
        body = esc(d.get(body_field) or "")
        badge = ""
        if kind == "verdict":
            vb = (d.get("verdict") or "").upper()
            badge = f'<span class="pill {"pill-critical" if vb=="FAIL" else "pill-good"}">{esc(vb)}</span>'
        sup = d.get("supersedes")
        sup_html = f'<span class="flag-inline">supersedes {esc(sup)}</span>' if sup else ""
        return f'''
        <details class="decision">
          <summary><code>{rid}</code> {badge} {subj} {sup_html}</summary>
          <p class="ts">{esc(d.get("ts"))} · {esc(d.get("agent",""))}</p>
          <p>{body}</p>
        </details>'''

    decisions_html = "".join(decision_block(d, "decision") for d in reversed(decisions))
    verdicts_html = "".join(decision_block(v, "verdict") for v in reversed(verdicts))

    def mailbox_block(name, info):
        recent = "".join(f"<li><code>{esc(f)}</code></li>" for f in info["recent"])
        return f'''
        <div class="mailbox-col">
          <h4>{esc(name)}<span class="count">{info["count"]}</span></h4>
          <ul>{recent or "<li class='muted'>empty</li>"}</ul>
        </div>'''

    mailbox_html = "".join(mailbox_block(k, v) for k, v in mailbox.items())

    agent_rows_html = "".join(
        f'<tr><td>{esc(h.get("agent"))}</td><td>{esc(h.get("status"))}</td>'
        f'<td class="num">{age_str(h.get("ts"), ref)[1]}</td>'
        f'<td class="detail">{esc((h.get("detail") or ""))[:160]}{"…" if len(h.get("detail") or "") > 160 else ""}</td></tr>'
        for h in agent_rows
    )

    tmux_html = ""
    if tmux_wins:
        tmux_html = "".join(
            f'<span class="pill {"pill-good" if w["active"] else "pill-neutral"}">{esc(w["name"])}</span>'
            for w in tmux_wins
        )
    else:
        tmux_html = f'<span class="pill pill-critical">no live tmux session — {esc(tmux_err)}</span>'

    quality_flags = []
    if reg_err:
        quality_flags.append(f"Postgres asset_registry query FAILED: {esc(reg_err)} — layer cards below show 0 live counts, do not trust them.")
    if total_assets_live and total_integrity == 0:
        quality_flags.append(f"0 of {total_assets_live} live assets have integrity_check_sql populated — no asset in the catalogue has an earned pass/fail detector yet (CLAUDE.md §N.8).")
    if inconsistent_layer_field:
        quality_flags.append(f"{inconsistent_layer_field} asset_registry rows have a NULL or inconsistently-formatted layer_name/layer_index — this dashboard keys layers off the asset_id prefix instead, not those columns.")
    if unassigned_assets:
        quality_flags.append(f"{len(unassigned_assets)} asset(s) don't match any known layer prefix: {', '.join(esc(a) for a in unassigned_assets)}.")
    if cost_usd is None:
        quality_flags.append(f"cost_usd is withheld, not estimated: {esc(pricing_note)}")
    if cs_err:
        quality_flags.append(f"CAMPAIGN_STATE.json failed to load: {esc(cs_err)} — rung/M0 status below is stale or empty.")
    if not hb_recent:
        quality_flags.append(f"last heartbeat is {esc(hb_age_txt)} — fleet may be idle, stalled, or between ticks.")

    quality_html = "".join(f"<li>{f}</li>" for f in quality_flags) or "<li class='muted'>no data-quality flags raised this run.</li>"

    html_out = f"""<title>Nirmana Rung Board</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --paper: #f5f2ea;
    --paper-raised: #ffffff;
    --ink: #1b1f2e;
    --ink-dim: #55597a;
    --line: #ddd7c6;
    --accent: #4854c9;
    --accent-soft: #e7e9fb;
    --ember: #b5601f;
    --sage: #3f7a4e;
    --sage-soft: #e3f0e5;
    --rust: #a3392f;
    --rust-soft: #f7e4e1;
    --neutral-soft: #eae7db;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --paper: #14151d;
      --paper-raised: #1c1e2a;
      --ink: #eceaf0;
      --ink-dim: #a3a3bd;
      --line: #33344a;
      --accent: #8b93f0;
      --accent-soft: #262a52;
      --ember: #e08a44;
      --sage: #6fbf82;
      --sage-soft: #1c3324;
      --rust: #e8776a;
      --rust-soft: #3a2222;
      --neutral-soft: #2a2b3a;
    }}
  }}
  :root[data-theme="dark"] {{
    --paper: #14151d;
    --paper-raised: #1c1e2a;
    --ink: #eceaf0;
    --ink-dim: #a3a3bd;
    --line: #33344a;
    --accent: #8b93f0;
    --accent-soft: #262a52;
    --ember: #e08a44;
    --sage: #6fbf82;
    --sage-soft: #1c3324;
    --rust: #e8776a;
    --rust-soft: #3a2222;
    --neutral-soft: #2a2b3a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--paper); color: var(--ink);
    font-family: "IBM Plex Sans", system-ui, sans-serif;
    font-size: 15px; line-height: 1.5;
  }}
  code, .num, .ts, .mono {{ font-family: "IBM Plex Mono", ui-monospace, monospace; font-variant-numeric: tabular-nums; }}
  h1, h2, h3, .rung-code {{ font-family: "Fraunces", Georgia, serif; text-wrap: balance; }}
  .wrap {{ max-width: 1280px; margin: 0 auto; padding: 28px 24px 80px; }}
  header.top {{ display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 6px; }}
  header.top h1 {{ font-size: 30px; font-weight: 700; margin: 0; letter-spacing: -0.01em; }}
  .subtitle {{ color: var(--ink-dim); font-size: 14px; margin: 2px 0 20px; }}
  .fresh-strip {{ display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 12.5px; color: var(--ink-dim); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 10px 0; margin-bottom: 26px; }}
  .fresh-strip b {{ color: var(--ink); }}

  .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin-bottom: 30px; }}
  .stat {{ background: var(--paper-raised); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }}
  .stat .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--ink-dim); margin-bottom: 6px; }}
  .stat .value {{ font-size: 22px; font-weight: 600; font-family: "IBM Plex Mono", monospace; }}
  .stat .sub {{ font-size: 12px; color: var(--ink-dim); margin-top: 4px; }}
  .bar {{ height: 6px; border-radius: 4px; background: var(--neutral-soft); margin-top: 8px; overflow: hidden; }}
  .bar > i {{ display: block; height: 100%; background: var(--accent); }}

  section {{ margin-bottom: 34px; }}
  section > h2 {{ font-size: 19px; font-weight: 600; margin: 0 0 12px; display: flex; align-items: center; gap: 10px; }}
  section > h2 .count {{ font-family: "IBM Plex Mono", monospace; font-size: 12px; color: var(--ink-dim); font-weight: 400; }}

  .pill {{ display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 500; text-transform: uppercase; letter-spacing: .03em; }}
  .pill-good {{ background: var(--sage-soft); color: var(--sage); }}
  .pill-active {{ background: var(--accent-soft); color: var(--accent); }}
  .pill-critical {{ background: var(--rust-soft); color: var(--rust); }}
  .pill-neutral {{ background: var(--neutral-soft); color: var(--ink-dim); }}

  .rung-board {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
  .rung-card {{ background: var(--paper-raised); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }}
  .rung-head {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
  .rung-code {{ font-size: 20px; font-weight: 700; }}
  .layer-name {{ color: var(--ink-dim); font-size: 13px; flex: 1; }}
  .rung-ladder {{ display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }}
  .rung-step {{ font-size: 10px; padding: 3px 6px; border-radius: 5px; background: var(--neutral-soft); color: var(--ink-dim); }}
  .rung-stats {{ display: grid; grid-template-columns: 1fr auto; gap: 4px 10px; margin: 0; }}
  .rung-stats div {{ display: contents; }}
  .rung-stats dt {{ font-size: 12px; color: var(--ink-dim); }}
  .rung-stats dd {{ margin: 0; font-size: 12.5px; text-align: right; }}
  .flag {{ margin-top: 10px; font-size: 12px; background: var(--rust-soft); color: var(--rust); padding: 6px 8px; border-radius: 6px; }}
  .carry {{ margin-top: 10px; font-size: 12.5px; }}
  .carry summary {{ cursor: pointer; color: var(--ember); font-weight: 500; }}
  .carry-source {{ color: var(--ink-dim); font-size: 11.5px; margin: 8px 0 2px; }}

  .tbl-wrap {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  table.mini {{ font-size: 12px; }}
  th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--ink-dim); font-weight: 500; }}
  td.num {{ font-family: "IBM Plex Mono", monospace; text-align: right; }}
  td.detail {{ color: var(--ink-dim); }}

  details.decision {{ background: var(--paper-raised); border: 1px solid var(--line); border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; }}
  details.decision summary {{ cursor: pointer; font-weight: 500; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
  details.decision p {{ font-size: 13.5px; white-space: pre-wrap; }}
  details.decision p.ts {{ color: var(--ink-dim); font-size: 11.5px; margin: 8px 0 4px; }}
  .flag-inline {{ font-size: 11px; color: var(--ember); }}

  .mailbox-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }}
  .mailbox-col h4 {{ font-size: 13px; margin: 0 0 6px; display: flex; justify-content: space-between; }}
  .mailbox-col .count {{ font-family: "IBM Plex Mono", monospace; color: var(--ink-dim); }}
  .mailbox-col ul {{ list-style: none; margin: 0; padding: 0; font-size: 11.5px; color: var(--ink-dim); }}
  .mailbox-col li {{ padding: 3px 0; border-top: 1px solid var(--line); word-break: break-all; }}
  .mailbox-col li:first-child {{ border-top: none; }}
  .muted {{ color: var(--ink-dim); }}

  .quality-panel {{ background: var(--paper-raised); border: 1px dashed var(--ink-dim); border-radius: 10px; padding: 14px 18px; }}
  .quality-panel h2 {{ margin-top: 0; }}
  .quality-panel ul {{ margin: 0; padding-left: 18px; font-size: 13px; }}
  .quality-panel li {{ margin-bottom: 6px; }}

  footer {{ color: var(--ink-dim); font-size: 11.5px; border-top: 1px solid var(--line); padding-top: 14px; margin-top: 40px; }}
  footer code {{ font-size: 11px; }}
</style>

<div class="wrap">
  <header class="top">
    <h1>Nirmāṇa Rung Board</h1>
  </header>
  <p class="subtitle">Asset-catalogue elevation across Brahmagyan &rarr; Mīmāṃsā (L0&ndash;L5) &middot; branch <code>campaign/nirmana-autonomous</code></p>

  <div class="fresh-strip">
    <span>generated <b>{esc(gen_ts)}</b></span>
    <span>campaign state <b>{esc(cs_age_txt)}</b></span>
    <span>last heartbeat <b>{esc(hb_age_txt)}</b> ({esc((last_hb or {}).get("agent","—"))})</span>
    <span>last spend poll <b>{esc(sp_age_txt)}</b></span>
    <span>fleet tmux <b>{"alive" if fleet_alive else "not detected"}</b></span>
  </div>

  <div class="stat-grid">
    <div class="stat">
      <div class="label">campaign / track</div>
      <div class="value">{esc((campaign_state or {}).get("track","—"))} · {esc((campaign_state or {}).get("campaign_slice","—"))}</div>
      <div class="sub">stage: {esc((campaign_state or {}).get("stage","—"))} &middot; plan v{esc((campaign_state or {}).get("plan_version","—"))}</div>
    </div>
    <div class="stat">
      <div class="label">M0 status</div>
      <div class="value"><span class="pill {status_pill_class(m0.get("status"))}">{esc(m0.get("status","—"))}</span></div>
      <div class="sub">latest verdict: {"".join(f'<span class=\"pill {"pill-critical" if (v.get("verdict") or "").upper()=="FAIL" else "pill-good"}\">{esc(v.get("id"))} {esc(v.get("verdict"))}</span> ' for v in verdicts[-2:])}</div>
    </div>
    <div class="stat">
      <div class="label">open threads</div>
      <div class="value">{len(open_threads)}</div>
      <div class="sub">{", ".join(f"{esc(k)}: {v}" for k, v in thread_state_counts.items())}</div>
    </div>
    <div class="stat">
      <div class="label">output tokens (campaign ceiling)</div>
      <div class="value">{f"{out_pct:.1f}%" if out_pct is not None else "—"}</div>
      <div class="sub">{f"{out_tok:,} / {out_ceil:,}" if out_tok is not None and out_ceil else "no data"}</div>
      <div class="bar"><i style="width:{min(out_pct or 0, 100):.1f}%"></i></div>
    </div>
    <div class="stat">
      <div class="label">all-class tokens (campaign ceiling)</div>
      <div class="value">{f"{all_pct:.1f}%" if all_pct is not None else "—"}</div>
      <div class="sub">{f"{all_tok:,} / {all_ceil:,}" if all_tok is not None and all_ceil else "no data"}</div>
      <div class="bar"><i style="width:{min(all_pct or 0, 100):.1f}%"></i></div>
    </div>
    <div class="stat">
      <div class="label">cost (USD)</div>
      <div class="value">withheld</div>
      <div class="sub">{esc(pricing_note)[:90]}</div>
    </div>
  </div>

  <section>
    <h2>Six-layer rung board <span class="count">R0&ndash;R5, live asset counts from Postgres</span></h2>
    <div class="rung-board">{rung_cards}</div>
  </section>

  <section>
    <h2>M-track <span class="count">{len(m_track)}</span></h2>
    <div class="tbl-wrap"><table>
      <thead><tr><th>slice</th><th>status</th><th>note</th></tr></thead>
      <tbody>{m_rows}</tbody>
    </table></div>
  </section>

  <section>
    <h2>Open threads <span class="count">{len(open_threads)}</span></h2>
    <div class="tbl-wrap"><table>
      <thead><tr><th>id</th><th>state</th><th>owner</th><th>what</th></tr></thead>
      <tbody>{thread_rows}</tbody>
    </table></div>
  </section>

  <section>
    <h2>Fleet activity <span class="count">last-seen per agent, {len(heartbeats)} heartbeat events on file</span></h2>
    <div class="tbl-wrap"><table>
      <thead><tr><th>agent</th><th>status</th><th>last seen</th><th>latest detail</th></tr></thead>
      <tbody>{agent_rows_html}</tbody>
    </table></div>
    <p style="margin-top:10px">tmux <code>{esc(TMUX_SESSION)}</code> windows: {tmux_html}</p>
  </section>

  <section>
    <h2>Mailbox <span class="count">most recent 5 per box</span></h2>
    <div class="mailbox-grid">{mailbox_html}</div>
  </section>

  <section>
    <h2>Decisions <span class="count">{len(decisions)}</span></h2>
    {decisions_html}
  </section>

  <section>
    <h2>Verdicts <span class="count">{len(verdicts)}</span></h2>
    {verdicts_html}
  </section>

  <section class="quality-panel">
    <h2>Data-quality flags <span class="count">computed this run, not hand-maintained</span></h2>
    <ul>{quality_html}</ul>
  </section>

  <footer>
    Sources read live on every run: <code>asset_registry</code> (Postgres) &middot;
    <code>autonomy/state/CAMPAIGN_STATE.json</code> &middot; <code>DECISIONS.jsonl</code> &middot;
    <code>VERDICTS.jsonl</code> &middot; <code>HEARTBEAT.jsonl</code> &middot; <code>SPEND.jsonl</code> &middot;
    <code>autonomy/mailbox/*</code> &middot; <code>tmux list-windows -t nirmana</code>.
    Regenerate: <code>python3 00_ARCHITECTURE/control/nirmana_tracker_generate.py</code>.
    Nothing on this page is estimated or carried over from a prior run.
  </footer>
</div>
"""
    OUT_PATH.write_text(html_out)
    print(f"wrote {OUT_PATH} ({len(html_out):,} bytes) at {gen_ts}")
    if quality_flags:
        print(f"{len(quality_flags)} data-quality flag(s) raised — see quality panel.")


if __name__ == "__main__":
    main()
