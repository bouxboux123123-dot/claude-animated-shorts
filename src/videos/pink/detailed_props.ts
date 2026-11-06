import * as THREE from "three";
import { makeMaterial, planks, beam, brick, tiles, ctex, rep } from "../../engine";

/**
 * Creates a photorealistic styled paint can with metallic silver rims,
 * wrapped paper label with branded header banner, printed typography, and wire bail handle.
 */
export function buildDetailedPaintCan(
  label = "WHITE",
  bannerCol = "#0284c7",
  canRadius = 0.12,
  canHeight = 0.26
): THREE.Group {
  const can = new THREE.Group();

  // 1. Procedural 512x512 Canvas2D Paint Can Label
  const labelTex = ctex(`paint_can_label_${label}_${bannerCol}`, 512, 512, (g) => {
    // Metallic tin background
    g.fillStyle = "#cbd5e1";
    g.fillRect(0, 0, 512, 512);

    // Fine brushed metal horizontal scratches
    g.strokeStyle = "rgba(255,255,255,0.4)";
    g.lineWidth = 1;
    for (let i = 0; i < 40; i++) {
      const y = (i * 13) % 512;
      g.beginPath();
      g.moveTo(0, y);
      g.lineTo(512, y);
      g.stroke();
    }

    // Paper label band (middle 70% of can)
    g.fillStyle = "#ffffff";
    g.fillRect(0, 80, 512, 350);

    // Brand color top banner
    g.fillStyle = bannerCol;
    g.fillRect(0, 80, 512, 95);

    // Thin accent stripe
    g.fillStyle = "#1e293b";
    g.fillRect(0, 175, 512, 6);

    // Main label title
    g.fillStyle = "#0f172a";
    g.font = "bold 64px sans-serif";
    g.textAlign = "center";
    g.fillText(label, 256, 280);

    // Subtext
    g.fillStyle = "#64748b";
    g.font = "bold 20px sans-serif";
    g.fillText("PREMIUM QUALITY", 256, 325);
    g.font = "16px sans-serif";
    g.fillText("INTERIOR / EXTERIOR • 1 GALLON", 256, 360);

    // Barcode & specs box on side
    g.fillStyle = "#e2e8f0";
    g.fillRect(40, 240, 60, 140);
    g.fillStyle = "#0f172a";
    for (let x = 45; x < 95; x += 4) {
      g.fillRect(x, 250, (x % 3 === 0 ? 3 : 1), 100);
    }
  });

  const canMat = makeMaterial(`paint_can_mat_${label}`, labelTex);
  const silverMat = makeMaterial("can_silver_rim", rep(beam("can_rim_shine", "#94a3b8"), 1, 1));

  // Can Cylinder Body
  const cyl = new THREE.Mesh(new THREE.CylinderGeometry(canRadius, canRadius, canHeight, 24), canMat);
  cyl.position.y = canHeight / 2;
  cyl.castShadow = true;
  cyl.receiveShadow = true;
  can.add(cyl);

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
 * Creates a digital laboratory/kitchen scale with illuminated LCD readout.
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

  // Digital LCD display screen
  const lcdTex = ctex("scale_lcd_tex", 128, 64, (g) => {
    g.fillStyle = "#042f2e";
    g.fillRect(0, 0, 128, 64);
    g.fillStyle = "#2dd4bf";
    g.font = "bold 26px monospace";
    g.textAlign = "right";
    g.fillText("1.000", 100, 42);
    g.font = "bold 14px monospace";
    g.fillText("GAL", 124, 42);
  });
  const lcdMat = new THREE.MeshBasicMaterial({ map: lcdTex });
  const lcd = new THREE.Mesh(new THREE.PlaneGeometry(0.14, 0.045), lcdMat);
  lcd.rotation.x = -Math.PI / 2 + 0.1;
  lcd.position.set(0, 0.036, 0.1);
  scale.add(lcd);

  return scale;
}

/**
 * Creates a glass measuring beaker with red liquid and measurement tick marks.
 */
