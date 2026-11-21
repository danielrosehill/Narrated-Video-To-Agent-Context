# `narrated-video-marks` sidecar format, version 1

> Copy of `docs/marks-format.md` in [Narrated-Video-Marker-Android](https://github.com/danielrosehill/Narrated-Video-Marker-Android), the recorder app that writes it. Change both together.

One JSON file per video, same folder, same base name:

```
NV_20261121_143005.mp4
NV_20261121_143005.marks.json
```

A mark means "the thing I'm talking about is in frame *now*". The user taps MARK (or a
volume key) while recording. The consumer (the `narrated-video-context` plugin, skill
`narrated-video-to-context`) takes a still at each mark and anchors it in the transcript.

```json
{
  "format": "narrated-video-marks",
  "version": 1,
  "video": "NV_20261121_143005.mp4",
  "recorded_at": "2026-11-21T14:30:05.123+02:00",
  "complete": true,
  "duration": 94.21,
  "clock": "recorded-duration",
  "capture": {"width": 1280, "height": 720, "rotation_degrees": 90},
  "app": {"id": "com.danielrosehill.narratedvideomarker", "version": "1.0"},
  "marks": [
    {"n": 1, "t": 12.48, "wall": "2026-11-21T14:30:17.6+02:00"},
    {"n": 2, "t": 31.02, "wall": "2026-11-21T14:30:36.1+02:00"}
  ]
}
```

| Field | Meaning |
|---|---|
| `format`, `version` | Always `narrated-video-marks`, `1`. Consumers reject anything else. |
| `video` | File name of the video, relative to the sidecar. |
| `recorded_at` | ISO 8601 start time with offset. |
| `complete` | `false` while recording or if the app died. Marks up to that point are still valid. |
| `duration` | Seconds, as reported by the recorder at the end. `null` if incomplete. |
| `clock` | `recorded-duration`: `t` is seconds of recorded media from the start of the file, i.e. the same timeline as the video's presentation timestamps. |
| `capture` | Encoder resolution as the sensor delivers it, before rotation. `rotation_degrees` is the rotation written into the MP4. |
| `marks[].n` | 1-based, in order. Undone marks are removed and the rest are not renumbered. |
| `marks[].t` | Seconds into the video when the mark was pressed, to the millisecond. |
| `marks[].wall` | Wall-clock time of the press. For information only; use `t`. |

## Timing notes

- `t` comes from CameraX's recorded duration at the last status event, plus the time
  elapsed since that event. Expect it to be within about ±100 ms of the true frame.
- Tapping the screen shakes the phone, so the best still is usually *just before* `t`.
  Consumers should search a window around `t` that is weighted earlier (the plugin uses
  −0.8 s to +0.4 s). A volume-key press shakes it less.
- Any recorder can produce this format. One field is required beyond `format` and
  `version`: `marks[].t` in seconds from the start of the video.
