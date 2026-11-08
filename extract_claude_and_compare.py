import os
import subprocess
import cv2
import numpy as np

VIDEO_PATH = r"c:\Users\PC\Downloads\final-animated-reel\roller_coaster_claude_20x.mp4"
ARTIFACT_DIR = r"C:\Users\PC\.gemini\antigravity\brain\a4b0e298-f434-4e6d-a513-0b634e792487"

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

# 2. Extract key beat frames
beats = [
    ("B01_workshop_bent_loop", 1.0, "Beat 1: Workshop Bent Loop"),
    ("B03_workshop_builder", 6.0, "Beat 3: Builder at Workbench"),
    ("B06_dummy_crushed", 12.5, "Beat 6: Crushed Dummy"),
    ("B08_hammer_beat", 16.0, "Beat 8: Hammering Bottom Curve"),
    ("B12_rival_crank", 24.5, "Beat 12: Rival Cranking Sides"),
    ("B14_fairground_dawn", 30.0, "Beat 14: Fairground Dawn Queue"),
    ("B18_lift_crest", 38.5, "Beat 18: Approaching Squeezed Loop"),
    ("B26_clothoid_apex", 55.0, "Beat 26: Clothoid Apex Float"),
    ("B29_circle_bottom_hit", 61.0, "Beat 29: Circular Bottom Slam"),
]

cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Total frames: {total_frames}, FPS: {fps}")

extracted_images = []

for tag, t, title in beats:
    frame_no = int(t * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    if ret:
        out_name = f"claude_{tag}.jpg"
        out_path = os.path.join(ARTIFACT_DIR, out_name)
        cv2.imwrite(out_path, frame)
        extracted_images.append((title, frame))
        print(f"Extracted {out_name} at frame {frame_no} ({t}s)")
    else:
        print(f"Failed to read frame {frame_no} for {tag}")

cap.release()

# 3. Create 3x3 contact grid
# Standardize tile size: Claude is 16:9 (1920x1080)
tile_w = 480
tile_h = 270 # 16:9 aspect ratio

grid_rows = []
for r in range(3):
    row_tiles = []
    for c in range(3):
        idx = r * 3 + c
        if idx < len(extracted_images):
            title, img = extracted_images[idx]
            resized = cv2.resize(img, (tile_w, tile_h))
            # Add header banner
            banner = np.zeros((40, tile_w, 3), dtype=np.uint8)
            cv2.putText(banner, title, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            tile_with_banner = np.vstack([banner, resized])
            row_tiles.append(tile_with_banner)
        else:
            blank = np.zeros((tile_h + 40, tile_w, 3), dtype=np.uint8)
            row_tiles.append(blank)
    grid_rows.append(np.hstack(row_tiles))

contact_grid = np.vstack(grid_rows)
grid_path = os.path.join(ARTIFACT_DIR, "claude_coaster_contact_grid.jpg")
cv2.imwrite(grid_path, contact_grid)
print(f"Created Claude contact grid: {grid_path} ({contact_grid.shape})")
