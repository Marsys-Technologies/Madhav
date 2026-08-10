"""
MR-09 — Naming coherence + service health + honest pointers.

Tests that will FAIL before the fixes are applied and PASS after.

Items under test:
  1. (NAMING) The Python transit service class name no longer equals
     the materializer's asset_id string "ka_gochara".  Either the class
     is renamed OR an explicit docstring sentinel is present.  We enforce
     the rename: GocharaTransitService must exist, KaGocharaService must
     be a backward-compat alias only.
  2. (HEALTH) GocharaTransitService.service_health() is callable and
     returns a dict with at least the keys "status" and "detail".
  3. (DISCOVERABILITY) The orchestrator's WRITER_REGISTRY does NOT contain
     "ka_gochara_sweep" after discover_all(), because the shim no longer
     registers a retired writer unconditionally.
  4. (DOCSTRING) ph_muhurta writer's module-level docstring does NOT claim
     "ka_gochara" as a live read-dependency (the wiring is a deferred
     enhancement, not implemented).
  5. (RULING) The ka_gochara_sweep shim source contains an inline reference
     to the superseding ruling disposition (MR-09 / MR-28).
"""
from __future__ import annotations

import importlib
import inspect
import re
import sys

import pytest


# ---------------------------------------------------------------------------
# 1. NAMING: GocharaTransitService exists and does not equal "ka_gochara"
# ---------------------------------------------------------------------------

class TestNamingCoherence:
    def test_GocharaTransitService_class_exists(self):
        """After MR-09: the transit service exports GocharaTransitService."""
        mod = importlib.import_module("services.ka_gochara.service")
        assert hasattr(mod, "GocharaTransitService"), (
            "services.ka_gochara.service must export GocharaTransitService "
            "(renamed from KaGocharaService to avoid collision with the "
            "materializer asset_id 'ka_gochara')"
        )

    def test_transit_class_name_differs_from_materializer_asset_id(self):
        """The primary class name must not equal the string 'ka_gochara'."""
        mod = importlib.import_module("services.ka_gochara.service")
        cls = getattr(mod, "GocharaTransitService", None)
        assert cls is not None, "GocharaTransitService not found"
        # The class name itself must not be 'KaGocharaService' (the old collision)
        # AND must not literally be 'ka_gochara' (the materializer asset_id).
        assert cls.__name__ != "ka_gochara", (
            "Transit service class __name__ must not equal materializer asset_id"
        )
        assert cls.__name__ == "GocharaTransitService", (
            f"Expected class __name__ 'GocharaTransitService', got {cls.__name__!r}"
        )

    def test_backward_compat_alias_present(self):
        """KaGocharaService must still exist as an alias so existing callers don't break."""
        mod = importlib.import_module("services.ka_gochara.service")
        alias = getattr(mod, "KaGocharaService", None)
        assert alias is not None, (
            "KaGocharaService backward-compat alias must remain in "
            "services.ka_gochara.service so ka_sangam.py imports keep working"
        )
        cls = getattr(mod, "GocharaTransitService")
        assert alias is cls, (
            "KaGocharaService alias must point to the same class as GocharaTransitService"
        )

    def test_materializer_writer_asset_id_unchanged(self):
        """The materializer writer in pipeline/orchestrator/writers/ka_gochara.py
        must retain asset_id='ka_gochara' (we are NOT renaming the writer)."""
        import pipeline.orchestrator.writers.ka_gochara as writer_mod
        assert writer_mod.KaGocharaWriter.asset_id == "ka_gochara", (
            "Materializer writer asset_id must remain 'ka_gochara' — the naming fix "
            "renames only the Python transit service class"
        )

    def test_module_docstring_documents_the_split(self):
        """Both modules must have docstrings that clarify the transit/materializer split."""
        service_mod = importlib.import_module("services.ka_gochara.service")
        doc = (service_mod.__doc__ or "")
        assert "transit" in doc.lower() or "GocharaTransitService" in doc or "materializer" in doc.lower(), (
            "services.ka_gochara.service module docstring must document that this module "
            "is the transit COMPUTATION service, distinct from the ka_gochara materializer"
        )


