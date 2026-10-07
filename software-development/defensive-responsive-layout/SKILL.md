---
name: defensive-responsive-layout
description: "Use when fixing responsive layout bugs in a frontend."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [css, tailwind, responsive, layout, flexbox, sidebar, overflow, playwright, verification]
    related_skills: [dogfood, mock-to-live-integration, single-file-web-artifacts, frontend-component-testing]
---

# Defensive Responsive Layout

## When to use

A layout breaks at some viewport or interaction state: a nav rail that cannot be
restored once collapsed, content overflowing the window on mobile, a table or URL
stretching the page, a control that disappears. Also when asked to "make it
responsive across all breakpoints" or to apply defensive CSS to an existing app.

Not for: single-file HTML artifacts (use `single-file-web-artifacts`), choosing a
visual direction (`ui-ux-pro-max`), or writing the unit tests
(`frontend-component-testing`).

## Procedure

1. **Reproduce with numbers before touching code.** Do not fix a layout bug you
   have only been told about. Measure the failing element's box and the container
   chain:
   ```python
   pg.locator("[data-testid=thing]").bounding_box()        # {'x','y','width','height'}
   pg.evaluate("""() => { const n = document.querySelector('nav');
       return {sh: n.scrollHeight, ch: n.clientHeight, ov: getComputedStyle(n).overflowY}; }""")
   ```
   Record the before/after table in the deliverable. `y=1325` in a 900px viewport
   is a fact; "the button is hidden" is an opinion.
2. **Walk the container chain** from the broken element to `<body>`, printing each
   ancestor's `width` / `clientWidth` / `scrollWidth` / `overflowX` / `minWidth`.
   The first ancestor whose `scrollWidth > clientWidth` while its own
   `overflowX` is `visible` is the culprit — everything above it is a victim.
3. **Fix the element that owns the constraint**, not the symptom. Hiding overflow
   on `<body>` to stop a scrollbar hides the bug and crushes the content.
4. **Audit every viewport AND every page.** A fix verified on one page at one
   width is unverified. Sweep the smallest supported width across all routes;
   that is where unbreakable strings and wide tables surface.
5. **Confirm visually, then check nothing regressed.** Screenshot the fixed state
   and read it; then re-run the app's other gates (unit tests, per-page audit).

## CSS invariants (the rules that prevent the whole bug class)

- **A scrollable flex child needs `min-h-0` (or `min-w-0`).** A flex item's
  default `min-height: auto` refuses to shrink below its content, so `overflow-y:
  auto` never engages — the child grows and pushes siblings out of the box.
  `flex-1 overflow-y-auto` alone is not enough; add `min-h-0`.
- **`overflow: visible` on a scroll region disables scrolling.** Setting it to
  let a tooltip escape trades a clipped tooltip for a broken layout: the region
  grows to full content height and any sibling footer is pushed off-screen. Keep
  the scroll container scrolling and move the thing that needs to escape.
- **`position: fixed` inside a `transform`ed ancestor is NOT viewport-fixed.**
  Any `transform`, `filter`, or `will-change` on an ancestor creates a containing
  block, so the fixed element positions and clips against that ancestor. A
  `translate-x` sidebar (used by every off-canvas drawer) therefore traps fixed
  children. Escape by rendering through a portal to `document.body`:
  ```tsx
  import { createPortal } from "react-dom";
  {open && createPortal(<Tooltip style={{top, left}} />, document.body)}
  ```
  Position it from `getBoundingClientRect()` on hover/focus, not CSS `left-full`,
  so it stays correct when the container scrolls.
- **Every `flex-1` child of a row needs `min-w-0`.** Without it the child floors at
  its content width and blows the row out. This is the single most common cause of
  a page that scrolls sideways on mobile.
- **Long unbreakable strings need an explicit break rule.** URLs, JWTs, SHA
  hashes, base64 blobs and JSON bodies have no break opportunities. Add
  `overflow-wrap: anywhere` (a `.break-anywhere` utility) to the value, and
  `shrink-0` to its sibling badge/label so the row wraps instead of overflowing.
