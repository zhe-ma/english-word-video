import { lazy, Suspense } from "react";
import type { PreviewResult } from "./types";

const PlayerView = lazy(async () => {
  const [{ Player }, { MarkerNotes }] = await Promise.all([
    import("@remotion/player"),
    import("@video/MarkerNotes"),
  ]);
  return {
    default: function PlayerView({ data }: { data: PreviewResult }) {
      const tl = {
        ...data.timeline,
        audioSrc: data.timeline.audioSrc ? `/${data.timeline.audioSrc}` : undefined,
      };
      return (
        <Player
          component={MarkerNotes}
          inputProps={tl}
          durationInFrames={Math.max(1, tl.durationInFrames || 1)}
          fps={tl.fps || 30}
          compositionWidth={1080}
          compositionHeight={1920}
          style={{ width: "100%", height: "100%" }}
          controls
          autoPlay={false}
        />
      );
    },
  };
});

export function Preview({ data }: { data: PreviewResult | null }) {
  if (!data) return <div className="player" />;
  return (
    <Suspense fallback={<div className="player muted" style={{ padding: 16 }}>载入预览…</div>}>
      <PlayerView data={data} />
    </Suspense>
  );
}
