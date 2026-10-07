---
name: browser-automation
description: "Automate browser tasks with Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, automation, web, scraping]
    homepage: https://github.com/NousResearch/hermes-agent
---

# Browser Automation with Hermes

## When to Use

Use this skill when automating browser interactions with Hermes — navigating pages, filling forms, clicking elements, scraping data, or verifying visual state. Also use when configuring browser behavior (headful mode, action gating) or working around bot detection.

## Configuration

### Headful Mode
Set `browser.headed = true` in config.yaml to show the browser window on the desktop. This is useful for:
- Verifying agent actions visually
- Debugging browser automation issues
- Building trust in agent behavior

**Note:** Headful mode may require a session restart (`/reset`) to take effect.

### Action Gating
Set `approvals.mode = smart` in config.yaml to enable smart approval mode. This automatically:
- Allows navigation, scrolling, and reading without confirmation
- Requires confirmation for destructive actions (submit, delete, modify)

## Workflow

### Basic Navigation
1. `browser_navigate` to open a URL
2. `browser_snapshot` to get page structure
3. `browser_click` / `browser_type` to interact
4. `browser_vision` to verify visual state

### Handling Bot Detection
When a site blocks automated access:
1. Try alternative search engines
2. Navigate directly to sites without aggressive bot protection
3. Use `browser_vision` to verify page state

### Verifying Actions
- `browser_vision` captures the viewport, not the OS window
- For visual verification of the browser window itself, look at the desktop directly

## Pitfalls

- **Client-rendered listings hide data in the JS bundle:** if a catalog/listing returns 200 but its grid is empty on page 2+, or `?filter=` params only work client-side, the dataset is embedded in a minified JS bundle (`modulepreload` links), not behind `?page=N`. Don't loop pagination and conclude the data isn't there; bracket-match the array out of the bundle and parse it with node (JS object literals with bare keys break `json.loads`). Full recipe: `references/spa-embedded-data.md`.

- **Bot detection varies by site:** Some sites block automated access while others don't. If one source fails, try alternatives.
- **`browser_vision` captures viewport only:** The screenshot shows the page content, not the browser window or OS interface.
- **Headful mode may require restart:** Configuration changes may not take effect until the session is reset.
- **Clicking search results may not navigate:** If `browser_click` on a search result doesn't change the page, use `browser_navigate` with the direct URL instead.
- **Never share unverified URLs from web search:** Web search can return content from other accounts with similar metrics. Always verify a URL belongs to the correct account before sharing it with the user.
- **Instagram reels grid may not render:** The profile header may load but reel thumbnails with view counts may be absent from the DOM. If `browser_snapshot` shows no reel links after scrolling, inform the user rather than guessing URLs.