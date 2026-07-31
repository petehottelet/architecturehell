---
name: architecturehell
description: Analyze photos of human-constructed buildings, houses, towers, skylines, streetscapes, and suburban development, then create an annotated image with funny, sharp, architecture-specific callouts. Use when the user asks to roast, critique, mark up, red-pen, praise, or add commentary to architecture or urban design in an image. Produce specific observational humor with profession-level architectural references, including a fully complimentary Roast Level 1, while preserving the source photo and avoiding generic insults or unsupported claims.
---

# ArchitectureHell

Turn a building photo into an affectionate architectural autopsy: visually specific, technically literate, funny, and a little unhinged.

## Required resources

Read these before drafting callouts:

- [references/critique-lenses.md](references/critique-lenses.md) for what to inspect by building and scene type.
- [references/voice-and-copy.md](references/voice-and-copy.md) for the humor system, architectural in-jokes, copy limits, and safety boundaries.
- [references/roast-level.md](references/roast-level.md) for interpreting and applying `--roast-level`.
- [references/manifest-schema.md](references/manifest-schema.md) before creating the renderer manifest.

Use [assets/reference-style.jpeg](assets/reference-style.jpeg) only when a visual style reference is helpful. Borrow its dense field-note energy and feature-level specificity; never copy its jokes or red color treatment.

## Workflow

1. Locate the skill directory from this `SKILL.md`; resolve all bundled paths from it rather than assuming the current working directory.
2. Parse `--roast-level <integer>` from the invocation or user request. Default to `6`. Accept only `1` through `11`; treat `11` as the documented absurdist easter egg, not as an out-of-range error. Read [references/roast-level.md](references/roast-level.md) and apply the selected level consistently.
3. Inspect the full-resolution input with the available image-viewing or vision tool. If no readable image is available, ask the user to attach one or provide a valid path.
4. Classify the scene: single facade, complex house, tower, skyline, streetscape, or sprawl. Note perspective distortion, occlusion, reflections, temporary objects, and photo artifacts before judging the design.
5. Inventory only visible evidence. Scan parti and massing, regulating lines, roofscape, openings, bay rhythm, material logic, entry sequence, circulation, site, scale, and context. Do not infer unseen structure, code compliance, cost, intent, or interior performance.
6. Draft twice as many callouts as needed, then keep the strongest non-redundant set:
   - 5–8 for a simple building or tight crop.
   - 7–12 for a complex facade, skyline, or wide urban scene.
   - Fewer when the image is sparse or label space is limited.
7. Ensure every callout points to a precise feature and contains an observation, not just a verdict. Favor references that reward architectural literacy—poche, datum, spandrel, rustication, rainscreen, facadism, value engineering, pro forma, studio jury language—while leaving enough context for a non-architect to enjoy the line.
   - At level `1` (**Glaze**), write sincere, architecture-specific compliments only. Set every callout `kind` to `merit`. Do not tease, criticize, hedge, damn with faint praise, or use backhanded qualifiers such as “almost,” “surprisingly,” “despite,” or “annoyingly.”
   - At levels `2`–`10`, include one moment of begrudging respect when the image genuinely earns it.
   - At level `11`, preserve feature specificity but deliberately abandon ordinary semantic coherence.
8. Choose target and label coordinates, plus `feature_bounds` for every callout. Put cards only in negative space; `feature_bounds` protects the annotated feature from label placement. If placement is uncertain, generate a temporary coordinate grid:

   ```text
   python <skill-dir>/scripts/annotate_architecture.py --input <image> --grid-output <temporary-grid.png>
   ```

9. Create a JSON manifest following [references/manifest-schema.md](references/manifest-schema.md). Record the selected `roast_level` value and use exact final copy; the renderer will not rewrite it.
10. Render non-destructively to a new PNG or JPEG:

   ```text
   python <skill-dir>/scripts/annotate_architecture.py --input <image> --manifest <callouts.json> --roast-level <level> --output <annotated-image.png>
   ```

11. Inspect the rendered image at full size. Revise one issue at a time until:
    - every arrow lands on the intended feature;
    - every label is readable and within bounds;
    - labels do not cover the evidence they discuss, faces, addresses, or existing credits/watermarks;
    - callouts and leaders do not collide distractingly;
    - the photo remains unchanged except for the annotation layer;
    - the jokes vary in construction and none are generic filler.
12. Deliver the annotated image and its saved path. State the Roast Level and summarize the creative angle in one sentence; do not explain every joke. At level `11`, do not translate the absurdity back into normal language.

## Rendering rules

- Prefer the bundled Pillow renderer because it preserves the input and renders exact text. Do not ask an image-generation model to redraw the building or typeset the callouts when deterministic local rendering is available.
- Preserve the source aspect ratio, crop, color, people, landscaping, signage, and watermark. Never overwrite the source unless the user explicitly requests replacement.
- Use normalized coordinates so the manifest survives resolution changes.
- Default to the title `ARCHITECTUREHELL // FIELD NOTES` unless the user supplies a title or asks for no title.
- Display `GLAZE` in the annotation title block at level `1`; otherwise display `ROAST <level>`.
- Render all callout cards as flat bright yellow (`#FFE600`) rectangles with black type and bright-yellow leaders. Do not add callout numbers, borders, shadows, or rounded corners. Callout kind controls the writing only, not the color.
- Every callout should include `feature_bounds` so the renderer can keep its yellow card off every feature being glazed or roasted.
- Use `issue` callouts for design critiques, `oddity` for delightful confusion, and `merit` for genuine or begrudging praise. At level `1`, use only `merit`; at other levels, keep `merit` rare enough to feel earned.
- Use a new descriptive output filename such as `<stem>-architecturehell.png`.
- If Pillow is unavailable, say which dependency is missing and ask the user to install `Pillow`; do not silently switch to a lower-fidelity workflow.

## Final quality gate

Reject and revise the draft if any answer is yes:

- Could the joke apply to almost any ugly building?
- Does it insult the owner, residents, neighborhood, culture, or income group rather than a visible design choice?
- Does it present an invisible technical, legal, safety, or accessibility claim as fact?
- Does it mistake camera perspective, shadow, foliage, reflection, renovation staging, or temporary clutter for architecture?
- Does the humor rely mainly on “who approved this,” “it’s giving,” “architect said,” or another tired reaction template?
- Does a profession-specific reference feel pasted on rather than clarifying the visual observation?
- At level `1`, does any callout criticize, tease, hedge, imply a defect, or use a `kind` other than `merit`?
- At levels `1`–`10`, has the wording become less coherent than the selected level permits?
- At level `11`, is the wording merely random rather than architecturally grounded absurdity?
- Are more than two callouts aimed at the same feature?
- Does annotation cover roughly a quarter or more of the useful image area?
- Is any callout too long to scan in about two seconds?
