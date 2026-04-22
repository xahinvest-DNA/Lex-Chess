(function () {
  "use strict";

  if (window.LexChessWidget && window.LexChessWidget.__ready) return;

  var currentScript = document.currentScript;
  var scriptOrigin = currentScript ? new URL(currentScript.src, window.location.href).origin : window.location.origin;

  var SERVICES = [
    { value: "bankrotstvo-fizicheskih-lic", label: "Банкротство физлиц" },
    { value: "razvod", label: "Развод" },
    { value: "razdel-imushchestva", label: "Раздел имущества" }
  ];

  var SLOTS = [
    "Сегодня 16:00-18:00",
    "Завтра 10:00-12:00",
    "Завтра 15:00-17:00",
    "Ближайший свободный слот"
  ];

  var STEPS = [
    {
      key: "service",
      label: "Направление",
      question: "С каким вопросом нужна помощь?",
      helper: "Работаем с физическими лицами: банкротство, развод, раздел имущества.",
      type: "choice",
      options: SERVICES
    },
    {
      key: "situation",
      label: "Ситуация",
      question: "Опишите ситуацию в двух-трех предложениях.",
      helper: "Что произошло, какие документы есть и чего хотите добиться?",
      type: "textarea",
      minLength: 20
    },
    {
      key: "urgency",
      label: "Срочность",
      question: "Насколько срочный вопрос?",
      type: "choice",
      options: ["Сегодня", "В ближайшие 3 дня", "1-2 недели", "Пока просто консультация"]
    },
    {
      key: "caseDetails",
      label: "Детали",
      question: "Уточните ключевые факты.",
      helper: "Например: сумма долга, есть ли дети, что нужно делить, есть ли суд или приставы.",
      type: "textarea",
      minLength: 3
    },
    {
      key: "documents",
      label: "Документы",
      question: "Документы уже есть?",
      type: "choice",
      options: ["Да, все основные", "Частично", "Пока нет"]
    },
    {
      key: "region",
      label: "Регион",
      question: "В каком регионе нужно вести вопрос?",
      helper: "Например: Москва, область, онлайн по РФ или другой регион.",
      type: "text",
      minLength: 2
    },
    {
      key: "name",
      label: "Имя",
      question: "Как к вам обращаться?",
      type: "text",
      minLength: 3
    },
    {
      key: "phone",
      label: "Телефон",
      question: "Оставьте номер телефона для связи.",
      helper: "Юрист или менеджер свяжется с вами по заявке.",
      type: "tel",
      minLength: 10
    },
    {
      key: "contact",
      label: "Канал",
      question: "Как удобнее получить ответ?",
      type: "choice",
      options: ["Телефон", "Telegram", "WhatsApp"]
    },
    {
      key: "consultationSlot",
      label: "Консультация",
      question: "Выберите предварительное окно для консультации.",
      helper: "Юрист подтвердит точное время после проверки заявки.",
      type: "choice",
      options: SLOTS
    },
    {
      key: "consents",
      label: "Согласия",
      question: "Подтвердите согласия, чтобы отправить заявку.",
      helper: "Без согласий мы не сможем обработать контактные данные и ответить.",
      type: "consents"
    }
  ];

  function init(userConfig) {
    var config = readConfig(userConfig || {});
    if (document.getElementById(config.mountId)) return;

    var host = document.createElement("div");
    host.id = config.mountId;
    document.body.appendChild(host);

    var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;
    var state = {
      open: config.open,
      step: 0,
      loading: false,
      message: "",
      telegramUrl: "",
      form: {
        service: SERVICES[0].value,
        situation: "",
        urgency: "В ближайшие 3 дня",
        caseDetails: "",
        documents: "Частично",
        region: "",
        name: "",
        phone: "",
        contact: "Телефон",
        consultationSlot: SLOTS[0],
        personalDataConsent: false,
        communicationConsent: false
      }
    };

    function setState(patch) {
      Object.assign(state, patch);
      render();
    }

    function update(field, value) {
      state.form[field] = value;
      state.message = "";
      render();
    }

    function canContinue() {
      var step = STEPS[state.step];
      if (step.type === "consents") {
        return state.form.personalDataConsent && state.form.communicationConsent;
      }
      var value = String(state.form[step.key] || "").trim();
      if (!value) return false;
      if (step.key === "phone") return value.replace(/\D/g, "").length >= step.minLength;
      return !step.minLength || value.length >= step.minLength;
    }

    function next() {
      if (!canContinue()) {
        setState({ message: "Заполните текущий шаг, чтобы продолжить." });
        return;
      }
      setState({ step: Math.min(state.step + 1, STEPS.length - 1), message: "" });
    }

    function back() {
      setState({ step: Math.max(state.step - 1, 0), message: "" });
    }

    function reset() {
      state.step = 0;
      state.loading = false;
      state.message = "";
      state.telegramUrl = "";
      state.form.situation = "";
      state.form.caseDetails = "";
      state.form.region = "";
      state.form.name = "";
      state.form.phone = "";
      state.form.personalDataConsent = false;
      state.form.communicationConsent = false;
      render();
    }

    function submit() {
      if (!canContinue()) {
        setState({ message: "Подтвердите согласия, чтобы отправить заявку." });
        return;
      }

      setState({ loading: true, message: "" });

      fetch(config.apiUrl, {
        method: "POST",
        mode: "cors",
        headers: {
          "Content-Type": "application/json",
          "X-LexChess-Widget": "1"
        },
        body: JSON.stringify(buildPayload(state.form, config))
      })
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) {
              throw new Error(data.error || "Не удалось отправить заявку.");
            }
            return data;
          });
        })
        .then(function (data) {
          state.loading = false;
          state.step = STEPS.length;
          state.telegramUrl = data.telegramUrl || "";
          state.message = data.crm && data.crm.leadId
            ? "Заявка принята и передана юристу."
            : "Заявка принята. Мы сохранили ее и свяжемся с вами.";
          render();
        })
        .catch(function (error) {
          setState({
            loading: false,
            message: error && error.message ? error.message : "Не удалось отправить заявку. Попробуйте еще раз."
          });
        });
    }

    function render() {
      root.innerHTML = "";
      root.appendChild(styleNode(config));

      var wrapper = el("div", "lcw lcw--" + config.position + (state.open ? " lcw--open" : ""));
      var button = el("button", "lcw__launcher", config.buttonText);
      button.type = "button";
      button.setAttribute("aria-expanded", String(state.open));
      button.addEventListener("click", function () {
        setState({ open: !state.open });
      });
      wrapper.appendChild(button);

      if (state.open) {
        wrapper.appendChild(renderPanel());
      }

      root.appendChild(wrapper);
    }

    function renderPanel() {
      var panel = el("section", "lcw__panel");
      var header = el("div", "lcw__header");
      header.appendChild(el("div", "lcw__brand", config.title));
      header.appendChild(el("p", "", config.subtitle));

      var close = el("button", "lcw__close", "×");
      close.type = "button";
      close.setAttribute("aria-label", "Закрыть");
      close.addEventListener("click", function () {
        setState({ open: false });
      });
      header.appendChild(close);
      panel.appendChild(header);

      if (state.step >= STEPS.length) {
        panel.appendChild(renderSuccess());
        return panel;
      }

      var step = STEPS[state.step];
      var progress = Math.round(((state.step + 1) / STEPS.length) * 100);
      var meta = el("div", "lcw__meta");
      meta.appendChild(el("span", "", "Шаг " + (state.step + 1) + " из " + STEPS.length));
      meta.appendChild(el("strong", "", step.label));
      panel.appendChild(meta);

      var bar = el("div", "lcw__progress");
      var fill = el("span");
      fill.style.width = progress + "%";
      bar.appendChild(fill);
      panel.appendChild(bar);

      var bubble = el("div", "lcw__bubble");
      bubble.appendChild(el("h3", "", step.question));
      if (step.helper) bubble.appendChild(el("p", "", step.helper));
      panel.appendChild(bubble);

      panel.appendChild(renderInput(step));

      if (state.message) {
        panel.appendChild(el("p", "lcw__message", state.message));
      }

      var actions = el("div", "lcw__actions");
      var backButton = el("button", "lcw__ghost", "Назад");
      backButton.type = "button";
      backButton.disabled = state.step === 0 || state.loading;
      backButton.addEventListener("click", back);
      actions.appendChild(backButton);

      var primary = el("button", "lcw__primary", state.step === STEPS.length - 1 ? (state.loading ? "Отправляем..." : "Отправить") : "Продолжить");
      primary.type = "button";
      primary.disabled = state.loading;
      primary.addEventListener("click", state.step === STEPS.length - 1 ? submit : next);
      actions.appendChild(primary);
      panel.appendChild(actions);

      return panel;
    }

    function renderInput(step) {
      if (step.type === "choice") {
        var list = el("div", "lcw__choices");
        step.options.forEach(function (option) {
          var value = typeof option === "string" ? option : option.value;
          var label = typeof option === "string" ? option : option.label;
          var item = el("button", state.form[step.key] === value ? "lcw__choice lcw__choice--active" : "lcw__choice", label);
          item.type = "button";
          item.addEventListener("click", function () {
            update(step.key, value);
          });
          list.appendChild(item);
        });
        return list;
      }

      if (step.type === "textarea") {
        var textarea = el("textarea", "lcw__field");
        textarea.value = state.form[step.key] || "";
        textarea.placeholder = "Напишите здесь...";
        textarea.addEventListener("input", function (event) {
          update(step.key, event.target.value);
        });
        return textarea;
      }

      if (step.type === "consents") {
        var box = el("div", "lcw__consents");
        box.appendChild(renderCheckbox("personalDataConsent", "Согласен на обработку персональных данных."));
        box.appendChild(renderCheckbox("communicationConsent", "Согласен получить ответ по заявке через выбранный канал связи."));
        box.appendChild(el("p", "lcw__legal", "Отправляя заявку, вы подтверждаете согласия. Точные условия консультации юрист согласует после первичной диагностики."));
        return box;
      }

      var input = el("input", "lcw__field");
      input.value = state.form[step.key] || "";
      input.type = step.type === "tel" ? "tel" : "text";
      input.placeholder = step.type === "tel" ? "+7 999 000-00-00" : "Ваш ответ";
      input.addEventListener("input", function (event) {
        update(step.key, event.target.value);
      });
      return input;
    }

    function renderCheckbox(key, text) {
      var label = el("label", "lcw__check");
      var input = el("input");
      input.type = "checkbox";
      input.checked = Boolean(state.form[key]);
      input.addEventListener("change", function (event) {
        update(key, event.target.checked);
      });
      label.appendChild(input);
      label.appendChild(el("span", "", text));
      return label;
    }

    function renderSuccess() {
      var success = el("div", "lcw__success");
      success.appendChild(el("div", "lcw__badge", "Заявка принята"));
      success.appendChild(el("h3", "", "Юрист получил контекст и свяжется с вами."));
      success.appendChild(el("p", "", state.message));

      if (state.telegramUrl) {
        var link = el("a", "lcw__primary lcw__link", "Открыть Telegram-чат");
        link.href = state.telegramUrl;
        link.target = "_blank";
        link.rel = "noopener";
        success.appendChild(link);
        success.appendChild(el("p", "lcw__legal", "Telegram необязателен. Он нужен, если хотите дослать документы, фото или уточнения."));
      }

      var again = el("button", "lcw__ghost lcw__wide", "Новая заявка");
      again.type = "button";
      again.addEventListener("click", reset);
      success.appendChild(again);
      return success;
    }

    render();
  }

  function readConfig(userConfig) {
    var dataset = currentScript ? currentScript.dataset : {};
    return {
      apiUrl: userConfig.apiUrl || dataset.apiUrl || scriptOrigin + "/api/leads",
      mountId: userConfig.mountId || dataset.mountId || "lex-chess-widget",
      title: userConfig.title || dataset.title || "Lex Chess",
      subtitle: userConfig.subtitle || dataset.subtitle || "Первичная юридическая диагностика",
      buttonText: userConfig.buttonText || dataset.buttonText || "Спросить юриста",
      position: userConfig.position || dataset.position || "right",
      accent: userConfig.accent || dataset.accent || "#f4f4f0",
      open: String(userConfig.open || dataset.open || "").toLowerCase() === "true"
    };
  }

  function buildPayload(form, config) {
    return {
      service: form.service,
      situation: form.situation,
      urgency: form.urgency,
      caseDetails: form.caseDetails,
      documents: form.documents,
      region: form.region,
      name: form.name,
      phone: form.phone,
      contact: form.contact,
      consultationSlot: form.consultationSlot,
      personalDataConsent: form.personalDataConsent,
      communicationConsent: form.communicationConsent,
      source: "widget",
      widgetTitle: config.title,
      pageUrl: window.location.href,
      utm: collectUtm()
    };
  }

  function collectUtm() {
    var params = new URLSearchParams(window.location.search);
    return {
      utm_source: params.get("utm_source") || "",
      utm_medium: params.get("utm_medium") || "",
      utm_campaign: params.get("utm_campaign") || "",
      utm_term: params.get("utm_term") || "",
      utm_content: params.get("utm_content") || ""
    };
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function styleNode(config) {
    var style = document.createElement("style");
    style.textContent = `
      :host { all: initial; }
      .lcw, .lcw * { box-sizing: border-box; font-family: Georgia, "Times New Roman", serif; }
      .lcw { position: fixed; z-index: 2147483000; bottom: 22px; color: #f6f6f1; }
      .lcw--right { right: 22px; }
      .lcw--left { left: 22px; }
      .lcw__launcher {
        border: 1px solid rgba(255,255,255,.22); border-radius: 999px; padding: 14px 20px;
        background: #070809; color: #f6f6f1; box-shadow: 0 20px 60px rgba(0,0,0,.36);
        font: 700 15px/1.1 Arial, sans-serif; letter-spacing: .02em; cursor: pointer;
      }
      .lcw__launcher:hover { background: #17191b; }
      .lcw__panel {
        position: absolute; bottom: 66px; width: 390px; max-width: calc(100vw - 28px);
        background: linear-gradient(155deg, #101113, #050607 68%); border: 1px solid rgba(255,255,255,.16);
        border-radius: 28px; padding: 18px; box-shadow: 0 26px 90px rgba(0,0,0,.45);
      }
      .lcw--right .lcw__panel { right: 0; }
      .lcw--left .lcw__panel { left: 0; }
      .lcw__header { position: relative; padding: 6px 42px 14px 4px; border-bottom: 1px solid rgba(255,255,255,.1); }
      .lcw__brand { font: 800 18px/1.1 Arial, sans-serif; letter-spacing: .08em; text-transform: uppercase; }
      .lcw__header p, .lcw__bubble p, .lcw__success p, .lcw__legal { margin: 7px 0 0; color: rgba(246,246,241,.72); font: 14px/1.45 Arial, sans-serif; }
      .lcw__close {
        position: absolute; top: 0; right: 0; width: 34px; height: 34px; border-radius: 50%;
        border: 1px solid rgba(255,255,255,.18); background: transparent; color: #f6f6f1; font-size: 24px; cursor: pointer;
      }
      .lcw__meta { display: flex; justify-content: space-between; gap: 14px; margin: 16px 0 8px; color: rgba(246,246,241,.66); font: 12px/1 Arial, sans-serif; }
      .lcw__meta strong { color: #f6f6f1; text-transform: uppercase; letter-spacing: .08em; }
      .lcw__progress { height: 6px; overflow: hidden; border-radius: 999px; background: rgba(255,255,255,.09); }
      .lcw__progress span { display: block; height: 100%; border-radius: inherit; background: ${config.accent}; transition: width .25s ease; }
      .lcw__bubble { margin: 16px 0 12px; padding: 16px; border-radius: 20px; background: rgba(255,255,255,.07); }
      .lcw__bubble h3, .lcw__success h3 { margin: 0; color: #fff; font: 700 21px/1.18 Georgia, "Times New Roman", serif; }
      .lcw__choices { display: grid; gap: 8px; }
      .lcw__choice, .lcw__ghost, .lcw__primary {
        border-radius: 999px; border: 1px solid rgba(255,255,255,.16); padding: 12px 14px;
        font: 700 14px/1.1 Arial, sans-serif; cursor: pointer;
      }
      .lcw__choice { width: 100%; text-align: left; background: rgba(255,255,255,.05); color: #f6f6f1; }
      .lcw__choice--active { background: ${config.accent}; color: #101113; border-color: ${config.accent}; }
      .lcw__field {
        width: 100%; min-height: 48px; border-radius: 18px; border: 1px solid rgba(255,255,255,.16);
        background: rgba(255,255,255,.06); color: #fff; padding: 14px; outline: none; font: 15px/1.4 Arial, sans-serif;
      }
      textarea.lcw__field { min-height: 118px; resize: vertical; }
      .lcw__field:focus { border-color: ${config.accent}; box-shadow: 0 0 0 3px rgba(244,244,240,.08); }
      .lcw__consents { display: grid; gap: 10px; }
      .lcw__check { display: flex; gap: 10px; color: rgba(246,246,241,.82); font: 13px/1.35 Arial, sans-serif; }
      .lcw__check input { margin-top: 2px; accent-color: #f4f4f0; }
      .lcw__message { margin: 12px 0 0; color: #ffd9a6; font: 14px/1.35 Arial, sans-serif; }
      .lcw__actions { display: flex; justify-content: space-between; gap: 10px; margin-top: 16px; }
      .lcw__ghost { background: transparent; color: #f6f6f1; min-width: 104px; }
      .lcw__ghost:disabled { opacity: .35; cursor: not-allowed; }
      .lcw__primary { flex: 1; background: ${config.accent}; color: #101113; border-color: ${config.accent}; text-align: center; text-decoration: none; }
      .lcw__success { display: grid; gap: 12px; padding-top: 18px; }
      .lcw__badge { width: max-content; border-radius: 999px; padding: 8px 12px; background: rgba(255,255,255,.1); color: rgba(246,246,241,.78); font: 700 12px/1 Arial, sans-serif; text-transform: uppercase; letter-spacing: .08em; }
      .lcw__link { display: block; }
      .lcw__wide { width: 100%; }
      @media (max-width: 520px) {
        .lcw { left: 12px; right: 12px; bottom: 12px; }
        .lcw__launcher { width: 100%; }
        .lcw__panel { left: 0 !important; right: 0 !important; width: 100%; bottom: 62px; border-radius: 22px; }
      }
    `;
    return style;
  }

  window.LexChessWidget = { __ready: true, init: init };

  function boot() {
    var autoInit = !currentScript || currentScript.dataset.autoInit !== "false";
    if (autoInit) init({});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
