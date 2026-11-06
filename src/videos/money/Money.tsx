import React, { useMemo, useEffect } from "react";
import * as THREE from "three";
import { AbsoluteFill, useCurrentFrame, staticFile, Audio } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";

import { World } from "./world";
import {
  InkPass,
  noInkFallback,
  LensBlur,
  GradeEffect,
  GRADES,
  GRADE_STRENGTH,
  gradeFor,
  KineticCaptions,
} from "../../engine";
import { TOTAL, FLASH_AT, shotAt } from "./story";
import wordsData from "./words.json";

export const MONEY_FRAMES = TOTAL;

const makeBloom = () => {
  return new BloomEffect({
    blendFunction: BlendFunction.ADD,
    intensity: 0.35,
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
      lens: new LensBlur({ maxCoC: 16, nearScale: 1.1 }),
      bloom: makeBloom(),
      tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
      grade: new GradeEffect(GRADES.workshop, GRADE_STRENGTH.workshop),
    }),
    [camera, scene]
  );

  useEffect(() => () => fx.ink.dispose(), [fx]);

  const cam = camera as THREE.PerspectiveCamera;
  target.copy(world.update(s.id, f, cam, scene));
  noInkFallback(world.root);

  // Autofocus depth of field on focal target
  cam.getWorldDirection(fwd);
  fpt.copy(target);
  fx.lens.focus = Math.max(0.5, fpt.sub(cam.position).dot(fwd));
  fx.lens.cInf = s.dofCoC ?? 8;

  // Grade preset per light mode
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
  const flash = f >= FLASH_AT && f < FLASH_AT + 3;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      <ThreeCanvas
        width={1080}
        height={1920}
        camera={{ fov: 38, near: 0.1, far: 200, position: [0, 1.4, 3.8] }}
        gl={{
          antialias: true,
          toneMapping: THREE.NoToneMapping,
        }}
      >
        <Inner />
      </ThreeCanvas>

      {/* Standardized kinetic word-pop subtitles locked to y = 0.67 H */}
      <KineticCaptions words={wordsData} yPercent={0.67} fontSize={56} strokeWidth={6} />

      {/* Master Soundtrack */}
      <Audio src={staticFile("mix.wav")} />

      {/* Dramatic narrative flash */}
      {flash && (
        <AbsoluteFill
          style={{
            backgroundColor: "#ffffff",
            opacity: 0.9,
            pointerEvents: "none",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
