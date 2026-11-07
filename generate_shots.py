#!/usr/bin/env python3
"""Generate shots.json from the audio timeline for "Why Roller Coasters Don't Fly Off The Tracks".

29 beats, 62.9s total, 30 fps = 1887 frames.
Each beat maps to a camera setup and a set.
"""
import json
import math

FPS = 30.0
TOTAL_FRAMES = 1887

beats = [
    # beat, start_s, end_s, text
    (1,  0.0,  2.5,  "He bent the roller coaster's loop out of shape."),
    (2,  2.5,  5.4,  "You see, it's the first ride ever to go upside down,"),
    (3,  5.4,  7.0,  "and it cost him everything."),
    (4,  7.0,  9.7,  "So of course, his rival copies it bolt for bolt."),
    (5,  9.7,  11.2, "But the night before opening,"),
    (6,  11.2, 13.9, "his test dummy comes back crushed like a soda can,"),
    (7,  13.9, 15.2, "but he can't miss the opening,"),
    (8,  15.2, 17.2, "so he grabs a hammer and beats the bottom"),
    (9,  17.2, 19.2, "into a long, lazy curve."),
    (10, 19.2, 21.0, "Does he know what he's doing? Not really."),
    (11, 21.0, 23.1, "His rival laughs, then sneaks in,"),
    (12, 23.1, 26.3, "and cranks the sides together until the loop is tall and skinny."),
    (13, 26.3, 28.2, "So the first cart will snap like a twig."),
    (14, 28.2, 31.9, "The next morning, the town lines up at the rival's perfect circle,"),
    (15, 31.9, 33.9, "and the rival climbs in front to show off."),
    (16, 33.9, 35.3, "The owner climbs into his,"),
    (17, 35.3, 37.2, "and as his cart tips over the first hill,"),
    (18, 37.2, 39.9, "he finally sees the tall, skinny loop ahead."),
    (19, 39.9, 41.1, "But it's too late."),
    (20, 41.1, 44.0, "You see, a car can creep around a hairpin turn at five,"),
    (21, 44.0, 46.0, "but take it at 60, and it flips."),
    (22, 46.0, 48.2, "A cart is fastest at the bottom of a loop,"),
    (23, 48.2, 50.7, "and a perfect circle puts a hairpin right there,"),
    (24, 50.7, 52.1, "which is what crushed the dummy."),
    (25, 52.1, 53.8, "But his hammer made the bottom gentle,"),
    (26, 53.8, 56.5, "and the rival's squeeze moved the hairpin up top,"),
    (27, 56.5, 57.5, "where the cart is crawling."),
    (28, 57.5, 59.8, "So he floats over without a scratch."),
    (29, 59.8, 62.9, "Just as the rival's cart hits the bottom of that perfect circle."),
]

