---
name: mcp-tool-integration
description: Adding MCP tools to Hermes agents for FastAPI backends.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [mcp, fastmcp, hermes, tools, integration]
    related_skills: [hermes-agent]
---

# MCP Tool Integration with Hermes

## When to Use

Use this skill when:
- Adding MCP tools to a Hermes agent for a FastAPI+SQLite backend
- Configuring FastMCP server with Hermes toolset integration
- Debugging why MCP tools don't appear in the agent registry
- Setting up read-only or write tools with proper audit trails

## Procedure

1. **Use FastMCP, not raw MCP SDK.** The MCP SDK v2.2.0 has API incompatibilities with standard `call_tool` patterns. FastMCP provides a decorator-based API that works correctly.

2. **Register tools under the correct toolset name.** MCP tools are registered under `mcp-{server_name}` (e.g., `mcp-tuntasumkm`), NOT the raw server name. This is a common source of confusion.

3. **Add the toolset to `platform_toolsets.cli`.** In `config.yaml`, add `mcp-{server_name}` to the `platform_toolsets.cli` list. Without this, MCP tools won't appear in the agent registry.

4. **Set `tools.include` for least-privilege.** In `config.yaml`, under `mcp_servers.{server_name}.tools`, set `include` to the list of approved tools. Do NOT use `exclude` — `hermes tools enable` only manipulates the exclude list.

5. **Verify with `--verbose`.** The LLM's self-report of available tools is unreliable. Use `hermes chat -q "test" --verbose 2>&1 | grep "mcp__"` to verify MCP tools are actually in the agent registry.

6. **Test MCP server health separately.** `hermes mcp test {server}` confirms the server is running and tools are discoverable, but does NOT prove they're in the agent registry.

## Pitfalls

- **`hermes tools enable` does NOT write `tools.include`.** It only manipulates `tools.exclude`. If you need an include list, you must edit `config.yaml` directly.
- **LLM self-report of tools is unreliable.** The model may omit MCP tools from its response even when they're registered. Always verify with `--verbose`.
- **Toolset name mismatch causes silent failure.** If `_merge_mcp_servers()` returns the raw server name but the toolset is registered as `mcp-{server_name}`, `resolve_toolset()` fails silently and no MCP tools appear.
- **Read-only tools must not mutate state.** Tools like `search_catalog`, `check_inventory`, and `calculate_order_total` must only perform SELECT queries. Write tools like `create_order_draft` must use `pending_approval` status and create audit log entries.
- **Use the existing database schema.** Do not create a second database or schema. Use the existing tables and columns.
- **Audit log entries require `actor` field.** Use `actor: "agent"` for MCP tool actions to distinguish from human actions.
- **Order IDs must be unique.** Use a combination of date and UUID to generate order IDs that won't conflict with existing records.
- **MCP tools cannot be batched in `tool_call`.** Only connector tools may be batched together. Attempting to batch two MCP tools in one `tool_call` invocation returns an error — issue them as separate calls.
- **Approval endpoints may depend on LLM env vars.** If the existing FastAPI approval workflow calls `_draft_reply()` → `draft_customer_reply()` → `chat_completion()` → `load_llm_config()`, it will crash with `KeyError` if `BYNARA_BASE_URL` is not set. Set `BYNARA_BASE_URL`, `LLM_PRIMARY_MODEL`, and `LLM_FALLBACK_MODEL` env vars before starting the server.
- **`--verbose` mode exposes partial API keys in terminal output.** The verbose log line `🔑 Using API key: sk-a5a87...ece7` displays a truncated but recognizable key prefix. During demo recording, use default output mode (no `--verbose`) to avoid exposing credentials on screen. If verbose is needed for debugging, record the terminal separately and edit out key lines before publishing.
- **Agent may attempt to batch MCP tools and fail.** The LLM sometimes tries to call two MCP tools in one `tool_call` invocation. Hermes rejects this with `tool_call takes exactly one entry for local tools; you sent 2`. The agent then retries with separate calls. This adds ~5 seconds to the demo but is expected behavior — not a bug. Do not "fix" it by changing the tool architecture.
- **Frontend must never infer actor from action name.** The backend `audit_logs.actor` field is the sole source of truth for who performed an action. A frontend that guesses actor based on action name (e.g., mapping `DEDUCT_STOCK` → `SYSTEM`) will misrepresent the boundary between agent and human. Always use `entry.actor` directly. The backend may store all post-approval actions (DEDUCT_STOCK, NOTIFY_CUSTOMER) with `actor="agent"` — the UI must reflect this faithfully, not invent a `SYSTEM` category that doesn't exist in the data.