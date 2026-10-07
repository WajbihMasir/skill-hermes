---
name: hermes-skill-library
description: "Install and consolidate Hermes skills; cut token cost."
version: 0.1.0
author: Shalahuddin, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, install, consolidation, library, token-cost, curation]
    related_skills: [hermes-agent-skill-authoring, hermes-agent]
---

# Hermes Skill Library

Install third-party skills into a Hermes profile, and consolidate an already-bloated
library down to class-level umbrellas. Covers the install routes, the per-turn cost
model that decides whether a skill is worth keeping, and the protected-skill
boundary. Does not cover authoring in-repo SKILL.md files — that is
`hermes-agent-skill-authoring`.

## When to Use

- User asks to install / add / try a skill from GitHub, a URL, or a pasted list
- User asks to "clean up", "consolidate", "merge", or "there are too many skills"
- You are about to delete, move, or reorganize installed skills
- Don't use for: writing a new in-repo SKILL.md (use `hermes-agent-skill-authoring`)

## The Cost Model (read this before adding anything)

**Every installed skill's `description` is injected into the system prompt and paid on
EVERY turn, whether or not the skill ever loads.** The body is free until loaded; the
description is not. A library's description total is a permanent tax on every message.

Measure before and after any change:

```bash
python scripts/skill_description_cost.py --top 20
```

Rules of thumb:

| Description length | Read |
|---|---|
| ≤ 60 chars | healthy (matches the authoring hardline) |
| 60–250 chars | acceptable for a broad umbrella |
| > 250 chars | a per-turn smell — trim it, or fold the skill into an umbrella |

A realistic bloat case: ten overlapping design skills ≈ 1,000 tokens/turn. Consolidating
to four ≈ 200. **The goal is one umbrella per class, with narrow techniques moved into
that umbrella's `references/` — not a flat list of one-topic skills.**

When the user has already collected many skills for one class, consolidation is usually
the right answer to "should I add more?" — say so plainly instead of installing more.

## Procedure: Install a Third-Party Skill

### Step 1 — Verify the source exists before acting on it

A research summary, a chat paste, or a recommendation list can name repos that do not
exist. Check every one before planning around it:

```bash
for r in owner/repo1 owner/repo2; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://api.github.com/repos/$r")
  echo "$code  $r"
done
```

`200` = real. Anything else, drop it from the plan and tell the user.

### Step 2 — Pick the install route

| Situation | Route |
|---|---|
| Single `SKILL.md`, no support files | `hermes skills install <raw-url>/SKILL.md --category <cat> --yes` |
| Indexed on skills.sh | `hermes skills search <name>`, then `hermes skills install skills-sh/<owner>/<repo>/<skill>` |
| Has `references/`, `scripts/`, `data/`, or `templates/` | clone and copy the skill directory (Step 3) |

`hermes skills inspect <identifier>` previews a skill without installing it — use it to
confirm the name and description before committing. `hermes skills install` runs a
security scan and quarantines before install; a `SAFE` verdict is expected for
mainstream repos.

### Step 3 — Multi-file skills: clone and copy the directory

A URL install brings `SKILL.md`; a skill whose value is its data or scripts needs the
whole directory:

```bash
git clone --depth 1 -q https://github.com/<owner>/<repo>.git repo
cp -r repo/<path-to-skill>/. <skills_dir>/<category>/<name>/
```

Copy only what the skill needs — `SKILL.md`, `references/`, `scripts/`, `data/`,
`templates/`. **Drop `demo/` and asset folders**: they are often the bulk of the repo
(tens of MB of screenshots and video) and the agent cannot read images anyway. A skill
that was 20 MB shrinks to under 100 KB with no loss of usable content.

### Step 4 — Normalize for Hermes

Four things break on skills written for another agent, in order of how often they bite:

1. **Claude-Code-only variables do not resolve.** Rewrite `${CLAUDE_PLUGIN_ROOT}`,
   `claude mcp ...`, and similar to Hermes equivalents (the skill's own directory, the
   `browser_exec` helpers) or the bundled script silently fails to run.
2. **Frontmatter `name:` must match the directory name.** If they differ, fix both.
3. **Two repos can ship the same `name:`.** The loader then cannot tell them apart.
   Rename the directory AND the frontmatter `name:`, and shorten the description.
