"""ORCID public API synchronization and README publication feed formatting."""

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import re
from typing import Any, Final
import urllib.request

from scripts.models import Publication

DEFAULT_ORCID_ID: Final[str] = "0000-0001-8466-5621"
DEFAULT_MAX_PUBLICATIONS: Final[int] = 4
DEFAULT_TIMEOUT_SECONDS: Final[float] = 10.0

_ORCID_API_BASE_URL: Final[str] = "https://pub.orcid.org/v3.0"
_FALLBACK_TITLE: Final[str] = "Unknown Title"
_FALLBACK_YEAR: Final[str] = "N/A"
_FALLBACK_JOURNAL_WHEN_MISSING: Final[str] = "Scientific Journal"
_FALLBACK_JOURNAL_WHEN_EMPTY: Final[str] = "Research Article"
_FALLBACK_DOI_URL: Final[str] = "#"
_DOI_BASE_URL: Final[str] = "https://doi.org/"

_FEED_SECTION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(<!-- GS-FEED:START -->).*?(<!-- GS-FEED:END -->)", flags=re.DOTALL
)


def _extract_nested_value(
    mapping: Mapping[str, Any], *keys: str, default: str
) -> str:
    """Safely traverses nested dictionaries to extract a non-empty string value."""
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return default
        current = current.get(key)
    if isinstance(current, str) and current.strip():
        return current.strip()
    return default


def _extract_journal_title(summary: Mapping[str, Any]) -> str:
    """Extracts the journal name from an ORCID work summary dictionary."""
    journal_node = summary.get("journal-title")
    if not isinstance(journal_node, Mapping) or not journal_node:
        return _FALLBACK_JOURNAL_WHEN_MISSING
    value = journal_node.get("value")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return _FALLBACK_JOURNAL_WHEN_EMPTY


def _extract_doi_url(summary: Mapping[str, Any]) -> str:
    """Extracts the first DOI link from an ORCID work summary's external IDs."""
    external_ids_container = summary.get("external-ids")
    if not isinstance(external_ids_container, Mapping):
        return _FALLBACK_DOI_URL
    external_ids = external_ids_container.get("external-id")
    if not isinstance(external_ids, Sequence) or isinstance(external_ids, (str, bytes)):
        return _FALLBACK_DOI_URL

    for external_id in external_ids:
        if not isinstance(external_id, Mapping):
            continue
        id_type = external_id.get("external-id-type")
        id_value = external_id.get("external-id-value")
        if (
            isinstance(id_type, str)
            and id_type.lower() == "doi"
            and isinstance(id_value, str)
            and id_value.strip()
        ):
            return f"{_DOI_BASE_URL}{id_value.strip()}"
    return _FALLBACK_DOI_URL


def _parse_single_work(work_group: Mapping[str, Any]) -> Publication | None:
    """Parses the primary work summary from a single ORCID group entry."""
    summaries = work_group.get("work-summary")
    if not isinstance(summaries, Sequence) or isinstance(summaries, (str, bytes)):
        return None
    if not summaries or not isinstance(summaries[0], Mapping):
        return None

    summary = summaries[0]
    title = _extract_nested_value(
        summary, "title", "title", "value", default=_FALLBACK_TITLE
    )
    year = _extract_nested_value(
        summary, "publication-date", "year", "value", default=_FALLBACK_YEAR
    )
    journal = _extract_journal_title(summary)
    doi_url = _extract_doi_url(summary)
    return Publication(title=title, year=year, journal=journal, doi_url=doi_url)


def parse_orcid_publications(
    payload: Mapping[str, Any], max_items: int = DEFAULT_MAX_PUBLICATIONS
) -> list[Publication]:
    """Parses up to `max_items` publications from an ORCID `/works` JSON payload.

    Args:
        payload: Deserialized JSON dictionary from the ORCID works endpoint.
        max_items: Maximum number of publications to return. Defaults to 4.

    Returns:
        Ordered list of parsed `Publication` instances.

    Raises:
        ValueError: If `max_items` is negative.
    """
    if max_items < 0:
        raise ValueError("max_items must be non-negative.")
    if max_items == 0:
        return []

    raw_groups = payload.get("group")
    if not isinstance(raw_groups, Sequence) or isinstance(raw_groups, (str, bytes)):
        return []

    publications: list[Publication] = []
    for group in raw_groups:
        if len(publications) >= max_items:
            break
        if not isinstance(group, Mapping):
            continue
        parsed = _parse_single_work(group)
        if parsed is not None:
            publications.append(parsed)

    return publications


