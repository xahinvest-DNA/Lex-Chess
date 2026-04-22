import { appendFile, readFile } from "node:fs/promises";
import path from "node:path";

import { submitLeadToBitrix } from "../lib/bitrix24.js";

const args = process.argv.slice(2);
const latestOnly = args.includes("--latest");
const force = args.includes("--force");
const fileName = args.find((arg) => !arg.startsWith("--")) || "site-leads-errors.jsonl";
const filePath = path.join(process.cwd(), "data", fileName);
const resendLogPath = path.join(process.cwd(), "data", "site-leads-resend.jsonl");

const content = await readFile(filePath, "utf8").catch((error) => {
  if (error.code === "ENOENT") {
    console.log(`No saved lead error file found: data/${fileName}`);
    return "";
  }
  throw error;
});

const events = content
  .split(/\r?\n/)
  .filter(Boolean)
  .map((line) => JSON.parse(line));

const alreadySent = force ? new Set() : await getResentRequestIds();
let candidates = events.filter((event) => event.lead && !event.crm?.leadId);

if (latestOnly && candidates.length) {
  candidates = [candidates.at(-1)];
}

const pending = candidates.filter((event) => !alreadySent.has(event.lead.requestId));

if (!pending.length) {
  console.log("No pending website leads to resend.");
  process.exit(0);
}

let sent = 0;
let failed = 0;

for (const event of pending) {
  const lead = event.lead;

  try {
    const result = await submitLeadToBitrix(lead);
    sent += 1;
    await appendFile(
      resendLogPath,
      `${JSON.stringify({ lead, crm: result, resentAt: new Date().toISOString() })}\n`,
      "utf8"
    );
    console.log(
      `OK requestId=${lead.requestId} leadId=${result.leadId} taskId=${result.taskId || "-"}`
    );
  } catch (error) {
    failed += 1;
    console.log(
      `ERROR requestId=${lead.requestId} ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

console.log(`Done. Sent: ${sent}. Failed: ${failed}.`);

async function getResentRequestIds() {
  const log = await readFile(resendLogPath, "utf8").catch((error) => {
    if (error.code === "ENOENT") return "";
    throw error;
  });

  return new Set(
    log
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((event) => event.lead?.requestId && event.crm?.leadId)
      .map((event) => event.lead.requestId)
  );
}