4. **A description over 60 chars** — trim it while you are already editing the file.

### Step 5 — Verify

```bash
hermes skills list            # present and enabled
hermes skills inspect <name>  # frontmatter parses
```

Then load it with `skill_view(<name>)` and, if it ships a script, **run that script
once** to prove it works before reporting success. A skill that parses but whose tool
crashes on invocation is not installed.

## Procedure: Consolidate a Bloated Library

1. **Inventory.** `hermes skills list`, then `python scripts/skill_description_cost.py`
   to rank by cost. Note which entries share a trigger — those are duplicates.
2. **Group by class.** If several skills answer the same request, they are one class.
3. **Pick the surviving umbrella.** Prefer a bundled skill: its `references/` inherits
   the same update protection as the skill itself (see Protected Skills below).
4. **Move content, do not summarize it.** Copy each absorbed skill's body verbatim into
   `references/<topic>.md` under the umbrella, strip its YAML frontmatter, and add a
   short header naming what it is and where it came from. Summarizing loses exactly the
   code recipes that made the skill worth keeping.
5. **Add one pointer line per new reference** in the umbrella's SKILL.md, saying what it
   contains and that it should be read on demand rather than upfront.
6. **Back up, then delete.** See Backups below. Delete only after the copy is verified.
7. **Re-verify:** every frontmatter still parses, the description total dropped, and no
   `references/` link points at a moved or deleted file.

## Backups

Copy to a **permanent** location, never `%TEMP%` or `/tmp` — those are cleared on
restart, so a "backup" there is lost exactly when it is needed:

```bash
cp -r <skills_dir>/<category>/<name> ~/.hermes/backups/<label>/<name>/
```

Verify the copy exists and is non-empty **before** deleting the original.

## Protected Skills — Know the Boundary

The `Source` column in `hermes skills list` tells you what you may touch:

| Source | Meaning | Autonomous writes |
|---|---|---|
| `builtin` | bundled, shipped with Hermes | no |
| `url` / `skills.sh` | hub-installed | no |
| `local` | created by a user or a foreground agent | no (user-owned) |

If the only skills that need changing are protected, say so and recommend
`hermes curator adopt <name>` rather than attempting an edit.

Two consequences worth stating to the user:

- **A `url`-sourced skill is replaced wholesale by `hermes skills update`.** Do not put
  your own `references/` files under one — a later update deletes them. Put added
  material under a bundled or local skill instead.
- **Editing a bundled skill's files is safe** — the copy becomes `user-modified` and
  `hermes update` skips it, which is the protection working as intended.

## Pitfalls

1. **Do not run `hermes skills reset` to "clean up" an edited bundled skill.** It deletes
   the manifest entry and permanently removes the update-protection path, leaving the
   skill worse off than before. `user-modified` is the correct steady state. Mechanism
   in `hermes-agent-skill-authoring`.
2. **Do not trust a pasted list of repos.** Verify each with the API call in Step 1;
   confident-sounding summaries routinely name projects that do not exist.
3. **Do not install a skill whose description is already long without trimming it.** The
   cost is paid every turn forever, and it is invisible at install time.
4. **Do not summarize a skill's content when folding it into `references/`.** Move the
   file; a paraphrase drops the recipes.
5. **Do not leave the frontmatter `name:` out of sync with the directory name.** The
   loader keys on both.
6. **Do not assume PyYAML is importable.** Parse frontmatter with stdlib `re` — the
   interpreter you get may have neither `yaml` nor `ruamel.yaml`.
7. **Do not back up into a temp directory.** See Backups.

## Verification

- [ ] `hermes skills list` shows exactly the intended set
- [ ] `python scripts/skill_description_cost.py` run, total reported to the user
- [ ] Every new/changed skill loads via `skill_view`
- [ ] Directory name == frontmatter `name:` for every skill touched
- [ ] Any script a new skill ships was executed once successfully
- [ ] No `references/` link points at a moved or deleted file
- [ ] Backup exists at a permanent path before anything was deleted

## Support Files

- `scripts/skill_description_cost.py` — prints each installed skill's description length
  and the library total, worst first. Stdlib only, cross-platform. Run before and after
  any library change.
