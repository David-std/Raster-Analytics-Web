"""Model-independent feature coverage and transformation utilities."""

from pipelines.features.coverage import (
    AnalysisUnit,
    FeatureCoverageReport,
    SourceCoverageSemantics,
    build_district_units,
    build_grid_units,
    load_source_geometries,
    profile_loaded_source_coverage,
    profile_source_coverage,
)

__all__ = [
    "AnalysisUnit",
    "FeatureCoverageReport",
    "SourceCoverageSemantics",
    "build_district_units",
    "build_grid_units",
    "load_source_geometries",
    "profile_loaded_source_coverage",
    "profile_source_coverage",
]
