# SKILLS.md

Пошаговые рецепты для типовых задач в проекте. Правила и структура — в [CLAUDE.md](CLAUDE.md).

---

## 1. Добавить API-тест

1. Эндпоинта нет в `app/api/endpoints.py` → добавить константу в нужную группу.
2. Добавить метод в `NaruzhuApi` (`app/api/client.py`) по образцу существующих:
   ```python
   def get_something(self, public_request_id: str) -> ApiResponse:
       return self._request("GET", Endpoints.GET_SOMETHING, params={"public_request_id": public_request_id})
   ```
3. Тест в `tests/api/test_<модуль>.py`:
   ```python
   @pytest.mark.api
   @allure.feature("API")
   @allure.story("<сценарий>")
   @allure.title("<кейс>")
   def test_get_something_valid_id(api, data):
       with allure.step("Send get-something"):
           r = api.get_something(data.get("runtime.public_request_id"))
       body = assert_ok_json(r, exact_keys=["data", "error"])
       assert body["error"] is None, f"\nURL: {r.url}\nJSON:\n{body}"
   ```
4. Негативные кейсы: пустые/невалидные параметры, без заголовков, чужой `public_request_id` — проверять код ответа и `error`.
5. Прогон: `pytest -m api -k get_something`.

## 2. Добавить SQL-проверку

1. Запрос в `app/db/queries.py`:
   ```python
   from sqlalchemy import text

   USER_BY_EMAIL = text("SELECT id, email, created_at FROM users WHERE email = :email")
   ```
2. Тест в `tests/db/test_<сущность>.py` с фикстурой `db_conn`:
   ```python
   @pytest.mark.db
   def test_user_created_after_verification(api, db_conn, faker):
       email = faker.email()
       api.request_email_verification(email=email)
       row = db_conn.execute(queries.USER_BY_EMAIL, {"email": email}).mappings().first()
       assert row is not None, f"User {email} not found in DB"
   ```
3. Только `SELECT`, только bind-параметры (`:name`). Связка API → БД — типовой e2e-паттерн.
4. Прогон: `pytest -m db` (нужны `SSH_*` и `DB_*` в `config/.env`).

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
