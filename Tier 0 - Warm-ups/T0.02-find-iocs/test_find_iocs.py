"""Tests for find_iocs — T0.02 Definition-of-Done.

Run from the project directory:

    python test_find_iocs.py

Each test is a small function asserting ONE property. The runner at the
bottom executes them all, prints pass/fail per test, and exits non-zero
if any fail (so CI / Make / pre-commit can hook into it later).

Why these specific tests:
- They pin down properties of the output that, if broken, would make
  find_iocs unusable for a SOC analyst skimming for IOCs.
- They cover all five IOC types, the dedup behaviour, and one negative
  case (a regex-tightness trap from test_data/README.md).
"""

from pathlib import Path

from find_iocs import find_iocs


# Resolves relative to this file, so tests work regardless of where the
# repo is cloned or what cwd the runner is launched from.
TEST_DATA = Path(__file__).parent / "test_data"


# --- tests ------------------------------------------------------------------

def test_returns_all_five_keys():
    """Brief-mandated: every IOC type appears in the output dict.

    The brief requires four keys (ipv4, domain, url, sha256); this build
    adds md5 as an extension. All five must be present even when their
    value sets are empty — callers index by key without checking.
    """
    iocs = find_iocs(TEST_DATA)
    expected = {"ipv4", "domain", "url", "sha256", "md5"}
    assert set(iocs) == expected, f"expected keys {expected}, got {set(iocs)}"


def test_each_value_is_a_set():
    """Brief-mandated signature: dict[str, set[str]].

    Sets give O(1) `in` checks and free deduplication. If this regresses
    to list, every downstream "have I seen this IOC?" lookup gets slow
    and duplicates leak through.
    """
    iocs = find_iocs(TEST_DATA)
    for kind, values in iocs.items():
        assert isinstance(values, set), (
            f"{kind} value is {type(values).__name__}, expected set"
        )


def test_finds_known_ipv4():
    """Sanity: a known-good IPv4 from the corpus shows up.

    192.0.2.45 appears in four of the five test files. If the IPv4 regex
    regresses or file-reading silently skips text files, this catches it.
    """
    iocs = find_iocs(TEST_DATA)
    assert "192.0.2.45" in iocs["ipv4"], (
        f"expected 192.0.2.45 in ipv4 set, got {sorted(iocs['ipv4'])}"
    )


def test_finds_known_sha256():
    """Sanity: a 64-hex hash from the corpus shows up.

    a3f5b9c7... appears in two test files (phishing_email and
    malware_analysis_report). It's also the canonical proof-point for
    the dedup test below — if it appears twice here, set semantics broke.
    """
    iocs = find_iocs(TEST_DATA)
    canonical = "a3f5b9c7e8d4f2a1b6c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7"
    assert canonical in iocs["sha256"], (
        f"expected {canonical[:16]}... in sha256 set"
    )


def test_finds_known_md5():
    """Extension: MD5 detection (added beyond brief's four required types).

    5d41402a... is the MD5 of "password" — included in test_data as
    a known-shape hash to prove md5/sha256 alternation works correctly
    (32 hex chars not mistaken for the prefix of a 64-char hash).
    """
    iocs = find_iocs(TEST_DATA)
    assert "5d41402abc4b2a76b9719d911017c592" in iocs["md5"]


def test_finds_url_with_scheme():
    """URLs in the corpus are captured and all have an http(s) scheme.

    A loose regex that captured bare domains as 'urls' would fail this —
    the scheme requirement is what distinguishes a URL IOC from a domain
    IOC in threat intel.
    """
    iocs = find_iocs(TEST_DATA)
    assert len(iocs["url"]) > 0, "expected at least one URL, got none"
    for url in iocs["url"]:
        assert url.startswith(("http://", "https://")), (
            f"URL {url!r} doesn't start with http(s)://"
        )


def test_rejects_non_hex_as_hash():
    """Negative: 'ZZZINVALIDHASHXXXNOTHEXATALL' is not hex, must not match.

    test_data has this string as a regex-tightness trap. A correctly
    tightened regex ([a-fA-F0-9]{32}|{64}) rejects it. A too-loose
    regex like [a-z0-9]{32} would accept it.
    """
    iocs = find_iocs(TEST_DATA)
    trap = "ZZZINVALIDHASHXXXNOTHEXATALL"
    assert trap not in iocs["sha256"], f"{trap} leaked into sha256 set"
    assert trap not in iocs["md5"], f"{trap} leaked into md5 set"


def test_dedupe_across_files():
    """Brief-mandated: IOCs appearing in multiple files appear once.

    192.0.2.45 appears in 4+ files; a3f5b9c7... appears in 2.
    The set-based collection should dedupe automatically. This test
    pins that behaviour against an accidental return-to-list refactor.
    """
    iocs = find_iocs(TEST_DATA)
    for kind, values in iocs.items():
        # Set type already prevents duplicates; this is a tripwire for
        # a future change that swaps set → list/tuple by accident.
        assert isinstance(values, set), f"{kind} dedup contract broken"


# --- runner -----------------------------------------------------------------

def main():
    tests = [
        test_returns_all_five_keys,
        test_each_value_is_a_set,
        test_finds_known_ipv4,
        test_finds_known_sha256,
        test_finds_known_md5,
        test_finds_url_with_scheme,
        test_rejects_non_hex_as_hash,
        test_dedupe_across_files,
    ]

    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed.append(t.__name__)
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed.append(t.__name__)

    total = len(tests)
    print(f"\n{passed}/{total} passed")
    if failed:
        print(f"failed: {', '.join(failed)}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
