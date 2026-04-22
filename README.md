# Legal Intake Bot for Telegram + Bitrix24

Telegram bot for a legal company that:

- responds immediately to inbound leads;
- asks a structured intake questionnaire;
- scores and qualifies the lead;
- creates a lead in Bitrix24;
- creates a follow-up task for the manager;
- stores a transcript summary in the CRM timeline;
- sends reminder follow-ups if the client stops midway.

## What is implemented

- Telegram intake flow in Russian for legal inquiries
- Domain scoring for hot / qualified / review / low-fit leads
- Bitrix24 integration through incoming webhook
- SQLite persistence for active sessions, reminders, and submissions
- Reminder loop for abandoned or unbooked leads
- Optional manager alert in Telegram
- Tests for scoring, Bitrix payload mapping, and storage

## Project structure

```text
app/
  bot/            Telegram handlers and keyboards
  domain/         Intake questions and qualification rules
  integrations/   Bitrix24 API client
  services/       Orchestration of intake flow
  storage/        SQLite persistence
  config.py       Environment settings
  main.py         Application entrypoint
docs/
  architecture.md
  research.md
tests/
```

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -e .
```

3. Copy `.env.example` to `.env` and fill in:

- `TELEGRAM_BOT_TOKEN`
- `BITRIX24_WEBHOOK_URL`
- `BITRIX24_RESPONSIBLE_ID`

4. Run the bot:

```bash
python -m app.main
```

## Bitrix24 setup

Create an incoming webhook in Bitrix24 with scopes for:

- `crm`
- `tasks`

Use the webhook URL in `.env` as `BITRIX24_WEBHOOK_URL`.

The bot creates:

- a CRM lead through `crm.item.add` with `entityTypeId=1`
- a manager task through `tasks.task.add`
- a CRM timeline comment through `crm.timeline.comment.add`

## Telegram flow

The bot asks:

1. practice area
2. client type
3. short case description
4. urgency
5. deadline or court date
6. opposing party
7. document readiness
8. geography
9. preferred consultation format
10. budget readiness
11. contact details

Then it:

- scores the lead
- confirms receipt
- optionally shares a booking link
- creates a Bitrix24 lead and task

## Notes

- The bot uses long polling, which is the simplest way to launch quickly.
- Reminder jobs run inside the same process.
- SQLite is enough for MVP and small-to-medium lead volume. For higher load, replace the storage layer.
- If your Bitrix24 has required custom fields, extend the payload mapping in `app/integrations/bitrix24.py`.
