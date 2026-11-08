"""look.py - toon materials, inverted-hull ink, EEVEE engine selector,
photometric lighting rigs and the per-mood TOON GAIN COMPENSATOR.

Everything that does not need Blender (palette, polygon helpers, mood table)
is importable without bpy so the pure evaluator can run on any machine.
"""
import math

try:
    import bpy
    import bmesh
    from mathutils import Vector, Quaternion
except ImportError:  # pure / headless-logic mode
    bpy = bmesh = None

# --------------------------------------------------------------------------
# Palette (sRGB) -----------------------------------------------------------
# --------------------------------------------------------------------------
PALETTE = dict(
    black=(0.03, 0.03, 0.04), white=(0.96, 0.95, 0.92), cream=(0.97, 0.9, 0.7),
    paper=(0.92, 0.88, 0.74), red=(0.85, 0.2, 0.18), orange=(0.95, 0.52, 0.15),
    yellow=(0.98, 0.82, 0.2), green=(0.3, 0.68, 0.35), green_dark=(0.18, 0.45, 0.25),
    teal=(0.2, 0.6, 0.62), blue=(0.22, 0.45, 0.85), navy=(0.12, 0.18, 0.4),
    purple=(0.5, 0.3, 0.65), pink=(0.95, 0.55, 0.65), sand=(0.93, 0.8, 0.55),
    sea=(0.2, 0.55, 0.8), sky=(0.55, 0.78, 0.97), grass=(0.4, 0.7, 0.3),
    wood=(0.58, 0.38, 0.2), wood_dark=(0.35, 0.22, 0.12), brick=(0.7, 0.3, 0.22),
    stone=(0.55, 0.55, 0.58), stone_dark=(0.3, 0.3, 0.34), iron=(0.42, 0.45, 0.5),
    iron_dark=(0.2, 0.22, 0.26), brass=(0.85, 0.65, 0.25), crust=(0.8, 0.5, 0.2),
    blueprint=(0.12, 0.3, 0.6), chalk=(0.9, 0.93, 0.9), board=(0.12, 0.2, 0.17),
    bulb=(1.0, 0.9, 0.6), fire=(1.0, 0.45, 0.1), grey=(0.5, 0.5, 0.52),
    skin_a=(0.98, 0.8, 0.65), skin_b=(0.85, 0.6, 0.42), skin_c=(0.6, 0.4, 0.28),
    skin_d=(1.0, 0.86, 0.76), smog=(0.62, 0.64, 0.68),
)
EMISSIVE = {"bulb", "fire"}


def to_lin(c):
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c)


# --------------------------------------------------------------------------
# Pure polygon helpers: polygons are CCW lists of (x, z) seen from camera ----
# --------------------------------------------------------------------------
def rect_poly(w, h, cx=0.0, cz=0.0):
    return [(cx - w / 2, cz - h / 2), (cx + w / 2, cz - h / 2),
            (cx + w / 2, cz + h / 2), (cx - w / 2, cz + h / 2)]


