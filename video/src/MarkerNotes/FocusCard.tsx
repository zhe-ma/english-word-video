import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { resolveMedia } from "../media";
import { C, EN, HL, ZH } from "../theme";
import type { Word } from "../types";

const BOX: React.CSSProperties = {
  position: "absolute", left: 72, right: 72, top: 340, height: 220, background: "#fff",
  borderRadius: 32, padding: "36px 48px", display: "flex", gap: 40, alignItems: "center",
};

export const FocusCard: React.FC<{ words: Word[]; total: number; audioSrc?: string }> = ({ words, total, audioSrc }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const idx = words.reduce((acc, w, i) => (t >= w.start ? i : acc), -1);

  if (idx < 0) {
    const s = spring({ frame, fps, config: { damping: 16 } });
    return (
      <div style={{ ...BOX, borderLeft: `20px solid ${HL.yellow}`, opacity: s, transform: `translateY(${(1 - s) * 30}px)` }}>
        <div style={{ fontFamily: ZH, fontSize: 48, fontWeight: 900, color: C.ink }}>
          今天 {total} 个词
          <div style={{ fontSize: 30, fontWeight: 600, color: C.muted, marginTop: 12 }}>认真听，读完就测你</div>
        </div>
      </div>
    );
  }

  const w = words[idx];
  const s = spring({ frame: frame - Math.round(w.start * fps), fps, config: { damping: 14, mass: 0.6 } });
  const long = w.word.length > 10;
  return (
    <div style={{ ...BOX, borderLeft: `20px solid ${HL[w.color]}` }}>
      <div style={{ opacity: s, transform: `translateY(${(1 - s) * 36}px)`, display: "flex", width: "100%", alignItems: "center" }}>
        <div>
          <div style={{ fontFamily: EN, fontSize: long ? 62 : 76, fontWeight: 800, lineHeight: 1, color: C.ink }}>{w.word}</div>
          <div style={{ fontFamily: EN, fontWeight: 600, fontSize: 28, color: "#8a8378", marginTop: 16, letterSpacing: 2 }}>{w.syllables}</div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ fontFamily: `"Lucida Grande", "Arial Unicode MS", ${EN}`, fontSize: 32, color: "#5d574e" }}>{w.ipa}</div>
          <div style={{ fontFamily: ZH, fontSize: 42, fontWeight: 800, marginTop: 14, color: C.ink }}>
            {w.pos} {w.meaning}
          </div>
          {audioSrc ? <Wave src={resolveMedia(audioSrc) ?? audioSrc} color={HL[w.color]} /> : null}
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
    <div style={{ display: "flex", gap: 6, alignItems: "center", justifyContent: "flex-end", height: 40, marginTop: 12 }}>
      {bars.map((v, i) => (
        <b key={i} style={{ width: 6, borderRadius: 3, background: color, height: Math.min(40, 6 + Math.sqrt(v) * 90) }} />
      ))}
    </div>
  );
};
