# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless>=4.9", "numpy>=1.26"]
# ///
"""Pick the best still for one moment in a video.

Extracts candidate frames in a window around an anchor time, scores each for
sharpness (variance of the Laplacian; motion blur and focus hunting score low)
and exposure, and writes the winner plus the runners-up so the agent can look
and swap if the winner is wrong (e.g. sharp but pointing at the floor).

Usage:
  uv run grab_frame.py VIDEO --at 12.4 --id F003 --frames-dir out/frames \
      [--before 0.6] [--after 1.6] [--step 0.2] [--keep 3] [--max-width 1600]

`--after` is longer than `--before` on purpose: people say "this cable here"
slightly before the camera settles on it.

Prints JSON: {"id", "file", "t", "sharpness", "alternates": [{"file","t","sharpness"}]}.
Alternates are written to <frames-dir>/_candidates/<id>/ and can be deleted at the end.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np


def duration(video: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "json", str(video)], check=True, capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def extract(video: Path, t: float, dest: Path, max_width: int) -> bool:
    # -ss before -i is a fast keyframe seek; ffmpeg then decodes accurately to t.
    # ffmpeg applies the phone's rotation metadata automatically.
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", f"scale='min({max_width},iw)':-2", "-q:v", "2", str(dest)],
                       capture_output=True)
    return r.returncode == 0 and dest.exists()


def score(path: Path) -> tuple[float, float]:
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    h = 720
    if img.shape[0] > h:  # score at a fixed height so sizes compare
        img = cv2.resize(img, (int(img.shape[1] * h / img.shape[0]), h))
    sharp = float(cv2.Laplacian(img, cv2.CV_64F).var())
    mean = float(np.mean(img))
    return sharp, mean


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--at", type=float, required=True, help="anchor time in seconds")
    ap.add_argument("--id", required=True, help="frame id, e.g. F003")
    ap.add_argument("--frames-dir", type=Path, required=True)
    ap.add_argument("--before", type=float, default=0.6)
    ap.add_argument("--after", type=float, default=1.6)
    ap.add_argument("--step", type=float, default=0.2)
    ap.add_argument("--keep", type=int, default=3, help="alternates to keep besides the winner")
    ap.add_argument("--max-width", type=int, default=1600)
    ap.add_argument("--ext", default="jpg", choices=["jpg", "png"])
    args = ap.parse_args()

    dur = duration(args.video)
    cand_dir = args.frames_dir / "_candidates" / args.id
    if cand_dir.exists():
        shutil.rmtree(cand_dir)
    cand_dir.mkdir(parents=True)

    start = max(0.0, args.at - args.before)
    end = min(dur - 0.05, args.at + args.after)
    times = list(np.arange(start, end + 1e-6, args.step)) or [min(args.at, dur - 0.05)]

    scored = []
    for t in times:
        p = cand_dir / f"{args.id}_{t:08.3f}.{args.ext}"
        if not extract(args.video, float(t), p, args.max_width):
            continue
        sharp, mean = score(p)
        # Penalise near-black / blown-out frames (pocket, lens flare) without discarding them.
        exposure_ok = 25 <= mean <= 235
        scored.append({"file": p, "t": round(float(t), 3), "sharpness": round(sharp, 1),
                       "rank": sharp if exposure_ok else sharp * 0.2})
    if not scored:
        raise SystemExit(f"no frames extracted around t={args.at}")

    scored.sort(key=lambda c: c["rank"], reverse=True)
    best = scored[0]
    final = args.frames_dir / f"{args.id}.{args.ext}"
    shutil.copy2(best["file"], final)

    keep = scored[1:1 + args.keep]
    keep_files = {c["file"] for c in keep}
    for c in scored:
        if c["file"] not in keep_files:
            c["file"].unlink(missing_ok=True)

    print(json.dumps({
        "id": args.id, "file": str(final), "t": best["t"], "sharpness": best["sharpness"],
        "anchor": args.at,
        "alternates": [{"file": str(c["file"]), "t": c["t"], "sharpness": c["sharpness"]} for c in keep],
    }))


if __name__ == "__main__":
    main()
