import Link from "next/link";
import { notFound } from "next/navigation";

import { articles, getArticle, getService, SITE } from "@/lib/site-data";

export function generateStaticParams() {
  return articles.map((article) => ({ slug: article.slug }));
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const article = getArticle(slug);
  if (!article) return {};

  return {
    title: article.title,
    description: article.description,
    alternates: {
      canonical: `/articles/${article.slug}`
    },
    openGraph: {
      title: article.title,
      description: article.description,
      url: `${SITE.url}/articles/${article.slug}`,
      images: ["/logo.jpg"]
    }
  };
}

export default async function ArticlePage({ params }) {
  const { slug } = await params;
  const article = getArticle(slug);
  if (!article) notFound();
  const service = getService(article.serviceSlug);

  return (
    <main className="section-shell article-page">
      <p className="eyebrow">{service.shortTitle}</p>
      <h1>{article.title}</h1>
      <p className="page-lead">{article.description}</p>

      <article className="article-body">
        {article.sections.map((section) => (
          <p key={section}>{section}</p>
        ))}
      </article>

      <div className="article-cta">
        <h2>Нужна оценка вашей ситуации?</h2>
        <p>Перейдите на профильную страницу и заполните короткую диагностику.</p>
        <Link className="button button--primary" href={`/services/${service.slug}#diagnostic`}>
          Оценить ситуацию
        </Link>
      </div>
    </main>
  );
}
