import React from "react";
import { AbsoluteFill } from "remotion";
import { Footer } from "./Footer";
import { Header } from "./Header";
import { Paper } from "./Paper";
import type { Timeline } from "./types";

/** 全文帧：和正文同一张纸、同一位置，注释全部展开。视频结尾停留。 */
export const Overview: React.FC<{ tl: Timeline }> = ({ tl }) => (
  <AbsoluteFill>
    <Header tl={tl} />
    <Paper tl={tl} t={null} />
    <Footer />
  </AbsoluteFill>
);
