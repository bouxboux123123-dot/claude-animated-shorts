"""Pink Prison Integrator: builds the 65-second film from lib/* + shots.json.
blender -b -P scene.py -- frames OUTDIR A B [SAMPLES]
blender -b -P scene.py -- gate OUTDIR
"""
import bpy, sys, os, json, math
from mathutils import Vector, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))
import look, sets, chars

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['frames', os.path.join(HERE, 'render'), '0', '10', '4']
MODE = args[0]
OUT = args[1]
SAMPLES = 4

SHOTS = json.load(open(os.path.join(HERE, 'shots.json')))
END = SHOTS[-1]['f_out']

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 0, END
look.setup_render(sc)
if os.environ.get('NATIVE'):
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100

S, P = sets.build_sets()
A = {sid: d['anchors'] for sid, d in S.items()}


def W(set_id, v):
    """shots position -> world Vector"""
    if isinstance(v, dict):
        a = A[set_id][v['anchor']].location
        o = v.get('off', [0, 0, 0])
        return Vector((a.x + o[0], a.y - o[1], a.z + o[2]))
    ox = sets.ORIGIN[set_id][0]
    return Vector((ox + v[0], -v[1], v[2]))


def constant(idb, names=None):
    for fc in chars._fcurves(idb):
        if names is None or fc.data_path in names:
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'


# ---------------------------------------------------------------- Characters
CH = {
    'guard': chars.make_char('guard', 'Guard'),
    'scientist': chars.make_char('scientist', 'Scientist'),
    'artisan': chars.make_char('artisan', 'Artisan'),
    'inmate': chars.make_char('inmate', 'Inmate'),
}

for c in CH.values():
    c.place(-5, (-300, 0, 0), 0)
    c.pose(-5, 'idle')
    c.face(-5, 'neutral')

# ---------------------------------------------------------------- Camera
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.clip_end = 400
cam.data.clip_start = 0.05
cam.data.sensor_width = 36
cam.data.sensor_fit = 'HORIZONTAL'
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 5.6


# ---------------------------------------------------------------- Set visibility
def _vis(scene, *a):
    f = scene.frame_current
    cur = next((x['set'] for x in SHOTS if x['f_in'] <= f < x['f_out']), SHOTS[-1]['set'])
    for sid, d in S.items():
        d['collection'].hide_render = (sid != cur)

bpy.app.handlers.frame_change_pre.append(_vis)

# ---------------------------------------------------------------- Lighting & Moods
runs = []
for s_ in SHOTS:
    key = (s_['moodkey'], s_['set'])
    if runs and runs[-1][0] == key:
        runs[-1][2] = s_['f_out'] - 1
    else:
        runs.append([key, s_['f_in'], s_['f_out'] - 1])

comp = look.setup_compositor(sc)
for key, f0, f1 in runs:
    look.apply_mood(sc, key[0], f0, f1, fill_x=sets.ORIGIN[key[1]][0])

for idb in (bpy.data.worlds['LOOK_World'], bpy.data.worlds['LOOK_World'].node_tree, comp,
            bpy.data.objects['LOOK_Sun'], bpy.data.objects['LOOK_Fill'], bpy.data.objects['LOOK_Lamp'],
            bpy.data.objects['LOOK_Sun'].data, bpy.data.objects['LOOK_Fill'].data, bpy.data.objects['LOOK_Lamp'].data):
    for fc in chars._fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'


# ---------------------------------------------------------------- Camera Choreography & Lookat
def lookat_euler(pos, tgt, roll_deg):
    dir_vec = tgt - pos
    if dir_vec.length < 1e-4:
        dir_vec = Vector((0, 1, 0))
    q = dir_vec.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.radians(roll_deg))
    return q.to_euler()


