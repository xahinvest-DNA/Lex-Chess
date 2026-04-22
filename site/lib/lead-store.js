import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";

export async function appendLeadEvent(fileName, payload) {
  const dataDir = path.join(process.cwd(), "data");
  await mkdir(dataDir, { recursive: true });
  await appendFile(path.join(dataDir, fileName), `${JSON.stringify(payload)}\n`, "utf8");
}
