PAR-F36-NEEDS-LEASE

From: S2 MĀTRĀ
Paths: platform/src/lib/retrieval/registry/layers/register_d7_channel.ts
Reason: F-36's DIAGNOSIS.md confirms this finding's mechanism (the offset-clamp-with-no-
disclosure defect at register_d7_channel.ts:924, echoed at :1140/:1216) is not in any file S2
owns. This file is NOT listed in ANY stream's OWNS array in LEASES.json — it is a lease gap, the
same situation LEASES.json documents for platform-mcp/src/lib/kala_envelope.ts before its
post-Phase-0 assignment to S5. It also is not the CL-06 "total dies under composition" defect at
all — this file's `total` field (register_d7_channel.ts:1091-1120) is ALREADY a correct,
independent COUNT(*) query, confirmed live and unaffected by the offset clamp; the actual bug is
a silent offset ceiling with no `offset_requested`/`offset_clamped` disclosure, closer in spirit
to S3's CL-13 disclosure work than to S2's CL-06 count-arithmetic work.
Ask: recommend assigning this file to S5 MŪLA by analogy — S5 already owns "capability SQL under
layers/L0_*" and every L1_ganita/**, L2_bodha/**, and (post-Phase-0) L3_kala/** query file;
register_d7_channel.ts is the same class of raw-retrieval-handler code, one directory up from
those. Alternatively, if the conductor judges the disclosure-pattern kinship to CL-13 stronger
than the file-family kinship to S5's other L*_query files, S3 SATYA (CL-13's owning stream) is a
plausible second candidate. Either way, S2 has no natural claim on this file and is not the right
stream to build the fix.
Status: OPEN, awaiting conductor disposition. Does not block any other S2 lane — no file overlap
with S2's OWNS list.
