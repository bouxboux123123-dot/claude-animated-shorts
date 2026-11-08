"""lib/look.py  --  LAYER 1 (LOOK)

Everything that decides how the film *looks* and nothing about what happens in it:

  * render configuration (EEVEE Next / EEVEE, compositing OFF)
  * toon materials (Shader-to-RGB banding, gain-normalised per lighting mood)
  * black inverted-hull ink outlines (Solidify + flipped normals + culled ink material)
  * photometric lighting rigs for the two moods  ('night_workshop', 'morning_fair')
  * two-tone sky dome (world shader gradient)
  * small deterministic FX pools (sparks, dust) driven purely by frame number

World convention used by every module
-------------------------------------
    X = screen right     Z = up     Y = depth (camera sits at -Y looking toward +Y)
    All paper-cutout cards live in the XZ plane, so an in-plane rotation is a rotation
    about the Y axis.  rot2()/Frame2D in props.py use that convention.
"""
import math
import random
from contextlib import contextmanager

import bpy
from mathutils import Vector

# --------------------------------------------------------------------------------------
# Photometric rules  (see "PHOTOMETRIC LIGHTING" in the brief)
# --------------------------------------------------------------------------------------
SUN_FLOOR_KEY = 40.0     # EEVEE Next: key suns must never be below 40 W/m^2
SUN_FLOOR_FILL = 10.0    # rim / fill suns: never in the dead 1-5 W/m^2 zone
STRICT_SUN_FLOOR = False  # True -> clamp EVERY sun (even rim/fill) up to SUN_FLOOR_KEY
WORLD_MIN_STRENGTH = 0.5  # "never plunge the scene into a black void"

MOODS = {
    "night_workshop": {
        "sky_zenith": (0.012, 0.020, 0.075),   # dark navy
        "sky_horizon": (0.040, 0.065, 0.170),
        "sky_strength": 1.0,
        "toon_gain": 0.6,                       # divides lit radiance before banding
        "suns": [
            {"name": "moon_rim", "energy": 35.0, "color": (0.58, 0.72, 1.00),
             "dir": (-0.35, -0.80, -0.45), "role": "rim", "angle_deg": 1.2},
        ],
        "points": [  # tungsten practicals, 500 W each, hung in front of the card plane
            {"name": "tungsten_L", "energy": 500.0, "color": (1.00, 0.60, 0.28),
             "anchor": "ws.lamp_L", "offset": (0.0, -4.5, -0.8), "radius": 0.30},
            {"name": "tungsten_R", "energy": 500.0, "color": (1.00, 0.60, 0.28),
             "anchor": "ws.lamp_R", "offset": (0.0, -4.5, -0.8), "radius": 0.30},
        ],
    },
    "morning_fair": {
        "sky_zenith": (0.30, 0.55, 0.95),
        "sky_horizon": (1.00, 0.72, 0.45),      # warm horizon
        "sky_strength": 1.2,
        "toon_gain": 40.0,
        "suns": [
            {"name": "sun_key", "energy": 60.0, "color": (1.00, 0.93, 0.80),
             "dir": (0.50, 0.55, -0.60), "role": "key", "angle_deg": 0.8},
            {"name": "sky_bounce", "energy": 15.0, "color": (0.70, 0.82, 1.00),
             "dir": (-0.45, 0.25, 0.35), "role": "fill", "angle_deg": 8.0},
        ],
        "points": [],
    },
}

LIGHTS = {m: [] for m in MOODS}
_WORLD = {}


# --------------------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------------------
def eevee_engine_id():
    """Blender 4.2-4.5 call it BLENDER_EEVEE_NEXT, 5.x renamed it back to BLENDER_EEVEE."""
    ids = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if cand in ids:
            return cand
    raise RuntimeError("No EEVEE engine available: %s" % ids)


