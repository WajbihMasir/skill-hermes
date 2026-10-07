---
name: proposal-revision
description: "Use when a reviewer returns feedback on a proposal draft."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [proposal, srs, review-response, scope, threat-model, metrics, timeline, academic]
    related_skills: [grounded-citations, document-to-action-items, architecture-audit]
---

# Proposal Revision (reviewer feedback → revised document)

Take a long draft (project proposal, SRS, thesis plan) plus a reviewer's
critique, and produce a revision that answers every point so the reviewer can
see it was answered. The deliverable is usually TWO documents: a concise core
proposal that is actually assessed, and the old long draft demoted to a
technical appendix.

## When to use

- A pembimbing / reviewer / stakeholder returns numbered feedback on a proposal.
- The critique says the document is too long, too broad, informal, or missing
  standard sections (threat model, timeline, metrics, risks, sign-off).

Not for: extracting obligations from contracts (`document-to-action-items`),
writing a handoff spec for another agent (`agent-handoff-specs`).

## Procedure

1. **Back up before editing anything.**
   `cp "<doc>" "<doc>.backup-sebelum-revisi.md"`. The original stays retrievable
   when the reviewer wants to compare.

2. **Inventory the feedback into a numbered list, then grep the document for
   each claim.** Reviewers cite real text ("§39 lists 21 Must-Have items",
   "§33 uses informal pronouns"). Locate the exact lines before planning, and
   verify quantifiable claims (`grep -c`) so your revision notes can cite what
   changed. Feedback you cannot locate is feedback you will answer wrongly.

3. **Decide per point: restructure, add a section, or sweep.**
   - *Scope too big* → restructure the priority list (step 4).
   - *Missing section* (threat model, timeline, metrics, risks, sign-off) → add
     it using the patterns in steps 5–7.
   - *Language / placeholders / length* → mechanical sweep (step 8).

4. **Cut scope to ONE vertical slice — do not just delete items.**
   A reviewer saying "this is two systems" wants a provable core loop, not a
   shorter list. Write the slice as a single arrow chain
   (`Event → Persiapan → Kesiapan → Bukti → Verifikasi → Tercatat`), keep the
   items that complete that chain, and **demote the rest to Should Have with an
   explicit `— dipindah dari Must Have` note**. Also promote any item the
   reviewer flags as strategically important (`— dinaikkan dari Could Have`).
   Label the slice header "Must Have — Vertical Slice Inti" so the reviewer sees
   the intent, not a quiet truncation.

5. **When two domains look "taped together", write an explicit connecting
   thread.** Answer with a dedicated section carrying: (a) 4–5 concrete
   integration arguments (shared population, one workflow engine, one audit
   trail, the metric itself), (b) a worked example explaining the disputed
   metric in plain terms ("SECURITY 96%" = 96% of that category's requirements
   for that event are complete, computed from real data), and (c) an **honest
   MVP-vs-roadmap split** — state which integration ships now and which is
   roadmap. Overclaiming integration the build does not have is the fastest way
   to lose the reviewer twice.

6. **Add a threat model as a STRIDE matrix with a status column.** One row per
   STRIDE category: scenario → mitigation → status (`Teruji` / `Sebagian` /
   `Roadmap`). Only mark `Teruji` for controls with actual tests behind them.
   Include the sections security reviewers always ask for: an **allowlist of
   fields** permitted on any unauthenticated page, the risk of personal data
   inside uploaded evidence plus a retention policy, and an explicit
   authentication decision (local accounts vs SSO, session lifetimes, what is
   roadmap).

7. **Every metric gets a baseline method, a target, and a verification method.**
   A metric without a baseline is not measurable. Table columns:
   `Metrik | Baseline (cara ukur di AS-IS) | Target | Verifikasi`. The baseline
   column names the measurement procedure (interview, observation, count); the
   actual number is collected during the AS-IS phase — say so instead of
   inventing a figure.

8. **Timeline: each phase gets duration + deliverable + a total.**
   `Tahap | Aktivitas | Durasi | Deliverable`, ending in a bold total in weeks,
   with a note that the user adjusts it to the real engagement length. Add a
   risks table (impact/probability/mitigation) and an empty stakeholder
   sign-off table (name, role, date, evidence) for the user to fill.

9. **Sweep language and placeholders mechanically, then verify.**
   `grep -n -i "\bgua\b"` for informal pronouns (also `aku`, `nggak`, `banget`),
   `grep -n "\[.*\]"` for unfilled placeholders. Replace with formal register
   (`saya`) and real values; if a value is genuinely unknown (full legal name),
   fill your best inference and flag it to the user for one-line correction.
   Re-grep after the sweep — target zero hits — and confirm you did not break
   markdown structure (a patch that drops a `> ` blockquote marker is a silent
   formatting regression; re-read the diff).

10. **Restructure long → concise core + appendix.**
    Write the new core (~300 lines) covering: executive summary, background,
    connecting thread, scope (MoSCoW), architecture & stack, security/threat
    model, adoption strategy, metrics, timeline, risks, sign-off, appendices.
    Demote the old document by adding a status note at its top: it is now the
    **Lampiran Teknis**, the assessed document is the new core, and *the core
    wins on conflict*. Two documents without a stated precedence is a defect.

11. **Close with a response-to-review table.** `# | Catatan | Tindakan` mapping
    every numbered reviewer point to the action taken and its section. This is
    what proves nothing was ignored, and it doubles as the reviewer's checklist.
    Template: `templates/review-response-table.md`.

## User preferences (apply by default)

- **Formal Bahasa Indonesia** in the document; no colloquial pronouns.
- **Concise core + appendix**, never a 1500+ line single document.
- Fill placeholders rather than leaving `[Nama Mahasiswa]`-style tokens; flag
  inferred values to the user in the chat summary, not in the document.
- Keep the chat reply short: what changed (table), which files were touched,
  and the handful of items only the user can supply (real name, real durations,
  measured baselines, sign-off evidence).

## Pitfalls

- **Demoting features without saying so reads as ignoring the feedback.** Every
  Must→Should move carries an explicit `— dipindah dari` marker plus a row in
  the response table.
- **Do not invent baseline numbers.** The AS-IS phase exists to measure them;
  ship the measurement method and leave the figure to the user.
- **Do not leave the old document as the canonical one.** Add the precedence
  note to the old file in the same pass, or the next reader quotes the outdated
  draft.
- **Mark security controls honestly.** A threat-model row claiming a control
  that is not built will not survive one question from a security reviewer;
  `Roadmap` is a respectable status.
- **Durations are estimates — say so.** Flag them for the user to adjust to the
  actual engagement length instead of presenting them as commitments.

## Files

- `templates/review-response-table.md` — starter tables for the response-to-
  review section and the STRIDE matrix.
