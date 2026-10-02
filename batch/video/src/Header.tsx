import React from "react";
import { C, HEADER_LABEL, LAYOUT, UI, ZH } from "./theme";
import type { Timeline } from "./types";

/** 栏目名：固定写「雅思单词学习」，细字、无底色胶囊。 */
export const TopLabel: React.FC<{ style?: React.CSSProperties }> = ({ style }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: ZH, fontSize: UI.label, fontWeight: 500,
    letterSpacing: 2, lineHeight: 1.15, color: C.onBg, ...style }}>
    <span style={{ width: 10, height: 10, borderRadius: 5, background: C.accent }} />
    {HEADER_LABEL}
  </div>
);

const titleSize = (title: string) => {
  const inner = 1080 - LAYOUT.cardLeft - LAYOUT.cardRight;
  return Math.max(32, Math.min(52, Math.floor(inner / Math.max(title.length, 1))));
};

/** 顶部：栏目名 + 一行标题。标题不换行，避免挡住下面的卡片。 */
export const Header: React.FC<{ tl: Timeline }> = ({ tl }) => (
  <div style={{ position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top: LAYOUT.labelTop }}>
    <TopLabel />
    <div style={{ fontFamily: ZH, color: C.title, fontSize: titleSize(tl.title), fontWeight: 600,
      marginTop: 8, letterSpacing: -0.4, lineHeight: 1.15, whiteSpace: "nowrap" }}>
      {tl.title}
    </div>
  </div>
);
