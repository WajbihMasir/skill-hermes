# CDP Target Resolution & WebSocket Management

## The Two WebSocket Levels

CDP exposes two types of WebSocket endpoints:

| Level | URL Pattern | Capabilities |
|-------|------------|--------------|
| Browser | `ws://.../devtools/browser/<uuid>` | `Target.*`, `Browser.*` only |
| Page | `ws://.../devtools/page/<id>` | All domains: `Network.*`, `Runtime.*`, `Page.*`, `DOM.*` |

## Resolution Algorithm

```python
async def resolve_page_ws(browser_ws_url: str) -> str:
    """Resolve browser-level WS to first available page target."""
    from urllib.parse import urlparse
    parsed = urlparse(browser_ws_url)
    host = f"http://{parsed.hostname}:{parsed.port}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{host}/json") as resp:
            targets = await resp.json()
            for t in targets:
                if t.get("type") == "page":
                    return t["webSocketDebuggerUrl"]
            raise RuntimeError("No page targets found")
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Network.enable` rejected | Using browser-level WS | Resolve to page WS first |
| `Runtime.evaluate` returns empty | No execution context | Wait for page load, use `Page.enable` |
| `Target.createTarget` fails | Browser not ready | Wait for `/json/version` to return 200 |
| WebSocket disconnects mid-command | Page navigated or closed | Implement reconnect logic |

## Session Management

When switching between tabs, each tab has its own WebSocket. The `TabManager` handles this by:
1. Creating a new target via `Target.createTarget`
2. Getting the new target's `webSocketDebuggerUrl` from `/json`
3. Opening a new WebSocket connection to that URL
4. Routing all subsequent commands through the new connection
