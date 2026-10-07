# Motion for single-file artifacts: recipes + how to verify it

A static page is a valid result. Add animation only with the three gates below,
and verify motion by measuring the DOM, never by trusting a screenshot.

## The three gates (mandatory)

```css
/* 1. reduced motion — disable AND land on a static, informative frame */
@media (prefers-reduced-motion: reduce){
  *{animation:none!important;transition:none!important}
  .film-scene{opacity:0}
  .film-scene.fs1{opacity:1;position:relative;inset:auto} /* first scene, static */
}

/* 2. user pause toggle (JS sets .motion-paused on <html>) */
.motion-paused *{animation-play-state:paused!important}

/* 3. progressive enhancement — visible by default, hidden only if supported */
@supports (animation-timeline: view()){
  .reveal{animation:reveal-up linear both;animation-timeline:view();
          animation-range:entry 8% cover 32%}
  @keyframes reveal-up{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
}
```

Pause toggle JS (add classes synchronously — never inside `requestAnimationFrame`,
which is skipped in background/throttled tabs):

```js
toggle.addEventListener('click', function(){
  var paused = document.documentElement.classList.toggle('motion-paused');
  toggle.setAttribute('aria-pressed', paused ? 'true' : 'false');
});
```

## Multi-scene "film" loop (highest-value product-hero motion)

One keyframe per scene, staggered `animation-delay`; the scene wrapper owns
opacity/transform, inner elements own their own staggered reveal.

```css
.film-scene{position:absolute;inset:22px 20px;opacity:0;
  animation:film-scene 10s cubic-bezier(.22,1,.36,1) infinite}
.film-scene.fs1{animation-delay:0s}
.film-scene.fs2{animation-delay:3.333s}
.film-scene.fs3{animation-delay:6.666s}
@keyframes film-scene{
  0%{opacity:0;transform:translateY(8px) scale(.985)}
  3%,30%{opacity:1;transform:none}
  33%,100%{opacity:0;transform:translateY(-6px) scale(1.01)}
}
/* typed line */
.film-type{display:inline-block;overflow:hidden;white-space:nowrap;max-width:0;
  animation:film-type 10s steps(52) infinite}
@keyframes film-type{0%,1%{max-width:0}13%,30%{max-width:52ch}33%,100%{max-width:0}}
/* staggered rows (nth-child delay) */
.film-row{opacity:0;animation:film-row 10s var(--ease-out) infinite}
@keyframes film-row{0%,33%{opacity:0;transform:translateY(6px)}
  38%,60%{opacity:1;transform:none}64%,100%{opacity:0}}
/* gauge / bar fill */
.film-bar i{display:block;height:100%;width:0;animation:film-bar 10s var(--ease-out) infinite}
@keyframes film-bar{0%,68%{width:0}78%,96%{width:72%}100%{width:0}}
```

**Critical:** because scenes overlap in time, verify that **exactly one** scene
has non-zero opacity at every timeline point (see freeze-and-seek below).

**Sizing:** give the stage a `min-height` matched to the *tallest* scene's real
content height (measure it), not a guessed value — an over-tall stage reads as a
mostly-empty frame in review.

## CSS scroll-driven draw (no JS)

```css
@supports (animation-timeline: view()){
  .spark polyline{stroke-dasharray:1;stroke-dashoffset:1;
    animation:draw linear both;animation-timeline:view();
    animation-range:entry 25% cover 45%}
  @keyframes draw{to{stroke-dashoffset:0}}
}
```

## Freeze-and-seek: inspect or capture a specific frame

Animations do not advance in background/headless tabs and `requestAnimationFrame`
never fires. Pause + seek with the Web Animations API, then read styles or capture:

```python
# browser_exec
js('''(() => {
  document.querySelectorAll('.film-scene, .film-bar i, .film-row')
    .forEach(el => el.getAnimations().forEach(a => { a.pause(); a.currentTime = 5000; }));
  return 'frozen';
})()''')
# now getComputedStyle(...).opacity is stable; capture the viewport here
```

