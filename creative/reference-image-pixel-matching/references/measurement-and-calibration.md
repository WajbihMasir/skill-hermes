# Measurement & Calibration Recipes

Copy-paste recipes for matching a hand-built page to a reference image. All snippets run
inside `execute_code` (Pillow) or `browser_exec` (CDP + `js`).

---

## 1. Pin the render width to the reference PNG's own width

A screenshot is captured at the viewport size, so the PNG's pixel width is the capture
width. Render at that width and compare 1:1. Confirm by checking a centred element's centre
sits near `png_width/2`.

```python
from PIL import Image
ref = Image.open(REF_PATH).convert("RGB")

def centered_span(im, y, thr=250, x0=60, x1=1500):
    """widest run of near-white pixels on row y"""
    px = im.load()
    xs = [x for x in range(x0, x1) if all(c > thr for c in px[x, y])]
    if not xs:
        return None
    runs, cur = [], [xs[0]]
    for a, b in zip(xs, xs[1:]):
        if b - a <= 6:
            cur.append(b)
        else:
            runs.append(cur); cur = [b]
    runs.append(cur)
    g = max(runs, key=len)
    return g[0], g[-1]

l, r = centered_span(ref, 700)
print("center", (l + r) / 2, "png_width/2", ref.width / 2)
```

A 1536-wide PNG whose dashboard frame spans x 208–1327 (centre 767.5 ≈ 768) → render at
**1536**. Do **not** subtract a scrollbar to invent a smaller "content width" — that
produced a spurious 1503 from a 1536 PNG and a `translateX(22px)` that broke every element.
Subtract a scrollbar only if the image visibly contains one.

---

## 2. Freeze animations for the measurement pass

```python
js("""(()=>{const s=document.createElement('style');s.id='noanim';
s.textContent='.fc,.blob,.spark,[class*=float],.brand-mark,.fc-line path{animation:none!important;transition:none!important}';
document.head.appendChild(s);return 1})()""")
```

Remove `#noanim` (or reload) before the final screenshot so the delivered image shows the
real page with motion.

---

## 3. DOM landmark readout

```python
print(js("""(()=>{const o=[];
const g=(s,n)=>{const e=document.querySelector(s);if(!e){o.push(n+'=MISSING');return;};
  const b=e.getBoundingClientRect();
  o.push(n+' t='+Math.round(b.top)+' b='+Math.round(b.bottom)+' l='+Math.round(b.left)+
         ' r='+Math.round(b.right)+' w='+Math.round(b.width));};
['.eyebrow','.hero h1','.hero .lede','.field','.peek-frame','.fc--a03','.fc--wa']
  .forEach(s=>g(s,s));
return o.join('\\n')})()"""))
```

Compare each against the same landmark read out of the reference PNG (section 4), patch
CSS by the delta, re-render, repeat until every box is within a few px.

---

## 4. Reference landmark scans (Pillow)

### 4a. Text — dark-ink bounding box

```python
def ink_bbox(im, box, thr=115):
    px = im.load(); pts = [(x, y) for y in range(box[1], box[3])
                          for x in range(box[0], box[2])
                          if all(c < thr for c in px[x, y])]
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)
```

Use it to compare a headline line's **left edge and width** (a width match with a left-edge
mismatch means a horizontal offset, e.g. a centered block that is not centered in the
reference frame — see section 6).

### 4b. Coloured text (green emphasis word)

```python
def green_bbox(im, box, lo=25, hi=210):
    px = im.load(); pts = [(x, y) for y in range(box[1], box[3])
                          for x in range(box[0], box[2])
                          if px[x, y][1] > px[x, y][0] + lo
                          and px[x, y][1] > px[x, y][2] + 15
                          and px[x, y][1] < hi]
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)
```

### 4c. Panels / cards — widest white run

```python
def white_span(im, y, thr=250, x0=60, x1=1500):
    px = im.load()
    xs = [x for x in range(x0, x1) if all(c > thr for c in px[x, y])]
    return (xs[0], xs[-1]) if xs else None
```

### 4d. Solid saturated glyph vs pale tint

Count strongly-saturated pixels in an icon box. A **pale tint + coloured glyph** yields a
handful of saturated pixels; a **solid block** yields hundreds.

```python
def saturated(im, box, d=60):
    px = im.load()
    n = 0
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            c = px[x, y]
            if max(c) - min(c) > d:
                n += 1
    return n
```

---

## 5. Per-band MAE and text/background split

```python
from PIL import Image, ImageChops
ref = Image.open(REF_PATH).convert("RGB").crop((0, 0, W, H))
live = Image.open(LIVE_PATH).convert("RGB")

def mae(box):
    d = ImageChops.difference(ref.crop(box), live.crop(box)).convert("L")
    data = list(d.getdata())
    return sum(data) / len(data)

for box, name in [((0,0,W,80),"navbar"), ((0,80,W,190),"eyebrow"),
                  ((0,190,W,480),"headline+cards"), ((0,620,W,H),"dashboard"),
                  ((0,0,W,H),"TOTAL")]:
    print(f"{name:18s} {mae(box):5.1f}")
```