- **A wide table belongs in its own scroll container.** Wrap it in
  `min-w-0 w-full overflow-x-auto` and give the table an explicit
  `min-w-[Npx]` so it scrolls inside the wrapper rather than widening `<main>`.
- **`overflow: hidden` on a rounded panel silently CLIPS an oversized child, and no
  page-level check catches it.** A card with `border-radius` + `overflow: hidden` (the
  standard look for a table panel or a product mock) crops a too-wide table instead of
  letting it overflow — so `documentElement.scrollWidth === clientWidth` reports clean
  while columns and the rightmost action button are cut off. For a *decorative* mock
  (a dashboard screenshot inside a landing page) the right fix is not a scroll container —
  it is to **progressively drop columns at narrow widths** so the mock stays legible:
  ```css
  @media (max-width: 680px) { .app-table th:nth-child(4), .app-table td:nth-child(4) { display: none; } }
  @media (max-width: 420px) { .app-table th:nth-child(2), .app-table td:nth-child(2) { display: none; } }
  ```
  Also shrink the action cell to an icon-only button (wrap its label in a span and hide
  the span) so the last column fits. Then re-run the per-element `fits`/`clipped` probe —
  the page-level overflow check will keep saying clean the whole time.
- **Pin the footer, don't just place it last.** A footer that must always be
  reachable gets `shrink-0` (never compressed) inside a parent with
  `overflow-hidden` (cannot escape) — `sticky bottom-0` is belt-and-braces.
- **Root-level guard:** `html, body, #root { max-width: 100%; overflow-x: hidden; }`
  plus a `max-w-[1920px] mx-auto` shell so ultrawide does not stretch the layout.
- **Ship two affordances for any collapse.** If a control can hide its own
  restore button, add a second always-visible one (a header/topbar toggle) and a
  keyboard shortcut. One affordance inside the thing being collapsed is a trap.
- **An inline element ignores `width` and `height` — a sized block must be
  `display: block`.** A `<span>` used as a progress bar, divider, or colour swatch
  silently drops its `height: 5px` and sizes to its text line box, so it paints as a
  tall blob instead of a thin bar. This reads in a screenshot review as "a stray
  coloured shape over the layout" and sends you hunting for a stray element that does
  not exist. Any element given explicit dimensions needs `display: block` (or a
  flex/grid child position). Symptom to grep for: a `<span>`/`<i>` with `width`/`height`
  or a percentage width in its style.
- **`position: absolute` resolves against the nearest *positioned* ancestor, not the
  section you meant.** Decorative cards placed with `top: 40%` inside a
  `position: relative` wrapper that is itself flow-sized (its own height collapses to
  ~0 once all its children are absolute) resolve those percentages against that tiny
  height, so every card piles up at the top instead of spreading across the section.
  Make the stage span what you intend — `.stage { position: absolute; inset: 0; }`
  inside a `position: relative` section — so percentages resolve against the full
  section height.

## Verification gate

Run a scripted multi-viewport audit and require all of it (copy
`templates/multi_viewport_audit.py` and fill in its page table):

1. **Both boxes clean at every width** — the window AND the content box:
   `documentElement.scrollWidth - clientWidth` and
   `main.scrollWidth - main.clientWidth`. The window check alone false-greens:
   a fixed sidebar absorbs the squeeze while `<main>` is crushed, so the document
   never reports overflow.
2. **The collapse/expand cycle survives** — collapse, assert the restore control
   is still inside the viewport (`box.y + box.height <= viewportHeight`), expand
   again via **each** affordance.
3. **Every route at the smallest supported width** (360–390px) reports zero
   overflow in both boxes.
4. **Drawer behaviour** — opens, shows its backdrop, and the backdrop closes it; plus
   the a11y contract: `role="dialog"` + `aria-modal="true"`, `inert` while closed, `Esc`
   closes, Tab is trapped inside, and focus returns to the trigger on close. Add the
   open/close classes **synchronously** — a class toggled inside `requestAnimationFrame`
   is skipped in a background/throttled tab, so the state flips but the transition (and
   the visible panel) never applies, leaving an inconsistent DOM.
