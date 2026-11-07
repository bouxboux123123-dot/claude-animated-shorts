#!/usr/bin/env python3
"""Generate acting.json from the audio timeline for "Why Roller Coasters Don't Fly Off The Tracks".

Dynamic interaction timeline driving hold and operate verbs.
Each action runs across its beat's frame range and drives a prop channel.
"""
import json

FPS = 30.0
TOTAL_FRAMES = 1887

# Beat frame ranges (recomputed to match shots.json timing)
beats = [
    (1,  0.0,  2.5),
    (2,  2.5,  5.4),
    (3,  5.4,  7.0),
    (4,  7.0,  9.7),
    (5,  9.7,  11.2),
    (6,  11.2, 13.9),
    (7,  13.9, 15.2),
    (8,  15.2, 17.2),
    (9,  17.2, 19.2),
    (10, 19.2, 21.0),
    (11, 21.0, 23.1),
    (12, 23.1, 26.3),
    (13, 26.3, 28.2),
    (14, 28.2, 31.9),
    (15, 31.9, 33.9),
    (16, 33.9, 35.3),
    (17, 35.3, 37.2),
    (18, 37.2, 39.9),
    (19, 39.9, 41.1),
    (20, 41.1, 44.0),
    (21, 44.0, 46.0),
    (22, 46.0, 48.2),
    (23, 48.2, 50.7),
    (24, 50.7, 52.1),
    (25, 52.1, 53.8),
    (26, 53.8, 56.5),
    (27, 56.5, 57.5),
    (28, 57.5, 59.8),
    (29, 59.8, 62.9),
]

acting = {'fps': FPS, 'total_frames': TOTAL_FRAMES, 'actions': []}


def f(t): return int(round(t * FPS))


def frame_range(i):
    """Frames [f_in, f_out) for beat i (1-indexed)."""
    t0 = beats[i - 1][1]
    if i == len(beats):
        return int(round(t0 * FPS)), TOTAL_FRAMES
    t1 = beats[i][1]
    return int(round(t0 * FPS)), int(round(t1 * FPS))


# Beat 1: "He bent the roller coaster's loop out of shape."
f_in, f_out = frame_range(1)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'builder', 'hand': 'right',
     'prop': 'hammer', 'socket': 'grip_main'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'loop_track',
     'channel': 'bend_bottom', 'from': 0.2, 'to': 1.0},
]

# Beat 2: "You see, it's the first ride ever to go upside down,"
f_in, f_out = frame_range(2)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'cart', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 0.5},
]

# Beat 3: "and it cost him everything."
f_in, f_out = frame_range(3)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'dummy', 'hand': 'right',
     'prop': 'dummy', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'dummy',
     'channel': 'crush_progress', 'from': 0.0, 'to': 1.0},
]

# Beat 4: "So of course, his rival copies it bolt for bolt."
f_in, f_out = frame_range(4)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'rival', 'hand': 'right',
     'prop': 'turnbuckle', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'turnbuckle',
     'channel': 'crank_angle', 'from': 0.0, 'to': 1.0},
]

# Beat 5: "But the night before opening,"
f_in, f_out = frame_range(5)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'builder', 'hand': 'right',
     'prop': 'hammer', 'socket': 'grip_main'},
]

# Beat 6: "his test dummy comes back crushed like a soda can,"
f_in, f_out = frame_range(6)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'dummy', 'hand': 'right',
     'prop': 'dummy', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'dummy',
     'channel': 'crush_progress', 'from': 0.0, 'to': 1.0},
]

# Beat 7: "but he can't miss the opening,"
f_in, f_out = frame_range(7)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'builder', 'hand': 'right',
     'prop': 'hammer', 'socket': 'grip_main'},
]

# Beat 8: "so he grabs a hammer and beats the bottom"
f_in, f_out = frame_range(8)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'builder', 'hand': 'right',
     'prop': 'hammer', 'socket': 'grip_main'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'hammer',
     'channel': 'swing_stroke', 'from': 0.0, 'to': 1.0},
]

# Beat 9: "into a long, lazy curve."
f_in, f_out = frame_range(9)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'builder', 'hand': 'right',
     'prop': 'hammer', 'socket': 'grip_main'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'loop_track',
     'channel': 'bend_bottom', 'from': 1.0, 'to': 0.0},
]

# Beat 10: "Does he know what he's doing? Not really."
f_in, f_out = frame_range(10)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'emotion', 'char': 'builder', 'emotion': 'shrug'},
]

