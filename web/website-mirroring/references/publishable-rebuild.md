# Publishable rebuild — turning a reference into the user's own work

## The rule that decides everything

Changing the content does NOT make a copy publishable. Copyright protects the
**expression** (the code, the prose, the images), and a modified copy is a
**derivative work** — which the rights holder controls exclusively. "I rewrote the
text" is not a defence; it is an admission that the original was the base.

- **May take:** the *idea* — section order, the fact that a hero is followed by a
  product mock, a three-column pricing table, a generic pill button, a 4-step "how it
  works" strip. Layout patterns and functional ideas are not protected.
- **May not take:** the code, the prose, the images, the fonts *as used*, the brand
  identity, and the exact palette.

Trademark is a **separate** right that does not care about the text at all: keeping a
name or logo infringes even with 100% new copy. Third-party marks shown inside the
reference (partner / technology logos) belong to *those* companies, so they must go too.

Fair use is not a licence. It is a defence argued in court, and using the whole of
someone's code for a commercial site essentially never passes it.

## "Can we copy their UI components?" — the question that always comes up

Answer it by the same idea/expression split, at component granularity, because the
user is usually asking about *components*, not the whole page:

- **Unprotected (copy the pattern freely):** an announcement bar, a sticky nav, a hero
  with an inline email capture, a product mock in a rounded panel, a row of 4 KPI cards,
  a status-badge table, a tab strip, a logo marquee, a 2-up comparison list, a stat grid,
  a 3-column pricing table with a "popular" badge, a `<details>` FAQ accordion, a
  multi-column footer, a testimonial carousel. These are industry conventions — an idea
  is not protected, and re-implementing a convention is not copying.
- **Protected (never copy):** their CSS/JS/HTML as written, their asset files, their
  copy, their fonts *as used*, their brand identity, and their exact palette.

**The practical test — put the two pages side by side.** If a layperson could believe
both came from the same company, it is too close. What makes it too close is identical
*colour + type + spacing + assets* together; change the palette and the typeface and you
have already broken the resemblance, because the shared part is only the unprotected
pattern.

So when the user asks to "tiru komponennya" (imitate the components), the correct move is
to add the *pattern* to their own build — fresh markup, own tokens, own copy — and say
plainly which parts are convention and which parts are off-limits. Do not copy the
reference's stylesheet and do not refuse the request as if it were a clone.

**Adding patterns incrementally is normal and safe.** A page can grow one conventional
component at a time (dropdown nav, tabs, chart, carousel, article cards) as long as each
is written fresh against the project's own tokens and passes the forbidden-string audit
below. Re-run the audit after each addition — a new component is the easiest place for a
stray copied string or asset path to sneak back in.

## Procedure

1. **Extract the skeleton, not the skin.** From the mirror, write down the section order
   and each section's *purpose* (hero states the value; mock proves it exists; feature grid
   enumerates capabilities; pricing qualifies the buyer; FAQ removes objections). Then work
   from that list, not from the mirror's markup.
2. **Write the code fresh.** New HTML, new CSS, new tokens. A licensed starting point
   (Tailwind, shadcn/ui) is safer than blank slate — but only if you can read its licence.
3. **Rewrite 100% of the copy** from the product's own source of truth (the PRD, the
   brief, the feature list) — never paraphrase the reference's sentences.
4. **Replace every asset.** Safe defaults:
   - icons → **Lucide** (ISC licence). Inline the SVG and keep a per-icon comment naming
     the source so the licence notice travels with the file.
   - fonts → a family with an explicit web licence, e.g. **SIL OFL 1.1** (Plus Jakarta
     Sans, Inter, Source Sans); or self-host and drop the CDN link.
   - imagery → own screenshots, or a permissively licensed stock source.
   - logo → redraw the user's supplied brand mark as **clean inline SVG**; never crop or
     embed the raster they handed you. See "Brand mark as SVG" below.
5. **Remove every brand and re-pick the palette.** Own name, own logo mark, own accent
   hex. A distinct palette is cheap and removes any "same design" argument.
6. **Invent the sample data.** Names, amounts and records inside a product mock must be
   obviously fictional — never real people or real tenants carried over from the reference.

## Brand mark as SVG

When the user supplies a brand-identity PNG and says "use this logo", do not crop the
bitmap into an `<img>` — it blurs when scaled and drags the sheet's background with it.
Redraw the mark as a small inline SVG with `stroke="currentColor"`, so one file serves
every size and colour context (white-on-green, dark mode, favicon).

- **Read the geometry off pixels, not vision alone.** Crop and upscale the icon with PIL
  (`Image.resize(..., LANCZOS)`) and confirm each feature with a pixel probe (count
  coloured pixels per row/column to get the bounding box). Vision is unreliable on shape —
  it will place the same chimney on the left in one pass and the right in the next.
