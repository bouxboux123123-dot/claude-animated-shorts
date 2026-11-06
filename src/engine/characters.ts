import * as THREE from "three";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";
import { NOINK } from "./ink";

export const INK = "#241726";
export const SKIN = "#ffe2c2";
export const WHITE = "#ffffff";
export const MOUTH = "#5a1e28";
export const TONGUE = "#e86e78";

type P2 = [number, number];

export class Pen {
  g: CanvasRenderingContext2D;
  ol = 12;
  rot: number[] | null = null;
  constructor(g: CanvasRenderingContext2D) {
    this.g = g;
  }
  P(x: number, y: number): P2 {
    if (!this.rot) return [x, y];
    const r = this.rot,
      a = r[0],
      cx = r[1],
      cy = r[2],
      dx = r.length > 3 ? r[3] : 0,
      dy = r.length > 4 ? r[4] : 0,
      c = Math.cos(a),
      s = Math.sin(a);
    return [cx + (x - cx) * c - (y - cy) * s + dx, cy + (x - cx) * s + (y - cy) * c + dy];
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
    if (w) {
      g.lineWidth = w;
      g.strokeStyle = strokeCol;
      g.lineJoin = "round";
      g.stroke();
    }
  }
  ell(
    cx: number,
    cy: number,
    rx: number,
    ry: number,
    fill: string | null,
    ol?: number,
    a0 = 0,
    a1 = 360,
    rot = 0,
    strokeCol = INK
  ) {
    const pts: P2[] = [];
    const rad = (d: number) => (d * Math.PI) / 180;
    const step = 8;
    for (let a = a0; a <= a1; a += step) {
      const th = rad(a);
      const x0 = rx * Math.cos(th);
      const y0 = ry * Math.sin(th);
      const r = rad(rot);
      const x = cx + x0 * Math.cos(r) - y0 * Math.sin(r);
      const y = cy + x0 * Math.sin(r) + y0 * Math.cos(r);
      pts.push([x, y]);
    }
    this.poly(pts, fill, ol, strokeCol);
  }
  line(pts: P2[], fill: string, w: number, ink = true) {
    const g = this.g;
    this.path(pts, false);
    g.lineCap = "round";
    g.lineJoin = "round";
    if (ink && w > 0) {
      g.lineWidth = w + 4;
      g.strokeStyle = INK;
      g.stroke();
    }
    g.lineWidth = Math.max(1, w);
    g.strokeStyle = fill;
    g.stroke();
  }
  rect(x: number, y: number, w: number, h: number, fill: string | null, ol?: number, strokeCol = INK) {
    this.poly(
      [
        [x, y],
        [x + w, y],
        [x + w, y + h],
        [x, y + h],
      ],
      fill,
      ol,
      strokeCol
    );
  }
}

// ---------------- CHARACTER CONTOUR BUILDER (characters.md) ----------------

/**
 * Superellipse head with dual exponents, chin egg taper, and gaze asymmetry
 * Crown n_top = 1.70, Jaw n_bot = 2.26, Egg = -0.125, Asymmetry = +0.10
 */
export function headPoints(
  cx = 300,
  cy = 280,
  w = 230,
  h = 214, // H/W ~ 0.93
  dir: "left" | "right" | "front" = "front",
  egg = -0.125,
  nTop = 1.7,
  nBot = 2.26
): P2[] {
  const pts: P2[] = [];
  const asym = dir === "front" ? 0 : dir === "right" ? 0.1 : -0.1;
  const a = w / 2;
  const b = h / 2;
  const steps = 64;

  for (let i = 0; i <= steps; i++) {
    const th = (i / steps) * Math.PI * 2;
    const c = Math.cos(th);
    const s = Math.sin(th);
    const n = s < 0 ? nTop : nBot;
    const exp = 2 / n;

    let X = Math.sign(c) * Math.pow(Math.abs(c), exp);
    let Y = Math.sign(s) * Math.pow(Math.abs(s), exp);

    // Egg chin taper & gaze asymmetry
    X *= (1 + egg * Y) * (1 + asym * Math.sign(X));

    pts.push([cx + a * X, cy + b * Y]);
  }
  return pts;
}

