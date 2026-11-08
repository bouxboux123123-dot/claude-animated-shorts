"""lib/props.py  --  LAYER 2 (PROPS)

NO STATIC MANNEQUIN SETS.  Every hero object is a PropSpec subclass that exposes

    CHANNELS   named scalar controls (clamped, with defaults)       -> what acting.json drives
    SOCKETS    named 2D grip points in the prop's own XZ plane        -> where hands attach
    update()   rebuild geometry / dynamic sockets from channels only  -> deterministic in f

A prop never animates itself over time.  Its entire state is a pure function of the channel values
that scene.apply_frame_actions(f) sets for frame f, so any frame can be rendered by any worker.

    LoopTrackProp       bend_bottom, squeeze_sides         (circle -> clothoid teardrop -> tall/skinny)
    SledgehammerProp    swing_stroke                        sockets grip_main, grip_twohand, head_strike
    TestDummyProp       crush_progress                      vertical accordion compression
    TurnbuckleCrankProp crank_angle                         (degrees, drives loop.squeeze_sides when linked)
    CoasterCartProp     track_progress [0..1]               arc-length parameter on a Bezier spline
"""
import bisect
import math

import bpy

from . import look
from .look import (build_card, capsule, ellipse, gear, new_empty, rect,
                   toon_material, flat_material)

# --------------------------------------------------------------------------------------
# 2D math shared with chars.py / scene.py     (rotation about Y == in-plane rotation)
# --------------------------------------------------------------------------------------


def rot2(x, z, th):
    c, s = math.cos(th), math.sin(th)
    return x * c + z * s, -x * s + z * c


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


EASES = {
    "linear": lambda t: t,
    "in": lambda t: t * t,
    "out": lambda t: 1.0 - (1.0 - t) * (1.0 - t),
    "inout": smooth,
}


def ease(name, t):
    return EASES.get(name or "inout", smooth)(clamp(t, 0.0, 1.0))


class Frame2D:
    """pos=[x,y,z] world, rot about Y, uniform scale, flip (+1/-1 mirrors local X like scale.x=-1)."""

    def __init__(self, pos, rot=0.0, scale=1.0, flip=1.0):
        self.pos, self.rot, self.scale, self.flip = pos, rot, scale, flip

    def to_world(self, lx, lz):
        wx, wz = rot2(self.flip * self.scale * lx, self.scale * lz, self.rot)
        return self.pos[0] + wx, self.pos[2] + wz

    def to_local(self, wx, wz):
        sx, sz = rot2(wx - self.pos[0], wz - self.pos[2], -self.rot)
        return self.flip * sx / self.scale, sz / self.scale


# --------------------------------------------------------------------------------------
# Bezier spline with arc-length parameterisation (used by the cart)
# --------------------------------------------------------------------------------------
class BezierPath:
    SAMPLES = 16

    def __init__(self, segs):
        self.segs = segs
        self.cum, self.ref = [0.0], [(0, 0.0)]
        self.seg_end = []
        total, prev = 0.0, segs[0][0]
        for i, sg in enumerate(segs):
            for k in range(1, self.SAMPLES + 1):
                t = k / float(self.SAMPLES)
                p = self._eval(sg, t)
                total += math.dist(prev, p)
                self.cum.append(total)
                self.ref.append((i, t))
                prev = p
            self.seg_end.append(total)
        self.length = max(total, 1e-6)

    @classmethod
    def from_points(cls, pts):
        """Catmull-Rom -> cubic Bezier conversion (so the path really is a Bezier spline)."""
        n, segs = len(pts), []
        for i in range(n - 1):
            p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
            b1 = tuple(p1[k] + (p2[k] - p0[k]) / 6.0 for k in range(3))
            b2 = tuple(p2[k] - (p3[k] - p1[k]) / 6.0 for k in range(3))
            segs.append((tuple(p1), b1, b2, tuple(p2)))
        return cls(segs)

    @staticmethod
    def _eval(sg, t):
        u = 1.0 - t
        a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        return tuple(a * sg[0][k] + b * sg[1][k] + c * sg[2][k] + d * sg[3][k] for k in range(3))

    @staticmethod
    def _deriv(sg, t):
        u = 1.0 - t
        return tuple(3 * u * u * (sg[1][k] - sg[0][k]) + 6 * u * t * (sg[2][k] - sg[1][k])
                     + 3 * t * t * (sg[3][k] - sg[2][k]) for k in range(3))

    def at(self, u):
        s = clamp(u, 0.0, 1.0) * self.length
        j = clamp(bisect.bisect_left(self.cum, s), 1, len(self.cum) - 1)
        c0, c1 = self.cum[j - 1], self.cum[j]
        f = 0.0 if c1 - c0 < 1e-9 else (s - c0) / (c1 - c0)
        (i0, t0), (i1, t1) = self.ref[j - 1], self.ref[j]
        if i1 != i0:           # crossing a segment boundary (t0 == 1.0 of previous seg)
            i0, t0 = i1, 0.0
        i, t = i1, lerp(t0, t1, f)
        sg = self.segs[i]
        d = self._deriv(sg, t)
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        return self._eval(sg, t), tuple(v / n for v in d)

    def u_at_sample(self, idx):
        return 0.0 if idx <= 0 else self.seg_end[min(idx, len(self.seg_end)) - 1] / self.length


