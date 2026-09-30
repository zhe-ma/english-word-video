import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

const el = document.getElementById("root")!;
window.addEventListener("error", (e) => {
  if (!el.innerText) el.innerHTML = `<pre style="padding:24px;color:#ff8a80">${e.message}\n${e.filename}:${e.lineno}</pre>`;
});
window.addEventListener("unhandledrejection", (e) => {
  if (!el.innerText) el.innerHTML = `<pre style="padding:24px;color:#ff8a80">${e.reason}</pre>`;
});

createRoot(el).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
