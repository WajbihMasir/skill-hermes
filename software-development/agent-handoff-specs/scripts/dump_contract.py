"""
Dump a FastAPI app's contract in compact, spec-writing form.

Usage (run from the backend root so imports resolve):
    python dump_contract.py app.main:app
    python dump_contract.py app.main:app --json openapi.json
    python dump_contract.py app.main:app --schemas-only

Prints every endpoint with parameter LOCATION (path/query/body), required
flags, defaults, request-body model and response models, then every schema as
'name: field:type!, ...' ('!' = required). Feed the output into the handoff
spec; never transcribe field names from memory.
"""
from __future__ import annotations

import importlib
import json
import sys


def load_app(ref: str):
    """'pkg.module:attr' -> FastAPI instance (attr defaults to 'app')."""
    mod_name, _, attr = ref.partition(":")
    mod = importlib.import_module(mod_name or "app.main")
    return getattr(mod, attr or "app")


def type_of(schema: dict) -> str:
    if not schema:
        return "?"
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "enum" in schema:
        return "|".join(str(v) for v in schema["enum"])
    if schema.get("type") == "array":
        return f"[{type_of(schema.get('items', {}))}]"
    if "anyOf" in schema:
        return "|".join(type_of(x) for x in schema["anyOf"])
    return schema.get("type", "?")


def dump_endpoints(spec: dict) -> None:
    print("===== ENDPOINTS =====")
    for path, ops in sorted(spec.get("paths", {}).items()):
        for method, op in sorted(ops.items()):
            print(f"\n{method.upper()} {path}  |  {op.get('summary', '')}")
            for p in op.get("parameters", []):
                s = p.get("schema") or {}
                bits = [f"in={p['in']}", f"type={type_of(s)}"]
                if p.get("required"):
                    bits.append("REQUIRED")
                if "default" in s:
                    bits.append(f"default={s['default']}")
                print(f"    param {p['name']}: {', '.join(bits)}")
            rb = op.get("requestBody")
            if rb:
                for ct, c in rb.get("content", {}).items():
                    print(f"    body({ct}): {type_of(c.get('schema') or {})}")
            for code, r in sorted(op.get("responses", {}).items()):
                for ct, c in (r.get("content") or {}).items():
                    print(f"    resp {code}: {type_of(c.get('schema') or {})}")


def dump_schemas(spec: dict) -> None:
    print("\n===== SCHEMAS =====")
    for name, s in sorted(spec.get("components", {}).get("schemas", {}).items()):
        if "enum" in s:
            print(f"{name}: ENUM {' | '.join(map(str, s['enum']))}")
            continue
        required = set(s.get("required", []))
        fields = [
            f"{fn}:{type_of(f)}{'!' if fn in required else ''}"
            for fn, f in s.get("properties", {}).items()
        ]
        print(f"{name}: {', '.join(fields)}")


def main() -> None:
    args = sys.argv[1:]
    out_json = None
    if "--json" in args:
        i = args.index("--json")
        out_json = args[i + 1]
        del args[i:i + 2]
    schemas_only = "--schemas-only" in args
    args = [a for a in args if a != "--schemas-only"]
    ref = args[0] if args else "app.main:app"

    app = load_app(ref)
    spec = app.openapi()

    if out_json:
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(spec, fh, indent=2)
        print(
            f"openapi.json -> {out_json} "
            f"({len(spec.get('paths', {}))} paths, "
            f"{len(spec.get('components', {}).get('schemas', {}))} schemas)"
        )
    if not schemas_only:
        dump_endpoints(spec)
    dump_schemas(spec)


if __name__ == "__main__":
    main()
