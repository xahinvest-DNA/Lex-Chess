import Link from "next/link";

import { SITE, services } from "@/lib/site-data";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-top">
        <div>
          <p className="eyebrow">Lex Chess</p>
          <h2>Первичная юридическая диагностика для частных клиентов.</h2>
          <p className="footer-lead">
            Работаем по трем направлениям: банкротство физических лиц, развод и раздел имущества. Без универсального
            каталога услуг и без обещаний результата до анализа ситуации.
          </p>
        </div>
        <a className="button button--primary footer-cta" href="#diagnostic">
          Перейти к заявке
        </a>
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
          <strong>Направления</strong>
          {services.map((service) => (
            <Link key={service.slug} href={`/services/${service.slug}`}>
              {service.shortTitle}
            </Link>
          ))}
        </div>
        <div>
          <strong>Полезное</strong>
          <Link href="/articles">Статьи и разборы</Link>
          <Link href="/#diagnostic">Онлайн-диагностика</Link>
          <Link href="/#faq">Частые вопросы</Link>
        </div>
        <div>
          <strong>Документы</strong>
          <Link href="/privacy">Политика конфиденциальности</Link>
          <Link href="/personal-data">Обработка персональных данных</Link>
          <Link href="/communication-consent">Согласие на обратную связь</Link>
        </div>
      </div>

      <p className="legal-note">
        Информация на сайте носит справочный характер и не является индивидуальной юридической консультацией,
        публичной офертой или гарантией результата. Правовая позиция формируется после анализа документов и фактических
        обстоятельств.
      </p>
    </footer>
  );
}
