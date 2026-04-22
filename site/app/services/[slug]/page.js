import Link from "next/link";
import { notFound } from "next/navigation";

import ConsultationTerms from "@/components/ConsultationTerms";
import LeadIntake from "@/components/LeadIntake";
import LegalDisclaimer from "@/components/LegalDisclaimer";
import JsonLd from "@/components/JsonLd";
import { faqSchema, serviceSchema } from "@/lib/schema";
import { getService, services, SITE } from "@/lib/site-data";

export function generateStaticParams() {
  return services.map((service) => ({ slug: service.slug }));
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const service = getService(slug);
  if (!service) return {};

  return {
    title: service.seoTitle,
    description: service.description,
    keywords: service.keywords,
    alternates: {
      canonical: `/services/${service.slug}`
    },
    openGraph: {
      title: service.seoTitle,
      description: service.description,
      url: `${SITE.url}/services/${service.slug}`,
      images: ["/logo.jpg"]
    }
  };
}

export default async function ServicePage({ params }) {
  const { slug } = await params;
  const service = getService(slug);
  if (!service) notFound();

  return (
    <main>
      <JsonLd data={serviceSchema(service)} />
      <JsonLd data={faqSchema(service.faq)} />

      <section className="service-hero section-shell">
        <p className="eyebrow">{service.accent}</p>
        <h1>{service.h1}</h1>
        <p>{service.lead}</p>
        <div className="hero__actions">
          <a className="button button--primary" href="#diagnostic">
            Получить оценку дела
          </a>
          <Link className="button button--ghost" href="/">
            На главную
          </Link>
        </div>
      </section>

      <section className="section-shell service-layout">
        <div className="content-column">
          <section className="text-block">
            <h2>Когда стоит обратиться</h2>
            <ul className="check-list">
              {service.symptoms.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="text-block">
            <h2>Что входит в работу</h2>
            <div className="proof-grid proof-grid--compact">
              {service.deliverables.map((item) => (
                <article className="proof-card" key={item}>
                  <h3>{item}</h3>
                </article>
              ))}
            </div>
          </section>

          <section className="text-block">
            <h2>Этапы</h2>
            <ol className="service-steps">
              {service.process.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          </section>

          <ConsultationTerms />

          <LegalDisclaimer />

          <section className="text-block">
            <h2>Частые вопросы</h2>
            <div className="faq-list">
              {service.faq.map((item) => (
                <details key={item.question}>
                  <summary>{item.question}</summary>
                  <p>{item.answer}</p>
                </details>
              ))}
            </div>
          </section>
        </div>

        <aside className="sticky-aside" id="diagnostic">
          <LeadIntake />
        </aside>
      </section>
    </main>
  );
}
