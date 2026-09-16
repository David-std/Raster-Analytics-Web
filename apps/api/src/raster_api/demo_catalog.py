"""Synthetic catalog used only by the mock vertical slice.

The names and representative points let the frontend exercise a Lima map. They do not
establish the final spatial unit, temporal granularity, study sample, or analytical result.
"""

from raster_api.domain.models import PeriodMetadata, SpatialUnitMetadata

DEMO_SPATIAL_UNITS: tuple[SpatialUnitMetadata, ...] = (
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-01",
        name="Cercado de Lima",
        unit_type="demo-point",
        latitude=-12.0464,
        longitude=-77.0428,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-02",
        name="La Victoria",
        unit_type="demo-point",
        latitude=-12.0678,
        longitude=-77.0150,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-03",
        name="San Isidro",
        unit_type="demo-point",
        latitude=-12.0977,
        longitude=-77.0365,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-04",
        name="Miraflores",
        unit_type="demo-point",
        latitude=-12.1219,
        longitude=-77.0299,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-05",
        name="Santiago de Surco",
        unit_type="demo-point",
        latitude=-12.1456,
        longitude=-76.9919,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-06",
        name="San Miguel",
        unit_type="demo-point",
        latitude=-12.0776,
        longitude=-77.0884,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-07",
        name="Los Olivos",
        unit_type="demo-point",
        latitude=-11.9912,
        longitude=-77.0708,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="demo-lima-08",
        name="San Juan de Lurigancho",
        unit_type="demo-point",
        latitude=-11.9828,
        longitude=-77.0030,
    ),
)

DEMO_PERIODS: tuple[PeriodMetadata, ...] = (
    PeriodMetadata(period_id="demo-period-a", name="Periodo demo A"),
    PeriodMetadata(period_id="demo-period-b", name="Periodo demo B"),
    PeriodMetadata(period_id="demo-period-c", name="Periodo demo C"),
)


def spatial_units() -> list[SpatialUnitMetadata]:
    return [item.model_copy() for item in DEMO_SPATIAL_UNITS]


def periods() -> list[PeriodMetadata]:
    return [item.model_copy() for item in DEMO_PERIODS]


def has_period(period_id: str) -> bool:
    return any(item.period_id == period_id for item in DEMO_PERIODS)
