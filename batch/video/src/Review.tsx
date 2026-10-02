import React from "react";
import { AbsoluteFill, interpolate, spring, useVideoConfig } from "remotion";
import { Footer } from "./Footer";
import { TopLabel } from "./Header";
import { C, EN, IPA_FONT, LAYOUT, ZH } from "./theme";
import type { Entry, Timeline } from "./types";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 词卡复习：学习项双列卡片，随音频逐张点亮（先读英文，再读中文释义）。 */
export const Review: React.FC<{ tl: Timeline; t: number }> = ({ tl, t }) => {
  const { fps } = useVideoConfig();
  const { items } = tl;
  const local = t - tl.review.start;
  const head = spring({ frame: Math.round(local * fps), fps, config: { damping: 18, mass: 0.8 } });
  const entries = new Map<number, Entry>(tl.review.groups.flatMap((g) => g.entries.map((e) => [e.i, e] as const)));
  const activeAt = (e?: Entry) => (e ? interpolate(t, [e.start - 0.15, e.start, e.end + 0.2, e.end + 0.4], [0, 1, 1, 0], CLAMP) : 0);
  const rows = Math.ceil(items.length / 2);
  const gap = 16;
  const cardsTop = LAYOUT.cardTop;
  const avail = LAYOUT.cardBottom - cardsTop;
  const rowH = Math.floor((avail - gap * (rows - 1)) / rows);
  const compact = rowH < 230;

  return (
    <AbsoluteFill style={{ fontFamily: ZH }}>
      <div style={{ position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top: LAYOUT.labelTop,
        color: C.title, opacity: head, transform: `translateY(${(1 - head) * 16}px)` }}>
        <TopLabel style={{ marginBottom: 16 }} />
        <div style={{ fontSize: 48, fontWeight: 600, letterSpacing: -0.4, lineHeight: 1.15 }}>
          今日词卡
          <span style={{ marginLeft: 14, fontSize: 28, fontWeight: 500, color: C.tertiary }}>{items.length}</span>
        </div>
      </div>

      <div style={{ position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top: cardsTop,
        display: "grid", gridTemplateColumns: "1fr 1fr", gap, alignContent: "start" }}>
        {items.map((w, i) => {
          const e = entries.get(i);
          const s = spring({ frame: Math.round((local - 0.2 - i * 0.05) * fps), fps, config: { damping: 16, mass: 0.7 } });
          const on = activeAt(e);
          const zhOn = e ? interpolate(t, [e.enEnd, e.enEnd + 0.15], [0, 1], CLAMP) * on : 0;
          const enSize = Math.min(compact ? 30 : 36, Math.floor(340 / Math.max(6, w.en.length * 0.58)));
          return (
            <div key={i} style={{ background: C.card, borderRadius: C.radius, padding: compact ? "14px 18px 12px" : "26px 24px 20px",
              height: rowH, position: "relative", overflow: "hidden", opacity: s, boxSizing: "border-box",
              display: "flex", flexDirection: "column", justifyContent: "center",
              border: `1px solid ${on > 0.4 ? C.accent : C.line}`,
              boxShadow: on > 0.05 ? "0 10px 24px rgba(0,0,0,0.06)" : "0 1px 2px rgba(0,0,0,0.03)",
              transform: `translateY(${(1 - s) * 24}px)` }}>
              <div style={{ fontFamily: EN, fontSize: enSize, fontWeight: C.enWeight, letterSpacing: "-0.02em", color: C.en,
                whiteSpace: "nowrap" }}>{w.en}</div>
              <div style={{ fontFamily: w.ipa ? IPA_FONT : ZH, fontSize: compact ? 18 : 24, fontWeight: 400,
                color: C.tertiary, marginTop: 4 }}>
                {w.ipa || "短语"}
              </div>
              <div style={{ fontSize: compact ? 24 : 28, fontWeight: 500, marginTop: compact ? 6 : 16, color: C.ink,
                whiteSpace: "nowrap" }}>
                {w.pos ? (
                  <span style={{ fontFamily: EN, fontWeight: 500, color: C.tertiary, marginRight: 8 }}>{w.pos}</span>
                ) : null}
                <span style={{ background: zhOn > 0.5 ? C.word : "transparent", borderRadius: 6, padding: "0 4px" }}>
                  {w.gloss}
                </span>
              </div>
              {w.senses?.length ? (
                <div style={{ fontSize: compact ? 18 : 22, fontWeight: 400, color: C.secondary, marginTop: 4,
                  lineHeight: 1.3 }}>
                  {w.senses.join("；")}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>

      <Footer opacity={head} />
    </AbsoluteFill>
  );
};