def ellipse_poly(rx, rz, n=24, cx=0.0, cz=0.0, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, z = rx * math.cos(a), rz * math.sin(a)
        pts.append((cx + x * c - z * s, cz + x * s + z * c))
    return pts


def tri_poly(p0, p1, p2):
    return [p0, p1, p2]


# --------------------------------------------------------------------------
# Moods + TOON GAIN COMPENSATOR -------------------------------------------
# --------------------------------------------------------------------------
PRACTICAL_WATTS = 500.0
MIN_SUN = 40.0

MOODS = {
    "noon_fair":         dict(sun_strength=52.0, sun_color=(1.0, 0.96, 0.85), sun_rot=(52, 0, -32),
                              world=(0.55, 0.78, 1.0), world_strength=0.9, practicals=False, gain_trim=1.0),
    "golden_dusk":       dict(sun_strength=44.0, sun_color=(1.0, 0.72, 0.42), sun_rot=(60, 0, -55),
                              world=(0.95, 0.55, 0.35), world_strength=0.7, practicals=False, gain_trim=1.0),
    "workshop_tungsten": dict(sun_strength=40.0, sun_color=(0.85, 0.9, 1.0), sun_rot=(48, 0, 20),
                              world=(0.12, 0.10, 0.14), world_strength=0.5, practicals=True, gain_trim=0.95),
    "bakery_warm":       dict(sun_strength=46.0, sun_color=(1.0, 0.88, 0.7), sun_rot=(50, 0, -20),
                              world=(0.9, 0.7, 0.5), world_strength=0.6, practicals=True, gain_trim=1.0),
    "grey_1923":         dict(sun_strength=60.0, sun_color=(0.8, 0.85, 0.95), sun_rot=(46, 0, -10),
                              world=(0.5, 0.52, 0.56), world_strength=0.8, practicals=False, gain_trim=1.0),
}


def recommended_gain(m):
    """Frontal irradiance on a card facing the camera: E*sin(rx)*cos(rz) / pi.
    Dividing the diffuse term by it keeps ColorRamp input in [0, ~1] so a
    40-60 W/m^2 sun never clips the bands to white."""
    rx, _, rz = (math.radians(a) for a in m["sun_rot"])
    return max(1.0, m["sun_strength"] * math.sin(rx) * math.cos(rz) / math.pi)


def _finalize_moods():
    for name, m in MOODS.items():
        assert m["sun_strength"] >= MIN_SUN, f"mood {name}: key sun must be >= {MIN_SUN} W/m^2"
        m["toon_gain"] = round(recommended_gain(m) * m["gain_trim"], 3)
        m["practical_watts"] = PRACTICAL_WATTS


_finalize_moods()


def validate_moods():
    for n, m in MOODS.items():
        assert m["sun_strength"] >= MIN_SUN and m["practical_watts"] == 500.0 and m["toon_gain"] > 1.0, n
    return True


# --------------------------------------------------------------------------
# Engine selection ---------------------------------------------------------
# --------------------------------------------------------------------------
def pick_engine():
    items = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if cand in items:
            return cand
    raise RuntimeError(f"No EEVEE engine in {items}")


def configure_render(scene, res=(1080, 1920), samples=4):
    scene.render.engine = pick_engine()
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 0, 1829
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except (TypeError, AttributeError):
        pass
    for attr, val in (("taa_render_samples", samples), ("use_shadows", True)):
        try:
            setattr(scene.eevee, attr, val)
        except (AttributeError, TypeError):
            pass


# --------------------------------------------------------------------------
# Materials ----------------------------------------------------------------
# --------------------------------------------------------------------------
def toon_material(name, rgb, gain=12.0, bands=(0.42, 0.72, 1.0)):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    diff = N.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2r = N.new("ShaderNodeShaderToRGB")
    bw = N.new("ShaderNodeRGBToBW")
    inv = N.new("ShaderNodeValue")
    inv.name = inv.label = "ToonGain"           # holds 1/gain, updated per mood
    inv.outputs[0].default_value = 1.0 / gain
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (bands[0],) * 3 + (1,)
    el[1].position, el[1].color = 0.34, (bands[1],) * 3 + (1,)
    e2 = el.new(0.68)
    e2.color = (bands[2],) * 3 + (1,)
    tint = N.new("ShaderNodeVectorMath")
    tint.operation = "MULTIPLY"
    tint.inputs[1].default_value = to_lin(rgb)
    em = N.new("ShaderNodeEmission")
    L.new(diff.outputs["BSDF"], s2r.inputs["Shader"])
    L.new(s2r.outputs["Color"], bw.inputs["Color"])
    L.new(bw.outputs["Val"], mul.inputs[0])
    L.new(inv.outputs[0], mul.inputs[1])
    L.new(mul.outputs[0], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], tint.inputs[0])
    L.new(tint.outputs[0], em.inputs["Color"])
    L.new(em.outputs[0], out.inputs["Surface"])
    mat["toon"] = True
    if hasattr(mat, "use_backface_culling"):
        mat.use_backface_culling = False
    return mat


def emissive_material(name, rgb, strength=4.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*to_lin(rgb), 1)
    em.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    mat["toon"] = False
    return mat


def mat_for(key, gain=12.0):
    name = "T_" + key
    m = bpy.data.materials.get(name)
    if m:
        return m
    if key in EMISSIVE:
        return emissive_material(name, PALETTE[key])
    return toon_material(name, PALETTE[key], gain)


def ink_material():
    mat = bpy.data.materials.get("INK") or emissive_material("INK", (0.0, 0.0, 0.0), 1.0)
    mat.use_backface_culling = True          # inverted hull: only far side shows
    return mat


def set_toon_gain(gain):
    """TOON GAIN COMPENSATOR - push 1/gain into every toon material."""
    for mat in bpy.data.materials:
        if mat.get("toon") and mat.node_tree:
            nd = mat.node_tree.nodes.get("ToonGain")
            if nd:
                nd.outputs[0].default_value = 1.0 / gain


