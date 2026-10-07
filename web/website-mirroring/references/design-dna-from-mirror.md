# Design DNA from a mirror (offline)

Goal: given a mirror (or any downloaded site) on disk, enumerate **every** UI component,
effect, and token with concrete values — no browser, no live fetch. This is the offline
sibling of the `taste` live pipeline; use it when the files are already present.

Inputs: the mirror dir — typically `index.html`, `assets/index-<hash>.css`,
`assets/index-<hash>.js`, `fonts/`, image dirs. Hashed asset names mean Vite/Rollup.

## Do the file work in ONE tool

On Windows the `execute_code` kernel and the `terminal` shell do not share `/tmp`. A file
written by a shell `curl -o /tmp/x` is invisible to Python `open('/tmp/x')`, and vice
versa. Download and read inside `execute_code` with `urllib`/`open`, or use an absolute
path both tools agree on. (Same rule as the API-JSON pitfall in
`contributing-to-open-source`.)

## 1. Inventory the tree

`find -type f` (or `os.walk`) and group by extension. Identify the single CSS bundle and
JS bundle. Note `fonts/` and image dirs — those name the typefaces and the art.

## 2. Design tokens — grep the `--vars`

```python
re.findall(r'(--[\w-]+)\s*:\s*([^;{}]+)', css)
```

Filter out Tailwind internals (`--tw-*`, `--default-*`) to surface the real tokens: the
brand palette (`--color-primary` etc.), type scale (`--text-*`), radii, easing, and any
`--secret-*`/theme overrides. The custom `--color-*` set IS the brand DNA.

## 3. Effects — keyframes and the custom class layer

Enumerate every keyframe: `re.findall(r'@keyframes\s+([\w-]+)\s*\{(.*?)\}\s*\}', css, re.S)`.
Then grep `animation:` / `transition:` / `animation-timeline:` for duration, easing, and
trigger. Note scroll-driven animation (`animation-timeline: view()` +
`animation-range`) — no JS involved.

Split the CSS into `selector{body}` pairs (`re.findall(r'([^{}]+)\{([^{}]*)\}', css)`) and
keep only selectors that are NOT Tailwind utilities. That hand-written set (e.g.
`hero-wash`, `card-hatch`, `rank-film-*`, `stats-*`) is where the bespoke effects live.
Detect Tailwind v4 by the presence of `@layer`, `@theme`, `@property`.

## 4. Structure — read the HTML

- Every `<section>` with its `aria-label` / classes.
- `<h1>`–`<h3>` text (the page's content outline).
- Buttons, `<figcaption>`, `<summary>`.
- `class="..."` frequency counter: the top-N tokens are the utility vocabulary and reveal
  repeated component patterns.

## 5. Interactivity — grep the JS by API name

Minified JS still contains API identifiers. Count: `IntersectionObserver`,
`ResizeObserver`, `requestAnimationFrame`, `matchMedia`, `prefers-reduced-motion`,
`aria-pressed`, `data-*` hooks. These name reveal-on-scroll, accordions, and
animation-pause toggles. Do NOT grep the JS for PascalCase component names — bundling
mangles them; read the rendered HTML for structure instead.

## 6. Accessibility — count the attributes

`aria-expanded`, `aria-pressed`, `aria-controls`, `inert`, `role="dialog"`, `skip-link`.
Their presence tells you what is keyboard-operable and what honours reduced motion.

## Report shape

Grouped inventory, concrete values only:

1. **Tech stack** — build tool (hashed assets), framework (`<div id="root">`), CSS layer
   (Tailwind v4 markers), icon set (inline `<svg class="lucide-*">`), fonts (`@font-face` src).
2. **Design tokens** — the custom `--color-*` / type / radius / easing, verbatim.
3. **Components** — one block each: markup sketch + classes + behaviour.
4. **Effects** — table of name → keyframes → duration → trigger.
5. **Interactivity** — feature → mechanism (which DOM API).
6. **Accessibility** — the affordances found.

## Pitfalls

- A "broken internal link" scan must treat **nested directories as valid page prefixes**:
  `/telegram` is fine when `telegram/index.mdx` exists. A flat slug set flags working
  links as broken.
- Decorative texture (`repeating-linear-gradient` + `clip-path`/`mask-image` blobs) is an
  *effect*, not layout — file it under effects, don't read it as structure.
- `codespell` returning zero hits means the copy is actually clean; do not invent typos to
  have something to report.
- Report what the files prove. If a value is not in the CSS/HTML, say so rather than
  guessing a token that "should" be there.
