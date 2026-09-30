import React from "react";
import { Easing, interpolate } from "remotion";
import { px } from "./FitBox";
import { C, EN, MARK, TEXT, ZH } from "./theme";
import type { Item, Page, Token } from "./types";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const LEADING_PUNCT = /^[，。！？；：、”’）》…—]+/;
const RADIUS = "0.24em";
const CLONE = { boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone" } as const;

/**
 * 纸上的正文：各段连成一整段，两端对齐。没读到的段变淡；学习项读到时刷上荧光黄，后面的「词性 释义」浮现。
 * t 为 null 表示全部读完的静态状态（结尾全文帧、封面）。
 */
export const MarkedText: React.FC<{ pages: Page[]; items: Item[]; t: number | null }> = ({ pages, items, t }) => (
  <p style={{ fontFamily: ZH, fontSize: px(TEXT.size), lineHeight: TEXT.lineHeight, fontWeight: 500, color: C.ink,
    letterSpacing: "0.02em", lineBreak: "strict", margin: 0 }}>
    {pages.map((p, k) => (
      <PageView key={k} p={p} items={items} t={t} />
    ))}
  </p>
);

const PageView: React.FC<{ p: Page; items: Item[]; t: number | null }> = ({ p, items, t }) => {
  const opacity = t === null ? 1 : interpolate(t, [p.start - 0.15, p.start + 0.1], [0.32, 1], CLAMP);
  const out: React.ReactNode[] = [];
  let carry = "";
  p.tokens.forEach((tk, i) => {
    if ("t" in tk) {
      const text = carry ? tk.t.slice(carry.length) : tk.t;
      carry = "";
      if (text) out.push(<span key={i}>{text}</span>);
      return;
    }
    const next = p.tokens[i + 1];
    const punct = next && "t" in next ? (next.t.match(LEADING_PUNCT)?.[0] ?? "") : "";
    carry = punct;
    if ("en" in tk) {
      out.push(
        <span key={i} style={{ whiteSpace: "nowrap" }}>
          <span style={{ fontFamily: EN, fontWeight: 600, margin: "0 0.1em" }}>{tk.en}</span>
          {punct}
        </span>,
      );
    } else {
      out.push(<WordView key={i} tk={tk} item={items[tk.i]} t={t} trailing={punct} />);
    }
  });
  return <span style={{ opacity }}>{out}</span>;
};

const WordView: React.FC<{ tk: Extract<Token, { i: number }>; item: Item; t: number | null; trailing: string }> = ({
  tk, item, t, trailing,
}) => {
  const start = tk.start ?? 0;
  const dur = Math.max(0.25, (tk.end ?? start) - start);
  const still = t === null;
  const p = still ? 1 : interpolate(t, [start, start + Math.min(dur, 0.4)], [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });
  const g = still ? 1 : interpolate(t, [start + 0.08, start + 0.35], [0, 1], { ...CLAMP, easing: Easing.out(Easing.cubic) });

  // 只用行内元素（不用 inline-block）：英文和释义之间允许折行，标点不会落到行首，
  // 折行处高亮各自成圆角块。释义始终占位、只改透明度，读到时不会重排。
  return (
    <>
      <span style={{ ...CLONE, margin: "0 0.1em", padding: "0.06em 0.2em", borderRadius: RADIUS,
        backgroundImage: `linear-gradient(${MARK}, ${MARK})`, backgroundRepeat: "no-repeat",
        backgroundSize: `${p * 100}% 100%` }}>
        <span style={{ fontFamily: EN, fontWeight: 600, whiteSpace: "nowrap" }}>{tk.text}</span>
        <wbr />
        <span style={{ ...CLONE, marginLeft: "0.3em", padding: "0.08em 0.3em", borderRadius: "0.3em", whiteSpace: "nowrap",
          fontSize: `${TEXT.gloss}em`, background: `rgba(255,255,255,${0.75 * g})`,
          borderBottom: `${px(3)} dashed rgba(31,27,22,${0.3 * (1 - g)})` }}>
          {item.pos ? (
            <span style={{ fontFamily: EN, fontWeight: 600, fontSize: "0.86em", marginRight: "0.25em",
              color: `rgba(122,115,103,${g})` }}>{item.pos}</span>
          ) : null}
          <span style={{ fontFamily: ZH, fontWeight: 500, color: `rgba(31,27,22,${g})` }}>{item.gloss}</span>
        </span>
      </span>
      {trailing}
    </>
  );
};
