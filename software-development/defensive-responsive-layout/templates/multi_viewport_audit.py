"""Multi-viewport responsive & collapse/expand audit (template).

Copy into the project's tools/ and fill in PAGES with the app's routes.
Every check prints [PASS]/[FAIL] and the script exits non-zero on any failure.

Usage: python tools/responsive_audit.py [base_url]
"""

import sys
import time

from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"

# --- EDIT ME: (nav testid suffix, accordion group testid suffix) ----------------
PAGES = [
    ("run", "operations"),
    ("findings", "operations"),
    ("jobs", "operations"),
    ("settings", "admin"),
]

# Smallest supported width first — that is where overflow surfaces.
VIEWPORTS = [
    {"name": "Mobile (small)", "width": 360, "height": 740, "mobile": True},
    {"name": "Mobile (iPhone)", "width": 390, "height": 844, "mobile": True},
    {"name": "Tablet", "width": 768, "height": 1024, "mobile": False},
    {"name": "Laptop", "width": 1366, "height": 768, "mobile": False},
    {"name": "Desktop", "width": 1920, "height": 1080, "mobile": False},
    {"name": "Ultrawide", "width": 2560, "height": 1440, "mobile": False},
]

PASS, FAIL, ERR = [], [], []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print("  [PASS] %s %s" % (name, detail))
    else:
        FAIL.append(name)
        print("  [FAIL] %s %s" % (name, detail))


def overflow_of(page):
    """Overflow on the window AND inside the content box.

    The window check alone false-greens: a fixed sidebar absorbs the squeeze and
    the document never overflows while <main> is crushed.
    """
    return page.evaluate(
        """() => {
            const d = document.documentElement;
            const m = document.querySelector('main');
            return {
                doc: Math.max(0, d.scrollWidth - d.clientWidth),
                main: m ? Math.max(0, m.scrollWidth - m.clientWidth) : 0,
                mainW: m ? m.clientWidth : 0,
            };
        }"""
    )


def widest_offenders(page, limit=8):
    """Elements whose right edge exceeds <main> — names the real culprit."""
    return page.evaluate(
        """(limit) => {
            const m = document.querySelector('main');
            if (!m) return [];
            const mr = m.getBoundingClientRect().right;
            const out = [];
            m.querySelectorAll('*').forEach((el) => {
                const r = el.getBoundingClientRect();
                if (r.right > mr + 2) {
                    out.push({tag: el.tagName,
                              cls: (el.className || '').toString().slice(0, 70),
                              w: Math.round(r.width),
                              txt: (el.textContent || '').trim().slice(0, 40)});
                }
            });
            return out.slice(0, limit);
        }""",
        limit,
    )


def test_collapse_cycle(browser):
    print("\n[1] Desktop — collapse/expand cycle")
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(700)

    sidebar = page.locator("[data-testid='sidebar']")
    toggle = page.locator("[data-testid='sidebar-toggle']")

    initial = sidebar.bounding_box()
    check("sidebar starts expanded", initial and initial["width"] > 200,
          "(width=%s)" % (initial["width"] if initial else "?"))

    toggle.click()
    page.wait_for_timeout(500)
    collapsed = sidebar.bounding_box()
    check("sidebar collapses", collapsed and collapsed["width"] <= 80,
          "(width=%s)" % (collapsed["width"] if collapsed else "?"))

    # THE critical assertion: the restore control must remain reachable.
    tb = toggle.bounding_box()
    check("restore toggle still on screen",
          tb is not None and tb["y"] >= 0 and tb["y"] + tb["height"] <= 900,
          "(y=%s, viewport=900)" % (tb["y"] if tb else "?"))

    toggle.click()
    page.wait_for_timeout(500)
    back = sidebar.bounding_box()
    check("expands via footer toggle", back and back["width"] > 200)

    # Second affordance: the app should expose a header/topbar toggle too.
    toggle.click()
    page.wait_for_timeout(400)
    alt = page.locator("[data-testid='desktop-sidebar-toggle']")
    if alt.count():
        check("header toggle visible when collapsed", alt.is_visible())
        alt.click()
        page.wait_for_timeout(500)
        again = sidebar.bounding_box()
        check("expands via header toggle", again and again["width"] > 200)

    # The nav rail must SCROLL, never overflow-visible (which grows the rail and
    # pushes the footer off-screen).
    nav_state = page.evaluate(
        """() => { const n = document.querySelector("[data-testid=sidebar-nav]")
                   || document.querySelector("nav");
                   return n ? getComputedStyle(n).overflowY : null; }"""
    )
    if nav_state:
        check("nav rail scrolls", nav_state in ("auto", "scroll"),
              "(overflow-y=%s)" % nav_state)
    ctx.close()


