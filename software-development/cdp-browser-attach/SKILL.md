---
name: cdp-browser-attach
description: "Attach Hermes to real Chrome via CDP to bypass bots."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [browser, cdp, stealth, bot-detection, chrome]
    homepage: https://github.com/NousResearch/hermes-agent
---

# CDP Browser Attach — Bypass Bot Detection

Attach Hermes browser automation to your real Chrome browser via Chrome DevTools Protocol (CDP). This eliminates bot detection (CAPTCHA, Cloudflare, PerimeterX) because all fingerprints are genuinely human.

## Why This Works

| Layer | Headless/Playwright | CDP Attach to Real Chrome |
|-------|---------------------|---------------------------|
| `navigator.webdriver` | `true` (bot giveaway) | `false` (real browser) |
| TLS/JA3 Fingerprint | Library-specific pattern | Genuine Chrome TLS handshake |
| WebGL/Font/Audio | Generic/empty | Real GPU, real fonts, real audio |
| IP Reputation | Datacenter (suspicious) | Your home/ISP IP |
| Cookies/History | Empty (bot indicator) | Real session data |

## Prerequisites

- Google Chrome or Brave installed
- Hermes Agent with browser toolset enabled

## Setup (3 Steps)

### 1. Kill Existing Chrome

```bash
# Windows
taskkill //F //IM chrome.exe

# macOS
killall "Google Chrome"

# Linux
pkill -f chrome
```

### 2. Launch Chrome with Remote Debugging

```bash
# Windows
"C:/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/chrome-dev-profile" --no-first-run --no-default-browser-check &

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-dev-profile" --no-first-run --no-default-browser-check &

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-dev-profile" --no-first-run --no-default-browser-check &
```

**Important:** Use a separate `--user-data-dir` to avoid conflicts with your main Chrome profile.

### 3. Configure Hermes

```bash
hermes config set browser.cdp_url "http://127.0.0.1:9222"
hermes config set browser.headed true
```

Or in `config.yaml`:
```yaml
browser:
  cdp_url: "http://127.0.0.1:9222"
  headed: true
```

## Action Gating (Human-in-the-Loop)

Configure Hermes to require confirmation for destructive actions:

```bash
hermes config set approvals.mode smart
hermes config set approvals.destructive_slash_confirm true
```

### Gating Rules

| Action Type | Behavior |
|-------------|----------|
| Navigate URL, scroll, read DOM | Auto-execute |
| Click navigation buttons | Auto-execute |
| Fill forms (non-destructive) | Auto-execute |
| Submit forms | **Require confirmation** |
| Login to accounts | **Require confirmation** |
| Delete/modify data | **Require confirmation** |
| Financial transactions | **Require confirmation** |

## Verification

After setup, verify CDP is active:

```bash
curl -s http://127.0.0.1:9222/json/version
```

Expected output:
```json
{
  "Browser": "Chrome/154.0.8037.58",
  "Protocol-Version": "1.3",
  "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/..."
}
```

In Hermes, navigate to any site — the `stealth_features` field should show `["cdp_override"]`.

## Tested Sites (All Pass)

| Site | Protection | Result |
|------|-----------|--------|
| Google | reCAPTCHA v3 | ✅ |
| Logam Mulia | Cloudflare | ✅ |
| Pegadaian | Cloudflare | ✅ |
| Airbnb | PerimeterX | ✅ |
| TikTok | ByteDance anti-bot | ✅ |
| Nike | PerimeterX/Human | ✅ |
| ChatGPT | Cloudflare Turnstile | ✅ |
| emergent.sh | Cloudflare Turnstile + SPA | ✅ |

## Python Toolkit (v4.1)

The `cdp_orchestrator` Python package provides programmatic access to all CDP capabilities:

| Module | Capability |
|--------|------------|
| `TabManager` | Create/list/switch/close tabs |
| `FormFiller` | Framework-aware input injection (React/Vue/Svelte) |
| `FormSubmitter` | Submit with full monitoring (network + errors + DOM stability) |
| `TurnstileHandler` | Detect/solve Cloudflare Turnstile |
| `DOMObserver` | MutationObserver injection, DOM stability detection |
| `NetworkMonitor` | Capture API responses after actions |
| `InboxPoller` | Poll temp email + extract verification links/OTP |
| `SessionBridge` | Export/import cookies to aiohttp |
| `APISniffer` | Sniff internal API endpoints |

### Quick Start

```python
from cdp_orchestrator import TabManager, FormSubmitter, TurnstileHandler

# Create tab
tm = TabManager(browser_ws_url)
await tm.connect()
tab_id = await tm.create_tab('https://example.com')

# Submit form with monitoring
fs = FormSubmitter(page_ws_url)
await fs.connect()
result = await fs.submit_with_monitoring(submit_action, url_pattern=r'api')
print(f'Success: {result.success}')
print(f'Errors: {result.errors}')
print(f'Captures: {result.network_captures}')
```

### Signup Flow (emergent.sh)

```python
# 1. Open signup modal
# 2. Click "Continue with Email"
# 3. Fill form with native value setter
# 4. Wait for Turnstile auto-solve (3-8s on residential IP)
# 5. Submit with form.requestSubmit() (NOT button.click())
# 6. Monitor network for API response
```

**Key insight:** Use `form.requestSubmit()` instead of `button.click()` for SPA forms. The native form submission triggers React/Vue event handlers correctly.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `cdp_url` not working | Ensure Chrome is running with `--remote-debugging-port=9222` |
| Chrome won't start with flag | Kill all Chrome processes first, use separate `--user-data-dir` |
| Still getting blocked | Clear site cookies in the dev profile, try again |
| CDP connection refused | Check firewall, ensure port 9222 is not blocked |

## Security Notes

- The CDP endpoint (`127.0.0.1:9222`) is only accessible locally — no external exposure
- Use a separate `--user-data-dir` to isolate from your main browsing profile
- Close Chrome with debugging port when not in use
- Do not expose port 9222 to network (no `--remote-debugging-address=0.0.0.0`)
