from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .api import QianhaiPowerData
from .const import DATA_COORDINATOR, DOMAIN


@dataclass(frozen=True, kw_only=True)
class QianhaiPowerSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[QianhaiPowerData], float | int | str | None]
    attrs_fn: Callable[[QianhaiPowerData], dict[str, Any]] | None = None
    step: int | None = None


SENSORS: tuple[QianhaiPowerSensorEntityDescription, ...] = (
    QianhaiPowerSensorEntityDescription(
        key="latest_bill",
        translation_key="latest_bill",
        value_fn=lambda data: data.latest_bill_month,
        attrs_fn=lambda data: _latest_bill_attributes(data),
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_month",
        translation_key="bill_month",
        value_fn=lambda data: data.latest_bill.amount_month
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="latest_bill_amount",
        translation_key="latest_bill_amount",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill_amount,
    ),
    QianhaiPowerSensorEntityDescription(
        key="latest_bill_usage",
        translation_key="latest_bill_usage",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.latest_bill_usage,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_owe",
        translation_key="bill_owe",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.owe if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_lock_owe",
        translation_key="bill_lock_owe",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.lock_owe if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_total_fee",
        translation_key="bill_total_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.total_fee if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_owe_flag",
        translation_key="bill_owe_flag",
        value_fn=lambda data: data.latest_bill.owe_flag if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_user_no",
        translation_key="bill_user_no",
        value_fn=lambda data: data.latest_bill.user_no if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_elec_cust_no",
        translation_key="bill_elec_cust_no",
        value_fn=lambda data: data.latest_bill.elec_cust_no if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_user_name",
        translation_key="bill_user_name",
        value_fn=lambda data: data.latest_bill.user_name if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_address",
        translation_key="bill_address",
        value_fn=lambda data: data.latest_bill.address if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_user_category",
        translation_key="bill_user_category",
        value_fn=lambda data: data.latest_bill.ele_user_category
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_type",
        translation_key="bill_type",
        value_fn=lambda data: data.latest_bill.is_electricity_bill
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_price",
        translation_key="bill_price",
        value_fn=lambda data: data.latest_bill.price if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_electricity_sort",
        translation_key="bill_electricity_sort",
        value_fn=lambda data: data.latest_bill.electricity_sort
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_last_read_date",
        translation_key="bill_last_read_date",
        value_fn=lambda data: data.latest_bill.last_read_date
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_current_read_date",
        translation_key="bill_current_read_date",
        value_fn=lambda data: data.latest_bill.current_read_date
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_metering_point_no",
        translation_key="bill_metering_point_no",
        value_fn=lambda data: data.latest_bill.metering_point_no
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_work_order_no",
        translation_key="bill_work_order_no",
        value_fn=lambda data: data.latest_bill.work_order_no
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_receivable_account_sn",
        translation_key="bill_receivable_account_sn",
        value_fn=lambda data: data.latest_bill.receivable_account_sn
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_electricity_fee",
        translation_key="bill_electricity_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.electricity_fee
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_base_fee",
        translation_key="bill_base_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.base_fee if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_additional_fee",
        translation_key="bill_additional_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.additional_fee
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_power_adjust_fee",
        translation_key="bill_power_adjust_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.power_adjust_fee
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_refund_fee",
        translation_key="bill_refund_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.refund_fee if data.latest_bill else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_reduction_fee",
        translation_key="bill_reduction_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.reduction_fee
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_previous_meter_reading",
        translation_key="bill_previous_meter_reading",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data: data.latest_bill.previous_meter_reading
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_current_meter_reading",
        translation_key="bill_current_meter_reading",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data: data.latest_bill.current_meter_reading
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_meter_multiplier",
        translation_key="bill_meter_multiplier",
        value_fn=lambda data: data.latest_bill.meter_multiplier
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_meter_asset_no",
        translation_key="bill_meter_asset_no",
        value_fn=lambda data: data.latest_bill.meter_asset_no
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_meter_read_type",
        translation_key="bill_meter_read_type",
        value_fn=lambda data: data.latest_bill.meter_read_type
        if data.latest_bill
        else None,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step1_power",
        translation_key="bill_step1_power",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.latest_bill.step1_power if data.latest_bill else None,
        step=1,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step1_name",
        translation_key="bill_step1_name",
        value_fn=lambda data: data.latest_bill.step1_name if data.latest_bill else None,
        step=1,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step1_percent",
        translation_key="bill_step1_percent",
        value_fn=lambda data: data.latest_bill.step1_percent if data.latest_bill else None,
        step=1,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step1_fee",
        translation_key="bill_step1_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.step1_fee if data.latest_bill else None,
        step=1,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step1_price",
        translation_key="bill_step1_price",
        native_unit_of_measurement="CNY/kWh",
        value_fn=lambda data: data.latest_bill.step1_price if data.latest_bill else None,
        step=1,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step2_power",
        translation_key="bill_step2_power",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.latest_bill.step2_power if data.latest_bill else None,
        step=2,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step2_name",
        translation_key="bill_step2_name",
        value_fn=lambda data: data.latest_bill.step2_name if data.latest_bill else None,
        step=2,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step2_percent",
        translation_key="bill_step2_percent",
        value_fn=lambda data: data.latest_bill.step2_percent if data.latest_bill else None,
        step=2,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step2_fee",
        translation_key="bill_step2_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.step2_fee if data.latest_bill else None,
        step=2,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step2_price",
        translation_key="bill_step2_price",
        native_unit_of_measurement="CNY/kWh",
        value_fn=lambda data: data.latest_bill.step2_price if data.latest_bill else None,
        step=2,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step3_power",
        translation_key="bill_step3_power",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.latest_bill.step3_power if data.latest_bill else None,
        step=3,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step3_name",
        translation_key="bill_step3_name",
        value_fn=lambda data: data.latest_bill.step3_name if data.latest_bill else None,
        step=3,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step3_percent",
        translation_key="bill_step3_percent",
        value_fn=lambda data: data.latest_bill.step3_percent if data.latest_bill else None,
        step=3,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step3_fee",
        translation_key="bill_step3_fee",
        native_unit_of_measurement="CNY",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.latest_bill.step3_fee if data.latest_bill else None,
        step=3,
    ),
    QianhaiPowerSensorEntityDescription(
        key="bill_step3_price",
        translation_key="bill_step3_price",
        native_unit_of_measurement="CNY/kWh",
        value_fn=lambda data: data.latest_bill.step3_price if data.latest_bill else None,
        step=3,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DataUpdateCoordinator[QianhaiPowerData] = hass.data[DOMAIN][
        entry.entry_id
    ][DATA_COORDINATOR]
    async_add_entities(
        QianhaiPowerSensor(coordinator, entry, description) for description in SENSORS
    )


class QianhaiPowerSensor(CoordinatorEntity[DataUpdateCoordinator[QianhaiPowerData]], SensorEntity):
    entity_description: QianhaiPowerSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[QianhaiPowerData],
        entry: ConfigEntry,
        description: QianhaiPowerSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "前海供电",
        }
        if description.step is not None:
            self._attr_entity_registry_enabled_default = _step_is_available(
                coordinator.data,
                description.step,
            )

    @property
    def native_value(self) -> float | int | str | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if self.entity_description.attrs_fn:
            return _compact_attrs(self.entity_description.attrs_fn(data))

        attrs = {
            "user_no": data.user_no,
            "user_name": data.user_name,
            "address": data.address,
            "result_code": data.result_code,
            "result_message": data.result_message,
            "raw_top_keys": ", ".join(data.raw_top_keys),
            "raw_data_keys": ", ".join(data.raw_data_keys),
        }
        return _compact_attrs(attrs)


def _latest_bill_attributes(data: QianhaiPowerData) -> dict[str, Any]:
    bill = data.latest_bill
    if bill is None:
        return {
            "bill_count": data.bill_count,
            "result_code": data.result_code,
            "result_message": data.result_message,
            "raw_top_keys": ", ".join(data.raw_top_keys),
        }
    return {
        "bill_count": data.bill_count,
        "amount_month": bill.amount_month,
        "amount": bill.money,
        "usage": bill.power,
        "owe": bill.owe,
        "lock_owe": bill.lock_owe,
        "total_fee": bill.total_fee,
        "owe_flag": bill.owe_flag,
        "user_no": bill.user_no,
        "elec_cust_no": bill.elec_cust_no,
        "user_name": bill.user_name,
        "address": bill.address,
        "ele_user_category": bill.ele_user_category,
        "is_electricity_bill": bill.is_electricity_bill,
        "metering_point_no": bill.metering_point_no,
        "work_order_no": bill.work_order_no,
        "receivable_account_sn": bill.receivable_account_sn,
        "price": bill.price,
        "electricity_sort": bill.electricity_sort,
        "last_read_date": bill.last_read_date,
        "current_read_date": bill.current_read_date,
        "electricity_fee": bill.electricity_fee,
        "base_fee": bill.base_fee,
        "additional_fee": bill.additional_fee,
        "power_adjust_fee": bill.power_adjust_fee,
        "refund_fee": bill.refund_fee,
        "reduction_fee": bill.reduction_fee,
        "previous_meter_reading": bill.previous_meter_reading,
        "current_meter_reading": bill.current_meter_reading,
        "meter_multiplier": bill.meter_multiplier,
        "meter_asset_no": bill.meter_asset_no,
        "meter_read_type": bill.meter_read_type,
        "step1_power": bill.step1_power,
        "step1_name": bill.step1_name,
        "step1_percent": bill.step1_percent,
        "step1_fee": bill.step1_fee,
        "step1_price": bill.step1_price,
        "step2_power": bill.step2_power,
        "step2_name": bill.step2_name,
        "step2_percent": bill.step2_percent,
        "step2_fee": bill.step2_fee,
        "step2_price": bill.step2_price,
        "step3_power": bill.step3_power,
        "step3_name": bill.step3_name,
        "step3_percent": bill.step3_percent,
        "step3_fee": bill.step3_fee,
        "step3_price": bill.step3_price,
        "raw_bill_keys": ", ".join(bill.raw.keys()),
        "result_code": data.result_code,
        "result_message": data.result_message,
    }


def _compact_attrs(attrs: dict[str, Any]) -> dict[str, Any] | None:
    compacted = {
        key: value
        for key, value in attrs.items()
        if value not in (None, "")
    }
    return compacted or None


def _step_is_available(data: QianhaiPowerData, step: int) -> bool:
    bill = data.latest_bill
    if bill is None:
        return step == 1

    values = (
        getattr(bill, f"step{step}_power", None),
        getattr(bill, f"step{step}_fee", None),
        getattr(bill, f"step{step}_price", None),
        getattr(bill, f"step{step}_name", None),
        getattr(bill, f"step{step}_percent", None),
    )
    return any(value not in (None, "") for value in values)
