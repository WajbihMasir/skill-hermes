# Design Craft Notes

Full-length craft notes preserved from MengTo/Skills (MIT, (c) Meng To). These are
longer, opinionated write-ups that complement `visual-techniques.md` (which holds the
copy-paste recipes). Read the one section you need.

| Section | Use when |
|---|---|
| 1. Design-First Prompting | You need to turn a fuzzy idea into a tight UI spec before building |
| 2. Awwwards-Quality Bar | You want the site to hold together as one art-directed whole |
| 3. Slop Audit — Evidence Rules | You are auditing an existing artifact and must not over-claim |
| 4. Cinematic Scroll Storytelling | You are building pinned/scrubbed/progress-linked scroll narratives |

---

## Design-First Prompting

This skill is for **design-first prompting**: turn fuzzy ideas into a tight spec that produces consistent UI.

## Core principle
**Prompt like a design system, not a wish.**

## Prompt Structure (copy/paste)
Use this skeleton, then fill the blanks.

```text
GOAL
- What are we making? (e.g., landing page hero / onboarding / dashboard / carousel slide)
- Who is it for? (persona)
- What’s the success criteria? (clarity, conversion, vibe)

FORMAT
- Size/aspect: (e.g., 1080x1350)
- Safe margins: (e.g., 90px)

LAYOUT (wireframe in words)
- Grid: (e.g., Swiss 6-col)
- Placement: (e.g., type-left / image-right)
- Hierarchy: H1 → subhead → body → CTA

TYPE SYSTEM
- Font vibe: (e.g., Söhne / Neue Haas / SF Pro)
- Weights: (H1 700, body 400)
- Leading: (tight for H1, readable for body)
- Tracking: (micro labels wider)

COLOR + MATERIAL
- Background: (hex or description)
- Text: (white/ivory/charcoal)
- One accent only: (cyan/lime/purple)
- Texture: (subtle grain, no plastic HDR)

IMAGERY / UI STYLE
- UI style: (minimal / glass / editorial / playful 3D)
- If photo: lighting + crop + texture rules
- If 3D: materials + lighting + softness

COPY (render EXACTLY)
- Line 1:
- Line 2:
- ...

CONSTRAINTS (change 1–2 things only)
- FONT: ___
- STYLE: ___
- MODE: ___

NEGATIVE PROMPT
- No logos, no watermarks
- No extra text beyond provided lines
- No gibberish typography
```

## Rules that improve consistency

### 1) Lock one “system”, then iterate with variants
- First output: nail **layout + hierarchy + copy**.
- Variants: change **ONE variable** at a time:
  - angle / crop
  - accent color
  - card arrangement
  - background tone

### 2) Treat typography as fragile
If the model keeps misspelling:
- Use **2-pass workflow**:
  1) Generate without text (reserve a clean text-safe area)
  2) Typeset in Figma

### 3) Use “constraints cards”
When you want the model to obey a style:
- Add a small “Constraints” panel with explicit values.
- It anchors the output like a mini style guide.

Example:
```text
Constraints
FONT  CANELA
STYLE  MINIMAL
MODE  DARK
```

### 4) Keep a local reference pack
Don’t ask the model to “remember” taste.
- Save references into a gitignored local reference folder, such as `refs/...`
- Point prompts to the reference style

## Fast iteration checklist (what to tweak)
- Spacing: margins, leading, baseline rhythm
- Contrast: background vs text
- Hierarchy: one hero line, one support line
- One accent only (don’t rainbow)
- Texture: add grain, remove smoothing

## Questions to ask (when user is vague)
- What’s the single message of this screen?
- What’s the hierarchy (H1 / sub / CTA)?
- Which style lane: minimal editorial vs playful 3D vs glass UI?
- Any must-keep constraints (font vibe, color, spacing, grid)?

---

## Awwwards-Quality Bar

Build a cohesive, memorable site whose visual idea, media, typography, and motion tell the same story. Treat “Awwwards quality” as an acceptance bar, never as an award or recognition claim.

## 1. Set the art direction