def test_viewports(browser):
    print("\n[2] Multi-viewport — zero overflow")
    for vp in VIEWPORTS:
        ctx = browser.new_context(
            viewport={"width": vp["width"], "height": vp["height"]})
        page = ctx.new_page()
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(900)
        ov = overflow_of(page)
        label = "%s %dx%d" % (vp["name"], vp["width"], vp["height"])
        check("%s — no window overflow" % label, ov["doc"] <= 1, "(doc=%s)" % ov["doc"])
        check("%s — no content overflow" % label, ov["main"] <= 4, "(main=%s)" % ov["main"])
        if vp["mobile"]:
            menu = page.locator("[data-testid='sidebar-mobile-toggle']")
            if menu.count() and menu.is_visible():
                menu.click()
                page.wait_for_timeout(450)
                backdrop = page.locator("[data-testid='sidebar-backdrop']")
                check("%s — backdrop shown" % label, backdrop.is_visible())
                if backdrop.is_visible():
                    # Click the VISIBLE strip: the element's centre is under the
                    # drawer, so a normal click retries until it times out.
                    box = backdrop.bounding_box()
                    if box:
                        page.mouse.click(box["x"] + box["width"] - 20,
                                         box["y"] + box["height"] / 2)
                    page.wait_for_timeout(500)
                    check("%s — backdrop closes drawer" % label,
                          not page.locator("[data-testid='sidebar-backdrop']").is_visible())
        ctx.close()


def test_all_pages_smallest(browser):
    """Every route at the smallest width — where offenders actually appear."""
    width = VIEWPORTS[0]["width"]
    print("\n[3] All routes at %dpx" % width)
    ctx = browser.new_context(viewport={"width": width, "height": 844})
    page = ctx.new_page()
    page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(800)

    bad = []
    for tab, group in PAGES:
        try:
            menu = page.locator("[data-testid='sidebar-mobile-toggle']")
            if menu.count() and menu.is_visible():
                box = page.locator("[data-testid='sidebar']").bounding_box()
                if box and box["x"] < 0:
                    menu.click()
                    page.wait_for_timeout(400)
            t = page.locator("[data-testid='nav-group-toggle-%s']" % group)
            if t.count() and t.first.get_attribute("aria-expanded") == "false":
                t.first.click()
                page.wait_for_timeout(250)
            nav = page.locator("[data-testid='nav-%s']" % tab)
            if not nav.count():
                continue
            nav.first.click(force=True)
            page.wait_for_timeout(1800)
            ov = overflow_of(page)
            if ov["doc"] > 4 or ov["main"] > 8:
                bad.append({"tab": tab, "doc": ov["doc"], "main": ov["main"],
                            "offenders": widest_offenders(page, 4)})
        except Exception as exc:
            bad.append({"tab": tab, "error": str(exc)[:80]})

    if bad:
        for b in bad:
            print("    offender: %s" % b)
    check("all %d routes fit %dpx" % (len(PAGES), width), not bad)
    ctx.close()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            test_collapse_cycle(browser)
            test_viewports(browser)
            test_all_pages_smallest(browser)
        finally:
            browser.close()
    print("\n" + "=" * 66)
    print("RESULT: %d passed, %d failed, %d errors" % (len(PASS), len(FAIL), len(ERR)))
    for f in FAIL:
        print("  FAILED: " + f)
    print("=" * 66)
    return 1 if (FAIL or ERR) else 0


if __name__ == "__main__":
    sys.exit(main())
