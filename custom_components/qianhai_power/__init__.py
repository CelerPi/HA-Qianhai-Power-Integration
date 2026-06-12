from __future__ import annotations

from datetime import datetime
import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import QianhaiPowerApiClient, QianhaiPowerApiError
from .const import (
    CONF_BASE_URL,
    CONF_JSESSIONID,
    CONF_MONTHS,
    CONF_OPEN_ID,
    CONF_PAY_TYPE,
    CONF_SETTLE_ACCT_NO,
    CONF_TOKEN,
    CONF_USER_NO,
    DATA_COORDINATOR,
    DEFAULT_BASE_URL,
    DEFAULT_MONTHS,
    DEFAULT_PAY_TYPE,
    DOMAIN,
    MONTHLY_REFRESH_DAY,
    MONTHLY_REFRESH_HOUR,
    MONTHLY_REFRESH_MINUTE,
)

PLATFORMS = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = QianhaiPowerApiClient(
        session,
        base_url=entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        open_id=entry.data[CONF_OPEN_ID],
        settle_acct_no=entry.data[CONF_SETTLE_ACCT_NO],
        user_no=entry.data.get(CONF_USER_NO),
        pay_type=entry.data.get(CONF_PAY_TYPE, DEFAULT_PAY_TYPE),
        token=entry.data.get(CONF_TOKEN),
        jsessionid=entry.data.get(CONF_JSESSIONID),
        months=entry.data.get(CONF_MONTHS, DEFAULT_MONTHS),
    )

    async def async_update_data():
        try:
            return await client.async_fetch()
        except QianhaiPowerApiError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
    )
    await coordinator.async_config_entry_first_refresh()
    _async_track_monthly_refresh(hass, entry, coordinator)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _async_track_monthly_refresh(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: DataUpdateCoordinator,
) -> None:
    remove_listener: Callable[[], None] | None = None
    cancelled = False

    def schedule_next(now: datetime | None = None) -> None:
        nonlocal remove_listener
        if cancelled:
            return
        refresh_at = _next_monthly_refresh(now or dt_util.now())

        def handle_refresh(fired_at: datetime) -> None:
            hass.async_create_task(coordinator.async_request_refresh())
            schedule_next(fired_at)

        remove_listener = async_track_point_in_time(hass, handle_refresh, refresh_at)

    def cancel_refresh() -> None:
        nonlocal cancelled
        cancelled = True
        if remove_listener is not None:
            remove_listener()

    schedule_next()
    entry.async_on_unload(cancel_refresh)


def _next_monthly_refresh(now: datetime) -> datetime:
    candidate = now.replace(
        day=MONTHLY_REFRESH_DAY,
        hour=MONTHLY_REFRESH_HOUR,
        minute=MONTHLY_REFRESH_MINUTE,
        second=0,
        microsecond=0,
    )
    if candidate > now:
        return candidate

    year = now.year
    month = now.month + 1
    if month > 12:
        year += 1
        month = 1
    return candidate.replace(year=year, month=month)
