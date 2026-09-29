import { continueRender, delayRender, staticFile } from "remotion";

const FONTS: [family: string, file: string, weight: string][] = [
  ["Poppins", "Poppins-SemiBold.ttf", "600"],
  ["Poppins", "Poppins-ExtraBold.ttf", "800"],
  ["Noto Sans SC", "NotoSansSC.ttf", "100 900"],
];

const handle = delayRender("load fonts");

Promise.all(
  FONTS.map(([family, file, weight]) =>
    new FontFace(family, `url('${staticFile(`fonts/${file}`)}')`, { weight })
      .load()
      .then((f) => document.fonts.add(f))
      .catch(() => console.warn(`字体加载失败，回退系统字体：${file}`)),
  ),
).then(() => continueRender(handle));