prev_e = None
for s in SHOTS:
    sid = s['set']
    f0, f1 = s['f_in'], s['f_out']
    c_start = s['camera'][0]
    c_end = s['camera'][-1]

    pos0 = W(sid, c_start['pos'])
    tgt0 = W(sid, c_start['target'])
    e0 = lookat_euler(pos0, tgt0, c_start.get('roll_deg', 0.0))
    if prev_e: e0.make_compatible(prev_e)

    pos1 = W(sid, c_end['pos'])
    tgt1 = W(sid, c_end['target'])
    e1 = lookat_euler(pos1, tgt1, c_end.get('roll_deg', 0.0))
    e1.make_compatible(e0)
    prev_e = e1

    # Keyframe start
    cam.location = pos0
    cam.rotation_euler = e0
    cam.data.lens = c_start.get('lens', 50)
    cam.data.dof.focus_distance = (tgt0 - pos0).length
    cam.keyframe_insert('location', frame=f0)
    cam.keyframe_insert('rotation_euler', frame=f0)
    cam.data.keyframe_insert('lens', frame=f0)
    cam.data.dof.keyframe_insert('focus_distance', frame=f0)

    # Keyframe end
    cam.location = pos1
    cam.rotation_euler = e1
    cam.data.lens = c_end.get('lens', 50)
    cam.data.dof.focus_distance = (tgt1 - pos1).length
    cam.keyframe_insert('location', frame=f1 - 1)
    cam.keyframe_insert('rotation_euler', frame=f1 - 1)
    cam.data.keyframe_insert('lens', frame=f1 - 1)
    cam.data.dof.keyframe_insert('focus_distance', frame=f1 - 1)

# ---------------------------------------------------------------- Impact Shakes
# Arm wrestling slam impact shake (frames 1040 to 1048)
for f in range(1040, 1049):
    sc.frame_set(f)
    decay = math.exp(-(f - 1040) / 2.5)
    sign = 1 if f % 2 == 0 else -1
    cam.location.x += sign * 0.035 * decay
    cam.location.z += sign * 0.02 * decay
    cam.keyframe_insert('location', frame=f)

# Bench tearing violent shake (frames 1490 to 1570)
for f in range(1490, 1571):
    sc.frame_set(f)
    cycle = (f - 1490) % 6
    sign = 1 if cycle < 3 else -1
    cam.location.x += sign * 0.018
    cam.location.z += math.sin(f * 0.6) * 0.012
    cam.keyframe_insert('location', frame=f)


# ---------------------------------------------------------------- Character Actions
char_state = {k: {'set': None, 'loc': None, 'f': -99, 'pose': 'idle'} for k in CH}

for s in SHOTS:
    sid = s['set']
    acts = sorted(s.get('actions', []), key=lambda a: a['f'])
    for a in acts:
        f = a['f']
        ck = a['char']
        act = a['act']
        ar = a['args']
        if ck not in CH: continue
        c = CH[ck]
        st = char_state[ck]

        if act == 'place':
            loc = W(sid, ar['loc'])
            rz = ar.get('rot_z', 0.0)
            if st['loc'] is not None and f > st['f'] + 1:
                c.place(f - 1, st['loc'], st.get('rot', 0.0))
            c.place(f, loc, rz)
            st.update(set=sid, loc=loc, f=f, rot=rz)
        elif act == 'pose':
            c.pose(f, ar['name'])
            st['pose'] = ar['name']
        elif act == 'face':
            c.face(f, ar['name'])

# Constant interpolation on character cuts
for c in CH.values():
    constant(c.root, ('location', 'rotation_euler'))

# ---------------------------------------------------------------- Render Execution
sc.eevee.taa_render_samples = SAMPLES
sc.render.use_motion_blur = False
sc.render.filepath = OUT
sc.render.image_settings.file_format = 'PNG'

def render_frame(f, path):
    sc.frame_set(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

os.makedirs(OUT, exist_ok=True)

if MODE == 'gate':
    for s in SHOTS:
        fm = (s['f_in'] + s['f_out']) // 2
        render_frame(fm, os.path.join(OUT, s['id'] + '.png'))
        print(f"Rendered gate still for {s['id']} at frame {fm}")
elif MODE == 'frames':
    a = int(args[2])
    b = int(args[3])
    if len(args) > 4:
        sc.eevee.taa_render_samples = int(args[4])
    print(f"Rendering frames {a} to {b} with {sc.eevee.taa_render_samples} samples...")
    for f in range(a, b):
        render_frame(f, os.path.join(OUT, 'f%04d.png' % f))
    print(f"Finished rendering frames {a} to {b}.")
