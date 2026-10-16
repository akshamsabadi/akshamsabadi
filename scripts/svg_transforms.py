"""Pure SVG transformation and construction functions for profile assets."""

import base64
import re
from typing import Final

from scripts.models import LogoSpec

_ANIMATED_PATH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"<path id=['\"]path0['\"].*?</path>", flags=re.DOTALL
)
_TEXT_PATH_OPEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"<textPath[^>]*>")
_TEXT_PATH_CLOSE_PATTERN: Final[re.Pattern[str]] = re.compile(r"</textPath>")
_TEXT_OPEN_TAG_PATTERN: Final[re.Pattern[str]] = re.compile(r"<text ")

_SHIELD_RECT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'<rect width="([^"]+)" height="([^"]+)" fill="([^"]+)"/>'
)

_XML_DECL_PATTERN: Final[re.Pattern[str]] = re.compile(r"<\?xml.*?\?>")
_HTML_COMMENT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"<!--.*?-->", flags=re.DOTALL
)
_FILL_ATTR_PATTERN: Final[re.Pattern[str]] = re.compile(r'fill="[^"]*"')
_SHAPE_TAGS: Final[tuple[str, ...]] = ("path", "circle", "polygon")


def convert_typing_svg_to_static(raw_svg: str) -> str:
    """Converts an animated typing SVG into a centered static text SVG.

    Strips `<path id='path0'>...</path>` animation elements and `<textPath>`
    wrappers while adding `y="50%"` vertical centering to `<text>` elements.

    Args:
        raw_svg: Raw SVG XML string returned by `readme-typing-svg`.

    Returns:
        Transformed static SVG XML string.

    Raises:
        ValueError: If `raw_svg` is empty or does not contain an `<svg` root tag.
    """
    if not raw_svg.strip() or "<svg" not in raw_svg:
        raise ValueError("Input must be a non-empty SVG string.")

    without_path = _ANIMATED_PATH_PATTERN.sub("", raw_svg)
    without_open_textpath = _TEXT_PATH_OPEN_PATTERN.sub("", without_path)
    without_textpath = _TEXT_PATH_CLOSE_PATTERN.sub("", without_open_textpath)
    return _TEXT_OPEN_TAG_PATTERN.sub('<text y="50%" ', without_textpath)


def _format_bordered_rect(
    match: re.Match[str], stroke_color: str, corner_radius: int
) -> str:
    """Formats a shields.io background `<rect>` with an inset rounded stroke."""
    width = float(match.group(1))
    height = float(match.group(2))
    fill_color = match.group(3)
    return (
        f'<rect width="{width - 1}" height="{height - 1}" x="0.5" y="0.5" '
        f'fill="{fill_color}" rx="{corner_radius}" ry="{corner_radius}" '
        f'stroke="{stroke_color}" stroke-width="1"/>'
    )


def inject_badge_border(
    raw_svg: str, stroke_color: str, corner_radius: int = 6
) -> str:
    """Replaces flat shields.io background rectangles with rounded bordered rects.

    Args:
        raw_svg: Raw SVG string returned by shields.io.
        stroke_color: Hex color string (e.g. '#89b4fa') for the border stroke.
        corner_radius: Corner radius (`rx` and `ry`) in pixels. Defaults to 6.

    Returns:
        SVG string with rounded stroke borders injected onto background rects.

    Raises:
        ValueError: If `raw_svg` or `stroke_color` is empty, or `corner_radius`
            is negative.
    """
    if not raw_svg.strip() or "<svg" not in raw_svg:
        raise ValueError("raw_svg must be a non-empty SVG string.")
    if not stroke_color.strip():
        raise ValueError("stroke_color must not be empty.")
    if corner_radius < 0:
        raise ValueError("corner_radius must be non-negative.")

    normalized_stroke = (
        stroke_color.strip()
        if stroke_color.strip().startswith("#")
        else f"#{stroke_color.strip()}"
    )
    return _SHIELD_RECT_PATTERN.sub(
        lambda match: _format_bordered_rect(match, normalized_stroke, corner_radius),
        raw_svg,
    )


