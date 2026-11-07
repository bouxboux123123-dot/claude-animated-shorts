"""Concrete procedural hero props for the roller-coaster short.

Every hero prop is a PropSpec and owns real mesh geometry plus named sockets.
Channel updates are deterministic and safe in Blender background mode.
"""
import math
import bpy
from mathutils import Vector

from .look import toon_mat, anchor_empty
from .meshlib import box, cylinder, tube_between, curve_tube


INK = (0.015, 0.012, 0.025)


def _link(collection, obj):
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    return obj


def _socket(collection, name, parent, location):
    sock = anchor_empty(collection, name, location, parent=parent)
    sock.empty_display_type = 'SPHERE'
    sock.empty_display_size = 0.12
    return sock


def _clear_children(root):
    # Keep sockets/IK empties; only rebuild concrete geometry children.
    for child in list(root.children):
        if child.type != 'EMPTY':
            bpy.data.objects.remove(child, do_unlink=True)


class PropSpec:
    """Base class for all concrete hero props."""
    channels = {}

    def __init__(self, name: str):
        self.name = name
        self._obj = None
        self.channel_values = dict(self.channels)
        self.collection = None

    def create(self, collection):
        self.collection = collection
        self._obj = bpy.data.objects.new(self.name, None)
        collection.objects.link(self._obj)
        return self._obj

    @property
    def obj(self):
        return self._obj

    def set_channel(self, channel, value):
        if channel not in self.channel_values:
            raise KeyError(f'{self.name}: unknown channel {channel}')
        self.channel_values[channel] = max(0.0, min(1.0, float(value)))
        method = getattr(self, f'set_{channel}', None)
        if method:
            method(value)


class LoopTrackProp(PropSpec):
    """Two rails around a morphing loop: bend_bottom + squeeze_sides."""
    channels = {'bend_bottom': 0.0, 'squeeze_sides': 0.0, 'snap_force': 0.0}

    def create(self, collection):
        super().create(collection)
        self.rail_material = toon_mat('track_steel', (0.45, 0.48, 0.54))
        self.tie_material = toon_mat('track_ties', (0.25, 0.15, 0.09))
        self._build_geometry()
        self.grip_socket = _socket(collection, f'{self.name}_track_socket', self._obj, (0, 0, 0))
        return self._obj

    def _points(self):
        bend = self.channel_values['bend_bottom']
        squeeze = self.channel_values['squeeze_sides']
        center_z, radius = 2.8, 2.45
        points = []
        # Start at bottom, travel clockwise; lower section becomes a longer lazy curve.
        for i in range(25):
            theta = -math.pi / 2 + (math.tau * i / 24.0)
            side_scale = 1.0 - 0.46 * squeeze
            x = radius * side_scale * math.cos(theta)
            z = center_z + radius * math.sin(theta)
            lower = max(0.0, -math.sin(theta))
            z += bend * 0.58 * lower
            x *= 1.0 - bend * 0.16 * lower
            points.append(Vector((x, 0, z)))
        return points

    def _build_geometry(self):
        _clear_children(self._obj)
        points = self._points()
        for y in (-0.16, 0.16):
            rail = curve_tube(f'{self.name}_rail_{y:+.2f}',
                              [(p.x, y, p.z) for p in points],
                              radius=0.085, sides=8, material=self.rail_material)
            _link(self.collection, rail)
            rail.parent = self._obj
        # Cross ties make the track read as a track, not a floating curve.
        for i, p in enumerate(points[::2]):
            tie = tube_between(f'{self.name}_tie_{i:02d}',
                               (p.x, -0.27, p.z), (p.x, 0.27, p.z),
                               radius=0.055, sides=6, material=self.tie_material)
            _link(self.collection, tie)
            tie.parent = self._obj

    def set_bend_bottom(self, value):
        self.channel_values['bend_bottom'] = max(0.0, min(1.0, float(value)))
        if self._obj:
            self._build_geometry()

    def set_squeeze_sides(self, value):
        self.channel_values['squeeze_sides'] = max(0.0, min(1.0, float(value)))
        if self._obj:
            self._build_geometry()


class SledgehammerProp(PropSpec):
    """Wooden shaft, steel head, and two explicit grip sockets."""
    channels = {'swing_stroke': 0.0}

    def create(self, collection):
        super().create(collection)
        wood = toon_mat('hammer_wood', (0.42, 0.18, 0.07))
        steel = toon_mat('hammer_steel', (0.36, 0.40, 0.47), metallic=0.35)
        shaft = cylinder(f'{self.name}_shaft', 0.075, 1.55, 12, wood)
        shaft.location.z = -0.18
        _link(collection, shaft); shaft.parent = self._obj
        head = box(f'{self.name}_head', (0.72, 0.36, 0.42), steel)
        head.location.z = 0.62
        _link(collection, head); head.parent = self._obj
        self.grip_main = _socket(collection, f'{self.name}_grip_main', self._obj, (0, 0, -0.62))
        self.grip_twohand = _socket(collection, f'{self.name}_grip_twohand', self._obj, (0, 0, -0.1))
        self._swing_root = self._obj
        return self._obj

    def set_swing_stroke(self, value):
        self.channel_values['swing_stroke'] = max(0.0, min(1.0, float(value)))
        # A normalized stroke arcs backward then down into the track.
        if self._obj:
            self._obj.rotation_euler.y = math.radians(-70.0 + 140.0 * self.channel_values['swing_stroke'])