- Inspect the user's reference evidence completely before implementation. Extract only high-level traits such as hierarchy, pacing, contrast, image treatment, and motion principles.
- Generate a materially new identity, layout, copy system, imagery, and interaction language. Never reuse, trace, or closely reproduce reference assets, screenshots, source code, identity, or copy.
- Use Aura.build top asset imagery only when the user requests it or it is relevant and available. Treat it as high-level inspiration, not an asset library.
- Select and name at least one compatible installed web-design skill. Follow the smallest relevant set and avoid combining unrelated aesthetic systems.
- Write a compact direction before coding: visual thesis, hero focal asset, type hierarchy, color system, section sequence, motion narrative, chosen smooth-scroll engine, Three.js decision, and asset provenance plan.

## 2. Build an honest asset system

- Generate original hero or project imagery when it materially improves the concept. Use appropriately licensed media when it is stronger, and keep provenance in the site source.
- Do not draw illustrations with model-authored SVG, CSS, or canvas paths. Use original generated or appropriately licensed transparent PNG cutouts for illustrative elements. Simple authored brand marks, interface icons, data graphics, and a justified Three.js shader canvas are allowed.
- Use photographs for every avatar. Prefer provided or appropriately licensed photos; never ship initials, illustrated heads, faceless silhouettes, or generated people presented as real customers, staff, or endorsers.
- Use Solar icons through Iconify for interface symbols. Use Iconify SVG Logos only for legitimate real-company marks in truthful contexts. Use Logo Ipsum only for explicitly disclosed fictional brand specimens, never as customer proof. Omit a logo wall when no honest proof exists.
- Provide deliberate aspect ratios, crop behavior, alt text, loading behavior, and missing-media fallbacks. Avoid generic stock imagery, copied mockups, watermarks, and decorative media without a narrative role.

## 3. Compose the hero

- Make the first viewport the site's strongest authored moment. Combine a clear message and CTA with original imagery, video, pointer-responsive interaction, or a justified Three.js scene.
- Create a composed GSAP intro sequence for the hero. Keep navigation, primary message, and CTA readable and usable before the animation completes.
- Make pointer effects additive. Support touch, keyboard, coarse pointers, window blur, and visibility changes without leaving the interface in an incomplete state.
- Design a static first frame that remains complete when JavaScript, media playback, WebGL, or motion is unavailable.

## 4. Build the motion system

- Use GSAP as the primary animation system.
- Evaluate Lenis and Locomotive Scroll, then choose exactly one as the site's sole smooth-scroll engine. Never install or initialize both. Connect the chosen engine correctly to GSAP ScrollTrigger, refresh measurements after media and font changes, and destroy it during cleanup.
- Bypass smooth scrolling and scrubbed timelines under `prefers-reduced-motion: reduce`. Render final states immediately instead of merely shortening animations.
- Choreograph the page section by section. Reveal major headings word by word with a restrained stagger, then sequence supporting copy and media.
- Preserve an unsplit accessible name for staggered text. Hide decorative split words from assistive technology, never split links or meaningful inline markup, and keep the unsplit content visible without JavaScript.
- Use CSS for simple hover, focus, and tap states. Reserve ScrollTrigger for justified scrubbed or pinned sequences and avoid multiple systems controlling the same property.

## 5. Add Three.js only with purpose

- Use Three.js and custom WebGL shaders when spatial depth, texture transition, displacement, or pointer response materially supports the art direction. Do not add a shader as ornamental background noise.
- Give the canvas one clear responsibility and keep it subordinate to semantic content and controls.
- Cap device pixel ratio, pause rendering offscreen or when the document is hidden, throttle pointer input, and avoid per-frame allocation.
- Provide a static poster and replace the canvas entirely under reduced motion or WebGL failure.
- Dispose animation frames, observers, event listeners, render targets, textures, geometries, materials, and the renderer. Handle context loss without breaking page content.

## 6. Meet the quality bar

- Build a complete semantic page, not a hero-only concept. Include responsive navigation, coherent section progression, concrete conversion content, final CTA, footer, robust form or control states when present, and visible keyboard focus.
- Require a distinct art-directed idea, memorable first viewport, disciplined typography and spacing, intentional image crops, authored transitions, and refined hover, focus, active, loading, disabled, error, touch, and reduced-motion behavior.
- Preserve performance with responsive media, lazy loading below the fold, bounded transforms, limited blur, capped canvas work, and no continuously animated offscreen content.
- Reject generic gradient blobs, ornamental bento grids, glass applied everywhere, stock component layouts, fake testimonials, invented partnerships, logo-wall theater, and motion with no narrative role.
- Never describe the result as award-winning or Awwwards-recognized unless the user provides verifiable evidence.

