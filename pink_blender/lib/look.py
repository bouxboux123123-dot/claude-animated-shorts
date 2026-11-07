"""LOOK module (v3 Pink Edition): toon materials, hull ink, moods, compositor grade. Blender 5.2, EEVEE.
"""
import bpy, math, random, os
from mathutils import Vector

SET_X = {'corridor': 0.0, 'mix_bench': 100.0, 'paint_wall': 200.0, 'pink_cell': 300.0,
         'arm_wrestle': 400.0, 'night_station': 500.0, 'blackboard': 600.0}
INK_RGB = (0.012, 0.01, 0.03, 1.0)

MOODS = {
    'prison': dict(top=(0.10, 0.16, 0.25), hor=(0.42, 0.50, 0.58), wstr=1.0,
                   sun=((0.85, 0.95, 1.0), 2.2, (-25, 60)), fill=((0.65, 0.75, 0.85), 100.0), lamp=((1.0, 0.8, 0.5), 0.0),
                   exp=0.0, sat=1.1, con=0.28, gam=1.0, gain=(0.92, 0.96, 1.05), lift=(1.0, 1.0, 1.0), vig=0.35, haze=0.12),
    'workshop': dict(top=(0.18, 0.28, 0.50), hor=(0.72, 0.68, 0.58), wstr=1.0,
                     sun=((1.0, 0.85, 0.65), 2.8, (-40, 50)), fill=((0.80, 0.78, 0.75), 110.0), lamp=((1.0, 0.8, 0.5), 0.0),
                     exp=0.0, sat=1.25, con=0.30, gam=1.0, gain=(1.05, 0.98, 0.88), lift=(1.0, 1.0, 1.0), vig=0.35, haze=0.15),
    'pink': dict(top=(0.38, 0.18, 0.32), hor=(0.96, 0.58, 0.75), wstr=1.0,
                 sun=((1.0, 0.76, 0.86), 2.6, (-30, 55)), fill=((1.0, 0.65, 0.82), 130.0), lamp=((1.0, 0.8, 0.5), 0.0),
                 exp=0.0, sat=1.65, con=0.32, gam=1.0, gain=(1.15, 0.90, 1.05), lift=(1.0, 0.98, 1.02), vig=0.38, haze=0.15),
    'night': dict(top=(0.02, 0.04, 0.15), hor=(0.06, 0.09, 0.25), wstr=0.8, rim=((0.72, 0.88, 1.0), 3.2, (55, 22)),
                  sun=((0.45, 0.60, 0.95), 1.8, (-120, 40)), fill=((0.50, 0.65, 0.90), 80.0), lamp=((1.0, 0.68, 0.30), 550.0),
                  exp=0.15, sat=1.8, con=0.25, gam=0.95, gain=(0.65, 0.75, 0.92), lift=(0.98, 0.99, 1.02), vig=0.5, haze=0.2),
}


def _node(nt, kind, loc=(0, 0), **inputs):
    n = nt.nodes.new(kind); n.location = loc
    for k, v in inputs.items(): n.inputs[k].default_value = v
    return n


def setup_render(scene, w=720, h=1280):
    r = scene.render
    r.engine = 'BLENDER_EEVEE'; r.resolution_x, r.resolution_y = w, h; r.resolution_percentage = 100
    r.fps = 30; r.image_settings.file_format = 'PNG'; r.film_transparent = False
    for vt in ('Standard',):
        try: scene.view_settings.view_transform = vt
        except Exception: pass
    try: scene.view_settings.look = 'None'
    except Exception: pass
    scene.view_settings.exposure = 0.0; scene.view_settings.gamma = 1.0
    ev = scene.eevee
    for k, v in dict(taa_render_samples=24, use_raytracing=False, use_shadows=True, shadow_ray_count=2,
                     shadow_step_count=6, use_volumetric_shadows=False, volumetric_samples=32,
                     volumetric_tile_size='4', bokeh_max_size=24.0).items():
        try: setattr(ev, k, v)
        except Exception as e: print('look: eevee opt', k, e)
    vl = scene.view_layers[0]; vl.use_pass_z = True
    return scene


def _ramp(nt, loc):
    r = nt.nodes.new('ShaderNodeValToRGB'); r.location = loc
    r.color_ramp.interpolation = 'LINEAR'; els = r.color_ramp.elements
    spec = [(0.0, (0.45, 0.42, 0.70)), (0.20, (0.45, 0.42, 0.70)), (0.27, (0.80, 0.76, 0.88)),
            (0.50, (0.80, 0.76, 0.88)), (0.57, (1.12, 1.0, 0.80))]
    while len(els) < len(spec): els.new(0.5)
    for e, (p, c) in zip(els, spec): e.position = p; e.color = (*c, 1)
    return r


