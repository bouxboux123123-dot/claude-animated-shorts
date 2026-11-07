"""Headless-safe procedural mesh helpers."""
import math
import bpy
from mathutils import Vector


def _material(name, color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.82
    return mat


def finish(obj, material, outline=True):
    obj.data.materials.append(material)
    if outline and hasattr(obj.data, 'materials'):
        ink = _material(f'{obj.name}_ink', (0.015, 0.012, 0.025))
        obj.data.materials.append(ink)
        mod = obj.modifiers.new('InkHull', 'SOLIDIFY')
        mod.thickness = 0.018
        mod.offset = 1.0
        mod.use_flip_normals = True
        mod.material_offset = 1
    return obj


def mesh_object(name, verts, faces, material=None, outline=True):
    mesh = bpy.data.meshes.new(f'{name}Mesh')
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    if material is not None:
        finish(obj, material, outline)
    return obj


def box(name, size=(1, 1, 1), material=None, outline=True):
    x, y, z = (v / 2 for v in size)
    verts = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
             (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
    return mesh_object(name, verts, faces, material, outline)


def cylinder(name, radius=0.2, depth=1.0, sides=16, material=None, outline=True):
    verts = []
    for z in (-depth / 2, depth / 2):
        verts.extend((radius * math.cos(2 * math.pi * i / sides),
                      radius * math.sin(2 * math.pi * i / sides), z)
                     for i in range(sides))
    faces = []
    faces.append(tuple(range(sides - 1, -1, -1)))
    faces.append(tuple(range(sides, 2 * sides)))
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    return mesh_object(name, verts, faces, material, outline)


def tube_between(name, a, b, radius=0.08, sides=10, material=None, outline=True):
    """Cylinder between points a and b, with local axis Z."""
    a, b = Vector(a), Vector(b)
    obj = cylinder(name, radius, (b - a).length, sides, material, outline)
    obj.location = (a + b) / 2
    obj.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return obj


def curve_tube(name, points, radius=0.12, sides=10, material=None, outline=True):
    """Connected bevel-like tube made from cylinders and joint spheres."""
    root = bpy.data.objects.new(name, None)
    if material is None:
        material = _material(f'{name}_mat', (0.6, 0.6, 0.6))
    for i, (a, b) in enumerate(zip(points, points[1:])):
        segment = tube_between(f'{name}_seg_{i:02d}', a, b, radius, sides, material, outline)
        segment.parent = root
    for i, p in enumerate(points[1:-1], 1):
        joint = cylinder(f'{name}_joint_{i:02d}', radius * 1.05, radius * 2.0,
                         sides, material, outline)
        joint.location = p
        joint.parent = root
    return root


def plane_card(name, width, height, material, outline=True):
    return box(name, (width, 0.06, height), material, outline)
