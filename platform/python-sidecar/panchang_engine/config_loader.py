"""
config_loader.py — YAML config loader for muhurat scoring weights.

Weights live in config/muhurat_weights.yaml. This module reads and caches them
at sidecar startup; individual event scoring calls use get_weights_for_event()
to receive the merged (defaults + event-overrides) weight dict.

Design:
  - Cached on first read via @lru_cache (Path objects are hashable).
  - Callers may pass config_path to override the default (useful in tests).
  - get_weights_for_event() performs a shallow merge: defaults first, then event
    overrides on top. Unknown keys in overrides are preserved (forward compat).

Source: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.4.1 (scoring rubric §W_* config).
"""
import yaml
from pathlib import Path
from functools import lru_cache


_DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "muhurat_weights.yaml"


@lru_cache(maxsize=8)
def load_muhurat_weights(config_path: Path = None) -> dict:
    """
    Load and cache weights from YAML.

    Cached on first call per unique config_path. Pass a different config_path
    to load alternate configs (useful in tests). Pass None to use the bundled
    default at config/muhurat_weights.yaml.

    Args:
        config_path: Absolute Path to a weights YAML file, or None for the default.

    Returns:
        Raw dict parsed from YAML: {"defaults": {...}, "events": {...}}.

    Raises:
        FileNotFoundError if config_path does not exist.
        yaml.YAMLError if the file is not valid YAML.
    """
    if config_path is None:
        config_path = _DEFAULT_CONFIG_PATH
    raw = yaml.safe_load(config_path.read_text())
    return raw


def get_weights_for_event(event: str, config_path: Path = None) -> dict:
    """
    Return effective weights for `event`: defaults merged with event-specific overrides.

    Merge strategy: start from a copy of "defaults", then apply any keys present
    in events[event] on top. Keys in defaults but absent from the event override
    retain their default value. This means per-event configs are partial — only
    the keys that differ from defaults need to be specified.

    Args:
        event: Event key (e.g. "vivah", "griha_pravesh"). If the event has no
               override entry, pure defaults are returned.
        config_path: Optional Path override (for testing). None = bundled default.

    Returns:
        dict with keys: tithi, nakshatra, vara, yoga, planet, native, avoid_penalty.
    """
    cfg = load_muhurat_weights(config_path)
    weights = dict(cfg["defaults"])
    weights.update(cfg.get("events", {}).get(event, {}))
    return weights


def invalidate_weights_cache() -> None:
    """
    Clear the lru_cache so the next call re-reads from disk.

    Call this after programmatically editing the YAML config (e.g. in tests or
    admin tooling). In production, a sidecar restart achieves the same effect.
    """
    load_muhurat_weights.cache_clear()
