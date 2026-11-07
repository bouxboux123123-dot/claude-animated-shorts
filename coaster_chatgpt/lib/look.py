"""Toon look-development and photometric lighting for Blender 5.2 EEVEE."""
from __future__ import annotations

import bpy
from mathutils import Vector

from .utils import ensure_collection, link_only, look_at

PALETTE = {
    'ink': (0.012, 0.018, 0.035, 1),
    'navy': (0.018, 0.035, 0.095, 1),
    'wood_dark': (0.16, 0.065, 0.035, 1),
    'wood': (0.43, 0.19, 0.075, 1),
    'wood_light': (0.78, 0.43, 0.16, 1),
    'steel': (0.18, 0.25, 0.32, 1),
    'steel_light': (0.53, 0.66, 0.72, 1),
    'cream': (0.95, 0.83, 0.61, 1),
    'red': (0.72, 0.06, 0.07, 1),
    'coral': (0.96, 0.23, 0.16, 1),
    'gold': (1.0, 0.56, 0.10, 1),
    'teal': (0.035, 0.34, 0.36, 1),
    'green': (0.13, 0.39, 0.22, 1),
    'blue': (0.08, 0.22, 0.62, 1),
    'skin': (0.83, 0.49, 0.31, 1),
    'skin_light': (1.0, 0.72, 0.49, 1),
    'white': (0.94, 0.94, 0.86, 1),
    'black': (0.025, 0.025, 0.035, 1),
}


