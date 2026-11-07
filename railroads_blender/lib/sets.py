"""SETS module for Railroads: Desert canyon environments and roadbeds.
Blender 5.2 (EEVEE Next), headless compatible.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Euler

try:
    from . import look
except Exception:
    import look

ORIGIN = {
    'canyon_track': (0, 0, 0),
    'canyon_chasm': (100, 0, 0),
    'finish_line': (200, 0, 0),
    'desert_buckle': (300, 0, 0),
}

def _coll(name):
    scene = bpy.context.scene
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    else:
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    return c

def _empty(c, name, loc=(0,0,0), rot_z=0.0):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.2
    e.location = loc
    e.rotation_euler = (0, 0, rot_z)
    c.objects.link(e)
    return e

def _box(c, name, sz, loc, mat, rot=(0,0,0), ink=0.015):
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
    if ink:
        look.ink_hull(ob, ink)
    return ob

# ---------------------------------------------------------------------------
# 1. CANYON TRACK (Roadbed carved into sandstone cliff)
# ---------------------------------------------------------------------------
def build_canyon_track():
    key = 'canyon_track'
    c = _coll('set_' + key)
    ox, oy, oz = ORIGIN[key]
    
    sandstone = look.toon_mat('pe_sandstone', look.DESERT_ROCK)
    sandstone_dark = look.toon_mat('pe_sandstone_dark', look.DESERT_DARK)
    ballast = look.toon_mat('pe_ballast', look.BALLAST_GREY)
    steel = look.toon_mat('pe_track_steel', look.STEEL_RAIL)
    tie_mat = look.toon_mat('pe_track_tie', look.WOOD_TIE)
    
    # 1. Roadbed ground ledge (12m wide, 24m deep)
    _box(c, "roadbed", (12.0, 24.0, 1.0), (ox, oy, oz - 0.5), sandstone, ink=0.02)
    
    # 2. Sheer canyon cliff wall (right side)
    _box(c, "cliff_wall_R", (4.0, 24.0, 14.0), (ox + 5.5, oy, oz + 6.0), sandstone_dark, ink=0.02)
    
    # 3. Chasm drop-off cliff (left side)
    _box(c, "chasm_cliff_L", (4.0, 24.0, 14.0), (ox - 6.5, oy, oz - 6.0), sandstone_dark, ink=0.02)
    
    # 4. Crushed stone ballast track bed
    _box(c, "ballast_bed", (3.2, 24.0, 0.12), (ox, oy, oz + 0.06), ballast, ink=0.015)
    
    # 5. Continuous background track section (wooden ties & steel rails)
    num_ties = 36
    for i in range(num_ties):
        ty = -11.0 + i * (22.0 / num_ties)
        # Skip the center joint area (y between -1.5 and 1.5) where the hero rail_joint prop sits
        if abs(ty) < 1.4:
            continue
        _box(c, f"tie_{i}", (0.28, 2.4, 0.16), (ox, oy + ty, oz + 0.16), tie_mat, ink=0.01)
        
    # Rails running north-south (leaving center 3m for hero interactive joint)
    for sx in (-0.71, 0.71):
        _box(c, f"rail_north_{sx}", (0.08, 9.0, 0.16), (ox + sx, oy + 6.0, oz + 0.30), steel, ink=0.012)
        _box(c, f"rail_south_{sx}", (0.08, 9.0, 0.16), (ox + sx, oy - 6.0, oz + 0.30), steel, ink=0.012)
        
    # Anchors
    anchors = {
        'saw_spot': _empty(c, f"anc_{key}_saw_spot", loc=(ox - 0.55, oy, oz + 0.12), rot_z=math.radians(-90)),
        'boss_spot': _empty(c, f"anc_{key}_boss_spot", loc=(ox + 0.65, oy + 0.3, oz + 0.12), rot_z=math.radians(90)),
        'joint_center': _empty(c, f"anc_{key}_joint_center", loc=(ox, oy, oz + 0.16)),
        'standoff_engineer': _empty(c, f"anc_{key}_standoff_engineer", loc=(ox - 0.7, oy + 1.2, oz + 0.12), rot_z=math.radians(-70)),
        'standoff_boss': _empty(c, f"anc_{key}_standoff_boss", loc=(ox + 0.7, oy + 1.2, oz + 0.12), rot_z=math.radians(110)),
    }
    return c, anchors

# ---------------------------------------------------------------------------
# 2. CANYON CHASM & TIMBER TRESTLE
# ---------------------------------------------------------------------------
def build_canyon_chasm():
    key = 'canyon_chasm'
    c = _coll('set_' + key)
    ox, oy, oz = ORIGIN[key]
    
    sandstone = look.toon_mat('pe_sandstone_deep', look.DESERT_ROCK)
    timber = look.toon_mat('pe_timber_wood', look.WOOD_TIE)
    steel = look.toon_mat('pe_trestle_steel', look.STEEL_RAIL)
    
    # Two canyon rim towers with a 16m abyss between them
    _box(c, "canyon_rim_A", (8.0, 16.0, 16.0), (ox - 12.0, oy, oz), sandstone, ink=0.02)
    _box(c, "canyon_rim_B", (8.0, 16.0, 16.0), (ox + 12.0, oy, oz), sandstone, ink=0.02)
    
    # Timber trestle bridge spanning the chasm
    _box(c, "bridge_deck", (20.0, 3.2, 0.4), (ox, oy, oz + 7.8), timber, ink=0.015)
    
    # Wooden trestle bents (vertical support towers)
    for bx in (-6.0, 0.0, 6.0):
        _box(c, f"bent_post_L_{bx}", (0.35, 0.35, 12.0), (ox + bx, oy - 1.2, oz + 2.0), timber, ink=0.01)
        _box(c, f"bent_post_R_{bx}", (0.35, 0.35, 12.0), (ox + bx, oy + 1.2, oz + 2.0), timber, ink=0.01)
        # Cross braces
        _box(c, f"bent_cross_{bx}", (0.2, 2.6, 0.15), (ox + bx, oy, oz + 3.5), timber, ink=0.008)
        _box(c, f"bent_cross_hi_{bx}", (0.2, 2.6, 0.15), (ox + bx, oy, oz + 6.0), timber, ink=0.008)
        
    # Rails across bridge deck
    for sy in (-0.71, 0.71):
        _box(c, f"bridge_rail_{sy}", (20.0, 0.08, 0.14), (ox, oy + sy, oz + 8.1), steel, ink=0.01)
        
    anchors = {
        'bridge_center': _empty(c, f"anc_{key}_bridge_center", loc=(ox, oy, oz + 8.2)),
        'chasm_look': _empty(c, f"anc_{key}_chasm_look", loc=(ox, oy, oz - 4.0)),
    }
    return c, anchors

# ---------------------------------------------------------------------------
# 3. FINISH LINE & MONUMENT
# ---------------------------------------------------------------------------
def build_finish_line():
    key = 'finish_line'
    c = _coll('set_' + key)
    ox, oy, oz = ORIGIN[key]
    
    sandstone = look.toon_mat('pe_finish_ground', look.DESERT_SAND)
    gold = look.glow('pe_gold_monument', look.GOLD_FINISH, strength=3.0)
    red = look.toon_mat('pe_finish_ribbon', (0.85, 0.12, 0.15))
    
    # Flat canyon plateau
    _box(c, "finish_plateau", (16.0, 16.0, 1.0), (ox, oy, oz - 0.5), sandstone, ink=0.02)
    
    # Golden survey monument pillar
    _box(c, "monument_base", (1.2, 1.2, 0.4), (ox, oy, oz + 0.2), gold, ink=0.015)
    _box(c, "monument_spire", (0.5, 0.5, 1.8), (ox, oy, oz + 1.1), gold, ink=0.015)
    
    # Red ceremonial ribbon
    _box(c, "ribbon", (0.04, 4.0, 0.2), (ox, oy, oz + 1.2), red, ink=0.008)
    
    anchors = {
        'finish_center': _empty(c, f"anc_{key}_finish_center", loc=(ox, oy, oz + 0.2)),
    }
    return c, anchors

# ---------------------------------------------------------------------------
# 4. DESERT BUCKLE (Scorching heat plain for sun-kink derailment)
# ---------------------------------------------------------------------------
def build_desert_buckle():
    key = 'desert_buckle'
    c = _coll('set_' + key)
    ox, oy, oz = ORIGIN[key]
    
    sand = look.toon_mat('pe_desert_sand', look.DESERT_SAND)
    
    # Vast flat desert terrain
    _box(c, "desert_ground", (20.0, 28.0, 1.0), (ox, oy, oz - 0.5), sand, ink=0.02)
    
    anchors = {
        'buckle_center': _empty(c, f"anc_{key}_buckle_center", loc=(ox, oy, oz)),
        'thermo_spot': _empty(c, f"anc_{key}_thermo_spot", loc=(ox + 1.8, oy - 2.0, oz + 0.5)),
    }
    return c, anchors

def build_sets():
    c_ct, A_ct = build_canyon_track()
    c_cc, A_cc = build_canyon_chasm()
    c_fl, A_fl = build_finish_line()
    c_db, A_db = build_desert_buckle()
    
    out = {
        'canyon_track': {'collection': c_ct, 'anchors': A_ct},
        'canyon_chasm': {'collection': c_cc, 'anchors': A_cc},
        'finish_line': {'collection': c_fl, 'anchors': A_fl},
        'desert_buckle': {'collection': c_db, 'anchors': A_db},
    }
    return out
