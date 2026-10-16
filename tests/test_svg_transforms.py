"""Unit tests for pure SVG transformation functions in `scripts.svg_transforms`."""

import base64
import xml.etree.ElementTree as ET
import pytest

from scripts.models import (
    BadgeSpec,
    CATPPUCCIN_BLUE,
    CATPPUCCIN_MAUVE,
    ExperienceEntrySpec,
    LogoSpec,
    ToolkitCategorySpec,
)
from scripts.svg_transforms import (
    build_badge_pill_svg,
    build_experience_timeline_svg,
    build_institution_logo_svg,
    build_technical_toolkit_svg,
    colorize_and_encode_logo_svg,
    convert_typing_svg_to_static,
    extract_embedded_png_base64,
    extract_embedded_svg_base64,
    extract_font_url_from_typing_svg,
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


class TestExtractorsAndExperienceTimelineSvg:
    """Tests for `extract_embedded_png_base64`, `extract_font_url_from_typing_svg`, and `build_experience_timeline_svg`."""

    def test_extract_embedded_png_base64_returns_payload(self) -> None:
        """Verifies embedded PNG base64 string is extracted accurately."""
        svg = '<svg><image href="data:image/png;base64,iVBORw0KGgo=" width="24"/></svg>'
        assert extract_embedded_png_base64(svg) == "iVBORw0KGgo="

    def test_extract_embedded_png_base64_raises_when_missing(self) -> None:
        """Verifies `ValueError` is raised if no PNG data URI is present."""
        with pytest.raises(ValueError, match="No embedded data:image/png;base64"):
            extract_embedded_png_base64("<svg><rect/></svg>")

    def test_extract_font_url_from_typing_svg_returns_data_uri(self) -> None:
        """Verifies `@font-face` truetype data URL is extracted."""
        svg = "<svg><style>@font-face { src: url(data:font/truetype;base64,AAEAAA==) format('truetype'); }</style></svg>"
        assert (
            extract_font_url_from_typing_svg(svg)
            == "data:font/truetype;base64,AAEAAA=="
        )

    def test_extract_font_url_from_typing_svg_raises_when_missing(self) -> None:
        """Verifies `ValueError` is raised when no font data URI exists."""
        with pytest.raises(ValueError, match="No embedded truetype font"):
            extract_font_url_from_typing_svg("<svg></svg>")

    def test_build_experience_timeline_svg_renders_valid_xml_with_current_pill_and_spine(
        self,
    ) -> None:
        """Verifies timeline SVG structure, connector spine, CURRENT pill, and XML escaping."""
        entries = [
            ExperienceEntrySpec(
                institution="Isomorphic Labs",
                role="Research Investigator",
                department="Exploratory Sciences",
                logo_stem="iso_logo",
                is_current=True,
            ),
            ExperienceEntrySpec(
                institution="Imperial College London",
                role="Postdoctoral Research Associate",
                department="Chemical Biology & Materials",
                logo_stem="imperial_logo",
                background_color="#8A0051",
            ),
        ]
        logos = {"iso_logo": "iVBORw0KGgo=", "imperial_logo": "QUJDRA=="}
        fonts = {500: "data:font/truetype;base64,FONT500=", 600: "data:font/truetype;base64,FONT600="}

        svg = build_experience_timeline_svg(entries, logos, font_urls=fonts)
        ET.fromstring(svg)

        assert 'viewBox="0 0 800 315"' in svg
        assert "FONT600=" in svg
        assert 'clipPath id="clip-iso_logo"' in svg
        assert '<line x1="19" y1="49" x2="19" y2="67" stroke="#45475a"' in svg
        assert ">CURRENT</text>" in svg
        assert "Chemical Biology &amp; Materials" in svg
        assert 'fill="#8A0051"' in svg

    def test_build_experience_timeline_svg_without_fonts_or_clipped_logos(self) -> None:
        """Verifies timeline SVG omits `<style>` and `<defs>` when not needed."""
        entries = [
            ExperienceEntrySpec(
                institution="AstraZeneca",
                role="Senior Scientist",
                department="Oncology Targeted Delivery",
                logo_stem="az_logo",
                background_color="#8A0051",
            )
        ]
        svg = build_experience_timeline_svg(
            entries, {"az_logo": "iVBORw0KGgo="}, font_urls=None
        )
        ET.fromstring(svg)
        assert "<style>" not in svg
        assert "<defs>" not in svg
        assert "<line " not in svg

    @pytest.mark.parametrize(
        ("entries", "logo_map", "match_msg"),
        [
            ([], {"iso_logo": "abc"}, "entries must not be empty"),
            (
                [
                    ExperienceEntrySpec(
                        institution="UCL",
                        role="PhD Researcher",
                        department="Chemistry",
                        logo_stem="ucl_logo",
                    )
                ],
                {},
                "Missing base64 PNG data for logo_stem 'ucl_logo'",
            ),
        ],
    )
    def test_build_experience_timeline_svg_invalid_inputs_raise_value_error(
        self,
        entries: list[ExperienceEntrySpec],
        logo_map: dict[str, str],
        match_msg: str,
    ) -> None:
        """Verifies empty `entries` or missing logo data raises `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            build_experience_timeline_svg(entries, logo_map)

    def test_extract_embedded_svg_base64_returns_payload(self) -> None:
        """Verifies embedded SVG base64 string is extracted from a badge SVG."""
        svg = '<svg><image href="data:image/svg+xml;base64,PHN2Zz4="/></svg>'
        assert extract_embedded_svg_base64(svg) == "PHN2Zz4="

    def test_extract_embedded_svg_base64_raises_when_missing(self) -> None:
        """Verifies `ValueError` is raised when no SVG data URI is present."""
        with pytest.raises(ValueError, match="No embedded data:image/svg\\+xml;base64"):
            extract_embedded_svg_base64("<svg><rect/></svg>")

    def test_build_technical_toolkit_svg_renders_categories_and_pills(self) -> None:
        """Verifies toolkit SVG structure, solid pastel fills, and dark #1e1e2e text/icons."""
        obsidian = BadgeSpec(
            name="Obsidian", stroke_color=CATPPUCCIN_MAUVE, logo_slug="obsidian"
        )
        vscode = BadgeSpec(
            name="VS Code", stroke_color=CATPPUCCIN_BLUE, custom_logo_svg="<svg/>"
        )
        categories = (
            ToolkitCategorySpec(
                title="Programming & Ecosystem", badges=(obsidian, vscode)
            ),
        )
        raw_icon_1 = base64.b64encode(
            b'<svg fill="#cba6f7"><path d="M0 0"/></svg>'
        ).decode("utf-8")
        raw_icon_2 = base64.b64encode(
            b'<svg fill="#89b4fa"><path d="M1 1"/></svg>'
        ).decode("utf-8")
        icons = {"Obsidian": raw_icon_1, "VS Code": raw_icon_2}
        svg = build_technical_toolkit_svg(
            categories, icons, font_url="data:font/truetype;base64,FONT600="
        )
        ET.fromstring(svg)

        assert 'viewBox="0 0 800 154"' in svg
        assert 'y="34"' in svg
        assert "Programming &amp; Ecosystem" in svg
        assert 'fill="#cba6f7" stroke="#cba6f7"' in svg
        assert 'fill="#89b4fa" stroke="#89b4fa"' in svg
        assert 'fill="#1e1e2e">OBSIDIAN</text>' in svg
        assert 'fill="#1e1e2e">VS CODE</text>' in svg

        embedded_b64 = extract_embedded_svg_base64(svg)
        decoded_icon = base64.b64decode(embedded_b64).decode("utf-8")
        assert 'fill="#1e1e2e"' in decoded_icon
        assert "#cba6f7" not in decoded_icon

    @pytest.mark.parametrize(
        ("categories", "icon_map", "match_msg"),
        [
            ((), {"Obsidian": "PHN2Zz4="}, "categories must not be empty"),
            (
                (
                    ToolkitCategorySpec(
                        title="Design & Visualisation",
                        badges=(
                            BadgeSpec(
                                name="PyMOL",
                                stroke_color=CATPPUCCIN_BLUE,
                                logo_slug="moleculer",
                            ),
                        ),
                    ),
                ),
                {},
                "Missing base64 SVG icon for badge 'PyMOL'",
            ),
        ],
    )
    def test_build_technical_toolkit_svg_invalid_inputs_raise_value_error(
        self,
        categories: tuple[ToolkitCategorySpec, ...],
        icon_map: dict[str, str],
        match_msg: str,
    ) -> None:
        """Verifies empty `categories` or missing badge icon raises `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            build_technical_toolkit_svg(categories, icon_map)

    def test_build_badge_pill_svg_renders_solid_poppins_pill(self) -> None:
        """Verifies standalone pill badge SVG has solid fill, dark text/icon, and embedded Poppins."""
        linkedin = BadgeSpec(
            name="LinkedIn", stroke_color=CATPPUCCIN_BLUE, custom_logo_svg="<svg/>"
        )
        raw_icon = base64.b64encode(
            b'<svg fill="#89b4fa"><path d="M0 0"/></svg>'
        ).decode("utf-8")
        svg = build_badge_pill_svg(
            linkedin, raw_icon, font_url="data:font/truetype;base64,FONT600="
        )
        ET.fromstring(svg)

        assert 'aria-label="LINKEDIN"' in svg
        assert "FONT600=" in svg
        assert 'fill="#89b4fa" stroke="#89b4fa"' in svg
        assert 'fill="#1e1e2e">LINKEDIN</text>' in svg

        embedded_b64 = extract_embedded_svg_base64(svg)
        decoded_icon = base64.b64decode(embedded_b64).decode("utf-8")
        assert 'fill="#1e1e2e"' in decoded_icon

    def test_build_badge_pill_svg_empty_icon_raises_value_error(self) -> None:
        """Verifies empty `icon_b64` raises `ValueError`."""
        linkedin = BadgeSpec(
            name="LinkedIn", stroke_color=CATPPUCCIN_BLUE, custom_logo_svg="<svg/>"
        )
        with pytest.raises(ValueError, match="icon_b64 must not be empty"):
            build_badge_pill_svg(linkedin, "   ")
