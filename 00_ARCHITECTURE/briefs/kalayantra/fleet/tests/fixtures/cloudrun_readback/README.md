Shaped from the Cloud Run v1 Job/Execution resources (the field paths deploy.yml and gochara_seal_execution_check.py already read) and the
values deploy.yml deploys. NOT captured from a live response: the first real run of `cloudrun_job_readback` is the proof of the shape.
`SOME_API_TOKEN` is a planted non-allowlisted plain value that must never reach the output.

`logs_run.json` (SR-J3-READ-KINDS) is an INVENTED `gcloud logging read` page (no native data, record ids are `00000000-0000-8000-8000-…`): `STRETCH_SINK/1` and `STRETCH_SINK_SUMMARY/1` lines as `stretch_sink.log_line` / `summary_line` print them, `[event] <json>` `asset.substep` lines as `events.emit_event` prints them, Cloud Logging nanosecond timestamps, and one unrelated line carrying a planted token that must never reach the output. Tests derive the truncated and malformed variants from it.