export function buildGraduatedBeaker(): THREE.Group {
  const beaker = new THREE.Group();

  const glassTex = ctex("beaker_glass_tex", 256, 256, (g) => {
    g.clearRect(0, 0, 256, 256);
    g.fillStyle = "rgba(255,255,255,0.15)";
    g.fillRect(0, 0, 256, 256);

    // Graduation lines
    g.strokeStyle = "#ffffff";
    g.lineWidth = 3;
    for (let i = 1; i <= 6; i++) {
      const y = 256 - i * 36;
      g.beginPath();
      g.moveTo(60, y);
      g.lineTo(120, y);
      g.stroke();
      g.fillStyle = "#ffffff";
      g.font = "bold 16px sans-serif";
      g.fillText(`${i * 100}ml`, 128, y + 6);
    }
    // Red volume label
    g.fillStyle = "#dc2626";
    g.fillRect(50, 40, 150, 30);
    g.fillStyle = "#ffffff";
    g.font = "bold 16px sans-serif";
    g.textAlign = "center";
    g.fillText("1 PINT RED", 125, 62);
  });

  const glassMat = new THREE.MeshLambertMaterial({
    map: glassTex,
    transparent: true,
    opacity: 0.85,
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
 * Builds the complete authentic scientific Paint Shop Workshop set.
 */
export function buildPaintShopWorkshop(root: THREE.Object3D, x = 0, y = 0, z = 0): THREE.Group {
  const shop = new THREE.Group();

  // 1. Back Wall & Sign
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

  // "PAINT SHOP" Sign
  const signTex = ctex("paint_shop_sign", 512, 128, (g) => {
    g.fillStyle = "#ffffff";
    g.fillRect(0, 0, 512, 128);
    g.strokeStyle = "#0f172a";
    g.lineWidth = 10;
    g.strokeRect(10, 10, 492, 108);
    g.fillStyle = "#0f172a";
    g.font = "bold 60px sans-serif";
    g.textAlign = "center";
    g.fillText("PAINT SHOP", 256, 85);
  });
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.4), new THREE.MeshBasicMaterial({ map: signTex }));
  sign.position.set(-1.8, 3.2, -2.48);
  shop.add(sign);

  // Wall Pinned Work Order Memo
  const memoTex = ctex("paint_shop_memo", 256, 320, (g) => {
    g.fillStyle = "#ffffff";
    g.fillRect(0, 0, 256, 320);
    g.fillStyle = "#ec4899"; // Pink header
    g.fillRect(0, 0, 256, 60);
    g.fillStyle = "#ffffff";
    g.font = "bold 24px sans-serif";
    g.textAlign = "center";
    g.fillText("ORDER #P-618", 128, 42);
    g.fillStyle = "#334155";
    for (let y = 90; y < 290; y += 22) {
      g.fillRect(30, y, 196, 6);
    }
  });
  const memo = new THREE.Mesh(new THREE.PlaneGeometry(0.35, 0.45), new THREE.MeshBasicMaterial({ map: memoTex }));
  memo.position.set(-0.6, 2.9, -2.48);
  shop.add(memo);

  // Workshop Window with Sunbeams
  const winTex = ctex("paint_shop_win_grid", 256, 256, (g) => {
    g.fillStyle = "#ffffff";
    g.fillRect(0, 0, 256, 256);
    g.fillStyle = "#0f172a";
    // 6 glass panes
    g.lineWidth = 12;
    g.strokeRect(6, 6, 244, 244);
    g.beginPath();
    g.moveTo(128, 0); g.lineTo(128, 256);
    g.moveTo(0, 85); g.lineTo(256, 85);
    g.moveTo(0, 170); g.lineTo(256, 170);
    g.stroke();
  });
  const winFrame = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 2.0), new THREE.MeshBasicMaterial({ map: winTex }));
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

  // 2. Wall Metal Shelving Unit with 8 Paint Cans
  const shelfMat = makeMaterial("shelf_metal", rep(beam("shelf_steel", "#334155"), 1, 1));
  const shelfGroup = new THREE.Group();
  for (const sy of [1.6, 2.1, 2.6]) {
    const plank = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.03, 0.35), shelfMat);
    plank.position.set(-1.8, sy, -2.3);
    shelfGroup.add(plank);
  }
  // Upright shelf posts
  for (const sx of [-2.65, -0.95]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.04, 1.8, 0.35), shelfMat);
    post.position.set(sx, 2.0, -2.3);
    shelfGroup.add(post);
  }
  // Colorful paint cans on the wall shelves
  const canColors = ["#0d9488", "#db2777", "#2563eb", "#ea580c", "#16a34a", "#9333ea", "#ca8a04", "#e11d48"];
  const canLabels = ["TEAL", "PINK", "BLUE", "ORANGE", "GREEN", "PURPLE", "YELLOW", "RED"];
  for (let row = 0; row < 2; row++) {
    const cy = row === 0 ? 2.12 : 2.62;
    for (let c = 0; c < 4; c++) {
      const idx = row * 4 + c;
      const can = buildDetailedPaintCan(canLabels[idx], canColors[idx], 0.08, 0.18);
      can.position.set(-2.4 + c * 0.4, cy, -2.3);
      shelfGroup.add(can);
    }
  }
  shop.add(shelfGroup);

  // 3. Heavy Wooden Craftsman Workbench
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
  // Lower wooden shelf
  const lowerShelf = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.03, 0.8), woodMat);
  lowerShelf.position.set(0, 0.22, 0);
  benchGroup.add(lowerShelf);

  // Paint cans on lower shelf
  const botCan1 = buildDetailedPaintCan("BLUE", "#1d4ed8", 0.09, 0.20);
  botCan1.position.set(0.6, 0.23, 0);
  const botCan2 = buildDetailedPaintCan("YELLOW", "#eab308", 0.09, 0.20);
  botCan2.position.set(0.85, 0.23, 0);
  benchGroup.add(botCan1, botCan2);

  // Green rubber cutting mat on tabletop
  const matTex = ctex("green_cutting_mat", 256, 256, (g) => {
    g.fillStyle = "#047857";
    g.fillRect(0, 0, 256, 256);
    g.strokeStyle = "rgba(255,255,255,0.4)";
    g.lineWidth = 1;
    for (let i = 0; i < 256; i += 24) {
      g.beginPath();
      g.moveTo(i, 0); g.lineTo(i, 256);
      g.moveTo(0, i); g.lineTo(256, i);
      g.stroke();
    }
  });
  const mat = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.6), new THREE.MeshLambertMaterial({ map: matTex }));
  mat.rotation.x = -Math.PI / 2;
  mat.position.set(0, 0.922, 0.05);
  mat.receiveShadow = true;
  benchGroup.add(mat);

  // Digital Scale placed on cutting mat
  const scale = buildDigitalScale();
  scale.position.set(0, 0.925, 0.05);
  benchGroup.add(scale);

  // The 1-Gallon "WHITE" Paint Can on the scale
  const whiteCan = buildDetailedPaintCan("WHITE", "#0284c7", 0.11, 0.24);
  whiteCan.position.set(0, 0.965, 0.03);
  benchGroup.add(whiteCan);

  // Red mixing spatula tool on the cutting mat
  const spatula = new THREE.Group();
  const handleMesh = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.01, 0.18), new THREE.MeshLambertMaterial({ color: 0x1e293b }));
  const paddleMesh = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.005, 0.06), new THREE.MeshLambertMaterial({ color: 0xdc2626 }));
  paddleMesh.position.z = 0.11;
  spatula.add(handleMesh, paddleMesh);
  spatula.position.set(0.32, 0.93, 0.08);
  spatula.rotation.y = 0.4;
  benchGroup.add(spatula);

  shop.add(benchGroup);

  // Overhead Fluorescent Ceiling Light Fixture
  const ceilFix = new THREE.Group();
  const fixBody = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.08, 0.35), new THREE.MeshLambertMaterial({ color: 0x334155 }));
  const fixTube = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.4, 8), new THREE.MeshBasicMaterial({ color: 0xffffff }));
  fixTube.rotation.z = Math.PI / 2;
  fixTube.position.y = -0.04;
  ceilFix.add(fixBody, fixTube);
  ceilFix.position.set(0, 3.8, 0);
  shop.add(ceilFix);

  shop.position.set(x, y, z);
  root.add(shop);
  return shop;
}

