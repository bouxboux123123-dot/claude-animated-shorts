"""lib/chars.py  --  LAYER 4 (CHARACTERS)

Flat paper-cutout cards standing in 3D space, each part a thin slab with a black inverted-hull ink line.

    builder : leather apron + flat cap          rival : sharp bowler + suit, tie, twirled moustache

Rig (char-local plane, origin between the feet, height ~3.0, character faces +X):

    root -> hips(lean) -> torso/apron/head(tilt)/face  +  shoulder_R/L -> upper arm -> elbow -> forearm -> hand
    ik_hand_R / ik_hand_L : empties showing the current hand target (debug / hookup point)

Arms are solved with a stateless analytic 2-bone IK, so the pose at frame f depends only on
(target, lean, f).  `flip=-1` mirrors the whole rig (scale.x = -1) so characters can face left.
"""
import math

from . import look
from .look import build_card, capsule, ellipse, flat_material, new_empty, rect, toon_material
from .props import Frame2D, clamp, lerp, rot2

HIPS = (0.0, 1.25)

STYLES = {
    "builder": dict(skin=(0.96, 0.78, 0.62), shirt=(0.82, 0.76, 0.58), pants=(0.30, 0.34, 0.46),
                    boots=(0.28, 0.17, 0.10), tw=0.50, aw=0.25, L1=0.85, L2=0.80, sdx=0.42, hrx=0.46),
    "rival": dict(skin=(0.92, 0.74, 0.60), shirt=(0.14, 0.14, 0.19), pants=(0.11, 0.11, 0.15),
                  boots=(0.05, 0.05, 0.06), tw=0.40, aw=0.20, L1=0.90, L2=0.85, sdx=0.36, hrx=0.40),
}

# brow = (left_deg, right_deg); +left / -right drops the INNER ends (angry), the opposite raises them (worried)
EMOTIONS = {
    "neutral": dict(brow_l=0, brow_r=0, brow_dz=0.00, eye=1.00, lean=0, tilt=0, mouth="flat"),
    "determined": dict(brow_l=20, brow_r=-20, brow_dz=-0.03, eye=0.85, lean=6, tilt=0, mouth="flat"),
    "worried": dict(brow_l=-22, brow_r=22, brow_dz=0.04, eye=1.15, lean=-3, tilt=6, mouth="frown"),
    "shocked": dict(brow_l=-8, brow_r=8, brow_dz=0.09, eye=1.50, lean=-8, tilt=0, mouth="open_o"),
    "smug": dict(brow_l=10, brow_r=-6, brow_dz=0.00, eye=0.70, lean=-2, tilt=-8, mouth="smirk"),
    "laugh": dict(brow_l=-10, brow_r=10, brow_dz=0.05, eye=0.55, lean=-6, tilt=10, mouth="laugh"),
    "panic": dict(brow_l=-26, brow_r=26, brow_dz=0.10, eye=1.60, lean=-10, tilt=0, mouth="wobble"),
    "sad": dict(brow_l=-16, brow_r=16, brow_dz=0.00, eye=0.90, lean=-4, tilt=10, mouth="frown"),
    "proud": dict(brow_l=0, brow_r=0, brow_dz=0.02, eye=0.80, lean=3, tilt=-4, mouth="smile"),
}
NUMERIC = ("brow_l", "brow_r", "brow_dz", "eye", "lean", "tilt")


def blend_expr(a, b, k):
    """Blend two emotion names -> (numeric params, mouth)."""
    ea, eb = EMOTIONS[a], EMOTIONS[b]
    p = {n: lerp(ea[n], eb[n], k) for n in NUMERIC}
    return p, (eb["mouth"] if k >= 0.5 else ea["mouth"])


def _crescent(w, depth, thick, sign=1.0, skew=0.0):
    ts = [i / 6.0 * 2 - 1 for i in range(7)]
    outer = [(t * w, sign * depth * (t * t - 1.0) + skew * t) for t in ts]
    return outer + [(x, z + thick) for x, z in reversed(outer)]


