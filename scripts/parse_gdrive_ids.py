import urllib.request
import re

url = "https://drive.google.com/drive/folders/19GbJMy2OYDy8WG1CbknjM_ukXesCvAwE?usp=sharing"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")

# Find patterns like "1abc...xyz", "cartoon-short-kit.zip"
for m in re.finditer(r'\["([a-zA-Z0-9_-]{25,})",\["([^"]+)"', html):
    print(m.groups())

# Also search around cartoon-short-kit.zip
idx = html.find("cartoon-short-kit.zip")
if idx != -1:
    print("Around cartoon-short-kit:", html[max(0, idx - 200):idx + 200])

idx_skill = html.find("SKILL.md")
if idx_skill != -1:
    print("Around SKILL.md:", html[max(0, idx_skill - 200):idx_skill + 200])
