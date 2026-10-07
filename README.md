# Hermes Skills Export

Exported: 2026-10-07
Source profile skills dir: `~/.hermes/skills`  (Windows: `%LOCALAPPDATA%\\hermes\\skills`)
Skills: **86** skill directories  (plus nested reference SKILL.md files)
Total size: ~7.5 MB

## Layout
The folder mirrors the source skills directory exactly:
    <category>/<skill-name>/SKILL.md      e.g. creative/landing-page-design/SKILL.md
    <category>/<skill-name>/references/   (support files, scripts/, data/, templates/)
Skills with no category sit at the top level, e.g. `backend-api-testing/SKILL.md`.

Categories: apple, autonomous-ai-agents, creative, devops, email, media, note-taking, productivity, research, social-media, software-development, web

## How to import into another Hermes agent

### Option A - copy the files (works for ALL skills, recommended)
Skills are plain directories; Hermes just reads them.

    # 1. On the other machine, find its skills dir:
    #    Linux/macOS: ~/.hermes/skills     Windows: %LOCALAPPDATA%\hermes\skills
    # 2. Copy each category folder in, preserving structure:
    cp -r hermes-skills-export/* <target-skills-dir>/
    # Windows PowerShell:
    #   Copy-Item .\hermes-skills-export\* "$env:LOCALAPPDATA\hermes\skills\" -Recurse -Force

    # 3. Verify
    hermes skills list

This is the only route that carries builtin, local and hub skills together, and it
also brings the support files (references/, scripts/, data/, templates/).

### Option B - snapshot (only hub/URL-installed skills)
`hermes skills snapshot export` only records skills installed from a registry
(skills.sh / a URL). Builtin and local skills are NOT included. Use it only to
reproduce the registry-installed set:

    hermes skills snapshot import hermes-skills-snapshot.json

The file `hermes-skills-snapshot.json` in this bundle is exactly that: the one
hub/URL skill in the source profile (`landing-page-design`).


## Import straight from this GitHub repo

    git clone --depth 1 https://github.com/WajbihMasir/skill-hermes.git
    # then copy the category folders into your skills dir:
    #   Linux/macOS: ~/.hermes/skills
    #   Windows:     %LOCALAPPDATA%\hermes\skills
    cp -r skill-hermes/* "$HOME/.hermes/skills/" 2>/dev/null || true
    # Windows PowerShell:
    #   Copy-Item .\skill-hermes\* "$env:LOCALAPPDATA\hermes\skills\" -Recurse -Force
    hermes skills list

## Notes
- `MANIFEST.json` lists every skill: name, category, path, file count, bytes.
- Builtin skills are re-seeded by Hermes itself on a fresh profile; copying them
  over is still safe and preserves any local edits.
- Excluded on purpose: `.hub/` cache (~48 MB), `.locks/`, `.usage.json`,
  `.curator_*` runtime state - none are needed to import skills.
