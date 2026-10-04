import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import type { Item, Page, Timeline, Token } from "../types";

const BG = "#000000";
/** 比纯黄 #FFFF00 厚一点，黑底上仍然扁平刺眼，但边缘不发虚。 */
const YELLOW = "#FFE500";
const WHITE = "#FFFFFF";
const CREAM = "#F3E6C8";
const IPA_COLOR = "#8FD4FF";
const LABEL = "#D4D4D4";
const BOX = 1080 - 56 - 188;
const ZH = `"PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Source Han Sans SC", sans-serif`;
const EN = `"Helvetica Neue", Helvetica, Arial, sans-serif`;
const IPA_FONT = `"Lucida Grande", "Hiragino Sans", "PingFang SC", sans-serif`;

type WordTok = { i: number; text: string; start?: number; end?: number };
type Piece = { text: string; word?: WordTok };

const isWord = (tok: Token): tok is WordTok => "i" in tok;

const piecesOf = (page: Page): Piece[] =>
  page.tokens.flatMap((tok) => {
    if ("t" in tok && tok.t) return [{ text: tok.t }];
    if ("en" in tok) return [{ text: tok.en }];
    if ("i" in tok) return [{ text: tok.text, word: tok }];
    return [];
  });

const posLabel = (pos: string) => (pos === "phr." ? "短语." : pos);

const clamp01 = (n: number) => Math.max(0, Math.min(1, n));

const PEAK = 1.42;

/** 单词砸下来：先放大再收回。字号按这个峰值算进安全区，放大时也不出屏。 */
const impact = (age: number) => {
  if (age < 0) return { scale: 0.55, x: 0 };
  const u = clamp01(age / 0.12);
  const ease = 1 - (1 - u) ** 3;
  const scale = PEAK - (PEAK - 1) * ease;
  const x = Math.sin(age * 90) * Math.exp(-age * 18) * 8;
  return { scale, x };
};

/** 西文约 0.56em，汉字和音标约 1em。用来在不测量 DOM 的情况下选字号。 */
const emOf = (text: string) => {
  let w = 0;
  for (const ch of text) {
    const c = ch.codePointAt(0) ?? 0;
    const narrow = c < 0x80 || (c >= 0x0250 && c <= 0x02ff) || (c >= 0x0300 && c <= 0x036f);
    if (ch === " " || ch === "\u00a0") w += 0.33;
    else if (narrow) w += 0.56;
    else w += 1;
  }
  return Math.max(w, 0.5);
};

const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));

const linesFor = (text: string, size: number, width = BOX) =>
  Math.max(1, Math.ceil((emOf(text) * size) / width));

/** 单行塞进宽度。放大峰值也算进去时，把宽度先除掉峰值。 */
const fitEn = (en: string, max: number) =>
  clamp(Math.floor(BOX / PEAK / emOf(en)), 28, max);

/** 先用大字换行；块的高度超出安全区再缩小。 */
const fitBlock = (text: string, max: number, min: number, maxHeight: number, lineHeight = 1.4) => {
  for (let size = max; size >= min; size -= 2) {
    if (linesFor(text, size) * size * lineHeight <= maxHeight) return size;
  }
  return min;
};

const BOX_H = 1920 - 310 - 450;

const titleLayout = (text: string) => {
  const clauses = text.split(/(?<=[，。！？、；：])/).filter((part) => part.length > 0);
  const parts = clauses.length ? clauses : [text];
  const widest = parts.reduce((a, b) => (emOf(a) > emOf(b) ? a : b));
  const size = clamp(Math.floor(BOX / emOf(widest)), 48, 84);
  const wrap = emOf(widest) * size > BOX + 1;
  const lines = wrap ? parts.reduce((n, part) => n + linesFor(part, size), 0) : parts.length;
  return { parts, size, wrap, h: lines * size * 1.22 };
};

