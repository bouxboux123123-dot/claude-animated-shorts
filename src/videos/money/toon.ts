// 2D Cartoon Cast & Procedural Assets for "How Money Is Printed"
// Built strictly on the reverse-engineered channel anatomy formula:
// 3.5 Head-Heights tall, superellipse heads (crown n=1.70, jaw n=2.26, H/W=0.93),
// plum ink outlines (#241726) weighted toward bottom-right, deadpan lidded half-disc eyes,
// single-stroke thin limbs with ink-dot hands, and NO blush / NO catchlights.
// Design space: 600 x 1000 units (soles anchored at y = 975).

export const INK = "#241726";
export const SKIN = "#ffe2c2";
export const WHITE = "#ffffff";
export const MOUTH_DARK = "#5a1e28";
export const TEETH_WHITE = "#ffffff";

export type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));

export class Pen {
  g: CanvasRenderingContext2D;
  ol = 12;
  rot: number[] | null = null;
  constructor(g: CanvasRenderingContext2D) {
    this.g = g;
  }

  P(x: number, y: number): P2 {
    if (!this.rot) return [x, y];
    const [a, cx, cy] = this.rot;
    const c = Math.cos(a),
      s = Math.sin(a);
    return [cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c];
  }

  path(pts: P2[], close: boolean) {
    const g = this.g;
    g.beginPath();
    pts.forEach((p, i) => {
      const [x, y] = this.P(p[0], p[1]);
      if (i) g.lineTo(x, y);
      else g.moveTo(x, y);
    });
    if (close) g.closePath();
  }

  poly(pts: P2[], fill: string | null, ol?: number, strokeCol = INK) {
    const g = this.g,
      w = ol ?? this.ol;
    this.path(pts, true);
    if (fill) {
      g.fillStyle = fill;
      g.fill();
    }
    if (w > 0) {
      g.lineWidth = w;
      g.strokeStyle = strokeCol;
      g.lineJoin = "round";
      g.stroke();
    }
  }

