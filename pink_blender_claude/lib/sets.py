"""sets.py -- 3D visual environments + hero props for "The Pink Experiment"
Blender 5.2 (EEVEE Next), headless, bpy / bmesh / mathutils.

Conventions
-----------
* Z up, camera sits at -Y looking +Y, characters face -Y (toward camera).
  Every set is built as a room that is OPEN at its front (y = 0 plane) and whose
  back wall is at local y = D, so the camera always shoots in from -Y.
* Units are meters. Each set lives in collection ``set_<name>`` at ORIGIN[name].
  Visibility is left at default (visible); scene.py toggles ``hide_render``.
* All Engine helpers (toon_mat, ink_hull, glow, box, cyl, empty) are expected in
  this module's namespace (see _check_helpers).  Assumptions about them:
      - box()/cyl() centre the primitive on ``loc`` (world coords, cyl axis = Z)
      - ``rot`` is an XYZ Euler in radians
      - they return the created object
      - empty() takes WORLD coordinates and a Z rotation in radians

Anchor registry (empties named ``anc_<set>_<anchor>`` -- dict KEYS are exact)
-----------------------------------------------------------------------------
  *_spot    = floor point where a character's feet go (rot_z carries the facing
              direction; 0 = facing -Y/camera).  bench_spot = seat surface.
  *_center  = centre of the key feature, on its surface:
              bench_center (bench top) | wall_center (wall face, mid-height)
              table_center (table top) | desk_center (desk top)
              board_center (chalkboard face) | cell_center (cell floor centre)
  corridor    : guard_spot, cell_door (door base centre on the wall plane)
  mix_bench   : bench_center, scientist_spot, artisan_spot
  paint_wall  : wall_center, artisan_spot
  pink_cell   : cell_center, inmate_spot, bench_spot
  arm_wrestle : table_center, guard_spot (yaw +90 = faces +X),
                inmate_spot (yaw -90 = faces -X)
  night_station: desk_center, guard_spot
  blackboard  : board_center, scientist_spot

Hero props (build_props): returned values are ROOT EMPTIES with all mesh parts
parented to them (move/parent the root).  They are built in collection ``props``
at PROP_ORIGIN, well away from every set.
"""

import math
import random
import os

import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

# ---------------------------------------------------------------------------
# Engine helpers: toon_mat, ink_hull, glow, box, cyl, empty
# ---------------------------------------------------------------------------
try:
    from . import look as _look
except Exception:
    try:
        import look as _look
    except Exception:
        _look = None

def toon_mat(name, rgb, tex=None, ink=True):
    if _look and hasattr(_look, 'toon_mat'):
        return _look.toon_mat(name, rgb, tex, ink)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    return m

def ink_hull(obj, width=0.018):
    if _look and hasattr(_look, 'ink_hull'):
        return _look.ink_hull(obj, width)
    return obj

def glow(name, rgb, strength=5.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    em.inputs[0].default_value = (*rgb[:3], 1)
    em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], o.inputs[0])
    return m

def prim(kind, name, sc=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None, parent=None, ink=0.015, seg=24):
    bm = bmesh.new()
    if kind == 'sphere':
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=1.0)
    elif kind == 'cyl':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=1.0, radius2=1.0, depth=2.0)
    elif kind == 'cone':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=1.0, radius2=0.0, depth=2.0)
    else:
        bmesh.ops.create_cube(bm, size=2.0)
    for v in bm.verts:
        v.co = (v.co.x * sc[0], v.co.y * sc[1], v.co.z * sc[2])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    if ink:
        ink_hull(o, ink)
    return o

def empty(c, name, loc=(0, 0, 0), rot_z=0.0, target=None):
    e = bpy.data.objects.new(name, None)
    c.objects.link(e)
    e.empty_display_size = 0.2
    e.location = loc
    e.rotation_euler = (0, 0, rot_z)
    if target:
        e['target'] = list(target)
    return e

def box(c, name, sz, loc, mat, rot=(0, 0, 0), ink=0.015):
    o = prim('cube', name, (sz[0] / 2, sz[1] / 2, sz[2] / 2), loc, rot, mat, ink=ink)
    if o.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(o)
    c.objects.link(o)
    return o

def cyl(c, name, r, h, loc, mat, rot=(0, 0, 0), ink=0.015, seg=24):
    o = prim('cyl', name, (r, r, h / 2), loc, rot, mat, ink=ink, seg=seg)
    if o.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(o)
    c.objects.link(o)
    return o

_REQUIRED_HELPERS = ('toon_mat', 'ink_hull', 'glow', 'box', 'cyl', 'empty')


def _check_helpers():
    missing = [n for n in _REQUIRED_HELPERS if n not in globals()]
    if missing:
        raise NameError("sets.py: engine helpers not found in namespace: %s" % ", ".join(missing))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ORIGIN = {
    'corridor': (0, 0, 0), 'mix_bench': (100, 0, 0), 'paint_wall': (200, 0, 0),
    'pink_cell': (300, 0, 0), 'arm_wrestle': (400, 0, 0), 'night_station': (500, 0, 0),
    'blackboard': (600, 0, 0),
}
PROP_ORIGIN = (-100.0, 0.0, 0.0)

BAKER_MILLER = (0.96, 0.56, 0.76)       # #FF91AF
SLATE_CONCRETE = (0.68, 0.68, 0.72)
STEEL_DARK = (0.25, 0.28, 0.35)
OAK_WOOD = (0.72, 0.48, 0.28)
CAFETERIA_BLUE = (0.24, 0.48, 0.78)
CHALK_GREEN = (0.16, 0.28, 0.22)
CHALK_RED = (0.95, 0.30, 0.30)

PI = math.pi
HP = math.pi / 2.0

LIGHT_SCALE = 1.0     # global multiplier for every practical/fill light in the sets
ADD_FILL = True       # one soft fill light per set so no set is ever pitch black

# ---------------------------------------------------------------------------
# Materials (cached; names prefixed pe_)
# ---------------------------------------------------------------------------
_MAT_DEFS = {
    # key: (rgb, outline)
    'pink': (BAKER_MILLER, True), 'pink_dark': ((0.82, 0.42, 0.62), False),
    'pink_light': ((0.99, 0.70, 0.84), False),
    'slate': (SLATE_CONCRETE, True), 'slate_dark': ((0.50, 0.50, 0.56), True),
    'slate_light': ((0.80, 0.80, 0.82), True),
    'steel': (STEEL_DARK, True), 'steel_mid': ((0.40, 0.43, 0.50), True),
    'silver': ((0.80, 0.82, 0.86), True),
    'black': ((0.03, 0.03, 0.04), False), 'white': ((0.93, 0.93, 0.90), True),
    'oak': (OAK_WOOD, True), 'oak_dark': ((0.50, 0.31, 0.17), True),
    'oak_line': ((0.40, 0.24, 0.12), False), 'oak_light': ((0.82, 0.60, 0.38), True),
    'caf_blue': (CAFETERIA_BLUE, True), 'caf_blue_dark': ((0.16, 0.33, 0.58), True),
    'caf_blue_scuff': ((0.42, 0.64, 0.90), False),
    'chalk_green': (CHALK_GREEN, True), 'chalk_smudge': ((0.24, 0.38, 0.32), False),
    'chalk_white': ((0.92, 0.93, 0.90), False),
    'drab': ((0.52, 0.53, 0.55), True), 'drab_dark': ((0.31, 0.32, 0.35), False),
    'tile_a': ((0.70, 0.70, 0.74), False), 'tile_b': ((0.52, 0.54, 0.60), False),
    'grout': ((0.22, 0.23, 0.27), False),
    'cafe_a': ((0.74, 0.72, 0.66), False), 'cafe_b': ((0.55, 0.55, 0.56), False),
    'yellow': ((0.95, 0.78, 0.12), True), 'red': ((0.78, 0.12, 0.10), True),
    'pigment': ((0.55, 0.03, 0.05), False), 'cream': ((0.90, 0.86, 0.72), True),
    'beige': ((0.82, 0.78, 0.66), True), 'beige_dark': ((0.62, 0.58, 0.46), True),
    'rubber': ((0.12, 0.12, 0.14), True), 'brass': ((0.80, 0.62, 0.25), True),
    'floor_conc': ((0.58, 0.58, 0.62), False), 'crack': ((0.10, 0.10, 0.13), False),
    'crt_body': ((0.62, 0.60, 0.52), True), 'crt_dark': ((0.02, 0.20, 0.07), False),
    'night_wall': ((0.28, 0.32, 0.42), True), 'night_ceil': ((0.18, 0.20, 0.27), True),
    'night_floor': ((0.20, 0.22, 0.27), False), 'night_pane': ((0.04, 0.07, 0.17), False),
    'cork': ((0.70, 0.52, 0.32), True), 'canvas': ((0.88, 0.85, 0.74), True),
    'hall_wall': ((0.84, 0.82, 0.70), True), 'hall_floor': ((0.66, 0.44, 0.26), False),
}
_GLOW_DEFS = {
    'fluor': ((0.92, 0.98, 1.00), 6.0), 'green_digit': ((0.20, 1.00, 0.35), 6.0),
    'crt': ((0.10, 0.80, 0.28), 2.2), 'crt_hi': ((0.35, 1.00, 0.50), 5.0),
    'pink_feed': ((0.96, 0.56, 0.76), 1.6), 'amber': ((1.00, 0.62, 0.18), 8.0),
    'red_led': ((1.00, 0.10, 0.10), 6.0), 'exit': ((0.20, 1.00, 0.40), 4.0),
    'pink_lamp': ((1.00, 0.88, 0.93), 5.0), 'window': ((0.80, 0.90, 1.00), 2.5),
    'chalk_red': (CHALK_RED, 0.9),
}
_cache = {}


def M(key):
    k = 'm:' + key
    if k not in _cache:
        rgb, ink = _MAT_DEFS[key]
        _cache[k] = toon_mat('pe_' + key, rgb, ink=ink)
    return _cache[k]


def MC(name, rgb, ink=True):
    """Cached custom-colour toon material."""
    k = 'c:' + name
    if k not in _cache:
        _cache[k] = toon_mat('pe_' + name, rgb, ink=ink)
    return _cache[k]


def G(key):
    k = 'g:' + key
    if k not in _cache:
        rgb, s = _GLOW_DEFS[key]
        _cache[k] = glow('pe_glow_' + key, rgb, s)
    return _cache[k]


def GLASS():
    """Semi-transparent glass (plain Principled alpha; falls back to a toon mat)."""
    if 'glass' in _cache:
        return _cache['glass']
    try:
        mat = bpy.data.materials.new('pe_glass')
        try:
            mat.use_nodes = True
        except Exception:
            pass
        nt = mat.node_tree
        bsdf = nt.nodes.get('Principled BSDF') or nt.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.75, 0.90, 0.96, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.05
        bsdf.inputs['Alpha'].default_value = 0.28
        for attr, val in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            try:
                setattr(mat, attr, val)
            except Exception:
                pass
        _cache['glass'] = mat
    except Exception:
        _cache['glass'] = toon_mat('pe_glass_fb', (0.75, 0.90, 0.96), ink=True)
    return _cache['glass']


