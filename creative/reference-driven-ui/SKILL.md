---
name: reference-driven-ui
description: Build UI from real design references, then polish.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, design-system, tokens, layout, ui-polish, accessibility, refero, mobbin, saaspo]
    related_skills: [design-md, taste, popular-web-designs, landing-page-design, ui-ux-pro-max, reference-image-pixel-matching]
---

# Reference-Driven UI

Turn a product brief into a real interface by driving three external reference
sources in order — tokens first, then layout, then a verification pass — and
reconciling them with the project's own tokens. This skill owns the *pipeline*
and the *decision rules*. The formal token file belongs to `design-md`; the
one-site reverse-engineering belongs to `taste`; do not duplicate them here.

## When to Use

- "Build me a landing page / pricing page / dashboard that looks like X"
- "Find a design system and use it as the base for this project"
- "Give the UI a proper design foundation, then implement and polish it"
- "Review the UI I just built against real references"
- Don't use for: extracting tokens from ONE live site (`taste`), authoring the
  DESIGN.md spec file alone (`design-md`), or pure visual inspiration browsing
  (`popular-web-designs`).

## The Pipeline (run in order)

| Phase | Job | Source | Mutates? |
|-------|-----|--------|----------|
| 0 · Brief | Audience, screens, states, constraints | user | no |
| 1 · Foundation | Pick a style, pull its DESIGN.md, adapt tokens | Refero | no (writes plan/`DESIGN.md` only) |
| 2 · Layout | Section blueprint per page type | Saaspo + Mobbin + Land-book | no |
| 3 · Implement | Build using the project's tokens | project | **yes** |
| 4 · Review | Accessibility, layout, type, color, copy, polish | jakub rules | no |
| 5 · Verify | Contrast, every state, variants | WCAG + `state-machine`/`variant` | no |

**Plan Mode fit:** Phases 0–2 are read-only research and end in a plan file +
`DESIGN.md`. Run them under Hermes plan mode (or the `plan-mode` plugin), submit,
and only enter Phase 3 after approval. This is the intended use of plan mode.

## Source Catalog

| Source | What it gives | Access |
|--------|---------------|--------|
| `styles.refero.design` | 2,000+ AI-readable design systems; DESIGN.md per style | browser, JS-rendered — wait ~4s |
| `saaspo.com` | Indexed page types: Landing 791, Pricing 392, Product 239, About, Blog… | browser; Cloudflare challenge on first hit — wait ~8s |
| `mobbin.com` | 621k shipped screens, flows, animations, UI elements | browser (public preview); **MCP** needs Pro/Team |
| `land-book.com` | Curated website gallery + Sections/OG/Motion tabs | browser, no login |
| `are.na` | Curated moodboards/collections | browser, no login |
| `dribbble.com` | Shot-level visual ideas | browser, no login |

**Do not use Pinterest** — it is behind a login wall (`body.innerText` empty,
only a login form present) and Hermes must never guess or type credentials.

## Phase 1 — Foundation (Refero → DESIGN.md)

1. **List styles:** open `https://styles.refero.design`, then read the anchors:

   ```python
   js('''JSON.stringify(Array.from(document.querySelectorAll('a'))
     .map(a=>a.href).filter(h=>h.includes('/style/')))''')
   ```

2. **Pick one** whose mood matches the brief (the card subtitle is a one-line
   art direction — use it as the tie-breaker, not just the brand name).

3. **Pull its DESIGN.md.** Style pages render the whole document into the HTML
   as a `<style-reference>`; extract it by tag-stripping from the H1:

   ```python
   new_tab(url); wait_for_load()
   js('window.scrollTo(0, document.body.scrollHeight)'); # trigger lazy render
   import time; time.sleep(4)
   html = js("document.documentElement.outerHTML")
   i = html.find("— Style Reference")
   seg = html[i-200:i+20000]
   ```
   Strip tags (`re.sub(r'<[^>]+>',' ',seg)`), unescape, collapse blank lines.
   The document's section order is: `Tokens — Colors` (each with a **Role**),
   `Tokens — Typography` (family, weights, sizes, line-height, letter-spacing,
   OpenType, **Substitute font**), `Type Scale`, `Spacing & Shapes`, `Border
   Radius`, `Shadows`, `Layout`, `Components` (one recipe each), `Do's and
   Don'ts`, `Surfaces`, `Elevation`, `Imagery`, `Agent Prompt Guide`.

4. **Adapt, don't copy.** The reference is a *captured site*, not your brand.
   Keep its role structure (canvas / surface / text / action / state) and its
   type pairing logic; replace the literal hexes and fonts with the project's
   if it has any. Leave unknowns explicit (see `references/design-md-template.md`).

5. **Hand off to `design-md`** to write/lint/export the file:
   `npx -y @google/design.md lint DESIGN.md` then export Tailwind/DTCG as needed.