## 7. Validate before handoff

- Run the production build and fix every failure.
- Check the page at desktop and mobile sizes when browser validation is requested or needed to resolve a blocker.
- Verify keyboard navigation, visible focus, touch behavior, content with JavaScript unavailable, static media fallbacks, and `prefers-reduced-motion` behavior.
- Check that only one smooth-scroll engine is installed and initialized, ScrollTrigger integration is correct, and all animation and WebGL resources clean up.
- Search rendered content and source for placeholders, copied reference identity, unsupported claims, misleading logos, uncredited media, and inaccessible split text.
- Report the chosen web-design skill, asset sources, motion stack, Three.js decision, validation performed, and any remaining limitation.

---

## Slop Audit — Evidence Rules

Run a diagnostic, evidence-backed audit. Identify the smallest set of removals or corrections that would improve the interface while preserving its existing direction.

## Boundaries

- Do not guess whether AI made the design.
- Do not assign a numeric slop score.
- Do not reject a visual technique in isolation. A gradient, serif, dark theme, glass effect, card, animation, or single-font system can be intentional.
- Do not prescribe a new font, palette, layout, design system, or art direction unless the user explicitly asks for one.
- Do not turn an audit into an implementation task.
- Mark anything outside the visible or provided evidence as unknown.

## Audit the Evidence

Inspect the artifact available in the request:

- screenshots and recordings
- rendered pages and relevant viewports
- interaction and state changes
- source code, tokens, assets, and copy
- console or runtime failures when they affect the experience

For every finding, cite a concrete location, component, behavior, or line of copy. Do not report a generic tendency without evidence in the artifact.

For a full-page or full-site review, work through the 10-tell diagnostic in the main `claude-design` SKILL.md ("Slop Diagnostic") and use only the tells relevant to the inspected artifact. Do not turn every checklist match into a finding. Group symptoms by root cause and report the highest-impact evidence.

## Classify Findings

Use one of these classes:

- **Quality defect:** an established usability, accessibility, content, responsive, or runtime problem.
- **Slop pattern:** a repeated default, decorative layer, or generated-looking convention with no useful role.

## What to Flag

### Decorative stacking

Flag combinations of glow, gradient text, glass, borders, shadows, grids, particles, beams, noise, floating shapes, or browser chrome when multiple layers perform the same decorative job or compete with the content.

### Component and template repetition

Flag:

- card treatment applied to nearly every content block
- repeated icon-heading-description tiles with interchangeable content
- nested rounded containers that do not communicate hierarchy
- generic landing-page sequences unrelated to the product's buying or usage journey
- headings, labels, pills, or CTA blocks that restate nearby information

### Typography and copy clutter

Flag:

- duplicate text or unnecessary labels
- empty superlatives, vague category claims, and generated filler
- decorative type treatments that obscure hierarchy or readability
- long centered paragraphs, awkward forced line breaks, or hard-to-scan text
- inconsistent type roles that look accidental rather than expressive

### Motion theater

Flag motion that delays access, repeats mechanically, distracts from reading, moves targets, blocks input, or lacks respect for reduced-motion preferences. Preserve motion that communicates state, causality, hierarchy, or spatial change.

### Fake proof

Flag invented or unverifiable metrics, customers, testimonials, awards, ratings, activity, dashboards, charts, logos, and portraits when they are presented as evidence.

### Established UI failures

Flag:

- unclear or competing primary actions
- low contrast or unreadable content
- clipping, overflow, overlap, or broken responsive behavior
- broken assets, links, scripts, or controls
- essential information available only on hover
- missing states required by the observed flow
- unclear labels, roles, feedback, or keyboard focus
- accidental inconsistency in spacing, type, color, radius, or icons
- visual hierarchy that contradicts task importance

## Use the Removal Test

For every candidate:

1. State what information, state, action, hierarchy, or brand meaning it provides.
2. Ask whether removing it would improve clarity without losing that role.
3. If yes, recommend removal or consolidation.
4. If no, recommend the smallest correction using the existing system.
5. Suggest a replacement only when deletion would create a real loss.

Default to subtraction. A replacement should inherit the product's existing language rather than introduce a new visual concept.

## Prioritize

- **P0:** blocks completion, creates a severe accessibility issue, or presents deceptive proof
- **P1:** materially harms comprehension, trust, navigation, or interaction
- **P2:** repeated slop or inconsistency that weakens hierarchy and identity
- **P3:** minor polish issue with limited user impact

