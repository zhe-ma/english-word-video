import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, EN, HL, ZH } from "../theme";
import type { Sentence, Timeline, Word } from "../types";
import { FocusCard } from "./FocusCard";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const LEADING_PUNCT = /^[，。！？；：、”’）》…—]+/;

export const Reading: React.FC<Timeline> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const { meta, words, sentences, summary } = props;
  const scale = props.layout?.fontScale ?? 1;

  const enter = spring({ frame, fps, config: { damping: 16, mass: 0.8 } });
  const exit = interpolate(t, [summary.start - 0.35, summary.start + 0.1], [0, 1], {
    ...CLAMP,
    easing: Easing.in(Easing.cubic),
  });
  const learned = words.filter((w) => t >= w.start).length;

  return (
    <AbsoluteFill style={{ transform: `translateX(${-1200 * exit}px) rotate(${-6 * exit}deg)`, opacity: 1 - exit * 0.6 }}>
      <div style={{ position: "absolute", left: 72, right: 72, top: 90, color: "#fff", fontFamily: ZH }}>
        <div style={{ display: "flex", alignItems: "center", gap: 20, fontSize: 30, fontWeight: 600, opacity: 0.9 }}>
          <span style={{ background: "#fff", color: C.bg, borderRadius: 12, padding: "4px 16px", fontWeight: 800, fontFamily: EN }}>
            Vol.{meta.id}
          </span>
          {meta.series} · {meta.level}
        </div>
        <div style={{ fontSize: 64, fontWeight: 900, marginTop: 18, letterSpacing: 2 }}>{meta.theme}</div>
        <div style={{ display: "flex", gap: 14, marginTop: 24 }}>
          {words.map((w, i) => (
            <i key={i} style={{ width: 56, height: 12, borderRadius: 6, background: i < learned ? HL[w.color] : "rgba(255,255,255,.18)" }} />
          ))}
        </div>
      </div>

      <FocusCard words={words} total={words.length} audioSrc={props.audioSrc} />

      <div
        style={{
          position: "absolute", left: 56, right: 56, top: 600, height: 920,
          background: `linear-gradient(${C.grid} 2px, transparent 2px) 0 0 / 100% 64px,
            linear-gradient(90deg, ${C.grid} 2px, transparent 2px) 0 0 / 64px 100%, ${C.paper}`,
          borderRadius: 28, padding: "80px 52px 48px", boxShadow: "0 30px 80px rgba(0,0,0,.35)",
          transform: `translateY(${(1 - enter) * 160}px) rotate(-0.6deg)`, opacity: enter,
        }}
      >
        <div style={{ position: "absolute", top: -26, left: "50%", width: 220, height: 56, marginLeft: -110,
          background: "rgba(255, 228, 92, .75)", transform: "rotate(2deg)", borderRadius: 4 }} />
        <p style={{ fontFamily: ZH, fontSize: 42 * scale, lineHeight: `${124 * scale}px`, fontWeight: 700,
          color: C.ink, lineBreak: "strict", margin: 0 }}>
          {sentences.map((s, i) => <SentenceView key={i} s={s} words={words} t={t} />)}
        </p>
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, top: 1580, textAlign: "center", color: "#fff",
        fontFamily: ZH, fontSize: 32, opacity: 0.6 }}>
        {learned < words.length ? `还剩 ${words.length - learned} 个词 · 看到最后有词卡` : "今日词卡马上来"}
      </div>
    </AbsoluteFill>
  );
};

const SentenceView: React.FC<{ s: Sentence; words: Word[]; t: number }> = ({ s, words, t }) => {
  const opacity = interpolate(t, [s.start - 0.15, s.start + 0.1], [0.32, 1], CLAMP);
  const out: React.ReactNode[] = [];
  let carry = "";
  s.tokens.forEach((tk, i) => {
    if ("w" in tk) {
      const next = s.tokens[i + 1];
      const punct = next && "t" in next ? (next.t.match(LEADING_PUNCT)?.[0] ?? "") : "";
      out.push(<WordView key={i} w={words[tk.w]} t={t} trailing={punct} />);
      carry = punct;
    } else {
      const text = carry ? tk.t.slice(carry.length) : tk.t;
      carry = "";
      if (text) out.push(<span key={i}>{text}</span>);
    }
  });
  return <span style={{ opacity }}>{out}</span>;
};

const WordView: React.FC<{ w: Word; t: number; trailing: string }> = ({ w, t, trailing }) => {
  const { fps } = useVideoConfig();
  const dur = Math.max(0.25, w.end - w.start);
  const p = interpolate(t, [w.start, w.start + dur], [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const started = t >= w.start;
  const pop = spring({ frame: Math.round((t - w.start - 0.08) * fps), fps, config: { damping: 11, mass: 0.6 } });

  return (
    <span style={{ whiteSpace: "nowrap" }}>
      <span style={{ position: "relative", display: "inline-block", padding: "0 8px",
        margin: trailing ? "0 0 0 4px" : "0 4px",
        lineHeight: 1.25, fontFamily: EN, fontWeight: 800, isolation: "isolate",
        borderBottom: started ? "5px solid transparent" : "5px dashed rgba(31,27,22,.25)" }}>
        <span style={{ position: "absolute", left: -2, right: -2, top: "46%", height: "48%", zIndex: -1,
          background: HL[w.color], borderRadius: "10px 4px 12px 6px",
          transform: `rotate(-1.5deg) scaleX(${p})`, transformOrigin: "left center" }} />
        {started ? (
          <span style={{ position: "absolute", left: "50%", bottom: "100%", whiteSpace: "nowrap",
            transform: `translate(-50%, ${6 - 8 * pop}px) scale(${0.6 + 0.4 * pop})`, opacity: pop,
            fontFamily: ZH, fontSize: 22, lineHeight: 1, fontWeight: 700,
            background: C.ink, color: "#fff", padding: "7px 12px", borderRadius: 10 }}>
            {w.pos} {w.meaning}
          </span>
        ) : null}
        {w.word}
      </span>
      {trailing}
    </span>
  );
};