  ell(cx: number, cy: number, rx: number, ry: number, fill: string | null, ol?: number, strokeCol = INK) {
    const pts: P2[] = [];
    for (let i = 0; i <= 36; i++) {
      const a = (i / 36) * Math.PI * 2;
      pts.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]);
    }
    this.poly(pts, fill, ol, strokeCol);
  }

  rect(x: number, y: number, w: number, h: number, fill: string | null, ol?: number, strokeCol = INK) {
    const pts: P2[] = [
      [x, y],
      [x + w, y],
      [x + w, y + h],
      [x, y + h],
    ];
    this.poly(pts, fill, ol, strokeCol);
  }

  line(pts: P2[], stroke: string, w: number) {
    const g = this.g;
    this.path(pts, false);
    g.strokeStyle = stroke;
    g.lineWidth = w;
    g.lineCap = "round";
    g.lineJoin = "round";
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

// ---------------- Superellipse Head Generator ----------------
// Formula: |2(x-cx)/W|^n + |2(y-cy)/H|^n = 1
// With n_top = 1.70, n_bot = 2.26, egg taper = -0.125, asymmetry = +0.10
export const superellipseHeadPts = (cx: number, cy: number, w: number, h: number): P2[] => {
  const pts: P2[] = [];
  const N = 48;
  const rx = w / 2;
  const ry = h / 2;

  for (let i = 0; i < N; i++) {
    const theta = (i / N) * Math.PI * 2;
    const sinT = Math.sin(theta);
    const cosT = Math.cos(theta);

    // Crown exponent 1.70, Jaw exponent 2.26
    const n = sinT < 0 ? 1.70 : 2.26;
    const p = 2 / n;

    const signX = cosT >= 0 ? 1 : -1;
    const signY = sinT >= 0 ? 1 : -1;

    let x = rx * Math.pow(Math.abs(cosT), p) * signX;
    let y = ry * Math.pow(Math.abs(sinT), p) * signY;

    // Chin taper (narrows towards chin when y > 0)
    if (y > 0) {
      x *= 1.0 - 0.125 * (y / ry);
    }
    // Organic asymmetry (+10% subtle lean)
    x += (sinT * 0.08 - cosT * 0.02) * rx;

    pts.push([cx + x, cy + y]);
  }
  return pts;
};

// ---------------- Weighted Outline Renderer ----------------
// Draws thick outline along bottom-right shadow side (64 deg) and thin at top-left
export const drawWeightedSuperellipse = (
  p: Pen,
  cx: number,
  cy: number,
  w: number,
  h: number,
  fill: string,
  baseOl = 12
) => {
  const pts = superellipseHeadPts(cx, cy, w, h);
  // Base fill with normal outline
  p.poly(pts, fill, baseOl);

  // Additional weighted shadow stroke on bottom-right (between 0 and 150 deg)
  const g = p.g;
  g.save();
  g.beginPath();
  let first = true;
  for (const pt of pts) {
    const dx = pt[0] - cx;
    const dy = pt[1] - cy;
    // Angle in radians: 0 is right, Math.PI/2 is bottom
    const angle = Math.atan2(dy, dx);
    if (angle > -0.2 && angle < 2.5) {
      const [px, py] = p.P(pt[0], pt[1]);
      if (first) {
        g.moveTo(px, py);
        first = false;
      } else {
        g.lineTo(px, py);
      }
    }
  }
  g.strokeStyle = INK;
  g.lineWidth = baseOl * 1.5; // 3x weighted shadow side
  g.lineCap = "round";
  g.stroke();
  g.restore();
};

export type CharRole = "citizen" | "worker" | "counterfeiter" | "inspector";

export const drawChar = (
  g: CanvasRenderingContext2D,
  role: CharRole,
  f: number,
  expression = "neutral"
) => {
  const p = new Pen(g);
  g.save();

  // Walking/breathing organic bob (3.5% of height)
  const bob = Math.sin(f * 0.22) * 9;
  const cx = 300;
  const headCy = 216 + bob;

  // Head dimensions: wider than tall (H/W = 0.93)
  const headW = 246;
  const headH = 228;

  // Outfit styling
  let skinCol = SKIN;
  let jacketCol = "#2563eb";
  let pantsCol = "#1e293b";
  let bootsCol = "#0f172a";
  let hatType = "hair";

  if (role === "worker") {
    jacketCol = "#ea580c";
    pantsCol = "#334155";
    hatType = "hard_hat";
  } else if (role === "counterfeiter") {
    jacketCol = "#374151";
    pantsCol = "#1f2937";
    hatType = "fedora";
  } else if (role === "inspector") {
    jacketCol = "#ffffff";
    pantsCol = "#0f172a";
    hatType = "spectacles";
  }

  // ---------------- 1. LEGS (Single thin lines: 3.5 HH tall) ----------------
  const hipY = 590 + bob;
  const ankleY = 945;
  const legStroke = 12;

  // Stance with subtle weight shift
  const leftX = cx - 44;
  const rightX = cx + 44;

  p.line([[leftX, hipY], [leftX - 4, ankleY]], pantsCol, legStroke);
  p.line([[rightX, hipY], [rightX + 4, ankleY]], pantsCol, legStroke);

  // Ink-dot / small shoe cuffs (soles anchored at y=975)
  p.ell(leftX - 8, ankleY + 16, 26, 14, bootsCol, 6);
  p.ell(rightX + 8, ankleY + 16, 26, 14, bootsCol, 6);

  // ---------------- 2. TORSO (Bean/Pill Shape, 1.13 HH) ----------------
  const torsoTop = headCy + headH * 0.44;
  const torsoH = hipY - torsoTop + 20;
  const torsoW = headW * 0.88;

  // Bean torso curve
  const torsoPts: P2[] = [
    [cx - torsoW * 0.42, torsoTop],
    [cx + torsoW * 0.42, torsoTop],
    [cx + torsoW * 0.48, torsoTop + torsoH * 0.55],
    [cx + torsoW * 0.38, hipY + 10],
    [cx - torsoW * 0.38, hipY + 10],
    [cx - torsoW * 0.48, torsoTop + torsoH * 0.55],
  ];
  p.poly(torsoPts, jacketCol, 12);

  // Collar / tie / vest details
  if (role === "inspector") {
    // White lab coat lapels and navy tie
    p.line([[cx - 24, torsoTop], [cx, torsoTop + 90], [cx + 24, torsoTop]], INK, 6);
    p.poly([[cx - 10, torsoTop + 85], [cx + 10, torsoTop + 85], [cx, torsoTop + 165]], "#1e3a8a", 4);
  } else if (role === "worker") {
    // High-vis reflective stripes
    p.line([[cx - torsoW * 0.42, torsoTop + 70], [cx + torsoW * 0.42, torsoTop + 70]], "#fde047", 10);
    p.line([[cx - torsoW * 0.45, torsoTop + 140], [cx + torsoW * 0.45, torsoTop + 140]], "#fde047", 10);
  } else if (role === "counterfeiter") {
    // Dark trench coat buttons & turned-up collar
    p.dot(cx, torsoTop + 65, 5, "#111827");
    p.dot(cx, torsoTop + 115, 5, "#111827");
    p.dot(cx, torsoTop + 165, 5, "#111827");
  }

  // ---------------- 3. ARMS (Single-stroke thin limbs + ink dot hands) ----------------
  const armStroke = 10;
  const handR = 12;
  const armSwing = Math.sin(f * 0.22) * 16;

  // Left arm
  const shoulderL: P2 = [cx - torsoW * 0.44, torsoTop + 30];
  const handL: P2 = [shoulderL[0] - 22, shoulderL[1] + 175 + armSwing];
  p.line([shoulderL, [shoulderL[0] - 12, shoulderL[1] + 90], handL], jacketCol, armStroke);
  p.dot(handL[0], handL[1], handR, skinCol);
  // Hand ink outline
  p.ell(handL[0], handL[1], handR, handR, null, 5);

  // Right arm (action pose based on role)
  const shoulderR: P2 = [cx + torsoW * 0.44, torsoTop + 30];
  let handRPos: P2 = [shoulderR[0] + 22, shoulderR[1] + 175 - armSwing];

  if (role === "worker" && (expression === "smirk" || expression === "action")) {
    // Pulling lever pose
    handRPos = [shoulderR[0] + 75, shoulderR[1] - 40];
    p.line([shoulderR, [shoulderR[0] + 50, shoulderR[1] + 20], handRPos], jacketCol, armStroke);
    // Draw heavy machine lever
    p.line([[handRPos[0] - 10, handRPos[1] + 160], [handRPos[0] + 15, handRPos[1] - 50]], "#71717a", 16);
    p.dot(handRPos[0] + 15, handRPos[1] - 50, 20, "#dc2626"); // Red knob on lever
  } else if (role === "inspector") {
    // Holding magnifying loupe
    handRPos = [cx + 65, headCy + 40];
    p.line([shoulderR, [shoulderR[0] + 30, shoulderR[1] + 80], handRPos], jacketCol, armStroke);
    // Magnifying glass rim + handle
    p.ell(handRPos[0] + 30, handRPos[1] - 20, 28, 28, "rgba(224, 242, 254, 0.4)", 6);
    p.line([handRPos, [handRPos[0] + 18, handRPos[1] - 8]], "#b45309", 8);
  } else {
    p.line([shoulderR, [shoulderR[0] + 12, shoulderR[1] + 90], handRPos], jacketCol, armStroke);
  }
  p.dot(handRPos[0], handRPos[1], handR, skinCol);
  p.ell(handRPos[0], handRPos[1], handR, handR, null, 5);

  // ---------------- 4. HEAD (Superellipse with Plum Outline) ----------------
  drawWeightedSuperellipse(p, cx, headCy, headW, headH, skinCol, 12);

  // ---------------- 5. FACIAL FEATURES (The Channel Standard) ----------------
  // Eye spacing = 0.26 W (narrower deadpan spacing: 246 * 0.26 = 64px)
  const eyeGap = headW * 0.26;
  const eyeY = headCy - 8;
  const eyeL = cx - eyeGap / 2;
  const eyeR = cx + eyeGap / 2;

  // Eyebrows (tapered dark strokes, Skeptical asymmetry)
  const browY = eyeY - 26;
  const browW = headW * 0.17;
  const browThickness = 6;

  if (expression === "shock") {
    // Shock arched high brows
    p.line([[eyeL - browW / 2, browY - 14], [eyeL + browW / 2, browY - 20]], INK, browThickness);
    p.line([[eyeR - browW / 2, browY - 20], [eyeR + browW / 2, browY - 14]], INK, browThickness);

    // Shock eyes: White circular sclera (0.22 W = 54px) + tiny pupil dots (0.06 W = 15px)
    const scleraR = 24;
    p.ell(eyeL, eyeY, scleraR, scleraR, WHITE, 6);
    p.ell(eyeR, eyeY, scleraR, scleraR, WHITE, 6);
    p.dot(eyeL, eyeY, 6, INK);
    p.dot(eyeR, eyeY, 6, INK);
  } else if (expression === "smirk") {
    // One skeptical raised eyebrow
    p.line([[eyeL - browW / 2, browY - 16], [eyeL + browW / 2, browY - 24]], INK, browThickness);
    p.line([[eyeR - browW / 2, browY - 4], [eyeR + browW / 2, browY - 2]], INK, browThickness);

    // Lidded deadpan half-discs
    drawLiddedEye(p, eyeL, eyeY, headW * 0.18);
    drawLiddedEye(p, eyeR, eyeY, headW * 0.18);
  } else {
    // Default Deadpan: level brows, lidded half-discs
    p.line([[eyeL - browW / 2, browY - 6], [eyeL + browW / 2, browY - 4]], INK, browThickness);
    p.line([[eyeR - browW / 2, browY - 4], [eyeR + browW / 2, browY - 6]], INK, browThickness);

    drawLiddedEye(p, eyeL, eyeY, headW * 0.18);
    drawLiddedEye(p, eyeR, eyeY, headW * 0.18);
  }

  // Mouth: positioned at y + 0.19 H (around headCy + 44)
  const mouthY = headCy + 44;
  if (expression === "smirk") {
    // Tilted confident smirk
    p.line([[cx - 24, mouthY + 4], [cx + 28, mouthY - 8]], INK, 7);
  } else if (expression === "shock") {
    // O-mouth (interior #5a1e28)
    p.ell(cx, mouthY + 8, 20, 26, MOUTH_DARK, 7);
  } else {
    // Neutral deadpan short dash
    p.line([[cx - 18, mouthY], [cx + 18, mouthY]], INK, 7);
  }

  // ---------------- 6. HATS & ACCESSORIES ----------------
  if (hatType === "hard_hat") {
    // Safety Yellow construction helmet
    const capY = headCy - headH * 0.38;
    p.ell(cx, capY, headW * 0.58, 48, "#eab308", 10);
    p.rect(cx - headW * 0.62, capY + 12, headW * 1.24, 16, "#ca8a04", 8);
  } else if (hatType === "fedora") {
    // Noir detective / counterfeiter fedora
    const capY = headCy - headH * 0.38;
    p.ell(cx, capY + 14, headW * 0.68, 22, "#1f2937", 8);
    p.rect(cx - headW * 0.44, capY - 42, headW * 0.88, 54, "#374151", 8);
    p.rect(cx - headW * 0.44, capY - 6, headW * 0.88, 16, "#991b1b", 0); // Red band
  } else if (hatType === "spectacles") {
    // Round wireframe glasses on eyes
    p.ell(eyeL, eyeY, 28, 28, null, 6, INK);
    p.ell(eyeR, eyeY, 28, 28, null, 6, INK);
    p.line([[eyeL + 28, eyeY], [eyeR - 28, eyeY]], INK, 5); // Bridge
  } else {
    // Simple stylized hair tuft
    const hairY = headCy - headH * 0.46;
    p.poly(
      [
        [cx - 50, hairY + 12],
        [cx - 20, hairY - 24],
        [cx + 25, hairY - 14],
        [cx + 55, hairY + 18],
      ],
      "#3b2f2f",
      8
    );
  }

  // Sweat drop on stress beats
  if (expression === "shock" && role === "counterfeiter") {
    p.poly(
      [
        [cx + headW * 0.46, headCy - 30],
        [cx + headW * 0.48, headCy - 8],
        [cx + headW * 0.43, headCy - 8],
      ],
      "#60a5fa",
      4
    );
  }

  g.restore();
};

// Helper: Deadpan lidded eye (lid line + dark half-disc below)
const drawLiddedEye = (p: Pen, x: number, y: number, w: number) => {
  const g = p.g;
  const hw = w / 2;
  // Lid line
  p.line([[x - hw, y - 4], [x + hw, y - 4]], INK, 7);

  // Dark half-disc suspended below the lid
  g.save();
  g.beginPath();
  g.arc(x, y - 4, hw * 0.72, 0, Math.PI, false);
  g.fillStyle = INK;
  g.fill();
  g.restore();
};

// ---------------- Dollar Card Renderer (When inspectable) ----------------
export const drawDollarCard = (
  g: CanvasRenderingContext2D,
  opts: { stage: string; tilt?: number }
) => {
  const p = new Pen(g);
  g.save();

  // Federal Reserve Green border & pale parchment paper texture
  const w = 560;
  const h = 260;
  const x = 20;
  const y = 45;

  p.rect(x, y, w, h, "#eef6ee", 10);
  p.rect(x + 16, y + 16, w - 32, h - 32, null, 6, "#15803d");

  // Intaglio fine lathe guilloche border pattern
  g.strokeStyle = "#166534";
  g.lineWidth = 2;
  for (let d = 26; d < 42; d += 5) {
    g.strokeRect(x + d, y + d, w - d * 2, h - d * 2);
  }

  // Center Oval Portrait frame
  p.ell(x + w / 2, y + h / 2, 85, 95, "#f0fdf4", 6, "#166534");

  // Ben Franklin simplified silhouette portrait
  p.ell(x + w / 2, y + h / 2 - 12, 34, 42, "#15803d", 0);
  p.poly(
    [
      [x + w / 2 - 50, y + h / 2 + 55],
      [x + w / 2 + 50, y + h / 2 + 55],
      [x + w / 2 + 30, y + h / 2 + 10],
      [x + w / 2 - 30, y + h / 2 + 10],
    ],
    "#14532d",
    0
  );

  // Numeral "100" in bottom-right: Quantum Color-Shifting Ink!
  const numX = x + w - 100;
  const numY = y + h - 45;

  // In quantum shot (S6), tilt causes numeral to flip from copper to emerald green!
  const tilt = opts.tilt ?? 0;
  const isEmerald = Math.abs(tilt) > 4;
  const numColor = isEmerald ? "#10b981" : "#b45309"; // Emerald vs Copper-Bronze

  g.font = '900 62px "Impact", sans-serif';
  g.fillStyle = numColor;
  g.strokeStyle = INK;
  g.lineWidth = 4;
  g.strokeText("100", numX, numY);
  g.fillText("100", numX, numY);

  // EURion constellation rings (Shot 8)
  if (opts.stage === "eurion" || opts.stage === "scanner") {
    const rings = [
      [x + 120, y + 80],
      [x + 160, y + 110],
      [x + 140, y + 155],
      [x + 195, y + 140],
      [x + 175, y + 185],
    ];
    for (const [rx, ry] of rings) {
      p.ell(rx, ry, 12, 12, null, 4, "#eab308"); // Yellow circles
      p.dot(rx, ry, 3, "#ca8a04");
    }
  }

  // Red & blue synthetic security fibers scattered on paper
  g.lineWidth = 2;
  const fibers = [
    [x + 85, y + 65, "#ef4444"],
    [x + 220, y + 75, "#3b82f6"],
    [x + 440, y + 85, "#ef4444"],
    [x + 380, y + 190, "#3b82f6"],
    [x + 120, y + 210, "#ef4444"],
  ];
  for (const [fx, fy, col] of fibers as [number, number, string][]) {
    g.strokeStyle = col;
    g.beginPath();
    g.moveTo(fx, fy);
    g.bezierCurveTo(fx + 6, fy - 8, fx + 14, fy + 4, fx + 22, fy - 6);
    g.stroke();
  }

  g.restore();
};
