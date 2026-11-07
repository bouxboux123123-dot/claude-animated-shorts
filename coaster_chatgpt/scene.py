"""Headless Blender scene builder and deterministic per-frame renderer.

Four-layer contract:
  1) lib/look.py + lib/props.py: reusable look and PropSpec channels
  2) lib/sets.py + lib/chars.py: modular stage, anchors, IK character rigs
  3) shots.json + acting.json: camera beats and acting grammar data
  4) apply_frame_actions(f): pure frame-index evaluation immediately before render

Run:
  blender -b --python scene.py -- --build-only
  blender -b --python scene.py -- --start 1 --end 1887 --step 1 --output //frames
  blender -b --python scene.py -- --frame 600 --output //frames
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_DIR = str(Path(__file__).resolve().parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from lib.utils import ensure_collection, make_empty, add_rod, look_at
from lib.look import build_lighting_rigs, apply_lighting_mood, make_flat_material
from lib.props import (
    LoopTrackProp, SledgehammerProp, TestDummyProp,
    TurnbuckleCrankProp, CoasterCartProp,
)
from lib.sets import build_all_sets, ANCHOR_REGISTRY, SET_COLLECTIONS, set_active_set
from lib.chars import build_builder, build_rival

FPS = 30
FRAME_START = 1
FRAME_END = 1887

SCENE = None
CAMERA = None
LIGHT_RIGS = None
PROPS = {}
PROP_COLLECTIONS = {}
CHARACTERS = {}
CHAR_COLLECTIONS = {}
FX_COLLECTION = None
SPARKS = []
SPARK_BASE_LOCATIONS = {}
SHOTS = []
ACTING_EVENTS = []


def _load_json(filename):
    with open(os.path.join(PROJECT_DIR, filename), 'r', encoding='utf-8') as handle:
        return json.load(handle)


def _reset_scene():
    # Idempotent builder: remove prior stage objects/collections, keep scene datablock.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection, do_unlink=True)
    global SET_COLLECTIONS, ANCHOR_REGISTRY
    SET_COLLECTIONS.clear()
    ANCHOR_REGISTRY.clear()


def _configure_scene(scene):
    scene.render.engine = 'BLENDER_EEVEE'  # Blender 5.x EEVEE Next engine id.
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = False
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.render.use_persistent_data = True
    scene.render.use_file_extension = True
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.render.filepath = '//frames/'
    if hasattr(scene, 'eevee'):
        scene.eevee.taa_render_samples = 64
        if hasattr(scene.eevee, 'use_shadows'):
            scene.eevee.use_shadows = True
    scene.view_settings.view_transform = 'Standard'
    try:
        scene.view_settings.look = 'Medium High Contrast'
    except Exception:
        pass
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.render.image_settings.color_depth = '8'
    scene.camera = None


def _create_camera(scene):
    data = bpy.data.cameras.new('Story_Camera_Data')
    camera = bpy.data.objects.new('Story_Camera', data)
    scene.collection.objects.link(camera)
    data.lens = 55
    data.sensor_fit = 'AUTO'
    data.clip_start = 0.1
    data.clip_end = 500.0
    scene.camera = camera
    return camera


def _make_sparks(collection, origin):
    mat = make_flat_material('MAT_FX_Sparks', (1.0, 0.44, 0.06, 1), emission=4.0)
    sparks = []
    origin = Vector(origin)
    # Static line geometry; only visibility is frame-driven, so no simulation state is involved.
    directions = [
        Vector((1.0, 0.0, 0.25)), Vector((-0.7, 0.0, 0.65)),
        Vector((0.45, 0.0, 1.0)), Vector((-0.15, 0.0, -1.0)),
        Vector((0.95, 0.0, -0.35)), Vector((-1.0, 0.0, -0.15)),
        Vector((0.35, 0.0, -0.8)), Vector((-0.35, 0.0, 0.9)),
        Vector((0.7, 0.0, 0.6)), Vector((-0.8, 0.0, -0.55)),
    ]
    for i, direction in enumerate(directions):
        direction.normalize()
        length = 0.25 + (i % 3) * 0.09
        obj = add_rod(f'FX_Spark_{i:02d}', collection, origin, origin + direction * length, 0.018, mat, 8)
        obj.hide_render = True
        obj.hide_viewport = True
        sparks.append(obj)
    return sparks


def build_scene():
    """Construct the whole scene from declarative module/data layers."""
    global SCENE, CAMERA, LIGHT_RIGS, PROPS, PROP_COLLECTIONS
    global CHARACTERS, CHAR_COLLECTIONS, FX_COLLECTION, SPARKS, SPARK_BASE_LOCATIONS, SHOTS, ACTING_EVENTS

    _reset_scene()
    scene = bpy.context.scene
    _configure_scene(scene)
    SCENE = scene

    build_all_sets()
    LIGHT_RIGS = build_lighting_rigs(scene)

    # Hero props are individual collections so their visibility can be controlled per beat.
    def prop_collection(key):
        col = ensure_collection('PROP_' + key)
        PROP_COLLECTIONS[key] = col
        return col

    anchors = ANCHOR_REGISTRY['workshop_night']
    PROPS = {
        'hero_loop': LoopTrackProp('hero_loop', prop_collection('hero_loop'), anchors['hero_loop'], radius=2.25),
        'rival_loop': LoopTrackProp('rival_loop', prop_collection('rival_loop'), anchors['rival_loop'], radius=2.25),
        'sledgehammer': SledgehammerProp('sledgehammer', prop_collection('sledgehammer'), (-3.80, 0.25, 1.50)),
        'test_dummy': TestDummyProp('test_dummy', prop_collection('test_dummy'), anchors['dummy_mark']),
        'turnbuckle': TurnbuckleCrankProp('turnbuckle', prop_collection('turnbuckle'), (3.2, 0.55, 2.55)),
        'builder_cart': CoasterCartProp('builder_cart', prop_collection('builder_cart')),
        'rival_cart': CoasterCartProp('rival_cart', prop_collection('rival_cart')),
    }
    bpy.context.view_layer.update()
    PROPS['builder_cart'].set_route_from_loop(PROPS['hero_loop'], approach=2.0, exit_length=3.8)
    PROPS['rival_cart'].set_route_from_loop(PROPS['rival_loop'], approach=1.0, exit_length=3.8)

    CHARACTERS = {}
    CHAR_COLLECTIONS = {}
    for key, builder_fn in [('builder', build_builder), ('rival', build_rival)]:
        col = ensure_collection('CHAR_' + key)
        CHAR_COLLECTIONS[key] = col
        start = anchors['builder_mark'] if key == 'builder' else anchors['rival_mark']
        CHARACTERS[key] = builder_fn(col, start)
    # Place the builder close enough to physically swing from the handle to the rail.
    CHARACTERS['builder'].set_anchor((-3.90, -0.30, 0.0))
    CHARACTERS['rival'].set_anchor((3.80, -0.10, 0.0))

    FX_COLLECTION = ensure_collection('FX_deterministic')
    SPARKS = _make_sparks(FX_COLLECTION, (-3.2, 0.25, 0.45))
    SPARK_BASE_LOCATIONS = {obj.name: obj.location.copy() for obj in SPARKS}

    CAMERA = _create_camera(scene)
    SHOTS = _load_json('shots.json')['shots']
    ACTING_EVENTS = _load_json('acting.json')['events']

    # Store project settings on the scene for inspection/render-farm tooling.
    scene['story_title'] = "Why Roller Coasters Don't Fly Off The Tracks"
    scene['story_architecture'] = '4-layer: look/assets | scene/rigs | story data | deterministic evaluation'
    scene['frame_count'] = FRAME_END
    scene['frame_rate'] = FPS
    scene['frame_state_function'] = 'apply_frame_actions(f)'
    apply_frame_actions(FRAME_START)
    return scene


def _active_shot(frame):
    for shot in SHOTS:
        if shot['start_frame'] <= frame <= shot['end_frame']:
            return shot
    return SHOTS[-1]


def _ease_value(easing, t):
    t = max(0.0, min(1.0, t))
    if easing == 'ease_in_out':
        return t * t * (3.0 - 2.0 * t)
    if easing == 'ease_out':
        return 1.0 - (1.0 - t) ** 3
    return t


def _event_value(event, frame):
    start = int(event['start_frame'])
    end = int(event['end_frame'])
    if frame < start:
        return None
    raw = 1.0 if end <= start else (frame - start) / float(end - start)
    t = _ease_value(event.get('easing', 'linear'), raw)
    return float(event.get('from', 0.0)) + (float(event.get('to', 1.0)) - float(event.get('from', 0.0))) * t


def _set_collection_visible(collection, visible):
    collection.hide_render = not visible
    collection.hide_viewport = not visible


def _reset_hand_targets(character):
    defaults = {'L': (-1.05, 0.0, 1.12), 'R': (1.05, 0.0, 1.12)}
    bpy.context.view_layer.update()
    for side, local in defaults.items():
        world = character.root.matrix_world @ Vector(local)
        character.set_hand_target(side, world)


def _set_actor_ride_parent(character, cart, enabled, seat_offset=(0.0, -0.04, 0.48)):
    if enabled:
        character.root.parent = cart.root
        character.root.location = Vector(seat_offset)
        character.root.rotation_euler = (0.0, 0.0, 0.0)
        character.root.scale = (0.56, 0.56, 0.56)
    else:
        if character.root.parent is not None:
            character.root.parent = None
        character.root.scale = (1.0, 1.0, 1.0)
        if character.name == 'builder':
            character.root.location = Vector((-3.90, -0.30, 0.0))
        else:
            character.root.location = Vector((3.80, -0.10, 0.0))
        character.root.rotation_euler = (0.0, 0.0, 0.0)


def apply_frame_actions(f):
    """Evaluate all story state from frame f only; safe for parallel/out-of-order renders."""
    if SCENE is None or not PROPS:
        raise RuntimeError('Call build_scene() before apply_frame_actions(f).')
    frame = max(FRAME_START, min(FRAME_END, int(f)))
    scene = SCENE
    scene.frame_set(frame)

    shot = _active_shot(frame)
    set_active_set(shot['active_set'])
    apply_lighting_mood(scene, shot['lighting_mood'], LIGHT_RIGS)
    cam = shot['camera']
    CAMERA.location = Vector(cam['position'])
    look_at(CAMERA, cam['look_at'])
    CAMERA.data.lens = float(cam.get('lens_mm', 55))

    # Frame-deterministic visibility for each modular prop collection.
    _set_collection_visible(PROP_COLLECTIONS['hero_loop'], True)
    _set_collection_visible(PROP_COLLECTIONS['rival_loop'], frame >= 211)
    _set_collection_visible(PROP_COLLECTIONS['sledgehammer'], 457 <= frame <= 576)
    _set_collection_visible(PROP_COLLECTIONS['test_dummy'], (337 <= frame <= 417) or (1522 <= frame <= 1563))
    _set_collection_visible(PROP_COLLECTIONS['turnbuckle'], 631 <= frame <= 789)
    _set_collection_visible(PROP_COLLECTIONS['builder_cart'], frame >= 1018)
    _set_collection_visible(PROP_COLLECTIONS['rival_cart'], frame >= 958)

    # Reset every channel before applying the active timeline curves.
    for prop in PROPS.values():
        prop.reset_channels()
    for character in CHARACTERS.values():
        _reset_hand_targets(character)
        character.set_emotion('neutral')

    # Channel evaluation: completed events hold their terminal value; future events do nothing.
    for event in ACTING_EVENTS:
        if event['verb'] != 'operate':
            continue
        if frame < int(event['start_frame']):
            continue
        prop = PROPS[event['prop']]
        value = _event_value(event, frame)
        prop.set_channel(event['channel'], value)

    # Update dynamic track meshes and dependent Bezier routes before placing carts.
    PROPS['hero_loop'].apply_channels()
    PROPS['rival_loop'].apply_channels()
    bpy.context.view_layer.update()
    PROPS['builder_cart'].set_route_from_loop(PROPS['hero_loop'], approach=2.0, exit_length=3.8)
    PROPS['rival_cart'].set_route_from_loop(PROPS['rival_loop'], approach=1.0, exit_length=3.8)
    for key in ('sledgehammer', 'test_dummy', 'turnbuckle'):
        PROPS[key].apply_channels()
    PROPS['builder_cart'].apply_channels()
    PROPS['rival_cart'].apply_channels()

    # Seat the cutout performers on their own cars only during their ride intervals.
    _set_actor_ride_parent(CHARACTERS['builder'], PROPS['builder_cart'], 1018 <= frame <= 1794)
    _set_actor_ride_parent(CHARACTERS['rival'], PROPS['rival_cart'], 958 <= frame <= 1887)
    bpy.context.view_layer.update()
    _reset_hand_targets(CHARACTERS['builder'])
    _reset_hand_targets(CHARACTERS['rival'])

    # Hold/clasp physically connect the IK target to the requested prop socket.
    for event in ACTING_EVENTS:
        if event['verb'] not in ('hold', 'clasp'):
            continue
        if not (int(event['start_frame']) <= frame <= int(event['end_frame'])):
            continue
        char = CHARACTERS[event['actor']]
        prop = PROPS[event['prop']]
        bpy.context.view_layer.update()
        socket_world = prop.socket_world(event['socket'])
        char.set_hand_target(event['hand'], socket_world)

    # Emotion clips drive pose and face shape keys with no dependence on prior frame.
    for event in ACTING_EVENTS:
        if event['verb'] == 'emotion' and int(event['start_frame']) <= frame <= int(event['end_frame']):
            CHARACTERS[event['actor']].set_emotion(event['emotion'])

    # Deterministic impacts: short spark flash and final cart jolt.
    spark_active = any(
        e['verb'] == 'impact' and e.get('effect') == 'sparks'
        and int(e['start_frame']) <= frame <= int(e['end_frame'])
        for e in ACTING_EVENTS
    )
    if spark_active:
        impact_center = PROPS['hero_loop'].socket_world('hammer_target')
        base_center = Vector((-3.2, 0.25, 0.45))
        delta = impact_center - base_center
    else:
        delta = Vector((0, 0, 0))
    for spark in SPARKS:
        spark.location = SPARK_BASE_LOCATIONS[spark.name] + delta
        spark.hide_render = not spark_active
        spark.hide_viewport = not spark_active
    rival_impact = next((e for e in ACTING_EVENTS if e['id'] == 'rival_bottom_impact'), None)
    if rival_impact and rival_impact['start_frame'] <= frame <= rival_impact['end_frame']:
        t = (frame - rival_impact['start_frame']) / max(1.0, rival_impact['end_frame'] - rival_impact['start_frame'])
        PROPS['rival_cart'].root.location.z += 0.06 * math.sin(t * math.pi * 8.0) * (1.0 - t)

    # Frame markers are useful in the timeline and survive .blend saves.
    scene.frame_set(frame)
    scene['current_story_beat'] = shot['beat']
    return shot


def render_frame(frame, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    apply_frame_actions(frame)
    SCENE.render.filepath = os.path.join(output_dir, f'{int(frame):04d}.png')
    SCENE.render.use_compositing = False
    bpy.ops.render.render(write_still=True)
    return SCENE.render.filepath


def _parse_cli():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description='Render Why Roller Coasters Don’t Fly Off The Tracks')
    parser.add_argument('--frame', type=int, default=None, help='Render exactly one frame.')
    parser.add_argument('--start', type=int, default=1, help='First frame inclusive.')
    parser.add_argument('--end', type=int, default=1887, help='Last frame inclusive.')
    parser.add_argument('--step', type=int, default=1, help='Frame stride for distributed rendering.')
    parser.add_argument('--output', default='//frames', help='PNG output directory.')
    parser.add_argument('--blend-output', default='//roller_coaster_story.blend', help='Saved Blender scene path.')
    parser.add_argument('--build-only', action='store_true', help='Build and save the .blend without rendering.')
    parser.add_argument('--no-save', action='store_true', help='Do not save the .blend file.')
    return parser.parse_args(argv)


def main():
    args = _parse_cli()
    scene = build_scene()
    output_dir = bpy.path.abspath(args.output)
    blend_path = bpy.path.abspath(args.blend_output)
    if not args.no_save:
        os.makedirs(os.path.dirname(blend_path) or '.', exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    if args.build_only:
        print(f'[story-director] Built scene: {blend_path}')
        return
    if args.frame is not None:
        frames = [args.frame]
    else:
        step = max(1, args.step)
        frames = range(max(FRAME_START, args.start), min(FRAME_END, args.end) + 1, step)
    for frame in frames:
        path = render_frame(frame, output_dir)
        print(f'[story-director] rendered frame {frame}: {path}')


if __name__ == '__main__':
    main()
