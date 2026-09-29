import { AbsoluteFill, Html5Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { C } from "../theme";
import type { Timeline } from "../types";
import { Reading } from "./Reading";
import { Summary } from "./Summary";

export const MarkerNotes: React.FC<Timeline> = (props) => {
  const { fps } = useVideoConfig();
  const summaryFrom = Math.round(props.summary.start * fps);
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {props.audioSrc ? <Html5Audio src={staticFile(props.audioSrc)} /> : null}
      <Sequence durationInFrames={summaryFrom + Math.round(0.2 * fps)} layout="none">
        <Reading {...props} />
      </Sequence>
      <Sequence from={summaryFrom} layout="none">
        <Summary {...props} />
      </Sequence>
    </AbsoluteFill>
  );
};
