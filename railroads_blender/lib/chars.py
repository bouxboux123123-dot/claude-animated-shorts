"""CHARS module for Railroads: Expressive 2D-in-3D Cartoon Card Characters.
Flat paper-cutout card bodies with thick black ink contours, facing camera with articulated IK arms.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Euler

try:
    from . import look
except Exception:
    import look

class Char:
    def __init__(self, name, root, head_card, torso_card, l_hand, r_hand):
        self.name = name
        self.root = root
        self.head_card = head_card
        self.torso_card = torso_card
        self.l_hand = l_hand
        self.r_hand = r_hand
        self.held_prop = None

    def place(self, frame, loc, rot_z=0.0):
        self.root.location = loc
        self.root.rotation_euler.z = rot_z
        self.root.keyframe_insert('location', frame=frame)
        self.root.keyframe_insert('rotation_euler', frame=frame)

    def hold_socket(self, frame, socket_empty, hand='right'):
        """Snap hand to prop grip socket."""
        target = self.r_hand if hand == 'right' else self.l_hand
        target.location = socket_empty.matrix_world.translation
        target.keyframe_insert('location', frame=frame)

    def set_emotion(self, frame, color_tint=None, steam=False):
        """Dynamic face emotional reaction (e.g. boss turning purple)."""
        if color_tint and self.head_card:
            mat = self.head_card.data.materials[0]
            if mat and mat.node_tree:
                bsdf = mat.node_tree.nodes.get('ShaderNodeBsdfPrincipled')
                if bsdf:
                    bsdf.inputs['Base Color'].default_value = (*color_tint[:3], 1.0)
                    bsdf.inputs['Base Color'].keyframe_insert('default_value', frame=frame)

def _card(c, name, w, h, mat, loc=(0,0,0), rot=(0,0,0), parent=None, ink=0.015):
    """Create a flat 2D double-sided cartoon card with ink outline."""
    bm = bmesh.new()
    hw, hh = w / 2, h / 2
    # Create flat rectangle in XZ plane
    v1 = bm.verts.new((-hw, 0, -hh))
    v2 = bm.verts.new((hw, 0, -hh))
    v3 = bm.verts.new((hw, 0, hh))
    v4 = bm.verts.new((-hw, 0, hh))
    bm.faces.new((v1, v2, v3, v4))
    
    # Extrude slightly for ink hull
    bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=0.02)
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

def make_character(c, role="engineer", name="char_engineer", loc=(0,0,0)):
    root = bpy.data.objects.new(name, None)
    root.empty_display_size = 0.2
    root.location = loc
    c.objects.link(root)
    
    white = look.toon_mat(f'ch_{name}_face', (0.98, 0.96, 0.92))
    ink_black = look.toon_mat('pe_char_ink', (0.02, 0.02, 0.03))
    
    if role == "engineer":
        body_col = (0.95, 0.55, 0.12) # High-vis orange vest
        hat_col = (1.0, 0.85, 0.10)  # Yellow hardhat
        pants_col = (0.20, 0.35, 0.65) # Denim blue
    elif role == "boss":
        body_col = (0.35, 0.20, 0.40) # Tycoon purple coat
        hat_col = (0.12, 0.12, 0.15)  # Dark bowler hat
        pants_col = (0.22, 0.22, 0.25) # Pinstripe dark
    else: # rival
        body_col = (0.18, 0.45, 0.75) # Blue coat
        hat_col = (0.15, 0.15, 0.18)  # Top hat
        pants_col = (0.18, 0.20, 0.22)
        
    torso_mat = look.toon_mat(f'ch_{name}_torso', body_col)
    hat_mat = look.toon_mat(f'ch_{name}_hat', hat_col)
    pants_mat = look.toon_mat(f'ch_{name}_pants', pants_col)
    
    # 1. Legs (stick-style tall cartoon legs)
    _card(c, f"{name}_legs", 0.30, 0.70, pants_mat, loc=(0, 0, 0.35), parent=root, ink=0.015)
    
    # 2. Torso Card
    torso = _card(c, f"{name}_torso", 0.48, 0.55, torso_mat, loc=(0, 0, 0.95), parent=root, ink=0.018)
    
    # 3. Head Card (expressive bean head)
    head = _card(c, f"{name}_head", 0.42, 0.38, white, loc=(0, -0.01, 1.38), parent=root, ink=0.022)
    
    # Dot eyes and cartoon brows
    _card(c, f"{name}_eye_L", 0.04, 0.05, ink_black, loc=(-0.08, -0.025, 1.40), parent=root, ink=0.0)
    _card(c, f"{name}_eye_R", 0.04, 0.05, ink_black, loc=(0.08, -0.025, 1.40), parent=root, ink=0.0)
    _card(c, f"{name}_brow_L", 0.08, 0.02, ink_black, loc=(-0.08, -0.025, 1.46), parent=root, ink=0.0)
    _card(c, f"{name}_brow_R", 0.08, 0.02, ink_black, loc=(0.08, -0.025, 1.46), parent=root, ink=0.0)
    
    # Hat
    if role == "engineer":
        # Curved safety hardhat
        _card(c, f"{name}_helmet", 0.52, 0.18, hat_mat, loc=(0, -0.02, 1.58), parent=root, ink=0.016)
    else:
        # Bowler / top hat
        _card(c, f"{name}_hat_brim", 0.54, 0.05, hat_mat, loc=(0, -0.02, 1.54), parent=root, ink=0.015)
        _card(c, f"{name}_hat_crown", 0.34, 0.25, hat_mat, loc=(0, -0.02, 1.68), parent=root, ink=0.015)
        
    # 4. Articulated Hands (Left and Right IK Target empties)
    l_hand = bpy.data.objects.new(f"{name}_hand_L", None)
    l_hand.empty_display_size = 0.06
    l_hand.location = (-0.32, -0.10, 0.95)
    l_hand.parent = root
    c.objects.link(l_hand)
    _card(c, f"{name}_mitten_L", 0.10, 0.10, white, loc=(0,0,0), parent=l_hand, ink=0.012)
    
    r_hand = bpy.data.objects.new(f"{name}_hand_R", None)
    r_hand.empty_display_size = 0.06
    r_hand.location = (0.32, -0.10, 0.95)
    r_hand.parent = root
    c.objects.link(r_hand)
    _card(c, f"{name}_mitten_R", 0.10, 0.10, white, loc=(0,0,0), parent=r_hand, ink=0.012)
    
    return Char(name, root, head, torso, l_hand, r_hand)
