import React from "react";
import { AbsoluteFill, interpolate, spring, useVideoConfig } from "remotion";
import { C, EN, HL, IPA_FONT, ZH } from "./theme";
import type { Entry, Timeline } from "./types";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 词卡复习：全部学习项双列卡片，随音频逐张高亮（先读英文，再读中文释义）。 */
export const Review: React.FC<{ tl: Timeline; t: number }> = ({ tl, t }) => {
  const { fps } = useVideoConfig();
  const { items } = tl;
  const local = t - tl.review.start;
  const head = spring({ frame: Math.round(local * fps), fps, config: { damping: 16 } });
  const entries = new Map<number, Entry>(tl.review.groups.flatMap((g) => g.entries.map((e) => [e.i, e] as const)));
  const activeAt = (e?: Entry) => (e ? interpolate(t, [e.start - 0.15, e.start, e.end + 0.2, e.end + 0.4], [0, 1, 1, 0], CLAMP) : 0);
  const anyActive = items.some((_, i) => activeAt(entries.get(i)) > 0.5);
  const compact = items.length > 8;
  const rowH = compact ? 196 : items.length > 6 ? 250 : 290;

  return (
    <AbsoluteFill style={{ fontFamily: ZH }}>
      <div style={{ position: "absolute", left: 72, top: 150, color: "#fff", opacity: head,
        transform: `translateY(${(1 - head) * 30}px)` }}>
        <div style={{ fontSize: 84, fontWeight: 800 }}>今日词卡 · {items.length}</div>
        <div style={{ fontSize: 34, opacity: 0.7, marginTop: 16 }}>
          {tl.vol ? `Vol.${tl.vol} ` : ""}{tl.title} · {tl.level}
        </div>
      </div>

      <div style={{ position: "absolute", left: 56, right: 56, top: 420, display: "grid",
        gridTemplateColumns: "1fr 1fr", gap: compact ? 24 : 28 }}>
        {items.map((w, i) => {
          const e = entries.get(i);
          const s = spring({ frame: Math.round((local - 0.3 - i * 0.06) * fps), fps, config: { damping: 13, mass: 0.7 } });
          const on = activeAt(e);
          const zhOn = e ? interpolate(t, [e.enEnd, e.enEnd + 0.15], [0, 1], CLAMP) * on : 0;
          const dim = anyActive && on < 0.5 ? 0.72 : 1;
          const enSize = Math.min(compact ? 44 : 50, Math.floor(380 / (w.en.length * 0.62)));
          return (
            <div key={i} style={{ background: C.paper, borderRadius: 28, padding: compact ? "28px 30px 24px 44px" : "34px 34px 30px 48px",
              height: rowH, position: "relative", overflow: "hidden", opacity: s * dim,
              boxShadow: on > 0 ? `0 0 0 ${6 * on}px ${HL[w.color]}` : "none",
              transform: `translateY(${(1 - s) * 40}px) scale(${(0.94 + 0.06 * s) * (1 + 0.04 * on)})` }}>
              <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 14, background: HL[w.color] }} />
              <span style={{ position: "absolute", right: 24, bottom: 16, fontSize: 56, fontWeight: 900,
                color: "rgba(31,27,22,.07)", fontFamily: EN }}>{String(i + 1).padStart(2, "0")}</span>
              <div style={{ fontFamily: EN, fontSize: enSize, fontWeight: 600, color: C.ink, whiteSpace: "nowrap" }}>{w.en}</div>
              <div style={{ fontFamily: w.ipa ? IPA_FONT : ZH, fontSize: compact ? 24 : 28, color: C.muted, marginTop: compact ? 4 : 10 }}>
                {w.ipa || "短语"}
              </div>
              <div style={{ fontSize: compact ? 30 : 34, fontWeight: 600, marginTop: compact ? 14 : 26, color: C.ink }}>
                {w.pos ? (
                  <em style={{ fontStyle: "normal", fontFamily: EN, color: C.muted, marginRight: 10 }}>{w.pos}</em>
                ) : null}
                <span style={{ background: zhOn > 0.5 ? `${HL[w.color]}88` : "transparent", borderRadius: 6, padding: "0 4px" }}>
                  {w.gloss}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, top: 1580, textAlign: "center", color: "#fff",
        fontSize: 34, opacity: 0.75 * head }}>
        {tl.hint}
      </div>
    </AbsoluteFill>
  );
};
