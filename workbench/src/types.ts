export type Level = { key: string; label: string };
export type Voice = { id: string; label: string };

export type Meta = {
  levels: Level[];
  voices: Voice[];
  defaultVoice: string;
  defaultRate: string;
  hanziRange: [number, number];
  wordsRange: [number, number];
  readingRange: [number, number];
  reviewKeys: string[];
  reviewPass: { total: number; min: number; hook: number; punchline: number };
};

export type Stats = {
  lexicon: number;
  usedWords: number;
  episodes: number;
  published: number;
  videos: number;
  remaining: Record<string, number>;
};

export type ThemeItem = { theme: string; genre?: string; usedBy?: string };
export type ThemeGroup = { group: string; items: ThemeItem[] };

export type Defaults = {
  level: string;
  theme: string;
  genre: string;
  words: number;
  voice: string;
  rate: string;
};

export type EpisodeRow = {
  id: string;
  theme: string;
  level: string;
  genre: string;
  steps: string[];
  publishedAt?: string;
  words: string[];
  text: string;
  cover?: string | null;
  video?: string | null;
};

export type WordHit = {
  word: string;
  ipa?: string;
  senses: string;
  inLevel?: boolean;
  used?: boolean;
  tag?: string;
  frq?: number;
  episodes?: { id: string; theme: string; published: boolean; review: boolean; meaning: string }[];
};

export type Plan = {
  id: string;
  series: string;
  level: string;
  level_key: string;
  theme: string;
  remaining_new_words: number;
  candidates: { word: string; ipa: string; senses: string }[];
  review_due: { word: string; ipa: string; senses: string }[];
  recent: { id: string; theme: string; genre: string; ending: string }[];
  picked: string[];
  voice?: string;
  rate?: string;
};

export type Token = { t: string } | { w: string };
export type ScriptWord = { word: string; pos: string; meaning: string; review?: boolean };
export type Script = {
  id: string;
  series?: string;
  level: string;
  theme: string;
  genre: string;
  review?: Record<string, number>;
  sentences: Token[][];
  words: ScriptWord[];
  layout?: { fontScale?: number };
  published_at?: string;
};

export type Report = { ok: boolean; errors: string[]; warnings: string[]; hanzi: number | null; text?: string };
export type QA = { ok: boolean; reading: number; errors: string[]; warnings: string[] };

export type EpisodeDetail = {
  id: string;
  steps: string[];
  plan: Plan | null;
  script: Script | null;
  drafts: string | null;
  report: Report | null;
  qa: QA | null;
  timeline: {
    reading: number;
    total: number;
    voice?: string;
    rate?: string;
    stale?: boolean;
    interp?: string[];
  } | null;
  files: {
    audio?: string | null;
    video?: string | null;
    cover?: string | null;
    frames: { name: string; url: string }[];
  };
};

export type EpFile = {
  path: string;
  name: string;
  size: number;
  mtime: number;
  kind: "source" | "artifact";
  url?: string | null;
};

export type Job = {
  id: string;
  ep: string;
  title: string;
  status: "running" | "done" | "failed";
  lines: string[];
  next: number;
  failed_step?: string | null;
};

export type UsageRow = {
  word: string;
  times: number;
  reviewTimes: number;
  published: boolean;
  meaning: string;
  lastId: string;
  lastTheme: string;
  episodes: { id: string; theme: string; published: boolean; review: boolean; meaning: string }[];
};

export type LexiconPage = {
  total: number;
  page: number;
  limit: number;
  level: string;
  items: WordHit[];
};

export type PreviewResult = {
  source: "tts" | "estimate";
  timeline: Record<string, unknown> & { durationInFrames: number; fps: number; audioSrc?: string };
};
