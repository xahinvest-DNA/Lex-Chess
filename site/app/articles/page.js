import Link from "next/link";

import { articles, getService } from "@/lib/site-data";

export const metadata = {
  title: "Статьи о банкротстве, разводе и разделе имущества",
  description:
    "Практические материалы для физических лиц: банкротство, развод через суд, раздел имущества супругов."
};

export default function ArticlesPage() {
  return (
    <main className="section-shell page-shell">
      <p className="eyebrow">Контент-хаб для SEO</p>
      <h1>Статьи и разборы для частных клиентов</h1>
      <p className="page-lead">
        Раздел нужен для long-tail запросов, внутренней перелинковки и доверия. Каждая статья
        привязана к основной услуге и усиливает посадочную страницу.
      </p>

      <div className="article-grid">
        {articles.map((article) => {
          const service = getService(article.serviceSlug);
          return (
            <Link className="article-card" href={`/articles/${article.slug}`} key={article.slug}>
              <span>{service.shortTitle}</span>
              <h2>{article.title}</h2>
              <p>{article.description}</p>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
