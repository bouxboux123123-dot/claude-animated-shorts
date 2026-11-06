// Light presets per narrative beat for "How Money Is Printed".
// az = degrees from the camera forward axis (0 = sun straight ahead, +90 = right, 180 = behind).
// lit/shade/lift are linear RGB multipliers.
type C3 = [number, number, number];

export type Light = "day" | "golden" | "midnight" | "alert";

export type LightPreset = {
  az: number;
  el: number;
  lit: C3;
  shade: C3;
  lift: C3;
  lambert: number;
  sideK: number;
  term: number;
  charTint: C3;
  charShade: number;
  top: string;
  hor: string;
  sunCol: string;
  sunI: number;
  sky: string;
  ground: string;
  hemiI: number;
};

export const LIGHTS: Record<Light, LightPreset> = {
  day: {
    az: 75,
    el: 48,
    lit: [1.58, 1.5, 1.33],
    shade: [0.3, 0.29, 0.36],
    lift: [0.05, 0.06, 0.11],
    lambert: 0.35,
    sideK: 0.84,
    term: 0.2,
    charTint: [1.0, 0.94, 0.92],
    charShade: 0.86,
    top: "#3e7fd2",
    hor: "#b8d0ec",
    sunCol: "#fff3e0",
    sunI: 2.8,
    sky: "#dcecff",
    ground: "#b49a78",
    hemiI: 0.65,
  },
  golden: {
    az: 15,
    el: 12,
    lit: [1.6, 0.82, 0.35],
    shade: [0.18, 0.16, 0.32],
    lift: [0.04, 0.06, 0.16],
    lambert: 0.35,
    sideK: 0.82,
    term: 0.08,
    charTint: [1.0, 0.82, 0.62],
    charShade: 0.88,
    top: "#6a4f8c",
    hor: "#ffd08a",
    sunCol: "#ffab5e",
    sunI: 4.5,
    sky: "#d8b0b8",
    ground: "#8a6a60",
    hemiI: 0.5,
  },
  midnight: {
    az: 180,
    el: 75,
    lit: [0.45, 0.65, 0.95],
    shade: [0.06, 0.08, 0.14],
    lift: [0.02, 0.03, 0.06],
    lambert: 0.25,
    sideK: 0.9,
    term: 0.1,
    charTint: [0.75, 0.85, 1.0],
    charShade: 0.92,
    top: "#0a0e17",
    hor: "#162032",
    sunCol: "#38bdf8",
    sunI: 1.8,
    sky: "#0f172a",
    ground: "#080c14",
    hemiI: 0.25,
  },
  alert: {
    az: 60,
    el: 55,
    lit: [1.9, 0.5, 0.5],
    shade: [0.25, 0.08, 0.12],
    lift: [0.06, 0.02, 0.03],
    lambert: 0.3,
    sideK: 0.85,
    term: 0.15,
    charTint: [1.0, 0.75, 0.75],
    charShade: 0.88,
    top: "#2a0808",
    hor: "#7f1d1d",
    sunCol: "#ef4444",
    sunI: 3.8,
    sky: "#450a0a",
    ground: "#1f1315",
    hemiI: 0.45,
  },
};
