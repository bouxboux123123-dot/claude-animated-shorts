import { LightMode, CameraShot, evaluateCamera } from "../../engine";
import * as THREE from "three";

export const FPS = 30;
export const TOTAL = 1958;

export type PinkShotDef = {
  id: number;
  a: number;
  b: number;
  light: LightMode;
  stage: "corridor" | "mix_bench" | "paint_wall" | "guards_corridor" | "stopwatch_rule" | "cell_door" | "pink_cell_inmate" | "door_exit" | "arm_wrestle" | "reaction" | "truckload_montage" | "night_station" | "night_quiet" | "night_pacing" | "bench_rage" | "blackboard_chart" | "rage_payoff";
  title: string;
  dofCoC?: number;
};

export const SHOTS: PinkShotDef[] = [
  { id: 1, a: 0, b: 102, light: "prison", stage: "corridor", title: "Hook: Painted the cell pink", dofCoC: 6 },
  { id: 2, a: 102, b: 215, light: "workshop", stage: "mix_bench", title: "Mixes pint of red into white", dofCoC: 8 },
  { id: 3, a: 215, b: 333, light: "pink", stage: "paint_wall", title: "Wrong shade repaint", dofCoC: 7 },
  { id: 4, a: 333, b: 429, light: "prison", stage: "guards_corridor", title: "Barbie is gonna love it", dofCoC: 6 },
  { id: 5, a: 429, b: 496, light: "prison", stage: "stopwatch_rule", title: "One strange rule", dofCoC: 8 },
  { id: 6, a: 496, b: 667, light: "prison", stage: "cell_door", title: "15 minute rule with stopwatch", dofCoC: 7 },
  { id: 7, a: 667, b: 847, light: "pink", stage: "pink_cell_inmate", title: "300lb inmate laughing", dofCoC: 8 },
  { id: 8, a: 847, b: 915, light: "prison", stage: "door_exit", title: "Pull him out 15 min later", dofCoC: 7 },
  { id: 9, a: 915, b: 1083, light: "prison", stage: "arm_wrestle", title: "Arm wrestle slam in 2s", dofCoC: 8 },
  { id: 10, a: 1083, b: 1157, light: "prison", stage: "reaction", title: "Wait what? Nobody can explain", dofCoC: 6 },
  { id: 11, a: 1157, b: 1283, light: "pink", stage: "truckload_montage", title: "Painting by the truckload", dofCoC: 7 },
  { id: 12, a: 1283, b: 1375, light: "night", stage: "night_station", title: "One night guard forgets", dofCoC: 8 },
  { id: 13, a: 1375, b: 1437, light: "night", stage: "night_quiet", title: "At 15m sitting quietly", dofCoC: 9 },
  { id: 14, a: 1437, b: 1477, light: "pink", stage: "night_pacing", title: "At 20 pacing", dofCoC: 8 },
  { id: 15, a: 1477, b: 1581, light: "pink", stage: "bench_rage", title: "Ripping bench out of floor", dofCoC: 7 },
  { id: 16, a: 1581, b: 1801, light: "workshop", stage: "blackboard_chart", title: "Scientist swore it drained fight", dofCoC: 7 },
  { id: 17, a: 1801, b: TOTAL, light: "pink", stage: "rage_payoff", title: "Exact opposite payoff", dofCoC: 6 },
];

export const shotAt = (f: number): PinkShotDef =>
  SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];

