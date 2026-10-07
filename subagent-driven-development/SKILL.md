---
name: subagent-driven-development
description: "Deploy sub-agents in parallel for independent modules."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [delegation, subagent, parallel, implementation, interface-contracts]
    related_skills: [test-driven-development, simplify-code]
---

# Subagent-Driven Development

Deploy multiple sub-agents in parallel to implement independent modules, each with a detailed interface contract that specifies exact function signatures, type hints, and error handling.

**Core principle:** Parallel implementation works when modules are truly independent and contracts are precise. Ambiguity in specs causes integration bugs that cost more than the parallelism saves.

## When to Use

Trigger this skill when:

- User says "deploy sub-agents" / "parallel implementation" / "implement in parallel"
- Multiple independent modules need implementation
- User provides or asks for detailed interface contracts
- Work can be split into non-overlapping file sets

Do NOT use when:
- Modules have complex interdependencies
- Shared state or race conditions are likely
- The user wants tight integration control

## The Process

### Phase 1 — Define Interface Contracts

Before deploying sub-agents, write a detailed spec for each module:

```markdown
## File: backend/module_name.py

### Classes and Functions:
- `ClassName(param: type) -> return_type`
- `method_name(self, arg: type) -> return_type`

### Error Handling:
- Raises `CustomError` when [condition]
- Returns `None` when [condition]

### Dependencies:
- Imports from `other_module.py`
- Uses `database.py` for persistence

### Test Spec:
- `test_function_name` — tests [behavior]
- `test_error_case` — tests [error condition]
```

**Key elements:**
- Exact function signatures with type hints
- Custom exception classes
- Import dependencies
- Test specifications
- Integration points with other modules

### Phase 2 — Deploy Sub-Agents in Parallel

**Splitting large phases:** When a phase has many modules, split into Part A and Part B for parallel execution. Each part gets a non-overlapping file set. This keeps sub-agent context manageable and reduces integration risk.

Use `delegate_task` with batch mode — pass all tasks in one `tasks` array:

```python
delegate_task(tasks=[
    {
        "goal": "Implement Module A with exact specifications...",
        "context": "Working directory: ...\nPython: ...\nDependencies: ...",
        "output_schema": {
            "properties": {
                "files_created": {"items": {"type": "string"}, "type": "array"},
                "success": {"type": "boolean"},
                "tests_passed": {"type": "integer"},
                "tests_total": {"type": "integer"}
            },
            "required": ["success", "files_created", "tests_passed", "tests_total"],
            "type": "object"
        }
    },
    {
        "goal": "Implement Module B with exact specifications...",
        "context": "...",
        "output_schema": { ... }
    }
])
```

**Critical rules:**
- Each sub-agent gets the COMPLETE spec for its module (not fragments)
- Each sub-agent gets the list of existing modules it can import
- Each sub-agent runs tests and reports results
- Use `output_schema` to enforce structured output
- Each sub-agent creates BOTH implementation and test files — tests verify the implementation
- Use mocks for dependencies in unit tests — keeps tests fast and isolated

### Phase 3 — Verify Integration

After all sub-agents complete:

1. **Run full test suite** — `pytest tests/ -v`
2. **Check for integration bugs** — imports, type mismatches, missing functions
3. **Fix issues manually** — sub-agents can't see each other's work
4. **Update test assertions** — when fixing bugs, assertions may need updating

## Pitfalls

- **Template markers in f-strings** — `{variable}` in code examples within `delegate_task` goals causes "unexpanded template marker" errors. Use string concatenation or escape braces.
- **Sub-agent repetition loops** — sub-agents may enter degenerate repetition loops. Check `files_created` in partial output; files may exist despite failure.
- **Test assertion staleness** — when fixing bugs, test assertions may encode old incorrect behavior. Update assertions to reflect correct behavior.
- **Missing client initialization** — test setups may not initialize all required objects (e.g., `client=None`). Ensure test fixtures create all necessary state.
- **False positive in similarity checks** — key overlap without value matching causes false positives. Check both keys AND values for meaningful comparison.
- **Windows file locking** — `tempfile.TemporaryDirectory()` cleanup may fail with `PermissionError` on Windows if DB connections aren't closed. Always call `db.close()` in test teardown.

## Output Schema

Always use `output_schema` to enforce structured output from sub-agents:

```json
{
  "success": true,
  "files_created": ["path/to/file1.py", "path/to/file2.py"],
  "tests_passed": 13,
  "tests_total": 13
}
```

This allows programmatic verification of sub-agent results.

## Integration with TDD

When combining with test-driven-development:

1. Write interface contracts (Phase 1)
2. Deploy sub-agents with TDD instructions in goal
3. Each sub-agent writes tests first, then implementation
4. Verify integration (Phase 3)

Sub-agents should:
- Write failing test first
- Run test to verify failure
- Write minimal implementation
- Run test to verify pass
- Report results

## Related

- `test-driven-development` — TDD principles and sub-agent TDD instructions
- `simplify-code` — parallel review/cleanup after implementation
- `requesting-code-review` — pre-commit quality gate