# --------------------------------------------------------------------------------------
# PropSpec base
# --------------------------------------------------------------------------------------
class PropSpec:
    kind = "prop"
    carried = False          # True: the prop follows the holding hand (tools). False: hands follow sockets.
    CHANNELS = {}            # name -> (default, lo, hi)
    SOCKETS = {}             # name -> (x, z) in prop-local plane

    def __init__(self, pid, **opts):
        self.id, self.opts = pid, opts
        self.coll = look.new_collection("PROP_" + pid)
        self.sock_objs = {}
        with look.into(self.coll):
            self.root = new_empty(pid + ".root", display="ARROWS", size=0.4)
            self.build()
            for n, (x, z) in self.SOCKETS.items():
                self.sock_objs[n] = new_empty("%s.sock.%s" % (pid, n), self.root, (x, 0, z), "SPHERE", 0.07)
        self.reset()

    # ---- to be provided by subclasses --------------------------------------------------
    def build(self):
        raise NotImplementedError

    def update(self):
        """Recompute geometry + dynamic sockets from self.ch (pure function)."""

    def propagate(self, props):
        """Derive channels of OTHER props (e.g. crank -> loop squeeze). Runs before update()."""

    def marker(self, name):
        raise KeyError(name)

    # ---- generic ------------------------------------------------------------------------
    def reset(self):
        self.ch = {k: v[0] for k, v in self.CHANNELS.items()}
        self.pos, self.rot, self.scale, self.visible = [0.0, 0.0, 0.0], 0.0, 1.0, False
        self.sockets = dict(self.SOCKETS)

    def set_channel(self, name, v):
        _, lo, hi = self.CHANNELS[name]
        self.ch[name] = clamp(float(v), lo, hi)

    def frame(self):
        return Frame2D(self.pos, self.rot, self.scale)

    def socket_world(self, name):
        sx, sz = self.sockets[name]
        return self.frame().to_world(sx, sz)

    def place_by_socket(self, name, wx, wz, y, rot):
        """Put the prop at rotation `rot` so that socket `name` lands exactly on (wx, wz)."""
        sx, sz = self.sockets[name]
        dx, dz = rot2(sx * self.scale, sz * self.scale, rot)
        self.rot, self.pos = rot, [wx - dx, y, wz - dz]

    def commit(self):
        self.root.location = self.pos
        self.root.rotation_euler = (0.0, self.rot, 0.0)
        self.root.scale = (self.scale,) * 3
        self.coll.hide_render = not self.visible
        self.coll.hide_viewport = not self.visible
        for n, (x, z) in self.sockets.items():
            self.sock_objs[n].location = (x, 0.0, z)

    def digest(self):
        r = lambda v: round(v, 4)
        return (self.id, self.visible, tuple(r(v) for v in self.pos), r(self.rot), r(self.scale),
                tuple(sorted((k, r(v)) for k, v in self.ch.items())))


