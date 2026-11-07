"""SETS module (Pink Prison Edition): Corridor, Mix Bench, Paint Wall, Pink Cell,
Arm Wrestle, Night Station, Blackboard sets + props. Blender 5.2, units = metres, Z up.
"""
import math, os, random
try:
    import bpy, bmesh
    from mathutils import Vector, Euler, Quaternion
except ImportError:
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.normpath(os.path.join(HERE, '..', 'tex'))
ORIGIN = {
    'corridor': (0, 0, 0),
    'mix_bench': (100, 0, 0),
    'paint_wall': (200, 0, 0),
    'pink_cell': (300, 0, 0),
    'arm_wrestle': (400, 0, 0),
    'night_station': (500, 0, 0),
    'blackboard': (600, 0, 0),
}

try:
    from . import look as _look
except Exception:
    try:
        import look as _look
    except Exception:
        _look = None


def toon_mat(name, rgb, tex=None, ink=True):
    if _look and hasattr(_look, 'toon_mat'):
        return _look.toon_mat(name, rgb, tex, ink)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    return m


def ink_hull(obj, width=0.018):
    if _look and hasattr(_look, 'ink_hull'):
        return _look.ink_hull(obj, width)
    return obj


def glow(name, rgb, strength=5.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); o = nt.nodes.new('ShaderNodeOutputMaterial')
    em.inputs[0].default_value = (*rgb[:3], 1); em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], o.inputs[0])
    return m


def newcoll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def prim(kind, name, sc=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None, ink=0.015, seg=24):
    bm = bmesh.new()
    if kind == 'sphere':
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=1.0)
    elif kind == 'cyl':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=1.0, radius2=1.0, depth=2.0)
    elif kind == 'cone':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=1.0, radius2=0.0, depth=2.0)
    else:
        bmesh.ops.create_cube(bm, size=2.0)
    for v in bm.verts:
        v.co = (v.co.x * sc[0], v.co.y * sc[1], v.co.z * sc[2])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat: o.data.materials.append(mat)
    o.location = loc; o.rotation_euler = rot
    if parent: o.parent = parent
    if ink: ink_hull(o, ink)
    return o


def empty(c, name, loc=(0, 0, 0), rot_z=0.0, target=None):
    e = bpy.data.objects.new(name, None)
    c.objects.link(e)
    e.empty_display_size = 0.2; e.location = loc; e.rotation_euler = (0, 0, rot_z)
    if target: e['target'] = list(target)
    return e


def box(c, name, sz, loc, mat, rot=(0, 0, 0), ink=0.015):
    o = prim('cube', name, (sz[0] / 2, sz[1] / 2, sz[2] / 2), loc, rot, mat, ink=ink)
    if o.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(o)
    c.objects.link(o)
    return o


def cyl(c, name, r, h, loc, mat, rot=(0, 0, 0), ink=0.015, seg=24):
    o = prim('cyl', name, (r, r, h / 2), loc, rot, mat, ink=ink, seg=seg)
    if o.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(o)
    c.objects.link(o)
    return o


# Material library
_MATS = {}
def M(name):
    if name in _MATS: return _MATS[name]
    t = lambda fn: os.path.join(TEX, fn) if os.path.exists(os.path.join(TEX, fn)) else None
    pal = {
        'concrete': ('concrete', (0.68, 0.68, 0.72), t('stone.png')),
        'concrete_dark': ('concrete_dark', (0.35, 0.38, 0.42), t('stone.png')),
        'tile_floor': ('tile_floor', (0.60, 0.62, 0.65), t('stone.png')),
        'pink_cell': ('pink_cell', (0.96, 0.56, 0.76), None),
        'pink_light': ('pink_light', (1.0, 0.76, 0.88), None),
        'pink_deep': ('pink_deep', (0.85, 0.36, 0.60), None),
        'steel': ('steel', (0.50, 0.55, 0.62), None),
        'steel_dark': ('steel_dark', (0.25, 0.28, 0.35), None),
        'iron_black': ('iron_black', (0.12, 0.12, 0.15), None),
        'oak': ('oak', (0.72, 0.48, 0.28), t('wood_dark.png')),
        'oak_dark': ('oak_dark', (0.45, 0.28, 0.16), t('wood_dark.png')),
        'chalkboard': ('chalkboard', (0.16, 0.28, 0.22), None),
        'chalk_white': ('chalk_white', (0.95, 0.95, 0.95), None),
        'chalk_red': ('chalk_red', (0.95, 0.30, 0.30), None),
        'white': ('white', (0.96, 0.96, 0.98), None),
        'blue_table': ('blue_table', (0.24, 0.48, 0.78), None),
        'glow_green': None,
        'glow_amber': None,
        'fluorescent': None,
    }
    if name == 'glow_green': m = glow('glow_green', (0.1, 0.9, 0.3), 8.0)
    elif name == 'glow_amber': m = glow('glow_amber', (1.0, 0.68, 0.25), 6.0)
    elif name == 'fluorescent': m = glow('fluorescent', (0.85, 0.95, 1.0), 5.0)
    else:
        n, c, tx = pal[name]
        m = toon_mat(n, c, tx)
    _MATS[name] = m
    return m


