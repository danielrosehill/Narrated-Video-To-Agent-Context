# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31"]
# ///
"""Word-aligned transcription of a narrated video.

Writes one normalised JSON file whatever the backend:

    {"backend": "...", "model": "...", "language": "en", "duration": 42.1,
     "words":    [{"w": "printer", "start": 12.34, "end": 12.71}, ...],
     "segments": [{"start": 10.0, "end": 14.2, "text": "..."}, ...]}

Backends:
  openai    POST /v1/audio/transcriptions, whisper-1, word + segment timestamps.
            Env OPENAI_API_KEY. OPENAI_BASE_URL overrides the host (any
            OpenAI-compatible server that supports timestamp_granularities).
  deepgram  POST /v1/listen, nova-3, word timestamps + utterances. Env DEEPGRAM_API_KEY.
  whisperx  Local WhisperX (forced alignment). Needs a GPU machine, and
            `uv tool install whisperx` or an env with whisperx installed. Heavy.

Usage:
  uv run transcribe.py VIDEO --out transcript.aligned.json [--backend openai] [--language en]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests


def extract_audio(video: Path, workdir: Path) -> Path:
    # 16 kHz mono MP3 keeps uploads small (OpenAI's limit is 25 MB, about 50 min at this rate).
    audio = workdir / "audio.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1",
         "-ar", "16000", "-b:a", "64k", str(audio)],
        check=True,
    )
    return audio


def probe_duration(video: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def run_openai(audio: Path, language: str | None, model: str) -> dict:
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY is not set")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    data = [("model", model), ("response_format", "verbose_json"),
            ("timestamp_granularities[]", "word"), ("timestamp_granularities[]", "segment")]
    if language:
        data.append(("language", language))
    with audio.open("rb") as fh:
        r = requests.post(f"{base}/audio/transcriptions", headers={"Authorization": f"Bearer {key}"},
                          data=data, files={"file": (audio.name, fh, "audio/mpeg")}, timeout=600)
    r.raise_for_status()
    j = r.json()
    return {
        "language": j.get("language"),
        "words": [{"w": w["word"], "start": w["start"], "end": w["end"]} for w in j.get("words", [])],
        "segments": [{"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                     for s in j.get("segments", [])],
    }


def run_deepgram(audio: Path, language: str | None, model: str) -> dict:
    key = os.environ.get("DEEPGRAM_API_KEY") or sys.exit("DEEPGRAM_API_KEY is not set")
    params = {"model": model, "smart_format": "true", "punctuate": "true", "utterances": "true"}
    if language:
        params["language"] = language
    else:
        params["detect_language"] = "true"
    r = requests.post("https://api.deepgram.com/v1/listen", params=params,
                      headers={"Authorization": f"Token {key}", "Content-Type": "audio/mpeg"},
                      data=audio.read_bytes(), timeout=600)
    r.raise_for_status()
    j = r.json()
    alt = j["results"]["channels"][0]["alternatives"][0]
    words = [{"w": w.get("punctuated_word", w["word"]), "start": w["start"], "end": w["end"]}
             for w in alt.get("words", [])]
    segs = [{"start": u["start"], "end": u["end"], "text": u["transcript"]}
            for u in j["results"].get("utterances", [])]
    return {"language": j["results"]["channels"][0].get("detected_language", language),
            "words": words, "segments": segs}


def run_whisperx(audio: Path, language: str | None, model: str) -> dict:
    try:
        import whisperx  # type: ignore
    except ImportError:
        sys.exit("whisperx is not importable here. Run this on a GPU machine with whisperx installed, "
                 "or use --backend openai / deepgram.")
    device = "cuda"
    m = whisperx.load_model(model, device, language=language)
    a = whisperx.load_audio(str(audio))
    res = m.transcribe(a)
    align_model, meta = whisperx.load_align_model(language_code=res["language"], device=device)
    res2 = whisperx.align(res["segments"], align_model, meta, a, device)
    words = [{"w": w["word"], "start": w["start"], "end": w["end"]}
             for s in res2["segments"] for w in s.get("words", []) if "start" in w]
    segs = [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in res2["segments"]]
    return {"language": res["language"], "words": words, "segments": segs}


BACKENDS = {"openai": (run_openai, "whisper-1"),
            "deepgram": (run_deepgram, "nova-3"),
            "whisperx": (run_whisperx, "large-v3")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--backend", choices=BACKENDS, default="openai")
    ap.add_argument("--model", help="override the backend's default model")
    ap.add_argument("--language", help="ISO code, e.g. en, he; omit to auto-detect")
    args = ap.parse_args()

    fn, default_model = BACKENDS[args.backend]
    model = args.model or default_model
    with tempfile.TemporaryDirectory() as td:
        audio = extract_audio(args.video, Path(td))
        result = fn(audio, args.language, model)
    out = {"backend": args.backend, "model": model, "source": args.video.name,
           "duration": probe_duration(args.video), **result}
    if not out["words"]:
        sys.exit("Backend returned no word timestamps; cannot align frames.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({"out": str(args.out), "words": len(out["words"]),
                      "segments": len(out["segments"]), "duration": out["duration"]}))


if __name__ == "__main__":
    main()