- **Ship two variants, sized deliberately.** Interior detail that reads at 150px merges
  into a blob below ~24px. Screenshot the mark at 40/32/24/20/16px and look: keep the full
  mark for ≥32px and a simplified one (interior detail dropped, stroke thickened) for the
  navbar, app-bar and favicon. Standard brand practice, not a compromise.
- **Validate every `.svg` parses** (`xml.dom.minidom.parse`) before referencing it — a
  malformed SVG renders as a broken-image icon with no console error. A broken `<img>` in
  your own test page is usually a wrong `src`, not a bad file: render the SVG directly.
- **Export the set a real brand needs:** full mark, simplified small mark, reversed/white
  mark, horizontal lockup (mark + wordmark), and a favicon wired with
  `<link rel="icon" type="image/svg+xml">`.

## Interactive components in a fresh build

When you add dropdowns, tabs, a carousel or a chart to a rebuilt page, keep them
vanilla and degrade gracefully — the artifact must still read with JavaScript off.

**Never gate content visibility on a JS-set class without a no-JS fallback.** An
`opacity: 0` entrance animation that JS is supposed to reveal is invisible — the whole
section, forever — if the script fails, is blocked, or is slow. Set the flag from
`<head>` and scope the hiding rule to it, so the default state is visible:

```html
<script>document.documentElement.classList.add("js");</script>
```
```css
.js .fc, .js .peek-frame { opacity: 0; transform: translateY(18px); }
.fc.is-in, .peek-frame.is-in { opacity: 1; }
```

Verify by rendering once with JavaScript disabled and confirming the content is present.
A reveal-on-scroll with no fallback is the single easiest way to ship a blank section.

- **A nav dropdown must become an open list on mobile, not a hover popover.** Hover has
  no meaning on touch. Inside the `@media (max-width: ...)` block that reveals the mobile
  menu, override the drop panel to `position: static` with `opacity/visibility` forced on,
  so it renders as an indented list inside the menu. Ship `aria-expanded` on the toggle.
- **Prefer a `<details>`/`<summary>` or a CSS-only control for the first pass.** Native
  elements carry the open/closed state and keyboard behaviour for free; reach for JS only
  for the parts that genuinely need it (filtering a table, advancing a carousel).
- **A carousel counter in the markup is stale the moment JS runs.** Set the initial
  "1 dari 3" text to the real first state (index 1, prev button `disabled`) in the HTML so
  it is correct before hydration and in a no-JS render — a wrong initial value reads as a
  bug even after the script fixes it.
- **A horizontal carousel's off-screen slides WILL appear in an overflow probe.**
  `getBoundingClientRect().right` for slides 2 and 3 exceeds `clientWidth`, so a naive
  "find elements past the viewport edge" check reports the carousel as broken. It is not —
  the track scrolls by design. Exclude descendants of a deliberate `overflow-x: auto`
  container (or the carousel track) from the overflow list, and confirm the page-level
  `documentElement.scrollWidth === clientWidth` instead.
- **Hero decoration is pure positioning — budget the side columns or it collides with
  the copy.** Floating cards around a centred hero must sit in reserved outer columns, or
  a wide headline runs straight through them. Cap the copy column (`max-width` on the
  inner wrapper, ~730px) and make the stage span the full section
  (`.stage { position: absolute; inset: 0; }`) so cards anchor to the section, not to a
  collapsed wrapper. Hide the decorative layer below the breakpoint where the columns
  disappear, and verify with a per-element `fits` probe that the headline box and each
  card box do not intersect.
- **A tab strip that only toggles a class is a lie.** Wire it to actually filter rows
  (`row.hidden = row.dataset.g !== want`) and give the tabs `role="tablist"` +
  `aria-selected`; verify by clicking the second tab and asserting the visible row count
  changed, not by looking at the highlight.

## Compliance audit — run it before saying "publishable"

Grep the finished files for the reference's fingerprints; every count must be zero.

```python
both = html + css
forbidden = [
    "<ref-brand>", "<ref-author>", "<ref-domain>",          # their identity
    "cursor", "claude", "chatgpt", "openai", "gemini",   # third-party marks
    "/logos/", "/screens/", "/customers/", "<their-cdn>",  # their assets
    "<ref-font-1>", "<ref-font-2>",                        # their fonts
]
hits = {f: both.lower().count(f) for f in forbidden if f.lower() in both.lower()}

assert both.lower().count("<their-accent-hex>") == 0   # their palette must not survive
assert html.count("<img") == 0 or "<their-cdn>" not in html  # no external imagery
```

**Expect false positives and judge them — do not just delete the match.** `cursor`
appears in the CSS property `cursor: pointer`; a licence name such as `lucide` appears in
your own attribution comments and must stay. Print surrounding context for every hit.

Then name the licences you *did* use (README or header comment) so the next person can
verify the chain.

## Report shape

State in a short table: what was reused (layout pattern — an idea), what is new (code,
copy, assets, palette), which third-party licences are now in play, and what the user must
still supply (real URLs; a privacy policy if the product stores personal data). Do not
claim "100% original" without the audit output behind it.
