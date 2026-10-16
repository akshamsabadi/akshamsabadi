"""Domain value objects and Catppuccin Mocha palette constants for profile assets."""

from dataclasses import dataclass
from typing import Final
import urllib.parse

CATPPUCCIN_BASE: Final[str] = "1e1e2e"
CATPPUCCIN_SURFACE0: Final[str] = "#313244"
CATPPUCCIN_SURFACE1: Final[str] = "#45475a"
CATPPUCCIN_OVERLAY0: Final[str] = "#6c7086"
CATPPUCCIN_SUBTEXT0: Final[str] = "#a6adc8"
CATPPUCCIN_MAUVE: Final[str] = "#cba6f7"
CATPPUCCIN_BLUE: Final[str] = "#89b4fa"
CATPPUCCIN_TEAL: Final[str] = "#94e2d5"
CATPPUCCIN_GREEN: Final[str] = "#a6e3a1"
CATPPUCCIN_YELLOW: Final[str] = "#f9e2af"
CATPPUCCIN_PEACH: Final[str] = "#fab387"
CATPPUCCIN_PINK: Final[str] = "#f5c2e7"
CATPPUCCIN_TEXT: Final[str] = "#cdd6f4"
PURE_WHITE: Final[str] = "#ffffff"

DEFAULT_FONT_FAMILY: Final[str] = "Poppins"
DEFAULT_LOGO_DIMENSION: Final[int] = 24
DEFAULT_CORNER_RADIUS: Final[int] = 4
DEFAULT_LOGO_PADDING: Final[int] = 2

_TYPING_SVG_BASE_URL: Final[str] = "https://readme-typing-svg.demolab.com"
_SHIELDS_BASE_URL: Final[str] = "https://img.shields.io/badge"


def _strip_hex_prefix(color: str) -> str:
    """Removes a leading '#' from a hexadecimal color string if present.

    Args:
        color: A hexadecimal color string (with or without leading '#').

    Returns:
        The normalized 6-character hexadecimal string without '#'.

    Raises:
        ValueError: If the normalized string is empty.
    """
    normalized = color.strip().lstrip("#")
    if not normalized:
        raise ValueError("Color string must not be empty.")
    return normalized


def _ensure_hex_prefix(color: str) -> str:
    """Ensures a hexadecimal color string starts with '#'.

    Args:
        color: A hexadecimal color string (with or without leading '#').

    Returns:
        The normalized hexadecimal string prefixed with '#'.

    Raises:
        ValueError: If the color string is empty.
    """
    return f"#{_strip_hex_prefix(color)}"


