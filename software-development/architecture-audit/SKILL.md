---
name: architecture-audit
description: "Architecture audit: trace, design, propose, no code changes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, audit, feasibility, design, hackathon, planning, review]
    related_skills: [spike, codebase-inspection]
---

# Architecture Audit

Use this skill when the user wants a **comprehensive architecture audit** — tracing execution flow, identifying gaps, proposing minimal changes, and defining boundaries — WITHOUT modifying any source code.

Load this when the user says things like:
- "audit this repository"
- "trace actual execution flow"
- "identify the current agent gap"
- "design the minimum viable architecture"
- "determine how X can be changed into Y WITHOUT rewrite"
- "feasibility audit for integrating X with Y"
- "event trigger & lifecycle audit"

## When to Use

Use this skill when the user wants a **comprehensive architecture audit** — tracing execution flow, identifying gaps, proposing minimal changes, and defining boundaries — WITHOUT modifying any source code.

Load this when the user says things like:
- "audit this repository"
- "trace actual execution flow"
- "identify the current agent gap"
- "design the minimum viable architecture"
- "determine how X can be changed into Y WITHOUT rewrite"
- "feasibility audit for integrating X with Y"
- "event trigger & lifecycle audit"

## When NOT to Use

- The user wants implementation — use `spike` or `test-driven-development` instead
- The answer is knowable from docs alone — just read the docs
- The work is a quick code review — use `requesting-code-review` instead

## Core principle

**Read source code directly** — never rely on README or docs alone. The user explicitly says: "Jangan hanya membaca README. Trace actual execution flow."

**Do NOT modify any files.** The user says: "JANGAN implementasikan apa pun." This is a read-only audit.

## Workflow

### Phase 1: Understand the Existing System

1. **Read every file in the execution path** — not just the main entry point
2. **Document the current architecture** with real function names, file paths, line numbers
3. **Trace the actual flow** — from input to output, through every function call
4. **Identify what each component does** — LLM vs deterministic, read-only vs write

### Phase 2: Identify the Gap

1. **What does the current system do?** — enumerate capabilities
2. **What is missing?** — what the new system needs
3. **Where can new capabilities be inserted?** — without breaking existing flow
4. **What should remain deterministic?** — don't move everything to the agent

### Phase 3: Design the Minimum

1. **Propose the smallest change** that achieves the goal
2. **Preserve what works** — explicitly list what must NOT change
3. **Define boundaries** — what the new system can/cannot do (enforced in code, not prompts)
4. **Propose contracts** — exact input/output schemas for new components
5. **List files** — NEW, MODIFIED, UNCHANGED with reasons

### Phase 4: Assess Risks

1. **What can break?** — with concrete mitigations
2. **What is the latency?** — account for process startup, not just LLM calls
3. **What is the fallback?** — if the new system fails
4. **What is the demo path?** — for hackathon context, 60-90 seconds max

## Output structure (user expects)

```
# <PROJECT> <AUDIT_TYPE>

1. Current Architecture
2. Current Capabilities
3. Gap Analysis
4. Proposed Architecture
5. Proposed Tool/Component Set
6. Agent Loop / Event Flow
7. Safety / Boundary
8. Reliability & Fallback Strategy
9. Minimal Change Plan
10. Files That Need Modification
11. Files That Should NOT Be Modified
12. Demo Impact (if hackathon)
13. Risks
14. Implementation Order
15. Final Recommendation
16. Before → After Architecture

# IMPLEMENTATION CHECKLIST
P0 / P1 / P2 / P3
```

## Pitfalls

- NEVER propose changes that break existing tests — the user's first constraint is "TANPA merusak fitur yang sudah bekerja"
- NEVER invent API endpoints that don't exist — verify from installed source/docs
- When comparing integration options, provide evidence from source code, not assumptions
- Mark NEW vs EXISTING fields explicitly in data contracts
- For hackathon context: always include demo path (60-90 seconds max for core flow)
- Latency claims must account for process startup overhead, not just LLM call time
- When the user says "DO NOT IMPLEMENT" — respect it. No code, no file creation, no dependency installation
- For multi-phase audits: each phase builds on the previous. Don't skip phases.
- When tracing execution: follow the actual code path, not the intended design
- When implementing UI that displays backend data, always verify actual backend values from the database/API — never infer or fabricate categories from action names or source code patterns. A frontend that guesses "SYSTEM" actor based on action name when backend only has "agent" and "human" is a truthfulness bug that misleads users about system boundaries
- When auditing MCP-based agent systems: MCP tool filtering is NOT a security boundary. Agent frameworks typically expose non-MCP tools (execute_code, terminal, browser, file access) that can bypass MCP restrictions. Always audit the FULL agent capability surface, not just MCP tools
- Distinguish state-transition enforcement from identity-based authorization. If an endpoint checks status but has no authentication, it enforces state transitions — it does NOT authorize identities. Calling it "authorization boundary" is misleading
- When audit logs record actor="agent" for side effects (stock deduction, notification), clarify whether this is logical origin (workflow attribution) or physical executor (who actually ran the SQL). Backend executing side effects after human approval should not be labeled as "agent executed" without clarification
- For demo/hackathon claims: absolute statements like "agent cannot bypass" are dangerous. Use defensible language: "MCP only exposes N tools" + "backend enforces state transitions" + "known limitation: agent has execute_code/terminal"
- When creating demo materials (script + PPT), verify synchronization with pptx_read.py --outline: layer numbering, stock numbers, tool lists, and filenames must match between script and slides

## Integration options comparison

When comparing integration options (e.g., how to invoke an agent framework), always provide:

| Option | Can it work? | Mechanism | Input | Output | Latency | Reliability | Complexity | Demo fit |
|--------|-------------|-----------|-------|--------|---------|-------------|------------|-----------|

And verify each option from installed source code — don't assume APIs exist.

## GO / NO-GO verdict

End every audit with a clear GO or NO-GO recommendation, with technical reasoning.

## Platform readiness assessment ("berapa persen cocok?")

When the audit is "how compatible is this project with platform X, and what must
be built to reach 100%", follow `references/platform-readiness-assessment.md`.
Core rules, in short:

- **Research the platform first, from primary sources**, and record which claims
  are primary vs secondary. Score the economics and the penalties, the mandatory
  requirements (especially anything with a date), the target's data model, the
  API auth scheme, the automation policy, and what gets accounts banned.
- **Score with a weighted table and show the raw table.** State that the weights
  are your choice and the reader can re-weight. Every sub-score needs stated
  evidence. Weight by what determines success, not by what is easy to build.
- **If two questions are being asked, give both numbers.** "Can this operate on
  the platform" and "is this useful to an operator today" are different answers.
- **Group gaps by what they block** (blocking / protective / quality / breadth),
  then show the **projected score after each phase** so the roadmap shows leverage.
- **Build the brakes before the accelerator.** When the platform penalises bad
  output, the pre-flight refusal and the quality/attestation gate are the
  highest-value components — never sequence a submission path before its gate.
- **End with an honest-limits section**: rules change and dated claims must be
  re-verified, the scorecard is judgement not measurement, detection is not
  acceptance, and capability claims were verified against a simple local target.
