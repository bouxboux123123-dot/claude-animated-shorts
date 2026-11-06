import fs from "node:fs";
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const outDir = path.resolve("out/pink_verification");
fs.mkdirSync(outDir, { recursive: true });

const browserExecutable = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const chromiumOptions = { gl: "angle" };

console.log("Bundling Remotion project for PinkPrisonShort...");
const serveUrl = await bundle({
  entryPoint: path.resolve("src/index.ts"),
  publicDir: path.resolve("public"),
});

console.log("Selecting composition PinkPrisonShort...");
const composition = await selectComposition({
  serveUrl,
  id: "PinkPrisonShort",
  browserExecutable,
  chromiumOptions,
});

const frames = [150, 270, 750, 1000, 1400, 1850];
const onBrowserLog = (l) => {
  if (l.type === "error" || l.type === "warning") {
    console.log(`[${l.type}]`, l.text.slice(0, 300));
  }
};

for (const f of frames) {
  const t0 = Date.now();
  const outPath = path.join(outDir, `pink_f${f.toString().padStart(4, "0")}.jpg`);
  await renderStill({
    composition,
    serveUrl,
    frame: f,
    output: outPath,
    imageFormat: "jpeg",
    jpegQuality: 92,
    scale: 0.5,
    browserExecutable,
    chromiumOptions,
    timeoutInMilliseconds: 60000,
    onBrowserLog,
  });
  console.log(`Rendered frame ${f} in ${((Date.now() - t0) / 1000).toFixed(1)}s -> ${outPath}`);
}
console.log("All verification stills rendered successfully!");
