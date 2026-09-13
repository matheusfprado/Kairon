import { spawnSync } from "node:child_process";
const run = (command, args) => {
  const result = spawnSync(command, args, { stdio: "inherit", shell: false });
  if (result.status !== 0) process.exit(result.status ?? 1);
};
run("pnpm", ["check:env"]);
run("pnpm", ["--filter", "@kairon/desktop", "tauri"]);