class TestDummyProp(PropSpec):
    """Accordion dummy made from body blocks, head, and two arms."""
    channels = {'crush_progress': 0.0}

    def create(self, collection):
        super().create(collection)
        mat = toon_mat('dummy_paint', (0.78, 0.58, 0.25))
        dark = toon_mat('dummy_dark', (0.22, 0.12, 0.08))
        self._body_parts = []
        for i in range(4):
            part = box(f'{self.name}_body_{i}', (0.48, 0.36, 0.38), mat)
            part.location.z = -0.55 + i * 0.38
            _link(collection, part); part.parent = self._obj
            self._body_parts.append(part)
        head = cylinder(f'{self.name}_head', 0.26, 0.30, 16, mat)
        head.rotation_euler.x = math.pi / 2
        head.location.z = 1.0
        _link(collection, head); head.parent = self._obj
        for side in (-1, 1):
            arm = tube_between(f'{self.name}_arm_{side:+d}', (side * 0.25, 0, 0.25),
                               (side * 0.62, 0, -0.05), 0.07, 8, dark)
            _link(collection, arm); arm.parent = self._obj
        self.grip_socket = _socket(collection, f'{self.name}_hand_socket', self._obj, (0.3, 0, 0.25))
        return self._obj

    def set_crush_progress(self, value):
        self.channel_values['crush_progress'] = max(0.0, min(1.0, float(value)))
        if not self._obj:
            return
        # Accordion compression leaves the head and base grounded.
        scale_z = 1.0 - 0.72 * self.channel_values['crush_progress']
        for part in self._body_parts:
            part.scale.z = scale_z
            part.location.z = -0.55 + self._body_parts.index(part) * 0.38 * scale_z


class TurnbuckleCrankProp(PropSpec):
    """Central crank wheel with two threaded rods and grip sockets."""
    channels = {'crank_angle': 0.0}

    def create(self, collection):
        super().create(collection)
        steel = toon_mat('turnbuckle_steel', (0.25, 0.29, 0.36), metallic=0.3)
        red = toon_mat('turnbuckle_handle', (0.68, 0.12, 0.08))
        for side in (-1, 1):
            rod = cylinder(f'{self.name}_rod_{side:+d}', 0.09, 1.25, 10, steel)
            rod.rotation_euler.y = math.pi / 2
            rod.location.x = side * 0.72
            _link(collection, rod); rod.parent = self._obj
        wheel = cylinder(f'{self.name}_wheel', 0.36, 0.18, 16, steel)
        wheel.rotation_euler.x = math.pi / 2
        _link(collection, wheel); wheel.parent = self._obj
        handle = tube_between(f'{self.name}_handle', (-0.48, 0, 0), (0.48, 0, 0), 0.07, 8, red)
        _link(collection, handle); handle.parent = self._obj
        self.grip_main = _socket(collection, f'{self.name}_grip_main', self._obj, (0.48, 0, 0))
        self.grip_twohand = _socket(collection, f'{self.name}_grip_twohand', self._obj, (-0.48, 0, 0))
        self._wheel = wheel
        return self._obj

    def set_crank_angle(self, value):
        self.channel_values['crank_angle'] = max(0.0, min(1.0, float(value)))
        if hasattr(self, '_wheel'):
            self._wheel.rotation_euler.z = math.tau * self.channel_values['crank_angle']


class CoasterCartProp(PropSpec):
    """Concrete cart body, seat, wheels, and deterministic track path."""
    channels = {'track_progress': 0.0}

    def create(self, collection):
        super().create(collection)
        body_mat = toon_mat('cart_body', (0.76, 0.08, 0.10))
        seat_mat = toon_mat('cart_seat', (0.15, 0.08, 0.06))
        wheel_mat = toon_mat('cart_wheels', (0.08, 0.08, 0.09), metallic=0.25)
        body = box(f'{self.name}_body', (1.0, 0.72, 0.42), body_mat)
        body.location.z = 0.52
        _link(collection, body); body.parent = self._obj
        seat = box(f'{self.name}_seat', (0.62, 0.52, 0.16), seat_mat)
        seat.location.z = 0.82
        _link(collection, seat); seat.parent = self._obj
        for x in (-0.34, 0.34):
            wheel = cylinder(f'{self.name}_wheel_{x:+.2f}', 0.13, 0.12, 12, wheel_mat)
            wheel.rotation_euler.x = math.pi / 2
            wheel.location = (x, 0, 0.27)
            _link(collection, wheel); wheel.parent = self._obj
        self.hand_socket = _socket(collection, f'{self.name}_hand_socket', self._obj, (0.35, 0, 0.95))
        self.track_points = [Vector((-8, 0, 0)), Vector((-1, 0, 0)), Vector((0, 6, 4)),
                           Vector((3.5, 4, 0.5)), Vector((4, 0, 0.35)), Vector((4, -4, 0.35)),
                           Vector((12, -6, 0))]
        return self._obj

    def set_track_progress(self, value):
        self.channel_values['track_progress'] = max(0.0, min(1.0, float(value)))
        if not self._obj or not hasattr(self, 'track_points'):
            return
        p = self.channel_values['track_progress'] * (len(self.track_points) - 1)
        i = min(int(p), len(self.track_points) - 2)
        t = p - i
        a, b = self.track_points[i], self.track_points[i + 1]
        self._obj.location = a.lerp(b, t)
        self._obj.rotation_euler = (b - a).to_track_quat('X', 'Z').to_euler()
