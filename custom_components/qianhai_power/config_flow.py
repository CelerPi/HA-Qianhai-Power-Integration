from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_BASE_URL,
    CONF_JSESSIONID,
    CONF_MONTHS,
    CONF_OPEN_ID,
    CONF_PAY_TYPE,
    CONF_SETTLE_ACCT_NO,
    CONF_TOKEN,
    CONF_USER_NO,
    DEFAULT_BASE_URL,
    DEFAULT_MONTHS,
    DEFAULT_PAY_TYPE,
    DOMAIN,
)


class QianhaiPowerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SETTLE_ACCT_NO])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"前海供电 {user_input[CONF_SETTLE_ACCT_NO]}",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Required(CONF_OPEN_ID): str,
                vol.Required(CONF_SETTLE_ACCT_NO): str,
                vol.Optional(CONF_USER_NO): str,
                vol.Optional(CONF_PAY_TYPE, default=DEFAULT_PAY_TYPE): str,
                vol.Optional(CONF_TOKEN): str,
                vol.Optional(CONF_JSESSIONID): str,
                vol.Optional(CONF_MONTHS, default=DEFAULT_MONTHS): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=24)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
