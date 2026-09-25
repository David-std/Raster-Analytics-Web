"""Model-independent feature coverage and transformation utilities."""

from pipelines.features.coverage import (
    AnalysisUnit,
    FeatureCoverageReport,
    SourceCoverageSemantics,
    build_district_units,
    build_grid_units,
    profile_source_coverage,
)
from pipelines.features.transform import (
    CategorizedGeometry,
    FeatureComposition,
    FeatureValue,
    line_length_density,
    point_density,
    polygon_category_composition,
)

__all__ = [
    "AnalysisUnit",
    "CategorizedGeometry",
    "FeatureComposition",
    "FeatureCoverageReport",
    "FeatureValue",
    "SourceCoverageSemantics",
    "build_district_units",
    "build_grid_units",
    "line_length_density",
    "point_density",
    "polygon_category_composition",
    "profile_source_coverage",
]