def toon_mat(name, rgb, tex=None, ink=True):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = _node(nt, 'ShaderNodeOutputMaterial', (1400, 0))
    dif = _node(nt, 'ShaderNodeBsdfDiffuse', (-600, 200)); dif.inputs['Color'].default_value = (1, 1, 1, 1)
    s2r = nt.nodes.new('ShaderNodeShaderToRGB'); s2r.location = (-400, 200)
    bw = nt.nodes.new('ShaderNodeRGBToBW'); bw.location = (-200, 200)
    ramp = _ramp(nt, (0, 200))
    L = nt.links.new
    L(dif.outputs[0], s2r.inputs[0]); L(s2r.outputs[0], bw.inputs[0]); L(bw.outputs[0], ramp.inputs[0])
    base = _node(nt, 'ShaderNodeRGB', (-600, -200)); base.outputs[0].default_value = (*rgb[:3], 1)
    col = base.outputs[0]
    if tex and os.path.exists(tex):
        tc = nt.nodes.new('ShaderNodeTexCoord'); tc.location = (-1000, -500)
        mp = nt.nodes.new('ShaderNodeMapping'); mp.location = (-800, -500)
        ti = nt.nodes.new('ShaderNodeTexImage'); ti.location = (-600, -500); ti.image = bpy.data.images.load(tex, check_existing=True)
        ti.projection = 'BOX'; ti.projection_blend = 0.2; ti.interpolation = 'Smart'
        L(tc.outputs['Object'], mp.inputs[0]); L(mp.outputs[0], ti.inputs[0])
        mt = nt.nodes.new('ShaderNodeMix'); mt.data_type = 'RGBA'; mt.blend_type = 'MULTIPLY'; mt.location = (-300, -300)
        mt.inputs[0].default_value = 1.0; L(col, mt.inputs[6]); L(ti.outputs[0], mt.inputs[7]); col = mt.outputs[2]
    nz = _node(nt, 'ShaderNodeTexNoise', (-800, -800), Scale=14.0, Detail=5.0, Roughness=0.6)
    nz.noise_dimensions = '3D'
    tc2 = nt.nodes.new('ShaderNodeTexCoord'); tc2.location = (-1000, -800)
    mp2 = nt.nodes.new('ShaderNodeMapping'); mp2.location = (-900, -800); mp2.inputs['Scale'].default_value = (1.0, 1.0, 0.3)
    L(tc2.outputs['Object'], mp2.inputs[0]); L(mp2.outputs[0], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.location = (-600, -800)
    mr.inputs['To Min'].default_value = 0.84; mr.inputs['To Max'].default_value = 1.08
    L(nz.outputs['Fac'], mr.inputs['Value'])
    mb = nt.nodes.new('ShaderNodeMix'); mb.data_type = 'RGBA'; mb.blend_type = 'MULTIPLY'; mb.location = (-100, -300)
    mb.inputs[0].default_value = 1.0; L(col, mb.inputs[6])
    mbv = nt.nodes.new('ShaderNodeCombineColor'); mbv.location = (-300, -800)
    for i in range(3): L(mr.outputs[0], mbv.inputs[i])
    L(mbv.outputs[0], mb.inputs[7])
    mxv = nt.nodes.new('ShaderNodeMath'); mxv.operation = 'MAXIMUM'; mxv.location = (-200, 500); mxv.inputs[1].default_value = 0.02
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'DIVIDE'; inv.location = (0, 500); inv.inputs[0].default_value = 1.0
    sc_ = nt.nodes.new('ShaderNodeVectorMath'); sc_.operation = 'SCALE'; sc_.location = (200, 500)
    L(bw.outputs[0], mxv.inputs[0]); L(mxv.outputs[0], inv.inputs[1]); L(s2r.outputs[0], sc_.inputs[0]); L(inv.outputs[0], sc_.inputs['Scale'])
    tn = nt.nodes.new('ShaderNodeMix'); tn.data_type = 'RGBA'; tn.location = (400, 500); tn.inputs[0].default_value = 0.4
    tn.inputs[6].default_value = (1, 1, 1, 1); L(sc_.outputs[0], tn.inputs[7])
    m0 = nt.nodes.new('ShaderNodeMix'); m0.data_type = 'RGBA'; m0.blend_type = 'MULTIPLY'; m0.location = (300, 150)
    m0.inputs[0].default_value = 1.0; L(ramp.outputs[0], m0.inputs[6]); L(tn.outputs[2], m0.inputs[7])
    m1 = nt.nodes.new('ShaderNodeMix'); m1.data_type = 'RGBA'; m1.blend_type = 'MULTIPLY'; m1.location = (500, 0)
    m1.inputs[0].default_value = 1.0; L(m0.outputs[2], m1.inputs[6]); L(mb.outputs[2], m1.inputs[7])
    fl = nt.nodes.new('ShaderNodeMix'); fl.data_type = 'RGBA'; fl.blend_type = 'MULTIPLY'; fl.location = (500, -150)
    fl.inputs[0].default_value = 1.0; fl.inputs[7].default_value = (0.2, 0.2, 0.24, 1); L(mb.outputs[2], fl.inputs[6])
    rm = nt.nodes.new('ShaderNodeLayerWeight'); rm.location = (500, -450); rm.inputs['Blend'].default_value = 0.3
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.location = (700, -450); rr.inputs['From Min'].default_value = 0.55; rr.inputs['From Max'].default_value = 0.9
    rr.inputs['To Max'].default_value = 0.5; L(rm.outputs['Fresnel'], rr.inputs['Value'])
    rc = nt.nodes.new('ShaderNodeMix'); rc.data_type = 'RGBA'; rc.blend_type = 'ADD'; rc.location = (900, -100)
    rc.inputs[7].default_value = (0.5, 0.78, 1.0, 1); L(rr.outputs[0], rc.inputs[0]); L(m1.outputs[2], rc.inputs[6])
    fa = nt.nodes.new('ShaderNodeMix'); fa.data_type = 'RGBA'; fa.blend_type = 'ADD'; fa.location = (1100, -100); fa.inputs[0].default_value = 1.0
    L(rc.outputs[2], fa.inputs[6]); L(fl.outputs[2], fa.inputs[7])
    last = fa.outputs[2]
    if ink:
        lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.location = (300, -300); lw.inputs['Blend'].default_value = 0.5
        er = nt.nodes.new('ShaderNodeMath'); er.operation = 'GREATER_THAN'; er.location = (500, -300); er.inputs[1].default_value = 0.93
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.location = (700, 0)
        mx.inputs[7].default_value = INK_RGB
        L(lw.outputs['Facing'], er.inputs[0]); L(er.outputs[0], mx.inputs[0]); L(last, mx.inputs[6]); last = mx.outputs[2]
    em = _node(nt, 'ShaderNodeEmission', (1000, 0), Strength=1.0); L(last, em.inputs['Color']); L(em.outputs[0], out.inputs[0])
    m['look_toon'] = True
    return m


_INK = None
def _ink_mat():
    global _INK
    if _INK is None or _INK.name not in bpy.data.materials:
        m = bpy.data.materials.new('LOOK_ink'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = INK_RGB; em.inputs['Strength'].default_value = 1.0
        o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], o.inputs[0])
        m.use_backface_culling = True; _INK = m
    return _INK


