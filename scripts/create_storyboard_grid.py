from PIL import Image, ImageDraw, ImageFont
import os
import glob

SHOTS = [
    ("Shot 1: Hook (Home Printer)", "out/stills/shot01_hook.png"),
    ("Shot 2: Solution 1 (Intaglio Press)", "out/stills/shot02_intaglio.png"),
    ("Shot 3: Problem 1 (Paper in Wash)", "out/stills/shot03_wash.png"),
    ("Shot 4: Solution 2 (Cotton Linen Cloth)", "out/stills/shot04_cloth.png"),
    ("Shot 5: Problem 2 (Counterfeiter)", "out/stills/shot05_counterfeiter.png"),
    ("Shot 6: Solution 3 (Color-Shifting Ink)", "out/stills/shot06_quantum.png"),
    ("Shot 7: Problem 3 (12k DPI Scanner)", "out/stills/shot07_scanner.png"),
    ("Shot 8: Solution 4 (EURion Freeze)", "out/stills/shot08_eurion.png"),
    ("Shot 9: Problem 4 (Midnight Rogue)", "out/stills/shot09_midnight.png"),
    ("Shot 10: Solution 5 (Laser Shredder)", "out/stills/shot10_shredder.png"),
    ("Shot 11: Payoff (High-Tech Armor)", "out/stills/shot11_armor.png"),
]

# Grid: 4 columns x 3 rows
cols = 4
rows = 3
thumb_w = 270
thumb_h = 480
header_h = 40

grid_w = cols * (thumb_w + 16) + 16
grid_h = rows * (thumb_h + header_h + 16) + 20

sheet = Image.new("RGB", (grid_w, grid_h), "#12141a")
draw = ImageDraw.Draw(sheet)

for i, (title, path) in enumerate(SHOTS):
    col = i % cols
    row = i // cols
    x = 16 + col * (thumb_w + 16)
    y = 16 + row * (thumb_h + header_h + 16)

    # Load and resize thumbnail
    im = Image.open(path).convert("RGB")
    im = im.resize((thumb_w, thumb_h), Image.LANCZOS)
    sheet.paste(im, (x, y + header_h))

    # Header label
    draw.rectangle([x, y, x + thumb_w, y + header_h], fill="#1e222d")
    draw.text((x + 6, y + 12), title, fill="#e6edf3")

out_local = "out/storyboard_grid.jpg"
out_artifact = "C:/Users/PC/.gemini/antigravity/brain/a4b0e298-f434-4e6d-a513-0b634e792487/storyboard_grid.jpg"

sheet.save(out_local, quality=92)
sheet.save(out_artifact, quality=92)
print("Saved storyboard grid to:", out_local, "and", out_artifact)
