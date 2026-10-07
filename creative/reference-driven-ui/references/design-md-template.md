# DESIGN.md template (reference-driven)

Fill this from a Refero style in Phase 1, then replace each bracket with an
observed rule or a deliberate project choice. **Leave unknowns explicit** — a
screenshot cannot establish product behavior, so say so instead of inventing it.

```md
# Design direction

Reference: [style URL and date reviewed]
Purpose: [audience and task]

## Typography
Display: [family, weight, size, line height, use]
Body:    [family, weight, size, line height, reading width]

## Color roles
Canvas and surfaces: [values and where they apply]
Text and actions:    [values and contrast requirements]

## Layout
Content width:  [value or range]
Spacing rhythm: [repeated gaps, not every one-off measurement]

## Open decisions
[What the reference cannot tell you about your product]
```

## Rules that make the file usable by an agent

- **Every color gets a job.** A hex without a role cannot tell an agent *when*
  to use it. Record canvas / surface / text / action / state separately, and
  never let a bright accent spread to every control.
- **Write the role of each face before sizes.** A hero-sized headline is not a
  global heading token — say where its scale ends and denser content begins.
- **Capture repeatable layout rules**, not a single hero composition:
  recurring container widths, gaps, card treatment, section transitions.
- **Distinguish what the reference proves from what it does not.** It suggests
  a visual direction; it does not define your copy, states, or responsive
  behavior. Put those under *Open decisions*.
- **Record image scale, crop, and surrounding whitespace** alongside palette
  and fonts, or the imagery cannot be reproduced.

## Formal spec

For the strict machine-readable shape (YAML front matter + canonical section
order + `{colors.primary}` references) use the `design-md` skill and lint with
`npx -y @google/design.md lint DESIGN.md`.
