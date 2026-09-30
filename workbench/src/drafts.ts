import type { Token } from "./types";

export const GENRES = [
  "吐槽小剧场", "朋友圈 vs 现实", "伪官方通知", "灵魂拷问对话",
  "拟人视角", "反鸡汤", "伪新闻", "说明书体", "节日热点",
];

export type Draft = { genre: string; words: string; text: string };

export function parseDrafts(md: string): { items: Draft[]; tail: string } {
  const idx = md.search(/^##\s*评审/m);
  const body = idx >= 0 ? md.slice(0, idx) : md;
  const tail = idx >= 0 ? md.slice(idx) : "";
  const parts = body.split(/^## /m).slice(1);
  const items: Draft[] = [];
  for (const part of parts) {
    const title = (part.split("\n")[0] || "").trim();
    const genre = title.replace(/^[A-Z0-9]+ · /, "").trim() || "吐槽小剧场";
    const wm = part.match(/单词[：:]\s*(.+)/);
    const q = part.match(/>([\s\S]*)/);
    const text = (q?.[1] || "").replace(/^>\s?/gm, "").trim();
    items.push({ genre, words: (wm?.[1] || "").trim(), text });
  }
  return { items, tail };
}

export function formatDrafts(id: string, theme: string, level: string, items: Draft[], tail: string) {
  const blocks = items.map((d, i) => {
    const mark = String.fromCharCode(65 + i);
    return `## ${mark} · ${d.genre}\n\n单词：${d.words}\n\n> ${d.text}\n`;
  });
  return [`# 第 ${id} 期 · ${theme}（${level}）\n`, ...blocks, tail].filter(Boolean).join("\n");
}

export function emptyDrafts(words: string[]): Draft[] {
  const w = words.join(", ");
  return [
    { genre: "吐槽小剧场", words: w, text: "" },
    { genre: "伪官方通知", words: w, text: "" },
    { genre: "拟人视角", words: w, text: "" },
  ];
}

export function mixedToSentences(text: string): Token[][] {
  return text.split(/(?<=[。！？])/).map((s) => s.trim()).filter(Boolean).map((sent) => {
    const tokens: Token[] = [];
    const re = /\s*([A-Za-z]+)\s*|([^A-Za-z]+)/g;
    let m: RegExpExecArray | null;
    while ((m = re.exec(sent))) {
      if (m[1]) tokens.push({ w: m[1] });
      else if (m[2]) tokens.push({ t: m[2] });
    }
    return tokens.length ? tokens : [{ t: sent }];
  });
}