const packList = (rows: { en: string; meta: string }[], titleH: number, boxH: number) => {
  const avail = Math.max(160, boxH - titleH);
  let en = 42;
  let meta = 32;
  let gap = 16;
  const height = () =>
    rows.reduce((h, row) => h + linesFor(row.en, en) * en * 1.15 + 4 + linesFor(row.meta, meta) * meta * 1.35 + gap, 0);
  while (height() > avail && (en > 22 || meta > 16 || gap > 6)) {
    if (en > 22) en -= 2;
    if (meta > 16) meta -= 1;
    if (gap > 6) gap -= 1;
  }
  return { en, meta, gap };
};

/** 正文只换两种浅色：熬和压是暖杏，嘲讽那句是浅珊瑚，其余保持白。 */
const zhTone = (text: string) => {
  if (/熬|加班|累|凌晨|周末|精疲|通宵|取消/.test(text)) return "#FFD0B5";
  if (/老板|未读|先放着|高度重视|圣旨|随口|报废|利润|笑话/.test(text)) return "#FFB4A2";
  return WHITE;
};

const Center: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      position: "absolute",
      left: 56,
      right: 188,
      top: 310,
      bottom: 450,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      textAlign: "center",
    }}
  >
    {children}
  </div>
);

const popIn = (age: number) => {
  const u = clamp01(age / 0.1);
  const ease = 1 - (1 - u) ** 2;
  return { y: (1 - ease) * 22 };
};

type Beat =
  | { kind: "zh"; text: string; from: number; to: number }
  | { kind: "word"; en: string; word: WordTok; from: number; to: number };

const showZh = (text: string) => text.replace(/^[，,。！？；、：:\s]+/, "").replace(/[，,。！？；、：:\s]+$/, "");

const splitClauses = (text: string) => {
  const parts: string[] = [];
  let buf = "";
  for (const ch of text) {
    buf += ch;
    if ("，,。！？；、：:".includes(ch)) {
      parts.push(buf);
      buf = "";
    }
  }
  if (buf.trim()) parts.push(buf);
  return parts.filter((s) => showZh(s).length > 0);
};

/** 只在标点处切开，不把一句话切成半截。 */
const sliceZh = (text: string, from: number, to: number) => {
  const bits = splitClauses(text);
  const clauses = bits.length ? bits : [text];
  const weights = clauses.map((s) => Math.max(1, showZh(s).length));
  const total = weights.reduce((a, b) => a + b, 0) || 1;
  const dur = Math.max(0.08, to - from);
  const out: { text: string; from: number; to: number }[] = [];
  let cursor = from;
  clauses.forEach((clause, i) => {
    const clean = showZh(clause);
    const bitDur = (dur * weights[i]) / total;
    if (clean) out.push({ text: clean, from: cursor, to: cursor + bitDur });
    cursor += bitDur;
  });
  return out;
};

const pageBeats = (page: Page): Beat[] => {
  const pieces = piecesOf(page);
  const beats: Beat[] = [];
  let cursor = page.start;
  let i = 0;
  while (i < pieces.length) {
    const piece = pieces[i];
    if (piece.word?.start != null) {
      const start = Math.max(cursor, piece.word.start);
      const spoken = Math.max(0.35, (piece.word.end ?? start + 0.5) - piece.word.start);
      const end = Math.min(page.end, start + Math.max(spoken, 0.32));
      if (end > start) beats.push({ kind: "word", en: piece.text, word: piece.word, from: start, to: end });
      cursor = Math.max(cursor, end);
      i += 1;
      continue;
    }
    let text = "";
    while (i < pieces.length && !pieces[i].word) {
      text += pieces[i].text;
      i += 1;
    }
    const nextStart = pieces[i]?.word?.start;
    const end = Math.max(cursor, Math.min(page.end, nextStart ?? page.end));
    if (text.trim() && end > cursor + 0.05) {
      for (const bit of sliceZh(text, cursor, end)) beats.push({ kind: "zh", ...bit });
    }
    cursor = end;
  }
  return beats;
};

