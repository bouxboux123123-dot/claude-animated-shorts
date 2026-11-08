"""Flat paper-cutout character rigs staged as 2D cards in the 3D sets."""
from __future__ import annotations

import bpy
from mathutils import Vector
from .look import toon_material, add_outline


def material(name, color):
    m = bpy.data.materials.get(name)
    if m is not None:
        try:
            _ = m.name
            return m
        except Exception:
            pass
    return toon_material(name, color)

class MatProxy:
    def __init__(self, name, color):
        self.name = name
        self.color = color
    def __call__(self):
        return material(self.name, self.color)
    def resolve(self):
        return material(self.name, self.color)

INK = MatProxy("Character ink | dark plum", (0.035, 0.018, 0.04, 1))
SKIN = MatProxy("Character | warm paper skin", (0.90, 0.64, 0.42, 1))
BUILDER_COAT = MatProxy("Builder | russet work shirt", (0.57, 0.22, 0.12, 1))
BUILDER_LEATHER = MatProxy("Builder | leather apron", (0.28, 0.13, 0.075, 1))
RIVAL_SUIT = MatProxy("Rival | midnight suit", (0.09, 0.12, 0.19, 1))
RIVAL_VEST = MatProxy("Rival | plum vest", (0.32, 0.12, 0.18, 1))
PAPER = MatProxy("Character | cream shirt", (0.91, 0.84, 0.66, 1))

def _resolve_mat(mat):
    if mat is None:
        return None
    if isinstance(mat, MatProxy):
        return mat.resolve()
    if callable(mat):
        return mat()
    try:
        _ = mat.name
        return mat
    except Exception:
        pass
    return None

