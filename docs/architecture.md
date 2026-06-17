# Architecture Notes

## Current Entity Surface Baseline

The integration currently uses `weather.twc` as the primary weather entity and can create a large optional companion sensor surface for dashboards, adapter cards, and optional TWC endpoint families.

As of the rearchitecture baseline, enabling every optional group creates:

| Group | Entity count |
| --- | ---: |
| Weather entity | 1 |
| Current detail sensors | 31 |
| Forecast adapter sensors | 110 |
| Pollen sensors | 25 |
| Tropical summary sensors | 4 |
| Air quality sensors | 27 |
| **Total** | **198** |

These counts are intentionally captured in tests before the architecture rework begins. Future sprints should update the baseline only when they intentionally reduce or reshape the entity surface.

## Rearchitecture Direction

The target architecture is to make `weather.twc` the main user-facing entity and treat companion sensors as optional support surfaces.

The core goals are:

- Keep a normal install low-noise, ideally with only `weather.twc` enabled by default.
- Split refresh coordination by data family so optional endpoint failures do not affect core weather updates.
- Align the weather entity with Home Assistant core weather integrations by using separate observation, daily forecast, and hourly forecast coordinators.
- Mark high-cardinality, duplicated, or dashboard-adapter sensors as disabled by default.
- Keep optional endpoint families, such as pollen, air quality, and tropical weather, isolated and clearly documented.

## Reference Pattern

Home Assistant core's AccuWeather integration is the closest reference for this rework. The relevant patterns are:

- separate observation, daily forecast, and hourly forecast coordinators;
- `CoordinatorWeatherEntity` for the weather platform;
- `DeviceInfo` for grouping entities under a service device;
- entity translation keys and stable unique IDs;
- forecast sensors created only when the provider payload contains the source key;
- non-essential sensors marked with `entity_registry_enabled_default=False`.
