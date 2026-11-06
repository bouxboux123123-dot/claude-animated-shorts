// 3D environment architecture for "How Money Is Printed"
// Rich, colorful industrial mint facility with Black Ink silhouette lines (#030303).
// All props are placed with optimal horizontal margins for 9:16 vertical reels.
import * as THREE from "three";
import { twoTone } from "./shade";

export const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);

export class MoneySceneBuilder {
  root: THREE.Group;

  officeGroup: THREE.Group;
  pressGroup: THREE.Group;
  washGroup: THREE.Group;
  clothGroup: THREE.Group;
  counterfeitGroup: THREE.Group;
  scannerGroup: THREE.Group;
  shredderGroup: THREE.Group;

  rollerTop!: THREE.Mesh;
  rollerBot!: THREE.Mesh;
  scannerLaser!: THREE.Mesh;
  shredderBeacon!: THREE.Mesh;
  washWater!: THREE.Mesh;

  fgGroup: THREE.Group;
  fgPillar!: THREE.Mesh;
  fgFlasks!: THREE.Group;
  fgMonitor!: THREE.Group;
  fgStanchion!: THREE.Group;

  constructor() {
    this.root = new THREE.Group();
    this.officeGroup = new THREE.Group();
    this.pressGroup = new THREE.Group();
    this.washGroup = new THREE.Group();
    this.clothGroup = new THREE.Group();
    this.counterfeitGroup = new THREE.Group();
    this.scannerGroup = new THREE.Group();
    this.shredderGroup = new THREE.Group();
    this.fgGroup = new THREE.Group();

    this.buildBaseRoom();
    this.buildOfficeStage();
    this.buildIntaglioPress();
    this.buildWashStage();
    this.buildClothStage();
    this.buildCounterfeitStage();
    this.buildScannerStage();
    this.buildShredderStage();
    this.buildForegroundProps();

    this.root.add(this.officeGroup);
    this.root.add(this.pressGroup);
    this.root.add(this.washGroup);
    this.root.add(this.clothGroup);
    this.root.add(this.counterfeitGroup);
    this.root.add(this.scannerGroup);
    this.root.add(this.shredderGroup);
    this.root.add(this.fgGroup);
  }

  private buildBaseRoom() {
    // 1. Concrete factory floor with warm grey two-tone tone
    const floorGeo = new THREE.PlaneGeometry(24, 24);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#7d8b99" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = 0;
    this.root.add(floor);

    // Hazard yellow safety stripes on floor
    for (let z = -6; z <= 6; z += 1.6) {
      const stripeGeo = new THREE.BoxGeometry(0.25, 0.015, 0.9);
      const stripeMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f59e0b" }));
      const s1 = new THREE.Mesh(stripeGeo, stripeMat);
      s1.position.set(-2.5, 0.008, z);
      this.root.add(s1);
      const s2 = new THREE.Mesh(stripeGeo, stripeMat);
      s2.position.set(2.5, 0.008, z);
      this.root.add(s2);
    }

    // 2. Mint back wall (mint/sage green factory wall)
    const wallGeo = new THREE.PlaneGeometry(24, 12);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#3d5a52" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 6, -5.0);
    this.root.add(wall);

    // Architectural cream trim line
    const trimGeo = new THREE.BoxGeometry(24, 0.3, 0.15);
    const trimMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f1f5f9" }));
    const trim = new THREE.Mesh(trimGeo, trimMat);
    trim.position.set(0, 4.2, -4.92);
    this.root.add(trim);

    // High industrial windows (light panels)
    for (let wx = -7.5; wx <= 7.5; wx += 5.0) {
      const winGeo = new THREE.PlaneGeometry(2.4, 3.2);
      const winMat = new THREE.MeshBasicMaterial({ color: "#e2e8f0" });
      const win = new THREE.Mesh(winGeo, winMat);
      win.position.set(wx, 7.5, -4.95);
      this.root.add(win);
      const mullGeo = new THREE.BoxGeometry(2.4, 0.1, 0.05);
      const mullMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
      const m1 = new THREE.Mesh(mullGeo, mullMat);
      m1.position.set(wx, 7.5, -4.9);
      this.root.add(m1);
    }

    // 3. Side structural steel columns
    const colMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    for (const px of [-3.8, 3.8]) {
      for (const pz of [-4.0, 0, 4.0]) {
        const colGeo = new THREE.BoxGeometry(0.55, 12, 0.55);
        const col = new THREE.Mesh(colGeo, colMat);
        col.position.set(px, 6, pz);
        this.root.add(col);
      }
    }
  }

