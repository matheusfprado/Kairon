import { existsSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
const root = process.cwd();
const venv = process.platform === "win32" ? path.join(root, ".venv", "Scripts", "python.exe") : path.join(root, ".venv", "bin", "python");
const commands = ["node", "pnpm", "cargo", "ollama"];
const missing = commands.filter((command) => spawnSync(command, ["--version"], { stdio: "ignore", shell: false }).status !== 0);
if (!existsSync(venv)) missing.push("Python venv (.venv)");
if (missing.length) { console.error(`Kairon nao pode iniciar ainda. Faltando: ${missing.join(", ")}`); process.exit(1); }
console.log("Ambiente Kairon OK.");
