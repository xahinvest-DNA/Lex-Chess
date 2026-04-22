const NON_TARGET_MARKERS = [
  "уголов",
  "арбитраж",
  "ооо",
  "юрлиц",
  "юр лицо",
  "юридическое лицо",
  "корпоратив",
  "налог",
  "тамож",
  "миграц",
  "договор постав",
  "госконтракт",
  "44-фз",
  "223-фз",
  "банкротство компании",
  "банкротство ооо"
];

const ADJACENT_MARKERS = [
  "алим",
  "место жительства ребенка",
  "порядок общения",
  "наслед",
  "трудов",
  "увольнен",
  "зарплат",
  "недвижим",
  "дду",
  "застройщик",
  "потребител",
  "взыскан"
];

const TARGET_MARKERS = {
  "bankrotstvo-fizicheskih-lic": ["долг", "кредит", "мфо", "банк", "пристав", "коллектор", "банкрот"],
  razvod: ["развод", "брак", "супруг", "супруга", "дет", "загс"],
  "razdel-imushchestva": ["раздел", "кварт", "дом", "ипот", "авто", "счет", "имущество", "дол"]
};

export function decideLeadRoute(lead) {
  const text = [
    lead.service,
    lead.situation,
    lead.caseDetails,
    lead.documents,
    lead.region,
    lead.contact
  ]
    .join(" ")
    .toLowerCase();

  let fit = "target";
  let route = routeForService(lead.service);
  let statusId = process.env.BITRIX24_TARGET_STATUS_ID || "IN_PROCESS";
  const reasons = [];

  if (hasAny(text, NON_TARGET_MARKERS)) {
    fit = "non_target";
    route = "manual_review";
    statusId = process.env.BITRIX24_NON_TARGET_STATUS_ID || "JUNK";
    reasons.push("В тексте есть маркеры нецелевого направления.");
  } else if (hasAny(text, ADJACENT_MARKERS)) {
    fit = "adjacent";
    route = "manual_review";
    statusId = process.env.BITRIX24_ADJACENT_STATUS_ID || "NEW";
    reasons.push("Запрос похож на смежную практику, нужна ручная проверка.");
  } else if (!hasAny(text, TARGET_MARKERS[lead.service] || [])) {
    fit = "adjacent";
    statusId = process.env.BITRIX24_ADJACENT_STATUS_ID || "NEW";
    reasons.push("Выбрано целевое направление, но в тексте мало подтверждающих фактов.");
  } else {
    reasons.push("Запрос соответствует текущей специализации.");
  }

  return {
    fit,
    route,
    statusId,
    responsibleId: responsibleForRoute(route),
    reasons
  };
}

function routeForService(service) {
  if (service === "bankrotstvo-fizicheskih-lic") return "bankruptcy";
  if (service === "razvod" || service === "razdel-imushchestva") return "family";
  return "manual_review";
}

function responsibleForRoute(route) {
  if (route === "bankruptcy" && process.env.BITRIX24_BANKRUPTCY_RESPONSIBLE_ID) {
    return Number(process.env.BITRIX24_BANKRUPTCY_RESPONSIBLE_ID);
  }
  if (route === "family" && process.env.BITRIX24_FAMILY_RESPONSIBLE_ID) {
    return Number(process.env.BITRIX24_FAMILY_RESPONSIBLE_ID);
  }
  if (route === "manual_review" && process.env.BITRIX24_REVIEW_RESPONSIBLE_ID) {
    return Number(process.env.BITRIX24_REVIEW_RESPONSIBLE_ID);
  }
  return Number(process.env.BITRIX24_RESPONSIBLE_ID || 1);
}

function hasAny(text, markers) {
  return markers.some((marker) => text.includes(marker));
}
