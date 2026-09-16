"""Model-independent feature coverage and transformation utilities."""

from pipelines.features.coverage import (
    AnalysisUnit,
    FeatureCoverageReport,
    SourceCoverageSemantics,
    build_district_units,
    build_grid_units,
    profile_source_coverage,
)

__all__ = [
    "AnalysisUnit",
    "FeatureCoverageReport",
    "SourceCoverageSemantics",
    "build_district_units",
    "build_grid_units",
    "profile_source_coverage",
]
