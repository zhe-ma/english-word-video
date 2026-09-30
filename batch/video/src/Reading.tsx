import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useVideoConfig } from "remotion";
import { FocusCard } from "./FocusCard";
import { Header } from "./Header";
import { Paper } from "./Paper";
import { LAYOUT, ZH } from "./theme";
import type { Timeline } from "./types";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
/** 入场动画提前开始的秒数：第一帧画面已基本就位，不出现空白首帧。 */
const PREROLL = 0.35;

/** 学习项的每次出现，按时间排序。 */
export function occurrences(tl: Timeline) {
  const out: { i: number; start: number }[] = [];
  for (const p of tl.pages) for (const tk of p.tokens) if ("i" in tk && tk.start !== undefined) out.push({ i: tk.i, start: tk.start });
  return out.sort((a, b) => a.start - b.start);
}

/** 正文：顶部标题和聚焦卡，下面一张手帐纸放下全文；读完整体滑出进入词卡。 */
export const Reading: React.FC<{ tl: Timeline; t: number }> = ({ tl, t }) => {
  const { fps } = useVideoConfig();
  const occ = occurrences(tl);
  const current = occ.filter((o) => t >= o.start).pop() ?? null;
  const learned = new Set(occ.filter((o) => t >= o.start).map((o) => o.i)).size;
  const enter = spring({ frame: Math.round((t + PREROLL) * fps), fps, config: { damping: 16, mass: 0.8 } });
  const exit = interpolate(t, [tl.review.start - 0.35, tl.review.start + 0.1], [0, 1], { ...CLAMP, easing: Easing.in(Easing.cubic) });

  return (
    <AbsoluteFill style={{ transform: `translateX(${-1200 * exit}px) rotate(${-6 * exit}deg)`, opacity: 1 - exit * 0.6 }}>
      <Header tl={tl} learned={learned} />
      <FocusCard items={tl.items} current={current} audioSrc={tl.audioSrc} />
      <Paper tl={tl} t={t} style={{ transform: `translateY(${(1 - enter) * 160}px)`, opacity: enter }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: LAYOUT.hintTop, textAlign: "center", color: "#fff",
        fontFamily: ZH, fontSize: 32, opacity: 0.6 }}>
        {tl.hint}
      </div>
    </AbsoluteFill>
  );
};
