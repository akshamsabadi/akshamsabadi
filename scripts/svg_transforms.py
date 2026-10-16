"""Pure SVG transformation and construction functions for profile assets."""

import base64
from collections.abc import Mapping, Sequence
import html
import re
from typing import Final

from scripts.models import (
    CATPPUCCIN_BASE,
    CATPPUCCIN_BLUE,
    CATPPUCCIN_GREEN,
    CATPPUCCIN_OVERLAY0,
    CATPPUCCIN_SUBTEXT0,
    CATPPUCCIN_SURFACE0,
    CATPPUCCIN_SURFACE1,
    ExperienceEntrySpec,
    LogoSpec,
    PURE_WHITE,
)

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

_EMBEDDED_PNG_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"data:image/png;base64,([A-Za-z0-9+/=]+)"
)
_EMBEDDED_FONT_URL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"src:\s*url\((data:font/truetype;base64,[^)]+)\)"
)

_TIMELINE_WIDTH: Final[int] = 800
_TIMELINE_HEIGHT: Final[int] = 315
_TIMELINE_START_Y: Final[int] = 8
_TIMELINE_ROW_STRIDE: Final[int] = 64
_TIMELINE_LOGO_X: Final[int] = 1
_TIMELINE_LOGO_SIZE: Final[int] = 36
_TIMELINE_LOGO_RADIUS: Final[int] = 8
_TIMELINE_LOGO_INSET: Final[int] = 3
_TIMELINE_SPINE_X: Final[int] = 19
_TIMELINE_SPINE_GAP: Final[int] = 5
_TIMELINE_TEXT_X: Final[int] = 52
_TIMELINE_INSTITUTION_Y_OFFSET: Final[int] = 14
_TIMELINE_ROLE_Y_OFFSET: Final[int] = 33
_CURRENT_PILL_X: Final[int] = 194
_CURRENT_PILL_Y_OFFSET: Final[int] = 0
_CURRENT_PILL_WIDTH: Final[int] = 66
_CURRENT_PILL_HEIGHT: Final[int] = 17
_CURRENT_PILL_RADIUS: Final[int] = 5
_CURRENT_PILL_TEXT_X: Final[int] = 227
_CURRENT_PILL_TEXT_Y_OFFSET: Final[int] = 12
_FONT_STACK: Final[str] = (
    "'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
)


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


def extract_embedded_png_base64(logo_svg: str) -> str:
    """Extracts the base64 PNG payload from an institution logo SVG string.

    Args:
        logo_svg: Raw SVG XML containing a `data:image/png;base64,...` href.

    Returns:
        The extracted base64-encoded PNG string.

    Raises:
        ValueError: If no embedded PNG data URI is found in `logo_svg`.
    """
    match = _EMBEDDED_PNG_PATTERN.search(logo_svg)
    if match is None:
        raise ValueError("No embedded data:image/png;base64 payload found in SVG.")
    return match.group(1)


def extract_font_url_from_typing_svg(raw_svg: str) -> str:
    """Extracts the `data:font/truetype;base64,...` URI from a typing SVG.

    Args:
        raw_svg: Raw SVG string returned by `readme-typing-svg.demolab.com`.

    Returns:
        The `data:font/truetype;base64,...` URL string.

    Raises:
        ValueError: If no embedded `@font-face` truetype data URL is present.
    """
    match = _EMBEDDED_FONT_URL_PATTERN.search(raw_svg)
    if match is None:
        raise ValueError("No embedded truetype font data URI found in SVG.")
    return match.group(1)


def _build_timeline_style_block(font_urls: Mapping[int, str] | None) -> str:
    """Builds the `<style>` element with `@font-face` declarations for Poppins."""
    if not font_urls:
        return ""
    rules: list[str] = []
    for weight in sorted(font_urls):
        data_url = font_urls[weight]
        rules.append(
            "    @font-face {\n"
            "      font-family: 'Poppins';\n"
            "      font-style: normal;\n"
            f"      font-weight: {weight};\n"
            "      font-display: fallback;\n"
            f"      src: url({data_url}) format('truetype');\n"
            "    }"
        )
    joined_rules = "\n".join(rules)
    return f"  <style>\n{joined_rules}\n  </style>\n"