# ---------------------------------------------------------------------------
# 2. HEALTH: GocharaTransitService.service_health() works
# ---------------------------------------------------------------------------

class TestTransitServiceHealth:
    def test_service_health_method_exists(self):
        """GocharaTransitService must have a service_health() method."""
        mod = importlib.import_module("services.ka_gochara.service")
        cls = getattr(mod, "GocharaTransitService")
        assert hasattr(cls, "service_health"), (
            "GocharaTransitService must expose a service_health() method "
            "(replaces the deleted self-test row from W6.4)"
        )

    def test_service_health_is_callable(self):
        mod = importlib.import_module("services.ka_gochara.service")
        cls = getattr(mod, "GocharaTransitService")
        assert callable(getattr(cls, "service_health")), (
            "GocharaTransitService.service_health must be callable"
        )

    def test_service_health_returns_status_and_detail(self):
        """service_health() (called without a real swe instance) must return a
        dict with at least 'status' and 'detail' keys.

        The method is designed to work with a real swisseph instance to run a
        test computation; we invoke it with a mock swe that returns a fixed
        value so we don't need the ephemeris files in CI.
        """
        mod = importlib.import_module("services.ka_gochara.service")
        cls = getattr(mod, "GocharaTransitService")

        class _FakeSwe:
            """Minimal swe double that makes a julday call succeed."""
            def julday(self, y, mo, d, h):
                return 2451545.0  # J2000.0

        instance = cls(_FakeSwe())
        result = instance.service_health()

        assert isinstance(result, dict), (
            f"service_health() must return a dict, got {type(result)}"
        )
        assert "status" in result, (
            f"service_health() result must have 'status' key, got keys: {list(result.keys())}"
        )
        assert "detail" in result, (
            f"service_health() result must have 'detail' key, got keys: {list(result.keys())}"
        )

    def test_service_health_status_is_string(self):
        """The 'status' value must be a non-empty string (e.g. 'ok', 'error')."""
        mod = importlib.import_module("services.ka_gochara.service")
        cls = getattr(mod, "GocharaTransitService")

        class _FakeSwe:
            def julday(self, y, mo, d, h):
                return 2451545.0

        result = cls(_FakeSwe()).service_health()
        assert isinstance(result["status"], str) and result["status"], (
            f"service_health()['status'] must be a non-empty string, got {result['status']!r}"
        )

    def test_service_health_returns_ok_when_swe_works(self):
        """When swe.julday() succeeds, status must be 'ok'."""
        mod = importlib.import_module("services.ka_gochara.service")
        cls = getattr(mod, "GocharaTransitService")

        class _FakeSwe:
            def julday(self, y, mo, d, h):
                return 2451545.0

        result = cls(_FakeSwe()).service_health()
        assert result["status"] == "ok", (
            f"Expected status='ok' when swe is functional, got {result['status']!r}"
        )

    def test_service_health_returns_error_when_swe_raises(self):
        """When swe.julday() raises, status must be 'error' (not an unhandled exception)."""
        mod = importlib.import_module("services.ka_gochara.service")
        cls = getattr(mod, "GocharaTransitService")

        class _BrokenSwe:
            def julday(self, y, mo, d, h):
                raise RuntimeError("ephemeris unavailable")

        result = cls(_BrokenSwe()).service_health()
        assert result["status"] == "error", (
            f"Expected status='error' when swe raises, got {result['status']!r}"
        )


# ---------------------------------------------------------------------------
# 3. DISCOVERABILITY: ka_gochara_sweep absent from WRITER_REGISTRY
# ---------------------------------------------------------------------------
#
# Strategy: rather than calling discover_all() (which hard-fails when the full
# writer module set can't be imported due to missing optional dependencies like
# jhora in CI), we directly import just the two shims under test and check
# the WRITER_REGISTRY state after each import.  This is the correct isolation
# level: we are testing what the SHIM does, not whether the full writer zoo loads.

