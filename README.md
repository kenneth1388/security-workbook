# security-workbook

Deliberate Python practice for security engineering. Each brief is a single-purpose exercise — solved cold, debriefed afterwards, and shipped here as a finished artefact.

The shape of the workbook is tiered:

| Tier | Scope | Status      |
|---|---|-------------|
| **Tier 0 — Warm-ups** | Single-function reps; stdlib only; typed and tested | Done        |
| Tier 1 — Mini-tools | Single-purpose CLI tools, public repo each | In progress |
| Tier 2 — Portfolio | Pip-installable packages with CI and ≥80% coverage | Planned     |
| Tier 3 — AI-Augmented | MCP servers, agent evals, prompt-injection work | Planned     |

Earlier tiers build the reflexes — typed functions, tests cold, docstrings as habit — that make later tiers tractable.

## Layout

```
security-workbook/
├── Tier 0 - Warm-ups/
│   ├── T0.01-freq-score/         ← bigram language model for DGA detection
│   └── T0.02-find-iocs/          ← IOC extractor from text directories
└── README.md                     ← you are here
```

Each brief folder is self-contained: source, tests, README, and (where applicable) sample data.

## Tier 0 briefs

### [T0.01 — freq-score](./Tier%200%20-%20Warm-ups/T0.01-freq-score/)

Character-level bigram model for scoring how English-like a string is. Useful for detecting DGA-generated domains (real domains score high, randomly-generated ones score low). Trained on Moby Dick by default; trains from any plain-text corpus.

**Stack:** `torch`, stdlib. **Tests:** 6 assertions covering brief-mandated cases + plumbing sanity checks.

### [T0.02 — find-iocs](./Tier%200%20-%20Warm-ups/T0.02-find-iocs/)

Walk a directory of text files, extract unique IOCs by type (`ipv4`, `domain`, `url`, `sha256`, `md5`). One compiled regex with named alternatives; results returned as `dict[str, set[str]]`.

**Stack:** Stdlib only (`pathlib`, `re`). **Tests:** 8 assertions covering output shape, known IOCs, dedup, and one regex-tightness trap.

## Context

This repo is the public-facing deliverable side of a private study workbook. The briefs themselves (problem statements, constraints, hint policy) live in an Obsidian vault and aren't in scope for this repo — only the finished work appears here.

Practice runway for the **GIAC Python Coder (GPYC)** certification. Each brief is structured as deliberate practice — solve cold, debrief, ship — rather than passive review.

## Running anything in here

Each brief is independent — no shared deps. From inside a brief folder:

```bash
python <module>.py        # if the module has a __main__ block
python test_<module>.py   # to run the tests
```

T0.01 has a `requirements.txt` (needs PyTorch). T0.02 is stdlib only.
