// 3D Environment Architecture for "How Money Is Printed"
// Rich, vibrant, colorful toon world with crisp ink silhouettes.
// Every stage is dressed with authentic diegetic props, avoiding empty walls.
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
  quantumGroup: THREE.Group;
  scannerGroup: THREE.Group;
  shredderGroup: THREE.Group;
  twistGroup: THREE.Group;

  pressCarrier!: THREE.Group;
  pressRoller!: THREE.Mesh;
  washWater!: THREE.Mesh;
  washSuds!: THREE.Mesh[];
  scannerLaser!: THREE.Mesh;
  scannerScreenMat!: THREE.MeshBasicMaterial;
  shredderTeeth!: THREE.Mesh;
  shredderBits!: THREE.Mesh[];

  constructor() {
    this.root = new THREE.Group();
    this.officeGroup = new THREE.Group();
    this.pressGroup = new THREE.Group();
    this.washGroup = new THREE.Group();
    this.clothGroup = new THREE.Group();
    this.counterfeitGroup = new THREE.Group();
    this.quantumGroup = new THREE.Group();
    this.scannerGroup = new THREE.Group();
    this.shredderGroup = new THREE.Group();
    this.twistGroup = new THREE.Group();

    this.buildOfficeStage();
    this.buildIntaglioPress();
    this.buildWashStage();
    this.buildClothStage();
    this.buildCounterfeitStage();
    this.buildQuantumStage();
    this.buildScannerStage();
    this.buildShredderStage();
    this.buildTwistStage();

    this.root.add(this.officeGroup);
    this.root.add(this.pressGroup);
    this.root.add(this.washGroup);
    this.root.add(this.clothGroup);
    this.root.add(this.counterfeitGroup);
    this.root.add(this.quantumGroup);
    this.root.add(this.scannerGroup);
    this.root.add(this.shredderGroup);
    this.root.add(this.twistGroup);
  }

  // ---------------- 1. OFFICE HOOK STAGE (Shot 1) ----------------
  private buildOfficeStage() {
    const g = this.officeGroup;

    // Cozy wood plank floor
    const floorGeo = new THREE.PlaneGeometry(16, 16);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#c29b68" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Warm cream office back wall with wainscoting
    const wallGeo = new THREE.PlaneGeometry(16, 9);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#e2d7c5" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 4.5, -3.5);
    g.add(wall);

    // Wood wainscoting lower panels
    const wainGeo = new THREE.BoxGeometry(16, 2.2, 0.1);
    const wainMat = twoTone(new THREE.MeshLambertMaterial({ color: "#8a532d" }));
    const wain = new THREE.Mesh(wainGeo, wainMat);
    wain.position.set(0, 1.1, -3.45);
    g.add(wain);

    // Executive Office Desk (centered, character stands beside it)
    const deskMat = twoTone(new THREE.MeshLambertMaterial({ color: "#6c3c1e" }));
    const deskTop = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.1, 1.2), deskMat);
    deskTop.position.set(0.0, 0.8, -0.4);
    g.add(deskTop);

    // Desk legs
    const legMat = twoTone(new THREE.MeshLambertMaterial({ color: "#2d180c" }));
    for (const dx of [-1.05, 1.05]) {
      for (const dz of [-0.45, 0.45]) {
        const leg = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.8, 0.1), legMat);
        leg.position.set(dx, 0.4, -0.4 + dz);
        g.add(leg);
      }
    }

    // Modern Computer Monitor on desk
    const monBase = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.2, 0.04, 16), legMat);
    monBase.position.set(-0.55, 0.82, -0.4);
    g.add(monBase);
    const monPole = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.35, 12), legMat);
    monPole.position.set(-0.55, 1.0, -0.4);
    g.add(monPole);
    const monScreen = new THREE.Mesh(
      new THREE.BoxGeometry(0.85, 0.52, 0.04),
      new THREE.MeshBasicMaterial({ color: "#38bdf8" }) // Glowing blue screen
    );
    monScreen.position.set(-0.55, 1.25, -0.38);
    g.add(monScreen);

    // Inkjet Desktop Printer on desk
    const prMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f8fafc" }));
    const printer = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.36, 0.55), prMat);
    printer.position.set(0.55, 1.0, -0.35);
    g.add(printer);

    // Jammed crumpled paper sticking out of printer
    const jamMat = new THREE.MeshBasicMaterial({ color: "#ffffff" });
    const jamPaper = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.03, 0.48), jamMat);
    jamPaper.position.set(0.55, 1.18, -0.15);
    jamPaper.rotation.set(0.35, 0.12, -0.1);
    g.add(jamPaper);

    // Framed Certificate on Wall: "ECONOMICS 101"
    const frameGeo = new THREE.BoxGeometry(1.2, 0.9, 0.05);
    const frameMat = twoTone(new THREE.MeshLambertMaterial({ color: "#d97706" }));
    const frame = new THREE.Mesh(frameGeo, frameMat);
    frame.position.set(-1.2, 3.2, -3.42);
    g.add(frame);
    const cert = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.7), new THREE.MeshBasicMaterial({ color: "#fffbeb" }));
    cert.position.set(-1.2, 3.2, -3.39);
    g.add(cert);
  }

  // ---------------- 2. INTAGLIO PRESS STAGE (Shot 2) ----------------
  private buildIntaglioPress() {
    const g = this.pressGroup;

    // Industrial concrete floor with yellow hazard stripes
    const floorGeo = new THREE.PlaneGeometry(20, 20);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#64748b" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Safety yellow hazard stripes
    for (let x = -4; x <= 4; x += 1.8) {
      const st = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.01, 1.2), twoTone(new THREE.MeshLambertMaterial({ color: "#eab308" })));
      st.position.set(x, 0.005, 0.6);
      g.add(st);
    }

    // Mint factory brick back wall with high arched steel windows
    const wallGeo = new THREE.PlaneGeometry(20, 12);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#475569" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 6, -4.5);
    g.add(wall);

    // Overhead industrial crane beam (Yellow steel I-beam)
    const beamGeo = new THREE.BoxGeometry(20, 0.8, 0.4);
    const beamMat = twoTone(new THREE.MeshLambertMaterial({ color: "#facc15" }));
    const beam = new THREE.Mesh(beamGeo, beamMat);
    beam.position.set(0, 7.5, -2.5);
    g.add(beam);

    // 20-TON HYDRAULIC INTAGLIO PRESS (Centerpiece)
    const pressGroup = new THREE.Group();
    pressGroup.position.set(0, 0, -1.8);

    // Massive cast-iron base
    const baseMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    const base = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.9, 2.2), baseMat);
    base.position.y = 0.45;
    pressGroup.add(base);

    // Twin giant steel pillars
    const pillarMat = twoTone(new THREE.MeshPhongMaterial({ color: "#94a3b8", specular: "#cbd5e1", shininess: 40 }));
    for (const px of [-1.4, 1.4]) {
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.32, 4.2, 24), pillarMat);
      col.position.set(px, 2.5, 0);
      pressGroup.add(col);
    }

    // Top crosshead block (Cast with "20 TONS")
    const topBlock = new THREE.Mesh(new THREE.BoxGeometry(3.8, 1.1, 1.8), baseMat);
    topBlock.position.y = 4.6;
    pressGroup.add(topBlock);

    // Hydraulic cylinders & polished engraving plate (stamps down on frame 137)
    this.pressCarrier = new THREE.Group();
    const pistonMat = twoTone(new THREE.MeshPhongMaterial({ color: "#e2e8f0", specular: "#ffffff", shininess: 60 }));
    const piston = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 1.6, 24), pistonMat);
    piston.position.y = 3.6;
    this.pressCarrier.add(piston);

    // Brass engraved printing plate
    const plateMat = twoTone(new THREE.MeshPhongMaterial({ color: "#ca8a04", specular: "#fef08a", shininess: 70 }));
    const plate = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.15, 1.2), plateMat);
    plate.position.y = 2.75;
    this.pressCarrier.add(plate);

    pressGroup.add(this.pressCarrier);

    // Steel inking rollers
    this.pressRoller = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 2.4, 24), pillarMat);
    this.pressRoller.rotation.z = Math.PI / 2;
    this.pressRoller.position.set(0, 1.35, -0.2);
    pressGroup.add(this.pressRoller);

    g.add(pressGroup);
  }

  // ---------------- 3. WASH STAGE (Shot 3) ----------------
  private buildWashStage() {
    const g = this.washGroup;

    // Laboratory tiled floor (cool blue tiles)
    const floorGeo = new THREE.PlaneGeometry(16, 16);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#93c5fd" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Lab tile back wall
    const wallGeo = new THREE.PlaneGeometry(16, 9);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f8fafc" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 4.5, -3.5);
    g.add(wall);

    // Commercial Washing Machine / Agitator Vat
    const drumMat = twoTone(new THREE.MeshPhongMaterial({ color: "#cbd5e1", specular: "#ffffff", shininess: 50 }));
    const washer = new THREE.Mesh(new THREE.BoxGeometry(2.2, 2.4, 2.0), drumMat);
    washer.position.set(0, 1.2, -1.2);
    g.add(washer);

    // Front circular glass window
    const windowRing = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.72, 0.1, 32), twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" })));
    windowRing.rotation.x = Math.PI / 2;
    windowRing.position.set(0, 1.35, -0.15);
    g.add(windowRing);

    // Swirling soapy water inside glass
    const waterMat = new THREE.MeshBasicMaterial({ color: "#06b6d4", transparent: true, opacity: 0.75 });
    this.washWater = new THREE.Mesh(new THREE.CircleGeometry(0.64, 32), waterMat);
    this.washWater.position.set(0, 1.35, -0.09);
    g.add(this.washWater);

    // Dissolving paper flakes / suds (swirl dynamically)
    this.washSuds = [];
    const sudMat = new THREE.MeshBasicMaterial({ color: "#ffffff" });
    for (let i = 0; i < 12; i++) {
      const sud = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.08), sudMat);
      sud.position.set((Math.random() - 0.5) * 0.8, 1.35 + (Math.random() - 0.5) * 0.8, -0.08);
      this.washSuds.push(sud);
      g.add(sud);
    }
  }

  // ---------------- 4. CLOTH LOOM STAGE (Shot 4) ----------------
  private buildClothStage() {
    const g = this.clothGroup;

    // Wooden workshop floor
    const floorGeo = new THREE.PlaneGeometry(16, 16);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#a16207" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Warm timber wall with hanging spools
    const wallGeo = new THREE.PlaneGeometry(16, 9);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#78350f" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 4.5, -3.5);
    g.add(wall);

    // Textile Weaving Loom Frame (Oak wood beams & brass gears)
    const loomMat = twoTone(new THREE.MeshLambertMaterial({ color: "#451a03" }));
    for (const lx of [-1.6, 1.6]) {
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.2, 3.2, 0.2), loomMat);
      post.position.set(lx, 1.6, -1.2);
      g.add(post);
    }
    const crossBar = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.2, 0.2), loomMat);
    crossBar.position.set(0, 3.0, -1.2);
    g.add(crossBar);

    // Rolls of woven cotton/linen substrate (75% cotton / 25% linen)
    const rollMat = twoTone(new THREE.MeshLambertMaterial({ color: "#fef3c7" })); // Off-white ecru
    const roll = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 2.8, 24), rollMat);
    roll.rotation.z = Math.PI / 2;
    roll.position.set(0, 1.8, -1.2);
    g.add(roll);

    // Hanging woven cloth sheet cascading downwards
    const sheetGeo = new THREE.PlaneGeometry(2.6, 1.6);
    const sheet = new THREE.Mesh(sheetGeo, rollMat);
    sheet.position.set(0, 1.0, -0.75);
    g.add(sheet);

    // Spools of red and blue security threads
    for (let i = -3; i <= 3; i++) {
      const spoolCol = i % 2 === 0 ? "#dc2626" : "#2563eb";
      const spool = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.35, 16), twoTone(new THREE.MeshLambertMaterial({ color: spoolCol })));
      spool.position.set(i * 0.45, 3.4, -1.2);
      g.add(spool);
    }
  }

  // ---------------- 5. COUNTERFEITER STAGE (Shot 5) ----------------
  private buildCounterfeitStage() {
    const g = this.counterfeitGroup;

    // Dark basement stone floor
    const floorGeo = new THREE.PlaneGeometry(16, 16);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#334155" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Rough brick wall
    const wallGeo = new THREE.PlaneGeometry(16, 9);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 4.5, -3.5);
    g.add(wall);

    // Secret chemical workbench
    const benchMat = twoTone(new THREE.MeshLambertMaterial({ color: "#0f172a" }));
    const bench = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.85, 1.4), benchMat);
    bench.position.set(0, 0.42, -0.6);
    g.add(bench);

    // Glass slab with mixed green ink
    const slabMat = twoTone(new THREE.MeshPhongMaterial({ color: "#15803d", specular: "#86efac", shininess: 80 }));
    const slab = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.04, 0.6), slabMat);
    slab.position.set(-0.5, 0.87, -0.5);
    g.add(slab);

    // Chemical flasks, jars of green pigment, ink bottles
    const flaskMat = new THREE.MeshBasicMaterial({ color: "#22c55e", transparent: true, opacity: 0.65 });
    const flask1 = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.35, 16), flaskMat);
    flask1.position.set(0.65, 1.02, -0.6);
    g.add(flask1);
    const flask2 = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.28, 16), new THREE.MeshBasicMaterial({ color: "#ca8a04", transparent: true, opacity: 0.7 }));
    flask2.position.set(0.95, 0.99, -0.55);
    g.add(flask2);

    // Architect desk lamp casting warm orange light
    const lampArm = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.6, 8), twoTone(new THREE.MeshLambertMaterial({ color: "#f59e0b" })));
    lampArm.position.set(0.8, 1.25, -0.9);
    g.add(lampArm);
  }

  // ---------------- 6. QUANTUM STAGE (Shot 6) ----------------
  private buildQuantumStage() {
    const g = this.quantumGroup;

    // Cleanroom white pedestal floor
    const floorGeo = new THREE.PlaneGeometry(16, 16);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#0f172a" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // High-tech architectural backdrop with grid lines
    const wallGeo = new THREE.PlaneGeometry(16, 9);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e1b4b" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 4.5, -3.5);
    g.add(wall);

    // Exhibition Easel mounting the giant bill
    const easelMat = twoTone(new THREE.MeshLambertMaterial({ color: "#d97706" }));
    for (const ex of [-0.65, 0.65]) {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.4, 12), easelMat);
      leg.position.set(ex, 1.2, -0.2);
      g.add(leg);
    }
  }

  // ---------------- 7. SCANNER & EURION STAGE (Shots 7 & 8) ----------------
  private buildScannerStage() {
    const g = this.scannerGroup;

    // Digital forensic lab floor
    const floorGeo = new THREE.PlaneGeometry(16, 16);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Lab wall with terminal monitors
    const wallGeo = new THREE.PlaneGeometry(16, 9);
    const wallMat = twoTone(new THREE.MeshLambertMaterial({ color: "#0f172a" }));
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(0, 4.5, -3.5);
    g.add(wall);

    // High-end Xerox/Digital Flatbed Scanner
    const scMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f8fafc" }));
    const scanner = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.45, 1.3), scMat);
    scanner.position.set(0, 0.75, -0.6);
    g.add(scanner);

    // Scanner glass bed
    const glassMat = new THREE.MeshBasicMaterial({ color: "#0f172a" });
    const glass = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.02, 0.95), glassMat);
    glass.position.set(0, 0.98, -0.6);
    g.add(glass);

    // Sweeping cyan scanning laser line (animated in world.ts)
    const laserMat = new THREE.MeshBasicMaterial({ color: "#22d3ee" });
    this.scannerLaser = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, 0.96), laserMat);
    this.scannerLaser.position.set(-0.55, 1.0, -0.6);
    g.add(this.scannerLaser);

    // Scanner LCD Status Screen (turns red with slashed circle on EURion refusal)
    this.scannerScreenMat = new THREE.MeshBasicMaterial({ color: "#10b981" }); // Normal green
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.28), this.scannerScreenMat);
    scr.position.set(0.65, 1.08, -0.15);
    scr.rotation.x = -0.3;
    g.add(scr);
  }

  // ---------------- 8. SHREDDER STAGE (Shot 10) ----------------
  private buildShredderStage() {
    const g = this.shredderGroup;

    // Industrial floor
    const floorGeo = new THREE.PlaneGeometry(16, 16);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#475569" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Industrial shredder housing
    const shMat = twoTone(new THREE.MeshLambertMaterial({ color: "#0f172a" }));
    const shredder = new THREE.Mesh(new THREE.BoxGeometry(2.0, 1.4, 1.2), shMat);
    shredder.position.set(-0.8, 0.7, -0.8);
    g.add(shredder);

    // Revolving interlocking steel cutting blades
    const bladeMat = twoTone(new THREE.MeshPhongMaterial({ color: "#cbd5e1", specular: "#ffffff", shininess: 60 }));
    this.shredderTeeth = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 1.6, 16), bladeMat);
    this.shredderTeeth.rotation.z = Math.PI / 2;
    this.shredderTeeth.position.set(-0.8, 1.35, -0.8);
    g.add(this.shredderTeeth);

    // Conveyor belt feeding bills into the teeth
    const convMat = twoTone(new THREE.MeshLambertMaterial({ color: "#1e293b" }));
    const conv = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.12, 0.6), convMat);
    conv.position.set(0.8, 1.25, -0.8);
    g.add(conv);

    // Flying shredded paper confetti bits
    this.shredderBits = [];
    const bitMat = new THREE.MeshBasicMaterial({ color: "#86efac" });
    for (let i = 0; i < 18; i++) {
      const bit = new THREE.Mesh(new THREE.PlaneGeometry(0.04, 0.16), bitMat);
      bit.position.set(-0.8 + (Math.random() - 0.5) * 0.6, 0.5 + Math.random() * 0.7, -0.8 + (Math.random() - 0.5) * 0.4);
      this.shredderBits.push(bit);
      g.add(bit);
    }
  }

  // ---------------- 9. TWIST PAYOFF STAGE (Shot 11) ----------------
  private buildTwistStage() {
    const g = this.twistGroup;

    // Grand polished marble mint entrance hall
    const floorGeo = new THREE.PlaneGeometry(20, 20);
    const floorMat = twoTone(new THREE.MeshLambertMaterial({ color: "#e2e8f0" }));
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);

    // Classical Treasury stone pillars with sunlight streaming between them
    const colMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f8fafc" }));
    for (const cx of [-3.2, -1.6, 1.6, 3.2]) {
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.4, 8.0, 24), colMat);
      col.position.set(cx, 4.0, -3.2);
      g.add(col);
    }

    // Grand architectural archway behind pillars
    const archMat = twoTone(new THREE.MeshLambertMaterial({ color: "#cbd5e1" }));
    const arch = new THREE.Mesh(new THREE.BoxGeometry(10, 1.5, 0.8), archMat);
    arch.position.set(0, 7.8, -3.2);
    g.add(arch);
  }

  // Set visible stage per narrative beat
  setVisibleStage(stage: string, f: number) {
    this.officeGroup.visible = stage === "office";
    this.pressGroup.visible = stage === "intaglio" || stage === "midnight";
    this.washGroup.visible = stage === "wash";
    this.clothGroup.visible = stage === "cloth";
    this.counterfeitGroup.visible = stage === "counterfeit";
    this.quantumGroup.visible = stage === "quantum";
    this.scannerGroup.visible = stage === "scanner" || stage === "eurion";
    this.shredderGroup.visible = stage === "shredder";
    this.twistGroup.visible = stage === "twist";

    // Dynamic animations
    if (stage === "intaglio") {
      // Stamp press carrier drop on impact frame 137
      const isStamp = f >= 135 && f < 144;
      this.pressCarrier.position.y = isStamp ? -0.45 : 0.0;
      this.pressRoller.rotation.x = f * 0.12;
    } else if (stage === "wash") {
      // Swirl water and suds
      this.washWater.rotation.z = f * 0.15;
      this.washSuds.forEach((sud, i) => {
        sud.rotation.z = f * 0.2 + i;
        sud.position.x = Math.sin(f * 0.1 + i) * 0.35;
        sud.position.y = 1.35 + Math.cos(f * 0.1 + i) * 0.35;
      });
    } else if (stage === "scanner" || stage === "eurion") {
      // Animate sweep of scanner laser
      const scanX = -0.45 + ((f * 0.04) % 1) * 0.9;
      this.scannerLaser.position.x = scanX;
      // Change screen color on EURion lock
      if (stage === "eurion") {
        this.scannerScreenMat.color.set(Math.floor(f * 0.3) % 2 === 0 ? "#ef4444" : "#ffffff");
      } else {
        this.scannerScreenMat.color.set("#10b981");
      }
    } else if (stage === "shredder") {
      // Rotate shredder cutting teeth and shower confetti
      this.shredderTeeth.rotation.y = f * 0.35;
      this.shredderBits.forEach((bit, i) => {
        bit.position.y = 0.5 + ((f * 0.08 + i * 0.3) % 1) * 0.8;
        bit.rotation.z = f * 0.2 + i;
      });
    }
  }
}
