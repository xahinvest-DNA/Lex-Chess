# Website Lead Integration

## Current behavior

The website form posts to:

```text
/api/leads
```

The route performs four actions:

1. validates required fields and consent checkboxes;
2. saves the lead locally in `site/data/site-leads.jsonl`;
3. creates a Bitrix24 CRM lead, task and timeline comment if Bitrix24 env vars are configured;
4. sends a Telegram manager notification if Telegram env vars are configured.

The endpoint intentionally returns `ok: true` even if Bitrix24 is temporarily unavailable. In that
case the local JSONL copy remains the fallback source of truth, and the CRM error is stored in
`site/data/site-leads-errors.jsonl`.

## Required Bitrix24 env vars

```text
BITRIX24_WEBHOOK_URL=https://your-company.bitrix24.ru/rest/1/your_webhook_code
BITRIX24_ENTITY_TYPE_ID=1
BITRIX24_RESPONSIBLE_ID=1
BITRIX24_CREATOR_ID=1
BITRIX24_SOURCE_ID=WEB
```

The webhook needs access to `crm` and `tasks`.

## Optional Telegram manager notification

```text
TELEGRAM_BOT_TOKEN=123456:replace_me
MANAGER_TELEGRAM_CHAT_ID=123456789
```

## Future deep-link handoff

The form returns a deep link based on `NEXT_PUBLIC_TELEGRAM_URL`:

```text
https://t.me/your_legal_bot?start=lead_<requestId>
```

The Telegram bot can load `site/data/site-leads.jsonl` by `requestId`, prefill known answers and ask
only the missing qualification questions.
