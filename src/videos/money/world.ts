// Dynamic 3D World Scene for "How Money Is Printed"
// Coordinates the rich 3D sets with the 3.5 HH superellipse cartoon cast.
// Solves the "persistent bill" bug: bill is only displayed diegetically when relevant,
// and never obscures the action.
import * as THREE from "three";
import { MoneySceneBuilder } from "./build";
import { drawChar, drawDollarCard, CharRole } from "./toon";
import { camAt, shotAt, V3 } from "./story";
import { NOINK } from "./ink";
import { LIGHTS } from "./lights";

export class World {
  root: THREE.Group;
  builder: MoneySceneBuilder;

  charMesh: THREE.Mesh;
  charCanvas: HTMLCanvasElement;
  charCtx: CanvasRenderingContext2D;
  charTex: THREE.CanvasTexture;

  billMesh: THREE.Mesh;
  billCanvas: HTMLCanvasElement;
  billCtx: CanvasRenderingContext2D;
  billTex: THREE.CanvasTexture;

  dirLight: THREE.DirectionalLight;
  hemiLight: THREE.HemisphereLight;
  spotLight: THREE.SpotLight;

  constructor() {
    this.root = new THREE.Group();
    this.builder = new MoneySceneBuilder();
    this.root.add(this.builder.root);

    // 1. Character billboard (600 x 1000 Canvas, 3.5 HH tall)
    this.charCanvas = document.createElement("canvas");
    this.charCanvas.width = 600;
    this.charCanvas.height = 1000;
    this.charCtx = this.charCanvas.getContext("2d")!;
    this.charTex = new THREE.CanvasTexture(this.charCanvas);
    this.charTex.colorSpace = THREE.SRGBColorSpace;

    // Plane geometry scaled to authentic 3.5 HH human proportion (approx 2.1m tall)
    const charGeo = new THREE.PlaneGeometry(1.3, 2.16);
    const charMat = new THREE.MeshBasicMaterial({
      map: this.charTex,
      transparent: true,
      depthTest: true,
      depthWrite: false,
    });
    this.charMesh = new THREE.Mesh(charGeo, charMat);
    this.charMesh.position.set(0.0, 1.08, 0.0);
    this.charMesh.layers.enable(NOINK);
    this.charMesh.layers.enable(0);
    this.root.add(this.charMesh);

    // 2. Dollar bill card billboard (600 x 350 Canvas)
    this.billCanvas = document.createElement("canvas");
    this.billCanvas.width = 600;
    this.billCanvas.height = 350;
    this.billCtx = this.billCanvas.getContext("2d")!;
    this.billTex = new THREE.CanvasTexture(this.billCanvas);
    this.billTex.colorSpace = THREE.SRGBColorSpace;

    const billGeo = new THREE.PlaneGeometry(0.85, 0.48);
    const billMat = new THREE.MeshBasicMaterial({
      map: this.billTex,
      transparent: true,
      depthTest: true,
      depthWrite: false,
    });
    this.billMesh = new THREE.Mesh(billGeo, billMat);
    this.billMesh.position.set(0.0, 1.2, 0.0);
    this.billMesh.layers.enable(NOINK);
    this.billMesh.layers.enable(0);
    this.billMesh.visible = false;
    this.root.add(this.billMesh);

    // 3. Scene Lighting
    this.dirLight = new THREE.DirectionalLight("#fff3e0", 2.8);
    this.dirLight.position.set(3, 8, 5);
    this.root.add(this.dirLight);

    this.hemiLight = new THREE.HemisphereLight("#dcecff", "#b49a78", 0.65);
    this.root.add(this.hemiLight);

    this.spotLight = new THREE.SpotLight("#22d3ee", 4.0, 12, Math.PI / 5, 0.3);
    this.spotLight.position.set(0, 3.2, 0);
    this.spotLight.target.position.set(0, 0.7, -0.8);
    this.root.add(this.spotLight);
    this.root.add(this.spotLight.target);
  }