def mouth_shape(name):
    if name == "flat":
        return rect(-0.12, -0.016, 0.12, 0.016)
    if name == "smile":
        return _crescent(0.17, 0.07, 0.035, 1.0)
    if name == "frown":
        return _crescent(0.15, 0.06, 0.035, -1.0)
    if name == "smirk":
        return _crescent(0.15, 0.05, 0.035, 1.0, 0.04)
    if name == "open_o":
        return ellipse(0.085, 0.115, 14)
    if name == "laugh":
        return [(0.21, 0.03), (-0.21, 0.03)] + [(0.21 * math.cos(math.pi * (k / 8.0)) * -1, 0.03 - 0.21 * math.sin(math.pi * (k / 8.0))) for k in range(1, 8)]
    zz = []
    for i in range(9):
        zz.append((-0.16 + 0.04 * i, 0.03 * (1 if i % 2 else -1)))
    return zz + [(x, z + 0.03) for x, z in reversed(zz)]


def dirang(dx, dz):
    return math.atan2(-dx, -dz)       # bone direction = (-sin t, -cos t); t=0 hangs straight down


def solve2(S, T, L1, L2, side):
    """Planar two-bone IK. Returns (theta1, theta2, hand_xz) with the target clamped to reach."""
    dx, dz = T[0] - S[0], T[1] - S[1]
    dl = math.hypot(dx, dz) or 1e-6
    d = clamp(dl, abs(L1 - L2) + 1e-3, L1 + L2 - 1e-3)
    psi = dirang(dx, dz)
    A = math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1.0, 1.0))
    best = None
    for sg in (1.0, -1.0):                      # elbow prefers outward + down
        t1 = psi + sg * A
        E = (S[0] - L1 * math.sin(t1), S[1] - L1 * math.cos(t1))
        score = 0.5 * side * (E[0] - S[0]) - 0.5 * (E[1] - S[1])
        if best is None or score > best[0]:
            best = (score, t1, E)
    _, t1, E = best
    Tc = (S[0] + dx / dl * d, S[1] + dz / dl * d)
    return t1, dirang(Tc[0] - E[0], Tc[1] - E[1]), Tc