class TestSweepWriterDiscoverability:
    def _isolated_registry(self):
        """Return the WRITER_REGISTRY state after a clean import of just the
        two shims under test (ka_gochara and ka_gochara_sweep).

        Avoids calling discover_all() which hard-fails on missing optional
        deps (jhora, swisseph data files, etc.) in CI environments.

        We must also remove any pre-existing 'ka_gochara_sweep' registry entry
        that was added before this test runs (e.g. from another test's
        discover_all() or a direct writer import in the same session), so the
        test measures what the SHIM does when imported from scratch, not what
        an earlier import already stamped in.
        """
        import pipeline.orchestrator.writers as w_pkg

        # Evict all sweep-related modules so re-import fires fresh
        to_evict = [
            k for k in sys.modules
            if "ka_gochara_sweep" in k
            or k in (
                "pipeline.orchestrator.writers.ka_gochara",
                "services.w2g",
                "services.w2g.materialize",
                "services.w2g.fingerprint",
                "services.w2g.tiers",
                "services.w2g.db_source",
            )
        ]
        for k in to_evict:
            sys.modules.pop(k, None)

        # Remove pre-existing registry entries for our two assets under test
        # (guards against earlier imports in the same pytest session)
        for aid in ("ka_gochara_sweep",):
            w_pkg.WRITER_REGISTRY.pop(aid, None)
            # Also remove from the private _REGISTRY dict (same object)
            w_pkg._REGISTRY.pop(aid, None)  # type: ignore[attr-defined]

        # Snapshot, then import our two shims
        before = set(w_pkg.WRITER_REGISTRY.keys())

        # Import the sweep shim — after MR-09 this must NOT re-add 'ka_gochara_sweep'
        importlib.import_module("pipeline.orchestrator.writers.ka_gochara_sweep")

        # Import the materializer shim — must still have 'ka_gochara'
        importlib.import_module("pipeline.orchestrator.writers.ka_gochara")

        after = set(w_pkg.WRITER_REGISTRY.keys())
        newly_added = after - before
        return newly_added, dict(w_pkg.WRITER_REGISTRY)

    def test_ka_gochara_sweep_not_in_dispatchable_registry(self):
        """After MR-09: importing the ka_gochara_sweep shim must NOT add
        'ka_gochara_sweep' to the WRITER_REGISTRY.

        The sweep writer is RETIRED — routing it into a new build plan is a bug.
        The shim now serves as a tombstone with the import line commented out.
        """
        newly_added, registry = self._isolated_registry()
        assert "ka_gochara_sweep" not in registry, (
            "ka_gochara_sweep must NOT appear in WRITER_REGISTRY after MR-09. "
            "The retired sweep shim should no longer unconditionally register "
            "the writer via @register. "
            f"Registry keys containing 'sweep': "
            f"{[k for k in registry if 'sweep' in k]}"
        )

    def test_ka_gochara_writer_still_in_registry(self):
        """The materializer ka_gochara must still be discoverable after
        the sweep shim is silenced."""
        newly_added, registry = self._isolated_registry()
        assert "ka_gochara" in registry, (
            "ka_gochara materializer writer must still appear in WRITER_REGISTRY. "
            "Only the retired sweep entry should be removed."
        )


# ---------------------------------------------------------------------------
# 4. DOCSTRING: ph_muhurta does not claim live ka_gochara wiring
# ---------------------------------------------------------------------------

