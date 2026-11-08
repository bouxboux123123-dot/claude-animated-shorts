"""lib/sets.py  --  LAYER 3 (SETS)

Three modular sets, each a SetSpec that owns one collection and registers named anchors:

    workshop_night   'ws.*'   night workshop: bench, blueprint, window, hanging tungsten lamps
    fairground_dawn  'fg.*'   opening-morning fairground: booth, bunting, ferris wheel, queue of townsfolk
    coaster_climax   'cc.*'   open hillside under the two loops, spectators, big sky

Anchors are the ONLY thing shots.json / acting.json / look.py use to refer to places.  Hero props and
characters are NOT part of a set; shots.json 'stage' decides which set anchor each one stands on.
"""
import math
import random

from . import look
from .look import (build_card, capsule, ellipse, flat_material, new_empty, rect,
                   toon_material)


class AnchorRegistry:
    def __init__(self):
        self._a, self._owner = {}, {}

    def register(self, name, xyz, set_name=None):
        self._a[name] = tuple(float(v) for v in xyz)
        self._owner[name] = set_name

    def get(self, name):
        if name not in self._a:
            raise KeyError("unknown anchor '%s' (have: %s)" % (name, ", ".join(sorted(self._a))))
        return self._a[name]

    def names(self, prefix=""):
        return sorted(n for n in self._a if n.startswith(prefix))

    def owner(self, name):
        return self._owner.get(name)


ANCHORS = AnchorRegistry()


class SetSpec:
    name, prefix = "", ""

    def __init__(self):
        self.coll = look.new_collection("SET_" + self.name)
        self.markers = {}
        with look.into(self.coll):
            self.build()
            for key, xyz in self.markers.items():          # visible anchor empties (debug only)
                new_empty("anchor.%s.%s" % (self.prefix, key), None, xyz, "SPHERE", 0.2)
        self.set_visible(False)

    def anchor(self, key, xyz):
        ANCHORS.register("%s.%s" % (self.prefix, key), xyz, self.name)
        self.markers[key] = tuple(xyz)

    def set_visible(self, v):
        self.coll.hide_render = not v
        self.coll.hide_viewport = not v

    def build(self):
        raise NotImplementedError


# --------------------------------------------------------------------------------------
def slab(name, pts, mat, y=0.0, depth=0.3, ink=0.0, x=0.0, z=0.0, rot_y=0.0):
    return build_card(name, pts, mat, depth=depth, ink=ink, loc=(x, y, z), rot_y=rot_y)


def npc(prefix, x, y, scale, body_rgb, hat_rgb, skin_rgb, kind):
    """Static townsfolk cut-out (capsule body + round head + hat)."""
    body = toon_material("npc_b_%02d%02d%02d" % tuple(int(c * 9) for c in body_rgb), body_rgb)
    hat = toon_material("npc_h_%02d%02d%02d" % tuple(int(c * 9) for c in hat_rgb), hat_rgb)
    skin = toon_material("npc_skin_%02d%02d%02d" % tuple(int(c * 9) for c in skin_rgb), skin_rgb)
    s = scale
    pts = [(-0.42 * s, 0), (0.42 * s, 0), (0.34 * s, 1.35 * s), (-0.34 * s, 1.35 * s)]
    slab(prefix + ".body", pts, body, y=y, depth=0.12, ink=0.03, x=x)
    slab(prefix + ".head", ellipse(0.34 * s, 0.36 * s, 14, 0, 1.70 * s), skin, y=y - 0.03, depth=0.12, ink=0.03, x=x)
    if kind == 0:     # flat cap
        slab(prefix + ".hat", [(-0.36 * s, 1.88 * s), (0.36 * s, 1.88 * s), (0.30 * s, 2.06 * s), (-0.26 * s, 2.06 * s)], hat, y=y - 0.06, depth=0.12, ink=0.03, x=x)
    elif kind == 1:   # top hat
        slab(prefix + ".hat", rect(-0.22 * s, 1.92 * s, 0.22 * s, 2.38 * s), hat, y=y - 0.06, depth=0.12, ink=0.03, x=x)
        slab(prefix + ".brim", rect(-0.38 * s, 1.88 * s, 0.38 * s, 1.96 * s), hat, y=y - 0.07, depth=0.12, ink=0.03, x=x)
    else:             # sun bonnet / pigtails
        slab(prefix + ".hat", ellipse(0.40 * s, 0.22 * s, 12, 0, 1.96 * s), hat, y=y - 0.06, depth=0.12, ink=0.03, x=x)


