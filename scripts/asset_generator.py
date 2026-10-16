"""Asset generation commands and canonical specifications for SVG titles, badges, and logos."""

from collections.abc import Sequence
from pathlib import Path
from typing import Final
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
    LogoSpec,
    TitleSpec,
)
from scripts.svg_transforms import (
    build_institution_logo_svg,
    colorize_and_encode_logo_svg,
    convert_typing_svg_to_static,
    inject_badge_border,
)

DEFAULT_HTTP_TIMEOUT_SECONDS: Final[float] = 15.0
_DEFAULT_USER_AGENT: Final[str] = "Mozilla/5.0"

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
    '<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#89b4fa">'
    "<title>Visual Studio Code</title>"
    '<path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.291L6.94 12.2a.746.746 '
    "0 0 1-.5.234l-5.466 2.06a.746.746 0 0 0-.294.697l5.426 10.55c.105.204.318.334"
    ".547.334h.01a.614.614 0 0 0 .444-.226l9.605-11.706a1.494 1.494 0 0 0-1.705-.29"
    'l-4.94 2.377A1.5 1.5 0 0 0 24 14.88V1.5a1.5 1.5 0 0 0-.85-1.413z"/>'
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
    BadgeSpec(
        name="Obsidian",
        stroke_color=CATPPUCCIN_MAUVE,
        logo_slug="obsidian",
    ),
    BadgeSpec(
        name="Antigravity",
        stroke_color=CATPPUCCIN_TEAL,
        custom_logo_svg=ANTIGRAVITY_ICON_SVG,
    ),
    BadgeSpec(
        name="VS Code",
        stroke_color=CATPPUCCIN_BLUE,
        custom_logo_svg=VSCODE_ICON_SVG,
    ),
    BadgeSpec(
        name="Google Colab",
        stroke_color=CATPPUCCIN_YELLOW,
        logo_slug="googlecolab",
    ),
    BadgeSpec(
        name="Overleaf",
        stroke_color=CATPPUCCIN_GREEN,
        logo_slug="overleaf",
    ),
    BadgeSpec(
        name="PyMOL",
        stroke_color=CATPPUCCIN_BLUE,
        logo_slug="moleculer",
    ),
    BadgeSpec(
        name="Inkscape",
        stroke_color=CATPPUCCIN_TEXT,
        logo_slug="inkscape",
    ),
    BadgeSpec(
        name="Blender",
        stroke_color=CATPPUCCIN_PEACH,
        logo_slug="blender",
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


def generate_badge_svg(
    spec: BadgeSpec,
    output_dir: Path,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> Path:
    """Fetches a shields.io badge SVG, injects a rounded border, and writes it.

    Args:
        spec: The `BadgeSpec` describing the badge.
        output_dir: Directory where the badge `.svg` will be written.
        timeout_seconds: Network timeout in seconds.

    Returns:
        Path to the written badge SVG file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    encoded_logo: str | None = None
    if spec.custom_logo_svg is not None:
        encoded_logo = colorize_and_encode_logo_svg(
            spec.custom_logo_svg, fill_color=spec.normalized_stroke_color
        )

    shield_url = spec.to_shields_url(encoded_custom_logo=encoded_logo)
    raw_shield_svg = _fetch_text(shield_url, timeout_seconds=timeout_seconds)
    bordered_svg = inject_badge_border(
        raw_shield_svg, stroke_color=spec.normalized_stroke_color
    )

    output_path = output_dir / spec.output_filename
    output_path.write_text(bordered_svg, encoding="utf-8")
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


def generate_all_assets(
    assets_root: Path,
    titles: Sequence[TitleSpec] = DEFAULT_TITLE_SPECS,
    badges: Sequence[BadgeSpec] = DEFAULT_BADGE_SPECS,
    logos: Sequence[LogoSpec] = DEFAULT_LOGO_SPECS,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> list[Path]:
    """Generates all configured title, badge, and logo SVG assets under `assets_root`.

    Args:
        assets_root: Root `assets/` directory path.
        titles: Sequence of title specifications to generate.
        badges: Sequence of badge specifications to generate.
        logos: Sequence of institution logo specifications to generate.
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

    return generated_paths
