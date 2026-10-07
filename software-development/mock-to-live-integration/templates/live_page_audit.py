"""
Per-page live-integration audit (template).

Drives every page of a dashboard against a running backend and asserts, per
page, that it: (a) rendered its root marker OR an honest empty state, (b)
actually called its API, and (c) produced zero console errors.

WHY a network log is required: a page backed by a mock fallback renders
perfectly. Only the request proves the data is real, and only the empty-state
case needs the request to distinguish "no data yet" from "broken wiring".

Copy into the project's tools/ dir, fill in PAGES, then:
    python tools/live_page_audit.py <frontend_url> <backend_url>
"""

import sys
import time

from playwright.sync_api import sync_playwright

FRONTEND = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
BACKEND = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000"

# (nav testid suffix, accordion group, expected root testid, required api fragment)
#   api fragment None = the page reads state fetched once at app mount (e.g. a
#   dashboard home that consumes shared context) — do not demand a per-tab call.
PAGES = [
    ("home", "main", "home-panel", None),
    ("items", "main", "items-panel", "/api/items"),
]


def main():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_context(viewport={"width": 1600, "height": 1000}).new_page()

        console_errors = []
        api_calls = []
        page.on("pageerror", lambda e: console_errors.append(str(e)[:200]))
        page.on("console", lambda m: console_errors.append(m.text[:200])
                if m.type == "error" else None)
        page.on("request", lambda r: api_calls.append(r.url) if "/api/" in r.url else None)

        page.goto(FRONTEND, wait_until="networkidle", timeout=60000)
        time.sleep(3)

        for tab, group, testid, api_frag in PAGES:
            console_errors.clear()
            api_calls.clear()
            status = {"tab": tab, "ok": False, "reason": ""}
            try:
                toggle = page.get_by_test_id("nav-group-toggle-%s" % group)
                if toggle.count() and toggle.first.get_attribute("aria-expanded") == "false":
                    toggle.first.click(force=True)
                    time.sleep(0.25)
                nav = page.get_by_test_id("nav-%s" % tab)
                if not nav.count():
                    status["reason"] = "nav item missing"
                    results.append(status)
                    continue
                # force=True: an accordion/sidebar mid-transition is "unstable"
                # to Playwright and a skipped click silently audits the PREVIOUS
                # page. Assert the root marker next, so a miss is caught here.
                nav.first.click(force=True)
                time.sleep(2.2)

                if not page.get_by_test_id(testid).count():
                    empty = page.locator("[data-testid$='-empty']")
                    if empty.count():
                        if api_frag and any(api_frag in u for u in api_calls):
                            status["ok"] = True
                            status["reason"] = "honest empty state (API called)"
                        elif api_frag:
                            status["reason"] = "empty state WITHOUT calling %s" % api_frag
                        else:
                            status["ok"] = True
                            status["reason"] = "honest empty state"
                        results.append(status)
                        continue
                    status["reason"] = "root testid %s not found" % testid
                    results.append(status)
                    continue

                if api_frag and not any(api_frag in u for u in api_calls):
                    status["reason"] = "no call to %s (hidden fallback?)" % api_frag
                    results.append(status)
                    continue

                if console_errors:
                    status["reason"] = "console errors: %s" % console_errors[:2]
                    results.append(status)
                    continue

                status["ok"] = True
                results.append(status)
            except Exception as exc:
                status["reason"] = "exception: %s" % str(exc)[:120]
                results.append(status)

        browser.close()

    ok = sum(1 for r in results if r["ok"])
    print("=" * 70)
    for r in results:
        print("  [%s] %-12s %s" % ("PASS" if r["ok"] else "FAIL", r["tab"], r["reason"]))
    print("=" * 70)
    print("E2E LIVE: %d/%d pages served real backend data" % (ok, len(results)))
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