# ---------------------------------------------------------------- Sets
def build_corridor(c):
    ox, oy, oz = ORIGIN['corridor']; A = {}
    # Floor
    box(c, 'corridor_floor', (10.0, 8.0, 0.2), (ox, oy, oz - 0.1), M('tile_floor'), ink=0)
    # Back wall
    box(c, 'corridor_backwall', (10.0, 0.3, 4.0), (ox, oy + 3.0, oz + 2.0), M('concrete'), ink=0)
    # Cell Door frame & door
    box(c, 'door_frame', (1.8, 0.4, 2.8), (ox, oy + 2.9, oz + 1.4), M('steel_dark'))
    box(c, 'door_panel', (1.4, 0.1, 2.5), (ox, oy + 2.85, oz + 1.35), M('steel'))
    # Window slit
    box(c, 'door_window', (0.35, 0.15, 0.6), (ox, oy + 2.85, oz + 1.8), M('iron_black'))
    # Fluorescent lights
    for x in (-2.5, 2.5):
        box(c, f'light_fixture_{x}', (1.2, 0.25, 0.1), (ox + x, oy, oz + 3.4), M('steel_dark'), ink=0)
        box(c, f'light_tube_{x}', (1.1, 0.15, 0.05), (ox + x, oy, oz + 3.33), M('fluorescent'), ink=0)
    A['guard_spot'] = empty(c, 'guard_spot', (ox, oy, oz), 0)
    A['cell_door'] = empty(c, 'cell_door', (ox, oy + 2.8, oz + 1.3), 0)
    return A


def build_mix_bench(c, props):
    ox, oy, oz = ORIGIN['mix_bench']; A = {}
    # Floor & wall
    box(c, 'bench_floor', (8.0, 6.0, 0.2), (ox, oy, oz - 0.1), M('concrete'), ink=0)
    box(c, 'bench_wall', (8.0, 0.3, 4.0), (ox, oy + 2.5, oz + 2.0), M('concrete_dark'), ink=0)
    # Oak Workbench
    box(c, 'workbench_top', (2.4, 1.1, 0.12), (ox, oy + 0.6, oz + 0.88), M('oak'))
    for x in (-1.0, 1.0):
        for y in (0.2, 1.0):
            box(c, f'bench_leg_{x}_{y}', (0.1, 0.1, 0.88), (ox + x, oy + y, oz + 0.44), M('oak_dark'))
    # Digital scale
    box(c, 'scale_body', (0.45, 0.35, 0.08), (ox - 0.5, oy + 0.6, oz + 0.98), M('white'))
    box(c, 'scale_pan', (0.28, 0.25, 0.02), (ox - 0.5, oy + 0.6, oz + 1.03), M('steel'))
    box(c, 'scale_lcd', (0.16, 0.06, 0.01), (ox - 0.5, oy + 0.45, oz + 1.02), M('glow_green'), ink=0)
    # Glass Beaker with red liquid
    cyl(c, 'beaker_glass', 0.1, 0.28, (ox + 0.45, oy + 0.6, oz + 1.08), M('white'), seg=16)
    cyl(c, 'beaker_liquid', 0.09, 0.18, (ox + 0.45, oy + 0.6, oz + 1.03), M('chalk_red'), seg=16)
    # Place paint can prop on workbench
    if 'paint_can' in props:
        props['paint_can'].location = Vector((ox, oy + 0.6, oz + 1.04))
    A['bench_center'] = empty(c, 'bench_center', (ox, oy + 0.6, oz + 0.94))
    A['scientist_spot'] = empty(c, 'scientist_spot', (ox - 0.4, oy - 0.2, oz), 0)
    A['artisan_spot'] = empty(c, 'artisan_spot', (ox + 0.4, oy - 0.2, oz), 0)
    return A


