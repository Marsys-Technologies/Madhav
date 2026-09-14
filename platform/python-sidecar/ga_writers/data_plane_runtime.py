"""Runtime L1 producer boundary for all nineteen Gaṇita writers.

The frozen WriterBase API is not extended.  Instead, each L1 adapter opts into
this class decorator.  On a real psycopg connection it opens an exact
build/generation partition before the numerical writer runs and records that
partition only after the writer returns successfully.  Migration 1033 uses the
transaction-local settings installed here to snapshot inserted producer rows;
the snapshots survive the legacy replace-in-place active tables.

Small unit-test doubles are deliberately ignored unless they set
``_l1_contract_test_double = True``.  They do not implement PostgreSQL
transaction settings or migration functions and are not evidence of the
runtime persistence contract.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from ga_writers.data_plane_contracts import (
    L0_RESOURCE_CONFIG_DIGEST,
    L0_RESOURCE_CONFIG_GENERATION_ID,
    L0_SEMANTIC_RELEASE_DIGEST,
    L0_SEMANTIC_RELEASE_ID,
    L1_CONTRACT_VERSION,
    ContractError,
)


CONTRACTED_L1_ASSETS = frozenset({
    "ga_positions",
    "ga_vargas",
    "ga_dashas",
    "ga_nakshatra",
    "ga_panchanga",
    "ga_sensitive",
    "ga_sensitive_degree",
    "ga_strength",
    "ga_structural",
    "ga_condition",
    "ga_yoga",
    "ga_vichara",
    "ga_sade_sati",
    "ga_transit_anchors",
    "ga_tajaka",
    "ga_ayurdaya",
    "ga_medical",
    "ga_vastu",
    "ga_prashna",
})

_T = TypeVar("_T", bound=type)


def _contract_sql_enabled(conn: Any) -> bool:
    """True for production psycopg connections and explicit contract fakes."""
    if getattr(conn, "_l1_contract_test_double", False):
        return True
    return conn.__class__.__module__.split(".", 1)[0] == "psycopg"


def _validate_invocation(ctx: Any, asset_id: str) -> tuple[str, str]:
    if asset_id not in CONTRACTED_L1_ASSETS:
        raise ContractError(f"unregistered L1 producer boundary: {asset_id!r}")
    chart_id = str((ctx.config or {}).get("chart_id") or "")
    build_id = str(ctx.build_id or "")
    if not chart_id or not build_id:
        raise ContractError("L1 runtime producer context requires chart_id and build_id")
    return chart_id, build_id


def _expected_partition_count(writer: Any, ctx: Any) -> int:
    if not getattr(writer, "has_substeps", False):
        return 1
    count = len(writer.plan_substeps(ctx))
    if count < 1:
        raise ContractError(f"{writer.asset_id} declared no producer partitions")
    return count


def _open_partition(
    ctx: Any,
    *,
    asset_id: str,
    partition_key: str,
    expected_partitions: int,
) -> None:
    chart_id, build_id = _validate_invocation(ctx, asset_id)
    correction_of = (ctx.config or {}).get("l1_correction_of_generation_id")
    with ctx.db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              set_config('madhav.l1_asset_id', %s, true),
              set_config('madhav.l1_chart_id', %s, true),
              set_config('madhav.l1_generation_id', %s, true),
              set_config('madhav.l1_partition_key', %s, true),
              set_config('madhav.l1_contract_version', %s, true)
            """,
            (asset_id, chart_id, build_id, partition_key, L1_CONTRACT_VERSION),
        )
        cur.execute(
            """
            SELECT public.open_l1_data_plane_generation(
              %s::uuid, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s
            )
            """,
            (
                chart_id,
                asset_id,
                build_id,
                partition_key,
                expected_partitions,
                correction_of,
                L1_CONTRACT_VERSION,
                L0_SEMANTIC_RELEASE_ID,
                L0_SEMANTIC_RELEASE_DIGEST,
                L0_RESOURCE_CONFIG_GENERATION_ID,
                L0_RESOURCE_CONFIG_DIGEST,
            ),
        )


def _complete_partition(
    ctx: Any,
    *,
    asset_id: str,
    partition_key: str,
    rows_inserted: int,
) -> None:
    chart_id, build_id = _validate_invocation(ctx, asset_id)
    with ctx.db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT public.complete_l1_data_plane_partition(
              %s::uuid, %s, %s, %s, %s
            )
            """,
            (chart_id, asset_id, build_id, partition_key, rows_inserted),
        )


def l1_producer_contract(cls: _T) -> _T:
    """Decorate one registered GA adapter without changing WriterBase."""
    asset_id = str(getattr(cls, "asset_id", ""))
    if asset_id not in CONTRACTED_L1_ASSETS:
        raise ContractError(f"cannot decorate unknown L1 asset {asset_id!r}")
    if getattr(cls, "__l1_data_plane_contract__", False):
        return cls

    run_method = cls.__dict__.get("run")
    substep_method = cls.__dict__.get("run_substep")
    if (run_method is None) == (substep_method is None):
        raise ContractError(
            f"{asset_id} must define exactly one frozen runtime shape before decoration"
        )

    def wrap(method: Callable[..., Any], *, substep: bool) -> Callable[..., Any]:
        @wraps(method)
        def guarded(self: Any, ctx: Any, *args: Any, **kwargs: Any) -> Any:
            if ctx.dry_run or not _contract_sql_enabled(ctx.db_conn):
                return method(self, ctx, *args, **kwargs)
            _validate_invocation(ctx, asset_id)

            partition_key = (
                str(getattr(args[0], "key", ""))
                if substep and args
                else asset_id
            )
            if not partition_key:
                raise ContractError(f"{asset_id} substep has no partition key")
            expected = _expected_partition_count(self, ctx)
            _open_partition(
                ctx,
                asset_id=asset_id,
                partition_key=partition_key,
                expected_partitions=expected,
            )
            result = method(self, ctx, *args, **kwargs)
            _complete_partition(
                ctx,
                asset_id=asset_id,
                partition_key=partition_key,
                rows_inserted=int(result.rows_inserted),
            )
            return result

        guarded.__l1_data_plane_contract__ = True  # type: ignore[attr-defined]
        return guarded

    if run_method is not None:
        setattr(cls, "run", wrap(run_method, substep=False))
    else:
        setattr(cls, "run_substep", wrap(substep_method, substep=True))
    cls.__l1_data_plane_contract__ = True
    cls.l1_data_plane_contract_version = L1_CONTRACT_VERSION
    return cls
