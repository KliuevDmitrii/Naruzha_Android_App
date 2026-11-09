# CLAUDE.md

Проект автотестов для VPN-клиента **Naruzhu** (Android, пакет `com.naruzhu.vpn`).
Слои тестирования: **API** (client-api), **SQL** (PostgreSQL через SSH-туннель), **Appium** (Android UI), **Web** (кабинет — пока не реализован).

Репозиторий: https://github.com/KliuevDmitrii/Naruzha_Android_App (ветка `main`).

## Стек

- Python 3.11, pytest 9, allure-pytest
- `requests` — API-клиент
- `sqlalchemy` + `psycopg2-binary` + `sshtunnel` — доступ к БД
- `Appium-Python-Client` (UiAutomator2) — мобильные тесты
- `selenium` — web
- `python-dotenv`, `faker`

## Команды

```bash
# окружение (Windows, venv уже в корне проекта)
venv\Scripts\activate
pip install -r requirements.txt

# прогоны
pytest -m api                      # только API
pytest -m db                       # только SQL (нужен SSH-доступ)
pytest -m ui                       # Appium (нужен запущенный Appium-сервер + устройство)
pytest --collect-only -q           # проверить, что всё собирается
pytest -m api --alluredir=allure-results
allure serve allure-results
```

## Структура

```
app/                    # "что тестируем": клиенты и Page Objects, без assert-ов
  base_page.py          # BasePage — общая база для ui/ и web/ (find, tap, type, ...)
  api/client.py         # NaruzhuApi — по методу на ручку (через request()), возвращают ApiResponse
  api/endpoints.py      # пути эндпоинтов, группы = папки Insomnia-коллекции "VPNN client-api v1"
  db/client.py          # DbClient — SSH-туннель + SQLAlchemy engine
  db/queries.py         # SQL-запросы (text()) для проверок
  ui/driver.py          # create_android_driver(config) — UiAutomator2 из cfg.appium
  ui/locators/          # локаторы экранов Android
  ui/pages/             # Page Objects Android (наследуют BasePage)
  web/driver.py         # create_web_driver(config) — Chrome/Firefox из cfg.web
  web/pages/            # Page Objects веб-кабинета (наследуют WebBasePage)
  web/locators/
config/
  .example.env          # шаблон и дефолты (в git)
  .env                  # локальные значения и секреты (НЕ в git)
testdata/
  api_data.py           # данные API-тестов: дефолты, parametrize-наборы, NOT_FOUND_CASES, KNOWN_ISSUES
  test_data.json        # шаблон данных тестового аккаунта (в git, пустой)
  test_data.local.json  # локальные/runtime-данные, сюда пишет DataProvider.save() (НЕ в git)
tests/
  conftest.py           # фикстуры: config, data, api, api_new_device, api_without_device, faker,
                        # public_request_id, public_user_id, account_email, account_otp, active_plan_id,
                        # db_engine, db_conn, appium_driver, web_driver; скриншот в Allure при падении;
                        # mutating-тесты пропускаются на ENV=prod
  helpers/              # переиспользуемые assert-хелперы (api_asserts.py)
  api/  db/  ui/  web/  # тесты по слоям (в каждой папке __init__.py)
utils/                  # ConfigProvider, DataProvider, waits, attachments, logger
```

## Конфигурация

- `ConfigProvider` грузит `config/.example.env`, затем `config/.env` поверх.
- `ENV=test | test2 | prod` выбирает `API_BASE_URL_TEST | API_BASE_URL_TEST_2 | API_BASE_URL`
  (test: `https://api.new.vpn-naruzhu.com`, test2: `https://api.new2.vpn-naruzhu.com`; адрес без `/client-api/v1`).
- Значения из `config/.env` перекрывают `.example.env` — смена URL в шаблоне не действует, если ключ задан в `.env`.
- Доступ к конфигу — только через `ConfigProvider` (`cfg.api`, `cfg.db`, `cfg.appium`), не через `os.getenv` в тестах.

## Правила для кода

- **Слои не смешиваются.** `app/` — клиенты и Page Objects без `assert`. Проверки — в `tests/` и `tests/helpers/`.
- **API:** новый эндпоинт → константа в `Endpoints` → метод в `NaruzhuApi` через `self.request(...)` (таймаут — `API_TIMEOUT`, Allure-вложения — автоматически). Формат ответа client-api: `{"data": ..., "error": {"code", "localized_message"}}`. Успех — `assert_ok_data(r)`, ошибка — `assert_api_error(r, status, code)`.
- **Тест-данные не хардкодить в тестах:** статичные — `testdata/api_data.py`, данные аккаунта — фикстуры из `test_data.local.json`, тариф — `active_plan_id`.
- **`@pytest.mark.mutating`** — на каждом тесте, который при успехе меняет данные стенда (ключи, биллинг, письма, отчёты). Известные баги — `xfail(strict=False)` с причиной из `KNOWN_ISSUES`.
- Позитивные тесты для `make-refund`, `set-free-status`, `change-server`, `gift-card-activation` не пишем без явного запроса — они необратимо меняют аккаунт.
- **SQL:** только чтение (`SELECT`). Запросы — в `app/db/queries.py` через `sqlalchemy.text()` с bind-параметрами, никакой конкатенации строк. Фикстура `db_conn` откатывает транзакцию после теста.
- **Appium / Web:** драйвер — только через фикстуры `appium_driver` / `web_driver`; UDID, пакет, URL не хардкодить в тестах. Ожидания — явные (`utils/waits.py`, методы `BasePage`), без `time.sleep`.
- **Маркеры обязательны:** каждый тест помечен `api` / `db` / `ui` / `web` / `e2e`; включён `--strict-markers`, новый маркер сначала добавить в `pytest.ini`.
- Новая папка с тестами — сразу с `__init__.py`, иначе одинаковые имена файлов (`test_smoke.py`) конфликтуют.
- **Allure:** `@allure.feature` = слой/модуль, `@allure.story` = сценарий, `@allure.title` = кейс; шаги через `with allure.step(...)`.
- Имена тестов: `test_<что>_<условие>` (например `test_request_email_verification_new_user`).
- Комментарии и сообщения в assert — можно на русском; идентификаторы — на английском.

## Безопасность

- Никогда не коммитить `config/.env`, ключи SSH, пароли БД, реальные OTP и email.
- Не запускать тесты, создающие данные или отправляющие письма, при `ENV=prod` без явного запроса.
- Не выполнять в БД `INSERT/UPDATE/DELETE/DDL`.
