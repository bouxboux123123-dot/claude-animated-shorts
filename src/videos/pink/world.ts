import * as THREE from "three";
import {
  buildPrisonCorridor,
  buildPinkCell,
  buildBlackboardScene,
  buildWallClock,
  Actor,
  CharacterSpec,
  LIGHTS,
  TONE,
  CHAR,
  LightMode,
} from "../../engine";
import { shotAt, updatePinkCamera } from "./story";
import {
  buildPaintShopWorkshop,
  buildCafeteriaPodC,
  buildImpactCrater,
  buildKnittingScarf,
} from "./detailed_props";
import {
  getPaintingGuardTexture,
  getScientistWorkshopTexture,
  getScientistSwatchTexture,
  getInmate300LandingTexture,
  getInmate300KnittingTexture,
  getInmate300RageTexture,
} from "./detailed_actors";

export class PinkWorld {
  root: THREE.Group;

  // Environment Stages
  corridorGroup: THREE.Group;
  pinkCellGroup: THREE.Group;
  mixBenchGroup: THREE.Group;
  armWrestleGroup: THREE.Group;
  blackboardGroup: THREE.Group;
  clockGroup: THREE.Group;

  // Detailed Stage Props
  impactCrater: THREE.Group;
  knittingScarf: THREE.Group;

  // Actors
  scientist: Actor;
  guard1: Actor;
  guard2: Actor;
  inmate: Actor;

  // Lighting
  dirLight: THREE.DirectionalLight;
  hemiLight: THREE.HemisphereLight;

  private currentSpecKeys: Record<string, string> = {};

  constructor() {
    this.root = new THREE.Group();

    // 1. CORRIDOR STAGE (origin x=0, z=0)
    this.corridorGroup = buildPrisonCorridor(this.root, 3.8, 14, 3.2);

    // 2. BAKER-MILLER PINK CELL STAGE (origin x=0, z=0)
    this.pinkCellGroup = buildPinkCell(this.root, 0, 0, 0, 3.6, 3.6, 3.0);

    // 3. SCIENTIFIC MIX BENCH WORKSHOP STAGE (authentic craftsman oak bench, digital scale, 1-gal WHITE can, memo, sunbeams)
    this.mixBenchGroup = buildPaintShopWorkshop(this.root, 0, 0, 0);

    // 4. DAYROOM / CAFETERIA POD C STAGE (two-tier cell block, blue picnic table, lunch trays, catwalk)
    this.armWrestleGroup = buildCafeteriaPodC(this.root, 0, 0, 0);

    // 5. BLACKBOARD EXPLANATION STAGE
    this.blackboardGroup = buildBlackboardScene(this.root, 0, 0, 0);

    // 6. WALL CLOCK (inside corridor / station)
    this.clockGroup = buildWallClock(this.root, 0, 2.3, -4.5);

    // 7. HERO DETAILED PROPS
    this.impactCrater = buildImpactCrater(1.2);
    this.root.add(this.impactCrater);

    this.knittingScarf = buildKnittingScarf();
    this.root.add(this.knittingScarf);

    // 8. ACTORS
    this.scientist = new Actor(this.root);
    this.guard1 = new Actor(this.root);
    this.guard2 = new Actor(this.root);
    this.inmate = new Actor(this.root);

    // 9. LIGHTING RIG
    this.dirLight = new THREE.DirectionalLight("#fff4e0", 3.0);
    this.dirLight.castShadow = true;
    this.dirLight.shadow.mapSize.width = 2048;
    this.dirLight.shadow.mapSize.height = 2048;
    this.dirLight.shadow.bias = -0.0003;
    this.root.add(this.dirLight);

    this.hemiLight = new THREE.HemisphereLight("#9bb8d9", "#2b3038", 0.6);
    this.root.add(this.hemiLight);
  }

  private setActorSpec(actor: Actor, id: string, spec: CharacterSpec, key: string) {
    if (this.currentSpecKeys[id] !== key) {
      this.currentSpecKeys[id] = key;
      actor.updateDrawing(spec, key);
    }
  }