def _try(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception:
        return None


def _use_nodes(idb):
    _try(setattr, idb, "use_nodes", True)   # deprecated (always-on) in 5.x, still needed < 5.0


_COLL = []


@contextmanager
def into(coll):
    """Everything created inside the `with` block is linked into `coll`."""
    _COLL.append(coll)
    try:
        yield coll
    finally:
        _COLL.pop()


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def _link(obj):
    (_COLL[-1] if _COLL else bpy.context.scene.collection).objects.link(obj)


def new_empty(name, parent=None, loc=(0, 0, 0), display="PLAIN_AXES", size=0.15):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = display
    o.empty_display_size = size
    _link(o)
    o.parent = parent
    o.location = loc
    return o


# --------------------------------------------------------------------------------------
# render configuration
# --------------------------------------------------------------------------------------
def configure_render(sc, res=(1920, 1080), samples=24, fps=30, frame_count=1887):
    sc.render.engine = eevee_engine_id()
    sc.render.resolution_x, sc.render.resolution_y = int(res[0]), int(res[1])
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 0, frame_count - 1
    sc.render.use_compositing = False     # direct, reliable frame generation (cloud workers)
    sc.render.use_sequencer = False
    sc.render.film_transparent = False
    im = sc.render.image_settings
    im.file_format, im.color_mode, im.color_depth = "PNG", "RGB", "8"
    sc.view_settings.view_transform = "Standard"   # toon look: no filmic/AgX roll-off
    _try(setattr, sc.view_settings, "look", "None")
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.display_settings.display_device = "sRGB"
    ee = sc.eevee
    _try(setattr, ee, "taa_render_samples", int(samples))
    _try(setattr, ee, "use_raytracing", False)    # Shader-to-RGB toon ramps need it off
    _try(setattr, ee, "use_shadows", True)
    _try(setattr, ee, "use_gtao", False)
    _try(setattr, sc.render, "filter_size", 0.8)


# --------------------------------------------------------------------------------------
# materials
# --------------------------------------------------------------------------------------
def _node(nt, idname, x=0, y=0, **props):
    n = nt.nodes.new(idname)
    n.location = (x, y)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def toon_material(name, rgb, band_cuts=(0.10, 0.45), shade=(0.40, 0.72, 1.0)):
    """3-band toon: Diffuse -> Shader-to-RGB -> luminance / ToonGain -> constant ramp -> x base colour.

    The 'ToonGain' value node is rewritten by set_mood() so that the banding thresholds stay
    meaningful under the very large photometric values (Sun 60 W/m^2, 500 W points)."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    _use_nodes(m)
    nt = m.node_tree
    nt.nodes.clear()
    diff = _node(nt, "ShaderNodeBsdfDiffuse", -900, 0)
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2r = _node(nt, "ShaderNodeShaderToRGB", -700, 0)
    bw = _node(nt, "ShaderNodeRGBToBW", -520, 0)
    gain = _node(nt, "ShaderNodeValue", -700, -200, label="ToonGain", name="ToonGain")
    gain.outputs[0].default_value = 1.0
    div = _node(nt, "ShaderNodeMath", -340, 0, operation="DIVIDE")
    ramp = _node(nt, "ShaderNodeValToRGB", -160, 0)
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[1].position = 0.0, band_cuts[1]
    els.new(band_cuts[0])
    for e, pos, g in zip(list(els), (0.0, band_cuts[0], band_cuts[1]), shade):
        e.position = pos
        e.color = (g, g, min(1.0, g * 1.04), 1.0)
    mix = _node(nt, "ShaderNodeMix", 60, 0, data_type="RGBA", blend_type="MULTIPLY")
    mix.inputs[0].default_value = 1.0
    mix.inputs[7].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    emi = _node(nt, "ShaderNodeEmission", 260, 0)
    out = _node(nt, "ShaderNodeOutputMaterial", 440, 0)
    L = nt.links.new
    L(diff.outputs["BSDF"], s2r.inputs["Shader"])
    L(s2r.outputs["Color"], bw.inputs["Color"])
    L(bw.outputs["Val"], div.inputs[0])
    L(gain.outputs[0], div.inputs[1])
    L(div.outputs[0], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], mix.inputs[6])
    L(mix.outputs[2], emi.inputs["Color"])
    L(emi.outputs["Emission"], out.inputs["Surface"])
    return m


def flat_material(name, rgb, strength=1.0):
    """Unlit flat colour (windows, bulbs, sparks, black ink, eyes)."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    _use_nodes(m)
    nt = m.node_tree
    nt.nodes.clear()
    emi = _node(nt, "ShaderNodeEmission", 0, 0)
    emi.inputs["Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    emi.inputs["Strength"].default_value = strength
    out = _node(nt, "ShaderNodeOutputMaterial", 200, 0)
    nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return m


def ink_material():
    m = flat_material("INK_BLACK", (0.0, 0.0, 0.0), 1.0)
    m.use_backface_culling = True            # inverted hull: only the far shell shows
    return m


# --------------------------------------------------------------------------------------
# 2D polygon helpers (all points are (x, z) in the card plane)
# --------------------------------------------------------------------------------------
def area2(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def ccw(pts):
    pts = [tuple(p) for p in pts]
    return pts if area2(pts) >= 0 else pts[::-1]


def ellipse(rx, rz, n=18, cx=0.0, cz=0.0):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cz + rz * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def rect(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def capsule(w, length, n=5):
    """Vertical capsule hanging DOWN from its pivot at (0,0) to (0,-length)."""
    r = w / 2.0
    top = [(r * math.cos(math.pi * i / n), r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    bot = [(-r * math.cos(math.pi * i / n), -length - r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    return top + bot


def gear(r_out, r_in, teeth=8):
    pts = []
    for i in range(teeth * 2):
        a = math.pi * i / teeth
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def build_card(name, pts, mat, depth=0.06, ink=0.035, parent=None, loc=(0, 0, 0),
               rot_y=0.0, scale=(1, 1, 1)):
    """Flat paper-cutout slab (front face toward the camera at -Y) with an inverted-hull outline.

    Hull = Solidify(offset=+1, flipped normals) on the same mesh, drawn with the culled black ink
    material in slot 1.  Because the slab has vertex normals with an in-plane component, the shell
    grows sideways and shows as a clean silhouette line around the card."""
    pts = ccw(pts)
    n, h = len(pts), depth / 2.0
    verts = [(x, -h, z) for x, z in pts] + [(x, h, z) for x, z in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, n + i, n + j, j))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    _link(obj)
    obj.parent = parent
    obj.location = loc
    obj.rotation_euler = (0.0, rot_y, 0.0)
    obj.scale = scale
    if ink and ink > 0:
        add_ink_hull(obj, ink)
    return obj


def add_ink_hull(obj, thickness=0.035):
    if len(obj.data.materials) < 2:
        obj.data.materials.append(ink_material())
    mod = obj.modifiers.new("ink_hull", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = 1
    return mod


# --------------------------------------------------------------------------------------
# sky dome + lighting
# --------------------------------------------------------------------------------------
def build_world():
    """Two-tone sky dome: horizon colour -> zenith colour keyed on the view-direction Z."""
    w = bpy.data.worlds.new("SkyDome")
    _use_nodes(w)
    nt = w.node_tree
    nt.nodes.clear()
    tc = _node(nt, "ShaderNodeTexCoord", -900, 0)
    sep = _node(nt, "ShaderNodeSeparateXYZ", -720, 0)
    mr = _node(nt, "ShaderNodeMapRange", -540, 0)
    mr.clamp = True
    mr.inputs["From Min"].default_value = -0.10
    mr.inputs["From Max"].default_value = 0.75
    ramp = _node(nt, "ShaderNodeValToRGB", -340, 0)
    ramp.color_ramp.interpolation = "EASE"
    bg = _node(nt, "ShaderNodeBackground", -100, 0)
    out = _node(nt, "ShaderNodeOutputWorld", 100, 0)
    L = nt.links.new
    L(tc.outputs["Object"], sep.inputs["Vector"])   # in a world shader this is the view direction
    L(sep.outputs["Z"], mr.inputs["Value"])
    L(mr.outputs["Result"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], bg.inputs["Color"])
    L(bg.outputs["Background"], out.inputs["Surface"])
    bpy.context.scene.world = w
    _WORLD.update(world=w, ramp=ramp, bg=bg)
    return w


def _aim(obj, direction):
    obj.rotation_euler = Vector(direction).normalized().to_track_quat("-Z", "Y").to_euler()


def _sun_energy(spec):
    e = float(spec["energy"])
    floor = SUN_FLOOR_KEY if (STRICT_SUN_FLOOR or spec["role"] == "key") else SUN_FLOOR_FILL
    return max(e, floor)


def build_lighting_rigs(anchors):
    """Create both rigs once (all lights live in collection LIGHTS); set_mood() toggles them."""
    coll = new_collection("LIGHTS")
    with into(coll):
        for mood, cfg in MOODS.items():
            for s in cfg["suns"]:
                ld = bpy.data.lights.new("%s.%s" % (mood, s["name"]), "SUN")
                ld.energy = _sun_energy(s)
                ld.color = s["color"]
                ld.angle = math.radians(s["angle_deg"])
                _try(setattr, ld, "use_shadow", s["role"] != "fill")
                o = bpy.data.objects.new("L.%s.%s" % (mood, s["name"]), ld)
                _link(o)
                _aim(o, s["dir"])
                LIGHTS[mood].append(o)
            for p in cfg["points"]:
                ld = bpy.data.lights.new("%s.%s" % (mood, p["name"]), "POINT")
                ld.energy = p["energy"]
                ld.color = p["color"]
                ld.shadow_soft_size = p["radius"]
                _try(setattr, ld, "use_shadow", True)
                o = bpy.data.objects.new("L.%s.%s" % (mood, p["name"]), ld)
                _link(o)
                ax = Vector(anchors.get(p["anchor"]))
                o.location = ax + Vector(p["offset"])
                LIGHTS[mood].append(o)


def assert_photometric(mood):
    """Hard guard used by scene.py before every render and by --selftest."""
    cfg = MOODS[mood]
    lights = LIGHTS[mood]
    assert lights, "mood %s has no lights (black void)" % mood
    assert cfg["sky_strength"] >= WORLD_MIN_STRENGTH, "world too dim in %s" % mood
    for o in lights:
        if o.data.type == "SUN":
            floor = SUN_FLOOR_KEY if (STRICT_SUN_FLOOR or "key" in o.name) else SUN_FLOOR_FILL
            assert o.data.energy >= floor, "%s sun %.1f W/m^2 below floor %.1f" % (o.name, o.data.energy, floor)
    keys = [o for o in lights if o.data.type == "SUN" and o.data.energy >= SUN_FLOOR_KEY]
    pts = [o for o in lights if o.data.type == "POINT"]
    assert keys or pts, "mood %s lacks a primary light" % mood


def set_mood(mood):
    cfg = MOODS[mood]
    for m, objs in LIGHTS.items():
        for o in objs:
            o.hide_render = (m != mood)
            o.hide_viewport = (m != mood)
    ramp, bg = _WORLD["ramp"], _WORLD["bg"]
    els = ramp.color_ramp.elements
    els[0].position, els[1].position = 0.0, 1.0
    els[0].color = (*cfg["sky_horizon"], 1.0)
    els[1].color = (*cfg["sky_zenith"], 1.0)
    bg.inputs["Strength"].default_value = cfg["sky_strength"]
    for mat in bpy.data.materials:
        if mat.node_tree and "ToonGain" in mat.node_tree.nodes:
            mat.node_tree.nodes["ToonGain"].outputs[0].default_value = cfg["toon_gain"]
    assert_photometric(mood)


# --------------------------------------------------------------------------------------
# deterministic FX pools: every particle position is a pure function of (burst, frame)
# --------------------------------------------------------------------------------------
class FXPool:
    def __init__(self, name, kind, n_bursts, per_burst, mat, shape, life):
        self.kind, self.n_bursts, self.per, self.life = kind, n_bursts, per_burst, life
        self.coll = new_collection("FX_" + name)
        self.objs = []
        with into(self.coll):
            for i in range(n_bursts * per_burst):
                o = build_card("%s.%03d" % (name, i), shape, mat, depth=0.02, ink=0)
                o.hide_render = True
                self.objs.append(o)

    def update(self, bursts, f, fps):
        for o in self.objs:
            o.hide_render = True
        for b in bursts:
            if b["kind"] != self.kind:
                continue
            age = (f - b["f0"]) / float(fps)
            if age < 0 or age > self.life:
                continue
            rng = random.Random(b["seed"])
            slot = b["slot"] % self.n_bursts
            ox, oy, oz = b["origin"]
            k = b["strength"]
            for i in range(self.per):
                o = self.objs[slot * self.per + i]
                a = rng.uniform(0.35, math.pi - 0.35)
                sp = rng.uniform(3.0, 9.0) * k
                vy = rng.uniform(-3.0, 0.0)
                if self.kind == "sparks":
                    vx, vz = math.cos(a) * sp, math.sin(a) * sp
                    x = ox + vx * age
                    z = oz + vz * age - 7.0 * age * age   # g = 14 m/s^2
                    cur_vz = vz - 14.0 * age
                    o.rotation_euler = (0.0, -math.atan2(cur_vz, vx), 0.0)
                    s = (0.20 + 0.035 * sp) * max(0.0, 1.0 - age / self.life)
                    o.scale = (s, 1.0, s)
                else:   # dust puffs rise, drift and shrink
                    vx, vz = math.cos(a) * sp * 0.35, 0.6 + math.sin(a) * sp * 0.25
                    x = ox + vx * age
                    z = oz + vz * age
                    s = (0.25 + 0.55 * math.sin(math.pi * age / self.life)) * (0.6 + 0.4 * k)
                    o.rotation_euler = (0.0, 0.0, 0.0)
                    o.scale = (s, 1.0, s)
                o.location = (x, oy + vy * age * 0.3 - 0.3, z)
                o.hide_render = False
