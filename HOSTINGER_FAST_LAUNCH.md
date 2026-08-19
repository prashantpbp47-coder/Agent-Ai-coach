# PartnersHub AI — Fast Hostinger Launch

## Goal

Launch the agent-sales system first. Do **not** build a separate premium engine in Phase 1.

Agent workflow:

1. Priya sends daily nurture/marketing message on WhatsApp.
2. Agent replies with a case.
3. Priya sends the official PBPartners quotation link.
4. Agent generates the quotation on PBPartners.
5. Agent sends the quotation screenshot/text to Priya.
6. Priya prepares a clean customer/agent follow-up message.
7. Agent sends it to the customer and follows up until closure.
8. New-agent leads are captured through PartnersHub AI.

## Hostinger requirement

The existing backend is Flask/Python. Hostinger's current documentation says Python/Flask require VPS hosting; Web/Cloud hosting plans do not provide the root access needed for Python. Use a Hostinger VPS for the backend.

## Fast deployment option: Docker Manager

Use the repository's `Dockerfile` and `docker-compose.hostinger.yml`.

1. Hostinger hPanel → VPS → Manage.
2. Install/select the Docker template if Docker Manager is not already available.
3. Docker Manager → Compose → Compose from URL/manual.
4. Use the repository's `docker-compose.hostinger.yml`.
5. Set the environment variables below.
6. Deploy.
7. Point the new domain to the VPS and enable SSL.

## Required environment variables

```text
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=gpt-4o-mini
INTERAKT_API_KEY=
INTERAKT_TEMPLATE_MARATHI=daily_motor_support_marathi
INTERAKT_TEMPLATE_HINDI=daily_motor_support_hindi
FAST_LAUNCH_API_KEY=<long-random-secret>
GOOGLE_SHEET_URL=<published-agent-sheet-csv-url>
DAILY_TARGET=500000
PBPARTNERS_URL=https://www.pbpartners.com/
```

Twilio variables are only needed for the existing voice-call features.

## Important WhatsApp rule

Proactive daily messages should use **approved WhatsApp templates** through Interakt. Free-form text should be used for an active customer conversation where the WhatsApp policy window allows it. Do not bypass Meta/Interakt template rules.

## Daily nurture batches

Use Hostinger cron to call the protected endpoint in batches. Default batch size is 25.

```text
POST https://YOUR-DOMAIN/api/daily-nurture?key=FAST_LAUNCH_API_KEY
Content-Type: application/json

{"offset":0,"batch_size":25,"language":"marathi"}
```

Then run the next batch with offsets 25, 50, 75, etc. The exact cron cadence should match the approved messaging limits and the Interakt account configuration.

## Useful URLs

- `/sales` — Priya Sales Command dashboard
- `/agents` — existing agent panel
- `/pbpartners` — redirects to PBPartners
- `/marketing-page` — new-agent recruitment page
- `/api/fast-health` — health/config check
- `/api/quote-message` — converts agent-supplied quotation text into a customer message
- `/api/new-agent` — captures a new-agent lead
- `/api/daily-nurture` — controlled WhatsApp nurture batch

## Phase 1 scope

Keep quotation generation on PBPartners. Do not reproduce PBPartners pricing logic. The AI should read the agent-supplied quotation and create a professional follow-up.

## Production next step

Move agent/lead/activity state from in-memory storage to PostgreSQL after the first live test. The API contracts in `fast_launch.py` are intentionally small so this migration can be done without changing the agent-facing workflow.
