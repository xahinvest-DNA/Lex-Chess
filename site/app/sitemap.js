import { articles, services, SITE } from "@/lib/site-data";

export default function sitemap() {
  const now = new Date();
  return [
    {
      url: SITE.url,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1
    },
    ...services.map((service) => ({
      url: `${SITE.url}/services/${service.slug}`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.9
    })),
    {
      url: `${SITE.url}/articles`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.7
    },
    {
      url: `${SITE.url}/privacy`,
      lastModified: now,
      changeFrequency: "yearly",
      priority: 0.3
    },
    {
      url: `${SITE.url}/personal-data`,
      lastModified: now,
      changeFrequency: "yearly",
      priority: 0.3
    },
    {
      url: `${SITE.url}/communication-consent`,
      lastModified: now,
      changeFrequency: "yearly",
      priority: 0.3
    },
    ...articles.map((article) => ({
      url: `${SITE.url}/articles/${article.slug}`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.6
    }))
  ];
}
