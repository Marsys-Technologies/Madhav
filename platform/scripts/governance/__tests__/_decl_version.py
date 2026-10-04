"""_decl_version.py: the declarations file's CURRENT version, read from the file at import, so a test that pins "the committed file is a real, validated declarations file" does not break at
every minor bump (C1-1 review MEDIUM 5b: three lanes bump the version in parallel and each one used to have to edit ~10 literals). The per-version CONTENT pins stay in the tests that own them."""
import json
import pathlib

CURRENT = json.loads((pathlib.Path(__file__).resolve().parent.parent / "asset_declarations.json").read_text(encoding="utf-8"))["version"]
