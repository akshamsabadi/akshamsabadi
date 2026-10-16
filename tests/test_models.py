"""Unit tests for domain value objects in `scripts.models`."""

from dataclasses import FrozenInstanceError
import pytest

from scripts import __version__
from scripts.models import (
    BadgeSpec,
    CATPPUCCIN_BASE,
    CATPPUCCIN_BLUE,
    CATPPUCCIN_MAUVE,
    ExperienceEntrySpec,
    LogoSpec,
    Publication,
    TitleSpec,
    ToolkitCategorySpec,
)


class TestPackageMetadata:
    """Tests for package-level version and metadata."""

    def test_version_matches_expected_semver(self) -> None:
        """Verifies the package version is set to 0.9.2."""
        assert __version__ == "0.9.2"


class TestTitleSpec:
    """Tests for `TitleSpec` normal, edge, and failure behaviors."""

    def test_creates_centered_title_and_builds_url(self) -> None:
        """Verifies URL construction for a centered title banner."""
        spec = TitleSpec(
            name="title_main",
            text="André Kütahya Shamsabadi",
            font_size=40,
            font_weight=600,
            color_hex=CATPPUCCIN_MAUVE,
            width=800,
            height=60,
            is_centered=True,
        )
        assert spec.output_filename == "title_main.svg"
        url = spec.to_typing_svg_url()
        assert "font=Poppins" in url
        assert "weight=600&size=40" in url
        assert "color=cba6f7" in url
        assert "&center=true&vCenter=true" in url
        assert "width=800&height=60" in url
        assert "lines=Andr%C3%A9+K%C3%BCtahya+Shamsabadi" in url

    def test_creates_left_aligned_title_without_center_param(self) -> None:
        """Verifies left-aligned titles omit `&center=true` and accept unprefixed hex."""
        spec = TitleSpec(
            name="title_about",
            text="✦ About Me",
            font_size=22,
            font_weight=600,
            color_hex="cba6f7",
            width=300,
            height=35,
            is_centered=False,
        )
        url = spec.to_typing_svg_url()
        assert "&center=true" not in url
        assert "color=cba6f7" in url

    def test_title_spec_is_immutable(self) -> None:
        """Verifies `TitleSpec` instances cannot be mutated after creation."""
        spec = TitleSpec(
            name="title_exp",
            text="✦ Experience",
            font_size=22,
            font_weight=600,
            color_hex=CATPPUCCIN_MAUVE,
            width=300,
            height=35,
        )
        with pytest.raises(FrozenInstanceError):
            spec.width = 500  # type: ignore[misc]

    @pytest.mark.parametrize(
        ("kwargs", "match_msg"),
        [
            (
                {
                    "name": "   ",
                    "text": "Valid",
                    "font_size": 20,
                    "font_weight": 500,
                    "color_hex": "#cba6f7",
                    "width": 100,
                    "height": 30,
                },
                "TitleSpec.name must not be empty",
            ),
            (
                {
                    "name": "title_valid",
                    "text": "",
                    "font_size": 20,
                    "font_weight": 500,
                    "color_hex": "#cba6f7",
                    "width": 100,
                    "height": 30,
                },
                "TitleSpec.text must not be empty",
            ),
            (
                {
                    "name": "title_valid",
                    "text": "Valid",
                    "font_size": 0,
                    "font_weight": 500,
                    "color_hex": "#cba6f7",
                    "width": 100,
                    "height": 30,
                },
                "font_size and font_weight must be positive",
            ),
            (
                {
                    "name": "title_valid",
                    "text": "Valid",
                    "font_size": 20,
                    "font_weight": 500,
                    "color_hex": "#cba6f7",
                    "width": -10,
                    "height": 30,
                },
                "width and height must be positive",
            ),
            (
                {
                    "name": "title_valid",
                    "text": "Valid",
                    "font_size": 20,
                    "font_weight": 500,
                    "color_hex": "#",
                    "width": 100,
                    "height": 30,
                },
                "Color string must not be empty",
            ),
        ],
    )
    def test_invalid_title_spec_raises_value_error(
        self, kwargs: dict[str, object], match_msg: str
    ) -> None:
        """Verifies invalid `TitleSpec` parameters raise `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            TitleSpec(**kwargs)  # type: ignore[arg-type]


class TestBadgeSpec:
    """Tests for `BadgeSpec` normal, edge, and failure behaviors."""

    def test_slug_badge_builds_shields_url_and_filename(self) -> None:
        """Verifies standard Simple Icons slug badge URL and output filename."""
        spec = BadgeSpec(
            name="Google Scholar",
            stroke_color=CATPPUCCIN_BLUE,
            logo_slug="google-scholar",
        )
        assert spec.output_filename == "badge_Google_Scholar.svg"
        assert spec.normalized_stroke_color == "#89b4fa"
        assert spec.label_color == CATPPUCCIN_BASE
        url = spec.to_shields_url()
        assert (
            url
            == "https://img.shields.io/badge/Google%20Scholar-1e1e2e"
            "?style=for-the-badge&logo=google-scholar&logoColor=89b4fa"
        )

    def test_custom_svg_badge_builds_data_uri_shields_url(self) -> None:
        """Verifies custom SVG badge embeds base64 data URI in shields URL."""
        spec = BadgeSpec(
            name="Antigravity",
            stroke_color="cba6f7",
            custom_logo_svg="<svg><path/></svg>",
        )
        assert spec.normalized_stroke_color == "#cba6f7"
        assert spec.output_filename == "badge_Antigravity.svg"
        url = spec.to_shields_url(encoded_custom_logo="PHN2Zz4%2B")
        assert "logo=data:image/svg%2Bxml;base64,PHN2Zz4%2B" in url
        assert "logoColor=cba6f7" in url

    def test_custom_svg_badge_without_encoded_logo_raises_value_error(self) -> None:
        """Verifies calling `to_shields_url` without `encoded_custom_logo` fails."""
        spec = BadgeSpec(
            name="Antigravity",
            stroke_color=CATPPUCCIN_MAUVE,
            custom_logo_svg="<svg/>",
        )
        with pytest.raises(ValueError, match="encoded_custom_logo is required"):
            spec.to_shields_url()

    @pytest.mark.parametrize(
        ("name", "stroke_color", "logo_slug", "custom_logo_svg", "match_msg"),
        [
            ("", "#89b4fa", "python", None, "BadgeSpec.name must not be empty"),
            ("Python", "", "python", None, "Color string must not be empty"),
            (
                "Python",
                "#89b4fa",
                None,
                None,
                "Exactly one of `logo_slug` or `custom_logo_svg`",
            ),
            (
                "Python",
                "#89b4fa",
                "python",
                "<svg/>",
                "Exactly one of `logo_slug` or `custom_logo_svg`",
            ),
        ],
    )
    def test_invalid_badge_spec_raises_value_error(
        self,
        name: str,
        stroke_color: str,
        logo_slug: str | None,
        custom_logo_svg: str | None,
        match_msg: str,
    ) -> None:
        """Verifies invalid `BadgeSpec` combinations raise `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            BadgeSpec(
                name=name,
                stroke_color=stroke_color,
                logo_slug=logo_slug,
                custom_logo_svg=custom_logo_svg,
            )


class TestToolkitCategorySpec:
    """Tests for `ToolkitCategorySpec` normal, edge, and failure behaviors."""

    def test_valid_toolkit_category_spec(self) -> None:
        """Verifies `ToolkitCategorySpec` stores title and badges tuple."""
        badge = BadgeSpec(
            name="Obsidian", stroke_color=CATPPUCCIN_MAUVE, logo_slug="obsidian"
        )
        category = ToolkitCategorySpec(
            title="Programming & Ecosystem", badges=(badge,)
        )
        assert category.title == "Programming & Ecosystem"
        assert category.badges == (badge,)

    @pytest.mark.parametrize(
        ("title", "badges", "match_msg"),
        [
            (
                "   ",
                (
                    BadgeSpec(
                        name="Obsidian",
                        stroke_color=CATPPUCCIN_MAUVE,
                        logo_slug="obsidian",
                    ),
                ),
                "ToolkitCategorySpec.title must not be empty",
            ),
            (
                "Design & Visualisation",
                (),
                "ToolkitCategorySpec.badges must not be empty",
            ),
        ],
    )
    def test_invalid_toolkit_category_raises_value_error(
        self, title: str, badges: tuple[BadgeSpec, ...], match_msg: str
    ) -> None:
        """Verifies empty `title` or empty `badges` raises `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            ToolkitCategorySpec(title=title, badges=badges)


