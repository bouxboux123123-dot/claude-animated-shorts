"""Headless Blender scene build and renderer for the roller-coaster short.

Usage:
  blender -b --python scene.py -- --build-only
  blender -b --python scene.py -- --render --output //rollercoaster_short.mp4
  blender -b --python scene.py -- --frame 900 --output //frame_0900.png

Frame state is always recomputed from its frame number by apply_frame_actions(f).
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

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from lib.look import configure_render, activate_mood, LIGHT_RIGS
from lib.props import LoopTrackProp, SledgehammerProp, TestDummyProp, TurnbuckleCrankProp, CoasterCartProp, ToyRoadsterProp
from lib.sets import build_all_sets
from lib.chars import CardCharacter

with (HERE / "shots.json").open(encoding="utf-8") as f:
    SHOTS = json.load(f)["shots"]
with (HERE / "acting.json").open(encoding="utf-8") as f:
    ACTING = json.load(f)["actions"]

STATE = {}


def _clear_scene():
    LIGHT_RIGS.clear()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)
    bpy.context.scene.world = bpy.data.worlds.new("Roller-coaster story world")


def _create_camera():
    data = bpy.data.cameras.new("Story camera")
    camera = bpy.data.objects.new("Story camera", data)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    return camera


def _make_crowd(center):
    """Small faceless cutout spectators to establish a fairground queue."""
    cx, cy, _ = center
    crowd = []
    colors = ((0.17,0.30,0.47,1),(0.67,0.20,0.14,1),(0.82,0.59,0.19,1),(0.27,0.42,0.27,1))
    from lib.look import toon_material, add_outline
    for i in range(11):
        x = cx - 11 + i * 2.0
        y = -4.1 - (i % 2) * 0.55
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1, location=(x,y,1.25))
        body = bpy.context.object
        body.name = f"Fair crowd | paper body {i+1:02d}"
        body.scale = (0.36, 0.12, 0.72)
        body.data.materials.append(toon_material(f"Crowd coat {i%4}", colors[i%4]))
        add_outline(body, 0.018)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1, location=(x,y-0.02,2.15))
        head = bpy.context.object
        head.name = f"Fair crowd | paper head {i+1:02d}"
        head.scale = (0.35,0.13,0.38)
        head.data.materials.append(toon_material("Crowd | warm skin", (0.86,0.59,0.40,1)))
        add_outline(head, 0.015)
        crowd.extend((body,head))
    return crowd


def build_scene(samples=4, res=None):
    _clear_scene()
    scene = bpy.context.scene
    w, h = 1080, 1920
    if res:
        try:
            parts = res.lower().split("x")
            w, h = int(parts[0]), int(parts[1])
        except Exception:
            pass
    configure_render(scene, width=w, height=h, samples=samples)
    anchors = build_all_sets()
    camera = _create_camera()

    # Hero props: all are PropSpec subclasses and expose the requested channels/sockets.
    props = {
        "loop_workshop": LoopTrackProp("LoopTrack workshop", (0, 0.6, 0), radius=3.05),
        "hammer_workshop": SledgehammerProp("Sledgehammer workshop", (-1.3,-0.5,1.2)),
        "test_dummy_workshop": TestDummyProp("TestDummy workshop", (2.4,-0.8,0)),
        "crank_workshop": TurnbuckleCrankProp("TurnbuckleCrank workshop", (3.2,0.0,2.2)),
        "loop_fairground": LoopTrackProp("LoopTrack fairground", (100,0.8,0), radius=3.05),
        "cart_builder_fairground": CoasterCartProp("CoasterCart builder fairground", (100,0.8,0)),
        "cart_rival_fairground": CoasterCartProp("CoasterCart rival fairground", (103,0.8,0)),
        "loop_builder": LoopTrackProp("LoopTrack builder climax", (196,0.8,0), radius=3.05),
        "loop_rival": LoopTrackProp("LoopTrack rival climax", (204,0.8,0), radius=3.05),
        "test_dummy_climax": TestDummyProp("TestDummy climax", (202, -0.8, 0)),
        "cart_builder_climax": CoasterCartProp("CoasterCart builder climax", (196,0.8,0)),
        "cart_rival_climax": CoasterCartProp("CoasterCart rival climax", (204,0.8,0)),
        "analogy_car": ToyRoadsterProp("Analogy roadster", (200,-3.0,0))
    }
    characters = {}
    for set_name in ("workshop_night", "fairground_dawn", "coaster_climax"):
        for role in ("builder", "rival"):
            actor_id = f"{role}_{set_name}"
            characters[actor_id] = CardCharacter(actor_id.replace("_", " ").title(), anchors[set_name][role], role)
    _make_crowd(anchors["fairground_dawn"]["center"])

    # A small, unlabelled wooden cash box makes the "cost him everything" beat legible.
    from lib.look import toon_material, add_outline
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-3.0, 0.7, 0.65))
    box = bpy.context.object
    box.name = "Workshop | empty coin box"
    box.dimensions = (0.8,0.55,0.42)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    box.data.materials.append(toon_material("Cash box | dark walnut", (0.24,0.12,0.06,1)))
    add_outline(box, 0.02)

    STATE.clear()
    STATE.update(scene=scene, camera=camera, anchors=anchors, props=props, characters=characters)
    scene["story_title"] = "Why Roller Coasters Don't Fly Off The Tracks"
    scene["story_frames"] = 1887
    scene["story_fps"] = 30
    scene.render.use_compositing = False
    _register_handlers()
    apply_frame_actions(1)
    scene.frame_set(1)
    return scene


def _shot_at(t):
    for shot in SHOTS:
        if shot["start"] <= t < shot["end"]:
            return shot
    return SHOTS[-1]


def _ease(t, curve="smoothstep"):
    t = max(0.0, min(1.0, t))
    if curve == "linear":
        return t
    if curve == "ease_in":
        return t*t
    if curve == "ease_out":
        return 1-(1-t)*(1-t)
    return t*t*(3-2*t)


def _interpolate_action(action, t):
    start, end = float(action["start"]), float(action["end"])
    a, b = float(action.get("from", 0)), float(action.get("to", 0))
    if t <= start:
        return a
    if t >= end:
        return b
    u = (t-start) / max(1e-8, end-start)
    if "peak" in action and action.get("verb") == "impact":
        peak = float(action["peak"])
        if u < 0.5:
            return a + (peak-a) * _ease(u*2)
        return peak + (b-peak) * _ease((u-0.5)*2)
    if action.get("repeats"):
        phase = (u * int(action["repeats"])) % 1.0
        return a + (b-a) * math.sin(math.pi*phase)
    return a + (b-a) * _ease(u, action.get("curve", "smoothstep"))


def _prop_key(alias, set_name):
    if alias == "cart_builder":
        return "cart_builder_fairground" if set_name == "fairground_dawn" else "cart_builder_climax"
    if alias == "cart_rival":
        return "cart_rival_fairground" if set_name == "fairground_dawn" else "cart_rival_climax"
    return alias


def _character_lean(action):
    if "lean" in action:
        return float(action["lean"])
    emotion = action.get("emotion", action.get("value", ""))
    mapping = {"strained":0.10,"wonder":-0.03,"smug":-0.08,"deflated":-0.08,"suspicious":0.08,
               "urgent":0.13,"determined":0.08,"doubtful":-0.05,"sheepish":-0.07,"effort":0.10,
               "sly":0.12,"proud":-0.08,"showoff":-0.10,"nervous":0.08,"alarm":0.16,
               "confident":-0.06,"relief":-0.04,"laugh_then_sneak":0.12}
    return mapping.get(str(emotion), 0.0)


def apply_frame_actions(f, set_frame=True):
    """Rebuild every animated control as a deterministic function of frame f."""
    if not STATE:
        return
    f = max(0, min(1886, int(f)))
    t = f / 30.0
    scene = STATE["scene"]
    shot = _shot_at(t)
    set_name = shot["set"]
    center = Vector(STATE["anchors"][set_name]["center"])
    activate_mood(scene, STATE["anchors"][set_name]["mood"])

    # Start from channel defaults every frame, then evaluate all timeline keys.
    channel_values = {key: dict(prop.channel_defaults) for key, prop in STATE["props"].items()}
    for action in ACTING:
        if "channel" not in action:
            continue
        alias = action.get("target", action.get("actor"))
        key = _prop_key(alias, set_name)
        if key not in channel_values:
            continue
        channel = action["channel"]
        if channel not in channel_values[key]:
            continue
        if t >= float(action["start"]):
            channel_values[key][channel] = _interpolate_action(action, t)
    # Inactive duplicate carts remain parked at their start; only current-set cart is driven.
    for key, prop in STATE["props"].items():
        for channel, value in channel_values[key].items():
            prop.set_channel(channel, value)
        prop.update(f)

    # Character poses reset to a neutral planted pose, then active cues drive IK targets.
    for actor_id, character in STATE["characters"].items():
        character.root.rotation_euler[1] = 0.0
        character.set_hand_target("left", (-0.96,-0.12,1.85))
        character.set_hand_target("right", (0.96,-0.12,1.85))
    bpy.context.view_layer.update()
    for action in ACTING:
        if not (float(action["start"]) <= t < float(action["end"])):
            continue
        actor_id = action.get("actor", "")
        character = STATE["characters"].get(actor_id)
        if character:
            if action["verb"] == "emotion":
                value = action.get("lean", None)
                character.set_emotion(_character_lean(action) if value is None else value)
            if action["verb"] in ("clasp", "hold") and action.get("target"):
                key = _prop_key(action["target"], set_name)
                prop = STATE["props"].get(key)
                socket = prop.sockets.get(action.get("socket", "")) if prop else None
                if socket:
                    local = character.root.matrix_world.inverted() @ socket.matrix_world.translation
                    hands = action.get("hands", ["right"])
                    for idx, hand in enumerate(hands):
                        offset = Vector(((-0.12 if idx == 0 else 0.12), 0, 0)) if len(hands)>1 else Vector((0,0,0))
                        character.set_hand_target(hand, local + offset)

    # Shot camera uses world-space set anchors with a gentle deterministic creep.
    camera = STATE["camera"]
    cam = shot["camera"]
    u = max(0.0, min(1.0, (t-shot["start"]) / max(1e-5, shot["end"]-shot["start"])))
    pos = center + Vector(cam["from"])
    look = center + Vector(cam["to"])
    pos += Vector((0.08*math.sin(u*math.pi), 0.10*u, 0.06*u))
    camera.location = pos
    camera.rotation_euler = (look-camera.location).to_track_quat("-Z", "Y").to_euler()
    fov = math.radians(float(cam.get("fov", 42)))
    camera.data.lens = max(18.0, min(70.0, 18.0 / math.tan(fov/2)))
    if set_frame:
        scene.frame_set(f)


def _render_pre(scene):
    apply_frame_actions(scene.frame_current)


def _frame_pre(scene):
    # Full per-frame update, but do not call frame_set from inside this handler.
    if STATE:
        apply_frame_actions(scene.frame_current, set_frame=False)


def _register_handlers():
    for handler in (bpy.app.handlers.render_pre, bpy.app.handlers.frame_change_pre):
        for old in list(handler):
            if getattr(old, "__name__", "") in ("_render_pre", "_frame_pre"):
                handler.remove(old)
    bpy.app.handlers.render_pre.append(_render_pre)
    bpy.app.handlers.frame_change_pre.append(_frame_pre)


def render_cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--render", action="store_true", help="Render the entire animation")
    parser.add_argument("--frame", type=int, help="Render one frame as an image")
    parser.add_argument("--frames", default=None, help="Frame range to render, e.g. 0-94 or 95-189")
    parser.add_argument("--out", default=None, help="Output directory for rendered frames")
    parser.add_argument("--samples", type=int, default=4, help="EEVEE Next TAA samples")
    parser.add_argument("--res", default=None, help="Resolution WxH, e.g. 1080x1920")
    parser.add_argument("--no-save", action="store_true", help="Do not save blend file")
    parser.add_argument("--output", default="//rollercoaster_short.mp4")
    parser.add_argument("--blend-output", default="//rollercoaster_short.blend")
    parser.add_argument("--preview", action="store_true", help="Use 540x960 preview resolution")
    args, _ = parser.parse_known_args(argv)
    res = "540x960" if args.preview else args.res
    scene = build_scene(samples=args.samples, res=res)
    scene.render.filepath = args.output
    if (args.build_only or args.render or args.frame is not None) and not args.no_save:
        bpy.ops.wm.save_as_mainfile(filepath=args.blend_output)
    if args.frames is not None:
        parts = args.frames.split("-")
        start_f, end_f = int(parts[0]), int(parts[1])
        out_dir = args.out or "frames"
        os.makedirs(out_dir, exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        for f in range(start_f, end_f + 1):
            apply_frame_actions(f)
            scene.render.filepath = os.path.join(out_dir, f"frame_{f:05d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"Rendered frame {f}", flush=True)
    elif args.frame is not None:
        apply_frame_actions(args.frame)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = args.output if args.output.lower().endswith(".png") else args.output + ".png"
        bpy.ops.render.render(write_still=True)
    elif args.render:
        scene.render.image_settings.file_format = "FFMPEG"
        scene.frame_start, scene.frame_end = 1, 1887
        # frame_change_pre evaluates every frame; render_pre reapplies the current state before render.
        bpy.ops.render.render(animation=True)
    else:
        scene.render.filepath = args.output
        print("Scene built. Use --render for animation or --frame N for a still.")
    return scene


if __name__ == "__main__":
    # Blender passes application arguments after '--'.
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render_cli(args)