@dataclass(frozen=True)
class TitleSpec:
    """Specification for a static Poppins SVG section title banner.

    Attributes:
        name: Output asset stem name (e.g. 'title_main').
        text: Visible heading text rendered inside the SVG.
        font_size: Font size in pixels.
        font_weight: CSS font weight (e.g. 500 or 600).
        color_hex: Hexadecimal text color (with or without '#').
        width: SVG viewport width in pixels.
        height: SVG viewport height in pixels.
        is_centered: Whether the text should be horizontally centered.
        font_family: Font family name used by the typing SVG endpoint.
    """

    name: str
    text: str
    font_size: int
    font_weight: int
    color_hex: str
    width: int
    height: int
    is_centered: bool = False
    font_family: str = DEFAULT_FONT_FAMILY

    def __post_init__(self) -> None:
        """Validates title specification fields upon initialization.

        Raises:
            ValueError: If required strings are empty or numeric dimensions
                are non-positive.
        """
        if not self.name.strip():
            raise ValueError("TitleSpec.name must not be empty.")
        if not self.text.strip():
            raise ValueError("TitleSpec.text must not be empty.")
        if self.font_size <= 0 or self.font_weight <= 0:
            raise ValueError("TitleSpec font_size and font_weight must be positive.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("TitleSpec width and height must be positive.")
        _strip_hex_prefix(self.color_hex)

    @property
    def output_filename(self) -> str:
        """Returns the target SVG filename for this title specification."""
        return f"{self.name}.svg"

    def to_typing_svg_url(self) -> str:
        """Constructs the request URL for the typing SVG generator service.

        Returns:
            Fully encoded URL string for fetching the raw title SVG.
        """
        color_param = _strip_hex_prefix(self.color_hex)
        encoded_lines = urllib.parse.quote_plus(self.text)
        center_query = "&center=true" if self.is_centered else ""
        return (
            f"{_TYPING_SVG_BASE_URL}?font={urllib.parse.quote(self.font_family)}"
            f"&weight={self.font_weight}&size={self.font_size}"
            f"&color={color_param}{center_query}&vCenter=true"
            f"&width={self.width}&height={self.height}&lines={encoded_lines}"
        )


@dataclass(frozen=True)
class BadgeSpec:
    """Specification for a Catppuccin-styled toolkit or social badge SVG.

    Attributes:
        name: Human-readable badge label (e.g. 'VS Code', 'Antigravity').
        stroke_color: Hexadecimal border and icon accent color.
        logo_slug: Optional Simple Icons slug (e.g. 'python', 'blender').
        custom_logo_svg: Optional raw SVG markup for custom embedded icons.
        label_color: Background hex color for the shield body.
    """

    name: str
    stroke_color: str
    logo_slug: str | None = None
    custom_logo_svg: str | None = None
    label_color: str = CATPPUCCIN_BASE

    def __post_init__(self) -> None:
        """Validates badge specification fields.

        Raises:
            ValueError: If `name` is empty, colors are invalid, or both
                `logo_slug` and `custom_logo_svg` are missing or both set.
        """
        if not self.name.strip():
            raise ValueError("BadgeSpec.name must not be empty.")
        _strip_hex_prefix(self.stroke_color)
        _strip_hex_prefix(self.label_color)
        has_slug = bool(self.logo_slug and self.logo_slug.strip())
        has_custom = bool(self.custom_logo_svg and self.custom_logo_svg.strip())
        if has_slug == has_custom:
            raise ValueError(
                "Exactly one of `logo_slug` or `custom_logo_svg` must be provided."
            )

    @property
    def normalized_stroke_color(self) -> str:
        """Returns the stroke color guaranteed to start with '#'."""
        return _ensure_hex_prefix(self.stroke_color)

    @property
    def output_filename(self) -> str:
        """Returns the standardized badge filename (e.g. 'badge_VS_Code.svg')."""
        sanitized_name = self.name.strip().replace(" ", "_")
        return f"badge_{sanitized_name}.svg"

    def to_shields_url(self, encoded_custom_logo: str | None = None) -> str:
        """Builds the shields.io URL for fetching the base badge SVG.

        Args:
            encoded_custom_logo: URL-safe base64 string when using a custom
                SVG logo. Required if `custom_logo_svg` is set.

        Returns:
            The complete shields.io badge URL.

        Raises:
            ValueError: If `custom_logo_svg` is set but `encoded_custom_logo`
                was not supplied.
        """
        encoded_name = urllib.parse.quote(self.name)
        bg_hex = _strip_hex_prefix(self.label_color)
        accent_hex = _strip_hex_prefix(self.stroke_color)

        if self.custom_logo_svg is not None:
            if not encoded_custom_logo:
                raise ValueError(
                    "encoded_custom_logo is required when custom_logo_svg is used."
                )
            logo_param = f"data:image/svg%2Bxml;base64,{encoded_custom_logo}"
        else:
            assert self.logo_slug is not None
            logo_param = urllib.parse.quote(self.logo_slug)

        return (
            f"{_SHIELDS_BASE_URL}/{encoded_name}-{bg_hex}"
            f"?style=for-the-badge&logo={logo_param}&logoColor={accent_hex}"
        )


@dataclass(frozen=True)
class ToolkitCategorySpec:
    """Specification for a category row in the unified technical toolkit SVG.

    Attributes:
        title: Category heading (e.g. 'Programming & Ecosystem').
        badges: Non-empty tuple of `BadgeSpec` items displayed in the category row.
    """

    title: str
    badges: tuple[BadgeSpec, ...]

    def __post_init__(self) -> None:
        """Validates toolkit category title and badge tuple.

        Raises:
            ValueError: If `title` is blank or `badges` is empty.
        """
        if not self.title.strip():
            raise ValueError("ToolkitCategorySpec.title must not be empty.")
        if not self.badges:
            raise ValueError("ToolkitCategorySpec.badges must not be empty.")


@dataclass(frozen=True)
class LogoSpec:
    """Specification for an institution logo SVG with rounded corners.

    Attributes:
        name: Output asset stem name (e.g. 'iso_logo', 'az_logo').
        source_url: URL of the source PNG/image icon.
        background_color: Optional hex background fill color. When set, the
            image is inset by `padding` inside a colored rounded rectangle;
            when None, the image fills the full viewport with a rounded clipPath.
        size: Total SVG width and height in pixels.
        corner_radius: Rounded corner radius (`rx`/`ry`) in pixels.
        padding: Inset padding in pixels when `background_color` is provided.
    """

    name: str
    source_url: str
    background_color: str | None = None
    size: int = DEFAULT_LOGO_DIMENSION
    corner_radius: int = DEFAULT_CORNER_RADIUS
    padding: int = DEFAULT_LOGO_PADDING

    def __post_init__(self) -> None:
        """Validates logo specification parameters.

        Raises:
            ValueError: If `name` or `source_url` is empty, dimensions are
                invalid, or padding exceeds available size.
        """
        if not self.name.strip():
            raise ValueError("LogoSpec.name must not be empty.")
        if not self.source_url.strip():
            raise ValueError("LogoSpec.source_url must not be empty.")
        if self.size <= 0:
            raise ValueError("LogoSpec.size must be positive.")
        if self.corner_radius < 0:
            raise ValueError("LogoSpec.corner_radius must be non-negative.")
        if self.padding < 0 or self.padding * 2 >= self.size:
            raise ValueError(
                "LogoSpec.padding must be non-negative and less than half of size."
            )
        if self.background_color is not None:
            _strip_hex_prefix(self.background_color)

    @property
    def output_filename(self) -> str:
        """Returns the target SVG filename for this logo."""
        return f"{self.name}.svg"


@dataclass(frozen=True)
class ExperienceEntrySpec:
    """Specification for a single row in the experience timeline SVG.

    Attributes:
        institution: Organization or university name.
        role: Job title or academic role.
        department: Division, department, or research area.
        logo_stem: Stem name of the logo SVG in `assets/logos/` (e.g. 'iso_logo').
        background_color: Optional solid background fill hex for inset logos.
        is_current: Whether to render the 'CURRENT' pill badge beside the institution.
    """

    institution: str
    role: str
    department: str
    logo_stem: str
    background_color: str | None = None
    is_current: bool = False

    def __post_init__(self) -> None:
        """Validates experience entry fields upon initialization.

        Raises:
            ValueError: If any required text field is blank or `background_color`
                is an invalid empty hex string.
        """
        if not self.institution.strip():
            raise ValueError("ExperienceEntrySpec.institution must not be empty.")
        if not self.role.strip():
            raise ValueError("ExperienceEntrySpec.role must not be empty.")
        if not self.department.strip():
            raise ValueError("ExperienceEntrySpec.department must not be empty.")
        if not self.logo_stem.strip():
            raise ValueError("ExperienceEntrySpec.logo_stem must not be empty.")
        if self.background_color is not None:
            _strip_hex_prefix(self.background_color)

    @property
    def logo_filename(self) -> str:
        """Returns the source logo SVG filename (e.g. 'iso_logo.svg')."""
        return f"{self.logo_stem}.svg"

    @property
    def normalized_background_color(self) -> str | None:
        """Returns the background hex color prefixed with '#', or None."""
        if self.background_color is None:
            return None
        return _ensure_hex_prefix(self.background_color)


@dataclass(frozen=True)
class Publication:
    """Represents a scientific publication parsed from ORCID metadata.

    Attributes:
        title: Title of the publication.
        year: Four-digit publication year or 'N/A'.
        journal: Name of the journal or publication venue.
        doi_url: Resolved DOI URL or '#' fallback.
    """

    title: str
    year: str
    journal: str
    doi_url: str

    def __post_init__(self) -> None:
        """Validates that publication fields are non-empty strings.

        Raises:
            ValueError: If any field is blank.
        """
        if not self.title.strip():
            raise ValueError("Publication.title must not be empty.")
        if not self.year.strip():
            raise ValueError("Publication.year must not be empty.")
        if not self.journal.strip():
            raise ValueError("Publication.journal must not be empty.")
        if not self.doi_url.strip():
            raise ValueError("Publication.doi_url must not be empty.")

    def to_markdown(self) -> str:
        """Formats the publication into the README wide-format Markdown block.

        Returns:
            Formatted Markdown string with heading, year, journal, and link.
        """
        return (
            f"#### {self.title}\n"
            f"**{self.year}** • *{self.journal}* • [Full Paper]({self.doi_url})"
        )
