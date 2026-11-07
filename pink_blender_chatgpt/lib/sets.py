import bpy
import bmesh
import math
from mathutils import Vector
from math import radians, sin, cos, pi
import os

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
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    em.inputs[0].default_value = (*rgb[:3], 1)
    em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], o.inputs[0])
    return m

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
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    if ink:
        ink_hull(o, ink)
    return o

def empty(c, name, loc=(0, 0, 0), rot_z=0.0):
    e = bpy.data.objects.new(name, None)
    c.objects.link(e)
    e.empty_display_size = 0.2
    e.location = loc
    e.rotation_euler = (0, 0, rot_z)
    return e

def box(c, name, sz=(1, 1, 1), loc=(0, 0, 0), mat=None, rot=(0, 0, 0), ink=0.015):
    o = prim('cube', name, (sz[0] / 2, sz[1] / 2, sz[2] / 2), loc, rot, mat, ink=ink)
    if o.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(o)
    c.objects.link(o)
    return o

def cyl(c, name, r=1.0, h=1.0, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), ink=0.015, seg=24):
    o = prim('cyl', name, (r, r, h / 2), loc, rot, mat, ink=ink, seg=seg)
    if o.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(o)
    c.objects.link(o)
    return o

# ============================================================
# COLOR PALETTE
# ============================================================

PINK = (0.96, 0.56, 0.76)
CONCRETE = (0.68, 0.68, 0.72)
STEEL = (0.25, 0.28, 0.35)
OAK = (0.72, 0.48, 0.28)
BLUE = (0.24, 0.48, 0.78)
CHALK_GREEN = (0.16, 0.28, 0.22)
CHALK_RED = (0.95, 0.30, 0.30)

BLACK = (0.025, 0.025, 0.035)
DARK_GREY = (0.13, 0.14, 0.17)
LIGHT_GREY = (0.82, 0.83, 0.86)
WHITE = (0.95, 0.95, 0.92)
RED = (0.75, 0.035, 0.025)
GREEN = (0.15, 1.0, 0.30)
AMBER = (1.0, 0.52, 0.08)

# ============================================================
# ARCHITECTURAL ORIGINS
# ============================================================

ORIGIN = {
    'corridor': (0, 0, 0),
    'mix_bench': (100, 0, 0),
    'paint_wall': (200, 0, 0),
    'pink_cell': (300, 0, 0),
    'arm_wrestle': (400, 0, 0),
    'night_station': (500, 0, 0),
    'blackboard': (600, 0, 0),
}

# ============================================================
# GENERAL UTILITIES
# ============================================================

def create_collection(name, parent=None):
    """Create a clean isolated collection."""
    collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if parent is None:
        if collection.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(collection)
    else:
        if collection.name not in parent.children:
            parent.children.link(collection)
    return collection

