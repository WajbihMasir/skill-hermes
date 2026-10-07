# Demo Recording Layout

## Recommended Window Arrangement

For hackathon demos showing the full agent→MCP→HITL→audit flow:

```
┌─────────────────────────────────────────────────────────┐
│  Browser Dashboard (left 50%)                           │
│  - Approval queue                                       │
│  - Order detail                                         │
│  - Audit trail                                          │
│  - Stock panel                                          │
├─────────────────────────────────────────────────────────┤
│  Hermes Terminal (right 50%)                            │
│  - Agent tool calls (default mode, NOT --verbose)       │
│  - Tool results                                         │
│  - Final response                                       │
└─────────────────────────────────────────────────────────┘
```

## Secret Exposure Rules

**MUST NOT appear in recording:**
- API keys (even truncated prefixes like `sk-a5a87...`)
- `.env` file contents
- Provider credentials
- Authentication cookies
- `BYNARA_API_KEY`, `BYNARA_BASE_URL`, or any secret env vars

**Safe to record:**
- Browser dashboard (no secrets)
- MCP tool names and arguments
- Order IDs, product names, stock levels
- Audit trail entries
- Agent reasoning text

**Rule:** Do NOT use `--verbose` flag during recording. Verbose mode displays partial API keys in terminal output.

## Demo Flow Timing

| Phase | Duration | What to show |
|---|---|---|
| User intent | 2s | Type the order request |
| Agent tool calls | 15-30s | search_catalog → check_inventory → calculate_order_total → create_order_draft |
| Dashboard HITL | 5s | Order appears in approval queue |
| Human approval | 5s | Click Approve → Confirm |
| Result | 5s | Stock deduction, audit trail update |

Total: ~30-50 seconds for the full Golden Path.

## Golden Path Script

1. **Scene 1 — Intent:** User types "Saya mau pesan [Product] [N] pcs"
2. **Scene 2 — Agent:** Hermes visibly invokes search_catalog
3. **Scene 3:** Hermes invokes check_inventory
4. **Scene 4:** Hermes invokes calculate_order_total
5. **Scene 5:** Hermes invokes create_order_draft
6. **Scene 6 — HITL:** Dashboard displays MENUNGGU APPROVAL
7. **Scene 7:** Human clicks Approve
8. **Scene 8:** Confirmation dialog appears
9. **Scene 9:** Human clicks Confirm Approval
10. **Scene 10:** Show approved status
11. **Scene 11:** Show stock X → X-N
12. **Scene 12:** Show Audit Trail with AGENT → HUMAN → AGENT → AGENT
