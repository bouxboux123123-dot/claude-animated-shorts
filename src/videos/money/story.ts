// Timeline and camera grammar for "How Money Is Printed" (60s vertical reel)
// Symmetrical smootherstep glides (18-35 frames), continuous hold push-ins (0.2%/frame),
// dynamic rolls (3-5 deg) on punch words, impact kicks (7 frames, sign flip every frame).
import { Light } from "./lights";

export const FPS = 30;
export const TOTAL = 1788;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };

// ---------------- shots ----------------
export type Stage =
  | "office"
  | "intaglio"
  | "wash"
  | "cloth"
  | "counterfeit"
  | "quantum"
  | "scanner"
  | "eurion"
  | "midnight"
  | "shredder"
  | "twist";

export type ShotDef = {
  id: number;
  a: number;
  b: number;
  light: Light;
  title: string;
  stage: Stage;
};

export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 91, light: "day", title: "Hook: Office printer", stage: "office" },
  { id: 2, a: 91, b: 284, light: "day", title: "Solution 1: 20-ton Intaglio press", stage: "intaglio" },
  { id: 3, a: 284, b: 434, light: "day", title: "Problem 1: Wood paper dissolves", stage: "wash" },
  { id: 4, a: 434, b: 610, light: "day", title: "Solution 2: Cotton/linen secret cloth", stage: "cloth" },
  { id: 5, a: 610, b: 728, light: "golden", title: "Problem 2: Counterfeiter copies ink", stage: "counterfeit" },
  { id: 6, a: 728, b: 919, light: "golden", title: "Solution 3: Color-shifting magnetic ink", stage: "quantum" },
  { id: 7, a: 919, b: 1085, light: "alert", title: "Problem 3: 12,000 DPI scanners", stage: "scanner" },
  { id: 8, a: 1085, b: 1289, light: "alert", title: "Solution 4: EURion constellation lock", stage: "eurion" },
  { id: 9, a: 1289, b: 1423, light: "midnight", title: "Problem 4: Rogue midnight operator", stage: "midnight" },
  { id: 10, a: 1423, b: 1628, light: "day", title: "Solution 5: Laser shredder & vision", stage: "shredder" },
  { id: 11, a: 1628, b: TOTAL, light: "golden", title: "Payoff: High-tech armor twist", stage: "twist" },
];

export const FLASH_AT = 91;
export const XFADE: Record<number, number> = { 3: 6, 5: 6, 7: 6, 9: 6, 11: 6 };

export const shotAt = (f: number): ShotDef => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];

export const layersAt = (f: number): { id: number; alpha: number }[] => {
  for (const s of SHOTS) {
    const x = XFADE[s.id];
    if (x && f >= s.a - x / 2 && f < s.a + x / 2) {
      return [{ id: s.id - 1, alpha: 1 }, { id: s.id, alpha: (f - (s.a - x / 2) + 1) / (x + 1) }];
    }
  }
  return [{ id: shotAt(f).id, alpha: 1 }];
};

// ---------------- camera math ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type ShotKey = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; s: (f: number) => ShotKey };

const mix = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3,
  look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k,
  roll: a.roll + (b.roll - a.roll) * k,
});

const full = (c: ShotKey): Cam => ({ fov: 40, roll: 0, ...c });

const run = (keys: Key[], f: number): Cam => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};

const pushK = (f: number, f0: number, rate: number, punch = 0, n = 35) => {
  const x = Math.max(0, f - f0);
  let s = rate * x;
  if (punch > rate) {
    for (let i = 0; i < Math.min(x, n); i++) {
      s += (punch - rate) * Math.max(0, Math.min(1, (i + 0.5) / 8, (n - i - 0.5) / 8));
    }
  }
  return Math.exp(-s);
};

const dolly = (pos: V3, look: V3, k: number, rest: Partial<Cam> = {}): ShotKey => ({
  pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k],
  look,
  ...rest,
});

const rolled = (s: (f: number) => ShotKey, roll: number) => (f: number): ShotKey => ({ ...s(f), roll });

