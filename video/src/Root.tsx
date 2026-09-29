import { Composition } from "remotion";
import "./fonts";
import { MarkerNotes } from "./MarkerNotes";
import sample from "./sample.json";
import type { Timeline } from "./types";

export const Root: React.FC = () => (
  <Composition
    id="MarkerNotes"
    component={MarkerNotes}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={sample.durationInFrames}
    defaultProps={sample as Timeline}
    calculateMetadata={({ props }) => ({ durationInFrames: props.durationInFrames, fps: props.fps })}
  />
);
