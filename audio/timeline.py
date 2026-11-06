# Picture timeline mirrored for "How Money Is Printed"
# Exact frame and second boundaries for audio ducking and SFX cues.
import math
import numpy as np

FPS = 30
TOTAL = 1788
DUR = TOTAL / FPS # 59.60 s exactly
fr = lambda f: f / FPS

# Key event times (seconds)
FLASH = fr(91)
INTAGLIO_STAMP = fr(120)
WATER_SPLASH = fr(340)
FOLD_SNAP = fr(540)
MAGNIFY_POP = fr(660)
COLOR_TILT = fr(830)
SCANNER_BEEP = fr(980)
EURION_LOCK = fr(1220)
ROGUE_CREAK = fr(1340)
LASER_SHRED = fr(1540)
PAYOFF_RING = fr(1720)

# id: (first frame, end frame, light, stage)
SHOTS = {
    1: (0, 91, "day", "hook"),
    2: (91, 284, "day", "intaglio"),
    3: (284, 434, "day", "wash"),
    4: (434, 610, "day", "cloth"),
    5: (610, 728, "golden", "counterfeit"),
    6: (728, 919, "golden", "quantum"),
    7: (919, 1085, "day", "scanner"),
    8: (1085, 1289, "day", "eurion"),
    9: (1289, 1423, "golden", "midnight"),
    10: (1423, 1628, "day", "shredder"),
    11: (1628, TOTAL, "golden", "twist")
}

XFADE = {3: 6, 5: 6, 7: 6, 9: 6, 11: 6}

def shot_t(i):
    a, b = SHOTS[i][:2]
    return fr(a), fr(b)

def shot_at(t):
    f = t * FPS
    for i, (a, b, *_r) in SHOTS.items():
        if a <= f < b:
            return i
    return 11
