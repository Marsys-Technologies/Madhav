"""Bind the three K6 registry probes on the caller-owned writer transaction."""


def bind_integrity_target(ctx):
    """No commit: the post-write probe reads these pins before the owner commits.

    (I) INTERPRETATION: the parameterless registry-probe interface requires a
    transaction-local binding. A standalone probe must explicitly bind its chart
    and build; missing or mismatched pins fail closed in migration 1375.
    """
    if getattr(ctx, 'dry_run', False):
        return
    with ctx.db_conn.cursor() as cur:
        cur.execute(
            "SELECT set_config('kala.integrity_chart_id', %s, true), "
            "set_config('kala.integrity_build_id', %s, true)",
            (str(ctx.config['chart_id']), str(ctx.build_id)),
        )
