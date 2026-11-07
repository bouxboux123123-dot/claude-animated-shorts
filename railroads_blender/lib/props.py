"""PROPS module for Railroads: Interactive PropSpec architecture.
Every prop exports: root Empty, grip_sockets (for character hands), and normalized action channels.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Euler

try:
    from . import look
except Exception:
    import look

class PropSpec:
    """Universal interactive prop container."""
    def __init__(self, name, root, grip_sockets=None, channels=None):
        self.name = name
        self.root = root
        self.grip_sockets = grip_sockets or {}
        self.channels = channels or {}

    def set_channel(self, channel_name, val):
        """Set a normalized [0.0, 1.0] parameter."""
        if channel_name in self.channels:
            self.channels[channel_name](val)

def _empty(c, name, loc=(0,0,0), rot=(0,0,0), parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.08
    e.location = loc
    e.rotation_euler = rot
    if parent:
        e.parent = parent
    c.objects.link(e)
    return e

def _box(c, name, sz, loc, mat, rot=(0,0,0), parent=None, ink=0.012):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    for v in bm.verts:
        v.co = (v.co.x * sz[0]/2, v.co.y * sz[1]/2, v.co.z * sz[2]/2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = rot
    if parent:
        ob.parent = parent
    if ink:
        look.ink_hull(ob, ink)
    return ob

def _cyl(c, name, r, h, loc, mat, rot=(0,0,0), parent=None, ink=0.012, seg=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = rot
    if parent:
        ob.parent = parent
    if ink:
        look.ink_hull(ob, ink)
    return ob

# ---------------------------------------------------------------------------
# 1. HACKSAW (with stroke channel)
# ---------------------------------------------------------------------------
def build_hacksaw(c, name="hacksaw", loc=(0,0,0)):
    root = _empty(c, f"prop_{name}", loc=loc)
    
    # Grip socket for character's right hand
    socket = _empty(c, f"{name}_socket_grip", loc=(0, 0, 0), parent=root)
    
    # Wooden handle
    wood = look.toon_mat('pe_tool_wood', look.WOOD_TIE)
    steel = look.toon_mat('pe_tool_steel', look.STEEL_DARK)
    silver = look.toon_mat('pe_tool_silver', look.STEEL_RAIL)
    
    _cyl(c, f"{name}_handle", r=0.02, h=0.14, loc=(0, 0, 0), mat=wood, rot=(math.radians(90), 0, 0), parent=root)
    
    # Moving blade assembly parented to a stroke empty
    stroke_empty = _empty(c, f"{name}_stroke_mount", loc=(0, 0.12, 0), parent=root)
    
    # C-frame steel bow
    _box(c, f"{name}_frame_back", sz=(0.015, 0.02, 0.42), loc=(0, 0.20, 0.15), mat=steel, rot=(0, math.radians(90), 0), parent=stroke_empty)
    _box(c, f"{name}_frame_up1", sz=(0.015, 0.02, 0.15), loc=(0, 0.0, 0.08), mat=steel, parent=stroke_empty)
    _box(c, f"{name}_frame_up2", sz=(0.015, 0.02, 0.15), loc=(0, 0.40, 0.08), mat=steel, parent=stroke_empty)
    
    # Thin serrated blade
    blade = _box(c, f"{name}_blade", sz=(0.003, 0.018, 0.42), loc=(0, 0.20, 0.01), mat=silver, rot=(0, math.radians(90), 0), parent=stroke_empty, ink=0.005)
    
    def set_stroke(val):
        # val in [0.0, 1.0] -> reciprocating saw motion +/- 0.08m
        stroke_empty.location.y = 0.12 + math.sin(val * 2 * math.pi) * 0.08
        
    channels = {'stroke': set_stroke}
    return PropSpec(name, root, {'hand': socket}, channels)

# ---------------------------------------------------------------------------
# 2. RAIL JOINT (with dynamic expansion gap channel)
# ---------------------------------------------------------------------------
def build_rail_joint(c, name="rail_joint", loc=(0,0,0)):
    root = _empty(c, f"prop_{name}", loc=loc)
    
    steel = look.toon_mat('pe_rail_steel', look.STEEL_RAIL)
    tie_mat = look.toon_mat('pe_rail_tie', look.WOOD_TIE)
    dark_steel = look.toon_mat('pe_rail_plate', look.STEEL_DARK)
    
    # Center wooden sleeper (tie)
    _box(c, f"{name}_tie", sz=(0.28, 2.4, 0.18), loc=(0, 0, -0.09), mat=tie_mat, parent=root)
    
    # Rail Left (fixed)
    # I-beam cross section: base flange, vertical web, head crown
    _box(c, f"{name}_rail_L_base", sz=(0.14, 1.5, 0.02), loc=(0, -0.76, 0.01), mat=steel, parent=root)
    _box(c, f"{name}_rail_L_web", sz=(0.03, 1.5, 0.12), loc=(0, -0.76, 0.08), mat=steel, parent=root)
    _box(c, f"{name}_rail_L_head", sz=(0.08, 1.5, 0.04), loc=(0, -0.76, 0.16), mat=steel, parent=root)
    
    # Rail Right (expands/contracts along Y)
    rail_R_root = _empty(c, f"{name}_rail_R_mount", loc=(0, 0.015, 0), parent=root)
    _box(c, f"{name}_rail_R_base", sz=(0.14, 1.5, 0.02), loc=(0, 0.75, 0.01), mat=steel, parent=rail_R_root)
    _box(c, f"{name}_rail_R_web", sz=(0.03, 1.5, 0.12), loc=(0, 0.75, 0.08), mat=steel, parent=rail_R_root)
    _box(c, f"{name}_rail_R_head", sz=(0.08, 1.5, 0.04), loc=(0, 0.75, 0.16), mat=steel, parent=rail_R_root)
    
    # Fishplate joint bars across the seam (with oval expansion slots)
    _box(c, f"{name}_fishplate_in", sz=(0.015, 0.50, 0.08), loc=(-0.025, 0, 0.08), mat=dark_steel, parent=root)
    _box(c, f"{name}_fishplate_out", sz=(0.015, 0.50, 0.08), loc=(0.025, 0, 0.08), mat=dark_steel, parent=root)
    
    # Bolts
    for sy in (-0.16, -0.06, 0.06, 0.16):
        _cyl(c, f"{name}_bolt_{sy}", r=0.014, h=0.09, loc=(0, sy, 0.08), mat=dark_steel, rot=(0, math.radians(90), 0), parent=root, seg=8)
        
    def set_gap(val):
        # val=0.0 -> 15mm gap (0.015m)
        # val=1.0 -> 0mm gap (closed tight)
        rail_R_root.location.y = 0.015 * (1.0 - val)
        
    channels = {'gap_closure': set_gap}
    return PropSpec(name, root, {}, channels)

# ---------------------------------------------------------------------------
# 3. WRENCH & BLUEPRINT PROPS
# ---------------------------------------------------------------------------
def build_wrench(c, name="wrench", loc=(0,0,0)):
    root = _empty(c, f"prop_{name}", loc=loc)
    socket = _empty(c, f"{name}_socket_grip", loc=(0, 0, 0), parent=root)
    steel = look.toon_mat('pe_wrench_steel', look.STEEL_RAIL)
    
    _box(c, f"{name}_shaft", sz=(0.03, 0.38, 0.015), loc=(0, 0.15, 0), mat=steel, parent=root)
    _cyl(c, f"{name}_head", r=0.045, h=0.015, loc=(0, 0.35, 0), mat=steel, parent=root, seg=12)
    _box(c, f"{name}_jaw_cut", sz=(0.025, 0.04, 0.02), loc=(0, 0.37, 0), mat=look.toon_mat('pe_black', (0.02, 0.02, 0.02)), parent=root)
    
    def set_tap(val):
        root.rotation_euler.x = math.sin(val * 4 * math.pi) * 0.15
        
    channels = {'tap': set_tap}
    return PropSpec(name, root, {'hand': socket}, channels)

def build_blueprint(c, name="blueprint", loc=(0,0,0)):
    root = _empty(c, f"prop_{name}", loc=loc)
    socket = _empty(c, f"{name}_socket_grip", loc=(0, 0, 0), parent=root)
    cyan = look.toon_mat('pe_blueprint_blue', (0.15, 0.45, 0.85))
    
    _cyl(c, f"{name}_roll", r=0.035, h=0.55, loc=(0, 0, 0), mat=cyan, rot=(0, math.radians(90), 0), parent=root, seg=16)
    
    def set_wave(val):
        root.rotation_euler.z = math.sin(val * 3 * math.pi) * 0.25
        
    channels = {'wave': set_wave}
    return PropSpec(name, root, {'hand': socket}, channels)

# ---------------------------------------------------------------------------
# 4. THERMOMETER (Dynamic Rising Mercury Channel)
# ---------------------------------------------------------------------------
def build_thermometer(c, name="thermometer", loc=(0,0,0)):
    root = _empty(c, f"prop_{name}", loc=loc)
    brass = look.toon_mat('pe_thermo_brass', (0.85, 0.65, 0.25))
    red = look.glow('pe_mercury_red', (1.0, 0.10, 0.10), strength=4.0)
    white = look.toon_mat('pe_glass_white', (0.95, 0.95, 0.98))
    
    # Backplate
    _box(c, f"{name}_backplate", sz=(0.14, 0.02, 0.90), loc=(0, 0, 0.45), mat=brass, parent=root)
    
    # Glass bulb & tube
    _cyl(c, f"{name}_bulb", r=0.035, h=0.07, loc=(0, -0.02, 0.08), mat=red, parent=root, seg=16)
    _cyl(c, f"{name}_tube", r=0.015, h=0.70, loc=(0, -0.02, 0.48), mat=white, parent=root, seg=12)
    
    # Rising mercury column
    merc_root = _empty(c, f"{name}_merc_root", loc=(0, -0.02, 0.12), parent=root)
    merc_cyl = _cyl(c, f"{name}_column", r=0.012, h=0.68, loc=(0, 0, 0.34), mat=red, parent=merc_root, seg=12, ink=0.0)
    
    def set_temp(val):
        # val in [0.0, 1.0] -> scale column Z from 0.1 (cool) to 1.0 (scorching heat)
        s = max(0.08, min(1.0, val))
        merc_root.scale.z = s
        
    channels = {'temperature': set_temp}
    return PropSpec(name, root, {}, channels)

# ---------------------------------------------------------------------------
# 5. BUCKLING TRACK (Sun Kink Dynamic Deformation Channel)
# ---------------------------------------------------------------------------
def build_buckling_track(c, name="buckling_track", loc=(0,0,0)):
    root = _empty(c, f"prop_{name}", loc=loc)
    steel = look.toon_mat('pe_buckle_steel', look.STEEL_RAIL)
    tie_mat = look.toon_mat('pe_buckle_tie', look.WOOD_TIE)
    
    ties = []
    # Build a 14-meter track stretch
    num_ties = 24
    for i in range(num_ties):
        y = -7.0 + i * (14.0 / num_ties)
        t_ob = _box(c, f"{name}_tie_{i}", sz=(0.28, 2.4, 0.16), loc=(0, y, -0.08), mat=tie_mat, parent=root)
        ties.append((y, t_ob))
        
    # Left and Right continuous rails with dense subdivisions for warping
    def make_warp_rail(rail_name, offset_x):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        # scale to rail cross section and 14m length
        for v in bm.verts:
            v.co = (v.co.x * 0.05, v.co.y * 7.0, v.co.z * 0.08)
        # subdivide along length (Y) so it can bend
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=28)
        me = bpy.data.meshes.new(rail_name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(rail_name, me)
        c.objects.link(ob)
        ob.data.materials.append(steel)
        ob.location = (offset_x, 0, 0.08)
        ob.parent = root
        look.ink_hull(ob, 0.012)
        return ob
        
    rail_L = make_warp_rail(f"{name}_rail_L", -0.71)
    rail_R = make_warp_rail(f"{name}_rail_R", 0.71)
    
    # Store original vertex X coords
    orig_L_x = [v.co.x for v in rail_L.data.vertices]
    orig_R_x = [v.co.x for v in rail_R.data.vertices]
    
    def set_buckle(val):
        # val in [0.0, 1.0] -> S-curve displacement
        # max displacement amplitude 0.75m
        amp = val * 0.75
        for i, v in enumerate(rail_L.data.vertices):
            y = v.co.y
            envelope = math.exp(-((y) / 3.0)**2) # Centered around y=0
            warp = math.sin(y * 1.2) * amp * envelope
            v.co.x = orig_L_x[i] + warp
        rail_L.data.update()
        
        for i, v in enumerate(rail_R.data.vertices):
            y = v.co.y
            envelope = math.exp(-((y) / 3.0)**2)
            warp = math.sin(y * 1.2) * amp * envelope
            v.co.x = orig_R_x[i] + warp
        rail_R.data.update()
        
        # Also warp ties
        for y, t_ob in ties:
            envelope = math.exp(-(y / 3.0)**2)
            warp = math.sin(y * 1.2) * amp * envelope
            t_ob.location.x = warp
            t_ob.rotation_euler.z = math.cos(y * 1.2) * (amp * 0.35) * envelope

    channels = {'buckle_progress': set_buckle}
    return PropSpec(name, root, {}, channels)
