#!/usr/bin/env python3
"""Report the per-turn token cost of the installed Hermes skills.

Every installed skill's frontmatter `description` is injected into the system prompt
and paid on EVERY turn, whether or not the skill ever loads. This ranks skills by
description length, worst first, so a bloated library is visible before you add more.

Stdlib only (no yaml / ruamel.yaml) and cross-platform.

Usage:
    python skill_description_cost.py                 # auto-detect skills dir
    python skill_description_cost.py <skills_dir>    # explicit dir
    python skill_description_cost.py --top 20        # only the 20 most expensive
"""

import argparse
import os
import re
import sys
from pathlib import Path

HEAVY = 250  # description length above which a skill is flagged


def default_skills_dir() -> Path:
    """Best-effort location of the profile's skills tree."""
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env) / "skills"
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/AppData/Local")
        return Path(base) / "hermes" / "skills"
    return Path.home() / ".hermes" / "skills"


def read_description(skill_md: Path):
    """Extract the frontmatter `description` value.

    Handles plain scalars, quoted scalars, and block scalars (``>-`` / ``|``).
    Returns None when the file has no usable frontmatter.
    """
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    close = re.search(r"\n---\s*\n", text[3:])
    if not close:
        return None

    collected, collecting, indent = [], False, None
    for line in text[3:close.start() + 3].splitlines():
        if collecting:
            if not line.strip():
                collected.append("")
                continue
            cur = len(line) - len(line.lstrip())
            if indent is None:
                indent = cur
            elif cur < indent:
                break
            collected.append(line.strip())
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m and m.group(1) == "description":
            val = m.group(2).strip()
            if val in (">", ">-", ">+", "|", "|-", "|+"):
                collecting = True
                continue
            return val.strip('"').strip("'")
    if collected:
        return " ".join(x for x in collected if x).strip()
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("skills_dir", nargs="?", default=None)
    ap.add_argument("--top", type=int, default=0,
                    help="show only the N most expensive skills")
    args = ap.parse_args(argv)

    root = Path(args.skills_dir) if args.skills_dir else default_skills_dir()
    if not root.is_dir():
        print(f"skills dir not found: {root}", file=sys.stderr)
        return 1

    rows = []
    for md in sorted(root.rglob("SKILL.md")):
        rel_parts = md.relative_to(root).parts
        if any(p.startswith(".") for p in rel_parts):  # .hub, quarantine, etc.
            continue
        desc = read_description(md)
        name = md.parent.name
        rel = md.parent.relative_to(root).as_posix()
        rows.append((name, -1 if desc is None else len(desc), rel))

    rows.sort(key=lambda r: -r[1])
    total = sum(max(r[1], 0) for r in rows)
    shown = rows[:args.top] if args.top else rows

    print(f"{'CHARS':>6}  {'SKILL':32s} PATH")
    for name, n, rel in shown:
        if n < 0:
            note = "  <-- no description"
        elif n > HEAVY:
            note = "  <-- heavy, trim or fold into an umbrella"
        else:
            note = ""
        print(f"{n:6d}  {name:32s} {rel}{note}")

    if args.top and len(rows) > args.top:
        print(f"\n(showing top {args.top} of {len(rows)})")
    print(f"\n{len(rows)} skill(s) | total description cost {total} chars "
          f"(~{total // 4} tokens) paid EVERY turn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
