"""scene.py  --  Director + headless CLI renderer

    blender -b -P scene.py -- --frames 0-1886 --out frames/ [--shard 3/32] [--res 1920x1080] [--samples 24]
    blender -b -P scene.py -- --plan 32          # print one command per cloud worker
    blender -b -P scene.py -- --selftest         # determinism check (random-order double evaluation)
    blender -b -P scene.py -- --save-blend story.blend

apply_frame_actions(f) is the ONLY thing that mutates the scene between frames.  It first resets every
prop/character to defaults and then rebuilds all state from shots.json + acting.json as a pure function
of f, so frames can be rendered in any order, on any machine, in parallel.
"""
import json
import math
import os
import random
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy                                   # noqa: E402
from mathutils import Quaternion, Vector     # noqa: E402

from lib import chars as C, look, props as P, sets as S   # noqa: E402

FPS, TOTAL = 30, 1887
GRIP_VERBS = ("hold", "clasp")
SIDES = ("R", "L")


def _json(name):
    with open(os.path.join(HERE, name)) as fh:
        return json.load(fh)


def eval_keys(keys, t, prev, res):
    """keys = [(time, value|None, ease)].  None = 'value the channel had before this event'."""
    if t >= keys[-1][0]:
        return prev if keys[-1][1] is None else res(keys[-1][1])
    for i in range(len(keys) - 1):
        t0, v0, _ = keys[i]
        t1, v1, e = keys[i + 1]
        if t < t1:
            a = prev if v0 is None else res(v0)
            b = prev if v1 is None else res(v1)
            return P.lerp(a, b, P.ease(e, (t - t0) / (t1 - t0)))
    return prev


