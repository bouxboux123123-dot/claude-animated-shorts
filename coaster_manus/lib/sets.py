"""Three modular sets and named staging anchors for the animated short."""
from __future__ import annotations

import math
import bpy
from .look import toon_material, add_outline, set_mood

MATERIALS = {}
ANCHORS = {}


def mat(name, color):
    if name not in MATERIALS:
        MATERIALS[name] = toon_material(name, color)
    return MATERIALS[name]


def box(name, loc, dims, material, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    if bevel:
        b = obj.modifiers.new("Painted soft edges", "BEVEL")
        b.width = bevel
        b.segments = 2
    add_outline(obj, 0.025)
    return obj


def cylinder(name, loc, radius, depth, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    add_outline(obj, 0.022)
    return obj


def curve(name, pts, material, bevel=0.035):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = bevel
    data.bevel_resolution = 2
    spline = data.splines.new("POLY")
    spline.points.add(len(pts)-1)
    for p, xyz in zip(spline.points, pts):
        p.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    return obj


def ground(name, cx, color):
    ground_mat = mat(name + " | painted ground", color)
    box(name + " | broad ground platform", (cx, 0, -0.30), (44, 34, 0.5), ground_mat, 0.2)
    return ground_mat


def build_workshop_night(center=(0, 0, 0)):
    cx, cy, cz = center
    set_mood(bpy.context.scene, "night_workshop", center)
    ground("Workshop", cx, (0.12, 0.14, 0.21, 1))
    brick = mat("Workshop | plum brick", (0.29, 0.16, 0.17, 1))
    wood = mat("Workshop | warm timber", (0.40, 0.23, 0.13, 1))
    iron = mat("Workshop | inked iron", (0.075, 0.10, 0.15, 1))
    glass = mat("Workshop | amber window", (0.96, 0.47, 0.13, 1))
    box("Workshop | rear brick wall", (cx, 7, 4.3), (28, 0.45, 9), brick)
    for x in (-9, -4, 4, 9):
        box("Workshop | timber post", (cx+x, 6.6, 4.4), (0.27, 0.25, 9.2), wood, 0.04)
    # Large glowing panes are merely painted surfaces; practical bulbs do the lighting.
    for x in (-6.5, 0, 6.5):
        box("Workshop | amber window", (cx+x, 6.72, 5.3), (2.7, 0.08, 2.4), glass, 0.03)
        box("Workshop | window crossbar", (cx+x, 6.62, 5.3), (0.10, 0.10, 2.5), iron, 0.015)
        box("Workshop | window sill", (cx+x, 6.58, 4.0), (3.0, 0.25, 0.16), wood, 0.02)
    for x in (-5.8, 5.8):
        box("Workshop | workbench", (cx+x, 0.4, 1.0), (5.2, 1.0, 0.35), wood)
        for legx in (-2.1, 2.1):
            box("Workshop | bench leg", (cx+x+legx, 0.4, 0.35), (0.22, 0.72, 1.25), iron, 0.03)
    # Riveted truss and wall-mounted gears establish a mechanical space.
    for x in range(-12, 13, 2):
        cylinder("Workshop | wall gear", (cx+x, 6.35, 2.3 + (x % 3)*0.15), 0.58, 0.10, iron, (math.pi/2, 0, 0))
    box("Workshop | overhead beam", (cx, 1, 8.3), (25, 0.3, 0.45), wood)
    ANCHORS["workshop_night"] = {
        "center": [cx, cy, cz], "mood": "night_workshop",
        "builder": [cx-4.6, -0.7, 0], "rival": [cx+5.2, 0.2, 0],
        "dummy": [cx+2.2, -0.2, 0], "loop": [cx, 0.7, 0],
        "camera_wide": [cx, -21, 7.0], "look_at": [cx, 0, 3.1]
    }


def build_fairground_dawn(center=(100, 0, 0)):
    cx, cy, cz = center
    set_mood(bpy.context.scene, "morning_fair", center)
    ground("Fairground dawn", cx, (0.55, 0.40, 0.25, 1))
    cream = mat("Fairground | canvas cream", (0.91, 0.78, 0.55, 1))
    red = mat("Fairground | circus red", (0.70, 0.12, 0.10, 1))
    blue = mat("Fairground | faded blue", (0.10, 0.30, 0.49, 1))
    gold = mat("Fairground | brass trim", (0.85, 0.50, 0.12, 1))
    # Ticket booth and big-top silhouette are assembled from modular primitives.
    box("Fairground | ticket booth", (cx-8, 4, 2.0), (5.0, 3.4, 4.0), cream)
    box("Fairground | ticket booth red awning", (cx-8, 2.2, 3.5), (5.5, 0.8, 0.4), red)
    box("Fairground | booth service window", (cx-8, 2.20, 2.5), (2.0, 0.08, 1.2), blue)
    cylinder("Fairground | big-top tent base", (cx+9, 8, 1.4), 4.3, 2.8, cream)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=4.1, radius2=0.08, depth=5.8, location=(cx+9, 8, 5.6))
    tent = bpy.context.object
    tent.name = "Fairground | big-top canopy"
    tent.data.materials.append(red)
    add_outline(tent, 0.025)
    for i in range(8):
        a = i * math.tau / 8
        x, y = cx+9+3.2*math.cos(a), 8+3.2*math.sin(a)
        box("Fairground | tent stripe", (x, y, 4.0), (0.35, 0.35, 4.1), cream, 0.04)
    # String of pennants and bulbs. Each pennant is visibly shaped, not a floating label.
    for i in range(13):
        x = cx - 13 + i * 2.15
        z = 7.4 + 0.5 * (1 - abs(i-6)/6)
        curve("Fairground | bunting cord", [(x-1.0, 2, z+0.45), (x, 2, z), (x+1.0, 2, z+0.45)], gold, 0.025)
        box("Fairground | pennant", (x, 1.97, z-0.2), (0.48, 0.09, 0.75), red if i % 2 else blue, 0.02)
    for x in range(-12, 13, 4):
        box("Fairground | striped fence post", (cx+x, -2.8, 0.85), (0.22, 0.22, 1.7), red, 0.02)
    curve("Fairground | fence rail", [(cx-13, -2.8, 1.4), (cx+13, -2.8, 1.4)], cream, 0.10)
    ANCHORS["fairground_dawn"] = {
        "center": [cx, cy, cz], "mood": "morning_fair",
        "builder": [cx-4.0, -0.8, 0], "rival": [cx+4.7, -0.2, 0],
        "loop": [cx, 1.1, 0], "cart_start": [cx-7, 0, 0],
        "camera_wide": [cx, -25, 8.3], "look_at": [cx, 0, 3.5]
    }


def build_coaster_climax(center=(200, 0, 0)):
    cx, cy, cz = center
    set_mood(bpy.context.scene, "coaster_climax", center)
    ground("Climax fairground", cx, (0.43, 0.39, 0.31, 1))
    wood = mat("Climax | golden track timber", (0.52, 0.31, 0.15, 1))
    cream = mat("Climax | warm rail supports", (0.81, 0.72, 0.52, 1))
    red = mat("Climax | cart red", (0.66, 0.10, 0.08, 1))
    # Approach hill and run-out are independent shapes around the hero loop anchor.
    for x, height in ((-10, 4.0), (-8, 6.0), (-6, 3.0), (5, 1.1), (8, 1.3), (11, 0.8)):
        box("Climax | timber trestle", (cx+x, 1.5, height/2), (0.28, 0.35, height), wood, 0.04)
        box("Climax | cross brace", (cx+x, 1.1, height*0.48), (1.9, 0.16, 0.16), cream, 0.03)
    curve("Climax | approach rail", [(cx-12, 0.7, 8), (cx-10, 0.7, 7), (cx-8, 0.7, 5.6), (cx-6, 0.7, 3.2), (cx-3.2, 0.7, 0.1)], wood, 0.10)
    curve("Climax | straight runout", [(cx+3.2, 0.7, 0.1), (cx+7, 0.7, 0.1), (cx+12, 0.7, 0.1)], wood, 0.10)
    # Background midway tower with flags, no text or signs.
    box("Climax | midway tower", (cx+14, 5.5, 4.3), (2.5, 2.0, 8.6), cream)
    for z in (2.0, 4.0, 6.0):
        box("Climax | tower red panel", (cx+12.72, 4.45, z), (0.12, 1.4, 0.75), red, 0.02)
    ANCHORS["coaster_climax"] = {
        "center": [cx, cy, cz], "mood": "coaster_climax",
        "builder": [cx-5.0, -0.7, 0], "rival": [cx+5.0, -0.3, 0],
        "loop": [cx, 0.7, 0], "cart_start": [cx-8, 0.7, 0],
        "camera_wide": [cx, -22, 7.7], "look_at": [cx, 0, 3.1]
    }


def build_all_sets():
    ANCHORS.clear()
    build_workshop_night((0, 0, 0))
    build_fairground_dawn((100, 0, 0))
    build_coaster_climax((200, 0, 0))
    return ANCHORS
