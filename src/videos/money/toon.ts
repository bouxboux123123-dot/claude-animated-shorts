// 2D cartoon characters and procedural props for "How Money Is Printed"
// Built on Canvas2D Pen API with bean-head characters, plum ink outlines (#241726).
export const INK = "#241726";
export const SKIN = "#ffe2c2";
const WHITE = "#ffffff";

export type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;

export const ellPts = (cx: number, cy: number, rx: number, ry: number, a0 = 0, a1 = 360, rot = 0): P2[] => {
  const pts: P2[] = [];
  const cosR = Math.cos(rot), sinR = Math.sin(rot);
  for (let i = 0; i <= 32; i++) {
    const a = rad(a0 + ((a1 - a0) * i) / 32);
    const x = rx * Math.cos(a), y = ry * Math.sin(a);
    pts.push([cx + x * cosR - y * sinR, cy + x * sinR + y * cosR]);
  }
  return pts;
};

export class Pen {
  g: CanvasRenderingContext2D;
  ol = 10;
  rot: number[] | null = null;
  constructor(g: CanvasRenderingContext2D) { this.g = g; }

  P(x: number, y: number): P2 {
    if (!this.rot) return [x, y];
    const [a, cx, cy] = this.rot;
    const c = Math.cos(a), s = Math.sin(a);
    return [cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c];
  }

  path(pts: P2[], close: boolean) {
    const g = this.g;
    g.beginPath();
    pts.forEach((p, i) => { const [x, y] = this.P(p[0], p[1]); if (i) g.lineTo(x, y); else g.moveTo(x, y); });
    if (close) g.closePath();
  }

  poly(pts: P2[], fill: string | null, ol?: number) {
    const g = this.g, w = ol ?? this.ol;
    this.path(pts, true);
    if (fill) { g.fillStyle = fill; g.fill(); }
    if (w) { g.lineWidth = w; g.strokeStyle = INK; g.lineJoin = "round"; g.stroke(); }
  }

  ell(cx: number, cy: number, rx: number, ry: number, fill: string | null, ol?: number, a0 = 0, a1 = 360, rot = 0) {
    this.poly(ellPts(cx, cy, rx, ry, a0, a1, rot), fill, ol);
  }

  rect(x: number, y: number, w: number, h: number, fill: string | null, ol?: number) {
    const pts: P2[] = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
    this.poly(pts, fill, ol);
  }

  line(pts: P2[], stroke: string, w: number) {
    const g = this.g;
    this.path(pts, false);
    g.strokeStyle = stroke;
    g.lineWidth = w;
    g.lineCap = "round";
    g.stroke();
  }

  dot(cx: number, cy: number, r: number, fill = INK) {
    const [x, y] = this.P(cx, cy);
    this.g.beginPath();
    this.g.arc(x, y, r, 0, Math.PI * 2);
    this.g.fillStyle = fill;
    this.g.fill();
  }
}

// ---------------- bean head character renderer ----------------
export type CharRole = "citizen" | "worker" | "counterfeiter" | "inspector";

