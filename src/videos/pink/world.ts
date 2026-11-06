import * as THREE from "three";
import {
  buildPrisonCorridor,
  buildPinkCell,
  buildArmWrestlingTable,
  buildBlackboardScene,
  buildWallClock,
  buildWorkbench,
  makeMaterial,
  metalPlates,
  rep,
  Actor,
  CharacterSpec,
  LIGHTS,
  TONE,
  CHAR,
  LightMode,
} from "../../engine";
import { shotAt, updatePinkCamera } from "./story";

export class PinkWorld {
  root: THREE.Group;

  // Environment Stages
  corridorGroup: THREE.Group;
  pinkCellGroup: THREE.Group;
  mixBenchGroup: THREE.Group;
  armWrestleGroup: THREE.Group;
  blackboardGroup: THREE.Group;
  clockGroup: THREE.Group;

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

    // 2. BAKER-MILLER PINK CELL STAGE (offset at x=10)
    this.pinkCellGroup = buildPinkCell(this.root, 10, 0, 0, 3.6, 3.6, 3.0);

    // 3. MIX BENCH STAGE (offset at x=-10)
    this.mixBenchGroup = new THREE.Group();
    this.mixBenchGroup.position.set(-10, 0, 0);
    buildWorkbench(this.mixBenchGroup, {
      x: 0,
      y: 0,
      z: 0,
      width: 2.4,
      depth: 1.2,
      height: 0.9,
      woodTone: "#475569",
      hasMat: false,
    });
    // Paint gallon can
    const tinMat = makeMaterial("paint_can_mat", rep(metalPlates("tin_can", "#cbd5e1"), 1, 1));
    const paintBucket = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.22, 0.45, 18), tinMat);
    paintBucket.position.set(0.2, 1.12, 0);
    paintBucket.castShadow = true;
    this.mixBenchGroup.add(paintBucket);
    // Beaker with bright red liquid
    const redMat = new THREE.MeshBasicMaterial({ color: 0xdc2626 });
    const beaker = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.24, 14), redMat);
    beaker.position.set(-0.25, 1.02, 0.1);
    this.mixBenchGroup.add(beaker);
    this.root.add(this.mixBenchGroup);

    // 4. ARM WRESTLING DAYROOM STAGE (offset at x=20)
    this.armWrestleGroup = buildArmWrestlingTable(this.root, 20, 0, 0);

    // 5. BLACKBOARD EXPLANATION STAGE (offset at x=-20)
    this.blackboardGroup = buildBlackboardScene(this.root, -20, 0, 0);

    // 6. WALL CLOCK (inside corridor / station)
    this.clockGroup = buildWallClock(this.root, 0, 2.3, -4.5);

    // 7. ACTORS
    this.scientist = new Actor(this.root);
    this.guard1 = new Actor(this.root);
    this.guard2 = new Actor(this.root);
    this.inmate = new Actor(this.root);

    // 8. LIGHTING RIG
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

    const focusPoint = new THREE.Vector3(0, 1.2, 0);

    // Shot stage dispatch
    switch (s.stage) {
      case "corridor": {
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);

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
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);
        this.mixBenchGroup.visible = true;
        this.mixBenchGroup.position.set(0, 0, 0);

        this.scientist.mesh.visible = true;
        this.scientist.blobMesh.visible = true;
        this.scientist.setPosition(0, 0, -0.45);
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
            expression: "scheming",
          },
          "sci_mix"
        );

        focusPoint.set(0, 1.1, 0);
        break;
      }

      case "paint_wall": {
        this.pinkCellGroup.visible = true;
        this.pinkCellGroup.position.set(0, 0, 0);

        this.guard1.mesh.visible = true;
        this.guard1.blobMesh.visible = true;
        this.guard1.setPosition(-0.55, 0, -0.2);
        this.setActorSpec(
          this.guard1,
          "g1",
          {
            build: "adult",
            skin: "#f6b988",
            outfit: "guard",
            headwear: "guard_peaked",
            holdingProp: "paint_roller",
            expression: "deadpan",
          },
          "g1_roller"
        );

        this.scientist.mesh.visible = true;
        this.scientist.blobMesh.visible = true;
        this.scientist.setPosition(0.65, 0, 0.1);
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
            expression: "scheming",
          },
          "sci_clip_wall"
        );

        focusPoint.set(0, 1.25, 0);
        break;
      }

      case "guards_corridor": {
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);

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
            build: "skinny", // skinny guard
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
        this.corridorGroup.position.set(0, 0, 0);

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
        this.pinkCellGroup.visible = true;
        this.pinkCellGroup.position.set(0, 0, 0);

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0, 0, 0);
        this.setActorSpec(
          this.inmate,
          "inm",
          {
            build: "stout",
            skin: "#e9c8ae",
            outfit: "inmate_orange",
            tattoos: true,
            hair: null,
            expression: "smile", // Cocky laughing
          },
          "inm_laugh"
        );

        focusPoint.set(0, 1.45, 0);
        break;
      }

      case "door_exit": {
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        // Slumped down 15%
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
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);
        this.armWrestleGroup.visible = true;
        this.armWrestleGroup.position.set(0, 0, 0);

        // Guard 2 (skinny) slamming inmate hand down
        this.guard2.mesh.visible = true;
        this.guard2.blobMesh.visible = true;
        this.guard2.setPosition(-0.9, 0, 0);
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
        this.inmate.setPosition(0.9, 0, 0);
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
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);
        this.armWrestleGroup.visible = true;
        this.armWrestleGroup.position.set(0, 0, 0);

        this.guard2.mesh.visible = true;
        this.guard2.blobMesh.visible = true;
        this.guard2.setPosition(-0.55, 0, 0);
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
        this.inmate.setPosition(0.55, 0, 0);
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

        focusPoint.set(0, 1.25, 0);
        break;
      }

      case "truckload_montage": {
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);

        this.guard1.mesh.visible = true;
        this.guard1.blobMesh.visible = true;
        this.guard1.setPosition(0, 0, 0);
        this.setActorSpec(
          this.guard1,
          "g1",
          {
            build: "adult",
            skin: "#f6b988",
            outfit: "guard",
            headwear: "guard_peaked",
            holdingProp: "paint_roller",
            expression: "smile",
          },
          "g1_rolling_many"
        );

        focusPoint.set(0, 1.2, 0);
        break;
      }

      case "night_station": {
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);
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
        this.pinkCellGroup.visible = true;
        this.pinkCellGroup.position.set(0, 0, 0);

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        // Sitting quietly on bunk bed
        this.inmate.setPosition(-0.95, 0.45, 0);
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
          "inm_sitting_still"
        );

        focusPoint.set(-0.95, 1.1, 0);
        break;
      }

      case "night_pacing": {
        this.pinkCellGroup.visible = true;
        this.pinkCellGroup.position.set(0, 0, 0);

        // Pacing back and forth
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
        this.pinkCellGroup.visible = true;
        this.pinkCellGroup.position.set(0, 0, 0);

        // Gripping welded bench, violent rage
        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0.8, 0, 0.4);
        this.setActorSpec(
          this.inmate,
          "inm",
          {
            build: "stout",
            skin: "#e9c8ae",
            outfit: "inmate_orange",
            tattoos: true,
            hair: null,
            expression: "shocked", // Eyes bulging wide
          },
          "inm_bench_rage"
        );

        focusPoint.set(0.8, 1.15, 0.4);
        break;
      }

      case "blackboard_chart": {
        this.corridorGroup.visible = true;
        this.corridorGroup.position.set(0, 0, 0);
        this.blackboardGroup.visible = true;
        this.blackboardGroup.position.set(-0.2, 0, -1.8);

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
        this.pinkCellGroup.visible = true;
        this.pinkCellGroup.position.set(0, 0, 0);

        this.inmate.mesh.visible = true;
        this.inmate.blobMesh.visible = true;
        this.inmate.setPosition(0, 0, 0);
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
          "inm_rage_payoff"
        );

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
