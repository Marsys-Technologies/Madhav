# AM-10 re-pin evidence — chart 482012f1-710e-4a25-994a-93821f5871aa

* old pin: `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb`  →  new build: `75524b3e-102a-43ec-8cee-3f57fee752c3`
* verdict: **CLEAN**

## Evidence bound to this verdict
* window-clipped edges excluded from the shift statistics (clipped on BOTH builds, required unchanged), per level: MD start 1 / end 1, AD start 1 / end 1, PD start 1 / end 1
* settled notice sha256: e6f6f29b31c0137bbec974f2b122bc06639e3156ac928f0094f6eb28052b3343; source message Suvarna SS madhav-06 SETTLED-1 2026-10-04T08:15Z
* forensic report sha256: eed22a05ef218841bab23ec556a5d39658024e9fa1e8373ea2dce7603944dc5f — this tool checks that the file EXISTS and is NON-EMPTY ONLY; CLEAN is NOT independent validation of the seven FORENSIC anchors (that evidence is the L1 owner's)

## (b) rows per level
| level | old | new |
|---|---|---|
| MD | 13 | 13 |
| AD | 104 | 104 |
| PD | 923 | 923 |

matched 1040 · only-old 0 · only-new 0

## (c) integrity (new build)
* orphans: 0 · duplicates: 0

## (d) measured boundary shift (seconds, new − old, matched by (level, path))
| level | side | min | max | mean | n |
|---|---|---|---|---|---|
| MD | start | 6993 | 6993 | 6993.0 | 12 |
| MD | end | 6993 | 6993 | 6993.0 | 12 |
| AD | start | 6993 | 6993 | 6993.0 | 103 |
| AD | end | 6993 | 6993 | 6993.0 | 103 |
| PD | start | 6992 | 6993 | 6992.9 | 922 |
| PD | end | 6992 | 6993 | 6992.9 | 922 |

## (f) lord flips at matched (level, path) rows: 0 (D7 — any is a STOP)

## (f2) 34 BOUNDARY-SENSITIVE oracle instant(s): the lord at the instant differs old → new because a boundary MOVED, not because a lord changed (D8: re-run every event-dated comparison at these)
* 2010-08-18T15:50:23Z: {'MD': 'Mercury', 'AD': 'Mercury', 'PD': 'Mercury'} → {'MD': 'Saturn', 'AD': 'Jupiter', 'PD': 'Rahu'}
* 2010-08-18T15:50:24Z: {'MD': 'Mercury', 'AD': 'Mercury', 'PD': 'Mercury'} → {'MD': 'Saturn', 'AD': 'Jupiter', 'PD': 'Rahu'}
* 2013-01-14T07:17:23Z: {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Ketu'} → {'MD': 'Mercury', 'AD': 'Mercury', 'PD': 'Saturn'}
* 2013-01-14T07:17:24Z: {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Ketu'} → {'MD': 'Mercury', 'AD': 'Mercury', 'PD': 'Saturn'}
* 2013-11-21T04:44:19Z: {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Mercury'} → {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Saturn'}
* 2013-11-21T04:44:20Z: {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Mercury'} → {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Saturn'}
* 2014-01-11T12:14:23Z: {'MD': 'Mercury', 'AD': 'Venus', 'PD': 'Venus'} → {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Mercury'}
* 2014-01-11T12:14:24Z: {'MD': 'Mercury', 'AD': 'Venus', 'PD': 'Venus'} → {'MD': 'Mercury', 'AD': 'Ketu', 'PD': 'Mercury'}
* 2017-09-17T20:20:23Z: {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Moon'} → {'MD': 'Mercury', 'AD': 'Sun', 'PD': 'Venus'}
* 2017-09-17T20:20:24Z: {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Moon'} → {'MD': 'Mercury', 'AD': 'Sun', 'PD': 'Venus'}
* 2018-10-28T04:09:53Z: {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Venus'} → {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Ketu'}
* 2018-10-28T04:09:54Z: {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Venus'} → {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Ketu'}
* 2019-01-22T09:54:53Z: {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Sun'} → {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Venus'}
* 2019-01-22T09:54:54Z: {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Sun'} → {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Venus'}
* 2019-02-17T06:50:23Z: {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Mars'} → {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Sun'}
* 2019-02-17T06:50:24Z: {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Mars'} → {'MD': 'Mercury', 'AD': 'Moon', 'PD': 'Sun'}
* 2019-06-21T00:55:52Z: {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Saturn'} → {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Jupiter'}
* 2019-06-21T00:55:53Z: {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Saturn'} → {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Jupiter'}
* 2019-08-17T09:18:53Z: {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Mercury'} → {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Saturn'}
* 2019-08-17T09:18:54Z: {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Mercury'} → {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Saturn'}
* 2020-02-14T11:47:23Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Rahu'} → {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Moon'}
* 2020-02-14T11:47:24Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Rahu'} → {'MD': 'Mercury', 'AD': 'Mars', 'PD': 'Moon'}
* 2020-11-04T09:13:29Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Saturn'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Jupiter'}
* 2020-11-04T09:13:30Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Saturn'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Jupiter'}
* 2021-03-31T20:29:50Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Mercury'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Saturn'}
* 2021-03-31T20:29:51Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Mercury'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Saturn'}
* 2021-10-04T03:09:26Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Venus'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Ketu'}
* 2021-10-04T03:09:27Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Venus'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Ketu'}
* 2022-03-08T08:42:26Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Sun'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Venus'}
* 2022-03-08T08:42:27Z: {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Sun'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Venus'}
* 2022-09-02T21:05:23Z: {'MD': 'Mercury', 'AD': 'Jupiter', 'PD': 'Jupiter'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Mars'}
* 2022-09-02T21:05:24Z: {'MD': 'Mercury', 'AD': 'Jupiter', 'PD': 'Jupiter'} → {'MD': 'Mercury', 'AD': 'Rahu', 'PD': 'Mars'}
* 2027-08-18T21:50:23Z: {'MD': 'Ketu', 'AD': 'Ketu', 'PD': 'Ketu'} → {'MD': 'Mercury', 'AD': 'Saturn', 'PD': 'Jupiter'}
* 2027-08-18T21:50:24Z: {'MD': 'Ketu', 'AD': 'Ketu', 'PD': 'Ketu'} → {'MD': 'Mercury', 'AD': 'Saturn', 'PD': 'Jupiter'}

## (3) re-measured reference rows (every id in full)
* MD Mercury: `58afa482-4bce-42df-9c0d-0b5a2e02305e` 2010-08-18T15:50:23Z..2027-08-18T21:50:23Z  →  `1d1a80c0-53c6-5ff7-930a-52ff0f306cae` 2010-08-18T17:46:56Z..2027-08-18T23:46:56Z
* AD Ketu: `133b4500-ad36-4fff-8814-c6b0b253ca05` 2013-01-14T07:17:23Z..2014-01-11T12:14:23Z  →  `2103a226-b814-5ec7-b987-dffb421d5288` 2013-01-14T09:13:56Z..2014-01-11T14:10:56Z
* AD Moon: `14f20359-c30e-425d-b50f-45b017568ace` 2017-09-17T20:20:23Z..2019-02-17T06:50:23Z  →  `68789a8d-85ae-5eb5-8d88-a8743b23073c` 2017-09-17T22:16:56Z..2019-02-17T08:46:56Z
* AD Mars: `b1e4d515-6a94-4054-89ff-1ed2487f66ae` 2019-02-17T06:50:23Z..2020-02-14T11:47:23Z  →  `c4821baa-f4b0-51d5-b035-28ba2bd36a78` 2019-02-17T08:46:56Z..2020-02-14T13:43:56Z
* AD Rahu: `25a4b815-39bb-4b4a-b922-84a71778bb4f` 2020-02-14T11:47:23Z..2022-09-02T21:05:23Z  →  `a91faefa-f0d9-5a5d-950c-0adafb276fc7` 2020-02-14T13:43:56Z..2022-09-02T23:01:56Z
* PD Mercury: `6b843ad2-0759-4e7f-af7d-d39eac8b0325` 2013-11-21T04:44:19Z..2014-01-11T12:14:23Z  →  `65e30373-9db8-5606-a2bb-7c540114e135` 2013-11-21T06:40:51Z..2014-01-11T14:10:56Z
* PD Venus: `203406df-ddc3-44b8-a174-e48c5546d009` 2018-10-28T04:09:53Z..2019-01-22T09:54:53Z  →  `91980ae7-4081-5373-8781-c8a31b03d4ef` 2018-10-28T06:06:26Z..2019-01-22T11:51:26Z
* PD Venus: `5c07a7c9-0848-4e54-9f0b-2a9652101cef` 2021-10-04T03:09:26Z..2022-03-08T08:42:26Z  →  `48338f36-94c3-5495-b946-68f7f6e512bc` 2021-10-04T05:05:59Z..2022-03-08T10:38:59Z
* PD Saturn: `a4cf46db-fcb5-479c-8aab-ca87bcb551ff` 2019-06-21T00:55:52Z..2019-08-17T09:18:53Z  →  `d4d08aca-8995-51f3-a8ba-f9238a5311b3` 2019-06-21T02:52:24Z..2019-08-17T11:15:26Z
* PD Saturn: `73eea5c0-631f-4b48-8c8f-483c910c6fde` 2020-11-04T09:13:29Z..2021-03-31T20:29:50Z  →  `f72e343c-b877-516b-a089-54494031aa2d` 2020-11-04T11:10:02Z..2021-03-31T22:26:23Z
