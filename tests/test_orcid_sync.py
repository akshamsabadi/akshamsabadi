"""Unit tests for ORCID synchronization and README formatting in `scripts.orcid_sync`."""

from io import BytesIO
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
import pytest

from scripts.models import Publication
from scripts.orcid_sync import (
    fetch_orcid_works,
    format_publications_markdown,
    parse_orcid_publications,
    sync_readme_with_orcid,
    update_readme_publications,
)


def _make_orcid_group(
    title: str = "Sample Paper",
    year: str | None = "2026",
    journal: str | None = "ACS Nano",
    doi: str | None = "10.1021/test",
) -> dict[str, Any]:
    """Builds a synthetic ORCID work group dictionary for testing."""
    summary: dict[str, Any] = {
        "title": {"title": {"value": title}},
    }
    if year is not None:
        summary["publication-date"] = {"year": {"value": year}}
    if journal is not None:
        summary["journal-title"] = {"value": journal} if journal else {}
    if doi is not None:
        summary["external-ids"] = {
            "external-id": [
                {"external-id-type": "issn", "external-id-value": "0000-0000"},
                {"external-id-type": "doi", "external-id-value": doi},
            ]
        }
    return {"work-summary": [summary]}


class TestParseOrcidPublications:
    """Tests for `parse_orcid_publications` across normal, edge, and failure cases."""

    def test_parses_up_to_max_items_in_order(self) -> None:
        """Verifies up to `max_items` works are parsed with complete metadata."""
        payload = {
            "group": [
                _make_orcid_group("Paper 1", "2026", "ACS Nano", "10.1021/p1"),
                _make_orcid_group("Paper 2", "2025", "JACS", "10.1021/p2"),
                _make_orcid_group("Paper 3", "2024", "Small", "10.1002/p3"),
            ]
        }
        pubs = parse_orcid_publications(payload, max_items=2)
        assert len(pubs) == 2
        assert pubs[0] == Publication(
            title="Paper 1",
            year="2026",
            journal="ACS Nano",
            doi_url="https://doi.org/10.1021/p1",
        )
        assert pubs[1].title == "Paper 2"

    def test_handles_missing_fields_and_malformed_entries_gracefully(self) -> None:
        """Verifies fallbacks for missing title, year, journal, DOI, and bad items."""
        payload: dict[str, Any] = {
            "group": [
                "not-a-dict",
                {"work-summary": []},
                {
                    "work-summary": [
                        {
                            "title": {},
                            "publication-date": None,
                            "journal-title": None,
                            "external-ids": {"external-id": ["bad-eid"]},
                        }
                    ]
                },
                {
                    "work-summary": [
                        {
                            "title": {"title": {"value": "Has Empty Journal Dict"}},
                            "journal-title": {"value": ""},
                        }
                    ]
                },
            ]
        }
        pubs = parse_orcid_publications(payload, max_items=4)
        assert len(pubs) == 2
        assert pubs[0] == Publication(
            title="Unknown Title",
            year="N/A",
            journal="Scientific Journal",
            doi_url="#",
        )
        assert pubs[1].journal == "Research Article"

    @pytest.mark.parametrize(
        ("payload", "max_items"),
        [
            ({}, 4),
            ({"group": "invalid-string"}, 4),
            ({"group": [_make_orcid_group()]}, 0),
        ],
    )
    def test_returns_empty_list_for_empty_or_zero_max_items(
        self, payload: dict[str, Any], max_items: int
    ) -> None:
        """Verifies empty payloads or `max_items=0` return an empty list."""
        assert parse_orcid_publications(payload, max_items=max_items) == []

    def test_negative_max_items_raises_value_error(self) -> None:
        """Verifies negative `max_items` raises `ValueError`."""
        with pytest.raises(ValueError, match="max_items must be non-negative"):
            parse_orcid_publications({}, max_items=-1)


