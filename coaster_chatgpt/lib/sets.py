"""Three modular environments and a central anchor registry."""
from __future__ import annotations

import math
import bpy

from .utils import ensure_collection, add_cube, add_cylinder, add_rod, add_uv_sphere
from .look import PALETTE, make_toon_material

ANCHOR_REGISTRY = {}
SET_COLLECTIONS = {}


def _materials():
    return {
        'wood': make_toon_material('MAT_Set_Wood', [PALETTE['wood_dark'], PALETTE['wood'], PALETTE['wood_light']]),
        'wood_dark': make_toon_material('MAT_Set_Wood_Dark', [(0.055, 0.028, 0.022, 1), PALETTE['wood_dark'], (0.30, 0.12, 0.055, 1)]),
        'cream': make_toon_material('MAT_Set_Cream', [(0.40, 0.26, 0.13, 1), PALETTE['cream'], PALETTE['white']]),
        'red': make_toon_material('MAT_Set_Red', [(0.20, 0.02, 0.03, 1), PALETTE['red'], (1.0, 0.32, 0.25, 1)]),
        'blue': make_toon_material('MAT_Set_Blue', [(0.015, 0.04, 0.17, 1), PALETTE['blue'], (0.38, 0.64, 1.0, 1)]),
        'green': make_toon_material('MAT_Set_Green', [(0.025, 0.14, 0.08, 1), PALETTE['green'], (0.42, 0.70, 0.34, 1)]),
        'gold': make_toon_material('MAT_Set_Gold', [(0.24, 0.11, 0.02, 1), PALETTE['gold'], (1.0, 0.82, 0.40, 1)]),
        'dark': make_toon_material('MAT_Set_Dark', [(0.012, 0.018, 0.032, 1), (0.08, 0.10, 0.14, 1), (0.23, 0.27, 0.31, 1)]),
        'grass': make_toon_material('MAT_Set_Grass', [(0.035, 0.12, 0.07, 1), (0.16, 0.35, 0.13, 1), (0.48, 0.62, 0.22, 1)]),
    }


def build_workshop_night():
    col = ensure_collection('SET_workshop_night')
    m = _materials()
    # Warm, readable workshop floor and back wall; never a black void.
    add_cube('Workshop_Floor', col, (0, 0.8, -0.28), (23, 13, 0.55), m['wood_dark'], 0.08)
    add_cube('Workshop_Back_Wall', col, (0, 4.4, 3.4), (23, 0.35, 7.0), m['dark'], 0.08)
    add_cube('Workshop_Left_Wall', col, (-11.2, 0.8, 3.4), (0.35, 8.0, 7.0), m['wood_dark'], 0.05)
    # Timber roof trusses.
    for x in (-8.5, -4.3, 0.0, 4.3, 8.5):
        add_rod('Workshop_Roof_Beam', col, (x, -2.5, 6.4), (x, 4.2, 6.4), 0.12, m['wood'])
    add_rod('Workshop_Roof_Ridge', col, (-10.5, 0.8, 6.7), (10.5, 0.8, 6.7), 0.16, m['wood_dark'])
    # Main bench and vice.
    add_cube('Blacksmith_Workbench_Top', col, (-5.2, -0.1, 1.05), (4.2, 1.65, 0.28), m['wood'], 0.09)
    for x in (-6.9, -3.5):
        for y in (-0.65, 0.45):
            add_cube('Workbench_Leg', col, (x, y, 0.45), (0.25, 0.25, 1.0), m['wood_dark'], 0.035)
    add_cube('Workbench_Vice_Base', col, (-4.0, -0.2, 1.30), (0.75, 0.48, 0.24), m['dark'], 0.04)
    add_cube('Workbench_Vice_Jaw', col, (-4.0, -0.2, 1.49), (0.14, 0.50, 0.24), m['steel'] if 'steel' in m else m['dark'], 0.02)
    # Pegboard/tool silhouettes.
    add_cube('Workshop_Toolboard', col, (-7.8, 3.95, 3.4), (4.0, 0.18, 2.5), m['wood'], 0.06)
    for i in range(5):
        x = -9.2 + i * 0.65
        add_rod('Tool_Hanger', col, (x, 3.78, 3.8), (x, 3.78, 4.45), 0.045, m['gold'])
        add_rod('Hanging_Tool_Handle', col, (x, 3.74, 3.05), (x, 3.74, 3.75), 0.035, m['wood_dark'])
    add_cube('Workshop_Sign', col, (0.0, 4.12, 5.2), (4.2, 0.16, 0.82), m['wood_dark'], 0.08)
    # Decorative bolts and shelves.
    for x in (-1.6, 1.6):
        add_uv_sphere('Sign_Bolt', col, (x, 4.0, 5.2), (0.075, 0.04, 0.075), m['gold'], 12, 8)
    add_cube('Workshop_Shelf', col, (7.4, 2.8, 1.6), (3.1, 0.8, 0.16), m['wood'], 0.04)
    for x in (6.3, 7.1, 7.9, 8.7):
        add_cylinder('Paint_Can', col, (x, 2.8, 1.98), 0.22, 0.55, m['red'] if x < 7.4 else m['blue'], 16)
    anchors = {
        'builder_mark': (-3.90, -0.30, 0.0),
        'rival_mark': (3.80, -0.10, 0.0),
        'workbench': (-5.2, -0.1, 1.2),
        'hero_loop': (-3.2, 0.35, 0.30),
        'rival_loop': (3.2, 0.85, 0.30),
        'dummy_mark': (-3.2, -0.95, 0.16),
        'crank_mark': (3.2, 0.55, 2.55),
    }
    ANCHOR_REGISTRY['workshop_night'] = anchors
    SET_COLLECTIONS['workshop_night'] = col
    return col


