import * as THREE from "three";
import { twoTone } from "./shade";

export const rng = (seed: number) => {
  let s = (seed * 9301 + 49297) % 233280 || 1;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
};

const cache = new Map<string, THREE.CanvasTexture>();

export const ctex = (
  key: string,
  w: number,
  h: number,
  draw: (g: CanvasRenderingContext2D, r: () => number) => void
): THREE.CanvasTexture => {
  let t = cache.get(key);
  if (!t) {
    const cv = typeof document !== "undefined" ? document.createElement("canvas") : ({} as HTMLCanvasElement);
    if (cv.getContext) {
      cv.width = w;
      cv.height = h;
      const g = cv.getContext("2d")!;
      draw(g, rng(key.length * 131 + key.charCodeAt(0)));
      t = new THREE.CanvasTexture(cv);
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 8;
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      cache.set(key, t);
    } else {
      // Fallback for headless non-DOM
      t = new THREE.CanvasTexture(cv);
    }
  }
  return t;
};

export const rep = (t: THREE.Texture, x: number, y: number) => {
  const c = t.clone();
  c.repeat.set(x, y);
  c.needsUpdate = true;
  return c;
};

const pick = <T>(r: () => number, a: T[]): T => a[Math.floor(r() * a.length) % a.length];

const _jc = new THREE.Color(),
  _hsl = { h: 0, s: 0, l: 0 };

export const jit = (r: () => number, hex: string, dv = 0.1, dh = 5, ds = 0.15) => {
  _jc.set(hex).getHSL(_hsl);
  const k = (a: number) => 1 + (r() * 2 - 1) * a;
  _jc.setHSL(
    (_hsl.h + ((r() * 2 - 1) * dh) / 360 + 1) % 1,
    Math.min(1, _hsl.s * k(ds)),
    Math.min(0.97, _hsl.l * k(dv))
  );
  return "#" + _jc.getHexString();
};

// ---------------- PROCEDURAL TEXTURES ----------------

/**
 * 1. WOOD PLANKS (Floors, decks, workbenches, crates)
 * Measured FWHM 3-4px seam lines, realistic board tone variation, subtle grain lines and nail heads.
 */
export const planks = (key = "planks_std", tone = "#c68a52") =>
  ctex(key, 512, 512, (g, r) => {
    for (let i = 0; i < 16; i++) {
      const rowTone = jit(r, tone, 0.08, 3, 0.1);
      g.fillStyle = rowTone;
      g.fillRect(0, i * 32, 512, 32);

      // Wood grain lines
      g.strokeStyle = "rgba(100,55,25,.25)";
      g.lineWidth = 1.5;
      for (let k = 0; k < 3; k++) {
        const y = i * 32 + 6 + r() * 20;
        g.beginPath();
        g.moveTo(0, y);
        g.bezierCurveTo(170, y + 4, 340, y - 4, 512, y + (r() - 0.5) * 4);
        g.stroke();
      }

      // Plank cut seam
      g.fillStyle = "rgba(50,28,14,.85)";
      g.fillRect(0, i * 32, 512, 2.5); // 2.5-3px seam

      // Vertical board butt-ends
      const cut1 = 120 + r() * 260;
      g.fillRect(cut1, i * 32, 2.5, 32);

      // Iron nail heads
      g.fillStyle = "#2d1b10";
      for (const x of [16, cut1 - 12, cut1 + 12, 496]) {
        if (x > 0 && x < 512) {
          g.beginPath();
          g.arc(x, i * 32 + 16, 2.0, 0, 7);
          g.fill();
        }
      }
    }
  });

/**
 * 2. WOOD BEAMS (Architectural rafters, table legs, framing posts)
 */
export const beam = (key = "beam_std", col = "#a8743f") =>
  ctex(key, 256, 256, (g, r) => {
    g.fillStyle = col;
    g.fillRect(0, 0, 256, 256);
    g.strokeStyle = "rgba(80,45,18,.2)";
    g.lineWidth = 2.0;
    for (let i = 0; i < 20; i++) {
      const y = r() * 256;
      g.beginPath();
      g.moveTo(0, y);
      g.bezierCurveTo(90, y + 4, 170, y - 4, 256, y);
      g.stroke();
    }
    // Edge chamfer highlight
    g.fillStyle = "rgba(255,255,255,.12)";
    g.fillRect(0, 0, 256, 4);
  });

/**
 * 3. BRICK (Factory walls, treasury masonry, chimney)
 */
