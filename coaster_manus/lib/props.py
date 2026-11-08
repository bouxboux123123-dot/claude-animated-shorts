"""Parametric hero props. Every visible hero prop derives from PropSpec."""
from __future__ import annotations

import math
import bpy
from mathutils import Vector
from .look import toon_material, add_outline


def _mat(name, color):
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
        return _mat(self.name, self.color)
    def resolve(self):
        return _mat(self.name, self.color)

WOOD = MatProxy("Paint | warm ochre wood", (0.55, 0.27, 0.10, 1))
IRON = MatProxy("Paint | blue-black iron", (0.055, 0.08, 0.13, 1))
BRASS = MatProxy("Paint | aged brass", (0.78, 0.49, 0.13, 1))
RED = MatProxy("Paint | fairground red", (0.66, 0.13, 0.10, 1))
CREAM = MatProxy("Paint | canvas cream", (0.88, 0.78, 0.58, 1))

def _resolve_mat(material):
    if material is None:
        return None
    if isinstance(material, MatProxy):
        return material.resolve()
    if callable(material):
        return material()
    try:
        _ = material.name
        return material
    except Exception:
        pass
    return None

def _finish(obj, name, material, outline=True):
    obj.name = name
    m = _resolve_mat(material)
    if m:
        obj.data.materials.append(m)
    if outline:
        add_outline(obj, 0.018)
    return obj


