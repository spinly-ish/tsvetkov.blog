# Directus stand

CMS-слой для tsvetkov.blog. Источник правды для постов и метаданных.

## Структура

- `docker-compose.yml` — локальный стенд (Directus + Postgres) для прототипирования.
- `.env.example` — шаблон переменных окружения. Копируется в `.env` и заполняется.
- `apply_schema.py` — скрипт-провижионер: создаёт коллекции `posts` и `site_config`, поля, роли через Directus REST API. Идемпотентный — повторный запуск ничего не ломает.
- `RAILWAY.md` — гайд деплоя продакшен-стенда на Railway.

## Локальный запуск

```bash
cd infra/directus
cp .env.example .env
# отредактируй .env: подставь сильные пароли, сгенерируй ключи через openssl rand -hex 32
docker compose up -d
open http://localhost:8055
# залогинься с ADMIN_EMAIL/ADMIN_PASSWORD из .env
```

После того как админ доступен:

```bash
# Применить схему
DIRECTUS_URL=http://localhost:8055 \
DIRECTUS_TOKEN=<статический токен из UI: User → Token> \
python3 apply_schema.py
```

Скрипт создаст:
- коллекцию `site_config` (singleton);
- коллекцию `posts` со всеми полями и индексом по `slug`;
- роль `agent` с правами Create/Read/Update в `posts` и Read в `site_config`;
- роль `build` с правами Read только опубликованных постов.

Токены `agent` и `build` создаются вручную в Directus UI после прогона скрипта (см. Settings → Access Tokens).

## Дальше

Этапы миграции — см. `../../docs/План развития блога/10-cms-migration.md`.
