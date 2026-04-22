import { appendLeadEvent } from "@/lib/lead-store";
import { submitLeadToBitrix } from "@/lib/bitrix24";
import { decideLeadRoute } from "@/lib/routing";
import { buildTelegramLeadDeepLink, notifyManagerInTelegram } from "@/lib/telegram";

export const runtime = "nodejs";

export async function POST(request) {
  const payload = await request.json();
  const required = ["service", "situation", "name", "phone"];
  const missing = required.filter((field) => !String(payload[field] || "").trim());

  if (missing.length) {
    return Response.json(
      { ok: false, error: "Заполните направление, ситуацию, имя и телефон." },
      { status: 400 }
    );
  }

  if (String(payload.situation).trim().length < 20) {
    return Response.json(
      { ok: false, error: "Опишите ситуацию чуть подробнее: минимум 20 символов." },
      { status: 400 }
    );
  }

  if (!payload.personalDataConsent || !payload.communicationConsent) {
    return Response.json(
      { ok: false, error: "Для отправки заявки нужно подтвердить согласия под формой." },
      { status: 400 }
    );
  }

  const requestUrl = new URL(request.url);
  const headers = request.headers;
  const lead = {
    ...payload,
    requestId: crypto.randomUUID(),
    source: "website",
    createdAt: new Date().toISOString(),
    pageUrl: payload.pageUrl || headers.get("referer") || "",
    referrer: headers.get("referer") || "",
    userAgent: headers.get("user-agent") || "",
    ip:
      headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
      headers.get("x-real-ip") ||
      "",
    utm: extractUtm(payload, requestUrl)
  };
  lead.routing = decideLeadRoute(lead);

  let crmResult = {
    configured: false,
    leadId: null,
    taskId: null,
    timelineCommentId: null,
    error: null
  };
  let telegramResult = {
    configured: false,
    sent: false,
    error: null
  };

  try {
    crmResult = await submitLeadToBitrix(lead);
  } catch (error) {
    crmResult = {
      ...crmResult,
      configured: true,
      error: error instanceof Error ? error.message : String(error)
    };
  }

  try {
    telegramResult = await notifyManagerInTelegram(lead, crmResult);
  } catch (error) {
    telegramResult = {
      ...telegramResult,
      configured: true,
      error: error instanceof Error ? error.message : String(error)
    };
  }

  await appendLeadEvent("site-leads.jsonl", {
    lead,
    crm: crmResult,
    telegram: telegramResult
  });

  if (crmResult.error) {
    await appendLeadEvent("site-leads-errors.jsonl", {
      lead,
      crm: crmResult,
      telegram: telegramResult
    });
  }

  const responseBody = {
    ok: true,
    requestId: lead.requestId,
    crm: {
      configured: crmResult.configured,
      leadId: crmResult.leadId,
      taskId: crmResult.taskId,
      error: crmResult.error
    },
    telegram: {
      configured: telegramResult.configured,
      sent: telegramResult.sent,
      error: telegramResult.error
    },
    telegramUrl: buildTelegramLeadDeepLink(lead.requestId)
  };

  if (crmResult.error) {
    return Response.json(
      {
        ...responseBody,
        ok: false,
        error:
          "Заявка сохранена локально, но пока не передана в CRM. Проверьте соединение с Bitrix24 и повторите отправку."
      },
      { status: 502 }
    );
  }

  return Response.json(responseBody);
}

function extractUtm(payload, requestUrl) {
  const fromPayload = payload.utm && typeof payload.utm === "object" ? payload.utm : {};
  const keys = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"];
  return Object.fromEntries(
    keys.map((key) => [key, fromPayload[key] || requestUrl.searchParams.get(key) || ""])
  );
}
