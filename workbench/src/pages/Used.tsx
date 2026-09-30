import { useEffect, useState } from "react";
import { api } from "../api";
import type { UsageRow } from "../types";

export function UsedPage({ go }: { go: (p: string) => void }) {
  const [rows, setRows] = useState<UsageRow[]>([]);
  const [q, setQ] = useState("");

  useEffect(() => { api.get<UsageRow[]>("/api/usage").then(setRows); }, []);
  const shown = rows.filter((r) => !q || r.word.includes(q.toLowerCase()) || r.meaning.includes(q) || r.lastTheme.includes(q));

  return (
    <>
      <h1>已用词</h1>
      <p className="sub">来自各期 script.json。入库后才算正式占用，草稿里出现过的也会列在这里。</p>
      <div className="row" style={{ marginBottom: 16 }}>
        <input type="search" placeholder="搜单词 / 释义 / 主题" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 260 }} />
        <span className="muted">{shown.length} / {rows.length}</span>
      </div>
      <div className="card">
        <table className="data">
          <thead>
            <tr><th>单词</th><th>释义</th><th>次数</th><th>状态</th><th>出现期</th></tr>
          </thead>
          <tbody>
            {shown.map((r) => (
              <tr key={r.word}>
                <td style={{ fontFamily: "Poppins, sans-serif", fontWeight: 700 }}>{r.word}</td>
                <td>{r.meaning}</td>
                <td>{r.times}{r.reviewTimes ? ` · 复习 ${r.reviewTimes}` : ""}</td>
                <td>{r.published ? <span className="pill ok">已入库</span> : <span className="pill warn">仅草稿</span>}</td>
                <td>
                  {r.episodes.map((ep) => (
                    <a key={ep.id} href={`/ep/${ep.id}`} onClick={(e) => { e.preventDefault(); go(`/ep/${ep.id}`); }} style={{ marginRight: 8 }}>
                      {ep.id} {ep.theme}
                    </a>
                  ))}
                </td>
              </tr>
            ))}
            {!shown.length && <tr><td colSpan={5} className="muted">还没有用过的词。</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
