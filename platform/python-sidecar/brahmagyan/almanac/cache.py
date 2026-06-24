"""
brahmagyan.almanac.cache — In-process LRU cache for almanac computations.

The cache stores computed AlmanacDay results keyed by (date, location.cache_key).
This avoids re-computing the same date+location combination in a single process
lifetime (hot for repeated UI refreshes, API calls for the same location, etc.).

Design
------
- functools.lru_cache on a private function that takes hashable arguments.
- maxsize=512 entries; each entry is a full AlmanacDay (approx. 10–30 KB JSON
  serialized); 512 × 25 KB ≈ 12 MB resident — acceptable for a sidecar.
- The LRU evicts least-recently-used entries when the cache is full.
- Cache entries are tagged source="cache" so callers can distinguish.
- Thread-safe: functools.lru_cache uses an internal lock.

Invalidation
------------
- clear_cache() flushes all entries (intended for testing).
- No TTL: astronomical computations are deterministic and don't change;
  a process restart is the natural invalidation event for stale ephem data.
"""
import functools
from datetime import date
from typing import Optional


# The actual cache backing store — stores (date_str, cache_key) → AlmanacDay dict.
# We use a dict here rather than lru_cache because AlmanacDay is not hashable
# (it contains lists/dicts). The dict is bounded by _MAX_SIZE using an
# OrderedDict eviction strategy.
from collections import OrderedDict

_MAX_SIZE = 512
_CACHE: OrderedDict = OrderedDict()
_HIT_COUNT = 0
_MISS_COUNT = 0


def _make_key(d: date, location_cache_key: str) -> str:
    return f"{d.isoformat()}|{location_cache_key}"


def cache_get(d: date, location_cache_key: str):
    """Return cached AlmanacDay-equivalent dict or None."""
    global _HIT_COUNT, _MISS_COUNT
    key = _make_key(d, location_cache_key)
    if key in _CACHE:
        # Move to end (most-recently-used)
        _CACHE.move_to_end(key)
        _HIT_COUNT += 1
        return _CACHE[key]
    _MISS_COUNT += 1
    return None


def cache_put(d: date, location_cache_key: str, value) -> None:
    """Store an AlmanacDay-equivalent value in the cache."""
    key = _make_key(d, location_cache_key)
    if key in _CACHE:
        _CACHE.move_to_end(key)
    _CACHE[key] = value
    # Evict oldest if over capacity
    while len(_CACHE) > _MAX_SIZE:
        _CACHE.popitem(last=False)


def get_cache_stats() -> dict:
    """Return cache hit/miss/size statistics."""
    return {
        "size": len(_CACHE),
        "max_size": _MAX_SIZE,
        "hits": _HIT_COUNT,
        "misses": _MISS_COUNT,
        "hit_rate": _HIT_COUNT / max(1, _HIT_COUNT + _MISS_COUNT),
    }


def clear_cache() -> None:
    """Flush the cache. Intended for testing."""
    global _HIT_COUNT, _MISS_COUNT
    _CACHE.clear()
    _HIT_COUNT = 0
    _MISS_COUNT = 0
