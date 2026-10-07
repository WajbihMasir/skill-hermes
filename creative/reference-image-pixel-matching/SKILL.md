---
name: reference-image-pixel-matching
description: "Recreate a UI pixel-accurately from a reference image."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pixel-perfect, design-reference, html, css, verification, measurement, landing-page, mockup]
    related_skills: [single-file-web-artifacts, website-mirroring, taste, claude-design, browser-harness-windows]
---

# Reference-Image Pixel Matching

## When to Use

Use when the user supplies a design reference — a screenshot, a hero PNG, a Figma export —
and wants a hand-built HTML/CSS page to match it as closely as possible: "100% identik",
"pixel-perfect", "persis sama", "make it look exactly like this image".

This is the **mock path with a numeric accuracy target**, so verification is measurement,
not opinion. If the reference is a *live site* and the user wants a byte-faithful copy,
mirror the real assets instead (`website-mirroring`). If they only want the general look,
use `claude-design`.

Sibling skills: build+verify loop for single-file artifacts in `single-file-web-artifacts`;
token extraction from a live URL in `taste`; browser recovery in `browser-harness-windows`.

## Deliverable

HTML + CSS (+ small vanilla JS) that lands on the reference's geometry. Static HTML/CSS is
the right tool: a framework (React/Next) adds a build step and changes nothing about pixel
accuracy — accuracy comes from measurement and calibration. Say so if the user offers to
let you use one.

## The procedure (order matters)

### 1. Pin the render width to the reference PNG's own pixel width — before any CSS

A screenshot (headless Chrome, an OS capture, a design export) is taken at the viewport
size, so **the reference PNG's pixel width IS the capture width.** Render at that width and
compare 1:1. Getting this right first matters: a wrong coordinate frame makes every element
land ~10-20px off and no per-element nudge fixes it.

Confirm it before trusting it — the centre of a wide centred element (dashboard frame, nav
pill) should land within a few px of `png_width / 2`:

```python
# reference PNG is 1536 wide → render at 1536, no scrollbar (a headless shot has none)
cdp('Emulation.setDeviceMetricsOverride', width=1536, height=1024, deviceScaleFactor=1, mobile=False)
cdp('Emulation.setScrollbarsHidden', hidden=True)
# dashboard frame x 208–1327 → centre 767.5 ≈ 1536/2 ✓
```

Do **not** derive a "content width" from a centred element and subtract a scrollbar: that
reasoning produced a spurious 1503 from a 1536-wide PNG, plus a `translateX(22px)` to
reconcile the residual, and shifted every element the wrong way for several iterations.
Subtract a scrollbar only when you can **see** a scrollbar strip in the image itself.

A small residual offset (a few px) between a block's centre and the frame's centre is
measurement noise or a deliberate composition nudge — reproduce it with a `translateX` on
the content wrapper, and disable that shift in the narrow breakpoints or the wrapper
overflows on mobile. But a **large** unexplained offset (≈20px) is a symptom that you
picked the wrong content width: re-derive it from the PNG width instead of papering over it
with a transform.

Hide the scrollbar so it cannot steal width and re-introduce a mismatch:

```python
js("""(()=>{const s=document.createElement('style');
s.textContent='html{scrollbar-width:none!important}::-webkit-scrollbar{display:none!important;width:0!important}';
document.head.appendChild(s);return 1})()""")
```

Assert `document.documentElement.clientWidth === <png width>` before measuring anything.

### 2. Freeze animations before measuring

Entrance/float animations translate elements (a float keyframe can move a card ±11px), so
`getBoundingClientRect()` returns a different box on every call and your "calibration"
chases noise. Inject a kill-switch for the measurement pass:

```python
js("""(()=>{const s=document.createElement('style');
s.textContent='.fc,.blob,[class*=float],.brand-mark{animation:none!important;transition:none!important}';
document.head.appendChild(s);return 1})()""")
```

Measure and calibrate with animations off, then take the **final screenshot with animations
live** so it reflects the real page.

### 3. Measure landmarks in the DOM — never by eye

