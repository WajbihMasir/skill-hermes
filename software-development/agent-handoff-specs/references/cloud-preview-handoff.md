# Cloud Preview Platform Handoff (emergent.sh-style builders)

Context: the receiving platform builds and hosts the app in its own cloud
sandbox. Its preview cannot reach the developer's machine, so a spec that
assumes `localhost:8000` yields a dead preview and a build that cannot be
demoed. The deliverable must work in BOTH worlds from one codebase.

## Stack flexibility (do not fight the scaffold)

- State the preferred stack (React + TS + Vite, dev port 5173) but ALLOW the
  platform's own scaffold — some builders default to CRA on port 3000. Both
  work because CORS and cookie SameSite key off exact origins: put every
  allowed origin in the spec (5173 and 3000) and keep the backend allowlist in
  sync.
- State the consequence: the env prefix differs (`VITE_*` vs `REACT_APP_*`), so
  all env access must funnel through ONE config module — the export then ports
  with a one-file edit.
- Accept Next.js only if pinned to a pure client-side SPA with NO API routes or
  server actions; the platform's default full-stack generation is the exact
  failure mode the frontend-only MUST NOT guards against.

## Dual-mode architecture (state it in the spec)

- `config.ts`: `API_MODE = env("VITE_API_MODE") ?? "mock"`,
  `API_BASE_URL = env("VITE_API_BASE_URL") ?? "http://localhost:8000/api/v1"`.
- One `ApiClient` TypeScript interface; `mock/adapter.ts` and `http/adapter.ts`
  implement it; `adapter.ts` picks by mode. Components import only the
  interface — no component may know the active mode.
- Mock mode: a "MODE DEMO" banner is always visible so demo data is never
  mistaken for real; the Demo Controls panel floats only in mock mode.
- Mock store persists to localStorage under a versioned key
  (`app_mock_store_v1`) so a preview reload does not wipe a mid-demo session;
  the "reset demo data" button clears that key. Never store tokens in any mode.
- Real mode: `credentials: 'include'` on every request; session from `GET /me`;
  silent refresh once on 401; nothing persisted client-side.

## Hard constraints to state verbatim

- Frontend-only: MUST NOT create a backend, database, or server routes; if the
  platform scaffolds one, delete it. (Cloud builders default to full-stack
  generation — without this line the export returns a second backend.)
- The preview must be fully functional with zero network access.
- One env var flips modes; the exported project runs with
  `npm install && npm run dev`.

## Mock seed spec (make the demo alive)

- One demo account per role, password-free login buttons, account id kept in
  sessionStorage (mock only) so a reload stays logged in.
- Dates relative to "today" so the homepage demo never goes stale: one event
  today, one in +3 days, one DRAFT, one COMPLETED yesterday.
- Seed the state needed for every demo beat: an evidence row owned by the
  reviewer account (to demo the SoD 403), pending reviews for the admin, unread
  notifications for the badge, audit rows covering every action type.
- Mirror the REAL backend in the mock: same error envelope, same 409/403/400
  codes, same pagination shapes, and the same loosenesses the backend actually
  has (see SKILL.md → "Answering the receiver's clarifying questions", item 3)
  plus the same "today" timezone semantics.

## Demo Controls (mock only)

Toggles: force OCC conflict on next mutation (bump a hidden version), force SoD
violation on next verify, slow network, force the homepage empty state, reset
data, and a list of demo account UUIDs so UUID-input forms are usable.

## Follow-up ladder

Ship the build in one prompt, then polish with short numbered follow-ups (F1…
Fn), one page or feature each: public homepage → OCC UX → compliance & review →
notifications → admin → dashboards → QA + docs. One concern per message keeps
the platform from rewriting working pages.

## Acceptance split

- Preview (mock) list: every screen reachable, every demo beat works, empty
  states correct.
- Local (real) list: the same beats against the live backend, plus silent
  refresh works, no out-of-contract endpoints, no console errors.
- The integration session (`mock-to-live-integration`) replays the LOCAL list
  with the seeded accounts after flipping the mode flag.
