"""props.py - PropSpec base class, closed-form 2-bone IK, hero props.

Every hero prop inherits PropSpec, owns normalized [0..1] channels and named
Empty sockets. Channels listed in `hand_driven` may only CHANGE while a
character holds/clasps one of the listed sockets; the engine raises
PropAssertionError otherwise (checked per frame and again at compile time).
"""
import math
from collections import namedtuple

from lib import look, sets

PI = math.pi
EPS = 1e-9


class PropAssertionError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Closed-form, stateless, analytic planar 2-bone IK ------------------------
# --------------------------------------------------------------------------
IK = namedtuple("IK", "a1 a2 elbow hand err reachable")


def solve2(S, T, L1, L2, side):
    """Planar 2-bone IK. S shoulder (x,z), T target (x,z).
    Angles are absolute, CCW from +X. side=+1 bends the elbow CCW of the
    shoulder->target line (elbow above/left), side=-1 CW (elbow below/right).
    Out-of-range targets clamp along the shoulder->target ray (reachable=False)."""
    dx, dz = T[0] - S[0], T[1] - S[1]
    dist = math.hypot(dx, dz)
    dmax, dmin = L1 + L2 - 1e-6, abs(L1 - L2) + 1e-6
    d = min(max(dist, dmin), dmax)
    base = math.atan2(dz, dx) if dist > EPS else -PI / 2
    cosA = max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))
    a1 = base + side * math.acos(cosA)
    ex, ez = S[0] + L1 * math.cos(a1), S[1] + L1 * math.sin(a1)
    tcx, tcz = S[0] + d * math.cos(base), S[1] + d * math.sin(base)
    a2 = math.atan2(tcz - ez, tcx - ex)
    hx, hz = ex + L2 * math.cos(a2), ez + L2 * math.sin(a2)
    return IK(a1, a2, (ex, ez), (hx, hz), math.hypot(hx - T[0], hz - T[1]), dmin <= dist <= dmax)


# --------------------------------------------------------------------------
# PropSpec -----------------------------------------------------------------
# --------------------------------------------------------------------------
def P(name, poly, color, pos=(0.0, 0.0), order=0, ink=0.02):
    return dict(name=name, poly=poly, color=color, pos=pos, order=order, ink=ink)


