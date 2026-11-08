"""chars.py - billboard card characters: illustrated faces, emotion state
machine, FK/IK posing. The pose solver is pure (no bpy); CharRig builds and
drives the Blender objects from its output.

Rig: Root -> Hips (sway/lean) -> Torso (lean) -> Head (tilt)
                                         \\-> Shoulder -> UpperArm -> Forearm -> Hand
All 2D math happens in the card plane (x right, z up) in ROOT-LOCAL space, so a
mirrored root (facing = -1) keeps CCW angles unchanged.
CCW angle phi  <->  Blender rotation_euler.y = -phi.
"""
import math
from dataclasses import dataclass

from lib import look
from lib.props import solve2

DEG = math.pi / 180.0
SH_X, SH_Z, HIPS_Z, HEAD_Z, HEAD_CZ = 0.30, 0.65, 0.80, 0.80, 0.34
L1, L2 = 0.52, 0.48
BLEND_FRAMES = 6

# --------------------------------------------------------------------------
# Emotion state machine ----------------------------------------------------
# brow = (angle_deg CCW, lift); pupil = dilation (0.5..1.6); lean deg fwd
# --------------------------------------------------------------------------
MOUTHS = ("flat", "smile", "frown", "smirk", "open_o", "laugh", "wobble")
EMOTIONS = {
    "neutral":    dict(brow_l=(0, 0.0),    brow_r=(0, 0.0),     pupil=1.0, lean=0,   tilt=0,   sway=1.0, mouth="flat"),
    "determined": dict(brow_l=(-18, -.02), brow_r=(18, -.02),   pupil=0.8, lean=8,   tilt=-2,  sway=0.5, mouth="flat"),
    "worried":    dict(brow_l=(20, .04),   brow_r=(-20, .04),   pupil=1.25, lean=-3, tilt=6,   sway=1.6, mouth="wobble"),
    "shocked":    dict(brow_l=(8, .10),    brow_r=(-8, .10),    pupil=0.5, lean=-6,  tilt=0,   sway=0.2, mouth="open_o"),
    "smug":       dict(brow_l=(-6, -.01),  brow_r=(15, .06),    pupil=0.85, lean=-4, tilt=5,   sway=0.8, mouth="smirk"),
    "laugh":      dict(brow_l=(10, .05),   brow_r=(-10, .05),   pupil=1.1, lean=-10, tilt=-4,  sway=2.2, mouth="laugh"),
    "panic":      dict(brow_l=(25, .08),   brow_r=(-25, .08),   pupil=1.6, lean=-8,  tilt=8,   sway=3.0, mouth="open_o"),
    "proud":      dict(brow_l=(5, .04),    brow_r=(-5, .04),    pupil=1.3, lean=-5,  tilt=-3,  sway=0.6, mouth="smile"),
    "angry":      dict(brow_l=(-28, -.04), brow_r=(28, -.04),   pupil=0.7, lean=12,  tilt=-3,  sway=1.2, mouth="frown"),
}
assert len(EMOTIONS) >= 8 and all(0.5 <= e["pupil"] <= 1.6 for e in EMOTIONS.values())
assert set(e["mouth"] for e in EMOTIONS.values()) == set(MOUTHS)


def _lerp(a, b, t):
    return a + (b - a) * t


def emotion_state(events, f):
    """events: [(frame, label)] sorted. Pure function of f."""
    cur_i = -1
    for i, (ef, _) in enumerate(events):
        if ef <= f:
            cur_i = i
    if cur_i < 0:
        e = EMOTIONS["neutral"]
        return dict(e, label="neutral")
    f0, label = events[cur_i]
    prev = EMOTIONS[events[cur_i - 1][1]] if cur_i > 0 else EMOTIONS["neutral"]
    cur = EMOTIONS[label]
    t = min(1.0, max(0.0, (f - f0) / BLEND_FRAMES))
    t = t * t * (3 - 2 * t)
    out = dict(label=label, mouth=cur["mouth"] if t >= 0.5 else prev["mouth"])
    for k in ("pupil", "lean", "tilt", "sway"):
        out[k] = _lerp(prev[k], cur[k], t)
    for k in ("brow_l", "brow_r"):
        out[k] = (_lerp(prev[k][0], cur[k][0], t), _lerp(prev[k][1], cur[k][1], t))
    return out


# --------------------------------------------------------------------------
# Specs --------------------------------------------------------------------
# --------------------------------------------------------------------------
@dataclass
class CharSpec:
    name: str
    skin: str
    shirt: str
    pants: str
    hair: str
    hat: str = "none"          # none|tophat|chef|cap|lady|hood
    hat_color: str = "black"
    extra: str = "none"        # none|tie|apron|coat|pocket
    scale: float = 1.0
    phase: float = 0.0