5. **Zero console errors**, then a screenshot read with vision.
6. **The no-JS path degrades, not breaks.** For a drawer, collapse, or accordion,
   prove the fallback by writing a scratch copy with every `<script>…</script>`
   physically removed and loading that (do not trust
   `Emulation.setScriptExecutionDisabled`, which may not apply to a new tab):
   ```python
   import re
   nojs = re.sub(r'<script>.*?</script>', '', src, flags=re.S)
   ```
   Assert every collapsible panel is visible and every JS-only control is hidden —
   never that the section is empty. Delete the scratch copy.

### Measuring a static page without a browser tool

When the page is a local file or `127.0.0.1` and `browser_exec` refuses it (private
address), do not fall back to eyeballing screenshots. Inject a probe that writes its
result into `document.title` and read it back with `--dump-dom` — exact numbers, no
image, no model in the loop:

```bash
chrome --headless=new --disable-gpu --window-size=420,900 \
  --virtual-time-budget=5000 --dump-dom "http://127.0.0.1:8777/index.html" 2>/dev/null \
  | grep -o '<title>M|[^<]*'
```

Build it by copying the page to a scratch dir and appending before `</body>`:

```html
<script>addEventListener('load',()=>setTimeout(()=>{
  const d=document.documentElement, out=[];
  out.push('vw='+d.clientWidth+' sw='+d.scrollWidth+(d.scrollWidth>d.clientWidth?' OVERFLOW':' ok'));
  document.querySelectorAll('*').forEach(el=>{const r=el.getBoundingClientRect();
    if(r.right>d.clientWidth+1) out.push(el.tagName+'.'+el.className);});
  document.title='M|'+out.join(' ;; ');
},900)});</script>
```

Sweep widths in a loop (`420/600/768/1024/1440`) and compare `scrollWidth` to
`clientWidth` at each. The probe file is a *copy* — delete it, never ship it.

## Pitfalls

- **Verify layout with DOM measurements, not vision — it lies for narrow viewports AND for animated/multi-scene UI.**
  Downscaling a tall 390px screenshot to fit the vision model's input blurs and clips
  small text, and the model then reports confident false positives — "headline cut off",
  "button clipped", "text overflowing" — for elements that measure perfectly fine. A
  vision pass is for *taste and gross structure* (is the rhythm right, is something
  obviously broken); for "does it fit", measure:
  ```js
  // per element: does its box stay inside its parent's, and does its own content clip?
  const r = el.getBoundingClientRect(), p = el.parentElement.getBoundingClientRect();
  fits   = r.right <= p.right + 1;
  clipped = el.scrollWidth > el.clientWidth + 1;
  ```
  Report `fits=YES clipped=NO` per element as evidence. Do not "fix" a layout on vision
  alone — you will restructure working markup chasing a rendering artefact of the review.
  A Chrome CLI screenshot taken with `--window-size=W,H` is NOT guaranteed to render at
  CSS viewport width `W`, so a "mobile" shot can come out at desktop layout width and read
  as catastrophically clipped. Before believing any breakpoint claim, set the real viewport
  with `Emulation.setDeviceMetricsOverride(width=390, mobile=True)` and require
  `documentElement.scrollWidth - clientWidth === 0`. The number is the verdict; the image
  is not. Keep a vision image small enough to be accepted — capture the viewport only
  (jpeg, `deviceScaleFactor=1`), never a full-page shot at scale 2. The same distrust
  applies to **animated** UI (a cross-fading "film", a carousel, a morphing accordion):
  a vision pass merges frames that never coexist and reports overlaps, ghost text, or
  "empty" regions the DOM disproves. Freeze the frame before judging it —
  `el.getAnimations().forEach(a=>{a.pause();a.currentTime=t})` — and confirm every
  visual claim with `getBoundingClientRect()` / computed styles before restructuring
  working markup.