export const drawChar = (g: CanvasRenderingContext2D, role: CharRole, f: number, expression = "neutral") => {
  const p = new Pen(g);
  g.save();

  // Subtle breathing/walking bob
  const bob = Math.sin(f * 0.18) * 8;
  const cx = 300, cy = 520 + bob;

  // Outfit colors
  let jacket = "#2b6cb0", pants = "#1a202c", hat = "hair";
  if (role === "worker") {
    jacket = "#dd6b20"; pants = "#2d3748"; hat = "helmet";
  } else if (role === "counterfeiter") {
    jacket = "#374151"; pants = "#1f2937"; hat = "fedora";
  } else if (role === "inspector") {
    jacket = "#f8fafc"; pants = "#0f172a"; hat = "glasses";
  }

  // 1. Legs
  p.line([[cx - 48, cy + 200], [cx - 48, cy + 380]], pants, 38);
  p.line([[cx + 48, cy + 200], [cx + 48, cy + 380]], pants, 38);
  // Boots
  p.ell(cx - 58, cy + 395, 44, 22, INK, 8);
  p.ell(cx + 58, cy + 395, 44, 22, INK, 8);

  // 2. Torso / Coat
  p.poly([
    [cx - 90, cy + 30],
    [cx + 90, cy + 30],
    [cx + 110, cy + 220],
    [cx - 110, cy + 220],
  ], jacket, 12);

  // Worker reflective safety stripes
  if (role === "worker") {
    p.rect(cx - 100, cy + 110, 200, 26, "#fbbf24", 0);
    p.line([[cx - 45, cy + 30], [cx - 45, cy + 110]], "#fbbf24", 16);
    p.line([[cx + 45, cy + 30], [cx + 45, cy + 110]], "#fbbf24", 16);
  }

  // 3. Bean Head
  const hy = cy - 95;
  const headPts: P2[] = [];
  for (let i = 0; i <= 36; i++) {
    const th = (i / 36) * Math.PI * 2;
    const rx = 94 * (1 + 0.1 * Math.sin(th));
    const ry = 108 * (1 - 0.08 * Math.cos(th));
    headPts.push([cx + rx * Math.cos(th), hy + ry * Math.sin(th)]);
  }
  p.poly(headPts, SKIN, 12);

  // 4. Hair / Hats
  if (hat === "hair") {
    p.poly([
      [cx - 85, hy - 40],
      [cx - 92, hy - 110],
      [cx - 40, hy - 130],
      [cx + 10, hy - 135],
      [cx + 60, hy - 125],
      [cx + 92, hy - 100],
      [cx + 85, hy - 35],
      [cx + 40, hy - 65],
      [cx - 30, hy - 65],
    ], "#4a2810", 10);
  } else if (hat === "helmet") {
    p.ell(cx, hy - 70, 115, 58, "#eab308", 12, 180, 360);
    p.rect(cx - 120, hy - 72, 240, 22, "#ca8a04", 10);
  } else if (hat === "fedora") {
    p.ell(cx, hy - 60, 135, 24, "#111827", 10);
    p.poly([
      [cx - 78, hy - 60],
      [cx - 68, hy - 130],
      [cx, hy - 115],
      [cx + 68, hy - 130],
      [cx + 78, hy - 60],
    ], "#1f2937", 10);
  }

  // 5. Eyes
  const eyeY = hy - 12;
  const eyeSep = 34;
  if (expression === "shock") {
    p.ell(cx - eyeSep, eyeY, 18, 24, WHITE, 6);
    p.ell(cx + eyeSep, eyeY, 18, 24, WHITE, 6);
    p.dot(cx - eyeSep, eyeY, 7, INK);
    p.dot(cx + eyeSep, eyeY, 7, INK);
  } else {
    p.ell(cx - eyeSep, eyeY, 12, 16, INK, 0);
    p.ell(cx + eyeSep, eyeY, 12, 16, INK, 0);
  }

  // Inspector Spectacles
  if (hat === "glasses") {
    p.ell(cx - eyeSep, eyeY, 28, 26, null, 8);
    p.ell(cx + eyeSep, eyeY, 28, 26, null, 8);
    p.line([[cx - 8, eyeY], [cx + 8, eyeY]], INK, 8);
  }

  // 6. Mouth
  const mouthY = hy + 46;
  if (expression === "shock") {
    p.ell(cx, mouthY + 6, 22, 28, INK, 0);
  } else if (expression === "smirk") {
    p.line([[cx - 22, mouthY], [cx + 5, mouthY + 10], [cx + 28, mouthY - 4]], INK, 8);
  } else {
    p.line([[cx - 24, mouthY], [cx + 24, mouthY]], INK, 8);
  }

  // 7. Arms and Hands
  if (expression === "shock") {
    // Both hands clutching cheeks in shock
    p.line([[cx - 90, cy + 45], [cx - 130, cy - 20], [cx - 100, hy + 20]], jacket, 32);
    p.line([[cx + 90, cy + 45], [cx + 130, cy - 20], [cx + 100, hy + 20]], jacket, 32);
    p.dot(cx - 96, hy + 20, 22, SKIN);
    p.dot(cx + 96, hy + 20, 22, SKIN);
  } else {
    // Natural presentation pose: left arm relaxed, right arm raised
    p.line([[cx - 90, cy + 45], [cx - 130, cy + 180]], jacket, 32);
    p.line([[cx + 90, cy + 45], [cx + 140, cy + 140]], jacket, 32);
    p.dot(cx - 135, cy + 195, 20, SKIN);
    p.dot(cx + 148, cy + 148, 20, SKIN);
  }

  g.restore();
};

