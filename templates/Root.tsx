import React from "react";
import { Composition, Still } from "remotion";
import { Cover } from "./Cover";
import { Episode } from "./Episode";
import "./fonts";
import sample from "./sample.json";
import type { Timeline } from "./types";

const props = sample as Timeline;

export const Root: React.FC = () => (
  <>
    <Composition
      id="Episode"
      component={Episode}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={props.durationInFrames}
      defaultProps={props}
      calculateMetadata={({ props: p }) => ({ durationInFrames: p.durationInFrames, fps: p.fps })}
    />
    <Still id="Cover" component={Cover} width={1080} height={1920} defaultProps={props} />
  </>
);
