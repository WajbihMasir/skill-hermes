# Client-rendered listings: get the data from the bundle

Use when a listing/catalog page fetches fine but the grid is empty, or only the
first page has items. The HTML "succeeded" (200, plausible size) yet carries no
data — a fake success of the same family as a WAF interstitial.

## Recognise it

- Page 1 (`/list`) is server-rendered with ~16 cards; `/list?page=2` and beyond
  return the same shell with an **empty grid container**. Fetching `?page=N` in a
  loop silently yields only page 1's items.
- A `?filter=...` URL param (e.g. `?free=true`) is read by client JS, not the
  server — fetching that URL still returns only the page-1 payload.
- `modulepreload` links / `script src` point at framework bundles
  (`/assets/main-<hash>.js`). The dataset is usually embedded in one of them as
  an array/object literal, not fetched from `/api/`.

Do NOT loop `?page=N` and conclude the site has one page of data.

## Recover the dataset

1. Fetch the HTML, collect bundle URLs:
   `re.findall(r'<link[^>]+href="([^"]+\.js)"', html)` (modulepreload) plus
   `script src`.
2. Fetch each bundle; grep for the field names you saw in the rendered page
   (a repeated object key like `slug:` or `designMdSlug`) to find the blob.
3. Bracket-match the array/object literal out of the minified JS, then parse it.

## Parse JS literals with node, not json.loads

Minified data is JS object-literal syntax: **bare keys**, single-quoted or
escaped strings, and raw quotes inside values. `json.loads` fails on this even
after a regex that quotes bare keys — string-escaping rules differ. Hand it to
node's parser instead:

```python
start = js.rfind("[{slug:", 0, js.find("designMdSlug"))   # anchor on a field name
j, depth = start, 0
while j < len(js):
    depth += js[j] == "["; depth -= js[j] == "]"
    if depth == 0 and js[j] == "]": break
    j += 1
open("arr.js", "w").write("const A=" + js[start:j+1] + ";console.log(JSON.stringify(A))")
# then: node arr.js > arr.json   ->  json.load(arr.json)
```

This is the reliable path; a pure-Python quote-fix is fragile.

## sitemap.xml is for URLs, not attributes

`sitemap.xml` enumerates every canonical page URL (good for finding slugs you
missed) but carries **no** per-item metadata (price, free/paid, category). For
attributes you still need the bundle blob or an API.

## Deriving a boolean attribute

When the site distinguishes tiers/status by an optional field, that field's
**presence** is the flag — e.g. a `designMdSlug` key present means "free
download", absent means "paid request only". Cross-check on a detail page (a
free one renders a Download CTA; a paid one renders a request CTA) before
reporting the split to the user.

## Worked example: getdesign.md catalog

VoltAgent's `getdesign.md` hosts 550+ DESIGN.md analyses. The full ~566-entry
dataset is embedded in its main bundle as objects with keys
`slug,title,category,tags,thumb,pages,favicon,website,tagline,addedAt` plus
optional `designMdSlug,highDemand,featured,priority,orders`. Presence of
`designMdSlug` marks a free/downloadable entry. A free entry's DESIGN.md is
installed with `npx getdesign@latest add <slug>` (verified working); the rest
are behind a ~$99/mo "Catalog Pass".
