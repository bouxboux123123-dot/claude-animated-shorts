"""LOOK module for Railroads: Desert canyon lighting, toon shaders, and compositor.
Blender 5.2 (EEVEE Next), headless compatible.
"""
import bpy
import math

BAKER_MILLER = (0.96, 0.56, 0.76)
DESERT_SAND = (0.82, 0.58, 0.38)
DESERT_ROCK = (0.68, 0.36, 0.22)
DESERT_DARK = (0.35, 0.18, 0.12)
STEEL_RAIL = (0.75, 0.78, 0.85)
STEEL_DARK = (0.28, 0.30, 0.36)
WOOD_TIE = (0.38, 0.26, 0.18)
BALLAST_GREY = (0.55, 0.52, 0.48)
GOLD_FINISH = (1.0, 0.82, 0.18)
SKY_DAWN = (0.42, 0.28, 0.36)
SKY_NOON = (0.28, 0.48, 0.78)

_MATS = {}

def toon_mat(name, rgb, ink=True):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*rgb[:3], 1.0)
    bsdf.inputs['Roughness'].default_value = 0.85
    bsdf.inputs['Metallic'].default_value = 0.0
    
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    _MATS[name] = mat
    return mat

def glow(name, rgb, strength=5.0):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs[0].default_value = (*rgb[:3], 1.0)
    em.inputs[1].default_value = strength
    
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    
    _MATS[name] = mat
    return mat

def ink_hull(obj, width=0.015):
    """Inverted hull black ink outline modifier."""
    mod = obj.modifiers.new(name="InkHull", type='SOLIDIFY')
    mod.thickness = width
    mod.offset = 1.0
    mod.use_flip_normals = True
    
    ink_m = _MATS.get('pe_ink')
    if not ink_m:
        ink_m = bpy.data.materials.new('pe_ink')
        ink_m.use_nodes = True
        nt = ink_m.node_tree
        nt.nodes.clear()
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.015, 1.0)
        bsdf.inputs['Roughness'].default_value = 1.0
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        _MATS['pe_ink'] = ink_m
        
    if ink_m.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(ink_m)
        
    idx = [i for i, m in enumerate(obj.data.materials) if m and m.name == ink_m.name][0]
    mod.material_offset = idx
    return obj

def setup_render(sc):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 720
    sc.render.resolution_y = 1280
    sc.render.resolution_percentage = 100
    sc.render.fps = 30
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.look = 'Medium High Contrast'
    
    # World background: deep atmospheric desert gradient
    world = bpy.data.worlds.new('Railroad_World')
    sc.world = world
    world.use_nodes = True
    wnt = world.node_tree
    bg = wnt.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.04, 0.04, 0.06, 1.0)
        bg.inputs['Strength'].default_value = 0.25 # Clean low ambient, NO flat wash!
    return world

def setup_lighting(c, time_of_day='noon'):
    """High-contrast cinematic 3-point desert lighting (Key:Fill >= 4:1)."""
    # 1. Main Sun (Key Light)
    sun_data = bpy.data.lights.new('Sun_Key', 'SUN')
    sun_data.energy = 5.5
    sun_data.color = (1.0, 0.96, 0.88) if time_of_day == 'noon' else (1.0, 0.65, 0.45)
    sun_data.angle = math.radians(1.2) # Sharp shadows
    sun_ob = bpy.data.objects.new('Sun_Key', sun_data)
    sun_ob.rotation_euler = (math.radians(55), math.radians(15), math.radians(-35))
    c.objects.link(sun_ob)
    
    # 2. Canyon Sky Bounce (Fill Light, Soft & Directional, 1/4 strength)
    fill_data = bpy.data.lights.new('Sky_Fill', 'SUN')
    fill_data.energy = 1.2
    fill_data.color = (0.45, 0.65, 0.95) # Sky blue bounce
    fill_ob = bpy.data.objects.new('Sky_Fill', fill_data)
    fill_ob.rotation_euler = (math.radians(-45), math.radians(20), math.radians(145))
    c.objects.link(fill_ob)
    
    # 3. Ground Warm Reflector (Canyon Red Sand Rim)
    rim_data = bpy.data.lights.new('Sand_Rim', 'SUN')
    rim_data.energy = 0.8
    rim_data.color = (0.9, 0.45, 0.25)
    rim_ob = bpy.data.objects.new('Sand_Rim', rim_data)
    rim_ob.rotation_euler = (math.radians(15), math.radians(-40), math.radians(90))
    c.objects.link(rim_ob)
    
    return sun_ob, fill_ob, rim_ob

def setup_compositor(sc):
    try:
        if hasattr(sc, 'compositing_node_group'):
            nt = bpy.data.node_groups.new('RR_comp', 'CompositorNodeTree')
            sc.compositing_node_group = nt
            return nt
    except Exception:
        pass
    return None
