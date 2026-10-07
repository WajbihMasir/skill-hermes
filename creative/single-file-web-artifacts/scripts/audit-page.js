// Browser probe for a single-file HTML artifact.
// Run via browser_exec:  print(js(open(r"<skill-dir>/scripts/audit-page.js").read()))
// Returns a JSON string. Install an error listener first:
//   js("window.__errs=[];addEventListener('error',e=>__errs.push(e.message))")
// Then run once per viewport after cdp('Emulation.setDeviceMetricsOverride', ...).
// Contrast + overflow findings are heuristics: confirm the named element before editing.
(() => {
  const vw = document.documentElement.clientWidth;
  const vh = document.documentElement.clientHeight;

  const name = el => {
    const t = el.tagName.toLowerCase();
    const c = typeof el.className === 'string' ? el.className : ''; // SVG className is not a string
    return t + (c ? '.' + c.trim().split(/\s+/).join('.') : '');
  };

  const isVisible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 &&
           s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05;
  };

  // --- WCAG relative luminance / contrast ratio ---
  const lum = c => {
    const m = String(c).match(/[\d.]+/g);
    if (!m || m.length < 3) return null;
    const [r, g, b] = m.slice(0, 3).map(v => {
      v = v / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ratio = (a, b) => {
    const L1 = lum(a), L2 = lum(b);
    if (L1 === null || L2 === null) return null;
    const hi = Math.max(L1, L2), lo = Math.min(L1, L2);
    return +(((hi + 0.05) / (lo + 0.05)).toFixed(2));
  };
  const effBg = el => {
    let n = el;
    while (n && n !== document.documentElement) {
      const bg = getComputedStyle(n).backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
      n = n.parentElement;
    }
    return getComputedStyle(document.body).backgroundColor || 'rgb(255, 255, 255)';
  };

  // --- horizontal overflow culprits (ignores intentional scroll containers) ---
  const overflow = [];
  document.querySelectorAll('*').forEach(el => {
    if (!isVisible(el)) return;
    const r = el.getBoundingClientRect();
    if (r.right <= vw + 1 && r.left >= -1) return;
    let p = el.parentElement, inScroll = false;
    while (p) {
      const ox = getComputedStyle(p).overflowX;
      if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') { inScroll = true; break; }
      p = p.parentElement;
    }
    if (inScroll) return;
    overflow.push({
      el: name(el),
      left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width),
      minWidth: getComputedStyle(el).minWidth,
      inlineStyle: el.getAttribute('style') || ''   // inline style outranks media queries
    });
  });

  // --- measured contrast failures ---
  const lowContrast = [];
  document.querySelectorAll('p,h1,h2,h3,h4,h5,h6,a,li,span,dt,dd,label,button,td,th,small,code,figcaption,blockquote').forEach(el => {
    if (!isVisible(el)) return;
    const txt = (el.textContent || '').trim();
    if (!txt) return;
    const s = getComputedStyle(el);
    const size = parseFloat(s.fontSize);
    const weight = parseInt(s.fontWeight, 10) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const need = large ? 3.0 : 4.5;
    const cr = ratio(s.color, effBg(el));
    if (cr !== null && cr < need) {
      lowContrast.push({
        el: name(el), text: txt.slice(0, 40),
        ratio: cr, need, fontSize: Math.round(size)
      });
    }
  });

  // --- tap targets below 44px ---
  const smallTargets = [];
  document.querySelectorAll('a,button,input,select,textarea,[role="button"]').forEach(el => {
    if (!isVisible(el)) return;
    const r = el.getBoundingClientRect();
    if (r.width < 44 || r.height < 44) {
      smallTargets.push({ el: name(el), w: Math.round(r.width), h: Math.round(r.height) });
    }
  });

  const reducedMotion = [...document.styleSheets].some(ss => {
    try { return [...ss.cssRules].some(r => r.conditionText && /prefers-reduced-motion/.test(r.conditionText)); }
    catch (e) { return false; }   // cross-origin sheet (e.g. Google Fonts)
  });

  return JSON.stringify({
    viewport: vw + 'x' + vh,
    horizontalScroll: document.documentElement.scrollWidth > vw,
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: vw,
    overflowCulprits: overflow.slice(0, 10),
    lowContrast: lowContrast.slice(0, 12),
    smallTapTargets: smallTargets.slice(0, 10),
    imgWithoutAlt: document.querySelectorAll('img:not([alt])').length,
    h1Count: document.querySelectorAll('h1').length,
    hasReducedMotionBlock: reducedMotion,
    jsErrors: (window.__errs || [])
  }, null, 1);
})()
