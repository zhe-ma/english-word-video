import React from "react";
import { AbsoluteFill } from "remotion";
import { Overview } from "./Overview";
import { C, LAYOUT, ZH } from "./theme";
import type { Timeline } from "./types";

/** 封面：纸张上方大标题，下面是全文高亮的手帐纸。 */
export const Cover: React.FC<Timeline> = (tl) => {
  const lines = tl.cover.length ? tl.cover : [tl.title];
  const longest = Math.max(...lines.map((l) => l.length));
  const room = LAYOUT.paperTop - 60 - 110;
  const size = Math.min(128, Math.floor(940 / longest), Math.floor(room / (lines.length * 1.22)));
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Overview tl={tl} showHeader={false} />
      <div style={{ position: "absolute", left: 60, right: 60, top: 110, height: room, display: "flex", flexDirection: "column",
        justifyContent: "center", fontFamily: ZH, fontSize: size, fontWeight: 900, lineHeight: 1.22, color: "#fff", letterSpacing: 2 }}>
        {lines.map((l, k) => (
          <div key={k}>{l}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