Confirm exclusivity across the whole timeline:

```python
res = js('''(() => {
  const scenes=[...document.querySelectorAll('.film-scene')];
  const anims=scenes.map(s=>s.getAnimations().find(a=>a.animationName==='film-scene'));
  const out=[];
  [0,1000,3000,4000,6000,7000,9000].forEach(t=>{
    anims.forEach(a=>{ if(a) a.currentTime=t; });
    out.push({t, o: scenes.map(s=>+getComputedStyle(s).opacity.slice(0,4))});
  });
  return JSON.stringify(out);
})()''')
# every row must have exactly one value > 0.05
```

## Verify reduced motion (emulate, then assert)

```python
cdp("Emulation.setEmulatedMedia", features=[{"name":"prefers-reduced-motion","value":"reduce"}])
js("getComputedStyle(document.querySelector('.film-scene')).animationName")   # 'none'
js("getComputedStyle(document.querySelector('.film-scene.fs1')).opacity")     # '1' — static fallback shown
cdp("Emulation.setEmulatedMedia", features=[])
```

## Verify the pause toggle

```python
js("document.getElementById('motion-toggle').click()")
js('''JSON.stringify({
  paused: document.documentElement.classList.contains('motion-paused'),
  pressed: document.getElementById('motion-toggle').getAttribute('aria-pressed'),
  film: getComputedStyle(document.querySelector('.film-scene')).animationPlayState,
  marquee: getComputedStyle(document.querySelector('.marquee-track')).animationPlayState
})''')  # film + marquee must both read 'paused', pressed must be 'true'
```

## Accessible off-canvas drawer (a motion-adjacent component worth getting right)

- `role="dialog"` + `aria-modal="true"`; the trigger carries `aria-expanded` +
  `aria-controls`.
- Closed state is `inert` (not just off-screen); open removes `inert`, moves focus
  to the close button, and adds a `keydown` handler for `Escape` + a Tab focus trap.
- Add the `.open` classes **synchronously** on open (the panel is already laid out
  via `transform`, so the transition still runs) — a `requestAnimationFrame` hop is
  skipped in background tabs and leaves the drawer in an inconsistent state.
- On close, restore focus to the trigger and re-add `inert`.

## Accordion morph (progressive enhancement, no height measurement)

Collapse a panel without ever measuring its height: animate `grid-template-rows`
between `0fr` and `1fr`. Content stays in the DOM; without JS every panel is open,
so a failed script never hides content.

```css
/* Default (no JS): panels open, affordance hidden */
.stat-panel{display:grid;grid-template-rows:1fr}
.stats:not(.stats--ready) .stat-arrow{display:none}

/* JS adds .stats--ready to switch the collapsed mode on */
.stats--ready .stat-panel{grid-template-rows:0fr;
  transition:grid-template-rows .42s cubic-bezier(.22,1,.36,1)}
.stats--ready .stat.is-active .stat-panel{grid-template-rows:1fr}
.stat-panel-in{overflow:hidden}  /* the grid child MUST clip, or 0fr still shows content */
```

Markup: the header is a `<button aria-expanded aria-controls>` inside a heading
element; the panel is `role="region" aria-labelledby`; keep one row open by default.

Verify by disabling the transition first — a background/headless tab does not run
a CSS *transition*, so the height reads as frozen and looks like a broken toggle:

```python
js("document.querySelectorAll('.stat-panel').forEach(p=>p.style.transition='none')")
js("document.getElementById('stat-h3').click()")
js("[...document.querySelectorAll('.stat-panel')].map(p=>p.getBoundingClientRect().height)")
# assert the clicked panel has height>0 and the previously-open one is 0
```

## Heading order is part of the audit

A section whose cards use `<h3>` but that has no `<h2>` (a stats strip between two
sections, say) makes the outline jump H1→H3. Add an `<h2 class="sr-only">` to the
section so the sequence stays H1→H2→H3. Assert the tag *sequence*, not just the
`h1` count.
