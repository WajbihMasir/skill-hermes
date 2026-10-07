---
name: contributing-to-open-source
description: "Contribute to a third-party OSS repo end to end."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, open-source, pull-requests, issues, contribution, beginners]
    category: software-development
    related_skills: [github, codebase-inspection]
---

# Contributing to open source

Advising on, planning, or making a contribution to a repo you do not own:
picking an issue, proposing a feature, or walking a newcomer through their
first pull request. The repo's own rules gate every PR, so learn them before
proposing or building anything.

## When to Use

- "I want to contribute to this repo, what should I build?"
- Picking a good issue or proposing a feature for a repo you do not own.
- Walking a newcomer through their first fork/branch/PR.
- Checking whether a planned contribution is wanted before investing effort.
- Finding a safe, unclaimed first task when the labelled beginner issues are all
  taken.

## Procedure

### 1. Recon the repo's rules first

Fetch the contribution docs and read them before suggesting anything. Raw text
via `curl -s https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>`:
`CONTRIBUTING.md`, `AGENTS.md`, `ARCHITECTURE.md`,
`.github/PULL_REQUEST_TEMPLATE.md`, and `SECURITY.md` / `THREAT_MODEL.md` when
present. These decide branch names, commit style, the required PR body shape,
and which files you must not touch. Done when the branch/commit/PR conventions
and any hard CI gates are known.

### 2. Inventory open work with its state

`gh issue list --state open --json number,title,labels,assignees` and
`gh pr list --state open --json number,title,author`. Classify by the repo's own
label axes (commonly type / priority / stage / role). Translate the stage axis
before starting: `now` = ready to build, `next` = sized but waiting, `later` =
still has an open question — ask in the thread first, because a PR that guesses
the answer usually gets closed. Done when each candidate issue has a stage and a
role.

### 3. Find the invited entry points

Labels such as `good first issue` and `help wanted` are the maintainers
explicitly asking for outside help. Filter to unassigned (`--assignee ""`) — an
assignee is the only signal of claimed work, because a branch on someone's fork
is invisible from the repo. Done when you have a shortlist of unassigned,
stage-appropriate issues.

### 4. Check for an existing PR covering the issue

`gh pr list --search "#<N>" --state all`. A single large sweep PR can cover many
issues at once, so an issue showing no PR still may already be in flight. Done
when you know every open PR touching the candidate issue.

### 5. Confirm no open PR already edits the target file

Assignees and issue references are not enough: a single sweep PR can rewrite
most of a docs tree, so a target file inside that set conflicts even when its
issue shows no PR. Union the changed files of every open PR (`gh pr list
--state open --json number`, then `gh pr view <n> --json files`, or the
`/pulls/<n>/files` API) into one set and pick a target outside it. Done when the
target file is absent from the union of every open PR's files.

### 6. Match the required PR body format exactly

Read the PR template and any in-repo skill describing the body shape. Repos
frequently fail CI on a PR that does not reference an issue or does not follow
the mandated format; put `Fixes #<N>` (or the repo's equivalent) in the body.
Some repos mandate a specific short, scannable format (e.g. outcome-first
summary, before/after, why-safe, test plan) rather than free prose — copy the
template verbatim and fill it.

### 7. Ship or guide the loop

Once the issue is claimed, the loop is: fork → clone → branch (`type/slug`,
include the issue number) → edit → `git diff` → commit (`type: imperative`) →
push → open the PR referencing the issue → answer review on the same branch
(push follow-up commits, do not force-push, do not open a second PR) → merge.
Run the repo's declared quality gates (lint/test/typecheck) before pushing.
See `references/first-pr-walkthrough.md` for the step-by-step commands to hand
a beginner. See `references/finding-a-safe-first-task.md` for the scan recipe
when the labelled beginner issues are all taken.

## When the invited issues are all claimed

`good first issue` and `help wanted` are usually one or two per repo and are
often taken; a single audit issue can absorb a dozen. Do not stop there — an
unfiled docs or config defect is still a valid first contribution. Scan for a
real, verifiable one (recipe: `references/finding-a-safe-first-task.md`):

- Cross-reference a docs list against the code it describes: a worker or
  feature directory that exists but is missing from a channel list, a table, or
  a sidebar. Highest signal, and the fix is unambiguous.
- Run `codespell` over the docs tree for typos.
- Resolve every internal link target against the set of real pages; treat
  nested directories as valid page prefixes or you will flag working links as
  broken.
- Diff the docs navigation file (e.g. a `meta.json` sidebar) against the actual
  page files to find orphan or missing entries.

Open an issue for the defect first, then PR against it — an unfiled fix still
needs an issue for the CI reference check. A docs-only change is the safest
first PR: check the CI workflow's `paths-ignore`, since docs-only PRs are often
skipped by code checks and cannot go red on lint or tests.

## Suggesting a feature to a repo you do not own

- Propose through a new issue first; do not open a feature PR that guesses at a
design question the maintainers have left open.
- Sweep existing issues and PRs for the same idea before proposing — duplicates
  get closed and cost the maintainer time.
- Read a couple of existing feature proposals to match the repo's tone, scope,
  and level of detail (acceptance criteria, non-goals).

## Teaching a first-time contributor

- Lead with the isolation fact: everything happens on their fork and branch, so
  nothing they do can break the upstream repo until a maintainer merges. This is
  the single most common beginner anxiety.
- Claim the issue by commenting and waiting to be assigned **before** building.
- A first PR does not need to be a feature: documentation and typo fixes are
  legitimate and valued, and are the safest way to learn the review process.
- Teach in the user's own language and at their stated level; ask how deep they
  want to go rather than dumping the whole process at once.

## Pitfalls

- Suggesting a feature without first sweeping existing issues and PRs for it.
- Restating the repo map or its `AGENTS.md` in your answer — those are
  always-loaded or fetched on demand, not the answer.
- Fetching API JSON that carries user text (issue/PR bodies) and parsing it from
  stdout: raw control characters (e.g. CR in bodies) corrupt it and break
  `json.loads`. Write it to a file and parse the file instead — and do the write
  and the read in the SAME tool. On Windows the `execute_code` kernel and the
  `terminal` shell do not share `/tmp`: a file written by a shell
  `curl -o /tmp/x.json` is invisible to Python `open('/tmp/x.json')`. Fetch and
  read inside `execute_code` with `urllib`/`open`, or use an absolute path both
  tools agree on.
- Reporting a contribution as possible without checking that the issue is
  unassigned and has no open PR.
- Reporting a doc or config file as safe to edit without checking whether an
  open PR already touches that exact file — an assignee check misses a sweep PR
  that rewrites the whole docs tree.
- Treating every entry from the issues API as an issue: it returns PRs too.
  Filter by the presence of a `pull_request` key.

## Verification

- [ ] Contribution docs read; branch/commit/PR conventions and CI gates known.
- [ ] Candidate issue is unassigned, stage-appropriate, and has no open PR.
- [ ] Required PR body format (and `Fixes #<N>` line) copied from the template.
- [ ] Target file is outside the union of every open PR's changed files.
- [ ] Quality gates run before pushing.
