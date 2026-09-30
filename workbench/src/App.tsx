import { Component, type ReactNode, useEffect, useState } from "react";
import { api } from "./api";
import { EpisodePage } from "./pages/Episode";
import { HomePage } from "./pages/Home";
import { LexiconPage } from "./pages/Lexicon";
import { UsedPage } from "./pages/Used";
import type { Meta, Stats } from "./types";

class Boundary extends Component<{ children: ReactNode }, { err: string }> {
  state = { err: "" };
  static getDerivedStateFromError(e: Error) { return { err: e.message || String(e) }; }
  render() {
    if (this.state.err) return <pre className="err" style={{ padding: 24 }}>{this.state.err}</pre>;
    return this.props.children;
  }
}

function path() {
  return location.pathname.replace(/\/+$/, "") || "/";
}

export function App() {
  const [route, setRoute] = useState(path);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const on = () => setRoute(path());
    window.addEventListener("popstate", on);
    return () => window.removeEventListener("popstate", on);
  }, []);

  useEffect(() => {
    api.get<Meta>("/api/meta").then(setMeta);
    api.get<Stats>("/api/stats").then(setStats);
  }, [route]);

  const go = (to: string) => {
    history.pushState({}, "", to);
    setRoute(path());
  };

  const ep = route.match(/^\/ep\/([\w-]+)$/)?.[1];

  return (
    <div className="app">
      <nav className="nav">
        <div className="brand">
          荧光笔手帐
          <small>单词视频工作台</small>
        </div>
        <a className={route === "/" ? "on" : ""} href="/" onClick={(e) => { e.preventDefault(); go("/"); }}>期数</a>
        <a className={route === "/used" ? "on" : ""} href="/used" onClick={(e) => { e.preventDefault(); go("/used"); }}>已用词</a>
        <a className={route === "/lexicon" ? "on" : ""} href="/lexicon" onClick={(e) => { e.preventDefault(); go("/lexicon"); }}>词库</a>
        <div className="foot">
          {stats ? `${stats.published} 期入库 · ${stats.usedWords} 词` : "…"}
        </div>
      </nav>
      <main className="main">
        <Boundary>
        {!meta ? <p className="muted">连接 API…</p> : ep ? (
          <EpisodePage id={ep} meta={meta} go={go} />
        ) : route === "/used" ? (
          <UsedPage go={go} />
        ) : route === "/lexicon" ? (
          <LexiconPage meta={meta} go={go} />
        ) : (
          <HomePage meta={meta} stats={stats} go={go} />
        )}
        </Boundary>
      </main>
    </div>
  );
}
