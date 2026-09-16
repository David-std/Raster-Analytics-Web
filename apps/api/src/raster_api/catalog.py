from raster_api.domain.models import PeriodMetadata, SpatialUnitMetadata

SPATIAL_UNITS: tuple[SpatialUnitMetadata, ...] = (
    SpatialUnitMetadata(
        spatial_unit_id="cercado-de-lima",
        name="Cercado de Lima",
        unit_type="area",
        latitude=-12.0464,
        longitude=-77.0428,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="la-victoria",
        name="La Victoria",
        unit_type="area",
        latitude=-12.0678,
        longitude=-77.0150,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="san-isidro",
        name="San Isidro",
        unit_type="area",
        latitude=-12.0977,
        longitude=-77.0365,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="miraflores",
        name="Miraflores",
        unit_type="area",
        latitude=-12.1219,
        longitude=-77.0299,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="santiago-de-surco",
        name="Santiago de Surco",
        unit_type="area",
        latitude=-12.1456,
        longitude=-76.9919,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="san-miguel",
        name="San Miguel",
        unit_type="area",
        latitude=-12.0776,
        longitude=-77.0884,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="los-olivos",
        name="Los Olivos",
        unit_type="area",
        latitude=-11.9912,
        longitude=-77.0708,
    ),
    SpatialUnitMetadata(
        spatial_unit_id="san-juan-de-lurigancho",
        name="San Juan de Lurigancho",
        unit_type="area",
        latitude=-11.9828,
        longitude=-77.0030,
    ),
)

PERIODS: tuple[PeriodMetadata, ...] = (
    PeriodMetadata(period_id="period-a", name="Period A"),
    PeriodMetadata(period_id="period-b", name="Period B"),
    PeriodMetadata(period_id="period-c", name="Period C"),
)


def spatial_units() -> list[SpatialUnitMetadata]:
    return [item.model_copy() for item in SPATIAL_UNITS]


def periods() -> list[PeriodMetadata]:
    return [item.model_copy() for item in PERIODS]


def has_period(period_id: str) -> bool:
    return any(item.period_id == period_id for item in PERIODS)
