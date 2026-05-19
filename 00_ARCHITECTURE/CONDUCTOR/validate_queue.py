#!/usr/bin/env python3
"""Validate session_queue.yaml against queue_entry_schema.json.

Usage:
    python validate_queue.py                         # validates session_queue.yaml
    python validate_queue.py smoke/smoke_queue.yaml  # validates alternate queue file

Exit codes:
    0  All entries valid
    1  Schema validation failure (see stderr)
    2  Import error or script error (check pip install jsonschema pyyaml)
"""
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

base = Path(__file__).parent

# Determine queue file to validate
queue_file = base / "session_queue.yaml"
if len(sys.argv) > 1:
    candidate = Path(sys.argv[1])
    if not candidate.is_absolute():
        candidate = base / candidate
    queue_file = candidate

if not queue_file.exists():
    print(f"ERROR: Queue file not found: {queue_file}", file=sys.stderr)
    sys.exit(2)

# Load schema
schema_path = base / "schemas" / "queue_entry_schema.json"
if not schema_path.exists():
    print(f"ERROR: Schema not found: {schema_path}", file=sys.stderr)
    sys.exit(2)

try:
    schema = json.loads(schema_path.read_text())
except json.JSONDecodeError as e:
    print(f"ERROR: Could not parse schema JSON: {e}", file=sys.stderr)
    sys.exit(2)

# Load queue
try:
    queue = yaml.safe_load(queue_file.read_text())
except yaml.YAMLError as e:
    print(f"ERROR: Could not parse queue YAML: {e}", file=sys.stderr)
    sys.exit(2)

if not isinstance(queue, dict):
    print("ERROR: Queue YAML must be a mapping at the top level", file=sys.stderr)
    sys.exit(1)

entries = queue.get("entries", [])
if not isinstance(entries, list):
    print("ERROR: Queue YAML must have an 'entries' list", file=sys.stderr)
    sys.exit(1)

# Validate each entry
failed = 0
for i, entry in enumerate(entries):
    session_id = entry.get("session_id", f"<entry {i}>")
    try:
        validate(instance=entry, schema=schema)
    except ValidationError as e:
        print(f"FAIL  [{session_id}]: {e.message}", file=sys.stderr)
        if e.path:
            print(f"      Path: {' -> '.join(str(p) for p in e.path)}", file=sys.stderr)
        failed += 1
    except SchemaError as e:
        print(f"ERROR: Schema itself is invalid: {e.message}", file=sys.stderr)
        sys.exit(2)

if failed:
    print(f"\nFAIL — {failed} of {len(entries)} entries invalid", file=sys.stderr)
    sys.exit(1)

# Cross-validate depends_on references
all_ids = {e.get("session_id") for e in entries}
dep_errors = 0
for entry in entries:
    for dep in entry.get("depends_on", []):
        if dep not in all_ids:
            print(f"FAIL  [{entry.get('session_id')}]: depends_on '{dep}' not found in queue",
                  file=sys.stderr)
            dep_errors += 1

if dep_errors:
    print(f"\nFAIL — {dep_errors} dangling depends_on reference(s)", file=sys.stderr)
    sys.exit(1)

print(f"OK — {len(entries)} entries valid ({queue_file.name})")