const Note: React.FC<{ item?: Item; size: number }> = ({ item, size }) => {
  if (!item) return null;
  const gloss = `${posLabel(item.pos)}${item.gloss}`;
  const glossSize = fitBlock(gloss, size, 26, 150, 1.35);
  const ipaSize = item.ipa ? fitBlock(item.ipa, glossSize, 22, 72, 1.3) : glossSize;
  return (
    <div style={{ textAlign: "center", maxWidth: BOX }}>
      <div style={{ fontFamily: ZH, fontWeight: 500, fontSize: glossSize, lineHeight: 1.35, color: CREAM }}>{gloss}</div>
      {item.ipa ? (
        <div style={{ marginTop: 6, fontFamily: IPA_FONT, fontWeight: 500, fontSize: ipaSize, lineHeight: 1.3, color: IPA_COLOR }}>
          {item.ipa}
        </div>
      ) : null}
    </div>
  );
};

const Mark: React.FC = () => (
  <div
    style={{
      position: "absolute",
      top: 252,
      left: 56,
      right: 188,
      zIndex: 3,
      fontFamily: ZH,
      fontWeight: 600,
      fontSize: 36,
      lineHeight: "44px",
      color: LABEL,
      letterSpacing: 1,
    }}
  >
    雅思单词学习
  </div>
);

const BeatView: React.FC<{ beat: Beat; items: Item[]; t: number }> = ({ beat, items, t }) => {
  const age = t - beat.from;
  if (beat.kind === "word") {
    const hit = impact(age);
    const item = items[beat.word.i];
    const size = fitEn(beat.en, 108);
    const bar = clamp01(age / 0.08);
    return (
      <Center>
        <div style={{ transform: `translateX(${hit.x}px) scale(${hit.scale})`, transformOrigin: "50% 50%" }}>
          <div style={{ fontFamily: EN, fontWeight: 700, fontSize: size, lineHeight: 1.05, color: YELLOW, letterSpacing: "-0.03em" }}>
            {beat.en}
          </div>
          <div style={{ height: 8, margin: "16px auto 0", width: Math.min(BOX * 0.46, Math.max(96, emOf(beat.en) * size * 0.72)), background: YELLOW, transform: `scaleX(${bar})`, transformOrigin: "center" }} />
        </div>
        <div style={{ marginTop: 22 }}>
          <Note item={item} size={52} />
        </div>
      </Center>
    );
  }
  const pop = popIn(age);
  return (
    <Center>
      <div
        style={{
          fontFamily: ZH,
          fontWeight: 700,
          fontSize: fitBlock(beat.text, 76, 44, BOX_H * 0.8),
          lineHeight: 1.4,
          maxWidth: BOX,
          color: zhTone(beat.text),
          transform: `translateY(${pop.y}px)`,
        }}
      >
        {beat.text}
      </div>
    </Center>
  );
};

const WordCard: React.FC<{ items: Item[]; t: number; at: number }> = ({ items, t, at }) => {
  const age = t - at;
  let y = 0;
  if (age < 0.18) {
    const u = clamp01(age / 0.18);
    if (u < 0.82) {
      const k = u / 0.82;
      y = -1500 * (1 - k * k * k);
    } else {
      y = Math.sin(((u - 0.82) / 0.18) * Math.PI) * 12;
    }
  }
  return (
    <AbsoluteFill style={{ background: BG }}>
      <div
        style={{
          position: "absolute",
          left: 56,
          right: 188,
          top: 328,
          bottom: 440,
          transform: `translateY(${y}px)`,
          background: "#FFFFFF",
          borderRadius: 24,
          padding: "28px 28px 22px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        {(() => {
          const cardH = 1920 - 328 - 440 - 50;
          const pack = packList(items.map(rowOf), 0, cardH);
          return items.map((item, i) => (
            <div key={item.en} style={{ marginBottom: i === items.length - 1 ? 0 : pack.gap }}>
              <div style={{ fontFamily: EN, fontWeight: 700, fontSize: pack.en, lineHeight: 1.15, color: "#141414", textAlign: "center" }}>
                {i + 1}. {item.en}
              </div>
              <div style={{ marginTop: 4, fontFamily: ZH, fontWeight: 500, fontSize: pack.meta, lineHeight: 1.35, color: "#3A3A3A", textAlign: "center" }}>
                {posLabel(item.pos)}
                {item.gloss}
                {item.ipa ? <span style={{ fontFamily: IPA_FONT, color: "#1565C0" }}>{`  ${item.ipa}`}</span> : null}
              </div>
            </div>
          ));
        })()}
      </div>
    </AbsoluteFill>
  );
};

