# BLOCKERS_BY_CLASS
bar: N-268 (named ceilings and disclosure gaps)
Measured on: full census of an evaluation copy of production, backup 1791835965446 taken 2026-10-12T20:15:07.308Z (instance amjis-ri02-validation-c720f1832, restored from amjis-postgres). Not a census of the live production database.

7 assets are not certified. GENUINE DEFECT = writer / data / code wrong, a non-canonical value / placeholder / source gap found, or a FAIL; MISSING DECLARATION = an engine form exists and the declaration is not written; STRUCTURAL = no engine form or detector exists / an instrument limit / needs a stored aggregate, a keyed read or a build run.

| class | blockers | assets with at least one | assets blocked ONLY by this class |
|---|---|---|---|
| GENUINE DEFECT | 5 | 4 | 4 |
| MISSING DECLARATION | 0 | 0 | 0 |
| STRUCTURAL | 2 | 1 | 0 |
| UNCLASSIFIED | 3 | 3 | 2 |

| asset | class | criterion | verdict | why |
|---|---|---|---|---|
| bg_ephemeris_engine | UNCLASSIFIED | Earn.service_state | NO_DETECTOR | no classification rule matches this blocker |
| bg_panchanga | UNCLASSIFIED | Earn.service_state | NO_DETECTOR | no classification rule matches this blocker |
| bo_chart_gestalt | GENUINE DEFECT | Null.blank_rows | PARTIAL | a listed constant literal is not shown to be an honest absence statement (a placeholder candidate: it reads as content) |
| bo_chart_gestalt | GENUINE DEFECT | Null.schema_default | PARTIAL | a listed constant literal is not shown to be an honest absence statement (a placeholder candidate: it reads as content) |
| bo_laksana | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_laksana_rerank | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_samskara | UNCLASSIFIED | Narr.agree | PARTIAL | no classification rule matches this blocker |
| bo_samskara | STRUCTURAL | Null.blank_rows | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| bo_samskara | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_structural | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