class CardChar:
    def __init__(self, cid, style):
        self.id, self.sty, self.style_name = cid, STYLES[style], style
        self.coll = look.new_collection("CHAR_" + cid)
        self.mouths = {}
        with look.into(self.coll):
            self._build()
        self.reset()

    # ------------------------------------------------------------------------------ build
    def _build(self):
        s, cid = self.sty, self.id
        M = lambda n, c: toon_material("%s_%s" % (cid, n), c)
        skin, shirt, pants, boots = M("skin", s["skin"]), M("shirt", s["shirt"]), M("pants", s["pants"]), M("boots", s["boots"])
        ink_flat = flat_material("char_black", (0.02, 0.02, 0.03), 1.0)
        white = toon_material("eye_white", (0.97, 0.97, 0.95))
        card = lambda n, pts, mat, par, loc=(0, 0, 0), d=0.05, ink=0.03, rot=0.0: build_card("%s.%s" % (cid, n), pts, mat, d, ink, par, loc, rot)
        self.root = new_empty(cid + ".root", None, (0, 0, 0), "ARROWS", 0.5)
        for k, x in (("L", -0.24), ("R", 0.24)):
            card("leg" + k, rect(-0.17, 0.2, 0.17, 1.3), pants, self.root, (x, 0.0, 0.0))
            card("boot" + k, [(-0.19, 0.0), (0.34, 0.0), (0.34, 0.14), (0.17, 0.22), (-0.19, 0.22)], boots, self.root, (x, -0.04, 0.0))
        self.hips = new_empty(cid + ".hips", self.root, (HIPS[0], -0.06, HIPS[1]))
        tw = s["tw"]
        card("torso", [(-tw * 0.85, -0.12), (tw * 0.85, -0.12), (tw + 0.08, 0.98), (-tw - 0.08, 0.98)], shirt, self.hips, d=0.06)
        self.head = new_empty(cid + ".head", self.hips, (0.0, -0.04, 0.98))
        hrx = s["hrx"]
        card("neck", rect(-0.14, -0.1, 0.14, 0.18), skin, self.head, (0, 0.04, 0), ink=0.025)
        card("skull", ellipse(hrx, 0.50, 22, 0, 0.52), skin, self.head, d=0.07)
        card("nose", ellipse(0.075, 0.08, 10, 0.02, 0.0), skin, self.head, (0.0, -0.06, 0.46), d=0.04, ink=0.02)
        face_y = -0.075
        self.sclera, self.pupil, self.brow = {}, {}, {}
        for k, x in (("L", -0.17), ("R", 0.17)):
            self.sclera[k] = card("eye" + k, ellipse(0.10, 0.12, 12), white, self.head, (x, face_y, 0.62), d=0.02, ink=0.015)
            self.pupil[k] = card("pupil" + k, ellipse(0.05, 0.05, 8), ink_flat, self.head, (x, face_y - 0.02, 0.62), d=0.02, ink=0)
            self.brow[k] = card("brow" + k, rect(-0.11, -0.022, 0.11, 0.022), ink_flat, self.head, (x, face_y - 0.02, 0.80), d=0.02, ink=0)
        mouth_mat = flat_material("mouth_dark", (0.16, 0.03, 0.04), 1.0)
        for nm in ("flat", "smile", "frown", "smirk", "open_o", "laugh", "wobble"):
            o = card("mouth_" + nm, mouth_shape(nm), mouth_mat, self.head, (0, face_y - 0.02, 0.30), d=0.02, ink=0)
            self.mouths[nm] = o
        (self._acc_builder if self.style_name == "builder" else self._acc_rival)(M, card, skin, shirt)
        self.sh, self.el, self.ik = {}, {}, {}
        for k, side in (("R", 1.0), ("L", -1.0)):
            y = -0.22 if k == "R" else -0.26
            self.sh[k] = new_empty("%s.shoulder%s" % (cid, k), self.hips, (side * s["sdx"], y, 0.88))
            card("upper" + k, capsule(s["aw"], s["L1"]), shirt, self.sh[k], d=0.06)
            self.el[k] = new_empty("%s.elbow%s" % (cid, k), self.sh[k], (0, 0, -s["L1"]))
            card("fore" + k, capsule(s["aw"] * 0.88, s["L2"]), skin, self.el[k], d=0.06)
            card("hand" + k, ellipse(0.17, 0.17, 12), skin, self.el[k], (0, -0.03, -s["L2"] - 0.05), d=0.07)
            self.ik[k] = new_empty("%s.ik_hand_%s" % (cid, k), self.root, (0, 0, 0), "SPHERE", 0.12)

    def _acc_builder(self, M, card, skin, shirt):
        leather, cap, band = M("apron", (0.50, 0.32, 0.18)), M("cap", (0.30, 0.34, 0.40)), M("band", (0.24, 0.16, 0.10))
        card("apron", [(-0.36, 0.92), (0.36, 0.92), (0.46, -0.1), (-0.46, -0.1)], leather, self.hips, (0, -0.07, 0), d=0.05)
        card("pocket", rect(-0.24, 0.08, 0.24, 0.40), band, self.hips, (0, -0.13, 0), d=0.03)
        for k, x in (("L", -0.30), ("R", 0.30)):
            card("strap" + k, [(x - 0.05, 0.88), (x + 0.05, 0.88), (x * 0.5 + 0.05, 0.98), (x * 0.5 - 0.05, 0.98)], band, self.hips, (0, -0.12, 0.0), d=0.03, ink=0.02)
        card("cap", [(-0.50, 0.72), (-0.52, 0.90), (-0.30, 1.06), (0.20, 1.10), (0.48, 1.00), (0.52, 0.84), (0.50, 0.72)], cap, self.head, (0, -0.12, 0), d=0.06)
        card("brim", [(0.20, 0.74), (0.92, 0.70), (0.94, 0.78), (0.30, 0.86)], cap, self.head, (0, -0.13, 0), d=0.05)

    def _acc_rival(self, M, card, skin, shirt):
        black, red, white = M("bowler", (0.08, 0.08, 0.10)), M("tie", (0.80, 0.14, 0.14)), M("shirtw", (0.95, 0.95, 0.92))
        card("shirtV", [(-0.16, 0.98), (0.16, 0.98), (0.0, 0.40)], white, self.hips, (0, -0.07, 0), d=0.03, ink=0.02)
        card("tie", [(-0.06, 0.86), (0.06, 0.86), (0.10, 0.40), (0.0, 0.26), (-0.10, 0.40)], red, self.hips, (0, -0.11, 0), d=0.03, ink=0.02)
        for k, sg in (("L", -1), ("R", 1)):
            card("lapel" + k, [(sg * 0.02, 0.98), (sg * 0.30, 0.96), (sg * 0.14, 0.30)], M("lapel", (0.20, 0.20, 0.27)), self.hips, (0, -0.09, 0), d=0.03, ink=0.02)
            card("mustache" + k, [(0, 0.0), (sg * 0.22, 0.03), (sg * 0.30, 0.13), (sg * 0.24, 0.16), (sg * 0.16, 0.07), (0, 0.06)], black, self.head, (0, -0.10, 0.37), d=0.03, ink=0.015)
        card("crown", [(-0.44, 0.86), (-0.36, 1.10), (0.0, 1.26), (0.36, 1.10), (0.44, 0.86)], black, self.head, (0, -0.12, 0), d=0.07)
        card("hatband", rect(-0.44, 0.86, 0.44, 0.96), red, self.head, (0, -0.15, 0), d=0.03, ink=0.02)
        card("hatbrim", [(-0.74, 0.82), (0.74, 0.82), (0.62, 0.92), (-0.62, 0.92)], black, self.head, (0, -0.14, 0), d=0.05)

    # ------------------------------------------------------------------------------ state
    def reset(self):
        self.pos, self.rot, self.scale, self.flip, self.visible = [0.0, 0.0, 0.0], 0.0, 1.0, 1.0, False
        self.params, self.mouth = dict(EMOTIONS["neutral"]), "flat"
        self.lean_extra = self.tilt_extra = 0.0
        self.arm = {"R": (0.0, 0.0), "L": (0.0, 0.0)}
        self.target = {"R": (0.0, 0.0), "L": (0.0, 0.0)}

    def frame(self):
        return Frame2D(self.pos, self.rot, self.scale, self.flip)

    @property
    def lean(self):
        return math.radians(self.params["lean"] + self.lean_extra)

    def shoulder_local(self, side):
        sx = self.sty["sdx"] * (1.0 if side == "R" else -1.0)
        x, z = rot2(sx, 0.88, self.lean)
        return HIPS[0] + x, HIPS[1] + z

    def shoulder_world(self, side):
        return self.frame().to_world(*self.shoulder_local(side))

    def idle_local(self, side, t):
        S = self.shoulder_local(side)
        sg = 1.0 if side == "R" else -1.0
        r = (self.sty["L1"] + self.sty["L2"]) * 0.90
        sway = 0.05 * math.sin(2 * math.pi * t / 2.4 + (0.0 if side == "R" else 1.7))
        return S[0] + sg * 0.16 + sway, S[1] - r

    def solve_arm(self, side, world_target):
        """Aim `side` hand at a world point; returns the ACTUAL hand world position (clamped to reach)."""
        fr = self.frame()
        T = fr.to_local(*world_target)
        S = self.shoulder_local(side)
        t1, t2, H = solve2(S, T, self.sty["L1"], self.sty["L2"], 1.0 if side == "R" else -1.0)
        self.arm[side], self.target[side] = (t1, t2), T
        return fr.to_world(*H)

    def commit(self):
        self.root.location = self.pos
        self.root.rotation_euler = (0.0, self.rot, 0.0)
        self.root.scale = (self.flip * self.scale, self.scale, self.scale)
        self.coll.hide_render = not self.visible
        self.coll.hide_viewport = not self.visible
        lean = self.lean
        self.hips.rotation_euler = (0.0, lean, 0.0)
        self.head.rotation_euler = (0.0, math.radians(self.params["tilt"] + self.tilt_extra), 0.0)
        e = self.params["eye"]
        for k in ("L", "R"):
            self.sclera[k].scale = (e, 1.0, e)
            self.brow[k].location = (self.brow[k].location[0], self.brow[k].location[1], 0.80 + self.params["brow_dz"])
        self.brow["L"].rotation_euler = (0.0, math.radians(self.params["brow_l"]), 0.0)
        self.brow["R"].rotation_euler = (0.0, math.radians(self.params["brow_r"]), 0.0)
        for nm, o in self.mouths.items():
            o.hide_render = (nm != self.mouth)
            o.hide_viewport = (nm != self.mouth)
        for k in ("R", "L"):
            t1, t2 = self.arm[k]
            self.sh[k].rotation_euler = (0.0, t1 - lean, 0.0)
            self.el[k].rotation_euler = (0.0, t2 - t1, 0.0)
            self.ik[k].location = (self.target[k][0], -0.4, self.target[k][1])

    def digest(self):
        r = lambda v: round(v, 4)
        return (self.id, self.visible, tuple(r(v) for v in self.pos), r(self.rot), r(self.scale), self.flip,
                tuple(r(self.params[n]) for n in NUMERIC), self.mouth, tuple(r(v) for k in "RL" for v in self.arm[k]))
