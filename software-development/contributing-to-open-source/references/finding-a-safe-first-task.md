# Finding a safe first task (when the labelled issues are taken)

`good first issue` / `help wanted` are typically one or two per repo and get
claimed fast. When they are gone, derive a task from a real, verifiable defect
nobody has filed. The rule: every claim must be checkable against the code or
the live site, and the target file must be outside every open PR.

## 1. Build the set of files open PRs already touch

```bash
gh pr list --state open --json number --jq '.[].number'   # then per PR:
gh pr view <n> --json files --jq '.files[].path'
```

Union all paths into one set. A single sweep PR can cover most of a docs tree —
this is the check that prevents a guaranteed conflict. Pick targets outside the
set.

## 2. Find an unclaimed issue (or the need for one)

The issues API returns issues *and* PRs mixed — filter by the presence of a
`pull_request` key before treating something as an issue. An issue is unclaimed
when no open PR references its number; search PR bodies, head-branch names, and
titles for `#<N>` (a `Fixes #N` in a body or a `type/<N>-slug` branch).

## 3. Scan docs for a verifiable defect

Cross-reference docs against the code — the strongest signal:

- List the real feature directories (e.g. `apps/platform/*`) and the docs lists
  that name them (channel lists, tables, sidebars). A directory that exists but
  is missing from a list is an unambiguous fix. Confirm the feature is real
  first: its source dir, its own docs page, and any hub-page mention.
- Typos: `codespell <docs-dir>` (install via `pip install codespell`).
- Internal links: extract `](/path)` targets and check each against the set of
  real pages. Treat a nested directory as a valid prefix, or you will flag
  working links as broken.
- Nav vs files: diff the sidebar file (e.g. `meta.json`) against the actual page
  files for orphans and missing entries.

Verify each candidate against the repo tree (the git trees API or `git ls-tree`)
and, when cheap, the live site (HTTP status of the rendered page) before
reporting it as a defect.

## 4. Prefer a docs-only change for a true first PR

Docs-only PRs are frequently exempted from code CI. Check the workflow files for
`paths-ignore` entries like `['**.md', 'docs/**', ...]` — if present, the code
checks (lint, tests, dead-code) will not run, so the PR cannot fail on them.

## 5. Open the issue, then the PR

Even an unfiled fix needs an issue, because CI often fails a PR with no issue
reference. File the issue with the exact `file:line` evidence, then branch
`docs/<slug>`, make the one-line change, and reference `Fixes #<N>`.
