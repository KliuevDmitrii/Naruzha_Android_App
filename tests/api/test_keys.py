import allure
import pytest

from app.api.client import NaruzhuApi
from testdata import api_data as td
from tests.helpers.api_asserts import assert_api_error, assert_ok_data


@pytest.mark.api
@allure.feature("API")
@allure.story("Keys (AWG)")
class TestKeys:
    """Выдача AWG-ключей: download-awg-key, download-physical-awg-key, download-anonymous-key."""

    @pytest.mark.parametrize("version", td.INVALID_AWG_VERSIONS)
    @allure.title("Invalid X-Supported-Awg-Version is rejected")
    def test_download_awg_key_invalid_awg_version(self, config, version):
        api = NaruzhuApi(config, awg_version=version)
        assert_api_error(api.download_awg_key(td.NONEXISTENT_ID), 400, "invalid_awg_version")

    @allure.title("download-awg-key without X-Device-Id gets device_id error")
    def test_download_awg_key_without_device(self, api_without_device):
        assert_api_error(api_without_device.download_awg_key(td.NONEXISTENT_ID), 400, "device_id")

    @allure.title("check-change-server without X-Device-Id gets device_id error")
    def test_check_change_server_without_device(self, api_without_device):
        assert_api_error(api_without_device.check_change_server(td.NONEXISTENT_ID), 400, "device_id")

    @pytest.mark.mutating
    @pytest.mark.parametrize("version", td.AWG_VERSIONS)
    @allure.title("download-awg-key returns config file for supported AWG version")
    def test_download_awg_key_success(self, config, public_request_id, version):
        api = NaruzhuApi(config, awg_version=version)
        r = api.download_awg_key(public_request_id, force_update_device=True)

        if isinstance(r.json, dict) and (r.json.get("error") or {}).get("code") == td.NO_SERVER_ERROR_CODE:
            pytest.skip(f"No available server for AWG {version} on this stand")

        with allure.step("Assert HTTP 200"):
            assert r.status_code == 200, f"\nURL: {r.url}\nBODY:\n{r.text[:500]}"

        with allure.step("Assert response is a config file"):
            assert "attachment" in r.headers.get("Content-Disposition", ""), f"Headers: {r.headers}"
            assert "[Interface]" in r.text, f"Not a WireGuard/AWG config:\n{r.text[:300]}"

    @allure.title("check-change-server returns availability flag")
    def test_check_change_server_flag(self, api, public_request_id):
        data = assert_ok_data(api.check_change_server(public_request_id))
        assert isinstance(data["is_change_server_available"], bool), f"Unexpected data: {data}"
