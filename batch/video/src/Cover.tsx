import React from "react";
import { CoverFrame } from "./stage/Stage";
import type { Timeline } from "./types";

/** 封面和视频第一帧同一张：标题加这一条的第一个词。 */
export const Cover: React.FC<Timeline> = (tl) => <CoverFrame tl={tl} />;
