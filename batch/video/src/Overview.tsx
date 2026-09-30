import React from "react";
import { AbsoluteFill } from "remotion";
import { TextCard } from "./FocusCard";
import { Header } from "./Header";
import { Paper } from "./Paper";
import type { Timeline } from "./types";

/**
 * 全文帧：和正文同一张纸、同一位置，所有学习项都已高亮、释义标签全部展开。
 * 视频结尾停留；封面复用时不显示顶部和卡片，由大标题覆盖。
 */
export const Overview: React.FC<{ tl: Timeline; showHeader?: boolean }> = ({ tl, showHeader = true }) => (
  <AbsoluteFill>
    {showHeader ? (
      <>
        <Header tl={tl} learned={tl.items.length} />
        <TextCard title={`${tl.items.length} 个词都在这儿了`} sub={tl.hint} />
      </>
    ) : null}
    <Paper tl={tl} t={null} />
  </AbsoluteFill>
);
