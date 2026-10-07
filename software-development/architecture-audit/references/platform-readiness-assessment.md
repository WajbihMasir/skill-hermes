# Platform Readiness Assessment

Scoring an existing codebase against an external platform's requirements: how
much of the target does it already serve, and what must be built to close the
gap. Produces a weighted scorecard plus a phased roadmap, not a rewrite plan.

Use when asked "how compatible is this project with X", "what percentage fit",
or "what do we need to build to be 100%".

## 1. Research the platform BEFORE scoring anything

Scoring against a half-understood platform produces confident nonsense. Gather,
in this order:

1. **The economics and the penalties.** What does success earn and what does
   failure cost? A platform where a bad submission is actively negative needs a
   different tool shape than one where it is merely ignored. Quantify it.
2. **The mandatory requirements.** What must be present for a submission to be
   accepted at all, and what recently changed? Requirements with a date attached
   ("from <date>, X is required") are the ones that invalidate existing tooling.
3. **The data model of the target.** How does the platform represent the things
   the tool must consume or produce? Enumerate the types, and note which carry
   independent flags rather than one boolean.
4. **The API.** Auth scheme, endpoints, pagination, rate limits. Verify the auth
   scheme — basic-auth vs bearer vs per-account token changes the client shape.
5. **The policy on automation.** Most platforms that accept machine-assisted work
   publish conditions for it. Quote the platform's own words; paraphrase loses
   the operative constraint.
6. **What gets accounts banned.** Enumerate the prohibited behaviours explicitly;
   they become hard gates, not warnings.

Prefer primary sources (the platform's own docs and policy pages). When a page
refuses to render for a fetch service, fall back to `curl` plus a tag-stripping
one-liner rather than skipping the source. **State in the write-up which claims
came from primary sources and which came from secondary reporting** — a readiness
score resting on second-hand policy summaries is not trustworthy.

## 2. Score with a weighted table, and show the raw table

```
| # | Dimension | Weight | Score | Weighted |
|---|-----------|--------|-------|----------|
| D1 | <capability> | 22% | 50% | 11.0 |
| ...
|   | TOTAL | 100% | | **41%** |
```

Rules that keep the number honest:

- **Every sub-score needs stated evidence**, so a reader can disagree with the
  score rather than just the conclusion. Cite the module, test, or measurement
  behind each one.
- **Publish the weights as your choice, not a fact.** State plainly that a
  different weighting yields a different total and that the raw table is there so
  it can be re-weighted. A single number with hidden weights is unfalsifiable.
- **Weight by what determines success, not by what is easy to build.** The
  dimension the tool is missing entirely often deserves more weight than the one
  it has half-finished.
- **If two questions are being asked, answer both.** "Can this operate on the
  platform end-to-end" and "is this useful to a human operator today" have
  different answers. Report both numbers explicitly instead of averaging them
  into one misleading figure.
- **Score what exists, not what is planned.** A module that is present but never
  exercised scores as missing until a test proves it runs.
- **Distinguish a strong dimension from a large one.** A safety/compliance layer
  is often the highest-scoring and least glamorous dimension; say so, because it
  is also the hardest to retrofit later.

## 3. The gap analysis is the deliverable

Group the gaps by what they block, and name the phase that closes each:

- **Blocking** — the platform cannot be used at all without it.
- **Protective** — the platform can be used, but the account/asset is at risk.
- **Quality** — output is produced but will be rejected or ignored.
- **Breadth** — capability the platform rewards but does not require.

Then compute a **projected score after each phase**, so the roadmap shows
leverage rather than a flat list:

```
| After | Score | Note |
| today | 41% | strong detector, no platform integration |
| +A | 61% | scope-driven, compliance-enforced |
| +B | 71% | account is now safe |
```

Order phases by leverage, and say which cluster is the 80/20.

## 4. Build the brakes before the accelerator

When the platform penalises bad output, the gate is not a nice-to-have — it is
the highest-value component. Sequence it accordingly:

- Build the **pre-flight refusal** (validate the action against the platform's
  rules and refuse with a recorded reason) before the action path exists.
- Build the **quality gate** and the **human attestation** before any submission
  path exists at all. A submit path with no gate will be used, and the cost lands
  on the user's account.
- Any gate the platform's policy implies (provenance, rate/volume caps,
  sign-off) belongs in the same cluster.