// ---------------- CHARACTER OUTFITS & ROLES ----------------

export type HairStyle = "comb_over" | "side_part" | "curly" | "bald_fringe" | "none";
export type Headwear = "cap" | "striped_cap" | "bowler" | "tophat" | "hard_hat" | "none";
export type OutfitType = "artisan_vest" | "banker_suit" | "inspector_coat" | "overalls" | "simple";
export type Expression =
  | "neutral"
  | "smile"
  | "happy"
  | "scheming"
  | "shocked"
  | "deadpan"
  | "suspicious"
  | "speaking";

export type CharacterSpec = {
  skin?: string;
  hair?: HairStyle;
  hairCol?: string;
  headwear?: Headwear;
  headwearCol?: string;
  beard?: boolean;
  beardCol?: string;
  moustache?: boolean;
  outfit?: OutfitType;
  coatCol?: string;
  vestCol?: string;
  shirtCol?: string;
  pantsCol?: string;
  expression?: Expression;
  facing?: "left" | "right" | "front";
  holdingProp?: "magnifying_glass" | "bill" | "tool" | "none";
  pose?: "standing" | "sitting" | "working" | "speaking";
};

/**
 * Draws a complete, stylized 2D cartoon character onto a design canvas (600 x 1000)
 */
export function drawCharacter(p: Pen, spec: CharacterSpec = {}) {
  const skin = spec.skin ?? SKIN;
  const facing = spec.facing ?? "front";
  const expr = spec.expression ?? "neutral";
  const pose = spec.pose ?? "standing";
  const hair = spec.hair ?? "comb_over";
  const hairCol = spec.hairCol ?? "#4a3322";
  const headwear = spec.headwear ?? "none";
  const outfit = spec.outfit ?? "artisan_vest";
  const vestCol = spec.vestCol ?? "#2d5a7b";
  const shirtCol = spec.shirtCol ?? "#f8fafc";
  const pantsCol = spec.pantsCol ?? "#334155";

  // Head center at [300, 280]
  const hpts = headPoints(300, 280, 225, 210, facing);

  // 1. TORSO & LEGS (behind head)
  if (pose === "sitting") {
    // Dangling legs
    p.line(
      [
        [260, 680],
        [260, 830],
        [250, 930],
      ],
      pantsCol,
      14,
      true
    );
    p.line(
      [
        [340, 680],
        [340, 830],
        [350, 930],
      ],
      pantsCol,
      14,
      true
    );
    // Shoes
    p.ell(245, 935, 16, 10, INK, 8);
    p.ell(355, 935, 16, 10, INK, 8);
  } else {
    // Standing legs (Legs = 1.4 HH ~ 300 units, soles at y = 975)
    p.line(
      [
        [260, 680],
        [255, 960],
      ],
      pantsCol,
      14,
      true
    );
    p.line(
      [
        [340, 680],
        [345, 960],
      ],
      pantsCol,
      14,
      true
    );
    // Shoes
    p.ell(250, 965, 18, 10, INK, 8);
    p.ell(350, 965, 18, 10, INK, 8);
  }

  // Torso shape (bean torso: y ~ 370 to 680)
  const torsoPts: P2[] = [
    [240, 390],
    [360, 390],
    [380, 520],
    [360, 680],
    [240, 680],
    [220, 520],
  ];
  p.poly(torsoPts, shirtCol, 12);

  // OUTFIT DETAILS: Vest / Suit / Overalls
  if (outfit === "artisan_vest" || outfit === "banker_suit") {
    // Vest front
    const vestPts: P2[] = [
      [240, 390],
      [270, 480],
      [270, 680],
      [240, 680],
      [220, 520],
    ];
    p.poly(vestPts, vestCol, 10);
    const vestRightPts: P2[] = [
      [360, 390],
      [330, 480],
      [330, 680],
      [360, 680],
      [380, 520],
    ];
    p.poly(vestRightPts, vestCol, 10);

    // Collar V-neck tie
    p.poly(
      [
        [285, 395],
        [315, 395],
        [308, 480],
        [300, 510],
        [292, 480],
      ],
      "#b91c1c",
      6
    );

    // Brass buttons on vest
    for (const by of [530, 580, 630]) {
      p.ell(280, by, 5, 5, "#facc15", 4);
    }
  } else if (outfit === "inspector_coat") {
    // Long coat
    p.poly(
      [
        [230, 390],
        [370, 390],
        [390, 720],
        [210, 720],
      ],
      vestCol,
      12
    );
    p.line(
      [
        [300, 430],
        [300, 720],
      ],
      INK,
      4,
      false
    );
    for (const by of [460, 530, 600]) {
      p.ell(315, by, 6, 6, "#e2e8f0", 4);
    }
  }

  // 2. HEAD (in front of torso)
  p.poly(hpts, skin, 12);

  // 3. HAIR (drawn on head)
  if (hair === "comb_over") {
    const hairPts: P2[] = [
      [195, 260],
      [210, 200],
      [260, 180],
      [340, 185],
      [390, 220],
      [395, 260],
      [380, 240],
      [320, 210],
      [240, 220],
      [195, 260],
    ];
    p.poly(hairPts, hairCol, 10);
  } else if (hair === "curly") {
    for (const [hx, hy, r] of [
      [210, 220, 26],
      [250, 190, 30],
      [300, 180, 32],
      [350, 190, 30],
      [385, 220, 26],
    ]) {
      p.ell(hx, hy, r, r, hairCol, 8);
    }
  }

  // HEADWEAR (if present)
  if (headwear === "cap" || headwear === "striped_cap") {
    const capCol = spec.headwearCol ?? (headwear === "striped_cap" ? "#3b82f6" : "#475569");
    // Cap brim
    p.poly(
      [
        [175, 230],
        [415, 230],
        [430, 250],
        [165, 250],
      ],
      capCol,
      10
    );
    // Cap dome
    p.poly(
      [
        [190, 230],
        [220, 160],
        [370, 160],
        [400, 230],
      ],
      capCol,
      10
    );
    if (headwear === "striped_cap") {
      // White engineer stripes
      for (let sx = 230; sx <= 360; sx += 24) {
        p.line(
          [
            [sx, 165],
            [sx, 225],
          ],
          "#ffffff",
          6,
          false
        );
      }
    }
  } else if (headwear === "bowler") {
    // Bowler hat
    p.poly(
      [
        [170, 240],
        [420, 240],
        [410, 252],
        [180, 252],
      ],
      "#1e293b",
      10
    );
    p.poly(
      [
        [210, 240],
        [220, 140],
        [370, 140],
        [380, 240],
      ],
      "#1e293b",
      10
    );
    p.rect(210, 225, 170, 15, "#b91c1c", 4); // Red hatband
  }

  // 4. EYES & NOSE (Eyes spacing ~ 0.26 W ~ 58 units)
  const eyeY = 275;
  const leftEyeX = 268;
  const rightEyeX = 328;

  if (expr === "deadpan") {
    // Lidded deadpan half circles
    p.ell(leftEyeX, eyeY, 14, 12, WHITE, 6, 0, 180);
    p.line(
      [
        [leftEyeX - 16, eyeY],
        [leftEyeX + 16, eyeY],
      ],
      INK,
      7,
      false
    );
    p.ell(leftEyeX, eyeY + 4, 6, 6, INK, 0);

    p.ell(rightEyeX, eyeY, 14, 12, WHITE, 6, 0, 180);
    p.line(
      [
        [rightEyeX - 16, eyeY],
        [rightEyeX + 16, eyeY],
      ],
      INK,
      7,
      false
    );
    p.ell(rightEyeX, eyeY + 4, 6, 6, INK, 0);
  } else if (expr === "scheming") {
    // Angled eyebrows, narrow pupils
    p.line(
      [
        [leftEyeX - 18, eyeY - 14],
        [leftEyeX + 14, eyeY - 8],
      ],
      INK,
      7,
      false
    );
    p.line(
      [
        [rightEyeX - 14, eyeY - 8],
        [rightEyeX + 18, eyeY - 14],
      ],
      INK,
      7,
      false
    );
    p.ell(leftEyeX, eyeY, 12, 8, INK, 0);
    p.ell(rightEyeX, eyeY, 12, 8, INK, 0);
  } else if (expr === "shocked") {
    // Huge round circular eyes
    p.ell(leftEyeX, eyeY, 18, 18, WHITE, 7);
    p.ell(leftEyeX, eyeY, 6, 6, INK, 0);
    p.ell(rightEyeX, eyeY, 18, 18, WHITE, 7);
    p.ell(rightEyeX, eyeY, 6, 6, INK, 0);
  } else {
    // Natural / speaking
    p.ell(leftEyeX, eyeY, 12, 10, INK, 0);
    p.ell(rightEyeX, eyeY, 12, 10, INK, 0);
    // Eyebrows
    p.line(
      [
        [leftEyeX - 14, eyeY - 16],
        [leftEyeX + 14, eyeY - 16],
      ],
      INK,
      6,
      false
    );
    p.line(
      [
        [rightEyeX - 14, eyeY - 16],
        [rightEyeX + 14, eyeY - 16],
      ],
      INK,
      6,
      false
    );
  }

  // 5. MOUTH
  const mouthY = 325;
  if (expr === "speaking") {
    // Open talking mouth showing teeth & tongue
    p.ell(298, mouthY, 20, 14, MOUTH, 6);
    p.rect(286, mouthY - 10, 24, 7, WHITE, 2); // Top teeth
    p.ell(298, mouthY + 6, 12, 6, TONGUE, 0); // Tongue
  } else if (expr === "scheming" || expr === "smile") {
    // Confident smirk / smile
    p.line(
      [
        [282, mouthY - 4],
        [300, mouthY + 6],
        [322, mouthY - 6],
      ],
      INK,
      7,
      false
    );
  } else {
    // Subtle straight deadpan line
    p.line(
      [
        [285, mouthY],
        [312, mouthY],
      ],
      INK,
      6,
      false
    );
  }

  // 6. ARMS & HANDS
  const prop = spec.holdingProp ?? "none";
  if (prop === "magnifying_glass") {
    // Left arm down, right arm holding loupe in front of face
    p.line(
      [
        [230, 420],
        [210, 540],
        [220, 600],
      ],
      shirtCol,
      12,
      true
    );
    p.ell(220, 605, 12, 12, skin, 6); // Left hand dot

    p.line(
      [
        [370, 420],
        [410, 480],
        [370, 360],
      ],
      shirtCol,
      12,
      true
    );
    p.ell(370, 360, 12, 12, skin, 6); // Right hand holding handle
    // Brass magnifying glass
    p.line(
      [
        [370, 360],
        [345, 310],
      ],
      "#ca8a04",
      8,
      true
    );
    p.ell(330, 285, 26, 26, "rgba(224,242,254,0.4)", 8, 0, 360, 0, "#ca8a04");
  } else if (prop === "bill") {
    // Hands holding currency bill at chest height
    p.line(
      [
        [230, 420],
        [260, 510],
      ],
      shirtCol,
      12,
      true
    );
    p.ell(265, 510, 12, 12, skin, 6);
    p.line(
      [
        [370, 420],
        [340, 510],
      ],
      shirtCol,
      12,
      true
    );
    p.ell(335, 510, 12, 12, skin, 6);
    // Currency note held flat between hands
    p.rect(260, 490, 80, 45, "#86efac", 6);
  } else {
    // Natural standing arms
    p.line(
      [
        [230, 420],
        [215, 550],
        [220, 610],
      ],
      shirtCol,
      12,
      true
    );
    p.ell(220, 615, 12, 12, skin, 6);
    p.line(
      [
        [370, 420],
        [385, 550],
        [380, 610],
      ],
      shirtCol,
      12,
      true
    );
    p.ell(380, 615, 12, 12, skin, 6);
  }
}

