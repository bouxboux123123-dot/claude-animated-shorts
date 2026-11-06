import json

with open("voice/words.json") as f:
    words = json.load(f)

# Find key anchor words for our 11 shots
targets = [
    ("Shot 1: Hook (Home Printer)", "Why"),
    ("Shot 2: Solution 1 (Intaglio Press)", "Because"),
    ("Shot 3: Problem 1 (Ordinary Paper Tears)", "Ordinary"),
    ("Shot 4: Solution 2 (Cotton Linen Fabric)", "cotton-linen"),
    ("Shot 5: Problem 2 (Counterfeiters Copy Ink)", "Counterfeiters"),
    ("Shot 6: Solution 3 (Color-Shifting Quantum Ink)", "quantum"),
    ("Shot 7: Problem 3 (High-Res Digital Scanners)", "High-res"),
    ("Shot 8: Solution 4 (EURion Constellation Locks Hardware)", "EURion"),
    ("Shot 9: Problem 4 (Rogue Midnight Printer)", "stops"),
    ("Shot 10: Solution 5 (Robotic Vision & Laser Shredder)", "robotic"),
    ("Shot 11: Callback Twist (High-Tech Armor)", "Which")
]

shot_markers = []
idx = 0
for title, kw in targets:
    for i in range(idx, len(words)):
        if kw.lower() in words[i]["word"].lower():
            shot_markers.append((title, words[i]["frame"], words[i]["start"], words[i]["word"]))
            idx = i + 1
            break

print("Shot Plan Breakdown:")
for i, (title, frame, sec, word) in enumerate(shot_markers):
    next_frame = shot_markers[i+1][1] if i + 1 < len(shot_markers) else 1788
    dur_f = next_frame - frame
    dur_s = dur_f / 30.0
    print(f"{title}: frames {frame:4d} - {next_frame:4d} ({dur_f:3d} f, {dur_s:4.1f} s) [starts on '{word}']")
