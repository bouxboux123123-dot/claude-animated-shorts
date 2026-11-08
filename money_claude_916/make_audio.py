import asyncio
import edge_tts
import subprocess
import os

BEATS = [
    (0.0, 2.8, "Why don't we just print a billion dollars for everybody, and we all get rich?"),
    (2.8, 5.6, "It sounds like genius. Until you actually do it."),
    (5.6, 8.5, "Imagine there are only ten people on an island, and only ten loaves of bread."),
    (8.5, 11.2, "Everyone has one dollar, so a loaf costs one dollar. Simple."),
    (11.2, 14.0, "Now, the government cranks the printing press all night long..."),
    (14.0, 16.8, "...and drops a million dollars onto everyone's doorstep."),
    (16.8, 19.5, "You're a millionaire! You sprint to the bakery to buy breakfast."),
    (19.5, 22.4, "Except... all nine other people are already standing in line,"),
    (22.4, 25.0, "and there are still only ten loaves of bread in the oven."),
    (25.0, 28.0, "You slam down a thousand dollars: Give me that loaf!"),
    (28.0, 31.0, "The guy behind you shouts: I'll pay ten thousand!"),
    (31.0, 34.2, "The lady in back yells: ONE HUNDRED THOUSAND!"),
    (34.2, 37.0, "Within ten minutes, that single loaf of bread costs one million dollars."),
    (37.0, 40.0, "You didn't get richer. The paper just got weaker."),
    (40.0, 43.0, "Because money isn't wealth. Goods and services are wealth."),
    (43.0, 46.2, "If you double the money without doubling the bread, you just double the price."),
    (46.2, 49.0, "This happened in Germany in 1923,"),
    (49.0, 52.0, "where it was literally cheaper to burn banknotes than to buy firewood,"),
    (52.0, 55.0, "and children built play-castles out of stacks of cash in the streets."),
    (55.0, 58.0, "So printing money doesn't create wealth, it just steals value from every dollar in your pocket."),
    (58.0, 61.0, "Next time someone says just print more, hand them a loaf of bread and ask for your million back."),
]

VOICE = "en-US-ChristopherNeural"
OUTPUT_DIR = "temp_audio"

async def gen_clips():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clips = []
    for i, (t0, t1, text) in enumerate(BEATS):
        target_dur = t1 - t0
        raw_mp3 = os.path.join(OUTPUT_DIR, f"beat_{i:02d}_raw.mp3")
        # generate TTS
        comm = edge_tts.Communicate(text, VOICE, rate="+5%")
        await comm.save(raw_mp3)
        
        # probe duration
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", raw_mp3]
        dur = float(subprocess.check_output(cmd).decode().strip())
        print(f"Beat {i:02d} ({t0:4.1f}s - {t1:4.1f}s): target={target_dur:.2f}s, actual={dur:.2f}s: {text[:30]}...")
        
        # adjust speed slightly if needed using atempo so it fits cleanly into the beat interval
        speed = dur / (target_dur - 0.15) if dur > (target_dur - 0.1) else 1.0
        # clamp speed between 0.8 and 1.3
        speed = max(0.85, min(1.35, speed))
        
        timed_wav = os.path.join(OUTPUT_DIR, f"beat_{i:02d}.wav")
        # pad with silence or speed up
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_mp3,
            "-filter_complex", f"atempo={speed:.4f},apad=pad_dur={target_dur:.2f}",
            "-t", f"{target_dur:.2f}",
            "-ar", "44100", "-ac", "2", timed_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clips.append(timed_wav)
    
    # concat all clips
    concat_list = os.path.join(OUTPUT_DIR, "concat.txt")
    with open(concat_list, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")
    
    os.makedirs("public", exist_ok=True)
    final_wav = "public/money.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-ar", "44100", "-ac", "2", final_wav
    ], check=True)
    
    # Check total duration
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", final_wav]
    total_dur = float(subprocess.check_output(cmd).decode().strip())
    print(f"\nSUCCESS! Created {final_wav} with total duration: {total_dur:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(gen_clips())
