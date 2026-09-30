import { staticFile } from "remotion";

/** 渲染用 staticFile；工作台预览传入 /media/... 绝对路径。 */
export function resolveMedia(src?: string) {
  if (!src) return undefined;
  if (/^(https?:|blob:|data:|\/)/.test(src)) return src;
  return staticFile(src);
}
