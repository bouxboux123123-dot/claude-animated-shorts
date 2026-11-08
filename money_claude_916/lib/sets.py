"""sets.py - modular sets, named AnchorRegistry, narrative environmental dressing.

Anchors and obstacles are pure data (registered at import) so the stateless
evaluator can query them without Blender. Geometry is built lazily.
"""
import math

from lib import look

# --------------------------------------------------------------------------
# AnchorRegistry (pure) ----------------------------------------------------
# --------------------------------------------------------------------------
class AnchorRegistry:
    def __init__(self):
        self._a = {}
        self.obstacles = []          # (name, (x,y,z), radius)

    def add(self, name, pos):
        self._a[name] = tuple(float(v) for v in pos)

    def get(self, name):
        if name not in self._a:
            raise KeyError(f"unknown anchor '{name}'")
        return self._a[name]

    def names(self, prefix=""):
        return sorted(n for n in self._a if n.startswith(prefix))

    def add_obstacle(self, name, pos, radius):
        self.obstacles.append((name, tuple(pos), float(radius)))

    def clearance(self, pos):
        if not self.obstacles:
            return 1e9
        return min(math.dist(pos, p) - r for _, p, r in self.obstacles)

    def push_clear(self, pos, min_clear=2.5):
        """Deterministically push a camera position out of any obstacle halo."""
        p = list(pos)
        for _ in range(6):
            moved = False
            for _, o, r in self.obstacles:
                d = math.dist(p, o)
                need = r + min_clear
                if d < need:
                    dirv = [(p[i] - o[i]) / (d or 1.0) for i in range(3)] if d > 1e-9 else [0, -1, 0]
                    p = [p[i] + dirv[i] * (need - d) for i in range(3)]
                    moved = True
            if not moved:
                break
        return tuple(p)

    def build(self, coll):
        for n, p in self._a.items():
            look.empty("A:" + n, loc=p, coll=coll)


REG = AnchorRegistry()
SET_ORIGINS = {"island": 0.0, "workshop": 100.0, "bakery": 200.0, "street": 300.0}
QUEUE_X0, QUEUE_DX = 201.6, 1.15


def queue_x(k):
    return QUEUE_X0 - QUEUE_DX * k


def _define():
    A = REG.add
    A("island.center", (0, 0, 0)); A("island.you_spot", (-0.8, 0.0, 0)); A("island.doorstep", (6.0, 1.5, 0))
    A("island.loaf_home", (2.5, 1.5, 1.0)); A("island.you_door", (5.2, 0.8, 0))
    A("workshop.press", (100.0, 0.6, 0)); A("workshop.lever", (97.5, 0.6, 0)); A("workshop.official_spot", (98.45, 0.45, 0))
    for i, x in enumerate((96, 99, 102, 105), 1):
        A(f"workshop.lamp_{i}", (x, 2.0, 6.0))
    A("bakery.counter_top", (204.0, 0.9, 1.0)); A("bakery.cash_home", (202.25, 0.9, 1.45))
    A("bakery.hammer_home", (205.4, 1.3, 1.0)); A("bakery.board", (207.4, 4.6, 0)); A("bakery.oven", (211.0, 5.5, 0))
    A("bakery.you_spot", (201.6, 0.1, 0)); A("bakery.baker_spot", (204.8, 1.8, 0)); A("bakery.sprint_start", (186.0, -0.8, 0))
    for k in range(1, 10):
        A(f"bakery.queue_{k}", (queue_x(k), 0.1, 0))
    for i, x in enumerate((196, 201, 206, 210), 1):
        A(f"bakery.lamp_{i}", (x, 2.5, 6.0))
    A("street.stove", (297.6, 0.5, 0)); A("street.lady_spot", (296.4, 0.4, 0)); A("street.kid_spot", (302.6, 0.2, 0))
    A("street.you_spot", (301.0, 0.0, 0)); A("street.castles", (305.0, 0.6, 0))
    A("offstage", (-500.0, 0.0, 0))
    for n, p, r in (("ferris", (-5, 12, 5), 5.5), ("press", (100, 0.6, 1.0), 1.4), ("counter", (204, 0.9, 0.6), 2.2),
                    ("oven", (211, 5.5, 1.5), 2.4), ("stove", (297.6, 0.5, 1.0), 0.9), ("hut", (6, 3.4, 1.3), 2.0),
                    ("bench", (92.5, 2.5, 0.8), 2.2), ("tent_a", (8, 9, 1.5), 2.0)):
        REG.add_obstacle(n, p, r)


