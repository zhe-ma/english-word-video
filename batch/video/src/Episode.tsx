import React from "react";
import { AbsoluteFill, Html5Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Stage } from "./stage/Stage";
import type { Timeline } from "./types";

/** 开头提示音，词卡落地时一声重击。正文跟着配音一句句闪。 */
export const Episode: React.FC<Timeline> = (tl) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{ background: "#000000" }}>
      {tl.audioSrc ? <Html5Audio src={staticFile(tl.audioSrc)} /> : null}
      <Sequence from={Math.round((tl.pages[0]?.start ?? 1) * fps)} durationInFrames={Math.round(0.4 * fps)}>
        <Html5Audio src={staticFile("sfx/ding.wav")} volume={0.5} />
      </Sequence>
      <Sequence from={Math.round(tl.review.start * fps)} durationInFrames={Math.round(0.55 * fps)}>
        <Html5Audio src={staticFile("sfx/boom.wav")} volume={0.72} />
      </Sequence>
      <Stage tl={tl} t={t} />
    </AbsoluteFill>
  );
};
