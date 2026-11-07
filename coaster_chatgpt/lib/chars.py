"""Articulated 2D-in-3D paper-cutout character rigs with IK hand sockets."""
from __future__ import annotations

import math
import bpy
from mathutils import Vector

from .utils import ensure_collection, make_empty, make_mesh_object
from .look import PALETTE, make_toon_material, make_ink_material, add_ink_outline


def _ellipse(cx, cz, rx, rz, count=18):
    return [(cx + rx * math.cos(2 * math.pi * i / count),
             cz + rz * math.sin(2 * math.pi * i / count)) for i in range(count)]


def _capsule_between(a, b, width, end_extra=0.08):
    a, b = Vector(a), Vector(b)
    d = b - a
    if d.length < 1e-6:
        d = Vector((0, 1))
    d.normalize()
    n = Vector((-d.y, d.x)) * width
    e = d * end_extra
    # CCW polygon in the local (x,z) plane.
    return [tuple(a - e + n), tuple(b + e + n), tuple(b + e - n), tuple(a - e - n)]


def _build_armature(name, collection):
    arm_data = bpy.data.armatures.new(name + '_ArmatureData')
    rig = bpy.data.objects.new(name + '_IK_Rig', arm_data)
    collection.objects.link(rig)
    rig.show_in_front = True
    rig.display_type = 'WIRE'
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    bones = {
        'root': ((0, 0, 0.0), (0, 0, 0.85), None),
        'spine': ((0, 0, 0.82), (0, 0, 2.02), 'root'),
        'head': ((0, 0, 2.00), (0, 0, 2.88), 'spine'),
        'upper_arm.L': ((-0.38, 0, 1.93), (-0.82, 0, 1.56), 'spine'),
        'forearm.L': ((-0.82, 0, 1.56), (-1.05, 0, 1.12), 'upper_arm.L'),
        'upper_arm.R': ((0.38, 0, 1.93), (0.82, 0, 1.56), 'spine'),
        'forearm.R': ((0.82, 0, 1.56), (1.05, 0, 1.12), 'upper_arm.R'),
        'thigh.L': ((-0.22, 0, 0.96), (-0.28, 0, 0.52), 'root'),
        'shin.L': ((-0.28, 0, 0.52), (-0.32, 0, 0.10), 'thigh.L'),
        'thigh.R': ((0.22, 0, 0.96), (0.28, 0, 0.52), 'root'),
        'shin.R': ((0.28, 0, 0.52), (0.32, 0, 0.10), 'thigh.R'),
    }
    edit_bones = {}
    for bone_name, (head, tail, parent_name) in bones.items():
        bone = arm_data.edit_bones.new(bone_name)
        bone.head = head
        bone.tail = tail
        edit_bones[bone_name] = bone
    for bone_name, (_, _, parent_name) in bones.items():
        if parent_name:
            edit_bones[bone_name].parent = edit_bones[parent_name]
            edit_bones[bone_name].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.select_set(False)
    return rig


