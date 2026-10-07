# httpx Cookie Management for Multi-User Scenarios

## The Problem

When testing multi-user flows (e.g., PIC creates event, Reviewer verifies evidence), you need to maintain separate cookie jars per user. httpx handles this automatically when you use separate `AsyncClient` instances per user.

## Pattern: Per-User Clients

```python
# Create separate clients per user
pic_client = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)
reviewer_client = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)
admin_client = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)

# Login each user
await pic_client.post("/auth/login", json={"email": "pic@test.com", "password": "..."})
await reviewer_client.post("/auth/login", json={"email": "reviewer@test.com", "password": "..."})
await admin_client.post("/auth/login", json={"email": "admin@test.com", "password": "..."})

# Cookies are auto-managed per client instance
resp = await pic_client.get("/api/v1/auth/me")  # Uses PIC's cookies
resp = await reviewer_client.get("/api/v1/auth/me")  # Uses Reviewer's cookies
```

## Cookie Security

`secure=True` cookies are NOT sent over HTTP. For local testing:

```python
# In your FastAPI auth router
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=False,  # Set True in production with HTTPS
    samesite="strict",
    max_age=900,
)
```

## Common Pitfalls

| Pitfall | Why | Fix |
|---------|-----|-----|
| Cookies not sent | `secure=True` rejects HTTP | Set `secure=False` for local testing |
| Cookie conflicts | Same client used for multiple users | Use separate `AsyncClient` per user |
| 307 redirects | Trailing slash mismatch | Use `follow_redirects=True` |
| Cookies lost after `async with` | Client closed when block exits | Create client without `async with`, close manually |

## Cleanup

Always close clients when done:

```python
await pic_client.aclose()
await reviewer_client.aclose()
await admin_client.aclose()
```
