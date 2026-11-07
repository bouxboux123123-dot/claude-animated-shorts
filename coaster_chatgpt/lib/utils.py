"""Shared Blender helpers for the roller-coaster story project.

These helpers intentionally avoid context-sensitive operators where practical.
"""
from __future__ import annotations

import math
import bpy
from mathutils import Vector


def ensure_collection(name: str, parent=None):
    """Create or reuse a collection and link it to parent (or the scene root)."""
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if parent is None:
        parent = bpy.context.scene.collection
    if collection.name not in parent.children:
        parent.children.link(collection)
    return collection


def link_only(obj, collection):
    """Ensure obj belongs to exactly the requested collection."""
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    return obj


def make_empty(name, collection, location=(0, 0, 0), display='PLAIN_AXES', size=0.25):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.empty_display_type = display
    obj.empty_display_size = size
    obj.location = Vector(location)
    return obj


def make_mesh_object(name, vertices, faces, collection, materials=None, material_indices=None):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for mat in materials or []:
        mesh.materials.append(mat)
    if material_indices:
        for poly, idx in zip(mesh.polygons, material_indices):
            poly.material_index = int(idx)
    return obj


def add_cube(name, collection, location, scale, material=None, bevel=0.0):
    # Unit cube; object scale remains unapplied for easy procedural editing.
    verts = [
        (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
        (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
        (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5),
        (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7),
        (0, 1, 5, 4), (1, 2, 6, 5),
        (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    obj = make_mesh_object(name, verts, faces, collection, [material] if material else [])
    obj.location = Vector(location)
    obj.scale = Vector(scale)
    if bevel > 0:
        mod = obj.modifiers.new('Soft_Edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new('Weighted_Normals', 'WEIGHTED_NORMAL')
    return obj


def _relink_operator_object(obj, collection):
    return link_only(obj, collection)


def add_cylinder(name, collection, location, radius, depth, material=None,
                 vertices=16, rotation=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth,
        location=location, rotation=rotation
    )
    obj = bpy.context.object
    obj.name = name
    _relink_operator_object(obj, collection)
    if material:
        obj.data.materials.append(material)
    if bevel > 0:
        mod = obj.modifiers.new('Soft_Edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new('Weighted_Normals', 'WEIGHTED_NORMAL')
    return obj


def add_uv_sphere(name, collection, location, scale, material=None, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=1.0, location=location
    )
    obj = bpy.context.object
    obj.name = name
    _relink_operator_object(obj, collection)
    obj.scale = Vector(scale)
    if material:
        obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def add_torus(name, collection, location, major_radius, minor_radius,
              material=None, rotation=(0, 0, 0), major_segments=24, minor_segments=8):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=major_segments,
        minor_segments=minor_segments,
        location=location,
        rotation=rotation,
        major_radius=major_radius,
        minor_radius=minor_radius,
    )
    obj = bpy.context.object
    obj.name = name
    _relink_operator_object(obj, collection)
    if material:
        obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def add_rod(name, collection, a, b, radius, material=None, vertices=12):
    """Create a cylinder between two world-space points."""
    a, b = Vector(a), Vector(b)
    delta = b - a
    length = delta.length
    mid = (a + b) * 0.5
    obj = add_cylinder(name, collection, mid, radius, length, material, vertices)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = delta.to_track_quat('Z', 'Y')
    return obj


def set_parent_keep_world(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def look_at(obj, target):
    direction = Vector(target) - obj.location
    if direction.length > 1e-6:
        obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def smoothstep(a, b, x):
    if abs(b - a) < 1e-8:
        return 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def set_object_visible(obj, visible: bool):
    obj.hide_render = not visible
    obj.hide_viewport = not visible


def collection_visible(collection, visible: bool):
    collection.hide_render = not visible
    collection.hide_viewport = not visible
