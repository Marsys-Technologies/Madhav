---
artifact: NATIVE_DIRECT_RULINGS_20261003
version: "1.0"
status: RECORD
date: 2026-10-03
source: "Owner's answers to the steward's two questions (AskUserQuestion, 2026-10-03), recorded verbatim by the steward"
changelog:
  - "1.0 (2026-10-03): recorded."
---

## Ruling 1 — timing of the protected window

Question: when to run the set-up sitting and the protected update block (which must not overlap the upstream S-L1 window).
Owner's answer (verbatim): **"As soon as possible."**
Steward's reading: run the set-up sitting and the protected train at the earliest moment all preconditions hold (source acceptance, 1243 applied and read back, the sitting checklist's pre-window checks), before Suvarna's W1 if their posted slot leaves room, otherwise immediately after SETTLED-1. Never across their window.

## Ruling 2 — who dispatches act 9 (the protected-window button)

Question: who presses the final dispatch (GitHub Actions → Deploy to Cloud Run → Run workflow → Gochara box).
Owner's answer (verbatim): **"You press it on my behalf."**
Effect: act 9 is dispatched by the steward (an AI agent session) under the owner's account at the governed moment of the sitting, and reported to the owner immediately afterwards. This supersedes the checklist's and runbook's "OWNER, in person" for act 9. It is recorded honestly: there is no separate human "yes" at the moment of dispatch; the owner's decision is this ruling.

## Ruling 3 — the first Gochara '5.0' build: a SMALL TEST build now, the one full build after Suvarṇa's elevation (steward id ST-OWNER-SMALL-TEST-1, M20261003T165948-a975)

Owner's words (verbatim): **"let's ship the code for the new Gochara and deploy it, but do a very small test rebuild to see if it's working, maybe 5%. ... Rather than doing a full rebuild now and losing it, I suggest we just test the deployed Gochara 5. If it is satisfactory, we wait for Suvarna's elevation when the upstream data is going to be up to date, and whatever corrections it finds with Gochara also get fixed in one rebuild of this expensive rebuild asset."**
Steward decision: agreed. Consequences recorded here: (1) the protected window and the code ship proceed unchanged. (2) NO full candidate build after SETTLED-1; the ONE full build and its seal move to AFTER Suvarṇa's elevation of the upstream assets and of Gochara itself. (3) In its place a SMALL TEST BUILD (about 5 percent of the full work): unsealed, never served, clearly marked as a test, removable. Scope to be proposed by Stream B with Stream A and approved by the steward BEFORE any production build; ST-SL1-HOLD still binds.
