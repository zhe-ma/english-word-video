import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import React from "react";
import { spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, EN, HL, IPA_FONT, LAYOUT, ZH } from "./theme";
import type { Item } from "./types";

export const CARD: React.CSSProperties = {
  position: "absolute", left: 60, right: 60, top: LAYOUT.cardTop, height: LAYOUT.cardHeight, background: "#fff",
  borderRadius: 30, padding: "26px 44px", display: "flex", gap: 36, alignItems: "center",
};

/** 白色卡片里的两行文字（开场、结尾用）。 */
export const TextCard: React.FC<{ title: string; sub: string; color?: string; style?: React.CSSProperties }> = ({
  title, sub, color = HL.yellow, style,
}) => (
  <div style={{ ...CARD, borderLeft: `20px solid ${color}`, ...style }}>
    <div style={{ fontFamily: ZH, fontSize: 46, fontWeight: 700, color: C.ink }}>
      {title}
      <div style={{ fontSize: 30, fontWeight: 400, color: C.muted, marginTop: 10 }}>{sub}</div>
    </div>
  </div>
);

/** 聚焦卡：显示当前读到的学习项。current 为学习项下标和开始时间，读到第一个之前为 null。 */
export const FocusCard: React.FC<{ items: Item[]; current: { i: number; start: number } | null; audioSrc?: string }> = ({
  items, current, audioSrc,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!current) {
    const s = spring({ frame: frame + Math.round(0.35 * fps), fps, config: { damping: 16 } });
    return <TextCard title={`今天 ${items.length} 个词`} sub="认真听，读完就测你"
      style={{ opacity: s, transform: `translateY(${(1 - s) * 30}px)` }} />;
  }

  const w = items[current.i];
  const s = spring({ frame: frame - Math.round(current.start * fps), fps, config: { damping: 14, mass: 0.6 } });
  const size = Math.min(70, Math.floor(540 / (w.en.length * 0.62)));
  return (
    <div style={{ ...CARD, borderLeft: `20px solid ${HL[w.color]}` }}>
      <div style={{ opacity: s, transform: `translateY(${(1 - s) * 36}px)`, display: "flex", width: "100%", alignItems: "center" }}>
        <div>
          <div style={{ fontFamily: EN, fontSize: size, fontWeight: 600, lineHeight: 1, color: C.ink, whiteSpace: "nowrap" }}>{w.en}</div>
          <div style={{ fontFamily: EN, fontWeight: 600, fontSize: 26, color: "#8a8378", marginTop: 14, letterSpacing: 2 }}>
            {w.kind === "phrase" ? "phrase · 短语" : w.syllables}
          </div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right", flex: "none" }}>
          {w.ipa ? <div style={{ fontFamily: IPA_FONT, fontSize: 30, color: "#5d574e" }}>{w.ipa}</div> : null}
          <div style={{ fontFamily: ZH, fontSize: 40, fontWeight: 600, marginTop: w.ipa ? 10 : 0, color: C.ink }}>
            {w.pos ? <span style={{ fontFamily: EN, color: C.muted, marginRight: 12 }}>{w.pos}</span> : null}
            {w.gloss}
          </div>
          {audioSrc ? <Wave src={staticFile(audioSrc)} color={HL[w.color]} /> : null}
        </div>
      </div>
    </div>
  );
};

const Wave: React.FC<{ src: string; color: string }> = ({ src, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const audioData = useAudioData(src);
  if (!audioData) return null;
  const bars = visualizeAudio({ fps, frame, audioData, numberOfSamples: 32 }).slice(1, 11);
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center", justifyContent: "flex-end", height: 30, marginTop: 8 }}>
      {bars.map((v, i) => (
        <b key={i} style={{ width: 6, borderRadius: 3, background: color, height: Math.min(30, 5 + Math.sqrt(v) * 70) }} />
      ))}
    </div>
  );
};
