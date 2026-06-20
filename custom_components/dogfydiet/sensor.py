from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DogfyDietCoordinator


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _next_order(data: dict[str, Any]) -> dict[str, Any] | None:
    orders = data.get("orders", [])
    now = datetime.now()
    future = []
    for order in orders:
        date_str = order.get("deliveryDate")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.replace(tzinfo=None) >= now.replace(tzinfo=None):
                future.append((dt, order))
        except (ValueError, TypeError):
            continue
    if future:
        future.sort(key=lambda x: x[0])
        return future[0][1]
    return orders[0] if orders else None


def _dog_age(dog: dict[str, Any]) -> str | None:
    birth = dog.get("birthdate")
    if not birth:
        return None
    try:
        bd = datetime.fromisoformat(birth.replace("Z", "+00:00")).replace(tzinfo=None)
        now = datetime.now()
        months = (now.year - bd.year) * 12 + now.month - bd.month
        years = months // 12
        remaining = months % 12
        if years > 0:
            return f"{years}a {remaining}m"
        return f"{remaining}m"
    except (ValueError, TypeError):
        return None


def _dog_name(dog: dict[str, Any]) -> str:
    return dog.get("name") or "Perro"


@dataclass(frozen=True, kw_only=True)
class DogfyDietSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], StateType | datetime]
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SUBSCRIPTION_SENSORS: tuple[DogfyDietSensorDescription, ...] = (
    DogfyDietSensorDescription(
        key="subscription_status",
        translation_key="subscription_status",
        icon="mdi:card-account-details",
        value_fn=lambda data: data.get("subscription", {}).get("status"),
        attr_fn=lambda data: {
            "amount": data.get("subscription", {}).get("amount"),
            "delivery_company": data.get("subscription", {}).get("deliveryCompany"),
            "payment_cycle_weeks": data.get("subscription", {}).get(
                "paymentCycleWeeks"
            ),
            "orders_in_cycle": data.get("subscription", {}).get("ordersInCycle"),
            "conservation": data.get("subscription", {}).get("conservationMethod"),
        },
    ),
    DogfyDietSensorDescription(
        key="subscription_amount",
        translation_key="subscription_amount",
        icon="mdi:currency-eur",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        value_fn=lambda data: data.get("subscription", {}).get("amount"),
    ),
    DogfyDietSensorDescription(
        key="next_order_date",
        translation_key="next_order_date",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:package-variant-closed",
        value_fn=lambda data: _parse_date(
            (_next_order(data) or {}).get("deliveryDate")
        ),
        attr_fn=lambda data: _next_order_attrs(data),
    ),
    DogfyDietSensorDescription(
        key="next_order_status",
        translation_key="next_order_status",
        icon="mdi:truck-delivery",
        value_fn=lambda data: (_next_order(data) or {}).get("status"),
        attr_fn=lambda data: _next_order_attrs(data),
    ),
)

DOG_SENSORS: tuple[DogfyDietSensorDescription, ...] = (
    DogfyDietSensorDescription(
        key="dog_weight",
        translation_key="dog_weight",
        icon="mdi:scale",
        native_unit_of_measurement="kg",
        value_fn=lambda dog: dog.get("weight"),
    ),
    DogfyDietSensorDescription(
        key="dog_daily_grams",
        translation_key="dog_daily_grams",
        icon="mdi:food-variant",
        native_unit_of_measurement="g",
        value_fn=lambda dog: dog.get("dailyGrams"),
    ),
    DogfyDietSensorDescription(
        key="dog_age",
        translation_key="dog_age",
        icon="mdi:cake-variant",
        value_fn=lambda dog: _dog_age(dog),
        attr_fn=lambda dog: {
            "breed_code": dog.get("breedCode"),
            "gender": dog.get("gender"),
            "sterilized": dog.get("isSterilized"),
            "activity_level": dog.get("activityLevel"),
            "appetite_level": dog.get("appetiteLevel"),
            "shape": dog.get("shape"),
            "age_group": dog.get("ageGroup"),
        },
    ),
)


def _next_order_attrs(data: dict[str, Any]) -> dict[str, Any]:
    order = _next_order(data)
    if not order:
        return {}
    attrs: dict[str, Any] = {}
    if order.get("_id"):
        attrs["order_id"] = order["_id"]
    if order.get("isLastInCycle") is not None:
        attrs["last_in_cycle"] = order["isLastInCycle"]
    payment = order.get("payment", {})
    if isinstance(payment, dict) and payment.get("amount"):
        attrs["amount"] = payment["amount"]
    delivery = order.get("delivery", {})
    if isinstance(delivery, dict) and delivery.get("deliveryCompany"):
        attrs["delivery_company"] = delivery["deliveryCompany"]
    package = order.get("package", {})
    if isinstance(package, dict) and package.get("bagCount"):
        attrs["bag_count"] = package["bagCount"]
    return attrs


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DogfyDietCoordinator = entry.runtime_data

    entities: list[SensorEntity] = []

    for desc in SUBSCRIPTION_SENSORS:
        entities.append(DogfyDietSensor(coordinator, entry, desc))

    for dog in coordinator.data.get("dogs", []):
        for desc in DOG_SENSORS:
            entities.append(DogfyDietDogSensor(coordinator, entry, desc, dog))

    async_add_entities(entities)


class DogfyDietSensor(CoordinatorEntity[DogfyDietCoordinator], SensorEntity):
    entity_description: DogfyDietSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DogfyDietCoordinator,
        entry: ConfigEntry,
        description: DogfyDietSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Dogfy Diet",
            "manufacturer": "Dogfy Diet",
            "model": "Subscription",
        }

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator.data)
        return None


class DogfyDietDogSensor(CoordinatorEntity[DogfyDietCoordinator], SensorEntity):
    entity_description: DogfyDietSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DogfyDietCoordinator,
        entry: ConfigEntry,
        description: DogfyDietSensorDescription,
        dog: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._dog_id = dog.get("_id", "")
        self._attr_unique_id = f"{entry.entry_id}_{self._dog_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.entry_id}_{self._dog_id}")},
            "name": f"Dogfy Diet - {_dog_name(dog)}",
            "manufacturer": "Dogfy Diet",
            "model": "Dog",
        }

    def _get_dog_data(self) -> dict[str, Any]:
        for dog in self.coordinator.data.get("dogs", []):
            if dog.get("_id") == self._dog_id:
                return dog
        return {}

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self._get_dog_data())

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self._get_dog_data())
        return None