def build_fairground_dawn():
    col = ensure_collection('SET_fairground_dawn')
    m = _materials()
    add_cube('Fairground_Ground', col, (0, 0.8, -0.36), (28, 18, 0.62), m['grass'], 0.12)
    # Ticket booth at rear center.
    add_cube('Ticket_Booth_Body', col, (0, 4.6, 1.2), (3.6, 1.3, 2.4), m['cream'], 0.08)
    add_cube('Ticket_Booth_Window', col, (0, 3.91, 1.55), (1.8, 0.08, 0.88), m['blue'], 0.035)
    add_cube('Ticket_Booth_Counter', col, (0, 3.75, 1.03), (2.3, 0.35, 0.16), m['wood_dark'], 0.03)
    # Striped circus tents.
    for tx, base_mat in [(-8.5, m['red']), (8.5, m['blue'])]:
        add_cylinder('Tent_Base', col, (tx, 3.2, 1.0), 2.0, 2.0, m['cream'], 24)
        # Simple conical roof generated from a cone primitive.
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=2.2, radius2=0.10, depth=2.0, location=(tx, 3.2, 3.0))
        roof = bpy.context.object
        roof.name = 'Fairground_Tent_Roof'
        for owner in list(roof.users_collection):
            owner.objects.unlink(roof)
        col.objects.link(roof)
        roof.data.materials.append(base_mat)
        for xoff in (-0.9, 0.0, 0.9):
            add_rod('Tent_Support', col, (tx+xoff, 2.35, 0.1), (tx+xoff, 2.35, 2.4), 0.055, m['wood'])
    # Bunting between tall poles.
    for x in range(-10, 11, 2):
        add_rod('Bunting_Pole', col, (x, -1.8, 0.0), (x, -1.8, 3.5), 0.045, m['wood_dark'])
    for i in range(10):
        x0 = -9.0 + i * 2.0
        add_rod('Bunting_Cord', col, (x0, -1.8, 3.25), (x0+2.0, -1.8, 3.25), 0.018, m['cream'])
        add_cube('Bunting_Flag', col, (x0+1.0, -1.82, 3.05), (0.62, 0.06, 0.38), m['red'] if i % 2 == 0 else m['gold'], 0.015)
    # Queue rails and warm pennants.
    for y in (-3.1, -4.15):
        for x in range(-8, 9, 2):
            add_cylinder('Queue_Post', col, (x, y, 0.55), 0.075, 1.1, m['wood_dark'], 12)
        for x in range(-7, 8, 2):
            add_rod('Queue_Rope', col, (x, y, 0.78), (x+2, y, 0.78), 0.035, m['red'])
    anchors = {
        'builder_mark': (-3.90, -0.30, 0.0),
        'rival_mark': (3.80, -0.10, 0.0),
        'hero_loop': (-3.2, 0.35, 0.30),
        'rival_loop': (3.2, 0.85, 0.30),
        'dummy_mark': (-3.2, -0.95, 0.16),
        'crank_mark': (3.2, 0.55, 2.55),
        'ticket_booth': (0, 3.5, 0),
    }
    ANCHOR_REGISTRY['fairground_dawn'] = anchors
    SET_COLLECTIONS['fairground_dawn'] = col
    return col


