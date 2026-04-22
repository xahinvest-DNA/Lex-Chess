import Link from "next/link";

import ConsultationTerms from "@/components/ConsultationTerms";
import LeadIntake from "@/components/LeadIntake";
import LegalDisclaimer from "@/components/LegalDisclaimer";
import JsonLd from "@/components/JsonLd";
import { faqSchema } from "@/lib/schema";
import { homeFaq, services, SITE } from "@/lib/site-data";

export default function HomePage() {
  return (
    <main>
      <JsonLd data={faqSchema(homeFaq)} />

      <section className="hero section-shell">
        <div className="hero__content">
          <p className="eyebrow">Банкротство физлиц · развод · раздел имущества</p>
          <h1>Юридическая защита для частных клиентов, когда на кону деньги, семья и имущество.</h1>
          <p className="hero__lead">
            Мы строим стратегию как шахматную партию: сначала видим риски, затем выбираем ход,
            который защищает вас от лишних потерь.
          </p>
          <div className="hero__actions">
            <a className="button button--primary" href="#diagnostic">
              Пройти диагностику
            </a>
            <a className="button button--ghost" href={`tel:${SITE.phone.replace(/\D/g, "")}`}>
              Позвонить юристу
            </a>
          </div>
          <div className="trust-strip" aria-label="Ключевые преимущества">
            <span>Физические лица</span>
            <span>Конфиденциально</span>
            <span>Документы и суд</span>
          </div>
        </div>
        <div className="hero__emblem" aria-hidden="true">
          <div className="emblem-card">
            <span>Legal strategy</span>
            <strong>01</strong>
            <p>Позиция строится до первого процессуального шага.</p>
          </div>
        </div>
      </section>

      <section className="section-shell section">
        <div className="section-head">
          <p className="eyebrow">Три практики</p>
          <h2>Сфокусированный сайт конвертирует лучше универсального каталога услуг.</h2>
          <p>
            Для SEO и продаж каждая специализация вынесена в отдельную посадочную страницу с
            собственным интентом, FAQ, внутренними ссылками и schema.org.
          </p>
        </div>
        <div className="service-grid">
          {services.map((service, index) => (
            <Link className="service-card" href={`/services/${service.slug}`} key={service.slug}>
              <span>0{index + 1}</span>
              <p className="eyebrow">{service.accent}</p>
              <h3>{service.shortTitle}</h3>
              <p>{service.description}</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="section-shell section">
        <ConsultationTerms />
      </section>

      <section className="section-shell split-section" id="diagnostic">
        <div>
          <p className="eyebrow">Будущая точка интеграции с ботом</p>
          <h2>Сайт-бот собирает лиды в структуре, удобной для Bitrix24 и юриста.</h2>
          <p>
            Пользователь проходит диагностику прямо на сайте, без обязательного перехода в
            мессенджер. Telegram остаётся опцией после отправки: сохранить диалог, дослать
            документы или получить уточнение.
          </p>
          <ul className="check-list">
            <li>направление и срочность для маршрутизации;</li>
            <li>описание ситуации для первичной оценки;</li>
            <li>контакт и канал связи для follow-up;</li>
            <li>сохранение источника lead source = website.</li>
          </ul>
        </div>
        <LeadIntake />
      </section>

      <section className="section-shell section">
        <div className="section-head">
          <p className="eyebrow">Архитектура доверия</p>
          <h2>Что должно быть на юридическом сайте, чтобы человек оставил заявку.</h2>
        </div>
        <div className="proof-grid">
          {[
            ["Проблема", "Показываем, что понимаем давление долгов, развода и имущественного спора."],
            ["Маршрут", "Объясняем этапы и документы без перегруза юридическим языком."],
            ["Риски", "Не обещаем гарантированный результат, а заранее называем ограничения."],
            ["Контакт", "Даем форму, телефон, Telegram и понятный следующий шаг."],
            ["SEO", "Создаем отдельные страницы под разные поисковые намерения."],
            ["Контент", "Добавляем статьи, FAQ, перелинковку, sitemap и schema.org."]
          ].map(([title, text]) => (
            <article className="proof-card" key={title}>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-shell section">
        <LegalDisclaimer />
      </section>

      <section className="section-shell process-section">
        <p className="eyebrow">Как работаем</p>
        <h2>От первичного контакта к юридической стратегии.</h2>
        <ol className="process-list">
          <li>
            <strong>Диагностика</strong>
            <span>Собираем факты, документы, срочность и желаемый результат.</span>
          </li>
          <li>
            <strong>Карта рисков</strong>
            <span>Показываем слабые места, сроки, доказательства и вероятные сценарии.</span>
          </li>
          <li>
            <strong>План действий</strong>
            <span>Выбираем переговоры, документы, суд или процедуру банкротства.</span>
          </li>
          <li>
            <strong>Сопровождение</strong>
            <span>Ведем коммуникацию, подачу документов и контроль результата.</span>
          </li>
        </ol>
      </section>

      <section className="section-shell faq-section" id="faq">
        <div className="section-head">
          <p className="eyebrow">FAQ</p>
          <h2>Ответы на вопросы, которые влияют на конверсию и поисковую видимость.</h2>
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
