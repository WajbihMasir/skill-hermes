---
name: video-demo-production
description: Produce video demos with synced PPT slides and narration.
version: 1.0.0
author: Nous Research
license: MIT
platform: [linux, macos, windows]
metadata:
  hermes:
    tags: [pptx, video-demo, speaker-script, synchronization, presentation]
    category: productivity
---

# Video Demo Production

Produce video demos with synchronized PPT slides and speaker narration. The core challenge is keeping visual content (PPT) and narration (script) perfectly aligned after multiple revision rounds.

## When to Use

- User asks to create a video demo with slides and narration
- User asks to sync PPT with a speaker script
- User asks to verify that a PPT deck matches a script
- User asks to fix desyncs between slides and narration

## Procedure

### 1. Write the Speaker Script First

The script is the source of truth. PPT slides are generated FROM the script, not the other way around.

Structure each scene with explicit markers:
```
[SLIDE: n]  →  Visual PPT content (what viewer sees on slide)
[DEMO]      →  Live demonstration (what presenter does)
```

### 2. Create the Deck Spec (JSON)

Translate the script into a JSON spec that the PPT generator can consume. Each slide should have:
- `layout`: visual layout type
- `title`: slide title
- `subtitle`: slide subtitle (often contains key positioning language)
- `notes`: speaker notes (should match script narration verbatim)

**Critical:** The `subtitle` and `notes` fields are where desyncs most commonly occur. They often contain the exact phrasing that gets revised.

### 3. Generate the PPT

Use a custom generator script (e.g., `create_deck.py`) that reads the JSON spec and produces the .pptx file. The generator uses python-pptx with explicit RGB text colors.

**Pitfall:** The bundled `pptx_create.py` from the powerpoint skill does NOT set text colors — default PowerPoint text is dark and invisible on dark backgrounds. Always use a custom generator with explicit `RGBColor` values.

### 4. Verify Synchronization (MANDATORY)

After every generation, read back the PPT text content and compare against the script:

```bash
python pptx_read.py output.pptx --outline
```

Extract all text from the output and diff against the script. Check:
- Slide titles
- Subtitles (most common desync location)
- Body text
- Speaker notes

**Pitfall:** Desyncs are almost always in the `subtitle` or `notes` fields, not the `title`. The title is usually stable; the subtitle and notes carry the nuanced language that gets revised.

### 5. Fix Desyncs in the Generator, NOT the Output

When a desync is found:
1. Identify whether the source is the JSON spec or the generator script
2. Fix the source file using `patch` (targeted edits)
3. Regenerate the PPT
4. Re-verify

**Pitfall:** Never edit the generated .pptx directly. Always fix the generator or spec and regenerate. The .pptx is a build artifact.

### 6. Version Management

When the user asks for a new version, create a new file (e.g., `v7.pptx`) rather than overwriting the previous version. This preserves the audit trail and allows rollback.

## Pitfalls

- **write_file fails silently on large files:** When writing generator scripts or specs with complex content, `write_file` may appear to succeed but the file is truncated or unchanged. Use `patch` for targeted edits or write via Python `open()` with a line list approach.

- **Patch tool requires exact match:** The `patch` tool needs an exact string match for `old_string`. If the file was read with pagination (offset/limit), the tool may refuse to match. Read the full file first, or use a smaller unique substring.

- **Subtitle desyncs are the most common:** When revising language for precision (e.g., changing "Authorization" to "Enforcement"), the subtitle is often missed because it's a short field that doesn't appear in the main script body. Always check subtitles explicitly.

- **Notes field carries the full narration:** The speaker notes in the PPT should match the script narration verbatim. If the script is revised, the notes must be updated too. This is the second most common desync location.

- **Regenerate after every fix:** After patching the generator or spec, always regenerate the PPT and re-verify. Do not assume the fix worked without reading back the output.

- **write_file refuses to overwrite paginated reads:** If a file was read with `offset`/`limit` (pagination), `write_file` will refuse to overwrite it with a `stale_write_blocked` error. Use `patch` for targeted edits instead, or read the full file first.

- **Verify DB state before recording:** Before starting a live demo recording, query the database to check current stock levels and order counts. If the script's expected output (e.g., `DEDUCT_STOCK | 5 -> 4`) doesn't match actual DB state (e.g., stock=2), either reset the DB or update the script's expected output to match reality. Mismatches between slide visuals and live terminal output are immediately visible to viewers.

## Verification Checklist

After generating a PPT, verify:
- [ ] Slide count matches script scene count
- [ ] All slide titles match script scene titles
- [ ] All subtitles match script positioning language
- [ ] All speaker notes match script narration verbatim
- [ ] No leftover text from previous versions
- [ ] File is a new version (not overwriting previous)

## Example Workflow

```
1. Write speaker-script.md with [SLIDE: n] and [DEMO] markers
2. Create deck_spec.json with title, subtitle, notes per slide
3. Run: python create_deck.py deck_spec.json output.pptx
4. Run: python pptx_read.py output.pptx --outline
5. Diff output against script
6. Fix desyncs in create_deck.py or deck_spec.json
7. Regenerate and re-verify
8. Commit with descriptive message
```
