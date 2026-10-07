---
name: browser-harness-windows
description: Use when browser_exec fails on Windows.
---

# browser_harness on Windows: make the browser usable

## 1. "BU_CDP_URL unreachable after 30s" — Chrome is not running

The harness auto-discovers a dedicated Chrome on port **9222**. Start one (never
touch the user's normal profile — use a separate `--user-data-dir`):

```
"C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="%LOCALAPPDATA%\hermes\chrome-automation" \
  --no-first-run --no-default-browser-check \
  --disable-features=Translate,MediaRouter \
  --window-size=1440,900 about:blank
```

A ready-made launcher lives at `~/.config/browser-harness/start-browser.bat`
(idempotent: no-ops when 9222 already answers). Run it with
`cd ~/.config/browser-harness && cmd /c start-browser.bat` — calling the .bat
path directly through a POSIX shell opens an interactive cmd instead.
Verify with `curl -s http://127.0.0.1:9222/json/version`.

**Use windowed (headed) mode, not `--headless=new`.** Headless makes
`Page.captureScreenshot` time out after 60s even though navigation works.

## 2. `fill_input` types nothing (empty value) on real sites

Root cause: Chrome **drops `Input.dispatchKeyEvent` while the browser window
lacks OS focus** (backgrounded, headless, or another app in front). `press_key`
therefore lands no characters, while `type_text` (which uses `Input.insertText`)
still works — that asymmetry is the tell.

Fix: enable focus emulation once per session:

```python
cdp("Emulation.setFocusEmulationEnabled", enabled=True)
```

It survives in-page navigation and later `browser_exec` calls. To make it
permanent, patch `press_key` in
`<venv>/Lib/site-packages/browser_harness/helpers.py` to call a cached
`_ensure_focus_emulation()` helper first. Restart Chrome after patching (the
module is imported per process).

Diagnose with: does `type_text("x")` set the value but `press_key("x")` not?
That is this bug, not a bad selector.

## 3. `PermissionError: [WinError 5] ... bu-default.port` after a forced kill

A `taskkill /F` on Chrome leaves the daemon stale, so it cannot unlink its
runtime files. Clear them, then retry — the harness recreates them:

```bash
rm -f ~/.config/browser-harness/runtime/bu-default.{port,pid}
```

## 4. `localhost` / `127.0.0.1` is blocked — this is intended

`browser_exec` refuses private/internal addresses (`Blocked: URL targets a
private or internal address`). This is a deliberate guardrail, **not** a broken
browser. To verify a local page, use headless Chrome screenshots instead:

```
chrome.exe --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1440,2600 --virtual-time-budget=10000 \
  --screenshot="out.png" "http://127.0.0.1:PORT/index.html"
```

`--virtual-time-budget` lets animations settle before capture. On `file://`,
bundled ES modules and woff2 fonts are blocked by CORS — serve over HTTP.

## 5. Search engines may serve a bot wall, not a broken browser

Bing/DuckDuckGo can return a page with no `input[name=q]` to automated Chrome.
Before blaming `fill_input`, print the actual inputs:
`js("JSON.stringify(Array.from(document.querySelectorAll('input')).map(i=>i.name))")`.
Test input helpers on `about:blank` with a self-made form to isolate browser
fault from site behaviour.