Return the five to eight highest-impact findings by default. Group repeated instances into one systemic finding.

## Output

```md
## Verdict
One concise paragraph about the dominant problems and what should be removed first.

## Checked scope
- Artifact, screen, state, and viewport actually inspected

## Findings
| Priority | Class | Pattern | Evidence | Harm | Remove or fix |
|---|---|---|---|---|---|
| P1 | Slop pattern | Repeated ornamental containers | Feature area uses the same layered card treatment for unrelated content | Flattens hierarchy and adds noise | Remove outer shells; retain grouping only where it communicates interaction |

## Unknowns
- Important states or behavior that could not be verified
```

Keep the report compact. Omit empty sections.

## Feedback Rules

- Lead with concrete evidence, not taste claims.
- Name the pattern and its harm.
- Recommend removal before restyling.
- Avoid generic compliments and exhaustive low-impact nitpicks.
- Preserve useful product-specific detail and intentional character.
- Do not cite a standard unless it directly supports the finding.
- Do not describe an aesthetic as universally bad.
- If the user explicitly asks for design swaps, place an optional replacement after the removal recommendation and keep it consistent with the existing system.
- End with the single removal or correction that would produce the largest improvement.

---

## 4. Cinematic Scroll Storytelling

## Use When
- A page should feel like a premium editorial story that unfolds as the user scrolls.
- The user mentions scroll-driven storytelling, scroll-linked animation, sticky card stacks, parallax, split text, preloader, or cinematic progression.
- A portfolio, studio, product, or landing page needs section-by-section reveals with layered depth.
- The implementation can use GSAP, ScrollTrigger, and Lenis.

## Effect Vocabulary
- Scroll-driven storytelling: sections reveal as a sequence while scrolling.
- Scroll-linked animation: progress is tied directly to scroll with `scrub`.
- Scroll-triggered motion: animation starts when a section enters the viewport.
- Staggered reveal: words, lines, cards, or elements enter with small delays.
- Progressive reveal: opacity, scale, blur, clip, or position changes over scroll progress.
- Sticky card stack: sticky cards layer, scale, and recede as the next card arrives.
- Parallax scrolling: background and foreground layers move at different speeds.
- Scroll scrubbing: animation follows the scrollbar through `scrub: true` or `scrub: 1`.
- Kinetic typography: masked split-text movement, usually word-by-word or line-by-line.
- Preloader: opening loading screen, progress bar, and intro transition.

## Target Feel
- Luxury editorial website.
- High-end creative studio portfolio.
- Apple-level motion polish.
- Modern Awwwards interaction language.
- Immersive cinematic landing page.

Avoid:
- Bounce, elastic, or springy motion.
- Aggressive scale jumps.
- Flashy gaming-style effects.
- Too many simultaneous scroll effects.
- Scroll hijacking that makes the page hard to read.

## Core Stack

```bash
npm i gsap lenis
```

```js
import Lenis from "lenis";
import "lenis/dist/lenis.css";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (!reduceMotion) {
  const lenis = new Lenis({
    lerp: 0.08,
    smoothWheel: true,
    wheelMultiplier: 0.9,
  });

  lenis.on("scroll", ScrollTrigger.update);

  gsap.ticker.add((time) => {
    lenis.raf(time * 1000);
  });

  gsap.ticker.lagSmoothing(0);
}

window.addEventListener("load", () => ScrollTrigger.refresh());
```

## Motion Tokens
- Enter ease: `power3.out` or `power4.out`.
- Scrubbed scenes: `ease: "none"` with `scrub: 0.8` to `1.4`.
- Text reveal duration: `0.8s` to `1.1s`.
- Card reveal duration: `0.9s` to `1.2s`.
- Word stagger: `0.035s` to `0.07s`.
- Line stagger: `0.08s` to `0.14s`.
- Card stagger: `0.06s` to `0.1s`.
- Reveal offset: `y: 24` to `48`.
- Blur: `4px` to `10px`, then `0px`.
- Sticky card scale depth: `1` down to `0.92`.

## Page Anatomy
1. Preloader: black screen, progress bar, brand/title, intro fade.
2. Hero: image parallax, masked headline reveal, subtle scroll cue.
3. Intro: word-by-word kinetic typography.
4. Story sections: scroll-triggered fade-up, blur-in, and clip reveals.
5. Recent Projects: sticky card stack with scale and layered depth.
6. Gallery or proof: scroll-scrubbed horizontal or progressive reveals.
7. Footer: parallax reveal or slow upward handoff.

