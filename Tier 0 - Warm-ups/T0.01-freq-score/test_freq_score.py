"""Tests for freq_score / bigram_maker — T0.01 Definition-of-Done.

Run from the project directory:

    python test_freq_score.py

Each test is a small function that asserts ONE property. The script at the
bottom runs them all, prints pass/fail per test, and exits non-zero if any
fail (so CI / Make / pre-commit can hook into it later).

Why these specific tests:
- They each pin down a property of the model that, if broken, would make
  freq_score useless for DGA detection (its actual job).
- Together they cover the brief's three required cases plus two
  "the plumbing didn't break" sanity checks.
"""

import math
from pathlib import Path

from bigram_maker import (
    make_bigram_model,
    save_bigram_model,
    load_bigram_model,
    freq_score,
    score,
)

# --- configuration ----------------------------------------------------------
# Adjust these two paths if your corpus or model file lives elsewhere.
CORPUS = Path("/Users/kennethokiria/Downloads/734e32aab75a4f7df06538dac9f00a5a-8da85d5acabc53fd66af17c252701b0ba395e6c1/moby.txt")
MODEL  = Path("/Users/kennethokiria/Documents/moby_bigram.json")


def setup():
    """Build the model file once if it's missing. Tests assume it exists."""
    if not MODEL.exists():
        print(f"model not found at {MODEL} — building from {CORPUS} ...")
        _, _, _, P, stoi, _ = make_bigram_model(CORPUS, verbose=False)
        save_bigram_model(MODEL, P, stoi)


# --- tests ------------------------------------------------------------------

def test_empty_string_returns_zero():
    """Brief-mandated: freq_score("") == 0.0 exactly.

    Why this matters: callers may pass empty input (e.g. a domain-name field
    that wasn't filled in). We want a sentinel value that's clearly "no
    information" rather than a misleading score.
    """
    result = freq_score("", MODEL)
    assert result == 0.0, f"empty string should return exactly 0.0, got {result!r}"


def test_english_scores_higher_than_gibberish():
    """Brief-mandated: real English words beat random-looking strings.

    This is the model's whole job. If this assertion ever flips, the model
    is broken (or you trained it on the wrong corpus). A failure here
    invalidates everything downstream that uses freq_score for detection.
    """
    english   = freq_score("google",     MODEL)
    gibberish = freq_score("xqv8z3jklm", MODEL)
    assert english > gibberish, (
        f"english ({english:.2f}) should score higher (less negative) "
        f"than gibberish ({gibberish:.2f})"
    )


def test_no_letters_returns_minus_infinity():
    """Brief-mandated: input with no scoreable bigrams → -inf.

    Different from the empty case: here the input had content, but after
    stripping non-letters there's nothing left to score. The convention
    is -inf because that's the limit of log(prob) as prob → 0 — i.e.
    "infinitely implausible."
    """
    result = freq_score("12345!@#", MODEL)
    assert result == -math.inf, f"no-letters input should return -inf, got {result!r}"


def test_save_load_round_trip_preserves_scores():
    """Sanity: saving and reloading the model gives identical scores.

    Why: the JSON serialisation is the only thing standing between the
    in-memory model and a future caller. If save/load drifts (e.g. float
    precision loss, key reordering), every cached model becomes unreliable.
    Catch it here, once, instead of debugging a mystery later.
    """
    # score with the on-disk model
    a = freq_score("whale", MODEL)

    # rebuild from corpus, save fresh, reload, score again
    _, _, _, P, stoi, _ = make_bigram_model(CORPUS, verbose=False)
    save_bigram_model(MODEL, P, stoi)
    b = freq_score("whale", MODEL)

    assert a == b, f"round-trip should preserve scores: {a} vs {b}"


def test_freq_score_returns_float():
    """Brief-mandated signature: -> float.

    The richer score() function returns a dict for inspection, but the
    brief contract for freq_score is a single float. This test pins the
    public API so we don't accidentally widen the return type later.
    """
    result = freq_score("whale", MODEL)
    assert isinstance(result, float), f"expected float, got {type(result).__name__}"


def test_deterministic():
    """Bonus: scoring the same input twice gives the same answer.

    A bigram model is a pure function — same inputs, same outputs, every
    time. If this fails, something stateful crept in (a global counter,
    a randomised tie-break, etc.) and needs hunting down.
    """
    a = freq_score("whale", MODEL)
    b = freq_score("whale", MODEL)
    assert a == b, f"non-deterministic: got {a} then {b}"


# --- runner -----------------------------------------------------------------

def main():
    setup()

    tests = [
        test_empty_string_returns_zero,
        test_english_scores_higher_than_gibberish,
        test_no_letters_returns_minus_infinity,
        test_save_load_round_trip_preserves_scores,
        test_freq_score_returns_float,
        test_deterministic,
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
