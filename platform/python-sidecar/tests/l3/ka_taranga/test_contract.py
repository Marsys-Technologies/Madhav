"""K6-4 guards the removal of the independent waveform engine."""
import ast
from pathlib import Path
from types import SimpleNamespace

from pipeline.orchestrator.writers.ka_taranga import KaTarangaWriter


def test_unactivated_dispatch_and_dry_run_need_no_database():
    # An accidental legacy DELETE, or enabling the candidate path by default,
    # must fail here without any mock connection supplying a green result.
    for config, dry in [({'chart_id': 'fixture'}, False),
                        ({'chart_id': 'fixture', 'taranga_candidate': True}, True)]:
        result = KaTarangaWriter().run(SimpleNamespace(config=config, dry_run=dry))
        assert result.rows_inserted == 0
        assert 'inactive' in result.notes or 'dry_run' in result.notes


def test_writer_uses_no_private_astrological_engine():
    import pipeline.orchestrator.writers.ka_taranga as module
    tree = ast.parse(Path(module.__file__).read_text())
    imports = [n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any('taranga_kernel' in name or 'taranga_service' in name for name in imports)
    assert not any(isinstance(n, ast.Name) and n.id in {'_GRAHA_DOMAINS', '_harmonic_mean'}
                   for n in ast.walk(tree))