// Camera choreography enforcing strict distance bounds (CU >= 2.2m, MS >= 3.0m, WS >= 4.2m)
export const CAMERA_SHOTS: CameraShot[] = [
  // Shot 1: Corridor tracking glide (MS: distance 3.4m -> 2.8m)
  {
    id: "shot_01",
    startFrame: 0,
    endFrame: 101,
    type: "MS",
    target: [0.0, 1.25, 0.0],
    posStart: [0.4, 1.05, 3.8],
    posEnd: [0.15, 1.2, 2.9],
    fov: 38,
    roll: -1.5,
  },
  // Shot 2: Mix table downward tilt (CU: distance 2.2m -> 1.85m)
  {
    id: "shot_02",
    startFrame: 102,
    endFrame: 214,
    type: "CU",
    target: [0.1, 1.15, 0.0],
    posStart: [0.2, 1.6, 2.2],
    posEnd: [0.05, 1.45, 1.85],
    fov: 38,
    roll: 1.5,
  },
  // Shot 3: Wrong shade repaint lateral track (MS: distance 2.6m -> 2.2m)
  {
    id: "shot_03",
    startFrame: 215,
    endFrame: 332,
    type: "MS",
    target: [0.05, 1.25, -0.1],
    posStart: [-0.3, 1.3, 2.6],
    posEnd: [0.2, 1.28, 2.2],
    fov: 38,
    roll: -1.2,
  },
  // Shot 4: Guards smirk push-in (MS: distance 3.2m -> 2.7m)
  {
    id: "shot_04",
    startFrame: 333,
    endFrame: 428,
    type: "MS",
    target: [0.0, 1.3, 0.0],
    posStart: [0.1, 1.38, 3.3],
    posEnd: [0.0, 1.35, 2.7],
    fov: 38,
    roll: 1.2,
  },
  // Shot 5: One strange rule (CU: distance 2.5m -> 2.2m)
  {
    id: "shot_05",
    startFrame: 429,
    endFrame: 495,
    type: "CU",
    target: [0.0, 1.35, 0.0],
    posStart: [0.35, 1.45, 2.7],
    posEnd: [0.1, 1.38, 2.25],
    fov: 37,
    roll: -2.0,
  },
  // Shot 6: Cell door diagonal glide to stopwatch (MS -> CU: distance 3.0m -> 2.3m)
  {
    id: "shot_06",
    startFrame: 496,
    endFrame: 666,
    type: "MS",
    target: [0.05, 1.3, 0.0],
    posStart: [0.35, 1.6, 3.1],
    posEnd: [0.1, 1.25, 2.3],
    fov: 38,
    roll: -2.2,
  },
  // Shot 7: 300lb Inmate entry (Low-angle Dutch tilt +4.5 deg, looking up)
  {
    id: "shot_07",
    startFrame: 667,
    endFrame: 846,
    type: "MS",
    target: [0.0, 1.45, 0.0],
    posStart: [-0.1, 0.65, 2.8],
    posEnd: [0.1, 0.9, 3.4],
    fov: 40,
    roll: 4.5, // Dutch tilt
  },
  // Shot 8: Pull him out 15 min later (MS: distance 2.6m -> 3.3m)
  {
    id: "shot_08",
    startFrame: 847,
    endFrame: 914,
    type: "MS",
    target: [0.0, 1.3, 0.0],
    posStart: [0.0, 1.38, 2.6],
    posEnd: [0.0, 1.32, 3.3],
    fov: 38,
    roll: -1.0,
  },
  // Shot 9: Arm wrestle slam (MS: distance 2.7m -> 2.1m with impact shake on frame 1040)
  {
    id: "shot_09",
    startFrame: 915,
    endFrame: 1082,
    type: "MS",
    target: [0.0, 1.05, 0.0],
    posStart: [0.05, 1.25, 2.7],
    posEnd: [0.0, 1.1, 2.1],
    fov: 38,
    roll: 2.0,
  },
  // Shot 10: Wait what? reaction (CU: distance 2.4m hold)
  {
    id: "shot_10",
    startFrame: 1083,
    endFrame: 1156,
    type: "CU",
    target: [0.0, 1.25, 0.0],
    posStart: [0.0, 1.28, 2.4],
    posEnd: [0.0, 1.26, 2.2],
    fov: 37,
    roll: -1.5,
  },
  // Shot 11: Truckload paint montage (WS crane: distance 4.2m -> 3.4m)
  {
    id: "shot_11",
    startFrame: 1157,
    endFrame: 1282,
    type: "WS",
    target: [0.0, 1.2, 0.0],
    posStart: [-0.9, 2.1, 4.4],
    posEnd: [0.7, 1.7, 3.3],
    fov: 40,
    roll: 3.0,
  },
  // Shot 12: Night station clock (MS: distance 3.2m -> 2.5m)
  {
    id: "shot_12",
    startFrame: 1283,
    endFrame: 1374,
    type: "MS",
    target: [0.0, 1.9, 0.0],
    posStart: [0.35, 1.7, 3.3],
    posEnd: [0.1, 1.85, 2.4],
    fov: 38,
    roll: -2.0,
  },
  // Shot 13: 15m sitting quietly (CU: distance 2.4m -> 1.9m)
  {
    id: "shot_13",
    startFrame: 1375,
    endFrame: 1436,
    type: "CU",
    target: [0.35, 1.1, 0.4],
    posStart: [0.35, 1.25, 2.4],
    posEnd: [0.35, 1.18, 1.9],
    fov: 37,
    roll: 1.0,
  },
  // Shot 14: 20 pacing lateral tracking (MS: distance 2.8m)
  {
    id: "shot_14",
    startFrame: 1437,
    endFrame: 1476,
    type: "MS",
    target: [0.0, 1.15, 0.0],
    posStart: [-0.5, 1.25, 2.8],
    posEnd: [0.5, 1.25, 2.8],
    fov: 38,
    roll: -1.5,
  },
  // Shot 15: Ripping bench rage (Low-angle Dutch tilt -5.5 deg, violent shake)
  {
    id: "shot_15",
    startFrame: 1477,
    endFrame: 1580,
    type: "MS",
    target: [0.35, 1.15, 0.4],
    posStart: [0.2, 0.85, 2.3],
    posEnd: [0.35, 0.95, 1.8],
    fov: 40,
    roll: -5.5, // Dutch tilt
  },
  // Shot 16: Blackboard curve explanation orbit (MS: distance 3.2m -> 2.7m)
  {
    id: "shot_16",
    startFrame: 1581,
    endFrame: 1800,
    type: "MS",
    target: [0.0, 1.45, 0.0],
    posStart: [0.8, 1.5, 3.2],
    posEnd: [-0.5, 1.42, 2.7],
    fov: 38,
    roll: 1.8,
  },
  // Shot 17: Exact opposite snap payoff (CU: distance 2.8m -> 1.85m)
  {
    id: "shot_17",
    startFrame: 1801,
    endFrame: TOTAL,
    type: "CU",
    target: [0.0, 1.35, 0.0],
    posStart: [0.0, 1.32, 2.8],
    posEnd: [0.0, 1.38, 1.85],
    fov: 37,
    roll: -3.0,
  },
];

export function updatePinkCamera(cam: THREE.PerspectiveCamera, frame: number) {
  evaluateCamera(CAMERA_SHOTS, frame, cam);

  // Impact shake on arm wrestling slam (frame 1040)
  if (frame >= 1040 && frame <= 1048) {
    const decay = Math.exp(-(frame - 1040) / 2.5);
    const sign = (frame % 2 === 0 ? 1 : -1);
    cam.position.x += sign * 0.035 * decay;
    cam.position.y += sign * 0.02 * decay;
  }

  // Violent shake on bench tearing rage (frames 1490 to 1570)
  if (frame >= 1490 && frame <= 1570) {
    const cycle = (frame - 1490) % 6;
    const sign = cycle < 3 ? 1 : -1;
    cam.position.x += sign * 0.018;
    cam.position.y += (Math.sin(frame * 0.6) * 0.012);
  }
}