def _cube(name, location, scale, material, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Hand-cut softened edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return _finish(obj, name, material)


def _cylinder(name, location, radius, depth, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=depth, location=location, rotation=rotation)
    return _finish(bpy.context.object, name, material)


def _curve(name, points, material, bevel=0.06, cyclic=False):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 2
    data.bevel_depth = bevel
    data.bevel_resolution = 2
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, xyz in zip(spline.points, points):
        p.co = (*xyz, 1)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    m = _resolve_mat(material)
    if m:
        data.materials.append(m)
    return obj


class PropSpec:
    """Base object with named sockets and explicit normalized animation channels."""
    channel_defaults = {}

    def __init__(self, name, location=(0, 0, 0)):
        self.name = name
        self.location = Vector(location)
        self.root = bpy.data.objects.new(name + " | root", None)
        bpy.context.collection.objects.link(self.root)
        self.root.location = self.location
        self.parts = []
        self.sockets = {}
        self.channels = dict(self.channel_defaults)
        self.root["prop_spec"] = self.__class__.__name__
        for key, value in self.channels.items():
            self.root[key] = float(value)

    def attach(self, obj):
        obj.parent = self.root
        self.parts.append(obj)
        return obj

    def socket(self, name, local_location):
        empty = bpy.data.objects.new(f"{self.name} | socket:{name}", None)
        bpy.context.collection.objects.link(empty)
        empty.parent = self.root
        empty.location = local_location
        empty.empty_display_type = "SPHERE"
        empty.empty_display_size = 0.13
        self.sockets[name] = empty
        return empty

    def set_channel(self, name, value):
        if name not in self.channels:
            raise KeyError(f"{self.name} has no channel {name!r}")
        value = max(0.0, min(1.0, float(value)))
        self.channels[name] = value
        self.root[name] = value

    def update(self, frame):
        """Subclasses derive all visible state from their channel values."""
        return None


class LoopTrackProp(PropSpec):
    channel_defaults = {"bend_bottom": 0.0, "squeeze_sides": 0.0}

    def __init__(self, name="LoopTrack", location=(0, 0, 0), radius=3.1, sides=2):
        super().__init__(name, location)
        self.radius = radius
        self.rail_gap = 0.54
        self.sides = sides
        self.rails = []
        self.ties = []
        self._build_static()

    def _shape(self, theta, offset):
        r = self.radius
        bend = self.channels["bend_bottom"]
        squeeze = self.channels["squeeze_sides"]
        sin_t, cos_t = math.sin(theta), math.cos(theta)
        # The side clamp narrows the middle of the loop; the top stays broad.
        side_weight = max(0.0, 1.0 - abs(cos_t) ** 1.7)
        xscale = 1.0 - 0.48 * squeeze * side_weight
        x = (r * sin_t + offset) * xscale
        z = r * (1.0 - cos_t)
        # Broaden the lower 70 degrees without lifting the rail off the ground.
        bottom_weight = max(0.0, cos_t) ** 5
        z -= bend * 0.45 * r * bottom_weight * (1.0 - cos_t)
        x += bend * 0.20 * r * sin_t * bottom_weight
        return (x, 0.0, z)

    def _build_static(self):
        count = 72
        for side in (-1, 1):
            pts = [self._shape(2 * math.pi * i / count, side * self.rail_gap / 2) for i in range(count + 1)]
            rail = self.attach(_curve(f"{self.name} | running rail {side}", pts, IRON, 0.095))
            self.rails.append(rail)
        for i in range(0, count, 4):
            theta = 2 * math.pi * i / count
            p0 = Vector(self._shape(theta, -self.rail_gap / 2))
            p1 = Vector(self._shape(theta, self.rail_gap / 2))
            # Cross ties are kept as small beveled bars; update positions with the track.
            mid = (p0 + p1) * 0.5
            tie = _cube(f"{self.name} | tie {i:02d}", self.location + mid, (self.rail_gap + 0.18, 0.20, 0.16), WOOD, 0.025)
            tie.parent = self.root
            tie.location = mid
            self.ties.append((i, tie))
        self.socket("track_entry", (-self.radius, 0, self.radius))
        self.socket("track_exit", (self.radius, 0, self.radius))
        self.update(1)

    def update(self, frame):
        count = 72
        for side, rail in zip((-1, 1), self.rails):
            spline = rail.data.splines[0]
            for i, point in enumerate(spline.points):
                point.co = (*self._shape(2 * math.pi * i / count, side * self.rail_gap / 2), 1)
        for i, tie in self.ties:
            theta = 2 * math.pi * i / count
            p0 = Vector(self._shape(theta, -self.rail_gap / 2))
            p1 = Vector(self._shape(theta, self.rail_gap / 2))
            mid = (p0 + p1) * 0.5
            tie.location = mid
            tie.dimensions.x = (p1 - p0).length + 0.12
            tie.rotation_euler[1] = math.atan2((p1 - p0).z, (p1 - p0).x)


class SledgehammerProp(PropSpec):
    channel_defaults = {"swing_stroke": 0.0}

    def __init__(self, name="Sledgehammer", location=(0, 0, 0)):
        super().__init__(name, location)
        self.handle = self.attach(_cylinder(name + " | ash handle", self.location, 0.085, 1.65, WOOD))
        self.head = self.attach(_cube(name + " | iron head", self.location, (0.72, 0.36, 0.34), IRON, 0.08))
        self.handle.location = (0, 0, 0)
        self.head.location = (0, 0, 0.85)
        self.handle.rotation_euler[1] = -0.18
        self.socket("grip_main", (0, 0, -0.25))
        self.socket("grip_twohand", (0, 0, -0.58))
        self.pivot = bpy.data.objects.new(name + " | swing pivot", None)
        bpy.context.collection.objects.link(self.pivot)
        self.pivot.parent = self.root
        self.handle.parent = self.pivot
        self.head.parent = self.pivot
        self.pivot.location = (0, 0, 0)
        self.spark = _cube(name + " | impact spark", (0, 0, 0), (0.05, 0.05, 0.05), BRASS, 0)
        self.spark.parent = self.root
        self.update(1)

    def update(self, frame):
        s = self.channels["swing_stroke"]
        self.pivot.rotation_euler[1] = -0.2 + math.sin(math.pi * s) * 1.55
        self.pivot.location = (0.25 * s, 0, 1.05 - 0.26 * s)
        self.spark.location = (0.5, -0.12, 0.12 + 0.24 * (1 - abs(2 * s - 1)))
        self.spark.scale = (0.18, 0.09, 0.35) if 0.42 < s < 0.7 else (0.001, 0.001, 0.001)


class TestDummyProp(PropSpec):
    channel_defaults = {"crush_progress": 0.0}

    def __init__(self, name="TestDummy", location=(0, 0, 0)):
        super().__init__(name, location)
        self.base = self.attach(_cube(name + " | weighted base", (0, 0, 0.15), (1.0, 0.55, 0.25), IRON))
        self.body = self.attach(_cube(name + " | accordion torso", (0, 0, 1.0), (0.72, 0.54, 1.45), CREAM, 0.17))
        self.head = self.attach(_cube(name + " | wooden head", (0, 0, 1.95), (0.65, 0.50, 0.57), WOOD, 0.18))
        for z in (0.58, 0.82, 1.06, 1.30):
            band = self.attach(_cube(name + " | torso fold", (0, -0.29, z), (0.76, 0.07, 0.07), RED, 0.02))
        self.body.parent = self.root
        self.head.parent = self.root
        self.socket("safety_belt", (0, -0.42, 0.95))
        self.socket("test_stand", (0, 0, 0.25))

    def update(self, frame):
        c = self.channels["crush_progress"]
        self.body.scale.z = 1.0 - 0.67 * c
        self.body.location.z = 1.0 - 0.48 * c
        self.head.location.z = 1.95 - 0.92 * c


class TurnbuckleCrankProp(PropSpec):
    channel_defaults = {"crank_angle": 0.0}

    def __init__(self, name="TurnbuckleCrank", location=(0, 0, 0)):
        super().__init__(name, location)
        self.bar = self.attach(_cylinder(name + " | threaded rod", (0, 0, 0), 0.08, 2.4, IRON, (0, math.pi / 2, 0)))
        self.wheel = self.attach(_cylinder(name + " | crank wheel", (0, 0, 0.2), 0.35, 0.12, BRASS, (math.pi / 2, 0, 0)))
        self.grip = self.attach(_cylinder(name + " | hand grip", (0, 0, 0.6), 0.075, 0.74, WOOD))
        self.wheel.parent = self.root
        self.grip.parent = self.root
        self.socket("crank_grip", (0, -0.1, 0.55))
        self.socket("brace_hand", (-0.45, 0, 0))

    def update(self, frame):
        angle = self.channels["crank_angle"] * math.tau * 1.4
        self.wheel.rotation_euler[1] = angle
        self.grip.location = (0, 0.6 * math.sin(angle), 0.2 + 0.6 * math.cos(angle))


class CoasterCartProp(PropSpec):
    channel_defaults = {"track_progress": 0.0}

    def __init__(self, name="CoasterCart", location=(0, 0, 0), path=None):
        super().__init__(name, location)
        self.path = path or self.default_path()
        self.path_curve = self._build_bezier_path()
        self.body = self.attach(_cube(name + " | red cart shell", (0, 0, 0), (1.65, 1.05, 0.62), RED, 0.18))
        self.seat = self.attach(_cube(name + " | padded seat", (0, 0.10, 0.36), (0.82, 0.62, 0.26), CREAM, 0.1))
        self.wheels = []
        for x in (-0.55, 0.55):
            for y in (-0.54, 0.54):
                wheel = self.attach(_cylinder(name + " | wheel", (x, y, -0.28), 0.22, 0.16, IRON, (math.pi / 2, 0, 0)))
                self.wheels.append(wheel)
        self.socket("rider_seat", (0, -0.08, 0.55))
        self.update(1)

    @staticmethod
    def default_path():
        # World-space local path: first hill -> track entry -> full loop -> run-out.
        return [(-8, 0, 8), (-6, 0, 5.8), (-4.4, 0, 2.8), (-3.0, 0, 0.08),
                (0, 0, 0.08), (3.0, 0, 0.08), (4.0, 0, 0.6), (3.6, 0, 2.2),
                (0, 0, 6.2), (-3.6, 0, 2.2), (-4.0, 0, 0.6), (-3.0, 0, 0.08),
                (0, 0, 0.08), (6, 0, 0.08), (9, 0, 1.0)]

    def _build_bezier_path(self):
        """Store the cart route as a real Blender cubic Bézier spline."""
        data = bpy.data.curves.new(self.name + " | cubic Bezier path", "CURVE")
        data.dimensions = "3D"
        data.resolution_u = 16
        spline = data.splines.new("BEZIER")
        spline.bezier_points.add(len(self.path)-1)
        for point, xyz in zip(spline.bezier_points, self.path):
            point.co = xyz
            point.handle_left_type = "AUTO"
            point.handle_right_type = "AUTO"
        obj = bpy.data.objects.new(self.name + " | hidden Bezier guide", data)
        bpy.context.collection.objects.link(obj)
        obj.location = self.location
        obj.hide_render = True
        obj.hide_set(True)
        return obj

    def _sample(self, t):
        """Evaluate the same cubic Bézier segments stored in path_curve."""
        points = self.path_curve.data.splines[0].bezier_points
        pos = max(0.0, min(1.0, float(t))) * (len(points)-1)
        i = min(int(pos), len(points)-2)
        u = pos-i
        p0, p1 = points[i], points[i+1]
        v = 1-u
        return Vector((v**3 * p0.co) + (3*v*v*u * p0.handle_right) +
                      (3*v*u*u * p1.handle_left) + (u**3 * p1.co))

    def update(self, frame):
        t = self.channels["track_progress"]
        p = self._sample(t)
        tangent = self._sample(min(1.0, t + 0.002)) - self._sample(max(0.0, t - 0.002))
        self.root.location = self.location + p
        self.root.rotation_euler[1] = -math.atan2(tangent.z, tangent.x) if tangent.length else 0


class ToyRoadsterProp(PropSpec):
    """Unlabelled toy roadster used only for the safe hairpin-speed analogy."""
    channel_defaults = {"drive_progress": 0.0, "flip_progress": 0.0}

    def __init__(self, name="AnalogyRoadster", location=(0, 0, 0)):
        super().__init__(name, location)
        red_paint = _mat("Analogy car | vermilion", (0.78, 0.12, 0.08, 1))
        blue_glass = _mat("Analogy car | blue glass", (0.18, 0.39, 0.57, 1))
        self.attach(_cube(name + " | toy roadster body", (0, 0, 0.38), (1.65, 0.78, 0.42), red_paint, 0.14))
        self.attach(_cube(name + " | blue cabin", (-0.10, 0, 0.68), (0.78, 0.62, 0.42), blue_glass, 0.12))
        self.wheels = []
        for x in (-0.52, 0.52):
            for y in (-0.40, 0.40):
                self.wheels.append(self.attach(_cylinder(name + " | toy wheel", (x, y, 0.14), 0.19, 0.13, IRON, (math.pi/2, 0, 0))))
        self.socket("driver_seat", (-0.08, -0.06, 0.86))
        self.update(1)

    def update(self, frame):
        drive = self.channels["drive_progress"]
        flip = self.channels["flip_progress"]
        self.root.location = self.location + Vector((-2.5 + 5.0*drive, 0, 0.10 + 1.10*math.sin(math.pi*flip)))
        self.root.rotation_euler[0] = math.tau * flip
