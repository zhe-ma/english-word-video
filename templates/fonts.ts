import { continueRender, delayRender, staticFile } from "remotion";

const FONTS: [family: string, file: string, weight: string][] = [
  ["Poppins", "Poppins-Regular.woff2", "400"],
  ["Poppins", "Poppins-Medium.woff2", "500"],
  ["Poppins", "Poppins-SemiBold.woff2", "600"],
  ["Poppins", "Poppins-Bold.woff2", "700"],
  ["Noto Sans SC", "NotoSansSC.woff2", "400 700"],
];

const handle = delayRender("load fonts");

/** 字体加载完成（失败也算完成，回退系统字体）。排版测量要等它。 */
export const fontsReady: Promise<void> = Promise.all(
  FONTS.map(([family, file, weight]) =>
    new FontFace(family, `url('${staticFile(`fonts/${file}`)}')`, { weight })
      .load()
      .then((f) => {
        document.fonts.add(f);
      })
      .catch(() => console.warn(`字体加载失败，回退系统字体：${file}`)),
  ),
).then(() => {
  continueRender(handle);
});
