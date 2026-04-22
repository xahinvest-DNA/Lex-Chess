export function isTelegramManagerConfigured() {
  return Boolean(process.env.TELEGRAM_BOT_TOKEN && process.env.MANAGER_TELEGRAM_CHAT_ID);
}

export function buildTelegramLeadDeepLink(requestId) {
  const baseUrl = process.env.NEXT_PUBLIC_TELEGRAM_URL;
  if (!baseUrl) return null;

  const url = new URL(baseUrl);
  url.searchParams.set("start", `lead_${requestId}`);
  return url.toString();
}

export async function notifyManagerInTelegram(lead, crmResult) {
  if (!isTelegramManagerConfigured()) {
    return {
      configured: false,
      sent: false,
      error: null
    };
  }

  const text = [
    "<b>Новая заявка с сайта</b>",
    `ID: <b>${escapeHtml(lead.requestId)}</b>`,
    `Услуга: <b>${escapeHtml(lead.service)}</b>`,
    `Имя: ${escapeHtml(lead.name)}`,
    `Телефон: ${escapeHtml(lead.phone)}`,
    `Срочность: ${escapeHtml(lead.urgency)}`,
    `Канал: ${escapeHtml(lead.contact)}`,
    `Документы: ${escapeHtml(lead.documents || "-")}`,
    `Регион: ${escapeHtml(lead.region || "-")}`,
    "",
    escapeHtml(lead.situation),
    "",
    crmResult?.leadId ? `Bitrix lead ID: <b>${crmResult.leadId}</b>` : "Bitrix lead ID: не создан"
  ].join("\n");

  const response = await fetch(
    `https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}/sendMessage`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        chat_id: process.env.MANAGER_TELEGRAM_CHAT_ID,
        text,
        parse_mode: "HTML",
        disable_web_page_preview: true
      }),
      cache: "no-store"
    }
  );

  const data = await response.json().catch(() => null);
  if (!response.ok || data?.ok === false) {
    throw new Error(`Telegram notify failed: ${JSON.stringify(data)}`);
  }

  return {
    configured: true,
    sent: true,
    error: null
  };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
