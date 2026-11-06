import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setEntryPoint("src/index.ts");
if (process.platform === "win32") {
  Config.setChromiumOpenGlRenderer("angle");
}
