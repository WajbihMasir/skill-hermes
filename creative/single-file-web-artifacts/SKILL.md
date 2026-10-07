---
name: single-file-web-artifacts
description: "Build and verify single-file HTML artifacts in a browser."
version: 0.1.0
author: Shalahuddin, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, css, landing-page, mockup, verification, accessibility, browser]
    related_skills: [claude-design, cdp-browser-attach, dogfood]
---

# Single-File Web Artifacts

Produce a self-contained HTML file (inline `<style>` + `<script>`, no build step) that
opens straight in a browser — landing pages, mockups, prototypes, decks. Covers the two
halves a future session gets wrong: making the design provably NOT a copy of the user's
existing artifacts, and verifying the rendered page in a real browser before claiming it
works.

Design taste and composition live in `claude-design`; section order and copy in
`landing-page-design`; the UI-rule database in `ui-ux-pro-max`. This skill is the
build + verify loop wrapped around them.

**If the user wants the page 100% identical to a live site, do not hand-build it here** —
download the real HTML/CSS/JS/assets and serve them locally (`website-mirroring`). A
recreation you wrote by eye always drifts in type metrics, spacing rhythm and icon shapes;
mirroring the actual files is exact.

**If the user points at a site as a layout reference but needs to PUBLISH the result**,
this is the right skill (fresh code) — but follow the compliance procedure in
`website-mirroring` → `references/publishable-rebuild.md`: take only the section
*structure*, write all copy and assets yourself, and run the forbidden-string audit before
claiming it is publishable. Editing a downloaded copy does not make it publishable.

**If the reference is an IMAGE (screenshot, hero PNG, Figma export) and the user wants the
page to match it pixel-accurately**, this skill still builds it — but verify by measurement,
not by eye: `reference-image-pixel-matching` has the procedure (derive the reference's true
content width first, freeze animations, compare DOM boxes against pixel scans, read residual
MAE per band).

## When to Use

- User asks for a "mockup", "landing page", "single file", or an HTML prototype
- User says the new design must not resemble an existing one
- You just wrote an HTML artifact and are about to say it is done
- Don't use for: a repo implementation in the project's real stack — build in the stack

## Deliverable Contract

- ONE file, self-contained: CSS in `<style>`, JS in `<script>`, no build step.
- One `<link>` to Google Fonts is fine; no other network dependency.
- Never overwrite an existing artifact the user may still want — pick a NEW filename.
- Verify before reporting. "Looks right" is not a result; probe output is.

## Step 0 — Get a real browser

Verification needs a live page. If `browser_exec` fails with a CDP-unreachable error,
start a dedicated automation Chrome and retry (full setup in `cdp-browser-attach`):

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="$LOCALAPPDATA/hermes-automation-chrome" \
  --headless=new --disable-gpu --no-first-run about:blank
```

Run it as a background process, then confirm `curl -s http://127.0.0.1:9222/json/version`
answers before driving it. Load the artifact with `new_tab("file:///<abs-path>")`.

**If `browser_exec` refuses the artifact's URL** (`Blocked: URL targets a private or
internal address` for `file://` or `127.0.0.1`, or a CDP-unreachable error), do not
conclude the artifact is untestable. Drive the Chrome CLI directly instead — the same
`--dump-dom` / `--screenshot` flags work without the browser tool:

```bash
# exact layout numbers: inject a probe that writes to document.title, read it back
chrome --headless=new --disable-gpu --window-size=390,844 \
  --virtual-time-budget=5000 --dump-dom "file:///C:/path/artifact.html" 2>/dev/null \
  | grep -o '<title>M|[^<]*'
# or a visual pass
chrome --headless=new --disable-gpu --hide-scrollbars --window-size=1440,2600 \
  --virtual-time-budget=10000 --screenshot="out.png" "file:///C:/path/artifact.html"
```

`--virtual-time-budget` lets entrance animations settle before capture. For a page whose
bundled ES modules or woff2 fonts are CORS-blocked on `file://`, serve it over HTTP
(`python -m http.server`) and point Chrome at `http://127.0.0.1:PORT/`.

## Procedure A — Prove non-mimicry

Run this whenever the user says the new design must not resemble an existing one.

1. **Read the prior artifacts' tokens — do not guess them:**
   `grep -oE '\-\-[a-z0-9-]+:\s*#[0-9a-fA-F]{3,6}' old.html` and
   `grep -oE 'family=[A-Za-z+]+' old.html`. Record background, accent hexes, font families.
2. **Invert on at least three axes:** flip the background value (dark ↔ light), move the
   accent hue, change the display type family. Two prior dark builds → build light.
3. **Assert it:** grep the new file for each old accent hex; it must return zero.
4. **Report the diff as a small table** (old bg / accent / font vs new) so the claim is
   checkable rather than asserted.

Skipping step 1 is what produces "this looks the same" — the model reuses memorised hexes
and fonts unless the old values are read first and explicitly ruled out.

## Procedure B — Verify the rendered page

Run the probe in `scripts/audit-page.js`, then fix what it reports.

```python
# browser_exec
goto_url("file:///C:/path/to/artifact.html"); wait_for_load()
js("window.__errs=[];addEventListener('error',e=>__errs.push(e.message))")
# for each viewport:
cdp('Emulation.setDeviceMetricsOverride', width=390, height=844, deviceScaleFactor=2, mobile=True)
print(js(open(r"<skill-dir>/scripts/audit-page.js").read()))
```

Check, in this order:

1. **Horizontal scroll** — `scrollWidth > clientWidth` must be false at 390px AND 1440px.
2. **Overflow culprits** — the probe names the element; fix the element, not the symptom.
3. **Contrast** — every text/background pair ≥ 4.5:1 (≥ 3:1 large/bold), measured.
4. **Tap targets** — interactive elements ≥ 44×44px at mobile width.
5. **Console errors** — zero.
6. **Interactions actually work** — click the primary control and assert the resulting DOM
   text changed to the expected value.
7. **Look at it** — `capture_screenshot()` + `vision_analyze` to confirm the design intent
   landed and nothing overlaps.

## Procedure C — Motion (optional: gate it, or don't ship it)

A static page is a fine result. If you add animation, all three gates are
mandatory — a looping animation without them is a liability, not polish:

1. **Reduced motion** — `@media (prefers-reduced-motion: reduce)` disables every
   animation AND lands on a static, still-informative frame (the first scene of a
   loop, not a blank region).
2. **Pause toggle** — a control with `aria-pressed` sets `.motion-paused` on
   `<html>` → `.motion-paused *{animation-play-state:paused!important}`.
3. **Progressive enhancement** — reveal/entrance motion keeps content visible by
   default and hides it only inside `@supports (animation-timeline: view())`.
   Prefer CSS scroll-driven animation over a JS `IntersectionObserver`.

A multi-scene "film" (cross-fading terminal/scan states) is the highest-value
motion for a product hero. Build it from one keyframe per scene with staggered
`animation-delay`, and confirm at every timeline point that **exactly one** scene
is visible. Recipes for the film, the scroll-driven draw, and freezing a frame to
inspect it are in `references/motion-verification.md`.

## Pitfalls

1. **Never gate visibility on a JS observer.** `.reveal{opacity:0}` plus an
   `IntersectionObserver` that adds `.in` leaves content permanently invisible when
   the observer is blocked, throttled, or unsupported. Hide content only inside
   `@supports (animation-timeline: view())` so the default is visible.
2. **Animations are frozen in background/headless tabs, and `requestAnimationFrame`
   never fires there.** `getComputedStyle().opacity` returns the frozen frame, so you
   cannot measure a running animation — pause and seek it instead
   (`el.getAnimations().forEach(a=>{a.pause();a.currentTime=t})`). For the same
   reason, never toggle a class from inside rAF; add it synchronously or the state
   (and its CSS transition) is skipped in a throttled tab.
3. **A vision model misreads animated or multi-scene UI.** It merges frames that
   never coexist and reports overlaps, ghost text, or "empty" regions the DOM
   disproves. Confirm any visual claim with `getBoundingClientRect()` / computed
   styles before restructuring working markup.
4. **On Windows, Chrome headless cannot write `--screenshot=` into the user
   profile directory** (`Failed to write file ... Access is denied`). Point the
   output at `%LOCALAPPDATA%\Temp\<dir>\shot.png`.
5. **An inline `style="..."` attribute beats a media query.** `style="min-width:460px"` in
   the HTML is not overridable by `@media` — it outranks the stylesheet, so the breakpoint
   silently loses. Move the value into a class. This is the usual cause of a stubborn
   mobile horizontal scroll.
6. **Do not trust an eyeballed colour judgement — measure it.** Vision reviewers report
   contrast differences that do not exist and miss ones that do. Compute the ratio from
   `getComputedStyle().color` against the effective background (walk ancestors until a
   non-transparent background).
7. **Colour alone is not a signal (WCAG 1.4.1).** A red-vs-green outcome needs a text or
   glyph label too (`✕ FUNDS LOST` / `✓ FUNDS INTACT`) plus a non-colour difference.
8. **Do not report "0 slop" from an audit you scored higher.** State the score and which
   tells fired, and mark a fired tell a false positive only with the reason. A
   confidently-clean claim a reviewer can disprove is worse than the finding itself.
9. **Grep the source before "fixing" a page artefact.** A junk prefix in `document.title`
   or an unexpected element often comes from a browser extension or the automation
   profile, not the file — grep first; if it is absent there, it is not yours.
10. **Honour `prefers-reduced-motion`.** Any entrance or looping animation needs a
    reduced-motion block that lands on the final state.
11. **A default `browser_exec` viewport can be narrow** (e.g. 762px). Set the width you
    intend to test with `Emulation.setDeviceMetricsOverride` instead of assuming desktop.

## Verification Checklist

- [ ] One self-contained file, new filename, existing artifacts untouched
- [ ] Probe run at 390px and 1440px: no horizontal scroll, no overflow culprits
- [ ] Heading sequence is H1→H2→H3 with no skipped levels; exactly one `h1`
- [ ] All text ≥ 4.5:1 (measured); tap targets ≥ 44px
- [ ] Zero console errors; primary interaction asserted to change DOM state
- [ ] `capture_screenshot` + `vision_analyze` reviewed (frozen frame if animated)
- [ ] Non-mimicry asserted by grep when the user asked for it
- [ ] Audit/slop score reported honestly, including fired tells
- [ ] If animated: reduced-motion + pause toggle + progressive enhancement all present

## Support Files

- `scripts/audit-page.js` — browser probe returning JSON: viewport, horizontal-scroll flag,
  overflow culprits (with their inline-style text), measured contrast failures, small tap
  targets, images missing `alt`, `h1` count, and reduced-motion support. Run via `js()`.
- `references/motion-verification.md` — multi-scene "film" loop recipe, CSS scroll-driven
  draw, motion gates, and the freeze-and-seek recipe for inspecting/capturing an animated
  frame with the Web Animations API.