export const brick = (key = "brick_std", baseCol = "#b35338", mortarCol = "#e2d5c3") =>
  ctex(key, 512, 512, (g, r) => {
    g.fillStyle = mortarCol;
    g.fillRect(0, 0, 512, 512);
    const cols = [baseCol, jit(r, baseCol, 0.08, 4), jit(r, baseCol, -0.08, -3)];
    for (let row = 0; row < 16; row++) {
      let x = (row % 2) * -32;
      while (x < 512) {
        g.fillStyle = pick(r, cols);
        g.fillRect(x + 2, row * 32 + 2, 60, 28);
        // Subtle flecks
        g.fillStyle = "rgba(0,0,0,.08)";
        for (let k = 0; k < 3; k++) g.fillRect(x + 6 + r() * 48, row * 32 + 4 + r() * 20, 3, 2);
        x += 64;
      }
    }
  });

/**
 * 4. CUT STONE & MASONRY (Classical pillars, foundation, vaults)
 */
export const stone = (key = "stone_std", baseCol = "#cbbfa6") =>
  ctex(key, 512, 512, (g, r) => {
    g.fillStyle = "#5d5446";
    g.fillRect(0, 0, 512, 512);
    for (let row = 0; row < 8; row++) {
      let x = row % 2 ? -60 : 0;
      while (x < 512) {
        const w = 90 + r() * 70;
        g.fillStyle = jit(r, baseCol, 0.07, 3);
        g.fillRect(x + 3, row * 64 + 3, w - 6, 58);
        // Bevel top highlight
        g.fillStyle = "rgba(255,255,255,.15)";
        g.fillRect(x + 3, row * 64 + 3, w - 6, 6);
        // Chisel texture
        g.fillStyle = "rgba(0,0,0,.06)";
        for (let k = 0; k < 8; k++) g.fillRect(x + 6 + r() * (w - 16), row * 64 + 8 + r() * 44, 4, 3);
        x += w;
      }
    }
  });

/**
 * 5. INDUSTRIAL METAL PLATES (Stamping presses, machinery, vault doors)
 * Steel/iron with riveted borders and plate seams.
 */
export const metalPlates = (key = "metal_plate", col = "#54606e") =>
  ctex(key, 512, 512, (g, r) => {
    g.fillStyle = "#22272e"; // Seam gap
    g.fillRect(0, 0, 512, 512);

    for (let y = 0; y < 2; y++) {
      for (let x = 0; x < 2; x++) {
        const px = x * 256 + 3,
          py = y * 256 + 3,
          pw = 250,
          ph = 250;
        g.fillStyle = jit(r, col, 0.05, 2);
        g.fillRect(px, py, pw, ph);

        // Plate top/left highlight
        g.fillStyle = "rgba(255,255,255,.16)";
        g.fillRect(px, py, pw, 5);
        g.fillRect(px, py, 5, ph);

        // Plate bottom/right bevel shadow
        g.fillStyle = "rgba(0,0,0,.25)";
        g.fillRect(px, py + ph - 5, pw, 5);
        g.fillRect(px + pw - 5, py, 5, ph);

        // Perimeter rivets
        g.fillStyle = "#1e2228";
        const drawRivet = (rx: number, ry: number) => {
          g.beginPath();
          g.arc(rx, ry, 3.5, 0, 7);
          g.fill();
          g.fillStyle = "rgba(255,255,255,.3)";
          g.beginPath();
          g.arc(rx - 1, ry - 1, 1.5, 0, 7);
          g.fill();
          g.fillStyle = "#1e2228";
        };

        for (let s = 20; s < pw - 10; s += 35) {
          drawRivet(px + s, py + 12);
          drawRivet(px + s, py + ph - 12);
        }
        for (let s = 20; s < ph - 10; s += 35) {
          drawRivet(px + 12, py + s);
          drawRivet(px + pw - 12, py + s);
        }
      }
    }
  });

/**
 * 6. SECURITY / CURRENCY PAPER (Banknote cotton-linen blend with security threads)
 */
export const paper = (key = "security_paper", baseCol = "#f1ece1") =>
  ctex(key, 512, 512, (g, r) => {
    g.fillStyle = baseCol;
    g.fillRect(0, 0, 512, 512);

    // Subtle paper grain
    g.fillStyle = "rgba(180,165,140,.12)";
    for (let i = 0; i < 4000; i++) {
      g.fillRect(r() * 512, r() * 512, 1.5, 1.5);
    }

    // Security fibers: random red and blue silk thread squiggles
    for (let i = 0; i < 70; i++) {
      g.strokeStyle = r() > 0.5 ? "rgba(210,40,40,.6)" : "rgba(30,80,210,.6)";
      g.lineWidth = 1.2;
      const sx = r() * 512,
        sy = r() * 512;
      g.beginPath();
      g.moveTo(sx, sy);
      g.bezierCurveTo(
        sx + (r() - 0.5) * 15,
        sy + (r() - 0.5) * 15,
        sx + (r() - 0.5) * 25,
        sy + (r() - 0.5) * 25,
        sx + (r() - 0.5) * 35,
        sy + (r() - 0.5) * 35
      );
      g.stroke();
    }
  });

