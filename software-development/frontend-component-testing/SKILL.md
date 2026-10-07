---
name: frontend-component-testing
description: "Use when adding Jest/RTL tests to a JS/TS frontend."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, react, testing, jest, rtl, vitest, jsdom]
    related_skills: [test-driven-development, dogfood, backend-api-testing]
---

# Frontend Component Testing (Jest + React Testing Library)

## When to Use

- Adding unit/component tests to a JS/TS frontend (React on CRA/craco/Vite).
- A test run fails to even start: peer-dep `ERESOLVE`, an unresolved `@/` alias,
  or a thrown `TypeError` from a `useEffect` (jsdom missing a browser API).
- You need to assert a component's interaction/state contract without a browser.

Not for: real-browser layout/console/keyboard verification (use `dogfood`),
backend API tests (use `backend-api-testing`), or test-first discipline itself
(use `test-driven-development`).

## Overview

Standing up and writing component / interaction tests for a JS/TS frontend.
Covers the plumbing that is easy to get wrong (peer-dep resolution, path-alias
mapping, jsdom gaps) so the tests actually run, plus the patterns that keep
component tests honest. Pair with `test-driven-development` for the RED-GREEN
cycle; this skill is the *how* for React on CRA/craco/Vite.

## Step 0 — Match the test library to the React version (the #1 setup failure)

Read the installed React version BEFORE choosing `@testing-library/react`:

```bash
node -e "console.log(require('react/package.json').version)"
```

- React 18 → `@testing-library/react@14`
- React 19 → `@testing-library/react@16`

Installing the wrong major fails with a peer error like
`peer react@"^18.0.0"` even though the real blocker is your React version, not
the package. Install the compatible set together:

```bash
npm install --save-dev @testing-library/react@16 @testing-library/dom@10 \
  @testing-library/jest-dom@6 @testing-library/user-event@14
```

If the project has a **pre-existing** peer conflict (a stray `react-day-picker`
/ `date-fns` mismatch is common), the install aborts with `ERESOLVE`. Retry with
`--legacy-peer-deps` — that accepts the existing conflict instead of failing on
it. Do NOT hand-edit `package.json` or `--force`.

## Step 1 — Wire the runner (CRA / craco)

CRA auto-loads `src/setupTests.ts` before every test — put the jest-dom import
there:

```ts
// src/setupTests.ts
import "@testing-library/jest-dom";
```

Path aliases (`@/...`) are a webpack-only concern until you also map them for
jest. In `craco.config.js` add a `jest.configure` block:

```js
jest: {
  configure: {
    moduleNameMapper: { "^@/(.*)$": "<rootDir>/src/$1" },
    setupFiles: ["<rootDir>/src/test/polyfills.js"],
  },
},
```

Run with `CI=true npm test -- --watchAll=false` (CI=true stops watch mode from
hanging a non-interactive shell). Vite/Vitest: set `test.environment: 'jsdom'`,
`test.setupFiles`, and `resolve.alias` in `vite.config.ts` instead.

### Env-file precedence: the test env file loses to the build env file

`dotenv` **never overrides a value already in `process.env`**, so the first file
loaded wins — not the most specific one. A tool config that eagerly calls
`require("dotenv").config()` (common in `craco.config.js`, `jest.config.js`,
vite plugins) loads `.env` before react-scripts/vite ever looks at `.env.test`,
so the test run silently inherits production settings.

Symptom: unit tests start hitting the network / rendering live-mode states even
though `.env.test` sets the mock flag. Verify with a throwaway probe rather than
reading the configs:

```ts
test("env probe", () => {
  console.log("FLAG =", process.env.REACT_APP_USE_MOCK);
  console.log("resolved =", require("@/lib/config").USE_MOCK);
});
```

Fix: gate the eager load on `NODE_ENV !== "test"` so the test runner's own
env-file resolution happens first:

```js
const nodeEnv = process.env.NODE_ENV || "development";
if (nodeEnv !== "test") require("dotenv").config();
```

Keep the intent explicit in the env files themselves (`.env` = live,
`.env.test` = mock) so the split is self-documenting. Delete the probe test once
confirmed — a permanent `console.log` test is noise.

## Step 2 — Polyfill the jsdom gaps (a file, not per-test mocks)

jsdom has no layout engine and lacks several browser APIs that component
libraries touch on mount. Put the stubs in ONE `src/test/polyfills.js` loaded via
`setupFiles`, not repeated in every test:

- `window.matchMedia` (Radix / theme helpers)
- `ResizeObserver` and `IntersectionObserver` (Recharts `ResponsiveContainer`)
- `Element.prototype.scrollIntoView` (autoscroll logs/timelines — jsdom throws
  `scrollIntoView is not a function`)
- `window.scrollTo` (silences "Not implemented" noise)
- `EventSource` (any SSE/streaming client that mounts a connection)

A missing polyfill surfaces as a thrown `TypeError` inside a `useEffect` during
render — that is a **test-environment gap, not an app bug**; fix it in the
polyfills file, never by weakening the component.

## Step 3 — Render pages inside their providers

Pages that call `useContext` must be wrapped. Add a helper so every test renders
the same way:

```tsx
// src/test/helpers.tsx
export function renderWithProviders(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}
```

For a global-keyboard component, render it inside the provider in the test
harness (not just in `App.tsx`) so its `window` listener is actually mounted —
a shortcut implemented in `App.tsx` alone is untestable in isolation.

## Step 4 — Assert on the element, not a substring

- A bare `body.innerText.includes("X")` false-positives when X appears in a
  tooltip, hint, or hidden row. Target the element: `getByTestId`, `getByRole`,
  `getByText(...)` with `{ exact: true }`.
- For a `<textarea>` or `<input>`, read `.value` (or RTL's
  `(el as HTMLInputElement).value`) — `textContent` / `innerText` is `""` for form
  fields, so a substring check silently fails on working code.
- jsdom has no layout, so you cannot assert pixel widths. Assert the **class
  contract** that drives the CSS instead (`expect(el.className).toContain("md:w-16")`)
  and leave true geometry to a real browser (see `dogfood` / Playwright probes).

## Pitfall — renaming a `data-testid` breaks every caller; grep before you widen

A testid is an interface. When a UI change reassigns or renames one (e.g.
repurposing `sidebar-toggle` from a mobile hamburger to a desktop collapse
button), every unit test AND every external script that referenced the old id
must be updated in the same change. Grep the WHOLE repo, not just the test tree:

```bash
search_files(pattern="old-testid", path=".")
```

A stale browser probe does not fail fast — clicking a now-hidden element blocks
until its click timeout and can **hang the entire run**. Fix each caller and
re-run each script; do not assume only the unit tests referenced it.

## Anti-patterns

- **One `jest.mock` per test file for a shared API module** — centralize the mock
  in a setup file or the mock factory, or every file drifts.
- **Asserting implementation details** (state values, internal method calls)
  instead of rendered output and user-visible behavior.
- **Testing the provider instead of the page** — render the page inside the real
  provider so context wiring is exercised.
- **Timer leaks from simulation animations** — `jest.useRealTimers()` in
  `afterEach`, and clear any `setTimeout` the component scheduled on unmount.

## Related

- `backend-api-testing` — the FastAPI/pytest sibling of this skill.
- `dogfood` — real-browser (Playwright) verification of the built app, where
  pixel-level layout, console errors, and keyboard flows are checked.
