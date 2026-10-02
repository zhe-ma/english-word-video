import React, { useLayoutEffect, useRef, useState } from "react";
import { continueRender, delayRender, getRemotionEnvironment } from "remotion";
import { fontsReady } from "./fonts";
import { TEXT } from "./theme";

/** 除最后一行外，行尾空出超过两成宽度的行数。用来判断字号是否大到把词组挤到了下一行。 */
const raggedLines = (root: HTMLElement) => {
  const box = root.getBoundingClientRect();
  const rows = new Map<number, number>();
  root.querySelectorAll<HTMLElement>("[data-piece]").forEach((el) => {
    for (const r of el.getClientRects()) {
      const key = Math.round(r.top);
      rows.set(key, Math.max(rows.get(key) ?? 0, r.right - box.left));
    }
  });
  const ends = [...rows.entries()].sort((a, b) => a[0] - b[0]).map(([, right]) => right);
  if (ends.length <= 1) return 0;
  return ends.slice(0, -1).filter((right) => box.width - right > box.width * 0.22).length;
};

/**
 * 在卡片高度里选字号（--s）和行距（--lh）。
 * 先用能放下注释的最小行距，取放得下的最大字号；若字号太大导致行尾大片空白，就略缩小，让一行排进更多字。
 * 高度还有余，再把行距拉开，把卡片填满。
 */
export const FitBox: React.FC<{ height: number; min?: number; max?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({
  height, min = 0.5, max = 1, style, children,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const [handle] = useState(() => delayRender("fit text"));
  const done = useRef(false);

  useLayoutEffect(() => {
    let alive = true;
    let tries = 0;
    const finish = () => {
      if (!done.current) {
        done.current = true;
        continueRender(handle);
      }
    };
    const fit = () => {
      const el = ref.current;
      if (!alive || !el) return;
      if (el.clientWidth === 0 && tries++ < 120) {
        requestAnimationFrame(fit);
        return;
      }
      const lhMin = TEXT.lineHeight;
      const lhMax = TEXT.lineHeightMax;
      let s = max;
      el.style.setProperty("--s", String(s));
      el.style.setProperty("--lh", String(lhMin));
      while (el.scrollHeight > height + 1 && s > min) {
        s = Math.max(min, +(s - 0.02).toFixed(2));
        el.style.setProperty("--s", String(s));
      }
      let best = { s, rag: raggedLines(el) };
      for (let step = 0; step < 8 && s - 0.02 >= min; step++) {
        const next = +(s - 0.02).toFixed(2);
        el.style.setProperty("--s", String(next));
        if (el.scrollHeight > height + 1) break;
        s = next;
        const rag = raggedLines(el);
        if (rag < best.rag) best = { s, rag };
        if (rag === 0) break;
      }
      s = best.s;
      el.style.setProperty("--s", String(s));
      let lh = lhMin;
      while (lh < lhMax) {
        const next = Math.min(lhMax, +(lh + 0.04).toFixed(2));
        el.style.setProperty("--lh", String(next));
        if (el.scrollHeight > height + 1) {
          el.style.setProperty("--lh", String(lh));
          break;
        }
        lh = next;
      }
      finish();
    };
    // Studio 里改代码热更新时内容会变，需要重新测量；渲染时只测一次保证每帧一致。
    let observer: ResizeObserver | undefined;
    fontsReady.then(() => {
      fit();
      const child = ref.current?.firstElementChild;
      if (alive && child && getRemotionEnvironment().isStudio) {
        let pending = false;
        observer = new ResizeObserver(() => {
          if (pending) return;
          pending = true;
          requestAnimationFrame(() => {
            pending = false;
            fit();
          });
        });
        observer.observe(child);
      }
    });
    return () => {
      alive = false;
      observer?.disconnect();
      finish();
    };
  }, [handle, height, min, max]);

  return (
    <div ref={ref} style={{ height, overflow: "hidden", ...style }}>
      {children}
    </div>
  );
};

/** 基准像素 × 当前缩放。 */
export const px = (n: number) => `calc(var(--s, 1) * ${n}px)`;