def _build_timeline_defs(entries: Sequence[ExperienceEntrySpec]) -> str:
    """Builds `<defs>` with rounded `<clipPath>` elements for full-bleed logos."""
    clip_paths: list[str] = []
    for index, entry in enumerate(entries):
        if entry.normalized_background_color is not None:
            continue
        logo_y = _TIMELINE_START_Y + index * _TIMELINE_ROW_STRIDE
        clip_paths.append(
            f'    <clipPath id="clip-{entry.logo_stem}">\n'
            f'      <rect x="{_TIMELINE_LOGO_X}" y="{logo_y}" '
            f'width="{_TIMELINE_LOGO_SIZE}" height="{_TIMELINE_LOGO_SIZE}" '
            f'rx="{_TIMELINE_LOGO_RADIUS}" ry="{_TIMELINE_LOGO_RADIUS}"/>\n'
            f"    </clipPath>"
        )
    if not clip_paths:
        return ""
    joined = "\n".join(clip_paths)
    return f"  <defs>\n{joined}\n  </defs>\n"


def _build_timeline_connector_lines(entry_count: int) -> str:
    """Builds vertical connector spine lines between consecutive timeline logos."""
    lines: list[str] = []
    for index in range(entry_count - 1):
        logo_y = _TIMELINE_START_Y + index * _TIMELINE_ROW_STRIDE
        next_logo_y = _TIMELINE_START_Y + (index + 1) * _TIMELINE_ROW_STRIDE
        y1 = logo_y + _TIMELINE_LOGO_SIZE + _TIMELINE_SPINE_GAP
        y2 = next_logo_y - _TIMELINE_SPINE_GAP
        lines.append(
            f'  <line x1="{_TIMELINE_SPINE_X}" y1="{y1}" '
            f'x2="{_TIMELINE_SPINE_X}" y2="{y2}" '
            f'stroke="{CATPPUCCIN_SURFACE1}" stroke-width="2" stroke-linecap="round"/>'
        )
    return "\n".join(lines) + ("\n" if lines else "")


def _build_timeline_logo_element(
    entry: ExperienceEntrySpec, logo_y: int, png_base64: str
) -> str:
    """Builds the 36x36 rounded logo and border elements for a single entry."""
    bg_color = entry.normalized_background_color
    if bg_color is not None:
        inner_size = _TIMELINE_LOGO_SIZE - 2 * _TIMELINE_LOGO_INSET
        img_x = _TIMELINE_LOGO_X + _TIMELINE_LOGO_INSET
        img_y = logo_y + _TIMELINE_LOGO_INSET
        return (
            f'  <rect x="{_TIMELINE_LOGO_X}" y="{logo_y}" '
            f'width="{_TIMELINE_LOGO_SIZE}" height="{_TIMELINE_LOGO_SIZE}" '
            f'rx="{_TIMELINE_LOGO_RADIUS}" ry="{_TIMELINE_LOGO_RADIUS}" '
            f'fill="{bg_color}" stroke="{CATPPUCCIN_SURFACE0}" stroke-width="1"/>\n'
            f'  <image href="data:image/png;base64,{png_base64}" '
            f'x="{img_x}" y="{img_y}" width="{inner_size}" height="{inner_size}"/>'
        )

    return (
        f'  <image href="data:image/png;base64,{png_base64}" '
        f'x="{_TIMELINE_LOGO_X}" y="{logo_y}" '
        f'width="{_TIMELINE_LOGO_SIZE}" height="{_TIMELINE_LOGO_SIZE}" '
        f'clip-path="url(#clip-{entry.logo_stem})"/>\n'
        f'  <rect x="{_TIMELINE_LOGO_X}" y="{logo_y}" '
        f'width="{_TIMELINE_LOGO_SIZE}" height="{_TIMELINE_LOGO_SIZE}" '
        f'rx="{_TIMELINE_LOGO_RADIUS}" ry="{_TIMELINE_LOGO_RADIUS}" '
        f'fill="none" stroke="{CATPPUCCIN_SURFACE0}" stroke-width="1"/>'
    )