def make_material(name, color, roughness=0.8, metallic=0.0):
    """Create a simple material for secondary details."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

def toon(name, color):
    """Create the supplied stylized toon material."""
    return toon_mat(name, color, ink=True)

def emissive(name, color, strength=5.0):
    return glow(name, color, strength)

def move_to_collection(obj, collection):
    """Move an object into its intended collection."""
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

def add_box(c, name, size, loc, mat, rot=(0, 0, 0), ink=0.015):
    return box(c, name, sz=size, loc=loc, mat=mat, rot=rot, ink=ink)

def add_cyl(c, name, radius, depth, loc, mat, rot=(0, 0, 0), ink=0.015, seg=24):
    return cyl(c, name, r=radius, h=depth, loc=loc, mat=mat, rot=rot, ink=ink, seg=seg)

def add_anchor(c, name, loc):
    return empty(c, name, loc)

def add_torus(c, name, major, minor, loc, mat, rot=(0, 0, 0), segments=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=major, radius2=major, depth=minor * 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    c.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    return obj

def add_text(c, name, body, loc, size, mat, rot=(radians(90), 0, 0), align='CENTER'):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.size = size
    curve.align_x = align
    curve.extrude = 0.001
    obj = bpy.data.objects.new(name, curve)
    c.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    return obj

def add_light(name, loc, color, energy, size=4.0, light_type='AREA', target=None):
    data = bpy.data.lights.new(name, light_type)
    data.energy = energy
    data.color = color
    if light_type == 'AREA':
        data.shape = 'DISK'
        data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    if target:
        direction = Vector(target) - obj.location
        obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return obj

# ============================================================
# HERO PROPS
# ============================================================

def build_props():
    c = create_collection("hero_props")

    pink = toon("PROP_Baker_Miller_Pink", PINK)
    steel = toon("PROP_Steel", STEEL)
    silver = toon("PROP_Silver", (0.72, 0.76, 0.82))
    white = toon("PROP_White", WHITE)
    black = toon("PROP_Black", BLACK)
    red = toon("PROP_Red", RED)
    wood = toon("PROP_Oak", OAK)

    props = {}

    # --------------------------------------------------------
    # PAINT CAN
    # --------------------------------------------------------
    can_x = 0
    can_y = 0

    can_body = add_cyl(c, "Hero_Paint_Can", 0.34, 0.65, (can_x, can_y, 0.36), steel, seg=48)
    add_cyl(c, "Paint_Can_Pink_Interior", 0.29, 0.035, (can_x, can_y, 0.695), pink, seg=48, ink=0.008)
    add_torus(c, "Paint_Can_Upper_Rim", 0.335, 0.035, (can_x, can_y, 0.70), silver)
    add_torus(c, "Paint_Can_Lower_Rim", 0.335, 0.025, (can_x, can_y, 0.065), silver)

    add_cyl(c, "Can_Handle_Left_Pivot", 0.035, 0.10, (-0.34, 0, 0.53), silver, rot=(0, radians(90), 0))
    add_cyl(c, "Can_Handle_Right_Pivot", 0.035, 0.10, (0.34, 0, 0.53), silver, rot=(0, radians(90), 0))

    handle_curve = bpy.data.curves.new("Paint_Can_Wire_Handle", 'CURVE')
    handle_curve.dimensions = '3D'
    handle_curve.bevel_depth = 0.012
    handle_curve.bevel_resolution = 3

    spline = handle_curve.splines.new('POLY')
    spline.points.add(32)
    for i, point in enumerate(spline.points):
        t = pi * i / 32
        point.co = (0.34 * cos(t), 0, 0.53 + 0.48 * sin(t), 1)

    handle_obj = bpy.data.objects.new("Paint_Can_Wire_Handle", handle_curve)
    c.objects.link(handle_obj)
    handle_obj.data.materials.append(silver)

    add_text(c, "Paint_Can_Label", "PINK", (0, -0.344, 0.38), 0.12, white)
    props['paint_can'] = can_body

    # --------------------------------------------------------
    # PAINT ROLLER
    # --------------------------------------------------------
    roller_x = 3.0

    roller_head = add_cyl(c, "Hero_Paint_Roller_Head", 0.105, 0.43, (roller_x, 0, 0.15), pink, rot=(0, radians(90), 0), seg=40)
    add_cyl(c, "Roller_Left_End", 0.11, 0.025, (roller_x - 0.22, 0, 0.15), silver, rot=(0, radians(90), 0))
    add_cyl(c, "Roller_Right_End", 0.11, 0.025, (roller_x + 0.22, 0, 0.15), silver, rot=(0, radians(90), 0))

    add_cyl(c, "Roller_Frame_Arm", 0.018, 0.32, (roller_x - 0.23, 0, -0.02), silver, rot=(0, radians(90), 0), ink=0.006)
    add_cyl(c, "Roller_Frame_Riser", 0.018, 0.28, (roller_x - 0.23, 0, -0.15), silver, ink=0.006)
    add_cyl(c, "Roller_Handle", 0.045, 0.28, (roller_x - 0.23, 0, -0.39), steel, ink=0.01)
    add_cyl(c, "Roller_Handle_Cap", 0.052, 0.04, (roller_x - 0.23, 0, -0.55), black)

    props['paint_roller'] = roller_head

    # --------------------------------------------------------
    # STOPWATCH
    # --------------------------------------------------------
    watch_x = 6.0
    watch_z = 0.25

    watch_case = add_cyl(c, "Hero_Stopwatch_Case", 0.22, 0.075, (watch_x, 0, watch_z), silver, rot=(radians(90), 0, 0), seg=48)
    add_cyl(c, "Stopwatch_White_Dial", 0.185, 0.012, (watch_x, -0.045, watch_z), white, rot=(radians(90), 0, 0), ink=0.006, seg=48)
    add_torus(c, "Stopwatch_Bezel", 0.20, 0.018, (watch_x, -0.053, watch_z), silver, rot=(radians(90), 0, 0))

    add_cyl(c, "Stopwatch_Crown", 0.035, 0.075, (watch_x, 0, watch_z + 0.25), silver)
    add_torus(c, "Stopwatch_Chain_Loop", 0.055, 0.012, (watch_x, 0, watch_z + 0.32), silver, rot=(radians(90), 0, 0))

    for i in range(12):
        angle = 2 * pi * i / 12
        x = watch_x + 0.15 * sin(angle)
        z = watch_z + 0.15 * cos(angle)
        add_cyl(c, "Stopwatch_Mark_%02d" % i, 0.009, 0.012, (x, -0.055, z), black, rot=(radians(90), 0, 0), ink=0.002, seg=8)

    hand = add_box(c, "Stopwatch_Second_Hand", (0.012, 0.015, 0.145), (watch_x, -0.068, watch_z + 0.07), red, ink=0.002)
    add_cyl(c, "Stopwatch_Center_Pin", 0.018, 0.02, (watch_x, -0.08, watch_z), silver, rot=(radians(90), 0, 0))

    props['stopwatch'] = watch_case
    props['stopwatch_hand'] = hand

    # --------------------------------------------------------
    # WELDED STEEL BENCH
    # --------------------------------------------------------
    bench_x = 10.0

    bench_top = add_box(c, "Hero_Bench_Seat", (1.9, 0.55, 0.14), (bench_x, 0, 0.68), steel)

    for x in (-0.75, 0.75):
        for y in (-0.18, 0.18):
            add_box(c, "Bench_Leg", (0.12, 0.12, 0.62), (bench_x + x, y, 0.31), steel)
            add_box(c, "Bench_Bolted_Base", (0.27, 0.24, 0.045), (bench_x + x, y, 0.025), silver)
            for bx in (-0.08, 0.08):
                for by in (-0.07, 0.07):
                    add_cyl(c, "Bench_Floor_Bolt", 0.022, 0.035, (bench_x + x + bx, y + by, 0.05), black)

    add_box(c, "Bench_Cross_Brace", (1.6, 0.08, 0.08), (bench_x, 0.20, 0.35), silver)
    props['bench'] = bench_top

    for p in props.values():
        p.hide_render = True

    return props

# ============================================================
# SET 1: MAX SECURITY CORRIDOR
# ============================================================

def build_corridor(c, ox):
    concrete = toon("Corridor_Concrete", CONCRETE)
    dark = toon("Corridor_Dark_Concrete", DARK_GREY)
    steel = toon("Corridor_Steel", STEEL)
    silver = toon("Corridor_Silver", (0.75, 0.77, 0.82))
    floor_mat = toon("Corridor_Floor", (0.42, 0.43, 0.46))
    white = toon("Corridor_White", WHITE)
    black = toon("Corridor_Black", BLACK)
    green = emissive("Corridor_Fluorescent", (0.72, 0.86, 1.0), 4)

    add_box(c, "Corridor_Floor", (8, 12, 0.20), (ox, 1, -0.10), floor_mat)

    for x in range(-4, 5):
        add_box(c, "Floor_Tile_Line", (0.012, 12, 0.008), (ox + x, 1, 0.005), dark, ink=0)
    for y in range(-5, 7):
        add_box(c, "Floor_Tile_Cross_Line", (8, 0.012, 0.008), (ox, y, 0.005), dark, ink=0)

    add_box(c, "Left_Concrete_Wall", (0.25, 12, 4.2), (ox - 4, 1, 2.1), concrete)
    add_box(c, "Right_Concrete_Wall", (0.25, 12, 4.2), (ox + 4, 1, 2.1), concrete)
    add_box(c, "Corridor_Back_Wall", (8, 0.25, 4.2), (ox, 7, 2.1), concrete)
    add_box(c, "Corridor_Ceiling", (8, 12, 0.18), (ox, 1, 4.25), dark)

    add_box(c, "Heavy_Steel_Cell_Door", (1.65, 0.20, 2.9), (ox, 5.65, 1.55), steel)
    for x in (-0.90, 0.90):
        add_box(c, "Door_Frame_Vertical", (0.12, 0.26, 3.1), (ox + x, 5.55, 1.55), steel)
    add_box(c, "Door_Frame_Top", (1.95, 0.25, 0.12), (ox, 5.55, 3.10), steel)

    add_box(c, "Door_Window_Dark", (0.85, 0.04, 0.42), (ox, 5.52, 2.25), black)
    for x in (-0.30, -0.10, 0.10, 0.30):
        add_box(c, "Door_Window_Bar", (0.035, 0.10, 0.46), (ox + x, 5.49, 2.25), silver)

    add_box(c, "Door_Handle", (0.06, 0.10, 0.30), (ox + 0.59, 5.43, 1.4), silver)
    add_box(c, "Security_Sign", (2.4, 0.06, 0.48), (ox, 5.49, 3.55), dark)
    add_text(c, "Security_Sign_Text", "POD C - MAX SECURITY", (ox, 5.445, 3.52), 0.20, white)

    for y in (-3.5, 0.0, 3.5):
        add_box(c, "Fluorescent_Housing", (1.5, 0.30, 0.09), (ox, y, 4.10), steel)
        add_box(c, "Fluorescent_Tube", (1.35, 0.22, 0.035), (ox, y, 4.045), green, ink=0)
        add_light("Corridor_Ceiling_Light", (ox, y, 3.9), (0.72, 0.82, 1.0), 260, 3, target=(ox, y, 0))

    return {
        'guard_spot': add_anchor(c, 'guard_spot', (ox, 1.0, 0)),
        'cell_door': add_anchor(c, 'cell_door', (ox, 5.0, 0)),
    }

# ============================================================
# SET 2: MIXING BENCH
# ============================================================

def build_mix_bench(c, ox):
    wood = toon("Mix_Oak", OAK)
    steel = toon("Mix_Steel", STEEL)
    silver = toon("Mix_Silver", (0.75, 0.77, 0.81))
    black = toon("Mix_Black", BLACK)
    pink = toon("Mix_Pink", PINK)
    red = toon("Mix_Deep_Red", RED)
    white = toon("Mix_White", WHITE)
    glass = make_material("Mix_Glass", (0.55, 0.15, 0.18), 0.15)
    green = emissive("Scale_Green_Digits", (0.1, 1.0, 0.25), 4)

    add_box(c, "Heavy_Oak_Workbench", (3.8, 1.35, 0.18), (ox, 0, 0.95), wood)
    for x in (-1.55, 1.55):
        for y in (-0.48, 0.48):
            add_box(c, "Workbench_Leg", (0.18, 0.18, 0.95), (ox + x, y, 0.475), wood)

    add_box(c, "Digital_Scale_Base", (0.75, 0.55, 0.16), (ox - 0.9, 0, 1.12), steel)
    add_box(c, "Digital_Scale_Display", (0.55, 0.035, 0.18), (ox - 0.9, -0.29, 1.29), black)
    add_text(c, "Scale_Digits", "000.00 g", (ox - 0.9, -0.315, 1.26), 0.12, green)
    add_box(c, "Scale_Weighing_Plate", (0.65, 0.48, 0.035), (ox - 0.9, 0, 1.23), silver)

    add_cyl(c, "Glass_Beaker", 0.22, 0.45, (ox + 0.2, 0, 1.27), glass, seg=40, ink=0.006)
    add_cyl(c, "Deep_Red_Pigment", 0.19, 0.19, (ox + 0.2, 0, 1.08), red, seg=40)
    add_torus(c, "Beaker_Rim", 0.22, 0.018, (ox + 0.2, 0, 1.495), silver)

    for z in (1.18, 1.27, 1.36):
        add_box(c, "Beaker_Measurement_Mark", (0.12, 0.015, 0.012), (ox + 0.2, -0.22, z), white, ink=0)

    swatches = [(1.0, 0.3, 0.5), (1.0, 0.55, 0.65), (0.96, 0.56, 0.76), (0.8, 0.3, 0.48), (0.65, 0.12, 0.30), (0.9, 0.75, 0.8)]
    for i, color in enumerate(swatches):
        angle = radians(-35 + i * 14)
        mat = toon("Swatch_%02d" % i, color)
        add_box(c, "Pantone_Color_Swatch_%02d" % i, (0.25, 0.75, 0.025), (ox + 1.15 + i * 0.055, 0.08, 1.12 + i * 0.006), mat, rot=(0, 0, angle))

    add_cyl(c, "Mix_Paint_Bucket", 0.29, 0.48, (ox + 1.8, 0.05, 1.20), steel)
    add_cyl(c, "Mix_Bucket_Paint", 0.255, 0.035, (ox + 1.8, 0.05, 1.45), pink)
    add_torus(c, "Mix_Bucket_Rim", 0.28, 0.025, (ox + 1.8, 0.05, 1.45), silver)

    return {
        'bench_center': add_anchor(c, 'bench_center', (ox, 0, 1)),
        'scientist_spot': add_anchor(c, 'scientist_spot', (ox - 1.4, -1.1, 0)),
        'artisan_spot': add_anchor(c, 'artisan_spot', (ox + 1.4, -1.1, 0)),
    }

# ============================================================
# SET 3: TWO-TONE PAINT WALL
# ============================================================

def build_paint_wall(c, ox):
    grey = toon("PaintWall_Unpainted_Concrete", CONCRETE)
    pink = toon("PaintWall_Baker_Miller_Pink", PINK)
    steel = toon("PaintWall_Tray_Steel", STEEL)
    dark = toon("PaintWall_Dark", DARK_GREY)

    add_box(c, "Grey_Cinderblock_Half", (2, 0.28, 4), (ox - 1, 0, 2), grey)
    add_box(c, "Pink_Painted_Half", (2, 0.28, 4), (ox + 1, 0, 2), pink)
    add_box(c, "Wall_Center_Seam", (0.025, 0.04, 4), (ox, -0.17, 2), dark)

    for z in (0.5, 1, 1.5, 2, 2.5, 3, 3.5):
        add_box(c, "Grey_Wall_Horizontal_Mortar", (1.96, 0.015, 0.025), (ox - 1, -0.155, z), dark, ink=0)

    for row in range(8):
        z = 0.25 + row * 0.5
        offset = 0.5 if row % 2 else 0
        for x in (-1.75, -0.75):
            xpos = ox + x + offset
            if xpos < ox - 0.03:
                add_box(c, "Grey_Wall_Vertical_Mortar", (0.02, 0.018, 0.48), (xpos, -0.16, z), dark, ink=0)

    add_box(c, "Paint_Wall_Floor", (6, 4, 0.15), (ox, 0, -0.075), dark)
    add_box(c, "Roller_Tray_Base", (1.15, 0.48, 0.08), (ox + 0.5, -0.85, 0.06), steel)
    add_box(c, "Roller_Tray_Pink_Paint", (0.85, 0.30, 0.025), (ox + 0.5, -0.85, 0.12), pink)

    for x in (-0.02, 1.02):
        add_box(c, "Tray_Raised_Edge", (0.06, 0.50, 0.12), (ox + x, -0.85, 0.12), steel)

    add_box(c, "Wall_Baseboard", (4.1, 0.10, 0.12), (ox, -0.19, 0.07), steel)

    return {
        'wall_center': add_anchor(c, 'wall_center', (ox, 0, 2)),
        'artisan_spot': add_anchor(c, 'artisan_spot', (ox + 2.5, -1.4, 0)),
    }

# ============================================================
# SET 4: PINK EXPERIMENT CELL
# ============================================================

def build_pink_cell(c, ox):
    pink = toon("Cell_Baker_Miller_Pink", PINK)
    pink_dark = toon("Cell_Pink_Shadow", (0.78, 0.34, 0.52))
    steel = toon("Cell_Steel", STEEL)
    silver = toon("Cell_Bolts", (0.72, 0.76, 0.82))
    concrete = toon("Cell_Cracked_Concrete", (0.46, 0.43, 0.43))
    black = toon("Cell_Black", BLACK)

    add_box(c, "Pink_Cell_Floor", (5, 6, 0.18), (ox, 1, -0.09), pink)
    add_box(c, "Pink_Cell_Back_Wall", (5, 0.20, 4), (ox, 4, 2), pink)
    add_box(c, "Pink_Cell_Left_Wall", (0.20, 6, 4), (ox - 2.5, 1, 2), pink)
    add_box(c, "Pink_Cell_Right_Wall", (0.20, 6, 4), (ox + 2.5, 1, 2), pink)
    add_box(c, "Pink_Cell_Ceiling", (5, 6, 0.18), (ox, 1, 4), pink)

    for x in (-2.2, -1.2, -0.2, 0.8, 1.8):
        add_box(c, "Pink_Cell_Back_Wall_Panel", (0.015, 0.012, 3.7), (ox + x, 3.88, 2), pink_dark, ink=0)

    bench_z = 0.82
    add_box(c, "Cell_Heavy_Steel_Bench_Seat", (1.9, 0.65, 0.15), (ox, 1.0, bench_z), steel)

    for x in (-0.72, 0.72):
        for y in (0.76, 1.24):
            add_box(c, "Cell_Bench_Leg", (0.14, 0.14, 0.72), (ox + x, y, 0.38), steel)
            add_box(c, "Cell_Bench_Bolted_Foot", (0.28, 0.25, 0.055), (ox + x, y, 0.055), silver)
            for dx in (-0.085, 0.085):
                for dy in (-0.075, 0.075):
                    add_cyl(c, "Cell_Bench_Base_Bolt", 0.025, 0.025, (ox + x + dx, y + dy, 0.09), silver, seg=12)

    add_box(c, "Cell_Bench_Cross_Brace", (1.55, 0.08, 0.09), (ox, 1.2, 0.38), steel)

    crater_x = ox
    crater_y = 1.0
    add_cyl(c, "Crater_Central_Damage", 0.58, 0.025, (crater_x, crater_y, 0.012), concrete, seg=64, ink=0.005)

    for radius in (0.38, 0.49, 0.60):
        add_torus(c, "Crater_Cracked_Ring", radius, 0.012, (crater_x, crater_y, 0.027), black)

    for i in range(16):
        angle = 2 * pi * i / 16
        length = 0.48 if i % 2 else 0.62
        x = crater_x + cos(angle) * length * 0.5
        y = crater_y + sin(angle) * length * 0.5
        add_box(c, "Crater_Radial_Fracture", (length, 0.018, 0.018), (x, y, 0.043), black, rot=(0, 0, angle), ink=0)

    for i in range(12):
        angle = 2 * pi * i / 12
        radius = 0.64
        x = crater_x + cos(angle) * radius
        y = crater_y + sin(angle) * radius
        add_box(c, "Crater_Concrete_Debris", (0.10, 0.07, 0.035), (x, y, 0.035), concrete, rot=(0, 0, angle))

    for x in (-2.35, -1.55, -0.75, 0.05, 0.85, 1.65, 2.35):
        add_cyl(c, "Pink_Cell_Front_Bar", 0.045, 3.9, (ox + x, -1.95, 1.95), steel, seg=16)

    for z in (0.15, 3.8):
        add_box(c, "Pink_Cell_Front_Crossbar", (5, 0.12, 0.10), (ox, -1.95, z), steel)

    add_light("Pink_Cell_Main_Light", (ox, 1.0, 3.8), (1.0, 0.68, 0.78), 400, 4, target=(ox, 1.0, 0.5))
    add_light("Pink_Cell_Fill_Light", (ox + 1.5, -0.8, 2.8), (1.0, 0.82, 0.90), 180, 3, target=(ox, 1.0, 1.0))

    return {
        'cell_center': add_anchor(c, 'cell_center', (ox, 1, 0)),
        'inmate_spot': add_anchor(c, 'inmate_spot', (ox, 0, 0)),
        'bench_spot': add_anchor(c, 'bench_spot', (ox, 1, 0.82)),
    }

# ============================================================
# SET 5: ARM WRESTLING / CAFETERIA
# ============================================================

def build_arm_wrestle(c, ox):
    floor = toon("Cafeteria_Floor", (0.36, 0.38, 0.42))
    blue = toon("Cafeteria_Blue_Table", BLUE)
    steel = toon("Cafeteria_Steel", STEEL)
    silver = toon("Cafeteria_Silver", (0.76, 0.78, 0.82))
    concrete = toon("Cafeteria_Concrete", CONCRETE)

    add_box(c, "Cafeteria_Floor", (8, 9, 0.20), (ox, 1, -0.10), floor)
    add_box(c, "Cafeteria_Back_Wall", (8, 0.20, 5), (ox, 5.5, 2.5), concrete)
    add_box(c, "Catwalk_Platform", (8, 1.0, 0.15), (ox, 3.5, 3.15), steel)
    add_box(c, "Catwalk_Top_Railing", (8, 0.10, 0.10), (ox, 3.0, 4.05), silver)
    add_box(c, "Catwalk_Mid_Railing", (8, 0.08, 0.07), (ox, 3.0, 3.60), steel)

    for x in range(-4, 5):
        add_box(c, "Catwalk_Vertical_Railing", (0.08, 0.08, 0.95), (ox + x, 3.0, 3.55), steel)

    add_box(c, "Blue_Cafeteria_Tabletop", (2.5, 1.0, 0.14), (ox, 0, 1.0), blue)

    for y in (-0.85, 0.85):
        add_box(c, "Cafeteria_Attached_Bench", (2.5, 0.38, 0.12), (ox, y, 0.62), blue)
        for x in (-0.95, 0.95):
            add_box(c, "Cafeteria_Bench_Leg", (0.12, 0.12, 0.60), (ox + x, y, 0.30), steel)

    for x in (-0.95, 0.95):
        for y in (-0.35, 0.35):
            add_box(c, "Cafeteria_Table_Leg", (0.13, 0.13, 0.85), (ox + x, y, 0.50), steel)

    for x in (-0.62, 0.62):
        add_box(c, "Stamped_Lunch_Tray", (0.75, 0.48, 0.035), (ox + x, -0.05, 1.10), silver)
        for dx in (-0.37, 0.37):
            add_box(c, "Tray_Raised_Side", (0.035, 0.48, 0.055), (ox + x + dx, -0.05, 1.13), steel)
        for dy in (-0.22, 0.22):
            add_box(c, "Tray_Raised_End", (0.75, 0.035, 0.055), (ox + x, -0.05 + dy, 1.13), steel)

    for x in (-2, 0, 2):
        add_light("Cafeteria_Light", (ox + x, 0, 4.5), (0.82, 0.88, 1.0), 300, 3, target=(ox + x, 0, 0))

    return {
        'table_center': add_anchor(c, 'table_center', (ox, 0, 1)),
        'guard_spot': add_anchor(c, 'guard_spot', (ox - 1.5, -1.8, 0)),
        'inmate_spot': add_anchor(c, 'inmate_spot', (ox + 1.5, -1.8, 0)),
    }

# ============================================================
# SET 6: NIGHT GUARD STATION
# ============================================================

def build_night_station(c, ox):
    wood = toon("Night_Desk_Wood", OAK)
    steel = toon("Night_Desk_Steel", STEEL)
    silver = toon("Night_Desk_Silver", (0.75, 0.77, 0.81))
    dark = toon("Night_Dark", DARK_GREY)
    green = emissive("CRT_Green", (0.12, 1.0, 0.30), 3.5)
    amber = emissive("Desk_Lamp_Amber", AMBER, 3)
    white = toon("Clock_White", WHITE)
    red = toon("Clock_Red", RED)

    add_box(c, "Night_Station_Floor", (6, 6, 0.18), (ox, 0, -0.09), dark)
    add_box(c, "Night_Station_Back_Wall", (6, 0.20, 4), (ox, 2.5, 2), dark)

    add_box(c, "Guard_Watch_Desk_Top", (2.8, 1.0, 0.16), (ox, -0.2, 1.1), wood)
    add_box(c, "Guard_Watch_Desk_Front", (2.8, 0.12, 0.9), (ox, -0.62, 0.55), steel)

    for x in (-1.2, 1.2):
        add_box(c, "Watch_Desk_Leg", (0.16, 0.75, 1.05), (ox + x, -0.2, 0.52), steel)

    add_box(c, "CRT_Monitor_Case", (1.2, 0.25, 0.85), (ox - 0.55, -0.15, 1.65), steel)
    add_box(c, "CRT_Green_Screen", (1.05, 0.025, 0.68), (ox - 0.55, -0.29, 1.68), green, ink=0.005)

    for z in (1.42, 1.53, 1.64, 1.75, 1.86, 1.97):
        add_box(c, "CRT_Scan_Line", (0.92, 0.008, 0.008), (ox - 0.55, -0.31, z), dark, ink=0)

    add_text(c, "CRT_Security_Text", "SECURITY CAM 03", (ox - 0.55, -0.325, 1.92), 0.085, green)
    add_box(c, "CRT_Monitor_Stand", (0.32, 0.30, 0.12), (ox - 0.55, -0.15, 1.18), steel)

    add_cyl(c, "Desk_Lamp_Base", 0.18, 0.06, (ox + 0.85, -0.15, 1.21), steel)
    add_cyl(c, "Desk_Lamp_Stem", 0.025, 0.45, (ox + 0.85, -0.15, 1.46), steel)
    add_cyl(c, "Desk_Lamp_Shade", 0.19, 0.16, (ox + 0.85, -0.15, 1.72), amber)
    add_light("Amber_Desk_Lamp_Light", (ox + 0.85, -0.25, 1.7), (1.0, 0.45, 0.12), 180, 2, target=(ox + 0.85, -0.6, 0))

    clock_x = ox + 1.5
    clock_y = 2.34
    clock_z = 3.0

    add_cyl(c, "Wall_Clock_Case", 0.48, 0.12, (clock_x, clock_y, clock_z), steel, rot=(radians(90), 0, 0), seg=48)
    add_cyl(c, "Wall_Clock_Face", 0.42, 0.025, (clock_x, clock_y - 0.075, clock_z), white, rot=(radians(90), 0, 0), seg=48)
    add_torus(c, "Wall_Clock_Bezel", 0.45, 0.025, (clock_x, clock_y - 0.09, clock_z), silver, rot=(radians(90), 0, 0))

    for i in range(12):
        angle = 2 * pi * i / 12
        x = clock_x + 0.34 * sin(angle)
        z = clock_z + 0.34 * cos(angle)
        add_cyl(c, "Clock_Marker", 0.018, 0.012, (x, clock_y - 0.10, z), dark, rot=(radians(90), 0, 0), seg=8)

    add_box(c, "Clock_Minute_Hand", (0.018, 0.015, 0.29), (clock_x, clock_y - 0.12, clock_z + 0.12), steel, rot=(0, 0, radians(96)))
    add_box(c, "Clock_Hour_Hand", (0.025, 0.015, 0.19), (clock_x - 0.04, clock_y - 0.13, clock_z + 0.08), red, rot=(0, 0, radians(245)))
    add_cyl(c, "Clock_Center", 0.035, 0.03, (clock_x, clock_y - 0.15, clock_z), red, rot=(radians(90), 0, 0))

    add_light("Night_Station_Ambient", (ox, 0, 3.7), (0.4, 0.45, 0.65), 150, 4, target=(ox, 0, 0))

    return {
        'desk_center': add_anchor(c, 'desk_center', (ox, -0.2, 1.1)),
        'guard_spot': add_anchor(c, 'guard_spot', (ox + 1.5, -1.3, 0)),
    }

# ============================================================
# SET 7: UNIVERSITY LECTURE HALL / BLACKBOARD
# ============================================================

def build_blackboard(c, ox):
    board = toon("Blackboard_Deep_Green", CHALK_GREEN)
    wood = toon("Blackboard_Wood_Frame", OAK)
    white = toon("Blackboard_White_Chalk", WHITE)
    red = toon("Blackboard_Red_Chalk", CHALK_RED)
    green = toon("Blackboard_Green_Chalk", (0.55, 0.85, 0.58))
    floor = toon("Lecture_Hall_Floor", (0.34, 0.34, 0.38))

    add_box(c, "Lecture_Hall_Floor", (8, 6, 0.20), (ox, 0, -0.10), floor)
    add_box(c, "Lecture_Hall_Blackboard", (4.8, 0.15, 2.8), (ox, 1.5, 2.4), board)

    for x in (-2.48, 2.48):
        add_box(c, "Blackboard_Vertical_Wood_Frame", (0.14, 0.23, 3.0), (ox + x, 1.36, 2.4), wood)
    for z in (0.94, 3.86):
        add_box(c, "Blackboard_Horizontal_Wood_Frame", (5.1, 0.23, 0.14), (ox, 1.36, z), wood)

    add_box(c, "Blackboard_Chalk_Tray", (4.9, 0.25, 0.09), (ox, 1.20, 0.90), wood)

    add_box(c, "Graph_X_Axis", (3.55, 0.025, 0.025), (ox + 0.15, 1.285, 1.60), white, ink=0.002)
    add_box(c, "Graph_Y_Axis", (0.025, 0.025, 1.95), (ox - 1.60, 1.285, 2.55), white, ink=0.002)

    add_box(c, "Graph_X_Arrow_Upper", (0.16, 0.025, 0.025), (ox + 1.86, 1.285, 1.65), white)
    add_box(c, "Graph_X_Arrow_Lower", (0.16, 0.025, 0.025), (ox + 1.86, 1.285, 1.55), white)
    add_box(c, "Graph_Y_Arrow_Left", (0.025, 0.025, 0.16), (ox - 1.65, 1.285, 3.45), white)
    add_box(c, "Graph_Y_Arrow_Right", (0.025, 0.025, 0.16), (ox - 1.55, 1.285, 3.45), white)

    add_text(c, "Graph_X_Label", "TIME", (ox + 0.25, 1.27, 1.30), 0.22, white)
    add_text(c, "Graph_Y_Label", "AGGRESSION", (ox - 1.48, 1.27, 3.54), 0.17, white)

    curve_data = bpy.data.curves.new("Aggression_Bell_Curve", 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 24
    curve_data.bevel_depth = 0.025
    curve_data.bevel_resolution = 4

    spline = curve_data.splines.new('POLY')
    points = []
    for i in range(30):
        t = i / 29
        x = -1.45 + t * 3.1
        z = 2.8 - 1.2 * math.exp(-((t - 0.45) ** 2) / 0.10)
        if 0.65 < t < 0.85:
            z -= 0.45
        if t > 0.78:
            z += ((t - 0.78) ** 2) * 18
        points.append((ox + x, 1.25, z))

    spline.points.add(len(points) - 1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1)

    curve_obj = bpy.data.objects.new("Aggression_Bell_Curve", curve_data)
    c.objects.link(curve_obj)
    curve_data.materials.append(red)

    add_text(c, "Time_15m_Label", "15m", (ox + 0.75, 1.25, 1.80), 0.15, green)
    add_text(c, "Time_20m_Label", "20m+", (ox + 1.45, 1.25, 2.05), 0.15, red)

    add_box(c, "Lecture_Lectern_Top", (1.0, 0.65, 0.12), (ox, -0.8, 1.25), wood)
    add_box(c, "Lecture_Lectern_Stem", (0.45, 0.40, 1.05), (ox, -0.8, 0.65), wood)
    add_box(c, "Lecture_Lectern_Base", (1.0, 0.65, 0.12), (ox, -0.8, 0.08), wood)

    add_box(c, "White_Chalk_Piece", (0.12, 0.035, 0.035), (ox - 1.8, 1.13, 0.98), white)
    add_box(c, "Red_Chalk_Piece", (0.12, 0.035, 0.035), (ox - 1.55, 1.13, 0.98), red)

    add_light("Lecture_Hall_Main_Light", (ox, -0.5, 4.8), (0.85, 0.88, 1.0), 400, 4, target=(ox, 1.5, 1.5))

    return {
        'board_center': add_anchor(c, 'board_center', (ox, 1.5, 2.4)),
        'scientist_spot': add_anchor(c, 'scientist_spot', (ox, -1.8, 0)),
    }

# ============================================================
# MASTER BUILD FUNCTION
# ============================================================

def build_sets():
    props = build_props()

    c_corridor = create_collection("set_corridor")
    c_mix = create_collection("set_mix_bench")
    c_pw = create_collection("set_paint_wall")
    c_cell = create_collection("set_pink_cell")
    c_arm = create_collection("set_arm_wrestle")
    c_ns = create_collection("set_night_station")
    c_bb = create_collection("set_blackboard")

    A_corridor = build_corridor(c_corridor, ORIGIN['corridor'][0])
    A_mix = build_mix_bench(c_mix, ORIGIN['mix_bench'][0])
    A_pw = build_paint_wall(c_pw, ORIGIN['paint_wall'][0])
    A_cell = build_pink_cell(c_cell, ORIGIN['pink_cell'][0])
    A_arm = build_arm_wrestle(c_arm, ORIGIN['arm_wrestle'][0])
    A_ns = build_night_station(c_ns, ORIGIN['night_station'][0])
    A_bb = build_blackboard(c_bb, ORIGIN['blackboard'][0])

    out = {
        'corridor': {'collection': c_corridor, 'anchors': A_corridor},
        'mix_bench': {'collection': c_mix, 'anchors': A_mix},
        'paint_wall': {'collection': c_pw, 'anchors': A_pw},
        'pink_cell': {'collection': c_cell, 'anchors': A_cell},
        'arm_wrestle': {'collection': c_arm, 'anchors': A_arm},
        'night_station': {'collection': c_ns, 'anchors': A_ns},
        'blackboard': {'collection': c_bb, 'anchors': A_bb},
    }

    return out, props
