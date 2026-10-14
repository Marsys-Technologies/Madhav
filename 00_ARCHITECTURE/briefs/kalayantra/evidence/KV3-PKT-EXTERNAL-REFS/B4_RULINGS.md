<!-- Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/lane2/B4_RULINGS.md -->
<!-- Original sha256: 97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e; date: 2026-10-14 -->
# Cockpit rulings on the B-4 packet plan's open points (session 94345d41, 2026-10-12)

Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T164123Z-b4-packetplan/OPEN_POINTS.md (OP-01 … OP-18). The owner's standing rule: no wasteful cycles from thin briefs — pilot first, stop when blocked.

- Q1 (OP-01): accepted. wave 0 = the first PRIORITY section; everything later is a preparation bucket, not an execution move. packet.wave is stamped by the cockpit, never guessed by a writer.
- Q2 (OP-02): accepted. No new BUILD packet for the 11 inherited ACCEPTED PRs; their admission descriptors are cockpit work at Wave 0, after installation.
- Q3 (OP-03): accepted. No builder packet for the 12 V-* exits; their exit descriptors are settled when the dispatcher exists.
- Q4 (OP-04), Q5 (OP-05): accepted. No writer invents child ids or split ids. J-0m, KA-3b, K5-G1b, K5-3 are NOT written now.
- Q6 (OP-06), Q7 (OP-07): accepted. No campaign packet edits the executor table, migrate.ts or deploy.yml; scopes follow the protected list.
- Q8 (OP-08): accepted. J-4a waits for J-4p's settled-build contract; not written now.
- Q9 (OP-09): accepted. K5-G1a/G1b wait for a schema-prerequisite item; not written now.
- Q10 (OP-10) to Q12 (OP-12), Q17 (OP-17): accepted as recommended.
- Q13 (OP-13): the shared evidence / PR-body template is frozen by the cockpit AFTER the pilot shows what the first two packets actually need; the pilot proposes it, does not assume it.
- Q14 (OP-14): accepted. No writer fabricates release pins or receipts. Campaign packets written before run/RELEASE_RECEIPT.json exists are DRAFTS: kypacket.py check is expected to refuse them on the missing pins and on nothing else; the pilot must show exactly that.
- Q15 (OP-15), Q16 (OP-16): items whose required source is missing or whose custody is unsettled are NOT written now; the cockpit resolves the source or the coordination first.
- Q18 (OP-18): the six-batch split is kept as the eventual plan. It is NOT launched now. Order of work: (1) pilot = J-0c and J-0d, the first two items the campaign executes; (2) cockpit reads the pilot; (3) only then, and only for items with no open point above, further writers.

## Amendment 2026-10-13 (owner: cut governance to the essential)
- Q15 amended: a required source that exists outside the checkout is mirrored into the assembly by the cockpit (byte-identical, provenance in the commit message) and the packet pins the mirror; drafting is NOT held for it. Done for 00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md (from campaign/pravaha @ eea2610d0, sha256 d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47). Only a source that exists nowhere holds a packet.
