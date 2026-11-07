"""Dynamic hero props. Every hero prop is a PropSpec with named channels/sockets."""
from __future__ import annotations

import math
from bisect import bisect_left
from typing import Dict, List, Sequence

import bpy
from mathutils import Vector

from .utils import (
    add_cube, add_cylinder, add_rod, add_torus, add_uv_sphere,
    make_empty, make_mesh_object, set_parent_keep_world,
)
from .look import PALETTE, make_toon_material


class PropSpec:
    """Base contract for an animatable story prop.

    Layer 1 declares geometry/channels. Layer 4 evaluates channel values from
    timeline data and calls apply_channels() deterministically.
    """
    channel_defaults: Dict[str, float] = {}
    channel_limits: Dict[str, tuple] = {}

    def __init__(self, name: str, collection, location=(0, 0, 0)):
        self.name = name
        self.collection = collection
        self.root = make_empty('PROP_' + name, collection, location, 'CUBE', 0.32)
        self.root['prop_spec'] = self.__class__.__name__
        self.channels = dict(self.channel_defaults)
        self.sockets = {}
        for key, value in self.channels.items():
            self.root[key] = float(value)

    def socket(self, name, location, display='SPHERE'):
        obj = make_empty(self.name + '_SOCKET_' + name, self.collection, location, display, 0.12)
        obj.parent = self.root
        obj.location = Vector(location)
        self.sockets[name] = obj
        return obj

    def set_channel(self, name: str, value: float):
        if name not in self.channel_defaults:
            raise KeyError(f'{self.name}: unsupported channel {name!r}')
        value = float(value)
        if name in self.channel_limits:
            lo, hi = self.channel_limits[name]
            value = max(lo, min(hi, value))
        self.channels[name] = value
        self.root[name] = value

    def reset_channels(self):
        for name, value in self.channel_defaults.items():
            self.set_channel(name, value)

    def apply_channels(self):
        """Subclasses evaluate geometry/transform from self.channels."""
        return None

    def socket_world(self, name):
        bpy.context.view_layer.update()
        return self.sockets[name].matrix_world.translation.copy()


class LoopTrackProp(PropSpec):
    """Two-rail loop with morphable lower curvature and side squeeze.

    bend_bottom: 0 = circular loop, 1 = broad clothoid-inspired teardrop bottom.
    squeeze_sides: 0 = full width, 1 = laterally clamped / tall skinny loop.
    """
    channel_defaults = {'bend_bottom': 0.0, 'squeeze_sides': 0.0}
    channel_limits = {'bend_bottom': (0.0, 1.0), 'squeeze_sides': (0.0, 1.0)}

    def __init__(self, name, collection, location=(0, 0, 0), radius=2.25, gauge=1.5):
        super().__init__(name, collection, location)
        self.radius = float(radius)
        self.gauge = float(gauge)
        self.rail_radius = 0.075
        self.wood_mat = make_toon_material('MAT_Track_Wood', [PALETTE['wood_dark'], PALETTE['wood'], PALETTE['wood_light']])
        self.steel_mat = make_toon_material('MAT_Track_Steel', [(0.075, 0.11, 0.16, 1), PALETTE['steel'], PALETTE['steel_light']])
        self.track_mesh = make_mesh_object(
            'TRACK_' + name, [], [], collection, [self.steel_mat, self.wood_mat]
        )
        self.track_mesh.parent = self.root
        self.track_mesh.location = (0, 0, 0)
        self.socket('hammer_target', (0.0, -0.05, 0.22))
        self.socket('clamp_left', (-self.radius, -0.12, self.radius))
        self.socket('clamp_right', (self.radius, -0.12, self.radius))
        self.socket('builder_rail', (-0.3, -self.gauge * 0.5, 0.0))
        self.socket('rival_rail', (0.3, self.gauge * 0.5, 0.0))
        self.apply_channels()

    def centerline_points(self, samples=120):
        bend = self.channels['bend_bottom']
        squeeze = self.channels['squeeze_sides']
        pts = []
        for i in range(samples + 1):
            t = i / samples
            a = -math.pi * 0.5 + (2.0 * math.pi * t)
            sa, ca = math.sin(a), math.cos(a)
            bottom_weight = max(0.0, -sa) ** 4
            top_weight = max(0.0, sa) ** 4
            side_weight = abs(ca) ** 4
            # Broaden the lower arc and gently taper the upper arc: a
            # clothoid-inspired teardrop rather than a uniformly scaled circle.
            x = self.radius * ca * (1.0 + 0.40 * bend * bottom_weight)
            x *= (1.0 - 0.12 * bend * top_weight)
            z = self.radius + self.radius * sa
            z += 0.035 * self.radius * bend * bottom_weight * (abs(ca) ** 2)
            # Pull the left/right walls inward without disturbing top and bottom.
            x *= (1.0 - 0.55 * squeeze * side_weight)
            pts.append(Vector((x, 0.0, z)))
        return pts

    def world_centerline_points(self, samples=120):
        self.root.update_tag()
        return [self.root.matrix_world @ p for p in self.centerline_points(samples)]

    @staticmethod
    def _append_box(vertices, faces, mat_indices, center, dims, material_index=1):
        cx, cy, cz = center
        sx, sy, sz = (d * 0.5 for d in dims)
        start = len(vertices)
        vertices.extend([
            (cx-sx, cy-sy, cz-sz), (cx+sx, cy-sy, cz-sz),
            (cx+sx, cy+sy, cz-sz), (cx-sx, cy+sy, cz-sz),
            (cx-sx, cy-sy, cz+sz), (cx+sx, cy-sy, cz+sz),
            (cx+sx, cy+sy, cz+sz), (cx-sx, cy+sy, cz+sz),
        ])
        local_faces = [
            (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
            (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        ]
        for face in local_faces:
            faces.append(tuple(start + i for i in face))
            mat_indices.append(material_index)

    def _track_rail_points(self):
        # Approach, loop, and exit share one continuous two-rail centerline.
        loop_pts = self.centerline_points()
        return (
            [Vector((-self.radius - 2.0, 0, 0)),
             Vector((-self.radius - 1.30, 0, 0)),
             Vector((-self.radius * 0.45, 0, 0))]
            + loop_pts
            + [Vector((1.25, 0, 0)), Vector((2.50, 0, 0)), Vector((3.80, 0, 0))]
        )

    def _build_track_mesh(self):
        pts = self._track_rail_points()
        vertices, faces, mats = [], [], []
        tube_sides = 8
        for side in (-1.0, 1.0):
            base = len(vertices)
            for i, p in enumerate(pts):
                prev_p = pts[max(0, i - 1)]
                next_p = pts[min(len(pts) - 1, i + 1)]
                tangent = Vector((next_p.x - prev_p.x, 0, next_p.z - prev_p.z))
                if tangent.length < 1e-6:
                    tangent = Vector((1, 0, 0))
                tangent.normalize()
                normal = Vector((-tangent.z, 0, tangent.x))
                center = p + Vector((0, side * self.gauge * 0.5, 0))
                for j in range(tube_sides):
                    ang = 2 * math.pi * j / tube_sides
                    v = center + self.rail_radius * (normal * math.cos(ang) + Vector((0, 1, 0)) * math.sin(ang))
                    vertices.append(tuple(v))
            ring_count = len(pts)
            for i in range(ring_count - 1):
                for j in range(tube_sides):
                    a = base + i * tube_sides + j
                    b = base + i * tube_sides + (j + 1) % tube_sides
                    c = base + (i + 1) * tube_sides + (j + 1) % tube_sides
                    d = base + (i + 1) * tube_sides + j
                    faces.append((a, b, c, d))
                    mats.append(0)
        # Wooden cross-ties every third sample, bridging the two rails.
        for i in range(0, len(pts), 3):
            p = pts[i]
            self._append_box(vertices, faces, mats, p, (0.13, self.gauge + 0.18, 0.10), 1)
        mesh = self.track_mesh.data
        mesh.clear_geometry()
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        if len(mesh.materials) == 0:
            mesh.materials.append(self.steel_mat)
            mesh.materials.append(self.wood_mat)
        for poly, idx in zip(mesh.polygons, mats):
            poly.material_index = idx

    def apply_channels(self):
        self._build_track_mesh()
        # The work sockets sit just outside the lower rail and follow squeeze.
        squeeze = self.channels['squeeze_sides']
        x = self.radius * (1.0 - 0.55 * squeeze)
        self.sockets['clamp_left'].location = (-x, -0.12, self.radius)
        self.sockets['clamp_right'].location = (x, -0.12, self.radius)
        self.sockets['hammer_target'].location = (0.0, -0.05, 0.18 + self.channels['bend_bottom'] * 0.12)


class SledgehammerProp(PropSpec):
    channel_defaults = {'swing_stroke': 0.0}
    channel_limits = {'swing_stroke': (0.0, 1.0)}

    def __init__(self, name, collection, location=(-3.8, 0.25, 1.5)):
        super().__init__(name, collection, location)
        wood = make_toon_material('MAT_Hammer_Handle', [PALETTE['wood_dark'], PALETTE['wood'], PALETTE['wood_light']])
        iron = make_toon_material('MAT_Hammer_Head', [(0.08, 0.10, 0.13, 1), PALETTE['steel'], PALETTE['steel_light']])
        handle = add_cylinder('Hammer_Handle', collection, (0, 0, 0), 0.075, 1.25, wood, 12)
        handle.location = (0, 0, -0.58)
        handle.parent = self.root
        handle.location = (0, 0, -0.58)
        head = add_cube('Hammer_Head', collection, (0, 0, 0), (0.72, 0.28, 0.30), iron, 0.045)
        head.parent = self.root
        head.location = (0, 0, -1.23)
        self.socket('grip_main', (0.0, -0.01, 0.0))
        self.socket('grip_twohand', (0.0, -0.01, -0.32))
        self.socket('impact_end', (0.0, -0.02, -1.23))
        self.apply_channels()

    def apply_channels(self):
        # A full downswing carries the head through the lower contact point.
        self.root.rotation_euler[1] = 0.25 - 0.80 * self.channels['swing_stroke']


class TestDummyProp(PropSpec):
    """Accordion-compressible crash dummy with accessible grip/seat sockets."""
    channel_defaults = {'crush_progress': 0.0}
    channel_limits = {'crush_progress': (0.0, 1.0)}

    def __init__(self, name, collection, location=(-3.2, -0.45, 0.15)):
        super().__init__(name, collection, location)
        silver = make_toon_material('MAT_Dummy_Silver', [(0.12, 0.15, 0.18, 1), (0.48, 0.54, 0.58, 1), (0.82, 0.87, 0.88, 1)])
        dark = make_toon_material('MAT_Dummy_Dark', [(0.03, 0.04, 0.05, 1), (0.12, 0.14, 0.16, 1), (0.26, 0.29, 0.31, 1)])
        self.rings = []
        self.base_z = 0.18
        self.stack_height = 1.45
        for i in range(7):
            z = self.base_z + 0.17 + i * 0.18
            tor = add_torus(f'Dummy_Accordion_Ring_{i:02d}', collection, (0, 0, 0), 0.29, 0.055, silver)
            tor.parent = self.root
            tor.location = (0, 0, z)
            tor.scale = (1.0, 0.78, 1.0)
            self.rings.append(tor)
        base = add_cylinder('Dummy_Base', collection, (0, 0, 0), 0.32, 0.18, dark, 20)
        base.parent = self.root
        base.location = (0, 0, self.base_z)
        self.head = add_uv_sphere('Dummy_Head', collection, (0, 0, 0), (0.31, 0.25, 0.31), silver)
        self.head.parent = self.root
        self.head.location = (0, 0, self.base_z + self.stack_height + 0.25)
        self.top_cap = add_cylinder('Dummy_Top_Cap', collection, (0, 0, 0), 0.28, 0.10, silver, 20)
        self.top_cap.parent = self.root
        self.top_cap.location = (0, 0, self.base_z + self.stack_height)
        self.socket('grip_left', (-0.32, 0, 0.95))
        self.socket('grip_right', (0.32, 0, 0.95))
        self.socket('seat_mount', (0, 0, self.base_z))
        self.socket('head_socket', (0, 0, self.base_z + self.stack_height + 0.25))
        self.apply_channels()

    def apply_channels(self):
        p = self.channels['crush_progress']
        compression = 1.0 - 0.78 * p
        for i, ring in enumerate(self.rings):
            ring.location.z = self.base_z + 0.17 + i * 0.18 * compression
            ring.scale.z = 1.0 - 0.08 * p
        self.top_cap.location.z = self.base_z + self.stack_height * compression
        self.head.location.z = self.base_z + self.stack_height * compression + 0.25 * compression
        self.head.scale = (0.31, 0.25, 0.31 * (1.0 - 0.35 * p))
        self.sockets['head_socket'].location.z = self.head.location.z


class TurnbuckleCrankProp(PropSpec):
    """Dual clamp crank. crank_angle is normalized turns (0..1), not radians."""
    channel_defaults = {'crank_angle': 0.0}
    channel_limits = {'crank_angle': (0.0, 1.0)}

    def __init__(self, name, collection, location=(3.2, 0.55, 2.55)):
        super().__init__(name, collection, location)
        metal = make_toon_material('MAT_Turnbuckle_Metal', [(0.07, 0.09, 0.12, 1), PALETTE['steel'], PALETTE['steel_light']])
        brass = make_toon_material('MAT_Turnbuckle_Brass', [(0.22, 0.10, 0.02, 1), (0.65, 0.35, 0.06, 1), (1.0, 0.72, 0.24, 1)])
        self.rod = add_cylinder('Turnbuckle_Threaded_Rod', collection, (0, 0, 0), 0.055, 4.20, metal, 16, rotation=(0, math.pi / 2, 0))
        self.rod.parent = self.root
        self.rod.location = (0, 0, 0)
        self.wheel = add_torus('Turnbuckle_Handwheel', collection, (0, 0, 0), 0.36, 0.065, brass, rotation=(math.pi/2, 0, 0))
        self.wheel.parent = self.root
        self.wheel.location = (0, -0.02, 0)
        self.handles = []
        for i in range(4):
            a = i * math.pi / 2
            end = (0.36 * math.cos(a), -0.02, 0.36 * math.sin(a))
            h = add_rod('Turnbuckle_Handle_%d' % i, collection, (0, -0.02, 0), end, 0.035, brass)
            h.parent = self.wheel
            # The handle rotates with the handwheel; geometry is local to its center.
            h.location = (end[0] * 0.5, 0.0, end[2] * 0.5)
            self.handles.append(h)
        self.left_jaw = add_cube('Turnbuckle_Left_Jaw', collection, (0, 0, 0), (0.18, 0.24, 0.34), brass, 0.035)
        self.right_jaw = add_cube('Turnbuckle_Right_Jaw', collection, (0, 0, 0), (0.18, 0.24, 0.34), brass, 0.035)
        self.left_jaw.parent = self.root
        self.right_jaw.parent = self.root
        self.socket('grip_crank', (0.36, -0.12, 0.0))
        self.socket('grip_brace', (-0.36, -0.12, 0.0))
        self.socket('jaw_left', (-2.10, 0, 0))
        self.socket('jaw_right', (2.10, 0, 0))
        self.apply_channels()

    def apply_channels(self):
        angle = self.channels['crank_angle'] * (math.pi * 6.0)
        self.wheel.rotation_euler[1] = angle
        inward = 1.10 * self.channels['crank_angle']
        self.left_jaw.location = (-2.10 + inward, 0, 0)
        self.right_jaw.location = (2.10 - inward, 0, 0)
        self.sockets['jaw_left'].location.x = -2.10 + inward
        self.sockets['jaw_right'].location.x = 2.10 - inward
        self.sockets['grip_crank'].location = (0.36 * math.cos(angle), -0.12, 0.36 * math.sin(angle))


class CoasterCartProp(PropSpec):
    """Cart with normalized track_progress along an arc-length sampled Bezier route."""
    channel_defaults = {'track_progress': 0.0}
    channel_limits = {'track_progress': (0.0, 1.0)}

    def __init__(self, name, collection, location=(0, 0, 0)):
        super().__init__(name, collection, location)
        red = make_toon_material('MAT_Cart_Red', [(0.22, 0.018, 0.025, 1), PALETTE['red'], (1.0, 0.25, 0.18, 1)])
        dark = make_toon_material('MAT_Cart_Dark', [(0.02, 0.025, 0.035, 1), (0.10, 0.13, 0.16, 1), (0.28, 0.32, 0.35, 1)])
        gold = make_toon_material('MAT_Cart_Gold', [(0.28, 0.12, 0.015, 1), PALETTE['gold'], (1.0, 0.82, 0.34, 1)])
        chassis = add_cube('Cart_Chassis', collection, (0, 0, 0), (1.25, 0.72, 0.20), dark, 0.08)
        chassis.parent = self.root
        chassis.location = (0, 0, 0)
        tub = add_cube('Cart_Seat_Tub', collection, (0, 0, 0), (0.95, 0.66, 0.60), red, 0.12)
        tub.parent = self.root
        tub.location = (0, 0, 0.38)
        back = add_cube('Cart_Seat_Back', collection, (0, 0, 0), (0.18, 0.58, 0.82), red, 0.09)
        back.parent = self.root
        back.location = (-0.42, 0, 0.56)
        self.wheels = []
        for x in (-0.43, 0.43):
            for y in (-0.72, 0.72):
                wheel = add_cylinder('Cart_Wheel', collection, (0, 0, 0), 0.22, 0.14, dark, 20, rotation=(math.pi/2, 0, 0))
                wheel.parent = self.root
                wheel.location = (x, y, -0.10)
                self.wheels.append(wheel)
                hub = add_cylinder('Cart_Wheel_Hub', collection, (0, 0, 0), 0.075, 0.16, gold, 16, rotation=(math.pi/2, 0, 0))
                hub.parent = self.root
                hub.location = (x, y, -0.10)
        self.handle = add_rod('Cart_Safety_Bar', collection, (-0.2, 0, 0.85), (0.48, 0, 0.85), 0.055, gold)
        self.handle.parent = self.root
        self.handle.location = (0.1, 0, 0.85)
        self.sockets = {}
        self.socket('seat_builder', (-0.02, -0.02, 0.73))
        self.socket('seat_rival', (-0.02, 0.02, 0.73))
        self.socket('grip_left', (0.22, -0.32, 0.87))
        self.socket('grip_right', (0.22, 0.32, 0.87))
        self.bezier_segments = []
        self._arc_lut = []
        self._arc_distances = []

    @staticmethod
    def segments_from_points(points: Sequence[Vector]):
        """Approximate a smooth cubic Bezier chain through a sequence of points."""
        pts = [Vector(p) for p in points]
        segments = []
        if len(pts) < 2:
            return segments
        for i in range(len(pts) - 1):
            p0, p3 = pts[i], pts[i + 1]
            prev_p = pts[i - 1] if i > 0 else (p0 - (p3 - p0))
            next_p = pts[i + 2] if i + 2 < len(pts) else (p3 + (p3 - p0))
            p1 = p0 + (p3 - prev_p) / 6.0
            p2 = p3 - (next_p - p0) / 6.0
            segments.append((p0, p1, p2, p3))
        return segments

    def set_bezier_segments(self, segments):
        self.bezier_segments = [tuple(Vector(p) for p in seg) for seg in segments]
        self._build_arc_lut()
        self.apply_channels()

    def set_route_from_loop(self, loop: LoopTrackProp, approach=4.8, exit_length=3.8):
        center = loop.root.matrix_world.translation.copy()
        r = loop.radius
        pts = [
            center + Vector((-r - approach, 0, 0)),
            center + Vector((-r - approach * 0.67, 0, 0)),
            center + Vector((-r - approach * 0.33, 0, 0)),
            center.copy(),
        ]
        # Start at the bottom of the loop and complete the full dynamic outline.
        pts.extend(loop.world_centerline_points(samples=72)[1:])
        pts.extend([
            center + Vector((exit_length * 0.33, 0, 0)),
            center + Vector((exit_length * 0.67, 0, 0)),
            center + Vector((exit_length, 0, 0)),
        ])
        self.set_bezier_segments(self.segments_from_points(pts))

    @staticmethod
    def _bezier(seg, t):
        p0, p1, p2, p3 = seg
        u = 1.0 - t
        return (u**3)*p0 + (3*u*u*t)*p1 + (3*u*t*t)*p2 + (t**3)*p3

    def _build_arc_lut(self):
        self._arc_lut = []
        self._arc_distances = []
        total = 0.0
        previous = None
        for si, seg in enumerate(self.bezier_segments):
            for j in range(25):
                if si > 0 and j == 0:
                    continue
                t = j / 24.0
                p = self._bezier(seg, t)
                if previous is not None:
                    total += (p - previous).length
                self._arc_lut.append((total, p, si, t))
                self._arc_distances.append(total)
                previous = p

    def position_and_tangent(self, progress):
        if not self._arc_lut:
            return self.root.location.copy(), Vector((1, 0, 0))
        target = max(0.0, min(1.0, progress)) * self._arc_distances[-1]
        idx = bisect_left(self._arc_distances, target)
        idx = max(1, min(len(self._arc_lut) - 1, idx))
        d0, p0, _, _ = self._arc_lut[idx - 1]
        d1, p1, _, _ = self._arc_lut[idx]
        fac = 0.0 if d1 - d0 < 1e-8 else (target - d0) / (d1 - d0)
        pos = p0.lerp(p1, fac)
        tangent = (p1 - p0).normalized() if (p1 - p0).length > 1e-8 else Vector((1, 0, 0))
        return pos, tangent

    def apply_channels(self):
        pos, tangent = self.position_and_tangent(self.channels['track_progress'])
        self.root.location = pos
        self.root.rotation_euler[1] = -math.atan2(tangent.z, tangent.x)