def build_paint_wall(c, props):
    ox, oy, oz = ORIGIN['paint_wall']; A = {}
    box(c, 'pw_floor', (8.0, 6.0, 0.2), (ox, oy, oz - 0.1), M('concrete'), ink=0)
    # Left half: drab grey wall
    box(c, 'pw_left', (3.0, 0.3, 3.8), (ox - 1.5, oy + 1.5, oz + 1.9), M('concrete'))
    # Right half: freshly rolled Baker-Miller Pink wall
    box(c, 'pw_right', (3.0, 0.32, 3.8), (ox + 1.5, oy + 1.49, oz + 1.9), M('pink_cell'))
    # Paint tray on floor
    box(c, 'paint_tray', (0.5, 0.7, 0.08), (ox + 0.8, oy + 0.4, oz + 0.04), M('steel_dark'))
    box(c, 'tray_paint', (0.42, 0.55, 0.04), (ox + 0.8, oy + 0.4, oz + 0.05), M('pink_cell'), ink=0)
    if 'paint_roller' in props:
        props['paint_roller'].location = Vector((ox + 0.2, oy + 0.8, oz + 1.4))
    A['wall_center'] = empty(c, 'wall_center', (ox, oy + 1.5, oz + 1.5))
    A['artisan_spot'] = empty(c, 'artisan_spot', (ox, oy, oz), 0)
    return A


def build_pink_cell(c, props):
    ox, oy, oz = ORIGIN['pink_cell']; A = {}
    # Pink floor & walls
    box(c, 'cell_floor', (6.0, 6.0, 0.2), (ox, oy, oz - 0.1), M('concrete_dark'), ink=0)
    box(c, 'cell_backwall', (6.0, 0.3, 3.8), (ox, oy + 2.5, oz + 1.9), M('pink_cell'), ink=0)
    box(c, 'cell_leftwall', (0.3, 5.0, 3.8), (ox - 2.8, oy, oz + 1.9), M('pink_cell'), ink=0)
    box(c, 'cell_rightwall', (0.3, 5.0, 3.8), (ox + 2.8, oy, oz + 1.9), M('pink_cell'), ink=0)
    # Front cell bars (spaced so camera can shoot through)
    for i in range(-5, 6):
        cyl(c, f'cell_bar_{i}', 0.025, 3.8, (ox + i * 0.5, oy - 2.4, oz + 1.9), M('steel_dark'), seg=12)
    # Heavy welded steel bench
    box(c, 'welded_bench', (1.8, 0.5, 0.08), (ox + 0.35, oy + 0.4, oz + 0.45), M('steel'))
    for x in (-0.7, 0.7):
        box(c, f'bench_weld_leg_{x}', (0.08, 0.45, 0.45), (ox + 0.35 + x, oy + 0.4, oz + 0.225), M('steel_dark'))
        # Bolted base plates
        box(c, f'bench_plate_{x}', (0.18, 0.5, 0.03), (ox + 0.35 + x, oy + 0.4, oz + 0.015), M('steel_dark'), ink=0)
    # Radial impact crater under bench for rage payoff
    cyl(c, 'impact_crater', 0.8, 0.02, (ox + 0.35, oy + 0.4, oz + 0.01), M('iron_black'), ink=0, seg=16)
    A['cell_center'] = empty(c, 'cell_center', (ox, oy, oz + 1.2))
    A['inmate_spot'] = empty(c, 'inmate_spot', (ox, oy, oz), 0)
    A['bench_spot'] = empty(c, 'bench_spot', (ox + 0.35, oy + 0.4, oz + 0.48), 0)
    return A


