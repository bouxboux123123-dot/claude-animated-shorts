import React from "react";
import { Composition } from "remotion";
import { MoneyShort, MONEY_FRAMES } from "./videos/money/Money";
import { MoneyScratchShort, SCRATCH_FRAMES } from "./videos/moneyscratch/MoneyScratch";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="MoneyShort"
        component={MoneyShort}
        durationInFrames={MONEY_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="MoneyScratch"
        component={MoneyScratchShort}
        durationInFrames={SCRATCH_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