shots = []
for i, (idx, t0, t1, text) in enumerate(beats):
    f_in = int(round(t0 * FPS))
    f_out = int(round(t1 * FPS))
    if i == len(beats) - 1:
        f_out = TOTAL_FRAMES

    # Map each beat to set and camera choreography
    if idx <= 13:
        # Beats 1-13: night workshop (builder hammering, rival sneaking in)
        sid = 'workshop_night'
        if idx == 1:
            cam = [
                {'pos': (-0.8, -1.5, 1.2), 'target': (0.5, 0, 0.8), 'lens': 35, 'roll_deg': -8.0},
                {'pos': (-0.6, -1.2, 1.0), 'target': (0.5, 0, 0.8), 'lens': 35, 'roll_deg': -8.0},
            ]
        elif idx == 2:
            cam = [
                {'pos': (0.0, -2.0, 1.5), 'target': (0.0, 0.0, 0.5), 'lens': 28, 'roll_deg': 0.0},
                {'pos': (0.0, -1.5, 1.2), 'target': (0.0, 0.0, 0.5), 'lens': 28, 'roll_deg': 0.0},
            ]
        elif idx == 3:
            cam = [
                {'pos': (-0.5, -1.8, 1.4), 'target': (0.0, 0.0, 0.6), 'lens': 45, 'roll_deg': 5.0},
                {'pos': (-0.4, -1.5, 1.3), 'target': (0.0, 0.0, 0.6), 'lens': 45, 'roll_deg': 5.0},
            ]
        elif idx == 4:
            cam = [
                {'pos': (-1.0, -2.2, 1.0), 'target': (0.5, 0.0, 0.7), 'lens': 35, 'roll_deg': -5.0},
                {'pos': (-0.8, -1.8, 0.9), 'target': (0.5, 0.0, 0.7), 'lens': 35, 'roll_deg': -5.0},
            ]
        elif idx == 5:
            cam = [
                {'pos': (-0.7, -2.0, 1.3), 'target': (0.0, 0.0, 0.5), 'lens': 40, 'roll_deg': -10.0},
                {'pos': (-0.5, -1.6, 1.1), 'target': (0.0, 0.0, 0.5), 'lens': 40, 'roll_deg': -10.0},
            ]
        elif idx == 6:
            cam = [
                {'pos': (0.0, -0.8, 0.6), 'target': (1.5, 0.5, 0.0), 'lens': 55, 'roll_deg': 15.0},
                {'pos': (0.1, -0.6, 0.5), 'target': (1.5, 0.5, 0.0), 'lens': 55, 'roll_deg': 15.0},
            ]
        elif idx == 7:
            cam = [
                {'pos': (-0.6, -1.5, 1.2), 'target': (0.5, 0.0, 0.8), 'lens': 35, 'roll_deg': -8.0},
                {'pos': (-0.5, -1.2, 1.0), 'target': (0.5, 0.0, 0.8), 'lens': 35, 'roll_deg': -8.0},
            ]
        elif idx == 8:
            cam = [
                {'pos': (-0.5, -1.0, 1.0), 'target': (0.5, 0.0, 0.8), 'lens': 50, 'roll_deg': 12.0},
                {'pos': (-0.4, -0.8, 0.9), 'target': (0.5, 0.0, 0.8), 'lens': 50, 'roll_deg': 12.0},
            ]
        elif idx == 9:
            cam = [
                {'pos': (-0.4, -0.8, 0.9), 'target': (0.5, 0.0, 0.8), 'lens': 50, 'roll_deg': 8.0},
                {'pos': (-0.3, -0.6, 0.8), 'target': (0.5, 0.0, 0.8), 'lens': 50, 'roll_deg': 8.0},
            ]
        elif idx == 10:
            cam = [
                {'pos': (-0.6, -1.2, 1.1), 'target': (0.0, 0.0, 0.6), 'lens': 40, 'roll_deg': -12.0},
                {'pos': (-0.5, -1.0, 1.0), 'target': (0.0, 0.0, 0.6), 'lens': 40, 'roll_deg': -12.0},
            ]
        elif idx == 11:
            cam = [
                {'pos': (2.0, -1.2, 0.8), 'target': (0.5, 0.0, 0.8), 'lens': 35, 'roll_deg': 8.0},
                {'pos': (1.5, -1.0, 0.7), 'target': (0.5, 0.0, 0.8), 'lens': 35, 'roll_deg': 8.0},
            ]
        elif idx == 12:
            cam = [
                {'pos': (1.8, -1.0, 0.9), 'target': (0.5, 0.0, 0.8), 'lens': 40, 'roll_deg': 10.0},
                {'pos': (1.5, -0.8, 0.8), 'target': (0.5, 0.0, 0.8), 'lens': 40, 'roll_deg': 10.0},
            ]
        else:  # idx == 13
            cam = [
                {'pos': (1.5, -0.8, 1.0), 'target': (0.5, 0.0, 0.8), 'lens': 45, 'roll_deg': 8.0},
                {'pos': (1.2, -0.6, 0.9), 'target': (0.5, 0.0, 0.8), 'lens': 45, 'roll_deg': 8.0},
            ]
    elif idx <= 15:
        # Beats 14-15: morning fairground establishing
        sid = 'fairground_dawn'
        if idx == 14:
            cam = [
                {'pos': (-15.0, -10.0, 6.0), 'target': (0.0, 3.0, 2.0), 'lens': 28, 'roll_deg': 0.0},
                {'pos': (-12.0, -8.0, 5.0), 'target': (0.0, 3.0, 2.0), 'lens': 28, 'roll_deg': 0.0},
            ]
        else:  # idx == 15
            cam = [
                {'pos': (8.0, 1.0, 3.0), 'target': (5.0, 5.0, 0.0), 'lens': 35, 'roll_deg': -5.0},
                {'pos': (7.0, 0.5, 2.8), 'target': (5.0, 5.0, 0.0), 'lens': 35, 'roll_deg': -5.0},
            ]
    elif idx <= 20:
        # Beats 16-20: owner cart going up lift hill, sees loop
        sid = 'fairground_dawn'
        if idx == 16:
            cam = [
                {'pos': (5.0, 4.0, 1.0), 'target': (5.0, 4.5, 0.0), 'lens': 35, 'roll_deg': 0.0},
                {'pos': (4.5, 3.8, 0.9), 'target': (5.0, 4.5, 0.0), 'lens': 35, 'roll_deg': 0.0},
            ]
        elif idx == 17:
            cam = [
                {'pos': (-6.0, 2.0, 5.0), 'target': (0.0, 6.0, 4.0), 'lens': 35, 'roll_deg': 8.0},
                {'pos': (-5.0, 1.5, 4.5), 'target': (0.0, 6.0, 4.0), 'lens': 35, 'roll_deg': 8.0},
            ]
        elif idx == 18:
            cam = [
                {'pos': (3.5, 3.0, 2.0), 'target': (4.0, 0.0, 3.0), 'lens': 30, 'roll_deg': 10.0},
                {'pos': (3.0, 2.5, 1.8), 'target': (4.0, 0.0, 3.0), 'lens': 30, 'roll_deg': 10.0},
            ]
        elif idx == 19:
            cam = [
                {'pos': (3.5, 2.0, 1.5), 'target': (4.0, 0.0, 2.0), 'lens': 40, 'roll_deg': 15.0},
                {'pos': (3.0, 1.8, 1.3), 'target': (4.0, 0.0, 2.0), 'lens': 40, 'roll_deg': 15.0},
            ]
        else:  # idx == 20
            cam = [
                {'pos': (8.0, 1.0, 3.0), 'target': (4.0, 0.0, 2.75), 'lens': 28, 'roll_deg': 0.0},
                {'pos': (7.0, 0.5, 2.8), 'target': (4.0, 0.0, 2.75), 'lens': 28, 'roll_deg': 0.0},
            ]
    else:
        # Beats 21-29: coaster climax - tight loop shots, cross-cut rival vs owner
        sid = 'coaster_climax'
        if idx == 21:
            cam = [
                {'pos': (4.0, -1.0, 2.0), 'target': (4.0, 0.0, 2.75), 'lens': 45, 'roll_deg': 20.0},
                {'pos': (4.0, -0.5, 1.8), 'target': (4.0, 0.0, 2.75), 'lens': 45, 'roll_deg': 20.0},
            ]
        elif idx == 22:
            cam = [
                {'pos': (4.0, -0.8, 1.5), 'target': (4.0, 0.0, 1.0), 'lens': 50, 'roll_deg': 25.0},
                {'pos': (4.0, -0.4, 1.2), 'target': (4.0, 0.0, 1.0), 'lens': 50, 'roll_deg': 25.0},
            ]
        elif idx == 23:
            cam = [
                {'pos': (4.0, -0.5, 2.0), 'target': (4.0, 0.0, 2.75), 'lens': 35, 'roll_deg': 10.0},
                {'pos': (4.0, -0.2, 1.8), 'target': (4.0, 0.0, 2.75), 'lens': 35, 'roll_deg': 10.0},
            ]
        elif idx == 24:
            cam = [
                {'pos': (4.0, 2.0, 0.5), 'target': (4.0, 0.0, 0.3), 'lens': 55, 'roll_deg': 30.0},
                {'pos': (4.0, 1.5, 0.4), 'target': (4.0, 0.0, 0.3), 'lens': 55, 'roll_deg': 30.0},
            ]
        elif idx == 25:
            cam = [
                {'pos': (4.0, 0.0, 2.75), 'target': (4.0, 0.0, 2.0), 'lens': 40, 'roll_deg': 0.0},
                {'pos': (4.0, 0.2, 2.5), 'target': (4.0, 0.0, 2.0), 'lens': 40, 'roll_deg': 0.0},
            ]
        elif idx == 26:
            cam = [
                {'pos': (-4.0, -1.0, 2.0), 'target': (-4.0, 0.0, 2.75), 'lens': 35, 'roll_deg': -10.0},
                {'pos': (-4.0, -0.5, 1.8), 'target': (-4.0, 0.0, 2.75), 'lens': 35, 'roll_deg': -10.0},
            ]
        elif idx == 27:
            cam = [
                {'pos': (-4.0, 0.0, 2.75), 'target': (-4.0, 0.0, 2.0), 'lens': 40, 'roll_deg': 0.0},
                {'pos': (-4.0, 0.2, 2.5), 'target': (-4.0, 0.0, 2.0), 'lens': 40, 'roll_deg': 0.0},
            ]
        elif idx == 28:
            cam = [
                {'pos': (4.0, -1.0, 2.0), 'target': (4.0, 0.0, 2.75), 'lens': 35, 'roll_deg': -5.0},
                {'pos': (4.0, -0.5, 1.8), 'target': (4.0, 0.0, 2.75), 'lens': 35, 'roll_deg': -5.0},
            ]
        else:  # idx == 29
            cam = [
                {'pos': (-4.0, 2.0, 0.5), 'target': (-4.0, 0.0, 0.3), 'lens': 55, 'roll_deg': -30.0},
                {'pos': (-4.0, 1.5, 0.4), 'target': (-4.0, 0.0, 0.3), 'lens': 55, 'roll_deg': -30.0},
            ]

    shots.append({
        'id': f"s{idx:02d}",
        'beat': idx,
        'f_in': f_in,
        'f_out': f_out,
        'set': sid,
        'text': text,
        'camera': cam
    })

with open('shots.json', 'w') as f:
    json.dump(shots, f, indent=2)

print(f"Generated {len(shots)} shots in shots.json")
print(f"Total frames: {TOTAL_FRAMES}")