_define()


# --------------------------------------------------------------------------
# Dressing helpers ---------------------------------------------------------
# --------------------------------------------------------------------------
class SetBuilder:
    name = ""

    def __init__(self):
        self.coll = None

    def build(self):
        self.coll = look.get_collection("SET:" + self.name)
        self.dress()
        return self

    def box(self, name, size, pos, color, ink=0.02, rot=(0, 0, 0)):
        return look.make_box(f"{self.name}.{name}", size, pos, color, self.coll, ink, rot)

    def card(self, name, poly, pos, color, ink=0.02, rot=0.0):
        return look.make_prism(f"{self.name}.{name}", poly, color, self.coll, pos, 0.04, ink, rot)

    def cutout(self, name, x, y, color, scale=1.0, skin="skin_b", hat=None):
        s = scale
        self.card(name + "_body", [(-.3 * s, 0), (.3 * s, 0), (.34 * s, 1.1 * s), (.2 * s, 1.5 * s), (-.2 * s, 1.5 * s), (-.34 * s, 1.1 * s)],
                  (x, y, 0.0), color)
        self.card(name + "_head", look.ellipse_poly(.3 * s, .33 * s, 16), (x, y - 0.03, 1.85 * s), skin)
        if hat:
            self.card(name + "_hat", look.rect_poly(.5 * s, .2 * s), (x, y - 0.05, 2.15 * s), hat)

    def lamp(self, name, x, y, z_top, drop):
        self.box(name + "_cord", (.04, .04, drop), (x, y, z_top - drop / 2), "black", ink=0)
        self.card(name + "_shade", [(-.55, 0), (.55, 0), (.25, .5), (-.25, .5)], (x, y, z_top - drop - 0.15), "iron_dark")
        self.card(name + "_bulb", look.ellipse_poly(.17, .2, 12), (x, y - 0.04, z_top - drop - 0.2), "bulb", ink=0)

    def lamps_row(self, tag, xs, y, z_top, drop=1.2):
        for i, x in enumerate(xs):
            self.lamp(f"{tag}{i}", x, y, z_top, drop)

    def beams(self, x0, x1, ys, z, posts):
        cx, w = (x0 + x1) / 2, x1 - x0
        for i, y in enumerate(ys):
            self.box(f"beam{i}", (w, .5, .5), (cx, y, z), "wood_dark")
        for i, px in enumerate(posts):
            self.box(f"post{i}", (.6, .6, z + .3), (px, 6.2, (z + .3) / 2), "wood_dark")


