import * as THREE from "three";
import { makeMaterial, planks, beam, brick, stone, metalPlates, tiles, glass, paper, rep } from "./textures";
import { twoTone } from "./shade";

export const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);

// ---------------- PROCEDURAL 3D SET BUILDERS ----------------

export type RoomConfig = {
  width?: number; // X size (default 12)
  depth?: number; // Z size (default 10)
  height?: number; // Y size (default 6)
  floorType?: "wood" | "tile" | "stone";
  wallType?: "brick" | "plaster" | "stone";
  window?: {
    wall?: "back" | "left" | "right";
    width?: number;
    height?: number;
    y?: number;
    sunbeams?: boolean;
  };
  ceilingBeams?: boolean;
};

/**
 * Builds a complete, rich 3D room with textured floor, walls, baseboards, molding,
 * windows, and optional volumetric sunlight shafts.
 */
export function buildRoom(root: THREE.Object3D, cfg: RoomConfig = {}) {
  const w = cfg.width ?? 12;
  const d = cfg.depth ?? 10;
  const h = cfg.height ?? 6;
  const group = new THREE.Group();

  // 1. FLOOR
  const floorTex =
    cfg.floorType === "tile" ? rep(tiles(), w / 2, d / 2) : rep(planks(), w / 2, d / 2);
  const floorMat = makeMaterial("room_floor_" + (cfg.floorType ?? "wood"), floorTex);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(w, d), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  group.add(floor);

  // 2. WALLS (Back wall and side walls)
  const wallTex =
    cfg.wallType === "stone"
      ? rep(stone(), w / 3, h / 3)
      : rep(brick("brick_wall", "#a85338"), w / 2, h / 2);
  const wallMat = makeMaterial("room_wall_" + (cfg.wallType ?? "brick"), wallTex);

  // Back wall
  const backWall = new THREE.Mesh(new THREE.PlaneGeometry(w, h), wallMat);
  backWall.position.set(0, h / 2, -d / 2);
  backWall.receiveShadow = true;
  group.add(backWall);

  // Left wall
  const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(d, h), wallMat);
  leftWall.position.set(-w / 2, h / 2, 0);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.receiveShadow = true;
  group.add(leftWall);

  // Right wall
  const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(d, h), wallMat);
  rightWall.position.set(w / 2, h / 2, 0);
  rightWall.rotation.y = -Math.PI / 2;
  rightWall.receiveShadow = true;
  group.add(rightWall);

  // 3. BASEBOARDS & MOLDING (Dark wood trim along bottom of walls)
  const trimMat = makeMaterial("wood_trim", rep(beam(), 4, 1));
  const baseH = 0.25;
  const baseThick = 0.05;

  const backBase = new THREE.Mesh(new THREE.BoxGeometry(w, baseH, baseThick), trimMat);
  backBase.position.set(0, baseH / 2, -d / 2 + baseThick / 2);
  group.add(backBase);

  const leftBase = new THREE.Mesh(new THREE.BoxGeometry(baseThick, baseH, d), trimMat);
  leftBase.position.set(-w / 2 + baseThick / 2, baseH / 2, 0);
  group.add(leftBase);

  const rightBase = new THREE.Mesh(new THREE.BoxGeometry(baseThick, baseH, d), trimMat);
  rightBase.position.set(w / 2 - baseThick / 2, baseH / 2, 0);
  group.add(rightBase);

  // 4. CEILING BEAMS (if enabled)
  if (cfg.ceilingBeams !== false) {
    const beamMat = makeMaterial("ceiling_beam", rep(beam(), 6, 1));
    for (let z = -d / 2 + 1.5; z < d / 2; z += 2.0) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, 0.35, 0.25), beamMat);
      b.position.set(0, h - 0.175, z);
      b.castShadow = true;
      group.add(b);
    }
  }

  // 5. WINDOW WITH MULLIONS & SUNBEAM
  if (cfg.window) {
    const winW = cfg.window.width ?? 3.2;
    const winH = cfg.window.height ?? 2.8;
    const winY = cfg.window.y ?? 3.4;
    const winGroup = new THREE.Group();

    // Outer frame
    const frameMat = makeMaterial("win_frame", rep(beam(), 2, 2));
    const fTop = new THREE.Mesh(new THREE.BoxGeometry(winW, 0.12, 0.1), frameMat);
    fTop.position.y = winH / 2;
    const fBot = new THREE.Mesh(new THREE.BoxGeometry(winW, 0.16, 0.14), frameMat);
    fBot.position.y = -winH / 2;
    const fL = new THREE.Mesh(new THREE.BoxGeometry(0.12, winH, 0.1), frameMat);
    fL.position.x = -winW / 2;
    const fR = new THREE.Mesh(new THREE.BoxGeometry(0.12, winH, 0.1), frameMat);
    fR.position.x = winW / 2;
    winGroup.add(fTop, fBot, fL, fR);

    // Inner mullions (crossbars)
    const mVert = new THREE.Mesh(new THREE.BoxGeometry(0.06, winH, 0.08), frameMat);
    const mHor1 = new THREE.Mesh(new THREE.BoxGeometry(winW, 0.06, 0.08), frameMat);
    mHor1.position.y = winH / 6;
    const mHor2 = new THREE.Mesh(new THREE.BoxGeometry(winW, 0.06, 0.08), frameMat);
    mHor2.position.y = -winH / 6;
    winGroup.add(mVert, mHor1, mHor2);

    // Glass pane
    const glassMat = new THREE.MeshBasicMaterial({
      map: glass(),
      transparent: true,
      opacity: 0.65,
      side: THREE.DoubleSide,
    });
    const pane = new THREE.Mesh(new THREE.PlaneGeometry(winW - 0.1, winH - 0.1), glassMat);
    winGroup.add(pane);

    // Volumetric sunlight shaft
    if (cfg.window.sunbeams !== false) {
      const beamMat = new THREE.MeshBasicMaterial({
        color: 0xfff6d6,
        transparent: true,
        opacity: 0.18,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
      });
      const beamGeo = new THREE.CylinderGeometry(winW * 0.45, winW * 0.9, 5.5, 16, 1, true);
      const sunBeam = new THREE.Mesh(beamGeo, beamMat);
      sunBeam.rotation.x = Math.PI / 3.5;
      sunBeam.rotation.z = -Math.PI / 8;
      sunBeam.position.set(0.6, -1.5, 2.2);
      winGroup.add(sunBeam);
    }

    winGroup.position.set(0, winY, -d / 2 + 0.08);
    group.add(winGroup);
  }

  root.add(group);
  return group;
}

