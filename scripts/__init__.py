"""Profile asset generation and ORCID publication synchronization package."""

from typing import Final

from scripts.asset_generator import (
    DEFAULT_BADGE_SPECS,
    DEFAULT_EXPERIENCE_SPECS,
    DEFAULT_LOGO_SPECS,
    DEFAULT_TITLE_SPECS,
    DEFAULT_TOOLKIT_CATEGORIES,
    EXPERIENCE_TIMELINE_FILENAME,
    TECHNICAL_TOOLKIT_FILENAME,
    generate_all_assets,
    generate_badge_svg,
    generate_experience_svg,
    generate_logo_svg,
    generate_technical_toolkit_svg,
    generate_title_svg,
)
from scripts.models import (
    BadgeSpec,
    ExperienceEntrySpec,
    LogoSpec,
    Publication,
    TitleSpec,
    ToolkitCategorySpec,
)
from scripts.orcid_sync import (
    DEFAULT_ORCID_ID,
    fetch_orcid_works,
    format_publications_markdown,
    parse_orcid_publications,
    sync_readme_with_orcid,
    update_readme_publications,
)
from scripts.svg_transforms import (
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

__version__: Final[str] = "0.9.2"

__all__: Final[list[str]] = [
    "__version__",
    "BadgeSpec",
    "DEFAULT_BADGE_SPECS",
    "DEFAULT_EXPERIENCE_SPECS",
    "DEFAULT_LOGO_SPECS",
    "DEFAULT_ORCID_ID",
    "DEFAULT_TITLE_SPECS",
    "DEFAULT_TOOLKIT_CATEGORIES",
    "EXPERIENCE_TIMELINE_FILENAME",
    "ExperienceEntrySpec",
    "LogoSpec",
    "Publication",
    "TECHNICAL_TOOLKIT_FILENAME",
    "TitleSpec",
    "ToolkitCategorySpec",
    "build_experience_timeline_svg",
    "build_institution_logo_svg",
    "build_technical_toolkit_svg",
    "colorize_and_encode_logo_svg",
    "convert_typing_svg_to_static",
    "extract_embedded_png_base64",
    "extract_embedded_svg_base64",
    "extract_font_url_from_typing_svg",
    "fetch_orcid_works",
    "format_publications_markdown",
    "generate_all_assets",
    "generate_badge_svg",
    "generate_experience_svg",
    "generate_logo_svg",
    "generate_technical_toolkit_svg",
    "generate_title_svg",
    "inject_badge_border",
    "parse_orcid_publications",
    "sync_readme_with_orcid",
    "update_readme_publications",
]
