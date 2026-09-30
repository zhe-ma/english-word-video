import { useCallback, useEffect, useRef, useState } from "react";
import { api, media } from "../api";
import { emptyDrafts, formatDrafts, GENRES, mixedToSentences, parseDrafts, type Draft } from "../drafts";
import { Preview } from "../Preview";
import type { EpisodeDetail, EpFile, Job, Meta, PreviewResult, Report, Script, Token, WordHit } from "../types";

const STEPS = ["plan", "drafts", "script", "valid", "tts", "qa", "video", "committed"];
const POS = ["n.", "v.", "vt.", "vi.", "adj."];

function blankScript(id: string, theme: string, level: string): Script {
  return {
    id, series: "一分钟情景单词", level, theme, genre: "吐槽小剧场",
    review: { hook: 4, relatable: 4, punchline: 4, fresh: 4, natural: 4, accurate: 4 },
    sentences: [[{ t: "" }]],
    words: [],
  };
}

function syncWords(s: Script): Script {
  const toks = s.sentences.flatMap((sent) => sent.filter((tk): tk is { w: string } => "w" in tk).map((tk) => tk.w));
  const by = Object.fromEntries(s.words.map((w) => [w.word.toLowerCase(), w]));
  return { ...s, words: toks.map((w) => by[w.toLowerCase()] || { word: w, pos: "n.", meaning: "" }) };
}

function scriptLine(s: Script) {
  return s.sentences.map((sent) => sent.map((tk) => ("w" in tk ? tk.w : tk.t)).join("")).join("");
}

