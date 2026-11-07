"""Concrete modular 3D sets for the roller-coaster short.

Each set owns real floors, platforms, workshop/fairground dressing, and named
anchor empties. Geometry is created directly, so background rendering works.
"""
import math
import bpy
from mathutils import Vector

from .look import anchor_empty, toon_mat
from .meshlib import box, cylinder, tube_between, curve_tube


class SetBuilder:
    def __init__(self, name: str):
        self.name = name
        self._col = None
        self.anchors = {}

    def collection(self):
        if self._col is None:
            self._col = bpy.data.collections.get(self.name) or bpy.data.collections.new(self.name)
            if self._col.name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(self._col)
        return self._col

    def anchor(self, name, location=(0, 0, 0), parent=None):
        existing = self.anchors.get(name)
        if existing:
            existing.location = location
            return existing
        e = anchor_empty(self.collection(), name, location, parent)
        self.anchors[name] = e
        return e

    def add(self, obj, location=None, parent=None):
        col = self.collection()
        if obj.name not in col.objects:
            col.objects.link(obj)
        if location is not None:
            obj.location = location
        if parent is not None:
            obj.parent = parent
        return obj

    def get_anchor(self, name):
        return self.anchors.get(name)


class WorkshopNightSet(SetBuilder):
    """Night workshop: workbench, timber wall, practicals, tools, and track jig."""
    def build(self):
        col = self.collection()
        floor = toon_mat('workshop_floor', (0.10, 0.08, 0.12))
        timber = toon_mat('workshop_timber', (0.25, 0.12, 0.08))
        metal = toon_mat('workshop_metal', (0.28, 0.31, 0.38), metallic=0.3)
        brass = toon_mat('workshop_brass', (0.66, 0.35, 0.10), metallic=0.45)
        # Floor and back wall
        self.add(box('workshop_floor', (14, 12, 0.18), floor), location=(0, 0, -0.09))
        self.add(box('workshop_back_wall', (14, 0.22, 7), timber), location=(0, 4.5, 3.4))
        # Workbench top, legs, shelf
        self.add(box('workbench_top', (6.2, 1.4, 0.28), timber), location=(0, 0.2, 1.05))
        for x in (-2.7, 2.7):
            for y in (-0.25, 0.65):
                self.add(box(f'workbench_leg_{x}_{y}', (0.24, 0.24, 2.1), metal), location=(x, y, 0.0))
        self.add(box('workbench_shelf', (5.6, 1.1, 0.16), timber), location=(0, 0.2, 0.22))
        # Track assembly jig: support posts and clamp bed
        for x in (-2.4, 2.4):
            self.add(cylinder(f'jig_post_{x}', 0.14, 2.2, 12, metal), location=(x, 0.2, 1.95))
        self.add(box('jig_bed', (5.4, 0.5, 0.18), metal), location=(0, 0.2, 1.4))
        # Wall slats / brass bolts give scale and silhouette.
        for i in range(-5, 6):
            self.add(box(f'wall_slats_{i}', (0.08, 0.05, 6.8), timber), location=(i * 0.9, 4.34, 3.4))
        for x in (-2.0, 0, 2.0):
            self.add(cylinder(f'wall_bolt_{x}', 0.09, 0.12, 12, brass), location=(x, 4.15, 3.4))
        # Anchors
        self.anchor('workbench', (0, 0.2, 1.2))
        self.anchor('track_mount', (0.5, 0.2, 1.7), self.anchors['workbench'])
        self.anchor('hammer_rack', (-1.2, 0.8, 2.0), self.anchors['workbench'])
        self.anchor('dummy_stand', (1.5, 0.5, 1.1), self.anchors['workbench'])
        self.anchor('builder_pos', (-0.8, -1.5, 0.0))
        self.anchor('rival_pos', (2.0, -1.2, 0.0))
        self.anchor('window', (3.0, 3.8, 2.5))
        return col