def _build_timeline_text_elements(entry: ExperienceEntrySpec, logo_y: int) -> str:
    """Builds the institution heading, optional CURRENT pill, and role subtitle."""
    escaped_institution = html.escape(entry.institution)
    escaped_role = html.escape(entry.role)
    escaped_department = html.escape(entry.department)

    inst_y = logo_y + _TIMELINE_INSTITUTION_Y_OFFSET
    role_y = logo_y + _TIMELINE_ROLE_Y_OFFSET

    elements: list[str] = [
        f'  <text x="{_TIMELINE_TEXT_X}" y="{inst_y}" '
        f'font-family="{_FONT_STACK}" font-weight="600" font-size="15.5" '
        f'fill="{PURE_WHITE}">{escaped_institution}</text>'
    ]

    if entry.is_current:
        pill_y = logo_y + _CURRENT_PILL_Y_OFFSET
        pill_text_y = logo_y + _CURRENT_PILL_TEXT_Y_OFFSET
        elements.append(
            f'  <rect x="{_CURRENT_PILL_X}" y="{pill_y}" '
            f'width="{_CURRENT_PILL_WIDTH}" height="{_CURRENT_PILL_HEIGHT}" '
            f'rx="{_CURRENT_PILL_RADIUS}" ry="{_CURRENT_PILL_RADIUS}" '
            f'fill="#{CATPPUCCIN_BASE}" stroke="{CATPPUCCIN_GREEN}" stroke-width="1"/>'
        )
        elements.append(
            f'  <text x="{_CURRENT_PILL_TEXT_X}" y="{pill_text_y}" '
            f'text-anchor="middle" font-family="\'Poppins\', sans-serif" '
            f'font-weight="600" font-size="9.5" letter-spacing="0.8" '
            f'fill="{CATPPUCCIN_GREEN}">CURRENT</text>'
        )

    elements.append(
        f'  <text x="{_TIMELINE_TEXT_X}" y="{role_y}" '
        f'font-family="{_FONT_STACK}" font-size="13.5">'
        f'<tspan font-weight="500" fill="{CATPPUCCIN_BLUE}">{escaped_role}</tspan>'
        f'<tspan fill="{CATPPUCCIN_OVERLAY0}"> · </tspan>'
        f'<tspan font-weight="400" font-style="italic" fill="{CATPPUCCIN_SUBTEXT0}">'
        f"{escaped_department}</tspan></text>"
    )
    return "\n".join(elements)


def build_experience_timeline_svg(
    entries: Sequence[ExperienceEntrySpec],
    logo_base64_map: Mapping[str, str],
    font_urls: Mapping[int, str] | None = None,
) -> str:
    """Constructs the complete Catppuccin & Poppins experience timeline SVG.

    Args:
        entries: Ordered sequence of `ExperienceEntrySpec` rows.
        logo_base64_map: Mapping from `logo_stem` to base64-encoded PNG data.
        font_urls: Optional mapping from font weight (e.g. 500, 600) to
            `data:font/truetype;base64,...` URL strings.

    Returns:
        Complete SVG XML string for `assets/experience_timeline.svg`.

    Raises:
        ValueError: If `entries` is empty or any entry's `logo_stem` is missing
            or empty in `logo_base64_map`.
    """
    if not entries:
        raise ValueError("entries must not be empty.")

    for entry in entries:
        b64 = logo_base64_map.get(entry.logo_stem, "").strip()
        if not b64:
            raise ValueError(
                f"Missing base64 PNG data for logo_stem '{entry.logo_stem}'."
            )

    style_block = _build_timeline_style_block(font_urls)
    defs_block = _build_timeline_defs(entries)
    connector_lines = _build_timeline_connector_lines(len(entries))

    row_blocks: list[str] = []
    for index, entry in enumerate(entries):
        logo_y = _TIMELINE_START_Y + index * _TIMELINE_ROW_STRIDE
        png_b64 = logo_base64_map[entry.logo_stem].strip()
        logo_markup = _build_timeline_logo_element(entry, logo_y, png_b64)
        text_markup = _build_timeline_text_elements(entry, logo_y)
        row_blocks.append(f"{logo_markup}\n{text_markup}")

    joined_rows = "\n".join(row_blocks)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_TIMELINE_WIDTH} {_TIMELINE_HEIGHT}" '
        f'width="{_TIMELINE_WIDTH}" height="{_TIMELINE_HEIGHT}" '
        f'style="background-color: #00000000;">\n'
        f"{style_block}"
        f"{defs_block}"
        f"{connector_lines}"
        f"{joined_rows}\n"
        f"</svg>\n"
    )
