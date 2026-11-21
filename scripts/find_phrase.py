# /// script
# requires-python = ">=3.10"
# ///
"""Find when a phrase was spoken in an aligned transcript.

Fuzzy-matches the phrase against the word list (case and punctuation ignored)
and prints the start/end time of each match, best first. Use it to turn the
agent's chosen quote ("fix the printer cable") into a frame anchor time.

Usage:
  uv run find_phrase.py transcript.aligned.json "fix the printer cable" [--top 3]
"""
from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def norm(s: str) -> str:
    return re.sub(r"[^\w']+", "", s.lower())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript", type=Path)
    ap.add_argument("phrase")
    ap.add_argument("--top", type=int, default=3)
    args = ap.parse_args()

    words = json.loads(args.transcript.read_text())["words"]
    toks = [norm(w["w"]) for w in words]
    target = [t for t in (norm(x) for x in args.phrase.split()) if t]
    n = len(target)
    if not n:
        raise SystemExit("empty phrase")

    hits = []
    for i in range(0, max(1, len(toks) - n + 1)):
        window = toks[i:i + n]
        r = SequenceMatcher(None, " ".join(window), " ".join(target)).ratio()
        hits.append((r, i))
    hits.sort(reverse=True)

    out, used = [], set()
    for r, i in hits:
        if any(abs(i - j) < n for j in used):
            continue
        used.add(i)
        span = words[i:i + n]
        out.append({"score": round(r, 3), "start": span[0]["start"], "end": span[-1]["end"],
                    "text": " ".join(w["w"] for w in span)})
        if len(out) >= args.top:
            break
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
