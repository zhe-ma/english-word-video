import React, { useLayoutEffect, useRef, useState } from "react";
import { continueRender, delayRender, getRemotionEnvironment } from "remotion";
import { fontsReady } from "./fonts";

/**
 * 在 [min, max] 之间找能放下内容的最大 CSS 变量 --s（子元素字号都乘以它）：
 * 短文案放大填满，长文案缩小放下。字体加载完、容器有了宽度之后测量一次。
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
      let s = max;
      el.style.setProperty("--s", String(s));
      while (el.scrollHeight > height + 1 && s > min) {
        s = Math.max(min, +(s - 0.02).toFixed(2));
        el.style.setProperty("--s", String(s));
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
