# Narrated Video To Agent Context

Film something on your phone, talk over it, and get context an AI agent can act on: a
clean transcript with a still for each thing you referred to, inline where you said it.

> "We need a new printer cable here."
>
> ![F001: office printer area (synthetic example frame)](examples/apartment-fix-list/frames/F001.jpg)

Example use: walk through the apartment narrating what needs fixing or cleaning, then
hand the bundle to an agent to build a task list, get quotes or order parts.

## Two ways in

| Mode | Input | Where frames come from |
|---|---|---|
| **marked** | video + `<name>.marks.json` | You pressed MARK while filming. Recorder app: [Narrated-Video-Marker-Android](https://github.com/danielrosehill/Narrated-Video-Marker-Android) (720p, volume key or on-screen button). |
| **inferred** | any video | After the fact: the agent reads the word-aligned transcript and picks the moments ("this", "here", named items). |

Either way, each anchor time gets a window of candidate frames. The sharpest well-exposed
one wins, and the agent looks at it and swaps in an alternate if it shows the wrong thing.

## Output

```
apartment-fix-list-2026-11-21/
├── context.md      # transcript, no timestamps, ![F001: caption](frames/F001.jpg) after each sentence
├── frames/F001.jpg …
├── frames.json     # id, time, mark, quote, caption, sharpness per frame
├── tasks.md        # profile-specific (e.g. fix list by room); optional
└── source/         # word-aligned transcript + marks sidecar
```

Spec: [`references/output-format.md`](references/output-format.md). Worked example:
[`examples/apartment-fix-list/`](examples/apartment-fix-list/).

## Skill

- `narrated-video-to-context`: the whole pipeline (probe, transcribe, plan anchors, grab
  frames, review, write the bundle).

## Scripts (usable on their own)

| Script | Does |
|---|---|
| `scripts/transcribe.py` | Word-timestamped transcript. Backends: `openai` (whisper-1, default; `OPENAI_BASE_URL` for compatible servers), `deepgram` (nova-3), `whisperx` (local GPU). |
| `scripts/find_phrase.py` | When was "<phrase>" said? Fuzzy match → start/end. |
| `scripts/grab_frame.py` | Best still around a time: sharpness (Laplacian variance) + exposure, keeps alternates. |

Needs `ffmpeg`, `ffprobe` and [`uv`](https://docs.astral.sh/uv/). Python dependencies
are declared inline. Hosted backends upload the audio (16 kHz mono MP3) to the provider.

## Install

```bash
claude plugins marketplace add danielrosehill/Claude-Code-Plugins
claude plugins install narrated-video-context@danielrosehill
```

## License

MIT
