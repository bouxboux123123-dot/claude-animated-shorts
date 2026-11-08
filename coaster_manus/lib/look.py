"""Stylized toon look and deterministic EEVEE Next lighting rigs."""
from __future__ import annotations
import bpy
from mathutils import Vector

LIGHT_RIGS = {}


def toon_material(name, color, roughness=0.82):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color[:3], color[3] if len(color) > 3 else 1.0)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = mat.diffuse_color
    bsdf.inputs["Roughness"].default_value = roughness
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def ink_material():
    return bpy.data.materials.get("Ink | near-black") or toon_material("Ink | near-black", (0.012, 0.008, 0.018, 1))


def add_outline(obj, thickness=0.028):
    if obj.type != "MESH" or obj.get("ink_outline"):
        return obj
    mod = obj.modifiers.new("Ink | inverted hull", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.material_offset = len(obj.data.materials)
    obj.data.materials.append(ink_material())
    obj["ink_outline"] = True
    return obj


def _set_world(scene, color, strength):
    world = scene.world or bpy.data.worlds.new("Story World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    world.color = color


def create_sky_dome(name, location=(0, 0, 0), radius=180):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=radius, location=location)
    dome = bpy.context.object
    dome.name = name
    mat = bpy.data.materials.new(name + " material")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.05
    ramp.color_ramp.elements[0].color = (0.06, 0.16, 0.34, 1)
    ramp.color_ramp.elements[1].position = 0.9
    ramp.color_ramp.elements[1].color = (0.96, 0.56, 0.30, 1)
    mid = ramp.color_ramp.elements.new(0.48)
    mid.color = (0.32, 0.48, 0.72, 1)
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 0.7
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    dome.data.materials.append(mat)
    dome.hide_render = True
    dome.hide_set(True)
    return dome


def add_sun(name, location, target, energy, color):
    data = bpy.data.lights.new(name, "SUN")
    data.energy = float(energy)
    data.color = color
    data.angle = 0.12
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    obj.hide_render = True
    return obj


def add_area(name, location, target, power, color, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = float(power)
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    obj.hide_render = True
    return obj


def set_mood(scene, mood, center=(0, 0, 0)):
    """Create (once) and register per-mood lights; all rigs are toggled per shot."""
    if mood in LIGHT_RIGS:
        return
    cx, cy, cz = center
    objects = []
    dome_name = "Night | navy-to-amber sky" if mood == "night_workshop" else f"{mood} | blue-to-peach sky"
    dome = create_sky_dome(dome_name, center, 180)
    objects.append(dome)
    if mood == "night_workshop":
        LIGHT_RIGS[mood] = {"objects": objects, "world": ((0.055, 0.085, 0.18), 0.65)}
        moon = add_sun("Night | cool moon rim 35 W/m²", (cx-20, cy+30, cz+35), center, 35.0, (0.35, 0.48, 1.0))
        objects.append(moon)
        for i, (dx,dy,dz) in enumerate(((-4,-1,7),(3,2,6),(0,5,8))):
            data = bpy.data.lights.new(f"Workshop tungsten practical {i+1} | 500 W", "POINT")
            data.energy = 500.0
            data.color = (1.0, 0.48, 0.18)
            data.shadow_soft_size = 2.0
            obj = bpy.data.objects.new(data.name, data)
            bpy.context.collection.objects.link(obj)
            obj.location = (cx+dx, cy+dy, cz+dz)
            obj.hide_render = True
            objects.append(obj)
    elif mood in ("morning_fair", "coaster_climax"):
        LIGHT_RIGS[mood] = {"objects": objects, "world": ((0.32, 0.47, 0.72), 0.8)}
        objects.append(add_sun("Fairground | blazing morning sun 60 W/m²", (cx-25,cy-15,cz+40), center, 60.0, (1.0,0.82,0.57)))
        objects.append(add_sun("Fairground | sky bounce 15 W/m²", (cx+20,cy+10,cz+25), center, 15.0, (0.52,0.68,1.0)))
        objects.append(add_area("Fairground | warm horizon fill", (cx,cy-15,cz+4), (cx,cy,cz+3), 1100, (1.0,0.58,0.34), 18))
    else:
        raise ValueError(f"Unknown lighting mood: {mood}")
    for obj in objects:
        obj.hide_render = True


def activate_mood(scene, mood):
    if mood not in LIGHT_RIGS:
        raise KeyError(f"Lighting mood was not built: {mood}")
    for key, rig in LIGHT_RIGS.items():
        for obj in rig["objects"]:
            obj.hide_render = (key != mood)
    color, strength = LIGHT_RIGS[mood]["world"]
    _set_world(scene, color, strength)


def configure_render(scene, width=1080, height=1920, fps=30, samples=4):
    ids = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_compositing = False
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    try:
        scene.eevee.taa_render_samples = samples
    except Exception:
        pass
    if scene.camera and scene.camera.data:
        scene.camera.data.lens = 45
    scene.render.filepath = "//rollercoaster_short.mp4"
    scene.frame_start = 1
    scene.frame_end = 1887
