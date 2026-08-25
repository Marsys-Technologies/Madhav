"""Shadow-only operating plan for the elevated tracker.

It produces distinct launchd job specifications for synchronization, retention-aware
snapshots and restore verification. Installation is intentionally outside this module:
an attested immutable release and the governed cutover packet are prerequisites.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import uuid
from pathlib import Path
from typing import Any

from elevation import ElevationStore, InvariantViolation, digest, utc_now


class ShadowOperations:
    LABEL_PREFIX = "com.marsys.pariprashna-assurance.shadow"

    def __init__(self, *, runtime: Path, source_sha: str, retention_days: int = 30, store: ElevationStore | None = None):
        if retention_days < 7:
            raise InvariantViolation("RETENTION_FLOOR", "shadow retention must keep at least seven daily snapshots")
        self.runtime = runtime
        self.source_sha = source_sha
        self.retention_days = retention_days
        self.store = store
        self.runtime.mkdir(parents=True, exist_ok=True)
        os.chmod(self.runtime, 0o700)

    def launchd_jobs(self) -> list[dict[str, Any]]:
        base = {
            "runtime": str(self.runtime),
            "source_sha": self.source_sha,
            "loopback_only": True,
            "accepted_service_target": False,
            "alert_on_failure": True,
        }
        return [
            {**base, "label": f"{self.LABEL_PREFIX}.sync", "frequency": "continuous", "purpose": "adapter synchronization and watchdog"},
            {**base, "label": f"{self.LABEL_PREFIX}.snapshot", "frequency": "daily", "purpose": f"immutable snapshot and {self.retention_days}-day retention"},
            {**base, "label": f"{self.LABEL_PREFIX}.restore", "frequency": "weekly", "purpose": "weekly restore verification"},
        ]

    def _store(self) -> ElevationStore:
        if not self.store:
            raise InvariantViolation("SHADOW_STORE_REQUIRED", "operations require an explicit shadow elevation store")
        return self.store

    def create_snapshot(self) -> dict[str, Any]:
        """Create a create-only private SQLite snapshot, never of the accepted runtime."""
        store = self._store()
        snapshots = self.runtime / "snapshots"
        snapshots.mkdir(mode=0o700, exist_ok=True)
        target = snapshots / f"shadow-{utc_now().replace(':', '').replace('-', '')}-{uuid.uuid4().hex}.sqlite3"
        source = sqlite3.connect(f"file:{store.database}?mode=ro", uri=True)
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close(); source.close()
        os.chmod(target, 0o400)
        return {"path": target, "source_sha": self.source_sha, "projection_hash": digest(store.reconcile(now="2000-01-01T00:00:00Z"))}

    def verify_restore(self, snapshot: Path) -> dict[str, Any]:
        if snapshot.parent != self.runtime / "snapshots" or not snapshot.is_file() or snapshot.is_symlink():
            raise InvariantViolation("SNAPSHOT_PATH", "restore verification accepts only a regular shadow snapshot")
        source_hash = digest(self._store().reconcile(now="2000-01-01T00:00:00Z"))
        with tempfile.TemporaryDirectory(dir=self.runtime, prefix="restore-") as recovery:
            target = Path(recovery) / "shadow.sqlite3"
            source = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
            destination = sqlite3.connect(target)
            try:
                source.backup(destination); destination.commit()
            finally:
                destination.close(); source.close()
            restored = ElevationStore(target)
            restored_hash = digest(restored.reconcile(now="2000-01-01T00:00:00Z"))
        return {"ok": source_hash == restored_hash, "source_hash": source_hash, "restored_hash": restored_hash, "isolated": True}


def cutover_guard(packet: dict[str, Any]) -> None:
    """Fail closed: no live swap is implied by a test, observation, release, or packet draft."""
    raise InvariantViolation("CUTOVER_NOT_AUTHORIZED", "this shadow implementation never performs a live cutover; a separately recorded native decision and independently verified packet are required")
