# `consumer_probe` — the authenticated consumer-path probe (J-6l-a61, W5W6-READINESS brief 01 Part B)

Script `fleet/consumer_probe.py` (standard library only) · table kind `consumer_probe` (`executor_ops.json`) · shard `tests/executor_pin_shards/J-6l-a61.json` ·
tests `tests/test_consumer_probe.py`. Nothing here was run against production or any live endpoint; every test uses a fake transport.

## What it is

One reviewed, read-only, `production:false` kind. A request carries only `args.probe`; the script holds the whole call (host, path, tool, arguments, chart).
Per probe: one `POST https://amjis-mcp-qm256lasva-el.a.run.app/mcp` (JSON-RPC `tools/call`, stateless Streamable HTTP, `Accept: application/json, text/event-stream`),
the credential in `Authorization: Bearer …` **only** (never `?api_key=`; `server.ts` `resolveAuthHeader` logs URLs), HTTPS, no redirect followed, no proxy.
The output is one `ky.consumer_probe/1` record of typed fields: no response body, no key, no chart id, no name.

* **Owner act O-W56-B (the key — never read, stored or requested by this change).** Provision a **READ-ONLY MCP key of role `guest`** (never `super_admin`) for a
  dedicated executor principal that is **entitled to the canonical chart only** (`remoteAuthorize(principal, chart_id)` gates every chart-scoped tool:
  `published_request.ts`, `register_gochara_windows.ts`), and put it in the executor's own environment as `KY_CONSUMER_PROBE_KEY` (`executor.env.example.sh`).
  Every probed tool is a `*_get` read; the rate limit is per `key_id` (`checkMcpRateLimit`), so a dedicated key does not eat the interactive budget.
* **Safe to ship enabled before the key exists.** The kind `needs: consumer_reader`, a capability that is true only while the executor holds the key
  (`capabilities()`); without it admission says `capability_missing: consumer_reader` (same style as `layer_verifier`). The executor hands the key to this kind's
  child alone (`execute`), under the one name `KY_CONSUMER_PROBE_KEY`; `CHILD_ENV_ALLOW` is unchanged, so no other kind's child ever receives it. `redact()` also
  scrubs the key's literal value from every receipt and log line, and `consumer_probe_proof` fails a receipt whose stdout/stderr contains it.
* **The executor accepts a run only on its own measurement of the record** (`consumer_probe_proof`): exactly one `ky.consumer_probe/1` line binding this
  `operation_id`, `request_sha256` and probe id; `status MEASURED`; `http_status 200`; `credentials_sent: true` (the header was sent); `credential_echoed: false`
  (measured by the script: the raw response body or Content-Type did not contain the key); `body_sha256`/`body_bytes` present; no `body`. A read-only run that holds
  is then accepted mechanically (`kind_read_only_per_table`), like `served_probe`.

## Probe ids and what each reads (the ids the pack must declare)