// ---------------- 3D ACTOR BILLBOARD & POOL ----------------

const blank = (() => {
  const c = typeof document !== "undefined" ? document.createElement("canvas") : ({} as HTMLCanvasElement);
  if (c.getContext) {
    c.width = c.height = 2;
  }
  return new THREE.CanvasTexture(c);
})();

export const SU = 0.00216; // 1000 design units = 2.16m
const BODY_GEO = (() => {
  const g = new THREE.PlaneGeometry(600 * SU, 1000 * SU);
  g.translate(0, (975 - 500) * SU, 0);
  return g;
})();

const CARD_GEO = new THREE.PlaneGeometry(1, 1);

export class Actor {
  mesh: THREE.Mesh;
  mat: THREE.MeshLambertMaterial;
  blobMesh: THREE.Mesh;

  constructor(parent: THREE.Object3D) {
    this.mat = cardShade(
      new THREE.MeshLambertMaterial({
        map: blank,
        alphaTest: 0.5,
        side: THREE.DoubleSide,
      })
    );
    this.mesh = new THREE.Mesh(BODY_GEO, this.mat);
    this.mesh.castShadow = false;
    this.mesh.receiveShadow = true;
    this.mesh.layers.set(NOINK);
    this.mesh.renderOrder = 2;

    // Contact shadow multiply blob under feet
    const blobTex = makeBlobTexture();
    this.blobMesh = new THREE.Mesh(CARD_GEO, blobMaterial(blobTex));
    this.blobMesh.rotation.x = -Math.PI / 2;
    this.blobMesh.scale.set(0.9, 0.5, 1);
    this.blobMesh.position.y = 0.02; // Just above floor
    this.blobMesh.renderOrder = 1;
    this.blobMesh.layers.set(NOINK);

    parent.add(this.blobMesh);
    parent.add(this.mesh);
  }