# ---------------------------------------------------------------------------
# Collections, anchors, lights
# ---------------------------------------------------------------------------
def _coll(name):
    scene = bpy.context.scene
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    else:
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    if c.name not in scene.collection.children:
        scene.collection.children.link(c)
    return c


def _anchors(c, key, spec):
    ox, oy, oz = ORIGIN[key]
    out = {}
    for n, (loc, yaw_deg) in spec.items():
        out[n] = empty(c, 'anc_%s_%s' % (key, n),
                       loc=(ox + loc[0], oy + loc[1], oz + loc[2]),
                       rot_z=math.radians(yaw_deg))
    return out


def _light(c, name, kind, loc, energy, color=(1, 1, 1), size=1.0, size_y=None,
           target=None, spot_deg=70.0, blend=0.6):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy * LIGHT_SCALE
    data.color = color
    if kind == 'AREA':
        data.shape = 'RECTANGLE' if size_y else 'SQUARE'
        data.size = size
        if size_y:
            data.size_y = size_y
    elif kind == 'SPOT':
        data.spot_size = math.radians(spot_deg)
        data.spot_blend = blend
        data.shadow_soft_size = 0.06
    else:
        data.shadow_soft_size = 0.1
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    tgt = Vector(target) if target is not None else Vector(loc) + Vector((0, 0, -1))
    ob.rotation_euler = (tgt - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.objects.link(ob)
    return ob


# ---------------------------------------------------------------------------
# Geometry utilities
# ---------------------------------------------------------------------------
def _strip_ink(ob):
    for m in list(ob.modifiers):
        if m.type == 'SOLIDIFY':
            ob.modifiers.remove(m)


def _xf(verts, loc, rot):
    m = Euler(rot, 'XYZ').to_matrix()
    lv = Vector(loc)
    return [tuple(m @ Vector(v) + lv) for v in verts]


def _tube_geo(R, r, a0, a1, ns, nm):
    full = abs((a1 - a0) - 2 * PI) < 1e-6
    n = ns if full else ns + 1
    verts, faces = [], []
    for i in range(n):
        a = a0 + (a1 - a0) * i / ns
        ca, sa = math.cos(a), math.sin(a)
        for j in range(nm):
            b = 2 * PI * j / nm
            rr = R + r * math.cos(b)
            verts.append((rr * ca, rr * sa, r * math.sin(b)))
    for i in range(ns):
        i2 = (i + 1) % n
        for j in range(nm):
            j2 = (j + 1) % nm
            faces.append((i * nm + j, i2 * nm + j, i2 * nm + j2, i * nm + j2))
    if not full:
        faces.append(tuple(range(nm)))
        faces.append(tuple(range((n - 1) * nm, n * nm)))
    return verts, faces


def _frustum_geo(rb, rt, h, seg, cap_b, cap_t):
    verts = []
    for r, z in ((rb, -h / 2), (rt, h / 2)):
        for i in range(seg):
            a = 2 * PI * i / seg
            verts.append((r * math.cos(a), r * math.sin(a), z))
    faces = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    if cap_b:
        faces.append(tuple(range(seg - 1, -1, -1)))
    if cap_t:
        faces.append(tuple(range(seg, 2 * seg)))
    return verts, faces


class F:
    """Local frame (origin + yaw) that builds geometry into collection ``c``.
    Local axes: +x right, +y away from camera, +z up (rotated by ``yaw`` about Z)."""

    def __init__(self, c, origin, yaw=0.0, tag=''):
        self.c, self.o, self.yaw, self.tag = c, Vector(origin), yaw, tag
        self._c, self._s = math.cos(yaw), math.sin(yaw)
        self.made = []

    # -- coordinates ---------------------------------------------------
    def p(self, x, y, z=0.0):
        return (self.o.x + x * self._c - y * self._s,
                self.o.y + x * self._s + y * self._c,
                self.o.z + z)

    def _r(self, rot):
        return (rot[0], rot[1], rot[2] + self.yaw)

    def _add(self, ob):
        self.made.append(ob)
        return ob

    # -- primitives ----------------------------------------------------
    def box(self, name, sz, loc, mat, rot=(0, 0, 0), ink=0.015):
        return self._add(box(self.c, self.tag + name, sz=sz, loc=self.p(*loc), mat=mat,
                             rot=self._r(rot), ink=ink))

    def deco(self, name, sz, loc, mat, rot=(0, 0, 0)):
        """Thin decal-like box: no outline."""
        ob = self.box(name, sz, loc, mat, rot, ink=0.001)
        _strip_ink(ob)
        return ob

    def cyl(self, name, r, h, loc, mat, rot=(0, 0, 0), ink=0.015, seg=24):
        return self._add(cyl(self.c, self.tag + name, r=r, h=h, loc=self.p(*loc), mat=mat,
                             rot=self._r(rot), ink=ink, seg=seg))

    def bar(self, name, p0, p1, t, mat, ink=0.012):
        """Square bar between two local points."""
        a, b = Vector(self.p(*p0)), Vector(self.p(*p1))
        d = b - a
        e = Vector((0, 1, 0)).rotation_difference(d.normalized()).to_euler()
        return self._add(box(self.c, self.tag + name, sz=(t, d.length, t), loc=tuple((a + b) / 2),
                             mat=mat, rot=tuple(e), ink=ink))

    def rod(self, name, p0, p1, r, mat, ink=0.01, seg=12):
        """Round rod between two local points."""
        a, b = Vector(self.p(*p0)), Vector(self.p(*p1))
        d = b - a
        e = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
        return self._add(cyl(self.c, self.tag + name, r=r, h=d.length, loc=tuple((a + b) / 2),
                             mat=mat, rot=tuple(e), ink=ink, seg=seg))

    # -- custom meshes -------------------------------------------------
    def mesh(self, name, verts, faces, mats, ink=None, closed=False, smooth=False, face_mat=None):
        me = bpy.data.meshes.new(self.tag + name)
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.update()
        if closed:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
        if smooth:
            try:
                me.shade_smooth()
            except Exception:
                pass
        for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
            me.materials.append(m)
        if face_mat is not None:
            for i, idx in enumerate(face_mat):
                me.polygons[i].material_index = idx
        ob = bpy.data.objects.new(self.tag + name, me)
        ob.location = self.o
        ob.rotation_euler = (0, 0, self.yaw)
        self.c.objects.link(ob)
        if ink:
            ink_hull(ob, ink)
        return self._add(ob)

    def tube(self, name, R, r, loc, rot, mat, a0=0.0, a1=2 * PI, ns=32, nm=8, ink=0.006):
        """Torus / arc tube (lies in local XY, then rotated by ``rot`` and moved to ``loc``)."""
        v, fcs = _tube_geo(R, r, a0, a1, ns, nm)
        return self.mesh(name, _xf(v, loc, rot), fcs, mat, ink=ink, closed=True, smooth=True)

    def frustum(self, name, rb, rt, h, loc, mat, rot=(0, 0, 0), seg=24,
                cap_b=False, cap_t=True, ink=0.008):
        """Cone frustum centred on ``loc`` (bottom radius rb, top radius rt)."""
        v, fcs = _frustum_geo(rb, rt, h, seg, cap_b, cap_t)
        return self.mesh(name, _xf(v, loc, rot), fcs, mat, ink=ink,
                         closed=(cap_b and cap_t), smooth=True)

    def lines(self, name, polys, w, mat, plane='xy', at=0.0, zf=None):
        """Flat ribbons. plane 'xy': points (x,y) at z=at(+zf), faces +Z.
        plane 'xz': points (x,z) at y=at, faces -Y (toward camera)."""
        hw = w / 2.0
        verts, faces = [], []

        def P(u, v):
            if plane == 'xy':
                return (u, v, at + (zf(u, v) if zf else 0.0))
            return (u, at, v)

        for pl in polys:
            for k in range(len(pl) - 1):
                (ax, ay), (bx, by) = pl[k], pl[k + 1]
                dx, dy = bx - ax, by - ay
                L = math.hypot(dx, dy)
                if L < 1e-6:
                    continue
                ux, uy = dx / L, dy / L
                nx, ny = -uy, ux
                ax, ay, bx, by = ax - ux * hw, ay - uy * hw, bx + ux * hw, by + uy * hw
                i = len(verts)
                verts += [P(ax + nx * hw, ay + ny * hw), P(ax - nx * hw, ay - ny * hw),
                          P(bx - nx * hw, by - ny * hw), P(bx + nx * hw, by + ny * hw)]
                faces.append((i, i + 1, i + 2, i + 3))
        if not faces:
            return None
        return self.mesh(name, verts, faces, mat)

    def blocks(self, name, x0, x1, z0, z1, at, mat, row=0.2, blk=0.4, w=0.007):
        """Cinder-block mortar lines on an XZ wall face."""
        polys = []
        n = int(round((z1 - z0) / row))
        for i in range(n + 1):
            polys.append([(x0, z0 + i * row), (x1, z0 + i * row)])
        for i in range(n):
            za, zb = z0 + i * row, z0 + (i + 1) * row
            x = x0 + (blk / 2 if i % 2 else blk)
            while x < x1 - 1e-6:
                polys.append([(x, za), (x, zb)])
                x += blk
        return self.lines(name, polys, w, mat, 'xz', at)

    def checker(self, name, x0, x1, y0, y1, z, tile, mat_a, mat_b):
        nx, ny = int(round((x1 - x0) / tile)), int(round((y1 - y0) / tile))
        verts, faces, fm = [], [], []
        for i in range(nx):
            for j in range(ny):
                xa, ya = x0 + i * tile, y0 + j * tile
                k = len(verts)
                verts += [(xa, ya, z), (xa + tile, ya, z), (xa + tile, ya + tile, z), (xa, ya + tile, z)]
                faces.append((k, k + 1, k + 2, k + 3))
                fm.append((i + j) % 2)
        return self.mesh(name, verts, faces, [mat_a, mat_b], face_mat=fm)

    def grid(self, name, x0, x1, y0, y1, nx, ny, zf, mat):
        verts, faces = [], []
        for i in range(nx + 1):
            for j in range(ny + 1):
                x = x0 + (x1 - x0) * i / nx
                y = y0 + (y1 - y0) * j / ny
                verts.append((x, y, zf(x, y)))
        for i in range(nx):
            for j in range(ny):
                a = i * (ny + 1) + j
                faces.append((a, a + ny + 1, a + ny + 2, a + 1))
        return self.mesh(name, verts, faces, mat, smooth=True)

    def txt(self, name, body, loc, size, mat, spin=0.0, align='CENTER', extrude=0.002):
        """Text standing upright, readable from -Y. ``spin`` = CCW rotation (radians) as seen by camera."""
        cu = bpy.data.curves.new(self.tag + name, 'FONT')
        cu.body = body
        cu.size = size
        cu.align_x = align
        cu.align_y = 'CENTER'
        cu.extrude = extrude
        cu.materials.append(mat)
        ob = bpy.data.objects.new(self.tag + name, cu)
        R = (Matrix.Rotation(self.yaw, 3, 'Z') @ Matrix.Rotation(-spin, 3, 'Y')
             @ Matrix.Rotation(HP, 3, 'X'))
        ob.rotation_euler = R.to_euler()
        ob.location = self.p(*loc)
        self.c.objects.link(ob)
        return self._add(ob)

    def parent_all(self, root):
        inv = Matrix.Translation(-self.o)
        for ob in self.made:
            ob.parent = root
            ob.matrix_parent_inverse = inv


def _room(f, W, D, H, floor=None, back=None, left=None, right=None, ceil=None, t=0.3, fwd=0.0):
    """Open-front room. Interior spans x[-W/2,W/2], y[0,D], z[0,H]."""
    y0, y1 = -fwd, D + t
    if floor:
        f.box('floor', (W + 2 * t, y1 - y0, t), (0, (y0 + y1) / 2, -t / 2 - 0.004), floor, ink=0.02)
    if back:
        f.box('wall_back', (W + 2 * t, t, H + 2 * t), (0, D + t / 2, H / 2), back, ink=0.02)
    if left:
        f.box('wall_left', (t, D, H + 2 * t), (-(W / 2 + t / 2), D / 2, H / 2), left, ink=0.02)
    if right:
        f.box('wall_right', (t, D, H + 2 * t), (W / 2 + t / 2, D / 2, H / 2), right, ink=0.02)
    if ceil:
        f.box('ceiling', (W + 2 * t, y1 - y0, t), (0, (y0 + y1) / 2, H + t / 2), ceil, ink=0.02)


def _fill(f, loc, energy, color=(1, 1, 1), size=2.5, target=None):
    if ADD_FILL:
        _light(f.c, f.tag + 'fill', 'AREA', f.p(*loc), energy, color, size=size,
               target=f.p(*target) if target else None)


# ---------------------------------------------------------------------------
# Shared set-dressing builders
# ---------------------------------------------------------------------------
def _fluor(f, x, y, z, length=1.2, energy=110.0):
    f.box('fl_housing', (0.36, length + 0.1, 0.07), (x, y, z - 0.035), M('slate_dark'), ink=0.006)
    for dx in (-0.08, 0.08):
        f.cyl('fl_tube', r=0.02, h=length, loc=(x + dx, y, z - 0.085), mat=G('fluor'),
              rot=(HP, 0, 0), ink=0.003, seg=12)
    _light(f.c, f.tag + 'fl_light', 'AREA', f.p(x, y, z - 0.12), energy, (0.9, 0.97, 1.0),
           size=0.5, size_y=length)


def _pendant(f, x, y, z_top, drop, shade_r, shade_mat, energy, color, aim_z, spot=80.0):
    zs = z_top - drop
    f.cyl('cord', r=0.006, h=drop, loc=(x, y, z_top - drop / 2), mat=M('black'), ink=0.003, seg=8)
    f.frustum('shade', shade_r, 0.07, 0.2, (x, y, zs), shade_mat, seg=28, cap_b=False, cap_t=True)
    f.cyl('bulb', r=0.04, h=0.06, loc=(x, y, zs - 0.07), mat=G('amber'), ink=0.003, seg=12)
    _light(f.c, f.tag + 'pend_light', 'SPOT', f.p(x, y, zs - 0.1), energy, color,
           target=f.p(x, y, aim_z), spot_deg=spot)


def _hand(f, name, pivot, theta, L, w, th, mat):
    """Clock/stopwatch hand on an XZ face; theta clockwise from 12 o'clock (radians)."""
    px, py, pz = pivot
    f.box(name, (w, th, L), (px + math.sin(theta) * L / 2, py, pz + math.cos(theta) * L / 2),
          mat, rot=(0, theta, 0), ink=0.002)


def _wall_clock(f, x, y, z, r=0.22, hour=2.35, minute=21.0):
    yf = y - 0.03
    f.cyl('clk_face', r=r, h=0.03, loc=(x, y - 0.015, z), mat=M('white'), rot=(HP, 0, 0), ink=0.006, seg=40)
    f.tube('clk_bezel', r, 0.016, (x, yf, z), (HP, 0, 0), M('black'), ns=40, nm=8, ink=0.004)
    for k in range(12):
        a = k * PI / 6
        L = 0.055 if k % 3 == 0 else 0.03
        rr = r - 0.03 - L / 2
        f.box('clk_tick', (0.014 if k % 3 == 0 else 0.008, 0.004, L),
              (x + math.sin(a) * rr, yf - 0.002, z + math.cos(a) * rr), M('black'), rot=(0, a, 0), ink=0.001)
    _hand(f, 'clk_hour', (x, yf - 0.007, z), hour * PI / 6, r * 0.5, 0.022, 0.006, M('black'))
    _hand(f, 'clk_min', (x, yf - 0.013, z), minute * PI / 30, r * 0.78, 0.014, 0.006, M('black'))
    f.cyl('clk_pin', r=0.012, h=0.012, loc=(x, yf - 0.016, z), mat=M('red'), rot=(HP, 0, 0), ink=0.002, seg=12)


def _door(f, num='C-14', detail=True):
    """Heavy steel cell door. Local origin = door base centre on the wall plane (y=0),
    room side is -y. Includes barred slit window, food slot, lock, rivets, hinges."""
    for sx in (-1, 1):
        f.box('jamb', (0.14, 0.18, 2.46), (sx * 0.64, -0.07, 1.2), M('steel'), ink=0.01)
    f.box('lintel', (1.42, 0.18, 0.14), (0, -0.07, 2.43), M('steel'), ink=0.01)
    f.box('slab', (1.08, 0.08, 2.34), (0, -0.10, 1.17), M('steel_mid'), ink=0.012)
    f.box('panel_lo', (0.84, 0.02, 0.72), (0, -0.15, 0.50), M('steel'), ink=0.006)
    f.box('panel_hi', (0.84, 0.02, 0.50), (0, -0.15, 1.97), M('steel'), ink=0.006)
    # barred slit window
    f.box('win_frame', (0.52, 0.03, 0.20), (0, -0.155, 1.68), M('steel'), ink=0.006)
    f.deco('win_dark', (0.44, 0.02, 0.11), (0, -0.168, 1.68), M('black'))
    for dx in (-0.14, -0.047, 0.047, 0.14):
        f.cyl('win_bar', r=0.008, h=0.13, loc=(dx, -0.176, 1.68), mat=M('silver'), ink=0.003, seg=8)
    # food slot, lock, handle
    f.box('slot', (0.34, 0.03, 0.09), (0, -0.155, 0.98), M('steel'), ink=0.006)
    f.deco('slot_dark', (0.28, 0.02, 0.035), (0, -0.172, 0.98), M('black'))
    f.box('lock', (0.12, 0.02, 0.24), (0.36, -0.15, 1.12), M('silver'), ink=0.005)
    f.deco('keyhole', (0.014, 0.01, 0.034), (0.36, -0.163, 1.10), M('black'))
    f.cyl('handle', r=0.012, h=0.1, loc=(0.36, -0.20, 1.24), mat=M('silver'), rot=(HP, 0, 0), ink=0.004, seg=10)
    # number plate + status lamp
    f.box('num_plate', (0.30, 0.015, 0.12), (0, -0.17, 2.62), M('yellow'), ink=0.004)
    f.txt('num_txt', num, (0, -0.1795, 2.62), 0.07, M('black'))
    f.box('lamp_house', (0.07, 0.05, 0.07), (0.88, -0.04, 2.15), M('steel'), ink=0.004)
    f.cyl('lamp_led', r=0.018, h=0.01, loc=(0.88, -0.07, 2.15), mat=G('red_led'), rot=(HP, 0, 0), ink=0.002, seg=10)
    if detail:
        for sx in (-1, 1):
            for k in range(7):
                f.cyl('rivet', r=0.014, h=0.012, loc=(sx * 0.48, -0.146, 0.15 + k * 0.33),
                      mat=M('silver'), rot=(HP, 0, 0), ink=0.002, seg=8)
        for zz in (0.3, 1.17, 2.0):
            f.box('hinge', (0.06, 0.07, 0.18), (-0.57, -0.17, zz), M('black'), ink=0.004)


def _paint_can(f, x, y, z):
    r, h = 0.11, 0.26
    f.cyl('can_body', r=r, h=h, loc=(x, y, z + h / 2), mat=M('silver'), ink=0.006, seg=32)
    f.cyl('can_label', r=r + 0.003, h=0.14, loc=(x, y, z + 0.13), mat=M('cream'), ink=0.003, seg=32)
    f.cyl('can_stripe', r=r + 0.004, h=0.04, loc=(x, y, z + 0.13), mat=M('pink'), ink=0.002, seg=32)
    f.tube('can_rim', r, 0.009, (x, y, z + h), (0, 0, 0), M('silver'), ink=0.004)
    f.tube('can_base', r, 0.007, (x, y, z + 0.005), (0, 0, 0), M('silver'), ink=0.003)
    f.cyl('can_paint', r=r - 0.012, h=0.006, loc=(x, y, z + h - 0.016), mat=M('pink'), ink=0.002, seg=32)
    f.tube('can_bail', r + 0.012, 0.004, (x, y, z + h - 0.04), (HP, 0, 0), M('silver'),
           a0=0.0, a1=PI, ns=20, nm=6, ink=0.003)
    for s in (-1, 1):
        f.box('can_ear', (0.02, 0.016, 0.03), (x + s * (r + 0.006), y, z + h - 0.04), M('silver'), ink=0.002)
    for a, L in ((-1.25, 0.09), (-1.75, 0.06), (-2.25, 0.11)):
        f.deco('can_drip', (0.028, 0.008, L),
               (x + (r + 0.004) * math.cos(a), y + (r + 0.004) * math.sin(a), z + h - 0.02 - L / 2),
               M('pink'), rot=(0, 0, a - HP))


def _paint_roller(f, x, y, z):
    """(x,y,z) = grip centre. Roller axis runs along +X."""
    hx = x + 0.145
    f.cyl('rol_grip', r=0.018, h=0.15, loc=(x, y, z), mat=M('steel'), ink=0.004, seg=16)
    f.cyl('rol_cap', r=0.02, h=0.012, loc=(x, y, z - 0.081), mat=M('silver'), ink=0.003, seg=16)
    f.cyl('rol_rod_v', r=0.0045, h=0.11, loc=(x, y, z + 0.13), mat=M('silver'), ink=0.003, seg=8)
    f.cyl('rol_rod_h', r=0.0045, h=0.285, loc=(x + 0.1425, y, z + 0.185), mat=M('silver'),
          rot=(0, HP, 0), ink=0.003, seg=8)
    f.cyl('rol_head', r=0.04, h=0.22, loc=(hx, y, z + 0.185), mat=M('pink'), rot=(0, HP, 0), ink=0.005, seg=32)
    for s in (-1, 1):
        f.cyl('rol_endcap', r=0.043, h=0.006, loc=(hx + s * 0.113, y, z + 0.185), mat=M('silver'),
              rot=(0, HP, 0), ink=0.003, seg=24)
    f.cyl('rol_knob', r=0.01, h=0.014, loc=(x + 0.29, y, z + 0.185), mat=M('steel'), rot=(0, HP, 0), ink=0.002, seg=10)


def _stopwatch(f, x, y, z, sec=20.0):
    """Face points toward -Y; crown/bow on top."""
    yf = y - 0.011
    f.cyl('sw_case', r=0.042, h=0.022, loc=(x, y, z), mat=M('silver'), rot=(HP, 0, 0), ink=0.003, seg=40)
    f.tube('sw_bezel', 0.042, 0.004, (x, yf, z), (HP, 0, 0), M('silver'), ns=40, nm=8, ink=0.002)
    f.cyl('sw_face', r=0.037, h=0.002, loc=(x, y - 0.0105, z), mat=M('white'), rot=(HP, 0, 0), ink=0.001, seg=40)
    for k in range(12):
        a = k * PI / 6
        rr = 0.03
        f.box('sw_tick', (0.0025, 0.001, 0.007 if k % 3 == 0 else 0.004),
              (x + math.sin(a) * rr, yf - 0.0015, z + math.cos(a) * rr), M('black'), rot=(0, a, 0), ink=0.001)
    _hand(f, 'sw_hand', (x, yf - 0.0035, z), sec * PI / 30, 0.032, 0.0022, 0.001, M('red'))
    f.cyl('sw_pin', r=0.003, h=0.003, loc=(x, yf - 0.005, z), mat=M('black'), rot=(HP, 0, 0), ink=0.001, seg=10)
    f.cyl('sw_crown', r=0.009, h=0.016, loc=(x, y, z + 0.0475), mat=M('silver'), ink=0.002, seg=16)
    f.cyl('sw_stem', r=0.005, h=0.01, loc=(x, y, z + 0.0585), mat=M('silver'), ink=0.001, seg=10)
    f.tube('sw_bow', 0.013, 0.0025, (x, y, z + 0.072), (HP, 0, 0), M('silver'), ns=24, nm=6, ink=0.0015)
    f.cyl('sw_pusher', r=0.0055, h=0.012, loc=(x + 0.0345, y, z + 0.0345), mat=M('silver'),
          rot=(0, PI / 4, 0), ink=0.0015, seg=10)


def _bench(f, x, y, z0, L=1.8, wide=0.4):
    """Welded heavy steel bench, bolted base plates, weld beads."""
    f.box('seat', (L, wide, 0.05), (x, y, z0 + 0.44), M('steel'), ink=0.012)
    f.box('spine', (L - 0.1, 0.06, 0.07), (x, y, z0 + 0.385), M('steel_mid'), ink=0.008)
    for s in (-1, 1):
        lx = x + s * (L / 2 - 0.2)
        f.box('leg', (0.06, wide - 0.04, 0.42), (lx, y, z0 + 0.21), M('steel_mid'), ink=0.01)
        f.box('plate', (0.28, wide + 0.06, 0.02), (lx, y, z0 + 0.01), M('steel_mid'), ink=0.008)
        for bx in (-0.09, 0.09):
            for by in (-1, 1):
                f.cyl('bolt', r=0.017, h=0.014, loc=(lx + bx, y + by * (wide / 2 + 0.005), z0 + 0.027),
                      mat=M('silver'), ink=0.003, seg=6)
        f.bar('brace', (lx, y, z0 + 0.08), (lx - s * 0.17, y, z0 + 0.38), 0.035, M('steel_mid'), ink=0.006)
        for off in (-1, 1):
            f.cyl('weld', r=0.007, h=wide - 0.08, loc=(lx + off * 0.034, y, z0 + 0.409),
                  mat=M('silver'), rot=(HP, 0, 0), ink=0.002, seg=8)
            f.cyl('weld', r=0.007, h=wide - 0.08, loc=(lx + off * 0.034, y, z0 + 0.024),
                  mat=M('silver'), rot=(HP, 0, 0), ink=0.002, seg=8)


def _tray(f, x, y, z, rz=0.0):
    f.box('tray', (0.42, 0.30, 0.012), (x, y, z + 0.006), M('silver'), rot=(0, 0, rz), ink=0.005)
    ca, sa = math.cos(rz), math.sin(rz)
    for (wx, wy, sx, sy) in ((-0.13, 0.065, 0.12, 0.10), (0.0, 0.065, 0.10, 0.10), (0.13, 0.065, 0.12, 0.10),
                             (-0.075, -0.07, 0.2, 0.10), (0.1, -0.07, 0.14, 0.10)):
        f.deco('tray_well', (sx, sy, 0.003), (x + wx * ca - wy * sa, y + wx * sa + wy * ca, z + 0.0125),
               M('steel_mid'), rot=(0, 0, rz))


# ===========================================================================
# 1. CORRIDOR
# ===========================================================================
def _build_corridor():
    key = 'corridor'
    c = _coll('set_' + key)
    o = ORIGIN[key]
    f = F(c, o, tag='cor_')
    W, D, H = 3.6, 9.6, 3.4
    _room(f, W, D, H, floor=M('slate_dark'), back=M('slate_light'), left=M('slate_light'),
          right=M('slate_light'), ceil=M('slate'))
    f.checker('tiles', -W / 2, W / 2, 0, D, 0.0, 0.6, M('tile_a'), M('tile_b'))
    f.lines('grout', [[(-W / 2, y), (W / 2, y)] for y in [i * 0.6 for i in range(int(D / 0.6) + 1)]] +
            [[(x, 0), (x, D)] for x in [-W / 2 + i * 0.6 for i in range(int(W / 0.6) + 1)]],
            0.008, M('grout'), 'xy', at=0.003)
    # dado (lower painted band) + stripe
    for sx in (-1, 1):
        f.box('dado', (0.03, D, 1.1), (sx * (W / 2 - 0.015), D / 2, 0.55), M('steel_mid'), ink=0.006)
        f.deco('dado_stripe', (0.04, D, 0.07), (sx * (W / 2 - 0.02), D / 2, 1.13), M('yellow'))
    f.box('dado_back', (W, 0.03, 1.1), (0, D - 0.015, 0.55), M('steel_mid'), ink=0.006)
    f.deco('dado_back_stripe', (W, 0.04, 0.07), (0, D - 0.02, 1.13), M('yellow'))
    f.deco('safety_line', (W, 0.14, 0.006), (0, D - 1.6, 0.003), M('yellow'))

    # end door + sign
    _door(F(c, (o[0], o[1] + D, o[2]), 0.0, 'cor_door_'), 'C-14', True)
    f.box('sign', (2.3, 0.05, 0.36), (0, D - 0.025, 3.0), M('yellow'), ink=0.008)
    f.deco('sign_edge', (2.2, 0.01, 0.03), (0, D - 0.052, 2.87), M('black'))
    f.deco('sign_edge', (2.2, 0.01, 0.03), (0, D - 0.052, 3.13), M('black'))
    f.txt('sign_txt', 'POD C - MAX SECURITY', (0, D - 0.056, 3.0), 0.13, M('black'))
    # side cell doors
    for i, yy in enumerate((2.4, 5.4, 8.2)):
        _door(F(c, (o[0] + W / 2, o[1] + yy, o[2]), -HP, 'cor_dr%d_' % i), 'C-%d' % (11 + i), False)
        _door(F(c, (o[0] - W / 2, o[1] + yy, o[2]), HP, 'cor_dl%d_' % i), 'C-%d' % (15 + i), False)

    # ceiling: fluorescent tubes, pipes
    for y in (1.2, 3.8, 6.4, 9.0):
        _fluor(f, 0, y, H, 1.2, 110.0)
    f.cyl('pipe', r=0.05, h=D, loc=(1.3, D / 2, H - 0.15), mat=M('steel_mid'), rot=(HP, 0, 0), ink=0.006)
    f.cyl('conduit', r=0.028, h=D, loc=(1.12, D / 2, H - 0.1), mat=M('red'), rot=(HP, 0, 0), ink=0.004, seg=12)
    for y in [0.8 + i * 1.6 for i in range(6)]:
        f.box('pipe_clamp', (0.06, 0.06, 0.22), (1.25, y, H - 0.11), M('steel'), ink=0.004)
    # fire extinguisher (right wall)
    f.cyl('ext_body', r=0.075, h=0.42, loc=(W / 2 - 0.12, 1.6, 1.25), mat=M('red'), ink=0.006, seg=20)
    f.cyl('ext_head', r=0.032, h=0.07, loc=(W / 2 - 0.12, 1.6, 1.50), mat=M('black'), ink=0.003, seg=12)
    f.cyl('ext_strap', r=0.08, h=0.03, loc=(W / 2 - 0.12, 1.6, 1.25), mat=M('steel_mid'), ink=0.003, seg=20)

    # lighting fill (guard + door)
    _fill(f, (0, -1.2, 2.8), 140, (1.0, 0.98, 0.95), 3.0, target=(0, 5.0, 1.0))
    return c, _anchors(c, key, {
        'guard_spot': ((0.4, 4.4, 0.0), 0.0),
        'cell_door': ((0.0, D, 0.0), 0.0),
    })


# ===========================================================================
# 2. MIX BENCH
# ===========================================================================
def _build_mix_bench():
    key = 'mix_bench'
    c = _coll('set_' + key)
    o = ORIGIN[key]
    f = F(c, o, tag='mix_')
    W, D, H = 6.4, 5.0, 3.2
    _room(f, W, D, H, floor=M('floor_conc'), back=M('beige'), left=M('beige'), right=M('beige'), ceil=M('slate'))
    f.lines('floor_joints', [[(-W / 2, y), (W / 2, y)] for y in (1.0, 2.0, 3.0, 4.0)] +
            [[(x, 0), (x, D)] for x in (-2.0, 0.0, 2.0)], 0.01, M('grout'), 'xy', at=0.003)
    f.blocks('wall_seams', -W / 2, W / 2, 0.0, H, D - 0.004, M('beige_dark'), 0.2, 0.4, 0.006)

    # --- heavy oak workbench ---
    by, top_z = 2.4, 1.0
    f.box('bench_top', (2.8, 0.95, 0.10), (0, by, top_z - 0.05), M('oak'), ink=0.015)
    f.lines('plank_lines', [[(x, by - 0.45), (x, by + 0.45)] for x in (-0.95, -0.35, 0.25, 0.85)],
            0.007, M('oak_line'), 'xy', at=top_z + 0.002)
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.box('bench_leg', (0.14, 0.14, 0.90), (sx * 1.25, by + sy * 0.38, 0.45), M('oak_dark'), ink=0.012)
    f.box('bench_shelf', (2.5, 0.84, 0.05), (0, by, 0.25), M('oak'), ink=0.01)
    f.box('bench_apron', (2.6, 0.04, 0.14), (0, by - 0.43, 0.88), M('oak_dark'), ink=0.008)
    for sx in (-0.6, 0.6):
        f.box('drawer', (0.72, 0.03, 0.18), (sx, by - 0.455, 0.88), M('oak'), ink=0.006)
        f.box('drawer_pull', (0.16, 0.03, 0.025), (sx, by - 0.49, 0.88), M('brass'), ink=0.004)
    f.box('vise_body', (0.20, 0.20, 0.14), (-1.55, by - 0.12, top_z + 0.07), M('steel'), ink=0.008)
    f.cyl('vise_screw', r=0.012, h=0.3, loc=(-1.55, by - 0.32, top_z + 0.07), mat=M('silver'), rot=(HP, 0, 0), ink=0.003, seg=10)
    f.cyl('vise_handle', r=0.01, h=0.18, loc=(-1.55, by - 0.46, top_z + 0.07), mat=M('silver'), rot=(0, HP, 0), ink=0.003, seg=8)

    # --- precision digital scale with glowing green digits ---
    sx0, sy0 = -0.70, 2.30
    f.box('scale_base', (0.36, 0.28, 0.04), (sx0, sy0, top_z + 0.02), M('steel_mid'), ink=0.006)
    f.box('scale_plate', (0.28, 0.22, 0.014), (sx0, sy0, top_z + 0.047), M('silver'), ink=0.004)
    f.box('scale_read', (0.20, 0.12, 0.10), (sx0 + 0.31, sy0, top_z + 0.05), M('steel'), ink=0.006)
    f.deco('scale_screen', (0.16, 0.012, 0.062), (sx0 + 0.31, sy0 - 0.062, top_z + 0.058), M('black'))
    f.txt('scale_digits', '12.50 g', (sx0 + 0.31, sy0 - 0.0705, top_z + 0.058), 0.04, G('green_digit'), extrude=0.001)
    # beaker with deep-red pigment sitting on the scale
    bz = top_z + 0.054
    f.cyl('beaker_pigment', r=0.052, h=0.10, loc=(sx0, sy0, bz + 0.056), mat=M('pigment'), ink=0.003, seg=28)
    f.cyl('beaker_glass', r=0.06, h=0.15, loc=(sx0, sy0, bz + 0.075), mat=GLASS(), ink=0.003, seg=28)
    f.tube('beaker_rim', 0.06, 0.004, (sx0, sy0, bz + 0.15), (0, 0, 0), GLASS(), ns=28, nm=6, ink=0.002)
    for k in range(4):
        f.deco('beaker_tick', (0.016 if k % 2 == 0 else 0.010, 0.004, 0.003),
               (sx0 + 0.058, sy0 - 0.012, bz + 0.03 + k * 0.025), M('white'))

    # --- Pantone swatch fan ---
    px, py = 0.45, 2.15
    zc = top_z + 0.004
    n = 10
    for i in range(n):
        a = math.radians(-52 + i * (104.0 / (n - 1)))
        d = (math.sin(a), -math.cos(a))
        rz = math.atan2(d[1], d[0]) - HP
        t = i / (n - 1)
        rgb = BAKER_MILLER if i == 3 else (0.99 - 0.20 * t, 0.84 - 0.70 * t, 0.90 - 0.62 * t)
        z = zc + i * 0.003
        f.box('swatch_card', (0.048, 0.22, 0.003), (px + d[0] * 0.11, py + d[1] * 0.11, z), M('white'), rot=(0, 0, rz), ink=0.002)
        f.deco('swatch_chip', (0.036, 0.11, 0.0016),
               (px + d[0] * 0.15, py + d[1] * 0.15, z + 0.0022), MC('swatch%d' % i, rgb, False), rot=(0, 0, rz))
    f.cyl('swatch_rivet', r=0.011, h=0.03, loc=(px, py, zc + 0.014), mat=M('silver'), ink=0.003, seg=12)

    # --- paint bucket on floor + stir stick ---
    _paint_can(f, 2.0, 1.7, 0.0)
    f.bar('stir_stick', (2.05, 1.72, 0.22), (2.25, 1.9, 0.62), 0.02, M('oak_light'), ink=0.003)
    # open pigment tins on the lower shelf
    for i, (tx, rgb) in enumerate(((-0.7, (0.78, 0.12, 0.10)), (-0.3, (0.95, 0.78, 0.12)), (0.1, (0.24, 0.48, 0.78)))):
        f.cyl('tin', r=0.07, h=0.09, loc=(tx, by, 0.30), mat=MC('tin%d' % i, rgb), ink=0.004, seg=20)

    # --- back wall: pegboard + shelves with jars ---
    f.box('pegboard', (2.8, 0.03, 1.0), (0, D - 0.015, 1.95), M('oak_light'), ink=0.006)
    f.lines('peg_dots', [[(x, z), (x + 0.001, z)] for x in [-1.3 + 0.2 * i for i in range(14)] for z in (1.6, 1.8, 2.0, 2.2, 2.4)],
            0.02, M('oak_line'), 'xz', at=D - 0.032)
    jar_cols = [(0.78, 0.12, 0.10), (0.96, 0.56, 0.76), (0.95, 0.78, 0.12), (0.24, 0.48, 0.78),
                (0.93, 0.93, 0.90), (0.20, 0.55, 0.30), (0.55, 0.03, 0.05), (0.85, 0.45, 0.15)]
    for sx, zz in ((-2.35, 1.5), (2.35, 1.5), (-2.35, 2.05), (2.35, 2.05)):
        f.box('shelf', (1.6, 0.28, 0.04), (sx, D - 0.14, zz), M('oak_dark'), ink=0.008)
        for k in range(5):
            jx = sx - 0.64 + k * 0.32
            col = jar_cols[(k + int(zz * 3) + (0 if sx < 0 else 3)) % len(jar_cols)]
            f.cyl('jar', r=0.07, h=0.17, loc=(jx, D - 0.14, zz + 0.105), mat=MC('jar%d_%d_%d' % (k, int(zz * 10), int(sx)), col), ink=0.004, seg=16)
            f.cyl('jar_lid', r=0.074, h=0.025, loc=(jx, D - 0.14, zz + 0.2), mat=M('silver'), ink=0.003, seg=16)

    # --- pendant over the bench + ceiling fluorescents ---
    _pendant(f, 0.0, by, H, 0.85, 0.28, M('steel'), 260, (1.0, 0.80, 0.55), 1.0, spot=95)
    _fluor(f, -1.8, 1.8, H, 1.2, 70.0)
    _fluor(f, 1.8, 1.8, H, 1.2, 70.0)
    _fill(f, (0, -1.2, 2.7), 120, (1.0, 0.97, 0.92), 3.0, target=(0, 3.2, 1.2))
    return c, _anchors(c, key, {
        'bench_center': ((0.0, by, top_z), 0.0),
        'scientist_spot': ((-1.0, 3.5, 0.0), 0.0),
        'artisan_spot': ((1.0, 3.5, 0.0), 0.0),
    })


# ===========================================================================
# 3. PAINT WALL
# ===========================================================================
def _build_paint_wall():
    key = 'paint_wall'
    c = _coll('set_' + key)
    o = ORIGIN[key]
    f = F(c, o, tag='pw_')
    W, D, H = 4.0, 4.5, 3.6
    _room(f, W, D, H, floor=M('floor_conc'), back=M('drab'), left=M('slate'), right=M('slate'), ceil=M('slate_dark'))
    f.lines('floor_joints', [[(-W / 2, y), (W / 2, y)] for y in (1.5, 3.0)] + [[(0, 0), (0, D)]],
            0.012, M('grout'), 'xy', at=0.003)

    # left half: drab cinderblock
    f.blocks('block_L', -W / 2, 0.0, 0.0, H, D - 0.004, M('drab_dark'), 0.2, 0.4, 0.012)
    # right half: freshly rolled Baker-Miller pink coat (slightly proud of the wall)
    f.box('pink_coat', (W / 2, 0.014, H - 0.02), (W / 4, D - 0.007, H / 2 - 0.01), M('pink'), ink=0.004)
    f.box('pink_edge', (0.035, 0.022, H - 0.02), (0.018, D - 0.011, H / 2 - 0.01), M('pink_light'), ink=0.003)
    f.blocks('block_R', 0.0, W / 2, 0.0, H, D - 0.0155, M('pink_dark'), 0.2, 0.4, 0.010)
    for bx, bw in ((0.55, 0.30), (1.05, 0.22), (1.55, 0.30)):          # roller-pass sheen
        f.deco('sheen', (bw, 0.003, H - 0.5), (bx, D - 0.0165, H / 2 - 0.05), M('pink_light'))
    for dx, L in ((0.12, 0.55), (0.30, 0.30), (0.46, 0.75)):           # drips along the seam side
        f.deco('drip', (0.03, 0.004, L), (dx, D - 0.0175, 0.62 - L / 2 + 0.15), M('pink'))
    f.deco('roller_edge_top', (W / 2, 0.003, 0.05), (W / 4, D - 0.0165, H - 0.1), M('pink_light'))

    # drop cloth, spilled pink, roller tray
    f.box('dropcloth', (2.5, 1.7, 0.01), (0.6, 3.55, 0.005), M('canvas'), rot=(0, 0, 0.07), ink=0.004)
    for sx, sy, r in ((0.2, 3.9, 0.07), (1.1, 3.3, 0.05), (0.75, 3.85, 0.09), (1.5, 3.7, 0.04)):
        f.cyl('spill', r=r, h=0.004, loc=(sx, sy, 0.012), mat=M('pink'), ink=0.001, seg=20)
    tx, ty = 0.20, 3.55
    f.box('tray_body', (0.52, 0.36, 0.045), (tx, ty, 0.03), M('silver'), ink=0.005)
    f.box('tray_paint', (0.42, 0.22, 0.008), (tx, ty - 0.03, 0.055), M('pink'), ink=0.002)
    f.box('tray_ramp', (0.46, 0.17, 0.01), (tx, ty + 0.13, 0.085), M('slate_light'), rot=(-0.35, 0, 0), ink=0.003)
    _paint_roller(f, tx - 0.42, ty - 0.35, 0.0)   # roller resting on the floor beside the tray
    _paint_can(f, 1.75, 3.6, 0.0)

    # tripod work lamp (key light on the wall)
    lx, ly = -1.55, 2.6
    for a in (0.0, 2.1, 4.2):
        f.rod('tripod', (lx, ly, 1.55), (lx + 0.45 * math.cos(a + 1.0), ly + 0.45 * math.sin(a + 1.0), 0.0),
              0.012, M('steel_mid'), ink=0.004)
    f.box('lamp_head', (0.38, 0.12, 0.28), (lx, ly, 1.7), M('steel'), ink=0.008)
    f.deco('lamp_glass', (0.32, 0.01, 0.22), (lx, ly - 0.065, 1.7), G('fluor'))
    _light(c, 'pw_work_light', 'SPOT', f.p(lx, ly - 0.12, 1.7), 420, (1.0, 0.97, 0.92),
           target=f.p(0.2, D, 1.6), spot_deg=75)
    _fluor(f, 0.0, 2.2, H, 1.2, 80.0)
    _fill(f, (0, -1.2, 2.9), 120, (1.0, 0.97, 0.95), 3.0, target=(0, 3.5, 1.2))
    return c, _anchors(c, key, {
        'wall_center': ((0.0, D, H / 2), 0.0),
        'artisan_spot': ((0.9, 2.9, 0.0), 0.0),
    })


# ===========================================================================
# 4. PINK CELL
# ===========================================================================
_CR_CX, _CR_CY, _CR_R = 0.0, 2.55, 0.52


def _crater_z(x, y):
    dx, dy = x - _CR_CX, y - _CR_CY
    r = math.hypot(dx, dy)
    th = math.atan2(dy, dx)
    R = _CR_R * (1.0 + 0.12 * math.sin(5 * th + 0.7) + 0.06 * math.sin(11 * th + 1.9))
    bowl = -0.075 * (1.0 - (r / R) ** 2) ** 1.2 if r < R else 0.0
    rim = 0.018 * math.exp(-((r - R) / 0.07) ** 2)
    return bowl + rim


def _build_pink_cell():
    key = 'pink_cell'
    c = _coll('set_' + key)
    o = ORIGIN[key]
    f = F(c, o, tag='cell_')
    W, D, H = 3.0, 3.4, 2.8
    _room(f, W, D, H, floor=None, back=M('pink'), left=M('pink'), right=M('pink'), ceil=M('pink'))
    # sub-floor slab (below the crater) + displaced concrete floor with impact crater
    f.box('subfloor', (W + 0.6, D + 0.3, 0.3), (0, D / 2 + 0.15, -0.09 - 0.15), M('slate_dark'), ink=0.02)
    f.grid('floor', -W / 2, W / 2, 0.0, D, 75, 85, _crater_z, M('floor_conc'))
    # radial cracks (ribbons that follow the crater surface)
    rng = random.Random(15)
    polys = []
    for k in range(10):
        th = k * 2 * PI / 10 + rng.uniform(-0.2, 0.2)
        r, pts = _CR_R * 0.12, []
        while r < _CR_R + rng.uniform(0.35, 0.8):
            pts.append((_CR_CX + r * math.cos(th), _CR_CY + r * math.sin(th)))
            th += rng.uniform(-0.09, 0.09)
            r += 0.055
        polys.append(pts)
        if len(pts) > 6:                                              # a branch
            bx, by = pts[len(pts) // 2]
            bth = th + rng.choice((-1, 1)) * 0.7
            polys.append([(bx + 0.05 * i * math.cos(bth + rng.uniform(-0.1, 0.1)),
                           by + 0.05 * i * math.sin(bth + rng.uniform(-0.1, 0.1))) for i in range(7)])
    polys = [[(max(-W / 2 + 0.02, min(W / 2 - 0.02, x)), max(0.02, min(D - 0.02, y))) for x, y in p] for p in polys]
    f.lines('crater_cracks', polys, 0.014, M('crack'), 'xy', at=0.004, zf=_crater_z)
    for i in range(16):                                               # rubble
        th = rng.uniform(0, 2 * PI)
        r = _CR_R * rng.uniform(0.95, 1.5)
        s = rng.uniform(0.025, 0.07)
        px, py = _CR_CX + r * math.cos(th), _CR_CY + r * math.sin(th)
        if abs(px) < W / 2 - 0.08 and 0.08 < py < D - 0.08:
            f.box('rubble', (s, s * rng.uniform(0.7, 1.3), s * 0.6), (px, py, _crater_z(px, py) + s * 0.25),
                  M('slate'), rot=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0, PI)), ink=0.004)

    # block seams on the three walls
    f.blocks('seams_back', -W / 2, W / 2, 0.0, H, D - 0.004, M('pink_dark'), 0.2, 0.4, 0.007)
    fl = F(c, (o[0] - W / 2, o[1], o[2]), HP, 'cell_L_')
    fl.blocks('seams_l', 0.0, D, 0.0, H, -0.004, M('pink_dark'), 0.2, 0.4, 0.007)
    fr = F(c, (o[0] + W / 2, o[1] + D, o[2]), -HP, 'cell_R_')
    fr.blocks('seams_r', 0.0, D, 0.0, H, -0.004, M('pink_dark'), 0.2, 0.4, 0.007)

    # welded steel bench against the back wall
    by = D - 0.45
    _bench(f, 0.0, by, 0.0, L=1.9, wide=0.4)
    # steel toilet / sink combo on the left wall
    f.box('toilet', (0.38, 0.55, 0.45), (-W / 2 + 0.2, 1.7, 0.225), M('steel_mid'), ink=0.008)
    f.cyl('toilet_bowl', r=0.14, h=0.03, loc=(-W / 2 + 0.2, 1.82, 0.46), mat=M('black'), ink=0.003, seg=20)
    f.box('sink', (0.34, 0.30, 0.12), (-W / 2 + 0.17, 1.4, 0.88), M('steel_mid'), ink=0.006)
    f.cyl('tap', r=0.012, h=0.1, loc=(-W / 2 + 0.06, 1.4, 1.0), mat=M('silver'), ink=0.003, seg=8)
    # vent grille
    f.box('vent', (0.5, 0.03, 0.30), (0.0, D - 0.015, 2.05), M('steel_mid'), ink=0.006)
    for k in range(5):
        f.deco('vent_slat', (0.44, 0.01, 0.02), (0.0, D - 0.032, 1.94 + k * 0.055), M('black'))
    # caged ceiling light
    f.box('lamp_house', (0.52, 0.52, 0.08), (0, 1.6, H - 0.04), M('steel'), ink=0.006)
    f.deco('lamp_glow', (0.42, 0.42, 0.01), (0, 1.6, H - 0.085), G('pink_lamp'))
    for k in (-0.14, 0, 0.14):
        f.rod('cage_a', (-0.25, 1.6 + k, H - 0.1), (0.25, 1.6 + k, H - 0.1), 0.006, M('steel_mid'), ink=0.002, seg=6)
        f.rod('cage_b', (k, 1.35, H - 0.1), (k, 1.85, H - 0.1), 0.006, M('steel_mid'), ink=0.002, seg=6)
    _light(c, 'cell_lamp', 'AREA', f.p(0, 1.6, H - 0.15), 170, (1.0, 0.90, 0.95), size=0.7)

    # front bars: wide gaps so the camera can shoot between them (centre gap at x=0)
    for k in range(-5, 5):
        bx = (k + 0.5) * 0.3
        f.cyl('bar', r=0.016, h=H - 0.2, loc=(bx, 0.05, H / 2), mat=M('steel'), ink=0.006, seg=12)
    f.box('rail_top', (W + 0.1, 0.08, 0.08), (0, 0.05, H - 0.06), M('steel'), ink=0.008)
    f.box('rail_bot', (W + 0.1, 0.08, 0.08), (0, 0.05, 0.06), M('steel'), ink=0.008)
    for sx in (-1, 1):
        f.box('post', (0.1, 0.1, H), (sx * (W / 2 + 0.02), 0.05, H / 2), M('steel'), ink=0.008)
    f.box('lock_box', (0.10, 0.09, 0.18), (W / 2 - 0.18, 0.05, 1.0), M('black'), ink=0.004)
    f.box('lock_plate', (0.14, 0.02, 0.22), (W / 2 - 0.18, 0.0, 1.0), M('steel_mid'), ink=0.004)
    _fill(f, (0, -0.8, 2.4), 110, (1.0, 0.95, 0.97), 2.4, target=(0, 2.0, 1.0))
    return c, _anchors(c, key, {
        'cell_center': ((0.0, D / 2, 0.0), 0.0),
        'inmate_spot': ((0.0, 1.5, 0.0), 0.0),
        'bench_spot': ((0.0, by, 0.465), 0.0),
    })


