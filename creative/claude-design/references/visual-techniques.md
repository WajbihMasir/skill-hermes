# Visual Technique Library

Concrete, copy-paste CSS/Tailwind recipes for high-end surfaces. Distilled from
MengTo/Skills (MIT, © Meng To) and elayadesign/ai-design-skills (MIT).

Load this when a section needs a specific craft technique — elevation, edge
treatment, motion, or a conversion blueprint. Do NOT read it top-to-bottom on
every landing-page task; jump to the section you need.

| Need | Section |
|---|---|
| Cards/panels look flat | [1. Elevation & Shadows](#1-elevation--shadows) |
| Premium card edges on dark UI | [2. Gradient Borders](#2-gradient-borders) |
| Reveal-on-scroll motion | [3. Scroll Animation](#3-scroll-animation) |
| Cinematic scrollytelling | [4. Scroll Storytelling](#4-scroll-storytelling) |
| Page structure / section order | [5. Conversion Blueprint](#5-conversion-blueprint) |
| "Is this AI slop?" audit | [6. Slop Audit](#6-slop-audit) |

---

## 1. Elevation & Shadows

Use when: a surface needs polished, layered elevation, or default Tailwind
shadows feel blunt. Keep shadows **neutral** — never tint them with strong color.

### sm — compact cards, form controls, pills, quiet surfaces

```txt
shadow-[0px_2px_3px_-1px_rgba(0,0,0,0.1),0px_1px_0px_0px_rgba(25,28,33,0.02),0px_0px_0px_1px_rgba(25,28,33,0.08)]
```

### md — cards, panels, popovers (default elevated surface)

```txt
shadow-[0px_0px_0px_1px_rgba(0,0,0,0.06),0px_1px_1px_-0.5px_rgba(0,0,0,0.06),0px_3px_3px_-1.5px_rgba(0,0,0,0.06),_0px_6px_6px_-3px_rgba(0,0,0,0.06),0px_12px_12px_-6px_rgba(0,0,0,0.06),0px_24px_24px_-12px_rgba(0,0,0,0.06)]
```

### lg — hero media, feature callouts, modals (strongest lift)

```txt
shadow-[0_2.8px_2.2px_rgba(0,_0,_0,_0.034),_0_6.7px_5.3px_rgba(0,_0,_0,_0.048),_0_12.5px_10px_rgba(0,_0,_0,_0.06),_0_22.3px_17.9px_rgba(0,_0,_0,_0.072),_0_41.8px_33.4px_rgba(0,_0,_0,_0.086),_0_100px_80px_rgba(0,_0,_0,_0.12)]
```

**Rules**
- One shadow strength per component state; change elevation only on real interaction.
- Never stack multiple shadow utilities on one element.
- Never mix these with default Tailwind shadow scales on the same component.
- Do not apply `lg` to dense lists or tiny controls.
- Shadows do not replace borders in low-contrast contexts.

Plain CSS equivalent of `md` (when not using Tailwind):

```css
.card {
  box-shadow:
    0 0 0 1px rgba(0,0,0,.06),
    0 1px 1px -.5px rgba(0,0,0,.06),
    0 3px 3px -1.5px rgba(0,0,0,.06),
    0 6px 6px -3px rgba(0,0,0,.06),
    0 12px 12px -6px rgba(0,0,0,.06),
    0 24px 24px -12px rgba(0,0,0,.06);
}
```

---

## 2. Gradient Borders

Use when: a dark glass / pricing / hero / feature card needs a more premium edge
than a flat `border`.

**Defaults:** width `1px` (`2px` only for large hero cards or active states);
radius inherits parent; angle `135deg` or `160deg`; stops = neutral highlight +
one brand accent + neutral fade; keep most stops **below `0.4` opacity** — subtle
beats shiny.

### Simple pattern (solid or translucent fill)

```css
.gradient-border {
  --surface: rgba(10, 14, 24, 0.72);
  --border-a: rgba(255, 255, 255, 0.34);
  --border-b: rgba(125, 92, 255, 0.36);
  --border-c: rgba(255, 255, 255, 0.08);

  border: 1px solid transparent;
  border-radius: 20px;
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(135deg, var(--border-a), var(--border-b), var(--border-c)) border-box;
}
```

### Masked pattern (surface already has a complex background)

```css
.gradient-border-mask {
  position: relative;
  border-radius: 20px;
}

.gradient-border-mask::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.34),
    rgba(125, 92, 255, 0.36) 45%,
    rgba(255, 255, 255, 0.08)
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
```

### Tailwind one-off

```html
<div class="rounded-2xl border border-transparent [background:linear-gradient(rgba(10,14,24,.72),rgba(10,14,24,.72))_padding-box,linear-gradient(135deg,rgba(255,255,255,.34),rgba(125,92,255,.36),rgba(255,255,255,.08))_border-box]">
```

**Taste rules**
- Apply to **one hierarchy level at a time**: primary card, active tab, selected plan, or hero panel.
- No rainbow borders, no full-saturation neon, no animated gradients by default.
- On hover/focus, brighten the existing stops — do not introduce a second hue.

---

## 3. Scroll Animation

Use when: elements should reveal once as they enter the viewport. Paused by
default, activated by an `IntersectionObserver`, so nothing flashes before
hydration.

```html
<script>
  /*
    1) Insert this in <head> along with the keyframes below.
    2) Add to the element's classes:
         [animation:animationIn_0.8s_ease-out_0.1s_both] animate-on-scroll
  */
  (function () {
    const style = document.createElement("style");
    style.textContent = `
      .animate-on-scroll { animation-play-state: paused !important; }
      .animate-on-scroll.animate { animation-play-state: running !important; }
    `;
    document.head.appendChild(style);

    const once = true; // set false to re-animate every time

    if (!window.__inViewIO) {
      window.__inViewIO = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate");
            if (once) window.__inViewIO.unobserve(entry.target);
          }
        });
      }, { threshold: 0.2, rootMargin: "0px 0px -10% 0px" });
    }

    window.initInViewAnimations = function (selector = ".animate-on-scroll") {
      document.querySelectorAll(selector).forEach((el) => {
        window.__inViewIO.observe(el); // observing twice is a no-op
      });
    };

    document.addEventListener("DOMContentLoaded", () => initInViewAnimations());
  })();
</script>

<style>
  @keyframes animationIn {
    0%   { opacity: 0; transform: translateY(24px); filter: blur(6px); }
    100% { opacity: 1; transform: translateY(0);    filter: blur(0); }
  }
</style>
```

**Tweaks that actually matter:** `threshold`, `rootMargin`, animation duration,
delay, and the `transform`/`blur` values. Stagger children with
`[animation-delay:80ms]`, `[animation-delay:160ms]`, … rather than one long delay.

**Always** honor `prefers-reduced-motion` — disable the transform/blur and keep
only a short opacity fade.

---

## 4. Scroll Storytelling

Use when: a page should *narrate* on scroll (pinned sections, scrubbed video,
progress-linked reveals) instead of just fading blocks in.

**Posture**
- One idea per scroll segment; the viewport is the stage, not a container.
- Motion must **clarify** sequence or state — never loop decoratively.
- Pin sparingly: 1–2 pinned moments per page maximum, or scrolling feels trapped.
- Give the user an exit: never block scroll for longer than one gesture.

**Technique ladder** (cheapest first — stop at the lowest rung that works)
1. **Reveal** — `IntersectionObserver` + keyframes (§3). 90% of cases.
2. **Parallax** — translate a background layer at a fraction of scroll delta.
3. **Progress-linked** — drive a value from scroll position (progress bar, line draw).
4. **Scrubbed media** — map scroll position to `video.currentTime`; preload, and always ship a static poster fallback.
5. **Pinned sequence** — `position: sticky` + a tall spacer; avoid JS scroll-jacking.

**Performance:** animate only `transform` and `opacity`. Batch reads/writes, and
throttle with `requestAnimationFrame`. Test on a mid-range phone, not just desktop.

---

## 5. Conversion Blueprint

Use when: deciding *what sections a landing page needs and in what order* — the
structure question, before any visual work.

**One offer, one audience, one primary conversion action.** If a page serves two
personas, route them (§5.3) rather than averaging the copy.

### 5.1 Section order

1. **Hero** — headline (value prop + hook), subheadline, one primary CTA, proof, visual
2. **Social proof** — logos, metrics, or named testimonials (never fake it)
3. **Problem / Pain** — the specific cost of the status quo
4. **How it works** — 3 steps, numbered `01 02 03`
5. **Benefits** — each tied back to the hero's promise
6. **Interactive demo** — let them *feel* it; the strongest differentiator
7. **FAQ** — objection killer, placed right before the final ask
8. **Final CTA** — callback to the hero hook, same narrative CTA (not a new one)

### 5.2 Copy rules

- **Headline litmus test:** seeing *only* the headline, does a stranger know what you sell?
  - ❌ "Improve your workflow" / "The future of productivity"
  - ✅ "Groceries delivered in 1 hour" / "Design websites visually — no code required"
- **Hook is one of two types:** a bold specific claim ("Cut deploy time from 4 hours to 12 minutes"), or the #1 objection answered ("No credit card required", "Works with your existing tools").
- **Subheadline** does exactly two jobs: says what it is, or explains how the claim is possible. 1–2 sentences.
- **Feature copy** = short blunt header + concise paragraph addressing ONE objection + an image of the product *in action*.
- **CTA continues the narrative:** ✅ "Find food near me", "See your savings" — ❌ "Get started", "Sign up".
- **Social proof cold start:** give free access to 3–5 recognizable companies then show their logos; use specific testimonials with real names; show aggregate stats. An empty logo bar is worse than no bar.

### 5.3 Multi-persona routing

If the product serves distinct roles (developer vs designer, individual vs team),
add a "choose your own adventure" element near the top — tabs, a split hero, or
segmented pages linked from the hero. Don't force everyone through one funnel.

### 5.4 Visual constraints

- **Nested radius:** `R_inner = R_outer − padding` (a 20px card with 12px padding → 8px inner elements).
- **Zero pill-on-pill:** if the navbar is already a floating pill, don't put pill badges inside it.
- **Base type 16px, line-height 1.5.** Body text never below 12px.

---

## 6. Slop Audit

Use when: an artifact looks generic and you need to find out *why* before polishing.
Diagnose first, then repair — recoloring a composition problem never fixes it.

Score each tell as 1 point (lower is better). The full 10-tell diagnostic lives in
the `claude-design` skill; the high-frequency offenders:

| Tell | Repair register |
|---|---|
| Tech gradient on everything | recolor |
| Default accent = indigo/violet (unchosen) | recolor |
| Icon + heading + sentence ×3, all equal weight | **re-layout** |
| Colored left strip on cards ("accent rail") | remove decoration |
| Glassmorphism with no elevation system behind it | remove decoration |
| Oversized stat numbers filling space that should tell story | remove decoration |
| Rounded-square icon centered above every heading | remove decoration |
| Everything centered (no composition committed) | **re-layout** |
| Inter/system-ui used by default rather than chosen | re-typeset |
| Composition doesn't match the surface type | **re-layout** (root cause) |

**Rules**
- Compositional tells (feature-tile grid, center stack, wrong surface) are causes — never declare done while they fire. Fix those by re-laying out, not recoloring.
- A color present in the DOM but covering <5% of the visible surface is decoration, not a brand color.
- If a principle could have been written without ever seeing this specific page, it is slop — delete it.