// ---------------- 3D FURNITURE & WORKBENCHES ----------------

export type WorkbenchConfig = {
  x?: number;
  y?: number;
  z?: number;
  width?: number; // default 2.6m
  depth?: number; // default 1.2m
  height?: number; // default 0.92m
  woodTone?: string;
  hasMat?: boolean;
};

/**
 * Builds a heavy wooden craftsman / treasury inspection workbench with thick top,
 * square legs, stretcher rails, lower shelf, and green inspection mat.
 */
export function buildWorkbench(root: THREE.Object3D, cfg: WorkbenchConfig = {}) {
  const x = cfg.x ?? 0;
  const y = cfg.y ?? 0;
  const z = cfg.z ?? 0;
  const w = cfg.width ?? 2.6;
  const d = cfg.depth ?? 1.2;
  const h = cfg.height ?? 0.92;

  const group = new THREE.Group();
  const woodMat = makeMaterial("bench_wood", rep(planks("bench_planks", cfg.woodTone ?? "#9a6538"), 2, 1));
  const postMat = makeMaterial("bench_post", rep(beam("bench_beam", "#7a4822"), 1, 2));

  // 1. Tabletop (thick beveled wood block)
  const topH = 0.1;
  const top = new THREE.Mesh(new THREE.BoxGeometry(w, topH, d), woodMat);
  top.position.y = h - topH / 2;
  top.castShadow = true;
  top.receiveShadow = true;
  group.add(top);

  // 2. Legs (4 thick posts)
  const legW = 0.12;
  const legH = h - topH;
  for (const dx of [-w / 2 + legW / 2 + 0.06, w / 2 - legW / 2 - 0.06]) {
    for (const dz of [-d / 2 + legW / 2 + 0.06, d / 2 - legW / 2 - 0.06]) {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(legW, legH, legW), postMat);
      leg.position.set(dx, legH / 2, dz);
      leg.castShadow = true;
      group.add(leg);
    }
  }

  // 3. Stretcher rails & lower storage shelf
  const shelfH = 0.05;
  const shelf = new THREE.Mesh(new THREE.BoxGeometry(w - 0.2, shelfH, d - 0.2), woodMat);
  shelf.position.y = 0.25;
  shelf.receiveShadow = true;
  group.add(shelf);

  // 4. Green inspection / cutting mat
  if (cfg.hasMat !== false) {
    const matMat = makeMaterial("cutting_mat", rep(planks("mat_tex", "#15803d"), 1, 1));
    const mat = new THREE.Mesh(new THREE.BoxGeometry(w * 0.65, 0.015, d * 0.7), matMat);
    mat.position.set(0, h + 0.008, 0);
    mat.receiveShadow = true;
    group.add(mat);
  }

  group.position.set(x, y, z);
  root.add(group);
  return group;
}

// ---------------- 3D STORAGE SHELVES WITH PROPS ----------------

export function buildShelves(
  root: THREE.Object3D,
  x = -4.5,
  y = 0,
  z = -3.5,
  w = 2.2,
  h = 3.2,
  d = 0.6
) {
  const group = new THREE.Group();
  const woodMat = makeMaterial("shelf_wood", rep(planks("shelf_p", "#854d0e"), 1, 2));

  // Uprights
  for (const dx of [-w / 2 + 0.05, w / 2 - 0.05]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.08, h, d), woodMat);
    post.position.set(dx, h / 2, 0);
    post.castShadow = true;
    group.add(post);
  }

  // Shelves (4 tiers)
  const numShelves = 4;
  for (let i = 0; i < numShelves; i++) {
    const sy = 0.3 + (i * (h - 0.5)) / (numShelves - 1);
    const shelf = new THREE.Mesh(new THREE.BoxGeometry(w, 0.06, d), woodMat);
    shelf.position.set(0, sy, 0);
    shelf.castShadow = true;
    group.add(shelf);

    // Micro-props on shelves: cans, bottles, paper boxes
    const canMat1 = makeMaterial("prop_can1", rep(metalPlates("can1", "#3b82f6"), 1, 1));
    const canMat2 = makeMaterial("prop_can2", rep(metalPlates("can2", "#eab308"), 1, 1));
    const paperMat = makeMaterial("prop_paper", rep(paper(), 1, 1));

    // Paint cans
    const can1 = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.22, 16), canMat1);
    can1.position.set(-w / 3, sy + 0.11, 0);
    can1.castShadow = true;
    const can2 = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.26, 16), canMat2);
    can2.position.set(-w / 3 + 0.25, sy + 0.13, 0);
    can2.castShadow = true;
    group.add(can1, can2);

    // Stacked currency reams / paper boxes
    const box = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.18, 0.3), paperMat);
    box.position.set(w / 4, sy + 0.09, 0);
    box.castShadow = true;
    group.add(box);
  }

  group.position.set(x, y, z);
  root.add(group);
  return group;
}

// ---------------- 3D INDUSTRIAL INTAGLIO STAMP PRESS ----------------

export function buildIntaglioPress(root: THREE.Object3D, x = 0, y = 0, z = 0) {
  const group = new THREE.Group();
  const steelMat = makeMaterial("press_steel", rep(metalPlates("press_st", "#334155"), 2, 2));
  const brassMat = makeMaterial("press_brass", rep(metalPlates("press_br", "#ca8a04"), 1, 1));

  // Heavy cast-iron base
  const base = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.45, 2.0), steelMat);
  base.position.y = 0.225;
  base.castShadow = true;
  base.receiveShadow = true;
  group.add(base);

  // Twin massive vertical side pillars
  for (const dx of [-1.1, 1.1]) {
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.4, 2.6, 0.8), steelMat);
    pillar.position.set(dx, 1.5, 0);
    pillar.castShadow = true;
    group.add(pillar);
  }

  // Top crossbeam arch
  const cross = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.5, 0.85), steelMat);
  cross.position.set(0, 2.75, 0);
  cross.castShadow = true;
  group.add(cross);

  // Twin counter-rotating roller cylinders
  const cylGeo = new THREE.CylinderGeometry(0.38, 0.38, 1.9, 24);
  const topCyl = new THREE.Mesh(cylGeo, brassMat);
  topCyl.rotation.z = Math.PI / 2;
  topCyl.position.set(0, 1.75, 0);
  topCyl.castShadow = true;
  const botCyl = new THREE.Mesh(cylGeo, steelMat);
  botCyl.rotation.z = Math.PI / 2;
  botCyl.position.set(0, 0.95, 0);
  botCyl.castShadow = true;
  group.add(topCyl, botCyl);

  // Stamping bed & conveyor deck
  const bed = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.08, 2.6), steelMat);
  bed.position.set(0, 1.35, 0);
  bed.receiveShadow = true;
  group.add(bed);

  // Hand wheel / gear on the side
  const wheel = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.06, 12, 24), brassMat);
  wheel.position.set(1.4, 1.75, 0);
  wheel.rotation.y = Math.PI / 2;
  group.add(wheel);

  // Pressure dials
  for (const gx of [-0.4, 0.4]) {
    const dial = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.06, 16), brassMat);
    dial.position.set(gx, 2.8, 0.45);
    dial.rotation.x = Math.PI / 2;
    group.add(dial);
  }

  group.position.set(x, y, z);
  root.add(group);
  return group;
}

// ---------------- 3D CURRENCY SHEET ON TABLE / BED ----------------

export function buildCurrencySheet(
  root: THREE.Object3D,
  x = 0,
  y = 0.94,
  z = 0,
  w = 0.95,
  l = 0.65
) {
  const paperMat = makeMaterial("currency_sheet_mat", rep(paper("sec_paper_note"), 1, 1));
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, 0.008, l), paperMat);
  mesh.position.set(x, y, z);
  mesh.receiveShadow = true;
  root.add(mesh);
  return mesh;
}
