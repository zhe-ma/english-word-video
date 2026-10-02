import React from "react";
import { AbsoluteFill } from "remotion";
import { Footer } from "./Footer";
import { TopLabel } from "./Header";
import { Paper } from "./Paper";
import { C, LAYOUT, ZH } from "./theme";
import type { Timeline } from "./types";

/** 封面：栏目名 + 大标题 + 全文卡片。全部落在抖音安全区内。 */
export const Cover: React.FC<Timeline> = (tl) => {
  const lines = tl.cover.length ? tl.cover : [tl.title];
  const longest = Math.max(...lines.map((l) => l.length));
  const room = LAYOUT.coverCardTop - LAYOUT.coverTitleTop - 28;
  const size = Math.min(76, Math.floor(820 / longest), Math.floor(room / (lines.length * 1.22)));
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{ position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top: LAYOUT.coverLabelTop }}>
        <TopLabel />
      </div>
      <div style={{ position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top: LAYOUT.coverTitleTop,
        fontFamily: ZH, fontSize: size, fontWeight: 600, lineHeight: 1.22, color: C.title, letterSpacing: -0.6 }}>
        {lines.map((l, k) => (
          <div key={k}>{l}</div>
        ))}
      </div>
      <Paper tl={tl} t={null} top={LAYOUT.coverCardTop} bottom={LAYOUT.coverCardBottom} />
      <Footer />
    </AbsoluteFill>
  );
};
