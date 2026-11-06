import React, { useMemo, useEffect } from "react";
import * as THREE from "three";
import { AbsoluteFill, useCurrentFrame, staticFile, Audio } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";
import { World } from "./world";
import { InkPass, noInkFallback } from "./ink";
import { LensBlur } from "./lensblur";
import { GradeEffect, GRADES, GRADE_STRENGTH, gradeFor } from "./grade";
import { TOTAL, FLASH_AT, shotAt, dofAt } from "./story";
import { KineticCaptions } from "./KineticCaptions";

export const MONEY_FRAMES = TOTAL;

const makeBloom = () => {
  return new BloomEffect({
    blendFunction: BlendFunction.ADD,
    intensity: 0.45,
    luminanceThreshold: 0.95,
    luminanceSmoothing: 0.25,
    mipmapBlur: true,
    levels: 6,
    radius: 0.5,
  });
};

const fwd = new THREE.Vector3(),
  fpt = new THREE.Vector3();

const Inner: React.FC = () => {
  const f = useCurrentFrame();
  const { camera, scene } = useThree();
  const s = shotAt(f);

  const world = useMemo(() => new World(), []);
  const target = useMemo(() => new THREE.Vector3(), []);

  const fx = useMemo(
    () => ({
      ink: new InkPass(scene, camera as THREE.PerspectiveCamera),
      lens: new LensBlur({ maxCoC: 18, nearScale: 1.1 }),
      bloom: makeBloom(),
      tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
      grade: new GradeEffect(GRADES.day, GRADE_STRENGTH.day),
    }),
    [camera, scene]
  );

  useEffect(() => () => fx.ink.dispose(), [fx]);

  const cam = camera as THREE.PerspectiveCamera;
  target.copy(world.update(s.id, f, cam, scene));
  noInkFallback(world.root);

  // Autofocus depth of field
  const d = dofAt(f);
  cam.getWorldDirection(fwd);
  if (d.focus) fpt.set(...d.focus(f));
  else fpt.copy(target);
  fx.lens.focus = Math.max(0.3, fpt.sub(cam.position).dot(fwd));
  fx.lens.cInf = d.cInf;

  // Dynamic color management: switch grade per narrative beat
  gradeFor(fx.grade, s.light);

  return (
    <>
      <primitive object={world.root} dispose={null} />
      <EffectComposer multisampling={4}>
        <primitive object={fx.ink} dispose={null} />
        <primitive object={fx.lens.pre} dispose={null} />
        <primitive object={fx.lens.main} dispose={null} />
        <primitive object={fx.bloom} dispose={null} />
        <primitive object={fx.tone} dispose={null} />
        <primitive object={fx.grade} dispose={null} />
      </EffectComposer>
    </>
  );
};

export const MoneyShort: React.FC = () => {
  const f = useCurrentFrame();
  const s = shotAt(f);

  // 4-frame white flash after hook (frame 91 to 94)
  const isFlash = f >= FLASH_AT && f < FLASH_AT + 4;
  const flashAlpha = isFlash ? 1 - (f - FLASH_AT) / 4 : 0;

  const bgCol =
    s.light === "midnight"
      ? "#080c14"
      : s.light === "alert"
      ? "#1a0808"
      : "#0f172a";

  return (
    <AbsoluteFill style={{ backgroundColor: bgCol }}>
      <ThreeCanvas
        width={1080}
        height={1920}
        shadows
        gl={{
          antialias: false,
          stencil: false,
          powerPreference: "high-performance",
          toneMappingExposure: 1.0,
        }}
        camera={{ fov: 40, near: 0.2, far: 500 }}
      >
        <Inner />
      </ThreeCanvas>

      {/* Kinetic Subtitles positioned at y = 0.67 H */}
      <KineticCaptions />

      {/* Hook transition flash */}
      {isFlash ? (
        <AbsoluteFill
          style={{
            backgroundColor: "#ffffff",
            opacity: flashAlpha,
            pointerEvents: "none",
          }}
        />
      ) : null}

      {/* Master Audio Track (Voice + Ducked March Bed + SFX) */}
      <Audio src={staticFile("mix.wav")} />
    </AbsoluteFill>
  );
};