class TestFormatAndUpdateReadmePublications:
    """Tests for `format_publications_markdown` and `update_readme_publications`."""

    def test_formats_multiple_publications_with_dividers(self) -> None:
        """Verifies publications are separated by `---` dividers except after the last."""
        pubs = [
            Publication("Paper A", "2026", "ACS Nano", "https://doi.org/10.1/a"),
            Publication("Paper B", "2025", "JACS", "https://doi.org/10.1/b"),
        ]
        md = format_publications_markdown(pubs)
        assert "---" in md
        assert md.count("---") == 1
        assert "#### Paper A" in md
        assert "#### Paper B" in md

    def test_formats_empty_publications_as_single_newline(self) -> None:
        """Verifies an empty sequence formats as a newline."""
        assert format_publications_markdown([]) == "\n"

    def test_replaces_section_between_gs_feed_markers(self) -> None:
        """Verifies content between `<!-- GS-FEED:START -->` and `END` is updated."""
        readme = (
            "# Title\n"
            "<!-- GS-FEED:START -->\nOld content\n<!-- GS-FEED:END -->\n"
            "Footer\n"
        )
        updated = update_readme_publications(readme, "\nNew Pubs\n\n")
        assert "Old content" not in updated
        assert "<!-- GS-FEED:START -->\n\nNew Pubs\n\n<!-- GS-FEED:END -->" in updated

    def test_returns_unchanged_readme_when_markers_absent(self) -> None:
        """Verifies `README.md` without feed markers is returned untouched."""
        readme = "# Profile README without feed markers\nSome content."
        assert update_readme_publications(readme, "\nNew Pubs\n") == readme


class TestFetchAndSyncOrcid:
    """Tests for `fetch_orcid_works` and `sync_readme_with_orcid`."""

    @patch("scripts.orcid_sync.urllib.request.urlopen")
    def test_fetch_orcid_works_returns_parsed_json(
        self, mock_urlopen: MagicMock
    ) -> None:
        """Verifies `fetch_orcid_works` sends JSON headers and parses dict payload."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = BytesIO(
            json.dumps({"group": []}).encode("utf-8")
        )
        mock_urlopen.return_value = mock_response

        result = fetch_orcid_works("0000-0001-8466-5621", timeout_seconds=5.0)
        assert result == {"group": []}

    @patch("scripts.orcid_sync.urllib.request.urlopen")
    def test_fetch_orcid_works_non_dict_json_raises_value_error(
        self, mock_urlopen: MagicMock
    ) -> None:
        """Verifies a JSON list response raises `ValueError`."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = BytesIO(b"[1, 2, 3]")
        mock_urlopen.return_value = mock_response

        with pytest.raises(ValueError, match="Expected JSON object"):
            fetch_orcid_works("0000-0001-8466-5621")

    @pytest.mark.parametrize(
        ("orcid_id", "timeout", "match_msg"),
        [
            ("   ", 10.0, "orcid_id must not be empty"),
            ("0000-0001", 0.0, "timeout_seconds must be positive"),
        ],
    )
    def test_fetch_orcid_works_invalid_args_raise_value_error(
        self, orcid_id: str, timeout: float, match_msg: str
    ) -> None:
        """Verifies invalid `orcid_id` or `timeout_seconds` raises `ValueError`."""
        with pytest.raises(ValueError, match=match_msg):
            fetch_orcid_works(orcid_id=orcid_id, timeout_seconds=timeout)

    @patch("scripts.orcid_sync.fetch_orcid_works")
    def test_sync_readme_with_orcid_updates_file_when_markers_present(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        """Verifies `sync_readme_with_orcid` writes updated publications and returns True."""
        mock_fetch.return_value = {
            "group": [_make_orcid_group("IsoDDE Report", "2026", "Tech Report", "10.1/iso")]
        }
        readme_file = tmp_path / "README.md"
        readme_file.write_text(
            "Header\n<!-- GS-FEED:START -->\n<!-- GS-FEED:END -->\n",
            encoding="utf-8",
        )

        changed = sync_readme_with_orcid(readme_file)
        assert changed is True
        assert "IsoDDE Report" in readme_file.read_text(encoding="utf-8")

    @patch("scripts.orcid_sync.fetch_orcid_works")
    def test_sync_readme_with_orcid_returns_false_when_unchanged(
        self, mock_fetch: MagicMock, tmp_path: Path
    ) -> None:
        """Verifies `sync_readme_with_orcid` returns False when no markers exist."""
        mock_fetch.return_value = {"group": []}
        readme_file = tmp_path / "README.md"
        readme_file.write_text("Header without markers\n", encoding="utf-8")

        assert sync_readme_with_orcid(readme_file) is False

    def test_sync_readme_missing_file_raises_file_not_found(
        self, tmp_path: Path
    ) -> None:
        """Verifies a missing `readme_path` raises `FileNotFoundError`."""
        with pytest.raises(FileNotFoundError):
            sync_readme_with_orcid(tmp_path / "nonexistent.md")