# --------------------------------------------------------------------------
# Geometry -----------------------------------------------------------------
# --------------------------------------------------------------------------
def get_collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def _finish(name, me, color, coll, ink, pos, rot=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(obj)
    me.materials.append(mat_for(color))
    if ink > 0:
        me.materials.append(ink_material())
        mod = obj.modifiers.new("InkHull", "SOLIDIFY")
        mod.thickness = ink
        mod.offset = 1.0
        mod.use_flip_normals = True
        mod.use_even_offset = True
        mod.material_offset = 1
        mod.use_rim = False
    obj.location = pos
    obj.rotation_euler = rot
    return obj


def make_prism(name, poly, color, coll=None, pos=(0, 0, 0), depth=0.03, ink=0.02, rot_deg=0.0):
    """Closed thin prism (so vertex normals fan outward at the rim and the
    Solidify hull grows IN the card plane -> a true ink outline)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    h = depth / 2
    f = [bm.verts.new((x, -h, z)) for x, z in poly]
    b = [bm.verts.new((x, h, z)) for x, z in poly]
    bm.faces.new(f)
    bm.faces.new(b[::-1])
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((f[i], b[i], b[j], f[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    return _finish(name, me, color, coll, ink, pos, (0.0, -math.radians(rot_deg), 0.0))


def make_box(name, size, pos, color, coll=None, ink=0.02, rot_deg=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bm.to_mesh(me)
    bm.free()
    return _finish(name, me, color, coll, ink, pos, tuple(math.radians(a) for a in rot_deg))


def make_ring(name, r0, r1, pos, color, coll=None, n=32):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    o = [bm.verts.new((r1 * math.cos(2 * math.pi * i / n), 0, r1 * math.sin(2 * math.pi * i / n))) for i in range(n)]
    i_ = [bm.verts.new((r0 * math.cos(2 * math.pi * i / n), 0, r0 * math.sin(2 * math.pi * i / n))) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((o[i], o[j], i_[j], i_[i]))
    bm.to_mesh(me)
    bm.free()
    return _finish(name, me, color, coll, 0.0, pos)


def make_text(name, body, pos, size, color, coll=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    obj = bpy.data.objects.new(name, cu)
    (coll or bpy.context.scene.collection).objects.link(obj)
    obj.data.materials.append(mat_for(color))
    obj.location = pos
    obj.rotation_euler = (math.radians(90), 0, 0)   # face the -Y camera
    return obj


def empty(name, parent=None, loc=(0, 0, 0), coll=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.08
    (coll or bpy.context.scene.collection).objects.link(e)
    e.parent = parent
    e.location = loc
    return e


# --------------------------------------------------------------------------
# Lighting rig -------------------------------------------------------------
# --------------------------------------------------------------------------
N_PRACTICALS = 4


def build_light_rig():
    coll = get_collection("RIG")
    sun = bpy.data.lights.new("KeySun", "SUN")
    sun.angle = math.radians(2.5)
    sun.energy = 52.0
    so = bpy.data.objects.new("KeySun", sun)
    coll.objects.link(so)
    for i in range(N_PRACTICALS):
        pl = bpy.data.lights.new(f"Practical_{i + 1}", "POINT")
        pl.energy = PRACTICAL_WATTS
        pl.shadow_soft_size = 0.12
        pl.color = (1.0, 0.78, 0.5)
        coll.objects.link(bpy.data.objects.new(f"Practical_{i + 1}", pl))
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    world.use_nodes = True
    bpy.context.scene.world = world
    return coll


def apply_mood(mood, lamp_positions=(), flash=0.0):
    m = MOODS[mood]
    sun = bpy.data.objects["KeySun"]
    sun.data.energy = m["sun_strength"]
    sun.data.color = m["sun_color"]
    sun.rotation_euler = tuple(math.radians(a) for a in m["sun_rot"])
    sun.location = (0, -20, 20)
    world = bpy.context.scene.world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (*to_lin(m["world"]), 1)
        bg.inputs["Strength"].default_value = m["world_strength"] + flash
    for i in range(N_PRACTICALS):
        o = bpy.data.objects[f"Practical_{i + 1}"]
        on = m["practicals"] and i < len(lamp_positions)
        o.hide_render = o.hide_viewport = not on
        o.data.energy = PRACTICAL_WATTS
        if on:
            o.location = lamp_positions[i]
    set_toon_gain(m["toon_gain"])


# --------------------------------------------------------------------------
# Camera -------------------------------------------------------------------
# --------------------------------------------------------------------------
def make_camera(scene):
    cam = bpy.data.cameras.new("ShortCam")
    cam.sensor_fit = "HORIZONTAL"          # horizontal framing guaranteed in 9:16
    cam.sensor_width = 36.0
    cam.clip_start, cam.clip_end = 0.5, 600.0
    obj = bpy.data.objects.new("ShortCam", cam)
    get_collection("RIG").objects.link(obj)
    scene.camera = obj
    return obj


def aim_camera(obj, pos, look, lens, roll=0.0):
    obj.location = pos
    d = Vector(look) - Vector(pos)
    q = d.to_track_quat("-Z", "Y")
    q = q @ Quaternion((0, 0, 1), roll)
    obj.rotation_euler = q.to_euler()
    obj.data.lens = lens
