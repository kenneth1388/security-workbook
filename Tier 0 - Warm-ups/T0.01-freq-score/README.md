# bigram_maker

A character-level bigram language model for scoring how plausibly English a string is. Trains from any plain-text corpus, persists to JSON, and scores arbitrary strings — useful for DGA detection (real domain names score high, randomly-generated ones score low).

Built as the deliverable for **Workbook T0.01 — `freq_score`**.

## What's in the model file

When you call `save_bigram_model`, you get a JSON file with two top-level keys:

```json
{
  "stoi": {".": 0, "a": 1, "b": 2, "c": 3, ..., "z": 26},
  "P":    [[0.0001, 0.1094, ...], [0.0717, 0.0001, ...], ..., 27 rows total]
}
```

| Key | Type | Meaning |
|---|---|---|
| `stoi` | `dict[str, int]` | "String to int" — maps each character to its row/column index. `.` is the word-boundary marker (index 0); `a–z` are 1–26. |
| `P` | `list[list[float]]` | 27×27 row-normalised probability matrix. `P[i][j]` is the probability that the next character has index `j`, given the current character has index `i`. **Each row sums to 1.0.** |

### Conventions

- **Boundary character `.`** marks word start and end. A word like `cat` is scored as the bigram sequence `.c, ca, at, t.` — five characters, four bigrams.
- **+1 Laplace smoothing** is applied during training before normalisation. Every cell of `P` is therefore nonzero, even for bigrams the corpus never contained. This stops `log(0) = -inf` from blowing up scores on unseen pairs.
- **Lowercase only.** Inputs are lowercased; non-letters are stripped before scoring (so `google.com` is scored as `googlecom`).

## Quick start

```python
from bigram_maker import make_bigram_model, save_bigram_model, freq_score

# 1. Train from a text corpus
_, _, _, P, stoi, _ = make_bigram_model("moby.txt")

# 2. Persist to disk
save_bigram_model("moby_bigram.json", P, stoi)

# 3. Score arbitrary strings (loads the JSON each call)
freq_score("whale",      "moby_bigram.json")    # → -10.64  (English-like)
freq_score("xqv8z3jklm", "moby_bigram.json")    # → -71.17  (gibberish)
freq_score("",           "moby_bigram.json")    # →   0.0   (empty sentinel)
```

## Score interpretation

`freq_score` returns the **log-likelihood sum** of the input's bigrams under the model.

| Return value | Reading |
|---|---|
| Closer to 0 (less negative) | More English-like |
| Very negative | Random / gibberish |
| Exactly `0.0` | Empty string (sentinel — no information) |
| `-inf` | Input had no scoreable letters (e.g. `"123!@#"`) |

Alongside the return value, `freq_score` prints **`avg_nll`** — a small positive number where **lower = more plausible**, matching the SANS convention. The two values are different views of the same score:

- `log_likelihood` is the raw sum (the brief's contract; signed, can be very negative)
- `avg_nll` is `-log_likelihood / n_bigrams` (small positive, normalised by length)

## Functions

Detailed docstrings are inline in `bigram_maker.py`. At a glance:

| Function | Returns |
|---|---|
| `make_bigram_model(file_path, verbose=True)` | `(doc_string, words, N, P, stoi, itos)` — full training artefacts |
| `save_bigram_model(out_path, P, stoi)` | Nothing (writes JSON to disk) |
| `load_bigram_model(in_path)` | `(P, stoi, itos)` |
| `score(word, P, stoi, verbose=True)` | A dict with `log_likelihood`, `nll`, `avg_nll`, `perplexity`, etc. — for development inspection |
| `freq_score(text, model_path)` | A single float (log-likelihood). Brief-compliant entry point. |

## Tests

```bash
python test_freq_score.py
```

Six assertions covering the three brief-mandated cases (empty input, English-vs-gibberish ordering, no-letters input) plus three plumbing sanity checks (save/load round-trip stability, return-type stability, determinism).

## Dependencies

- `torch` — count tensor and probability matrix
- Standard library only otherwise: `json`, `re`, `pathlib`, `math`

## Reference model

The reference `moby_bigram.json` in this project was trained on Moby Dick (Project Gutenberg plain text, 1.24M characters, 222k words after lowercase + letter-only extraction). Training-set average NLL: **2.30** (uniform 27-character baseline ≈ 3.30, so the model is meaningfully better than random).
