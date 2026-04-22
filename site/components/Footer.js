import Link from "next/link";

import { SITE, services } from "@/lib/site-data";

export default function Footer() {
  return (
    <footer className="footer">
      <div>
        <p className="eyebrow">Юридическая стратегия для частных клиентов</p>
        <h2>Начните с диагностики, а не с обещаний.</h2>
      </div>
      <div className="footer-grid">
        <div>
          <strong>{SITE.legalName}</strong>
          <p>{SITE.address}</p>
          <p>
            <a href={`tel:${SITE.phone.replace(/\D/g, "")}`}>{SITE.phone}</a>
          </p>
          <p>
            <a href={`mailto:${SITE.email}`}>{SITE.email}</a>
          </p>
        </div>
        <div>
          <strong>Услуги</strong>
          {services.map((service) => (
            <Link key={service.slug} href={`/services/${service.slug}`}>
              {service.shortTitle}
            </Link>
          ))}
        </div>
        <div>
          <strong>SEO-разделы</strong>
          <Link href="/articles">Статьи и разборы</Link>
          <Link href="/#diagnostic">Онлайн-диагностика</Link>
          <Link href="/#faq">Вопросы и ответы</Link>
        </div>
        <div>
          <strong>Документы</strong>
          <Link href="/privacy">Политика конфиденциальности</Link>
          <Link href="/personal-data">Обработка персональных данных</Link>
          <Link href="/communication-consent">Согласие на обратную связь</Link>
        </div>
      </div>
      <p className="legal-note">
        Информация на сайте не является индивидуальной юридической консультацией. Точный маршрут
        определяется после анализа документов и фактических обстоятельств.
      </p>
    </footer>
  );
}