/**
 * Builds the authentic multi-tier Prison Cafeteria "POD C" set.
 */
export function buildCafeteriaPodC(root: THREE.Object3D, x = 0, y = 0, z = 0): THREE.Group {
  const pod = new THREE.Group();

  // Floor (concrete with gray tone)
  const floorMat = makeMaterial("podc_floor", rep(tiles(), 8, 8));
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  pod.add(floor);

  // Back Cell Block Wall (two stories high)
  const wallMat = makeMaterial("podc_wall", rep(brick("podc_brick", "#64748b"), 6, 4));
  const backWall = new THREE.Mesh(new THREE.PlaneGeometry(16, 7.5), wallMat);
  backWall.position.set(0, 3.75, -5.5);
  backWall.receiveShadow = true;
  pod.add(backWall);

  // "POD C" Sign high on wall
  const podSignTex = ctex("pod_c_sign", 512, 128, (g) => {
    g.fillStyle = "#1e293b";
    g.fillRect(0, 0, 512, 128);
    g.strokeStyle = "#475569";
    g.lineWidth = 8;
    g.strokeRect(8, 8, 496, 112);
    g.fillStyle = "#f8fafc";
    g.font = "bold 68px sans-serif";
    g.textAlign = "center";
    g.fillText("POD C", 256, 88);
  });
  const podSign = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.6), new THREE.MeshBasicMaterial({ map: podSignTex }));
  podSign.position.set(0, 6.2, -5.48);
  pod.add(podSign);

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

  // Open door panel swung open
  const doorPanel = new THREE.Mesh(new THREE.BoxGeometry(1.3, 2.3, 0.05), frameMat);
  doorPanel.position.set(-1.25, 1.15, 0.4);
  doorPanel.rotation.y = 1.2;
  doorC4.add(doorPanel);

  // Glowing pink interior doorway
  const pinkGlow = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 2.3), new THREE.MeshBasicMaterial({ color: "#f472b6" }));
  pinkGlow.position.set(0, 1.15, -0.05);
  doorC4.add(pinkGlow);

  doorC4.position.set(2.4, 0, -5.4);
  pod.add(doorC4);

  // 4. Blue Molded Cafeteria Picnic Table (running along Z axis)
  const tableGroup = new THREE.Group();
  const bluePlasticMat = new THREE.MeshLambertMaterial({ color: 0x2563eb });
  const tableMetalMat = new THREE.MeshLambertMaterial({ color: 0x1e293b });

  // Tabletop (width 0.9 along X, length 2.2 along Z)
  const ttop = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.06, 2.2), bluePlasticMat);
  ttop.position.set(0, 0.82, 0);
  ttop.castShadow = true;
  ttop.receiveShadow = true;
  tableGroup.add(ttop);

  // Attached left & right benches (along Z axis)
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

  // Food trays, drinks, and lunch on table
  const trayMat = new THREE.MeshLambertMaterial({ color: 0xf8fafc });
  for (const [tx, tz] of [[-0.15, -0.5], [0.15, 0.5]]) {
    const tray = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.02, 0.42), trayMat);
    tray.position.set(tx, 0.86, tz);
    tableGroup.add(tray);

    // Burger / sandwich
    const bun = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.04, 12), new THREE.MeshLambertMaterial({ color: 0xd97706 }));
    bun.position.set(tx, 0.89, tz - 0.08);
    tableGroup.add(bun);

    // Beverage can
    const can = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.09, 12), new THREE.MeshLambertMaterial({ color: 0xef4444 }));
    can.position.set(tx, 0.91, tz + 0.12);
    tableGroup.add(can);
  }

  tableGroup.position.set(0, 0, 0);
  pod.add(tableGroup);

  // Overhead Industrial Hanging Lamps
  for (const lx of [-3, 0, 3]) {
    const lamp = new THREE.Group();
    const cable = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, 2.2, 6), tableMetalMat);
    cable.position.y = 6.0;
    const shade = new THREE.Mesh(new THREE.ConeGeometry(0.25, 0.2, 16, 1, true), new THREE.MeshLambertMaterial({ color: 0x475569 }));
    shade.position.y = 4.9;
    shade.rotation.x = Math.PI;
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    bulb.position.y = 4.88;
    lamp.add(cable, shade, bulb);
    lamp.position.set(lx, 0, 0);
    pod.add(lamp);
  }

  pod.position.set(x, y, z);
  root.add(pod);
  return pod;
}

