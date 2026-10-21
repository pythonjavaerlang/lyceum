"""Open Graph image generation (Pillow), adapted from light-fastapi.

Generates 1200x630 social-share images with Ukrainian (Cyrillic) title text and
writes them under the output ``og/`` directory. Filenames are keyed by the page
slug so each page gets a stable, unique image.

A Cyrillic-capable TrueType font is required; we prefer the font bundled with
the repository (captcha/fonts/arialbd.ttf) so the build is reproducible on both
Windows and Linux, then fall back to common system fonts.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config

logger = logging.getLogger(__name__)

OG_WIDTH = config.OG_WIDTH
OG_HEIGHT = config.OG_HEIGHT

# Brand palette — deep православний navy/gold.
_BG_TOP = (11, 42, 74)        # deep navy
_BG_BOTTOM = (23, 74, 122)    # lighter blue
_TEXT_COLOR = (255, 255, 255)
_ACCENT = (251, 176, 52)      # gold (matches site yellow-button)
_FOOTER_COLOR = (205, 218, 235)

_FONTS = Path(__file__).resolve().parent / "assets" / "fonts"
_MEDIA_FONTS = Path(__file__).resolve().parent / "assets" / "media" / "fonts"

# Prefer a repo-bundled Cyrillic font for reproducibility, then system fonts.
_FONT_CANDIDATES = [
    str(_FONTS / "arialbd.ttf"),
    str(_MEDIA_FONTS / "Georgia.ttf"),
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _load_font(size: int):
    for candidate in _FONT_CANDIDATES:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _make_background():
    strip = Image.new("RGB", (1, OG_HEIGHT))
    top, bottom = _BG_TOP, _BG_BOTTOM
    for y in range(OG_HEIGHT):
        ratio = y / OG_HEIGHT
        strip.putpixel(
            (0, y),
            tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)),
        )
    return strip.resize((OG_WIDTH, OG_HEIGHT))


def render_og_image(title: str, *, subtitle: str = "", site_name: str = config.SITE_NAME) -> Image.Image:
    img = _make_background()
    draw = ImageDraw.Draw(img)

    margin = 90
    max_text_width = OG_WIDTH - 2 * margin

    # Gold accent bar near the top.
    draw.rectangle([margin, 110, margin + 120, 124], fill=_ACCENT)

    title_font = _load_font(62)
    sub_font = _load_font(34)
    footer_font = _load_font(30)

    lines = _wrap_text(draw, (title or site_name).strip(), title_font, max_text_width)
    lines = lines[:5]

    try:
        ascent, descent = title_font.getmetrics()
        line_height = ascent + descent + 12
    except AttributeError:
        line_height = 74
    block_height = line_height * len(lines)
    y = max(165, (OG_HEIGHT - block_height) // 2 - 20)

    for line in lines:
        draw.text((margin, y), line, font=title_font, fill=_TEXT_COLOR)
        y += line_height

    if subtitle:
        sub_lines = _wrap_text(draw, subtitle.strip(), sub_font, max_text_width)[:2]
        y += 6
        for line in sub_lines:
            draw.text((margin, y), line, font=sub_font, fill=_FOOTER_COLOR)
            y += 44

    draw.text((margin, OG_HEIGHT - 70), site_name, font=footer_font, fill=_FOOTER_COLOR)
    return img


def generate_og_image(slug: str, title: str, out_dir: Path, *, subtitle: str = "") -> str:
    """Generate and save the OG image for a page. Returns the site-relative URL."""
    og_dir = out_dir / "og"
    og_dir.mkdir(parents=True, exist_ok=True)
    name = (slug or "index").strip("/").replace("/", "_") or "index"
    rel = f"og/{name}.jpg"
    dst = og_dir / f"{name}.jpg"
    try:
        img = render_og_image(title, subtitle=subtitle)
        img.save(dst, "JPEG", quality=85, optimize=True)
    except Exception:  # pragma: no cover
        logger.exception("Failed to generate OG image for slug=%r", slug)
    return rel
