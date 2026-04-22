"use client";

import { useMemo, useState } from "react";

import { bookingSlots, services } from "@/lib/site-data";

const SERVICE_CONTEXT = {
  "bankrotstvo-fizicheskih-lic":
    "Укажите примерную сумму долга, банки/МФО, есть ли имущество и приставы.",
  razvod: "Укажите, есть ли дети, согласие супруга и спор по алиментам или месту проживания.",
  "razdel-imushchestva":
    "Укажите, что нужно делить: квартира, авто, ипотека, счета, долги или другое имущество."
};

const STEPS = [
  {
    key: "service",
    label: "Направление",
    type: "choice",
    question: "С чем нужна помощь?",
    helper: "Мы работаем только с физическими лицами: банкротство, развод и раздел имущества.",
    options: services.map((service) => ({ value: service.slug, label: service.shortTitle }))
  },
  {
    key: "situation",
    label: "Ситуация",
    type: "textarea",
    question: "Опишите ситуацию в двух-трёх предложениях.",
    helper: "Что произошло, какие документы есть и чего хотите добиться?",
    minLength: 20
  },
  {
    key: "urgency",
    label: "Срочность",
    type: "choice",
    question: "Насколько срочный вопрос?",
    options: ["Сегодня", "В ближайшие 3 дня", "1-2 недели", "Пока просто консультация"]
  },
  {
    key: "caseDetails",
    label: "Детали",
    type: "textarea",
    question: "Уточните ключевые факты по направлению.",
    helper: "Подсказка изменится после выбора услуги.",
    minLength: 3
  },
  {
    key: "documents",
    label: "Документы",
    type: "choice",
    question: "Документы уже есть?",
    options: ["Да, все основные", "Частично", "Пока нет"]
  },
  {
    key: "region",
    label: "Регион",
    type: "text",
    question: "В каком регионе нужно вести вопрос?",
    helper: "Например: Москва, Московская область, онлайн по РФ или другой регион.",
    minLength: 2
  },
  {
    key: "name",
    label: "Имя",
    type: "text",
    question: "Как к вам обращаться?",
    helper: "Укажите имя и фамилию.",
    minLength: 3
  },
  {
    key: "phone",
    label: "Телефон",
    type: "tel",
    question: "Оставьте номер телефона для связи.",
    helper: "Юрист или менеджер свяжется с вами по заявке.",
    minLength: 10
  },
  {
    key: "contact",
    label: "Канал",
    type: "choice",
    question: "Как удобнее получить ответ?",
    options: ["Телефон", "Telegram", "WhatsApp"]
  },
  {
    key: "consultationSlot",
    label: "Консультация",
    type: "choice",
    question: "Выберите предварительное окно для первой консультации.",
    helper: "Юрист подтвердит точное время после проверки заявки.",
    options: bookingSlots
  },
  {
    key: "consents",
    label: "Согласия",
    type: "consents",
    question: "Подтвердите согласия, чтобы отправить заявку.",
    helper: "Без согласий мы не сможем обработать контактные данные и ответить по заявке."
  }
];

const defaultForm = {
  service: services[0].slug,
  situation: "",
  urgency: "В ближайшие 3 дня",
  caseDetails: "",
  documents: "Частично",
  region: "",
  name: "",
  phone: "",
  contact: "Телефон",
  consultationSlot: bookingSlots[0],
  personalDataConsent: false,
  communicationConsent: false
};