NPC_BODIES = [(0.82, 0.30, 0.28), (0.28, 0.52, 0.78), (0.95, 0.78, 0.25), (0.40, 0.70, 0.40), (0.70, 0.40, 0.72), (0.95, 0.55, 0.25)]
NPC_SKINS = [(0.96, 0.78, 0.62), (0.80, 0.56, 0.40), (0.62, 0.42, 0.30), (0.98, 0.84, 0.70)]


def crowd(prefix, xs, y, seed, scale=0.62):
    rng = random.Random(seed)
    for i, x in enumerate(xs):
        npc("%s.%02d" % (prefix, i), x, y + rng.uniform(-0.5, 0.5), scale * rng.uniform(0.9, 1.15),
            NPC_BODIES[rng.randrange(len(NPC_BODIES))], NPC_BODIES[rng.randrange(len(NPC_BODIES))],
            NPC_SKINS[rng.randrange(len(NPC_SKINS))], rng.randrange(3))


def outdoor_backdrop(prefix, y_far=42.0):
    """Ground, rolling hills, low sun disc: shared by the two daylight sets."""
    grass = toon_material("fg_grass", (0.36, 0.62, 0.30))
    path = toon_material("fg_path", (0.80, 0.68, 0.48))
    far = toon_material("fg_hill_far", (0.52, 0.64, 0.66))
    mid = toon_material("fg_hill_mid", (0.40, 0.62, 0.42))
    sun = flat_material("fg_sun_disc", (1.0, 0.86, 0.55), 1.0)
    slab(prefix + ".ground", rect(-90, -1, 90, 0), grass, y=0, depth=90)
    slab(prefix + ".path", rect(-90, -0.12, 90, 0.02), path, y=-5.5, depth=7.5)
    for i, (cx, rx, rz, m, yy) in enumerate([(-38, 30, 9, far, y_far + 14), (14, 34, 11, far, y_far + 10),
                                              (52, 28, 8, far, y_far + 12), (-16, 24, 6, mid, y_far - 6),
                                              (30, 26, 5, mid, y_far - 8)]):
        slab("%s.hill%d" % (prefix, i), ellipse(rx, rz, 30, cx, 0), m, y=yy, depth=0.6)
    slab(prefix + ".sun", ellipse(3.0, 3.0, 28, -26, 10.5), sun, y=y_far + 30, depth=0.2)


def ferris_wheel(prefix, cx, cz, r, y):
    steel = toon_material("fw_steel", (0.88, 0.86, 0.82))
    cab = [toon_material("fw_cab%d" % i, c) for i, c in enumerate([(0.86, 0.28, 0.25), (0.26, 0.54, 0.84), (0.96, 0.78, 0.22)])]
    n_rim = 28
    seg = 2 * math.pi * r / n_rim * 1.08
    for i in range(n_rim):
        a = 2 * math.pi * i / n_rim
        slab("%s.rim%02d" % (prefix, i), rect(-seg / 2, -0.12, seg / 2, 0.12), steel, y=y, depth=0.2,
             x=cx + r * math.cos(a), z=cz + r * math.sin(a), rot_y=-math.atan2(math.cos(a), -math.sin(a)))
    for i in range(12):
        a = 2 * math.pi * i / 12
        slab("%s.spoke%02d" % (prefix, i), rect(0, -0.07, r, 0.07), steel, y=y + 0.1, depth=0.15, x=cx, z=cz, rot_y=-a)
        slab("%s.cab%02d" % (prefix, i), rect(-0.5, -1.0, 0.5, -0.1), cab[i % 3], y=y - 0.1, depth=0.3, ink=0.03,
             x=cx + r * math.cos(a), z=cz + r * math.sin(a))
    slab(prefix + ".legL", [(cx - 0.4, cz), (cx + 0.4, cz), (cx - 4.5, 0), (cx - 6.0, 0)], steel, y=y + 0.3, depth=0.3)
    slab(prefix + ".legR", [(cx - 0.4, cz), (cx + 0.4, cz), (cx + 6.0, 0), (cx + 4.5, 0)], steel, y=y + 0.3, depth=0.3)