def ink_hull(obj, width=0.018):
    if obj.type != 'MESH': return obj
    if 'LOOK_ink' in obj.modifiers: obj.modifiers['LOOK_ink'].thickness = width; return obj
    obj.data.materials.append(_ink_mat())
    md = obj.modifiers.new('LOOK_ink', 'SOLIDIFY'); md.thickness = width; md.offset = 1
    md.use_flip_normals = True; md.use_rim = False; md.material_offset = len(obj.data.materials) - 1
    return obj


def _rig(scene):
    ob = bpy.data.objects
    def get(name, kind, make):
        o = ob.get(name)
        if o is None:
            l = make(); o = ob.new(name, l); scene.collection.objects.link(o)
        return o
    sun = get('LOOK_Sun', 'SUN', lambda: bpy.data.lights.new('LOOK_Sun', 'SUN')); sun.data.angle = math.radians(4)
    fill = get('LOOK_Fill', 'AREA', lambda: bpy.data.lights.new('LOOK_Fill', 'AREA')); fill.data.size = 6.0
    rim = get('LOOK_Rim', 'SUN', lambda: bpy.data.lights.new('LOOK_Rim', 'SUN')); rim.data.angle = math.radians(6)
    lamp = get('LOOK_Lamp', 'POINT', lambda: bpy.data.lights.new('LOOK_Lamp', 'POINT')); lamp.data.shadow_soft_size = 0.4
    w = scene.world
    if w is None or 'look_world' not in w:
        w = bpy.data.worlds.new('LOOK_World'); w['look_world'] = True; scene.world = w; w.use_nodes = True
        nt = w.node_tree; nt.nodes.clear(); L = nt.links.new
        tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ')
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.45
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.name = 'mix'
        top = nt.nodes.new('ShaderNodeRGB'); top.name = 'top'; hor = nt.nodes.new('ShaderNodeRGB'); hor.name = 'hor'
        bg = nt.nodes.new('ShaderNodeBackground'); bg.name = 'bg'; o = nt.nodes.new('ShaderNodeOutputWorld')
        L(tc.outputs['Generated'], sp.inputs[0]); L(sp.outputs['Z'], mr.inputs['Value']); L(mr.outputs[0], mx.inputs[0])
        L(hor.outputs[0], mx.inputs[6]); L(top.outputs[0], mx.inputs[7]); L(mx.outputs[2], bg.inputs[0]); L(bg.outputs[0], o.inputs[0])
    return sun, fill, lamp, w


