"""LOOK module for "Why Roller Coasters Don't Fly Off The Tracks".
Toon materials, ink outlines, photometric lighting rigs, two-tone sky dome.
Blender 5.2 (EEVEE Next), headless compatible.

Architecture rules enforced here:
  * EEVEE Next engine; every SUN light energy >= 40.0 W/m^2.
  * Direct reliable frame generation: compositing disabled.
  * Never a black void: every mood keeps a lit sky dome.
"""
import bpy
import math
from mathutils import Color

INK = (0.02, 0.02, 0.03, 1.0)          # black inverted-hull ink outline
PAPER_WHITE = (0.96, 0.94, 0.90)       # 2D card base

# Mood palettes ---------------------------------------------------------------
NIGHT = dict(
    sky_zenith=(0.015, 0.02, 0.05),   # deep navy
    sky_horizon=(0.04, 0.05, 0.09),
    sun_color=(0.70, 0.80, 1.00),      # cool moon rim
    sun_energy=40.0,                   # >= 40.0 W/m^2 (rule 4)
    practical_color=(1.0, 0.70, 0.40), # tungsten 500W
    practical_energy=500.0,
    sky_strength=1.0,
)
MORNING = dict(
    sky_zenith=(0.55, 0.75, 1.00),     # blazing morning sky
    sky_horizon=(1.00, 0.60, 0.25),    # warm horizon
    sun_color=(1.00, 0.94, 0.80),
    sun_energy=60.0,                   # >= 40.0 W/m^2 (rule 4)
    bounce_color=(0.70, 0.85, 1.00),
    bounce_energy=40.0,
    sky_strength=1.2,
)

_MATS = {}


def _mat(name, rgb, metallic=0.0, roughness=0.85, emission=0.0):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*rgb[:3], 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if emission > 0.0:
        bsdf.inputs['Emission Strength'].default_value = emission
        bsdf.inputs['Emission Color'].default_value = (*rgb[:3], 1.0)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    _MATS[name] = mat
    return mat


def toon_mat(name, rgb, ink=True, metallic=0.0, roughness=1.0):
    """Flat, painted toon material with optional metal/roughness tuning."""
    return _mat(name, rgb, metallic=metallic, roughness=roughness)


def ink_hull(obj, width=0.015):
    """Black inverted-hull ink outline via a Solidify + flip-normals modifier."""
    mod = obj.modifiers.new(name="InkHull", type='SOLIDIFY')
    mod.thickness = width
    mod.offset = 1.0          # push the hull outward
    mod.use_flip_normals = True
    mod.use_rim = False
    ink_m = _MATS.get('pe_ink')
    if not ink_m:
        ink_m = _mat('pe_ink', INK[:3], roughness=1.0)
        _MATS['pe_ink'] = ink_m
    if ink_m.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(ink_m)
    idx = [i for i, m in enumerate(obj.data.materials)
           if m and m.name == ink_m.name][0]
    mod.material_offset = idx
    return obj


def anchor_empty(collection, name, location=(0, 0, 0), parent=None):
    """Named empty used as a prop/character socket or set anchor."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location = location
    if parent is not None:
        e.parent = parent
    collection.objects.link(e)
    return e


def setup_render(sc):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 720
    sc.render.resolution_y = 1280
    sc.render.resolution_percentage = 100
    sc.render.fps = 30
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.use_compositing = False          # direct frame generation
    sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.look = 'Medium High Contrast'
    if hasattr(sc, 'eevee'):
        try:
            sc.eevee.taa_render_samples = 16
        except Exception:
            pass


def setup_sky(sc, mood='workshop_night'):
    """Two-tone sky dome: never a black void."""
    pal = NIGHT if mood in ('night_workshop', 'workshop_night') else MORNING
    world = bpy.data.worlds.new('World')
    sc.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()
    
    tex = wnt.nodes.new('ShaderNodeTexCoord')
    sp = wnt.nodes.new('ShaderNodeSeparateXYZ')
    mr = wnt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.0
    mr.inputs['From Max'].default_value = 0.5
    
    mix = wnt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    
    top = wnt.nodes.new('ShaderNodeRGB')
    top.outputs[0].default_value = (*pal['sky_zenith'], 1.0)
    
    hor = wnt.nodes.new('ShaderNodeRGB')
    hor.outputs[0].default_value = (*pal['sky_horizon'], 1.0)
    
    bg = wnt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = pal['sky_strength']
    out = wnt.nodes.new('ShaderNodeOutputWorld')
    
    wnt.links.new(tex.outputs['Generated'], sp.inputs[0])
    wnt.links.new(sp.outputs['Z'], mr.inputs['Value'])
    wnt.links.new(mr.outputs[0], mix.inputs[0])
    wnt.links.new(hor.outputs[0], mix.inputs[6])
    wnt.links.new(top.outputs[0], mix.inputs[7])
    wnt.links.new(mix.outputs[2], bg.inputs['Color'])
    wnt.links.new(bg.outputs[0], out.inputs['Surface'])
    
    return world, pal


def _link(collection, obj):
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    return obj


def setup_lighting(sc, collection, mood='workshop_night'):
    """Photometric rig per mood. All SUN lights >= 40.0 W/m^2."""
    pal = NIGHT if mood in ('night_workshop', 'workshop_night') else MORNING
    lights = []

    # Sun / moon rim (W/m^2) - must be >= 40.0 in EEVEE Next.
    sun = bpy.data.lights.new('Sun_Rim', 'SUN')
    sun.energy = pal['sun_energy']
    sun.color = pal['sun_color']
    sun.angle = math.radians(1.5)
    sun_ob = bpy.data.objects.new('Sun_Rim', sun)
    sun_ob.rotation_euler = (math.radians(60), math.radians(10), math.radians(-40))
    _link(collection, sun_ob)
    lights.append(sun_ob)

    # Practical tungsten / bounce fill (W for point, W/m^2 for sun).
    if mood in ('night_workshop', 'workshop_night'):
        pt = bpy.data.lights.new('Tungsten_Practical', 'POINT')
        pt.energy = pal['practical_energy']
        pt.color = pal['practical_color']
        pt_ob = bpy.data.objects.new('Tungsten_Practical', pt)
        pt_ob.location = (-2.5, 1.5, 2.5)
        _link(collection, pt_ob)
        lights.append(pt_ob)
    else:
        bounce = bpy.data.lights.new('Sky_Bounce', 'SUN')
        bounce.energy = pal['bounce_energy']
        bounce.color = pal['bounce_color']
        bounce.angle = math.radians(4.0)
        bounce_ob = bpy.data.objects.new('Sky_Bounce', bounce)
        bounce_ob.rotation_euler = (math.radians(-20), math.radians(30), math.radians(100))
        _link(collection, bounce_ob)
        lights.append(bounce_ob)

    return lights
