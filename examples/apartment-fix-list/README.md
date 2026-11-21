# Example: apartment fix list (marked mode)

A synthetic 12-second clip: espeak-ng narration over three ffmpeg test patterns, each
standing in for a room. The kitchen scene is blurred for its first three seconds to test
the sharpness picker. The marks file simulates three MARK presses from the
Narrated Video Marker app.

- `input/`: what the user hands over (`clip.mp4` + `clip.marks.json`).
- `context.md`, `frames/`, `frames.json`: the bundle (format: `references/output-format.md`).
- `tasks.md`: the task file from the `apartment-fix-list` profile.
- `source/`: the aligned transcript (OpenAI whisper-1, word timestamps) and the marks copy.

Generated on 2026-11-21 with the scripts in `scripts/` and the steps in the skill.
Real runs have phone footage, but the structure is identical.