# --------------------------------------------------------------------------
class IslandSet(SetBuilder):
    name = "island"

    def dress(self):
        self.box("sand", (36, 16, .4), (0, 6, -.2), "sand")
        self.box("sea", (90, 40, .2), (0, 38, -.9), "sea", ink=0)
        self.card("sky", look.rect_poly(90, 30), (0, 34, 14), "sky", ink=0)
        self.card("sun", look.ellipse_poly(3, 3, 28), (-12, 33.5, 15), "yellow", ink=0)
        for i, (cx, cz) in enumerate(((10, 18), (-4, 21), (20, 16))):
            self.card(f"cloud{i}", look.ellipse_poly(4.0, 1.1, 20), (cx, 33, cz), "white", ink=0)
        self.card("horizon_hills", [(-45, 0), (45, 0), (45, 3.4), (30, 5.5), (12, 3.2), (-6, 6.0), (-26, 3.6), (-45, 4.4)],
                  (0, 32, 2.0), "teal", ink=0)
        # ferris wheel
        hx, hy, hz, R = -5.0, 12.0, 7.2, 5.0
        n = 24
        for i in range(n):
            a = 2 * math.pi * i / n
            self.box(f"fw_rim{i}", (2 * math.pi * R / n * 1.08, .15, .15), (hx + R * math.cos(a), hy, hz + R * math.sin(a)),
                     "red" if i % 2 else "white", 0.01, (0, -(math.degrees(a) + 90), 0))
        for i in range(12):
            a = 2 * math.pi * i / 12
            self.box(f"fw_spoke{i}", (R, .1, .1), (hx + R / 2 * math.cos(a), hy, hz + R / 2 * math.sin(a)), "iron", 0.01,
                     (0, -math.degrees(a), 0))
            self.card(f"fw_gond{i}", look.rect_poly(.7, .55), (hx + R * math.cos(a), hy - .2, hz + R * math.sin(a) - .4),
                      ("yellow", "blue", "green", "orange")[i % 4])
        for sgn in (-1, 1):
            self.box(f"fw_leg{sgn}", (.3, .3, 8.4), (hx + sgn * 1.9, hy, 3.6), "iron_dark", 0.02, (0, sgn * 14, 0))
        # tents + bunting
        for i, (tx, ty) in enumerate(((8, 9), (-10, 8), (3, 12.5))):
            self.box(f"tent{i}_body", (3.2, 3, 2.2), (tx, ty, 1.1), "cream")
            self.card(f"tent{i}_roof", [(-2, 0), (2, 0), (0, 1.7)], (tx, ty - 1.6, 2.2), "red")
            self.card(f"tent{i}_stripe", [(-.6, 0), (.6, 0), (0, 1.0)], (tx, ty - 1.65, 2.25), "white", ink=0)
        for i in range(30):
            t = i / 29
            x = -9 + 18 * t
            z = 4.8 - 0.9 * math.sin(math.pi * t)
            self.card(f"bunt{i}", [(-.18, 0), (.18, 0), (0, -.45)], (x, 2.9, z), ("red", "yellow", "blue", "green")[i % 4], ink=0.012)
        for sx in (-9, 9):
            self.box(f"pole{sx}", (.12, .12, 5), (sx, 2.9, 2.5), "wood_dark")
        # ten islanders + spectator rows
        cols = ("red", "blue", "green", "purple", "orange", "teal", "pink", "yellow", "navy", "brick")
        for i in range(10):
            self.cutout(f"islander{i}", -4.1 + 0.91 * i, 3.2, cols[i], 1.0, ("skin_a", "skin_b", "skin_c", "skin_d")[i % 4])
        for i in range(16):
            self.cutout(f"spec{i}", -9 + 1.2 * i, 6.5 + (i % 2) * .8, cols[(i * 3) % 10], 1.15, ("skin_b", "skin_a")[i % 2],
                        hat=("red", "navy", None, "yellow")[i % 4])
        for sx in (-7.2, 7.4):
            self.box(f"palm{sx}", (.35, .35, 4.6), (sx, 2.6, 2.3), "wood", 0.02, (0, 6 * (1 if sx > 0 else -1), 0))
            for j in range(5):
                a = math.radians(20 + j * 35)
                self.card(f"palm{sx}_leaf{j}", look.ellipse_poly(1.5, .28, 12, 0, 0, a), (sx + math.cos(a) * 1.2, 2.5, 4.7 + math.sin(a) * .8), "green")
        # bread table with ten loaves, crate stack
        self.box("table_top", (2.6, 1.0, .12), (2.5, 1.5, .94), "wood")
        for sx in (-1, 1):
            self.box(f"table_leg{sx}", (.15, .15, .94), (2.5 + sx * 1.15, 1.5, .47), "wood_dark")
        for i in range(10):
            self.card(f"loaf{i}", look.ellipse_poly(.2, .11, 14), (1.45 + i * 0.235, 1.2, 1.12), "crust", 0.012)
        self.box("crate_a", (1.0, 1.0, 1.0), (4.3, 1.8, .5), "wood")
        # doorstep hut
        self.box("hut", (3.4, 2.4, 2.8), (6, 3.4, 1.4), "cream")
        self.card("hut_door", look.rect_poly(.95, 1.9), (6, 2.15, .95), "wood_dark")
        self.card("hut_roof", [(-2.2, 0), (2.2, 0), (0, 1.5)], (6, 2.1, 2.8), "brick")
        self.box("doorstep", (2.6, 1.4, .12), (6, 1.9, .06), "stone")


