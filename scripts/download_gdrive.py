import urllib.request
import os

files = [
    ("1VNvNonHXP_eDOaM87eb3qJkNbVDyp8tL", "out/cartoon-short-kit.zip"),
    ("1VV9w5JKzV2i8Mzoh_zEfkXyX3lhzBYCJ", "out/reachmora_SKILL.md")
]

for fid, out_path in files:
    url = f"https://drive.google.com/uc?export=download&id={fid}"
    print(f"Downloading {fid} -> {out_path}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(out_path, "wb") as out:
        out.write(resp.read())
    print("Done. Size:", os.path.getsize(out_path))
