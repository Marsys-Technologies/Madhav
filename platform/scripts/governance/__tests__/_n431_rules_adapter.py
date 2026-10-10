"""_n431_rules_adapter.py: the thinnest possible adapter from the sandbox's `function(input_dict)` contract to the real bg_rules parser (N-431 R2 smoke test).

`brahmagyan.l0_rules.extract_rules_from_chunk(chunk, valid_text_ids, ...)` takes two arguments and yields rows, while the sandbox calls `function(input_dict)` once per input and
JSON-serialises the return. This adapter is the glue: input `{"chunk": {...}, "valid_text_ids": [...]}` -> the list of rows the parser yields. It adds no logic of its own.
The rows the parser yields are already JSON-native (rule_id is a str, the *_jsonb columns are JSON text), so nothing is coerced. If the census wires the real check it must pin its
OWN adapter (this file is a test fixture), because the adapter is part of the code whose behaviour is being certified.
"""
from __future__ import annotations

from brahmagyan.l0_rules import extract_rules_from_chunk


def run_chunk(item):
    return list(extract_rules_from_chunk(item["chunk"], set(item["valid_text_ids"])))
