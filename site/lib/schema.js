import { SITE, services } from "@/lib/site-data";

export function legalServiceSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "LegalService",
    name: SITE.legalName,
    url: SITE.url,
    telephone: SITE.phone,
    email: SITE.email,
    image: `${SITE.url}/logo.jpg`,
    priceRange: "По результатам диагностики",
    areaServed: SITE.areaServed,
    address: {
      "@type": "PostalAddress",
      addressLocality: SITE.city,
      addressCountry: "RU",
      streetAddress: SITE.address
    },
    hasOfferCatalog: {
      "@type": "OfferCatalog",
      name: "Юридические услуги для физических лиц",
      itemListElement: services.map((service) => ({
        "@type": "Offer",
        itemOffered: {
          "@type": "Service",
          name: service.shortTitle,
          description: service.description,
          url: `${SITE.url}/services/${service.slug}`
        }
      }))
    }
  };
}

export function faqSchema(items) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer
      }
    }))
  };
}

export function serviceSchema(service) {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    serviceType: service.shortTitle,
    name: service.title,
    description: service.description,
    provider: {
      "@type": "LegalService",
      name: SITE.legalName,
      url: SITE.url,
      telephone: SITE.phone
    },
    areaServed: SITE.areaServed,
    hasOfferCatalog: {
      "@type": "OfferCatalog",
      name: `Работы по направлению: ${service.shortTitle}`,
      itemListElement: service.deliverables.map((name) => ({
        "@type": "Offer",
        itemOffered: {
          "@type": "Service",
          name
        }
      }))
    }
  };
}
