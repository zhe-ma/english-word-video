import { continueRender, delayRender, staticFile } from "remotion";

const FONTS: [family: string, file: string, weight: string][] = [
  ["Poppins", "Poppins-Regular.ttf", "400"],
  ["Poppins", "Poppins-Medium.ttf", "500"],
  ["Poppins", "Poppins-SemiBold.ttf", "600"],
  ["Poppins", "Poppins-Bold.ttf", "700"],
  ["Nunito", "Nunito-SemiBold.ttf", "600"],
  ["Nunito", "Nunito-Bold.ttf", "700"],
  ["Noto Sans SC", "NotoSansSC.ttf", "100 900"],
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
