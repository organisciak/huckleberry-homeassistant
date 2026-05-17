"""Test Huckleberry component setup."""
from unittest.mock import patch

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from custom_components.huckleberry.const import DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.huckleberry import _sanitize_child_document_payload
from huckleberry_api.firebase_types import FirebaseChildDocument


async def test_setup_entry(hass: HomeAssistant, mock_huckleberry_api):
    """Test setting up the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test_password",
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.huckleberry.HuckleberryAPI",
        return_value=mock_huckleberry_api,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state.value == "loaded"
    assert len(hass.states.async_all()) > 0


def test_sanitize_child_document_payload_handles_nullable_sweetspot_values() -> None:
    """Test sanitization keeps child payload valid when sweetspot values are nullable."""
    payload = {
        "childsName": "Test Child",
        "lastInsightRequest": {"int": None},
        "sweetspot": {
            "selectedNapDay": "None",
            "sweetSpotTimes": {
                "0": "None",
                "1": 1700000000,
            },
        },
    }

    validated = FirebaseChildDocument.model_validate(
        _sanitize_child_document_payload(payload)
    )

    assert validated.lastInsightRequest is None
    assert validated.sweetspot is not None
    assert validated.sweetspot.selectedNapDay is None
    assert validated.sweetspot.sweetSpotTimes == {"1": 1700000000}
