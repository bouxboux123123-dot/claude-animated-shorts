import urllib.request
import re
import json

url = "https://drive.google.com/drive/folders/19GbJMy2OYDy8WG1CbknjM_ukXesCvAwE?usp=sharing"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    print("HTML length:", len(html))
    # Look for file names and IDs
    matches = re.findall(r'\["([a-zA-Z0-9_-]{25,})",\["([^"]+)"', html)
    print("Found files:", matches)
    for m in re.finditer(r'([A-Za-z0-9_ -]+\.(?:md|zip|py|json|tsx|ts|txt))', html):
        print("File match:", m.group(0))
except Exception as e:
    print("Error:", e)
