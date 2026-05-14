# test_data — sample inputs for `find_iocs`

Four synthetic text files plus this README. Each file mimics a realistic source of IOCs that a SOC analyst might receive (phishing email, firewall log, malware analysis writeup, mixed clipboard). Together they exercise:

- All four IOC types the brief asks for: `ipv4`, `domain`, `sha256`, `url`
- Near-misses that must be **rejected** by a correct regex
- Duplicates that must be **deduplicated** across files

## What each file is for

| File | Mimics | Stress-tests |
|---|---|---|
| `phishing_email.txt` | Saved phishing email with headers + body | URL extraction, multi-IOC-type single document |
| `firewall_log_excerpt.txt` | Firewall/IDS log with structured `key=value` fields | IP regex against partial / malformed addresses |
| `malware_analysis_report.txt` | Researcher writeup with hashes and network IOCs | SHA256 vs MD5 vs short hex (length matters) |
| `mixed_artefacts.txt` | Clipboard / scratchpad — the "everything else" pile | Cross-file dedup + tight-vs-loose domain regex |

## Things your function should catch

Read each file once and you'll see roughly:

- A handful of unique IPv4 IOCs (some appearing in multiple files)
- A handful of unique domains and URLs
- Two SHA256 hashes (one of which is shared between two files)

The exact counts are deliberately not listed here — deriving them from the test files is part of writing your test assertions. (If you list them in this README, you've effectively answered the question for yourself.)

## Things your function should NOT catch

Inspect each file's footnote comments to see the booby traps. Examples:

- **`192.0.2`** — only three octets, not a full IPv4
- **`999.999.999.999`** — four octets but each out of range (decide what your regex does with this)
- **`5d41402abc4b2a76b9719d911017c592`** — 32-char MD5 hash, not 64-char SHA256
- **`1234567890abcdef`** — 16-char hex, way too short
- **`ZZZINVALIDHASHXXXNOTHEXATALL`** — not hex at all
- **`function.method`**, **`project.config`** — look domain-ish but are programming syntax
- **`1.2.3.4`** — looks IP-ish but is a version number in context

A tight regex rejects all of these. A loose regex lets some through. Part of T0.02 is finding the right tightness.

## Bonus: testing the binary-file skip path

The brief says non-UTF-8 files should be **skipped** (catch `UnicodeDecodeError`, move on). To exercise that path:

```bash
# from inside test_data/
cp /any/random.pdf ./binary_sample.bin
# or generate a random binary file
head -c 1024 /dev/urandom > random.bin
```

Drop any binary file (PDF, image, `.pyc`, random bytes) into `test_data/` and your function should walk past it without crashing.

## Why these are safe to commit

- All IPv4 addresses are from RFC 5737 reserved blocks (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` — TEST-NET-1/2/3)
- All TLDs are RFC 2606 reserved (`.example`, `.test`, `.invalid`)
- Hashes are randomly generated hex strings, not derived from real malware
- No actual malicious infrastructure is referenced anywhere

These reserved blocks exist precisely so course material and documentation can use realistic-looking IOCs without accidentally pointing at real systems.
