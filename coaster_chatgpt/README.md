# Why Roller Coasters Don't Fly Off The Tracks — Blender Story Director

**Target:** Blender 5.2 · EEVEE · 30 fps · 1080 × 1920 · 9:16 · frames 1–1887

This is a procedural, headless-ready scene project. It uses no external Python packages beyond Blender's bundled `bpy` and `mathutils` modules.

## Project layout

```text
roller_coaster_story_director/
├── scene.py                 # Scene builder, frame evaluator, CLI renderer
├── shots.json               # 29 gapless camera beats, mapped to audio time
├── acting.json              # hold / clasp / operate / emotion / impact grammar
└── lib/
    ├── __init__.py
    ├── utils.py             # Shared geometry, collection, and transform helpers
    ├── look.py              # Toon shaders, black hull outlines, sky domes, lighting
    ├── props.py             # PropSpec and five dynamic hero-prop implementations
    ├── sets.py              # Three modular environments and anchor registry
    └── chars.py             # Paper-cutout Builder/Rival, armature IK, hand targets
```

## Four-layer architecture

1. **Look and asset specifications** — `look.py` defines the toon pipeline, ink outlines, two-tone sky domes and two photometric lighting moods. `props.py` defines reusable `PropSpec` instances and their channels/sockets.
2. **Scene and character construction** — `sets.py` builds `workshop_night`, `fairground_dawn`, and `coaster_climax`, with named anchors. `chars.py` creates flat XZ paper-cutout performers, black inverted-hull outlines, articulated bones, IK constraints, and named hand targets.
3. **Story data** — `shots.json` contains all 29 camera beats. `acting.json` contains the five acting verbs and timed prop/character interactions. Frame ranges are inclusive, contiguous, and gapless.
4. **Deterministic evaluation** — `scene.py` evaluates all channels, prop geometry, IK targets, set visibility, lighting mood, camera position, and impact effects from frame `f` alone. It does not depend on previously evaluated frames or simulation caches.

## Dynamic hero props

| Prop | Channels | Named sockets / behavior |
|---|---|---|
| `LoopTrackProp` | `bend_bottom`, `squeeze_sides` | Rebuilds continuous approach/loop/exit rails and sleepers; broad lower-radius teardrop morph and independent side squeeze |
| `SledgehammerProp` | `swing_stroke` | `grip_main`, `grip_twohand`, `impact_end`; rotates around the main grip pivot |
| `TestDummyProp` | `crush_progress` | `grip_left`, `grip_right`, `seat_mount`, `head_socket`; accordion-ring compression |
| `TurnbuckleCrankProp` | `crank_angle` | `grip_crank`, `grip_brace`, `jaw_left`, `jaw_right`; three crank revolutions close the jaws |
| `CoasterCartProp` | `track_progress` | `seat_builder`, `seat_rival`, `grip_left`, `grip_right`; arc-length sampling along a cubic Bezier chain |

The hero loop and rival loop are separate `LoopTrackProp` objects. The hammer drives the builder loop's lower curve; the turnbuckle drives the rival loop's side squeeze. The cart route is rebuilt from the current loop outline before each frame is rendered.

## Lighting notes

- `night_workshop`: 500 W tungsten point practical, cool 40 W/m² Sun rim, and navy two-tone sky dome at strength 1.0.
- `morning_fair`: 60 W/m² morning Sun, 15 W area-light sky fill, and warm-horizon two-tone sky dome at strength 1.2.
- All Sun lamps are held at or above 40 W/m². The requested 15 W bounce is implemented as an area light rather than a sub-minimum Sun lamp.
- The world background and emissive sky dome remain visible; the lighting does not drop the scene into a black void.

Blender 5.x uses the EEVEE engine identifier `BLENDER_EEVEE` (the former `BLENDER_EEVEE_NEXT` identifier was renamed in Blender 5.0). Compositing is explicitly disabled with `scene.render.use_compositing = False`.

## Command line

Build the `.blend` without rendering:

```bash
blender -b --python scene.py -- --build-only --blend-output //roller_coaster_story.blend
```

Render the complete sequence as individual PNGs:

```bash
blender -b --python scene.py -- --start 1 --end 1887 --step 1 --output //frames
```

Render one deterministic frame (suitable for a farm worker):

```bash
blender -b --python scene.py -- --frame 540 --output //frames
```

Run the pure-Python timeline/contract checks (does not require Blender):

```bash
python validate_project.py
```

Render a shard of the timeline:

```bash
blender -b --python scene.py -- --start 1 --end 630 --step 1 --output //frames
blender -b --python scene.py -- --start 631 --end 1260 --step 1 --output //frames
blender -b --python scene.py -- --start 1261 --end 1887 --step 1 --output //frames
```

## Direct Python use

```python
import scene
scene.build_scene()
scene.apply_frame_actions(540)  # always call immediately before rendering
bpy.ops.render.render(write_still=True)
```

`apply_frame_actions(f)` is deterministic and may be called out of order. It resets channels and character targets, re-evaluates both loops, reconstructs dependent cart paths, applies the matching shot/lighting mood, and then resolves holds/clasps/impacts for that exact frame.

## Scope

The project builds the 3D set, characters, props, animation controls, camera beats, and still-frame renderer. It does not synthesize or embed the supplied voice-over; `shots.json` preserves the exact beat timing so the audio can be added in a separate edit or sequencer pass.