def ellipsoid(name, loc, scale, mat, outline=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    m = _resolve_mat(mat)
    if m:
        obj.data.materials.append(m)
    if outline:
        add_outline(obj, 0.025)
    return obj


def flat_box(name, loc, scale, mat, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m = _resolve_mat(mat)
    if m:
        obj.data.materials.append(m)
    if bevel:
        mod = obj.modifiers.new("Card-stock rounded corner", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    add_outline(obj, 0.022)
    return obj


def line(name, points, mat=INK, width=0.035):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = width
    data.bevel_resolution = 2
    spline = data.splines.new("POLY")
    spline.points.add(len(points)-1)
    for p, v in zip(spline.points, points):
        p.co = (*v, 1)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    m = _resolve_mat(mat)
    if m:
        data.materials.append(m)
    return obj


class CardCharacter:
    def __init__(self, name, location, costume="builder"):
        self.name = name
        self.costume = costume
        self.root = bpy.data.objects.new(name + " | card rig", None)
        bpy.context.collection.objects.link(self.root)
        self.root.location = location
        self.parts = []
        self.targets = {}
        self.arms = {}
        self._build()

    def attach(self, obj):
        obj.parent = self.root
        self.parts.append(obj)
        return obj

    def socket(self, name, local):
        obj = bpy.data.objects.new(f"{self.name} | IK target {name}", None)
        bpy.context.collection.objects.link(obj)
        obj.parent = self.root
        obj.location = local
        obj.empty_display_type = "SPHERE"
        obj.empty_display_size = 0.10
        self.targets[name] = obj
        return obj

    def _build(self):
        shirt = BUILDER_COAT if self.costume == "builder" else PAPER
        jacket = BUILDER_LEATHER if self.costume == "builder" else RIVAL_SUIT
        vest = BUILDER_LEATHER if self.costume == "builder" else RIVAL_VEST
        # Legs and boots. Cards face toward -Y, so all facial details sit in front.
        for side, x in (("L", -0.31), ("R", 0.31)):
            leg = self.attach(flat_box(f"{self.name} | {side} trouser leg", (x, 0, 0.78), (0.38, 0.34, 1.2), jacket, 0.08))
            boot = self.attach(flat_box(f"{self.name} | {side} boot", (x+0.04, -0.06, 0.13), (0.62, 0.48, 0.27), INK, 0.08))
        torso = self.attach(ellipsoid(self.name + " | jacket torso", (0, 0, 2.05), (0.72, 0.34, 0.94), shirt))
        if self.costume == "builder":
            apron = self.attach(flat_box(self.name + " | leather apron", (0, -0.34, 1.95), (0.77, 0.11, 1.05), BUILDER_LEATHER, 0.07))
            for z in (1.6, 1.86, 2.12):
                self.attach(flat_box(self.name + " | apron stitch", (0, -0.41, z), (0.36, 0.025, 0.025), PAPER, 0.01))
        else:
            self.attach(flat_box(self.name + " | vest", (0, -0.31, 2.04), (0.44, 0.10, 0.74), vest, 0.04))
            self.attach(flat_box(self.name + " | tie", (0, -0.39, 2.22), (0.11, 0.06, 0.52), RED_TIE, 0.02))
        # Arms have two-segment posing via IK-style wrist target empties.
        for side, sign in (("left", -1), ("right", 1)):
            shoulder = (0.56*sign, -0.03, 2.52)
            target = (0.96*sign, -0.12, 1.85)
            self.socket(side, target)
            sleeve = self.attach(ellipsoid(f"{self.name} | {side} sleeve", shoulder, (0.29, 0.23, 0.46), shirt))
            upper = line(f"{self.name} | {side} upper arm", [shoulder, (0.78*sign, -0.06, 2.18), target], INK, 0.07)
            upper.parent = self.root
            self.arms[side] = upper
            hand = self.attach(ellipsoid(f"{self.name} | {side} hand", target, (0.16, 0.12, 0.16), SKIN, outline=False))
            self.arms[side + "_hand"] = hand
        # Head and expressive face card.
        head = self.attach(ellipsoid(self.name + " | bean head", (0, -0.04, 3.20), (0.73, 0.28, 0.78), SKIN))
        # Eyes are small ink dots with no highlights; brows and mouth are curves.
        for x in (-0.23, 0.23):
            self.attach(ellipsoid(self.name + " | ink-dot eye", (x, -0.31, 3.30), (0.065, 0.035, 0.09), INK, outline=False))
        mouth = line(self.name + " | mouth", [(-0.18, -0.32, 2.97), (0, -0.34, 2.94), (0.18, -0.32, 2.97)], INK, 0.025)
        mouth.parent = self.root
        if self.costume == "builder":
            cap = self.attach(flat_box(self.name + " | flat cap", (0, -0.02, 3.90), (1.13, 0.56, 0.23), BUILDER_LEATHER, 0.08))
            self.attach(flat_box(self.name + " | cap brim", (0, -0.36, 3.82), (0.92, 0.34, 0.12), BUILDER_LEATHER, 0.04))
        else:
            crown = self.attach(ellipsoid(self.name + " | bowler crown", (0, -0.02, 3.88), (0.51, 0.42, 0.34), INK))
            brim = self.attach(flat_box(self.name + " | bowler brim", (0, -0.03, 3.73), (1.18, 0.59, 0.12), INK, 0.06))
        self.root["character_role"] = self.costume
        self.root["acting_channels"] = "hold, operate, clasp, emotion, impact"

    def set_hand_target(self, hand, local_position):
        """Set a physical IK hand target in character-local coordinates."""
        target = self.targets[hand]
        target.location = local_position
        arm = self.arms[hand]
        points = arm.data.splines[0].points
        shoulder = Vector(((-0.56 if hand == "left" else 0.56), -0.03, 2.52))
        wrist = Vector(local_position)
        elbow = (shoulder + wrist) * 0.5 + Vector((0, -0.04, 0.08))
        for p, v in zip(points, (shoulder, elbow, wrist)):
            p.co = (*v, 1)
        self.arms[hand + "_hand"].location = local_position

    def set_emotion(self, value):
        """A tiny whole-card lean gives the emotion channel a visible acting cue."""
        self.root.rotation_euler[1] = max(-0.18, min(0.18, float(value)))


RED_TIE = material("Rival | muted red tie", (0.56, 0.08, 0.09, 1))


def build_characters(anchors):
    builder = CardCharacter("Builder", anchors["workshop_night"]["builder"], "builder")
    rival = CardCharacter("Rival", anchors["workshop_night"]["rival"], "rival")
    return {"builder": builder, "rival": rival}