class PropSpec:
    defaults = {}      # channel -> default in [0,1]
    hand_driven = {}   # channel -> tuple of sockets that must be grasped to move it
    sockets = {}       # socket -> (x, z) local rest position

    def __init__(self, name, home):
        for ch, v in self.defaults.items():
            assert 0.0 <= v <= 1.0, f"{name}.{ch} default outside [0,1]"
        for ch, socks in self.hand_driven.items():
            assert ch in self.defaults and all(s in self.sockets for s in socks), f"{name}: bad hand_driven {ch}"
        self.name, self.home = name, tuple(home)
        self.rig = None
        self.reset()

    # ----- pure state -----
    def reset(self):
        self.values = dict(self.defaults)
        self.root, self.mirror = self.home, 1.0

    def clamp(self, ch, v):
        if ch not in self.defaults:
            raise KeyError(f"{self.name} has no channel '{ch}'")
        return min(1.0, max(0.0, float(v)))

    def pose(self, v):                       # whole-prop pose about root: (dx, dz, rot_ccw)
        return (0.0, 0.0, 0.0)

    def socket_local(self, socket, v):
        return self.sockets[socket]

    def part_pose(self, v):                  # {part: (dx, dz, rot_ccw)}
        return {}

    def socket_world(self, socket, v=None, root=None, mirror=None):
        v = self.values if v is None else v
        root = self.root if root is None else root
        m = self.mirror if mirror is None else mirror
        px, pz, rot = self.pose(v)
        lx, lz = self.socket_local(socket, v)
        c, s = math.cos(rot), math.sin(rot)
        return (root[0] + m * (lx * c - lz * s + px), root[1], root[2] + lx * s + lz * c + pz)

    def check_motion(self, frame, prev, cur, held_sockets):
        """HARD ASSERTION: hand-driven channel moved without a grasp."""
        for ch, need in self.hand_driven.items():
            if abs(cur[ch] - prev[ch]) > 1e-9 and not (set(need) & set(held_sockets)):
                raise PropAssertionError(
                    f"frame {frame}: prop '{self.name}' channel '{ch}' moved ({prev[ch]:.4f}->{cur[ch]:.4f}) "
                    f"but no character grasps any of {need}")

    # ----- geometry -----
    def parts(self):
        return []

    def build(self):
        coll = look.get_collection("PROP:" + self.name)
        root = look.empty(f"P:{self.name}", coll=coll)
        pose = look.empty(f"P:{self.name}.pose", root, coll=coll)
        parts = {}
        for p in self.parts():
            o = look.make_prism(f"{self.name}.{p['name']}", p["poly"], p["color"], coll, (0, 0, 0), 0.03, p["ink"])
            o.parent = pose
            parts[p["name"]] = (o, p)
        socks = {s: look.empty(f"S:{self.name}.{s}", pose, coll=coll) for s in self.sockets}
        self.rig = dict(root=root, pose=pose, parts=parts, socks=socks, coll=coll)
        self.build_extra(coll, pose)
        return self

    def build_extra(self, coll, pose):
        pass

    def apply_bpy(self, v, root, mirror):
        r = self.rig
        r["root"].location = root
        r["root"].scale = (mirror, 1, 1)
        px, pz, rot = self.pose(v)
        r["pose"].location = (px, 0, pz)
        r["pose"].rotation_euler = (0, -rot, 0)
        pp = self.part_pose(v)
        for name, (o, p) in r["parts"].items():
            dx, dz, rr = pp.get(name, (0, 0, 0))
            o.location = (p["pos"][0] + dx, -0.012 * p["order"], p["pos"][1] + dz)
            o.rotation_euler = (0, -rr, 0)
        for s, e in r["socks"].items():
            lx, lz = self.socket_local(s, v)
            e.location = (lx, 0, lz)
        self.apply_extra(v)

    def apply_extra(self, v):
        pass


# --------------------------------------------------------------------------
# Hero props ---------------------------------------------------------------
# --------------------------------------------------------------------------
class PrintingPress(PropSpec):
    defaults = {"crank": 0.0}
    hand_driven = {"crank": ("grip_main",)}
    AXLE, R, TURNS = (-1.0, 1.2), 0.3, 3

    sockets = {"grip_main": (-1.0, 0.9)}      # rest value; socket_local() orbits the axle

    def _theta(self, v):
        return -PI / 2 + v["crank"] * self.TURNS * 2 * PI

    def socket_local(self, socket, v):
        t = self._theta(v)
        return (self.AXLE[0] + self.R * math.cos(t), self.AXLE[1] + self.R * math.sin(t))

    def part_pose(self, v):
        t = self._theta(v)
        return {"crank_arm": (0, 0, t), "knob": (self.R * math.cos(t), self.R * math.sin(t), 0),
                "sheet": (v["crank"] * 0.5, 0, 0), "roller": (0, 0, v["crank"] * 6.0)}

    def parts(self):
        ax = self.AXLE
        return [P("base", look.rect_poly(2.2, .7), "iron_dark", (0, .35), 0),
                P("body", look.rect_poly(1.5, .9), "iron", (0, 1.15), 1),
                P("top", look.rect_poly(1.8, .25), "iron_dark", (0, 1.7), 2),
                P("roller", look.ellipse_poly(.3, .3, 18), "brass", (.2, 1.15), 2),
                P("shaft", look.rect_poly(.25, .12), "brass", (-.88, 1.2), 2),
                P("hub", look.ellipse_poly(.12, .12, 12), "brass", ax, 3),
                P("crank_arm", look.rect_poly(self.R, .1, self.R / 2, 0), "iron", ax, 4),
                P("knob", look.ellipse_poly(.1, .1, 12), "wood", ax, 5),
                P("sheet", look.rect_poly(.7, .05), "paper", (1.2, 1.0), 3, 0.01),
                P("stack", look.rect_poly(.6, .25), "green", (1.45, .55), 3)]


