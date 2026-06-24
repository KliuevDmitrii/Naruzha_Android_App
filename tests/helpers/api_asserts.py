import json
import allure

def assert_ok_json(
    r,
    expected_keys: list[str] | None = None,
    exact_keys: list[str] | None = None,
):
    with allure.step("Attach raw response"):
        allure.attach(r.url, name="URL", attachment_type=allure.attachment_type.TEXT)
        allure.attach(str(r.status_code), name="Status Code", attachment_type=allure.attachment_type.TEXT)
        allure.attach(r.text, name="Response Body", attachment_type=allure.attachment_type.TEXT)

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