def apply_mood(scene, mood, f_start, f_end, lamp_at=None, fill_x=None):
    if mood not in MOODS: mood = 'prison'
    P = MOODS[mood]; sun, fill, lamp, w = _rig(scene); nt = w.node_tree
    for f in (f_start, f_end):
        nt.nodes['top'].outputs[0].default_value = (*P['top'], 1); nt.nodes['top'].outputs[0].keyframe_insert('default_value', frame=f)
        nt.nodes['hor'].outputs[0].default_value = (*P['hor'], 1); nt.nodes['hor'].outputs[0].keyframe_insert('default_value', frame=f)
        s = nt.nodes['bg'].inputs['Strength']; s.default_value = P['wstr']; s.keyframe_insert('default_value', frame=f)
        sun.data.color = P['sun'][0]; sun.data.energy = P['sun'][1]
        az, el = P['sun'][2]
        sun.rotation_euler = (math.radians(90 - el), 0, math.radians(az))
        sun.keyframe_insert('rotation_euler', frame=f); sun.data.keyframe_insert('energy', frame=f); sun.data.keyframe_insert('color', frame=f)
        fill.data.color = P['fill'][0]; fill.data.energy = P['fill'][1]
        fill.location = (fill_x if fill_x is not None else 0.0, -6.0, 5.0)
        fill.keyframe_insert('location', frame=f); fill.data.keyframe_insert('energy', frame=f); fill.data.keyframe_insert('color', frame=f)
        lamp.data.color = P['lamp'][0]; lamp.data.energy = P['lamp'][1]
        if lamp_at: lamp.location = lamp_at; lamp.keyframe_insert('location', frame=f)
        lamp.data.keyframe_insert('energy', frame=f); lamp.data.keyframe_insert('color', frame=f)
        _grade_key(scene, mood, f)