def _set_input(node, names, value):
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def make_toon_material(name: str, colors=None, roughness=0.8):
    """Create a three-band EEVEE toon material using Shader-to-RGB."""
    if colors is None:
        colors = [PALETTE['wood_dark'], PALETTE['wood'], PALETTE['wood_light']]
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = colors[1]
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (640, 0)
    diffuse = nt.nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (-500, 0)
    diffuse.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1)
    diffuse.inputs['Roughness'].default_value = roughness
    shader_rgb = nt.nodes.new('ShaderNodeShaderToRGB')
    shader_rgb.location = (-270, 0)
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-40, 0)
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = colors[0]
    mid = ramp.color_ramp.elements.new(0.48)
    mid.color = colors[1]
    high = ramp.color_ramp.elements.new(0.78)
    high.color = colors[2]
    principled = nt.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (350, 0)
    _set_input(principled, ['Roughness'], roughness)
    _set_input(principled, ['Metallic'], 0.0)
    nt.links.new(diffuse.outputs['BSDF'], shader_rgb.inputs['Shader'])
    nt.links.new(shader_rgb.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    nt.links.new(principled.outputs['BSDF'], out.inputs['Surface'])
    return mat


def make_flat_material(name: str, color, roughness=0.86, emission=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    if emission > 0:
        shader = nodes.new('ShaderNodeEmission')
        shader.inputs['Color'].default_value = color
        shader.inputs['Strength'].default_value = emission
    else:
        shader = nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Base Color'].default_value = color
        shader.inputs['Roughness'].default_value = roughness
    mat.node_tree.links.new(shader.outputs[0], out.inputs['Surface'])
    return mat


def make_ink_material(name='MAT_Ink_Black'):
    return make_flat_material(name, PALETTE['ink'], roughness=1.0)


def add_ink_outline(obj, thickness=0.035, ink_material=None):
    """Inverted-hull silhouette outline for flat cartoon cards and props."""
    ink_material = ink_material or make_ink_material()
    if len(obj.data.materials) == 0:
        obj.data.materials.append(ink_material)
    obj.data.materials.append(ink_material)
    solid = obj.modifiers.new('INK_Inverted_Hull', 'SOLIDIFY')
    solid.thickness = thickness
    solid.offset = 1.0
    solid.use_rim = True
    solid.material_offset = len(obj.data.materials) - 1
    solid.material_offset_rim = len(obj.data.materials) - 1
    return solid


def create_two_tone_sky_dome(collection, name, lower_color, upper_color, strength=1.0):
    """Large emissive sphere with a vertical two-tone horizon-to-zenith ramp."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=80.0, location=(0, 0, 0))
    dome = bpy.context.object
    dome.name = name
    link_only(dome, collection)
    dome.display_type = 'TEXTURED'
    for p in dome.data.polygons:
        p.use_smooth = True
    mat = bpy.data.materials.new(name + '_SkyMat')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    geo = nodes.new('ShaderNodeNewGeometry')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    mapper = nodes.new('ShaderNodeMapRange')
    mapper.inputs['From Min'].default_value = -12.0
    mapper.inputs['From Max'].default_value = 30.0
    mapper.inputs['To Min'].default_value = 0.0
    mapper.inputs['To Max'].default_value = 1.0
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = lower_color
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = upper_color
    ramp.color_ramp.interpolation = 'EASE'
    emit = nodes.new('ShaderNodeEmission')
    emit.inputs['Strength'].default_value = strength
    mat.node_tree.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    mat.node_tree.links.new(sep.outputs['Z'], mapper.inputs['Value'])
    mat.node_tree.links.new(mapper.outputs['Result'], ramp.inputs['Fac'])
    mat.node_tree.links.new(ramp.outputs['Color'], emit.inputs['Color'])
    mat.node_tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    dome.data.materials.append(mat)
    dome['sky_strength'] = float(strength)
    return dome


def _add_sun(collection, name, energy, color, location, target, angle=0.12):
    light_data = bpy.data.lights.new(name, type='SUN')
    light_data.energy = max(40.0, float(energy))  # Hard floor: no under-powered Sun lamps.
    light_data.color = color
    light_data.angle = angle
    obj = bpy.data.objects.new(name, light_data)
    collection.objects.link(obj)
    obj.location = Vector(location)
    look_at(obj, target)
    return obj


def _add_point(collection, name, energy, color, location, radius=1.2):
    data = bpy.data.lights.new(name, type='POINT')
    data.energy = float(energy)
    data.color = color
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = Vector(location)
    return obj


def _add_area(collection, name, energy, color, location, target, size=8.0, shape='DISK'):
    data = bpy.data.lights.new(name, type='AREA')
    data.energy = float(energy)
    data.color = color
    data.shape = shape
    data.size = size
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = Vector(location)
    look_at(obj, target)
    return obj


def build_lighting_rigs(scene):
    """Create both moods once; frame evaluation only toggles their collections."""
    night = ensure_collection('LIGHTING_night_workshop')
    morning = ensure_collection('LIGHTING_morning_fair')
    night_sky_col = ensure_collection('SKY_night_workshop')
    morning_sky_col = ensure_collection('SKY_morning_fair')

    _add_point(night, 'Night_Practical_Tungsten_500W', 500.0, (1.0, 0.48, 0.19), (-3.8, -1.0, 4.5), 1.6)
    _add_point(night, 'Night_Workbench_Bounce_180W', 180.0, (1.0, 0.66, 0.34), (-5.0, -2.0, 2.2), 1.2)
    _add_sun(night, 'Night_Moon_Rim_40Wm2', 40.0, (0.32, 0.52, 1.0), (5, 4, 9), (0, 0, 2), 0.18)
    _add_area(night, 'Night_Cool_Fill', 260.0, (0.18, 0.34, 0.72), (0, -8, 5), (0, 0, 2), 7.0)
    create_two_tone_sky_dome(
        night_sky_col, 'SkyDome_Night_Navy',
        (0.055, 0.09, 0.19, 1), (0.012, 0.025, 0.075, 1), 1.0
    )

    _add_sun(morning, 'Morning_Sun_60Wm2', 60.0, (1.0, 0.79, 0.53), (-5, -8, 10), (0, 0, 1), 0.10)
    # The requested 15 W sky bounce is an AREA light, not a second Sun below the 40 W minimum.
    _add_area(morning, 'Morning_Sky_Dome_Fill_15W', 15.0, (0.56, 0.72, 1.0), (0, -4, 8), (0, 0, 1), 12.0)
    _add_area(morning, 'Morning_Front_Softbox', 420.0, (1.0, 0.77, 0.48), (0, -10, 6), (0, 0, 2), 9.0)
    create_two_tone_sky_dome(
        morning_sky_col, 'SkyDome_Morning_Warm_Horizon',
        (1.0, 0.57, 0.25, 1), (0.18, 0.46, 0.82, 1), 1.2
    )

    # Keep both worlds readable even if a dome is hidden by a collection toggle.
    world = scene.world or bpy.data.worlds.new('Story_World')
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (0.08, 0.12, 0.22, 1)
    bg.inputs['Strength'].default_value = 0.35

    rigs = {
        'night_workshop': (night, night_sky_col),
        'morning_fair': (morning, morning_sky_col),
    }
    apply_lighting_mood(scene, 'night_workshop', rigs)
    return rigs


def apply_lighting_mood(scene, mood, rigs):
    if mood not in rigs:
        mood = 'morning_fair'
    for name, (light_col, sky_col) in rigs.items():
        active = name == mood
        light_col.hide_render = not active
        light_col.hide_viewport = not active
        sky_col.hide_render = not active
        sky_col.hide_viewport = not active
    if scene.world and scene.world.use_nodes:
        bg = scene.world.node_tree.nodes.get('Background')
        if bg:
            if mood == 'night_workshop':
                bg.inputs['Color'].default_value = (0.035, 0.055, 0.12, 1)
                bg.inputs['Strength'].default_value = 0.38
            else:
                bg.inputs['Color'].default_value = (0.35, 0.47, 0.65, 1)
                bg.inputs['Strength'].default_value = 0.45