class WorkshopSet(SetBuilder):
    name = "workshop"

    def dress(self):
        self.box("floor", (30, 16, .4), (100, 5, -.2), "wood_dark")
        self.box("wall", (30, .3, 11), (100, 7, 5.5), "brick")
        for i, bx in enumerate((95, 100, 105)):
            self.card(f"bp{i}", look.rect_poly(3.6, 2.6), (bx, 6.8, 4.4), "blueprint", 0.02)
            look.make_ring(f"bp{i}_gear", .55, .66, (bx - .6, 6.7, 4.5), "white", self.coll)
            look.make_ring(f"bp{i}_gear2", .3, .38, (bx + .7, 6.7, 4.0), "white", self.coll, 20)
            for j in range(3):
                self.box(f"bp{i}_ln{j}", (1.3, .02, .03), (bx, 6.7, 3.5 + .22 * j), "white", ink=0)
        self.beams(84, 116, (2.0, 4.0, 6.0), 7.6, (94, 106))
        self.lamps_row("pend", (96, 99, 102, 105), 2.0, 7.4)
        # workbench with vice and tools
        self.box("bench_top", (4.0, 1.2, .15), (92.5, 2.5, 1.0), "wood")
        for sx in (-1.8, 1.8):
            self.box(f"bench_leg{sx}", (.2, 1.0, 1.0), (92.5 + sx, 2.5, .5), "wood_dark")
        self.box("vice_base", (.5, .4, .3), (91.4, 2.5, 1.22), "iron_dark")
        self.box("vice_jaw", (.55, .15, .35), (91.4, 2.3, 1.5), "iron")
        self.box("vice_screw", (.08, .08, .6), (91.4, 2.1, 1.35), "iron_dark", 0.01, (90, 0, 0))
        self.card("pegboard", look.rect_poly(3.4, 2.2), (92.5, 6.8, 3.0), "wood", 0.02)
        for i in range(5):
            self.box(f"tool{i}", (.12, .05, 1.1), (91.2 + .6 * i, 6.65, 3.0), ("iron", "red", "iron", "blue", "iron")[i], 0.01, (0, 18 * (i - 2), 0))
        for i, (cx, cz) in enumerate(((107.5, .55), (108.8, .55), (108.2, 1.65))):
            self.box(f"crate{i}", (1.1, 1.1, 1.1), (cx, 2.6, cz), "wood")
            self.card(f"crate{i}_slat", look.rect_poly(1.0, .12), (cx, 2.0, cz), "wood_dark", 0.01)
        self.box("barrel", (.9, .9, 1.1), (110, 3.5, .55), "iron_dark")


class BakerySet(SetBuilder):
    name = "bakery"

    def dress(self):
        self.box("floor", (34, 16, .4), (199, 5, -.2), "stone")
        self.box("wall", (34, .3, 11), (199, 7, 5.5), "cream")
        for i in range(8):
            self.box(f"brickrow{i}", (34, .05, .06), (199, 6.8, 1.0 + i * 1.1), "brick", 0)
        self.beams(184, 214, (2.0, 4.0, 6.0), 7.8, (185, 213))
        self.lamps_row("pend", (196, 201, 206, 210), 2.5, 7.6)
        ox, oy = 211.0, 5.5
        self.box("oven_body", (4.2, 2.2, 3.4), (ox, oy, 1.7), "brick")
        self.card("oven_arch", look.ellipse_poly(1.3, 1.15, 24), (ox, oy - 1.15, 1.5), "black")
        self.card("oven_fire", look.ellipse_poly(1.0, .8, 20), (ox, oy - 1.2, 1.25), "fire", 0)
        self.box("oven_tray", (2.6, .4, .08), (ox, oy - 1.3, 1.0), "iron_dark", 0.01)
        for i in range(10):
            self.card(f"oven_loaf{i}", look.ellipse_poly(.13, .1, 12), (ox - 1.15 + i * .255, oy - 1.4, 1.14), "crust", 0.01)
        self.box("counter", (4.1, 1.0, 1.0), (204.0, .95, .5), "wood")
        self.box("counter_top", (4.3, 1.2, .1), (204.0, .95, 1.05), "wood_dark", 0.015)
        for i in range(3):
            self.card(f"basket{i}", look.ellipse_poly(.35, .18, 12), (202.7 + i * .55, .5, 1.22), "crust", 0.012)
        self.card("sign", look.rect_poly(4.0, .9), (205, 6.7, 6.2), "wood_dark")
        look.make_text("bakery.sign_text", "BAKERY", (205, 6.55, 6.2), 0.7, "cream", self.coll)
        for i in range(2):
            self.box(f"shelf{i}", (6.0, .6, .1), (197, 6.5, 2.3 + i * 1.5), "wood")
            for j in range(8):
                self.card(f"shelf{i}_loaf{j}", look.ellipse_poly(.22, .12, 12), (194.5 + j * .65, 6.3, 2.48 + i * 1.5), "crust", 0.01)
        for i in range(3):
            self.box(f"flour{i}", (1.0, 1.0, 1.1), (212.5 + 0.0, 2.2 + i * 1.1, .55), "paper")
        # the other seven people in the queue (k=2..8); guy (1) and lady (9) are characters
        cols = ("red", "blue", "green", "purple", "orange", "teal", "navy")
        for k in range(2, 9):
            self.cutout(f"queue{k}", queue_x(k), 0.1, cols[k - 2], 1.0, ("skin_a", "skin_b", "skin_c", "skin_d")[k % 4],
                        hat=(None, "red", None, "yellow")[k % 4])
        self.box("chalk_line", (11, .6, .02), (196, .5, .01), "chalk", 0)


