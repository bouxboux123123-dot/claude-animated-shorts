# Why Roller Coasters Don’t Fly Off The Tracks

A Blender 5.2 / EEVEE Next procedural source project for the supplied 62.9-second, 29-beat short. The visual story is built from animated geometry and flat paper-cutout characters, with all hero props controlled through explicit channels and sockets.

## Project structure

- `scene.py` builds the scene, evaluates the camera/acting/prop state from frame number, and provides the headless render CLI.
- `lib/look.py` contains toon materials, inverted-hull outlines, two-tone sky domes, render settings, and per-set lighting rigs.
- `lib/props.py` defines `PropSpec` and the five required animated prop types: `LoopTrackProp`, `SledgehammerProp`, `TestDummyProp`, `TurnbuckleCrankProp`, and `CoasterCartProp`.
- `lib/sets.py` builds `workshop_night`, `fairground_dawn`, and `coaster_climax`, then exposes the anchor registry.
- `lib/chars.py` builds flat builder/rival character cards with arm targets and named IK-style hand sockets.
- `shots.json` defines 29 contiguous camera/story beats for 1,887 frames at 30 fps.
- `acting.json` defines the five required acting verbs and the interaction timeline.
- `SCRIPT.md` preserves the supplied narration and records the historical caveat.

## Run in Blender 5.2

From this project directory, with Blender 5.2 available on `PATH`:

```bash
blender -b --python scene.py -- --build-only
blender -b --python scene.py -- --frame 900 --output //frame_0900.png
blender -b --python scene.py -- --render --output //rollercoaster_short.mp4
```

The default output is vertical 1440×2560, 30 fps, H.264. Use `--preview` for a 540×960 preview. The script saves `rollercoaster_short.blend` by default when building or rendering; override with `--blend-output /absolute/path/short.blend`.

`apply_frame_actions(f)` is deterministic and derives track shape, dummy compression, hammer swing, crank rotation, coaster position, character hand targets, lighting mood, and camera framing from the requested frame. A render-pre callback invokes it immediately before each rendered frame. Compositing is disabled for reliable headless rendering.

## Validation and limits

The Python sources passed syntax parsing, and the JSON checks confirmed the 29 shot ranges are contiguous, cover all 1,887 frames, and use only the declared acting verbs. The sandbox used to create this package does not have Blender installed, so the `.blend` scene and video have **not** been rendered or visually validated here. Run the commands above in Blender 5.2 to produce them.

The package renders picture only. No narration recording, music, or sound effects were attached, so audio generation and final audio mux are not included.

## Historical note

The script’s central engineering principle is grounded in coaster physics, but its “first ride ever” phrasing is too broad: Guinness World Records describes a full-size centrifugal railway built by Tarr & Riley in 1842, before the famous American loop coasters. A University of Gothenburg physics article explains why a circular loop produces stronger acceleration near the bottom and why modern loop profiles use a larger-radius bottom and tighter top. The specific rival, hammer repair, crushed dummy, and opening-day incidents in this script are not supported by those sources and should be presented as dramatization, not verified biography. See `SCRIPT.md` for source links.

Run the Blender-independent package checks with:

```bash
python3 tests/validate_structure.py
```
