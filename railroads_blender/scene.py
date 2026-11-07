"""Railroads Scene Integrator: Builds the 65.26-second film with dynamic prop action channels.
blender -b -P scene.py -- frames OUTDIR START END [SAMPLES]
"""
import bpy
import sys
import os
import json
import math
from mathutils import Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))

import look
import sets
import props
import chars

# CLI Arguments
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['frames', os.path.join(HERE, 'render'), '0', '10', '4']
MODE = args[0]
OUT = args[1]
START = int(args[2])
END = int(args[3])
SAMPLES = int(args[4]) if len(args) > 4 else 4

# Load timeline
SHOTS = json.load(open(os.path.join(HERE, 'shots.json')))
ACTING = json.load(open(os.path.join(HERE, 'acting.json')))
TOTAL_FRAMES = SHOTS[-1]['f_out']

# Reset Blender scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start = 0
sc.frame_end = TOTAL_FRAMES

# Setup look & lighting
look.setup_render(sc)
sun_ob, fill_ob, rim_ob = look.setup_lighting(sc.collection)
look.setup_compositor(sc)

# Build Sets
S = sets.build_sets()

# Build Hero Props (with PropSpec interactive sockets and channels)
P = {}
P['hacksaw'] = props.build_hacksaw(S['canyon_track']['collection'], "hacksaw", loc=(sets.ORIGIN['canyon_track'][0] - 0.45, 0.0, 0.20))
P['rail_joint'] = props.build_rail_joint(S['canyon_track']['collection'], "rail_joint", loc=sets.ORIGIN['canyon_track'])
P['wrench'] = props.build_wrench(S['canyon_track']['collection'], "wrench", loc=(sets.ORIGIN['canyon_track'][0] - 0.7, 1.2, 0.35))
P['blueprint'] = props.build_blueprint(S['canyon_track']['collection'], "blueprint", loc=(sets.ORIGIN['canyon_track'][0] + 0.7, 1.2, 0.45))
P['thermometer'] = props.build_thermometer(S['desert_buckle']['collection'], "thermometer", loc=(sets.ORIGIN['desert_buckle'][0] + 1.8, -2.0, 0.5))
P['buckling_track'] = props.build_buckling_track(S['desert_buckle']['collection'], "buckling_track", loc=sets.ORIGIN['desert_buckle'])

# Build Characters
CH = {}
CH['engineer'] = chars.make_character(S['canyon_track']['collection'], "engineer", "char_engineer", loc=(sets.ORIGIN['canyon_track'][0] - 0.55, 0.0, 0.12))
CH['boss'] = chars.make_character(S['canyon_track']['collection'], "boss", "char_boss", loc=(sets.ORIGIN['canyon_track'][0] + 0.65, 0.3, 0.12))

# Setup Camera
cam = bpy.data.objects.new('Camera_Main', bpy.data.cameras.new('Camera_Main'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.clip_end = 500
cam.data.clip_start = 0.05
cam.data.sensor_width = 36
cam.data.sensor_fit = 'HORIZONTAL'

# Coordinate helper
def W(set_id, local_xyz):
    ox, oy, oz = sets.ORIGIN[set_id]
    return Vector((ox + local_xyz[0], oy + local_xyz[1], oz + local_xyz[2]))

def lookat_euler(pos, tgt, roll_deg):
    dir_vec = tgt - pos
    if dir_vec.length < 1e-4:
        dir_vec = Vector((0, 1, 0))
    q = dir_vec.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.radians(roll_deg))
    return q.to_euler()

# Keyframe Camera across all 28 shots
prev_e = None
for s in SHOTS:
    sid = s['set']
    f0, f1 = s['f_in'], s['f_out']
    c_start = s['camera'][0]
    c_end = s['camera'][-1]

    pos0 = W(sid, c_start['pos'])
    tgt0 = W(sid, c_start['target'])
    e0 = lookat_euler(pos0, tgt0, c_start.get('roll_deg', 0.0))
    if prev_e:
        e0.make_compatible(prev_e)

    pos1 = W(sid, c_end['pos'])
    tgt1 = W(sid, c_end['target'])
    e1 = lookat_euler(pos1, tgt1, c_end.get('roll_deg', 0.0))
    e1.make_compatible(e0)
    prev_e = e1

    # Keyframe start
    cam.location = pos0
    cam.rotation_euler = e0
    cam.data.lens = c_start.get('lens', 35)
    cam.keyframe_insert('location', frame=f0)
    cam.keyframe_insert('rotation_euler', frame=f0)
    cam.data.keyframe_insert('lens', frame=f0)

    # Keyframe end
    cam.location = pos1
    cam.rotation_euler = e1
    cam.data.lens = c_end.get('lens', 35)
    cam.keyframe_insert('location', frame=f1 - 1)
    cam.keyframe_insert('rotation_euler', frame=f1 - 1)
    cam.data.keyframe_insert('lens', frame=f1 - 1)

# Set visibility toggle per shot
def _vis(scene, *a):
    f = scene.frame_current
    cur = next((x['set'] for x in SHOTS if x['f_in'] <= f < x['f_out']), SHOTS[-1]['set'])
    for sid, d in S.items():
        d['collection'].hide_render = (sid != cur)

bpy.app.handlers.frame_change_pre.append(_vis)

# ---------------------------------------------------------------------------
# Dynamic Action & Prop Operation Execution
# ---------------------------------------------------------------------------
def apply_frame_actions(f):
    for a in ACTING:
        if a['f_in'] <= f <= a['f_out']:
            act = a['act']
            span = max(1, a['f_out'] - a['f_in'])
            progress = (f - a['f_in']) / span
            
            if act == 'hold':
                char_obj = CH.get(a['char'])
                prop_obj = P.get(a['prop'])
                socket = prop_obj.grip_sockets.get(a.get('socket', 'hand'))
                if char_obj and socket:
                    char_obj.hold_socket(f, socket, hand=a.get('hand', 'right'))
                    
            elif act == 'operate':
                prop_obj = P.get(a['prop'])
                if prop_obj:
                    v0 = a.get('from', 0.0)
                    v1 = a.get('to', 1.0)
                    current_val = v0 + (v1 - v0) * progress
                    prop_obj.set_channel(a['channel'], current_val)
                    
            elif act == 'emotion':
                char_obj = CH.get(a['char'])
                if char_obj:
                    char_obj.set_emotion(f, a.get('color'))

# ---------------------------------------------------------------------------
# Frame Rendering Execution
# ---------------------------------------------------------------------------
os.makedirs(OUT, exist_ok=True)
sc.render.image_settings.file_format = 'PNG'

print(f"=====================================================")
print(f"Rendering Railroads frames {START} to {END} (samples={SAMPLES})")
print(f"=====================================================")

for f in range(START, END):
    sc.frame_set(f)
    apply_frame_actions(f)
    out_file = os.path.join(OUT, f"f{f:04d}.png")
    sc.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print(f"Rendered frame {f:04d} -> {out_file}")

print("Slice render complete!")