## Markup Pattern

```html
<div class="preloader" data-preloader>
  <div class="preloader__bar" data-preloader-bar></div>
</div>

<main>
  <section class="hero" data-parallax-section>
    <img data-parallax-layer data-speed="-0.18" src="/hero.jpg" alt="">
    <h1 data-split-reveal>Design that unfolds with cinematic restraint.</h1>
  </section>

  <section data-story-section>
    <p data-split-reveal="words">Every block arrives with quiet intent.</p>
  </section>

  <section class="project-stack" data-sticky-stack>
    <article data-stack-card>Project One</article>
    <article data-stack-card>Project Two</article>
    <article data-stack-card>Project Three</article>
  </section>

  <footer data-footer-parallax>...</footer>
</main>
```

## Preloader Sequence

Use a preloader to set the cinematic tone, then hand off into the hero reveal.

```js
function initPreloader() {
  const loader = document.querySelector("[data-preloader]");
  const bar = document.querySelector("[data-preloader-bar]");
  if (!loader) return Promise.resolve();

  if (reduceMotion) {
    loader.remove();
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    const tl = gsap.timeline({
      defaults: { ease: "power3.out" },
      onComplete: () => {
        loader.remove();
        resolve();
      },
    });

    tl.fromTo(bar, { scaleX: 0, transformOrigin: "left" }, { scaleX: 1, duration: 1.1 })
      .to(loader, { yPercent: -100, duration: 0.9, ease: "power4.inOut" }, "+=0.15");
  });
}
```

## Split Text Reveal

Use masked overflow containers. Avoid splitting text that contains links or meaningful inline markup.

```js
function splitWords(element) {
  if (element.dataset.splitReady === "true") return;

  const text = element.textContent || "";
  const parts = text.split(/(\s+)/);
  element.textContent = "";
  element.setAttribute("aria-label", text.trim());

  parts.forEach((part) => {
    if (!part.trim()) {
      element.appendChild(document.createTextNode(part));
      return;
    }

    const mask = document.createElement("span");
    const word = document.createElement("span");
    mask.className = "split-word-mask";
    word.className = "split-word";
    word.textContent = part;
    mask.setAttribute("aria-hidden", "true");
    mask.appendChild(word);
    element.appendChild(mask);
  });

  element.dataset.splitReady = "true";
}

function initSplitReveals() {
  if (reduceMotion) {
    gsap.set("[data-split-reveal]", { autoAlpha: 1 });
    return;
  }

  gsap.utils.toArray("[data-split-reveal]").forEach((element) => {
    splitWords(element);
    const words = element.querySelectorAll(".split-word");

    gsap.fromTo(
      words,
      { yPercent: 110, autoAlpha: 0, filter: "blur(8px)" },
      {
        yPercent: 0,
        autoAlpha: 1,
        filter: "blur(0px)",
        duration: 0.95,
        ease: "power4.out",
        stagger: 0.05,
        scrollTrigger: {
          trigger: element,
          start: "top 82%",
          once: true,
        },
      }
    );
  });
}
```

```css
.split-word-mask {
  display: inline-block;
  overflow: hidden;
  vertical-align: top;
}

.split-word {
  display: inline-block;
  will-change: transform, opacity, filter;
}
```

## Scroll-Triggered Reveals

Use these for normal sections. They should play once and feel composed, not twitchy.

```js
function initSectionReveals() {
  if (reduceMotion) {
    gsap.set("[data-story-section], [data-reveal-item]", { autoAlpha: 1, clearProps: "all" });
    return;
  }

  gsap.utils.toArray("[data-story-section]").forEach((section) => {
    const items = section.querySelectorAll("[data-reveal-item]");
    const targets = items.length ? items : section.children;

    gsap.fromTo(
      targets,
      { y: 36, autoAlpha: 0, filter: "blur(8px)" },
      {
        y: 0,
        autoAlpha: 1,
        filter: "blur(0px)",
        duration: 1,
        ease: "power4.out",
        stagger: 0.08,
        scrollTrigger: {
          trigger: section,
          start: "top 82%",
          once: true,
        },
      }
    );
  });
}
```

## Scroll-Linked Progression

