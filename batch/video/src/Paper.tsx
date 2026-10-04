import React from "react";
import { FitBox } from "./FitBox";
import { MarkedText } from "./MarkedText";
import { C, LAYOUT, TEXT } from "./theme";
import type { Page, Timeline } from "./types";

const PAD = { top: 44, side: 48, bottom: 40 };

/** 朗读时只留正在说的那一句，避免第一帧铺满整段。全文帧和封面仍展示全部。 */
const spokenPage = (pages: Page[], t: number) => {
  if (!pages.length) return null;
  if (t < pages[0].start) return pages[0];
  for (let i = pages.length - 1; i >= 0; i--) {
    if (t >= pages[i].start) return pages[i];
  }
  return pages[0];
};

/** 正文卡片：只放正文。提示语在卡片外面。 */
export const Paper: React.FC<{
  tl: Timeline;
  t: number | null;
  top?: number;
  bottom?: number;
  style?: React.CSSProperties;
}> = ({ tl, t, top = LAYOUT.cardTop, bottom = LAYOUT.cardBottom, style }) => {
  const height = bottom - top;
  const textH = height - PAD.top - PAD.bottom;
  const focus = t === null ? null : spokenPage(tl.pages, t);
  const pages = focus ? [focus] : tl.pages;
  return (
    <div
      style={{
        position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top, height,
        background: C.card, borderRadius: C.radius, boxSizing: "border-box",
        border: `1px solid ${C.line}`,
        boxShadow: C.shadow,
        padding: `${PAD.top}px ${PAD.side}px ${PAD.bottom}px`,
        display: "flex", flexDirection: "column",
        ...style,
      }}
    >
      <FitBox
        key={focus ? focus.start : "all"}
        height={textH}
        min={TEXT.min}
        max={focus ? 2.4 : TEXT.max}
        style={{ flex: "none", display: "flex", alignItems: "center" }}
      >
        <MarkedText pages={pages} items={tl.items} t={focus ? null : t} />
      </FitBox>
    </div>
  );
};