  update(shotId: number, f: number, camera: THREE.PerspectiveCamera, scene: THREE.Scene): THREE.Vector3 {
    const s = shotAt(f);
    const cam = camAt(s.id, f);

    camera.layers.enable(0);
    camera.layers.enable(NOINK);

    camera.position.set(...cam.pos);
    const target = new THREE.Vector3(...cam.look);
    camera.lookAt(target);
    camera.fov = cam.fov;
    camera.rotation.z = cam.roll;
    camera.updateProjectionMatrix();

    // Yaw billboard towards camera while keeping upright
    this.charMesh.quaternion.copy(camera.quaternion);

    // Apply color management & lighting presets
    const lp = LIGHTS[s.light];
    this.dirLight.color.set(lp.sunCol);
    this.dirLight.intensity = lp.sunI;
    this.hemiLight.color.set(lp.sky);
    this.hemiLight.groundColor.set(lp.ground);
    this.hemiLight.intensity = lp.hemiI;

    const radAz = (lp.az * Math.PI) / 180;
    const radEl = (lp.el * Math.PI) / 180;
    const sunDist = 12;
    this.dirLight.position.set(
      camera.position.x + sunDist * Math.sin(radAz) * Math.cos(radEl),
      camera.position.y + sunDist * Math.sin(radEl),
      camera.position.z + sunDist * Math.cos(radAz) * Math.cos(radEl)
    );
    this.dirLight.target.position.copy(target);

    // Update 3D stage geometry
    this.builder.setVisibleStage(s.stage, f);

    // Narrative Casting & Character Posing
    let role: CharRole = "citizen";
    let expr = "neutral";
    let charPos: V3 = [0.0, 1.08, 0.0];
    let billVisible = false;
    let billPos: V3 = [0.0, 1.25, 0.0];
    let billScale = 0.55;
    let billTilt = 0;
    let isFlatOnScanner = false;

    if (s.stage === "office") {
      // Shot 1: Citizen at office desk looking at jammed printer
      role = "citizen";
      expr = "smirk";
      charPos = [-0.15, 1.08, 0.1];
      billVisible = false; // NO giant bill in shot 1!
    } else if (s.stage === "intaglio") {
      // Shot 2: Mint Press Master beside the 20-ton press
      role = "worker";
      expr = f >= 135 && f < 144 ? "action" : "smirk";
      charPos = [0.25, 1.08, -0.4];
      billVisible = false;
    } else if (s.stage === "wash") {
      // Shot 3: Citizen in shock at dissolving paper in washing vat
      role = "citizen";
      expr = "shock";
      charPos = [-0.45, 1.08, 0.0];
      billVisible = false;
    } else if (s.stage === "cloth") {
      // Shot 4: Textile worker by the cotton/linen loom
      role = "worker";
      expr = "neutral";
      charPos = [-0.25, 1.08, 0.1];
      billVisible = false;
    } else if (s.stage === "counterfeit") {
      // Shot 5: Counterfeiter mixing green ink in secret den
      role = "counterfeiter";
      expr = "shock";
      charPos = [-0.15, 1.08, 0.0];
      billVisible = false;
    } else if (s.stage === "quantum") {
      // Shot 6: Quantum macro inspection - bill mounted on clean easel!
      role = "inspector";
      expr = "smirk";
      charPos = [0.65, 1.08, -0.2];
      billVisible = true;
      billPos = [-0.05, 1.22, -0.15];
      billScale = 0.68;
      // Tilt wobble causes the numerals to flip copper <-> emerald
      billTilt = 8.0 * Math.sin((f - 728) * 0.1);
    } else if (s.stage === "scanner" || s.stage === "eurion") {
      // Shot 7 & 8: Bill lying flat on the scanner glass
      role = "inspector";
      expr = s.stage === "eurion" ? "shock" : "neutral";
      charPos = [0.45, 1.08, -0.3];
      billVisible = true;
      isFlatOnScanner = true;
      billPos = [0.0, 0.99, -0.6]; // On the glass bed
      billScale = 0.52;
    } else if (s.stage === "midnight") {
      // Shot 9: Midnight surveillance
      role = "counterfeiter";
      expr = "shock";
      charPos = [0.15, 1.08, -0.6];
      billVisible = false;
    } else if (s.stage === "shredder") {
      // Shot 10: Inspector beside the laser shredder
      role = "worker";
      expr = "smirk";
      charPos = [0.35, 1.08, -0.4];
      billVisible = false;
    } else if (s.stage === "twist") {
      // Shot 11: Citizen holding the finished armor bill proudly
      role = "citizen";
      expr = "smirk";
      charPos = [-0.1, 1.08, 0.0];
      billVisible = true;
      billPos = [0.32, 1.15, 0.12]; // Held at chest height
      billScale = 0.34; // Modest, realistic handheld scale
    }

    this.charMesh.position.set(...charPos);

    this.billMesh.visible = billVisible;
    if (billVisible) {
      this.billMesh.position.set(...billPos);
      this.billMesh.scale.set(billScale, billScale, billScale);
      if (isFlatOnScanner) {
        this.billMesh.rotation.set(-Math.PI / 2, 0, 0);
      } else {
        this.billMesh.quaternion.copy(camera.quaternion);
        if (billTilt !== 0) {
          this.billMesh.rotation.z += (billTilt * Math.PI) / 180;
        }
      }
    }

    // Render Canvas2D Characters
    this.charCtx.clearRect(0, 0, 600, 1000);
    drawChar(this.charCtx, role, f, expr);
    this.charTex.needsUpdate = true;

    // Render Canvas2D Bill (if visible)
    if (billVisible) {
      this.billCtx.clearRect(0, 0, 600, 350);
      drawDollarCard(this.billCtx, { stage: s.stage, tilt: billTilt });
      this.billTex.needsUpdate = true;
    }

    // Dynamic Atmospheric Spotlights per narrative beat
    if (s.stage === "scanner") {
      const scanX = -0.45 + ((f * 0.04) % 1) * 0.9;
      this.spotLight.color.set("#22d3ee");
      this.spotLight.intensity = 5.0;
      this.spotLight.position.set(scanX, 2.5, -0.6);
      this.spotLight.target.position.set(scanX, 0.8, -0.6);
    } else if (s.stage === "eurion") {
      // Flashing red emergency alarm strobe
      const isRed = Math.floor(f * 0.3) % 2 === 0;
      this.spotLight.color.set(isRed ? "#ef4444" : "#ffffff");
      this.spotLight.intensity = isRed ? 9.0 : 1.5;
      this.spotLight.position.set(0.0, 2.8, -0.6);
      this.spotLight.target.position.set(0.0, 0.8, -0.6);
    } else if (s.stage === "midnight") {
      // Security camera searchlight beam
      this.spotLight.color.set("#e0f2fe");
      this.spotLight.intensity = 8.0;
      this.spotLight.position.set(0.0, 4.5, -1.2);
      this.spotLight.target.position.set(0.15, 1.0, -0.6);
    } else if (s.stage === "shredder") {
      // Red warning beacon
      const beaconFlash = (Math.sin(f * 0.5) + 1) * 0.5;
      this.spotLight.color.set("#ef4444");
      this.spotLight.intensity = beaconFlash * 5.0;
      this.spotLight.position.set(-0.8, 2.8, -0.8);
      this.spotLight.target.position.set(-0.8, 0.9, -0.8);
    } else {
      this.spotLight.intensity = 0.0;
    }

    return target;
  }
}
