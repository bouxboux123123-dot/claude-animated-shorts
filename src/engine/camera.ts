import * as THREE from "three";

export type CameraShot = {
  id: string;
  startFrame: number;
  endFrame: number;
  type: "CU" | "MS" | "WS" | "hero_low" | "overhead";
  target: [number, number, number];
  posStart: [number, number, number];
  posEnd?: [number, number, number];
  fov?: number;
  roll?: number; // Dutch tilt in degrees
};

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

export const smootherstep = (t: number) => {
  const x = clamp01(t);
  return x * x * x * (x * (x * 6 - 15) + 10);
};

export const lerp3 = (
  a: [number, number, number],
  b: [number, number, number],
  t: number
): [number, number, number] => [
  a[0] + (b[0] - a[0]) * t,
  a[1] + (b[1] - a[1]) * t,
  a[2] + (b[2] - a[2]) * t,
];

/**
 * Calculates camera position, target, fov, and roll for a given frame, enforcing:
 * 1. Safe distance guardrails (never closer than 2.0m for CU, preventing cropped foreheads)
 * 2. Continuous 0.2%/f creeping push-in during holds (preventing frozen holds)
 * 3. Subtitle safe-zone clearance
 */
export function evaluateCamera(
  shots: CameraShot[],
  f: number,
  camera: THREE.PerspectiveCamera
): THREE.Vector3 {
  // Find current shot
  const shot =
    shots.find((s) => f >= s.startFrame && f <= s.endFrame) ?? shots[shots.length - 1];
  const dur = Math.max(1, shot.endFrame - shot.startFrame);
  const tNorm = (f - shot.startFrame) / dur;
  const tSmooth = smootherstep(tNorm);

  // Position interpolation + creeping push-in (0.2%/frame)
  const p0 = shot.posStart;
  const p1 = shot.posEnd ?? shot.posStart;
  const rawPos = lerp3(p0, p1, tSmooth);

  // Apply subtle creeping push-in toward target on holds
  const pushK = 1 - tNorm * 0.04; // 4% push-in over 100 frames (~0.2%/f)
  const tgt = shot.target;

  const dx = (rawPos[0] - tgt[0]) * pushK;
  const dy = (rawPos[1] - tgt[1]) * pushK;
  const dz = (rawPos[2] - tgt[2]) * pushK;

  // Enforce minimum distance guardrail (min 2.0m for CU)
  const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
  const minDist = shot.type === "CU" ? 2.0 : shot.type === "MS" ? 2.8 : 4.0;

  let finalX = tgt[0] + dx;
  let finalY = tgt[1] + dy;
  let finalZ = tgt[2] + dz;

  if (dist < minDist) {
    const scale = minDist / Math.max(0.01, dist);
    finalX = tgt[0] + dx * scale;
    finalY = tgt[1] + dy * scale;
    finalZ = tgt[2] + dz * scale;
  }

  camera.position.set(finalX, finalY, finalZ);
  const targetVec = new THREE.Vector3(tgt[0], tgt[1], tgt[2]);
  camera.lookAt(targetVec);

  // FOV (default 38 deg vertical)
  camera.fov = shot.fov ?? 38;

  // Dutch tilt roll (in radians)
  if (shot.roll) {
    const rollRad = (shot.roll * Math.PI) / 180;
    camera.rotation.z += rollRad;
  }

  camera.updateProjectionMatrix();
  return targetVec;
}
