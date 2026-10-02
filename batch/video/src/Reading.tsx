import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useVideoConfig } from "remotion";
import { Footer } from "./Footer";
import { Header } from "./Header";
import { Paper } from "./Paper";
import type { Timeline } from "./types";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
/** 入场动画提前开始的秒数：第一帧画面已基本就位，不出现空白首帧。 */
const PREROLL = 0.35;

/** 正文：顶部栏目名和标题，下面一张手帐纸放下全文；读完整体滑出进入词卡。 */
export const Reading: React.FC<{ tl: Timeline; t: number }> = ({ tl, t }) => {
  const { fps } = useVideoConfig();
  const enter = spring({ frame: Math.round((t + PREROLL) * fps), fps, config: { damping: 16, mass: 0.8 } });
  const exit = interpolate(t, [tl.review.start - 0.35, tl.review.start + 0.1], [0, 1], { ...CLAMP, easing: Easing.in(Easing.cubic) });

  return (
    <AbsoluteFill style={{ transform: `translateX(${-1200 * exit}px) rotate(${-6 * exit}deg)`, opacity: 1 - exit * 0.6 }}>
      <Header tl={tl} />
      <Paper tl={tl} t={t} style={{ transform: `translateY(${(1 - enter) * 80}px)`, opacity: enter }} />
      <Footer opacity={enter} />
    </AbsoluteFill>
  );
};
