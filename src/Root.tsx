import React from "react";
import { Composition } from "remotion";
import { MoneyShort, MONEY_FRAMES } from "./videos/money/Money";

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
        component={MoneyShort}
        durationInFrames={MONEY_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
