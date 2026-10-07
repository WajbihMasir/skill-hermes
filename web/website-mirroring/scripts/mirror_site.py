#!/usr/bin/env python3
"""Mirror a live page's frontend for offline use.

Usage:
    python mirror_site.py https://example.com/ ./mirror

Downloads the HTML plus every asset it references (HTML attributes, CSS url(),
JS string literals), saves it path-preserving, rewrites root-absolute paths to
relative so the tree is portable, strips analytics, and writes a start.bat.

Gotchas baked in:
  * Requests gzip only. Brotli bytes are not decoded by urllib and decode to
    mojibake.
  * JS string literals are rewritten by exact quote-wrapped replacement, never a
    bare regex on '/' (which corrupts them into invalid JS).
  * Bundled ES modules are blocked over file:// (CORS, origin 'null'), so the
    tree must be served over http -- hence the launcher.

Always verify the result against the live page with headless-Chrome screenshots
before claiming the mirror is identical (see SKILL.md step 9).
"""
import gzip
import os
import re
import sys
import urllib.request
from urllib.parse import urlparse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

ASSET_EXT = r"(?:png|jpe?g|webp|svg|gif|avif|ico|woff2?|css|js)"


def fetch(url, referer=None, timeout=60):
    headers = {"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data, resp.headers.get("Content-Type", "")


def save(out, path, data):
    p = os.path.join(out, path.lstrip("/").replace("/", os.sep))
    os.makedirs(os.path.dirname(p) or out, exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(data)
    return p


def mirror(page_url, out):
    parts = urlparse(page_url)
    origin = f"{parts.scheme}://{parts.netloc}"
    os.makedirs(out, exist_ok=True)

    html = fetch(page_url)[0].decode("utf-8", "replace")
    if not re.search(r"<h1[^>]*>\s*\S", html) and 'id="root"></div>' in html:
        print("WARNING: body looks client-rendered; snapshot the DOM with "
              "`chrome --headless=new --dump-dom` instead.")

    # --- enumerate asset refs from the HTML -------------------------------
    refs = set()
    for m in re.finditer(r'(?:src|href)="([^"]+)"', html):
        u = m.group(1)
        if u.startswith(origin):
            u = u[len(origin):]
        if u.startswith("/"):
            refs.add(u.split("#")[0])

    assets = {r for r in refs if not r.endswith((".md", ".txt", ".xml"))}
    queue = [r for r in refs if re.search(r"\.(css|js)$", r)]
    done = set()

    # --- crawl CSS/JS for deeper refs -------------------------------------
    while queue:
        a = queue.pop()
        if a in done:
            continue
        done.add(a)
        try:
            data, _ = fetch(origin + a, referer=page_url)
        except Exception as exc:  # noqa: BLE001
            print("  FAIL", a, exc)
            continue
        save(out, a, data)
        assets.add(a)
        text = data.decode("utf-8", "replace")
        if a.endswith(".css"):
            for u in re.findall(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', text):
                if u.startswith("/"):
                    queue.append(u.split("#")[0])
        elif a.endswith(".js"):
            for u in re.findall(r'["\'](/[A-Za-z0-9_\-/]+\.' + ASSET_EXT + r')["\']', text):
                queue.append(u)

    # --- download the remaining assets ------------------------------------
    for a in sorted(assets):
        if a in done:
            continue
        done.add(a)
        try:
            data, _ = fetch(origin + a, referer=page_url)
            save(out, a, data)
        except Exception as exc:  # noqa: BLE001
            print("  FAIL", a, exc)

    # --- rewrite the HTML --------------------------------------------------
    def fix(m):
        quote, path = m.group(1), m.group(2)
        if path.startswith("//"):
            return m.group(0)
        if os.path.exists(os.path.join(out, path.lstrip("/").replace("/", os.sep))):
            return f'{quote}="./{path.lstrip("/")}"'
        return f'{quote}="#"'

    html = re.sub(r'(href|src)="(/[^"]*)"', fix, html)
    html = re.sub(
        r'<script[^>]*(?:googletagmanager|cloudflareinsights)[^>]*>\s*</script>\s*',
        "", html)
    save(out, "/index.html", html.encode("utf-8"))

    # --- rewrite CSS + JS --------------------------------------------------
    for root, _dirs, files in os.walk(out):
        rel_dir = os.path.relpath(root, out)
        up = "" if rel_dir == "." else "../" * rel_dir.count(os.sep)
        for name in files:
            path = os.path.join(root, name)
            if name.endswith(".css"):
                text = open(path, encoding="utf-8").read()
                text = re.sub(r'url\((["\']?)/',
                              lambda m: f"url({m.group(1)}{up}", text)
                open(path, "w", encoding="utf-8").write(text)
            elif name.endswith(".js"):
                text = open(path, encoding="utf-8").read()
                for rel in assets:
                    for q in ('"', "'"):
                        text = text.replace(q + rel + q, q + "." + rel + q)
                open(path, "w", encoding="utf-8").write(text)

    # --- launcher ----------------------------------------------------------
    with open(os.path.join(out, "start.bat"), "w", encoding="utf-8") as fh:
        fh.write("@echo off\r\ncd /d \"%~dp0\"\r\n"
                 "start \"\" http://127.0.0.1:8777/index.html\r\n"
                 "python -m http.server 8777\r\n")

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _d, fs in os.walk(out) for f in fs)
    print(f"mirrored {len(done)} assets -> {out} "
          f"({total / 1048576:.2f} MB)")
    print("serve it, then screenshot-compare against the live page.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    mirror(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "./mirror")
