// Light presets per time of day or interior environment. The sun is CAMERA-RELATIVE and frozen per shot (world.ts update()):
// az = degrees from the shot camera's forward axis (0 = sun straight ahead = backlight, +90 = screen right,
// 180 = behind camera), el = elevation. lit/shade/lift are LINEAR RGB multipliers for shade.ts (may exceed 1).
type C3 = [number, number, number];
export type LightPreset = {
  az: number; el: number;
  lit: C3; shade: C3; lift: C3; lambert: number; sideK: number; term: number;      // world two-tone (shade.ts)
  charTint: C3; charShade: number; charGrad: number; bodyGrad: number; sideTint: C3; // character cards (cast.ts)
  blob: C3; actorShadow: boolean;                                                    // contact blobs / card shadows
  top: string; hor: string; skyCurve: C3; fog: string; fogNear: number; fogFar: number; sunDisc: string; // depth.md 6.5
  sunCol: string; sunI: number; sky: string; ground: string; hemiI: number;         // three lights (unpatched mats only)
  bias: number; normalBias: number;
};

export type LightMode = "day" | "golden" | "workshop" | "night" | "prison" | "pink";

export const LIGHTS: Record<LightMode, LightPreset> = {
  day: {
    az: 75, el: 48,
    lit: [1.58, 1.5, 1.33], shade: [0.3, 0.29, 0.36], lift: [0.05, 0.06, 0.11], lambert: 0.35, sideK: 0.84, term: 0.2,
    charTint: [1.0, 0.94, 0.92], charShade: 0.86, charGrad: 0.07, bodyGrad: 0.2, sideTint: [0.92, 0.90, 0.96],
    blob: [0.62, 0.58, 0.58], actorShadow: false,
    top: "#3e7fd2", hor: "#b8d0ec", skyCurve: [0.0, 0.5, 0.6], fog: "#b8d0ec", fogNear: 25, fogFar: 300, sunDisc: "#000000",
    sunCol: "#fff3e0", sunI: 2.8, sky: "#dcecff", ground: "#b49a78", hemiI: 0.55,
    bias: -0.00025, normalBias: 0.015,
  },
  golden: {
    az: 6, el: 7,
    lit: [1.5, 0.68, 0.24], shade: [0.15, 0.15, 0.3], lift: [0.04, 0.06, 0.17], lambert: 0.35, sideK: 0.82, term: 0.07,
    charTint: [1.0, 0.78, 0.56], charShade: 0.88, charGrad: 0.1, bodyGrad: 0.25, sideTint: [0.85, 0.80, 0.95],
    blob: [0.75, 0.74, 0.9], actorShadow: true,
    top: "#6a4f8c", hor: "#ffd08a", skyCurve: [0.05, 0.6, 1.0], fog: "#efb489", fogNear: 50, fogFar: 380, sunDisc: "#ffcf9e",
    sunCol: "#ffab5e", sunI: 5.5, sky: "#d8b0b8", ground: "#8a6a60", hemiI: 0.5,
    bias: -0.0006, normalBias: 0.03,
  },
  workshop: {
    // Warm interior workshop: sunlight streaming through high arched windows, warm floor bounce, deep wood/brick tones
    az: 55, el: 38,
    lit: [1.62, 1.48, 1.25], shade: [0.38, 0.34, 0.45], lift: [0.08, 0.08, 0.14], lambert: 0.38, sideK: 0.88, term: 0.22,
    charTint: [1.0, 0.95, 0.90], charShade: 0.85, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.90, 0.88, 0.95],
    blob: [0.55, 0.50, 0.52], actorShadow: true,
    top: "#4a6fa5", hor: "#cbd5e1", skyCurve: [0.0, 0.4, 0.7], fog: "#cbd5e1", fogNear: 15, fogFar: 120, sunDisc: "#ffffff",
    sunCol: "#fff6e5", sunI: 3.4, sky: "#e2e8f0", ground: "#785238", hemiI: 0.65,
    bias: -0.0003, normalBias: 0.02,
  },
  night: {
    // Dramatic moody interior / midnight mystery: cool blue ambient, warm spotlight focus
    az: 15, el: 25,
    lit: [1.2, 1.1, 0.9], shade: [0.12, 0.14, 0.28], lift: [0.03, 0.04, 0.09], lambert: 0.42, sideK: 0.75, term: 0.15,
    charTint: [0.85, 0.88, 1.0], charShade: 0.82, charGrad: 0.12, bodyGrad: 0.3, sideTint: [0.75, 0.75, 0.95],
    blob: [0.4, 0.4, 0.5], actorShadow: true,
    top: "#0f172a", hor: "#1e293b", skyCurve: [0.1, 0.5, 0.9], fog: "#1e293b", fogNear: 10, fogFar: 80, sunDisc: "#38bdf8",
    sunCol: "#93c5fd", sunI: 2.2, sky: "#1e293b", ground: "#0f172a", hemiI: 0.35,
    bias: -0.0004, normalBias: 0.02,
  },
  prison: {
    // Cold institutional fluorescent dayroom / corridor
    az: 70, el: 65,
    lit: [1.52, 1.55, 1.62], shade: [0.28, 0.32, 0.42], lift: [0.06, 0.07, 0.12], lambert: 0.36, sideK: 0.82, term: 0.18,
    charTint: [0.96, 0.96, 1.0], charShade: 0.85, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.85, 0.88, 0.96],
    blob: [0.52, 0.52, 0.56], actorShadow: true,
    top: "#1e293b", hor: "#4a6075", skyCurve: [0.0, 0.4, 0.7], fog: "#4a6075", fogNear: 20, fogFar: 140, sunDisc: "#ffffff",
    sunCol: "#dcecf8", sunI: 3.0, sky: "#9bb8d9", ground: "#2b3038", hemiI: 0.6,
    bias: -0.0003, normalBias: 0.02,
  },
  pink: {
    // Baker-Miller Pink cell with vibrant magenta bounce
    az: 60, el: 55,
    lit: [1.62, 1.38, 1.48], shade: [0.55, 0.28, 0.42], lift: [0.12, 0.06, 0.10], lambert: 0.35, sideK: 0.85, term: 0.2,
    charTint: [1.02, 0.88, 0.95], charShade: 0.84, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.98, 0.82, 0.92],
    blob: [0.55, 0.45, 0.50], actorShadow: true,
    top: "#831843", hor: "#e66b97", skyCurve: [0.0, 0.5, 0.8], fog: "#e66b97", fogNear: 15, fogFar: 100, sunDisc: "#f472b6",
    sunCol: "#fff1f2", sunI: 3.2, sky: "#e97ebb", ground: "#8c3b5d", hemiI: 0.7,
    bias: -0.0003, normalBias: 0.02,
  },
};

