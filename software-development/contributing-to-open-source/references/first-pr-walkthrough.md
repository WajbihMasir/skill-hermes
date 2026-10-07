# First-PR walkthrough (for a newcomer)

Hand this to a user who has never contributed to GitHub before. It assumes only
git and a GitHub account. Replace `<owner>/<repo>` and `<branch>` as needed.

## Setup (once)

```bash
git --version   # if missing, install git first
git config --global user.name "Their Name"
git config --global user.email "their@email"   # the email on their GitHub account
```

## The loop

1. **Fork** — on the repo page, click Fork → Create fork. Their copy now lives
   at `github.com/<their-user>/<repo>`.
2. **Clone** — copy the HTTPS URL of *their fork*:
   ```bash
   git clone https://github.com/<their-user>/<repo>.git
   cd <repo>
   git remote add upstream https://github.com/<owner>/<repo>.git
   ```
   `origin` = their fork; `upstream` = the original.
3. **Branch** — never work on `main`:
   ```bash
   git checkout -b docs/short-slug
   ```
4. **Edit** the file(s), then inspect before committing:
   ```bash
   git status
   git diff          # red = removed, green = added; read it every time
   ```
5. **Commit**:
   ```bash
   git add .
   git commit -m "docs: clarify the local setup steps"
   ```
   Message form: `type: imperative` (`fix:` / `feat:` / `docs:`).
6. **Push**:
   ```bash
   git push -u origin docs/short-slug
   ```
7. **Open the PR** — GitHub shows a "Compare & pull request" banner. Fill the
   repo's required body (see the umbrella SKILL.md step 5) and include the
   `Fixes #<N>` line so CI's issue-reference check passes.
8. **Review loop** — edit, `git add`, `git commit`, `git push` to the SAME
   branch. Do not force-push, do not open a second PR.
9. **Merge** — a maintainer merges; done.

## Phrases that confuse beginners — translate on sight

| Term | Meaning |
|---|---|
| `origin` | their fork |
| `upstream` | the original repo |
| `main` | the primary branch |
| `HEAD` | where they are now |
| CI / checks | automated test robots; red ❌ = fix, green ✅ = pass |
| merge | the change is accepted into the original |

## Framing that lands

- Nothing they do can break the upstream repo — their work is isolated on their
  fork/branch until a maintainer merges. Say this early.
- A first PR may be a docs/typo fix; that is a real, valued contribution and
  the safest way to learn the review flow.
- Maintainers are humans who welcome help; asking a question in the issue thread
  is the correct move, not a failure.