/**
 * 7. FLOOR TILES (Checkerboard or clean laboratory/treasury floor)
 */
export const tiles = (key = "tiles_std", col1 = "#f8fafc", col2 = "#334155") =>
  ctex(key, 256, 256, (g, r) => {
    g.fillStyle = "#1e293b"; // Grout line
    g.fillRect(0, 0, 256, 256);
    const sz = 64;
    for (let y = 0; y < 4; y++) {
      for (let x = 0; x < 4; x++) {
        const isAlt = (x + y) % 2 === 0;
        g.fillStyle = isAlt ? jit(r, col1, 0.03, 1) : jit(r, col2, 0.03, 1);
        g.fillRect(x * sz + 1.5, y * sz + 1.5, sz - 3, sz - 3);
        // Polish reflection highlight
        g.fillStyle = "rgba(255,255,255,.08)";
        g.fillRect(x * sz + 2, y * sz + 2, sz - 4, (sz - 4) / 2);
      }
    }
  });

/**
 * 8. WINDOW GLASS (Translucent pane with light sheen)
 */
export const glass = (key = "glass_pane") =>
  ctex(key, 256, 256, (g) => {
    const gr = g.createLinearGradient(0, 0, 256, 256);
    gr.addColorStop(0, "rgba(220, 240, 255, 0.35)");
    gr.addColorStop(0.45, "rgba(255, 255, 255, 0.65)");
    gr.addColorStop(0.55, "rgba(220, 240, 255, 0.25)");
    gr.addColorStop(1, "rgba(180, 210, 240, 0.35)");
    g.fillStyle = gr;
    g.fillRect(0, 0, 256, 256);

    // Diagonal bright reflection glare
    g.strokeStyle = "rgba(255, 255, 255, 0.5)";
    g.lineWidth = 8;
    g.beginPath();
    g.moveTo(40, 0);
    g.lineTo(256, 216);
    g.stroke();
  });

/**
 * 9. GRASS & OUTDOOR MEADOW
 */
export const grass = (key = "grass_std") =>
  ctex(key, 512, 512, (g, r) => {
    g.fillStyle = "#79b950";
    g.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 70; i++) {
      g.fillStyle = pick(r, ["rgba(96,160,60,.35)", "rgba(140,205,95,.3)"]);
      g.beginPath();
      g.ellipse(r() * 512, r() * 512, 30 + r() * 60, 18 + r() * 30, r() * 3, 0, 7);
      g.fill();
    }
    g.lineCap = "round";
    for (let i = 0; i < 2600; i++) {
      const x = r() * 512,
        y = r() * 512,
        l = 5 + r() * 8;
      g.strokeStyle = pick(r, ["#5f9c3d", "#8fcc5f", "#6aa844", "#9ad46a"]);
      g.lineWidth = 2;
      g.beginPath();
      g.moveTo(x, y);
      g.lineTo(x + (r() - 0.5) * 4, y - l);
      g.stroke();
    }
    for (let i = 0; i < 35; i++) {
      g.fillStyle = pick(r, ["#fff7d0", "#ffe066", "#ffb3c8", "#b3e5fc"]);
      g.beginPath();
      g.arc(r() * 512, r() * 512, 3, 0, 7);
      g.fill();
    }
  });

/**
 * 10. CINDERBLOCK WALL (Institutional prison hallway)
 */
export const cinderblock = (key = "cinderblock_slate", baseTone = "#4a6075", mortarCol = "#2d3a47") =>
  ctex(key, 512, 512, (g, r) => {
    g.fillStyle = mortarCol;
    g.fillRect(0, 0, 512, 512);
    const blockH = 64;
    const blockW = 128;
    for (let y = 0; y < 512; y += blockH) {
      const row = Math.floor(y / blockH);
      const offset = (row % 2) * (blockW / 2);
      for (let x = -blockW / 2 + offset; x < 512 + blockW; x += blockW) {
        g.fillStyle = jit(r, baseTone, 0.07, 3, 0.1);
        g.fillRect(x + 2, y + 2, blockW - 4, blockH - 4);

        // Concrete grain stipple
        for (let k = 0; k < 12; k++) {
          g.fillStyle = r() > 0.5 ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.08)";
          g.fillRect(x + 4 + r() * (blockW - 12), y + 4 + r() * (blockH - 12), 2 + r() * 3, 2 + r() * 2);
        }
      }
    }
  });