// ---------------- framings per shot ----------------
// Shot 1: Office printer hook (0 to 91)
const S1a = (f: number) => dolly([0.05, 1.25, 2.5], [0.05, 1.15, 0.1], pushK(f, 0, 0.002), { fov: 42, roll: -0.015 });
const S1b = (f: number) => dolly([0.08, 1.22, 2.1], [0.08, 1.15, 0.1], pushK(f, 20, 0.002, 0.006, 30), { fov: 38, roll: -0.035 });

// Shot 2: Intaglio 20-ton press (91 to 284)
const S2a = (f: number) => dolly([0.45, 1.1, 2.5], [-0.05, 1.35, -0.6], pushK(f, 91, 0.0025, 0.006, 35), { fov: 41, roll: 0.03 });
const S2b = (f: number) => dolly([-0.3, 1.25, 2.0], [0.08, 1.25, -0.5], pushK(f, 182, 0.002), { fov: 38, roll: -0.02 });

// Shot 3: Wash tub disintegrating paper (284 to 434)
const S3a = (f: number) => dolly([-0.05, 1.35, 2.2], [-0.08, 0.95, -0.2], pushK(f, 284, 0.002), { fov: 39, roll: -0.02 });
const S3b = (f: number) => dolly([-0.15, 1.2, 1.7], [-0.15, 0.8, -0.25], pushK(f, 369, 0.0025, 0.006, 32), { fov: 36, roll: 0.035 });

// Shot 4: Cotton linen cloth fibers (434 to 610)
const S4a = (f: number) => dolly([-0.05, 1.25, 2.3], [-0.05, 1.15, 0.1], pushK(f, 434, 0.002), { fov: 40, roll: -0.015 });
const S4b = (f: number) => dolly([-0.18, 1.2, 1.8], [-0.15, 1.15, 0.15], pushK(f, 512, 0.002, 0.006, 35), { fov: 36, roll: 0.04 });

// Shot 5: Counterfeiter copying green ink (610 to 728)
const S5a = (f: number) => dolly([0.35, 1.3, 2.2], [0.05, 1.18, 0], pushK(f, 610, 0.002), { fov: 39, roll: -0.03 });
const S5b = (f: number) => dolly([0.12, 1.22, 1.7], [0.08, 1.2, 0], pushK(f, 680, 0.0025, 0.006, 25), { fov: 35, roll: 0.035 });

// Shot 6: Quantum color-shifting magnetic ink macro (728 to 919) - frames the "$100" numeral
const S6a = (f: number) => {
  const tiltWobble = 0.06 * Math.sin((f - 728) * 0.1);
  return dolly([0.18, 1.12, 0.95], [0.18, 1.08, 0.0], pushK(f, 728, 0.002, 0.005, 40), { fov: 30, roll: tiltWobble });
};
const S6b = (f: number) => {
  const tiltWobble = 0.07 * Math.sin((f - 835) * 0.12);
  return dolly([0.18, 1.1, 0.88], [0.18, 1.08, 0.0], pushK(f, 835, 0.002, 0.006, 35), { fov: 27, roll: tiltWobble });
};

// Shot 7: Flatbed digital scanner 12,000 DPI (919 to 1085)
const S7a = (f: number) => dolly([0.1, 1.6, 1.8], [-0.05, 0.85, -0.6], pushK(f, 919, 0.002), { fov: 42, roll: -0.02 });
const S7b = (f: number) => dolly([0.0, 1.7, 1.4], [-0.08, 0.85, -0.65], pushK(f, 1016, 0.0025, 0.005, 30), { fov: 38, roll: 0.025 });

// Shot 8: EURion constellation lock & freeze (1085 to 1289)
const S8a = (f: number) => dolly([-0.1, 1.5, 1.4], [-0.12, 0.84, -0.7], pushK(f, 1085, 0.002), { fov: 35, roll: -0.02 });
const S8b = (f: number) => dolly([0.15, 1.3, 1.9], [0.1, 1.15, 0], pushK(f, 1242, 0.003, 0.008, 35), { fov: 38, roll: 0.05 });