- **A horizontal carousel's off-screen slides are SUPPOSED to exceed the viewport — do
  not "fix" them.** A scroll-snap track with `grid-auto-flow: column` places slides 2..N to
  the right of the visible area by design, so a per-element `r.right > clientWidth` sweep
  reports the carousel (and every descendant) as overflowing. Exclude descendants of a
  deliberate `overflow-x: auto` container from the overflow list, and let the page-level
  `documentElement.scrollWidth === clientWidth` check decide whether the page really
  scrolls. The same applies to a `<details>`-driven or off-canvas drawer whose closed
 state is parked outside the box, and to any deliberate scroll box: a terminal or code
 block with `overflow-x: auto` legitimately holds children wider than the viewport, so its
 descendants appear in the sweep while the page itself does not scroll. Exclude them and
 let page-level `documentElement.scrollWidth === clientWidth` decide.
- **A tall page needs a window as tall as the page, or the bottom sections are simply
  absent from the shot.** Measure first (`documentElement.scrollHeight`), then screenshot
  with `--window-size=W,<scrollHeight>`; a fixed 2000–3000px window silently omits
  pricing/FAQ/footer and reads as "missing content".
- **A headless screenshot can come back byte-identical because it was served from
  cache — that means you rendered the OLD page, not that nothing changed.** After
  editing a file, a re-render that produces the exact same file size as the previous
  shot is the tell. Bust it: copy the edited files to a fresh directory (or append a
  `?v=<timestamp>` query to the URL) and point `--user-data-dir` at a new path, then
  screenshot that. Trusting the cached shot leads you to "fix" a bug that is already
  gone, or to declare a change invisible when it did land.
- **A control gated on its own output is dead on arrival.**
  `disabled={results.length === 0}` on the button whose job is to *fetch* results
  can never be pressed, so the data never arrives. Gate on the input instead
  (`disabled={rows.length === 0}`) and explain the precondition in `title`. Walk
  every disabled condition and ask what sets it.
- **Clicking a backdrop that sits under the drawer times out.** Playwright targets
  an element's centre; with a 240px drawer over a 390px backdrop the centre is
  covered, and the click retries until it fails. Click the visible strip by
  coordinates (`page.mouse.click(box.x + box.width - 20, box.y + box.height/2)`)
  rather than reaching for `force=True`, which skips the hit-test you want.
- **Assert on the intended new behaviour, don't weaken the assertion.** When a UI
  change is deliberate (a tooltip now renders on hover instead of 31 always-mounted
  nodes; an empty state replaces canned data), update the test to assert the NEW
  contract *more* precisely — and say so in the summary. Loosening a check until it
  passes, or leaving a stale one, are both how a real regression ships.
- **A stale process serves stale code.** After rebuilding, confirm the served
  bundle matches disk before trusting a browser result:
  `curl -s http://localhost:3000/ | grep -o 'main\.[a-f0-9]*\.js'` vs
  `ls build/static/js/main.*.js`. Restart the static server after each build.
- **A UI action backed by a real service needs a condition wait, not a sleep.**
  An LLM-backed reply measured at 3.5–8s fails a `sleep(2)` assertion that then
  looks like an app bug. Use `wait_for_function` on the rendered DOM with a
  generous timeout.
- **Animate-aware nav clicks.** A sidebar mid-transition is "unstable" to
  Playwright, so `click()` waits and then fails. Use `click(force=True)` for
  animated nav and assert the page root marker before asserting content —
  otherwise the previous page is still mounted and the next assertion validates
  the wrong screen.
- **Check the smallest width, not just 390px.** 360px is a common Android floor
  and finds offenders a 390px check misses.

## Support Files

- `templates/multi_viewport_audit.py` — multi-viewport + collapse/expand audit:
  asserts window and content-box overflow, the toggle staying on-screen, both
  expand affordances, drawer/backdrop behaviour, and a per-route sweep at the
  smallest width. Copy it, fill in the route table, run it.
