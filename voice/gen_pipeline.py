import asyncio
import json
import os
import subprocess
import edge_tts
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel

SCRIPT_PARAGRAPHS = [
    # 0: Hook (Question)
    "Why can't you just print trillions of dollars on your office printer?",
    # 1: Solution 1
    "Because real cash is forged under twenty tons of mechanical pressure, using steel plates that physically engrave sharp 3D ridges.",
    # 2: Problem 1
    "The problem? Ordinary wood paper under twenty tons of force disintegrates into wet oatmeal.",
    # 3: Solution 2
    "The solution: cash isn't paper. It's a secret cotton-linen cloth that survives four thousand double folds.",
    # 4: Problem 2
    "The problem? Counterfeiters can buy cotton and copy the green ink.",
    # 5: Solution 3
    "The solution is quantum optics. The numerals use magnetic ink that flips from copper to emerald when tilted three degrees.",
    # 6: Problem 3
    "The problem? High-res digital scanners don't tilt. They copy every pixel flat.",
    # 7: Solution 4
    "The solution: the EURion constellation. A five-ring pattern hidden on the bill that forces scanner hardware to instantly freeze.",
    # 8: Problem 4
    "The problem? What stops a rogue government printer from running extra sheets at midnight?",
    # 9: Solution 5
    "The solution: robotic cameras scanning ten thousand sheets an hour. If one millimeter is off, it gets laser-shredded into briquettes.",
    # 10: Callback Twist
    "Which means that dollar in your pocket isn't paper. It's high-tech armor disguised as pocket change."
]

async def build_voice():
    os.makedirs("voice/raw", exist_ok=True)
    wav_files = []
    
    # Generate each line with rate="+22%"
    for i, line in enumerate(SCRIPT_PARAGRAPHS):
        part_mp3 = f"voice/raw/p_{i:02d}.mp3"
        part_wav = f"voice/raw/p_{i:02d}.wav"
        comm = edge_tts.Communicate(line, "en-US-ChristopherNeural", rate="+22%")
        await comm.save(part_mp3)
        # Direct clean conversion to 48kHz mono 16-bit
        subprocess.run(["ffmpeg", "-y", "-i", part_mp3, "-ar", "48000", "-ac", "1", part_wav], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wav_files.append(part_wav)

    # Concat with 0.1s gap between lines
    gap = np.zeros(int(48000 * 0.10), dtype=np.float32)
    combined = []
    for f in wav_files:
        d, sr = sf.read(f)
        if d.ndim > 1:
            d = d.mean(axis=1)
        combined.append(d.astype(np.float32))
        combined.append(gap)
    
    full_audio = np.concatenate(combined[:-1])
    wav_path = "voice/voice.wav"
    sf.write(wav_path, full_audio, 48000)
    dur = len(full_audio) / 48000.0
    print(f"Generated voice/voice.wav: {dur:.2f} seconds ({int(round(dur * 30))} frames @ 30fps).")
    
    # Convert to 16kHz for whisper
    wav_16k = "voice/voice_16k.wav"
    subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-ar", "16000", "-ac", "1", wav_16k], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Run faster-whisper alignment at 16kHz
    print("Running word-level alignment at 16kHz...")
    d16, _ = sf.read(wav_16k)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(d16, word_timestamps=True, language="en")
    
    words_data = []
    for segment in segments:
        for word in segment.words:
            w = word.word.strip()
            if w:
                words_data.append({
                    "word": w,
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "frame": int(round(word.start * 30))
                })
                
    with open("voice/words.json", "w", encoding="utf-8") as f:
        json.dump(words_data, f, indent=2)
    print(f"Saved {len(words_data)} aligned words to voice/words.json.")

if __name__ == "__main__":
    asyncio.run(build_voice())