  update(frame: number, camera: THREE.PerspectiveCamera): THREE.Vector3 {
    const s = shotAt(frame);
    const lightMode: LightMode = s.light;
    const lp = LIGHTS[lightMode];

    // 1. Two-tone shader uniforms
    TONE.uLitCol.value.set(...lp.lit);
    TONE.uShadeCol.value.set(...lp.shade);
    TONE.uShadeLift.value.set(...lp.lift);
    TONE.uLambert.value = lp.lambert;
    TONE.uSideK.value = lp.sideK;
    TONE.uTerm.value = lp.term;

    // 2. Character card uniforms
    CHAR.uCharTint.value.set(...lp.charTint);
    CHAR.uCharShade.value = lp.charShade;
    CHAR.uGrad.value = lp.charGrad;
    CHAR.uBodyGrad.value = lp.bodyGrad;
    CHAR.uSideTint.value.set(...lp.sideTint);

    // 3. Directional light & ambient
    this.dirLight.intensity = lp.sunI;
    this.dirLight.color.set(lp.sunCol);
    this.hemiLight.intensity = lp.hemiI;

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

    // 4. Stage visibility & Actor positioning per shot
    const hideAll = () => {
      this.corridorGroup.visible = false;
      this.pinkCellGroup.visible = false;
      this.mixBenchGroup.visible = false;
      this.armWrestleGroup.visible = false;
      this.blackboardGroup.visible = false;
      this.clockGroup.visible = false;
      this.impactCrater.visible = false;
      this.knittingScarf.visible = false;
      this.scientist.mesh.visible = false;
      this.scientist.blobMesh.visible = false;
      this.guard1.mesh.visible = false;
      this.guard1.blobMesh.visible = false;
      this.guard2.mesh.visible = false;
      this.guard2.blobMesh.visible = false;
      this.inmate.mesh.visible = false;
      this.inmate.blobMesh.visible = false;
    };

    hideAll();

    // Toggle front bars visibility (hide bars for interior framing)
    const frontBars = this.pinkCellGroup.getObjectByName("frontBars");
    if (frontBars) {
      frontBars.visible = (s.stage === "stopwatch_rule" || s.stage === "cell_door" || s.stage === "door_exit");
    }

    const focusPoint = new THREE.Vector3(0, 1.2, 0);

    // Shot stage dispatch
    switch (s.stage) {
      case "corridor": {
        this.corridorGroup.visible = true;

        this.scientist.mesh.visible = true;
        this.scientist.blobMesh.visible = true;
        this.scientist.setPosition(-0.45, 0, 0.4);
        this.setActorSpec(
          this.scientist,
          "sci",
          {
            build: "adult",
            skin: "#ffe0b4",
            outfit: "lab_coat",
            glasses: true,
            hair: "comb_over",
            hairCol: "#94a3b8",
            holdingProp: "clipboard",
            expression: "speaking",
          },
          "sci_clip"
        );

        this.guard1.mesh.visible = true;
        this.guard1.blobMesh.visible = true;
        this.guard1.setPosition(0.5, 0, 0.3);
        this.setActorSpec(
          this.guard1,
          "g1",
          {
            build: "adult",
            skin: "#f6b988",
            outfit: "guard",
            headwear: "guard_peaked",
            expression: "deadpan",
          },
          "g1_idle"
        );

        focusPoint.set(0, 1.25, 0.35);
        break;
      }

      case "mix_bench": {
        // Detailed Scientific Paint Shop Workshop
        this.mixBenchGroup.visible = true;

        this.scientist.mesh.visible = true;
        this.scientist.blobMesh.visible = true;
        this.scientist.setPosition(0.35, 0, -0.4);
        this.scientist.mat.map = getScientistWorkshopTexture();
        this.scientist.mat.needsUpdate = true;
        this.currentSpecKeys["sci"] = "sci_workshop_custom";

        focusPoint.set(0, 1.15, 0);
        break;
      }

      case "paint_wall": {
        // Inside Pink Cell repainting with roller & Pantone swatch
        this.pinkCellGroup.visible = true;

        this.guard1.mesh.visible = true;
        this.guard1.blobMesh.visible = true;
        this.guard1.setPosition(-0.5, 0, -0.3);
        this.guard1.mat.map = getPaintingGuardTexture();
        this.guard1.mat.needsUpdate = true;
        this.currentSpecKeys["g1"] = "g1_painting_custom";

        this.scientist.mesh.visible = true;
        this.scientist.blobMesh.visible = true;
        this.scientist.setPosition(0.6, 0, 0.0);
        this.scientist.mat.map = getScientistSwatchTexture();
        this.scientist.mat.needsUpdate = true;
        this.currentSpecKeys["sci"] = "sci_swatch_custom";

        focusPoint.set(0.05, 1.25, -0.1);
        break;
      }

      case "guards_corridor": {
        this.corridorGroup.visible = true;

        this.guard1.mesh.visible = true;
        this.guard1.blobMesh.visible = true;
        this.guard1.setPosition(-0.4, 0, 0);
        this.setActorSpec(
          this.guard1,
          "g1",
          {
            build: "adult",
            skin: "#f6b988",
            outfit: "guard",
            headwear: "guard_peaked",
            expression: "smile",
          },
          "g1_smirk"
        );

        this.guard2.mesh.visible = true;
        this.guard2.blobMesh.visible = true;
        this.guard2.setPosition(0.4, 0, 0);
        this.setActorSpec(
          this.guard2,
          "g2",
          {
            build: "skinny",
            skin: "#ecd0b6",
            outfit: "guard",
            headwear: "guard_peaked",
            expression: "smile",
          },
          "g2_skinny_smirk"
        );

        focusPoint.set(0, 1.3, 0);
        break;
      }

      case "stopwatch_rule":
      case "cell_door": {
        this.corridorGroup.visible = true;

        this.scientist.mesh.visible = true;
        this.scientist.blobMesh.visible = true;
        this.scientist.setPosition(0, 0, 0);
        this.setActorSpec(
          this.scientist,
          "sci",
          {
            build: "adult",
            skin: "#ffe0b4",
            outfit: "lab_coat",
            glasses: true,
            hair: "comb_over",
            hairCol: "#94a3b8",
            holdingProp: "stopwatch",
            expression: "speaking",
          },
          "sci_stopwatch"
        );

        focusPoint.set(0, 1.35, 0);
        break;
      }

      case "pink_cell_inmate": {
        // Inmate entry with impact crater & laughing expression
        this.pinkCellGroup.visible = true;
        this.impactCrater.visible = true;
        this.impactCrater.position.set(0, 0.015, 0);

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0, 0, 0);
        this.inmate.mat.map = getInmate300LandingTexture();
        this.inmate.mat.needsUpdate = true;
        this.currentSpecKeys["inm"] = "inm_landing_custom";

        focusPoint.set(0, 1.45, 0);
        break;
      }

      case "door_exit": {
        this.corridorGroup.visible = true;

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0, -0.08, 0.2);
        this.setActorSpec(
          this.inmate,
          "inm",
          {
            build: "stout",
            skin: "#e9c8ae",
            outfit: "inmate_orange",
            tattoos: true,
            hair: null,
            expression: "deadpan",
          },
          "inm_slumped"
        );

        focusPoint.set(0, 1.3, 0.2);
        break;
      }

