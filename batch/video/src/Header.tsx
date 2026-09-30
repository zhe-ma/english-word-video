import React from "react";
import { C, EN, HL, LAYOUT, ZH } from "./theme";
import type { Timeline } from "./types";

/** 顶部：Vol 徽章、系列 · 级别、标题、学习项进度条。learned 为已读到的学习项数。 */
export const Header: React.FC<{ tl: Timeline; learned: number }> = ({ tl, learned }) => (
  <div style={{ position: "absolute", left: 60, right: 60, top: LAYOUT.headerTop, color: "#fff", fontFamily: ZH }}>
    <div style={{ display: "flex", alignItems: "center", gap: 18, fontSize: 30, fontWeight: 500, opacity: 0.85 }}>
      {tl.vol ? (
        <span style={{ background: "#fff", color: C.bg, borderRadius: 12, padding: "2px 14px", fontWeight: 800, fontFamily: EN }}>
          Vol.{tl.vol}
        </span>
      ) : null}
      {tl.series} · {tl.level}
    </div>
    <div style={{ fontSize: tl.title.length > 14 ? 54 : 62, fontWeight: 800, marginTop: 12, letterSpacing: 2, lineHeight: 1.25,
      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
      {tl.title}
    </div>
    <div style={{ display: "flex", gap: 14, marginTop: 18 }}>
      {tl.items.map((w, i) => (
        <i key={i} style={{ width: tl.items.length > 8 ? 52 : 60, height: 12, borderRadius: 6,
          background: i < learned ? HL[w.color] : "rgba(255,255,255,.18)" }} />
      ))}
    </div>
  </div>
);