export type WorldLook = {
  sky: { c: string[]; e: number[] };
  water: { near: string; mid: string; far: string; crest: string; trough: string; glint: string; shade: C3 };
  bounce: C3;
  sat: number;
  cloud: { lit: string; mid: string; shade: string };
};

export const LOOK: Record<LightMode, WorldLook> = {
  day: {
    sky: { c: ["#b8d0ec", "#9cbfea", "#6a9fe0", "#4f8cdb", "#3373cc"], e: [0, 3, 8, 16, 40] },
    water: { near: "#22a7b6", mid: "#167fb2", far: "#1a5596", crest: "#7ddfe8", trough: "#0e4a80", glint: "#ffffff", shade: [0.5, 0.56, 0.72] },
    cloud: { lit: "#fbf8f1", mid: "#e1e5f3", shade: "#c3cbe9" },
    bounce: [0, 0, 0],
    sat: 1.08,
  },
  golden: {
    sky: { c: ["#ffc47c", "#f7ae78", "#e8967c", "#c4848e", "#8a6f8a"], e: [0, 4, 10, 20, 40] },
    water: { near: "#1e3a6e", mid: "#355f96", far: "#d4a48e", crest: "#d9a088", trough: "#16294f", glint: "#ffe2b0", shade: [0.42, 0.46, 0.72] },
    cloud: { lit: "#ffd2a8", mid: "#f2a08f", shade: "#a98fc4" },
    bounce: [0.04, 0.02, 0.0],
    sat: 1.1,
  },
  workshop: {
    sky: { c: ["#cbd5e1", "#94a3b8", "#64748b", "#475569", "#334155"], e: [0, 5, 12, 22, 45] },
    water: { near: "#38bdf8", mid: "#0284c7", far: "#0369a1", crest: "#bae6fd", trough: "#075985", glint: "#ffffff", shade: [0.4, 0.5, 0.7] },
    cloud: { lit: "#f8fafc", mid: "#e2e8f0", shade: "#94a3b8" },
    bounce: [0.06, 0.04, 0.01],
    sat: 1.12,
  },
  night: {
    sky: { c: ["#1e293b", "#0f172a", "#090d16", "#04070e", "#020408"], e: [0, 4, 10, 25, 45] },
    water: { near: "#0e2a47", mid: "#081d33", far: "#040f1a", crest: "#38bdf8", trough: "#020912", glint: "#7dd3fc", shade: [0.2, 0.3, 0.5] },
    cloud: { lit: "#334155", mid: "#1e293b", shade: "#0f172a" },
    bounce: [0.02, 0.02, 0.04],
    sat: 1.05,
  },
  prison: {
    sky: { c: ["#1e293b", "#334155", "#475569", "#64748b", "#94a3b8"], e: [0, 5, 12, 25, 50] },
    water: { near: "#22a7b6", mid: "#167fb2", far: "#1a5596", crest: "#7ddfe8", trough: "#0e4a80", glint: "#ffffff", shade: [0.5, 0.56, 0.72] },
    cloud: { lit: "#f1f5f9", mid: "#cbd5e1", shade: "#64748b" },
    bounce: [0.01, 0.02, 0.04],
    sat: 1.04,
  },
  pink: {
    sky: { c: ["#831843", "#9d174d", "#be185d", "#db2777", "#f472b6"], e: [0, 6, 14, 28, 55] },
    water: { near: "#ec4899", mid: "#db2777", far: "#9d174d", crest: "#fbcfe8", trough: "#831843", glint: "#ffffff", shade: [0.6, 0.3, 0.45] },
    cloud: { lit: "#fdf2f8", mid: "#fbcfe8", shade: "#f472b6" },
    bounce: [0.12, 0.03, 0.08],
    sat: 1.18,
  },
};