A roadmap that lists "add submission" before "add gate" is wrong regardless of
how the phases are numbered.

## 5. Honest limits section (required)

End the assessment with what the score does NOT establish:

- Rules change; anything with a date must be re-verified before relying on it.
- The scorecard is judgement, not measurement — weights are a choice.
- Detection is not acceptance; a true finding can still be rejected as known or
  accepted risk.
- Every capability claim was verified against a deliberately simple local target,
  not a real one.
- A tool cannot carry the account; only a human decision can accept the risk.

## Worked example: bug-bounty platform (HackerOne)

Concrete shape of a platform where a bad submission is **negative**, which drives
the whole design. Verify current values before reuse — policy here changes.

**Reputation economy (the real gate).** An account starts at a fixed score;
states move it. Indicative magnitudes: a resolved/triaged report earns a few
points; a duplicate filed after public disclosure and a not-applicable verdict
both *lose* points; spam loses the most. Reputation gates private invitations and
caps submission volume. **A tool that submits at volume is an account-destroying
machine unless it gates.** Two rejected reports can cost more than one accepted
report earns.

**Mandatory severity.** Severity became required for bug-bounty/VDP/challenge
reports. Supported calculators are CVSS 3.1, a platform-custom 3.0, and CVSS 4.0,
selectable per program — a tool emitting only one version cannot serve programs
requiring another. A severity label that disagrees with its own vector destroys
credibility (see `audit-robustness-probes`, severity vs confidence).

**Structured scope, not one allow-list.** Assets are typed (domain, wildcard,
URL, CIDR, iOS/Android/Windows app, source code, executable, hardware/IoT, AI
model, other) and each carries **independent** flags: eligibility for submission
vs eligibility for bounty, plus per-asset instruction text and labels. An asset
can be in scope to report but **not eligible for payout** — a tool treating scope
as one boolean works for free and can violate a per-asset instruction it never
read. Exclusions are hard blocks.

**Hacker API.** REST, versioned, HTTP **basic** auth with an account API
username + token (not a password). Program + structured-scope retrieval, your own
reports, and a disclosed-report feed. The disclosed-report feed is the
**duplicate-check source** — without consulting it, a tool cannot know a finding
is already public.

**Automation policy.** The platform explicitly permits and encourages
responsible AI-assisted research while naming the failure modes it penalises:
**duplicates, unverifiable submissions, and reports lacking depth.** Those are
engineering problems with engineering fixes (duplicate lookup, evidence capture,
quality scoring) — not reasons to avoid tooling. Expect a human-accountability
requirement and account/identity verification.

**Report content a triager needs:** verbatim request/response transcript,
reproduction steps with REAL captured identifiers (not template placeholders),
impact, remediation, a CWE mapping, and a screenshot for UI-observable bugs.
A template that emits `{id}` and `user_a` is not submission-ready.

**Assessment dimensions that fell out of this** (reusable weighting):

| Dimension | Weight | Why |
|---|---|---|
| Vulnerability-class detection | 22% | the core value; specialist depth beats generalist breadth |
| Safety & compliance | 18% | out-of-scope requests and accidental flooding lose accounts |
| Evidence & report quality | 22% | determines whether a finding is accepted at all |
| Platform integration | 20% | scope ingestion, API, submission path |
| Reputation protection | 10% | duplicate lookup; decides account survival at volume |
| Asset-type coverage | 8% | unlocks wildcard/mobile/source programs |

Note the ordering effect: a codebase can score well on safety (a verified
scope-guard, SSRF firewall, rate limiter, audit chain) and still be far from
usable, because the **integration and duplicate-prevention** dimensions are the
ones that decide whether operating it is safe.