/**
 * Creates the radial floor impact crater decal with broken concrete fissures and pink under-glow.
 */
export function buildImpactCrater(radius = 1.1): THREE.Group {
  const crater = new THREE.Group();

  const craterTex = ctex(`crater_tex_${radius}`, 512, 512, (g) => {
    g.clearRect(0, 0, 512, 512);

    // Radial cracks
    g.strokeStyle = "#1e1b4b";
    g.lineWidth = 5;
    g.lineCap = "round";

    const numCracks = 16;
    for (let i = 0; i < numCracks; i++) {
      const a = (i / numCracks) * Math.PI * 2;
      let x = 256;
      let y = 256;
      g.beginPath();
      g.moveTo(x, y);
      const len = 120 + ((i * 37) % 110);
      for (let s = 0; s < 5; s++) {
        const segLen = len / 5;
        const jA = a + ((Math.sin(i * 5 + s) * 0.35));
        x += Math.cos(jA) * segLen;
        y += Math.sin(jA) * segLen;
        g.lineTo(x, y);
      }
      g.stroke();
    }

    // Secondary hairline fractures
    g.lineWidth = 2;
    g.strokeStyle = "#475569";
    for (let i = 0; i < 24; i++) {
      const a = (i / 24) * Math.PI * 2 + 0.1;
      g.beginPath();
      g.moveTo(256 + Math.cos(a) * 60, 256 + Math.sin(a) * 60);
      g.lineTo(256 + Math.cos(a + 0.2) * 160, 256 + Math.sin(a + 0.2) * 160);
      g.stroke();
    }

    // Central pink energy glow core
    const radG = g.createRadialGradient(256, 256, 10, 256, 256, 180);
    radG.addColorStop(0, "rgba(244,114,182,0.85)");
    radG.addColorStop(0.3, "rgba(236,72,153,0.4)");
    radG.addColorStop(1, "rgba(236,72,153,0)");
    g.fillStyle = radG;
    g.beginPath();
    g.arc(256, 256, 180, 0, Math.PI * 2);
    g.fill();
  });

  const mat = new THREE.MeshBasicMaterial({
    map: craterTex,
    transparent: true,
    depthWrite: false,
  });

  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(radius * 2, radius * 2), mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = 0.015; // Just above floor
  crater.add(mesh);

  return crater;
}