def _append_poly(vertices, faces, face_materials, groups, poly, bone, material_index):
    start = len(vertices)
    vertices.extend([(float(x), -0.025, float(z)) for x, z in poly])
    signed_area = sum(poly[i][0] * poly[(i+1) % len(poly)][1] - poly[(i+1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    indices = list(range(start, start + len(poly)))
    if signed_area < 0:
        indices.reverse()  # consistent -Y-facing paper-card normals
    faces.append(tuple(indices))
    face_materials.append(material_index)
    groups.setdefault(bone, []).extend(range(start, start + len(poly)))


def _attach_weighted_mesh(obj, rig, groups, outline=0.035):
    for bone_name, indices in groups.items():
        vg = obj.vertex_groups.get(bone_name) or obj.vertex_groups.new(name=bone_name)
        if indices:
            vg.add(indices, 1.0, 'REPLACE')
    mod = obj.modifiers.new('Paper_Card_Armature', 'ARMATURE')
    mod.object = rig
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False
    if outline > 0:
        add_ink_outline(obj, outline, make_ink_material())
    return obj


def _make_feature(name, collection, rig, poly, bone='head', color=None, material=None, outline=0.0):
    vertices = [(x, -0.055, z) for x, z in poly]
    signed_area = sum(poly[i][0] * poly[(i+1) % len(poly)][1] - poly[(i+1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    face_indices = list(range(len(vertices)))
    if signed_area < 0:
        face_indices.reverse()
    faces = [tuple(face_indices)]
    mats = [material] if material else []
    obj = make_mesh_object(name, vertices, faces, collection, mats)
    obj.parent = rig.parent
    obj.location = (0, 0, 0)
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(vertices))), 1.0, 'REPLACE')
    mod = obj.modifiers.new('Feature_Armature', 'ARMATURE')
    mod.object = rig
    if outline > 0:
        add_ink_outline(obj, outline, make_ink_material())
    return obj


class CharacterRig:
    def __init__(self, name, root, armature, collection, hand_targets, style):
        self.name = name
        self.root = root
        self.armature = armature
        self.collection = collection
        self.hand_targets = hand_targets
        self.style = style
        self.emotion = 'neutral'
        self.mouth = None
        self.brows = []

    def set_anchor(self, location):
        self.root.parent = None
        self.root.location = Vector(location)
        self.root.rotation_euler = (0, 0, 0)

    def set_hand_target(self, side, world_position):
        target = self.hand_targets[side]
        bpy.context.view_layer.update()
        local = self.root.matrix_world.inverted() @ Vector(world_position)
        target.location = local

    def set_emotion(self, emotion):
        self.emotion = emotion
        self.root['emotion'] = emotion
        head = self.armature.pose.bones.get('head')
        if head:
            tilt = {'worried': -0.12, 'smug': 0.16, 'surprised': 0.0, 'determined': -0.06, 'joy': 0.08, 'neutral': 0.0}.get(emotion, 0.0)
            head.rotation_mode = 'XYZ'
            head.rotation_euler[1] = tilt
        if self.mouth:
            # Shape-key mouth poses are deterministic and independent of prior frames.
            for key in self.mouth.data.shape_keys.key_blocks:
                if key.name != 'Basis':
                    key.value = 0.0
            key_name = {'worried': 'frown', 'smug': 'smile', 'joy': 'smile', 'surprised': 'open', 'determined': 'flat'}.get(emotion)
            if key_name and self.mouth.data.shape_keys.key_blocks.get(key_name):
                self.mouth.data.shape_keys.key_blocks[key_name].value = 1.0


def build_character(name, collection, location, style='builder'):
    """Build a flat illustrated character with articulated, socket-driven arms."""
    root = make_empty(name + '_Root', collection, location, 'CIRCLE', 0.42)
    rig = _build_armature(name, collection)
    rig.parent = root
    rig.location = (0, 0, 0)

    skin = make_toon_material('MAT_Character_Skin', [(0.35, 0.14, 0.08, 1), PALETTE['skin'], PALETTE['skin_light']])
    shirt = make_toon_material('MAT_Builder_Shirt', [(0.02, 0.07, 0.10, 1), (0.12, 0.28, 0.34, 1), (0.40, 0.58, 0.60, 1)])
    leather = make_toon_material('MAT_Builder_Leather', [(0.09, 0.035, 0.02, 1), (0.31, 0.12, 0.045, 1), (0.62, 0.31, 0.11, 1)])
    suit = make_toon_material('MAT_Rival_Suit', [(0.018, 0.025, 0.045, 1), (0.08, 0.10, 0.16, 1), (0.27, 0.31, 0.38, 1)])
    white = make_toon_material('MAT_Character_White', [(0.38, 0.39, 0.40, 1), (0.82, 0.82, 0.75, 1), (1.0, 0.98, 0.86, 1)])
    accent = make_toon_material('MAT_Character_Accent', [(0.18, 0.025, 0.035, 1), PALETTE['red'], (1.0, 0.30, 0.22, 1)])
    dark = make_toon_material('MAT_Character_Dark', [(0.012, 0.015, 0.025, 1), (0.055, 0.065, 0.085, 1), (0.20, 0.22, 0.26, 1)])
    gold = make_toon_material('MAT_Character_Gold', [(0.24, 0.10, 0.015, 1), PALETTE['gold'], (1.0, 0.82, 0.36, 1)])

    mats = [shirt, leather, suit, skin, white, accent, dark, gold]
    vertices, faces, face_mats, groups = [], [], [], {}

    # Torso and neck.
    torso_mat = 0 if style == 'builder' else 2
    _append_poly(vertices, faces, face_mats, groups,
                 [(-0.46, 0.92), (-0.44, 1.95), (-0.30, 2.12), (0.30, 2.12), (0.44, 1.95), (0.46, 0.92)],
                 'spine', torso_mat)
    _append_poly(vertices, faces, face_mats, groups,
                 [(-0.13, 1.94), (-0.13, 2.24), (0.13, 2.24), (0.13, 1.94)], 'spine', 3)

    if style == 'builder':
        # Leather apron panel and straps over the shirt.
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.36, 1.88), (0.36, 1.88), (0.31, 0.95), (-0.31, 0.95)], 'spine', 1)
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.31, 1.92), (-0.18, 1.92), (-0.29, 2.17), (-0.42, 2.12)], 'spine', 1)
        _append_poly(vertices, faces, face_mats, groups,
                     [(0.18, 1.92), (0.31, 1.92), (0.42, 2.12), (0.29, 2.17)], 'spine', 1)
        # Apron pocket and belt.
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.18, 1.34), (0.18, 1.34), (0.17, 1.12), (-0.17, 1.12)], 'spine', 7)
        # Cap: brim plus low, flat crown.
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.43, 2.71), (0.43, 2.71), (0.35, 2.82), (-0.35, 2.82)], 'head', 6)
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.39, 2.78), (-0.31, 2.99), (0.14, 3.02), (0.39, 2.83)], 'head', 6)
    else:
        # Crisp waistcoat, lapels, and red tie.
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.10, 2.08), (0.10, 2.08), (0.13, 1.15), (0.0, 1.02), (-0.13, 1.15)], 'spine', 5)
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.38, 2.05), (-0.12, 2.02), (-0.02, 1.84), (-0.22, 1.70)], 'spine', 4)
        _append_poly(vertices, faces, face_mats, groups,
                     [(0.38, 2.05), (0.12, 2.02), (0.02, 1.84), (0.22, 1.70)], 'spine', 4)
        # Sharp bowler: wide brim, upright crown and small highlight.
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.50, 2.72), (0.50, 2.72), (0.43, 2.80), (-0.43, 2.80)], 'head', 6)
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.34, 2.76), (-0.30, 3.03), (-0.18, 3.12), (0.18, 3.12), (0.30, 3.03), (0.34, 2.76)], 'head', 6)
        _append_poly(vertices, faces, face_mats, groups,
                     [(-0.18, 3.05), (0.18, 3.05), (0.16, 3.10), (-0.16, 3.10)], 'head', 7)

    # Head silhouette.
    _append_poly(vertices, faces, face_mats, groups, _ellipse(0, 2.48, 0.42, 0.47), 'head', 3)

    # Arms are separate weighted paper sleeves, so IK can articulate them.
    for side, sign in [('L', -1), ('R', 1)]:
        shoulder = (sign * 0.38, 1.92)
        elbow = (sign * 0.82, 1.56)
        wrist = (sign * 1.05, 1.12)
        _append_poly(vertices, faces, face_mats, groups,
                     _capsule_between(shoulder, elbow, 0.15, 0.07), 'upper_arm.' + side, torso_mat)
        _append_poly(vertices, faces, face_mats, groups,
                     _capsule_between(elbow, wrist, 0.13, 0.07), 'forearm.' + side, torso_mat)
        _append_poly(vertices, faces, face_mats, groups,
                     _ellipse(wrist[0], wrist[1], 0.16, 0.14, 14), 'forearm.' + side, 3)
        # Legs and boots.
        hip = (sign * 0.22, 0.96)
        knee = (sign * 0.28, 0.52)
        ankle = (sign * 0.32, 0.10)
        _append_poly(vertices, faces, face_mats, groups,
                     _capsule_between(hip, knee, 0.17, 0.05), 'thigh.' + side, torso_mat if style == 'builder' else 2)
        _append_poly(vertices, faces, face_mats, groups,
                     _capsule_between(knee, ankle, 0.14, 0.05), 'shin.' + side, 6)
        foot_x = sign * 0.39
        _append_poly(vertices, faces, face_mats, groups,
                     [(foot_x-0.20, 0.03), (foot_x+0.18, 0.03), (foot_x+0.14, 0.19), (foot_x-0.16, 0.19)], 'shin.' + side, 6)

    body = make_mesh_object(name + '_Paper_Cutout', vertices, faces, collection, mats, face_mats)
    body.parent = root
    body.location = (0, 0, 0)
    _attach_weighted_mesh(body, rig, groups, outline=0.045)
    body['billboard_character'] = True
    body['art_direction'] = 'flat paper-cutout in XZ plane, facing camera at negative Y'

    # Face features are independent flat cards weighted to the head bone.
    eye_mat = dark
    eye_l = _make_feature(name + '_Eye_L', collection, rig, _ellipse(-0.145, 2.53, 0.045, 0.065, 12), color=PALETTE['black'], material=eye_mat)
    eye_r = _make_feature(name + '_Eye_R', collection, rig, _ellipse(0.145, 2.53, 0.045, 0.065, 12), color=PALETTE['black'], material=eye_mat)
    mouth_poly = [(-0.12, 2.27), (-0.06, 2.24), (0.0, 2.235), (0.06, 2.24), (0.12, 2.27), (0.08, 2.22), (0.0, 2.205), (-0.08, 2.22)]
    mouth = _make_feature(name + '_Mouth', collection, rig, mouth_poly, material=dark)
    # Mouth shape keys: smile, frown, open, and flat. Preserve deterministic neutral basis.
    mouth.shape_key_add(name='Basis')
    smile = mouth.shape_key_add(name='smile')
    frown = mouth.shape_key_add(name='frown')
    opened = mouth.shape_key_add(name='open')
    flat = mouth.shape_key_add(name='flat')
    for i, v in enumerate(mouth.data.vertices):
        co = v.co.copy()
        # Original mesh local coordinates already carry exact X/Z.
        if i in (0, 4):
            smile.data[i].co.z -= 0.045
            frown.data[i].co.z += 0.045
        if i in (1, 2, 3, 5, 6, 7):
            opened.data[i].co.z += (0.04 if i in (1, 3, 5, 7) else -0.025)
        flat.data[i].co.z = co.z + (0.0 if i in (0, 4) else 0.01)
    brow_l = _make_feature(name + '_Brow_L', collection, rig,
                           [(-0.24, 2.67), (-0.08, 2.70), (-0.07, 2.75), (-0.25, 2.72)], material=dark)
    brow_r = _make_feature(name + '_Brow_R', collection, rig,
                           [(0.08, 2.70), (0.24, 2.67), (0.25, 2.72), (0.07, 2.75)], material=dark)

    # IK hand target empties. These are driven to real prop sockets by acting.json.
    hand_targets = {}
    for side, sign in [('L', -1), ('R', 1)]:
        target = make_empty(name + '_IK_HAND_' + side, collection, (sign * 1.05, 0, 1.12), 'SPHERE', 0.10)
        target.parent = root
        target.location = (sign * 1.05, 0, 1.12)
        pole = make_empty(name + '_IK_POLE_' + side, collection, (sign * 0.75, -0.45, 1.55), 'CIRCLE', 0.08)
        pole.parent = root
        pole.location = (sign * 0.75, -0.45, 1.55)
        forearm = rig.pose.bones['forearm.' + side]
        ik = forearm.constraints.new('IK')
        ik.name = 'HAND_SOCKET_IK_' + side
        ik.target = target
        ik.pole_target = pole
        ik.chain_count = 2
        ik.use_stretch = False
        hand_targets[side] = target

    # Keep control empties out of the render but available for the director.
    for obj in list(collection.objects):
        if obj.name.startswith(name + '_IK_'):
            obj.hide_render = True

    char = CharacterRig(name, root, rig, collection, hand_targets, style)
    char.mouth = mouth
    char.brows = [brow_l, brow_r]
    char.set_emotion('neutral')
    return char


def build_builder(collection, location=(-5.7, -1.4, 0.0)):
    return build_character('builder', collection, location, 'builder')


def build_rival(collection, location=(4.6, -1.3, 0.0)):
    return build_character('rival', collection, location, 'rival')