def format_publications_markdown(publications: Sequence[Publication]) -> str:
    """Formats a sequence of publications into a divider-separated Markdown block.

    Args:
        publications: Sequence of `Publication` objects to render.

    Returns:
        Formatted Markdown block suitable for insertion between feed markers.
    """
    if not publications:
        return "\n"

    rendered_blocks = [pub.to_markdown() for pub in publications]
    joined = "\n\n---\n\n".join(rendered_blocks)
    return f"\n{joined}\n\n"


def update_readme_publications(
    readme_text: str, publications_markdown: str
) -> str:
    """Replaces content between `<!-- GS-FEED:START -->` and `<!-- GS-FEED:END -->`.

    If the markers are not present in `readme_text`, returns `readme_text`
    unchanged so profile READMEs without an inline feed section remain intact.

    Args:
        readme_text: Existing contents of `README.md`.
        publications_markdown: Formatted Markdown string of publications.

    Returns:
        Updated `README.md` text with the refreshed publication feed.
    """
    if not _FEED_SECTION_PATTERN.search(readme_text):
        return readme_text

    return _FEED_SECTION_PATTERN.sub(
        lambda match: f"{match.group(1)}\n{publications_markdown}{match.group(2)}",
        readme_text,
    )


def fetch_orcid_works(
    orcid_id: str = DEFAULT_ORCID_ID,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Fetches the JSON works summary for the given ORCID identifier.

    Args:
        orcid_id: ORCID identifier (e.g. '0000-0001-8466-5621').
        timeout_seconds: HTTP request timeout in seconds.

    Returns:
        Parsed JSON response dictionary from ORCID.

    Raises:
        ValueError: If `orcid_id` is empty or `timeout_seconds` is non-positive,
            or if the returned payload is not a JSON object.
    """
    if not orcid_id.strip():
        raise ValueError("orcid_id must not be empty.")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive.")

    url = f"{_ORCID_API_BASE_URL}/{orcid_id.strip()}/works"
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Expected JSON object from ORCID works endpoint.")
    return payload


def sync_readme_with_orcid(
    readme_path: Path,
    orcid_id: str = DEFAULT_ORCID_ID,
    max_items: int = DEFAULT_MAX_PUBLICATIONS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> bool:
    """Fetches latest ORCID publications and updates `readme_path` if markers exist.

    Args:
        readme_path: Filesystem path to `README.md`.
        orcid_id: ORCID identifier to query.
        max_items: Maximum number of recent publications to include.
        timeout_seconds: Network timeout in seconds.

    Returns:
        True if `readme_path` was modified and written, False if no changes
        were needed or if feed markers were absent.

    Raises:
        FileNotFoundError: If `readme_path` does not exist.
    """
    if not readme_path.exists():
        raise FileNotFoundError(f"README file not found: {readme_path}")

    original_text = readme_path.read_text(encoding="utf-8")
    payload = fetch_orcid_works(orcid_id=orcid_id, timeout_seconds=timeout_seconds)
    publications = parse_orcid_publications(payload, max_items=max_items)
    markdown_block = format_publications_markdown(publications)
    updated_text = update_readme_publications(original_text, markdown_block)

    if updated_text == original_text:
        return False

    readme_path.write_text(updated_text, encoding="utf-8")
    return True


if __name__ == "__main__":  # pragma: no cover
    default_readme = Path(__file__).resolve().parent.parent / "README.md"
    was_updated = sync_readme_with_orcid(default_readme)
    status = "Updated" if was_updated else "No changes needed for"
    print(f"{status} {default_readme.name}.")
