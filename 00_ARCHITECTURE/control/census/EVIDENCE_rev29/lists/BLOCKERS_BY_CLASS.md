# BLOCKERS_BY_CLASS
bar: N-268 (named ceilings and disclosure gaps)
Measured on: full census of an evaluation copy of production, backup 1791769727082 taken 2026-10-12T01:50:08.186Z (instance amjis-ri02-validation-c720f1832, restored from amjis-postgres). Not a census of the live production database.

6 assets are not certified. GENUINE DEFECT = writer / data / code wrong, a non-canonical value / placeholder / source gap found, or a FAIL; MISSING DECLARATION = an engine form exists and the declaration is not written; STRUCTURAL = no engine form or detector exists / an instrument limit / needs a stored aggregate, a keyed read or a build run.

| class | blockers | assets with at least one | assets blocked ONLY by this class |
|---|---|---|---|
| GENUINE DEFECT | 3 | 3 | 1 |
| MISSING DECLARATION | 2 | 1 | 0 |
| STRUCTURAL | 6 | 2 | 1 |
| UNCLASSIFIED | 3 | 3 | 1 |

| asset | class | criterion | verdict | why |
|---|---|---|---|---|
| bg_sky_calendar | UNCLASSIFIED | Carr.D3 | PARTIAL | no classification rule matches this blocker |
| bo_laksana | UNCLASSIFIED | Ldgr.source_presence | ERRORED | no classification rule matches this blocker |
| bo_laksana | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_laksana_rerank | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_samskara | UNCLASSIFIED | Narr.agree | PARTIAL | no classification rule matches this blocker |
| bo_samskara | STRUCTURAL | Null.blank_rows | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| bo_samskara | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_structural | MISSING DECLARATION | Ldgr.source_presence | NO_DETECTOR | the Ldgr target-table / applicability ruling is not written |
| ga_structural | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| ga_structural | MISSING DECLARATION | Vocab.identity | NO_DETECTOR | the identity key declaration is not written |
| ga_vichara | STRUCTURAL | Build.history | PARTIAL | nothing has exercised the current code and contract yet: a build run is needed |
| ga_vichara | STRUCTURAL | Null.blank_rows | PARTIAL | no row data was read / unknown or empty entries in the checkable-row count |
| ga_vichara | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_vichara | STRUCTURAL | Vocab.alias | PARTIAL | no whole value is a term / unread columns: the spelling cannot be graded |
