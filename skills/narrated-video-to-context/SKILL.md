---
name: narrated-video-to-context
description: Turn a narrated phone video (e.g. apartment fix list) into agent context with an aligned transcript and stills referenced inline.
---

# Narrated video → agent context

The user filmed something and talked over it: "we need a new printer cable here", "this
tap drips". Produce a bundle an agent can work from: a clean transcript, one still per
thing referred to, and each still referenced inline right after the sentence it
illustrates. Format: `references/output-format.md`.

There are two modes, picked by what arrives with the video:

- **marked**: there is a `<video-base>.marks.json` sidecar (`references/marks-format.md`,
  written by the Narrated Video Marker Android app, or by any tool using that format).
  The user pressed MARK when the subject was in frame. **Marks are the anchors.**
- **inferred** (post facto): just a video. Work out the anchors from the transcript.

## Inputs

- Video path (MP4/MOV/WebM, any phone). Look for a sidecar with the same base name and
  `.marks.json` next to it.
- Purpose / profile (`references/task-profiles.md`): from the user's words, else `general`.
- Output folder: the user's, else `<video-dir>/<slug>-context/`, where the slug comes from
  the profile and the date.

## Data storage

Settings only, in `${WORKSPACE:narrated-video-context}/config.json`:
`{"backend": "openai|deepgram|whisperx", "language": "en", "output_root": "<optional>"}`.
Private profiles go in `${WORKSPACE:narrated-video-context}/profiles.md`. Bundles go where
the user says, never into the workspace. Create the config on first use. Ask once which
backend has a key, and suggest `openai`.

## Steps

1. **Probe.** `ffprobe -v error -show_entries format=duration:stream=codec_type,width,height -of json <video>`.
   Confirm there's an audio stream. Read the sidecar if present, and check
   `format == "narrated-video-marks"` and `version == 1`. `complete: false` is fine:
   use the marks it has.

2. **Transcribe with word timestamps.**
   `uv run ${PLUGIN_ROOT}/scripts/transcribe.py <video> --out <out>/source/transcript.aligned.json --backend <b> [--language xx]`
   - `openai` (whisper-1, word + segment timestamps; `OPENAI_BASE_URL` for compatible
     servers) or `deepgram` (nova-3): hosted, cheap, light on the machine. Default.
   - `whisperx`: forced alignment, best timing, but needs a GPU. Run it only on a machine
     that has one. Never on a laptop without asking.
   - Hosted backends upload the audio to the provider. Say so in one line before the first run.
   Copy the sidecar into `<out>/source/` as well.

3. **Read the transcript** (segments, not the word list) and plan the frames:
   - *marked*: for each mark, find the words around its `t` (about 4 s before to 2 s
     after). That is the sentence the frame belongs to. A mark with no speech near it still
     gets a frame. Caption it from the image, and list it in `## Notes`.
   - *inferred*: choose the moments a viewer would need to see. Concrete referents ("this",
     "here", "over there", named items), filtered by the profile. Get each anchor with
     `uv run ${PLUGIN_ROOT}/scripts/find_phrase.py <transcript> "<phrase>"`. Take the
     match's `end`: the camera usually lands on the thing as the sentence finishes.
   - In marked mode, add a few transcript frames only if the user asks. Otherwise list
     clear unmarked referents in `## Notes` ("mentioned but not marked: the boiler").

4. **Grab a still per anchor.**
   `uv run ${PLUGIN_ROOT}/scripts/grab_frame.py <video> --at <t> --id F00N --frames-dir <out>/frames [window]`
   - marked: `--before 0.8 --after 0.4`. Tapping shakes the phone, so the good frame is
     just before the press.
   - inferred: the defaults (`--before 0.6 --after 1.6`).
   It returns the sharpest, well-exposed candidate plus `alternates`.

5. **Look at every frame** (Read the image). Keep it only if it shows what the sentence
   is about. If it doesn't:
   - try the `alternates` in order, copying the good one over `frames/F00N.jpg`;
   - otherwise re-run `grab_frame.py` with a wider or shifted window (e.g. `--at <t+1.5>`
     `--after 3`) — the user often points the camera a beat late;
   - if still nothing, drop it and note "no usable frame" in `## Notes`.
   Write the caption from what you see. Set `reviewed: true`.

6. **Write the bundle** per `references/output-format.md`: `context.md` (clean prose, no
   timestamps, each frame on its own line after its sentence) and `frames.json`. If the
   profile has a task file (e.g. `tasks.md` for apartment-fix-list), write it too. It
   references the same frame files. Renumber IDs if you dropped any, then delete
   `frames/_candidates/`.

7. **Report** in a few lines: the bundle path, the mode, the frame count, and anything in
   `## Notes`. Don't paste the transcript back.

## Notes

- Requires `ffmpeg`/`ffprobe` and `uv`. The scripts pull their Python dependencies
  (requests, opencv-python-headless) through inline `uv` metadata.
- Long videos (> 20 min): transcription is fine (16 kHz mono MP3 is about 0.5 MB/min).
  In inferred mode, cap at about 40 frames and ask before going beyond.
- Phone rotation: ffmpeg applies the MP4 rotation tag on extraction, so frames come out
  upright.
- Example input/output: `examples/apartment-fix-list/` in the plugin repo.
- Related: the `video-steering` skill (screen recordings for software feedback) samples
  frames by scene change. This skill anchors frames to what was *said* or *marked*.
