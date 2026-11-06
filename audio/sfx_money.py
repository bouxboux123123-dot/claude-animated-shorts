# Synthesized SFX for "How Money Is Printed"
# Pure DSP using numpy + scipy (dsp.py)
import numpy as np
from scipy import signal
import timeline as T
from dsp import SR, ns, tt, lp, hp, bp, st, dbg, write_wav

def make_sfx():
    N = ns(T.DUR)
    sfx = np.zeros(N, dtype=np.float32)

    def add_hit(t0, sound, gain_db=0.0):
        i0 = ns(t0)
        i1 = min(N, i0 + len(sound))
        if i0 < N:
            sfx[i0:i1] += sound[:i1 - i0] * dbg(gain_db)

    # 1. Flash & Office Printer (t = 0.5s & 3.03s)
    t = tt(0.4)
    paper_feed = np.sin(2 * np.pi * 120 * t) * np.exp(-t * 12) + np.random.normal(0, 0.05, len(t)) * np.exp(-t * 20)
    add_hit(0.2, paper_feed, -6.0)

    # 2. 20-Ton Intaglio Stamp (t = 3.8s)
    t_stamp = tt(0.8)
    sub = np.sin(2 * np.pi * 55 * t_stamp * np.exp(-t_stamp * 4)) * np.exp(-t_stamp * 6)
    clang = (np.sin(2 * np.pi * 440 * t_stamp) + 0.5 * np.sin(2 * np.pi * 880 * t_stamp)) * np.exp(-t_stamp * 15)
    press_hit = lp(sub * 0.8 + clang * 0.3, 1200)
    add_hit(3.8, press_hit, +2.0)
    add_hit(5.5, press_hit, 0.0)

    # 3. Wet Oatmeal Water Squelch (t = 11.5s)
    t_wet = tt(0.6)
    noise = np.random.normal(0, 0.2, len(t_wet))
    squelch = bp(noise, 400, 2500) * np.exp(-t_wet * 5)
    add_hit(11.5, squelch, -4.0)

    # 4. Cotton Cloth Snap (t = 16.0s)
    t_snap = tt(0.3)
    snap = (np.sin(2 * np.pi * 950 * t_snap) + np.random.normal(0, 0.3, len(t_snap))) * np.exp(-t_snap * 25)
    add_hit(16.0, snap, -2.0)

    # 5. Counterfeiter Optical Ping (t = 22.0s)
    t_ping = tt(0.7)
    ping = np.sin(2 * np.pi * 1800 * t_ping) * np.exp(-t_ping * 8)
    add_hit(22.0, ping, -6.0)

    # 6. Quantum Color Tilt Shimmer (t = 26.5s)
    t_shim = tt(1.2)
    mod = np.sin(2 * np.pi * 8 * t_shim)
    shimmer = np.sin(2 * np.pi * (1200 + 400 * mod) * t_shim) * np.exp(-t_shim * 3)
    add_hit(26.5, shimmer, -5.0)

    # 7. Scanner Motor Hum (t = 32.0s)
    t_scan = tt(1.5)
    hum = (np.sin(2 * np.pi * 220 * t_scan) + 0.3 * np.sin(2 * np.pi * 440 * t_scan)) * (1 - np.exp(-t_scan * 5)) * np.exp(-t_scan * 1.5)
    add_hit(32.0, hum, -6.0)

    # 8. EURion Constellation Lock / Emergency Stop (t = 38.5s)
    t_lock = tt(0.9)
    alarm = (np.sin(2 * np.pi * 880 * t_lock) + np.sin(2 * np.pi * 1760 * t_lock)) * (np.sin(2 * np.pi * 16 * t_lock) > 0) * np.exp(-t_lock * 4)
    add_hit(38.5, alarm, -3.0)

    # 9. Midnight Rogue Operator Creak (t = 44.0s)
    t_creak = tt(1.0)
    creak = np.sin(2 * np.pi * 85 * np.exp(t_creak * 1.5)) * np.exp(-t_creak * 2)
    add_hit(44.0, creak, -5.0)

    # 10. Laser Shredder Grinder (t = 50.0s)
    t_shred = tt(1.8)
    saw = signal.sawtooth(2 * np.pi * 140 * t_shred) * np.exp(-t_shred * 2)
    grit = np.random.normal(0, 0.25, len(t_shred)) * np.exp(-t_shred * 2.5)
    shredder = lp(saw + grit, 3500)
    add_hit(50.0, shredder, 0.0)

    # 11. Armor Cash Impact / Chime (t = 56.5s)
    t_coin = tt(1.5)
    bell = (np.sin(2 * np.pi * 1560 * t_coin) + 0.6 * np.sin(2 * np.pi * 3120 * t_coin)) * np.exp(-t_coin * 3.5)
    thump = np.sin(2 * np.pi * 60 * t_coin) * np.exp(-t_coin * 8)
    add_hit(56.5, bell * 0.4 + thump * 0.8, -2.0)

    return st(sfx)

if __name__ == "__main__":
    audio = make_sfx()
    write_wav("audio/sfx_stem.wav", audio)
    print(f"Generated audio/sfx_stem.wav ({len(audio)/SR:.2f} s).")
