# Task profiles

The bundle is generic: a transcript with frames. A profile says what the walkthrough is
*for*. That changes which moments deserve a frame (in inferred mode), what the captions
pay attention to, and the optional task file written next to `context.md`.

Pick one from the user's words, or ask in a single line if it's unclear. "General" is fine.

## apartment-fix-list (the bundled example)

Walk-around of a home: things to fix, clean, replace or buy.

- Frame-worthy: each distinct item ("this cable", "the tap", "this corner needs cleaning").
- Captions: the item, where it is, and the visible defect.
- Task file `tasks.md`: one checklist line per item, grouped by room, each followed by its frame.

  ```markdown
  ## Office
  - [ ] Replace the frayed printer cable (USB-B): F001
    ![F001](frames/F001.jpg)
  ```

  Mark as *(inferred)* any category (fix / clean / buy) or detail that wasn't said.

## general

No task file. `context.md` only. Frame every concrete referent ("this", "here", a named object).

## Writing your own

Add a section here, or keep private profiles in
`${WORKSPACE:narrated-video-context}/profiles.md`. The skill reads that file too if it
exists. A profile needs three things: what deserves a frame, what captions focus on, and
the shape of the task file (or "none").

Ideas: site survey (defects for a contractor), inventory (insurance or moving), "how my
setup is wired" (cables and ports for an IT helper), garden jobs, car damage.
