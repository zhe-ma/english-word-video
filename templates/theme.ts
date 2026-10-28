const POPPINS = `"Poppins", "Avenir Next", "Helvetica Neue", "Segoe UI", "Noto Sans SC", sans-serif`;

/** 配色与圆角。画面只有这一套风格：深色底、暖白卡片、深蓝英文。 */
const P = {
  bg: "#2A2724", card: "#F7F4EF", ink: "#333333", secondary: "#888888", tertiary: "#888888",
  word: "transparent", en: "#002FA7", enWeight: 700, enFont: POPPINS, enLine: "",
  line: "rgba(0,0,0,0.05)", accent: "#002FA7", gloss: "#555555", pos: "#555555", ipa: "#5E5E5E",
  title: "#F6F3EE", onBg: "#C9C4BC",
  radius: 28, shadow: "0 18px 48px rgba(0,0,0,0.28)",
};

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
  title: P.title,
  onBg: P.onBg,
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

export const ZH = `"Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Source Han Sans SC", sans-serif`;
export const EN = P.enFont;
export const IPA_FONT = `"Lucida Grande", "Segoe UI", "Arial Unicode MS", ${EN}`;

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
export const TEXT = { size: 42, lineHeight: 3.3, lineHeightMax: 3.8, anno: 0.7, ipa: 0.92, min: 0.55, max: 1.12 };