const holdBeat = (beats: Beat[], t: number) => {
  let cur: Beat | null = null;
  for (const beat of beats) {
    if (t >= beat.from) cur = beat;
  }
  return cur;
};

/** 标点处优先断行。一句放得下就一行，放不下再缩小，缩到 48 仍超宽才拆开。 */
const Title: React.FC<{ text: string }> = ({ text }) => {
  const layout = titleLayout(text);
  return (
    <div style={{ fontFamily: ZH, fontWeight: 700, fontSize: layout.size, lineHeight: 1.22, color: YELLOW }}>
      {layout.parts.map((part, i) => (
        <span key={i} style={{ whiteSpace: layout.wrap ? "normal" : "nowrap" }}>
          {part}
        </span>
      ))}
    </div>
  );
};

const rowOf = (item: Item, i: number) => ({
  en: `${i + 1}. ${item.en}`,
  meta: `${posLabel(item.pos)}${item.gloss}${item.ipa ? `  ${item.ipa}` : ""}`,
});

/** 封面：标题点题，下面把本篇单词、释义、音标排开。只占视频第 0 帧。 */
const Poster: React.FC<{ tl: Timeline }> = ({ tl }) => {
  const title = (tl.cover.length ? tl.cover : [tl.title]).join("");
  const layout = titleLayout(title);
  const pack = packList(tl.items.map(rowOf), layout.h + 28, BOX_H);
  return (
    <AbsoluteFill style={{ background: BG }}>
      <Mark />
      <div
        style={{
          position: "absolute",
          left: 56,
          right: 188,
          top: 310,
          bottom: 450,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <Title text={title} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: pack.gap }}>
          {tl.items.map((item, i) => (
            <div key={item.en} style={{ textAlign: "center" }}>
              <div style={{ fontFamily: EN, fontWeight: 700, fontSize: pack.en, lineHeight: 1.1, color: WHITE, letterSpacing: "-0.02em" }}>
                {i + 1}. {item.en}
              </div>
              <div style={{ marginTop: 4, fontFamily: ZH, fontWeight: 500, fontSize: pack.meta, lineHeight: 1.35, color: CREAM }}>
                {posLabel(item.pos)}
                {item.gloss}
                {item.ipa ? <span style={{ fontFamily: IPA_FONT, color: IPA_COLOR }}>{`  ${item.ipa}`}</span> : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Stage: React.FC<{ tl: Timeline; t: number | null }> = ({ tl, t }) => {
  const coverUntil = tl.pages[0]?.start ?? 1;
  if (t === null || t < coverUntil) return <Poster tl={tl} />;
  const beats = tl.pages.flatMap(pageBeats);
  const reviewAt = tl.review.start;
  if (t !== null && t >= reviewAt) {
    return (
      <AbsoluteFill style={{ background: BG }}>
        <WordCard items={tl.items} t={t} at={reviewAt} />
        <Mark />
      </AbsoluteFill>
    );
  }

  const now = t ?? 2.2;
  const zoom = t === null ? 1 : interpolate(now, [coverUntil, reviewAt], [1, 1.03], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const beat = holdBeat(beats, now);

  return (
    <AbsoluteFill style={{ background: BG }}>
      <div style={{ position: "absolute", inset: 0, transform: `scale(${zoom})`, transformOrigin: "50% 46%" }}>
        {beat ? <BeatView key={beat.from} beat={beat} items={tl.items} t={now} /> : null}
      </div>
      <Mark />
    </AbsoluteFill>
  );
};

export const CoverFrame: React.FC<{ tl: Timeline }> = ({ tl }) => <Stage tl={tl} t={null} />;
