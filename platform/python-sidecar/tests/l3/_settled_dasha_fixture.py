"""Receipt identity labels for isolated SQL fixtures, not native chart facts."""
import json
from uuid import UUID

from services.gochara_kernel.dasha_read import SETTLEMENT_PATH

_receipt = json.loads(SETTLEMENT_PATH.read_text())
CHART_ID = str(UUID(_receipt["chart_id"]))
BUILD_ID = str(UUID(_receipt["run_id"]))

DASHA_DDL = f"""
DROP TABLE IF EXISTS chart_dashas;
CREATE TABLE chart_dashas (
  dasha_row_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id UUID NOT NULL,
  build_id UUID NOT NULL DEFAULT '{BUILD_ID}'::uuid,
  ayanamsha_id TEXT NOT NULL,
  system_id TEXT NOT NULL,
  level_n INT NOT NULL,
  parent_row_id UUID,
  lord_graha TEXT,
  start_iso TIMESTAMPTZ NOT NULL,
  end_iso TIMESTAMPTZ NOT NULL,
  verification_pass_status TEXT NOT NULL DEFAULT 'two_pass_verified',
  applies_to_this_chart_flag BOOLEAN NOT NULL DEFAULT TRUE,
  is_truncated_at_window_start BOOLEAN NOT NULL DEFAULT FALSE,
  is_truncated_at_window_end BOOLEAN NOT NULL DEFAULT FALSE,
  start_date DATE, end_date DATE, lord_to_parent_relationship TEXT
);
"""


def seed_default_periods(conn):
    conn.execute("DELETE FROM chart_dashas WHERE chart_id = %s", (CHART_ID,))
    for system, lord in [("vimshottari", "Venus"), ("yogini", "Mangala")]:
        conn.execute("""INSERT INTO chart_dashas
            (chart_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso, end_iso)
            VALUES (%s, 'lahiri_chitrapaksha', %s, 1, %s,
                    '2020-01-01T00:00:00Z', '2030-01-01T00:00:00Z')""",
                     (CHART_ID, system, lord))