def setup_compositor(scene):
    scene.render.use_compositing = True
    nt = bpy.data.node_groups.new('LOOK_comp', 'CompositorNodeTree'); scene.compositing_node_group = nt
    nt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    L = nt.links.new
    def mix(loc, blend, fac=1.0):
        n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = blend; n.location = loc
        n.inputs[0].default_value = fac; return n
    rl = nt.nodes.new('CompositorNodeRLayers'); rl.location = (-1400, 0)
    ku = _node(nt, 'CompositorNodeKuwahara', (-1150, 200), Size=2); ku.name = 'ku'; ku.inputs['Type'].default_value = 'Classic'
    gl = _node(nt, 'CompositorNodeGlare', (-900, 200), Threshold=1.0, Strength=0.25, Size=0.6); gl.inputs['Type'].default_value = 'Bloom'
    cb = _node(nt, 'CompositorNodeColorBalance', (-400, 200)); cb.name = 'cb'; cb.inputs['Type'].default_value = 'Lift/Gamma/Gain'
    hs = nt.nodes.new('CompositorNodeHueSat'); hs.name = 'hs'; hs.location = (-150, 200)
    L(rl.outputs['Image'], ku.inputs['Image']); L(ku.outputs[0], gl.inputs['Image']); L(gl.outputs[0], cb.inputs['Image']); L(cb.outputs[0], hs.inputs['Image'])
    sob = _node(nt, 'CompositorNodeFilter', (-1150, -400)); sob.inputs['Type'].default_value = 'Sobel'
    zc = nt.nodes.new('ShaderNodeMath'); zc.operation = 'MINIMUM'; zc.inputs[1].default_value = 40.0; zc.location = (-1300, -400)
    L(rl.outputs['Depth'], zc.inputs[0]); L(zc.outputs[0], sob.inputs['Image'])
    bw = nt.nodes.new('CompositorNodeRGBToBW'); bw.location = (-950, -400); L(sob.outputs[0], bw.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.location = (-750, -400); mr.name = 'inkmap'
    mr.inputs['From Min'].default_value = 0.35; mr.inputs['From Max'].default_value = 1.2; mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.15
    L(bw.outputs[0], mr.inputs['Value'])
    hz = mix((0, 450), 'MIX'); hzr = nt.nodes.new('ShaderNodeMapRange'); hzr.name = 'hazeamt'; hzr.location = (-300, 450)
    hzr.inputs['From Min'].default_value = 4.0; hzr.inputs['From Max'].default_value = 40.0; hzr.inputs['To Max'].default_value = 0.3
    hzc = nt.nodes.new('CompositorNodeRGB'); hzc.name = 'hazecol'; hzc.location = (-300, 650)
    L(zc.outputs[0], hzr.inputs['Value']); L(hzr.outputs[0], hz.inputs[0]); L(hs.outputs[0], hz.inputs[6]); L(hzc.outputs[0], hz.inputs[7])
    mi = mix((150, 200), 'MULTIPLY'); L(hz.outputs[2], mi.inputs[6]); L(mr.outputs[0], mi.inputs[7])
    el = _node(nt, 'CompositorNodeEllipseMask', (-750, -700)); el.inputs['Position'].default_value = (0.5, 0.5); el.inputs['Size'].default_value = (0.9, 0.9)
    bl = _node(nt, 'CompositorNodeBlur', (-500, -700), Size=(260, 260)); bl.inputs['Type'].default_value = 'Gaussian'
    L(el.outputs[0], bl.inputs['Image'])
    vr = nt.nodes.new('ShaderNodeMapRange'); vr.name = 'vig'; vr.location = (-250, -700); vr.inputs['To Min'].default_value = 0.5
    L(bl.outputs[0], vr.inputs['Value'])
    vm = mix((400, 200), 'MULTIPLY'); L(mi.outputs[2], vm.inputs[6]); L(vr.outputs[0], vm.inputs[7])
    wb = _node(nt, 'CompositorNodeBlur', (650, 200), Size=(0.0, 0.0)); wb.name = 'whipblur'; wb.inputs['Type'].default_value = 'Gaussian'
    L(vm.outputs[2], wb.inputs['Image'])
    dp = mix((900, 200), 'MIX', 0.0); dp.name = 'dip'; dp.inputs[7].default_value = (0.10, 0.03, 0.02, 1); L(wb.outputs[0], dp.inputs[6])
    go = nt.nodes.new('NodeGroupOutput'); go.location = (1150, 200); L(dp.outputs[2], go.inputs[0])
    return nt


def _grade_key(scene, mood, f):
    nt = getattr(scene, 'compositing_node_group', None)
    if nt is None or 'hs' not in nt.nodes: return
    P = MOODS[mood]
    if 'ku' in nt.nodes:
        kz = nt.nodes['ku'].inputs['Size']; kz.default_value = 0.0 if mood == 'night' else 2.0; kz.keyframe_insert('default_value', frame=f)
    hc = nt.nodes['hazecol'].outputs[0]; hc.default_value = (*P['hor'], 1); hc.keyframe_insert('default_value', frame=f)
    ha = nt.nodes['hazeamt'].inputs['To Max']; ha.default_value = P['haze']; ha.keyframe_insert('default_value', frame=f)
    for name, sock, val in (('hs', 'Saturation', P['sat']),
                            ('cb', 'Gain', (*P['gain'], 1)), ('cb', 'Lift', (*P['lift'], 1)), ('cb', 'Gamma', (P['gam'],) * 3 + (1,)), ('vig', 'To Min', 1.0 - P['vig'])):
        want = isinstance(val, tuple)
        s = [i for i in nt.nodes[name].inputs if i.name == sock and hasattr(i.default_value, '__len__') == want][0]
        s.default_value = val; s.keyframe_insert('default_value', frame=f)