Read exact boxes from the real browser, and read the same landmarks out of the reference
PNG by pixel scan. Then patch CSS by the exact deltas and re-render. Repeat until every
landmark is within a few px.

```python
js("""(()=>{const o=[];const g=(s,n)=>{const e=document.querySelector(s);if(!e){o.push(n+'=X');return;};
const b=e.getBoundingClientRect();o.push(n+' t='+Math.round(b.top)+' l='+Math.round(b.left)+
' r='+Math.round(b.right)+' w='+Math.round(b.width));};
g('.hero h1','H1');g('.peek-frame','DASH');g('.fc--a03','A03');return o.join('\\n')})()""")
```

In the reference image: a **dark-ink bounding-box scan** locates text (threshold R,G,B all
below ~115); a **white-run scan** locates panels/cards. Recipes in
`references/measurement-and-calibration.md`.

### 4. Localize residual error — per-band MAE, then split text vs background

Whole-page MAE hides where the problem is. Compute MAE per horizontal band (navbar /
eyebrow / headline / form / dashboard) to find the worst band, then split that band into
**text pixels** (reference dark) vs **background pixels** (reference light):

```python
from PIL import Image, ImageChops
d = ImageChops.difference(ref.crop(box), live.crop(box)).convert("L")
mae = sum(d.getdata()) / (d.width * d.height)
```

Typical split: text band MAE ~100-130 (pure font anti-aliasing — **unfixable without the
exact font file**), background band MAE ~20 (gradient/blob mismatch — **fixable**). This
tells you where to spend effort and what to tell the user.

### 5. Verify every `vision_analyze` claim against pixels before acting

Vision review is good for **reading** fine detail (is the eyebrow uppercase? how many spark
lines? is the checkmark filled? is the badge top-right or bottom?). It is unreliable for
**judging** position and equality — in practice it reports differences that do not exist
and misses real ones, and it contradicts itself across calls.

Before acting on a vision claim:

- "element is shifted" → confirm with `getBoundingClientRect` / an ink bounding box
- "colour differs" → sample the pixels at the same coordinate in both images
- "active state differs" → sample both images at that exact pixel
- "element is missing / not there" → query the DOM for it and scan its pixels; vision
  reports present icons and elements as absent whenever the crop it inspects is downscaled
- "too large / too small" → measure the ink bounding box in both images; a 2-up stacked
  comparison makes vision call the lower copy "zoomed in" when the boxes are identical

Use vision to generate hypotheses; act on pixel evidence.

### 6. Report honestly

State the MAE and what causes the residual. "MAE 20, residual is anti-aliasing in the text
band" is true and useful. "100% identical" when the text renders in a different font is
not — see the copyright note below.

## When hand-matching plateaus: the image-as-hero fallback

Hand-building is the right default, but it has a hard floor (unknown font, hand-drawn
doodles, organic gradients). When the user has iterated several times and still says it is
not close — and especially when they propose it themselves — offer this alternative plainly
and implement it if they agree: **paste the reference image as the hero section**.

Expect it to be rejected on sight more often than not: pasted text is not crisp at
non-native widths and the page reads as "just a screenshot". Offer it as an option, never as
the recommended fix, and always back up the hand-built markup first (see the rule below) —
reverting means rebuilding the hero HTML from the surviving CSS.

Result: MAE 0.000000 — identical by definition, not by calibration.

Do it as image **plus an interaction layer**, never a bare `<img>`:

1. Save the reference into `assets/` at full resolution and load it from a plain
   `<img src="...">`. Do **not** wrap it in `<picture>` with a WebP `srcset` (that path can
   hang the browser), and do not ship lossy WebP (it adds MAE ≈ 1). PNG and **lossless**
   WebP both diff to MAE 0; lossless WebP is the smaller file.
2. Overlay a transparent, absolutely-positioned layer sized to the image, with one empty
   `<a>`/`<button>` per interactive element. Measure each element's box in the reference
   PNG and express it as **percentages of the image**, so the hotspots stay aligned when
   the image scales. The email field becomes a real `<input>` with transparent chrome;
   give it a visible text colour and a white background on `:focus`/`:not(:placeholder-shown)`
   so typed text is readable over the image's own placeholder.
