#!/usr/bin/env python3
"""Render exact ArchitectureHell callouts over an architecture photograph."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as exc:
    raise SystemExit("Pillow is required. Install it with: python -m pip install Pillow") from exc


BRIGHT_YELLOW = (255, 230, 0)
CALLOUT_INK = (18, 18, 14, 255)
PALETTE = {
    kind: {
        "fill": (*BRIGHT_YELLOW, 245),
        "line": (*BRIGHT_YELLOW, 255),
        "ink": CALLOUT_INK,
    }
    for kind in ("issue", "oddity", "merit")
}
INK = (23, 21, 20, 255)
PAPER = (249, 244, 232, 255)


def font_candidates(bold: bool) -> list[Path]:
    return [
        Path("C:/Windows/Fonts") / ("arialbd.ttf" if bold else "arial.ttf"),
        Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
        Path("/usr/share/fonts/truetype/dejavu")
        / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ]


def load_font(size: int, bold: bool = False, preferred: str | None = None) -> ImageFont.ImageFont:
    candidates = [Path(preferred)] if preferred else []
    candidates.extend(font_candidates(bold))
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> float:
    box = draw.textbbox((0, 0), text, font=font)
    return float(box[2] - box[0])


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> str:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if text_width(draw, candidate, font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return "\n".join(lines)


def normalized_point(value: Any, name: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must be a two-number JSON array")
    try:
        x, y = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain numbers") from exc
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        raise ValueError(f"{name} values must be between 0 and 1")
    return x, y


def normalized_bounds(value: Any, name: str) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"{name} must be a four-number JSON array")
    try:
        left, top, right, bottom = (float(component) for component in value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain numbers") from exc
    if not (0.0 <= left < right <= 1.0 and 0.0 <= top < bottom <= 1.0):
        raise ValueError(
            f"{name} must be normalized as [left, top, right, bottom] with positive area"
        )
    return left, top, right, bottom


def validate_manifest(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("manifest must be a JSON object")
    roast_level = raw.get("roast_level", 6)
    if isinstance(roast_level, bool) or not isinstance(roast_level, int) or not 1 <= roast_level <= 11:
        raise ValueError("roast_level must be an integer from 1 through 11")
    callouts = raw.get("callouts")
    if not isinstance(callouts, list) or not 1 <= len(callouts) <= 18:
        raise ValueError("callouts must be a list containing 1 to 18 items")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(callouts, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"callout {index} must be an object")
        copy = item.get("text")
        if not isinstance(copy, str) or not copy.strip():
            raise ValueError(f"callout {index}.text must be a non-empty string")
        if len(copy) > 180:
            raise ValueError(f"callout {index}.text exceeds 180 characters")
        target = normalized_point(item.get("target"), f"callout {index}.target")
        label_raw = item.get("label")
        label = normalized_point(label_raw, f"callout {index}.label") if label_raw is not None else None
        bounds_raw = item.get("feature_bounds")
        feature_bounds = (
            normalized_bounds(bounds_raw, f"callout {index}.feature_bounds")
            if bounds_raw is not None
            else None
        )
        try:
            width = float(item.get("width", 0.23))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"callout {index}.width must be a number") from exc
        if not 0.12 <= width <= 0.50:
            raise ValueError(f"callout {index}.width must be between 0.12 and 0.50")
        kind = item.get("kind", "issue")
        if kind not in PALETTE:
            raise ValueError(f"callout {index}.kind must be issue, oddity, or merit")
        if roast_level == 1 and kind != "merit":
            raise ValueError(
                f"callout {index}.kind must be merit at Roast Level 1; "
                "Level 1 is complimentary-only"
            )
        normalized.append(
            {
                "text": copy.strip(),
                "target": target,
                "label": label,
                "feature_bounds": feature_bounds,
                "width": width,
                "kind": kind,
            }
        )
    return {
        "title": raw.get("title"),
        "subtitle": raw.get("subtitle"),
        "roast_level": roast_level,
        "callouts": normalized,
    }


def overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int], gap: int) -> bool:
    return not (
        a[2] + gap <= b[0]
        or b[2] + gap <= a[0]
        or a[3] + gap <= b[1]
        or b[3] + gap <= a[1]
    )


def place_box(
    preferred_x: int,
    preferred_y: int,
    width: int,
    height: int,
    canvas: tuple[int, int],
    occupied: Iterable[tuple[int, int, int, int]],
    protected: Iterable[tuple[int, int, int, int]],
    margin: int,
) -> tuple[int, int, int, int]:
    canvas_w, canvas_h = canvas
    base_x = min(max(preferred_x, margin), max(margin, canvas_w - width - margin))
    base_y = min(max(preferred_y, margin), max(margin, canvas_h - height - margin))
    step_y = max(8, round(canvas_h * 0.012))
    step_x = max(12, round(canvas_w * 0.025))
    x_candidates = [base_x]
    y_candidates = [base_y]
    for offset in range(1, 80):
        y_candidates.extend((base_y + offset * step_y, base_y - offset * step_y))
        x_candidates.extend((base_x + offset * step_x, base_x - offset * step_x))
    clearance = max(6, margin // 2)
    for candidate_x in x_candidates:
        x = min(max(candidate_x, margin), max(margin, canvas_w - width - margin))
        for candidate_y in y_candidates:
            y = min(max(candidate_y, margin), max(margin, canvas_h - height - margin))
            rect = (x, y, x + width, y + height)
            if all(not overlaps(rect, other, gap=clearance) for other in occupied) and all(
                not overlaps(rect, feature, gap=clearance) for feature in protected
            ):
                return rect
    return (base_x, base_y, base_x + width, base_y + height)


def connection_point(target: tuple[int, int], box: tuple[int, int, int, int]) -> tuple[int, int]:
    tx, ty = target
    left, top, right, bottom = box
    candidates = [
        (left, min(max(ty, top), bottom)),
        (right, min(max(ty, top), bottom)),
        (min(max(tx, left), right), top),
        (min(max(tx, left), right), bottom),
    ]
    return min(candidates, key=lambda point: math.dist(point, target))


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    target: tuple[int, int],
    color: tuple[int, int, int, int],
    scale: float,
) -> None:
    sx, sy = start
    tx, ty = target
    halo_width = max(4, round(5 * scale))
    line_width = max(2, round(3 * scale))
    draw.line((sx, sy, tx, ty), fill=(18, 16, 15, 230), width=halo_width)
    draw.line((sx, sy, tx, ty), fill=color, width=line_width)
    angle = math.atan2(ty - sy, tx - sx)
    length = max(10, round(15 * scale))
    spread = math.pi / 7
    points = [
        (tx, ty),
        (tx - length * math.cos(angle - spread), ty - length * math.sin(angle - spread)),
        (tx - length * math.cos(angle + spread), ty - length * math.sin(angle + spread)),
    ]
    draw.polygon(points, fill=(18, 16, 15, 230))
    inner = max(6, length - max(2, round(3 * scale)))
    inner_points = [
        (tx, ty),
        (tx - inner * math.cos(angle - spread), ty - inner * math.sin(angle - spread)),
        (tx - inner * math.cos(angle + spread), ty - inner * math.sin(angle + spread)),
    ]
    draw.polygon(inner_points, fill=color)


def draw_title(
    draw: ImageDraw.ImageDraw,
    title: str | None,
    subtitle: str | None,
    roast_level: int,
    title_font: ImageFont.ImageFont,
    subtitle_font: ImageFont.ImageFont,
    canvas_width: int,
    margin: int,
) -> tuple[int, int, int, int] | None:
    if not title:
        return None
    badge = "GLAZE" if roast_level == 1 else f"ROAST {roast_level:02d}"
    max_text_width = round(canvas_width * 0.45)
    wrapped_title = wrap_text(draw, str(title), title_font, max_text_width)
    wrapped_subtitle = wrap_text(draw, str(subtitle), subtitle_font, max_text_width) if subtitle else ""
    title_box = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font, spacing=4)
    sub_box = (
        draw.multiline_textbbox((0, 0), wrapped_subtitle, font=subtitle_font, spacing=3)
        if wrapped_subtitle
        else (0, 0, 0, 0)
    )
    badge_box = draw.textbbox((0, 0), badge, font=subtitle_font)
    pad_x = max(14, margin)
    pad_y = max(10, margin // 2)
    content_width = max(title_box[2], sub_box[2], badge_box[2])
    width = content_width + 2 * pad_x
    height = title_box[3] + badge_box[3] + 2 * pad_y + max(5, margin // 3)
    if wrapped_subtitle:
        height += sub_box[3] + max(5, margin // 3)
    rect = (margin, margin, margin + width, margin + height)
    draw.rounded_rectangle(rect, radius=max(5, margin // 2), fill=(20, 18, 17, 232), outline=PAPER, width=2)
    x = rect[0] + pad_x
    y = rect[1] + pad_y
    draw.text((x, y), badge, font=subtitle_font, fill=(*BRIGHT_YELLOW, 255))
    y += badge_box[3] + max(5, margin // 3)
    draw.multiline_text((x, y), wrapped_title, font=title_font, fill=PAPER, spacing=4)
    if wrapped_subtitle:
        y += title_box[3] + max(5, margin // 3)
        draw.multiline_text(
            (x, y), wrapped_subtitle, font=subtitle_font, fill=(230, 223, 208, 255), spacing=3
        )
    return rect


def render_annotations(
    source: Image.Image,
    manifest: dict[str, Any],
    preferred_font: str | None,
) -> Image.Image:
    base = ImageOps.exif_transpose(source).convert("RGBA")
    width, height = base.size
    scale = max(0.65, min(2.4, width / 1600.0))
    margin = max(12, round(min(width, height) * 0.016))
    font_size = max(16, min(44, round(width / 58)))
    body_font = load_font(font_size, bold=True, preferred=preferred_font)
    title_font = load_font(max(20, round(font_size * 1.16)), bold=True, preferred=preferred_font)
    subtitle_font = load_font(max(12, round(font_size * 0.65)), preferred=preferred_font)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    occupied: list[tuple[int, int, int, int]] = []
    title_rect = draw_title(
        draw,
        manifest.get("title"),
        manifest.get("subtitle"),
        manifest["roast_level"],
        title_font,
        subtitle_font,
        width,
        margin,
    )
    if title_rect:
        occupied.append(title_rect)

    protected: list[tuple[int, int, int, int]] = []
    fallback_half_width = max(28, round(width * 0.045))
    fallback_half_height = max(24, round(height * 0.055))
    for callout in manifest["callouts"]:
        if callout["feature_bounds"]:
            left, top, right, bottom = callout["feature_bounds"]
            protected.append(
                (round(left * width), round(top * height), round(right * width), round(bottom * height))
            )
        else:
            target_x = round(callout["target"][0] * width)
            target_y = round(callout["target"][1] * height)
            protected.append(
                (
                    max(0, target_x - fallback_half_width),
                    max(0, target_y - fallback_half_height),
                    min(width, target_x + fallback_half_width),
                    min(height, target_y + fallback_half_height),
                )
            )

    prepared: list[dict[str, Any]] = []
    for callout in manifest["callouts"]:
        box_width = max(150, min(width - 2 * margin, round(width * callout["width"])))
        pad_x = max(9, round(font_size * 0.55))
        pad_y = max(8, round(font_size * 0.42))
        wrapped = wrap_text(
            draw,
            callout["text"],
            body_font,
            box_width - pad_x * 2,
        )
        bbox = draw.multiline_textbbox(
            (0, 0), wrapped, font=body_font, spacing=max(2, round(font_size * 0.16))
        )
        box_height = bbox[3] - bbox[1] + pad_y * 2
        target = (
            round(callout["target"][0] * width),
            round(callout["target"][1] * height),
        )
        if callout["label"]:
            preferred_x = round(callout["label"][0] * width)
            preferred_y = round(callout["label"][1] * height)
        else:
            preferred_x = margin if target[0] < width / 2 else width - box_width - margin
            preferred_y = target[1] - box_height // 2
        rect = place_box(
            preferred_x,
            preferred_y,
            box_width,
            box_height,
            (width, height),
            occupied,
            protected,
            margin,
        )
        occupied.append(rect)
        prepared.append(
            {
                "wrapped": wrapped,
                "rect": rect,
                "target": target,
                "kind": callout["kind"],
                "pad_x": pad_x,
                "pad_y": pad_y,
            }
        )

    for item in prepared:
        draw_arrow(
            draw,
            connection_point(item["target"], item["rect"]),
            item["target"],
            PALETTE[item["kind"]]["line"],
            scale,
        )

    for item in prepared:
        left, top, right, bottom = item["rect"]
        palette = PALETTE[item["kind"]]
        draw.rectangle(item["rect"], fill=palette["fill"])
        draw.multiline_text(
            (left + item["pad_x"], top + item["pad_y"]),
            item["wrapped"],
            font=body_font,
            fill=palette["ink"],
            spacing=max(2, round(font_size * 0.16)),
        )

    if title_rect:
        draw_title(
            draw,
            manifest.get("title"),
            manifest.get("subtitle"),
            manifest["roast_level"],
            title_font,
            subtitle_font,
            width,
            margin,
        )
    return Image.alpha_composite(base, layer)


def render_grid(source: Image.Image, preferred_font: str | None) -> Image.Image:
    base = ImageOps.exif_transpose(source).convert("RGBA")
    width, height = base.size
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font_size = max(12, round(width / 80))
    font = load_font(font_size, bold=True, preferred=preferred_font)
    line_width = max(1, round(min(width, height) / 700))
    for step in range(11):
        x = round(width * step / 10)
        y = round(height * step / 10)
        draw.line((x, 0, x, height), fill=(247, 197, 72, 210), width=line_width)
        draw.line((0, y, width, y), fill=(247, 197, 72, 210), width=line_width)
        if step < 10:
            label = f"{step / 10:.1f}"
            draw.rectangle((x + 2, 2, x + 62, font_size + 13), fill=(18, 16, 15, 215))
            draw.text((x + 6, 5), f"x {label}", font=font, fill=PAPER)
            draw.rectangle((2, y + 2, 64, y + font_size + 13), fill=(18, 16, 15, 215))
            draw.text((6, y + 5), f"y {label}", font=font, fill=PAPER)
    return Image.alpha_composite(base, layer)


def save_image(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        image.convert("RGB").save(path, quality=95, optimize=True)
    elif suffix == ".webp":
        image.save(path, quality=95, method=6)
    else:
        image.save(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="source photograph")
    parser.add_argument("--manifest", type=Path, help="JSON callout manifest")
    parser.add_argument("--output", type=Path, help="final annotated image")
    parser.add_argument("--grid-output", type=Path, help="optional coordinate-grid preview")
    parser.add_argument(
        "--roast-level",
        type=int,
        choices=range(1, 12),
        metavar="1-11",
        help="override the manifest Roast Level",
    )
    parser.add_argument("--font", help="optional path to a TrueType/OpenType font")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        raise SystemExit(f"Input image not found: {args.input}")
    if args.grid_output is None and (args.manifest is None or args.output is None):
        raise SystemExit("Provide --manifest and --output, or provide --grid-output")
    try:
        with Image.open(args.input) as source:
            source.load()
            if args.grid_output:
                save_image(render_grid(source, args.font), args.grid_output)
                print(f"Wrote coordinate grid: {args.grid_output}")
            if args.manifest:
                if args.output is None:
                    raise SystemExit("--output is required with --manifest")
                raw = json.loads(args.manifest.read_text(encoding="utf-8"))
                if args.roast_level is not None:
                    if not isinstance(raw, dict):
                        raise ValueError("manifest must be a JSON object")
                    raw["roast_level"] = args.roast_level
                manifest = validate_manifest(raw)
                result = render_annotations(source, manifest, args.font)
                save_image(result, args.output)
                print(f"Wrote annotated image: {args.output}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
