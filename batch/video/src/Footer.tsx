import React from "react";
import { C, FOOTER_HINT, LAYOUT, UI, ZH } from "./theme";

/** 固定提示，放在卡片外面、卡片正下方。 */
export const Footer: React.FC<{ opacity?: number }> = ({ opacity = 1 }) => (
  <div style={{ position: "absolute", left: LAYOUT.cardLeft, right: LAYOUT.cardRight, top: LAYOUT.hintTop,
    textAlign: "center", color: C.onBg, fontFamily: ZH, fontSize: UI.footer, fontWeight: 500,
    letterSpacing: 1, lineHeight: 1.2, opacity }}>
    {FOOTER_HINT}
  </div>
);