def _inject_fill_into_tag(
    match: re.Match[str], tag_name: str, fill_color: str
) -> str:
    """Adds a `fill` attribute to an SVG shape opening or self-closing tag."""
    attributes = match.group(1)
    closing_slash = match.group(2)
    if "fill=" in attributes:
        return match.group(0)
    return f'<{tag_name}{attributes} fill="{fill_color}"{closing_slash}>'


def _apply_shape_fill(svg_text: str, fill_color: str) -> str:
    """Applies `fill_color` to existing `fill` attributes and unstyled shape tags."""
    recolored = _FILL_ATTR_PATTERN.sub(f'fill="{fill_color}"', svg_text)
    for tag in _SHAPE_TAGS:
        pattern = re.compile(rf"<{tag}\b([^/>]*)(/?)>")
        recolored = pattern.sub(
            lambda match: _inject_fill_into_tag(match, tag, fill_color),
            recolored,
        )
    return recolored


def colorize_and_encode_logo_svg(
    raw_svg: str, fill_color: str | None = None
) -> str:
    """Sanitizes, optionally recolors, and URL-safe base64-encodes an icon SVG.

    Args:
        raw_svg: Raw SVG markup for the logo icon.
        fill_color: Optional hex color to override shape fills.

    Returns:
        Base64-encoded SVG string with `+` escaped as `%2B` for shields.io URLs.

    Raises:
        ValueError: If `raw_svg` is empty or does not contain `<svg`.
    """
    if not raw_svg.strip() or "<svg" not in raw_svg:
        raise ValueError("raw_svg must be a non-empty SVG string.")

    cleaned_svg = _XML_DECL_PATTERN.sub("", raw_svg)
    cleaned_svg = _HTML_COMMENT_PATTERN.sub("", cleaned_svg).strip()

    if fill_color is not None:
        if not fill_color.strip():
            raise ValueError("fill_color must not be an empty string when provided.")
        cleaned_svg = _apply_shape_fill(cleaned_svg, fill_color.strip())

    encoded = base64.b64encode(cleaned_svg.encode("utf-8")).decode("utf-8")
    return encoded.replace("+", "%2B")


def build_institution_logo_svg(image_bytes: bytes, spec: LogoSpec) -> str:
    """Wraps raw PNG/image bytes into a rounded 24x24 SVG container.

    When `spec.background_color` is set, renders a colored `<rect>` background
    and insets the `<image>` by `spec.padding`. Otherwise, clips the full-bleed
    `<image>` using a `<clipPath id="round">` rounded rectangle.

    Args:
        image_bytes: Raw binary image payload (e.g. PNG bytes).
        spec: The `LogoSpec` defining dimensions, rounding, and background.

    Returns:
        Complete SVG XML string embedding the base64-encoded image.

    Raises:
        ValueError: If `image_bytes` is empty.
    """
    if not image_bytes:
        raise ValueError("image_bytes must not be empty.")

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    size = spec.size
    radius = spec.corner_radius

    if spec.background_color is not None:
        bg_color = (
            spec.background_color
            if spec.background_color.startswith("#")
            else f"#{spec.background_color}"
        )
        inner_size = size - 2 * spec.padding
        offset = spec.padding
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">\n'
            f'  <rect width="{size}" height="{size}" rx="{radius}" ry="{radius}" fill="{bg_color}" />\n'
            f'  <image href="data:image/png;base64,{encoded_image}" '
            f'width="{inner_size}" height="{inner_size}" x="{offset}" y="{offset}" />\n'
            f"</svg>"
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">\n'
        f"  <defs>\n"
        f'    <clipPath id="round">\n'
        f'      <rect width="{size}" height="{size}" rx="{radius}" ry="{radius}" />\n'
        f"    </clipPath>\n"
        f"  </defs>\n"
        f'  <image href="data:image/png;base64,{encoded_image}" '
        f'width="{size}" height="{size}" clip-path="url(#round)" />\n'
        f"</svg>"
    )