# Beat 11: "His rival laughs, then sneaks in,"
f_in, f_out = frame_range(11)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'emotion', 'char': 'rival', 'emotion': 'laugh'},
]

# Beat 12: "and cranks the sides together until the loop is tall and skinny."
f_in, f_out = frame_range(12)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'rival', 'hand': 'right',
     'prop': 'turnbuckle', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'loop_track',
     'channel': 'squeeze_sides', 'from': 0.0, 'to': 1.0},
    {'f_in': f_in, 'f_out': f_out, 'act': 'impact', 'prop': 'loop_track',
     'channel': 'snap_force', 'from': 0.0, 'to': 1.0},
]

# Beat 13: "So the first cart will snap like a twig."
f_in, f_out = frame_range(13)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 1.0},
]

# Beat 14: "The next morning, the town lines up at the rival's perfect circle,"
f_in, f_out = frame_range(14)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'crowd', 'hand': 'right',
     'prop': 'spectate', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'loop_track',
     'channel': 'squeeze_sides', 'from': 1.0, 'to': 0.0},
]

# Beat 15: "and the rival climbs in front to show off."
f_in, f_out = frame_range(15)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'rival', 'hand': 'right',
     'prop': 'turnbuckle', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'emotion', 'char': 'rival', 'emotion': 'smug'},
]

# Beat 16: "The owner climbs into his,"
f_in, f_out = frame_range(16)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'owner', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 0.2},
]

# Beat 17: "and as his cart tips over the first hill,"
f_in, f_out = frame_range(17)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'owner', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.2, 'to': 0.6},
]

# Beat 18: "he finally sees the tall, skinny loop ahead."
f_in, f_out = frame_range(18)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'owner', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.6, 'to': 0.95},
]

# Beat 19: "But it's too late."
f_in, f_out = frame_range(19)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'emotion', 'char': 'owner', 'emotion': 'shock'},
]

# Beat 20: "You see, a car can creep around a hairpin turn at five,"
f_in, f_out = frame_range(20)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'owner', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 0.3},
]

# Beat 21: "but take it at 60, and it flips."
f_in, f_out = frame_range(21)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'owner', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 0.7},
]

# Beat 22: "A cart is fastest at the bottom of a loop,"
f_in, f_out = frame_range(22)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'owner', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 0.3},
]

# Beat 23: "and a perfect circle puts a hairpin right there,"
f_in, f_out = frame_range(23)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'owner', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.3, 'to': 0.9},
]

# Beat 24: "which is what crushed the dummy."
f_in, f_out = frame_range(24)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'dummy', 'hand': 'right',
     'prop': 'dummy', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'dummy',
     'channel': 'crush_progress', 'from': 0.0, 'to': 1.0},
]

# Beat 25: "But his hammer made the bottom gentle,"
f_in, f_out = frame_range(25)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'builder', 'hand': 'right',
     'prop': 'hammer', 'socket': 'grip_main'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'loop_track',
     'channel': 'bend_bottom', 'from': 0.0, 'to': 0.2},
]

# Beat 26: "and the rival's squeeze moved the hairpin up top,"
f_in, f_out = frame_range(26)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'rival', 'hand': 'right',
     'prop': 'turnbuckle', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'loop_track',
     'channel': 'squeeze_sides', 'from': 0.0, 'to': 1.0},
]

# Beat 27: "where the cart is crawling."
f_in, f_out = frame_range(27)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'cart', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 0.05},
]

# Beat 28: "So he floats over without a scratch."
f_in, f_out = frame_range(28)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'cart', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.05, 'to': 0.25},
]

# Beat 29: "Just as the rival's cart hits the bottom of that perfect circle."
f_in, f_out = frame_range(29)
acting['actions'] += [
    {'f_in': f_in, 'f_out': f_out, 'act': 'hold', 'char': 'rival', 'hand': 'right',
     'prop': 'cart', 'socket': 'hand'},
    {'f_in': f_in, 'f_out': f_out, 'act': 'operate', 'prop': 'cart',
     'channel': 'track_progress', 'from': 0.0, 'to': 0.0},
]

with open('acting.json', 'w') as f:
    json.dump(acting, f, indent=2)

print(f"Generated acting.json with {len(acting['actions'])} actions across {len(beats)} beats")
print(f"Total frames: {TOTAL_FRAMES}")
