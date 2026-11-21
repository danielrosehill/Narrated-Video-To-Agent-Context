# `narrated-frame-context` bundle, version 1

What the skill produces: a folder an agent can read cold. It holds a clean transcript with
stills referenced inline, plus a JSON index of those stills.

```
apartment-fix-list-2026-11-21/
├── context.md                      # read this first
├── frames/
│   ├── F001.jpg
│   ├── F002.jpg
│   └── ...
├── frames.json                     # machine index of every frame
└── source/
    ├── transcript.aligned.json     # word timestamps (to re-extract or re-pick frames)
    └── NV_20261121_143005.marks.json   # only when the video came with marks
```

The video is **not** copied in, because it's big. `frames.json` records its path. Copy
it into `source/` only if the user asks.

## `context.md`

```markdown
# Apartment fix list: walkthrough 2026-11-21

Source: NV_20261121_143005.mp4 (1:34), recorded 2026-11-21 14:30 +02:00.
Mode: marked (7 marks). Frames: 7. Purpose: things to fix or clean in the apartment.

## Transcript

Okay, starting in the office. We need a new printer cable here, the old one is
frayed right at the plug.

![F001: frayed printer cable at the back of the printer](frames/F001.jpg)

Moving into the kitchen...
```

Rules:

- **No timestamps in the prose.** Timing lives in `frames.json`.
- Light clean-up only. Remove fillers ("um", "so yeah") and false starts, fix ASR errors
  you're sure of, and split into paragraphs at topic or room changes. Never add information
  that wasn't said. Mark an unclear word as `[unclear]`.
- A frame goes **on its own line, right after the sentence it illustrates**, as a
  standard Markdown image: `![<ID>: <caption>](frames/<ID>.jpg)`. The ID comes first in
  the alt text so a plain-text reader still sees it. Agents, GitHub and any Markdown
  viewer all understand this form.
- Captions describe what is *visible* (≤ 12 words). They don't repeat the narration.
- IDs are `F001`, `F002`, … in order of time, with no gaps in the final bundle.
- Optional `## Notes` at the end: things said with no usable frame ("couldn't get the
  boiler in shot"), marks that had nothing nearby in the narration, and so on.

## `frames.json`

```json
{
  "format": "narrated-frame-context",
  "version": 1,
  "title": "Apartment fix list: walkthrough 2026-11-21",
  "purpose": "things to fix or clean in the apartment",
  "source": {"video": "/abs/or/relative/path/NV_20261121_143005.mp4", "duration": 94.2,
             "recorded_at": "2026-11-21T14:30:05+02:00"},
  "mode": "marked",
  "transcription": {"backend": "openai", "model": "whisper-1", "language": "en"},
  "frames": [
    {
      "id": "F001",
      "file": "frames/F001.jpg",
      "t": 12.2,
      "anchor": 12.48,
      "origin": "mark",
      "mark_n": 1,
      "quote": "We need a new printer cable here",
      "caption": "frayed printer cable at the back of the printer",
      "sharpness": 412.7,
      "reviewed": true
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `mode` | `marked` (anchors from a marks sidecar), `inferred` (anchors chosen from the transcript) or `mixed`. |
| `frames[].t` | Time of the still actually used. |
| `frames[].anchor` | The time it was searched around: the mark's `t`, or the matching phrase's start. |
| `origin` | `mark` or `transcript`. |
| `mark_n` | The mark's `n` from the sidecar, if any. |
| `quote` | The words in `context.md` the frame follows, verbatim. |
| `sharpness` | Laplacian variance from `grab_frame.py`. Only comparable within one video. |
| `reviewed` | `true` once the agent has looked at the image and accepted it. |