/**
 * Builds the authentic pink and white striped knitted scarf with yarn ball and needles.
 */
export function buildKnittingScarf(): THREE.Group {
  const group = new THREE.Group();

  const knitTex = ctex("knitted_scarf_ribs", 256, 512, (g) => {
    // Alternating pink and white stripes with loop ribs
    const stripeH = 32;
    for (let i = 0; i < 16; i++) {
      g.fillStyle = i % 2 === 0 ? "#f472b6" : "#ffffff";
      g.fillRect(0, i * stripeH, 256, stripeH);

      // Knit loop stitches
      g.strokeStyle = i % 2 === 0 ? "#db2777" : "#cbd5e1";
      g.lineWidth = 2;
      for (let x = 8; x < 256; x += 16) {
        g.beginPath();
        g.arc(x, i * stripeH + 16, 6, 0, Math.PI);
        g.stroke();
      }
    }
  });

  const scarfMat = new THREE.MeshLambertMaterial({
    map: knitTex,
    side: THREE.DoubleSide,
  });

  // Hanging scarf section flowing from hands down to bench and curling on floor
  const scarfGeo = new THREE.PlaneGeometry(0.32, 1.4, 8, 16);
  // Curve scarf forward onto floor
  const pos = scarfGeo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    if (y < -0.4) {
      // Curve forward on floor
      pos.setZ(i, (pos.getZ(i) || 0) + (-0.4 - y) * 0.8);
      pos.setY(i, -0.4);
    }
  }
  scarfGeo.computeVertexNormals();

  const scarf = new THREE.Mesh(scarfGeo, scarfMat);
  scarf.position.set(0, 0.7, 0.25);
  group.add(scarf);

  // Pink ball of yarn on the floor
  const yarnMat = new THREE.MeshLambertMaterial({ color: 0xec4899 });
  const yarn = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 16), yarnMat);
  yarn.position.set(0.38, 0.08, 0.55);
  yarn.castShadow = true;
  group.add(yarn);

  // Yarn thread connecting ball to scarf
  const threadGeo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0.1, 0.1, 0.4),
    new THREE.Vector3(0.24, 0.04, 0.48),
    new THREE.Vector3(0.38, 0.08, 0.55),
  ]);
  const thread = new THREE.Line(threadGeo, new THREE.LineBasicMaterial({ color: 0xec4899, linewidth: 3 }));
  group.add(thread);

  return group;
}