3. Keep the real headline in a `.sr-only` block so the page still carries semantic text for
   search engines and screen readers.
4. Hide any hand-built navbar — the navbar is now inside the image.

State the trade-offs once, plainly: the hero is no longer responsive (the layout inside the
image is locked), its text is not selectable or indexable, and editing the copy means
replacing the image. Everything below the hero stays normal HTML/CSS. Full recipe in
`references/image-as-hero-fallback.md`.

## Always-on rules

- **Render at the reference PNG's own pixel width and compare 1:1; verify a centred
  element sits near `png_width/2`. Never invent a content width by subtracting a scrollbar.**
- **Never measure with animations running.** Freeze them, then screenshot live.
- **Never act on a vision claim you have not confirmed with pixels.**
- **Score every change and keep the best-measured version.** Re-render and re-measure after
  each edit; if the number got worse, revert. Vision-guided "fixes" regress more often than
  they help — two vision-suggested arrowhead edits dropped a stroke's pixel match from 71%
  to 30% and 46%, and both had to be undone.
- **Enumerate decorative elements from the reference; never add doodles it does not have.**
  Scan for saturated line pixels outside text/card regions to get the exact set — extra
  arrows and lines read as a different design even when every box matches.
- **When several references are supplied, the specific artwork wins for anything it shows.**
  Sample its pixels for colours and geometry; use a design-system sheet only for what the
  artwork omits (component states, spacing scale). A token list in a sheet is not evidence —
  the hero's own pixels are.
- **Verify in a real browser, and if the browser tool fails, recover it** rather than
  settling for CLI screenshots alone — see `browser-harness-windows` for the launch and
  focus fixes.
- **Never claim "100% identical" while text renders in a different font.** Name the MAE
  and the cause.
- **When hand-matching plateaus and the user asks to paste the reference as the hero, do it
  — but as image + transparent hotspot overlay + `.sr-only` text, never a bare `<img>`.**
  A bare image loses every click target and all semantic text.
- **Back up the hand-built markup (git init, or copy `index.html`) before swapping in the
  image-as-hero.** The swap replaces the hero section; if the user then rejects the image
  and asks for manual again, reverting is otherwise a full reconstruction from the
  surviving CSS alone.
- **Disable full-page decorative overlays (noise/grain, vignette) before any pixel
  comparison.** They add uniform MAE and make a pixel-perfect result look broken.

## Pitfalls

1. **A container's `color`/`stroke` outranks `currentColor` on a child.** A white checkmark
   inside a green circle rendered invisible because `.trust svg{color:brand}` beat the
   child's inherited colour. Fix with a more specific rule on the child
   (`.trust .ck svg{color:#fff}`), not by removing the container rule.
2. **A parent `overflow:hidden` clips glow/shadow positioned outside it.** A bottom glow
   anchored below the hero was invisible until it moved to a pseudo-element of a
   non-clipping ancestor. Check the nearest `overflow` ancestor before debugging a missing
   gradient.
3. **`text-transform` and letter-spacing change measured width.** Fix case/spacing before
   nudging `font-size` — an uppercase eyebrow measures very differently from a lowercase
   one at the same size.
4. **A straight CSS underline looks wrong against a hand-drawn reference.** Use an inline
   SVG path with a slight arc and tapered ends (`preserveAspectRatio="none"`), not a
   `border-radius` bar.
5. **Full-page CDP capture can time out on very tall pages.** Use the Chrome CLI for the
   full-page shot; CDP `Page.captureScreenshot` for the viewport.
6. **Font mismatch is a hard floor.** If the reference's typeface is unknown, text bands
   will never reach MAE < ~40. Ask the user for the font (or the font file) rather than
   grinding on it.
7. **Decorative elements must be counted from the reference, not imagined.** A page with an
   extra doodle arrow, or a missing one, reads as a different design even when every box
   matches. Enumerate them by pixel scan (recipe in the references file) before adding any.
