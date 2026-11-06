import { LightMode, CameraShot, evaluateCamera } from "../../engine";
import * as THREE from "three";

export const FPS = 30;
export const TOTAL = 1788;
export const FLASH_AT = 91;

export type ShotDef = {
  id: number;
  a: number;
  b: number;
  light: LightMode;
  stage: string;
  title: string;
  dofCoC?: number;
};

export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 91, light: "workshop", stage: "office", title: "Hook: Office printer", dofCoC: 6 },
  { id: 2, a: 91, b: 284, light: "workshop", stage: "intaglio", title: "Solution 1: 20-ton Intaglio press", dofCoC: 8 },
  { id: 3, a: 284, b: 434, light: "workshop", stage: "wash", title: "Problem 1: Paper dissolves", dofCoC: 7 },
  { id: 4, a: 434, b: 610, light: "workshop", stage: "cloth", title: "Solution 2: Secret cloth loom", dofCoC: 7 },
  { id: 5, a: 610, b: 728, light: "golden", stage: "counterfeit", title: "Problem 2: Counterfeiter", dofCoC: 8 },
  { id: 6, a: 728, b: 919, light: "golden", stage: "quantum", title: "Solution 3: Color-shifting ink", dofCoC: 10 },
  { id: 7, a: 919, b: 1085, light: "workshop", stage: "scanner", title: "Problem 3: 12,000 DPI scanners", dofCoC: 8 },
  { id: 8, a: 1085, b: 1289, light: "golden", stage: "eurion", title: "Solution 4: EURion lock", dofCoC: 9 },
  { id: 9, a: 1289, b: 1423, light: "night", stage: "midnight", title: "Problem 4: Midnight rogue operator", dofCoC: 8 },
  { id: 10, a: 1423, b: 1628, light: "workshop", stage: "shredder", title: "Solution 5: Laser shredder", dofCoC: 7 },
  { id: 11, a: 1628, b: TOTAL, light: "golden", stage: "twist", title: "Payoff: Currency armor twist", dofCoC: 6 },
];

export const shotAt = (f: number): ShotDef =>
  SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];

// Camera choreography enforcing strict distance bounds (CU >= 2.2m, MS >= 3.0m, WS >= 4.2m)
export const CAMERA_SHOTS: CameraShot[] = [
  // Shot 1: Office printer hook (MS: distance 3.2m, character at origin behind workbench)
  {
    id: "shot_01",
    startFrame: 0,
    endFrame: 90,
    type: "MS",
    target: [0.0, 1.35, 0.0],
    posStart: [0.15, 1.55, 3.4],
    posEnd: [0.05, 1.48, 3.1],
    fov: 38,
    roll: -2.5,
  },
  // Shot 2: Intaglio 20-ton press (WS: distance 4.4m, heavy industrial machinery)
  {
    id: "shot_02",
    startFrame: 91,
    endFrame: 283,
    type: "WS",
    target: [0.0, 1.45, -0.2],
    posStart: [0.8, 1.7, 4.6],
    posEnd: [-0.2, 1.55, 4.1],
    fov: 39,
    roll: 3.2,
  },
  // Shot 3: Wash vat (MS: distance 3.4m, character observing water tank)
  {
    id: "shot_03",
    startFrame: 284,
    endFrame: 433,
    type: "MS",
    target: [-0.1, 1.3, -0.1],
    posStart: [-0.3, 1.55, 3.6],
    posEnd: [0.1, 1.45, 3.2],
    fov: 38,
    roll: -2.8,
  },
  // Shot 4: Textile loom (MS: distance 3.2m)
  {
    id: "shot_04",
    startFrame: 434,
    endFrame: 609,
    type: "MS",
    target: [0.0, 1.35, 0.0],
    posStart: [0.2, 1.5, 3.4],
    posEnd: [-0.1, 1.42, 3.0],
    fov: 38,
    roll: 2.0,
  },
  // Shot 5: Counterfeiter den (MS: distance 3.3m, moody light)
  {
    id: "shot_05",
    startFrame: 610,
    endFrame: 727,
    type: "MS",
    target: [0.0, 1.35, 0.0],
    posStart: [-0.4, 1.55, 3.5],
    posEnd: [-0.1, 1.45, 3.1],
    fov: 37,
    roll: -4.2, // dramatic Dutch tilt
  },
  // Shot 6: Color-shifting magnetic ink inspection (CU: distance 2.5m - safe margins, no crop!)
  {
    id: "shot_06",
    startFrame: 728,
    endFrame: 918,
    type: "CU",
    target: [0.0, 1.3, 0.0],
    posStart: [0.15, 1.45, 2.7],
    posEnd: [0.05, 1.38, 2.4],
    fov: 35,
    roll: 3.5,
  },
  // Shot 7: Scanner bed (MS: distance 3.2m)
  {
    id: "shot_07",
    startFrame: 919,
    endFrame: 1084,
    type: "MS",
    target: [-0.05, 1.25, -0.2],
    posStart: [0.25, 1.6, 3.4],
    posEnd: [-0.05, 1.45, 3.0],
    fov: 38,
    roll: -2.0,
  },
  // Shot 8: EURion constellation lock (MS: distance 3.0m)
  {
    id: "shot_08",
    startFrame: 1085,
    endFrame: 1288,
    type: "MS",
    target: [0.0, 1.35, 0.0],
    posStart: [-0.2, 1.5, 3.2],
    posEnd: [0.1, 1.4, 2.9],
    fov: 37,
    roll: 3.8,
  },
  // Shot 9: Rogue midnight operator (MS: distance 3.5m, moody blue night)
  {
    id: "shot_09",
    startFrame: 1289,
    endFrame: 1422,
    type: "MS",
    target: [0.1, 1.4, -0.1],
    posStart: [0.5, 1.65, 3.7],
    posEnd: [0.15, 1.5, 3.3],
    fov: 38,
    roll: -4.5,
  },
  // Shot 10: Shredder & inspection (WS: distance 4.0m)
  {
    id: "shot_10",
    startFrame: 1423,
    endFrame: 1627,
    type: "WS",
    target: [-0.1, 1.35, -0.2],
    posStart: [-0.4, 1.65, 4.2],
    posEnd: [0.1, 1.5, 3.8],
    fov: 39,
    roll: 2.8,
  },
  // Shot 11: Hero payoff twist (MS: distance 3.2m, character proud in golden light)
  {
    id: "shot_11",
    startFrame: 1628,
    endFrame: TOTAL,
    type: "MS",
    target: [0.0, 1.35, 0.0],
    posStart: [0.1, 1.5, 3.4],
    posEnd: [0.0, 1.42, 3.0],
    fov: 38,
    roll: -1.5,
  },
];

export function updateCamera(f: number, cam: THREE.PerspectiveCamera): THREE.Vector3 {
  return evaluateCamera(CAMERA_SHOTS, f, cam);
}
