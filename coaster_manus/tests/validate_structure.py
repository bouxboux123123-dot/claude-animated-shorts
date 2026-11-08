"""Fast source-package checks; works in ordinary Python without Blender/bpy."""
from __future__ import annotations
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    for path in ROOT.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    shots = json.loads((ROOT / "shots.json").read_text(encoding="utf-8"))
    acting = json.loads((ROOT / "acting.json").read_text(encoding="utf-8"))
    assert len(shots["shots"]) == 29
    assert shots["frame_count"] == 1887 and shots["fps"] == 30
    assert shots["shots"][0]["frame_start"] == 1
    assert shots["shots"][-1]["frame_end"] == 1887
    for prev, current in zip(shots["shots"], shots["shots"][1:]):
        assert prev["frame_end"] + 1 == current["frame_start"]
        assert prev["end"] == current["start"]
    assert set(acting["verbs"]) == {"hold", "operate", "clasp", "emotion", "impact"}
    assert all(item["verb"] in acting["verbs"] for item in acting["actions"])
    source = (ROOT / "lib" / "props.py").read_text(encoding="utf-8")
    required = {
        "LoopTrackProp": ("bend_bottom", "squeeze_sides"),
        "SledgehammerProp": ("swing_stroke",),
        "TestDummyProp": ("crush_progress",),
        "TurnbuckleCrankProp": ("crank_angle",),
        "CoasterCartProp": ("track_progress",),
    }
    for cls, channels in required.items():
        assert f"class {cls}(PropSpec)" in source
        for channel in channels:
            assert f'"{channel}"' in source
    print("PASS: source syntax; 29 contiguous shots / 1,887 frames; acting verbs and prop channels")


if __name__ == "__main__":
    main()
