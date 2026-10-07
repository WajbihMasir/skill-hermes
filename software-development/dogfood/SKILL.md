---
name: dogfood
description: "Exploratory QA of web apps: find bugs, evidence, reports."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: []
---

# Dogfood: Systematic Web Application QA Testing

## Overview

This skill guides you through systematic exploratory QA testing of web applications using the browser toolset. You will navigate the application, interact with elements, capture evidence of issues, and produce a structured bug report.

## Prerequisites

- Browser toolset must be available (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`, `browser_back`, `browser_press`)
- A target URL and testing scope from the user

## Inputs

The user provides:
1. **Target URL** — the entry point for testing
2. **Scope** — what areas/features to focus on (or "full site" for comprehensive testing)
3. **Output directory** (optional) — where to save screenshots and the report (default: `./dogfood-output`)

## Workflow

Follow this 5-phase systematic workflow:

### Phase 1: Plan

1. Create the output directory structure:
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
2. Identify the testing scope based on user input.
3. Build a rough sitemap by planning which pages and features to test:
   - Landing/home page
   - Navigation links (header, footer, sidebar)
   - Key user flows (sign up, login, search, checkout, etc.)
   - Forms and interactive elements
   - Edge cases (empty states, error pages, 404s)

### Phase 2: Explore

For each page or feature in your plan:

1. **Navigate** to the page:
   ```
   browser_navigate(url="https://example.com/page")
   ```

2. **Take a snapshot** to understand the DOM structure:
   ```
   browser_snapshot()
   ```

3. **Check the console** for JavaScript errors:
   ```
   browser_console(clear=true)
   ```
   Do this after every navigation and after every significant interaction. Silent JS errors are high-value findings.

4. **Take an annotated screenshot** to visually assess the page and identify interactive elements:
   ```
   browser_vision(question="Describe the page layout, identify any visual issues, broken elements, or accessibility concerns", annotate=true)
   ```
   The `annotate=true` flag overlays numbered `[N]` labels on interactive elements. Each `[N]` maps to ref `@eN` for subsequent browser commands.

5. **Test interactive elements** systematically:
   - Click buttons and links: `browser_click(ref="@eN")`
   - Fill forms: `browser_type(ref="@eN", text="test input")`
   - Test keyboard navigation: `browser_press(key="Tab")`, `browser_press(key="Enter")`
   - Scroll through content: `browser_scroll(direction="down")`
   - Test form validation with invalid inputs
   - Test empty submissions

6. **After each interaction**, check for:
   - Console errors: `browser_console()`
   - Visual changes: `browser_vision(question="What changed after the interaction?")`
   - Expected vs actual behavior

### Phase 3: Collect Evidence

For every issue found:

1. **Take a screenshot** showing the issue:
   ```
   browser_vision(question="Capture and describe the issue visible on this page", annotate=false)
   ```
   Save the `screenshot_path` from the response — you will reference it in the report.

2. **Record the details**:
   - URL where the issue occurs
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Console errors (if any)
   - Screenshot path

3. **Classify the issue** using the issue taxonomy (see `references/issue-taxonomy.md`):
   - Severity: Critical / High / Medium / Low
   - Category: Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge issues that are the same bug manifesting in different places.
3. Assign final severity and category to each issue.
4. Sort by severity (Critical first, then High, Medium, Low).
5. Count issues by severity and category for the executive summary.

### Phase 5: Report

Generate the final report using the template at `templates/dogfood-report-template.md`.

The report must include:
1. **Executive summary** with total issue count, breakdown by severity, and testing scope
2. **Per-issue sections** with:
   - Issue number and title
   - Severity and category badges
   - URL where observed
   - Description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshot references (use `MEDIA:<screenshot_path>` for inline images)
   - Console errors if relevant
3. **Summary table** of all issues
4. **Testing notes** — what was tested, what was not, any blockers

Save the report to `{output_dir}/report.md`.

## Local / internal targets (localhost, 127.0.0.1)

When the hosted browser tool refuses internal addresses ("URL targets a private
or internal address"), do NOT give up on visual QA — drive Playwright directly
from the terminal and read the screenshots with `vision_analyze`:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox"])
    pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL, wait_until="networkidle")
    # click sidebar tabs by visible text, screenshot each
    pg.get_by_text("Analytics", exact=True).first.click()
    pg.screenshot(path="out/analytics.png", full_page=True)
    print(pg.inner_text("body"))          # text-first, verifiable
    print(errs)                            # silent JS errors
```

Text-first is what catches most bugs: print `inner_text('body')` per page and
assert the expected values are present. Use `vision_analyze` only to confirm
layout (charts, overlap). Screenshots + body text together are strong evidence.

**Assert on exact values, not substrings.** A check like `"MOCK" in body.upper()`
false-positives when the word appears anywhere (e.g. a tooltip). Target the
specific element (`pg.locator('text=MOCK').count()`).

## High-yield bug classes for dashboards

- **Env vars not reaching the browser.** CRA's DefinePlugin only inlines
  `process.env.REACT_APP_*` when referenced **literally**. A dynamic lookup
  (`process.env[key]` in a loop) is never replaced, so `process.env` is `{}` and
  a mock/live flag is silently stuck. Vite: use `import.meta.env.VITE_*` (and
  never `import.meta` under CRA/webpack — it is a hard syntax error).
- **CORS on non-default dev ports.** CRA/Vite pick a free port when 3000 is
  busy; a fixed `allow_origins=["...:3000"]` then breaks every API call. Prefer
  `allow_origin_regex` covering any localhost port in dev.
- **Header counters that only update from live events** show 0 on load while the
  list page shows data — seed them from a fetch on mount.
- **Mock data that is too uniform** (all timestamps the same day) makes trend
  charts render a flat line / single point; spread mock timestamps over days.
- **Fixed-width sidebars on mobile.** A `w-60 shrink-0` sidebar with no
  breakpoint stays 240px on a 390px screen, squeezing `<main>` to ~150px with
  clipped content. A naive check (`documentElement.scrollWidth - innerWidth`)
  returns **0** and false-greens, because the sidebar absorbs the squeeze and
  the document never overflows. Assert on the **content box** instead:
  `main.scrollWidth - main.clientWidth`; fix with an off-canvas drawer
  (`-translate-x-full` → `translate-x-0`, `md:static`) plus a hamburger toggle.
- **Toolbars that do not wrap.** A row of export/action buttons
  (`flex justify-between` without `flex-wrap`) overflows on narrow screens;
  add `flex-wrap` and give long labels `max-w-full min-w-0` + `shrink-0` badges.
- **`inner_text()` on a `<textarea>` returns `""`** — read `.value` (Playwright
  `input_value()`) for form fields, or the check silently fails on working code.

## Tools Reference

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Go to a URL |
| `browser_snapshot` | Get DOM text snapshot (accessibility tree) |
| `browser_click` | Click an element by ref (`@eN`) or text |
| `browser_type` | Type into an input field |
| `browser_scroll` | Scroll up/down on the page |
| `browser_back` | Go back in browser history |
| `browser_press` | Press a keyboard key |
| `browser_vision` | Screenshot + AI analysis; use `annotate=true` for element labels |
| `browser_console` | Get JS console output and errors |

## Tips

- **Always check `browser_console()` after navigating and after significant interactions.** Silent JS errors are among the most valuable findings.
- **Use `annotate=true` with `browser_vision`** when you need to reason about interactive element positions or when the snapshot refs are unclear.
- **Test with both valid and invalid inputs** — form validation bugs are common.
- **Scroll through long pages** — content below the fold may have rendering issues.
- **Test navigation flows** — click through multi-step processes end-to-end.
- **Check responsive behavior** by noting any layout issues visible in screenshots.
- **Don't forget edge cases**: empty states, very long text, special characters, rapid clicking.
- **Verify BOTH modes** for any mock/live toggle: MOCK renders seeded data;
  LIVE must actually fetch from the backend (watch network requests — a
  dashboard that silently falls back to mock is a real bug, not a pass).
- **Vision reviews hallucinate** color/contrast differences. Before "fixing" a
  reported color issue, read the actual tokens in the source; the reviewer may
  have misread two distinct colors as identical.
- When reporting screenshots to the user, include `MEDIA:<screenshot_path>` so they can see the evidence inline.