# ===========================================================================
# 5. ARM WRESTLE (prison cafeteria)
# ===========================================================================
def _build_arm_wrestle():
    key = 'arm_wrestle'
    c = _coll('set_' + key)
    o = ORIGIN[key]
    f = F(c, o, tag='arm_')
    W, D, H = 12.0, 9.0, 6.8
    _room(f, W, D, H, floor=M('slate_dark'), back=M('slate'), left=M('slate'), right=M('slate'), ceil=M('slate_dark'))
    f.checker('floor_tiles', -W / 2, W / 2, 0, D, 0.0, 0.75, M('cafe_a'), M('cafe_b'))
    f.blocks('wall_seams', -W / 2, W / 2, 0.0, H, D - 0.004, M('drab_dark'), 0.4, 0.8, 0.012)
    f.lines('danger_zone', [[(-1.7, 2.7), (1.7, 2.7), (1.7, 6.3), (-1.7, 6.3), (-1.7, 2.7)]], 0.06,
            M('yellow'), 'xy', at=0.004)

    # second-tier catwalk
    cz = 3.2
    f.box('deck', (W, 2.8, 0.12), (0, D - 1.4, cz - 0.06), M('steel'), ink=0.012)
    for x in [-W / 2 + 0.5 + i * 1.5 for i in range(8)]:
        f.box('deck_beam', (0.12, 2.8, 0.2), (x, D - 1.4, cz - 0.22), M('steel_mid'), ink=0.008)
    ry = D - 2.8
    for x in [-W / 2 + 0.1 + i * 0.75 for i in range(int(W / 0.75) + 1)]:
        f.box('rail_post', (0.05, 0.05, 1.05), (x, ry, cz + 0.525), M('steel_mid'), ink=0.006)
    f.box('rail_top', (W, 0.06, 0.05), (0, ry, cz + 1.05), M('steel_mid'), ink=0.006)
    for zz in (0.7, 0.35):
        f.box('rail_mid', (W, 0.03, 0.03), (0, ry, cz + zz), M('steel_mid'), ink=0.004)
    f.box('toe_plate', (W, 0.02, 0.1), (0, ry, cz + 0.06), M('steel_mid'), ink=0.004)
    for x in (-5.7, -2.9, 2.9, 5.7):
        f.box('column', (0.3, 0.3, H), (x, ry, H / 2), M('steel'), ink=0.01)
    # cell doors on both tiers
    for i, x in enumerate((-4.2, -1.4, 1.4, 4.2)):
        _door(F(c, (o[0] + x, o[1] + D, o[2]), 0.0, 'arm_lo%d_' % i), 'A-%d' % (1 + i), False)
        _door(F(c, (o[0] + x, o[1] + D, o[2] + cz + 0.06), 0.0, 'arm_up%d_' % i), 'B-%d' % (1 + i), False)

    # blue picnic table (long axis = Y so both fighters are in profile to camera)
    ty = 4.5
    f.box('table_top', (0.80, 1.90, 0.07), (0, ty, 0.76), M('caf_blue'), ink=0.012)
    f.box('table_rim', (0.84, 1.94, 0.02), (0, ty, 0.715), M('caf_blue_dark'), ink=0.006)
    f.box('table_beam', (0.06, 1.8, 0.06), (-0.2, ty, 0.69), M('caf_blue_dark'), ink=0.006)
    f.box('table_beam', (0.06, 1.8, 0.06), (0.2, ty, 0.69), M('caf_blue_dark'), ink=0.006)
    for sx in (-1, 1):
        f.box('bench_seat', (0.28, 1.90, 0.05), (sx * 0.66, ty, 0.46), M('caf_blue'), ink=0.01)
        for sy in (-0.7, 0.7):
            f.bar('a_leg', (sx * 0.95, ty + sy, 0.0), (sx * 0.20, ty + sy, 0.74), 0.06, M('caf_blue_dark'), ink=0.008)
    for sy in (-0.7, 0.7):
        f.box('bench_cross', (1.8, 0.06, 0.05), (0, ty + sy, 0.40), M('caf_blue_dark'), ink=0.006)
    f.lines('scuffs', [[(-0.25, ty - 0.8), (-0.2, ty - 0.2)], [(0.3, ty + 0.1), (0.22, ty + 0.7)],
                       [(-0.1, ty + 0.4), (0.1, ty + 0.55)], [(0.15, ty - 0.55), (0.3, ty - 0.35)]],
            0.02, M('caf_blue_scuff'), 'xy', at=0.797)
    # stamped metal lunch trays
    _tray(f, 0.0, ty + 0.72, 0.795, 0.0)
    _tray(f, 0.02, ty - 0.72, 0.795, 0.12)
    _tray(f, 0.66, ty + 0.75, 0.485, HP)
    _tray(f, 0.66, ty + 0.75, 0.497, HP + 0.05)
    f.cyl('cup', r=0.035, h=0.08, loc=(0.1, ty + 0.72, 0.84), mat=M('silver'), ink=0.003, seg=16)

    # big caged pendants
    for px in (-3.6, 0.0, 3.6):
        _pendant(f, px, ty, H, 1.6, 0.42, M('steel'), 520 if px == 0 else 300, (1.0, 0.92, 0.80), 0.0, spot=100)
    for x in (-3.0, 3.0):
        _fluor(f, x, D - 1.4, cz, 1.2, 60.0)       # under-catwalk lighting
    _fill(f, (0, -1.5, 5.0), 400, (1.0, 0.97, 0.93), 6.0, target=(0, 5.0, 1.0))
    return c, _anchors(c, key, {
        'table_center': ((0.0, ty, 0.795), 0.0),
        'guard_spot': ((-0.78, ty, 0.0), 90.0),
        'inmate_spot': ((0.78, ty, 0.0), -90.0),
    })


