"""puckling — a Python port of Facebook's Duckling for English and Arabic."""

from __future__ import annotations

from puckling.api import (
    Context,
    DimensionName,
    Entity,
    Options,
    ResolvedEntity,
    ResolvedValue,
    TemperatureResolvedValue,
    analyze,
    parse,
    supported_dimensions,
)
from puckling.dimensions.amount_of_money.types import AmountOfMoneyValue
from puckling.dimensions.credit_card.types import CreditCardValue
from puckling.dimensions.distance.types import DistanceUnit, DistanceValue
from puckling.dimensions.duration.types import DurationValue, NormalizedDuration
from puckling.dimensions.email.types import EmailValue
from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.ordinal.types import OrdinalValue
from puckling.dimensions.phone_number.types import PhoneNumberValue
from puckling.dimensions.quantity.types import QuantityValue
from puckling.dimensions.temperature.types import (
    TemperatureIntervalDirection,
    TemperatureIntervalValue,
    TemperatureOpenIntervalValue,
    TemperatureUnit,
    TemperatureValue,
)
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalDirection,
    IntervalValue,
    OpenIntervalValue,
    TimeValue,
)
from puckling.dimensions.url.types import UrlValue
from puckling.dimensions.volume.types import VolumeUnit, VolumeValue
from puckling.locale import Lang, Locale, Region

__all__ = [
    "AmountOfMoneyValue",
    "Context",
    "CreditCardValue",
    "DimensionName",
    "DistanceUnit",
    "DistanceValue",
    "DurationValue",
    "EmailValue",
    "Entity",
    "Grain",
    "InstantValue",
    "IntervalDirection",
    "IntervalValue",
    "Lang",
    "Locale",
    "NormalizedDuration",
    "NumeralValue",
    "OpenIntervalValue",
    "Options",
    "OrdinalValue",
    "PhoneNumberValue",
    "QuantityValue",
    "Region",
    "ResolvedEntity",
    "ResolvedValue",
    "TemperatureIntervalDirection",
    "TemperatureIntervalValue",
    "TemperatureOpenIntervalValue",
    "TemperatureResolvedValue",
    "TemperatureUnit",
    "TemperatureValue",
    "TimeValue",
    "UrlValue",
    "VolumeUnit",
    "VolumeValue",
    "analyze",
    "parse",
    "supported_dimensions",
]

__version__ = "0.1.0"