class PressLever(PropSpec):
    defaults = {"pull": 0.0}
    hand_driven = {"pull": ("grip_main",)}
    PIVOT, LEN = (0.0, 0.6), 0.8
    sockets = {"grip_main": (-0.139, 1.388)}  # rest value; socket_local() sweeps an arc

    def _phi(self, v):
        return math.radians(100 - 80 * v["pull"])

    def socket_local(self, socket, v):
        p = self._phi(v)
        return (self.PIVOT[0] + self.LEN * math.cos(p), self.PIVOT[1] + self.LEN * math.sin(p))

    def part_pose(self, v):
        p = self._phi(v)
        return {"arm": (0, 0, p - PI / 2), "ball": (self.LEN * math.cos(p), self.LEN * math.sin(p), 0)}

    def parts(self):
        return [P("plate", look.rect_poly(.6, .15), "iron_dark", (0, .075), 0),
                P("post", look.rect_poly(.12, .5), "iron", (0, .35), 1),
                P("arm", look.rect_poly(.09, self.LEN, 0, self.LEN / 2), "wood", self.PIVOT, 2),
                P("ball", look.ellipse_poly(.1, .1, 12), "red", self.PIVOT, 3)]


class Hammer(PropSpec):
    defaults = {"swing": 0.0}
    hand_driven = {"swing": ("grip_main",)}
    sockets = {"grip_main": (0.0, -0.2)}

    def pose(self, v):                       # raised-back (225 deg) -> strike (45 deg)
        return (0.0, 0.0, math.radians(225 - 180 * v["swing"]))

    def parts(self):
        return [P("handle", look.rect_poly(.07, .6, 0, -.3), "wood", (0, 0), 0),
                P("grip", look.rect_poly(.1, .18), "red", (0, -.2), 1),
                P("head", look.rect_poly(.38, .2), "iron", (0, -.6), 1)]


class CashStack(PropSpec):
    defaults = {"slam": 0.0, "wilt": 0.0}
    hand_driven = {"slam": ("grip_main", "grip_twohand_L", "grip_twohand_R")}
    sockets = {"grip_main": (0.0, 0.1), "grip_twohand_L": (-0.22, 0.12), "grip_twohand_R": (0.22, 0.12)}
    DROP = 0.45

    def pose(self, v):
        return (0.0, -self.DROP * v["slam"], 0.0)

    def part_pose(self, v):
        w = v["wilt"]
        return {f"bill{i}": (w * 0.05 * (i - 2), -w * 0.01 * i, w * 0.14 * (i - 2)) for i in range(5)}

    def parts(self):
        out = [P(f"bill{i}", look.rect_poly(.56, .05), ("green", "green_dark")[i % 2], (0, .025 + .05 * i), i, 0.008) for i in range(5)]
        out.append(P("band", look.rect_poly(.1, .27), "paper", (0, .13), 6, 0.008))
        return out


class Loaf(PropSpec):
    defaults = {"bounce": 0.0}
    hand_driven = {}
    sockets = {"grip_main": (0.28, 0.03), "grip_twohand_L": (-0.3, 0.04), "grip_twohand_R": (0.3, 0.04)}

    def pose(self, v):
        return (0.0, 0.12 * math.sin(PI * v["bounce"]), 0.0)

    def parts(self):
        out = [P("body", look.ellipse_poly(.4, .17, 22), "crust", (0, 0), 0)]
        out += [P(f"score{i}", look.rect_poly(.03, .12), "cream", (-.16 + .16 * i, .03), 1, 0.004) for i in range(3)]
        return out


