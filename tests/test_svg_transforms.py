"""Unit tests for pure SVG transformation functions in `scripts.svg_transforms`."""

import base64
import pytest

from scripts.models import LogoSpec
from scripts.svg_transforms import (
    build_institution_logo_svg,
    colorize_and_encode_logo_svg,
    convert_typing_svg_to_static,
    inject_badge_border,
)


class TestConvertTypingSvgToStatic:
    """Tests for `convert_typing_svg_to_static`."""

    def test_strips_animation_path_and_centers_text(self) -> None:
        """Verifies `<path id='path0'>` and `<textPath>` are removed and `y="50%"` added."""
        raw_svg = (
            "<svg viewBox='0 0 800 60'>"
            "<path id='path0'><animate attributeName='d'/></path>"
            "<text font-family='Poppins' fill='#cba6f7'>"
            "<textPath xlink:href='#path0'>André Kütahya Shamsabadi</textPath>"
            "</text></svg>"
        )
        result = convert_typing_svg_to_static(raw_svg)
        assert "<path" not in result
        assert "<textPath" not in result
        assert "</textPath>" not in result
        assert '<text y="50%" font-family=\'Poppins\'' in result
        assert "André Kütahya Shamsabadi" in result

    def test_handles_double_quoted_path_id_and_already_static_svg(self) -> None:
        """Verifies double-quoted `id="path0"` is also stripped cleanly."""
        raw_svg = (
            '<svg><path id="path0">\n<animate/>\n</path>'
            '<text fill="#89b4fa"><textPath href="#path0">Sub</textPath></text></svg>'
        )
        result = convert_typing_svg_to_static(raw_svg)
        assert "path0" not in result
        assert '<text y="50%" fill="#89b4fa">Sub</text>' in result

    @pytest.mark.parametrize("invalid_svg", ["", "   ", "<div>not an svg</div>"])
    def test_invalid_svg_raises_value_error(self, invalid_svg: str) -> None:
        """Verifies empty or non-SVG strings raise `ValueError`."""
        with pytest.raises(ValueError, match="non-empty SVG string"):
            convert_typing_svg_to_static(invalid_svg)


class TestInjectBadgeBorder:
    """Tests for `inject_badge_border`."""

    def test_replaces_background_rect_with_rounded_stroke_border(self) -> None:
        """Verifies width/height are inset by 1px and stroke attributes are injected."""
        raw_svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="114.5" height="28" fill="#1e1e2e"/></svg>'
        result = inject_badge_border(raw_svg, stroke_color="#cba6f7", corner_radius=6)
        assert (
            '<rect width="113.5" height="27.0" x="0.5" y="0.5" '
            'fill="#1e1e2e" rx="6" ry="6" stroke="#cba6f7" stroke-width="1"/>'
        ) in result

    def test_normalizes_unprefixed_stroke_color(self) -> None:
        """Verifies stroke color without `#` is prefixed automatically."""
        raw_svg = '<svg><rect width="80" height="28" fill="#1e1e2e"/></svg>'
        result = inject_badge_border(raw_svg, stroke_color="89b4fa", corner_radius=4)
        assert 'stroke="#89b4fa"' in result
        assert 'rx="4" ry="4"' in result

    @pytest.mark.parametrize(
        ("raw_svg", "stroke_color", "corner_radius", "match_msg"),
        [
            ("", "#89b4fa", 6, "raw_svg must be a non-empty SVG"),
            ("<svg/>", "   ", 6, "stroke_color must not be empty"),
            ("<svg/>", "#89b4fa", -1, "corner_radius must be non-negative"),
        ],
    )
    def test_invalid_inputs_raise_value_error(
        self, raw_svg: str, stroke_color: str, corner_radius: int, match_msg: str
    ) -> None:
        """Verifies invalid arguments to `inject_badge_border` raise `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            inject_badge_border(raw_svg, stroke_color, corner_radius)


class TestColorizeAndEncodeLogoSvg:
    """Tests for `colorize_and_encode_logo_svg`."""

    def test_strips_xml_comments_and_recolors_shapes(self) -> None:
        """Verifies XML prolog/comments are removed and shapes receive `fill_color`."""
        raw_svg = (
            '<?xml version="1.0"?>'
            "<!-- comment -->"
            '<svg viewBox="0 0 24 24" fill="#000000">'
            '<path d="M0 0"/>'
            '<circle cx="5" cy="5" r="2" fill="#ffffff"/>'
            '<polygon points="0,0 1,1"/>'
            "</svg>"
        )
        encoded = colorize_and_encode_logo_svg(raw_svg, fill_color="#cba6f7")
        decoded = base64.b64decode(encoded.replace("%2B", "+")).decode("utf-8")
        assert "<?xml" not in decoded
        assert "<!--" not in decoded
        assert "#000000" not in decoded
        assert "#ffffff" not in decoded
        assert '<path d="M0 0" fill="#cba6f7"/>' in decoded
        assert '<polygon points="0,0 1,1" fill="#cba6f7"/>' in decoded

    def test_encodes_without_recoloring_when_fill_color_is_none(self) -> None:
        """Verifies original fills are preserved when `fill_color` is omitted."""
        raw_svg = '<svg><path d="M1 1" fill="#123456"/></svg>'
        encoded = colorize_and_encode_logo_svg(raw_svg, fill_color=None)
        decoded = base64.b64decode(encoded.replace("%2B", "+")).decode("utf-8")
        assert 'fill="#123456"' in decoded

    @pytest.mark.parametrize(
        ("raw_svg", "fill_color", "match_msg"),
        [
            ("", "#89b4fa", "raw_svg must be a non-empty SVG"),
            ("<svg/>", "   ", "fill_color must not be an empty string"),
        ],
    )
    def test_invalid_inputs_raise_value_error(
        self, raw_svg: str, fill_color: str | None, match_msg: str
    ) -> None:
        """Verifies invalid inputs raise `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            colorize_and_encode_logo_svg(raw_svg, fill_color=fill_color)


class TestBuildInstitutionLogoSvg:
    """Tests for `build_institution_logo_svg`."""

    def test_builds_background_rect_logo_when_background_color_set(self) -> None:
        """Verifies logos with `background_color` use a `<rect>` and inset `<image>`."""
        spec = LogoSpec(
            name="az_logo",
            source_url="https://example.com/az.png",
            background_color="8A0051",
            size=24,
            corner_radius=4,
            padding=2,
        )
        svg = build_institution_logo_svg(b"fake-png-bytes", spec)
        assert '<rect width="24" height="24" rx="4" ry="4" fill="#8A0051" />' in svg
        assert 'width="20" height="20" x="2" y="2"' in svg
        assert "clipPath" not in svg

    def test_builds_clipped_logo_when_background_color_is_none(self) -> None:
        """Verifies logos without `background_color` use `<clipPath id="round">`."""
        spec = LogoSpec(
            name="iso_logo",
            source_url="https://example.com/iso.png",
            background_color=None,
        )
        svg = build_institution_logo_svg(b"fake-png-bytes", spec)
        assert '<clipPath id="round">' in svg
        assert 'clip-path="url(#round)"' in svg
        assert 'width="24" height="24"' in svg

    def test_empty_image_bytes_raises_value_error(self) -> None:
        """Verifies empty `image_bytes` raises `ValueError`."""
        spec = LogoSpec(name="iso_logo", source_url="https://example.com/iso.png")
        with pytest.raises(ValueError, match="image_bytes must not be empty"):
            build_institution_logo_svg(b"", spec)
