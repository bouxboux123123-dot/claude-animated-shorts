#!/usr/bin/env python3
"""Headless CLI renderer for the roller-coaster short.

Frame state is a deterministic function of frame f: apply_frame_actions(f) updates
the registered prop + character objects from acting.json channels, then the scene
(lights / camera / geometry) is applied from shots.json. Run:
    blender.exe -b -P scene.py -- -f 0 -o out/frame_####.png
"""
import os
import sys
import json
import math
from pathlib import Path

try:
    import bpy
except Exception:
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ─── Load data ───
with open(os.path.join(HERE, 'shots.json'), 'r') as f:
    SHOTS = json.load(f)

with open(os.path.join(HERE, 'acting.json'), 'r') as f:
    ACTING = json.load(f)

FPS = ACTING['fps']
TOTAL_FRAMES = ACTING['total_frames']
ACTIONS = ACTING['actions']

# ─── Prop & character registries ───
PROPREGISTRY = {}      # name -> PropSpec instance (with channel_values)
CHARREGISTRY = {}      # name -> CardRig instance


def register_prop(name, spec=None):
    """Register once; a missing spec is a no-op for unknown non-hero actions."""
    if spec is not None and name not in PROPREGISTRY:
        PROPREGISTRY[name] = spec
    return PROPREGISTRY.get(name)


def init_props(collection):
    """Spawn every concrete PropSpec exactly once."""
    if PROPREGISTRY:
        return
    from lib.props import (LoopTrackProp, SledgehammerProp, TestDummyProp,
                           TurnbuckleCrankProp, CoasterCartProp)
    specs = {
        'loop_track': LoopTrackProp('loop_track'),
        'hammer': SledgehammerProp('hammer'),
        'dummy': TestDummyProp('dummy'),
        'turnbuckle': TurnbuckleCrankProp('turnbuckle'),
        'cart': CoasterCartProp('cart'),
    }
    for name, spec in specs.items():
        spec.create(collection)
        register_prop(name, spec)
    # Keep the hero props in a readable layout for workshop close-ups.
    PROPREGISTRY['loop_track'].obj.location = (0, 0, 0)
    PROPREGISTRY['hammer'].obj.location = (-1.8, -0.2, 1.8)
    PROPREGISTRY['dummy'].obj.location = (1.5, 0.4, 1.0)
    PROPREGISTRY['turnbuckle'].obj.location = (2.0, 0.2, 1.8)
    PROPREGISTRY['cart'].obj.location = (-8.0, 0, 0)


def register_char(name, char):
    CHARREGISTRY[name] = char
    return char


# ─── Core helpers ───
def find_shot(frame):
    for s in SHOTS:
        if s['f_in'] <= frame < s['f_out']:
            return s
    return None


def find_actions(frame):
    return [a for a in ACTIONS if a['f_in'] <= frame < a['f_out']]


def apply_frame_actions(frame):
    """Single deterministic function of frame f. Drives every prop channel."""
    active = find_actions(frame)
    if not PROPREGISTRY:
        return
    for act in active:
        t = 0.0 if act['f_out'] <= act['f_in'] else (frame - act['f_in']) / (act['f_out'] - act['f_in'])
        frm = act.get('from', 0.0)
        to = act.get('to', 1.0)
        val = frm + (to - frm) * t
        prop = act.get('prop')
        channel = act.get('channel')
        spec = register_prop(prop) if prop else None
        if spec and channel:
            spec.set_channel(channel, val)
            print(f'  f{frame} {prop}.{channel}={val:.3f}')
        elif spec and prop:
            # Legacy hold directives without an explicit channel.
            to = act.get('to', 1.0)
            if 'swing_stroke' in spec.channel_values:
                spec.set_channel('swing_stroke', to)