  private buildOfficeStage() {
    // Desk table for Shot 1
    const deskMat = twoTone(new THREE.MeshLambertMaterial({ color: "#b45309" }));
    const topGeo = new THREE.BoxGeometry(1.6, 0.08, 1.0);
    const top = new THREE.Mesh(topGeo, deskMat);
    top.position.set(-0.35, 0.76, 0.2);
    this.officeGroup.add(top);

    // Desk legs
    const legGeo = new THREE.BoxGeometry(0.08, 0.76, 0.08);
    const legMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1f2937" }));
    for (const dx of [-0.7, 0.7]) {
      for (const dz of [-0.4, 0.4]) {
        const leg = new THREE.Mesh(legGeo, legMat);
        leg.position.set(-0.35 + dx, 0.38, 0.2 + dz);
        this.officeGroup.add(leg);
      }
    }

    // Desktop inkjet printer
    const printerMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f8fafc" }));
    const printerGeo = new THREE.BoxGeometry(0.65, 0.32, 0.5);
    const printer = new THREE.Mesh(printerGeo, printerMat);
    printer.position.set(-0.38, 0.96, 0.2);
    this.officeGroup.add(printer);

    // Paper tray & jammed cheap paper sheet
    const paperGeo = new THREE.BoxGeometry(0.35, 0.02, 0.4);
    const paperMat = new THREE.MeshBasicMaterial({ color: "#ffffff" });
    const paper = new THREE.Mesh(paperGeo, paperMat);
    paper.position.set(-0.38, 1.16, 0.3);
    paper.rotation.x = 0.45;
    this.officeGroup.add(paper);
  }

  private buildIntaglioPress() {
    // 20-ton industrial Intaglio press (placed at z = -2.2, behind character)
    const frameMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    const steelMat = twoTone(new THREE.MeshLambertMaterial({ color: "#94a3b8" }));
    const brassMat = twoTone(new THREE.MeshLambertMaterial({ color: "#d97706" }));

    // Side upright steel frames
    for (const sx of [-1.8, 1.8]) {
      const frameGeo = new THREE.BoxGeometry(0.45, 3.6, 0.9);
      const f = new THREE.Mesh(frameGeo, frameMat);
      f.position.set(sx, 1.8, -2.2);
      this.pressGroup.add(f);
    }

    // Heavy crossbeam
    const beamGeo = new THREE.BoxGeometry(4.0, 0.6, 0.9);
    const beam = new THREE.Mesh(beamGeo, frameMat);
    beam.position.set(0, 3.3, -2.2);
    this.pressGroup.add(beam);

    // Hydraulic cylinders on top crossbeam
    for (const hx of [-0.9, 0.9]) {
      const pGeo = new THREE.CylinderGeometry(0.22, 0.22, 0.7, 24);
      const p = new THREE.Mesh(pGeo, steelMat);
      p.position.set(hx, 3.8, -2.2);
      this.pressGroup.add(p);
    }

    // Two massive steel Intaglio printing rollers
    const rollerGeo = new THREE.CylinderGeometry(0.46, 0.46, 3.1, 32);
    this.rollerTop = new THREE.Mesh(rollerGeo, steelMat);
    this.rollerTop.rotation.z = Math.PI / 2;
    this.rollerTop.position.set(0, 2.2, -2.2);
    this.pressGroup.add(this.rollerTop);

    this.rollerBot = new THREE.Mesh(rollerGeo, steelMat);
    this.rollerBot.rotation.z = Math.PI / 2;
    this.rollerBot.position.set(0, 1.25, -2.2);
    this.pressGroup.add(this.rollerBot);

    // Stamped intaglio sheet feeding through rollers
    const sheetGeo = new THREE.PlaneGeometry(2.6, 1.4);
    const sheetMat = twoTone(new THREE.MeshLambertMaterial({ color: "#dcfce7" }));
    const sheet = new THREE.Mesh(sheetGeo, sheetMat);
    sheet.rotation.x = -Math.PI / 2;
    sheet.position.set(0, 1.72, -1.8);
    this.pressGroup.add(sheet);

    // Pressure Gauge Dial ("20 TONS")
    const dialGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.1, 32);
    const dial = new THREE.Mesh(dialGeo, brassMat);
    dial.rotation.x = Math.PI / 2;
    dial.position.set(1.8, 2.7, -1.7);
    this.pressGroup.add(dial);