export function EpisodePage({ id, meta, go }: { id: string; meta: Meta; go: (p: string) => void }) {
  const [ep, setEp] = useState<EpisodeDetail | null>(null);
  const [files, setFiles] = useState<EpFile[]>([]);
  const [script, setScript] = useState<Script | null>(null);
  const [draftItems, setDraftItems] = useState<Draft[]>([]);
  const [draftTail, setDraftTail] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [search, setSearch] = useState("");
  const [hits, setHits] = useState<WordHit[]>([]);
  const [voice, setVoice] = useState(meta.defaultVoice);
  const [rate, setRate] = useState(meta.defaultRate);
  const [job, setJob] = useState<Job | null>(null);
  const [msg, setMsg] = useState("");
  const [picking, setPicking] = useState(false);
  const [booting, setBooting] = useState(false);
  const poll = useRef<number>(0);

  const reload = useCallback(async () => {
    const d = await api.get<EpisodeDetail>(`/api/episodes/${id}`);
    setEp(d);
    setReport(d.report);
    if (d.script) setScript(d.script);
    else if (d.plan) setScript(blankScript(id, d.plan.theme, d.plan.level));
    const picked = (d.plan?.picked || []).map((w) => (typeof w === "string" ? w : String(w)));
    if (d.drafts) {
      const parsed = parseDrafts(d.drafts);
      setDraftItems(parsed.items.length ? parsed.items : emptyDrafts(picked));
      setDraftTail(parsed.tail);
    } else {
      setDraftItems(emptyDrafts(picked));
      setDraftTail("");
    }
    if (d.plan?.voice) setVoice(d.plan.voice);
    if (d.plan?.rate) setRate(d.plan.rate);
    api.get<EpFile[]>(`/api/episodes/${id}/files`).then(setFiles);
    return d;
  }, [id]);

  useEffect(() => { reload(); }, [reload]);

  useEffect(() => {
    if (!script?.sentences?.length) return;
    const t = window.setTimeout(() => {
      api.send<PreviewResult>(`/api/episodes/${id}/preview`, "POST", { script }).then(setPreview).catch(() => {});
      api.send<Report>(`/api/episodes/${id}/check`, "POST", script).then(setReport).catch(() => {});
    }, 400);
    return () => clearTimeout(t);
  }, [id, script]);

  const watch = (j: Job) => {
    setJob(j);
    window.clearInterval(poll.current);
    poll.current = window.setInterval(async () => {
      const next = await api.get<Job>(`/api/jobs/${j.id}?since=0`);
      setJob(next);
      if (next.status !== "running") {
        window.clearInterval(poll.current);
        reload();
      }
    }, 800);
  };

  const run = async (steps: { cmd: string; args?: string[] }[]) => {
    setMsg("");
    try {
      const j = await api.send<Job>(`/api/episodes/${id}/run`, "POST", { steps });
      watch(j);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    }
  };

  if (!ep) return <p className="muted">加载 {id}…</p>;
  const plan = ep.plan;
  const pickedList = (plan?.picked || []).map((w) => (typeof w === "string" ? w : String(w)));
  const picked = new Set(pickedList);
  const levelKey = plan?.level_key || "cet4";
  const full = script && script.sentences[0] && ("t" in script.sentences[0][0] || "w" in script.sentences[0][0])
    ? scriptLine(script) : "";

  const togglePick = async (word: string) => {
    if (!plan) return;
    const next = picked.has(word) ? pickedList.filter((w) => w !== word) : [...pickedList, word];
    await api.send(`/api/episodes/${id}/plan`, "PUT", { picked: next });
    reload();
  };

  const savePlan = async (patch: object) => {
    await api.send(`/api/episodes/${id}/plan`, "PUT", patch);
    reload();
  };

  const autoPick = async () => {
    setPicking(true); setMsg("");
    try {
      await api.send(`/api/episodes/${id}/autopick`, "POST", { level: levelKey, theme: plan?.theme, n: 6 });
      await reload();
      setMsg("已按主题选好 6 个词，不满意再点一次换一批");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setPicking(false);
    }
  };

  const saveDrafts = async () => {
    const text = formatDrafts(id, script?.theme || plan?.theme || "", script?.level || plan?.level || "", draftItems, draftTail);
    await api.send(`/api/episodes/${id}/drafts`, "PUT", { text });
    setMsg("草稿已保存");
  };

  const adopt = async (d: Draft) => {
    if (!script) return;
    const sentences = mixedToSentences(d.text);
    const names = sentences.flatMap((sent) => sent.filter((tk): tk is { w: string } => "w" in tk).map((tk) => tk.w));
    const words = [];
    for (const w of names) {
      const info = await api.get<{ senses?: { pos: string; text: string }[] }>(`/api/lookup?word=${encodeURIComponent(w)}&level=${levelKey}`);
      const sense = info.senses?.[0];
      const meaning = (sense?.text || "").split(/[，,；;、]/)[0].slice(0, 8);
      words.push({ word: w, pos: sense?.pos || "n.", meaning, review: false });
    }
    setScript(syncWords({ ...script, genre: d.genre, sentences, words }));
    setMsg(`已采用「${d.genre}」稿，检查释义后保存校验`);
  };

  const saveScript = async () => {
    if (!script) return;
    const r = await api.send<{ report: Report }>(`/api/episodes/${id}/script`, "PUT", syncWords(script));
    setReport(r.report);
    setMsg(r.report.ok ? "文案已保存，校验通过" : "文案已保存，校验未通过");
    reload();
  };

  const find = async () => {
    const rows = await api.get<WordHit[]>(`/api/words?q=${encodeURIComponent(search)}&level=${levelKey}&limit=12`);
    setHits(rows);
  };

  const setSent = (i: number, tokens: Token[]) => {
    if (!script) return;
    setScript(syncWords({ ...script, sentences: script.sentences.map((s, k) => (k === i ? tokens : s)) }));
  };

  const setDraft = (i: number, patch: Partial<Draft>) => {
    setDraftItems(draftItems.map((d, k) => (k === i ? { ...d, ...patch } : d)));
  };

  return (
    <>
      <div className="row spread">
        <div>
          <h1>第 {id} 期 {script?.theme || plan?.theme || ""}</h1>
          <p className="sub">{script?.level || plan?.level} · {script?.genre || "未定形态"}
            {script?.published_at ? " · 已入库" : ""}</p>
        </div>
        <div className="row">
          {!script?.published_at && (
            <button className="btn" disabled={booting} onClick={async () => {
              setBooting(true);
              try {
                await api.send(`/api/episodes/${id}/bootstrap`, "POST", {
                  level: levelKey, theme: plan?.theme, words: 6, voice, rate,
                });
                await reload();
                setMsg("已按默认重做选题、选词、三稿和定稿，请再改一改");
              } catch (e) {
                setMsg(e instanceof Error ? e.message : String(e));
              } finally {
                setBooting(false);
              }
            }}>{booting ? "重做中…" : "按默认重做底稿"}</button>
          )}
          <button className="btn ghost" onClick={() => go("/")}>返回往期</button>
        </div>
      </div>

      <div className="steps">
        {STEPS.map((s) => <span key={s} className={`pill ${ep.steps.includes(s) ? "on" : ""}`}>{s}</span>)}
      </div>

      {full && (
        <div className="card paper">
          <h2>本期文案</h2>
          <p style={{ fontSize: 16, lineHeight: 1.7, margin: "0 0 12px" }}>{full}</p>
          <div className="chips">
            {(script?.words || []).map((w) => (
              <span key={w.word} className="chip on" style={{ minWidth: 0 }}>
                <b>{w.word}</b><small>{w.pos} {w.meaning}{w.review ? " · 复习" : ""}</small>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="studio">
        <div>
          <div className="card">
            <h2>1. 选词</h2>
            {plan && (
              <>
                <div className="row" style={{ marginBottom: 12 }}>
                  <label className="lbl">主题
                    <input defaultValue={plan.theme} key={plan.theme}
                      onBlur={(e) => { if (e.target.value !== plan.theme) savePlan({ theme: e.target.value }); }} />
                  </label>
                  <button className="btn primary" disabled={picking} onClick={autoPick}>
                    {picking ? "选词中…" : pickedList.length ? "换一批" : "按主题自动选词"}
                  </button>
                </div>
                <p className="muted">平台按主题从词库挑 6 个未用词（可含到期复习词）。不必从候选里手点。</p>
                <div className="chips">
                  {pickedList.map((w) => (
                    <div key={w} className="chip on" onClick={() => togglePick(w)}><b>{w}</b><small>再点去掉</small></div>
                  ))}
                </div>
                <details style={{ marginTop: 14 }}>
                  <summary className="muted">自己改词</summary>
                  <div className="row" style={{ margin: "10px 0" }}>
                    <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="中文释义或英文前缀"
                      onKeyDown={(e) => e.key === "Enter" && find()} />
                    <button className="btn" onClick={find}>查词</button>
                    <button className="btn ghost" onClick={() => api.send(`/api/episodes/${id}/replan`, "POST", { level: levelKey, theme: plan.theme }).then(reload)}>重抽候选</button>
                  </div>
                  {!!hits.length && (
                    <div className="chips">
                      {hits.map((h) => (
                        <div key={h.word} className={`chip ${picked.has(h.word) ? "on" : ""}`} onClick={() => togglePick(h.word)}>
                          <b>{h.word}</b><small>{h.inLevel ? "词表内" : "词表外"} {h.used ? "用过" : ""} · {h.senses}</small>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="chips" style={{ marginTop: 8 }}>
                    {(plan.candidates || []).map((c) => (
                      <div key={c.word} className={`chip ${picked.has(c.word) ? "on" : ""}`} onClick={() => togglePick(c.word)}>
                        <b>{c.word}</b><small>{c.senses}</small>
                      </div>
                    ))}
                  </div>
                </details>
              </>
            )}
          </div>

          <div className="card">
            <div className="row spread">
              <h2>2. 写 3 稿</h2>
              <button className="btn" onClick={saveDrafts}>保存草稿</button>
            </div>
            <div className="hint">
              用 3 种形态各写一段中英混读。4–7 句，大约 50 个汉字；英文单词用原形嵌进句子，最后一句不放单词。
              第一句要有画面，结尾反转或自嘲，不解释笑点。例：外卖刷了四十分钟，我还在hesitate。
              写完点「采用此稿」，会拆成下面的定稿句子。
            </div>
            {draftItems.map((d, i) => (
              <div key={i} className="draft-box">
                <div className="row" style={{ marginBottom: 8 }}>
                  <label className="lbl">形态
                    <select value={d.genre} onChange={(e) => setDraft(i, { genre: e.target.value })}>
                      {GENRES.map((g) => <option key={g}>{g}</option>)}
                    </select>
                  </label>
                  <label className="lbl" style={{ flex: 1 }}>用到的词
                    <input value={d.words} onChange={(e) => setDraft(i, { words: e.target.value })}
                      placeholder={pickedList.join(", ")} />
                  </label>
                  <button className="btn ghost" disabled={!d.text.trim()} onClick={() => adopt(d)}>采用此稿</button>
                </div>
                <textarea value={d.text} onChange={(e) => setDraft(i, { text: e.target.value })}
                  placeholder={`第 ${i + 1} 稿。把 ${pickedList.slice(0, 4).join("、") || "单词"} 嵌进一段小事里。`} />
              </div>
            ))}
          </div>

          <div className="card">
            <div className="row spread">
              <h2>3. 定稿</h2>
              <button className="btn primary" onClick={saveScript}>保存并校验</button>
            </div>
            {script && (
              <>
                <div className="row" style={{ marginBottom: 12 }}>
                  <label className="lbl">主题<input value={script.theme} onChange={(e) => setScript({ ...script, theme: e.target.value })} /></label>
                  <label className="lbl">形态<input value={script.genre} onChange={(e) => setScript({ ...script, genre: e.target.value })} /></label>
                  <label className="lbl">级别
                    <select value={script.level} onChange={(e) => setScript({ ...script, level: e.target.value })}>
                      {meta.levels.map((l) => <option key={l.label} value={l.label}>{l.label}</option>)}
                    </select>
                  </label>
                </div>
                {script.sentences.map((sent, i) => (
                  <div key={i} className="sent">
                    <span className="muted">{i + 1}</span>
                    {sent.map((tk, j) => (
                      <input key={j} className={"tok" + ("w" in tk ? " w" : "")}
                        value={"w" in tk ? tk.w : tk.t}
                        placeholder={"w" in tk ? "word" : "中文"}
                        onChange={(e) => {
                          const next = sent.map((x, k) => k !== j ? x : ("w" in tk ? { w: e.target.value } : { t: e.target.value }));
                          setSent(i, next);
                        }} />
                    ))}
                    <button className="btn ghost" onClick={() => setSent(i, [...sent, { t: "" }])}>+中文</button>
                    <button className="btn ghost" onClick={() => setSent(i, [...sent, { w: "" }])}>+词</button>
                    <button className="btn ghost" onClick={() => setScript({ ...script, sentences: script.sentences.filter((_, k) => k !== i) })}>删句</button>
                  </div>
                ))}
                <button className="btn" style={{ marginTop: 8 }} onClick={() => setScript({ ...script, sentences: [...script.sentences, [{ t: "" }]] })}>加一句</button>

                <h2 style={{ marginTop: 18 }}>单词释义</h2>
                <table className="data">
                  <thead><tr><th>单词</th><th>词性</th><th>释义</th><th>复习</th></tr></thead>
                  <tbody>
                    {script.words.map((w, i) => (
                      <tr key={i}>
                        <td style={{ fontFamily: "Poppins, sans-serif", fontWeight: 700 }}>{w.word}</td>
                        <td>
                          <select value={w.pos} onChange={(e) => {
                            const words = script.words.map((x, k) => k === i ? { ...x, pos: e.target.value } : x);
                            setScript({ ...script, words });
                          }}>
                            {POS.map((p) => <option key={p}>{p}</option>)}
                          </select>
                        </td>
                        <td>
                          <input value={w.meaning} onChange={(e) => {
                            const words = script.words.map((x, k) => k === i ? { ...x, meaning: e.target.value } : x);
                            setScript({ ...script, words });
                          }} />
                        </td>
                        <td>
                          <input type="checkbox" checked={!!w.review} onChange={(e) => {
                            const words = script.words.map((x, k) => k === i ? { ...x, review: e.target.checked } : x);
                            setScript({ ...script, words });
                          }} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <h2 style={{ marginTop: 18 }}>评审分</h2>
                <div className="row">
                  {meta.reviewKeys.map((k) => (
                    <label key={k} className="lbl">{k}
                      <input type="number" min={1} max={5} value={script.review?.[k] ?? 0}
                        onChange={(e) => setScript({ ...script, review: { ...script.review, [k]: Number(e.target.value) } })} />
                    </label>
                  ))}
                </div>
              </>
            )}
            {report && (
              <div style={{ marginTop: 14 }}>
                <span className={`pill ${report.ok ? "ok" : "bad"}`}>{report.ok ? "校验通过" : "未通过"}</span>
                {report.hanzi != null && <span className="muted"> · 汉字 {report.hanzi}（目标 {meta.hanziRange[0]}–{meta.hanziRange[1]}）</span>}
                {report.errors.map((e) => <p key={e} className="err">✗ {e}</p>)}
                {report.warnings.map((e) => <p key={e} className="warn">! {e}</p>)}
              </div>
            )}
          </div>

          <div className="card">
            <h2>4. 配音 / 出片</h2>
            <div className="row" style={{ marginBottom: 12 }}>
              <label className="lbl">音色
                <select value={voice} onChange={(e) => { setVoice(e.target.value); savePlan({ voice: e.target.value }); }}>
                  {meta.voices.map((v) => <option key={v.id} value={v.id}>{v.label}</option>)}
                </select>
              </label>
              <label className="lbl">语速
                <input value={rate} onChange={(e) => setRate(e.target.value)} onBlur={() => savePlan({ rate })} placeholder="+5%" />
              </label>
            </div>
            <div className="row">
              <button className="btn primary" disabled={job?.status === "running"} onClick={() => run([
                { cmd: "tts", args: ["--voice", voice, "--rate", rate] },
                { cmd: "qa-audio" },
              ])}>配音并检查</button>
              <button className="btn" disabled={job?.status === "running"} onClick={() => run([{ cmd: "render" }])}>渲染成片</button>
              <button className="btn" disabled={job?.status === "running"} onClick={() => run([{ cmd: "commit" }])}>入库</button>
            </div>
            {ep.timeline && (
              <p className="muted" style={{ marginTop: 10 }}>
                朗读 {ep.timeline.reading.toFixed(1)}s（目标 {meta.readingRange[0]}–{meta.readingRange[1]}s）
                · 总长 {ep.timeline.total.toFixed(1)}s
                {ep.timeline.stale ? " · 文案已改，配音过期" : ""}
              </p>
            )}
            {ep.qa && !ep.qa.ok && ep.qa.errors.map((e) => <p key={e} className="err">✗ {e}</p>)}
            {ep.files.audio && <audio controls src={media(ep.files.audio)} style={{ width: "100%", marginTop: 10 }} />}
            {job && (
              <div className="log" style={{ marginTop: 12 }}>
                <div className={job.status === "failed" ? "err" : job.status === "done" ? "ok" : "muted"}>{job.title} · {job.status}</div>
                {job.lines.join("\n")}
              </div>
            )}
            {msg && <p className="muted">{msg}</p>}
          </div>

          <div className="card">
            <h2>项目文件</h2>
            <table className="data">
              <thead><tr><th>文件</th><th>类型</th><th>大小</th></tr></thead>
              <tbody>
                {files.map((f) => (
                  <tr key={f.path}>
                    <td className="mono">{f.url ? <a href={media(f.url)} target="_blank" rel="noreferrer">{f.path}</a> : f.path}</td>
                    <td><span className={`pill ${f.kind === "source" ? "on" : ""}`}>{f.kind}</span></td>
                    <td className="muted">{f.size > 1024 * 1024 ? `${(f.size / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(f.size / 1024)} KB`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="preview-box">
          {ep.files.video ? (
            <>
              <video controls src={media(ep.files.video)} style={{ width: "100%", borderRadius: 12, background: "#111" }} />
              <div className="cap">成片，直接看</div>
            </>
          ) : (
            <>
              <div className="player"><Preview data={preview} /></div>
              <div className="cap">{preview ? (preview.source === "tts" ? "真实配音预览" : "估算预览，渲染后这里换成视频") : "有文案后出现预览"}</div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