// ---------------- dollar bill card & props ----------------
export type BillProps = {
  stage: string;
  tilt?: number; // degrees
};

export const drawDollarCard = (g: CanvasRenderingContext2D, props: BillProps) => {
  const p = new Pen(g);
  g.save();

  const w = 540, h = 280;
  const x0 = 30, y0 = 35;

  // 1. Banknote Cotton Linen Cloth Base (#e8e6dc)
  p.rect(x0, y0, w, h, "#e8e6dc", 12);

  // 2. Intaglio green engraved borders
  p.rect(x0 + 14, y0 + 14, w - 28, h - 28, "#dce7da", 6);
  p.rect(x0 + 24, y0 + 24, w - 48, h - 48, null, 4);

  // Red and blue security silk fibers (Fact 2)
  p.line([[x0 + 70, y0 + 55], [x0 + 95, y0 + 78]], "#dc2626", 5);
  p.line([[x0 + 410, y0 + 170], [x0 + 440, y0 + 195]], "#2563eb", 5);
  p.line([[x0 + 170, y0 + 210], [x0 + 195, y0 + 230]], "#dc2626", 5);
  p.line([[x0 + 340, y0 + 80], [x0 + 365, y0 + 102]], "#2563eb", 5);

  // 3. Center Oval Portrait
  const cx = x0 + w / 2, cy = y0 + h / 2;
  p.ell(cx, cy, 74, 90, "#c4d6c0", 8);
  p.ell(cx, cy - 6, 46, 54, SKIN, 6);
  p.dot(cx - 14, cy - 10, 5);
  p.dot(cx + 14, cy - 10, 5);
  p.line([[cx - 10, cy + 16], [cx + 10, cy + 16]], INK, 4);

  // 4. Color-Shifting Numeral "100" (Fact 3)
  // Shifts between copper (#c26d24) and emerald (#16a34a)
  const tilt = props.tilt ?? 0;
  const shiftT = Math.max(0, Math.min(1, (tilt + 5) / 10));
  const numCol = shiftT > 0.5 ? "#16a34a" : "#c26d24";

  g.fillStyle = numCol;
  g.font = "bold 56px sans-serif";
  g.textAlign = "center";
  g.fillText("100", x0 + w - 95, y0 + h - 45);
  g.strokeStyle = INK;
  g.lineWidth = 4;
  g.strokeText("100", x0 + w - 95, y0 + h - 45);

  // 5. EURion Constellation (Fact 4): 5 yellow/gold rings
  const ringCol = "#eab308";
  const rX = x0 + 110, rY = y0 + 75;
  const rings: P2[] = [[0, 0], [28, -12], [56, 4], [26, 30], [50, 44]];
  for (const [dx, dy] of rings) {
    p.ell(rX + dx, rY + dy, 9, 9, null, 4);
    g.strokeStyle = ringCol;
    g.lineWidth = 4;
    g.stroke();
  }

  // Intaglio Header
  g.fillStyle = "#1e3a1e";
  g.font = "bold 22px monospace";
  g.fillText("FEDERAL RESERVE NOTE", cx, y0 + 52);

  // Lock overlay in EURion emergency stop beat
  if (props.stage === "eurion") {
    g.fillStyle = "rgba(239, 68, 68, 0.4)";
    g.fillRect(x0, y0, w, h);
    g.fillStyle = "#ef4444";
    g.font = "bold 38px sans-serif";
    g.fillText("LOCK: EURION DETECTED", cx, cy + 100);
  }

  g.restore();
};
