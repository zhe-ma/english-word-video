import React from "react";
import { FitBox } from "./FitBox";
import { MarkedText } from "./MarkedText";
import { C, LAYOUT, TEXT, ZH } from "./theme";
import type { Timeline } from "./types";

const PAD = { top: 44, side: 34, bottom: 32 };
const SOURCE_H = 48;

/** 手帐纸：网格底纹，全文一页放完，底部一行出处小字。t 为 null 表示全部读完。 */
export const Paper: React.FC<{ tl: Timeline; t: number | null; style?: React.CSSProperties }> = ({ tl, t, style }) => {
  const height = LAYOUT.paperBottom - LAYOUT.paperTop;
  return (
    <div
      style={{
        position: "absolute", left: 40, right: 40, top: LAYOUT.paperTop, height,
        background: `linear-gradient(${C.grid} 2px, transparent 2px) 0 0 / 100% 64px,
          linear-gradient(90deg, ${C.grid} 2px, transparent 2px) 0 0 / 64px 100%, ${C.paper}`,
        borderRadius: 28, padding: `${PAD.top}px ${PAD.side}px ${PAD.bottom}px`, boxShadow: "0 30px 80px rgba(0,0,0,.35)",
        ...style,
      }}
    >
      <FitBox height={height - PAD.top - PAD.bottom - (tl.source ? SOURCE_H : 0)} min={TEXT.min} max={TEXT.max}>
        <MarkedText pages={tl.pages} items={tl.items} t={t} />
      </FitBox>
      {tl.source ? (
        <div style={{ position: "absolute", left: PAD.side, right: PAD.side, bottom: PAD.bottom, fontFamily: ZH,
          fontSize: 26, lineHeight: 1, color: C.muted, fontWeight: 600, textAlign: "right" }}>
          —— {tl.source}
        </div>
      ) : null}
    </div>
  );
};