Split the worst band into text vs background to see what is fixable:

```python
px_ref, px_d = ref.load(), ImageChops.difference(ref, live).convert("L").load()
text, bg = [], []
for y in range(190, 480):
    for x in range(0, W, 2):
        (text if all(v < 140 for v in px_ref[x, y]) else bg).append(px_d[x, y])
print("text MAE", sum(text)/len(text), "| bg MAE", sum(bg)/len(bg))
```

Text ~100-130 = font anti-aliasing, unfixable without the exact font. Background ~20 =
gradient mismatch, fixable. Act on the background; tell the user about the text floor.

---

## 6. Calibration worked example

Symptom: every element is a few px off and nothing you nudge converges.

1. Note the reference PNG is 1536 wide → render at **1536** (no scrollbar in a headless
   shot), compare 1:1.
2. Check a centred anchor: dashboard frame x 208–1327 → centre 767.5 ≈ 1536/2 ✓. Headline
   line-1 ink x 469–1078 → centre 773.5, only +5.5px off centre — small, not a global shift.
3. Now per-element deltas are small and meaningful (a few px) and the remaining work is
   real calibration (font size, line-height, spacing), not chasing a global offset.

Do **not** repeat the trap of deriving content width 1503 from a frame centre and adding
`translateX(22px)`: the offset was an artefact of the wrong width and it shifted every
element the wrong way. A genuine composition offset (the hero deliberately nudged off the
frame's centre) is reproduced with `transform: translateX(...)` on the content wrapper,
disabled in narrow breakpoints.

When one CSS value moves a landmark, the mapping is usually linear even under a
`perspective`/`rotateX` transform: probe two or three values and interpolate instead of
re-guessing one at a time. (`margin-top` 37 → dashboard y 652, 45 → 660, 53 → 668, so the
answer is 45.)

---

## 7. Capture: viewport vs full page

Viewport (exact, fast):

```python
r = cdp('Page.captureScreenshot', format='png', captureBeyondViewport=False,
        _response_timeout=60)
open(out, "wb").write(base64.b64decode(r["data"]))
```

Full page of a very tall document — CDP `captureBeyondViewport` can time out; use the
Chrome CLI instead:

```bash
chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1503,9300 --virtual-time-budget=15000 \
  --screenshot="out.png" "file:///C:/path/index.html"
```

---

## 8. Browser recovery

`browser_exec` checks CDP *before* your code runs, so a dead browser aborts the call
before any recovery code executes. Launch Chrome from a terminal instead, then retry the
`browser_exec` call:

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/<you>/AppData/Local/hermes/chrome-automation" \
  --no-first-run --no-default-browser-check --window-size=1536,1024 about:blank
```

Confirm with a socket/HTTP probe, then re-run. See `browser-harness-windows` for the full
launch, focus, and stale-daemon fixes.

---

## 9. Decorative elements: enumerate, then classify stroke style

To find every doodle/arrow/line the reference has — and to confirm you have not invented
one — scan for saturated *line* pixels while masking out the text and card regions:

```python
def line_map(im, x0, x1, y0, y1, step=6, text_boxes=(), card_boxes=()):
    px = im.load()
    def masked(x, y):
        if any(a <= x <= b and c <= y <= d for a, c, b, d in text_boxes + card_boxes):
            return True
        r, g, b = px[x, y]
        return not (g > r + 20 and g > b + 12 and g < 215)   # green stroke
    for y in range(y0, y1, step):
        row = ''.join('.' if masked(x, y) else '#' for x in range(x0, x1, step))
        if '#' in row:
            print(f"{y:4d} {row}")
```

Clusters of `#` outside the masked boxes are the doodle set. Then classify each stroke as
solid or dashed by counting gaps along it:

```python
def stroke_gaps(im, x0, x1, y0, y1):
    px = im.load()
    cols = {x for x in range(x0, x1)
            if any(px[x, y][1] > px[x, y][0] + 20 and px[x, y][1] > px[x, y][2] + 12
                   and px[x, y][1] < 215 for y in range(y0, y1))}
    if not cols:
        return None
    lo, hi = min(cols), max(cols)
    gaps = sum(1 for x in range(lo, hi + 1) if x not in cols)
    return gaps, lo, hi          # gaps == 0 → solid; a run of gaps → dashed
```

Back it with an `Image.NEAREST` 8× crop — nearest-neighbour, **not** LANCZOS, or the
smoothing hides the gaps:

```python
c = im.crop(box)
c.resize((c.width * 8, c.height * 8), Image.NEAREST).save("zoom.png")
```

Do this for every stroke before writing any SVG; then match the reference's own style
(solid stays solid, dashed gets `stroke-dasharray`), not what a prompt or the design sheet
claims the style is.

---

## 10. Reconstruct a curved stroke from its pixels

Eyeballing a bezier wastes iterations. Extract the reference stroke's **centreline** and
build the path through those points.

```python
import collections
px = im.load()
by_row = collections.defaultdict(list)
for y in range(y0, y1):                       # curve only — stop before the arrowhead
    for x in range(x0, x1):
        r, g, b = px[x, y]
        if g > r + 12 and g > b + 2 and 150 < g < 240:
            by_row[y].append(x)
for y in sorted(by_row):                      # one (centre-x, y) per row = the spine
    xs = by_row[y]
    print(y, (min(xs) + max(xs)) // 2)
```

Fit a cubic through the first/middle/last points, express them **relative to the stroke's
bounding-box origin**, and set `preserveAspectRatio="none"` on the SVG so the viewBox
scales to the CSS box.

For the arrowhead: sample the row-widths in the head region to tell an **open V** (two
narrow runs meeting at a vertex) from a **filled chevron** (one wide contiguous run). Mask
out adjacent cards first — a green badge or icon inside a nearby card is *not* part of the
arrowhead and will inflate the measured width by 3× and send you the wrong way.

---

## 11. Score a stroke with a pixel-overlap metric, not vision

Vision cannot reliably judge whether two curves match. Use set overlap of the two strokes'
pixels with a small tolerance:

```python
def stroke_px(px, box):
    return {(x, y) for y in range(box[1], box[3]) for x in range(box[0], box[2])
            if px[x, y][1] > px[x, y][0] + 12 and px[x, y][1] > px[x, y][2] + 2
            and px[x, y][1] < 240}

R, L = stroke_px(ref.load(), BOX), stroke_px(live.load(), BOX)
RAD = 3
precision = sum(any((x+dx, y+dy) in R for dx in range(-RAD, RAD+1)
                    for dy in range(-RAD, RAD+1)) for x, y in L) / max(1, len(L))
recall    = sum(any((x+dx, y+dy) in L for dx in range(-RAD, RAD+1)
                    for dy in range(-RAD, RAD+1)) for x, y in R) / max(1, len(R))
print(f"precision {precision:.0%}  recall {recall:.0%}")
```

Read it as: **precision** = how much of your stroke sits on the reference (too low → you
are drawing where nothing exists, e.g. wrong position or wrong curvature); **recall** =
how much of the reference you cover (too low → your stroke is too short, too thin, or a
missing piece). A stroke that is perfectly placed but 40% too short scores 100% / 60%.
Always measure inside a box that excludes neighbouring cards and badges.

---

## 12. Detect and calibrate a 3D perspective tilt

A "3D screen" panel in the reference (a dashboard mockup tilted back) is **not** a flat
rectangle: its width grows from top to bottom. A flat panel — or a token `rotateX(.7deg)` —
will never match. Measure the panel's width at several rows:

```python
def span(im, y, thr=249, x0=120, x1=1470):
    px = im.load()
    xs = [x for x in range(x0, x1) if all(c > thr for c in px[x, y])]
    return (xs[0], xs[-1], xs[-1] - xs[0]) if xs else None

for y in range(660, 1024, 60):
    print(y, span(ref, y))
```

Reference dashboard: width 1081 at y660 → 1194 at y1020, i.e. it **widens ~113px** over
360px of height. Reproduce with `transform: perspective(<d>px) rotateX(<a>deg)` and
`transform-origin: top center`. The knobs interact:

- `rotateX` angle sets how much the bottom widens;
- `perspective` distance sets the strength (smaller = stronger);
- frame `max-width` sets the absolute scale (the *top* edge width).

Calibrate by matching the reference's **spread** (bottom − top) first, then its top width.
Worked values: `perspective(430px) rotateX(3.6deg)` with `max-width: 1216px` matched a
1081→1194 spread. Also update any `prefers-reduced-motion` override that re-declares the
same transform, or the tilt silently disappears for reduced-motion users.

---

## 13. Test font candidates by MAE before committing to a font hunt

When the reference typeface is unknown, do not guess-and-check one font at a time. Render
one headline line in N candidate fonts at the reference's size and position, score each
against the reference text with MAE (section 5), and take the lowest.

```python
# _fonttest.html: one absolutely-positioned block per font at the reference's x/size
fonts = ["Plus Jakarta Sans", "Nunito", "Poppins", "DM Sans", "Manrope", "Outfit", "Figtree"]
# screenshot it, then for each block search a vertical window (baselines differ):
best = min((mae(ref_line, block.crop_at(dy)), dy) for dy in range(-40, 41))
```

Two outcomes are both useful:

- one candidate clearly lowest → adopt it;
- all candidates within ~1 MAE of each other → **the font is not your dominant error**;
  stop hunting and spend the effort elsewhere. (Swapping the site font for the best
  candidate moved total MAE by only 0.1.)

Confirm a candidate actually loaded — use `document.fonts.load('700 60px "<name>"')` +
`document.fonts.ready`, or canvas `measureText`. A font that failed to load measures as the
fallback, so every candidate reads identical (all ~1523px is the tell).
