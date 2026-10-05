---
artifact: NATIVE_DIRECT_RULINGS_20261005
version: "1.0"
status: RECORD
date: 2026-10-05
source: "Owner's statements to the operating steward (madhav-f2), recorded verbatim by the steward (steward M20261005T070426-90c6, OWNER-RULING-6-7); written down by Stream B"
changelog:
  - "1.0 (2026-10-05): recorded."
---

## Ruling 6 — small-test owner items 1 and 2: the owner goes with the steward's recommendation

Owner's words (verbatim): **"for 1 and 2, I'll go with your recommendation."**

Context (the steward's, not the owner's words):
- Item 1 = which database identity runs the small-test clean-up tool (the teardown). The steward's recommendation: the application owner role (`amjis_app`) as a one-off, with the owner's word to use that credential.
- Item 2 = the declared control-plane exception for the Firebase management service agent. The steward's recommendation: KEEP the exception in force until PR 3119 (the proper allow-list change) is merged, then remove the exception variable.

Steward's reading (recorded as the steward's): both recommendations are accepted; the steward will state this reading back to the owner for correction.

## Ruling 7 — the time range Gochara builds for ANY chart (the formula)

Owner's words (verbatim): **"For time range, let me give you the approach you should take. This is the formula for every person's chart. Gochara should use the following algorithm logic to determine the range in which it should build. Any person's longevity is assumed to be 100 years. The superset we will first consider is from the birth date to 100 years of that person. The logic we will apply is: If the person's life event log is available, then the life event log's first event is what we will consider the starting date, not the birth date. If the person's life event log is not available, then we will consider the date on which the rebuild is happening to be the date. The end date remains the birth date plus 100 years of longevity. The start date depends on a choice between the earliest date in the life event log and, if the life event log is missing, the current date. Did you understand this? Let's close this first."**

Steward's reading (recorded as the steward's reading): the horizon END is the birth date plus 100 years for every chart (the native's: 2084-02-05). The horizon START is the date of the earliest life-event-log event when a log exists, else the date of the build.

Open point the steward put back to the owner: the native's log opens with the birth itself (1984-02-05) as its first entry, then an entry dated 1995 (year only), then 1998-02-16; which is the first event for this rule.

Stream B's notes for the record (consequences read from the code, not rulings): (1) the sky-event substrate and the per-body arc index cover 1998-01-01 to 2085-01-01 (`SUBSTRATE_DOMAIN_START/END`): a start before 1998 (the birth, or the 1995 entry) lies OUTSIDE what the builder can see, so it needs the domain extended first and the whole substrate rebuilt; a start of 1998-02-16 or later and an end of 2084-02-05 are inside it. (2) It supersedes the scored horizon (1998-01-01 to 2026-04-17) as the horizon for a build meant to be served, and settles gap G9 in principle; the one-year small test (all_classes_1y) and the one_class_full slice are unaffected. (3) A start that is a date of build moves with every rebuild, so a generation's horizon would be part of its identity (the manifest vector already carries it).
