# Lex Chess Legal Site

Next.js site for a legal practice focused on private clients:

- bankruptcy of individuals;
- divorce;
- division of marital property.

## Run locally

```bash
npm install
npm run dev
```

Production build:

```bash
npm run build
npm run start
```

## Pages

- `/`
- `/services/bankrotstvo-fizicheskih-lic`
- `/services/razvod`
- `/services/razdel-imushchestva`
- `/articles`
- `/articles/kak-prohodit-bankrotstvo-fizlic`
- `/articles/razvod-cherez-sud-chto-nuzhno`
- `/articles/razdel-imushchestva-posle-razvoda`
- `/privacy`
- `/personal-data`
- `/communication-consent`
- `/sitemap.xml`
- `/robots.txt`

## Lead capture

The diagnostic form posts to `/api/leads`.

The endpoint:

- validates required fields and consent checkboxes;
- saves a local JSONL copy;
- creates a Bitrix24 lead through `crm.item.add` when `BITRIX24_WEBHOOK_URL` is configured;
- creates a manager task through `tasks.task.add`;
- adds a timeline comment through `crm.timeline.comment.add`;
- optionally notifies the manager in Telegram when `TELEGRAM_BOT_TOKEN` and `MANAGER_TELEGRAM_CHAT_ID` are configured.

All leads are saved to:

```text
site/data/site-leads.jsonl
```

CRM sync errors are also saved to:

```text
site/data/site-leads-errors.jsonl
```

The form sends UTM tags and the current page URL so Bitrix24 can preserve lead attribution.

## Embeddable widget

Any external site or website builder can load the intake widget with one script:

```html
<script
  src="https://dnatext.ru/widget.js"
  data-title="Lex Chess"
  data-subtitle="Первичная юридическая диагностика"
  data-button-text="Спросить юриста"
  data-position="right"
  data-accent="#f4f4f0"
  defer
></script>
```

For another backend domain, override the API endpoint:

```html
<script
  src="https://dnatext.ru/widget.js"
  data-api-url="https://dnatext.ru/api/leads"
  defer
></script>
```

Set `WIDGET_ALLOWED_ORIGINS` to a comma-separated allowlist for production, for example:

```text
WIDGET_ALLOWED_ORIGINS=https://client-site.ru,https://www.client-site.ru
```

## SEO foundations

- metadata and canonical URLs;
- Open Graph image from the provided logo;
- `robots.js`;
- `sitemap.js`;
- `manifest.js`;
- JSON-LD: `LegalService`, `Service`, `FAQPage`;
- separate landing pages for each legal service;
- article hub for long-tail search demand.