class FairgroundDawnSet(SetBuilder):
    """Morning fairground: real track, lift supports, queue rails, and flags."""
    def build(self):
        col = self.collection()
        grass = toon_mat('fairground_grass', (0.24, 0.48, 0.24))
        wood = toon_mat('fairground_wood', (0.42, 0.20, 0.10))
        steel = toon_mat('fairground_steel', (0.55, 0.58, 0.66), metallic=0.25)
        gold = toon_mat('fairground_gold', (0.95, 0.55, 0.08), metallic=0.2)
        self.add(box('fairground_ground', (36, 28, 0.18), grass), location=(2, 0, -0.1))
        # Lift hill and track approach
        lift = [(-8, 0, 0.25), (-3, 0, 0.25), (0, 2, 1.7), (0, 6, 4.0), (4, 4, 0.35)]
        self.add(curve_tube('fairground_lift_rail_a', [(x, -0.18, z) for x, y, z in lift], 0.08, 8, steel), location=(0, 0, 0))
        self.add(curve_tube('fairground_lift_rail_b', [(x, 0.18, z) for x, y, z in lift], 0.08, 8, steel), location=(0, 0, 0))
        for i, (x, y, z) in enumerate(lift[::1]):
            self.add(tube_between(f'lift_tie_{i}', (x, -0.35, z), (x, 0.35, z), 0.045, 6, wood), location=(0, y, 0))
        # Tall support towers
        for x, y, z in [(-5, 0, 1.3), (-2.5, 2.5, 2.0), (0, 6, 2.0), (4, 4, 2.0), (4, -4, 2.0)]:
            self.add(cylinder(f'fair_support_{x}_{y}', 0.12, max(1.2, z * 2), 10, steel), location=(x, y, z / 2))
        # Queue rails
        for x in (4.0, 5.4, 6.8):
            self.add(tube_between(f'queue_post_{x}', (x, 4, 0), (x, 7, 0), 0.05, 8, wood))
            self.add(tube_between(f'queue_rail_{x}', (x, 4, 0.95), (x, 7, 0.95), 0.05, 8, gold))
        # Flags on the skyline
        for i, x in enumerate((-6, 0, 6, 12)):
            self.add(cylinder(f'flag_pole_{i}', 0.035, 4.0, 8, wood), location=(x, 5, 2.0))
            flag = box(f'flag_{i}', (0.8, 0.04, 0.45), gold if i % 2 else steel)
            self.add(flag, location=(x + 0.4, 5, 3.5))
        anchors = {
            'track_start': (-8, 0, 0), 'lift_hill_top': (0, 6, 4),
            'loop_entrance': (4, 4, 0), 'loop_apex': (4, 0, 5.5),
            'loop_exit': (4, -4, 0), 'finish_brake': (12, -6, 0),
            'cam_establish': (-15, -10, 6), 'cam_lift_hill': (-6, 2, 5),
            'cam_loop_side': (8, 1, 3), 'cam_loop_top': (4, -6, 7),
            'cam_finish': (16, -2, 4), 'rival_queue': (5, 5, 0),
            'owner_queue': (5, 4, 0),
        }
        for name, pos in anchors.items(): self.anchor(name, pos)
        return col


class CoasterClimaxSet(SetBuilder):
    """Climax set: two concrete loop tracks and the cross-cut camera anchors."""
    def build(self):
        col = self.collection()
        steel = toon_mat('climax_steel', (0.52, 0.56, 0.65), metallic=0.3)
        dark = toon_mat('climax_dark', (0.18, 0.22, 0.30))
        # Ground and two loop support frames
        self.add(box('climax_ground', (28, 22, 0.18), dark), location=(0, 0, -0.1))
        for cx in (4, -4):
            for x in (cx - 1.2, cx + 1.2):
                self.add(cylinder(f'loop_support_{cx}_{x}', 0.14, 5.5, 10, steel), location=(x, 0.25, 2.75))
            for theta in range(0, 360, 20):
                a = math.radians(theta); b = math.radians(theta + 20)
                r = 2.45
                p0 = (cx + r * math.cos(a), 0, 2.75 + r * math.sin(a))
                p1 = (cx + r * math.cos(b), 0, 2.75 + r * math.sin(b))
                self.add(tube_between(f'loop_{cx}_{theta}', p0, p1, 0.085, 8, steel))
        # Add explicit loop anchors
        anchors = {
            'loop_center': (4, 0, 2.75), 'loop_bottom': (4, 0, 0), 'loop_top': (4, 0, 5.5),
            'loop_left': (1.55, 0, 2.75), 'loop_right': (6.45, 0, 2.75),
            'cart_start': (-8, 0, 0), 'cart_lift_top': (0, 6, 4),
            'cart_pre_loop': (3.5, 4, 0.5), 'cart_loop_bottom': (4, 2, 0.3),
            'cart_loop_apex': (4, 0, 5.5), 'cart_loop_exit': (4, -3, 1),
            'cart_finish': (12, -6, 0), 'rival_loop_center': (-4, 0, 2.75),
            'rival_cart_bottom': (-4, 2, 0.3), 'cam_owner_pov': (4, -1, 2),
            'cam_rival_pov': (-4, -1, 2), 'cam_loop_inside': (4, 0, 2.75),
            'cam_wide_cross': (0, -12, 8),
        }
        for name, pos in anchors.items(): self.anchor(name, pos)
        return col


SETS = {
    'workshop_night': WorkshopNightSet('workshop_night'),
    'fairground_dawn': FairgroundDawnSet('fairground_dawn'),
    'coaster_climax': CoasterClimaxSet('coaster_climax'),
}


def build_all():
    """Build all concrete sets and return their collections."""
    return {name: builder.build() for name, builder in SETS.items()}
