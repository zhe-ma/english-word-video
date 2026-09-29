export type Token = { t: string } | { w: number };

export type Sentence = { start: number; end: number; tokens: Token[] };

export type Word = {
  word: string;
  ipa: string;
  syllables: string;
  pos: string;
  meaning: string;
  color: "yellow" | "green" | "pink" | "blue";
  review?: boolean;
  start: number;
  end: number;
};

export type Timeline = {
  meta: { id: string; series: string; level: string; theme: string };
  layout?: { fontScale?: number };
  fps: number;
  durationInFrames: number;
  reading: { start: number; end: number };
  summary: { start: number; end: number };
  sentences: Sentence[];
  words: Word[];
  audioSrc?: string;
};
