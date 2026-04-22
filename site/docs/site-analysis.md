# Анализ структуры юридических сайтов и SEO-архитектуры

## Что повторяется у эффективных юридических сайтов

- Сильный первый экран с конкретной специализацией, а не общей фразой "юридические услуги".
- Быстрый CTA: консультация, диагностика, телефон, мессенджер.
- Разделение услуг на отдельные посадочные страницы под разные поисковые намерения.
- Блоки доверия: опыт, конфиденциальность, договор, понятный процесс, юридические риски.
- Описание этапов работы, документов и ограничений без обещания гарантированного результата.
- FAQ под возражения и long-tail поисковые запросы.
- Контент-хаб со статьями, который усиливает основные посадочные страницы.

## Выводы по нишам

### Банкротство физических лиц

Конвертируют страницы, где сразу видны: анализ долга, последствия, риски для имущества,
стоимость/рассрочка или понятный способ получить оценку, этапы процедуры, предупреждения о
последствиях банкротства.

### Развод

Важны спокойствие, конфиденциальность, возможность развода без личного участия, сценарии через ЗАГС
или суд, дети, алименты, связь с имущественным спором.

### Раздел имущества

Нужны конкретные активы: недвижимость, автомобили, ипотека, бизнес, долги, скрытые активы,
соглашение или суд, расчет позиции.

## SEO-решение в проекте

- App Router в Next.js.
- Отдельные URL под каждую услугу.
- Человекопонятные slug: `/services/bankrotstvo-fizicheskih-lic`, `/services/razvod`,
  `/services/razdel-imushchestva`.
- `metadata`, canonical, Open Graph.
- `robots.js`, `sitemap.js`, `manifest.js`.
- JSON-LD: `LegalService`, `Service`, `FAQPage`.
- Внутренняя перелинковка: главная → услуги → статьи → диагностика.
- Контент-хаб `/articles` для информационных запросов.

## Источники

- Google SEO Starter Guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Google helpful content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google LocalBusiness structured data: https://developers.google.com/search/docs/appearance/structured-data/local-business
- Next.js App Router docs: https://nextjs.org/docs/app
- Next.js robots metadata docs: https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots
- Next.js sitemap metadata docs: https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap
