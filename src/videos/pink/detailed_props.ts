import * as THREE from "three";
import { makeMaterial, planks, beam, brick, tiles, rep } from "../../engine";

/**
 * Creates a clean stylized storybook paint can with metallic silver rims,
 * colored band wrap, and wire bail handle. (No programmatic UI fonts or barcodes).
 */
export function buildDetailedPaintCan(
  bandCol = "#0284c7",
  canRadius = 0.11,
  canHeight = 0.24
): THREE.Group {
  const can = new THREE.Group();
  const silverMat = makeMaterial("can_silver_rim", rep(beam("can_rim_shine", "#cbd5e1"), 1, 1));
  const bandMat = new THREE.MeshLambertMaterial({ color: bandCol });

  // Can Cylinder Body
  const cyl = new THREE.Mesh(new THREE.CylinderGeometry(canRadius, canRadius, canHeight, 24), silverMat);
  cyl.position.y = canHeight / 2;
  cyl.castShadow = true;
  cyl.receiveShadow = true;
  can.add(cyl);

  // Colored brand wrap band (middle section)
  const band = new THREE.Mesh(new THREE.CylinderGeometry(canRadius + 0.001, canRadius + 0.001, canHeight * 0.65, 24), bandMat);
  band.position.y = canHeight / 2;
  can.add(band);

  // Top and bottom metallic rolled rims
  const topRim = new THREE.Mesh(new THREE.CylinderGeometry(canRadius + 0.005, canRadius + 0.005, 0.015, 24), silverMat);
  topRim.position.y = canHeight;
  const botRim = new THREE.Mesh(new THREE.CylinderGeometry(canRadius + 0.005, canRadius + 0.005, 0.012, 24), silverMat);
  botRim.position.y = 0.006;
  can.add(topRim, botRim);

  // Wire bail handle
  const handleGeo = new THREE.TorusGeometry(canRadius * 0.95, 0.003, 6, 16, Math.PI);
  const handle = new THREE.Mesh(handleGeo, silverMat);
  handle.position.set(0, canHeight * 0.8, 0);
  handle.rotation.z = Math.PI / 2;
  handle.rotation.y = -0.4;
  can.add(handle);

  return can;
}

/**
 * Creates a stylized laboratory scale with sleek stainless plate and teal indicator.
 */
export function buildDigitalScale(): THREE.Group {
  const scale = new THREE.Group();

  const chassisMat = makeMaterial("scale_chassis", rep(beam("scale_dark", "#1e293b"), 1, 1));
  const plateMat = makeMaterial("scale_plate", rep(beam("scale_silver", "#cbd5e1"), 1, 1));

  // Scale body
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.035, 0.28), chassisMat);
  body.position.y = 0.0175;
  body.castShadow = true;
  body.receiveShadow = true;
  scale.add(body);

  // Circular stainless weighing plate
  const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.01, 24), plateMat);
  plate.position.set(0, 0.04, -0.02);
  plate.castShadow = true;
  scale.add(plate);

  // Teal digital display strip
  const lcdMat = new THREE.MeshBasicMaterial({ color: "#2dd4bf" });
  const lcd = new THREE.Mesh(new THREE.PlaneGeometry(0.10, 0.03), lcdMat);
  lcd.rotation.x = -Math.PI / 2 + 0.1;
  lcd.position.set(0, 0.036, 0.1);
  scale.add(lcd);

  return scale;
}

/**
 * Creates a clean glass measuring beaker with red liquid.
 */
export function buildGraduatedBeaker(): THREE.Group {
  const beaker = new THREE.Group();

  const glassMat = new THREE.MeshLambertMaterial({
    color: "#e2e8f0",
    transparent: true,
    opacity: 0.7,
    side: THREE.DoubleSide,
  });

  const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.05, 0.18, 16), glassMat);
  cup.position.y = 0.09;
  cup.castShadow = true;
  beaker.add(cup);

  // Red liquid fill inside
  const liquidMat = new THREE.MeshLambertMaterial({ color: 0xdc2626 });
  const liquid = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.045, 0.14, 16), liquidMat);
  liquid.position.y = 0.07;
  beaker.add(liquid);

  return beaker;
}

/**
 * Builds the scientific Paint Shop Workshop set.
 */
export function buildPaintShopWorkshop(root: THREE.Object3D, x = 0, y = 0, z = 0): THREE.Group {
  const shop = new THREE.Group();

  // 1. Back Wall
  const wallMat = makeMaterial("paint_shop_wall", rep(brick("workshop_brick", "#64748b"), 3, 2));
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(8, 4.5), wallMat);
  wall.position.set(0, 2.25, -2.5);
  wall.receiveShadow = true;
  shop.add(wall);

  // Floor
  const floorMat = makeMaterial("paint_shop_floor", rep(tiles(), 4, 4));
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(8, 6), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  shop.add(floor);

  // Workshop Window with Sunbeams
  const winFrameMat = makeMaterial("win_frame_mat", rep(beam("win_wood", "#1e293b"), 1, 1));
  const winFrame = new THREE.Mesh(new THREE.BoxGeometry(1.5, 2.0, 0.06), winFrameMat);
  winFrame.position.set(1.6, 2.7, -2.48);
  shop.add(winFrame);

  // Soft sunbeam volumetric light shaft from window
  const beamMat = new THREE.MeshBasicMaterial({
    color: "#fff5cc",
    transparent: true,
    opacity: 0.18,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const sunbeam = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 1.4, 3.8, 16, 1, true), beamMat);
  sunbeam.rotation.x = 0.65;
  sunbeam.rotation.z = -0.35;
  sunbeam.position.set(1.2, 1.6, -1.0);
  shop.add(sunbeam);

  // 2. Wall Metal Shelving Unit with 8 Colorful Paint Cans
  const shelfMat = makeMaterial("shelf_metal", rep(beam("shelf_steel", "#334155"), 1, 1));
  const shelfGroup = new THREE.Group();
  for (const sy of [1.6, 2.1, 2.6]) {
    const plank = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.03, 0.35), shelfMat);
    plank.position.set(-1.8, sy, -2.3);
    shelfGroup.add(plank);
  }
  for (const sx of [-2.65, -0.95]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.04, 1.8, 0.35), shelfMat);
    post.position.set(sx, 2.0, -2.3);
    shelfGroup.add(post);
  }

  // Colorful cans on the wall shelves
  const canColors = ["#0d9488", "#db2777", "#2563eb", "#ea580c", "#16a34a", "#9333ea", "#ca8a04", "#e11d48"];
  for (let row = 0; row < 2; row++) {
    const cy = row === 0 ? 2.12 : 2.62;
    for (let c = 0; c < 4; c++) {
      const idx = row * 4 + c;
      const can = buildDetailedPaintCan(canColors[idx], 0.08, 0.18);
      can.position.set(-2.4 + c * 0.4, cy, -2.3);
      shelfGroup.add(can);
    }
  }
  shop.add(shelfGroup);

  // 3. Wooden Craftsman Workbench
  const woodMat = makeMaterial("oak_workbench", rep(planks("oak_planks", "#b45309"), 2, 1));
  const benchGroup = new THREE.Group();
  // Tabletop
  const top = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.08, 1.1), woodMat);
  top.position.set(0, 0.88, 0);
  top.castShadow = true;
  top.receiveShadow = true;
  benchGroup.add(top);

  // Steel legs & stretcher rails
  const legMat = makeMaterial("table_steel_legs", rep(beam("legs_black", "#1e293b"), 1, 1));
  for (const [lx, lz] of [[-1.1, -0.45], [1.1, -0.45], [-1.1, 0.45], [1.1, 0.45]]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.88, 0.08), legMat);
    leg.position.set(lx, 0.44, lz);
    leg.castShadow = true;
    benchGroup.add(leg);
  }

  // Green cutting mat on tabletop
  const matMat = new THREE.MeshLambertMaterial({ color: "#047857" });
  const mat = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.6), matMat);
  mat.rotation.x = -Math.PI / 2;
  mat.position.set(0, 0.922, 0.05);
  mat.receiveShadow = true;
  benchGroup.add(mat);

  // Digital Scale placed on cutting mat
  const scale = buildDigitalScale();
  scale.position.set(0, 0.925, 0.05);
  benchGroup.add(scale);

  // Clean stylized "WHITE" Paint Can on the scale
  const whiteCan = buildDetailedPaintCan("#f8fafc", 0.11, 0.24);
  whiteCan.position.set(0, 0.965, 0.03);
  benchGroup.add(whiteCan);

  // Red mixing spatula tool
  const spatula = new THREE.Group();
  const handleMesh = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.01, 0.18), new THREE.MeshLambertMaterial({ color: 0x1e293b }));
  const paddleMesh = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.005, 0.06), new THREE.MeshLambertMaterial({ color: 0xdc2626 }));
  paddleMesh.position.z = 0.11;
  spatula.add(handleMesh, paddleMesh);
  spatula.position.set(0.32, 0.93, 0.08);
  spatula.rotation.y = 0.4;
  benchGroup.add(spatula);

  shop.add(benchGroup);

  shop.position.set(x, y, z);
  root.add(shop);
  return shop;
}

/**
 * Builds the multi-tier Prison Cafeteria "POD C" set.
 */
export function buildCafeteriaPodC(root: THREE.Object3D, x = 0, y = 0, z = 0): THREE.Group {
  const pod = new THREE.Group();

  // Floor
  const floorMat = makeMaterial("podc_floor", rep(tiles(), 8, 8));
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  pod.add(floor);

  // Back Cell Block Wall
  const wallMat = makeMaterial("podc_wall", rep(brick("podc_brick", "#64748b"), 6, 4));
  const backWall = new THREE.Mesh(new THREE.PlaneGeometry(16, 7.5), wallMat);
  backWall.position.set(0, 3.75, -5.5);
  backWall.receiveShadow = true;
  pod.add(backWall);

  // Second tier walkway catwalk
  const walkMat = makeMaterial("catwalk_steel", rep(beam("catwalk_metal", "#334155"), 4, 1));
  const catwalk = new THREE.Mesh(new THREE.BoxGeometry(16, 0.15, 1.8), walkMat);
  catwalk.position.set(0, 3.6, -4.6);
  catwalk.receiveShadow = true;
  pod.add(catwalk);

  // Handrail on catwalk
  for (let rx = -7.5; rx <= 7.5; rx += 1.5) {
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.1, 8), walkMat);
    post.position.set(rx, 4.2, -3.75);
    pod.add(post);
  }
  const topRail = new THREE.Mesh(new THREE.BoxGeometry(16, 0.04, 0.04), walkMat);
  topRail.position.set(0, 4.75, -3.75);
  pod.add(topRail);

  // Open Cell Door C-4 glowing pink in the background
  const doorC4 = new THREE.Group();
  const frameMat = makeMaterial("c4_frame", rep(beam("c4_steel", "#1e293b"), 1, 1));
  const frameL = new THREE.Mesh(new THREE.BoxGeometry(0.1, 2.4, 0.15), frameMat);
  frameL.position.set(-0.7, 1.2, 0);
  const frameR = new THREE.Mesh(new THREE.BoxGeometry(0.1, 2.4, 0.15), frameMat);
  frameR.position.set(0.7, 1.2, 0);
  const frameT = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.1, 0.15), frameMat);
  frameT.position.set(0, 2.35, 0);
  doorC4.add(frameL, frameR, frameT);

  const pinkGlow = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 2.3), new THREE.MeshBasicMaterial({ color: "#f472b6" }));
  pinkGlow.position.set(0, 1.15, -0.05);
  doorC4.add(pinkGlow);
  doorC4.position.set(2.4, 0, -5.4);
  pod.add(doorC4);

  // Blue Molded Cafeteria Picnic Table (aligned along Z axis)
  const tableGroup = new THREE.Group();
  const bluePlasticMat = new THREE.MeshLambertMaterial({ color: 0x2563eb });
  const tableMetalMat = new THREE.MeshLambertMaterial({ color: 0x1e293b });

  const ttop = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.06, 2.2), bluePlasticMat);
  ttop.position.set(0, 0.82, 0);
  ttop.castShadow = true;
  ttop.receiveShadow = true;
  tableGroup.add(ttop);

  // Attached left & right benches
  for (const bx of [-0.68, 0.68]) {
    const bench = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.05, 2.2), bluePlasticMat);
    bench.position.set(bx, 0.48, 0);
    bench.castShadow = true;
    bench.receiveShadow = true;
    tableGroup.add(bench);
  }

  // Steel tubular frame under table and benches
  const frameGeo = new THREE.BoxGeometry(1.5, 0.8, 0.06);
  for (const fz of [-0.8, 0.8]) {
    const tf = new THREE.Mesh(frameGeo, tableMetalMat);
    tf.position.set(0, 0.4, fz);
    tf.castShadow = true;
    tableGroup.add(tf);
  }

  tableGroup.position.set(0, 0, 0);
  pod.add(tableGroup);

  pod.position.set(x, y, z);
  root.add(pod);
  return pod;
}

/**
 * Creates the radial floor impact crater decal.
 */
export function buildImpactCrater(radius = 1.1): THREE.Group {
  const crater = new THREE.Group();
  const craterMat = new THREE.MeshBasicMaterial({
    color: "#f472b6",
    transparent: true,
    opacity: 0.6,
    depthWrite: false,
  });
  const mesh = new THREE.Mesh(new THREE.CircleGeometry(radius, 24), craterMat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = 0.015;
  crater.add(mesh);
  return crater;
}

/**
 * Builds the pink and white striped knitted scarf with yarn ball.
 */
export function buildKnittingScarf(): THREE.Group {
  const group = new THREE.Group();
  const scarfMat = new THREE.MeshLambertMaterial({ color: "#f472b6" });

  const scarfGeo = new THREE.PlaneGeometry(0.32, 1.2, 4, 8);
  const scarf = new THREE.Mesh(scarfGeo, scarfMat);
  scarf.position.set(0, 0.6, 0.25);
  group.add(scarf);

  const yarnMat = new THREE.MeshLambertMaterial({ color: 0xec4899 });
  const yarn = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), yarnMat);
  yarn.position.set(0.35, 0.08, 0.5);
  group.add(yarn);

  return group;
}
