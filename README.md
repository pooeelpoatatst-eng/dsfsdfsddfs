# Hosted Telegram Userbot Service

Single-worker, multi-user Telegram userbot service for Railway. A standard Bot API control bot manages encrypted Telegram user sessions; each connected account gets its own Telethon client and isolated runtime.

## Security warning

Telegram user sessions grant high-level access to the connected account. Protect PostgreSQL and `SESSION_ENCRYPTION_KEY`, keep Railway variables private, and never export the database. This service stores only Fernet-encrypted StringSessions. It does not store login codes, 2FA passwords, or ordinary message history.

## Architecture

- `app/control_bot`: aiogram control plane and login FSM.
- `app/userbot`: independently managed Telethon clients, outgoing pipeline, command registry, per-chat modes and rate limits.
- `app/database`: SQLAlchemy async models/repositories and Alembic migration.
- `app/services`: shared AI, encryption and SSRF validation services.

One Railway worker is appropriate for an MVP / limited number of active accounts. Horizontal scaling later needs sharding and distributed session ownership.

## Telegram prerequisites

Create the normal **control bot** with [@BotFather](https://t.me/BotFather) and set its token as `CONTROL_BOT_TOKEN`.

Create one Telegram application for the service at `my.telegram.org`; set `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`. Connecting users never enter API credentials themselves.

## Environment

Copy `.env.example` to `.env` and set:

```dotenv
CONTROL_BOT_TOKEN=
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/userbot
SESSION_ENCRYPTION_KEY=
AI_API_KEY=
AI_BASE_URL=https://codex.sale/v1
AI_MODEL=gpt-5.4-mini
```

Generate a Fernet key once and preserve it permanently; changing it makes existing encrypted sessions unreadable:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Local setup

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

Use PostgreSQL, not SQLite: this project uses PostgreSQL JSONB columns. `DATABASE_URL` must use the `postgresql+asyncpg://` dialect locally. Railway's injected URL may need this scheme changed from `postgres://` to `postgresql+asyncpg://`.

## Railway deployment

1. Create a GitHub repository and push this project (never push `.env`).
2. Railway: **New Project** -> **Deploy from GitHub**.
3. Add a PostgreSQL service.
4. Add all variables from `.env.example`; set `DATABASE_URL` to the PostgreSQL connection URL using `postgresql+asyncpg://`.
5. Generate and set `SESSION_ENCRYPTION_KEY` using the command above.
6. Deploy. The Docker command applies `alembic upgrade head` before starting the persistent worker.

## First account connection

1. Open the control bot and send `/start`.
2. Press **Connect Telegram**.
3. Send the phone number, then the Telegram code; send 2FA password only when requested.
4. Input messages containing these secrets are deleted when Telegram permits it. The password is never persisted.
5. The session is encrypted, saved to PostgreSQL, and its isolated Telethon client starts.

## Implemented commands

- Core: `.help`, `.kawaii`, `.switch`, `.bold`, `.italic`, `.underline`, `.strike`, `.monospace`, `.spoiler`, `.sw`, `.leet`, `.love`, `.type`, `.ping`, `.core`.
- Automation: per-chat/global kawaii mode, `//` escape, local/AI hybrid transformation, AFK direct-message reply and configurable AI replies.
- Personal AI style: `.afkai prompt <описание>`, `.afkai learn [1-400]`, `.afkai on|off|status`. Learning here means a private style context made from the owner's own chat messages; it is not a model fine-tune.
- AI tools: `.ai`, `.sum`, `.replyai`, `.rewrite`, `.translate`, `.explain`, `.tasks`, `.planai`, `.proofread`, `.ideas`.
- Music: `.ym <Yandex Music track URL>` resolves a public audio result and sends the file in the current chat. `.ymplaylist set <public Yandex Music playlist URL>` then `.randomtrack` chooses a random playlist entry and sends it as audio.
- Games: `.flip`, `.dice`, `.ttt`, `.2048`, `.rps`, `.guess`, `.wordly`. Interactive games are inline messages sent from the connected account (`via @control_bot`) in the same chat; enable Inline Mode for the control bot in @BotFather once.

`.kawaii` is persistent for the current chat. Ordinary later outgoing messages are edited; `.kawaii off` disables it. `//message` sends the message without transformation.

## Current MVP boundary

Media transcoding, moderation, external weather/currency providers, downloader endpoints, announcements, persistent game sessions across a process restart, and further games remain outside this version. They are intentionally not registered as fake commands.

## Troubleshooting

- `SESSION_ENCRYPTION_KEY must be a valid Fernet key`: generate a valid key above.
- Account shows disconnected after restart: Telegram may have revoked the session; reconnect through the control bot.
- AI unavailable: Kawaii leaves the original outgoing message unchanged. Short messages and explicit `.kawaii local` use the local transformer.
- Telegram FloodWait: the operation is rate-limited; the process and other users continue running.
- Interactive game is not sent: enable Inline Mode once in @BotFather for the control bot (Bot Settings → Inline Mode). Inline messaging can then work in both private chats and groups.
