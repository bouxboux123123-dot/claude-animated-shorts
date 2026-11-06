import json
with open('voice/words.json') as f:
    w = json.load(f)
for i in range(0, len(w), 8):
    chunk = w[i:i+8]
    txt = ' '.join(f"{x['word']}[{x['frame']}]" for x in chunk)
    print(f"{i:3d}: {txt}")