def bunting(prefix, x0, x1, z, y, n=14):
    cols = [toon_material("bunt%d" % i, c) for i, c in enumerate([(0.9, 0.25, 0.25), (0.98, 0.82, 0.25), (0.25, 0.6, 0.9), (0.95, 0.95, 0.9)])]
    pole = toon_material("bunt_pole", (0.5, 0.36, 0.22))
    for xx in (x0, x1):
        slab("%s.pole%d" % (prefix, int(xx)), rect(-0.12, 0, 0.12, z + 0.4), pole, y=y, depth=0.25, ink=0.03, x=xx)
    for i in range(n):
        t = (i + 0.5) / n
        slab("%s.flag%02d" % (prefix, i), [(-0.30, 0), (0.30, 0), (0, -0.75)], cols[i % 4], y=y - 0.05, depth=0.05, ink=0.02,
             x=x0 + (x1 - x0) * t, z=z - 0.9 * math.sin(math.pi * t) + 0.35)


# --------------------------------------------------------------------------------------
class WorkshopNight(SetSpec):
    name, prefix = "workshop_night", "ws"

    def build(self):
        floor = toon_material("ws_floor", (0.34, 0.24, 0.16))
        pa, pb = toon_material("ws_plank_a", (0.46, 0.35, 0.26)), toon_material("ws_plank_b", (0.40, 0.30, 0.22))
        dark = toon_material("ws_dark", (0.22, 0.16, 0.12))
        paper = toon_material("ws_paper", (0.80, 0.88, 0.96))
        steel = toon_material("ws_steel", (0.56, 0.60, 0.66))
        crate = toon_material("ws_crate", (0.60, 0.44, 0.26))
        glass = flat_material("ws_glass", (0.30, 0.45, 0.90), 1.0)
        moon = flat_material("ws_moon", (0.92, 0.96, 1.0), 1.0)
        bulb = flat_material("ws_bulb", (1.0, 0.82, 0.45), 1.0)
        slab("ws.floor", rect(-40, -1, 40, 0), floor, y=0, depth=40)
        for i in range(-12, 13):
            slab("ws.plank%+03d" % i, rect(i * 3.0 - 1.5, 0, i * 3.0 + 1.47, 12.6), pa if i % 2 else pb, y=7.0, depth=0.4)
        slab("ws.beam", rect(-40, 10.8, 40, 12.2), dark, y=5.5, depth=3.0)
        for x in (-14, 0, 14):
            slab("ws.post%d" % x, rect(-0.35, 0, 0.35, 11.0), dark, y=6.2, depth=0.6, x=x)
        # window with moon
        slab("ws.win.frame", rect(-12.2, 4.0, -7.8, 9.4), dark, y=6.55, depth=0.2, ink=0.04)
        slab("ws.win.glass", rect(-11.9, 4.3, -8.1, 9.1), glass, y=6.40, depth=0.1)
        slab("ws.win.moon", ellipse(0.8, 0.8, 24, -9.6, 7.9), moon, y=6.33, depth=0.05)
        slab("ws.win.mullV", rect(-10.08, 4.3, -9.92, 9.1), dark, y=6.30, depth=0.08)
        slab("ws.win.mullH", rect(-11.9, 6.62, -8.1, 6.78), dark, y=6.30, depth=0.08)
        # bench + tools
        slab("ws.bench.top", rect(-13.5, 2.5, -6.8, 2.95), dark, y=3.2, depth=2.8, ink=0.04)
        for x in (-13.2, -7.1):
            slab("ws.bench.leg%d" % x, rect(-0.2, 0, 0.2, 2.5), dark, y=3.2, depth=0.5, ink=0.03, x=x)
        slab("ws.bench.vice", rect(-8.2, 2.95, -7.4, 3.45), steel, y=2.5, depth=0.5, ink=0.03)
        for i, (x, w) in enumerate([(-12.6, 0.9), (-11.4, 0.6), (-10.4, 1.1)]):
            slab("ws.bench.tool%d" % i, rect(x, 2.95, x + w, 3.2 + 0.1 * i), steel, y=2.2, depth=0.2, ink=0.03)
        # blueprint
        slab("ws.blueprint", rect(-1.8, 5.0, 3.8, 9.2), paper, y=6.5, depth=0.06, ink=0.03)
        line = flat_material("ws_bp_line", (0.25, 0.40, 0.70), 1.0)
        for k in range(5):
            slab("ws.bp.line%d" % k, rect(-1.4, 5.5 + 0.7 * k, 3.4 - 0.4 * k, 5.58 + 0.7 * k), line, y=6.44, depth=0.03)
        slab("ws.bp.loop", ellipse(1.1, 1.1, 24, 1.0, 7.4), line, y=6.45, depth=0.03)
        slab("ws.bp.hole", ellipse(0.95, 0.95, 24, 1.0, 7.4), paper, y=6.43, depth=0.03)
        # crates / barrels (right)
        slab("ws.crate1", rect(10.5, 0, 12.6, 2.1), crate, y=3.0, depth=1.6, ink=0.04)
        slab("ws.crate2", rect(12.6, 0, 14.4, 1.6), crate, y=3.2, depth=1.4, ink=0.04)
        slab("ws.crate3", rect(11.0, 2.1, 12.4, 3.2), crate, y=3.0, depth=1.2, ink=0.04)
        # hanging lamps (bulb meshes; the real 500 W lights are placed by look.build_lighting_rigs)
        for tag, x in (("L", -6.5), ("R", 6.0)):
            slab("ws.lamp%s.cord" % tag, rect(-0.04, 8.4, 0.04, 12.6), dark, y=1.5, depth=0.06, x=x)
            slab("ws.lamp%s.shade" % tag, [(-0.9, 7.6), (0.9, 7.6), (0.35, 8.5), (-0.35, 8.5)], dark, y=1.5, depth=0.3, ink=0.04, x=x)
            slab("ws.lamp%s.bulb" % tag, ellipse(0.38, 0.38, 16, 0, 7.55), bulb, y=1.4, depth=0.1, x=x)
        self.anchor("lamp_L", (-6.5, 1.5, 7.8))
        self.anchor("lamp_R", (6.0, 1.5, 7.8))
        self.anchor("track_stand", (0.0, 0.0, 0.0))
        self.anchor("builder_work", (-2.75, -1.6, 0.0))
        self.anchor("builder_bench", (-9.0, -1.9, 0.0))
        self.anchor("builder_idle", (-4.2, -1.8, 0.0))
        self.anchor("cart_spot", (-5.0, -0.8, 0.15))
        self.anchor("dummy_in_cart", (-5.0, -0.85, 0.55))
        self.anchor("bench_hammer", (-9.6, -0.6, 3.0))
        self.anchor("crank", (4.9, -1.0, 2.0))
        self.anchor("rival_crank", (5.9, -2.3, 0.0))
        self.anchor("rival_door", (12.5, -2.0, 0.0))
        self.anchor("rival_mid", (9.0, -2.2, 0.0))
        self.anchor("rival_window", (-10.0, -2.2, 0.0))


