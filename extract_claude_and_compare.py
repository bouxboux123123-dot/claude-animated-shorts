import subprocess
import os
import glob
from PIL import Image, ImageDraw, ImageFont

VIDEO_PATH = r"c:\Users\PC\Downloads\final-animated-reel\roller_coaster_claude_20x.mp4"
ARTIFACT_DIR = r"C:\Users\PC\.gemini\antigravity\brain\a4b0e298-f434-4e6d-a513-0b634e792487"
OUT_DIR = r"c:\sticky 3d\out_claude"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Probe video
cmd = [
    "ffprobe", "-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
    "-of", "default=noprint_wrappers=1", VIDEO_PATH
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("=== Claude Video Stream Info ===")
print(res.stdout)

# Check audio stream
cmd_a = [
    "ffprobe", "-v", "error", "-select_streams", "a:0",
    "-show_entries", "stream=codec_name,sample_rate,channels,duration",
    "-of", "default=noprint_wrappers=1", VIDEO_PATH
]
res_a = subprocess.run(cmd_a, capture_output=True, text=True)
print("=== Claude Audio Stream Info ===")
print(res_a.stdout)

# 2. Extract key beat frames matching ChatGPT and Gemini
key_frames = [
    (30, "01_workshop_loop", "Beat 1: Bent Loop"),
    (370, "06_dummy_crushed", "Beat 6: Crushed Dummy"),
    (510, "08_hammer_bend", "Beat 8: Hammering Bottom"),
    (700, "12_rival_crank", "Beat 12: Rival Cranking Sides"),
    (850, "14_fairground_dawn", "Beat 14: Fairground Dawn"),
    (1100, "18_lift_crest", "Beat 18: Approaching Squeezed Loop"),
    (1300, "21_climax_dual_loops", "Beat 21: Dual Loop Climax"),
    (1600, "26_hero_clothoid_apex", "Beat 26: Clothoid Apex Float"),
    (1820, "29_rival_circle_crash", "Beat 29: Circular Bottom Slam"),
]

extracted_files = []

for frame_num, label, title in key_frames:
    sec = frame_num / 30.0
    out_file = os.path.join(OUT_DIR, f"{label}_f{frame_num:04d}.jpg")
    cmd = [
        "ffmpeg", "-y", "-ss", f"{sec:.3f}", "-i", VIDEO_PATH,
        "-vframes", "1", "-q:v", "2", out_file
    ]
    subprocess.run(cmd, capture_output=True)
    if os.path.exists(out_file):
        print(f"Extracted {label}: {out_file} ({os.path.getsize(out_file)} bytes)")
        extracted_files.append((out_file, title))

# 3. Build 3x3 contact grid for Claude (widescreen 16:9 tiles)
thumb_w, thumb_h = 480, 270
grid = Image.new('RGB', (thumb_w * 3, thumb_h * 3), (20, 20, 20))
draw = ImageDraw.Draw(grid)

for idx, (f_path, title) in enumerate(extracted_files[:9]):
    row = idx // 3
    col = idx % 3
    with Image.open(f_path) as im:
        im_resized = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x_pos = col * thumb_w
        y_pos = row * thumb_h
        grid.paste(im_resized, (x_pos, y_pos))
        draw.rectangle([x_pos, y_pos, x_pos + thumb_w, y_pos + 26], fill=(0, 0, 0))
        draw.text((x_pos + 8, y_pos + 6), title, fill=(255, 255, 255))

claude_grid_path = os.path.join(ARTIFACT_DIR, "claude_coaster_contact_grid.jpg")
grid.save(claude_grid_path, quality=90)
print(f"Saved Claude contact grid to {claude_grid_path}")