def build_coaster_climax():
    col = ensure_collection('SET_coaster_climax')
    m = _materials()
    add_cube('Climax_Ground', col, (0, 1.0, -0.40), (30, 20, 0.65), m['grass'], 0.10)
    # Wooden support bents around both loop lanes.
    for loop_x, loop_y in [(-3.2, 0.35), (3.2, 0.85)]:
        for side in (-1, 1):
            x = loop_x + side * 2.55
            add_rod('Loop_Support_Pole', col, (x, loop_y, 0.0), (x, loop_y, 4.45), 0.14, m['wood_dark'])
            add_rod('Loop_Support_Brace', col, (x, loop_y, 1.2), (loop_x, loop_y, 2.0), 0.075, m['wood'])
            add_rod('Loop_Support_Brace', col, (x, loop_y, 3.3), (loop_x, loop_y, 4.0), 0.075, m['wood'])
        add_rod('Loop_Top_Crossbar', col, (loop_x-2.5, loop_y, 4.45), (loop_x+2.5, loop_y, 4.45), 0.13, m['wood_dark'])
    # Distant spectator grandstand, graphic crowd dots.
    add_cube('Grandstand_Base', col, (0, 6.3, 1.0), (18, 1.1, 2.0), m['wood_dark'], 0.10)
    for row in range(3):
        z = 1.2 + row * 0.42
        y = 5.72 + row * 0.13
        for i in range(21):
            x = -8.0 + i * 0.8
            color = m['red'] if (i + row) % 4 == 0 else (m['blue'] if (i + row) % 3 == 0 else m['cream'])
            add_uv_sphere('Crowd_Dot', col, (x, y, z), (0.14, 0.10, 0.17), color, 10, 6)
    # Festoon lights along the ride boundary.
    for x in (-9, -6, -3, 0, 3, 6, 9):
        add_cylinder('Fairground_Lamp_Post', col, (x, -5.2, 2.3), 0.07, 4.6, m['wood_dark'], 12)
        add_uv_sphere('Fairground_Lamp_Bulb', col, (x, -5.2, 4.65), (0.18, 0.18, 0.18), m['gold'], 12, 8)
    anchors = {
        'builder_mark': (-3.90, -0.30, 0.0),
        'rival_mark': (3.80, -0.10, 0.0),
        'hero_loop': (-3.2, 0.35, 0.30),
        'rival_loop': (3.2, 0.85, 0.30),
        'dummy_mark': (-3.2, -0.95, 0.16),
        'crank_mark': (3.2, 0.55, 2.55),
    }
    ANCHOR_REGISTRY['coaster_climax'] = anchors
    SET_COLLECTIONS['coaster_climax'] = col
    return col


def build_all_sets():
    """Construct all modular sets and return their collections/anchors."""
    build_workshop_night()
    build_fairground_dawn()
    build_coaster_climax()
    return SET_COLLECTIONS


def get_anchor(set_name, anchor_name):
    return ANCHOR_REGISTRY[set_name][anchor_name]


def set_active_set(name):
    for set_name, collection in SET_COLLECTIONS.items():
        active = set_name == name
        collection.hide_render = not active
        collection.hide_viewport = not active
