import { PRESET_ID } from "./preset";

const POPPINS = `"Poppins", "Avenir Next", "Helvetica Neue", "Noto Sans SC", sans-serif`;
const NUNITO = `"Nunito", "Poppins", "Avenir Next", "Noto Sans SC", sans-serif`;

type Preset = {
  bg: string;
  card: string;
  ink: string;
  secondary: string;
  tertiary: string;
  /** 学习词底色；透明表示不铺底。 */
  word: string;
  en: string;
  enWeight: number;
  enFont: string;
  /** 学习词下划线，没有则空字符串。 */
  enLine: string;
  line: string;
  accent: string;
  gloss: string;
  pos: string;
  ipa: string;
  /** 深色底上的标题。不写则用 ink。 */
  title?: string;
  /** 深色底上的次要字，栏目名和卡片外提示。不写则用 secondary。 */
  onBg?: string;
  radius: number;
  shadow: string;
};

/** 五套只改颜色、英文样子和圆角，版心和字号共用。 */
export const PRESETS: Record<string, Preset> = {
  /** 现在这套：浅灰底白卡片，学习词加一层淡蓝。 */
  plain: {
    bg: "#2A2724", card: "#F7F4EF", ink: "#333333", secondary: "#888888", tertiary: "#888888",
    word: "transparent", en: "#002FA7", enWeight: 700, enFont: POPPINS, enLine: "",
    line: "rgba(0,0,0,0.05)", accent: "#002FA7", gloss: "#555555", pos: "#555555", ipa: "#666666",
    title: "#F6F3EE", onBg: "#C9C4BC",
    radius: 28, shadow: "0 18px 48px rgba(0,0,0,0.28)",
  },
  /** 简约，但英文本身用蓝色，不再靠大面积底色。 */
  focus: {
    bg: "#F6F4EF", card: "#FFFFFF", ink: "#1C1917", secondary: "#57534E", tertiary: "#57534E",
    word: "transparent", en: "#0B57D0", enWeight: 600, enFont: POPPINS, enLine: "",
    line: "rgba(0,0,0,0.05)", accent: "#0B57D0", gloss: "#1C1917", pos: "#44403C", ipa: "#44403C",
    radius: 24, shadow: "0 12px 32px rgba(60,40,20,0.06)",
  },
  /** 醒目：英文下面一条黄线，像刊头。 */
  poster: {
    bg: "#F3EFE4", card: "#FFFEFB", ink: "#141414", secondary: "#3F3F3F", tertiary: "#3F3F3F",
    word: "transparent", en: "#141414", enWeight: 600, enFont: POPPINS, enLine: "3px solid #F5C400",
    line: "rgba(0,0,0,0.08)", accent: "#F5C400", gloss: "#141414", pos: "#333333", ipa: "#333333",
    radius: 18, shadow: "0 10px 28px rgba(0,0,0,0.06)",
  },
  /** 软一点：暖底、圆体英文、浅杏色词底。 */
  soft: {
    bg: "#FFF1E8", card: "#FFFFFF", ink: "#4A342E", secondary: "#8C6458", tertiary: "#8C6458",
    word: "#FFE0C7", en: "#4A342E", enWeight: 700, enFont: NUNITO, enLine: "",
    line: "rgba(120,70,40,0.08)", accent: "#F0927A", gloss: "#9A3B2F", pos: "#6B453C", ipa: "#6B453C",
    radius: 32, shadow: "0 14px 36px rgba(180,100,60,0.08)",
  },
  /** 深色：英文用亮蓝，适合夜里刷。 */
  night: {
    bg: "#0E1014", card: "#181B22", ink: "#F4F4F5", secondary: "#C8C8CE", tertiary: "#C8C8CE",
    word: "transparent", en: "#8EBEFF", enWeight: 600, enFont: POPPINS, enLine: "",
    line: "rgba(255,255,255,0.08)", accent: "#8EBEFF", gloss: "#FFFFFF", pos: "#E4E4EA", ipa: "#E4E4EA",
    radius: 22, shadow: "none",
  },
};

const P = PRESETS[PRESET_ID] ?? PRESETS.plain;

export const C = {
  bg: P.bg,
  card: P.card,
  ink: P.ink,
  secondary: P.secondary,
  tertiary: P.tertiary,
  word: P.word,
  en: P.en,
  enWeight: P.enWeight,
  enLine: P.enLine,
  line: P.line,
  accent: P.accent,
  title: P.title ?? P.ink,
  onBg: P.onBg ?? P.secondary,
  radius: P.radius,
  shadow: P.shadow,
};

export const HL = {
  yellow: "#E8E8ED",
  green: "#E8E8ED",
  pink: "#E8E8ED",
  blue: "#E8E8ED",
} as const;

export const ANNO = { pos: P.pos, ipa: P.ipa, gloss: P.gloss, gap: "0.1em" };

export const HEADER_LABEL = "雅思单词学习";
export const FOOTER_HINT = "不熟悉的单词，评论区打出来";

export const ZH = `"Noto Sans SC", "PingFang SC", "Source Han Sans SC", sans-serif`;
export const EN = P.enFont;
export const IPA_FONT = `"Lucida Grande", "Arial Unicode MS", ${EN}`;

export const UI = { label: 44, footer: 42, footerH: 64 };

/**
 * 抖音信息流安全区（1080×1920，比例仍是 9:16）。
 * 画布比例没问题，会被挡住的是播放器叠层：
 * - 顶 236：状态栏 +「直播 / 同城 / 关注 / 推荐」
 * - 底 412：昵称、文案、音乐、底栏
 * - 右 176：头像、赞、评论、收藏、分享
 * - 左 56：边距
 * 卡片宽高由这块安全区算出来，换文案不用改这里。
 */
export const SAFE = { top: 236, right: 176, bottom: 412, left: 56 };
const CANVAS_H = 1920;
const LABEL_TOP = SAFE.top - 16;
const LABEL_BOX = 52;
const TITLE_GAP = 8;
const TITLE_BOX = 64;
const CARD_GAP = 56;

export const LAYOUT = {
  /** 标题靠上，卡片从标题下方留出空隙再开始，两者不重叠。 */
  labelTop: LABEL_TOP,
  titleTop: LABEL_TOP + LABEL_BOX + TITLE_GAP,
  cardLeft: SAFE.left,
  cardRight: SAFE.right,
  cardTop: LABEL_TOP + LABEL_BOX + TITLE_GAP + TITLE_BOX + CARD_GAP,
  cardBottom: CANVAS_H - SAFE.bottom - 56,
  hintTop: CANVAS_H - SAFE.bottom - 48,
  coverLabelTop: LABEL_TOP,
  coverTitleTop: LABEL_TOP + LABEL_BOX + TITLE_GAP,
  coverCardTop: LABEL_TOP + LABEL_BOX + TITLE_GAP + 188,
  coverCardBottom: CANVAS_H - SAFE.bottom - 56,
};

/**
 * 字号（--s）和行距（--lh）由 FitBox 按卡片高度选取。
 * lineHeight 是能放下下方注释的最小行距，lineHeightMax 是有空余时拉开的上限。
 * anno 为注释相对正文的字号比例。
 */
export const TEXT = { size: 42, lineHeight: 2.45, lineHeightMax: 3.15, anno: 0.7, min: 0.68, max: 1.12 };
