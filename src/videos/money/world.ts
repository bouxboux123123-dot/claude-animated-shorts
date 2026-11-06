import * as THREE from "three";
import {
  buildRoom,
  buildWorkbench,
  buildShelves,
  buildIntaglioPress,
  buildCurrencySheet,
  Actor,
  CharacterSpec,
  LIGHTS,
  TONE,
  CHAR,
  LightMode,
} from "../../engine";
import { shotAt, updateCamera } from "./story";

export class World {
  root: THREE.Group;
  actor: Actor;
  dirLight: THREE.DirectionalLight;
  hemiLight: THREE.HemisphereLight;
  currencySheet: THREE.Mesh;
  pressGroup: THREE.Group;

  private currentSpecKey = "";

  constructor() {
    this.root = new THREE.Group();

    // 1. ARCHITECTURAL ROOM & ENVIRONMENT (Using engine procedural textures & sets)
    buildRoom(this.root, {
      width: 14,
      depth: 12,
      height: 6.5,
      floorType: "wood",
      wallType: "brick",
      ceilingBeams: true,
      window: {
        wall: "back",
        width: 3.6,
        height: 3.0,
        y: 3.6,
        sunbeams: true,
      },
    });

    // 2. FURNITURE & PROPS
    // Craftsman inspection workbench
    buildWorkbench(this.root, {
      x: 0,
      y: 0,
      z: 0,
      width: 2.8,
      depth: 1.3,
      height: 0.95,
      woodTone: "#925b30",
      hasMat: true,
    });

    // Wall storage shelves with cans and paper reams
    buildShelves(this.root, -4.8, 0, -3.8, 2.4, 3.4, 0.65);

    // Heavy 20-ton industrial stamping press
    this.pressGroup = buildIntaglioPress(this.root, 3.2, 0, -1.8);

    // Physical 3D currency sheet resting on the green cutting mat
    this.currencySheet = buildCurrencySheet(this.root, 0, 0.97, 0, 0.9, 0.55);

    // 3. 2D CARTOON ACTOR IN 3D SPACE (3.5 HH, superellipse head, tailored costume, contact shadow)
    this.actor = new Actor(this.root);
    // Positioned behind the workbench
    this.actor.setPosition(0, 0, -0.45);

    // 4. SCENE LIGHTING (Camera-relative sun + ambient)
    this.dirLight = new THREE.DirectionalLight("#fff4e0", 3.2);
    this.dirLight.castShadow = true;
    this.dirLight.shadow.mapSize.width = 2048;
    this.dirLight.shadow.mapSize.height = 2048;
    this.dirLight.shadow.bias = -0.0003;
    this.root.add(this.dirLight);

    this.hemiLight = new THREE.HemisphereLight("#e2e8f0", "#785238", 0.65);
    this.root.add(this.hemiLight);
  }

  update(
    shotId: number,
    f: number,
    camera: THREE.PerspectiveCamera,
    scene: THREE.Scene
  ): THREE.Vector3 {
    const s = shotAt(f);
    const lightMode: LightMode = s.light;
    const lp = LIGHTS[lightMode];

    // 1. Sync two-tone shader uniforms with current light preset
    TONE.uLitCol.value.set(...lp.lit);
    TONE.uShadeCol.value.set(...lp.shade);
    TONE.uShadeLift.value.set(...lp.lift);
    TONE.uLambert.value = lp.lambert;
    TONE.uSideK.value = lp.sideK;
    TONE.uTerm.value = lp.term;

    // 2. Sync character card lighting uniforms
    CHAR.uCharTint.value.set(...lp.charTint);
    CHAR.uCharShade.value = lp.charShade;
    CHAR.uGrad.value = lp.charGrad;
    CHAR.uBodyGrad.value = lp.bodyGrad;
    CHAR.uSideTint.value.set(...lp.sideTint);

    // 3. Update directional light direction & intensity
    this.dirLight.intensity = lp.sunI;
    this.dirLight.color.set(lp.sunCol);
    this.hemiLight.intensity = lp.hemiI;

    // Camera-relative sun position
    const rad = (d: number) => (d * Math.PI) / 180;
    const azRad = rad(lp.az);
    const elRad = rad(lp.el);
    const sunDist = 18;
    this.dirLight.position.set(
      camera.position.x + sunDist * Math.sin(azRad) * Math.cos(elRad),
      camera.position.y + sunDist * Math.sin(elRad),
      camera.position.z + sunDist * Math.cos(azRad) * Math.cos(elRad)
    );
    this.dirLight.target.position.copy(camera.position);
    this.dirLight.target.updateMatrixWorld();

    // 4. Update actor outfit, hair, and expression based on narrative beat
    let spec: CharacterSpec;
    let specKey = "";

    if (s.id === 6) {
      // Inspection beat: Artisan holding magnifying glass loupe examining currency
      specKey = "inspect_loupe";
      spec = {
        outfit: "artisan_vest",
        hair: "comb_over",
        expression: "scheming",
        holdingProp: "magnifying_glass",
      };
    } else if (s.id === 9) {
      // Rogue midnight operator: Suspicious expression
      specKey = "midnight_rogue";
      spec = {
        outfit: "overalls",
        hair: "side_part",
        expression: "suspicious",
      };
    } else if (s.id === 11) {
      // Final payoff twist: Proud banker holding dollar bill at chest level
      specKey = "payoff_banker";
      spec = {
        outfit: "banker_suit",
        hair: "comb_over",
        expression: "happy",
        holdingProp: "bill",
      };
    } else {
      // Standard artisan / craftsman at workbench
      specKey = "standard_artisan";
      spec = {
        outfit: "artisan_vest",
        hair: "comb_over",
        expression: f % 90 < 45 ? "speaking" : "neutral",
      };
    }

    if (specKey !== this.currentSpecKey) {
      this.actor.updateDrawing(spec, specKey);
      this.currentSpecKey = specKey;
    }

    // Orient billboard to camera
    this.actor.lookAtCamera(camera);

    // 5. Currency prop visibility: In shot 11, bill is held in hand; otherwise on table
    this.currencySheet.visible = s.id !== 11;

    // 6. Update camera trajectory
    const target = updateCamera(f, camera);
    return target;
  }
}
