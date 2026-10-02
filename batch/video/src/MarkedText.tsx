import React from "react";
import { Easing, interpolate } from "remotion";
import { px } from "./FitBox";
import { ANNO, C, EN, TEXT, ZH } from "./theme";
import type { Item, Page, Token } from "./types";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const LEADING_PUNCT = /^[，。！？；：、”’）》…—]+/;

/** 标点跟在前一个字后面，中文本身可以在任意字间断开，一行尽量排满。 */
const stickPunct = (text: string) => text.replace(/([，。！？；：、”’）》…—])/g, "\u2060$1");

/**
 * 纸上的正文。没读到的句子也保持同色。学习词用预设里的字重和颜色。
 * 像在书上注一行：单词下方是词性和释义，不带括号。读到那个词时淡入。
 * t 为 null 表示全部读完的静态状态（结尾全文帧、封面）。
 */
export const MarkedText: React.FC<{ pages: Page[]; items: Item[]; t: number | null }> = ({ pages, items, t }) => (
  <p style={{ fontFamily: ZH, fontSize: px(TEXT.size), lineHeight: "var(--lh)", fontWeight: 400, color: C.ink,
    letterSpacing: "0.01em", margin: 0 }}>
    {pages.map((p, k) => (
      <PageView key={k} p={p} items={items} t={t} />
    ))}
  </p>
);

const PageView: React.FC<{ p: Page; items: Item[]; t: number | null }> = ({ p, items, t }) => {
  const out: React.ReactNode[] = [];
  let carry = "";
  p.tokens.forEach((tk, i) => {
    if ("t" in tk) {
      const text = carry ? tk.t.slice(carry.length) : tk.t;
      carry = "";
      if (text) out.push(<span key={i} data-piece="">{stickPunct(text)}</span>);
      return;
    }
    const next = p.tokens[i + 1];
    const punct = next && "t" in next ? (next.t.match(LEADING_PUNCT)?.[0] ?? "") : "";
    carry = punct;
    if ("en" in tk) {
      out.push(
        <span key={i} style={{ whiteSpace: "nowrap" }}>
          <span style={{ fontFamily: EN, fontWeight: 400 }}>{tk.en}</span>
          {punct}
        </span>,
      );
    } else {
      out.push(<WordView key={i} tk={tk} item={items[tk.i]} t={t} trailing={punct} room={needsRoom(p.tokens, i)} />);
    }
  });
  return <span>{out}</span>;
};

/** 下一个学习词若只隔着一两个字（如「与」），给当前注释留出位置，避免两行注叠在一起。 */
const needsRoom = (tokens: Token[], i: number) => {
  const rest = tokens.slice(i + 1);
  const bridge = rest.findIndex((tk) => !("t" in tk));
  if (bridge < 0) return false;
  const between = rest.slice(0, bridge).map((tk) => ("t" in tk ? tk.t : "")).join("");
  return [...between].filter((ch) => ch.trim() && !LEADING_PUNCT.test(ch)).length <= 2;
};

/** 一行注释，落在统一行距里，不把这一行再撑高。 */
const note = (opacity: number): React.CSSProperties => ({
  position: "absolute", top: "100%", left: "50%", transform: "translateX(-50%)", marginTop: "0.14em",
  width: "max-content", whiteSpace: "nowrap",
  opacity, fontSize: `${TEXT.anno}em`, lineHeight: 1, fontWeight: 500, letterSpacing: 0,
  fontFamily: ZH, color: ANNO.gloss,
});

const WordView: React.FC<{ tk: Extract<Token, { i: number }>; item: Item; t: number | null; trailing: string; room?: boolean }> = ({
  tk, item, t, trailing, room,
}) => {
  const start = tk.start ?? 0;
  const g = t === null ? 1 : interpolate(t, [start + 0.15, start + 0.55], [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const pos = item.pos.replace(/^phrase\.$/i, "phr.");

  return (
    <span data-piece="" style={{ whiteSpace: "nowrap", marginRight: room ? "0.6em" : undefined }}>
      <span style={{ position: "relative" }}>
        <span style={{ fontFamily: EN, fontWeight: C.enWeight, letterSpacing: "-0.02em", color: C.en,
          background: C.word === "transparent" ? undefined : C.word, borderRadius: "0.18em",
          padding: C.word === "transparent" ? undefined : "0 0.06em",
          borderBottom: C.enLine || undefined }}>{tk.text}</span>
        <span style={note(g)}>
          {pos ? <span style={{ fontFamily: EN, fontWeight: 600 }}>{pos} </span> : null}
          {item.gloss}
        </span>
      </span>
      {trailing}
    </span>
  );
};
