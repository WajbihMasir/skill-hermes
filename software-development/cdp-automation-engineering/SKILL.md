---
name: cdp-automation-engineering
description: "Build CDP browser automation tools."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [cdp, browser, automation, python, asyncio]
    homepage: https://github.com/NousResearch/hermes-agent
---

# CDP Automation Engineering

Build production-grade browser automation tools using Chrome DevTools Protocol (CDP) with Python asyncio.

## When to Use

Use this skill when:
- Building Python asyncio libraries that communicate with Chrome via CDP
- Creating multi-tab browser automation tools
- Implementing framework-aware form fillers for React/Vue/Svelte SPAs
- Building network interceptors or API sniffers
- Debugging why a form submission didn't navigate (capture the API response)
- Implementing email polling for verification codes

Do NOT use for:
- Simple one-off browser tasks (use `browser-automation` skill)
- Non-browser automation tasks
- Node.js/TypeScript CDP tools (patterns differ)

## Architecture Overview

A CDP automation toolkit typically has these layers:

| Layer | Module | Purpose |
|-------|--------|---------|
| Connection | `browser_spawner` | Auto-detect Chrome, launch with CDP flags |
| Lifecycle | `process_supervisor` | Zero-crash process management, auto-revive |
| Inspection | `network_interceptor` | Capture XHR/Fetch responses |
| Inspection | `runtime_evaluator` | Direct JS execution for deep DOM access |
| Session | `session_bridge` | Export cookies to HTTP clients |
| Navigation | `tab_manager` | Multi-tab create/list/switch/close |
| Interaction | `form_filler` | Framework-aware form input injection |
| Monitoring | `network_monitor` | Capture API responses after actions |
| Utility | `inbox_poller` | Async email polling with link/OTP extraction |

## Critical Pitfalls

### 1. Browser-Level vs Page-Level WebSocket

**Rule:** CDP WebSocket URLs containing `/devtools/browser/` are browser-level and CANNOT send `Network.enable`, `Runtime.evaluate`, or `Page.navigate`. Always resolve to a page-level target first.

```python
# WRONG — browser-level WS rejects page commands
ws_url = "ws://127.0.0.1:9222/devtools/browser/..."
await ws.send_json({"method": "Network.enable"})  # ERROR

# CORRECT — resolve to page target first
async with aiohttp.ClientSession() as s:
    async with s.get("http://127.0.0.1:9222/json") as r:
        targets = await r.json()
        page_ws = next(t["webSocketDebuggerUrl"] for t in targets if t["type"] == "page")
```

### 2. Listener Must Start Before Commands

**Rule:** Start the async listener task BEFORE sending CDP commands. If you send first, the response arrives before anyone is listening and is lost.

```python
# WRONG — response lost
await ws.send_json({"id": 1, "method": "Network.enable"})
listener = asyncio.create_task(listen_loop())  # Too late!

# CORRECT — listener ready first
listener = asyncio.create_task(listen_loop())
await ws.send_json({"id": 1, "method": "Network.enable"})
```

### 3. React/Vue Controlled Components Ignore Direct Value Assignment

**Rule:** `element.value = 'x'` is silently ignored by React, Vue, and Svelte controlled components. Use native value setters.

```javascript
// IGNORED by React/Vue
input.value = 'hello';

// WORKS — triggers framework reactivity
const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value'
).set;
nativeSetter.call(input, 'hello');
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
input.dispatchEvent(new Event('blur', { bubbles: true }));
```

### 4. Form Submit Not Navigating ≠ Success

**Rule:** When a form submit doesn't change the URL, the API almost certainly returned an error. Use `NetworkMonitor.capture_response_after_action()` to capture the response body and status code.

```python
response = await monitor.capture_response_after_action(
    action_callback=lambda: click_submit(),
    url_pattern=r"/api/signup",
    timeout=10.0,
)
if response and response["status"] != 200:
    print(f"Error: {response['body']}")
```

### 5. Multi-Step Flows Need Separate Tabs

**Rule:** For flows like temp-mail + signup, always use separate tabs. Navigating away from a temp mail page loses the session.

```python
tab_mgr = TabManager(browser_ws_url)
email_tab = await tab_mgr.create_tab("https://etempmail.net")
signup_tab = await tab_mgr.create_tab("https://app.example.com/signup")
# Read email from email_tab, fill form in signup_tab
```

## Module Patterns

### Network Interceptor Pattern

```python
class NetworkInterceptor:
    def __init__(self, ws_url: str):
        self._ws_url = ws_url
        self._responses: Dict[str, Dict] = {}
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self):
        # Resolve browser-level to page-level WS
        if "/devtools/browser/" in self._ws_url:
            self._ws_url = await self._resolve_page_ws()
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(self._ws_url)
        self._listen_task = asyncio.create_task(self._listen_loop())  # Start BEFORE commands
        await self._send("Network.enable")

    async def wait_for_response(self, url_pattern: str, timeout: float = 10.0):
        pattern = re.compile(url_pattern)
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            for rid, resp in self._responses.items():
                if pattern.search(resp["url"]) and resp["body"] is not None:
                    return resp
            await asyncio.sleep(0.2)
        return None
```

### Form Filler Pattern

```python
class FormFiller:
    async def fill_input(self, selector: str, value: str) -> bool:
        js = f"""
        (function() {{
            const input = document.querySelector('{selector}');
            if (!input) return false;
            const nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(input, {repr(value)});
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            return true;
        }})()
        """
        return await self._evaluate(js)
```

### Inbox Poller Pattern

```python
class InboxPoller:
    def __init__(self, fetch_func, condition_func=None, timeout=60, interval=5):
        self._fetch_func = fetch_func
        self._condition_func = condition_func or (lambda emails: len(emails) > 0)
        self._timeout = timeout
        self._interval = interval

    async def poll(self):
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < self._timeout:
            emails = await self._fetch_func()
            if self._condition_func(emails):
                return emails
            await asyncio.sleep(self._interval)
        return None

    @staticmethod
    def extract_links(text: str) -> List[str]:
        return re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)

    @staticmethod
    def extract_otp(text: str, length: int = 6) -> List[str]:
        return re.findall(rf'\b\d{{{length}}}\b', text)
```

## Testing Strategy

1. **Unit tests** verify imports, class instantiation, and method signatures
2. **Integration tests** connect to a real Chrome instance and verify end-to-end behavior
3. **Field tests** kill Chrome mid-operation and verify auto-recovery

Always test with a real Chrome instance — CDP behavior varies by Chromium version.

## References

- `references/cdp-target-resolution.md` — Detailed CDP target resolution and WebSocket session management
- `references/framework-form-filling.md` — Deep dive on React/Vue/Svelte form injection techniques
