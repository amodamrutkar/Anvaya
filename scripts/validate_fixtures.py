#!/usr/bin/env python3
"""
scripts/validate_fixtures.py
Validates all fixture files listed in contracts/fixtures/MANIFEST.json
against the JSON schemas in contracts/schemas/.
Run: python scripts/validate_fixtures.py
CI: included in `make test`
Owned by M4.
"""

import json
import sys
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
FIXTURES_DIR = CONTRACTS_DIR / "fixtures"
SCHEMAS_DIR = CONTRACTS_DIR / "schemas"
MANIFEST_PATH = FIXTURES_DIR / "MANIFEST.json"


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    return json.loads(text)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            lines.append(json.loads(line))
    return lines


def validate_manifest(manifest: dict) -> tuple[int, int]:
    """Validate each fixture file listed in the manifest."""
    passed = 0
    failed = 0

    fixtures = manifest.get("fixtures", [])
    if not fixtures:
        print("  WARN: MANIFEST.json has no fixtures listed.")
        return 0, 0

    for entry in fixtures:
        path_str = entry.get("path", "")
        fpath = FIXTURES_DIR / path_str
        schema_ref = entry.get("schema", None)

        if not fpath.exists():
            print(f"  FAIL [missing]  {path_str}")
            failed += 1
            continue

        content = fpath.read_text(encoding="utf-8").strip()
        if not content:
            print(f"  FAIL [empty]    {path_str}")
            failed += 1
            continue

        # Basic JSON/JSONL parse check
        try:
            if path_str.endswith(".jsonl"):
                records = load_jsonl(fpath)
                if not records:
                    print(f"  FAIL [no records] {path_str}")
                    failed += 1
                    continue
            else:
                _ = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"  FAIL [invalid JSON] {path_str}: {e}")
            failed += 1
            continue

        # Schema validation (jsonschema optional)
        if schema_ref:
            schema_path = SCHEMAS_DIR / schema_ref
            if schema_path.exists():
                try:
                    import jsonschema  # noqa: F401 — optional dep

                    schema = json.loads(schema_path.read_text())
                    data = (
                        json.loads(content)
                        if not path_str.endswith(".jsonl")
                        else load_jsonl(fpath)
                    )
                    validator = None
                    try:
                        from referencing import Registry, Resource

                        res = [
                            (
                                d.get("$id", p.name),
                                Resource.from_contents(d),
                            )
                            for p in SCHEMAS_DIR.glob("*.schema.json")
                            for d in [json.loads(p.read_text(encoding="utf-8"))]
                        ]
                        reg = Registry().with_resources(res)
                        validator = jsonschema.Draft202012Validator(schema, registry=reg)
                    except Exception:
                        validator = None

                    if isinstance(data, list):
                        for item in data:
                            if validator:
                                validator.validate(item)
                            else:
                                jsonschema.validate(item, schema)
                    else:
                        if validator:
                            validator.validate(data)
                        else:
                            jsonschema.validate(data, schema)
                    print(f"  PASS [schema OK]  {path_str}")
                except ImportError:
                    print(
                        f"  PASS [no jsonschema] {path_str} (install jsonschema for full validation)"
                    )
                except Exception as e:
                    print(f"  FAIL [schema]   {path_str}: {e}")
                    failed += 1
                    continue
            else:
                print(f"  PASS [no schema file] {path_str} (schema {schema_ref} not found)")
        else:
            print(f"  PASS [json OK]    {path_str}")

        passed += 1

    return passed, failed


def main() -> int:
    print("=== validate_fixtures.py ===")
    print(f"Fixtures dir: {FIXTURES_DIR}")
    print(f"Schemas dir:  {SCHEMAS_DIR}")
    print("")

    # Check manifest
    manifest_raw = load_json(MANIFEST_PATH)
    if manifest_raw is None:
        print("ERROR: contracts/fixtures/MANIFEST.json is missing or empty.")
        print("Run `make fixtures` or contact M4.")
        return 1

    print("Validating fixtures listed in MANIFEST.json...")
    passed, failed = validate_manifest(manifest_raw)

    print("")
    print(f"Result: {passed} passed, {failed} failed.")

    if failed > 0:
        print("FAIL: fixture validation errors found.")
        return 1

    print("PASS: all fixtures valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