def clear_scene():
    """Remove everything so frames are deterministic per registration."""
    for collection in list(bpy.data.collections):
        for obj in list(collection.objects):
            if hasattr(obj, 'materials') and getattr(obj, 'data', None):
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def build_scene(frame, samples=None):
    if bpy is None:
        return
    sc = bpy.context.scene
    sc.frame_set(frame)

    # 1. Render settings (EEVEE Next rules: compositing off, sun energy >= 40)
    try:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        # Blender 5.2 release-candidate builds may still expose the legacy enum.
        sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 720
    sc.render.resolution_y = 1280
    sc.render.resolution_percentage = 100
    sc.render.fps = 30
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.use_compositing = False
    sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.look = 'Medium High Contrast'
    if hasattr(sc, 'eevee'):
        try:
            sc.eevee.taa_render_samples = samples if samples is not None else 16
        except Exception:
            pass

    # 2. Build concrete sets once; cache the collections for later frame lookups
    shot = find_shot(frame) or SHOTS[-1]
    mood = shot['set']
    if not hasattr(build_scene, '_collections_built'):
        import lib.sets as sets_mod
        sets_mod.build_all()
        build_scene._collections_built = True

    # Toggle set visibility: only show the set for the current shot
    for set_name in ['workshop_night', 'fairground_dawn', 'coaster_climax']:
        col = bpy.data.collections.get(set_name)
        if col:
            col.hide_render = (set_name != mood)

    # 3. Re-apply the photometric environment when the shot mood changes.
    if getattr(build_scene, '_mood', None) != mood:
        import lib.look as look_mod
        look_mod.setup_sky(sc, mood)
        look_mod.setup_lighting(sc, sc.collection, mood)
        build_scene._mood = mood

    # 4. Spawn concrete props and character cards once.
    init_props(bpy.context.scene.collection)
    init_cards()

    # 5. Apply frame actions to concrete PropSpec channels.
    apply_frame_actions(frame)

    # 6. Place characters at scene anchors.
    place_characters(mood)

    # 7. Camera follows shot
    cam_pos, cam_target, cam_lens, cam_roll = pick_camera(shot, frame)
    from mathutils import Vector
    cam_obj = sc.camera
    cam_obj.location = cam_pos
    cam_obj.data.lens = cam_lens
    dir_vec = Vector(cam_target) - Vector(cam_pos)
    rot = dir_vec.to_track_quat('-Z', 'Y').to_euler()
    cam_obj.rotation_euler = rot
    cam_obj.rotation_euler.z += math.radians(cam_roll)
    sc.camera = cam_obj

    # 8. Debug every 30 frames.
    if frame % 30 == 0:
        print(f'  concrete props={list(PROPREGISTRY)} chars={list(CHARREGISTRY)} frame={frame}/{TOTAL_FRAMES}')


def init_cards():
    """Create CardRig instances for Builder & Rival."""
    if 'builder' not in CHARREGISTRY:
        from lib.chars import Builder
        builder = Builder()
        builder.create(bpy.context.scene.collection)
        builder.obj.location = (-0.8, -1.5, 0.0)
        register_char('builder', builder)
        register_char('owner', builder)
    if 'rival' not in CHARREGISTRY:
        from lib.chars import Rival
        rival = Rival()
        rival.create(bpy.context.scene.collection)
        rival.obj.location = (2.0, -1.2, 0.0)
        register_char('rival', rival)


def place_characters(mood):
    """Place Builder and Rival at real set anchors."""
    import lib.sets as sets_mod
    b_pos = None
    r_pos = None
    if mood in ('workshop_night', 'night_workshop'):
        b_pos = sets_mod.SETS['workshop_night'].anchors.get('builder_pos')
        r_pos = sets_mod.SETS['workshop_night'].anchors.get('rival_pos')
    elif mood == 'fairground_dawn':
        b_pos = sets_mod.SETS['fairground_dawn'].anchors.get('owner_queue')
        r_pos = sets_mod.SETS['fairground_dawn'].anchors.get('rival_queue')
    elif mood == 'coaster_climax':
        b_pos = sets_mod.SETS['coaster_climax'].anchors.get('loop_bottom')
        r_pos = sets_mod.SETS['coaster_climax'].anchors.get('rival_loop_center')

    if b_pos and 'builder' in CHARREGISTRY and CHARREGISTRY['builder'].obj:
        CHARREGISTRY['builder'].obj.location = tuple(b_pos.location)
    if r_pos and 'rival' in CHARREGISTRY and CHARREGISTRY['rival'].obj:
        CHARREGISTRY['rival'].obj.location = tuple(r_pos.location)