# ===========================================================================
# 6. NIGHT STATION
# ===========================================================================
def _build_night_station():
    key = 'night_station'
    c = _coll('set_' + key)
    o = ORIGIN[key]
    f = F(c, o, tag='ns_')
    W, D, H = 5.0, 4.0, 3.0
    _room(f, W, D, H, floor=M('night_floor'), back=M('night_wall'), left=M('night_wall'),
          right=M('night_wall'), ceil=M('night_ceil'))
    f.lines('floor_tiles', [[(-W / 2, y), (W / 2, y)] for y in (1.0, 2.0, 3.0)] +
            [[(x, 0), (x, D)] for x in (-1.5, -0.5 + 0.0, 0.5, 1.5)], 0.01, M('grout'), 'xy', at=0.003)
    f.box('dado', (W, 0.03, 0.95), (0, D - 0.015, 0.475), M('steel'), ink=0.006)
    f.deco('dado_stripe', (W, 0.04, 0.05), (0, D - 0.02, 0.98), M('yellow'))

    # guard watch desk (top surface z = 0.78)
    dy = 2.3
    f.box('desk_top', (1.9, 0.85, 0.06), (0, dy, 0.75), M('oak_dark'), ink=0.012)
    for s in (-1, 1):
        f.box('pedestal', (0.5, 0.75, 0.72), (s * 0.7, dy, 0.36), M('steel'), ink=0.01)
        for k in range(3):
            f.deco('drawer_line', (0.44, 0.01, 0.2), (s * 0.7, dy - 0.38, 0.14 + k * 0.22), M('steel_mid'))
            f.box('drawer_pull', (0.12, 0.02, 0.02), (s * 0.7, dy - 0.395, 0.17 + k * 0.22), M('silver'), ink=0.003)
    f.box('modesty', (0.9, 0.03, 0.5), (0, dy - 0.4, 0.46), M('steel'), ink=0.008)
    f.box('desk_plate', (0.22, 0.01, 0.07), (0, dy - 0.42, 0.55), M('brass'), ink=0.002)
    # swivel chair
    gy = 3.1
    f.cyl('chair_post', r=0.03, h=0.35, loc=(0, gy, 0.25), mat=M('steel_mid'), ink=0.004, seg=10)
    for k in range(3):
        f.box('chair_foot', (0.6, 0.05, 0.04), (0, gy, 0.06), M('steel_mid'), rot=(0, 0, k * PI / 3), ink=0.004)
    f.box('chair_seat', (0.48, 0.46, 0.07), (0, gy, 0.46), M('rubber'), ink=0.006)
    f.box('chair_back', (0.46, 0.06, 0.52), (0, gy + 0.23, 0.80), M('rubber'), ink=0.006)

    # CRT security monitor, yawed toward guard + camera
    fc = F(c, f.p(-0.72, dy, 0.78), math.radians(50), 'ns_crt_')
    fc.box('base', (0.3, 0.26, 0.04), (0, 0, 0.02), M('crt_body'), ink=0.004)
    fc.cyl('swivel', r=0.1, h=0.03, loc=(0, 0, 0.055), mat=M('crt_body'), ink=0.004, seg=20)
    fc.box('case_front', (0.50, 0.12, 0.42), (0, -0.07, 0.28), M('crt_body'), ink=0.008)
    fc.box('case_rear', (0.36, 0.26, 0.30), (0, 0.12, 0.28), M('crt_body'), ink=0.008)
    fc.deco('bezel', (0.43, 0.01, 0.35), (0, -0.131, 0.28), M('black'))
    fc.deco('screen', (0.40, 0.005, 0.32), (0, -0.1385, 0.28), G('crt'))
    fc.lines('scanlines', [[(-0.19, 0.28 + k * 0.03), (0.19, 0.28 + k * 0.03)] for k in range(-5, 6)],
             0.004, M('crt_dark'), 'xz', at=-0.1425)
    fc.lines('quad', [[(0, 0.12), (0, 0.44)], [(-0.2, 0.28), (0.2, 0.28)]], 0.008, M('crt_dark'), 'xz', at=-0.1432)
    fc.deco('feed_pink', (0.17, 0.004, 0.13), (0.095, -0.1445, 0.195), G('pink_feed'))
    fc.txt('cam_label', 'CAM 04', (-0.095, -0.1475, 0.40), 0.03, G('crt_hi'), extrude=0.0005)
    _light(c, 'ns_crt_light', 'AREA', fc.p(0, -0.22, 0.28), 38, (0.2, 1.0, 0.4), size=0.35,
           target=fc.p(0, -2.0, 0.2))

    # amber desk lamp (articulated arm, cone shade, spot)
    lx, ly = 0.68, 2.35
    f.cyl('lamp_base', r=0.075, h=0.025, loc=(lx, ly, 0.79), mat=M('black'), ink=0.004, seg=20)
    f.bar('lamp_arm1', (lx, ly, 0.80), (lx + 0.08, ly + 0.02, 1.12), 0.018, M('brass'), ink=0.004)
    f.bar('lamp_arm2', (lx + 0.08, ly + 0.02, 1.12), (lx - 0.10, ly - 0.03, 1.28), 0.018, M('brass'), ink=0.004)
    f.frustum('lamp_shade', 0.11, 0.035, 0.12, (lx - 0.14, ly - 0.04, 1.27), M('steel'), rot=(0.0, 0.35, 0.0),
              seg=24, cap_b=False, cap_t=True)
    f.cyl('lamp_bulb', r=0.03, h=0.04, loc=(lx - 0.15, ly - 0.04, 1.2), mat=G('amber'), ink=0.003, seg=12)
    _light(c, 'ns_lamp', 'SPOT', f.p(lx - 0.15, ly - 0.05, 1.2), 220, (1.0, 0.62, 0.28),
           target=f.p(0.35, 2.1, 0.78), spot_deg=85)
    _light(c, 'ns_lamp_bounce', 'POINT', f.p(lx - 0.1, ly - 0.1, 1.0), 18, (1.0, 0.65, 0.3))

    # desk dressing
    f.box('keyboard', (0.40, 0.15, 0.02), (-0.05, 2.03, 0.79), M('crt_body'), ink=0.004)
    f.deco('keys', (0.36, 0.11, 0.004), (-0.05, 2.03, 0.802), M('steel_mid'))
    f.cyl('mug', r=0.04, h=0.09, loc=(0.36, 2.0, 0.825), mat=M('white'), ink=0.004, seg=18)
    f.tube('mug_handle', 0.02, 0.006, (0.405, 2.0, 0.825), (HP, 0, 0), M('white'), ns=14, nm=6, ink=0.002)
    f.box('phone', (0.20, 0.17, 0.07), (0.15, 2.45, 0.815), M('black'), ink=0.004)
    for i, (px, py, rz) in enumerate(((-0.35, 1.98, 0.15), (-0.28, 1.95, -0.1), (0.62, 2.1, 0.3))):
        f.box('paper', (0.22, 0.30, 0.004), (px, py, 0.782 + i * 0.004), M('white'), rot=(0, 0, rz), ink=0.001)

    # analog wall clock: hands past the 15/20-minute marks (2:21)
    _wall_clock(f, 1.0, D, 2.05, 0.22, hour=2.35, minute=21.0)
    # window + blinds, night outside
    f.box('win_frame', (1.34, 0.08, 1.14), (-1.6, D - 0.04, 1.9), M('black'), ink=0.008)
    f.deco('win_pane', (1.16, 0.01, 0.96), (-1.6, D - 0.085, 1.9), M('night_pane'))
    for i in range(12):
        f.box('blind', (1.16, 0.012, 0.04), (-1.6, D - 0.10, 2.34 - i * 0.075), M('beige_dark'), rot=(0.35, 0, 0), ink=0.002)
    # corkboard + filing cabinet
    f.box('cork', (0.80, 0.03, 0.60), (1.95, D - 0.015, 1.7), M('cork'), ink=0.006)
    for px, pz, rz in ((1.75, 1.85, 0.05), (1.98, 1.62, -0.08), (2.15, 1.82, 0.1)):
        f.deco('pin_paper', (0.17, 0.003, 0.22), (px, D - 0.033, pz), M('white'), rot=(0, rz, 0))
    f.box('cabinet', (0.5, 0.6, 1.3), (-2.1, 3.4, 0.65), M('steel'), ink=0.01)
    for k in range(3):
        f.deco('cab_line', (0.44, 0.01, 0.3), (-2.1, 3.09, 0.22 + k * 0.4), M('steel_mid'))
        f.box('cab_pull', (0.12, 0.02, 0.02), (-2.1, 3.08, 0.30 + k * 0.4), M('silver'), ink=0.002)

    _fill(f, (0, 2.0, H - 0.1), 30, (0.5, 0.6, 1.0), 3.0, target=(0, 2.5, 0.8))
    return c, _anchors(c, key, {
        'desk_center': ((0.0, dy, 0.78), 0.0),
        'guard_spot': ((0.0, gy, 0.0), 0.0),
    })


