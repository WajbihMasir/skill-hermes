---
name: website-mirroring
description: "Clone a site exactly: mirror its real assets offline."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mirror, clone, offline, html, css, assets, landing-page, archive]
    related_skills: [single-file-web-artifacts, claude-design, taste, blocked-page-recovery]
---

# Website Mirroring — Faithful Offline Clone

## When to Use

Use when the user wants a site's frontend **exactly as it is**: "clone this page",
"mirror this site", "save it offline", "100% identik", "persis sama".

Do NOT use for "make me something like this" / "in the style of" — that is a mock
(`claude-design`, `single-file-web-artifacts`). Do NOT use to extract design tokens
(`taste`).

The deliverable is the site's **real** HTML, CSS, JS, fonts, and images, saved locally —
not a hand-written approximation of them.

Design taste / composition lives in `claude-design`; design-token extraction in `taste`;
single-file artifact build+verify in `single-file-web-artifacts`. This skill is the
**mirror** path: copy the actual assets.

## Decide first: mock vs mirror

Two different deliverables. Pick per the ask; if ambiguous, ask once — the gap between
them is large and expensive to redo.

| Ask | Deliverable |
|---|---|
| "make me something like this", "in the style of", "a mockup" | **Mock** — write fresh HTML/CSS approximating the look. See `claude-design` / `single-file-web-artifacts`. |
| "clone this", "mirror it", "identical", "100% identik" | **Mirror** — download and serve the real assets. This is the ONLY way to be pixel-identical. |
| "use it only as a layout reference, I want to publish it" | **Rebuild** — original code, copy and assets following the mirror's *structure*. See `references/publishable-rebuild.md`. |
| "match this screenshot / PNG / Figma export exactly" | **Pixel-match a mock** — no live site to mirror; build HTML/CSS and calibrate against the image by measurement. See `reference-image-pixel-matching`. |

**State the trade-off out loud before starting a mirror:** recreating a page by eye always
drifts (type metrics, spacing rhythm, icon shapes, motion timing). Downloading the real
files is exact and is also *less* work. When the user says "identical", do not hand-build
and hope — mirror.

## Procedure

Run `scripts/mirror_site.py <url> <outdir>` for the mechanical part, then apply the
verification and fixes below. Do it by hand when the site needs judgement (auth, SPA
routing, API-driven data).

1. **Fetch the HTML — request gzip only.**
   ```python
   headers = {"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip"}
   ```
   Do NOT advertise `br` unless you decode it. A server that answers with brotli returns
   compressed bytes; `gzip.decompress` fails and a naive `.decode()` yields mojibake that
   looks like a broken site. Advertise only what you decode.

2. **Check it is server-rendered before promising a mirror.** If the saved HTML already
   contains the visible copy (search for the `<h1>` text and a body sentence), it is SSR —
   the static mirror will show content. If the body is an empty `<div id="root"></div>`,
   the page is client-rendered: the static HTML alone renders blank. In that case snapshot
   the *rendered* DOM instead:
   ```bash
   chrome --headless=new --disable-gpu --virtual-time-budget=10000 \
          --dump-dom "https://example.com/" > index.html
   ```

3. **Enumerate assets from three places, not one.** HTML attributes miss most of the page:
   - HTML: `<script src>`, `<link href>`, `<img src>`, `srcset`
   - CSS: every `url(...)` — fonts usually live only here
   - JS: string literals such as `"/logos/x.svg"`, `"/screens/overview.webp"` — bundled
     apps hold image paths as plain strings

4. **Download preserving the URL path structure** so relative rewrites stay simple.
   Expect 40-60 files / a few MB for a typical landing page.

5. **Rewrite root-absolute paths to relative** (see `references/asset-rewriting.md` for the
   exact rules and the corrupting mistake to avoid):
   - in `index.html`: `/x` → `./x`
   - in CSS under `/assets/`: `url(/x)` → `url(../x)`
   - in JS: `"/x"` → `"./x"`, by **exact quote-wrapped replacement**

6. **Neuter links to pages you did not mirror.** Internal routes (`/pricing`, `/blog`) that
   have no local file should become `#`, not dead paths — otherwise every click 404s.
   Keep the skip-link (`#main-content`) pointing at its real anchor.

7. **Strip third-party analytics** (Google Tag Manager, Cloudflare beacon). They are
   external, non-visual, and fail offline.

8. **Serve over HTTP — never `file://`.** A bundled ES module (`<script type="module">`)
   is blocked under `file://` with a CORS error (`origin 'null'`), so the page renders
   unstyled and empty. Ship a launcher:
   ```bat
   @echo off
   cd /d "%~dp0"
   start "" http://127.0.0.1:8777/index.html
   python -m http.server 8777
   ```
   Tell the user to double-click it, and explicitly warn that double-clicking `index.html`
   will NOT work.

