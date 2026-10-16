"""Asset generation commands and canonical specifications for SVG titles, badges, logos, timeline, and toolkit."""

from collections.abc import Sequence
from pathlib import Path
from typing import Final
import urllib.parse
import urllib.request

from scripts.models import (
    BadgeSpec,
    CATPPUCCIN_BLUE,
    CATPPUCCIN_GREEN,
    CATPPUCCIN_MAUVE,
    CATPPUCCIN_PEACH,
    CATPPUCCIN_TEAL,
    CATPPUCCIN_TEXT,
    CATPPUCCIN_YELLOW,
    ExperienceEntrySpec,
    LogoSpec,
    TitleSpec,
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

DEFAULT_HTTP_TIMEOUT_SECONDS: Final[float] = 15.0
EXPERIENCE_TIMELINE_FILENAME: Final[str] = "experience_timeline.svg"
TECHNICAL_TOOLKIT_FILENAME: Final[str] = "technical_toolkit.svg"
_DEFAULT_USER_AGENT: Final[str] = "Mozilla/5.0"
_TYPING_SVG_FONT_ENDPOINT: Final[str] = "https://readme-typing-svg.demolab.com"
_TIMELINE_FONT_WEIGHTS: Final[tuple[int, ...]] = (400, 500, 600)

LINKEDIN_ICON_SVG: Final[str] = (
    '<svg xmlns="http://www.w3.org/2000/svg" fill="#89b4fa" viewBox="0 0 16 16">'
    '<path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708'
    "c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248"
    "V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52"
    "-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 "
    "8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216"
    ".662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0"
    '-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z"/>'
    "</svg>"
)

ANTIGRAVITY_ICON_SVG: Final[str] = (
    '<svg fill="#94e2d5" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
    "<title>Antigravity</title>"
    '<path d="M21.751 22.607c1.34 1.005 3.35.335 1.508-1.508C17.73 15.74 18.904 1 '
    "12.037 1 5.17 1 6.342 15.74.815 21.1c-2.01 2.009.167 2.511 1.507 1.506 "
    '5.192-3.517 4.857-9.714 9.715-9.714 4.857 0 4.522 6.197 9.714 9.715z"/>'
    "</svg>"
)

VSCODE_ICON_SVG: Final[str] = (
    '<svg fill="#89b4fa" role="img" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
    "<title>VS Code</title>"
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M70.9119 99.3171C72.4869 99.9307 '
    "74.2828 99.8914 75.8725 99.1264L96.4608 89.2197C98.6242 88.1787 100 85.9892 100 "
    "83.5872V16.4133C100 14.0113 98.6243 11.8218 96.4609 10.7808L75.8725 0.873756C73.7862 "
    "-0.130129 71.3446 0.11576 69.5135 1.44695C69.252 1.63711 69.0028 1.84943 68.769 "
    "2.08341L29.3551 38.0415L12.1872 25.0096C10.589 23.7965 8.35363 23.8959 6.86933 "
    "25.2461L1.36303 30.2549C-0.452552 31.9064 -0.454633 34.7627 1.35853 36.417L16.2471 "
    "50.0001L1.35853 63.5832C-0.454633 65.2374 -0.452552 68.0938 1.36303 69.7453L6.86933 "
    "74.7541C8.35363 76.1043 10.589 76.2037 12.1872 74.9905L29.3551 61.9587L68.769 "
    "97.9167C69.3925 98.5406 70.1246 99.0104 70.9119 99.3171ZM75.0152 27.2989L45.1091 "
    '50.0001L75.0152 72.7012V27.2989Z"/>'
    "</svg>"
)

DEFAULT_TITLE_SPECS: Final[tuple[TitleSpec, ...]] = (
    TitleSpec(
        name="title_main",
        text="André Kütahya Shamsabadi",
        font_size=40,
        font_weight=600,
        color_hex=CATPPUCCIN_MAUVE,
        width=800,
        height=60,
        is_centered=True,
    ),
    TitleSpec(
        name="title_sub",
        text="Chemical Biologist • AI/ML • Data Visualisation",
        font_size=20,
        font_weight=500,
        color_hex=CATPPUCCIN_BLUE,
        width=800,
        height=40,
        is_centered=True,
    ),
    TitleSpec(
        name="title_about",
        text="✦ About Me",
        font_size=22,
        font_weight=600,
        color_hex=CATPPUCCIN_MAUVE,
        width=300,
        height=35,
    ),
    TitleSpec(
        name="title_exp",
        text="✦ Experience",
        font_size=22,
        font_weight=600,
        color_hex=CATPPUCCIN_MAUVE,
        width=300,
        height=35,
    ),
    TitleSpec(
        name="title_tech",
        text="✦ Technical Toolkit",
        font_size=22,
        font_weight=600,
        color_hex=CATPPUCCIN_MAUVE,
        width=400,
        height=35,
    ),
    TitleSpec(
        name="title_graphs",
        text="✦ Aesthetic Data Vis. & Graphics",
        font_size=22,
        font_weight=600,
        color_hex=CATPPUCCIN_MAUVE,
        width=800,
        height=35,
    ),
)

_OBSIDIAN_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="Obsidian",
    stroke_color=CATPPUCCIN_MAUVE,
    logo_slug="obsidian",
)
_ANTIGRAVITY_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="Antigravity",
    stroke_color=CATPPUCCIN_TEAL,
    custom_logo_svg=ANTIGRAVITY_ICON_SVG,
)
_VSCODE_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="VS Code",
    stroke_color=CATPPUCCIN_BLUE,
    custom_logo_svg=VSCODE_ICON_SVG,
)
_GOOGLE_COLAB_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="Google Colab",
    stroke_color=CATPPUCCIN_YELLOW,
    logo_slug="googlecolab",
)
_OVERLEAF_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="Overleaf",
    stroke_color=CATPPUCCIN_GREEN,
    logo_slug="overleaf",
)
_PYMOL_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="PyMOL",
    stroke_color=CATPPUCCIN_BLUE,
    logo_slug="moleculer",
)
_INKSCAPE_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="Inkscape",
    stroke_color=CATPPUCCIN_TEXT,
    logo_slug="inkscape",
)
_BLENDER_BADGE: Final[BadgeSpec] = BadgeSpec(
    name="Blender",
    stroke_color=CATPPUCCIN_PEACH,
    logo_slug="blender",
)

