# SKILLS.md

Пошаговые рецепты для типовых задач в проекте. Правила и структура — в [CLAUDE.md](CLAUDE.md).

---

## 1. Добавить API-тест

1. Эндпоинта нет в `app/api/endpoints.py` → добавить константу в нужную группу.
2. Добавить метод в `NaruzhuApi` (`app/api/client.py`) по образцу существующих:
   ```python
   def get_something(self, public_request_id: str) -> ApiResponse:
       return self.request("GET", Endpoints.GET_SOMETHING, params={"public_request_id": public_request_id})
   ```
   Опциональные поля собирать через `_clean({...})` — `None` не уходит в запрос.
3. Данные — в `testdata/api_data.py` (статичные значения, наборы для `parametrize`, ожидаемые `error.code`).
   Данные аккаунта — фикстуры `public_request_id`, `public_user_id`, `account_email`, `account_otp`
   (из `testdata/test_data.local.json`, если не заданы — тест пропускается).
4. Тест в `tests/api/test_<группа>.py`:
   ```python
   @pytest.mark.api
   @allure.feature("API")
   @allure.story("<группа из коллекции>")
   @allure.title("<кейс>")
   def test_get_something_existing(api, public_request_id):
       data = assert_ok_data(api.get_something(public_request_id))
       assert data["field"], f"Unexpected data: {data}"
   ```
5. Негатив: `assert_api_error(r, 404, "vpnn_request_not_found")`. Кейс «несуществующая заявка» —
   просто строка в `NOT_FOUND_CASES` (`testdata/api_data.py`), тест писать не нужно.
   Без устройства — фикстура `api_without_device`, «новое устройство» — `api_new_device`,
   произвольное тело — `api.request("POST", Endpoints.X, json={...})`.
6. Ручка меняет данные (ключи, биллинг, письма) → `@pytest.mark.mutating` (на `ENV=prod` пропускается).
7. Известный баг/расхождение с докой → текст в `KNOWN_ISSUES` и `@pytest.mark.xfail(reason=..., strict=False)`.
8. Прогон: `pytest -m api -k get_something`; без меняющих данные: `pytest -m "api and not mutating"`.

## 2. Добавить SQL-проверку

Таблицы и связи — в docstring `app/db/queries.py`
(`users.id <- requests.user_id`, `requests.db_id <- amnesia_keys/request_actions/request_events.request_id`,
`wg_servers.id <- amnesia_keys.server_id`).

1. Готового метода в `NaruzhuDb` нет → запрос в `app/db/queries.py` на базе констант колонок:
   ```python
   ACTIVE_KEYS_BY_REQUEST_ID = text(
       f"SELECT {AMNESIA_KEYS_COLUMNS} FROM public.amnesia_keys "
       "WHERE request_id = :request_id AND status = 'active'"
   )
   ```
   и метод в `app/db/repository.py`:
   ```python
   def active_keys_by_request_id(self, request_id: int) -> List[Row]:
       return self._all(q.ACTIVE_KEYS_BY_REQUEST_ID, request_id=request_id)
   ```
2. Тест в `tests/db/` — фикстура `db`, маркер `db`; допустимые значения (статусы, типы) — в `testdata/db_data.py`.
3. Связка API -> БД — в `tests/e2e/` с маркерами `e2e`, `api`, `db` (и `mutating`, если API меняет данные).
   Пользователь без почтового ящика: регистрация через API, OTP — из БД:
   ```python
   from tests.helpers.accounts import register_account

   def test_something_for_new_user(api, db, faker):
       account = register_account(api, db, email=faker.email())   # API -> users -> requests.comments.otp_code -> check-email-otp
       row = db.request_by_public_id(account.public_request_id)
       ...
   ```
   Достаточно общего аккаунта на прогон — фикстуры `public_request_id` / `public_user_id` / `account_email`
   (при пустом `test_data.local.json` аккаунт создаётся сам). OTP по email — `db.otp_by_email(email)`.
4. Только `SELECT`, только bind-параметры (`:name`), без WHERE — с `:limit`. `client_private_key` не выводить.
5. Прогон: `pytest -m db`, сквозные: `pytest -m e2e` (нужны `SSH_*`, `DB_*` в `config/.env`; база выбирается по `ENV`).

## 3. Добавить Appium-экран (Page Object)

1. Локаторы — `app/ui/locators/<screen>_locators.py`:
   ```python
   from appium.webdriver.common.appiumby import AppiumBy

   class LoginLocators:
       EMAIL_INPUT = (AppiumBy.ID, "com.naruzhu.vpn:id/email")
       CONTINUE_BTN = (AppiumBy.ACCESSIBILITY_ID, "Continue")
   ```
   Приоритет: `ACCESSIBILITY_ID` → `ID` → `ANDROID_UIAUTOMATOR` → XPath (крайний случай).
2. Page Object — `app/ui/pages/<screen>_page.py`, наследует `app.base_page.BasePage`:
   ```python
   class LoginPage(BasePage):
       def enter_email(self, email: str) -> "LoginPage":
           self.type(LoginLocators.EMAIL_INPUT, email)
           return self
   ```
   Методы-действия возвращают следующий page или `self`. Без assert.
3. Ожидания — методы `BasePage` / `utils/waits.py`, не `time.sleep`.
4. Тест в `tests/ui/` с маркером `@pytest.mark.ui` и фикстурой `appium_driver`.
5. Перед прогоном: `appium` запущен, `adb devices` видит устройство, `UDID` в `.env` совпадает.
6. Инспекция локаторов: Appium Inspector или `adb shell uiautomator dump`.

## 4. Добавить Web-тест (кабинет)

1. В `config/.env` задать `WEB_BASE_URL` (пусто → web-тесты пропускаются), `WEB_BROWSER`, `WEB_HEADLESS`.
2. Page Objects — `app/web/pages/`, наследуют `WebBasePage` и задают `path = "/login"`; локаторы — `app/web/locators/` (`By.CSS_SELECTOR`, `By.ID`, ...).
3. Тесты — `tests/web/`, маркер `@pytest.mark.web`, фикстура `web_driver`.
4. Скриншот и page source при падении прикладываются в Allure автоматически (хук в `conftest.py`).

## 5. Оформить найденный баг

```
Заголовок: [Слой] Кратко: что не так при каком условии
Окружение: ENV=test, build/версия, устройство/браузер
Шаги:
  1. ...
Ожидаемо: ...
Фактически: ...
Доказательства: запрос/ответ (curl), SQL-выборка, скриншот/видео, логи (adb logcat)
Severity / Priority
```

## 6. Перед коммитом

- `pytest --collect-only -q` — всё собирается.
- Прогнать затронутый слой (`pytest -m api` и т.д.).
- В диффе нет `config/.env`, ключей, реальных email/OTP, `__pycache__`.