class PriceBoard(PropSpec):
    defaults = {"price": 0.0}
    hand_driven = {}
    sockets = {"face": (0.0, 1.15)}
    LABELS = ("$1", "$1,000", "$10,000", "$100,000", "$1,000,000")

    def label(self, v):
        return self.LABELS[int(round(v["price"] * (len(self.LABELS) - 1)))]

    def parts(self):
        return [P("legL", look.rect_poly(.1, .65), "wood_dark", (-.6, .325), 0),
                P("legR", look.rect_poly(.1, .65), "wood_dark", (.6, .325), 0),
                P("frame", look.rect_poly(1.75, 1.15), "wood", (0, 1.2), 1),
                P("surface", look.rect_poly(1.6, 1.0), "board", (0, 1.2), 2, 0.01)]

    def build_extra(self, coll, pose):
        t = look.make_text(f"{self.name}.text", self.LABELS[0], (0, -0.05, 1.2), 0.3, "chalk", coll)
        t.parent = pose
        self.rig["text"] = t

    def apply_extra(self, v):
        self.rig["text"].data.body = self.label(v)


class MoneyRain(PropSpec):
    defaults = {"fall": 0.0}
    hand_driven = {}
    sockets = {"center": (0.0, 0.0)}
    N = 28

    def part_pose(self, v):
        out = {}
        for i in range(self.N):
            x0 = ((i * 53) % 100) / 100 * 2.4 - 1.2
            delay = ((i * 29) % 100) / 100 * 0.45
            spin = ((i * 17) % 100) / 100 * 6 - 3
            tn = min(1.0, max(0.0, (v["fall"] - delay) / 0.55))
            if v["fall"] <= delay:
                out[f"bill{i}"] = (x0, 60.0, 0.0)
            else:
                z = 14.0 * (1 - tn * tn) + 0.04 + (i % 4) * 0.03
                out[f"bill{i}"] = (x0 + 0.4 * math.sin(tn * 6 + i) * (1 - tn), z, spin * tn)
        return out

    def parts(self):
        return [P(f"bill{i}", look.rect_poly(.36, .18), ("green", "green_dark")[i % 2], (0, 0), i % 6, 0.008) for i in range(self.N)]


class Stove(PropSpec):
    defaults = {"burn": 0.0}
    hand_driven = {}
    sockets = {"mouth": (-0.45, 0.55)}

    def part_pose(self, v):
        b = v["burn"]
        return {"flame": (0, 0 if b > 0.02 else -5.0, 0.12 * math.sin(b * 60)),
                "flame2": (0.08, 0 if b > 0.3 else -5.0, -0.12 * math.sin(b * 47))}

    def parts(self):
        return [P("body", look.rect_poly(1.0, 1.2), "iron_dark", (0, .6), 0),
                P("door", look.rect_poly(.5, .4), "black", (0, .55), 1),
                P("flame", look.ellipse_poly(.2, .3, 12), "fire", (0, .55), 2, 0),
                P("flame2", look.ellipse_poly(.12, .2, 12), "yellow", (0, .52), 3, 0),
                P("pipe", look.rect_poly(.18, 1.6), "iron", (.3, 2.0), 0),
                P("lid", look.rect_poly(1.1, .1), "iron", (0, 1.25), 1)]


def make_props():
    R = sets.REG
    return {
        "press": PrintingPress("press", R.get("workshop.press")),
        "lever": PressLever("lever", R.get("workshop.lever")),
        "hammer": Hammer("hammer", R.get("bakery.hammer_home")),
        "cash": CashStack("cash", R.get("bakery.cash_home")),
        "loaf": Loaf("loaf", R.get("island.loaf_home")),
        "board": PriceBoard("board", R.get("bakery.board")),
        "rain": MoneyRain("rain", R.get("island.doorstep")),
        "stove": Stove("stove", R.get("street.stove")),
    }