# ===========================================================================
# 7. BLACKBOARD (lecture hall)
# ===========================================================================
def _build_blackboard():
    key = 'blackboard'
    c = _coll('set_' + key)
    o = ORIGIN[key]
    f = F(c, o, tag='bb_')
    W, D, H = 9.0, 6.5, 4.0
    _room(f, W, D, H, floor=M('hall_floor'), back=M('hall_wall'), left=M('hall_wall'),
          right=M('hall_wall'), ceil=M('slate_light'))
    f.lines('floor_planks', [[(x, 0), (x, D)] for x in [-W / 2 + i * 0.25 for i in range(int(W / 0.25) + 1)]],
            0.008, M('oak_line'), 'xy', at=0.003)
    f.box('wainscot', (W, 0.05, 1.0), (0, D - 0.025, 0.5), M('oak'), ink=0.006)
    f.box('wainscot_rail', (W, 0.07, 0.06), (0, D - 0.035, 1.03), M('oak_dark'), ink=0.006)
    for sx in (-1, 1):
        f.box('wainscot_side', (0.05, D, 1.0), (sx * (W / 2 - 0.025), D / 2, 0.5), M('oak'), ink=0.006)
    # windows on the left wall (daylight)
    for wy in (1.8, 4.4):
        f.box('win_frame', (0.08, 1.3, 1.9), (-W / 2 + 0.04, wy, 2.3), M('oak_dark'), ink=0.008)
        f.deco('win_pane', (0.01, 1.14, 1.74), (-W / 2 + 0.085, wy, 2.3), G('window'))
    _light(c, 'bb_window_light', 'AREA', f.p(-W / 2 + 0.4, 3.1, 2.4), 320, (0.85, 0.92, 1.0), size=1.6, size_y=2.4,
           target=f.p(0.0, 3.5, 1.2))
    # exit sign
    f.box('exit_box', (0.5, 0.06, 0.2), (3.2, D - 0.03, 3.1), M('black'), ink=0.004)
    f.txt('exit_txt', 'EXIT', (3.2, D - 0.065, 3.1), 0.11, G('exit'), extrude=0.001)

    # --- chalkboard with wooden frame ---
    bz, BW, BH = 1.75, 3.6, 2.2
    yb = D - 0.063                     # chalk plane
    f.box('board', (BW, 0.03, BH), (0, D - 0.045, bz), M('chalk_green'), ink=0.004)
    for sx in (-1, 1):
        f.box('frame_side', (0.12, 0.10, BH + 0.24), (sx * (BW / 2 + 0.06), D - 0.05, bz), M('oak'), ink=0.01)
    for sz in (-1, 1):
        f.box('frame_tb', (BW + 0.24, 0.10, 0.12), (0, D - 0.05, bz + sz * (BH / 2 + 0.06)), M('oak'), ink=0.01)
    f.box('tray', (BW + 0.24, 0.14, 0.05), (0, D - 0.10, bz - BH / 2 - 0.145), M('oak_dark'), ink=0.008)
    f.box('tray_lip', (BW + 0.24, 0.02, 0.07), (0, D - 0.175, bz - BH / 2 - 0.135), M('oak_dark'), ink=0.006)
    for i, (cx, cr, rz) in enumerate(((-0.9, 'chalk_white', 0.2), (-0.78, 'chalk_white', -0.1), (1.1, 'chalk_red', 0.3))):
        col = M('chalk_white') if cr == 'chalk_white' else G('chalk_red')
        f.cyl('chalk_stick', r=0.008, h=0.09, loc=(cx, D - 0.10, bz - BH / 2 - 0.108), mat=col,
              rot=(0, HP, rz), ink=0.001, seg=8)
    f.box('eraser', (0.14, 0.06, 0.04), (0.6, D - 0.10, bz - BH / 2 - 0.105), M('beige_dark'), ink=0.004)
    f.deco('eraser_felt', (0.14, 0.062, 0.01), (0.6, D - 0.10, bz - BH / 2 - 0.122), M('black'))
    # eraser smudges
    f.lines('smudges', [[(-1.5, bz + 0.9), (-0.7, bz + 0.6)], [(0.9, bz - 0.5), (1.6, bz - 0.9)],
                        [(-1.6, bz - 0.2), (-1.1, bz - 0.45)], [(0.5, bz + 0.95), (1.4, bz + 0.8)]],
            0.16, M('chalk_smudge'), 'xz', at=yb + 0.0008)

    # --- chalk graph: TIME vs AGGRESSION ---
    rng = random.Random(20)
    x0, x1 = -1.25, 1.35
    vb, vtop = bz - 0.75, bz + 0.88
    px = lambda t: x0 + t / 30.0 * (x1 - x0)
    pz = lambda y: vb + y * 1.45
    jit = lambda: rng.uniform(-0.003, 0.003)
    white, red = M('chalk_white'), G('chalk_red')
    f.lines('axes', [[(x0, vb), (x1 + 0.03, vb + jit())], [(x0, vb), (x0 + jit(), vtop)]], 0.02, white, 'xz', at=yb)
    f.lines('arrows', [[(x1 - 0.06, vb + 0.05), (x1 + 0.03, vb), (x1 - 0.06, vb - 0.05)],
                       [(x0 - 0.05, vtop - 0.08), (x0, vtop + 0.01), (x0 + 0.05, vtop - 0.08)]], 0.018, white, 'xz', at=yb)
    f.lines('ticks', [[(px(t), vb - 0.035), (px(t), vb + 0.035)] for t in (5, 10, 25, 30)], 0.016, white, 'xz', at=yb)
    # bell curve (white) -> calm drop at 15 -> flat -> red spike after 20
    bell = [(px(t), pz(0.06 + 0.52 * math.exp(-((t - 6.0) / 3.4) ** 2)) + jit()) for t in [i * 0.4 for i in range(38)]]
    flat = [(px(15 + i * 0.5), pz(0.06) + jit()) for i in range(0, 11)]
    spike = [(px(20 + i * 0.25), pz(0.06 + 0.90 * (math.exp(i * 0.25 / 2.8) - 1) / (math.exp(10 / 2.8) - 1)) + jit())
             for i in range(0, 41)]
    f.lines('curve_white', [bell, flat], 0.022, white, 'xz', at=yb + 0.0005)
    f.lines('curve_red', [spike], 0.026, red, 'xz', at=yb + 0.001)
    # dashed markers at 15 and 20 minutes
    for t, mat in ((15, white), (20, red)):
        z, polys = vb + 0.05, []
        while z < vtop - 0.05:
            polys.append([(px(t), z), (px(t), z + 0.07)])
            z += 0.12
        f.lines('marker_%d' % t, polys, 0.014, mat, 'xz', at=yb)
    # labels
    f.txt('lbl_time', 'TIME', ((x0 + x1) / 2, bz - 1.0, yb - 0.002), 0.16, white)
    f.txt('lbl_aggr', 'AGGRESSION', (x0 - 0.30, (vb + vtop) / 2 - 0.02, yb - 0.002), 0.14, white, spin=HP)
    f.txt('lbl_15', '15m', (px(15), vb - 0.12, yb - 0.002), 0.085, white)
    f.txt('lbl_20', '20m', (px(20), vb - 0.12, yb - 0.002), 0.085, red)

    # --- wooden lectern ---
    lx, ly = 1.9, 3.4
    f.box('lectern_body', (0.55, 0.42, 0.95), (lx, ly, 0.475), M('oak_dark'), ink=0.012)
    f.box('lectern_top', (0.66, 0.46, 0.04), (lx, ly, 1.0), M('oak'), rot=(math.radians(14), 0, 0), ink=0.01)
    f.box('lectern_lip', (0.66, 0.025, 0.045), (lx, ly - 0.215, 0.975), M('oak'), ink=0.006)
    f.box('lectern_base', (0.62, 0.48, 0.05), (lx, ly, 0.025), M('oak'), ink=0.008)
    f.box('lectern_panel', (0.42, 0.01, 0.55), (lx, ly - 0.215, 0.5), M('oak_light'), ink=0.003)
    f.box('book', (0.26, 0.19, 0.03), (lx - 0.12, ly, 1.04), M('red'), rot=(math.radians(14), 0, 0.1), ink=0.004)
    f.cyl('mic_stem', r=0.006, h=0.3, loc=(lx + 0.2, ly + 0.08, 1.17), mat=M('steel_mid'), ink=0.002, seg=8)
    f.cyl('mic_head', r=0.018, h=0.05, loc=(lx + 0.2, ly + 0.08, 1.34), mat=M('black'), ink=0.003, seg=12)

    # ceiling lights
    for lyy in (1.8, 4.6):
        for lxx in (-2.4, 2.4):
            _fluor(f, lxx, lyy, H, 1.2, 70.0)
    _fill(f, (0, -1.0, 3.2), 200, (1.0, 0.98, 0.93), 4.0, target=(0, D, 1.5))
    return c, _anchors(c, key, {
        'board_center': ((0.0, yb, bz), 0.0),
        'scientist_spot': ((-2.0, 3.8, 0.0), 0.0),
    })