## Phase 2 — Layout (Saaspo + Mobbin + Land-book)

- **Saaspo page types** are addressable directly:
  `https://saaspo.com/page-types/saas-<type>-page-examples`
  (`landing`, `pricing`, `product`, `about`, `blog`, `customers`, `integrations`,
  `404`, `changelog`…). Read the tile URLs to get real product examples.
- **Mobbin** — if the MCP is connected, ask it for the flow/pattern directly
  (e.g. "proven paywall patterns"). Otherwise read the public preview pages.
- **Land-book** — use `/sections` for section-level layout, `/websites` for
  full-page rhythm.

Deliverable for this phase: a **section list** for the target page, each row
`section → reference → what to borrow`, e.g.
`hero → saaspo:lovable.dev → centered proof band + single CTA`.
Borrow *structure and rhythm*, never the copy or the brand assets.

## Phase 3 — Implement

Build with the project's tokens and component library. If the project has none,
use the `DESIGN.md` from Phase 1 as the single source. Do not invent a new
color/type per component — that is the exact failure this pipeline prevents.

## Phase 4 — Review (the jakub rules)

The `jakubkrehel/skills` collection is the review layer, **vendored in full**
under `references/jakub/` (MIT, 13 skills, commit `d574cc8`). Read the specific
`references/jakub/<skill>/SKILL.md` plus its topic files for exact values — do
not work from memory. Run `better-interface` first for a consolidated ranked
verdict, then the focused ones. Ownership map:

| Skill | Owns |
|-------|------|
| `better-interface` | Cross-discipline review, one ranked verdict |
| `better-ui` | Radius (concentric), optical alignment, shadows, icon states, motion |
| `better-typography` | Type scale, spacing, wrapping, truncation, OpenType |
| `better-colors` | OKLCH palettes, semantic tokens, contrast |
| `better-accessibility` | Focus, keyboard, ARIA, names, forms, motion, zoom (WCAG 2.2) |
| `better-layout` | Grouping, alignment, reading order, responsive, RTL |
| `better-writing` | Labels, errors, empty states, confirmations, voice |
| `interface-review` | Change-scoped review of a branch/PR/diff |
| `explain-interface` | How a live effect/animation was built |
| `break` | Stress-test a component under every scenario |
| `state-machine` | Render every state with mock data + switcher |
| `variant` | Build and compare multiple variants |
| `build-design` | Build UI to match a Figma file or design image |

**Rule that overrides taste:** a *trigger* (WCAG failure, broken interaction,
same detail done two ways) is always a finding. A density/radius/voice you
merely disagree with is **not** — leave deliberate project choices alone.

Each vendored skill also ships topic files with the exact recipes (e.g.
`references/jakub/better-ui/surfaces.md`, `.../better-colors/contrast.md`,
`.../better-accessibility/focus-and-keyboard.md`). Read them when a finding
needs a concrete value; `references/jakub/README.md` is the upstream index.

## Phase 5 — Verify

- Contrast on the final palette: `npx -y @google/design.md lint DESIGN.md`
  (WCAG AA is the load-bearing reason to run it).
- Every reachable state rendered, not just the happy path (`state-machine`).
- Responsive + translated/RTL text still holds (`better-layout`).
- Reduced-motion and focus states present (`better-accessibility`).

## Pitfalls

- **Refero style pages are client-rendered.** `innerText` looks empty; the data
  is in the raw HTML. Scroll to the bottom, wait ~4s, then parse
  `documentElement.outerHTML` — do not conclude the page is empty.
- **Saaspo shows a Cloudflare "Just a moment…" page on first load.** Wait ~8s
  and re-read; a headless fetch gets the challenge page instead.
- **Pinterest = login wall.** Skip it; use Land-book / Are.na / Dribbble.
- **Mobbin MCP is paid.** The site is browsable for free; the MCP is Pro/Team.
- **Don't copy a reference literally.** A DESIGN.md from Refero is an
  interpreted capture, not an official brand guide — keep the role logic,
  swap the values for the project's own.
- **Don't paraphrase the jakub rules from memory.** They carry exact values
  (`cubic-bezier(0.2, 0, 0, 1)`, outer radius = inner + padding + border) and
  a digest loses them. Read `references/jakub/<skill>/SKILL.md` itself.
- **Don't build a router skill.** This file must stay actionable on its own;
  it points at `design-md`/`taste` only for the parts they genuinely own.

## Verification Checklist

- [ ] A `DESIGN.md` exists with colors, typography, and layout roles filled
- [ ] Its unknown/product-specific decisions are explicit, not guessed
- [ ] A section blueprint exists, one row per section with its reference
- [ ] Every finding from Phase 4 cites a location and a concrete fix
- [ ] Contrast checked; no WCAG AA failures left unreported
- [ ] All states and variants rendered, not just the default