| probe id | MCP tool and arguments (script table) | what the answer states → `result` |
|---|---|---|
| `gochara_served_head` | `gochara_activation_get {chart_id}` (no `as_of_date`: the tool resolves the **authoritative** generation itself and withholds a governed generation that is not published and sealed) | `coverage.status:'unpublished'` → `absent`; else the generation named by `coverage.coverage_manifest.generation` / the window rows → `served` (null generation → `unstated`; two generations or `backing_data_reachable:false` → `refused`) |
| `kala_view_1` … `kala_view_7` | `kala_<view>_get {chart_id, published_request:{limit:1}}` for the views `now, ahead, priority, elect, story, ritual, explain` (`registry_alias.ts` `KalaView`; the same seven as `ka_tulana` `"views"`) | published snapshot with rows → `served`; published, no rows → `no_matching_rows`; `manifest_id:null, empty_reason:'unpublished'` → `absent`; anything not the documented snapshot, a tool error or another view/chart → `refused` |
| `kala_now_sentinel` | `kala_now_get {chart_id, published_request:{limit:50}}` | as above, plus: every published `kala_obstruction` `effective_state` is `information_unavailable` or `evaluated_silent` → `sentinel_negative_space`; some other valid state → `served`; no usable obstruction state → `no_obstruction_state` |
| `kala_arrival_line` | the same call, read as `arrivalFromPublishedNow` reads it | published `kala_obstruction` rows with `data.generation == snapshot.generation` and a state in the closed vocabulary → `served` with `effective_states`; otherwise `no_obstruction_state` (the consumer's arrival line is null) |

`kala_now_sentinel` and `kala_arrival_line` are one tool call read two ways (per-probe `result` enums, not extra tools). Result enum: `served, absent, no_matching_rows,
no_obstruction_state, sentinel_negative_space, unstated, refused`.

**For the pack revision (brief 08; this change does not edit the pack):**
* `gates.HEAD_PROBES` → `["gochara_served_head"]` (plus `kala_view_1` … `kala_view_7` if the head gate also wants the Kāla heads). `consumer_gate.K96_READ_PROBES` →
  `["kala_view_1", …, "kala_view_7", "kala_now_sentinel", "kala_arrival_line"]`. `http_probe.NOT_MEASURABLE` names `kala_seven_views`: that aggregate id is **not** a probe
  here; the pack declares the seven `kala_view_N` ids instead.
* `gates.live` must read, from the receipt's `consumer_probe` block (or the output line): `schema == "ky.consumer_probe/1"`, `status == "MEASURED"`, `http_status == 200`,
  `result` (the expected per-probe value), `generation`, `manifest_id`, `body_sha256`, `credentials_sent is True`, `credential_echoed is False`. **A `null` generation or
  `result` of `refused/absent/unstated` is not a pass** (N.8). The executor receipt is `COMPLETED` only when the proof above holds, but it does not judge `result` — the gate does.
* The probe kind for these ids is `consumer_probe`, not `http_probe`: `pack/readiness.probe_ids_of_tree` currently reads `ops["http_probe"]["script"]` and must also read
  `ops["consumer_probe"]["script"]` (its `PROBES` keys) in the pack revision. The pack's templates `29-probe-before`, `31-probe-after`, `31-probe-after-rollback` ask for
  `consumer_probe probe=<id>` for these ids and stay `http_probe probe=mcp_health` for the credential-free health/image/migration read.
* `image` and `migration_set` are **always null** here: neither response states them. The deployed image digest and migration set come from `http_probe mcp_health`.

## Mapping to `fleet/j6_live_readback.py` (J-6l)

| J-6l input | from `consumer_probe` | note |
|---|---|---|
| `ky.j6_consumer_path/1` (`mode:'authority'`, `result:'ACCEPTED'`, `by` ∈ v1..v4, `binding`, `deployment_sha256`, `evidence_sha256`) | **not produced here.** `evidence_sha256` may be the sha256 of the verifier-accepted receipt of a `consumer_probe` run (`output_sha256` of the receipt); the ACCEPTED verdict and `by` are the independent verifier's | the probe is the *measurement*; acceptance stays with a V signer (`j6_live_readback.py` header: "owed by an independent verifier") |
| `ky.j6_deployment_observation/1` (`image_digest`, `commit`, `migrations`, `url`, `observed_at`) | `url` = `https://amjis-mcp-qm256lasva-el.a.run.app/mcp` is the consumer URL; **`image_digest`/`commit`/`migrations` come from `http_probe mcp_health`**, not from here | `observed_at` ↔ record `measured_at` |
| `response.status` | record `http_status` | |
| `response.sha256`, `response.bytes` | record `body_sha256` (**canonical digest of the tool result object**), `body_bytes` (raw HTTP bytes) | **not equal to `raw_sha(body)`** — see below |
| `response.served_generation`, `served_manifest_id` | record `generation`, `manifest_id` | |
| `response.body_base64` and the `gochara_v5_windows/1` envelope (`schema`, `seal`, `classes[].completeness`, `refusal`, `manifest_status`) | **cannot be supplied**: this kind keeps no body by design | |

**Open point for the cockpit (not settled here, because it is a decision about `j6_live_readback.py`, which this change does not edit).** `j6_live_readback.capture()`
verifies `gochara_v5_windows/1` — the Python sidecar's `serving_reader.read_v5` envelope (`POST /api/compute/gochara/v5/windows`) — and keeps its exact bytes. The MCP tool
`gochara_activation_get` that `gochara_served_head` calls is a **different surface** (it serves `kala_gochara_windows` for the authoritative generation and states `coverage`,
not that envelope). So a `consumer_probe` record evidences that a consumer sees the served head and its generation through MCP; it does **not** replace the sealed-envelope capture.
Options: (a) keep the operator-captured body for the J-6l capture and use `consumer_probe` as the independent consumer-path evidence the V signer cites;
(b) add a digest-bound sample mode to `j6_live_readback`; (c) add a second probe id once the flip exposes the envelope on a consumer route. (I) INTERPRETATION: (a) is what
this change assumes; nothing in it depends on the choice.

## Fields stated nowhere stay null (CLAUDE.md §N.7.6)

`image`, `migration_set`: never stated by either response → always null. `generation`/`manifest_id`: only as the response states them (Kāla snapshot top level; Gochara
`coverage.coverage_manifest.generation` / window rows); a Kāla `manifest_id` that is not a UUID is not recorded. `effective_states`: only the closed vocabulary of
`arrival_state.ts`, only for the two NOW probes.

## Not verified here (no live call was made)

The wire format (`tools/call` with `Accept: application/json, text/event-stream`, a stateless transport answering JSON or one SSE frame, `structuredContent.object` or
`content[0].text`) is taken from the repository's own clients (`platform/scripts/audit/doctrine_harness/lib/mcp_client.ts`, `platform/scripts/gochara/probe_gochara.py`,
`deploy.yml` smoke) and the server source; the installed SDK (`platform-mcp/node_modules`) was not present. The first live run is the owner's O-W56-B follow-up and should be
a single `probe=kala_view_1` read before any gate relies on the kind.
