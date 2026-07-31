# Renderer manifest

The renderer accepts one JSON object:

```json
{
  "title": "ARCHITECTUREHELL // FIELD NOTES",
  "subtitle": "eight decisions currently in design development",
  "roast_level": 6,
  "callouts": [
    {
      "text": "five windows establish a datum; number six drops the studio",
      "target": [0.58, 0.42],
      "label": [0.69, 0.24],
      "feature_bounds": [0.53, 0.33, 0.63, 0.52],
      "width": 0.24,
      "kind": "issue"
    },
    {
      "text": "annoyingly, this reveal is doing real work",
      "target": [0.82, 0.58],
      "label": [0.72, 0.70],
      "feature_bounds": [0.78, 0.50, 0.87, 0.65],
      "width": 0.23,
      "kind": "merit"
    }
  ]
}
```

## Fields

- `title`: optional string. Omit for no title.
- `subtitle`: optional short string rendered under the title.
- `roast_level`: optional integer from `1` through `11`; default `6`. The renderer displays it but does not rewrite callout copy.
- `callouts`: required list of 1–18 objects.
- `callouts[].text`: required exact label copy, 1–140 characters.
- `callouts[].target`: required `[x, y]` point on the feature, normalized from `0.0` at the top-left to `1.0` at the bottom-right.
- `callouts[].label`: optional normalized `[x, y]` top-left corner for the label box. The renderer chooses an edge position when omitted.
- `callouts[].feature_bounds`: optional normalized `[left, top, right, bottom]` extent of the feature, with positive area. Supply it for every callout; the renderer treats all supplied bounds as protected placement zones.
- `callouts[].width`: optional normalized label width from `0.12` to `0.50`; default `0.23`.
- `callouts[].kind`: optional `issue`, `oddity`, or `merit`; default `issue`.

The renderer may nudge a label horizontally or vertically to prevent overlap. It does not move the target, and it avoids all protected feature bounds. Without `feature_bounds`, it protects a conservative area around the target point.

The CLI flag `--roast-level <integer>` overrides `roast_level` in the manifest. Use the flag in the normal skill workflow so the selected level is explicit at render time.

At Roast Level `1` (**Glaze**), every callout must set `"kind": "merit"`. The renderer rejects Level 1 manifests containing `issue` or `oddity` callouts and labels the title block `GLAZE`.

## Placement heuristics

- Place the target in the center of the evidence, not on its edge.
- Define `feature_bounds` around the whole visible feature, not merely the arrow tip. This is the renderer's guarantee that the yellow card will not cover an item being discussed.
- Put labels over low-information areas such as sky, lawn, blank wall, road, or deep shadow.
- Keep labels away from the feature they discuss.
- Prefer short leaders and avoid crossing more than one other leader.
- Alternate left and right label zones on dense images.
- Use wider labels for phrases that should read in one or two lines; use narrower labels for compact notes.
- Keep all normalized values to two or three decimal places. False precision does not improve placement.

## Coordinate grid

Generate a temporary 10-by-10 grid when visual estimation is not enough:

```text
python <skill-dir>/scripts/annotate_architecture.py --input facade.jpg --grid-output facade-grid.png
```

Read `x` left-to-right and `y` top-to-bottom. Delete or ignore the grid after the final render.
