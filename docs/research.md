# Research Notes

## Telegram Bot API

- Official Telegram Bot API states that bots receive updates either via `getUpdates` or via webhooks, and these are mutually exclusive.
- `getUpdates` with long polling is acceptable for straightforward bot deployments and fast MVP launches.
- Telegram supports reply keyboards and inline keyboards, which is enough for guided intake flows.

Source:

- https://core.telegram.org/bots/api

## Bitrix24 integration choices

- Bitrix24 incoming webhooks are suitable for internal integrations and do not expire, which makes them practical for a single-company deployment.
- The old `crm.lead.add` method is marked deprecated in current Bitrix24 docs; the recommended universal method is `crm.item.add`.
- For leads, Bitrix24 documents `entityTypeId = 1`.
- Bitrix24 supports task creation with `tasks.task.add`.
- Bitrix24 supports adding a transcript or summary to CRM timeline via `crm.timeline.comment.add`.

Sources:

- https://apidocs.bitrix24.com/local-integrations/local-webhooks.html
- https://apidocs.bitrix24.com/api-reference/crm/universal/crm-item-add.html
- https://apidocs.bitrix24.com/api-reference/crm/leads/crm-lead-add.html
- https://apidocs.bitrix24.com/api-reference/tasks/tasks-task-add.html
- https://apidocs.bitrix24.com/api-reference/crm/timeline/comments/crm-timeline-comment-add.html

## Legal intake process research

- Legal intake should start immediately when the lead first reaches out.
- A brief pre-screen before consultation helps filter poor-fit inquiries.
- Intake works best when it is structured into clear stages with reminders and follow-up.
- Appointment reminders and consistent lead tracking are recommended for conversion.

These points informed the bot design: a short guided questionnaire, immediate response, structured qualification, and automated follow-up.

Sources:

- https://www.clio.com/blog/client-intake-process-stages/
- https://www.clio.com/blog/improve-client-intake-law-firm/
- https://www.mycase.com/blog/law-firm-operations/law-firm-client-intake-form/
