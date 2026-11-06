import subprocess
import os

SHOTS = [
    (1, 45, "shot01_hook"),
    (2, 180, "shot02_intaglio"),
    (3, 360, "shot03_wash"),
    (4, 520, "shot04_cloth"),
    (5, 670, "shot05_counterfeiter"),
    (6, 820, "shot06_quantum"),
    (7, 1000, "shot07_scanner"),
    (8, 1190, "shot08_eurion"),
    (9, 1350, "shot09_midnight"),
    (10, 1520, "shot10_shredder"),
    (11, 1700, "shot11_armor")
]

os.makedirs("out/stills", exist_ok=True)
for num, frame, name in SHOTS:
    out_path = f"out/stills/{name}.png"
    print(f"Rendering Shot {num} at frame {frame} -> {out_path}...")
    cmd = [
        "npx", "remotion", "still", "src/index.ts", "MoneyShort",
        out_path, f"--frame={frame}", "--scale=0.5"
    ]
    subprocess.run(cmd, shell=True, check=True)
print("All 11 shot stills rendered successfully!")
