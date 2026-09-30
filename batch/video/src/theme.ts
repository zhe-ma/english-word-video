export const C = {
  bg: "#2B2A33",
  paper: "#FFFBF2",
  ink: "#1F1B16",
  grid: "rgba(120, 100, 70, .09)",
  muted: "#7a7367",
};

export const HL = {
  yellow: "#FFE45C",
  green: "#9EF0B0",
  pink: "#FFB3D1",
  blue: "#A9D8FF",
} as const;

/** 正文里的荧光笔底色，比 HL.yellow 淡，避免整段一片黄。 */
export const MARK = "#FFEFA6";

export const ZH = `"Noto Sans SC", "PingFang SC", "Source Han Sans SC", sans-serif`;
export const EN = `"Poppins", "Avenir Next", "Helvetica Neue", ${ZH}`;
export const IPA_FONT = `"Lucida Grande", "Arial Unicode MS", ${EN}`;

/** 1080×1920 竖屏上各块的位置（px）。正文纸张在正文、全文帧、封面里位置一致。 */
export const LAYOUT = {
  headerTop: 70,
  cardTop: 270,
  cardHeight: 180,
  paperTop: 490,
  paperBottom: 1800,
  hintTop: 1832,
};

/** 正文基准字号；FitBox 在 [min, max] 倍之间取能放下的最大值。gloss 为释义相对正文的字号比例。 */
export const TEXT = { size: 52, lineHeight: 1.85, gloss: 0.8, min: 0.7, max: 1.25 };
