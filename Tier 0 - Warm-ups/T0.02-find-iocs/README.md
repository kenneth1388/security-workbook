# find_iocs

Extract indicators of compromise (IOCs) from text files in a directory tree. Scans recursively, deduplicates via set, and groups findings by IOC type — the kind of thing a SOC analyst would point at a folder of saved emails / log dumps / incident notes to pull out everything reportable in one pass.

Built as the deliverable for **Workbook T0.02 — `find_iocs`**.

## Supported IOC types

| Key | Pattern | Notes |
|---|---|---|
| `ipv4` | Strict 0–255 per octet (`25[0-5]\|2[0-4]\d\|1?\d?\d`) | Rejects `999.999.999.999` and `192.0.2` (incomplete) |
| `domain` | RFC 1035-style labels with `[A-Za-z]{2,}` TLD | Will match `function.method`-shaped strings; see limitations |
| `url` | `https?://` scheme + domain | Captures scheme + domain only; query strings and paths are dropped |
| `sha256` | `[a-fA-F0-9]{64}` (case-insensitive hex) | 64 chars exactly |
| `md5` | `[a-fA-F0-9]{32}` (case-insensitive hex) | 32 chars exactly — extension beyond the brief's four required types |

The five alternatives sit in one compiled regex, ordered most-specific-first so URLs win over bare domains and SHA-256 wins over MD5 when both could match at a position.

## Quick start

```python
from pathlib import Path
from find_iocs import find_iocs

iocs = find_iocs(Path("./test_data"))

print(f"unique IPv4s found: {len(iocs['ipv4'])}")
print(f"unique URLs found:  {len(iocs['url'])}")
print(f"unique hashes:      {len(iocs['sha256']) + len(iocs['md5'])}")

for ip in sorted(iocs["ipv4"]):
    print(ip)
```

Sample output from the included `test_data/`:

```
unique IPv4s found: 8
unique URLs found:  5
unique hashes:      4
10.0.0.42
10.0.0.5
192.0.2.45
198.51.100.12
198.51.100.99
203.0.113.42
203.0.113.7
203.0.113.99
```

## Signature

```python
def find_iocs(directory: Path) -> dict[str, set[str]]:
    ...
```

| Param | Type | Notes |
|---|---|---|
| `directory` | `pathlib.Path` | Root directory to scan. Must exist; subdirectories are walked recursively. |

**Returns:** dict with five keys (`ipv4`, `domain`, `url`, `sha256`, `md5`), each mapping to a `set[str]` of unique findings.

**Behaviour:**
- Walks `directory.rglob("*.txt")` — only `.txt` files are scanned. Other files in the tree (READMEs, binaries, configs) are ignored.
- Files that can't be decoded as UTF-8 are silently skipped (`UnicodeDecodeError` caught per brief).

## Tests

```bash
python test_find_iocs.py
```

Eight assertions covering:

- All five output keys present, all values are sets (signature contract)
- Specific known IOCs found in the corpus (IPv4, SHA-256, MD5)
- URL pattern includes the scheme (`http(s)://...`)
- Non-hex string like `ZZZINVALIDHASHXXXNOTHEXATALL` is rejected from hash sets
- Dedup across files (`192.0.2.45` appears in 4+ test files → one entry)

## Test data

Five files in `test_data/`:

- `phishing_email.txt` — exercises URL extraction + multi-type single document
- `firewall_log_excerpt.txt` — IP regex against structured `key=value` log fields
- `malware_analysis_report.txt` — SHA-256 vs MD5 length discrimination
- `mixed_artefacts.txt` — cross-file dedup + tight-vs-loose domain regex
- `README.md` — describes the corpus and intentional regex traps

All IPv4s are from RFC 5737 reserved blocks (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`) and all TLDs are RFC 2606 reserved (`.example`, `.test`, `.invalid`) — safe to commit, won't accidentally point at real systems.

## Known limitations

These are honest trade-offs of a "look-shaped-like-an-IOC" regex approach. A real IOC extractor would layer parsing libraries on top; for the brief, knowing what slips through matters more than catching everything.

- **TLD permissiveness.** `[A-Za-z]{2,}` matches any 2+ letter ending, so file-shaped strings like `stage2.bin`, `function.method`, `project.config` register as domains. A TLD allow-list (`com`, `org`, `net`, …) or library like `tldextract` would close this.
- **URLs lose paths.** `https://evil.example/payload?id=8472` is captured as `https://evil.example`. Fine for "did this URL appear?" — wrong for "what was the full target?"
- **Internationalized domains.** Patterns are ASCII-only. `bücher.de` and Punycode `xn--*` forms won't match.
- **Bare-domain false positives.** A version number like `1.2.3.4` matches the IPv4 pattern (it's structurally valid). Context would have to be inferred elsewhere.

## Dependencies

Standard library only: `pathlib`, `re`.

## Original brief

The problem statement lives in my private Workbook (Obsidian vault, not in this repo). Briefly: given a directory, walk it recursively, scan UTF-8 text files for IOCs, return `dict[str, set[str]]` grouped by type. Stdlib only.
