import type { HL } from "./theme";

export type Token =
  | { t: string }
  | { en: string }
  | { i: number; text: string; start?: number; end?: number };

export type Page = { start: number; end: number; tokens: Token[] };

export type Item = {
  en: string;
  pos: string;
  gloss: string;
  /** 词卡上的更多释义。正文只显示 gloss。 */
  senses?: string[];
  kind: "word" | "phrase";
  ipa: string;
  syllables: string;
  color: keyof typeof HL;
};

export type Entry = { i: number; start: number; enEnd: number; end: number };

export type Timeline = {
  id: string;
  /** 栏目名，画面左上角 */
  series: string;
  title: string;
  cover: string[];
  /** 卡片下方的固定提示 */
  footer: string;
  items: Item[];
  pages: Page[];
  review: { start: number; end: number; groups: { start: number; end: number; entries: Entry[] }[] };
  overview: { start: number; end: number };
  fps: number;
  durationInFrames: number;
  estimated?: boolean;
  audioSrc?: string;
};
