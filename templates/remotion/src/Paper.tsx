import React from "react";
import { FitBox } from "./FitBox";
import { MarkedText } from "./MarkedText";
import { C, LAYOUT, TEXT } from "./theme";
import type { Timeline } from "./types";

const PAD = { top: 44, side: 48, bottom: 40 };

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
      <FitBox height={textH} min={TEXT.min} max={TEXT.max} style={{ flex: "none" }}>
        <MarkedText pages={tl.pages} items={tl.items} t={t} />
      </FitBox>
    </div>
  );
};