CHAR_SPECS = [
    CharSpec("you", "skin_a", "orange", "navy", "wood_dark", "hood", "orange", "pocket", 1.0, 0.0),
    CharSpec("official", "skin_d", "navy", "navy", "iron_dark", "tophat", "black", "tie", 1.0, 1.1),
    CharSpec("baker", "skin_b", "white", "stone", "wood_dark", "chef", "white", "apron", 1.0, 2.3),
    CharSpec("guy", "skin_c", "green", "wood_dark", "black", "cap", "yellow", "none", 1.0, 3.1),
    CharSpec("lady", "skin_a", "purple", "navy", "wood_dark", "lady", "pink", "coat", 1.0, 4.0),
    CharSpec("kid", "skin_d", "red", "blue", "wood_dark", "cap", "yellow", "none", 0.62, 5.2),
]


def make_chars():
    return {s.name: s for s in CHAR_SPECS}


def dims(spec):
    s = spec.scale
    return dict(s=s, sh_x=SH_X * s, sh_z=SH_Z * s, hips_z=HIPS_Z * s, head_z=HEAD_Z * s, l1=L1 * s, l2=L2 * s)


# --------------------------------------------------------------------------
# Pure pose solver ---------------------------------------------------------
# --------------------------------------------------------------------------
def blink_factor(f, phase):
    return 0.1 if int(f + phase * 17) % 96 < 3 else 1.0


def pose_actor(spec, f, pos, facing, events, squash=0.0, grips=None, walk_phase=None):
    """pos=(x,y,z) root world position. grips={'L'|'R': (target_world_xyz, elbow_side)}.
    Returns a dict of everything needed to drive (and hash) the rig."""
    d = dims(spec)
    grips = grips or {}
    emo = emotion_state(events, f)
    ph = spec.phase
    sway = emo["sway"] * 2.0 * DEG * math.sin(2 * math.pi * f / 48.0 + ph)
    hips_rot = sway + (-squash * 0.05)
    torso_rot = -emo["lean"] * DEG + 0.4 * sway * math.sin(2 * math.pi * f / 96.0 + ph)
    head_rot = emo["tilt"] * DEG - 0.5 * sway
    cum = hips_rot + torso_rot
    c, sn = math.cos(cum), math.sin(cum)
    arms = {}
    for hand, sx in (("L", -d["sh_x"]), ("R", d["sh_x"])):
        sh = (sx * c - d["sh_z"] * sn, d["hips_z"] + sx * sn + d["sh_z"] * c)
        if hand in grips:
            tw, side = grips[hand]
            tgt = ((tw[0] - pos[0]) * facing, tw[2] - pos[2])
        else:
            side = -1
            tgt = (sh[0] + math.copysign(0.10 * d["s"], sx) + 0.04 * d["s"] * math.sin(2 * math.pi * f / 60.0 + ph + sx),
                   sh[1] - (d["l1"] + d["l2"]) * 0.9)
        ik = solve2(sh, tgt, d["l1"], d["l2"], side)
        arms[hand] = dict(shoulder=sh, target=tgt, a_up=ik.a1 + math.pi / 2 - cum, a_fore=ik.a2 - ik.a1,
                          hand=ik.hand, err=ik.err, reachable=ik.reachable, gripping=hand in grips,
                          hand_world=(pos[0] + facing * ik.hand[0], pos[1], pos[2] + ik.hand[1]))
    legs = (0.0, 0.0)
    if walk_phase is not None:
        legs = (0.45 * math.sin(walk_phase), -0.45 * math.sin(walk_phase))
    return dict(pos=tuple(pos), facing=facing, emo=emo, hips_rot=hips_rot, torso_rot=torso_rot, head_rot=head_rot,
                squash=squash, blink=blink_factor(f, ph), legs=legs, arms=arms)


def default_pose(spec):
    return pose_actor(spec, 0, (-500.0, 0.0, 0.0), 1, [])


# --------------------------------------------------------------------------
# Face shapes (pure) -------------------------------------------------------
# --------------------------------------------------------------------------
def mouth_poly(shape, s):
    w = 0.11 * s

    def band(fn, th, n=9):
        xs = [-w + 2 * w * i / (n - 1) for i in range(n)]
        return [(x, fn(x) - th / 2) for x in xs] + [(x, fn(x) + th / 2) for x in reversed(xs)]

    if shape == "flat":
        return band(lambda x: 0.0, .03 * s)
    if shape == "smile":
        return band(lambda x: .06 * s * ((x / w) ** 2 - .4), .032 * s)
    if shape == "frown":
        return band(lambda x: -.06 * s * ((x / w) ** 2 - .4), .032 * s)
    if shape == "smirk":
        return band(lambda x: .05 * s * max(0, x / w) ** 1.5 - .012 * s * max(0, -x / w), .032 * s)
    if shape == "open_o":
        return look.ellipse_poly(.055 * s, .075 * s, 16)
    if shape == "laugh":
        return [(1.1 * w * math.cos(a), .02 * s + .15 * s * math.sin(a)) for a in [math.pi + math.pi * i / 12 for i in range(13)]]
    if shape == "wobble":
        return band(lambda x: .02 * s * math.sin(x / w * 3 * math.pi), .03 * s, 13)
    raise KeyError(shape)


