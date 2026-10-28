import React from "react";
import { AbsoluteFill, Html5Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Overview } from "./Overview";
import { Reading } from "./Reading";
import { Review } from "./Review";
import { C } from "./theme";
import type { Timeline } from "./types";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 正文（手帐纸，逐张）→ 词卡复习（有声）→ 全文帧。第一帧就是正文。 */
export const Episode: React.FC<Timeline> = (tl) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const reviewOut = interpolate(t, [tl.overview.start - 0.3, tl.overview.start], [1, 0], CLAMP);
  const overviewIn = interpolate(t, [tl.overview.start - 0.05, tl.overview.start + 0.25], [0, 1], CLAMP);
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {tl.audioSrc ? <Html5Audio src={staticFile(tl.audioSrc)} /> : null}
      {t < tl.review.start + 0.2 ? <Reading tl={tl} t={t} /> : null}
      {t >= tl.review.start - 0.05 && reviewOut > 0 ? (
        <AbsoluteFill style={{ opacity: reviewOut }}>
          <Review tl={tl} t={t} />
        </AbsoluteFill>
      ) : null}
      {overviewIn > 0 ? (
        <AbsoluteFill style={{ opacity: overviewIn, transform: `translateY(${(1 - overviewIn) * 40}px)` }}>
          <Overview tl={tl} />
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