def build_arm_wrestle(c):
    ox, oy, oz = ORIGIN['arm_wrestle']; A = {}
    # Cafeteria concrete floor
    box(c, 'cafeteria_floor', (10.0, 8.0, 0.2), (ox, oy, oz - 0.1), M('tile_floor'), ink=0)
    box(c, 'cafeteria_wall', (10.0, 0.3, 4.2), (ox, oy + 3.5, oz + 2.1), M('concrete'), ink=0)
    # Upper catwalk railing in background
    box(c, 'catwalk_floor', (10.0, 1.2, 0.15), (ox, oy + 3.0, oz + 2.8), M('steel_dark'), ink=0)
    box(c, 'catwalk_rail', (10.0, 0.05, 0.9), (ox, oy + 2.4, oz + 3.3), M('steel'), ink=0)
    # Blue heavy picnic / arm-wrestle table
    box(c, 'picnic_table_top', (2.0, 0.9, 0.08), (ox, oy, oz + 0.76), M('blue_table'))
    for x in (-0.8, 0.8):
        box(c, f'table_leg_{x}', (0.1, 0.8, 0.72), (ox + x, oy, oz + 0.36), M('steel_dark'))
    # Benches attached to table
    for y in (-0.65, 0.65):
        box(c, f'table_bench_{y}', (1.8, 0.32, 0.06), (ox, oy + y, oz + 0.44), M('blue_table'))
    # Metal lunch tray
    box(c, 'lunch_tray', (0.42, 0.32, 0.02), (ox, oy, oz + 0.81), M('steel'))
    A['table_center'] = empty(c, 'table_center', (ox, oy, oz + 0.8))
    A['guard_spot'] = empty(c, 'guard_spot', (ox - 0.35, oy, oz), math.pi / 2)
    A['inmate_spot'] = empty(c, 'inmate_spot', (ox + 0.35, oy, oz), -math.pi / 2)
    return A


def build_night_station(c):
    ox, oy, oz = ORIGIN['night_station']; A = {}
    box(c, 'ns_floor', (8.0, 6.0, 0.2), (ox, oy, oz - 0.1), M('concrete_dark'), ink=0)
    box(c, 'ns_backwall', (8.0, 0.3, 4.0), (ox, oy + 2.5, oz + 2.0), M('concrete_dark'), ink=0)
    # Desk
    box(c, 'guard_desk', (2.2, 1.0, 0.1), (ox, oy + 0.5, oz + 0.75), M('oak_dark'))
    for x in (-0.95, 0.95):
        box(c, f'desk_leg_{x}', (0.1, 0.9, 0.72), (ox + x, oy + 0.5, oz + 0.36), M('steel_dark'))
    # CRT monitor glowing
    box(c, 'crt_monitor', (0.5, 0.4, 0.4), (ox - 0.4, oy + 0.6, oz + 1.02), M('steel_dark'))
    box(c, 'crt_screen', (0.42, 0.02, 0.32), (ox - 0.4, oy + 0.39, oz + 1.02), M('glow_green'), ink=0)
    # Desk lamp casting amber cone
    cyl(c, 'desk_lamp_base', 0.12, 0.03, (ox + 0.6, oy + 0.6, oz + 0.82), M('steel_dark'), seg=16)
    cyl(c, 'desk_lamp_shade', 0.14, 0.16, (ox + 0.6, oy + 0.55, oz + 1.15), M('glow_amber'), ink=0, seg=16)
    # Analog wall clock showing 15 / 20 min
    cyl(c, 'wall_clock', 0.38, 0.06, (ox, oy + 2.35, oz + 2.3), M('white'), (math.pi / 2, 0, 0), seg=24)
    cyl(c, 'clock_rim', 0.40, 0.04, (ox, oy + 2.36, oz + 2.3), M('steel_dark'), (math.pi / 2, 0, 0), seg=24)
    # Clock hands
    box(c, 'clock_hour', (0.03, 0.01, 0.16), (ox, oy + 2.31, oz + 2.38), M('iron_black'), ink=0)
    box(c, 'clock_minute', (0.18, 0.01, 0.02), (ox + 0.09, oy + 2.31, oz + 2.3), M('chalk_red'), ink=0)
    A['desk_center'] = empty(c, 'desk_center', (ox, oy + 0.5, oz + 0.85))
    A['guard_spot'] = empty(c, 'guard_spot', (ox, oy - 0.3, oz), 0)
    return A