def pick_camera(shot, frame):
    cam = shot['camera']
    if len(cam) >= 2:
        dur = shot['f_out'] - shot['f_in']
        t = max(0.0, min(1.0, (frame - shot['f_in']) / dur)) if dur > 0 else 0.0
        c0, c1 = cam[0], cam[1]
        pos = [c0['pos'][i] + (c1['pos'][i] - c0['pos'][i]) * t for i in range(3)]
        target = [c0['target'][i] + (c1['target'][i] - c0['target'][i]) * t for i in range(3)]
        lens = c0['lens'] + (c1['lens'] - c0['lens']) * t
        roll = c0['roll_deg'] + (c1['roll_deg'] - c0['roll_deg']) * t
    else:
        c0 = cam[0]
        pos, target, lens, roll = c0['pos'], c0['target'], c0['lens'], c0['roll_deg']
    return pos, target, lens, roll


def render_frame(frame, out_path, samples=None):
    if bpy is None:
        print(f"[render] frame {frame} -> {out_path} (bpy unavailable)")
        return
    sc = bpy.context.scene
    sc.frame_set(frame)
    build_scene(frame, samples=samples)
    abs_out = os.path.abspath(str(out_path))
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    sc.render.filepath = abs_out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered frame {frame} -> {abs_out}")


def selfcheck():
    """One runnable check that fails if the frame→action logic breaks."""
    errors = []
    prev_end = 0
    for s in SHOTS:
        if s['f_in'] != prev_end:
            errors.append(f"shot {s['id']}: gap/overlap")
        prev_end = s['f_out']
    if prev_end != TOTAL_FRAMES:
        errors.append(f"shots end at {prev_end}, expected {TOTAL_FRAMES}")
    for a in ACTIONS:
        if a['f_out'] <= a['f_in']:
            errors.append(f"action f={a['f_in']}-{a['f_out']} invalid range")
        if a['f_out'] > TOTAL_FRAMES:
            errors.append(f"action f={a['f_out']} exceeds TOTAL_FRAMES")
        if a.get('act') == 'operate' and not a.get('prop'):
            errors.append(f"action f={a['f_in']}: operate needs prop+channel")
    for f in [0, 75, 1886]:
        if find_shot(f) is None:
            errors.append(f"frame {f} has no shot")
    if errors:
        print("SELFCHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"SELFCHECK PASSED: {len(SHOTS)} shots, {len(ACTIONS)} actions, total_frames={TOTAL_FRAMES}, fps={FPS}")


def main():
    raw_args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]

    # Check for batch frames mode: frames <out_dir> <start> <end> [samples]
    if len(raw_args) >= 4 and raw_args[0] == 'frames':
        out_dir = os.path.abspath(raw_args[1])
        start_f = int(raw_args[2])
        end_f = int(raw_args[3])
        samples = int(raw_args[4]) if len(raw_args) > 4 else 4
        os.makedirs(out_dir, exist_ok=True)
        print(f"=====================================================")
        print(f"Rendering Coaster frames {start_f} to {end_f} (samples={samples})")
        print(f"=====================================================")
        for f in range(start_f, end_f):
            out_file = os.path.join(out_dir, f"f{f:04d}.png")
            render_frame(f, out_file, samples=samples)
        print("Slice render complete!")
        return

    parser = argparse_nohelp()
    args = parser.parse_args(raw_args)
    if args.selfcheck:
        selfcheck()
        return
    if args.shots:
        for s in SHOTS:
            print(f"{s['id']}: beat {s['beat']} f={s['f_in']}-{s['f_out']} set={s['set']} \"{s['text'][:60]}...\"")
        return
    if args.acting:
        for a in ACTIONS:
            print(f"f={a['f_in']}-{a['f_out']} act={a.get('act')} char={a.get('char')} prop={a.get('prop')} ch={a.get('channel')}")
        return
    frame = args.frame
    if not (0 <= frame < TOTAL_FRAMES):
        print(f"Frame {frame} out of range [0, {TOTAL_FRAMES-1}]")
        sys.exit(1)
    out = args.output.format(frame) if '{' in args.output else args.output
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    render_frame(frame, out)


def argparse_nohelp():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--frame', type=int, default=0)
    parser.add_argument('-o', '--output', type=str, default='out/frame_{:04d}.png')
    parser.add_argument('--shots', action='store_true')
    parser.add_argument('--acting', action='store_true')
    parser.add_argument('--selfcheck', action='store_true')
    return parser


if __name__ == '__main__':
    main()