# --------------------------------------------------------------------------------------
# LoopTrackProp
# --------------------------------------------------------------------------------------
def track_points(R, bend, squeeze, H=5.6, lin=9.0, lane=1.4, n_lift=8, n_in=30, n_loop=96, n_out=18):
    """Full centreline (x, y, z) of lift hill + descent + loop + run-out, and marker indices.

    bend=0     -> constant curvature  == perfect circle (hairpin radius R at the bottom)
    bend=1     -> curvature ramps linearly with arc length from gentle (bottom) to tight (top): clothoid
    squeeze=1  -> sides clamped together, weighted by height: tall & skinny, tight hairpin at the TOP,
                  bottom (entry/exit) left untouched so the lead-in / run-out still connect."""
    pts = []
    for i in range(n_lift):                          # lift hill, arrives flat at the crest
        t = i / float(n_lift)
        pts.append((-lin - 5.5 + 5.5 * t, 0.0, (H - 2.6) + 2.6 * math.sin(t * math.pi / 2)))
    P = [(-lin, H), (-lin * 0.5, H), (-lin * 0.5, 0.0), (0.0, 0.0)]
    for i in range(n_in):                            # first drop, cubic Bezier S-curve
        t, u = i / float(n_in), 1.0 - i / float(n_in)
        a, b, c, d = u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3
        pts.append((a * P[0][0] + b * P[1][0] + c * P[2][0] + d * P[3][0], 0.0,
                    a * P[0][1] + b * P[1][1] + c * P[2][1] + d * P[3][1]))
    L = 2 * math.pi * R
    ds, k0 = L / (n_loop - 1), 1.0 / R
    kb = k0 * (1.0 - 0.78 * bend)
    kt = 2 * k0 - kb                                  # keeps total turning at exactly 2*pi
    x = z = th = 0.0
    loop = [(0.0, 0.0)]
    for i in range(1, n_loop):
        s_mid = (i - 0.5) * ds
        tau = (s_mid / (L / 2)) if s_mid <= L / 2 else ((L - s_mid) / (L / 2))
        kap = kb + (kt - kb) * tau
        th_mid = th + 0.5 * kap * ds
        x += math.cos(th_mid) * ds
        z += math.sin(th_mid) * ds
        th += kap * ds
        loop.append((x, z))
    zmax = max(p[1] for p in loop) or 1.0
    xc = loop[n_loop // 2][0]
    sq = []
    for (px, pz) in loop:
        w = clamp(pz / zmax, 0.0, 1.0)
        sq.append((xc + (px - xc) * (1.0 - 0.60 * squeeze * w), pz * (1.0 + 0.50 * squeeze * w)))
    for i, (px, pz) in enumerate(sq):
        pts.append((px, lane * smooth(i / float(n_loop - 1)), pz))
    ex, ez = sq[-1]
    for i in range(1, n_out + 1):
        pts.append((ex + i * 0.9, lane, ez))
    base = n_lift + n_in
    idx = {"lift_start": 0, "lift_mid": n_lift // 2, "crest": n_lift, "drop_mid": n_lift + n_in // 2,
           "pre_loop": base - 4, "loop_in": base, "loop_q1": base + n_loop // 4,
           "top_in": base + n_loop // 2 - 8, "loop_top": base + n_loop // 2,
           "top_out": base + n_loop // 2 + 8, "loop_q3": base + (3 * n_loop) // 4,
           "loop_out": base + n_loop - 1, "exit": len(pts) - 1}
    return pts, idx, base, n_loop


class LoopTrackProp(PropSpec):
    kind = "loop_track"
    CHANNELS = {"bend_bottom": (0.0, 0.0, 1.0), "squeeze_sides": (0.0, 0.0, 1.0)}
    SOCKETS = {"strike_spot": (0.9, 0.35), "bottom": (0.0, 0.2),
               "clamp_ascent": (2.8, 2.0), "clamp_descent": (-2.8, 2.0)}
    RAIL_W, RAIL_D, TIE_W, TIE_L, ZC = 0.30, 0.45, 0.62, 0.10, 2.0

    def build(self):
        self.R = self.opts.get("R", 3.0)
        self.params = dict(H=self.opts.get("H", 5.6), lin=self.opts.get("lin", 9.0))
        pts, self.idx, self.loop0, self.nloop = track_points(self.R, 0, 0, **self.params)
        self._pts, self._key, self._path, self._path_key = pts, None, None, None
        n = len(pts)
        self.tie_ids = list(range(0, n, 3))
        rail_mat = toon_material("rail_" + self.id, self.opts.get("rail", (0.80, 0.17, 0.14)))
        tie_mat = toon_material("tie_wood", (0.45, 0.30, 0.18))
        # rails: 4 verts per sample (LF, RF, LB, RB), 4 quads per segment
        faces = []
        for i in range(n - 1):
            a, b = 4 * i, 4 * (i + 1)
            faces += [(a, a + 1, b + 1, b), (b + 2, b + 3, a + 3, a + 2),
                      (a, b, b + 2, a + 2), (a + 1, a + 3, b + 3, b + 1)]
        self.rail_mesh = bpy.data.meshes.new(self.id + ".rail")
        self.rail_mesh.from_pydata([(0, 0, 0)] * (4 * n), [], faces)
        self.rail_mesh.materials.append(rail_mat)
        self.rail_obj = bpy.data.objects.new(self.id + ".rail", self.rail_mesh)
        look._link(self.rail_obj)
        self.rail_obj.parent = self.root
        look.add_ink_hull(self.rail_obj, 0.05)
        nt = len(self.tie_ids)
        self.tie_mesh = bpy.data.meshes.new(self.id + ".ties")
        self.tie_mesh.from_pydata([(0, 0, 0)] * (4 * nt), [], [(4 * k, 4 * k + 1, 4 * k + 2, 4 * k + 3) for k in range(nt)])
        self.tie_mesh.materials.append(tie_mat)
        tie_obj = bpy.data.objects.new(self.id + ".ties", self.tie_mesh)
        look._link(tie_obj)
        tie_obj.parent = self.root
        # static pillars under the lift + descent (they never move with the channels)
        pil_mat = toon_material("pillar_steel", (0.45, 0.50, 0.56))
        for k in range(1, self.loop0, 4):
            x, _, z = pts[k]
            if z > 0.6:
                build_card("%s.pillar%02d" % (self.id, k), rect(-0.14, 0.0, 0.14, z - 0.12), pil_mat,
                           depth=0.2, ink=0.03, parent=self.root, loc=(x, 0.45, 0.0))
        self._rebuild(0.0, 0.0)

    # -------------------------------------------------------------------------------------
    def _frames(self, pts):
        n, out = len(pts), []
        for i in range(n):
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
            tx, tz = b[0] - a[0], b[2] - a[2]
            ln = math.hypot(tx, tz) or 1.0
            out.append((tx / ln, tz / ln))
        return out

    def _rebuild(self, b, s):
        pts, idx, _, _ = track_points(self.R, b, s, **self.params)
        self._pts, self._key, self._path = pts, (round(b, 5), round(s, 5)), None
        fr, h = self._frames(pts), self.RAIL_D / 2.0
        flat = []
        for (x, y, z), (tx, tz) in zip(pts, fr):
            lx, lz = -tz, tx
            W = self.RAIL_W
            flat += [x + lx * W, y - h, z + lz * W, x - lx * W, y - h, z - lz * W,
                     x + lx * W, y + h, z + lz * W, x - lx * W, y + h, z - lz * W]
        self.rail_mesh.vertices.foreach_set("co", flat)
        self.rail_mesh.update()
        tf = []
        for i in self.tie_ids:
            (x, y, z), (tx, tz) = pts[i], fr[i]
            lx, lz = -tz, tx
            W, T, yy = self.TIE_W, self.TIE_L, y - h - 0.02
            tf += [x + lx * W - tx * T, yy, z + lz * W - tz * T, x - lx * W - tx * T, yy, z - lz * W - tz * T,
                   x - lx * W + tx * T, yy, z - lz * W + tz * T, x + lx * W + tx * T, yy, z + lz * W + tz * T]
        self.tie_mesh.vertices.foreach_set("co", tf)
        self.tie_mesh.update()
        # dynamic sockets: where the turnbuckle clamps bite (first rising / last falling crossing of ZC)
        lo, hi = self.loop0, self.loop0 + self.nloop
        asc = desc = None
        for i in range(lo, hi - 1):
            z0, z1 = pts[i][2], pts[i + 1][2]
            if asc is None and z0 < self.ZC <= z1:
                f = (self.ZC - z0) / (z1 - z0)
                asc = (lerp(pts[i][0], pts[i + 1][0], f), self.ZC)
            if z0 >= self.ZC > z1:
                f = (z0 - self.ZC) / (z0 - z1)
                desc = (lerp(pts[i][0], pts[i + 1][0], f), self.ZC)
        self._clamps = (asc or self.SOCKETS["clamp_ascent"], desc or self.SOCKETS["clamp_descent"])

    def update(self):
        key = (round(self.ch["bend_bottom"], 5), round(self.ch["squeeze_sides"], 5))
        if key != self._key:
            self._rebuild(*key)
        self.sockets["clamp_ascent"], self.sockets["clamp_descent"] = self._clamps

    def local_to_world(self, p):
        return (self.pos[0] + self.scale * p[0], self.pos[1] + self.scale * p[1], self.pos[2] + self.scale * p[2])

    def get_path(self):
        if self._path is None:
            self._path = BezierPath.from_points(self._pts)
        return self._path

    def markers(self):
        path = self.get_path()
        return {k: path.u_at_sample(i) for k, i in self.idx.items()}

    def digest(self):
        return super().digest() + (round(sum(p[0] + 3 * p[2] + 7 * p[1] for p in self._pts), 3),)


# --------------------------------------------------------------------------------------
# SledgehammerProp  (carried tool)
# --------------------------------------------------------------------------------------
class SledgehammerProp(PropSpec):
    kind = "sledgehammer"
    carried = True
    CHANNELS = {"swing_stroke": (0.0, 0.0, 1.0)}      # 0 carry | 0.25 cocked back | 1.0 impact
    SOCKETS = {"grip_main": (0.0, 0.15), "grip_twohand": (0.0, 0.95), "head_strike": (0.0, 2.50)}
    CARRY_DEG, COCK_DEG, HIT_DEG = -10.0, -62.0, 122.0

    def build(self):
        wood = toon_material("hammer_wood", (0.55, 0.38, 0.22))
        steel = toon_material("hammer_steel", (0.55, 0.58, 0.64))
        dark = toon_material("hammer_band", (0.22, 0.24, 0.30))
        build_card("hammer.handle", rect(-0.09, -0.05, 0.09, 2.55), wood, depth=0.10, ink=0.04, parent=self.root, loc=(0, 0.0, 0))
        build_card("hammer.head", rect(-0.68, 2.12, 0.68, 2.88), steel, depth=0.16, ink=0.05, parent=self.root, loc=(0, -0.05, 0))
        build_card("hammer.band", rect(-0.09, 2.0, 0.09, 2.14), dark, depth=0.14, ink=0, parent=self.root, loc=(0, -0.06, 0))
        build_card("hammer.face", rect(-0.72, 2.2, -0.60, 2.80), dark, depth=0.18, ink=0, parent=self.root, loc=(0, -0.06, 0))
        build_card("hammer.grip", rect(-0.11, 0.0, 0.11, 0.55), dark, depth=0.12, ink=0, parent=self.root, loc=(0, -0.03, 0))

    def hold_pose(self):
        """(angle, radius) of the grip around the holder's shoulder, in the holder's local frame."""
        u = self.ch["swing_stroke"]
        deg = lerp(self.CARRY_DEG, self.COCK_DEG, u / 0.25) if u <= 0.25 else \
            lerp(self.COCK_DEG, self.HIT_DEG, (u - 0.25) / 0.75)
        return math.radians(deg), lerp(0.95, 1.30, u)


# --------------------------------------------------------------------------------------
# TestDummyProp
# --------------------------------------------------------------------------------------
class TestDummyProp(PropSpec):
    kind = "test_dummy"
    CHANNELS = {"crush_progress": (0.0, 0.0, 1.0)}
    SOCKETS = {"grip_torso": (0.62, 1.3), "grip_head": (0.4, 2.5), "seat_hip": (0.0, 0.9)}
    SEGS = [("boots", 0.80, 0.22, 0), ("shins", 0.56, 0.45, 1), ("thighs", 0.72, 0.45, 1),
            ("hips", 0.88, 0.28, 0), ("belly", 0.82, 0.36, 1), ("chest", 1.04, 0.55, 1),
            ("neck", 0.30, 0.14, 0), ("head", 0.72, 0.64, 1)]
    WGT = [0.90, 1.0, 1.0, 0.90, 1.0, 0.80, 0.60, 0.12]      # how much each ring gives way

    def build(self):
        mats = [toon_material("dummy_black", (0.13, 0.13, 0.16)), toon_material("dummy_yellow", (0.98, 0.80, 0.16))]
        self.seg_objs = []
        for i, (nm, w, h, c) in enumerate(self.SEGS):
            if nm == "head":
                pts = ellipse(w / 2, h / 2, 16, 0, h / 2)
            else:
                r = 0.08
                pts = [(-w / 2 + r, 0), (w / 2 - r, 0), (w / 2, r), (w / 2, h - r), (w / 2 - r, h), (-w / 2 + r, h), (-w / 2, h - r), (-w / 2, r)]
            self.seg_objs.append(build_card("dummy." + nm, pts, mats[c], depth=0.10, ink=0.035, parent=self.root, loc=(0, 0, 0)))
        mark = flat_material("dummy_mark", (0.05, 0.05, 0.05))
        self.mark = [build_card("dummy.x%d" % k, rect(-0.16, -0.025, 0.16, 0.025), mark, depth=0.02, ink=0, parent=self.seg_objs[-1],
                                loc=(0.0, -0.07, 0.30), rot_y=(math.pi / 4) * (1 if k else -1)) for k in range(2)]

    def update(self):
        c = self.ch["crush_progress"]
        z = 0.0
        for i, (nm, w, h, col) in enumerate(self.SEGS):
            f = 1.0 - 0.78 * c * self.WGT[i]
            o = self.seg_objs[i]
            bulge = 1.0 + (0.55 if i % 2 else 0.10) * c * (1.0 if nm != "head" else 0.0)
            o.scale = (bulge, 1.0, f)
            o.location = (0.07 * c * (1 if i % 2 else -1), 0.0, z)
            z += h * f
        self.sockets["grip_torso"] = (0.62, lerp(1.3, 0.55, c))
        self.sockets["grip_head"] = (0.4, z - 0.15)
        self.sockets["seat_hip"] = (0.0, lerp(0.9, 0.42, c))
        self.height = z

    def digest(self):
        return super().digest() + (round(self.height, 4),)


# --------------------------------------------------------------------------------------
# TurnbuckleCrankProp
# --------------------------------------------------------------------------------------
class TurnbuckleCrankProp(PropSpec):
    kind = "turnbuckle_crank"
    CHANNELS = {"crank_angle": (0.0, 0.0, 3600.0)}          # degrees
    SOCKETS = {"grip_handle": (0.0, 0.85), "grip_hub": (0.0, 0.0)}
    ARM = 0.85

    def build(self):
        iron = toon_material("turn_iron", (0.30, 0.32, 0.38))
        brass = toon_material("turn_brass", (0.86, 0.66, 0.22))
        red = toon_material("turn_knob", (0.85, 0.18, 0.15))
        self.linked = None
        self.turns = 3.0
        build_card("tb.stand", rect(-0.26, -2.05, 0.26, 0.0), iron, depth=0.30, ink=0.04, parent=self.root, loc=(0, 0.25, 0))
        build_card("tb.foot", rect(-0.9, -2.15, 0.9, -1.95), iron, depth=0.60, ink=0.04, parent=self.root, loc=(0, 0.1, 0))
        build_card("tb.hub", ellipse(0.34, 0.34, 18), brass, depth=0.12, ink=0.04, parent=self.root, loc=(0, -0.10, 0))
        self.arm = new_empty("tb.arm", self.root, (0, -0.2, 0))
        build_card("tb.arm.bar", rect(-0.09, -0.1, 0.09, self.ARM), brass, depth=0.10, ink=0.04, parent=self.arm)
        build_card("tb.arm.knob", ellipse(0.17, 0.17, 14, 0, self.ARM), red, depth=0.14, ink=0.04, parent=self.arm, loc=(0, -0.04, 0))
        self.rod = build_card("tb.rod", rect(0.0, -0.07, 1.0, 0.07), brass, depth=0.14, ink=0.03, parent=self.root, loc=(-1, -0.02, 0))
        self.plates = [build_card("tb.plate%d" % k, rect(-0.12, -0.55, 0.12, 0.55), iron, depth=0.20, ink=0.035, parent=self.root, loc=(0, -0.05, 0))
                       for k in range(2)]

    def link(self, loop, turns=3.0):
        self.linked, self.turns = loop, float(turns)

    def propagate(self, props):
        if self.linked is not None:
            self.linked.set_channel("squeeze_sides", clamp(self.ch["crank_angle"] / (360.0 * self.turns), 0.0, 1.0))

    def update(self):
        th = math.radians(self.ch["crank_angle"])
        self.arm.rotation_euler = (0.0, th, 0.0)
        hx, hz = rot2(0.0, self.ARM, th)
        self.sockets["grip_handle"] = (hx, hz)
        if self.linked is not None:
            xs = []
            for k, name in enumerate(("clamp_ascent", "clamp_descent")):
                wx, wz = self.linked.socket_world(name)
                lx, lz = (wx - self.pos[0]) / self.scale, (wz - self.pos[2]) / self.scale
                self.plates[k].location = (lx, -0.05, lz)
                xs.append(lx)
            x0 = min(xs + [0.0])
            self.rod.location = (x0, -0.02, 0.0)
            self.rod.scale = (max(-x0, 0.01), 1.0, 1.0)


# --------------------------------------------------------------------------------------
# CoasterCartProp
# --------------------------------------------------------------------------------------
class CoasterCartProp(PropSpec):
    kind = "coaster_cart"
    CHANNELS = {"track_progress": (0.0, 0.0, 1.0)}
    SOCKETS = {"seat": (0.0, 0.40), "bar": (0.50, 1.12)}
    WHEEL_R = 0.30

    def build(self):
        body = toon_material("cart_" + self.id, self.opts.get("color", (0.15, 0.62, 0.66)))
        trim = toon_material("cart_trim", (0.93, 0.90, 0.80))
        dark = toon_material("cart_dark", (0.20, 0.21, 0.26))
        self.track, self.on_track, self.wheels = None, False, []
        build_card("cart.chassis", rect(-1.05, 0.26, 1.05, 0.50), dark, depth=0.30, ink=0.035, parent=self.root, loc=(0, 0.0, 0))
        build_card("cart.tub", [(-1.08, 0.45), (1.02, 0.45), (1.26, 0.80), (1.10, 1.02), (-1.04, 1.02)], body, depth=0.14,
                   ink=0.045, parent=self.root, loc=(0, -0.42, 0))
        build_card("cart.stripe", rect(-1.0, 0.72, 1.12, 0.82), trim, depth=0.16, ink=0, parent=self.root, loc=(0, -0.44, 0))
        build_card("cart.back", rect(-0.98, 0.45, -0.38, 1.35), body, depth=0.14, ink=0.04, parent=self.root, loc=(0, 0.16, 0))
        build_card("cart.post", rect(0.45, 0.95, 0.56, 1.14), dark, depth=0.10, ink=0.03, parent=self.root, loc=(0, -0.48, 0))
        build_card("cart.bar", ellipse(0.17, 0.12, 12, 0.50, 1.14), dark, depth=0.12, ink=0.03, parent=self.root, loc=(0, -0.52, 0))
        for k, x in enumerate((-0.62, 0.62)):
            self.wheels.append(build_card("cart.wheel%d" % k, gear(self.WHEEL_R, self.WHEEL_R * 0.78, 8), dark, depth=0.10, ink=0.03,
                                          parent=self.root, loc=(x, -0.22, 0.30)))

    def reset(self):
        super().reset()
        self.track, self.on_track = None, False

    def bind(self, track):
        self.track, self.on_track = track, True

    def marker(self, name):
        return self.track.markers()[name] if self.track else 0.0

    def update(self):
        if not (self.on_track and self.track):
            for w in self.wheels:
                w.rotation_euler = (0.0, 0.0, 0.0)
            return
        path = self.track.get_path()
        u = self.ch["track_progress"]
        p, t = path.at(u)
        wx, wy, wz = self.track.local_to_world(p)
        self.pos = [wx, wy - 0.55 * self.scale, wz]
        self.rot = -math.atan2(t[2], t[0])
        spin = (u * path.length * self.track.scale) / (self.WHEEL_R * self.scale)
        for w in self.wheels:
            w.rotation_euler = (0.0, spin, 0.0)

    def digest(self):
        return super().digest() + (self.on_track,)


PROP_TYPES = {"loop_track": LoopTrackProp, "sledgehammer": SledgehammerProp, "test_dummy": TestDummyProp,
              "turnbuckle_crank": TurnbuckleCrankProp, "coaster_cart": CoasterCartProp}