DEFAULT_BADGE_SPECS: Final[tuple[BadgeSpec, ...]] = (
    BadgeSpec(
        name="LinkedIn",
        stroke_color=CATPPUCCIN_BLUE,
        custom_logo_svg=LINKEDIN_ICON_SVG,
    ),
    BadgeSpec(
        name="Google Scholar",
        stroke_color=CATPPUCCIN_BLUE,
        logo_slug="google-scholar",
    ),
    BadgeSpec(
        name="ORCID",
        stroke_color=CATPPUCCIN_GREEN,
        logo_slug="orcid",
    ),
    _OBSIDIAN_BADGE,
    _ANTIGRAVITY_BADGE,
    _VSCODE_BADGE,
    _GOOGLE_COLAB_BADGE,
    _OVERLEAF_BADGE,
    _PYMOL_BADGE,
    _INKSCAPE_BADGE,
    _BLENDER_BADGE,
)

DEFAULT_TOOLKIT_CATEGORIES: Final[tuple[ToolkitCategorySpec, ...]] = (
    ToolkitCategorySpec(
        title="Programming & Ecosystem",
        badges=(
            _OBSIDIAN_BADGE,
            _ANTIGRAVITY_BADGE,
            _VSCODE_BADGE,
            _GOOGLE_COLAB_BADGE,
            _OVERLEAF_BADGE,
        ),
    ),
    ToolkitCategorySpec(
        title="Design & Visualisation",
        badges=(
            _PYMOL_BADGE,
            _INKSCAPE_BADGE,
            _BLENDER_BADGE,
        ),
    ),
)

DEFAULT_LOGO_SPECS: Final[tuple[LogoSpec, ...]] = (
    LogoSpec(
        name="iso_logo",
        source_url="https://avatars.githubusercontent.com/u/96115000?v=4",
    ),
    LogoSpec(
        name="az_logo",
        source_url="https://www.google.com/s2/favicons?domain=astrazeneca.com&sz=128",
        background_color="#8A0051",
    ),
    LogoSpec(
        name="kavli_logo",
        source_url="https://www.google.com/s2/favicons?domain=kavlinano.ox.ac.uk&sz=128",
        background_color="#FFFFFF",
    ),
    LogoSpec(
        name="imperial_logo",
        source_url="https://www.google.com/s2/favicons?domain=imperial.ac.uk&sz=128",
    ),
    LogoSpec(
        name="ucl_logo",
        source_url="https://www.google.com/s2/favicons?domain=ucl.ac.uk&sz=128",
    ),
)

