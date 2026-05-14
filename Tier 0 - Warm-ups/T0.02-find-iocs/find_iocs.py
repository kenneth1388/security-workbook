"""Extract indicators of compromise (IOCs) from text files in a directory tree.

Built as the deliverable for Workbook T0.02 — find_iocs.
"""

from pathlib import Path
import re


_IOC_RE = re.compile(
    r"(?P<url>https?://(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,})\b"
    r"|"
    r"\b(?P<ipv4>(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d))\b"
    r"|"
    r"\b(?P<domain>(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,})\b"
    r"|"
    r"\b(?P<sha256>[a-fA-F0-9]{64})\b"
    r"|"
    r"\b(?P<md5>[a-fA-F0-9]{32})\b"
)


def find_iocs(directory: Path) -> dict[str, set[str]]:
    """Scan all text files under `directory` and return unique IOCs by type.

    Walks `directory` recursively, reads each file as UTF-8 text, and matches
    the content against patterns for IPv4 addresses, domains, URLs, MD5
    hashes, and SHA-256 hashes. Files that cannot be decoded as UTF-8 (e.g.
    binary blobs) are silently skipped per the brief.

    Order of regex alternation matters: URL is tried before domain so URLs
    don't get caught by the bare-domain pattern; SHA-256 (64 hex) before MD5
    (32 hex) so the longer hash wins when both could match at a position.

    Args:
        directory: Root directory to scan. May contain subdirectories or be
            empty; non-existent paths raise `FileNotFoundError`.

    Returns:
        Dict with five keys (`ipv4`, `domain`, `url`, `sha256`, `md5`), each
        mapping to a set of unique strings found across all readable files.
        Keys with no hits remain present as empty sets.

    Raises:
        FileNotFoundError: If `directory` does not exist.

    Example:
        >>> from pathlib import Path
        >>> iocs = find_iocs(Path("./test_data"))
        >>> "192.0.2.45" in iocs["ipv4"]
        True
    """
    iocs: dict[str, set[str]] = {
        "ipv4": set(),
        "domain": set(),
        "url": set(),
        "sha256": set(),
        "md5": set(),
    }

    for path in directory.rglob("*.txt"):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        for match in _IOC_RE.finditer(text):
            iocs[match.lastgroup].add(match.group())

    return iocs