9. **Verify — compare the mirror to the live page.**
   ```bash
   chrome --headless=new --disable-gpu --hide-scrollbars --window-size=1440,2600 \
          --virtual-time-budget=10000 --enable-logging=stderr --log-level=0 \
          --screenshot="out.png" "http://127.0.0.1:8777/index.html"
   ```
   - `--enable-logging=stderr` surfaces console / CORS / failed-load lines — grep for
     `CONSOLE|CORS|Failed to load|ERR_`. A clean run prints none.
   - `--virtual-time-budget` lets entrance animations settle before the shot.
   - Screenshot the **live** URL the same way and diff the two with `vision_analyze`.
   - Assert every downloaded file serves 200 from the local server, and confirm the HTML
     has no remaining root-absolute asset refs.
   - Validate bundled JS parses: `node --input-type=module --check < app.js`.

10. **Report honestly.** State file count and size, the launcher path, the exact changes
    made for offline use, and the copyright caveat below.

## Reading a mirror — enumerate its components and effects

When the ask is "what UI components / effects does this site use" and you already have the
files (a mirror you built, or any downloaded page), you need no browser and not the live
`taste` pipeline. The bundle holds everything: design tokens are the `--vars`, the effects
are `@keyframes` plus the hand-written (non-utility) classes, structure is the HTML, and
interactivity is a handful of DOM API names in the JS. Grep each in turn and report
concrete values only (hex, px, ms, easing) — never "clean and modern". Full recipe and the
grep patterns: `references/design-dna-from-mirror.md`.

## Pitfalls

1. **Never rewrite JS string literals with a bare regex on `/`.** `re.sub(r'"(/', '"."')`
   corrupts them into `"."/customers/x.webp"` — invalid JS that silently breaks the bundle.
   Replace **exact quote-wrapped strings** (`'"' + path + '"'` → `'"."' + path`), only for
   files that were actually downloaded. If the bundle is already corrupted, re-download it
   pristine rather than trying to repair the mangled text.
2. **`browser_exec` commonly refuses `file://` and `127.0.0.1`** (private/internal address).
   Verify a local mirror by driving the Chrome CLI directly as in step 9, not through the
   browser tool.
3. **A text-only extraction (`web_extract`) is not enough to build a mirror** — it returns
   prose, not the asset graph. Fetch the HTML yourself so you can see the `<script>`, `<link>`
   and inline `url()` references.
4. **Do not claim "100% identical" from a hand-built recreation.** If you wrote the CSS
   yourself, it is a mock; say so. Only the mirror path earns the claim, and it must be
   backed by a side-by-side screenshot.
5. **Mirroring is not always possible**: pages behind login, or fully client-rendered
   pages whose data arrives from an authenticated API, cannot be mirrored statically. Say
   which one you are in, rather than shipping a blank page.

## Copyright

A mirror is a byte-for-byte copy of someone else's code, fonts, and imagery. Deliver it
for learning, design research, or personal archiving, and say plainly that it must not be
published, hosted, or used commercially.

**Changing the content does not make it publishable.** Copyright protects the expression,
and a modified copy is a *derivative work* the rights holder controls exclusively — "I
rewrote the text" is an admission that the original was the base. Trademark is a separate
right that ignores your text entirely: keeping the name or logo infringes regardless. And
fair use is a defence argued in court, not a licence — do not offer it as a route to
publication.

When the user wants something they can ship, there are two correct paths:

- **Rebuild from the reference** — fresh code, 100% new copy, own assets, own brand,
  following only the mirror's section *structure* (an unprotected idea). Full procedure and
  compliance audit in `references/publishable-rebuild.md`.
- **Write a mock** (`claude-design`) when they never needed the original's specifics.

## Support Files

- `scripts/mirror_site.py` — fetches a page plus its asset graph (HTML attrs, CSS `url()`,
  JS string literals), saves it path-preserving, rewrites paths to relative, strips
  analytics, and writes a `start.bat` launcher.
- `references/asset-rewriting.md` — the per-file-type rewrite rules and the JS-corruption
  pitfall in detail.
- `references/publishable-rebuild.md` — how to turn a mirror into a work the user may
  legally publish: what may be reused (structure/ideas) vs what must be original, how to
  answer "can we copy their UI components?" (the component-level idea/expression split and
  the side-by-side "same company?" test), safe licence choices for icons and fonts, how to
  redraw a supplied brand mark as clean inline SVG (with the size-variant rule), how to
  build the added components as vanilla accessible widgets (dropdown→list on mobile, real
  tab filtering, carousel counter), and the forbidden-string audit to run before claiming
  it is publishable.
- `references/design-dna-from-mirror.md` — enumerate a mirrored site's design tokens,
  components, keyframe effects, and interactivity offline (no browser), with the CSS/HTML/JS
  grep recipes and the reporting shape.
