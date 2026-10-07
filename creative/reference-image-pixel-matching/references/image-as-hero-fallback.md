# The image-as-hero fallback

When a hand-built page cannot close the gap to the reference — unknown font, hand-drawn
doodles, organic gradients — pasting the reference image as the hero gives an exact match.
This file is the recipe.

## When to offer it

- The user has iterated 2-3+ times and still says it is not close.
- The reference contains hand-drawn or organic art you cannot reproduce from primitives.
- The user proposes it themselves ("just paste the image").

Say the trade-offs before doing it; do not silently swap the deliverable.

Expect it to be **rejected on sight** about half the time: pasted text is not crisp at
non-native widths and the result reads as "just a screenshot". Offer it as one option, never
as the recommended fix, and **back up the hand-built markup first** (`git init`, or copy
`index.html` and `styles.css` to a dated sibling) — the swap replaces the hero section, and
if the user then says "manual again" you are rebuilding the hero HTML from the surviving CSS
alone (the CSS usually survives; the markup does not).

## 1. Add the image

```python
from PIL import Image
im = Image.open(REF_PATH).convert("RGB")
im.save("assets/hero.png", "PNG", optimize=True)               # MAE 0
im.save("assets/hero.webp", "WEBP", lossless=True, method=6)   # MAE 0, smaller
```

Markup — a plain `<img>`, no `<picture>`:

```html
<img class="shot-img" src="assets/hero.png" alt="…full description of the hero…"
     width="1536" height="1024" fetchpriority="high" decoding="async">
```

## 2. Measure the hotspots

Read each interactive element's box straight out of the reference PNG, then store it as a
percentage of the image width/height.

```python
px = im.load(); W, H = im.size

def green_bbox(x0, x1, y0, y1):           # a green button, e.g. "Coba gratis"
    pts = [(x, y) for y in range(y0, y1) for x in range(x0, x1)
           if px[x, y][1] > px[x, y][0] + 35 and px[x, y][1] > px[x, y][2] + 20
           and px[x, y][1] > 100]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)

l, r, t, b = green_bbox(1150, 1400, 15, 80)
print(f"left {l/W:.4f} top {t/H:.4f} width {(r-l)/W:.4f} height {(b-t)/H:.4f}")
```

White panels (the email field) via a white-run scan; dark text runs locate nav links.

## 3. Overlay CSS

```css
.hero-shot  { position: relative; }
.shot-frame { position: relative; max-width: 1536px; margin-inline: auto;
              line-height: 0; overflow: hidden; }
.shot-img   { display: block; width: 100%; height: auto; }
.shot-hot   { position: absolute; inset: 0; }        /* tracks the image box */
.hot        { position: absolute; display: block; border-radius: 999px;
              background: transparent; }
.hot--nav-cta { left: 79.10%; top: 2.34%; width: 8.86%; height: 4.40%; }
/* …one rule per measured element… */

/* email: a real input, invisible chrome, readable on focus */
.hot--form input { flex: 1; height: 100%; border: 0; background: transparent;
                   color: #16221d; caret-color: var(--brand); }
.hot--form input:focus,
.hot--form input:not(:placeholder-shown) { background: #fff; }
```

Because the hotspots are percentages, they stay aligned when the image scales down.

## 4. Verify — three checks

1. **Image rendered at natural size.** Assert `img.naturalWidth` *and* sample pixels; a
   uniform whole-image colour offset means the image is not showing and you are looking at
   the page background.
2. **Hotspots are hit-testable.** `document.elementFromPoint(cx, cy)` at each element's
   centre must return your `.hot`, not the image.
3. **Pixel comparison is MAE 0.** Screenshot at the image's exact size and diff:

```python
from PIL import ImageChops
d = ImageChops.difference(ref, live).convert("L")
data = list(d.getdata())
print(sum(data)/len(data), max(data))       # expect 0.0, 0
```

## Pitfalls that cost time

- **A full-page fixed overlay (noise `grain`, vignette) poisons the diff.** An
  `opacity:.035` fixed grain layer across the viewport added a uniform MAE ≈ 1.2 to every
  cell and made a pixel-perfect hero report MAE 17. Disable it before comparing; find it
  with `getComputedStyle` on the suspected layer, or just diff and look for a uniform
  whole-image offset.
- **`<picture>` + WebP `srcset` can hang Chrome.** Ship a plain `<img src="…png">`.
- **Lossy WebP adds error** (MAE ≈ 1 at q92). PNG and lossless WebP are both MAE 0;
  lossless WebP is the smaller file.
- **CDP `Page.captureScreenshot` can time out while the browser is flaky.** The Chrome CLI
  at the exact window size is a reliable substitute for the comparison shot:

```bash
chrome --headless=new --disable-gpu --hide-scrollbars --user-data-dir=/tmp/cc \
  --window-size=1536,1024 --virtual-time-budget=20000 --screenshot=out.png \
  "file:///C:/path/index.html"
```

## Legal note specific to this fallback

Shipping the exact artwork is a different act from shipping a derivative: you are
distributing the original file, so the risk is strictly higher than a redraw. Record this in
the README and state it once. If the user says the artwork is their own (or AI-generated for
them), accept it and stop repeating the warning — but note that copyright status of AI
output varies by jurisdiction, so for public/commercial use they should confirm they hold
the rights.