class Director:
    def __init__(self, res=(1920, 1080), samples=24):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.sc = bpy.context.scene
        shots = _json("shots.json")
        acting = _json("acting.json")
        cfg_res = shots.get("render", {}).get("res")
        look.configure_render(self.sc, res or cfg_res or (1920, 1080), samples, FPS, TOTAL)
        self.sets = S.build_sets()
        look.build_world()
        look.build_lighting_rigs(S.ANCHORS)
        self.props, self.chars = {}, {}
        for pid, d in acting["cast"]["props"].items():
            self.props[pid] = P.PROP_TYPES[d["type"]](pid, **d.get("opts", {}))
        for cid, d in acting["cast"]["chars"].items():
            self.chars[cid] = C.CardChar(cid, d["style"])
        for a, b in acting["cast"].get("links", {}).items():
            self.props[a].link(self.props[b["loop"]], b.get("turns", 3.0))
        self.sparks = look.FXPool("sparks", "sparks", 6, 14, look.flat_material("fx_spark", (1.0, 0.72, 0.18), 1.0),
                                  [(-0.5, 0), (0, 0.10), (0.5, 0), (0, -0.10)], 0.6)
        self.dust = look.FXPool("dust", "dust", 4, 9, look.toon_material("fx_dust", (0.82, 0.76, 0.66)), look.ellipse(0.5, 0.42, 10), 0.9)
        cam = bpy.data.cameras.new("cam")
        cam.sensor_width, cam.clip_start, cam.clip_end = 36.0, 0.1, 500.0
        self.cam = bpy.data.objects.new("CAMERA", cam)
        self.sc.collection.objects.link(self.cam)
        self.sc.camera = self.cam
        self._compile(shots, acting)

    # --------------------------------------------------------------------------- compile
    def _compile(self, shots, acting):
        self.shots = shots["shots"]
        for s in self.shots:
            s["f0"], s["f1"] = round(s["t0"] * FPS), round(s["t1"] * FPS)
        assert self.shots[0]["f0"] == 0 and self.shots[-1]["f1"] == TOTAL, "shots must cover frames 0..%d" % (TOTAL - 1)
        assert all(a["f1"] == b["f0"] for a, b in zip(self.shots, self.shots[1:])), "shots must be contiguous"
        self.chan, self.grips, self.emos, self.impacts = {}, [], {}, []
        for ev in acting["events"]:
            v = ev["verb"]
            if v == "operate":
                keys = [(k[0], k[1], k[2] if len(k) > 2 else "inout") for k in ev["keys"]]
                self.chan.setdefault((ev["prop"], ev["channel"]), []).append({"keys": keys, "t0": keys[0][0], "ev": ev})
            elif v in GRIP_VERBS:
                self.grips.append(ev)
            elif v == "emotion":
                self.emos.setdefault(ev["actor"], []).append(ev)
            elif v == "impact":
                self.impacts.append(ev)
            else:
                raise ValueError("unknown verb " + v)
        for lst in self.chan.values():
            lst.sort(key=lambda e: e["t0"])
        for lst in self.emos.values():
            lst.sort(key=lambda e: e["t0"])
        self.impacts.sort(key=lambda e: e["t"])
        for i, ev in enumerate(self.impacts):
            ev["_f0"], ev["_slot"], ev["_seed"] = round(ev["t"] * FPS), i, zlib.crc32(("%s%d" % (ev.get("id", ""), i)).encode())
        for lst in self.chan.values():                       # "characters MUST physically grip what they drive"
            for e in lst:
                ev, via = e["ev"], e["ev"].get("via", e["ev"]["prop"])
                if ev.get("actor") is None:      # physical / environmental events (ride physics, crush replay, resets)
                    continue
                ok = any(g["actor"] == ev["actor"] and g["t0"] <= e["t0"] + 1e-6 and g["t1"] >= e["keys"][-1][0] - 1e-6 and
                         any(isinstance(h, list) and h[0] == via for h in g.get("hands", {}).values()) for g in self.grips)
                assert ok, "operate '%s' by %s has no covering hold/clasp on '%s' (t=%.2f)" % (ev.get("id"), ev["actor"], via, e["t0"])

    def shot_at(self, f):
        for s in self.shots:
            if s["f0"] <= f < s["f1"]:
                return s
        raise ValueError("frame %d outside 0..%d" % (f, TOTAL - 1))

    # --------------------------------------------------------------------------- the one entry point
    def apply(self, f):
        t = f / float(FPS)
        shot = self.shot_at(f)
        for n, s in self.sets.items():
            s.set_visible(n == shot["set"])
        look.set_mood(shot["mood"])
        for o in list(self.props.values()) + list(self.chars.values()):
            o.reset()
        self._stage(shot, t)
        self._channels(t, track=False)
        for p in self.props.values():
            p.propagate(self.props)
        order = sorted(self.props.values(), key=lambda p: p.kind != "loop_track")
        for p in order:
            if p.kind == "loop_track":
                p.update()
        self._channels(t, track=True)
        for p in order:
            if p.kind != "loop_track":
                p.update()
        self._acting(shot, t)
        bursts = self._fx(shot, f)
        self._camera(shot, f, bursts)
        for p in self.props.values():
            p.commit()
        for c in self.chars.values():
            c.commit()

    # --------------------------------------------------------------------------- stage
    def _stage(self, shot, t):
        st = shot["stage"]
        for pid, d in st.get("props", {}).items():
            p = self.props[pid]
            p.visible = True
            if "anchor" in d:
                p.pos = [a + b for a, b in zip(S.ANCHORS.get(d["anchor"]), d.get("offset", (0, 0, 0)))]
            p.rot, p.scale = math.radians(d.get("rot_deg", 0.0)), d.get("scale", 1.0)
        for pid, d in st.get("props", {}).items():
            if "track" in d:
                self.props[pid].bind(self.props[d["track"]])
        for cid, d in st.get("chars", {}).items():
            c = self.chars[cid]
            c.visible = True
            a = S.ANCHORS.get(d["anchor"])
            pos = list(a)
            mv = d.get("move")
            if mv:
                k = P.ease("inout", (t - mv["t0"]) / (mv["t1"] - mv["t0"]))
                b = S.ANCHORS.get(mv["to"])
                pos = [P.lerp(a[i], b[i], k) for i in range(3)]
                if 0.0 < k < 1.0:
                    pos[2] += mv.get("hop", 0.0) * abs(math.sin(2 * math.pi * 2.5 * (t - mv["t0"])))
            c.pos, c.scale, c.flip, c.rot = pos, d.get("scale", 1.0), d.get("face", 1.0), math.radians(d.get("rot_deg", 0.0))

    def _channels(self, t, track):
        for (pid, ch), lst in self.chan.items():
            if (ch == "track_progress") != track:
                continue
            p = self.props[pid]
            res = lambda v, p=p: p.marker(v[1:]) if isinstance(v, str) else v
            v = p.ch[ch]
            for e in lst:
                if t < e["t0"]:
                    break
                v = eval_keys(e["keys"], t, v, res)
            p.set_channel(ch, v)

    # --------------------------------------------------------------------------- acting
    def _acting(self, shot, t):
        for cid, c in self.chars.items():
            if not c.visible:
                continue
            # emotion (stateless blend between the two most recent emotion events)
            evs = [e for e in self.emos.get(cid, []) if e["t0"] <= t]
            cur = evs[-1] if evs else {"emotion": "neutral", "t0": 0.0, "blend": 0.01}
            prev = evs[-2]["emotion"] if len(evs) > 1 else "neutral"
            k = P.ease("inout", (t - cur["t0"]) / max(cur.get("blend", 0.25), 1e-3)) * cur.get("intensity", 1.0)
            c.params, c.mouth = C.blend_expr(prev, cur["emotion"], k)
            c.lean_extra = 0.8 * math.sin(2 * math.pi * t / 3.1 + zlib.crc32(cid.encode()) % 7)
            c.tilt_extra = 1.5 * math.sin(2 * math.pi * t / 2.3)
            active = {}
            for g in self.grips:
                if g["actor"] == cid and g["t0"] <= t <= g["t1"]:
                    kin = P.smooth((t - g["t0"]) / max(g.get("blend", 0.3), 1e-3))
                    kout = P.smooth((g["t1"] - t) / max(g.get("blend_out", 0.3), 1e-3))
                    g = dict(g, _k=min(kin, kout))
                    active[id(g)] = g
                    if "root" in g:                                  # mount: body follows a prop socket
                        pr = self.props[g["root"][0]]
                        wx, wz = pr.socket_world(g["root"][1])
                        pos = [wx, pr.pos[1], wz]
                        c.pos = [P.lerp(c.pos[i], pos[i], g["_k"]) for i in range(3)]
                        c.rot = P.lerp(c.rot, pr.rot, g["_k"])
            hand = {}
            for g in active.values():
                for side, spec in g.get("hands", {}).items():
                    hand[side] = (spec, g["_k"])
            idle = {s: c.frame().to_world(*c.idle_local(s, t)) for s in SIDES}
            done = set()
            carried = {}
            for side in SIDES:                                       # 1) carried tools: hand drives the prop
                if side in hand and isinstance(hand[side][0], list) and self.props[hand[side][0][0]].carried:
                    carried.setdefault(hand[side][0][0], []).append(side)
            for pid, sides in carried.items():
                pr, side = self.props[pid], sides[0]
                spec, k = hand[side]
                th, rho = pr.hold_pose()
                sx, sz = c.shoulder_local(side)
                gw = c.frame().to_world(sx + rho * math.sin(th), sz + rho * math.cos(th))
                tgt = (P.lerp(idle[side][0], gw[0], k), P.lerp(idle[side][1], gw[1], k))
                hw = c.solve_arm(side, tgt)
                held_rot = c.rot + c.flip * th
                keep_pos, keep_rot = list(pr.pos), pr.rot
                pr.place_by_socket(spec[1], hw[0], hw[1], c.pos[1] - 0.5 * c.scale, held_rot)
                pr.pos = [P.lerp(keep_pos[i], pr.pos[i], k) for i in range(3)]
                pr.rot = P.lerp(keep_rot, pr.rot, k)
                done.add(side)
            for side in SIDES:                                       # 2) everything else: hand follows socket
                if side in done or side not in hand:
                    continue
                spec, k = hand[side]
                if isinstance(spec, list):
                    tw = self.props[spec[0]].socket_world(spec[1])
                else:
                    tw = c.frame().to_world(*spec["local"])
                c.solve_arm(side, (P.lerp(idle[side][0], tw[0], k), P.lerp(idle[side][1], tw[1], k)))
                done.add(side)
            for side in SIDES:
                if side not in done:
                    c.solve_arm(side, idle[side])

    # --------------------------------------------------------------------------- fx + camera
    def _fx(self, shot, f):
        bursts = []
        for ev in self.impacts:
            age = (f - ev["_f0"]) / float(FPS)
            if ev["_f0"] < shot["f0"] or age < 0 or age > 1.0:
                continue
            pr = self.props[ev["at"][0]]
            if not pr.visible:
                continue
            wx, wz = pr.socket_world(ev["at"][1])
            for kind in ev.get("kinds", ["sparks"]):
                bursts.append({"kind": kind, "f0": ev["_f0"], "slot": ev["_slot"], "seed": ev["_seed"],
                               "origin": (wx, pr.pos[1] - 0.6, wz), "strength": ev.get("strength", 1.0),
                               "shake": ev.get("shake", 0.0)})
        self.sparks.update(bursts, f, FPS)
        self.dust.update(bursts, f, FPS)
        return bursts

    def _point(self, spec):
        if isinstance(spec, list):
            return Vector(spec)
        off = Vector(spec.get("offset", (0, 0, 0)))
        if "anchor" in spec:
            return Vector(S.ANCHORS.get(spec["anchor"])) + off
        o = self.props.get(spec["follow"]) or self.chars[spec["follow"]]
        return Vector(o.pos) + off

    def _camera(self, shot, f, bursts):
        c = shot["cam"]
        k = P.ease(c.get("ease", "inout"), (f - shot["f0"]) / float(max(1, shot["f1"] - shot["f0"] - 1)))
        p0, l0 = self._point(c["pos"]), self._point(c["look"])
        p1, l1 = self._point(c.get("pos2", c["pos"])), self._point(c.get("look2", c["look"]))
        pos, look_at = p0.lerp(p1, k), l0.lerp(l1, k)
        seen = set()
        for b in bursts:
            age = (f - b["f0"]) / float(FPS)
            if b["shake"] > 0 and b["slot"] not in seen:
                seen.add(b["slot"])
                a = b["shake"] * math.exp(-9.0 * age)
                d = Vector((a * math.sin(83 * age + b["seed"] % 7), 0.0, a * math.cos(67 * age + b["seed"] % 5)))
                pos, look_at = pos + d, look_at + d
        q = (look_at - pos).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(c.get("roll", 0.0)))
        self.cam.location, self.cam.rotation_euler = pos, q.to_euler()
        self.cam.data.lens = P.lerp(c.get("lens", 35.0), c.get("lens2", c.get("lens", 35.0)), k)

    # --------------------------------------------------------------------------- misc
    def digest(self):
        r = lambda v: round(v, 4)
        fx = tuple(o.hide_render for o in self.sparks.objs + self.dust.objs)
        lights = tuple(o.hide_render for m in look.LIGHTS.values() for o in m)
        return (tuple(p.digest() for p in self.props.values()), tuple(c.digest() for c in self.chars.values()),
                tuple(r(v) for v in self.cam.location), tuple(r(v) for v in self.cam.rotation_euler), r(self.cam.data.lens),
                tuple(s.coll.hide_render for s in self.sets.values()), fx, lights, tuple(r(sum(o.scale) + sum(o.location)) for o in self.sparks.objs + self.dust.objs if not o.hide_render))