# --------------------------------------------------------------------------
# Blender rig --------------------------------------------------------------
# --------------------------------------------------------------------------
class CharRig:
    def __init__(self, spec):
        self.spec = spec
        self.o = {}

    def build(self):
        sp, d = self.spec, dims(self.spec)
        s = d["s"]
        coll = look.get_collection("CHAR:" + sp.name)
        E = lambda n, par=None, loc=(0, 0, 0): look.empty(f"{sp.name}.{n}", par, loc, coll)

        def C(n, poly, color, par, y, z=0.0, x=0.0, ink=0.018):
            o = look.make_prism(f"{sp.name}.{n}", poly, color, coll, (x, y, z), 0.025, ink)
            o.parent = par
            return o

        r = self.o
        r["root"] = E("root")
        r["hips"] = E("hips", r["root"], (0, 0, d["hips_z"]))
        r["torso"] = E("torso", r["hips"])
        # legs hang from the hips but belong to root so feet stay planted
        r["leg"] = {}
        for k, sx in (("L", -.13), ("R", .13)):
            lg = E("leg" + k, r["root"], (sx * s, 0, d["hips_z"]))
            C("leg" + k + "_card", look.rect_poly(.2 * s, d["hips_z"], 0, -d["hips_z"] / 2), sp.pants, lg, 0.03)
            C("shoe" + k, look.ellipse_poly(.17 * s, .07 * s, 10, .05 * s, -d["hips_z"] + .04 * s), "black", lg, 0.035, ink=0.01)
            r["leg"][k] = lg
        body_bottom = -.45 * s if sp.extra == "coat" else 0.0
        tp = [(-.30 * s, body_bottom), (.30 * s, body_bottom), (.34 * s, .55 * s), (.2 * s, .78 * s), (-.2 * s, .78 * s), (-.34 * s, .55 * s)]
        r["torso_card"] = C("torso_card", tp, sp.shirt, r["torso"], -0.02)
        if sp.extra == "tie":
            C("tie", [(0, .72 * s), (.06 * s, .5 * s), (0, .2 * s), (-.06 * s, .5 * s)], "red", r["torso"], -0.04, ink=0.01)
        elif sp.extra == "apron":
            C("apron", [(-.22 * s, 0), (.22 * s, 0), (.22 * s, .6 * s), (.1 * s, .7 * s), (-.1 * s, .7 * s), (-.22 * s, .6 * s)], "cream", r["torso"], -0.04)
        elif sp.extra == "pocket":
            C("pocket", look.rect_poly(.3 * s, .14 * s, 0, .18 * s), "orange", r["torso"], -0.04, ink=0.01)
        elif sp.extra == "coat":
            C("lapelL", [(0, .7 * s), (-.2 * s, .72 * s), (-.05 * s, .3 * s)], "white", r["torso"], -0.04, ink=0.01)
            C("lapelR", [(0, .7 * s), (.05 * s, .3 * s), (.2 * s, .72 * s)], "white", r["torso"], -0.04, ink=0.01)
        # head + face
        r["head"] = E("head", r["torso"], (0, 0, d["head_z"]))
        if sp.hat == "hood":
            C("hood", look.ellipse_poly(.45 * s, .47 * s, 20, 0, HEAD_CZ * s), sp.hat_color, r["head"], 0.03)
        C("head_card", look.ellipse_poly(.36 * s, .39 * s, 24, 0, HEAD_CZ * s), sp.skin, r["head"], -0.04)
        C("hair", look.ellipse_poly(.37 * s, .2 * s, 16, 0, .6 * s), sp.hair, r["head"], -0.05, ink=0.01)
        hat = sp.hat
        if hat == "tophat":
            C("hat_brim", look.rect_poly(.8 * s, .07 * s, 0, .72 * s), sp.hat_color, r["head"], -0.07)
            C("hat_top", look.rect_poly(.5 * s, .45 * s, 0, .95 * s), sp.hat_color, r["head"], -0.06)
        elif hat == "chef":
            C("chef_band", look.rect_poly(.55 * s, .16 * s, 0, .72 * s), sp.hat_color, r["head"], -0.06)
            C("chef_puff", look.ellipse_poly(.36 * s, .28 * s, 16, 0, .95 * s), sp.hat_color, r["head"], -0.06)
        elif hat == "cap":
            C("cap_dome", look.ellipse_poly(.38 * s, .2 * s, 16, 0, .68 * s), sp.hat_color, r["head"], -0.07)
            C("cap_brim", look.rect_poly(.3 * s, .06 * s, .3 * s, .66 * s), sp.hat_color, r["head"], -0.075, ink=0.01)
        elif hat == "lady":
            C("lady_brim", look.ellipse_poly(.55 * s, .09 * s, 18, 0, .7 * s), sp.hat_color, r["head"], -0.07)
            C("lady_crown", look.ellipse_poly(.28 * s, .2 * s, 14, 0, .82 * s), sp.hat_color, r["head"], -0.06)
        eyes, brows, pup, mouths = {}, {}, {}, {}
        for k, sx in (("L", -1), ("R", 1)):
            ex = sx * .14 * s
            eyes[k] = C("sclera" + k, look.ellipse_poly(.095 * s, .115 * s, 14), "white", r["head"], -0.09, .40 * s, ex, 0.01)
            pup[k] = C("pupil" + k, look.ellipse_poly(.05 * s, .05 * s, 10), "black", r["head"], -0.1, .40 * s, ex + .015 * s, 0.0)
            brows[k] = C("brow" + k, look.rect_poly(.15 * s, .03 * s), "black", r["head"], -0.095, .55 * s, ex, 0.0)
        C("nose", look.ellipse_poly(.04 * s, .05 * s, 10), "skin_c", r["head"], -0.09, .27 * s, .04 * s, 0.01)
        for m in MOUTHS:
            mouths[m] = C("mouth_" + m, mouth_poly(m, s), "black", r["head"], -0.1, .13 * s, 0.0, 0.0)
        r.update(eyes=eyes, brows=brows, pupils=pup, mouths=mouths)
        # arms
        r["sh"], r["up"], r["fore"], r["hand"] = {}, {}, {}, {}
        for k, sx in (("L", -1), ("R", 1)):
            y = 0.02 if k == "L" else -0.06
            sh = E("shoulder" + k, r["torso"], (sx * d["sh_x"], 0, d["sh_z"]))
            up = E("upper" + k, sh)
            fo = E("fore" + k, up, (0, 0, -d["l1"]))
            ha = E("hand" + k, fo, (0, 0, -d["l2"]))
            C("upper" + k + "_card", look.rect_poly(.17 * s, d["l1"], 0, -d["l1"] / 2), sp.shirt, up, y)
            C("fore" + k + "_card", look.rect_poly(.15 * s, d["l2"], 0, -d["l2"] / 2), sp.shirt if sp.extra != "tie" else sp.skin, fo, y - 0.005)
            C("hand" + k + "_card", look.ellipse_poly(.1 * s, .1 * s, 12, 0, -.02 * s), sp.skin, ha, y - 0.01, ink=0.015)
            r["sh"][k], r["up"][k], r["fore"][k], r["hand"][k] = sh, up, fo, ha
        return self

    def apply(self, st):
        r, sp, d = self.o, self.spec, dims(self.spec)
        s = d["s"]
        r["root"].location = st["pos"]
        r["root"].scale = (st["facing"], 1, 1)
        r["hips"].rotation_euler = (0, -st["hips_rot"], 0)
        r["torso"].rotation_euler = (0, -st["torso_rot"], 0)
        sq = st["squash"]
        r["torso_card"].scale = (1 + 0.1 * sq, 1, 1 - 0.15 * sq)
        r["head"].location = (0, 0, d["head_z"] - 0.12 * sq * s)
        r["head"].rotation_euler = (0, -st["head_rot"], 0)
        for k, ang in zip("LR", st["legs"]):
            r["leg"][k].rotation_euler = (0, -ang, 0)
        emo = st["emo"]
        for m, o in r["mouths"].items():
            o.hide_render = o.hide_viewport = (m != emo["mouth"])
        for k, key in (("L", "brow_l"), ("R", "brow_r")):
            ang, lift = emo[key]
            r["brows"][k].location = (r["brows"][k].location.x, r["brows"][k].location.y, (.55 + lift) * s)
            r["brows"][k].rotation_euler = (0, -ang * DEG, 0)
            r["pupils"][k].scale = (emo["pupil"], 1, emo["pupil"] * st["blink"])
            r["eyes"][k].scale = (1, 1, st["blink"])
        for k, a in st["arms"].items():
            r["up"][k].rotation_euler = (0, -a["a_up"], 0)
            r["fore"][k].rotation_euler = (0, -a["a_fore"], 0)