Use scrubbed timelines for cinematic progression. Keep scrubbed animation linear and let the scroll position do the timing.

```js
function initProgressionScenes() {
  if (reduceMotion) return;

  gsap.utils.toArray("[data-progress-scene]").forEach((scene) => {
    const media = scene.querySelector("[data-progress-media]");
    const copy = scene.querySelectorAll("[data-progress-copy]");

    gsap.timeline({
      scrollTrigger: {
        trigger: scene,
        start: "top top",
        end: "+=140%",
        scrub: 1.1,
        pin: true,
        anticipatePin: 1,
      },
    })
      .fromTo(media, { scale: 1.08 }, { scale: 1, ease: "none" })
      .fromTo(copy, { autoAlpha: 0, y: 40 }, { autoAlpha: 1, y: 0, stagger: 0.15, ease: "none" }, 0.15);
  });
}
```

## Sticky Card Stack

Use `position: sticky` for layout, and ScrollTrigger for layered scale/depth. Earlier cards should recede as later cards arrive.

```css
[data-sticky-stack] {
  position: relative;
}

[data-stack-card] {
  position: sticky;
  top: 12vh;
  transform-origin: center top;
  will-change: transform, opacity;
}
```

```js
function initStickyCardStack() {
  if (reduceMotion) return;

  gsap.utils.toArray("[data-sticky-stack]").forEach((stack) => {
    const cards = gsap.utils.toArray(stack.querySelectorAll("[data-stack-card]"));

    cards.forEach((card, index) => {
      const nextCard = cards[index + 1];
      if (!nextCard) return;

      gsap.to(card, {
        scale: 0.92 + index * 0.015,
        autoAlpha: 0.72,
        y: -24,
        ease: "none",
        scrollTrigger: {
          trigger: nextCard,
          start: "top 78%",
          end: "top 24%",
          scrub: true,
          invalidateOnRefresh: true,
        },
      });
    });
  });
}
```

## Parallax

Use parallax for hero images, background layers, and footer reveals. Keep distance small.

```js
function initParallax() {
  if (reduceMotion) return;

  gsap.utils.toArray("[data-parallax-layer]").forEach((layer) => {
    const speed = Number(layer.dataset.speed || -0.16);
    const section = layer.closest("[data-parallax-section]") || layer;

    gsap.to(layer, {
      y: () => window.innerHeight * speed,
      ease: "none",
      scrollTrigger: {
        trigger: section,
        start: "top bottom",
        end: "bottom top",
        scrub: 1,
        invalidateOnRefresh: true,
      },
    });
  });
}
```

Footer parallax reveal:

```js
function initFooterReveal() {
  if (reduceMotion) return;

  const footer = document.querySelector("[data-footer-parallax]");
  if (!footer) return;

  gsap.fromTo(
    footer,
    { yPercent: -12, autoAlpha: 0.85 },
    {
      yPercent: 0,
      autoAlpha: 1,
      ease: "none",
      scrollTrigger: {
        trigger: footer,
        start: "top bottom",
        end: "top 45%",
        scrub: 1,
      },
    }
  );
}
```

## Build Order
1. Build the static page first.
2. Add preloader and hero entrance.
3. Add split text reveals.
4. Add section-by-section reveals.
5. Add sticky card stack progression.
6. Add parallax layers.
7. Add scrubbed pinned scenes only where the story needs them.
8. Add reduced-motion and touch fallbacks.
9. Run browser QA across desktop and mobile.

## Prompt Template

```txt
Create a cinematic scroll-driven landing page with smooth Lenis scrolling, GSAP ScrollTrigger animations, staggered text reveals, sticky card stack progression, parallax backgrounds, scroll-scrubbed transitions, section-by-section storytelling, and an immersive preloader animation. Use layered depth, scaling transitions, progressive opacity changes, and smooth viewport-triggered motion for a premium editorial experience.
```

## QA Checklist
- Content is readable with JavaScript disabled.
- Reduced-motion users see static content and no smooth-scroll layer.
- Scroll-triggered reveals play once.
- Scroll-linked scenes use `scrub` intentionally.
- Sticky cards do not overlap the footer or trap the page.
- Parallax movement stays subtle and does not harm readability.
- Preloader exits reliably even if images load slowly.
- `ScrollTrigger.refresh()` runs after images/fonts/layout shifts.
- Mobile has simplified pinning or no pinning if performance drops.
