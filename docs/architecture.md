# Architecture

## Goal

Build a Telegram intake bot for a law firm that does first response, lead qualification, CRM sync, manager handoff, and follow-up automation.

## Flow

1. Lead writes to the Telegram bot.
2. Bot starts a short legal intake questionnaire.
3. Answers are persisted in SQLite after each step.
4. Qualification service assigns a score, status, and routing priority.
5. Bitrix24 client creates:
   - CRM lead
   - manager task
   - timeline comment with transcript summary
6. Bot confirms intake and invites the lead to book a consultation or wait for a callback.
7. Reminder loop nudges abandoned or unbooked leads.

## Modules

### `app/domain`

- Intake questionnaire definitions
- Legal routing and qualification rules
- Shared data models

### `app/services`

- Session orchestration
- Validation
- Reminder processing
- Formatting for CRM and manager handoff

### `app/integrations`

- Bitrix24 REST client via incoming webhook

### `app/storage`

- SQLite schema and repository methods

### `app/bot`

- Telegram handlers
- Keyboard builders

## Lead scoring approach

Signals used:

- practice area fit
- urgency and deadlines
- geography fit
- readiness of documents
- readiness to pay for consultation
- preferred consultation format

Statuses:

- `hot`: urgent and high-fit, manager reaction expected quickly
- `qualified`: strong fit, should be contacted in the same business day
- `review`: incomplete or mixed-fit, still worth manual review
- `low_fit`: weak fit or likely non-commercial lead

## Production extension points

- replace long polling with webhook deployment
- replace SQLite with PostgreSQL
- add practice-area-specific branching
- push events from Bitrix24 back into Telegram
- add calendar integration or booking provider sync
- add conflict-check workflow