    const faceGeo = new THREE.CircleGeometry(0.3, 32);
    const faceMat = new THREE.MeshBasicMaterial({ color: "#ffffff" });
    const face = new THREE.Mesh(faceGeo, faceMat);
    face.position.set(1.8, 2.7, -1.64);
    this.pressGroup.add(face);

    const needleGeo = new THREE.BoxGeometry(0.04, 0.24, 0.02);
    const needleMat = new THREE.MeshBasicMaterial({ color: "#ef4444" });
    const needle = new THREE.Mesh(needleGeo, needleMat);
    needle.position.set(1.8, 2.74, -1.62);
    needle.rotation.z = 0.5;
    this.pressGroup.add(needle);
  }

  private buildWashStage() {
    // Industrial wash basin for Shot 3 (centered at x = -0.42)
    const tubMat = twoTone(new THREE.MeshLambertMaterial({ color: "#475569" }));
    const tubGeo = new THREE.CylinderGeometry(0.65, 0.55, 0.7, 32);
    const tub = new THREE.Mesh(tubGeo, tubMat);
    tub.position.set(-0.42, 0.35, -0.35);
    this.washGroup.add(tub);

    // Water surface
    const waterGeo = new THREE.CircleGeometry(0.6, 32);
    const waterMat = new THREE.MeshBasicMaterial({ color: "#38bdf8", transparent: true, opacity: 0.85 });
    this.washWater = new THREE.Mesh(waterGeo, waterMat);
    this.washWater.rotation.x = -Math.PI / 2;
    this.washWater.position.set(-0.42, 0.68, -0.35);
    this.washGroup.add(this.washWater);

    // Dissolving paper mush / flakes in the water
    for (let i = 0; i < 7; i++) {
      const flakeGeo = new THREE.PlaneGeometry(0.11, 0.07);
      const flakeMat = new THREE.MeshBasicMaterial({ color: "#f1f5f9" });
      const flake = new THREE.Mesh(flakeGeo, flakeMat);
      flake.rotation.x = -Math.PI / 2;
      flake.rotation.z = i * 0.9;
      flake.position.set(-0.42 + 0.3 * Math.cos(i), 0.69, -0.35 + 0.3 * Math.sin(i));
      this.washGroup.add(flake);
    }
  }

  private buildClothStage() {
    // Textile staging table (Shot 4)
    const tableMat = twoTone(new THREE.MeshLambertMaterial({ color: "#64748b" }));
    const tableGeo = new THREE.BoxGeometry(1.4, 0.75, 0.9);
    const table = new THREE.Mesh(tableGeo, tableMat);
    table.position.set(-0.45, 0.38, -0.55);
    this.clothGroup.add(table);

    // Fabric bolt roll
    const boltGeo = new THREE.CylinderGeometry(0.22, 0.22, 1.0, 24);
    const boltMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f8fafc" }));
    const bolt = new THREE.Mesh(boltGeo, boltMat);
    bolt.rotation.z = Math.PI / 2;
    bolt.position.set(-0.45, 0.94, -0.55);
    this.clothGroup.add(bolt);

    // Red & blue security thread spools
    const spoolGeo = new THREE.CylinderGeometry(0.07, 0.07, 0.18, 16);
    const redSpool = new THREE.Mesh(spoolGeo, new THREE.MeshBasicMaterial({ color: "#ef4444" }));
    redSpool.position.set(0.12, 0.85, -0.4);
    this.clothGroup.add(redSpool);

    const blueSpool = new THREE.Mesh(spoolGeo, new THREE.MeshBasicMaterial({ color: "#3b82f6" }));
    blueSpool.position.set(0.12, 0.85, -0.65);
    this.clothGroup.add(blueSpool);
  }

  private buildCounterfeitStage() {
    // Shady counterfeiter alchemy / chemical desk (Shot 5)
    const deskMat = twoTone(new THREE.MeshLambertMaterial({ color: "#27272a" }));
    const deskGeo = new THREE.BoxGeometry(1.8, 0.78, 1.1);
    const desk = new THREE.Mesh(deskGeo, deskMat);
    desk.position.set(0, 0.39, -0.7);
    this.counterfeitGroup.add(desk);

    // Glowing green counterfeit ink flask
    const flaskMat = new THREE.MeshBasicMaterial({ color: "#22c55e" });
    const flaskGeo = new THREE.ConeGeometry(0.15, 0.32, 16);
    const flask = new THREE.Mesh(flaskGeo, flaskMat);
    flask.position.set(-0.35, 0.94, -0.5);
    this.counterfeitGroup.add(flask);

    // Amber reagent bottle
    const botMat = twoTone(new THREE.MeshLambertMaterial({ color: "#d97706" }));
    const botGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.28, 16);
    const bot = new THREE.Mesh(botGeo, botMat);
    bot.position.set(0.35, 0.92, -0.5);
    this.counterfeitGroup.add(bot);
  }

  private buildScannerStage() {
    // Flatbed digital scanner table (Shot 7 & 8)
    const tableMat = twoTone(new THREE.MeshLambertMaterial({ color: "#334155" }));
    const tableGeo = new THREE.BoxGeometry(1.6, 0.72, 1.2);
    const table = new THREE.Mesh(tableGeo, tableMat);
    table.position.set(-0.15, 0.36, -0.7);
    this.scannerGroup.add(table);

    // Scanner housing
    const scanHousingMat = twoTone(new THREE.MeshLambertMaterial({ color: "#0f172a" }));
    const scanHousingGeo = new THREE.BoxGeometry(1.3, 0.14, 0.85);
    const scanHousing = new THREE.Mesh(scanHousingGeo, scanHousingMat);
    scanHousing.position.set(-0.15, 0.76, -0.7);
    this.scannerGroup.add(scanHousing);

    // Glowing scanner glass bed
    const glassGeo = new THREE.PlaneGeometry(1.0, 0.65);
    const glassMat = new THREE.MeshBasicMaterial({ color: "#06b6d4" });
    const glass = new THREE.Mesh(glassGeo, glassMat);
    glass.rotation.x = -Math.PI / 2;
    glass.position.set(-0.15, 0.835, -0.7);
    this.scannerGroup.add(glass);

    // Moving laser scanning bar
    const laserGeo = new THREE.BoxGeometry(0.04, 0.02, 0.65);
    const laserMat = new THREE.MeshBasicMaterial({ color: "#22d3ee" });
    this.scannerLaser = new THREE.Mesh(laserGeo, laserMat);
    this.scannerLaser.position.set(-0.15, 0.845, -0.7);
    this.scannerGroup.add(this.scannerLaser);
  }

  private buildShredderStage() {
    // Robotic inspection conveyor and laser shredder bin (Shot 10)
    const shredMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    const binGeo = new THREE.BoxGeometry(1.2, 1.8, 1.2);
    const bin = new THREE.Mesh(binGeo, shredMat);
    bin.position.set(-0.95, 0.9, -0.9);
    this.shredderGroup.add(bin);

    // Conveyor belt feeding defective sheets into shredder
    const convGeo = new THREE.BoxGeometry(1.6, 0.1, 0.75);
    const convMat = twoTone(new THREE.MeshLambertMaterial({ color: "#0f172a" }));
    const conv = new THREE.Mesh(convGeo, convMat);
    conv.position.set(0.2, 0.95, -0.9);
    this.shredderGroup.add(conv);

    // High-speed computer vision camera inspection head
    const camHeadGeo = new THREE.BoxGeometry(0.32, 0.42, 0.32);
    const camHeadMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f8fafc" }));
    const camHead = new THREE.Mesh(camHeadGeo, camHeadMat);
    camHead.position.set(0.2, 1.65, -0.9);
    this.shredderGroup.add(camHead);

    const lensGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.12, 16);
    const lensMat = new THREE.MeshBasicMaterial({ color: "#06b6d4" });
    const lens = new THREE.Mesh(lensGeo, lensMat);
    lens.position.set(0.2, 1.4, -0.9);
    this.shredderGroup.add(lens);

    // Flashing red warning beacon on top of shredder bin
    const beaconGeo = new THREE.CylinderGeometry(0.12, 0.15, 0.25, 16);
    const beaconMat = new THREE.MeshBasicMaterial({ color: "#ef4444" });
    this.shredderBeacon = new THREE.Mesh(beaconGeo, beaconMat);
    this.shredderBeacon.position.set(-0.95, 1.95, -0.9);
    this.shredderGroup.add(this.shredderBeacon);
  }

  private buildForegroundProps() {
    // 1. Industrial foreground pillar edge on the left
    const pillarMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    const fgPillarGeo = new THREE.BoxGeometry(0.4, 4.0, 0.4);
    this.fgPillar = new THREE.Mesh(fgPillarGeo, pillarMat);
    this.fgPillar.position.set(-1.15, 1.6, 0.95);
    this.fgGroup.add(this.fgPillar);

    // 2. Foreground chemical reagent bottles on a shelf edge (right)
    this.fgFlasks = new THREE.Group();
    const shelfGeo = new THREE.BoxGeometry(0.8, 0.06, 0.3);
    const shelf = new THREE.Mesh(shelfGeo, pillarMat);
    shelf.position.set(0.95, 1.0, 1.15);
    this.fgFlasks.add(shelf);
    const fBot1 = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.22, 12), new THREE.MeshBasicMaterial({ color: "#d97706" }));
    fBot1.position.set(0.85, 1.14, 1.15);
    this.fgFlasks.add(fBot1);
    const fBot2 = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.24, 12), new THREE.MeshBasicMaterial({ color: "#22c55e" }));
    fBot2.position.set(1.1, 1.15, 1.15);
    this.fgFlasks.add(fBot2);
    this.fgGroup.add(this.fgFlasks);

    // 3. Foreground safety stanchion with warning stripes
    this.fgStanchion = new THREE.Group();
    const postMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f59e0b" }));
    const postGeo = new THREE.CylinderGeometry(0.04, 0.04, 1.2, 12);
    const post = new THREE.Mesh(postGeo, postMat);
    post.position.set(-0.95, 0.6, 1.2);
    this.fgStanchion.add(post);
    this.fgGroup.add(this.fgStanchion);

    // 4. Foreground monitor console edge
    this.fgMonitor = new THREE.Group();
    const monGeo = new THREE.BoxGeometry(0.45, 0.32, 0.08);
    const monMat = twoTone(new THREE.MeshLambertMaterial({ color: "#0f172a" }));
    const mon = new THREE.Mesh(monGeo, monMat);
    mon.position.set(-0.75, 1.1, 1.05);
    mon.rotation.y = 0.4;
    this.fgMonitor.add(mon);
    const screenGeo = new THREE.PlaneGeometry(0.4, 0.27);
    const screenMat = new THREE.MeshBasicMaterial({ color: "#0284c7" });
    const screen = new THREE.Mesh(screenGeo, screenMat);
    screen.position.set(-0.74, 1.1, 1.1);
    screen.rotation.y = 0.4;
    this.fgMonitor.add(screen);
    this.fgGroup.add(this.fgMonitor);
  }

  setVisibleStage(stage: string, f: number) {
    this.officeGroup.visible = stage === "office";
    this.pressGroup.visible = stage === "intaglio" || stage === "midnight";
    this.washGroup.visible = stage === "wash";
    this.clothGroup.visible = stage === "cloth";
    this.counterfeitGroup.visible = stage === "counterfeit";
    this.scannerGroup.visible = stage === "scanner" || stage === "eurion";
    this.shredderGroup.visible = stage === "shredder";

    this.fgPillar.visible = stage === "intaglio" || stage === "midnight";
    this.fgFlasks.visible = stage === "counterfeit";
    this.fgMonitor.visible = stage === "scanner" || stage === "eurion";
    this.fgStanchion.visible = stage === "shredder";

    if (this.pressGroup.visible) {
      this.rollerTop.rotation.y = f * 0.18;
      this.rollerBot.rotation.y = -f * 0.18;
    }

    if (this.scannerGroup.visible) {
      const laserX = -0.15 + 0.38 * Math.sin(f * 0.22);
      this.scannerLaser.position.x = laserX;
      if (stage === "eurion") {
        const isRed = Math.floor(f * 0.4) % 2 === 0;
        (this.scannerLaser.material as THREE.MeshBasicMaterial).color.set(isRed ? "#ef4444" : "#ffedd5");
      } else {
        (this.scannerLaser.material as THREE.MeshBasicMaterial).color.set("#22d3ee");
      }
    }

    if (this.shredderGroup.visible) {
      const beaconFlash = (Math.sin(f * 0.5) + 1) * 0.5;
      (this.shredderBeacon.material as THREE.MeshBasicMaterial).color.set(beaconFlash > 0.4 ? "#ef4444" : "#450a0a");
    }

    if (this.washGroup.visible) {
      this.washWater.position.y = 0.68 + 0.015 * Math.sin(f * 0.2);
    }
  }
}