# ===========================================================================
# Hero props
# ===========================================================================
def build_props():
    """Hero props, each as a root Empty with parts parented. Located at PROP_ORIGIN."""
    _check_helpers()
    c = _coll('props')
    props = {}
    specs = (
        ('paint_can', 0.0, lambda f: _paint_can(f, 0, 0, 0)),
        ('paint_roller', 2.0, lambda f: _paint_roller(f, 0, 0, 0)),
        ('stopwatch', 4.0, lambda f: _stopwatch(f, 0, 0, 0)),
        ('bench', 6.0, lambda f: _bench(f, 0, 0, 0, L=1.8, wide=0.4)),
    )
    for name, dy, builder in specs:
        loc = (PROP_ORIGIN[0], PROP_ORIGIN[1] + dy, PROP_ORIGIN[2])
        f = F(c, loc, tag='prop_%s_' % name)
        builder(f)
        root = empty(c, 'prop_' + name, loc=loc, rot_z=0.0)
        f.parent_all(root)
        props[name] = root
    return props


# ===========================================================================
# Deliverable
# ===========================================================================
def build_sets():
    _check_helpers()
    props = build_props()
    c_corridor, A_corridor = _build_corridor()
    c_mix, A_mix = _build_mix_bench()
    c_pw, A_pw = _build_paint_wall()
    c_cell, A_cell = _build_pink_cell()
    c_arm, A_arm = _build_arm_wrestle()
    c_ns, A_ns = _build_night_station()
    c_bb, A_bb = _build_blackboard()
    out = {
        'corridor': {'collection': c_corridor, 'anchors': A_corridor},
        'mix_bench': {'collection': c_mix, 'anchors': A_mix},
        'paint_wall': {'collection': c_pw, 'anchors': A_pw},
        'pink_cell': {'collection': c_cell, 'anchors': A_cell},
        'arm_wrestle': {'collection': c_arm, 'anchors': A_arm},
        'night_station': {'collection': c_ns, 'anchors': A_ns},
        'blackboard': {'collection': c_bb, 'anchors': A_bb},
    }
    return out, props