      case "arm_wrestle": {
        // Cafeteria POD C multi-tier prison block
        this.armWrestleGroup.visible = true;

        this.guard2.mesh.visible = true;
        this.guard2.blobMesh.visible = true;
        this.guard2.setPosition(-0.65, 0.22, 0);
        this.setActorSpec(
          this.guard2,
          "g2",
          {
            build: "skinny",
            skin: "#ecd0b6",
            outfit: "guard",
            headwear: "guard_peaked",
            expression: frame >= 1040 ? "smile" : "scheming",
          },
          frame >= 1040 ? "g2_slam_win" : "g2_slam_pull"
        );

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0.65, 0.22, 0);
        this.setActorSpec(
          this.inmate,
          "inm",
          {
            build: "stout",
            skin: "#e9c8ae",
            outfit: "inmate_orange",
            tattoos: true,
            hair: null,
            expression: frame >= 1040 ? "shocked" : "deadpan",
          },
          frame >= 1040 ? "inm_arm_shock" : "inm_arm_lose"
        );

        focusPoint.set(0, 0.95, 0);
        break;
      }

      case "reaction": {
        this.armWrestleGroup.visible = true;

        this.guard2.mesh.visible = true;
        this.guard2.blobMesh.visible = true;
        this.guard2.setPosition(-0.55, 0.22, 0);
        this.setActorSpec(
          this.guard2,
          "g2",
          {
            build: "skinny",
            skin: "#ecd0b6",
            outfit: "guard",
            headwear: "guard_peaked",
            expression: "shocked",
          },
          "g2_shock"
        );

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0.55, 0.22, 0);
        this.setActorSpec(
          this.inmate,
          "inm",
          {
            build: "stout",
            skin: "#e9c8ae",
            outfit: "inmate_orange",
            tattoos: true,
            hair: null,
            expression: "shocked",
          },
          "inm_shock"
        );

        focusPoint.set(0, 1.15, 0);
        break;
      }

      case "truckload_montage": {
        this.corridorGroup.visible = true;

        this.guard1.mesh.visible = true;
        this.guard1.blobMesh.visible = true;
        this.guard1.setPosition(0, 0, 0);
        this.guard1.mat.map = getPaintingGuardTexture();
        this.guard1.mat.needsUpdate = true;
        this.currentSpecKeys["g1"] = "g1_painting_custom";

        focusPoint.set(0, 1.2, 0);
        break;
      }

      case "night_station": {
        this.corridorGroup.visible = true;
        this.clockGroup.visible = true;
        this.clockGroup.position.set(0, 2.2, -1.8);

        this.guard1.mesh.visible = true;
        this.guard1.blobMesh.visible = true;
        this.guard1.setPosition(0, 0, -0.4);
        this.setActorSpec(
          this.guard1,
          "g1",
          {
            build: "adult",
            skin: "#f6b988",
            outfit: "guard",
            headwear: "guard_peaked",
            expression: "deadpan",
          },
          "g1_asleep"
        );

        focusPoint.set(0, 1.9, -1.0);
        break;
      }

      case "night_quiet": {
        // Inmate sitting quietly knitting pink scarf
        this.pinkCellGroup.visible = true;
        this.knittingScarf.visible = true;
        this.knittingScarf.position.set(0.35, 0, 0.4);

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0.35, 0.25, 0.4);
        this.inmate.mat.map = getInmate300KnittingTexture();
        this.inmate.mat.needsUpdate = true;
        this.currentSpecKeys["inm"] = "inm_knitting_custom";

        focusPoint.set(0.35, 1.1, 0.4);
        break;
      }

      case "night_pacing": {
        this.pinkCellGroup.visible = true;

        const paceX = Math.sin((frame - 1437) * 0.28) * 0.75;
        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(paceX, 0, 0);
        this.setActorSpec(
          this.inmate,
          "inm",
          {
            build: "stout",
            skin: "#e9c8ae",
            outfit: "inmate_orange",
            tattoos: true,
            hair: null,
            expression: "scheming",
          },
          "inm_pacing"
        );

        focusPoint.set(paceX, 1.15, 0);
        break;
      }

      case "bench_rage": {
        // Gripping welded bench, violent rage & snapped needles
        this.pinkCellGroup.visible = true;
        this.knittingScarf.visible = true;
        this.knittingScarf.position.set(0.35, 0, 0.4);

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0.35, 0, 0.4);
        this.inmate.mat.map = getInmate300RageTexture();
        this.inmate.mat.needsUpdate = true;
        this.currentSpecKeys["inm"] = "inm_rage_custom";

        focusPoint.set(0.35, 1.15, 0.4);
        break;
      }

      case "blackboard_chart": {
        this.blackboardGroup.visible = true;
        this.blackboardGroup.position.set(0, 0, 0);

        this.scientist.mesh.visible = true;
        this.scientist.blobMesh.visible = true;
        this.scientist.setPosition(0.85, 0, -0.6);
        this.setActorSpec(
          this.scientist,
          "sci",
          {
            build: "adult",
            skin: "#ffe0b4",
            outfit: "lab_coat",
            glasses: true,
            hair: "comb_over",
            hairCol: "#94a3b8",
            holdingProp: "clipboard",
            expression: "speaking",
          },
          "sci_blackboard"
        );

        focusPoint.set(0, 1.45, 0);
        break;
      }

      case "rage_payoff": {
        // Finale: glowing red eyes, red lightning fury aura, snapped needles
        this.pinkCellGroup.visible = true;

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0, 0, 0);
        this.inmate.mat.map = getInmate300RageTexture();
        this.inmate.mat.needsUpdate = true;
        this.currentSpecKeys["inm"] = "inm_rage_payoff_custom";

        focusPoint.set(0, 1.35, 0);
        break;
      }
    }

    // Billboard characters toward camera
    if (this.scientist.mesh.visible) this.scientist.lookAtCamera(camera);
    if (this.guard1.mesh.visible) this.guard1.lookAtCamera(camera);
    if (this.guard2.mesh.visible) this.guard2.lookAtCamera(camera);
    if (this.inmate.mesh.visible) this.inmate.lookAtCamera(camera);

    return focusPoint;
  }
}
