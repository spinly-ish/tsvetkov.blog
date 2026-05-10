# Деплой Directus на Railway — пошаговый гайд

Гайд предполагает, что **проект на Railway уже создан** и в нём подняты сервисы:

- **Postgres** (Railway add-on)
- **Directus** (из Docker image `directus/directus:11`)

Доменный регистратор — **Namecheap**, целевой поддомен — `cms.tsvetkov.blog`.

После прохождения всех шагов будет:
- работающий `https://cms.tsvetkov.blog/admin` с залогиненным админом,
- два токена (`build` и `agent`),
- готовая база с применённой схемой коллекций.

---

## Оглавление

1. [[#1. Сгенерировать KEY и SECRET]]
2. [[#2. Прописать переменные окружения у Directus]]
3. [[#3. Подключить Postgres к Directus]]
4. [[#4. Включить публичный URL Railway]]
5. [[#5. Добавить Volume для uploads]]
6. [[#6. Перезапустить и проверить, что Directus поднялся]]
7. [[#7. Подключить домен cms.tsvetkov.blog через Namecheap]]
8. [[#8. Привязать домен в Railway и дождаться SSL]]
9. [[#9. Первый логин в админку]]
10. [[#10. Создать роли agent и build (через apply_schema.py)]]
11. [[#11. Создать пользователей и static-токены]]
12. [[#12. Положить токены в нужные места]]
13. [[#13. Smoke-test через curl]]
14. [[#Что дальше]]

---

## 1. Сгенерировать KEY и SECRET

Directus требует две случайные 32-байтные hex-строки. На локальной машине:

```bash
openssl rand -hex 32   # это будет KEY
openssl rand -hex 32   # это будет SECRET
```

Сохрани обе в любой временный буфер (пейст-бад, заметка) — сразу понадобятся в шаге 2.

> **Что это такое.** `KEY` идентифицирует инстанс Directus (используется для кэша, очередей). `SECRET` — соль для подписи JWT-токенов сессий. Если поменять `SECRET`, все выданные сессии инвалидируются.

⬆ [[#Оглавление]]

---

## 2. Прописать переменные окружения у Directus

В Railway открой **Directus сервис → Variables**. Добавь следующие переменные (нажимай `+ New Variable` для каждой):

### Обязательные

| Переменная       | Значение                                    |
| ---------------- | ------------------------------------------- |
| `KEY`            | значение из шага 1                          |
| `SECRET`         | значение из шага 1                          |
| `ADMIN_EMAIL`    | `tsvetkov.evgenij@gmail.com`                |
| `ADMIN_PASSWORD` | сильный пароль, который сохрани в 1Password |

### Подключение к Postgres (см. шаг 3 — там подробнее про references)

| Переменная    | Значение                     |
| ------------- | ---------------------------- |
| `DB_CLIENT`   | `pg`                         |
| `DB_HOST`     | `${{ Postgres.PGHOST }}`     |
| `DB_PORT`     | `${{ Postgres.PGPORT }}`     |
| `DB_DATABASE` | `${{ Postgres.PGDATABASE }}` |
| `DB_USER`     | `${{ Postgres.PGUSER }}`     |
| `DB_PASSWORD` | `${{ Postgres.PGPASSWORD }}` |

> Если твой Postgres-сервис называется **не** `Postgres` (например, `postgres-db`) — подставь его имя в `${{ <ИмяСервиса>.PG... }}`.

### Сетевые / CORS

| Переменная           | Значение                                                                                            |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| `PUBLIC_URL`         | временно `https://<temp>.up.railway.app` (см. шаг 4), позже заменишь на `https://cms.tsvetkov.blog` |
| `CORS_ENABLED`       | `true`                                                                                              |
| `CORS_ORIGIN`        | `https://tsvetkov.blog,https://www.tsvetkov.blog`                                                   |
| `WEBSOCKETS_ENABLED` | `true`                                                                                              |
| `LOG_LEVEL`          | `info`                                                                                              |

После сохранения Railway автоматически перезапустит сервис.

> **Не сохраняй** перезапуск, пока не пропишешь все переменные DB_* — иначе Directus упадёт с ошибкой подключения к базе. Если Railway уже перезапустил — ничего страшного, после следующего сохранения он перезапустится снова и подхватит всё.

⬆ [[#Оглавление]]

---

## 3. Подключить Postgres к Directus

Railway позволяет ссылаться на переменные одного сервиса из другого через синтаксис `${{ <Service>.<VAR> }}`. Это удобно: если Postgres-пароль изменится — Directus подхватит новый автоматически.

**Как проверить, что reference работает:**
1. В Directus сервис → Variables найди свою переменную `DB_HOST`.
2. Справа должно быть зелёное значение типа `containers-us-west-XX.railway.app` (это резолвнутый PGHOST).
3. Если красное `<not found>` — значит имя сервиса в скобках не совпадает с реальным. Открой Postgres-сервис, посмотри его имя в верху страницы, и поправь references.

> **Важно.** В Railway переменные Postgres-сервиса (`PGHOST`, `PGPORT`, …) — это **внутренние private network** адреса. Directus и Postgres внутри одного Railway-проекта общаются по приватной сети без выхода в интернет — это и быстрее, и безопаснее.

⬆ [[#Оглавление]]

---

## 4. Включить публичный URL Railway

Прежде чем настраивать кастомный домен, нужен временный публичный URL — на нём проверим, что Directus вообще поднялся.

В Directus сервис → **Settings → Networking → Public Networking**:
1. Нажать `Generate Domain`.
2. Railway создаст что-то вроде `tsvetkov-blog-cms-production-xxxx.up.railway.app`.
3. **Скопируй этот URL** — он понадобится в шаге 7 для CNAME.
4. Вернись в Variables и поменяй `PUBLIC_URL` на этот сгенерированный URL (с `https://`).

⬆ [[#Оглавление]]

---

## 5. Добавить Volume для uploads

Без volume любые загруженные файлы (картинки, документы) пропадут при следующем деплое — потому что контейнер пересоздаётся.

В Directus сервис → **Settings → Volumes → New Volume**:
- **Mount path**: `/directus/uploads`
- **Size**: `1 GB` (достаточно на старте, потом можно увеличить)

> На первом этапе миграции картинки постов остаются в `/pics/` репозитория — volume пока не критичен. Но добавить лучше сразу, чтобы потом не переделывать.

⬆ [[#Оглавление]]

---

## 6. Перезапустить и проверить, что Directus поднялся

После сохранения переменных Railway автоматически перезапускает сервис. Открой вкладку **Deployments** у Directus сервис — должен идти новый билд.

Жди, пока статус не станет **Active** (обычно 30–90 секунд).

**Проверка:**
1. Открой временный URL из шага 4: `https://<temp>.up.railway.app/server/health`.
2. Должно вернуть JSON: `{"status":"ok"}`.
3. Открой `https://<temp>.up.railway.app/admin` — должна загрузиться страница логина Directus.

**Если не работает:**
- Открой **Deployments → последний → Logs**.
- Самые частые ошибки:
  - `getaddrinfo ENOTFOUND <pghost>` — неправильно прописана reference на Postgres (см. шаг 3).
  - `password authentication failed` — `DB_PASSWORD` reference резолвится в пустую строку.
  - `KEY and SECRET environment variables are required` — забыл шаг 1.

⬆ [[#Оглавление]]

---

## 7. Подключить домен cms.tsvetkov.blog через Namecheap

Заходим в Namecheap.

1. **Dashboard → Domain List → Manage** напротив `tsvetkov.blog`.
2. Сверху вкладки: `Domain | Products | Sharing & Transfer | Advanced DNS`. Открой **Advanced DNS**.
3. В разделе **Host Records** нажми `Add New Record`.
4. Заполни:
   - **Type**: `CNAME Record`
   - **Host**: `cms` (только поддомен, БЕЗ `.tsvetkov.blog`)
   - **Value**: тот URL из шага 4, **без** `https://` и **без** слэша в конце. Пример: `tsvetkov-blog-cms-production-xxxx.up.railway.app`
   - **TTL**: `Automatic` (или `5 min` для быстрой проверки)
5. Нажми зелёную галочку справа, чтобы сохранить.

> **Важно.** Если для основного домена `tsvetkov.blog` уже есть запись типа `URL Redirect` или `A Record` на `@` — её НЕ трогаем. Мы добавляем отдельную запись только для поддомена `cms`.

**Проверка распространения DNS** (с локальной машины):

```bash
dig cms.tsvetkov.blog CNAME +short
```

Должно вернуть `tsvetkov-blog-cms-production-xxxx.up.railway.app.` (с точкой в конце). Обычно у Namecheap распространение занимает 5–30 минут, иногда до часа.

Если возвращает пусто — подожди ещё, обновление DNS не мгновенное.

⬆ [[#Оглавление]]

---

## 8. Привязать домен в Railway и дождаться SSL

Когда `dig` уже возвращает CNAME (шаг 7) — возвращайся в Railway.

В Directus сервис → **Settings → Networking → Custom Domain**:
1. Нажми `+ Custom Domain`.
2. Введи: `cms.tsvetkov.blog`.
3. Railway покажет нужную DNS-запись для проверки. Если CNAME из шага 7 уже виден — Railway сразу подтвердит и начнёт выписывать Let's Encrypt сертификат.
4. Жди 1–5 минут. Когда статус станет **Active** с зелёной галочкой — сертификат выписан.

**После выписки сертификата:**
1. Вернись в **Variables** Directus сервис.
2. Поменяй `PUBLIC_URL` с временного `*.up.railway.app` на `https://cms.tsvetkov.blog`.
3. Сохрани — Railway снова перезапустит сервис.

**Финальная проверка:**

```bash
curl -I https://cms.tsvetkov.blog/server/health
```

Должно вернуть `HTTP/2 200`.

⬆ [[#Оглавление]]

---

## 9. Первый логин в админку

Открой `https://cms.tsvetkov.blog/admin`.

Залогинься:
- **Email**: `tsvetkov.evgenij@gmail.com`
- **Password**: тот, что сохранил в `ADMIN_PASSWORD`

После логина окажешься в пустой админке — коллекций пока нет. Это нормально, схему применим в шаге 10.

**Сразу создай static token для админа** (понадобится в шаге 10):

1. Кликни иконку профиля внизу слева → **Settings → User Directory** (или просто `Settings → My Profile`).
2. Открой свою карточку (Admin User).
3. Прокрути вниз до поля **Token**.
4. Нажми кнопку с генератором (иконка стрелочки/обновления) — Directus сгенерирует строку.
5. **Скопируй токен сейчас** (после сохранения он покажется в виде звёздочек, и достать его будет нельзя — только перегенерировать).
6. Нажми галочку «Сохранить» вверху справа.

Сохрани этот токен временно — назовём его `DIRECTUS_ADMIN_TOKEN`. Он используется только для применения схемы (шаг 10) и потом не нужен.

⬆ [[#Оглавление]]

---

## 10. Создать роли agent и build (через apply_schema.py)

Применить схему коллекций (`site_config`, `posts`) и создать роли (`agent`, `build`) можно одной командой с локальной машины:

```bash
cd /Users/evgeniytsvetkov/Desktop/workspace/Projects/tsvetkov.blog

DIRECTUS_URL=https://cms.tsvetkov.blog \
DIRECTUS_TOKEN=<DIRECTUS_ADMIN_TOKEN из шага 9> \
python3 infra/directus/apply_schema.py
```

Скрипт идемпотентный — если что-то не так, можно запускать повторно. Должен напечатать что-то вроде:

```
✓ collection 'site_config' created
✓ collection 'posts' created
✓ role 'agent' created (id=...)
✓ role 'build' created (id=...)
Schema applied.
```

**Проверка в админке:**
1. Открой `https://cms.tsvetkov.blog/admin/content` — слева должны появиться `Site Config` и `Posts`.
2. Открой `Settings → Access Control` — должны быть роли `Administrator`, `agent`, `build`.

⬆ [[#Оглавление]]

---

## 11. Создать пользователей и static-токены

В Directus 11 токены привязываются к пользователю. Создаём двух «технических» пользователей.

### 11.1. Пользователь `build` (для CI)

В админке:
1. **Settings → User Directory → + Create User** (плюсик вверху справа).
2. Заполни:
   - **First Name**: `Build`
   - **Last Name**: `CI`
   - **Email**: `build@tsvetkov.blog` (фейковый, не используется для логина)
   - **Password**: можно оставить пустым (логин по токену)
   - **Role**: `build` (выбрать из выпадашки)
   - **Status**: `Active`
3. Прокрути вниз → поле **Token** → сгенерируй и **скопируй сразу**.
4. Сохрани (галочка вверху справа).

Сохрани токен как `DIRECTUS_BUILD_TOKEN`.

### 11.2. Пользователь `agent` (для меня и других агентов)

То же самое:
- **First Name**: `Agent`
- **Last Name**: `Claude`
- **Email**: `agent@tsvetkov.blog`
- **Role**: `agent`
- **Token**: сгенерируй, сохрани как `DIRECTUS_AGENT_TOKEN`.

⬆ [[#Оглавление]]

---

## 12. Положить токены в нужные места

### 12.1. `DIRECTUS_BUILD_TOKEN` → GitHub Secrets

1. Открой репозиторий на GitHub: `https://github.com/<твой-username>/tsvetkov.blog`.
2. **Settings → Secrets and variables → Actions → New repository secret**.
3. Добавь два секрета:
   - **Name**: `DIRECTUS_URL`, **Value**: `https://cms.tsvetkov.blog`
   - **Name**: `DIRECTUS_BUILD_TOKEN`, **Value**: токен из шага 11.1

> CI workflow уже подготовлен (`.github/workflows/deploy.yml`): когда оба секрета доступны, билд автоматически переключается на `--source=directus`. Пока секреты не заданы — собирает по-старому из `data/posts.json`.

### 12.2. `DIRECTUS_AGENT_TOKEN` → локально (для меня и агентов)

Сохрани локально, чтобы я (и другие агенты) могли работать с CMS:

```bash
mkdir -p ~/.config/tsvetkov-blog
cat > ~/.config/tsvetkov-blog/agent.env <<EOF
DIRECTUS_URL=https://cms.tsvetkov.blog
DIRECTUS_AGENT_TOKEN=<токен из шага 11.2>
EOF
chmod 600 ~/.config/tsvetkov-blog/agent.env
```

> **Не коммить** этот файл. Он лежит вне репо специально.

### 12.3. `DIRECTUS_ADMIN_TOKEN` (из шага 9) — можно отозвать

Админский токен использовался только для применения схемы. После шага 10 его можно безопасно удалить:
- В админке → Settings → My Profile → поле Token → стереть → Сохранить.

⬆ [[#Оглавление]]

---

## 13. Smoke-test через curl

Проверим, что роли и токены работают как задумано.

> **Важно для zsh** (дефолтный shell macOS). Символ `?` zsh пытается раскрыть как glob — поэтому **все URL с query-string оборачивай в кавычки**: `"https://...?limit=1"`. Без кавычек получишь `zsh: no matches found`.

Сначала экспортируй токены в текущую сессию:

```bash
export DIRECTUS_BUILD_TOKEN="<токен из шага 11.1>"
export DIRECTUS_AGENT_TOKEN="<токен из шага 11.2>"
```

### 13.1. Build-токен видит коллекцию `posts`

```bash
curl -H "Authorization: Bearer $DIRECTUS_BUILD_TOKEN" \
  "https://cms.tsvetkov.blog/items/posts?limit=1"
```

Должно вернуть `{"data":[]}` (постов ещё нет, но запрос проходит — значит роль настроена).

### 13.2. Agent-токен умеет создавать пост

Коллекция `posts` помечает много полей как обязательные (это намеренно, чтобы CMS не позволяла сохранять полупустые посты). Поэтому payload включает все required-поля:

```bash
curl -X POST \
  -H "Authorization: Bearer $DIRECTUS_AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "test",
    "date": "2026-05-10",
    "read_time_min": 1,
    "image": "/pics/test.jpg",
    "status": "draft",
    "title_en": "Test",
    "title_ru": "Тест",
    "description_en": "Test description",
    "description_ru": "Тестовое описание",
    "excerpt_en": "Test excerpt",
    "excerpt_ru": "Тестовый отрывок",
    "image_alt_card_en": "Test alt card",
    "image_alt_card_ru": "Тест alt карточки",
    "image_alt_post_en": "Test alt post",
    "image_alt_post_ru": "Тест alt поста",
    "body_md_en": "Test body",
    "body_md_ru": "Тестовое тело"
  }' \
  "https://cms.tsvetkov.blog/items/posts"
```

Должно вернуть JSON созданного поста, начинающийся с `{"data":{"id":...}}`. Скопируй `id` из ответа.

Удали тестовый пост:

```bash
curl -X DELETE \
  -H "Authorization: Bearer $DIRECTUS_AGENT_TOKEN" \
  "https://cms.tsvetkov.blog/items/posts/<id из ответа>"
```

DELETE возвращает 204 No Content — пустой ответ = успех.

### 13.3. Без токена — 403

```bash
curl -i "https://cms.tsvetkov.blog/items/posts"
```

Должно вернуть `403 Forbidden` (или `401`). Это значит, что публичная роль не имеет доступа к `posts` — ровно как настроено в `apply_schema.py`.

⬆ [[#Оглавление]]

---

## Что дальше

После того как все 13 шагов прошли — пиши мне в чате: **«Directus готов»** + URL и подтверждение, что есть оба токена.

Я подхвачу с шага миграции контента:

1. **Миграция постов** — `python3 scripts/migrate_to_directus.py` перельёт 12 постов из `data/posts.json` (метаданные + HTML тела, конвертированные в Markdown).
2. **Smoke-test build** — `python3 scripts/build.py --source=directus` локально, сравним shasum с текущим выводом, чтобы убедиться, что HTML не отличается.
3. **Маркеры BUILD:BODY** — `python3 scripts/add_body_markers.py` оборачивает тела всех 24 HTML-файлов маркерами, чтобы `build.py` мог их обновлять.
4. **Коммит** — маркеры + `data/snapshot.json` в `main`.
5. **Cutover в CI** — после того как ты добавил GitHub secrets, любой push (или ручной `Run workflow`) пересоберёт сайт уже из Directus.
6. **Webhook в Directus** → GitHub `repository_dispatch` (`event_type: directus_publish`), чтобы публикация поста через CMS сама запускала пересборку сайта.

После шага 6 — миграция завершена.

⬆ [[#Оглавление]]

---

## Бэкапы

- **Railway Pro план** — daily backups Postgres из коробки.
- **Hobby план** — бэкапов нет, придётся настраивать `pg_dump` руками. Сделаем после Этапа 5, если решим, что нужно.

## Стоимость

- **Hobby** ($5/мес): хватит для Directus + Postgres на старте.
- **Pro** ($20/мес): нужен для бэкапов и без auto-sleep.

## Откат

Если что-то пошло не так — удали проект на Railway. Картинки в `/pics/` и сам репо при этом остаются нетронуты, сайт продолжает работать на `data/posts.json` (CI собирает старым способом, пока секреты `DIRECTUS_*` не заданы).
