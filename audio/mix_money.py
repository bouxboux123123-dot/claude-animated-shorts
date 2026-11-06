# Master Audio Mix for "How Money Is Printed"
# Combines voice narration + synthesized SFX + dynamic march beat bed.
# Implements EBU R128 loudness normalization (-14.0 LUFS) & true peak limiting (<= -1.2 dBTP).

import os
import json
import numpy as np
from dsp import (
    SR, ns, tt, lp, hp, bp, st, dbg, read_wav, write_wav,
    integrated, true_peak, fades
)
import timeline as T

def mix_soundtrack():
    print("Mixing soundtrack...")
    N = ns(T.DUR)

    # 1. Load voice track
    voice_raw, _ = read_wav("voice/voice.wav")
    voice = st(voice_raw)
    
    # Pad voice to exact length N if needed
    if voice.shape[1] < N:
        pad = np.zeros((2, N - voice.shape[1]), dtype=np.float32)
        voice = np.concatenate([voice, pad], axis=1)
    else:
        voice = voice[:, :N]

    # 2. Load SFX stem
    sfx_raw, _ = read_wav("audio/sfx_stem.wav")
    if sfx_raw.shape[1] < N:
        pad = np.zeros((2, N - sfx_raw.shape[1]), dtype=np.float32)
        sfx = np.concatenate([sfx_raw, pad], axis=1)
    else:
        sfx = sfx_raw[:, :N]

    # 3. Synthesize rhythmic march bed (2 steps/s = 120 BPM march)
    t = tt(T.DUR)
    bpm = 124
    beat_dur = 60.0 / bpm
    n_beats = int(T.DUR / beat_dur)
    bed = np.zeros(N, dtype=np.float32)

    snare_len = int(0.18 * SR)
    t_snare = np.arange(snare_len) / SR
    noise = np.random.normal(0, 0.3, snare_len)
    snare = bp(noise, 800, 4500) * np.exp(-t_snare * 22)
    snare += np.sin(2 * np.pi * 185 * t_snare) * np.exp(-t_snare * 30) * 0.4

    kick_len = int(0.22 * SR)
    t_kick = np.arange(kick_len) / SR
    f_kick = 110 * np.exp(-t_kick * 28) + 45
    kick = np.sin(2 * np.pi * f_kick * t_kick) * np.exp(-t_kick * 14) * 0.6

    for b in range(n_beats):
        pos = int(b * beat_dur * SR)
        if b % 2 == 0:
            end = min(N, pos + kick_len)
            bed[pos:end] += kick[:end - pos]
        else:
            end = min(N, pos + snare_len)
            bed[pos:end] += snare[:end - pos]

    music = st(bed)

    # 4. Ducking bed under speech
    with open("voice/words.json") as f:
        words = json.load(f)

    duck_gain = np.ones(N, dtype=np.float32)
    for w in words:
        i0 = max(0, ns(w["start"] - 0.05))
        i1 = min(N, ns(w["end"] + 0.08))
        duck_gain[i0:i1] = dbg(-8.0) # -8 dB ducking

    # Smooth ducking gain transitions
    smooth_win = int(0.04 * SR)
    kernel = np.hanning(smooth_win)
    kernel /= kernel.sum()
    duck_gain = np.convolve(duck_gain, kernel, mode="same")
    music = music * duck_gain

    # 5. Summing stems
    # Rule: music +3 dB, SFX -6 dB, voice unchanged
    mix = voice + sfx * dbg(-6.0) + music * dbg(-8.0)

    # 6. EBU R128 loudness mastering to -14.0 LUFS
    cur_lufs = integrated(mix)
    gain_needed = -14.0 - cur_lufs
    print(f"Current integrated loudness: {cur_lufs:.1f} LUFS. Applying {gain_needed:+.1f} dB gain.")
    mix = mix * dbg(gain_needed)

    # Limiter for true peak <= -1.2 dBTP
    peak = true_peak(mix)
    print(f"Peak before ceiling: {peak:.2f} dBTP")
    if peak > -1.2:
        mix = mix * dbg(-1.2 - peak)

    final_lufs = integrated(mix)
    final_peak = true_peak(mix)
    print(f"Mastering complete: {final_lufs:.1f} LUFS, {final_peak:.2f} dBTP.")

    # Save to audio/mix.wav and public/voice.wav
    write_wav("audio/mix.wav", mix)
    write_wav("public/voice.wav", mix)
    print("Master audio saved to audio/mix.wav and public/voice.wav.")

if __name__ == "__main__":
    mix_soundtrack()
