import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, EN, HL, ZH } from "../theme";
import type { Timeline } from "../types";

export const Summary: React.FC<Timeline> = ({ meta, words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const head = spring({ frame, fps, config: { damping: 16 } });
  const rowH = words.length > 6 ? 250 : 290;

  return (
    <AbsoluteFill style={{ fontFamily: ZH }}>
      <div style={{ position: "absolute", left: 72, top: 150, color: "#fff", opacity: head,
        transform: `translateY(${(1 - head) * 30}px)` }}>
        <div style={{ fontSize: 84, fontWeight: 900 }}>今日词卡 · {words.length}</div>
        <div style={{ fontSize: 34, opacity: 0.7, marginTop: 16 }}>Vol.{meta.id} {meta.theme} · {meta.level}</div>
      </div>

      <div style={{ position: "absolute", left: 56, right: 56, top: 420, display: "grid",
        gridTemplateColumns: "1fr 1fr", gap: 28 }}>
        {words.map((w, i) => {
          const s = spring({ frame: frame - Math.round((0.3 + i * 0.08) * fps), fps, config: { damping: 13, mass: 0.7 } });
          const long = w.word.length > 11;
          return (
            <div key={w.word} style={{ background: C.paper, borderRadius: 28, padding: "34px 34px 30px 48px",
              height: rowH, position: "relative", overflow: "hidden", opacity: s,
              transform: `translateY(${(1 - s) * 40}px) scale(${0.94 + 0.06 * s})` }}>
              <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 14, background: HL[w.color] }} />
              <span style={{ position: "absolute", right: 24, bottom: 16, fontSize: 56, fontWeight: 900,
                color: "rgba(31,27,22,.07)", fontFamily: EN }}>{String(i + 1).padStart(2, "0")}</span>
              {w.review ? (
                <span style={{ position: "absolute", right: 24, top: 24, fontSize: 22, fontWeight: 700,
                  background: C.ink, color: "#fff", borderRadius: 8, padding: "4px 10px" }}>复习</span>
              ) : null}
              <div style={{ fontFamily: EN, fontSize: long ? 42 : 50, fontWeight: 800, color: C.ink }}>{w.word}</div>
              <div style={{ fontFamily: `"Lucida Grande", "Arial Unicode MS", ${EN}`, fontSize: 28, color: C.muted, marginTop: 10 }}>{w.ipa}</div>
              <div style={{ fontSize: 34, fontWeight: 800, marginTop: 26, color: C.ink }}>
                <em style={{ fontStyle: "normal", background: HL[w.color], padding: "2px 10px", borderRadius: 8,
                  marginRight: 10, fontSize: 26 }}>{w.pos}</em>
                {w.meaning}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, top: 1580, textAlign: "center", color: "#fff",
        fontSize: 34, opacity: 0.75 * head }}>
        截图收藏 · 评论区默写打卡
      </div>
    </AbsoluteFill>
  );
};