class FairgroundDawn(SetSpec):
    name, prefix = "fairground_dawn", "fg"

    def build(self):
        outdoor_backdrop("fg")
        red, white = toon_material("fg_red", (0.86, 0.26, 0.24)), toon_material("fg_white", (0.96, 0.94, 0.88))
        wood, dark = toon_material("fg_wood", (0.62, 0.44, 0.26)), toon_material("fg_dark", (0.24, 0.20, 0.18))
        ferris_wheel("fg.wheel", 26.0, 12.0, 8.5, 26.0)
        bunting("fg.bunt1", -30, -4, 6.4, 3.0)
        bunting("fg.bunt2", 6, 24, 6.0, 3.0, n=11)
        # ticket booth
        slab("fg.booth.body", rect(8.0, 0, 12.2, 3.3), wood, y=2.0, depth=1.6, ink=0.04)
        slab("fg.booth.roof", [(7.6, 3.3), (12.6, 3.3), (12.2, 4.3), (8.0, 4.3)], red, y=1.9, depth=2.0, ink=0.04)
        slab("fg.booth.hole", rect(9.0, 1.3, 11.2, 2.7), dark, y=1.18, depth=0.1)
        for i in range(5):
            slab("fg.booth.awn%d" % i, rect(8.0 + i * 0.84, 2.8, 8.0 + (i + 1) * 0.84, 3.3), red if i % 2 == 0 else white, y=1.1, depth=0.12, ink=0.02)
        # opening-day arch
        slab("fg.arch.postL", rect(-0.2, 0, 0.2, 6.0), wood, y=-3.0, depth=0.4, ink=0.04, x=-1.5)
        slab("fg.arch.postR", rect(-0.2, 0, 0.2, 6.0), wood, y=-3.0, depth=0.4, ink=0.04, x=4.5)
        slab("fg.arch.banner", rect(-1.9, 5.0, 4.9, 6.3), red, y=-3.1, depth=0.12, ink=0.04)
        slab("fg.arch.star", [(1.5 + 0.55 * math.cos(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45),
                               5.65 + 0.55 * math.sin(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45)) for k in range(10)],
             toon_material("fg_gold", (0.98, 0.82, 0.25)), y=-3.2, depth=0.06)
        # anchors (loops are placed first; stations are derived from them)
        rl, ol = (-4.0, 3.0, 0.0), (14.0, 7.0, 0.0)
        self.anchor("rival_loop", rl)
        self.anchor("owner_loop", ol)
        plat = toon_material("fg_platform", (0.58, 0.52, 0.46))
        for tag, (lx, ly, _) in (("rival", rl), ("owner", ol)):
            sx = lx - 14.3
            slab("fg.station.%s.deck" % tag, rect(sx - 2.4, 2.4, sx + 2.4, 2.8), plat, y=ly - 0.2, depth=1.8, ink=0.04)
            for dx in (-2.0, 2.0):
                slab("fg.station.%s.leg%d" % (tag, dx), rect(-0.18, 0, 0.18, 2.4), plat, y=ly, depth=0.4, ink=0.03, x=sx + dx)
            slab("fg.station.%s.stairs" % tag, [(sx - 2.4, 2.4), (sx - 5.4, 0), (sx - 5.0, 0), (sx - 2.0, 2.4)], plat, y=ly - 0.4, depth=1.0, ink=0.03)
            self.anchor("station_" + tag, (sx, ly - 0.55, 2.8))
        crowd("fg.crowd", [-26 + 1.35 * i for i in range(10)], -1.6, seed=11)
        crowd("fg.crowd2", [14 + 1.6 * i for i in range(6)], -3.4, seed=29)
        self.anchor("crowd_line", (-26.0, -1.6, 0.0))
        self.anchor("rival_front", (-14.5, -2.4, 0.0))
        self.anchor("rival_stairs", (-17.0, -1.8, 0.0))
        self.anchor("owner_gate", (3.0, -2.4, 0.0))
        self.anchor("owner_stairs", (4.0, -2.6, 0.0))
        self.anchor("owner_stand", (-0.5, -3.2, 0.0))


