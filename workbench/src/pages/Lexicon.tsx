import { useEffect, useState } from "react";
import { api } from "../api";
import type { LexiconPage as Page, Meta } from "../types";

export function LexiconPage({ meta, go }: { meta: Meta; go: (p: string) => void }) {
  const [level, setLevel] = useState("cet4");
  const [used, setUsed] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page | null>(null);

  const load = (p = page) => {
    const qs = new URLSearchParams({ level, used, q, page: String(p), limit: "40" });
    api.get<Page>(`/api/lexicon?${qs}`).then(setData);
  };

  useEffect(() => { setPage(1); load(1); }, [level, used]);

  return (
    <>
      <h1>词库</h1>
      <p className="sub">ECDICT 本地库，按级别过滤。点单词可看它出现在哪一期。</p>
      <div className="row" style={{ marginBottom: 16 }}>
        <select value={level} onChange={(e) => setLevel(e.target.value)}>
          {meta.levels.map((l) => <option key={l.key} value={l.key}>{l.label}</option>)}
        </select>
        <select value={used} onChange={(e) => setUsed(e.target.value)}>
          <option value="">全部</option>
          <option value="new">未用</option>
          <option value="used">已用</option>
        </select>
        <input type="search" placeholder="英文前缀或中文释义" value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { setPage(1); load(1); } }} />
        <button className="btn" onClick={() => { setPage(1); load(1); }}>查找</button>
        {data && <span className="muted">{data.total} 条</span>}
      </div>
      <div className="card">
        <table className="data">
          <thead>
            <tr><th>单词</th><th>音标</th><th>释义</th><th>级别</th><th>占用</th></tr>
          </thead>
          <tbody>
            {data?.items.map((w) => (
              <tr key={w.word}>
                <td style={{ fontFamily: "Poppins, sans-serif", fontWeight: 700 }}>{w.word}</td>
                <td className="muted">{w.ipa}</td>
                <td>{w.senses}</td>
                <td>{w.inLevel ? <span className="pill ok">{data.level}</span> : <span className="pill">{w.tag || "—"}</span>}</td>
                <td>
                  {w.used ? w.episodes?.map((ep) => (
                    <a key={ep.id} href={`/ep/${ep.id}`} onClick={(e) => { e.preventDefault(); go(`/ep/${ep.id}`); }}>{ep.id} </a>
                  )) : <span className="muted">未用</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && data.total > data.limit && (
          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn ghost" disabled={page <= 1} onClick={() => { const p = page - 1; setPage(p); load(p); }}>上一页</button>
            <span className="muted">{page} / {Math.ceil(data.total / data.limit)}</span>
            <button className="btn ghost" disabled={page * data.limit >= data.total} onClick={() => { const p = page + 1; setPage(p); load(p); }}>下一页</button>
          </div>
        )}
      </div>
    </>
  );
}
