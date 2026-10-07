# Asset Rewriting for Offline Mirrors

Goal: a mirrored tree that renders identically when served from a local static server, with
no dependency on the origin.

## Rule table

| File | Location | Original | Rewritten | Why |
|---|---|---|---|---|
| HTML | root | `/logos/x.svg` | `./logos/x.svg` | page sits at root |
| CSS | `/assets/` | `url(/fonts/a.woff2)` | `url(../fonts/a.woff2)` | CSS is one level down |
| JS | `/assets/` | `"/screens/a.webp"` | `"./screens/a.webp"` | resolved against the **document**, not the script |

JS asset URLs are resolved relative to the HTML document, so `./screens/a.webp` from
`/assets/app.js` correctly lands on `/screens/a.webp`. Do not use `../` in JS.

## The corrupting mistake

Rewriting JS with a regex on the leading slash destroys string literals:

```python
# WRONG — mangles every path into "."/x.webp" (invalid JS)
js = re.sub(r'"(/[^"]*)"', r'"."\1"', js)
```

Replace exact quote-wrapped strings, and only for files that were downloaded:

```python
for rel in downloaded_paths:          # e.g. "/screens/overview.webp"
    for q in ('"', "'"):
        js = js.replace(q + rel + q, q + "." + rel + q)
```

Verify afterwards that no root-absolute asset refs remain:

```python
re.findall(r'["\'](/[A-Za-z0-9_\-/]+\.(?:png|jpe?g|webp|svg|gif|avif|woff2?|css|js))["\']', js)
```

## Choosing what to rewrite vs neuter

- **Rewrite** when the referenced file exists in the mirror (assets, the one page).
- **Neuter to `#`** when it is an internal route you did not mirror (`/pricing`, `/blog`,
  `/learn/*`) — a dead path 404s on every click; `#` is inert.
- **Leave absolute** when it is a genuine external link (a customer's own website, a GitHub
  repo, an app subdomain) — those should still work.

## Analytics to strip

`googletagmanager.com/gtag/js`, inline `gtag(...)` bootstrap, and
`static.cloudflareinsights.com/beacon.min.js`. None are visual; all fail offline.

## Verification one-liner set

```python
# every local ref resolves on disk
missing = [r for r in refs if not os.path.exists(os.path.join(out, r.lstrip('/')))]
# no absolute asset refs left in HTML/JS
abs_left = re.findall(r'(?:href|src)="(/[^"]*)"', html)
```