class CoasterClimax(SetSpec):
    name, prefix = "coaster_climax", "cc"

    def build(self):
        outdoor_backdrop("cc", y_far=46.0)
        wood, dark = toon_material("fg_wood", (0.62, 0.44, 0.26)), toon_material("fg_dark", (0.24, 0.20, 0.18))
        ferris_wheel("cc.wheel", -26.0, 12.5, 9.0, 34.0)
        bunting("cc.bunt", 3, 22, 7.6, 6.0, n=12)
        grand = toon_material("cc_stand", (0.70, 0.58, 0.42))
        slab("cc.stand", [(-14, 0), (-6, 0), (-6, 2.4), (-14, 4.2)], grand, y=9.0, depth=2.0, ink=0.04)
        crowd("cc.spectators", [-13.0 + 1.1 * i for i in range(7)], 7.6, seed=5, scale=0.7)
        crowd("cc.front", [-5.0 + 1.5 * i for i in range(5)], -4.5, seed=17)
        slab("cc.rail", rect(-22, 0.6, 14, 0.75), dark, y=-3.6, depth=0.1, ink=0.02)
        for i in range(10):
            slab("cc.railpost%d" % i, rect(-0.07, 0, 0.07, 0.8), dark, y=-3.6, depth=0.12, x=-22 + 4.0 * i)
        self.anchor("owner_loop", (0.0, 0.0, 0.0))
        self.anchor("rival_loop", (26.0, 7.0, 0.0))
        self.anchor("owner_bottom", (1.2, -1.0, 0.0))
        self.anchor("rival_bottom", (26.0, 5.6, 0.0))
        self.anchor("crowd", (-5.0, -4.5, 0.0))


def build_sets():
    return {s.name: s for s in (WorkshopNight(), FairgroundDawn(), CoasterClimax())}