class StreetSet(SetBuilder):
    name = "street"

    def dress(self):
        self.box("road", (34, 9, .3), (300, 2.5, -.15), "stone")
        for i in range(14):
            self.box(f"cobble{i}", (34, .05, .03), (300, -1.5 + i * .65, .0), "stone_dark", 0)
        self.card("smog_sky", look.rect_poly(90, 40), (300, 32, 14), "smog", ink=0)
        for i, bx in enumerate((289, 295, 301, 307, 313)):
            h = 12 + (i % 3) * 2.4
            self.box(f"bld{i}", (5.6, 2.5, h), (bx, 8.5, h / 2), ("brick", "stone", "cream", "brick", "stone")[i])
            for r in range(4):
                for c in range(3):
                    self.card(f"bld{i}_w{r}{c}", look.rect_poly(.9, 1.3), (bx - 1.6 + c * 1.6, 7.2, 3.0 + r * 2.5),
                              "yellow" if (r + c + i) % 3 == 0 else "iron_dark", 0.015)
        for i, lx in enumerate((292, 300, 308)):
            self.box(f"lamppost{i}", (.15, .15, 4.0), (lx, 3.5, 2.0), "iron_dark")
            self.card(f"lamphead{i}", look.ellipse_poly(.25, .3, 10), (lx, 3.45, 4.1), "cream", 0.01)
        self.card("rate_sign", look.rect_poly(5.0, 1.1), (300, 6.9, 10.6), "board", 0.03)
        look.make_text("street.rate_text", "1 USD = 4.2 TRILLION MARKS", (300, 6.75, 10.6), 0.42, "chalk", self.coll)
        self.card("year_sign", look.ellipse_poly(1.3, .8, 20), (294, 6.8, 7.5), "red", 0.03)
        look.make_text("street.year_text", "1923", (294, 6.65, 7.5), 0.6, "white", self.coll)
        for i in range(5):                        # firewood pile
            self.box(f"log{i}", (.9, .25, .25), (295.0 + (i % 3) * .3, 1.2, .15 + (i // 3) * .27), "wood", 0.012, (0, 0, 8 * i))
        # kids' play-castles made of stacks of cash
        cx, cy, _ = REG.get("street.castles")
        for t, (ox, w) in enumerate(((0, 4), (2.3, 3))):
            for lvl in range(w):
                for j in range(w - lvl):
                    self.box(f"castle{t}_{lvl}_{j}", (.8, .4, .24), (cx + ox + (j - (w - lvl - 1) / 2) * .85, cy, .12 + lvl * .26),
                             ("green", "green_dark")[(lvl + j) % 2], 0.012)
            self.card(f"castle{t}_flag", [(0, 0), (.35, .12), (0, .25)], (cx + ox, cy, .12 + w * .26 + .15), "red", 0.01)
        self.box("bale", (1.4, .9, .9), (293.5, 1.6, .45), "green_dark")


SETS = {"island": IslandSet, "workshop": WorkshopSet, "bakery": BakerySet, "street": StreetSet}


def build_all():
    rig = look.get_collection("ANCHORS")
    REG.build(rig)
    return {n: cls().build() for n, cls in SETS.items()}


def lamp_positions(set_name):
    return [REG.get(n) for n in REG.names(set_name + ".lamp_")]


def show_only(active):
    for n in SETS:
        c = look.bpy.data.collections.get("SET:" + n)
        if c:
            c.hide_render = c.hide_viewport = (n != active)
