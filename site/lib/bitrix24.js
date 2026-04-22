import { services } from "./site-data.js";

const DEFAULT_ENTITY_TYPE_ID = 1;

export function isBitrixConfigured() {
  return Boolean(process.env.BITRIX24_WEBHOOK_URL);
}

export async function submitLeadToBitrix(lead) {
  if (!isBitrixConfigured()) {
    return {
      configured: false,
      leadId: null,
      taskId: null,
      timelineCommentId: null,
      error: null
    };
  }

  const service = services.find((item) => item.slug === lead.service);
  const leadResponse = await callBitrix("crm.item.add", buildLeadPayload(lead, service));
  const leadId = Number(leadResponse?.item?.id);

  if (!leadId) {
    throw new Error("Bitrix24 did not return created lead id.");
  }

  const taskResponse = await callBitrix("tasks.task.add", buildTaskPayload(lead, service, leadId));
  const taskId = Number(taskResponse?.task?.id || taskResponse?.item?.id || 0) || null;
  const taskStarted = taskId ? await startTask(taskId) : false;

  const timelineResponse = await callBitrix(
    "crm.timeline.comment.add",
    buildTimelinePayload(lead, service, leadId)
  );
  const timelineCommentId = Number(timelineResponse || 0) || null;

  return {
    configured: true,
    leadId,
    taskId,
    taskStarted,
    timelineCommentId,
    error: null
  };
}

async function callBitrix(method, payload) {
  const baseUrl = process.env.BITRIX24_WEBHOOK_URL.replace(/\/+$/, "");
  let response;

  try {
    response = await fetch(`${baseUrl}/${method}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
      cache: "no-store"
    });
  } catch (error) {
    const cause = error?.cause?.message ? ` (${error.cause.message})` : "";
    throw new Error(`Bitrix24 network error: ${error.message}${cause}`);
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(`Bitrix24 HTTP ${response.status}: ${JSON.stringify(data)}`);
  }

  if (data?.error) {
    throw new Error(`${data.error}: ${data.error_description || "Bitrix24 API error"}`);
  }

  return data?.result;
}

async function startTask(taskId) {
  try {
    await callBitrix("tasks.task.start", { taskId });
    return true;
  } catch {
    return false;
  }
}

function buildLeadPayload(lead, service) {
  const [firstName, ...restName] = String(lead.name || "").trim().split(/\s+/);
  const fields = {
    title: `${service?.shortTitle || "Юридическая заявка"} | ${lead.name}`,
    name: firstName || lead.name,
    lastName: restName.join(" "),
    sourceId: process.env.BITRIX24_SOURCE_ID || "WEB",
    sourceDescription: "Website diagnostic form",
    assignedById: Number(lead.routing?.responsibleId || process.env.BITRIX24_RESPONSIBLE_ID || 1),
    comments: buildCrmComment(lead, service),
    statusDescription: buildStatusDescription(lead),
    statusId: lead.routing?.statusId || process.env.BITRIX24_TARGET_STATUS_ID || "IN_PROCESS",
    originatorId: "legal-site",
    originId: lead.requestId,
    utmSource: lead.utm?.utm_source || "website",
    utmMedium: lead.utm?.utm_medium || "form",
    utmCampaign: lead.utm?.utm_campaign || "",
    fm: [
      {
        typeId: "PHONE",
        valueType: "WORK",
        value: lead.phone
      }
    ]
  };

  return {
    entityTypeId: Number(process.env.BITRIX24_ENTITY_TYPE_ID || DEFAULT_ENTITY_TYPE_ID),
    fields
  };
}

function buildTaskPayload(lead, service, leadId) {
  const deadline = new Date(Date.now() + getResponseWindowHours(lead.urgency) * 60 * 60 * 1000);
  return {
    fields: {
      TITLE: `[${lead.consultationSlot || "слот не выбран"}] [website] ${service?.shortTitle || "Юридическая заявка"} | ${lead.name}`,
      DESCRIPTION: buildTaskDescription(lead, service),
      CREATED_BY: Number(
        process.env.BITRIX24_CREATOR_ID || process.env.BITRIX24_RESPONSIBLE_ID || 1
      ),
      RESPONSIBLE_ID: Number(lead.routing?.responsibleId || process.env.BITRIX24_RESPONSIBLE_ID || 1),
      PRIORITY: getTaskPriority(lead),
      DEADLINE: deadline.toISOString(),
      UF_CRM_TASK: [`L_${leadId}`]
    }
  };
}

function buildTimelinePayload(lead, service, leadId) {
  return {
    fields: {
      ENTITY_ID: leadId,
      ENTITY_TYPE: "lead",
      COMMENT: buildCrmComment(lead, service)
    }
  };
}

export function buildCrmComment(lead, service) {
  return [
    `Направление: ${service?.shortTitle || lead.service}`,
    `Клиент: ${lead.name}`,
    `Телефон: ${lead.phone}`,
    `Предпочтительное время: ${lead.consultationSlot || "-"}`,
    `Канал связи: ${lead.contact}`,
    `Срочность: ${lead.urgency}`,
    `Регион: ${lead.region || "-"}`,
    `Документы: ${lead.documents || "-"}`,
    `Ключевые факты: ${lead.caseDetails || "-"}`,
    "",
    "Ситуация:",
    cleanSituation(lead.situation)
  ].join("\n");
}

function buildTaskDescription(lead, service) {
  return [
    buildCrmComment(lead, service),
    "",
    `Маршрут: ${humanFit(lead.routing?.fit)}. ${humanRoute(lead.routing?.route)}.`
  ].join("\n");
}

function cleanSituation(situation = "") {
  return String(situation)
    .split(/\r?\n/)
    .filter((line) => !line.startsWith("Направление:"))
    .filter((line) => !line.startsWith("Ключевые факты:"))
    .filter((line) => !line.startsWith("Документы:"))
    .filter((line) => !line.startsWith("Регион:"))
    .join("\n")
    .trim();
}

function getResponseWindowHours(urgency) {
  if (String(urgency || "").includes("Сегодня")) return 1;
  if (String(urgency || "").includes("3")) return 4;
  return 24;
}

function getTaskPriority(lead) {
  if (lead.routing?.fit === "non_target") return 1;
  if (String(lead.urgency || "").includes("Сегодня")) return 2;
  if (String(lead.urgency || "").includes("3")) return 2;
  return 1;
}

function buildStatusDescription(lead) {
  return `${humanFit(lead.routing?.fit)}. ${humanRoute(lead.routing?.route)}. Контакт: ${
    lead.consultationSlot || "-"
  }.`;
}

function humanFit(fit) {
  if (fit === "non_target") return "Нецелевое обращение";
  if (fit === "adjacent") return "Смежное обращение";
  return "Целевой лид";
}

function humanRoute(route) {
  if (route === "bankruptcy") return "Маршрут: банкротство";
  if (route === "family") return "Маршрут: семейное право";
  if (route === "manual_review") return "Маршрут: ручная проверка";
  return "Маршрут: общий";
}