class TestPhMuhurtaDocstring:
    def _get_module_docstring(self) -> str:
        import pipeline.orchestrator.writers.ph_muhurta as mod
        return (mod.__doc__ or "")

    def test_reads_line_does_not_claim_ka_gochara_as_live_dependency(self):
        """The ph_muhurta module docstring 'Reads:' line must NOT list 'ka_gochara'
        as if it is an implemented live read dependency.

        The actual _load_gochara_transits method returns {} explicitly and logs a
        note about the wiring being deferred.  The docstring must not contradict
        the code.
        """
        doc = self._get_module_docstring()
        # Find the "Reads:" block in the docstring
        reads_match = re.search(r"Reads:(.*?)(?:Writes:|$)", doc, re.DOTALL | re.IGNORECASE)
        if reads_match:
            reads_block = reads_match.group(1)
            # ka_gochara must NOT appear as an uncommented/unlabeled live dependency
            # Acceptable: "ka_gochara (PLANNED)" or "ka_gochara [deferred]" or absent
            # Not acceptable: "· ka_gochara ·" (bare, implying it's live)
            bare_kagochara = re.search(r"[·•]\s*ka_gochara\s*[·•\n]", reads_block)
            assert bare_kagochara is None, (
                "ph_muhurta module docstring 'Reads:' block must not list 'ka_gochara' "
                "as a bare live dependency.  The gochara wiring is deferred (returns {} "
                "explicitly in _load_gochara_transits).  Use a PLANNED/deferred label "
                "or remove it from the Reads list entirely.\n"
                f"Found reads block:\n{reads_block}"
            )

    def test_load_gochara_transits_method_returns_empty_explicitly(self):
        """_load_gochara_transits must explicitly return {} (not via a swallowed
        error), confirming the implementation matches the corrected docstring."""
        import pipeline.orchestrator.writers.ph_muhurta as mod
        src = inspect.getsource(mod.PhMuhurtaWriter._load_gochara_transits)
        # Must NOT have a table query (would indicate the old broken path)
        assert "FROM kala_gochara" not in src, (
            "_load_gochara_transits must not query FROM kala_gochara (that table does not exist)"
        )
        # Must return {} explicitly
        assert "return {}" in src, (
            "_load_gochara_transits must return {} explicitly (deferred wiring path)"
        )


# ---------------------------------------------------------------------------
# 5. RULING REFERENCE: shim source documents the superseding ruling
# ---------------------------------------------------------------------------

class TestRulingReference:
    def test_sweep_shim_documents_superseding_ruling(self):
        """The ka_gochara_sweep shim must contain an inline reference to the
        superseding ruling (MR-09 or MR-28) so the '2026-06-26 do NOT add
        writers/ka_gochara.py' ruling is not left as an unchallenged constraint.
        """
        import pipeline.orchestrator.writers.ka_gochara_sweep as shim_mod
        src = inspect.getsource(shim_mod)
        has_mr09 = "MR-09" in src
        has_mr28 = "MR-28" in src
        has_superseded = "supersed" in src.lower()
        assert has_mr09 or has_mr28 or has_superseded, (
            "pipeline/orchestrator/writers/ka_gochara_sweep.py must document "
            "the superseding ruling (MR-09 or MR-28) that resolves the "
            "2026-06-26 'do NOT add writers/ka_gochara.py' directive. "
            "This shim is the natural home for that cross-reference."
        )

    def test_service_module_documents_the_asset_split(self):
        """services/ka_gochara/service.py must mention the materializer
        asset_id distinction so any future reader understands why the class
        was renamed.
        """
        mod = importlib.import_module("services.ka_gochara.service")
        src = inspect.getsource(mod)
        has_materializer = "materializer" in src.lower()
        has_asset_id = "asset_id" in src or "asset id" in src.lower()
        has_distinction = "MR-09" in src or "distinct" in src.lower() or "different" in src.lower()
        assert has_materializer or has_asset_id or has_distinction, (
            "services/ka_gochara/service.py must document that this module is "
            "the transit COMPUTATION service, distinct from the 'ka_gochara' "
            "materializer writer (asset_id in pipeline/orchestrator/writers/ka_gochara.py). "
            "This prevents future naming confusion (MR-09 root cause)."
        )
