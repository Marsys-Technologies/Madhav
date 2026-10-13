# BLOCKERS_BY_CLASS
bar: N-268 (named ceilings and disclosure gaps)
Measured on: full census of an evaluation copy of production, backup 1791868791537 taken 2026-10-13T05:21:32.951Z (instance amjis-ri02-validation-c720f1832, restored from amjis-postgres). Not a census of the live production database.

5 assets are not certified. GENUINE DEFECT = writer / data / code wrong, a non-canonical value / placeholder / source gap found, or a FAIL; MISSING DECLARATION = an engine form exists and the declaration is not written; STRUCTURAL = no engine form or detector exists / an instrument limit / needs a stored aggregate, a keyed read or a build run.

| class | blockers | assets with at least one | assets blocked ONLY by this class |
|---|---|---|---|
| GENUINE DEFECT | 4 | 4 | 4 |
| MISSING DECLARATION | 0 | 0 | 0 |
| STRUCTURAL | 2 | 1 | 0 |
| UNCLASSIFIED | 1 | 1 | 0 |

| asset | class | criterion | verdict | why |
|---|---|---|---|---|
| bo_laksana | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_laksana_rerank | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| bo_samskara | UNCLASSIFIED | Narr.agree | PARTIAL | no classification rule matches this blocker |
| bo_samskara | STRUCTURAL | Null.blank_rows | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| bo_samskara | STRUCTURAL | Null.schema_default | PARTIAL | the writer scan has an unresolved write path or a truncated listing (the scan cannot prove the column clean) |
| ga_structural | GENUINE DEFECT | Vocab.alias | PARTIAL | mixed spelling families of canonical terms in one column (cross-layer drift) |
| ga_vichara | GENUINE DEFECT | Build.dag | FAIL | a FAIL verdict |