8. **Decide solid vs dashed by pixel gap-scan, not vision.** Vision contradicts itself on
   dash patterns (calls solid "dashed" and vice versa). Sample along the stroke for gaps, or
   view an `Image.NEAREST` 8× zoom — a continuous run of coloured pixels is solid.
9. **An absolutely-positioned overlay with `height:100%` grows to fit its absolute
   children.** One child whose bottom sits past the container pushes every later sibling
   down, and the "dashboard is 8px low" you are chasing is really this. Give the overlay no
   explicit height, or `overflow:hidden`.
10. **Same-specificity CSS: a later rule silently overrides an earlier `animation`/
    `transform`.** `.card{animation:enter}` written after `.card--a{animation:float}` kills
    the float. Confirm the keyframe you intend actually runs with
    `getComputedStyle(el).animationName` in the browser.
11. **A descendant selector for `stroke-dasharray` hits *every* `path`, arrowhead included.**
    `.line--dashed path{stroke-dasharray:8 8}` chopped the arrowhead into dashes, so it read
    as "fragmented/broken". Give the curve path its own class and dash only that
    (`.line--dashed .curve{stroke-dasharray:8 8}`); leave the arrowhead path solid.
12. **Draw the shaft and its arrowhead from one set of measured points, in one coordinate
    system.** Author the curve to *start at the barb vertex* so the join is continuous, then
    confirm the join with a pixel overlay — not by eye. A shaft that begins a few px away
    from the head reads as a detached, floating arrowhead.
13. **A fixed full-page overlay (noise `grain`, vignette) poisons every pixel comparison.**
    An `opacity:.035` grain layer across the viewport added a uniform MAE ≈ 1.2 to every
    cell and made a pixel-perfect hero report MAE 17. Disable it before diffing; a uniform
    whole-image offset in the difference map is the tell.
14. **A whole-image uniform diff means the element is not rendering, not that it is
    misaligned.** Sample pixels in both images before chasing geometry — if every sampled
    pixel equals the page background, the image never painted (check `naturalWidth` *and*
    the pixels; `naturalWidth` alone can be correct while nothing is visible).
15. **A `<picture>` with a WebP `srcset` can hang the browser; lossy WebP adds error.**
    For an exact-match hero ship a plain `<img src="…png">` (or lossless WebP) — PNG and
    lossless WebP both diff to MAE 0, lossy q92 to ≈ 1.

## Copyright

A hand-built page that reproduces another product's design is a **derivative work**.
Deliver it for learning, design research, or personal archiving, and say plainly it must
not be published, hosted, or used commercially. Rewriting the copy does not make it
publishable — the `website-mirroring` skill carries the original-work path in its own
`references/publishable-rebuild.md`.

Shipping the reference file itself (the image-as-hero fallback) is a **stronger** act than a
redraw: you are distributing the original artwork, not an approximation of it.

**Establish provenance before asserting anything.** A reference the user made themselves —
AI-generated artwork, their own design sheet — is their work and carries no third-party
claim; a design sheet shipped alongside it is a token source, not someone else's IP. Ask
who made the artwork, or check whether the brand exists as a real product, before framing
it as derivative. Repeating a copyright warning the user has already told you is wrong is
a real cost: it burns their trust and they will (rightly) push back. State the constraint
once, conditionally, and drop it when the user says the work is theirs.

## Support Files

- `references/measurement-and-calibration.md` — copy-paste recipes: reference landmark
  scans (dark-ink, white-run), decorative-element enumeration and dash/solid detection,
  per-band MAE and text/background split, animation freeze, scrollbar pin, viewport vs
  full-page capture, a calibration worked example, 3D perspective-tilt detection and
  calibration, and testing font candidates by MAE.
- `references/image-as-hero-fallback.md` — the paste-the-reference fallback: when to offer
  it, image encoding (PNG vs lossless WebP), measuring hotspot boxes and the overlay CSS,
  the three verification checks, the pitfalls that cost time, and how to revert to the
  hand-built version (back up first; rebuild the markup from the surviving CSS).
