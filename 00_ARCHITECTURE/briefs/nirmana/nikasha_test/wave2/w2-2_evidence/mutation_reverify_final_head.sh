set -u
cd /Users/Dev/madhav-nikasha
F=platform/scripts/governance/asset_census.py; T=platform/scripts/governance/__tests__/test_w2_2_latest_row_registration_timing.py; W1=platform/scripts/governance/__tests__/test_w2_1_earned_verdicts.py; S=/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/e1effe6d-cae4-4643-b098-d49444a83a68/scratchpad/w2-2
echo "# ==== re-verification at final HEAD $(git rev-parse --short HEAD) by the finishing builder: one or two mutations per committed row, each reverting that row's core change"
bash $S/mut.sh V-R233-raw-error-read $F "$W1 -k live_c4" live <<'EOF'
                "coalesce(left(translate(a.error, E'\\n\\r' || chr(31), '   '),200),''), "
=====>>>
                "coalesce(left(a.error,200),''), "
EOF
bash $S/mut.sh V-R44-last-read-row-wins $F "$T -k r44" live <<'EOF'
        if rec["_key"] > cur["_key"]:
=====>>>
        if True:
EOF
bash $S/mut.sh V-R44-tie-not-flagged $F "$T -k r44" live <<'EOF'
                cur["ambiguous"] = True
=====>>>
                cur["ambiguous"] = False
EOF
bash $S/mut.sh V-R49-first-error-kept $F "$T -k r49" live <<'EOF'
        if state == "error" and disp != "blocked_dependency" and err:
=====>>>
        if state == "error" and disp != "blocked_dependency" and err and not d["sample_error"]:
EOF
bash $S/mut.sh V-R49-partial-order-key $F "$T -k r49" live <<'EOF'
                "ORDER BY a.asset_id, r.created_at, a.run_id")
=====>>>
                "ORDER BY a.asset_id, r.created_at")
EOF
bash $S/mut.sh V-R45-stale-counts-live $F "$T -k r45" live <<'EOF'
        elif rec.get("state") == "lit":
=====>>>
        elif rec.get("state") in ("lit", "stale"):
EOF
bash $S/mut.sh V-R45-any-chart-record $F "$T -k r45" live <<'EOF'
                      else (by[""], "global") if "" in by else (None, ""))
=====>>>
                      else (by[""], "global") if "" in by else ((next(iter(by.values())), "other") if by else (None, "")))
EOF
bash $S/mut.sh V-D6.2-link-key-ignored $F "$T -k d6_2" live <<'EOF'
              and att["ended_epoch"] == rec.get("built_epoch"))
=====>>>
              )
EOF
bash $S/mut.sh V-D6.2-probe-green-without-receipt $F "$T -k d6_2" live <<'EOF'
            if not (att["receipt"] and era is not None and att["created_epoch"] >= era):
=====>>>
            if not (era is not None and att["created_epoch"] >= era):
EOF
bash $S/mut.sh V-R43-constants-unresolved $F "$T -k r43" live <<'EOF'
        if isinstance(a, ast.Name) and consts and a.id in consts:
=====>>>
        if False:
EOF
bash $S/mut.sh V-R43-shim-imports-unfollowed $F "$T -k r43" live <<'EOF'
        for g in _first_party_imports(_parse(f), f.parent):
=====>>>
        for g in []:
EOF
bash $S/mut.sh V-R46-view-not-counted $F "$T -k r46" live <<'EOF'
                   if r["target_table"] in cat.get("views", set()) and not _count_tables(r["count_sql"])}
=====>>>
                   if False}
EOF
bash $S/mut.sh V-R50-short-lines-padded-and-counted $F "$T -k r50" live <<'EOF'
    bad = [x for x in rows if len(x) != 7]
=====>>>
    bad = []; rows = [(x + [""] * 7)[:7] for x in rows]
EOF
bash $S/mut.sh V-R51-comments-count-as-serving $F "$T -k r51" live <<'EOF'
        code = _ts_code(txt)
=====>>>
        code = txt
EOF
bash $S/mut.sh V-R51-comment-only-reads-closable-na $F "$T -k r51" live <<'EOF'
        elif not cap["modules"] and cap.get("comment_only"):
=====>>>
        elif False:
EOF
bash $S/mut.sh V-R53-any-kind-waves-through $F "$T -k r53" live <<'EOF'
        elif r["asset_kind"] == "service" or not r["has_writer"]:
=====>>>
        elif r["asset_kind"] or not r["has_writer"]:
EOF
bash $S/mut.sh V-R53-unowned-single-table-passes $F "$T -k r53" live <<'EOF'
        if own:
=====>>>
        if True:
EOF
bash $S/mut.sh V-R54-severity-dropped $F "$T -k r54" offline <<'EOF'
                                            severity=round(frac, 4))
=====>>>
                                            severity=None)
EOF
bash $S/mut.sh V-R232-substring-match $F "$T -k r232" offline <<'EOF'
            if _DENSITY_DECL.search(_ts_code(txt, blank_strings=True)):
=====>>>
            if "density_contract" in txt:
EOF