class TestLogoSpec:
    """Tests for `LogoSpec` normal, edge, and failure behaviors."""

    def test_valid_logo_spec_properties(self) -> None:
        """Verifies `LogoSpec` defaults and `output_filename`."""
        spec = LogoSpec(
            name="az_logo",
            source_url="https://example.com/az.png",
            background_color="#8A0051",
        )
        assert spec.output_filename == "az_logo.svg"
        assert spec.size == 24
        assert spec.corner_radius == 4
        assert spec.padding == 2

    @pytest.mark.parametrize(
        ("kwargs", "match_msg"),
        [
            (
                {"name": "", "source_url": "https://example.com/a.png"},
                "LogoSpec.name must not be empty",
            ),
            (
                {"name": "iso", "source_url": "   "},
                "LogoSpec.source_url must not be empty",
            ),
            (
                {"name": "iso", "source_url": "https://a.com", "size": 0},
                "LogoSpec.size must be positive",
            ),
            (
                {"name": "iso", "source_url": "https://a.com", "corner_radius": -1},
                "LogoSpec.corner_radius must be non-negative",
            ),
            (
                {"name": "iso", "source_url": "https://a.com", "size": 24, "padding": 12},
                "LogoSpec.padding must be non-negative and less than half of size",
            ),
            (
                {"name": "iso", "source_url": "https://a.com", "background_color": "#"},
                "Color string must not be empty",
            ),
        ],
    )
    def test_invalid_logo_spec_raises_value_error(
        self, kwargs: dict[str, object], match_msg: str
    ) -> None:
        """Verifies invalid `LogoSpec` inputs raise `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            LogoSpec(**kwargs)  # type: ignore[arg-type]


class TestExperienceEntrySpec:
    """Tests for `ExperienceEntrySpec` normal, edge, and failure behaviors."""

    def test_valid_experience_entry_properties(self) -> None:
        """Verifies `logo_filename` and `normalized_background_color`."""
        current_entry = ExperienceEntrySpec(
            institution="Isomorphic Labs",
            role="Research Investigator",
            department="Exploratory Sciences",
            logo_stem="iso_logo",
            is_current=True,
        )
        assert current_entry.logo_filename == "iso_logo.svg"
        assert current_entry.normalized_background_color is None
        assert current_entry.is_current is True

        bg_entry = ExperienceEntrySpec(
            institution="AstraZeneca",
            role="Senior Scientist",
            department="Oncology Targeted Delivery",
            logo_stem="az_logo",
            background_color="8A0051",
        )
        assert bg_entry.normalized_background_color == "#8A0051"

    @pytest.mark.parametrize(
        ("kwargs", "match_msg"),
        [
            (
                {
                    "institution": "   ",
                    "role": "Role",
                    "department": "Dept",
                    "logo_stem": "iso_logo",
                },
                "ExperienceEntrySpec.institution must not be empty",
            ),
            (
                {
                    "institution": "Org",
                    "role": "",
                    "department": "Dept",
                    "logo_stem": "iso_logo",
                },
                "ExperienceEntrySpec.role must not be empty",
            ),
            (
                {
                    "institution": "Org",
                    "role": "Role",
                    "department": "  ",
                    "logo_stem": "iso_logo",
                },
                "ExperienceEntrySpec.department must not be empty",
            ),
            (
                {
                    "institution": "Org",
                    "role": "Role",
                    "department": "Dept",
                    "logo_stem": "",
                },
                "ExperienceEntrySpec.logo_stem must not be empty",
            ),
            (
                {
                    "institution": "Org",
                    "role": "Role",
                    "department": "Dept",
                    "logo_stem": "iso_logo",
                    "background_color": "#",
                },
                "Color string must not be empty",
            ),
        ],
    )
    def test_invalid_experience_entry_raises_value_error(
        self, kwargs: dict[str, object], match_msg: str
    ) -> None:
        """Verifies invalid `ExperienceEntrySpec` inputs raise `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            ExperienceEntrySpec(**kwargs)  # type: ignore[arg-type]


class TestPublication:
    """Tests for `Publication` formatting and validation."""

    def test_to_markdown_formats_publication_correctly(self) -> None:
        """Verifies `Publication.to_markdown` produces the expected heading and metadata."""
        pub = Publication(
            title="Utilizing Constrained Bicyclic Peptides for In Vitro Diagnostics",
            year="2026",
            journal="ACS Nano",
            doi_url="https://doi.org/10.1021/acsnano.6c00001",
        )
        expected = (
            "#### Utilizing Constrained Bicyclic Peptides for In Vitro Diagnostics\n"
            "**2026** • *ACS Nano* • [Full Paper](https://doi.org/10.1021/acsnano.6c00001)"
        )
        assert pub.to_markdown() == expected

    @pytest.mark.parametrize(
        ("title", "year", "journal", "doi_url"),
        [
            ("", "2026", "ACS Nano", "https://doi.org/10.1"),
            ("Title", "  ", "ACS Nano", "https://doi.org/10.1"),
            ("Title", "2026", "", "https://doi.org/10.1"),
            ("Title", "2026", "ACS Nano", ""),
        ],
    )
    def test_empty_publication_field_raises_value_error(
        self, title: str, year: str, journal: str, doi_url: str
    ) -> None:
        """Verifies blank fields in `Publication` raise `ValueError`."""
        with pytest.raises(ValueError, match="must not be empty"):
            Publication(title=title, year=year, journal=journal, doi_url=doi_url)
