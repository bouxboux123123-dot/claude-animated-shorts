import bpy

def setup_eevee_next():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.use_compositing = False
    
    # EEVEE photometric settings
    try:
        scene.eevee.use_raytracing = True
        scene.eevee.ray_tracing_options.resolution_scale = '1'
    except Exception:
        pass

def setup_sky_dome(mood):
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    
    bg = nodes.new('ShaderNodeBackground')
    out = nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs[0], out.inputs[0])
    
    if mood == 'night_workshop':
        bg.inputs[0].default_value = (0.01, 0.02, 0.05, 1) # Dark navy
        bg.inputs[1].default_value = 1.0 # Strength
    elif mood == 'morning_fair':
        bg.inputs[0].default_value = (0.8, 0.6, 0.4, 1) # Warm horizon
        bg.inputs[1].default_value = 1.2 # Strength

def setup_lighting(mood):
    for obj in list(bpy.context.scene.collection.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
            
    if mood == 'night_workshop':
        moon = bpy.data.lights.new(name="Moon", type='SUN')
        moon.energy = 45.0 # >= 40.0 W/m^2 rule
        moon.color = (0.5, 0.7, 1.0)
        moon_obj = bpy.data.objects.new(name="Moon", object_data=moon)
        bpy.context.scene.collection.objects.link(moon_obj)
        moon_obj.rotation_euler = (0.5, 0.5, 0)
        
        prac = bpy.data.lights.new(name="Tungsten", type='POINT')
        prac.energy = 500.0 # 500W point
        prac.color = (1.0, 0.6, 0.2)
        prac_obj = bpy.data.objects.new(name="Tungsten", object_data=prac)
        bpy.context.scene.collection.objects.link(prac_obj)
        prac_obj.location = (0, 0, 5)
        
    elif mood == 'morning_fair':
        sun = bpy.data.lights.new(name="BlazingSun", type='SUN')
        sun.energy = 60.0 # >= 40.0 W/m^2 rule
        sun.color = (1.0, 0.9, 0.7)
        sun_obj = bpy.data.objects.new(name="BlazingSun", object_data=sun)
        bpy.context.scene.collection.objects.link(sun_obj)
        sun_obj.rotation_euler = (0.8, -0.4, 0.2)
        
        bounce = bpy.data.lights.new(name="SkyBounce", type='SUN')
        bounce.energy = 40.0 # Keeping above 40 threshold, soft fill
        bounce.color = (0.4, 0.6, 1.0)
        bounce_obj = bpy.data.objects.new(name="SkyBounce", object_data=bounce)
        bpy.context.scene.collection.objects.link(bounce_obj)
        bounce_obj.rotation_euler = (-2.0, 0, 0)

def create_toon_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Simple toon mapping
    diff = nodes.new('ShaderNodeBsdfDiffuse')
    diff.inputs['Color'].default_value = color
    s2rgb = nodes.new('ShaderNodeShaderToRGB')
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.32
    out = nodes.new('ShaderNodeOutputMaterial')
    
    mat.node_tree.links.new(diff.outputs[0], s2rgb.inputs[0])
    mat.node_tree.links.new(s2rgb.outputs[0], ramp.inputs[0])
    mat.node_tree.links.new(ramp.outputs[0], out.inputs[0])
    return mat

def add_ink_outline(obj):
    mat_black = bpy.data.materials.new("OutlineInk")
    mat_black.use_backface_culling = True
    mat_black.diffuse_color = (0, 0, 0, 1)
    
    obj.data.materials.append(mat_black)
    mat_idx = len(obj.data.materials) - 1
    
    mod = obj.modifiers.new(name="InkOutline", type='SOLIDIFY')
    mod.thickness = -0.05
    mod.use_flip_normals = True
    mod.material_offset = mat_idx
