#!/usr/bin/env python3
"""scene.py - headless runner for the 61 s vertical cartoon short.

    blender -b -P scene.py -- --frames 0-60 --out out/ --samples 4
    blender -b -P scene.py -- --selftest
    python3 scene.py --selftest            (pure-logic mode, no Blender needed)

Frame state is a PURE, DETERMINISTIC function of the frame number:
Project.state(f) rebuilds everything from shots.json + acting.json; nothing
is carried between frames. apply_frame_actions(f) first resets every prop,
character, set, light and the camera to defaults, then applies that state.
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

try:
    import bpy
except ImportError:
    bpy = None

from lib import look, sets as S, props as P, chars as C   # noqa: E402

FPS, TOTAL, MIN_CAM_CLEAR, REACH_TOL = 30, 1830, 2.5, 1e-3
EASE = {"linear": lambda t: t, "in": lambda t: t * t, "out": lambda t: 1 - (1 - t) ** 2,
        "inout": lambda t: t * t * (3 - 2 * t)}


class TimelineError(RuntimeError):
    pass


class HandReachError(RuntimeError):
    pass


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(a, b, t):
    return tuple(lerp(a[i], b[i], t) for i in range(3))


def _round(o, nd=5):
    if isinstance(o, float):
        return round(o, nd) + 0.0
    if isinstance(o, dict):
        return {k: _round(v, nd) for k, v in sorted(o.items())}
    if isinstance(o, (list, tuple)):
        return [_round(v, nd) for v in o]
    return o


def stable_hash(o):
    return hashlib.sha1(json.dumps(_round(o), sort_keys=True).encode()).hexdigest()[:16]


# ==========================================================================
# Project: compiled, immutable timeline + pure evaluator
# ==========================================================================
class Project:
    def __init__(self, shots=None, acting=None):
        self.shots_doc = shots if shots is not None else json.load(open(os.path.join(ROOT, "shots.json")))
        self.acting = acting if acting is not None else json.load(open(os.path.join(ROOT, "acting.json")))
        self.props = P.make_props()
        self.specs = C.make_chars()
        self.compile()

    # ------------------------------------------------------------------ compile
    def compile(self):
        shots = sorted(self.shots_doc["shots"], key=lambda s: s["f0"])
        if shots[0]["f0"] != 0 or shots[-1]["f1"] != TOTAL:
            raise TimelineError(f"shots must cover [0,{TOTAL})")
        for a, b in zip(shots, shots[1:]):
            if a["f1"] != b["f0"]:
                raise TimelineError(f"shot gap/overlap between {a['id']} and {b['id']}")
        for s in shots:
            if s["set"] not in S.SETS or s["mood"] not in look.MOODS:
                raise TimelineError(f"shot {s['id']}: bad set/mood")
            for end in ("from", "to"):
                clr = S.REG.clearance(tuple(s[end]["pos"]))
                if clr < MIN_CAM_CLEAR:
                    raise TimelineError(f"shot {s['id']} {end}: camera only {clr:.2f} m from obstacle (< {MIN_CAM_CLEAR})")
        self.shots = shots
        self.holds, self.operates, self.impacts = [], {}, []
        self.emotions = {n: [] for n in self.specs}
        self.moves = {n: [] for n in self.specs}
        for a in self.acting["actors"]:
            if a not in self.specs:
                raise TimelineError(f"unknown actor {a}")
        for e in self.acting["events"]:
            v = e["verb"]
            if v == "hold":
                self._add_hold(e["actor"], e["hand"], e["prop"], e["socket"], e)
            elif v == "clasp":
                for hand, sock in (("L", "grip_twohand_L"), ("R", "grip_twohand_R")):
                    self._add_hold(e["actor"], hand, e["prop"], sock, e, e.get("elbows", [-1, -1])["LR".index(hand)] if "elbows" in e else -1)
            elif v == "operate":
                p = self._prop(e["prop"])
                p.clamp(e["channel"], e["to"])
                self.operates.setdefault((e["prop"], e["channel"]), []).append(e)
            elif v == "emotion":
                if e["emotion"] not in C.EMOTIONS:
                    raise TimelineError(f"unknown emotion {e['emotion']}")
                self.emotions[e["actor"]].append((e["f0"], e["emotion"]))
            elif v == "move":
                self.moves[e["actor"]].append(e)
            elif v == "impact":
                t = e["target"]
                if not (t in ("camera", "world") or (t.startswith("actor:") and t[6:] in self.specs)):
                    raise TimelineError(f"bad impact target {t}")
                self.impacts.append(e)
            else:
                raise TimelineError(f"unknown verb {v}")
        for n in self.specs:
            self.emotions[n].sort()
            self.moves[n].sort(key=lambda m: m["f0"])
        for lst in self.operates.values():
            lst.sort(key=lambda e: e["f0"])
        self._check_holds()
        self._check_operate_coverage()

    def _prop(self, name):
        if name not in self.props:
            raise TimelineError(f"unknown prop {name}")
        return self.props[name]

    def _add_hold(self, actor, hand, prop, socket, e, elbow=None):
        p = self._prop(prop)
        if socket not in p.sockets:
            raise TimelineError(f"prop {prop} has no socket {socket}")
        if actor not in self.specs:
            raise TimelineError(f"unknown actor {actor}")
        self.holds.append(dict(actor=actor, hand=hand, prop=prop, socket=socket, f0=e["f0"], f1=e["f1"],
                               carry=bool(e.get("carry", False)), at=tuple(e.get("at", (0.5, 1.2))), dy=e.get("dy", -0.02),
                               elbow=e.get("elbow", -1) if elbow is None else elbow))

    def _check_holds(self):
        for i, a in enumerate(self.holds):
            for b in self.holds[i + 1:]:
                if a["f0"] > b["f1"] or b["f0"] > a["f1"]:
                    continue
                if a["actor"] == b["actor"] and a["hand"] == b["hand"]:
                    raise TimelineError(f"{a['actor']} hand {a['hand']} holds two things at once")
                if a["prop"] == b["prop"] and a["socket"] == b["socket"]:
                    raise TimelineError(f"socket {a['prop']}.{a['socket']} grasped twice")
                if a["prop"] == b["prop"] and a["carry"] and b["carry"] and (a["actor"] != b["actor"] or a["at"] != b["at"] or a["dy"] != b["dy"]):
                    raise TimelineError(f"prop {a['prop']} carried inconsistently")

    def _check_operate_coverage(self):
        for (pn, ch), evs in self.operates.items():
            need = self.props[pn].hand_driven.get(ch)
            if not need:
                continue
            for e in evs:
                for f in range(e["f0"], e["f1"] + 1):
                    if not any(h["prop"] == pn and h["socket"] in need and h["f0"] <= f <= h["f1"] for h in self.holds):
                        raise P.PropAssertionError(
                            f"operate {pn}.{ch} [{e['f0']},{e['f1']}] not covered by a hold/clasp of {need} at frame {f}")

    # ------------------------------------------------------------------ samplers
    def shot_at(self, f):
        for s in self.shots:
            if s["f0"] <= f < s["f1"]:
                return s
        raise TimelineError(f"frame {f} outside timeline")

    def holds_at(self, f):
        return [h for h in self.holds if h["f0"] <= f <= h["f1"]]

    def channel(self, prop, ch, f):
        cur = self.props[prop].defaults[ch]
        for e in self.operates.get((prop, ch), []):
            if f < e["f0"]:
                break
            start = e.get("from", cur)
            if f >= e["f1"]:
                cur = e["to"]
                continue
            t = (f - e["f0"]) / (e["f1"] - e["f0"])
            return self.props[prop].clamp(ch, lerp(start, e["to"], EASE[e.get("ease", "inout")](t)))
        return self.props[prop].clamp(ch, cur)

    def actor_motion(self, name, f):
        a = self.acting["actors"][name]
        cur, face, walking, phase = tuple(a["pos"]), a.get("facing", 1), False, 0.0
        for m in self.moves[name]:
            if f < m["f0"]:
                break
            if "facing" in m:
                face = m["facing"]
            if f >= m["f1"]:
                cur = tuple(m["to"])
                continue
            t = (f - m["f0"]) / (m["f1"] - m["f0"])
            cur = (lerp(cur[0], m["to"][0], t), lerp(cur[1], m["to"][1], t))
            walking, phase = True, f * 0.7
            break
        bob = 0.06 * abs(math.sin(phase)) if walking else 0.0
        return (cur[0], cur[1], bob), face, (phase if walking else None)

    def _impact_env(self, target, f):
        total = 0.0
        for e in self.impacts:
            if e["target"] != target:
                continue
            dt = f - e["f0"]
            if 0 <= dt < e["dur"]:
                t = dt / e["dur"]
                total += e["strength"] * math.exp(-3 * t) * (math.cos(10 * t) if target.startswith("actor") else 1.0)
        return total

    def camera_at(self, f, shot):
        t = (f - shot["f0"]) / max(1, shot["f1"] - 1 - shot["f0"])
        t = EASE[shot.get("ease", "inout")](min(1.0, max(0.0, t)))
        a, b = shot["from"], shot["to"]
        pos, look_ = lerp3(a["pos"], b["pos"], t), lerp3(a["look"], b["look"], t)
        amp = 0.15 * self._impact_env("camera", f)
        if amp:
            off = (math.sin(f * 2.9 + 1.3) * amp, math.sin(f * 3.7 + .4) * amp * .6, math.sin(f * 3.3 + 2.2) * amp)
            pos = tuple(pos[i] + off[i] for i in range(3))
            look_ = tuple(look_[i] + off[i] * .5 for i in range(3))
        pos = S.REG.push_clear(pos, MIN_CAM_CLEAR)
        return dict(pos=pos, look=look_, lens=lerp(a["lens"], b["lens"], t), roll=lerp(a.get("roll", 0), b.get("roll", 0), t))

    # ------------------------------------------------------------------ THE pure evaluator
    def state(self, f):
        shot = self.shot_at(f)
        holds = self.holds_at(f)
        motion = {n: self.actor_motion(n, f) for n in self.specs}
        pstate = {}
        for pn, p in self.props.items():
            vals = {ch: self.channel(pn, ch, f) for ch in p.defaults}
            prev = {ch: self.channel(pn, ch, f - 1) for ch in p.defaults} if f > 0 else vals
            p.check_motion(f, prev, vals, [h["socket"] for h in holds if h["prop"] == pn])
            carry = [h for h in holds if h["prop"] == pn and h["carry"]]
            if carry:
                h = carry[0]
                pos, face, _ = motion[h["actor"]]
                root, mirror = (pos[0] + face * h["at"][0], pos[1] + h["dy"], pos[2] + h["at"][1]), float(face)
            else:
                root, mirror = p.home, 1.0
            pstate[pn] = dict(values=vals, root=root, mirror=mirror, label=p.label(vals) if hasattr(p, "label") else "")
        astate = {}
        for n, spec in self.specs.items():
            pos, face, wp = motion[n]
            grips = {}
            for h in holds:
                if h["actor"] == n:
                    ps = pstate[h["prop"]]
                    grips[h["hand"]] = (self.props[h["prop"]].socket_world(h["socket"], ps["values"], ps["root"], ps["mirror"]), h["elbow"])
            sq = max(-1.0, min(1.0, self._impact_env("actor:" + n, f)))
            st = C.pose_actor(spec, f, pos, face, self.emotions[n], sq, grips, wp)
            for hand, a in st["arms"].items():
                if a["gripping"] and a["err"] > REACH_TOL:
                    raise HandReachError(f"frame {f}: {n}.{hand} cannot reach its grip target (err {a['err']:.4f} m)")
            astate[n] = st
        return dict(frame=f, shot=shot["id"], set=shot["set"], mood=shot["mood"], camera=self.camera_at(f, shot),
                    flash=0.5 * self._impact_env("world", f), props=pstate, actors=astate)

    def state_hash(self, f):
        return stable_hash(self.state(f))


# ==========================================================================
# Blender world (only when bpy is present)
# ==========================================================================
class World:
    def __init__(self, project, res, samples):
        self.p = project
        sc = bpy.context.scene
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        look.validate_moods()
        look.configure_render(sc, res, samples)
        look.build_light_rig()
        self.cam = look.make_camera(sc)
        S.build_all()
        for pr in project.props.values():
            pr.build()
        self.rigs = {n: C.CharRig(sp).build() for n, sp in project.specs.items()}

    def reset_all(self):
        for pr in self.p.props.values():
            pr.apply_bpy(pr.defaults, pr.home, 1.0)
        for n, rig in self.rigs.items():
            rig.apply(C.default_pose(self.p.specs[n]))
        S.show_only(None)
        look.apply_mood("noon_fair", [], 0.0)

    def apply(self, st):
        S.show_only(st["set"])
        look.apply_mood(st["mood"], S.lamp_positions(st["set"]), st["flash"])
        for pn, ps in st["props"].items():
            self.p.props[pn].apply_bpy(ps["values"], ps["root"], ps["mirror"])
        for an, a in st["actors"].items():
            self.rigs[an].apply(a)
        c = st["camera"]
        look.aim_camera(self.cam, c["pos"], c["look"], c["lens"], c["roll"])
        bpy.context.view_layer.update()

    def scene_hash(self):
        """Hash actual Blender transforms (cam, prop roots/sockets, actor roots/hands)."""
        out = {"cam": tuple(self.cam.matrix_world.translation), "camq": tuple(self.cam.matrix_world.to_quaternion())}
        for pn, pr in self.p.props.items():
            out["p_" + pn] = tuple(pr.rig["root"].matrix_world.translation)
            for s, e in pr.rig["socks"].items():
                out[f"s_{pn}.{s}"] = tuple(e.matrix_world.translation)
        for an, rig in self.rigs.items():
            out["a_" + an] = tuple(rig.o["root"].matrix_world.translation)
            for k, h in rig.o["hand"].items():
                out[f"h_{an}{k}"] = tuple(h.matrix_world.translation)
        return stable_hash(out)

    def grip_error(self, st):
        """Max distance between a gripping hand empty and its prop socket empty in WORLD space."""
        worst = 0.0
        for h in self.p.holds_at(st["frame"]):
            hand = self.rigs[h["actor"]].o["hand"][h["hand"]].matrix_world.translation
            sock = self.p.props[h["prop"]].rig["socks"][h["socket"]].matrix_world.translation
            worst = max(worst, (hand - sock).length)
        return worst


_CTX = {}


def _ctx(args=None):
    if "project" not in _CTX:
        _CTX["project"] = Project()
        if bpy:
            res = tuple(int(v) for v in (args.res if args else "1080x1920").lower().split("x"))
            _CTX["world"] = World(_CTX["project"], res, args.samples if args else 4)
    return _CTX


def apply_frame_actions(f):
    """Stateless frame handler: reset everything, then rebuild from the timeline."""
    c = _ctx()
    st = c["project"].state(f)              # pure; raises on any assertion
    if bpy:
        c["world"].reset_all()
        c["world"].apply(st)
        bpy.context.scene.frame_current = f
    return st


# ==========================================================================
# Self-test: determinism + IK + assertions
# ==========================================================================
def selftest(args):
    t0 = time.time()
    rng = random.Random(args.seed)
    proj = Project()
    frames = list(range(TOTAL))
    base, worst_err, grips = {}, 0.0, 0
    for f in frames:                                   # also exercises every assertion & reach check
        st = proj.state(f)
        base[f] = stable_hash(st)
        for a in st["actors"].values():
            for arm in a["arms"].values():
                if arm["gripping"]:
                    grips += 1
                    worst_err = max(worst_err, arm["err"])
    order = frames[:]
    rng.shuffle(order)
    for f in order:
        assert proj.state_hash(f) == base[f], f"non-deterministic state at frame {f}"
    for f in rng.sample(frames, 200):                   # repeated evaluation of the same frame
        assert proj.state_hash(f) == proj.state_hash(f) == base[f]
    runners = 20
    size = math.ceil(TOTAL / runners)
    for r in range(runners):                            # 20 independent 'cloud runners'
        shard = frames[r * size:(r + 1) * size]
        rng.shuffle(shard)
        fresh = Project()
        for f in shard:
            assert fresh.state_hash(f) == base[f], f"runner {r} diverged at frame {f}"
    # negative test: an un-held hand-driven operate MUST be rejected
    bad = json.loads(json.dumps(proj.acting))
    bad["events"] = [e for e in bad["events"] if not (e["verb"] == "hold" and e["prop"] == "lever")]
    try:
        Project(proj.shots_doc, bad)
        raise SystemExit("SELFTEST FAIL: lever moved without grasp but no error was raised")
    except P.PropAssertionError as ex:
        print("  negative test OK ->", str(ex)[:96])
    clear = min(min(S.REG.clearance(tuple(s[e]["pos"])) for e in ("from", "to")) for s in proj.shots)
    print(f"  pure: {TOTAL} frames, grip-frames={grips}, max hand error={worst_err:.2e} m, min camera clearance={clear:.2f} m")
    print(f"  pure: 3 passes + 20 shards identical (shuffled, seed={args.seed})")
    if bpy:
        c = _ctx(args)
        sample = rng.sample(frames, 40)
        h1 = {}
        for f in sample:
            apply_frame_actions(f)
            h1[f] = c["world"].scene_hash()
            assert c["world"].grip_error(c["project"].state(f)) < REACH_TOL, f"hand off socket at frame {f}"
        rng.shuffle(sample)
        for f in sample:
            apply_frame_actions(f)
            assert c["world"].scene_hash() == h1[f], f"bpy scene differs on re-eval at frame {f}"
        print("  bpy : 40 frames re-evaluated in shuffled order -> identical transforms, hands on sockets")
    print(f"SELFTEST PASS in {time.time() - t0:.1f}s")
    return 0


# ==========================================================================
# CLI
# ==========================================================================
def parse_frames(spec):
    if "-" in spec:
        a, b = spec.split("-", 1)
        return int(a), int(b)
    return int(spec), int(spec)


def main(argv):
    ap = argparse.ArgumentParser(description="61 s vertical cartoon short - stateless frame runner")
    ap.add_argument("--frames", default=f"0-{TOTAL - 1}", help="START-END inclusive (parallel slicing)")
    ap.add_argument("--out", default="out")
    ap.add_argument("--samples", type=int, default=4)
    ap.add_argument("--no-save", action="store_true", help="evaluate only, do not render/write images")
    ap.add_argument("--res", default="1080x1920")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--seed", type=int, default=1234)
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest(args)
    a, b = parse_frames(args.frames)
    if not (0 <= a <= b < TOTAL):
        raise SystemExit(f"--frames must lie in 0-{TOTAL - 1}")
    os.makedirs(args.out, exist_ok=True)
    _ctx(args)
    hashes = {}
    for f in range(a, b + 1):
        st = apply_frame_actions(f)
        hashes[f] = stable_hash(st)
        if bpy and not args.no_save:
            bpy.context.scene.render.filepath = os.path.join(args.out, f"frame_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        if (f - a) % 30 == 0:
            print(f"frame {f:4d}  shot={st['shot']}  hash={hashes[f]}", flush=True)
    with open(os.path.join(args.out, f"hashes_{a:04d}-{b:04d}.json"), "w") as fh:
        json.dump(hashes, fh, indent=1)
    return 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    sys.exit(main(argv))
