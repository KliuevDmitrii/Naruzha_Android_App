# Naruzha Android App — автотесты

Автотесты VPN-клиента **Naruzhu**: API (client-api), SQL (PostgreSQL через SSH), Android (Appium) и Web.

## Быстрый старт

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy config\.example.env config\.env   # заполнить своими значениями
```

## Запуск

```bash
pytest -m api                                  # API
pytest -m db                                   # SQL (нужны SSH_* и DB_*)
pytest -m ui                                   # Android: Appium-сервер + устройство (UDID)
pytest -m web                                  # Web: нужен WEB_BASE_URL
pytest -m api --alluredir=allure-results && allure serve allure-results
```

Окружение выбирается переменной `ENV` в `config/.env`: `test` (по умолчанию), `test2`, `prod`.

## Структура

```
app/        клиенты и Page Objects (api, db, ui, web), без assert
config/     .example.env (шаблон) и .env (локально, не в git)
testdata/   test_data.json; runtime-данные пишутся в test_data.local.json
tests/      api/ db/ ui/ web/ + conftest.py и helpers/
utils/      конфиг, тест-данные, ожидания, Allure-вложения
```

Подробные правила — в [CLAUDE.md](CLAUDE.md), рецепты — в [SKILLS.md](SKILLS.md).
