// Dynamic 3D world scene for "How Money Is Printed"
// Coordinates the 3D factory scenery with Canvas2D character and dollar card billboards.
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

    // 1. Character billboard (600 x 1000 Canvas)
    this.charCanvas = document.createElement("canvas");
    this.charCanvas.width = 600;
    this.charCanvas.height = 1000;
    this.charCtx = this.charCanvas.getContext("2d")!;
    this.charTex = new THREE.CanvasTexture(this.charCanvas);
    this.charTex.colorSpace = THREE.SRGBColorSpace;

    const charGeo = new THREE.PlaneGeometry(1.4, 2.3);
    const charMat = new THREE.MeshBasicMaterial({ map: this.charTex, transparent: true, depthTest: true });
    this.charMesh = new THREE.Mesh(charGeo, charMat);
    this.charMesh.position.set(0.1, 1.15, 0.0);
    this.charMesh.layers.enable(NOINK);
    this.charMesh.layers.enable(0);
    this.root.add(this.charMesh);

    // 2. Dollar bill billboard (600 x 350 Canvas)
    this.billCanvas = document.createElement("canvas");
    this.billCanvas.width = 600;
    this.billCanvas.height = 350;
    this.billCtx = this.billCanvas.getContext("2d")!;
    this.billTex = new THREE.CanvasTexture(this.billCanvas);
    this.billTex.colorSpace = THREE.SRGBColorSpace;

    const billGeo = new THREE.PlaneGeometry(1.0, 0.58);
    const billMat = new THREE.MeshBasicMaterial({ map: this.billTex, transparent: true, depthTest: true });
    this.billMesh = new THREE.Mesh(billGeo, billMat);
    this.billMesh.position.set(0.38, 1.12, 0.15);
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

    this.builder.setVisibleStage(s.stage, f);

    let role: CharRole = "citizen";
    let expr = "neutral";
    let charPos: V3 = [0.02, 1.15, 0.0];
    let billVisible = false;
    let billPos: V3 = [0.38, 1.12, 0.15];
    let billScale = 0.38;
    let billTilt = 0;
    let isFlatOnScanner = false;

    if (s.stage === "office") {
      role = "citizen";
      expr = "neutral";
      charPos = [0.02, 1.15, 0.0];
      billVisible = true;
      billPos = [0.38, 1.12, 0.15];
      billScale = 0.38;
    } else if (s.stage === "intaglio") {
      role = "worker";
      expr = "smirk";
      charPos = [0.15, 1.15, 0.0];
      billVisible = false;
    } else if (s.stage === "wash") {
      role = "citizen";
      expr = "shock";
      charPos = [0.22, 1.15, 0.0];
      billVisible = false;
    } else if (s.stage === "cloth") {
      role = "worker";
      expr = "neutral";
      charPos = [0.12, 1.15, 0.0];
      billVisible = true;
      billPos = [-0.32, 1.16, 0.15];
      billScale = 0.40;
    } else if (s.stage === "counterfeit") {
      role = "counterfeiter";
      expr = "smirk";
      charPos = [0.08, 1.15, 0.0];
      billVisible = false;
    } else if (s.stage === "quantum") {
      role = "inspector";
      expr = "smirk";
      charPos = [0.35, 1.15, -0.3];
      billVisible = true;
      billPos = [0.0, 1.2, 0.0];
      billScale = 0.82;
      billTilt = 8 * Math.sin((f - 728) * 0.1);
    } else if (s.stage === "scanner" || s.stage === "eurion") {
      role = "inspector";
      expr = s.stage === "eurion" ? "shock" : "neutral";
      charPos = [0.26, 1.15, -0.2];
      billVisible = true;
      isFlatOnScanner = true;
      billPos = [-0.15, 0.84, -0.7];
      billScale = 0.52;
    } else if (s.stage === "midnight") {
      role = "counterfeiter";
      expr = "shock";
      charPos = [0.08, 1.15, -0.2];
      billVisible = false;
    } else if (s.stage === "shredder") {
      role = "worker";
      expr = "shock";
      charPos = [0.12, 1.15, 0.0];
      billVisible = false;
    } else if (s.stage === "twist") {
      role = "citizen";
      expr = "smirk";
      charPos = [0.0, 1.15, 0.0];
      billVisible = true;
      billPos = [0.42, 1.22, 0.12];
      billScale = 0.40;
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

    this.charCtx.clearRect(0, 0, 600, 1000);
    drawChar(this.charCtx, role, f, expr);
    this.charTex.needsUpdate = true;

    if (billVisible) {
      this.billCtx.clearRect(0, 0, 600, 350);
      drawDollarCard(this.billCtx, { stage: s.stage, tilt: billTilt });
      this.billTex.needsUpdate = true;
    }

    if (s.stage === "scanner") {
      const scanX = -0.15 + 0.38 * Math.sin(f * 0.22);
      this.spotLight.color.set("#22d3ee");
      this.spotLight.intensity = 5.0;
      this.spotLight.position.set(scanX, 2.5, -0.7);
      this.spotLight.target.position.set(scanX, 0.8, -0.7);
    } else if (s.stage === "eurion") {
      const isRed = Math.floor(f * 0.4) % 2 === 0;
      this.spotLight.color.set(isRed ? "#ef4444" : "#ffffff");
      this.spotLight.intensity = isRed ? 8.0 : 1.0;
      this.spotLight.position.set(-0.15, 2.8, -0.7);
      this.spotLight.target.position.set(-0.15, 0.8, -0.7);
    } else if (s.stage === "midnight") {
      this.spotLight.color.set("#e0f2fe");
      this.spotLight.intensity = 7.5;
      this.spotLight.position.set(0.1, 4.2, -1.0);
      this.spotLight.target.position.set(0.1, 1.15, -0.2);
    } else if (s.stage === "shredder") {
      const beaconFlash = (Math.sin(f * 0.5) + 1) * 0.5;
      this.spotLight.color.set("#ef4444");
      this.spotLight.intensity = beaconFlash * 4.0;
      this.spotLight.position.set(-0.95, 2.8, -0.9);
      this.spotLight.target.position.set(-0.95, 0.9, -0.9);
    } else {
      this.spotLight.intensity = 0.0;
    }

    return target;
  }
}
