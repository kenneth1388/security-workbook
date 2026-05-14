import json, re, torch
from pathlib import Path


def make_bigram_model(file_path, verbose=True):
    doc_string = Path(file_path).read_text().lower()
    words = re.findall(r'[a-z]+', doc_string)

    chars = sorted(set(''.join(words)))
    stoi = {s: i + 1 for i, s in enumerate(chars)}
    stoi['.'] = 0
    itos = {i: s for s, i in stoi.items()}

    # 1. COUNT bigrams
    N = torch.zeros((len(stoi), len(stoi)), dtype=torch.int32)
    for w in words:
        chs = ['.'] + list(w) + ['.']
        for ch1, ch2 in zip(chs, chs[1:]):
            N[stoi[ch1], stoi[ch2]] += 1

    # 2. BUILD probabilities (with +1 Laplace smoothing)
    P = (N + 1).float()
    P /= P.sum(1, keepdim=True)

    # 3. SCORE the corpus under the model
    log_likelihood = 0.0
    av = 0
    for w in words:
        chs = ['.'] + list(w) + ['.']
        for ch1, ch2 in zip(chs, chs[1:]):
            prob = P[stoi[ch1], stoi[ch2]]
            log_likelihood += torch.log(prob)
            av += 1

    nll = -log_likelihood
    avg_nll = nll / av

    if verbose:
        print(f"loaded {len(doc_string):,} chars")
        print(f"extracted {len(words):,} words; first 10: {words[:10]}")
        print(f"vocab: {len(chars)} unique chars: {chars}")
        print(f"N total bigram count: {N.sum().item():,}")
        print(f"N top-left 6×6:\n{N[:6, :6]}")
        print(f"P top-left 6×6 (rows sum to 1):\n{P[:6, :6]}")
        print(f"P row sums: {P.sum(1)}")
        print(f"bigrams scored:           {av:,}")
        print(f"log likelihood:           {log_likelihood.item():.4f}")
        print(f"negative log likelihood:  {nll.item():.4f}")
        print(f"avg NLL (loss):           {avg_nll.item():.4f}   (lower = better)")

    return doc_string, words, N, P, stoi, itos


def save_bigram_model(out_path, P, stoi):
    payload = {
        "stoi": stoi,  # str → int, already JSON-safe
        "P": P.tolist(),  # tensor → nested list
    }
    Path(out_path).write_text(json.dumps(payload, indent=2))
    print(f"saved → {out_path}  ({Path(out_path).stat().st_size:,}bytes)")


def load_bigram_model(in_path):
    payload = json.loads(Path(in_path).read_text())
    stoi = payload["stoi"]
    P = torch.tensor(payload["P"])
    itos = {i: s for s, i in stoi.items()}  # rebuild inverse
    return P, stoi, itos


def score(word, P, stoi, verbose=True):
    """Score a word's likelihood under a bigram model."""
    if not word:  # empty string → exactly 0.0
        return 0.0
    cleaned = re.sub(r'[^a-z]', '', word.lower())
    if not cleaned:  # had content but zero letters → no bigrams scoreable
        return float('-inf')  # per the brief

    chs = ['.'] + list(cleaned) + ['.']
    log_likelihood = 0.0
    n = 0
    for ch1, ch2 in zip(chs, chs[1:]):
        p = P[stoi[ch1], stoi[ch2]]
        log_likelihood += torch.log(p)
        n += 1
        if verbose:
            print(f"{ch1}{ch2}: prob={p.item():.4f} logprob={torch.log(p).item():+.4f}")

    nll = -log_likelihood
    avg_nll = nll / n
    perplexity = torch.exp(avg_nll)

    result = {
        "input": word,
        "cleaned": cleaned,
        "n_bigrams": n,
        "log_likelihood": log_likelihood.item(),
        "nll": nll.item(),
        "avg_nll": avg_nll.item(),
        "perplexity": perplexity.item(),
    }
    if verbose:
        print(f"\nlog_likelihood : {result['log_likelihood']:+.4f}")
        print(f"NLL            : {result['nll']:.4f}")
        print(f"avg NLL (loss) : {result['avg_nll']:.4f}")
        print(f"perplexity     : {result['perplexity']:.4f}   (lower = more plausible)")
    return result


def freq_score(text, model_path):
    """Brief-compliant entry point. Returns a single float (the log-probability sum).

    Higher (closer to 0) = more English-like. Lower = more random.
    Empty string → 0.0.  String with no letters → -inf.

    Also prints the avg_nll for readability (small positive number, SANS-style:
    lower = more plausible). Print is a side effect; return value is what
    callers/tests rely on.
    """
    P, stoi, _ = load_bigram_model(model_path)
    result = score(text, P, stoi, verbose=False)
    if isinstance(result, dict):
        print(f"avg_nll: {result['avg_nll']:.4f}")
        return result["log_likelihood"]
    return result   # pass-through for 0.0 (empty) and -inf (no letters)