/**
 * 11. BAKER-MILLER PINK WALL (Saturated painted cell wall)
 */
export const pinkCellWall = (key = "pink_cell_wall", baseTone = "#e66b97", mortarCol = "#c8527e") =>
  ctex(key, 512, 512, (g, r) => {
    g.fillStyle = baseTone;
    g.fillRect(0, 0, 512, 512);

    // Subtle painted-over cinderblock mortar lines
    g.strokeStyle = mortarCol;
    g.lineWidth = 3;
    const blockH = 64;
    const blockW = 128;
    for (let y = 0; y <= 512; y += blockH) {
      g.beginPath();
      g.moveTo(0, y);
      g.lineTo(512, y);
      g.stroke();
      const row = Math.floor(y / blockH);
      const offset = (row % 2) * (blockW / 2);
      for (let x = offset; x <= 512; x += blockW) {
        g.beginPath();
        g.moveTo(x, y);
        g.lineTo(x, y + blockH);
        g.stroke();
      }
    }

    // Soft painted roller stipple
    for (let i = 0; i < 300; i++) {
      const x = r() * 512, y = r() * 512;
      g.fillStyle = r() > 0.5 ? "rgba(233, 126, 187, 0.16)" : "rgba(209, 97, 139, 0.14)";
      g.beginPath();
      g.arc(x, y, 4 + r() * 10, 0, Math.PI * 2);
      g.fill();
    }
  });

/**
 * 12. BLACKBOARD SCIENTIFIC CHART (Explanation curve)
 */
export const blackboardChart = (key = "blackboard_chart") =>
  ctex(key, 512, 512, (g) => {
    // Slate chalkboard
    g.fillStyle = "#1e2925";
    g.fillRect(0, 0, 512, 512);

    // Subtle chalk dust smudges
    g.fillStyle = "rgba(255,255,255,0.03)";
    g.fillRect(10, 10, 492, 492);

    // Chalk axes
    g.strokeStyle = "rgba(255, 255, 255, 0.5)";
    g.lineWidth = 4;
    g.beginPath();
    g.moveTo(60, 440);
    g.lineTo(460, 440); // X axis (Time)
    g.moveTo(60, 440);
    g.lineTo(60, 80);  // Y axis (Aggression/Strength)
    g.stroke();

    // Dotted guide line at 15m
    g.strokeStyle = "rgba(244, 114, 182, 0.4)";
    g.setLineDash([8, 6]);
    g.beginPath();
    g.moveTo(220, 440);
    g.lineTo(220, 120);
    g.stroke();
    g.setLineDash([]);

    // Curve: Starts high, dips dramatically at 15m, then shoots to stratosphere
    g.strokeStyle = "#f472b6"; // Pink chalk curve
    g.lineWidth = 6;
    g.beginPath();
    g.moveTo(70, 200);
    g.bezierCurveTo(140, 220, 180, 400, 220, 410); // drops to bottom at 15 min
    g.bezierCurveTo(260, 420, 320, 360, 380, 180);
    g.bezierCurveTo(410, 90, 430, 70, 460, 60);   // sky high at 30 min+
    g.stroke();

    // Chalk text annotations
    g.fillStyle = "#ffffff";
    g.font = "bold 22px sans-serif";
    g.fillText("MUSCLE STRENGTH", 80, 60);
    g.font = "bold 18px sans-serif";
    g.fillStyle = "#f472b6";
    g.fillText("15 MIN (CALM)", 160, 470);
    g.fillStyle = "#ef4444";
    g.fillText("30 MIN (RAGE!)", 340, 100);
  });

// ---------------- MATERIAL CACHE & WRAPPERS ----------------

const matCache = new Map<string, THREE.MeshLambertMaterial>();

/**
 * Creates or retrieves a cached MeshLambertMaterial wrapped with twoTone cel shading
 */
export const makeMaterial = (
  key: string,
  mapTexture: THREE.Texture,
  options: Partial<THREE.MeshLambertMaterialParameters> = {}
): THREE.MeshLambertMaterial => {
  let m = matCache.get(key);
  if (!m) {
    m = twoTone(
      new THREE.MeshLambertMaterial({
        map: mapTexture,
        ...options,
      })
    );
    matCache.set(key, m);
  }
  return m;
};