  updateDrawing(spec: CharacterSpec, key: string) {
    const cv = typeof document !== "undefined" ? document.createElement("canvas") : null;
    if (cv) {
      cv.width = 600;
      cv.height = 1000;
      const g = cv.getContext("2d")!;
      drawCharacter(new Pen(g), spec);
      const tex = new THREE.CanvasTexture(cv);
      tex.colorSpace = THREE.SRGBColorSpace;
      this.mat.map = tex;
      this.mat.needsUpdate = true;
    }
  }

  setPosition(x: number, y: number, z: number) {
    this.mesh.position.set(x, y, z);
    this.blobMesh.position.set(x, y + 0.02, z);
  }

  lookAtCamera(cam: THREE.Camera) {
    this.mesh.quaternion.copy(cam.quaternion);
  }
}

function makeBlobTexture(): THREE.CanvasTexture {
  const cv = typeof document !== "undefined" ? document.createElement("canvas") : ({} as HTMLCanvasElement);
  if (cv.getContext) {
    cv.width = cv.height = 128;
    const g = cv.getContext("2d")!;
    const gr = g.createRadialGradient(64, 64, 10, 64, 64, 60);
    gr.addColorStop(0, "rgba(0,0,0,0.75)");
    gr.addColorStop(0.5, "rgba(0,0,0,0.35)");
    gr.addColorStop(1, "rgba(0,0,0,0.0)");
    g.fillStyle = gr;
    g.fillRect(0, 0, 128, 128);
  }
  return new THREE.CanvasTexture(cv);
}
