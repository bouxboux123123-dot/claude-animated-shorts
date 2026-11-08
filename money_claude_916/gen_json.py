#!/usr/bin/env python3
"""Regenerates shots.json and acting.json (frame numbers derived from beat seconds)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib import sets as S  # noqa: E402

FPS = 30
BEATS = [  # (end_sec, line)
    (2.8, "Why don't we just print a billion dollars for everybody, and we all get rich?"),
    (5.6, "It sounds like genius. Until you actually do it."),
    (8.5, "Imagine there are only ten people on an island, and only ten loaves of bread."),
    (11.2, "Everyone has one dollar, so a loaf costs one dollar. Simple."),
    (14.0, "Now, the government cranks the printing press all night long..."),
    (16.8, "...and drops a million dollars onto everyone's doorstep."),
    (19.5, "You're a millionaire! You sprint to the bakery to buy breakfast."),
    (22.4, "Except... all nine other people are already standing in line,"),
    (25.0, "and there are still only ten loaves of bread in the oven."),
    (28.0, "You slam down a thousand dollars: 'Give me that loaf!'"),
    (31.0, "The guy behind you shouts: 'I'll pay ten thousand!'"),
    (34.2, "The lady in back yells: 'ONE HUNDRED THOUSAND!'"),
    (37.0, "Within ten minutes, that single loaf of bread costs one million dollars."),
    (40.0, "You didn't get richer. The paper just got weaker."),
    (43.0, "Because money isn't wealth. Goods and services are wealth."),
    (46.2, "If you double the money without doubling the bread, you just double the price."),
    (49.0, "This happened in Germany in 1923,"),
    (52.0, "where it was literally cheaper to burn banknotes than to buy firewood,"),
    (55.0, "and children built play-castles out of stacks of cash in the streets."),
    (58.0, "So printing money doesn't create wealth\u2014it just steals value from every dollar in your pocket."),
    (61.0, "Next time someone says 'just print more,' hand them a loaf of bread and ask for your million back."),
]
EDGES = [0] + [round(s * FPS) for s, _ in BEATS]
assert EDGES[-1] == 1830

# (set, mood, angle, ease, from(pos, look, lens), to(pos, look, lens))
SHOTS = [
    ("island", "noon_fair", "push-in", "inout", ((-0.8, -5.4, 1.6), (-0.8, 0, 1.9), 26), ((-0.8, -4.2, 1.8), (-0.8, 0, 2.0), 30)),
    ("island", "noon_fair", "worms-eye tilt up at ferris wheel", "inout", ((-0.8, -4.6, 0.25), (-1.5, 2, 3.4), 22), ((-0.8, -4.6, 0.6), (-1.2, 2, 2.9), 22)),
    ("island", "noon_fair", "high-angle stacked wide of ten islanders", "inout", ((0, -8.5, 6.5), (0, 3.2, 1.2), 24), ((0, -7, 3.5), (0, 3.2, 1.5), 24)),
    ("island", "noon_fair", "bread table slide", "inout", ((1.4, -4.6, 1.4), (1.9, 1.2, 1.2), 30), ((1.9, -4.0, 1.3), (2.2, 1.2, 1.2), 32)),
    ("workshop", "workshop_tungsten", "worms-eye up at the press", "inout", ((98.8, -5.6, 0.3), (100, 0.6, 3.4), 22), ((99.2, -5.0, 2.2), (99.6, 0.6, 1.6), 28)),
    ("island", "golden_dusk", "plunge: money drops on the doorstep", "in", ((6, -2.5, 15), (6, 1.2, 0), 28), ((6, -2.0, 9.5), (6, 1.2, 0.5), 28)),
    ("bakery", "bakery_warm", "tracking sprint", "linear", ((192, -5, 1.5), (192, 0, 1.3), 30), ((200, -5, 1.5), (200.5, 0, 1.3), 30)),
    ("bakery", "bakery_warm", "queue reveal pan", "inout", ((201.6, -5.2, 1.7), (201, 0, 1.5), 24), ((197, -6, 2.2), (196.5, 0, 1.5), 24)),
    ("bakery", "bakery_warm", "worms-eye at the oven", "inout", ((207.5, -5, 0.4), (210, 5.5, 2.5), 24), ((208, -4.6, 0.9), (211, 5.5, 1.6), 28)),
    ("bakery", "bakery_warm", "slam push-in", "inout", ((202.0, -4, 1.6), (202.3, 0, 1.3), 32), ((202.2, -3.6, 1.5), (202.4, 0, 1.2), 34)),
    ("bakery", "bakery_warm", "guy shouts", "inout", ((200.6, -4.2, 1.7), (200.6, 0, 1.7), 32), ((200.3, -3.8, 1.8), (200.4, 0, 1.8), 34)),
    ("bakery", "bakery_warm", "lady far back", "inout", ((193.5, -4.6, 1.8), (191.8, 0, 1.7), 30), ((192.8, -4.0, 1.9), (191.4, 0, 1.8), 32)),
    ("bakery", "bakery_warm", "baker, then worms-eye up at price board", "inout", ((204.2, -4.5, 1.8), (204.4, 0, 2.0), 30), ((206.6, -4.0, 0.4), (207.2, 4.6, 3.3), 26)),
    ("bakery", "bakery_warm", "worried close", "inout", ((201.8, -4.2, 1.6), (201.8, 0, 1.4), 30), ((201.8, -3.6, 1.7), (201.8, 0, 1.3), 32)),
    ("island", "noon_fair", "loaf medium", "inout", ((1.0, -4.6, 1.4), (0.8, 0, 1.5), 30), ((0.9, -4.0, 1.5), (0.8, 0, 1.4), 32)),
    ("island", "noon_fair", "high-angle down on the loaf", "inout", ((1.0, -5.0, 5.0), (0.8, 0, 0.5), 28), ((0.9, -4.5, 2.6), (0.8, 0, 1.2), 28)),
    ("street", "grey_1923", "worms-eye up the 1923 facades", "inout", ((300, -7, 0.3), (300, 2, 6), 22), ((299.5, -6, 1.5), (299, 0, 3), 24)),
    ("street", "grey_1923", "stove burn", "inout", ((297.2, -4, 1.4), (297, 0.5, 1.5), 30), ((297.0, -3.7, 1.7), (297, 0.5, 1.4), 30)),
    ("street", "grey_1923", "cash castles", "inout", ((303.5, -5, 0.5), (304, 0.5, 1.8), 26), ((304, -4.5, 1.2), (304.2, 0.5, 1.0), 28)),
    ("street", "grey_1923", "moral close", "inout", ((301, -4.6, 1.6), (301, 0, 1.8), 30), ((301, -4.0, 1.8), (301, 0, 2.0), 30)),
    ("bakery", "bakery_warm", "final offer push-in", "inout", ((201.9, -4.6, 1.6), (202.3, 0, 1.5), 30), ((202.0, -3.4, 1.55), (202.4, 0, 1.5), 28)),
]
assert len(SHOTS) == len(BEATS) == 21


def shots_doc():
    out = []
    for i, (st, mood, angle, ease, a, b) in enumerate(SHOTS):
        out.append(dict(id=f"b{i + 1:02d}", beat=i + 1, f0=EDGES[i], f1=EDGES[i + 1], set=st, mood=mood, angle=angle, ease=ease,
                        line=BEATS[i][1],
                        **{"from": dict(pos=list(a[0]), look=list(a[1]), lens=a[2], roll=0.0),
                           "to": dict(pos=list(b[0]), look=list(b[1]), lens=b[2], roll=0.0)}))
    return dict(fps=FPS, total_frames=1830, resolution=[1080, 1920], sensor_fit="HORIZONTAL", shots=out)


def acting_doc():
    A = S.REG.get
    off = [-500.0, 0.0]
    xy = lambda n: list(A(n)[:2])
    actors = {"you": dict(pos=xy("island.you_spot"), facing=1), "official": dict(pos=off, facing=1),
              "baker": dict(pos=xy("bakery.baker_spot"), facing=-1), "guy": dict(pos=off, facing=1),
              "lady": dict(pos=off, facing=1), "kid": dict(pos=off, facing=-1)}
    ev = []
    emo = lambda a, f, e: ev.append(dict(verb="emotion", actor=a, f0=f, emotion=e))
    tele = lambda a, f, pos, face=1: ev.append(dict(verb="move", actor=a, f0=f, f1=f, to=pos, facing=face))
    walk = lambda a, f0, f1, pos: ev.append(dict(verb="move", actor=a, f0=f0, f1=f1, to=pos, facing=1))
    op = lambda p, ch, f0, f1, to, ease="inout", **k: ev.append(dict(verb="operate", prop=p, channel=ch, f0=f0, f1=f1, to=to, ease=ease, **k))
    hold = lambda a, h, p, s, f0, f1, **k: ev.append(dict(verb="hold", actor=a, hand=h, prop=p, socket=s, f0=f0, f1=f1, **k))
    clasp = lambda a, p, f0, f1, **k: ev.append(dict(verb="clasp", actor=a, prop=p, f0=f0, f1=f1, **k))
    imp = lambda f, dur, tgt, s: ev.append(dict(verb="impact", f0=f, dur=dur, target=tgt, strength=s))

    # ---- you
    for f, e in ((0, "determined"), (84, "smug"), (130, "worried"), (168, "neutral"), (255, "proud"), (420, "neutral"), (450, "shocked"),
                 (504, "laugh"), (560, "determined"), (585, "neutral"), (600, "worried"), (672, "panic"), (750, "angry"), (790, "panic"),
                 (930, "shocked"), (1026, "worried"), (1110, "worried"), (1200, "determined"), (1290, "smug"), (1386, "neutral"),
                 (1650, "proud"), (1740, "smug")):
        emo("you", f, e)
    tele("you", 420, xy("island.you_door"))
    tele("you", 504, xy("bakery.sprint_start"))
    walk("you", 504, 570, xy("bakery.you_spot"))
    tele("you", 1200, [0.2, 0.2])
    tele("you", 1650, xy("street.you_spot"))
    tele("you", 1740, xy("bakery.you_spot"))
    # ---- official runs the press
    tele("official", 336, xy("workshop.official_spot"))
    tele("official", 420, off)
    for f, e in ((336, "determined"), (380, "laugh"), (410, "smug")):
        emo("official", f, e)
    hold("official", "R", "press", "grip_main", 336, 419, carry=False, elbow=-1)
    hold("official", "L", "lever", "grip_main", 336, 400, carry=False, elbow=1)
    op("press", "crank", 345, 415, 1.0, "linear", **{"from": 0.0})
    op("lever", "pull", 345, 395, 1.0)
    # ---- baker (holds the price mallet the whole short; swings it at beat 13)
    for f, e in ((0, "neutral"), (780, "shocked"), (840, "neutral"), (1026, "smug"), (1070, "laugh"), (1110, "smug")):
        emo("baker", f, e)
    hold("baker", "R", "hammer", "grip_main", 0, 1829, carry=True, at=[0.3, 1.8], dy=-0.3)
    op("hammer", "swing", 1050, 1062, 1.0, "in")
    op("hammer", "swing", 1070, 1100, 0.0, "inout")
    # ---- queue
    tele("guy", 504, [S.queue_x(1), 0.1]); tele("guy", 1200, off)
    for f, e in ((504, "neutral"), (840, "angry"), (900, "smug"), (1026, "shocked")):
        emo("guy", f, e)
    tele("lady", 504, [S.queue_x(9), 0.1]); tele("lady", 1470, xy("street.lady_spot")); tele("lady", 1560, off)
    for f, e in ((504, "neutral"), (930, "angry"), (990, "angry"), (1026, "shocked"), (1470, "worried"), (1530, "panic")):
        emo("lady", f, e)
    tele("kid", 1560, xy("street.kid_spot"), -1); tele("kid", 1740, off, -1)
    emo("kid", 1560, "laugh"); emo("kid", 1650, "proud")
    # ---- cash: carried two-handed while sprinting, one-handed slam at the counter, then burned at the stove
    clasp("you", "cash", 504, 749, carry=True, at=[0.55, 1.1], dy=-0.02)
    hold("you", "R", "cash", "grip_main", 750, 840, carry=True, at=[0.65, 1.45], dy=0.8)
    op("cash", "slam", 765, 780, 1.0, "in")
    op("cash", "wilt", 1140, 1190, 1.0, "linear")
    clasp("lady", "cash", 1470, 1559, carry=True, at=[0.55, 1.7], dy=-0.02)
    # ---- loaf
    clasp("you", "loaf", 1200, 1385, carry=True, at=[0.55, 1.1], dy=-0.02)
    op("loaf", "bounce", 1210, 1225, 1.0, "out"); op("loaf", "bounce", 1225, 1240, 0.0, "in")
    hold("you", "R", "loaf", "grip_main", 1760, 1829, carry=True, at=[0.8, 1.45], dy=-0.6)
    # ---- display channels (no hands involved)
    op("rain", "fall", 420, 504, 1.0, "linear")
    for f0, f1, v in ((780, 790, .25), (870, 880, .5), (960, 970, .75), (1062, 1066, 1.0)):
        op("board", "price", f0, f1, v, "out")
    op("stove", "burn", 1480, 1555, 1.0, "linear")
    # ---- impacts
    for f, d, t, s in ((462, 20, "actor:you", .5), (480, 20, "camera", .5), (780, 24, "camera", .7), (780, 24, "actor:baker", .4),
                       (1062, 28, "camera", 1.0), (1062, 28, "actor:you", .6), (1062, 20, "world", .4), (1530, 20, "world", .5),
                       (1800, 16, "camera", .3), (1800, 16, "actor:you", .3)):
        imp(f, d, t, s)
    return dict(verbs=["operate", "hold", "clasp", "emotion", "impact", "move"], actors=actors, events=ev)


if __name__ == "__main__":
    json.dump(shots_doc(), open(os.path.join(ROOT, "shots.json"), "w"), indent=1)
    json.dump(acting_doc(), open(os.path.join(ROOT, "acting.json"), "w"), indent=1)
    print("wrote shots.json, acting.json")
