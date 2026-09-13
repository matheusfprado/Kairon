import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const python = process.platform === "win32"
  ? path.join(root, ".venv", "Scripts", "python.exe")
  : path.join(root, ".venv", "bin", "python");
const result = spawnSync(existsSync(python) ? python : "python3", process.argv.slice(2), { stdio: "inherit" });
process.exit(result.status ?? 1);
