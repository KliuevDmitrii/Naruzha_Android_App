import json
import allure


def assert_ok_json(
    r,
    expected_keys: list[str] | None = None,
    exact_keys: list[str] | None = None,
):
    # запрос/ответ уже приложены в Allure клиентом (NaruzhuApi._wrap)
    with allure.step("Assert status_code == 200"):
        assert r.status_code == 200, f"\nURL: {r.url}\nBODY:\n{r.text}"

    with allure.step("Assert Content-Type is JSON"):
        content_type = r.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"\nURL: {r.url}\nExpected JSON, got Content-Type: {content_type}"
        )

    with allure.step("Assert JSON is parsed"):
        assert r.json is not None, f"\nURL: {r.url}\nExpected JSON, got:\n{r.text}"

    body = r.json

    if expected_keys:
        with allure.step(f"Assert JSON contains keys: {expected_keys}"):
            for k in expected_keys:
                assert k in body, (
                    f"\nURL: {r.url}\nMissing key '{k}'\nJSON:\n{json.dumps(body, indent=2)}"
                )

    if exact_keys:
        with allure.step(f"Assert JSON has EXACT keys: {exact_keys}"):
            assert set(body.keys()) == set(exact_keys), (
                f"\nURL: {r.url}\nExpected keys: {exact_keys}\nActual keys: {list(body.keys())}"
            )

    return body


def assert_ok_data(r):
    """Успешный ответ client-api: HTTP 200, {data, error=null}. Возвращает data."""
    body = assert_ok_json(r, exact_keys=["data", "error"])

    with allure.step("Assert error is null"):
        assert body["error"] is None, f"\nURL: {r.url}\nJSON:\n{body}"

    return body["data"]


def assert_api_error(r, status: int, code: str):
    """Ошибка client-api: HTTP status, data = null, error.code = code. Возвращает error."""
    with allure.step(f"Assert HTTP {status}"):
        assert r.status_code == status, (
            f"\nURL: {r.url}\nExpected {status}, got {r.status_code}\nBODY:\n{r.text}"
        )

    with allure.step("Assert body is JSON {data, error}"):
        assert isinstance(r.json, dict), f"\nURL: {r.url}\nExpected JSON, got:\n{r.text[:500]}"
        assert set(r.json.keys()) == {"data", "error"}, f"\nURL: {r.url}\nKeys: {list(r.json.keys())}"
        assert r.json["data"] is None, f"\nURL: {r.url}\ndata must be null:\n{r.text}"

    error = r.json["error"]
    with allure.step(f"Assert error.code == {code}"):
        assert isinstance(error, dict), f"\nURL: {r.url}\nerror must be object:\n{r.text}"
        assert error.get("code") == code, f"\nURL: {r.url}\nExpected code {code}, got:\n{r.text}"
        assert error.get("localized_message"), f"\nURL: {r.url}\nEmpty localized_message:\n{r.text}"

    return error
