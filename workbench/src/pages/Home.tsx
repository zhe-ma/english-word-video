import { useEffect, useState } from "react";
import { api, media } from "../api";
import type { Defaults, EpisodeRow, Meta, Stats, ThemeGroup } from "../types";

function stepLabel(steps: string[], published?: string) {
  if (published) return "已入库";
  if (steps.includes("video")) return "已出片";
  if (steps.includes("tts")) return "已配音";
  if (steps.includes("script")) return "已有文案";
  return "筹划中";
}

export function HomePage({ meta, stats, go }: { meta: Meta; stats: Stats | null; go: (p: string) => void }) {
  const [eps, setEps] = useState<EpisodeRow[]>([]);
  const [themes, setThemes] = useState<ThemeGroup[]>([]);
  const [level, setLevel] = useState("cet4");
  const [theme, setTheme] = useState("");
  const [words, setWords] = useState(6);
  const [voice, setVoice] = useState(meta.defaultVoice);
  const [rate, setRate] = useState(meta.defaultRate);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const loadDefaults = (lv: string) => {
    api.get<Defaults>(`/api/defaults?level=${lv}`).then((d) => {
      setTheme(d.theme);
      setWords(d.words);
      setVoice(d.voice);
      setRate(d.rate);
    });
  };

  useEffect(() => {
    api.get<EpisodeRow[]>("/api/episodes").then(setEps);
    api.get<ThemeGroup[]>("/api/themes").then(setThemes);
    loadDefaults(level);
  }, []);

  const create = async () => {
    setBusy(true); setErr("");
    try {
      const r = await api.send<{ id: string }>("/api/episodes", "POST", { level, theme, words, voice, rate });
      go(`/ep/${r.id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1>工作台</h1>
      <p className="sub">点一次就出一期底稿：自动选题、选词、写三稿、生成定稿。你只改不满意的地方。配音和出片仍要确认后点。</p>

      {stats && (
        <div className="stats">
          <div className="stat"><b>{stats.episodes}</b><span>期目录</span></div>
          <div className="stat"><b>{stats.published}</b><span>已入库</span></div>
          <div className="stat"><b>{stats.videos}</b><span>已出片</span></div>
          <div className="stat"><b>{stats.usedWords}</b><span>已用单词</span></div>
          <div className="stat"><b>{stats.lexicon.toLocaleString()}</b><span>词库条目</span></div>
        </div>
      )}

      <div className="card">
        <h2>新建一期</h2>
        <div className="row">
          <label className="lbl">级别
            <select value={level} onChange={(e) => { setLevel(e.target.value); loadDefaults(e.target.value); }}>
              {meta.levels.map((l) => <option key={l.key} value={l.key}>{l.label}</option>)}
            </select>
          </label>
          <label className="lbl" style={{ flex: 1, minWidth: 220 }}>主题（已自动选下一档未用过的）
            <input list="themes" value={theme} onChange={(e) => setTheme(e.target.value)} />
            <datalist id="themes">
              {themes.flatMap((g) => g.items.map((it) => (
                <option key={it.theme} value={it.theme} />
              )))}
            </datalist>
          </label>
          <button className="btn primary" disabled={busy} onClick={create}>{busy ? "生成底稿…" : "创建一期"}</button>
        </div>
        <details style={{ marginTop: 12 }}>
          <summary className="muted">调节默认值</summary>
          <div className="row" style={{ marginTop: 10 }}>
            <label className="lbl">词数
              <input type="number" min={4} max={8} value={words} onChange={(e) => setWords(Number(e.target.value))} />
            </label>
            <label className="lbl">音色
              <select value={voice} onChange={(e) => setVoice(e.target.value)}>
                {meta.voices.map((v) => <option key={v.id} value={v.id}>{v.label}</option>)}
              </select>
            </label>
            <label className="lbl">语速
              <input value={rate} onChange={(e) => setRate(e.target.value)} />
            </label>
          </div>
        </details>
        {err && <p className="err">{err}</p>}
      </div>

      <h2>往期</h2>
      <div className="archive">
        {eps.map((e) => (
          <a key={e.id} className="ep-card" href={`/ep/${e.id}`} onClick={(ev) => { ev.preventDefault(); go(`/ep/${e.id}`); }}>
            {e.cover && <img className="cover" src={media(e.cover)} alt="" />}
            <h3>Vol.{e.id}　{e.theme || "未定主题"}</h3>
            <div className="muted">{e.level} · {e.genre || "未定形态"} · {stepLabel(e.steps, e.publishedAt)}</div>
            {!!e.words.length && (
              <div className="chips" style={{ marginTop: 8 }}>
                {e.words.map((w) => <span key={w} className="pill">{w}</span>)}
              </div>
            )}
            {e.text && <p className="quote">{e.text}</p>}
            {e.video && <span className="pill ok">有成片</span>}
          </a>
        ))}
      </div>
      {!eps.length && <p className="muted">还没有期，点上面的创建即可。</p>}
    </>
  );
}
