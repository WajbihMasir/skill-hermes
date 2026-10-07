---
name: agent-handoff-specs
description: "Use when another agent builds against your backend."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [handoff, spec, golden-prompt, frontend, api-contract, integration, delegation]
    related_skills: [fastapi-api-hardening, mock-to-live-integration, backend-api-testing, subagent-driven-development]
---

# Agent Handoff Specs ("Golden Prompt")

Write the contract that lets a DIFFERENT agent (or team) build a component
against a system you own — usually the frontend against a finished backend —
with no repo access, no ability to run the service, and no follow-up questions.
The build happens elsewhere; the result comes back to you for integration. This
is phase one of a two-phase loop: write the spec so the later integration
session can verify against the same criteria and the same accounts.

## When to use

- The user wants an external AI agent / another team to build a component
  against your backend and will paste a prompt to it ("buatin golden prompt").
- You need the receiver to work without hallucinating: every endpoint, field,
  enum, and constraint must be derivable from the document alone.

Not for: contracts between Hermes subagents you deploy yourself
(`subagent-driven-development`), making an existing frontend real
(`mock-to-live-integration`), hardening the backend itself
(`fastapi-api-hardening`).

## Procedure

1. **Extract the contract from code — never from memory.** Run
   `scripts/dump_contract.py <module:attr> --json openapi.json` from the backend
   root. It prints every endpoint with parameter LOCATION (path/query/body),
   required flags, defaults, request bodies and response models, plus every
   schema with required-field markers, and writes the raw OpenAPI file to
   attach. Cross-check anything surprising against the router source — a field
   that is query in one route and body in another is exactly what the receiver
   would guess wrong.

2. **Walk the flagship demo scenario against the extracted contract BEFORE
   writing it down as acceptance criteria.** Step by step: URL, actor, and the
   permission the actor needs. Every step that cannot be expressed is a defect —
   in the backend, the seed data, or your draft — and it is cheaper to fix now
   than to explain after the build. Writing the spec is itself a verification
   pass; the receiving agent cannot fix your backend.

3. **Write the spec with these sections** (the order that worked):
   role & mission (what is being built, what already exists, language) →
   non-negotiable technical rules (stack, dev port, request conventions) →
   auth & session semantics → error contract + required UI behavior per code →
   domain invariants the UI must respect → full endpoint reference (method,
   path, permission, request, response, param location) → screen/route map with
   per-screen notes and explicit empty states → deliverables & quality rules →
   numbered acceptance criteria with seeded accounts → appendix for the human
   (exact commands to run the backend).

   Write prose in the user's language (they forward the document); keep
   identifiers, paths, field names, and error codes verbatim.

