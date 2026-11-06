import asyncio
import json
import os
import subprocess
import edge_tts
from faster_whisper import WhisperModel

SCRIPT = """Why can't you just print trillions of dollars on your home office printer?
Because real currency isn't printed with inkjet—it's forged under twenty tons of mechanical pressure using intaglio steel plates that physically engrave microscopic ridges into the surface.
The problem? If you put ordinary wood paper under twenty tons of pressure, or leave it in the wash, it turns into soggy oatmeal.
The solution is that dollars aren't paper at all. It's a secret seventy-five percent cotton and twenty-five percent linen fabric woven with red and blue synthetic fibers that can survive four thousand double folds.
The problem? Counterfeiters can steal cotton linen and copy the green ink.
The solution is quantum optics. The numerals are printed with color-shifting ink containing magnetic flakes that flip from copper to emerald green when tilted by three degrees.
The problem? Modern scanners don't tilt—they capture twelve thousand DPI digital clones.
The solution is the EURion constellation. A secret five-ring geometric pattern that forces any commercial scanner or photocopier hardware to immediately shut down and refuse to scan.
The problem? What stops a rogue government press operator from running off extra sheets at midnight?
The solution is automated robotic inspection. High-speed cameras scan ten thousand sheets every hour at sub-millimeter precision. If a single millimeter is off, it gets laser-marked and ejected into industrial blades that chop it into solid briquettes.
Which means that dollar in your pocket isn't paper—it's high-tech armor disguised as pocket change."""

async def generate():
    mp3_path = "voice/voice.mp3"
    wav_path = "voice/voice.wav"
    
    # 3.7 words/s fast steady delivery (+8% rate)
    communicate = edge_tts.Communicate(SCRIPT, "en-US-ChristopherNeural", rate="+8%")
    await communicate.save(mp3_path)
    print("TTS generated mp3.")
    
    # Convert to 48kHz 16-bit mono wav
    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ar", "48000", "-ac", "1", wav_path], check=True)
    print("Converted to 48kHz wav.")
    
    # Extract word timestamps using faster-whisper
    print("Running faster-whisper alignment...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(wav_path, word_timestamps=True, language="en")
    
    words_data = []
    for segment in segments:
        for word in segment.words:
            clean_word = word.word.strip()
            if clean_word:
                words_data.append({
                    "word": clean_word,
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "probability": round(word.probability, 3)
                })
                
    with open("voice/words.json", "w", encoding="utf-8") as f:
        json.dump(words_data, f, indent=2)
        
    print(f"Alignment complete: {len(words_data)} words saved to voice/words.json.")
    print(f"Total duration: {info.duration:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(generate())
