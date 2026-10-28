import React from "react";
import { C, LAYOUT, UI, ZH } from "./theme";

/** 固定提示，放在卡片外面、卡片正下方。 */
export const Footer: React.FC<{ text: string; opacity?: number }> = ({ text, opacity = 1 }) => (
  <div style={{ position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top: LAYOUT.hintTop,
    textAlign: "center", color: C.onBg, fontFamily: ZH, fontSize: UI.footer, fontWeight: 500,
    letterSpacing: 1, lineHeight: 1.2, opacity }}>
    {text}
  </div>
);