// Shot 9: Rogue midnight operator at press (1289 to 1423)
const S9a = (f: number) => dolly([0.45, 1.3, 2.3], [0.05, 1.2, -0.4], pushK(f, 1289, 0.002), { fov: 40, roll: -0.035 });
const S9b = (f: number) => dolly([0.2, 1.22, 1.85], [0.08, 1.18, -0.3], pushK(f, 1366, 0.0025, 0.005, 30), { fov: 36, roll: 0.025 });

// Shot 10: Computer vision inspection & laser shredder (1423 to 1628)
const S10a = (f: number) => dolly([-0.05, 1.3, 2.3], [-0.05, 1.15, -0.4], pushK(f, 1423, 0.002), { fov: 41, roll: -0.02 });
const S10b = (f: number) => dolly([-0.3, 1.25, 1.8], [-0.35, 1.05, -0.6], pushK(f, 1576, 0.003, 0.007, 35), { fov: 37, roll: 0.04 });

// Shot 11: Hero dollar bill armor twist (1628 to TOTAL)
const S11a = (f: number) => dolly([0.08, 1.2, 2.3], [0.08, 1.2, 0.1], pushK(f, 1628, 0.002), { fov: 39, roll: -0.02 });
const S11b = (f: number) => dolly([0.04, 1.12, 1.9], [0.08, 1.25, 0.1], pushK(f, 1715, 0.0025, 0.006, 35), { fov: 36, roll: 0.015 });

const CAMS: Record<number, Key[]> = {
  1: [
    { f: 0, s: S1a },
    { f: 20, dur: 28, s: S1b },
  ],
  2: [
    { f: 91, cut: true, s: S2a },
    { f: 182, dur: 32, s: S2b },
  ],
  3: [
    { f: 284, cut: true, s: S3a },
    { f: 369, dur: 30, s: S3b },
  ],
  4: [
    { f: 434, cut: true, s: S4a },
    { f: 512, dur: 35, s: S4b },
    { f: 568, dur: 20, s: rolled(S4b, 0.04) },
  ],
  5: [
    { f: 610, cut: true, s: S5a },
    { f: 680, dur: 26, s: S5b },
  ],
  6: [
    { f: 728, cut: true, s: S6a },
    { f: 835, dur: 30, s: S6b },
  ],
  7: [
    { f: 919, cut: true, s: S7a },
    { f: 1016, dur: 30, s: S7b },
  ],
  8: [
    { f: 1085, cut: true, s: S8a },
    { f: 1242, cut: true, s: S8b },
  ],
  9: [
    { f: 1289, cut: true, s: S9a },
    { f: 1366, dur: 34, s: S9b },
  ],
  10: [
    { f: 1423, cut: true, s: S10a },
    { f: 1576, cut: true, s: S10b },
  ],
  11: [
    { f: 1628, cut: true, s: S11a },
    { f: 1715, dur: 40, s: S11b },
  ],
};

const KICKS: [number, number][] = [
  [4.57, 1.4],   // Frame 137: 20-ton mechanical press stamp!
  [12.30, 0.9],  // Frame 369: Disintegrates in wash!
  [41.40, 1.6],  // Frame 1242: EURion freeze alarm trip!
  [52.53, 1.3],  // Frame 1576: Laser shredded!
];

export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0) * FPS + 1e-6);
    if (n >= 0 && n < 7) {
      a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
    }
  }
  return a;
};

export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id] ?? CAMS[1], f);
  const a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1;
  const m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return {
    ...c,
    look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m],
    roll: c.roll + a * 0.005,
  };
};

// ---------------- thin-lens DOF ----------------
export type DofDef = { cInf: number; focus?: (f: number) => V3 };
export const dofAt = (f: number): DofDef => {
  const s = shotAt(f);
  if (s.stage === "quantum") {
    return { cInf: 14, focus: () => [0.18, 1.08, 0.0] };
  }
  if (s.stage === "office" || s.stage === "cloth" || s.stage === "counterfeit" || s.stage === "twist") {
    return { cInf: 8, focus: () => [0.08, 1.35, 0.0] };
  }
  return { cInf: 3 };
};