export default function LeadIntake() {
  const [form, setForm] = useState(defaultForm);
  const [stepIndex, setStepIndex] = useState(0);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const [telegramUrl, setTelegramUrl] = useState("");

  const step = STEPS[stepIndex];
  const progress = Math.round(((stepIndex + 1) / STEPS.length) * 100);
  const helperText = useMemo(() => {
    if (step.key === "caseDetails") {
      return SERVICE_CONTEXT[form.service] || step.helper;
    }
    return step.helper;
  }, [form.service, step]);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setMessage("");
  }

  function canContinue() {
    if (step.type === "consents") {
      return form.personalDataConsent && form.communicationConsent;
    }
    const value = String(form[step.key] || "").trim();
    if (!value) return false;
    if (step.minLength && value.length < step.minLength) return false;
    return true;
  }

  function next() {
    if (!canContinue()) {
      setMessage("Заполните текущий шаг, чтобы продолжить.");
      return;
    }
    setMessage("");
    setStepIndex((current) => Math.min(current + 1, STEPS.length - 1));
  }

  function back() {
    setMessage("");
    setStepIndex((current) => Math.max(current - 1, 0));
  }

  async function submit(event) {
    event.preventDefault();
    if (!canContinue()) {
      setMessage("Подтвердите согласия, чтобы отправить заявку.");
      return;
    }

    setStatus("loading");
    setMessage("");
    setTelegramUrl("");

    const response = await fetch("/api/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        situation: buildSituation(form),
        pageUrl: typeof window !== "undefined" ? window.location.href : "",
        utm: collectUtm()
      })
    });
    const data = await response.json();

    if (!response.ok) {
      setStatus("error");
      setMessage(
        data.error ||
          "Не удалось отправить заявку. Проверьте соединение и попробуйте ещё раз."
      );
      return;
    }

    setStatus("success");
    setTelegramUrl(data.telegramUrl || "");
    setMessage(
      data.crm?.leadId
        ? `Заявка принята и передана юристу. Номер обращения: ${data.requestId}.`
        : `Заявка принята. Номер обращения: ${data.requestId}. Мы сохранили её и свяжемся с вами.`
    );
  }

  if (status === "success") {
    return (
      <div className="intake-card intake-card--success">
        <p className="eyebrow">Заявка принята</p>
        <h2>Юрист получил контекст и свяжется с вами.</h2>
        <p className="form-message form-message--success">{message}</p>
        <div className="after-submit-actions">
          {telegramUrl ? (
            <a className="button button--ghost" href={telegramUrl} target="_blank">
              Открыть Telegram-чат
            </a>
          ) : null}
          <button
            className="button button--primary"
            type="button"
            onClick={() => {
              setForm(defaultForm);
              setStatus("idle");
              setStepIndex(0);
              setMessage("");
              setTelegramUrl("");
            }}
          >
            Отправить новую заявку
          </button>
        </div>
        <p className="telegram-note">
          Telegram необязателен. Он нужен только если хотите сохранить диалог, дослать документы или
          получать уточнения в мессенджере.
        </p>
      </div>
    );
  }

  return (
    <form className="intake-card intake-chat" onSubmit={submit}>
      <div className="intake-card__head">
        <p className="eyebrow">Онлайн-диагностика</p>
        <h2>Ответьте на несколько вопросов прямо на сайте.</h2>
        <div className="chat-progress" aria-label={`Прогресс ${progress}%`}>
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="chat-step-meta">
        <span>
          Шаг {stepIndex + 1} из {STEPS.length}
        </span>
        <strong>{step.label}</strong>
      </div>

      <div className="chat-bubble">
        <h3>{step.question}</h3>
        {helperText ? <p>{helperText}</p> : null}
      </div>

      <StepInput step={step} form={form} update={update} />

      {message ? <p className={`form-message form-message--${status}`}>{message}</p> : null}

      <div className="chat-actions">
        <button className="button button--ghost" type="button" onClick={back} disabled={stepIndex === 0}>
          Назад
        </button>
        {stepIndex < STEPS.length - 1 ? (
          <button className="button button--primary" type="button" onClick={next}>
            Продолжить
          </button>
        ) : (
          <button className="button button--primary" disabled={status === "loading"}>
            {status === "loading" ? "Отправляем..." : "Отправить заявку"}
          </button>
        )}
      </div>
    </form>
  );
}

function StepInput({ step, form, update }) {
  if (step.type === "choice") {
    return (
      <div className="choice-list">
        {step.options.map((option) => {
          const value = typeof option === "string" ? option : option.value;
          const label = typeof option === "string" ? option : option.label;
          return (
            <button
              className={form[step.key] === value ? "choice-pill choice-pill--active" : "choice-pill"}
              key={value}
              type="button"
              onClick={() => update(step.key, value)}
            >
              {label}
            </button>
          );
        })}
      </div>
    );
  }

  if (step.type === "textarea") {
    return (
      <textarea
        value={form[step.key]}
        onChange={(event) => update(step.key, event.target.value)}
        minLength={step.minLength}
        placeholder="Напишите здесь..."
        required
      />
    );
  }

  if (step.type === "consents") {
    return (
      <div className="consent-box">
        <label className="checkbox-line">
          <input
            type="checkbox"
            checked={form.personalDataConsent}
            onChange={(event) => update("personalDataConsent", event.target.checked)}
            required
          />
          <span>
            Согласен на обработку персональных данных по{" "}
            <a href="/privacy" target="_blank">
              политике конфиденциальности
            </a>{" "}
            и{" "}
            <a href="/personal-data" target="_blank">
              согласию на обработку данных
            </a>
            .
          </span>
        </label>
        <label className="checkbox-line">
          <input
            type="checkbox"
            checked={form.communicationConsent}
            onChange={(event) => update("communicationConsent", event.target.checked)}
            required
          />
          <span>
            Согласен получить ответ по заявке через выбранный канал связи согласно{" "}
            <a href="/communication-consent" target="_blank">
              согласию на обратную связь
            </a>
            .
          </span>
        </label>
      </div>
    );
  }

  return (
    <input
      value={form[step.key]}
      onChange={(event) => update(step.key, event.target.value)}
      inputMode={step.type === "tel" ? "tel" : "text"}
      placeholder={step.type === "tel" ? "+7 999 000-00-00" : "Ваш ответ"}
      required
    />
  );
}

function buildSituation(form) {
  const service = services.find((item) => item.slug === form.service);
  return [
    form.situation,
    "",
    `Направление: ${service?.shortTitle || form.service}`,
    `Ключевые факты: ${form.caseDetails}`,
    `Документы: ${form.documents}`,
    `Регион: ${form.region}`
  ].join("\n");
}

function collectUtm() {
  if (typeof window === "undefined") return {};

  const params = new URLSearchParams(window.location.search);
  return {
    utm_source: params.get("utm_source") || "",
    utm_medium: params.get("utm_medium") || "",
    utm_campaign: params.get("utm_campaign") || "",
    utm_term: params.get("utm_term") || "",
    utm_content: params.get("utm_content") || ""
  };
}
