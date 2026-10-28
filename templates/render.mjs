// 批量渲染：node render.mjs jobs.json
// jobs: [{kind: "video" | "still", composition, props, out, frame?, concurrency?}]
// 整批只打包一次、只开一个浏览器。
import { bundle } from "@remotion/bundler";
import { openBrowser, renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const jobs = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

const t0 = Date.now();
const serveUrl = await bundle({
  entryPoint: path.join(here, "src/index.ts"),
  publicDir: path.join(here, "public"),
  rootDir: here,
});
console.log(`打包完成 ${((Date.now() - t0) / 1000).toFixed(1)}s`);

// 默认用 Remotion 自己下载的 Chrome Headless Shell；下载不了时可以用环境变量 VB_BROWSER 指定本机 Chrome / Edge 路径。
const browser = await openBrowser("chrome", process.env.VB_BROWSER ? { browserExecutable: process.env.VB_BROWSER } : {});
try {
  for (const job of jobs) {
    fs.mkdirSync(path.dirname(job.out), { recursive: true });
    const common = {
      serveUrl,
      inputProps: job.props,
      puppeteerInstance: browser,
      onBrowserLog: (log) => {
        if (log.type === "error" || log.type === "warning" || process.env.VB_DEBUG) console.log(`  [browser] ${log.text}`);
      },
    };
    const composition = await selectComposition({ ...common, id: job.composition });
    const start = Date.now();
    if (job.kind === "video") {
      let last = -1;
      await renderMedia({
        ...common,
        composition,
        codec: "h264",
        crf: 20,
        outputLocation: job.out,
        concurrency: job.concurrency ?? null,
        onProgress: ({ progress }) => {
          const pct = Math.floor(progress * 10) * 10;
          if (pct !== last) {
            last = pct;
            process.stdout.write(`  ${path.basename(path.dirname(job.out))} 渲染 ${pct}%\r`);
          }
        },
      });
      process.stdout.write("\n");
    } else {
      await renderStill({ ...common, composition, output: job.out, frame: job.frame ?? 0 });
    }
    console.log(`✓ ${job.out} (${((Date.now() - start) / 1000).toFixed(1)}s)`);
  }
} finally {
  await browser.close({ silent: true });
}
