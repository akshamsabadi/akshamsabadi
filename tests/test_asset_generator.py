"""Unit tests for asset generation commands and canonical specs in `scripts.asset_generator`."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scripts.asset_generator import (
    ANTIGRAVITY_ICON_SVG,
    DEFAULT_BADGE_SPECS,
    DEFAULT_LOGO_SPECS,
    DEFAULT_TITLE_SPECS,
    _fetch_bytes,
    generate_all_assets,
    generate_badge_svg,
    generate_logo_svg,
    generate_title_svg,
)
from scripts.models import BadgeSpec, CATPPUCCIN_MAUVE, LogoSpec, TitleSpec


class TestCanonicalSpecs:
    """Tests verifying the integrity of default title, badge, and logo specifications."""

    def test_default_badge_specs_include_antigravity_and_exclude_legacy_tools(
        self,
    ) -> None:
        """Verifies `DEFAULT_BADGE_SPECS` contains active badges and omits removed ones."""
        badge_names = {spec.name for spec in DEFAULT_BADGE_SPECS}
        assert len(DEFAULT_BADGE_SPECS) == 11
        assert "Antigravity" in badge_names
        assert "VS Code" in badge_names
        assert "Google Colab" in badge_names
        assert "Python" not in badge_names
        assert "LaTeX" not in badge_names
        assert "D3.js" not in badge_names
        assert "Jupyter" not in badge_names

    def test_default_title_and_logo_specs_are_non_empty(self) -> None:
        """Verifies default title and institution logo specs are populated."""
        assert len(DEFAULT_TITLE_SPECS) == 6
        assert len(DEFAULT_LOGO_SPECS) == 5


class TestAssetGenerationCommands:
    """Tests for `generate_title_svg`, `generate_badge_svg`, `generate_logo_svg`, and `generate_all_assets`."""

    @patch("scripts.asset_generator._fetch_text")
    def test_generate_title_svg_writes_static_svg_file(
        self, mock_fetch_text: MagicMock, tmp_path: Path
    ) -> None:
        """Verifies `generate_title_svg` transforms and saves the title SVG."""
        mock_fetch_text.return_value = (
            "<svg><path id='path0'></path>"
            "<text fill='#cba6f7'><textPath>✦ About Me</textPath></text></svg>"
        )
        spec = TitleSpec(
            name="title_about",
            text="✦ About Me",
            font_size=22,
            font_weight=600,
            color_hex=CATPPUCCIN_MAUVE,
            width=300,
            height=35,
        )
        out_path = generate_title_svg(spec, tmp_path / "assets")
        assert out_path.exists()
        assert out_path.name == "title_about.svg"
        content = out_path.read_text(encoding="utf-8")
        assert '<text y="50%"' in content
        assert "path0" not in content

    @patch("scripts.asset_generator._fetch_text")
    def test_generate_badge_svg_handles_custom_svg_logo_and_injects_border(
        self, mock_fetch_text: MagicMock, tmp_path: Path
    ) -> None:
        """Verifies `generate_badge_svg` encodes custom SVG logos and adds a border."""
        mock_fetch_text.return_value = (
            '<svg><rect width="120" height="28" fill="#1e1e2e"/></svg>'
        )
        spec = BadgeSpec(
            name="Antigravity",
            stroke_color=CATPPUCCIN_MAUVE,
            custom_logo_svg=ANTIGRAVITY_ICON_SVG,
        )
        out_path = generate_badge_svg(spec, tmp_path / "badges")
        assert out_path.exists()
        assert out_path.name == "badge_Antigravity.svg"
        assert 'stroke="#cba6f7"' in out_path.read_text(encoding="utf-8")

    @patch("scripts.asset_generator._fetch_bytes")
    def test_generate_logo_svg_writes_wrapped_institution_logo(
        self, mock_fetch_bytes: MagicMock, tmp_path: Path
    ) -> None:
        """Verifies `generate_logo_svg` embeds fetched image bytes into an SVG."""
        mock_fetch_bytes.return_value = b"\x89PNG\r\n\x1a\n"
        spec = LogoSpec(
            name="iso_logo",
            source_url="https://example.com/iso.png",
        )
        out_path = generate_logo_svg(spec, tmp_path / "logos")
        assert out_path.exists()
        assert out_path.name == "iso_logo.svg"
        assert "data:image/png;base64," in out_path.read_text(encoding="utf-8")

    @patch("scripts.asset_generator._fetch_bytes")
    @patch("scripts.asset_generator._fetch_text")
    def test_generate_all_assets_creates_expected_directory_structure(
        self,
        mock_fetch_text: MagicMock,
        mock_fetch_bytes: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Verifies `generate_all_assets` writes titles, badges, and logos to subdirectories."""
        mock_fetch_text.return_value = (
            '<svg><rect width="100" height="28" fill="#1e1e2e"/>'
            '<text fill="#cba6f7">T</text></svg>'
        )
        mock_fetch_bytes.return_value = b"png-bytes"

        paths = generate_all_assets(
            assets_root=tmp_path,
            titles=(DEFAULT_TITLE_SPECS[0],),
            badges=(DEFAULT_BADGE_SPECS[0],),
            logos=(DEFAULT_LOGO_SPECS[0],),
        )
        assert len(paths) == 3
        assert (tmp_path / "title_main.svg").exists()
        assert (tmp_path / "badges" / "badge_LinkedIn.svg").exists()
        assert (tmp_path / "logos" / "iso_logo.svg").exists()

    @patch("scripts.asset_generator.urllib.request.urlopen")
    def test_fetch_bytes_reads_response_stream(
        self, mock_urlopen: MagicMock
    ) -> None:
        """Verifies `_fetch_bytes` returns bytes from `urlopen`."""
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = BytesIO(b"svg-bytes")
        mock_urlopen.return_value = mock_resp
        assert _fetch_bytes("https://example.com/test.svg", timeout_seconds=5.0) == b"svg-bytes"

    @pytest.mark.parametrize(
        ("url", "timeout", "match_msg"),
        [
            ("   ", 5.0, "URL must not be empty"),
            ("https://example.com", 0.0, "timeout_seconds must be positive"),
        ],
    )
    def test_fetch_bytes_invalid_arguments_raise_value_error(
        self, url: str, timeout: float, match_msg: str
    ) -> None:
        """Verifies `_fetch_bytes` validates URL and timeout parameters."""
        with pytest.raises(ValueError, match=match_msg):
            _fetch_bytes(url, timeout_seconds=timeout)