DIRECTOR = None


def apply_frame_actions(f):
    DIRECTOR.apply(int(f))


def render_frame(f, out_dir):
    apply_frame_actions(f)                                   # right before rendering
    sc = bpy.context.scene
    sc.frame_set(f)
    apply_frame_actions(f)                                   # frame_set must never be able to disturb state
    sc.render.filepath = os.path.join(out_dir, "frame_%05d.png" % f)
    bpy.ops.render.render(write_still=True)


def _parse(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="scene.py")
    ap.add_argument("--frames", default="0-%d" % (TOTAL - 1))
    ap.add_argument("--shard", default=None, help="i/n : render the i-th of n contiguous chunks")
    ap.add_argument("--out", default=os.path.join(HERE, "frames"))
    ap.add_argument("--res", default=None)
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--plan", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--save-blend", default=None)
    return ap.parse_args(argv)


def main():
    global DIRECTOR
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    a = _parse(argv)
    if a.plan:
        n, step = a.plan, math.ceil(TOTAL / a.plan)
        for i in range(n):
            lo, hi = i * step, min(TOTAL - 1, (i + 1) * step - 1)
            if lo <= hi:
                print("blender -b -P scene.py -- --frames %d-%d --out frames/ --skip-existing" % (lo, hi))
        return
    res = tuple(int(v) for v in a.res.lower().split("x")) if a.res else None
    DIRECTOR = Director(res, a.samples)
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
    if a.selftest:
        frames = sorted(set([0, TOTAL - 1] + [s["f0"] for s in DIRECTOR.shots] + [s["f1"] - 1 for s in DIRECTOR.shots] +
                            [round(x * 29.3) for x in range(1, 64)]))
        frames = [f for f in frames if 0 <= f < TOTAL]
        first = {}
        for f in frames:
            apply_frame_actions(f)
            first[f] = DIRECTOR.digest()
        order = frames[:]
        random.Random(7).shuffle(order)
        bad = []
        for f in order:
            apply_frame_actions(f)
            if DIRECTOR.digest() != first[f]:
                bad.append(f)
        print("SELFTEST frames=%d nondeterministic=%s" % (len(frames), bad))
        sys.exit(1 if bad else 0)
    lo, hi = (int(v) for v in a.frames.split("-"))
    if a.shard:
        i, n = (int(v) for v in a.shard.split("/"))
        step = math.ceil((hi - lo + 1) / n)
        lo, hi = lo + i * step, min(hi, lo + (i + 1) * step - 1)
    os.makedirs(a.out, exist_ok=True)
    for f in range(lo, hi + 1):
        if a.skip_existing and os.path.exists(os.path.join(a.out, "frame_%05d.png" % f)):
            continue
        render_frame(f, a.out)
        print("rendered", f, flush=True)


if __name__ == "__main__":
    main()