DEFAULT_EXPERIENCE_SPECS: Final[tuple[ExperienceEntrySpec, ...]] = (
    ExperienceEntrySpec(
        institution="Isomorphic Labs",
        role="Research Investigator",
        department="Exploratory Sciences",
        logo_stem="iso_logo",
        is_current=True,
    ),
    ExperienceEntrySpec(
        institution="AstraZeneca",
        role="Senior Scientist",
        department="Oncology Targeted Delivery",
        logo_stem="az_logo",
        background_color="#8A0051",
    ),
    ExperienceEntrySpec(
        institution="Kavli Institute for Nanoscience Discovery, University of Oxford",
        role="Research Associate / Academic Visitor",
        department="Biomedical Engineering",
        logo_stem="kavli_logo",
        background_color="#FFFFFF",
    ),
    ExperienceEntrySpec(
        institution="Imperial College London",
        role="Postdoctoral Research Associate",
        department="Chemical Biology & Materials",
        logo_stem="imperial_logo",
    ),
    ExperienceEntrySpec(
        institution="UCL",
        role="PhD Researcher",
        department="Synthetic Organic Chemistry",
        logo_stem="ucl_logo",
    ),
)


def _fetch_bytes(
    url: str, timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS
) -> bytes:
    """Downloads raw bytes from `url` with a standard User-Agent header."""
    if not url.strip():
        raise ValueError("URL must not be empty.")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive.")

    request = urllib.request.Request(
        url, headers={"User-Agent": _DEFAULT_USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        data: bytes = response.read()
    return data


def _fetch_text(
    url: str, timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS
) -> str:
    """Downloads UTF-8 decoded text from `url`."""
    return _fetch_bytes(url, timeout_seconds=timeout_seconds).decode("utf-8")


def generate_title_svg(
    spec: TitleSpec,
    output_dir: Path,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> Path:
    """Fetches a typing SVG banner, converts it to static text, and writes it.

    Args:
        spec: The `TitleSpec` describing the title banner.
        output_dir: Directory where the resulting `.svg` file will be saved.
        timeout_seconds: Network timeout in seconds.

    Returns:
        Path to the written SVG file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_svg = _fetch_text(spec.to_typing_svg_url(), timeout_seconds=timeout_seconds)
    static_svg = convert_typing_svg_to_static(raw_svg)
    output_path = output_dir / spec.output_filename
    output_path.write_text(static_svg, encoding="utf-8")
    return output_path


def _fetch_badge_poppins_font_url(
    spec: BadgeSpec,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> str:
    """Fetches a subsetted Poppins 600 truetype data URL for a single badge pill."""
    encoded_lines = urllib.parse.quote_plus(spec.name.upper())
    url = (
        f"{_TYPING_SVG_FONT_ENDPOINT}?font=Poppins&weight=600"
        f"&size=15&color=cba6f7&lines={encoded_lines}"
    )
    raw_svg = _fetch_text(url, timeout_seconds=timeout_seconds)
    return extract_font_url_from_typing_svg(raw_svg)


def generate_badge_svg(
    spec: BadgeSpec,
    output_dir: Path,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> Path:
    """Builds a Catppuccin & Poppins solid-filled pill badge SVG and writes it.

    Args:
        spec: The `BadgeSpec` describing the badge.
        output_dir: Directory where the badge `.svg` will be written.
        timeout_seconds: Network timeout in seconds.

    Returns:
        Path to the written badge SVG file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / spec.output_filename

    if spec.custom_logo_svg is not None:
        encoded_logo = colorize_and_encode_logo_svg(
            spec.custom_logo_svg, fill_color=spec.normalized_stroke_color
        )
        icon_b64 = encoded_logo.replace("%2B", "+")
    elif output_path.exists():
        icon_b64 = extract_embedded_svg_base64(
            output_path.read_text(encoding="utf-8")
        )
    else:
        raw_shield_svg = _fetch_text(
            spec.to_shields_url(), timeout_seconds=timeout_seconds
        )
        icon_b64 = extract_embedded_svg_base64(raw_shield_svg)

    font_url = _fetch_badge_poppins_font_url(spec, timeout_seconds=timeout_seconds)
    pill_svg = build_badge_pill_svg(spec, icon_b64=icon_b64, font_url=font_url)
    output_path.write_text(pill_svg, encoding="utf-8")
    return output_path


def generate_logo_svg(
    spec: LogoSpec,
    output_dir: Path,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> Path:
    """Downloads an institution icon, wraps it in a rounded SVG, and writes it.

    Args:
        spec: The `LogoSpec` describing the institution logo.
        output_dir: Directory where the logo `.svg` will be saved.
        timeout_seconds: Network timeout in seconds.

    Returns:
        Path to the written logo SVG file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    image_bytes = _fetch_bytes(spec.source_url, timeout_seconds=timeout_seconds)
    logo_svg = build_institution_logo_svg(image_bytes, spec)
    output_path = output_dir / spec.output_filename
    output_path.write_text(logo_svg, encoding="utf-8")
    return output_path


def _fetch_poppins_font_urls(
    entries: Sequence[ExperienceEntrySpec],
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> dict[int, str]:
    """Fetches subsetted Poppins truetype base64 URLs for all timeline text."""
    combined_glyphs = "CURRENT · " + " ".join(
        f"{entry.institution} {entry.role} {entry.department}" for entry in entries
    )
    encoded_lines = urllib.parse.quote_plus(combined_glyphs)
    font_urls: dict[int, str] = {}
    for weight in _TIMELINE_FONT_WEIGHTS:
        url = (
            f"{_TYPING_SVG_FONT_ENDPOINT}?font=Poppins&weight={weight}"
            f"&size=15&color=cba6f7&lines={encoded_lines}"
        )
        raw_svg = _fetch_text(url, timeout_seconds=timeout_seconds)
        font_urls[weight] = extract_font_url_from_typing_svg(raw_svg)
    return font_urls


def generate_experience_svg(
    assets_root: Path,
    entries: Sequence[ExperienceEntrySpec] = DEFAULT_EXPERIENCE_SPECS,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> Path:
    """Generates `assets/experience_timeline.svg` from local logos and Poppins fonts.

    Args:
        assets_root: Root `assets/` directory containing `logos/*.svg`.
        entries: Sequence of `ExperienceEntrySpec` rows to render.
        timeout_seconds: Network timeout in seconds for font subsetting requests.

    Returns:
        Path to the generated `experience_timeline.svg` file.
    """
    assets_root.mkdir(parents=True, exist_ok=True)
    logos_dir = assets_root / "logos"
    logo_base64_map: dict[str, str] = {}

    for entry in entries:
        logo_path = logos_dir / entry.logo_filename
        if not logo_path.exists():
            raise FileNotFoundError(f"Required logo SVG not found: {logo_path}")
        logo_svg_text = logo_path.read_text(encoding="utf-8")
        logo_base64_map[entry.logo_stem] = extract_embedded_png_base64(logo_svg_text)

    font_urls = _fetch_poppins_font_urls(entries, timeout_seconds=timeout_seconds)
    timeline_svg = build_experience_timeline_svg(
        entries=entries,
        logo_base64_map=logo_base64_map,
        font_urls=font_urls,
    )
    output_path = assets_root / EXPERIENCE_TIMELINE_FILENAME
    output_path.write_text(timeline_svg, encoding="utf-8")
    return output_path


def _fetch_toolkit_poppins_font_url(
    categories: Sequence[ToolkitCategorySpec],
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> str:
    """Fetches a subsetted Poppins 600 truetype data URL for toolkit headers and pills."""
    glyph_parts: list[str] = []
    for category in categories:
        glyph_parts.append(category.title)
        for badge in category.badges:
            glyph_parts.append(badge.name.upper())
    encoded_lines = urllib.parse.quote_plus(" ".join(glyph_parts))
    url = (
        f"{_TYPING_SVG_FONT_ENDPOINT}?font=Poppins&weight=600"
        f"&size=15&color=cba6f7&lines={encoded_lines}"
    )
    raw_svg = _fetch_text(url, timeout_seconds=timeout_seconds)
    return extract_font_url_from_typing_svg(raw_svg)


def generate_technical_toolkit_svg(
    assets_root: Path,
    categories: Sequence[ToolkitCategorySpec] = DEFAULT_TOOLKIT_CATEGORIES,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> Path:
    """Generates `assets/technical_toolkit.svg` from badge icons and Poppins 600 font.

    Args:
        assets_root: Root `assets/` directory containing `badges/*.svg`.
        categories: Sequence of `ToolkitCategorySpec` rows to render.
        timeout_seconds: Network timeout in seconds for font subsetting request.

    Returns:
        Path to the generated `technical_toolkit.svg` file.

    Raises:
        FileNotFoundError: If a required badge SVG in `assets/badges/` is missing.
    """
    assets_root.mkdir(parents=True, exist_ok=True)
    badges_dir = assets_root / "badges"
    icon_base64_map: dict[str, str] = {}

    for category in categories:
        for badge in category.badges:
            if badge.custom_logo_svg is not None:
                encoded = colorize_and_encode_logo_svg(
                    badge.custom_logo_svg, fill_color=badge.normalized_stroke_color
                )
                icon_base64_map[badge.name] = encoded.replace("%2B", "+")
                continue

            badge_path = badges_dir / badge.output_filename
            if not badge_path.exists():
                raise FileNotFoundError(
                    f"Required badge SVG not found: {badge_path}"
                )
            badge_svg_text = badge_path.read_text(encoding="utf-8")
            icon_base64_map[badge.name] = extract_embedded_svg_base64(badge_svg_text)

    font_url = _fetch_toolkit_poppins_font_url(
        categories, timeout_seconds=timeout_seconds
    )
    toolkit_svg = build_technical_toolkit_svg(
        categories=categories,
        icon_base64_map=icon_base64_map,
        font_url=font_url,
    )
    output_path = assets_root / TECHNICAL_TOOLKIT_FILENAME
    output_path.write_text(toolkit_svg, encoding="utf-8")
    return output_path


def generate_all_assets(
    assets_root: Path,
    titles: Sequence[TitleSpec] = DEFAULT_TITLE_SPECS,
    badges: Sequence[BadgeSpec] = DEFAULT_BADGE_SPECS,
    logos: Sequence[LogoSpec] = DEFAULT_LOGO_SPECS,
    experiences: Sequence[ExperienceEntrySpec] = DEFAULT_EXPERIENCE_SPECS,
    toolkit_categories: Sequence[ToolkitCategorySpec] = DEFAULT_TOOLKIT_CATEGORIES,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> list[Path]:
    """Generates all configured title, badge, logo, experience, and toolkit SVG assets.

    Args:
        assets_root: Root `assets/` directory path.
        titles: Sequence of title specifications to generate.
        badges: Sequence of badge specifications to generate.
        logos: Sequence of institution logo specifications to generate.
        experiences: Sequence of experience timeline entries to generate.
        toolkit_categories: Sequence of toolkit categories to generate.
        timeout_seconds: Network timeout in seconds per request.

    Returns:
        List of paths to all generated SVG files.
    """
    generated_paths: list[Path] = []
    badges_dir = assets_root / "badges"
    logos_dir = assets_root / "logos"

    for title_spec in titles:
        generated_paths.append(
            generate_title_svg(title_spec, assets_root, timeout_seconds=timeout_seconds)
        )
    for badge_spec in badges:
        generated_paths.append(
            generate_badge_svg(badge_spec, badges_dir, timeout_seconds=timeout_seconds)
        )
    for logo_spec in logos:
        generated_paths.append(
            generate_logo_svg(logo_spec, logos_dir, timeout_seconds=timeout_seconds)
        )
    if experiences:
        generated_paths.append(
            generate_experience_svg(
                assets_root, entries=experiences, timeout_seconds=timeout_seconds
            )
        )
    if toolkit_categories:
        generated_paths.append(
            generate_technical_toolkit_svg(
                assets_root,
                categories=toolkit_categories,
                timeout_seconds=timeout_seconds,
            )
        )

    return generated_paths
