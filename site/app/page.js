import Link from "next/link";

import ConsultationTerms from "@/components/ConsultationTerms";
import LeadIntake from "@/components/LeadIntake";
import LegalDisclaimer from "@/components/LegalDisclaimer";
import JsonLd from "@/components/JsonLd";
import { faqSchema } from "@/lib/schema";
import { homeFaq, services, SITE } from "@/lib/site-data";

const trustPoints = [
  "Работаем только с физическими лицами",
  "Конфиденциальная первичная диагностика",
  "Онлайн и очно по согласованию"
];

const clientBenefits = [
  "Понимает, подходит ли его ситуация под нашу специализацию.",
  "Не повторяет одно и то же в форме, мессенджере и звонке.",
  "Получает понятный следующий шаг без завышенных обещаний."
];

const diagnosticPoints = [
  "Система собирает направление, срочность, документы и удобный канал связи.",
  "Юрист получает уже собранный контекст, а не пустую заявку без деталей.",
  "Telegram остается опцией после отправки, а не обязательным шагом."
];

const processSteps = [
  {
    title: "Коротко описываете ситуацию",
    text: "Оставляете заявку на сайте и проходите первичную диагностику без лишней переписки."
  },
  {
    title: "Получаем структуру по делу",
    text: "Форма собирает нужные вводные: направление, срочность, факты, документы и способ связи."
  },
  {
    title: "Согласуем следующий шаг",
    text: "После первичной оценки согласуем формат консультации, документы и удобное время контакта."
  }
];

export default function HomePage() {
  return (
    <main>
      <JsonLd data={faqSchema(homeFaq)} />

      <section className="hero hero--light section-shell">
        <div className="hero__content">
          <p className="eyebrow">Банкротство физических лиц • развод • раздел имущества</p>
          <h1>Юридическая помощь частным клиентам в спокойной, понятной и аккуратной подаче.</h1>
          <p className="hero__lead">
            Сайт помогает человеку быстро понять, с какой проблемой мы работаем, что происходит после заявки и как
            выглядит первый контакт с юристом. Без перегруза, без тяжелой атмосферы и без пустых обещаний.
          </p>

          <div className="hero__actions">
            <a className="button button--primary" href="#diagnostic">
              Получить первичную оценку
            </a>
            <a className="button button--ghost" href={`tel:${SITE.phone.replace(/\D/g, "")}`}>
              Позвонить юристу
            </a>
          </div>

          <div className="trust-strip" aria-label="Преимущества">
            {trustPoints.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>

        <aside className="hero-visual">
          <div className="hero-photo-card">
            <img
              src="https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=1400&q=80"
              alt="Спокойная консультация с юристом в светлом офисе"
              loading="eager"
            />
            <div className="hero-photo-badge">
              <strong>Lex Chess</strong>
              <span>Первичный контакт должен вызывать доверие, а не напряжение.</span>
            </div>
          </div>
        </aside>
      </section>

      <section className="section-shell section section--compact">
        <div className="section-head">
          <div>
            <p className="eyebrow">Направления</p>
            <h2>Оставляем три четких услуги, чтобы человеку было легче узнать свою ситуацию и оставить заявку.</h2>
          </div>
          <p>
            Узкая структура повышает доверие и работает лучше универсального каталога: человек сразу видит, что сайт
            сделан под конкретные запросы частных клиентов.
          </p>
        </div>
        <div className="service-grid">
          {services.map((service, index) => (
            <Link className="service-card" href={`/services/${service.slug}`} key={service.slug}>
              <span>0{index + 1}</span>
              <p className="eyebrow">{service.accent}</p>
              <h3>{service.shortTitle}</h3>
              <p>{service.description}</p>
              <strong className="service-card__cta">Подробнее</strong>
            </Link>
          ))}
        </div>
      </section>

      <section className="section-shell photo-story">
        <div className="photo-story__image">
          <img
            src="https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1400&q=80"
            alt="Работа с документами и правовой оценкой"
            loading="lazy"
          />
        </div>
        <div className="photo-story__content">
          <p className="eyebrow">Первое впечатление</p>
          <h2>Доверие появляется, когда сайт выглядит как аккуратная консультация, а не как перегруженный лендинг.</h2>
          <p>
            Поэтому мы убрали лишнюю дробность, уменьшили количество равнозначных карточек и добавили живые визуальные
            акценты. Теперь структура воспринимается спокойнее и ближе к реальной юридической практике.
          </p>
          <ul className="check-list">
            {clientBenefits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section-shell split-section split-section--highlight" id="diagnostic">
        <div className="split-section__content">
          <p className="eyebrow">Диагностика на сайте</p>
          <h2>Основное действие остается одним: человек оставляет заявку прямо на сайте и получает понятный маршрут.</h2>
          <p>
            Логику intake-бота мы сохранили, но окружили ее более спокойной и доверительной подачей. Теперь форма не
            спорит с дизайном страницы, а выглядит как органичное продолжение консультации.
          </p>
          <ul className="check-list">
            {diagnosticPoints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <LeadIntake />
      </section>

      <section className="section-shell process-section">
        <div className="section-head section-head--single">
          <div>
            <p className="eyebrow">Как это выглядит</p>
            <h2>Простой путь от первого вопроса до следующего практического шага.</h2>
          </div>
        </div>
        <ol className="process-list process-list--compact">
          {processSteps.map((item) => (
            <li key={item.title}>
              <strong>{item.title}</strong>
              <span>{item.text}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="section-shell section">
        <ConsultationTerms />
      </section>

      <section className="section-shell section">
        <LegalDisclaimer />
      </section>

      <section className="section-shell faq-section" id="faq">
        <div className="section-head">
          <div>
            <p className="eyebrow">FAQ</p>
            <h2>Короткие ответы на вопросы, которые чаще всего мешают человеку оставить заявку.</h2>
          </div>
          <p>
            FAQ оставляем как важный доверительный и SEO-блок, но без лишнего визуального шума вокруг него.
          </p>
        </div>
        <div className="faq-list">
          {homeFaq.map((item) => (
            <details key={item.question}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </section>
    </main>
  );
}
