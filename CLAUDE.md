# Narrated-Video-To-Agent-Context

Plugin `narrated-video-context`. Release tier: small (`v1.0`, `v1.1`, …).

- One skill: `skills/narrated-video-to-context/SKILL.md`. Scripts in `scripts/` are uv inline-metadata scripts.
- `references/marks-format.md` is a copy of `docs/marks-format.md` in
  `danielrosehill/Narrated-Video-Marker-Android` (the recorder app). Change both together.
- `references/output-format.md` is the bundle contract (`narrated-frame-context` v1).
- Regenerate `examples/apartment-fix-list/` with the scripts if the format changes. The clip is synthetic (espeak-ng + ffmpeg test patterns).