4. **Attach the machine-readable spec and forbid invention.** State: "only use
   endpoints in the attached spec; if something seems missing, stop and report
   rather than invent." The raw `openapi.json` is what the later integration
   session diffs real requests against. Deliver the contract as ONE
   self-contained document — sections that exist only as chat turns get lost
   when the prompt is pasted piecemeal, and the receiver will report them
   missing. When that happens, ship the missing sections as a standalone
   attachment and open it with a precedence line ("this document wins over your
   memory/context"), restating the answers already given in chat so the
   attachment supersedes rather than contradicts them.

5. **Ship an idempotent seed script with fixed credentials** (upsert by email,
   re-assign the role) so the builder, the smoke test, and the later integration
   session share one account source. Acceptance criteria without runnable
   accounts are decoration.

6. **State hard constraints as MUST / MUST NOT**: do not modify the backend, do
   not invent endpoints, do not fabricate data; if the backend cannot run, any
   mock is opt-in and documented.

## What OpenAPI cannot express — put each in prose

These are the integration breakers; none of them are visible in the schema.

- **Token transport and session semantics.** HttpOnly cookies: every request
  needs `credentials: 'include'`; the token is unreadable from JS; never store
  it in localStorage; auth state comes from `GET /me`, not from decoding the
  token. Silent refresh: on 401 call refresh ONCE, retry the original request,
  then redirect to login.
- **Exact dev origin.** CORS allowlist and cookie SameSite both key off the
  exact origin string — `localhost:5173`, not `127.0.0.1:5173` (different sites
  for cookies). State the allowed origins verbatim.
- **Cookie path scoping.** A `Set-Cookie` `path` attribute must be a prefix of
  the route that sets it, or a BROWSER silently never sends the cookie back —
  while curl and scripted clients (which set cookies manually) keep working.
  Check every `set_cookie`/`delete_cookie` path against the router's real
  prefix (`/api/v1/auth`, not `/auth/refresh`) before shipping the spec, and
  state the paths so the receiver can verify them.
- **Error envelope and the UI behavior per code.** Domain errors
  `{error, message}` with per-code behavior (SOD_VIOLATION → "you cannot review
  your own submission"; OCC_CONFLICT → reload dialog, never auto-overwrite) vs
  Pydantic 422 `detail: [...]` (map to form fields). The behavior is the part
  codegen cannot invent.
- **Domain invariants.** OCC (`expected_version` = the last version read),
  state machines (enumerate allowed transitions), SoD (hide self-review
  actions), upload constraints (magic bytes, size cap), presigned URL TTL.
- **Param-location quirks.** Enumerate `in:` per parameter; the same logical
  field can be query on one route and body on another.
- **Pagination envelope inconsistency.** `{data,total,page,per_page}` vs
  `{data,total,skip,limit}` vs a bare list — state the shape per endpoint.
- **What does NOT exist.** No user-list endpoint → UUID inputs; write-only
  fields are not echoed; deferred features must be named so the receiver does
  not build them. Telling the receiver what NOT to build matters as much as the
  endpoint list.

## Cloud preview platforms (emergent.sh, v0, bolt-style builders)

The receiver's preview runs in a cloud sandbox that CANNOT reach the
developer's `localhost`, so a real-mode-only spec yields a dead preview and a
build nobody can demo. The spec must be dual-mode:

- **MOCK is the default** — the preview is a full working demo with no backend;
  REAL is one env var (`VITE_API_MODE=real`) for the local integration run. The
  mode lives in the API adapter only; components must not know which is active.
- **Forbid the platform's default scaffold in writing.** These builders default
  to generating a backend + database; state frontend-only as a hard MUST NOT, or
  the export comes back full-stack and unusable against yours.
- **Split acceptance criteria**: one list runnable in the preview (mock) and a
  second for the local run (real). The preview list is what the user demos.
- **Spec a Demo Controls panel** (mock only): simulate OCC 409, SoD 403, slow
  network, force the empty state, reset data — security behaviors become
  demonstrable without attacking the real backend.
- **Mock persistence**: localStorage under a versioned key, mock-only, never
  tokens; real mode stores nothing.

Recipe (architecture, mock seed spec, follow-up ladder):
`references/cloud-preview-handoff.md`.

## Answering the receiver's clarifying questions

The receiver stops building and asks; treat the question set as an audit of
both the spec and the backend.

1. **Verify every claim against the source before answering.** Questions arrive
   as confident assertions about your system, and some are wrong (a receiver
   assumed an empty readiness category reads 0%; it reads 100%). Check each
   against the code and answer with what the code does, not what it should do.
2. **Every question the spec could not answer is a defect — fix it now.** The
   unanswerables are exactly the prose the spec was missing (who sets `pic_id`;
   can a PUBLISHED record still be edited; does the review action update the
   parent aggregate). Where the answer exposes a real bug, fix the backend
   before replying.
3. **Some answers are contract changes, not explanations — make them and sync
   everything.** When a question exposes that the response schema cannot
   express a distinction the consumer needs, add the explicit field rather than
   explaining the rule in prose. The recurring case: a computed metric that
   defaults to a perfect score for empty input (100% readiness when nothing is
   defined) is indistinguishable from a genuinely perfect one — add a `has_*`
   boolean so the UI can render "nothing defined" instead of a misleading
   all-green state. After any schema addition: regenerate `openapi.json`, update
   every copy of the contract (main spec AND attachment docs), and extend the
   tests that assert the field. An answer that lives only in the chat is a
   defect for the next reader.
4. **State the backend's loosenesses and dead values explicitly** so the mock
   replicates ACTUAL behavior, not idealized behavior: checks the backend does
   NOT enforce (assignee ownership, upload preconditions), enum values no code
   path ever assigns, fields never populated, which timezone "today" means. A
   mock stricter than the backend teaches wrong behavior and makes the
   integration session chase phantom bugs.
5. **Close the loop with "decisions are final, proceed."** Number the answers
   to match the questions and end with an explicit go-ahead so the receiver
   stops asking.
6. **Deliver a paste-ready reply.** Write the answers addressed to the receiver
   in the language the receiver used, then a short summary for the user in
   theirs — the user forwards the reply verbatim and keeps the summary.

## Pitfalls

- **A spec written from memory hallucinates field names and param locations.**
  Derive everything from the dump; the receiver has no reality to check
  against.
- **Fix backend bugs the spec-writing — and the receiver's questions — expose
  before shipping.** Expect the demo walkthrough to surface real defects — a
  role missing a permission its journey needs, a smoke script calling a route
  that no longer exists, a cookie path that breaks in a browser while curl
  works — and expect the receiver's clarifying questions to surface more (an
  aggregate whose source field nothing writes; an acceptance step whose
  precondition the seed has already passed). Fix them now; the receiving agent
  cannot.
- **Endpoints alone under-specify the integration.** Cookie/CORS/refresh
  semantics are invisible in the schema and are the top cause of "the UI is
  built but nothing works".
- **Give the auth matrix (role → permissions) and test accounts with
  passwords.** Without accounts the acceptance criteria are unrunnable and the
  receiver guesses roles.
- **Mark what is out of scope for this version.** A receiver that does not know
  a feature is deferred will build an invented version of it.

## Files

- `scripts/dump_contract.py` — extract endpoints + schemas from a FastAPI app
  (`python scripts/dump_contract.py app.main:app --json openapi.json`).
- `references/cloud-preview-handoff.md` — dual-mode (mock-default) recipe for
  cloud preview builders: adapter architecture, mock seed spec, demo controls,
  follow-up ladder, acceptance split.