def build_blackboard(c):
    ox, oy, oz = ORIGIN['blackboard']; A = {}
    box(c, 'bb_floor', (8.0, 6.0, 0.2), (ox, oy, oz - 0.1), M('oak'), ink=0)
    box(c, 'bb_wall', (8.0, 0.3, 4.0), (ox, oy + 2.5, oz + 2.0), M('concrete'), ink=0)
    # Chalkboard frame and slate
    box(c, 'board_frame', (3.6, 0.12, 2.2), (ox, oy + 2.35, oz + 2.1), M('oak_dark'))
    box(c, 'board_slate', (3.3, 0.04, 1.9), (ox, oy + 2.31, oz + 2.1), M('chalkboard'), ink=0)
    # Chalk axes
    box(c, 'axis_x', (2.4, 0.02, 0.03), (ox, oy + 2.28, oz + 1.4), M('chalk_white'), ink=0)
    box(c, 'axis_y', (0.03, 0.02, 1.2), (ox - 1.1, oy + 2.28, oz + 2.0), M('chalk_white'), ink=0)
    # Chalk Bell Curve: calm drop at 15m, steep spike into red at 20m+
    box(c, 'curve_drop', (1.0, 0.02, 0.04), (ox - 0.5, oy + 2.28, oz + 1.8), M('chalk_white'), ink=0)
    box(c, 'curve_spike', (0.8, 0.02, 0.05), (ox + 0.4, oy + 2.28, oz + 2.4), M('chalk_red'), (0, -0.4, 0), ink=0)
    # Academic lectern
    box(c, 'lectern', (0.6, 0.5, 1.1), (ox + 1.1, oy + 0.8, oz + 0.55), M('oak_dark'))
    A['board_center'] = empty(c, 'board_center', (ox, oy + 2.3, oz + 2.1))
    A['scientist_spot'] = empty(c, 'scientist_spot', (ox - 0.3, oy + 0.5, oz), 0)
    return A


def build_props():
    props = {}
    # Paint Can
    can = prim('cyl', 'paint_can', (0.16, 0.16, 0.18), (0, 0, 0.18), mat=M('steel'), ink=0.012, seg=24)
    prim('cyl', 'can_rim', (0.17, 0.17, 0.01), (0, 0, 0.35), mat=M('steel_dark'), parent=can, ink=0.008, seg=24)
    prim('cyl', 'can_paint_top', (0.15, 0.15, 0.01), (0, 0, 0.34), mat=M('pink_cell'), parent=can, ink=0, seg=24)
    props['paint_can'] = can

    # Paint Roller
    roller = prim('cyl', 'paint_roller', (0.05, 0.05, 0.18), (0, 0, 0), mat=M('pink_cell'), rot=(0, math.pi / 2, 0), ink=0.01, seg=20)
    prim('cyl', 'roller_rod', (0.008, 0.008, 0.35), (0, -0.15, 0), mat=M('steel_dark'), parent=roller, rot=(math.pi / 2, 0, 0), ink=0.005)
    props['paint_roller'] = roller

    # Pocket Stopwatch
    watch = prim('cyl', 'stopwatch', (0.06, 0.06, 0.015), (0, 0, 0), mat=M('steel'), rot=(math.pi / 2, 0, 0), ink=0.008, seg=20)
    prim('cyl', 'watch_face', (0.05, 0.05, 0.002), (0, -0.01, 0), mat=M('white'), parent=watch, rot=(math.pi / 2, 0, 0), ink=0, seg=20)
    props['stopwatch'] = watch

    # Welded Bench prop
    bench = prim('cube', 'prop_bench', (0.9, 0.25, 0.04), (0, 0, 0.45), mat=M('steel'), ink=0.015)
    props['bench'] = bench

    for p in props.values():
        p.hide_render = True
    return props


def build_sets():
    props = build_props()
    out = {}
    for sid, fn in (
        ('corridor', build_corridor),
        ('mix_bench', lambda c: build_mix_bench(c, props)),
        ('paint_wall', lambda c: build_paint_wall(c, props)),
        ('pink_cell', lambda c: build_pink_cell(c, props)),
        ('arm_wrestle', build_arm_wrestle),
        ('night_station', build_night_station),
        ('blackboard', build_blackboard),
    ):
        c = newcoll('set_' + sid)
        out[sid] = {'collection': c, 'anchors': fn(c)}
    return out, props
