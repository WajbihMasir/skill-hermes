# HITL Approval Workflow Integration

## Pattern

When an MCP tool creates a draft that requires human approval, the existing FastAPI approval workflow remains authoritative. The MCP tool must NOT:
- Approve or reject orders
- Deduct stock
- Send customer messages
- Modify inventory

## Verified Workflow

1. **Agent creates draft** via `create_order_draft` MCP tool → INSERT order with `status=pending_approval` + audit log entry (`actor=agent, action=create_draft`)
2. **Human approves** via existing `POST /api/v1/orders/{order_id}/approve` endpoint
3. **Existing workflow handles:**
   - Stock validation (typed failure if insufficient)
   - LLM-drafted customer reply (with template fallback)
   - Atomic status transition (`_claim_pending()` — `UPDATE ... WHERE status='pending_approval'`)
   - Atomic stock deduction (`UPDATE inventory SET stock = stock - ? WHERE stock >= ?`)
   - Audit log entries (3 entries: human approve, agent deduct stock, agent notify customer)
   - Mocked outbound reply (fire-and-log)

## Idempotency

The `_claim_pending()` function uses atomic `UPDATE orders SET status = ? WHERE id = ? AND status = 'pending_approval'`. If a second approval is attempted, `cur.rowcount == 0` → returns `ORDER_NOT_PENDING` typed failure. This prevents double stock deduction.

## Audit Trail

| # | Actor | Action | Before | After |
|---|---|---|---|---|
| 1 | `agent` | `create_draft` | `""` | `pending_approval` |
| 2 | `human` | `APPROVE_ORDER` | `pending_approval` | `approved` |
| 3 | `agent` | `DEDUCT_STOCK` | `reserved` | `deducted` |
| 4 | `agent` | `NOTIFY_CUSTOMER` | `llm:agnes-2.5-flash` | `sent` |

## Security Boundary

- Agent can create draft: YES
- Agent can approve: NO (no MCP tool for this)
- Agent can deduct stock directly: NO (no MCP tool for this)
- Agent can send customer message directly: NO (no MCP tool for this)

## Environment Variables for LLM-Drafted Replies

The approval endpoint calls `_draft_reply()` which requires:
- `BYNARA_API_KEY` — API key for LLM provider
- `BYNARA_BASE_URL` — Base URL (e.g., `https://router.bynara.id/v1`)
- `LLM_PRIMARY_MODEL` — Primary model name
- `LLM_FALLBACK_MODEL` — Fallback model name

Without these, `load_llm_config()` raises `KeyError` and the approval endpoint returns 500.
