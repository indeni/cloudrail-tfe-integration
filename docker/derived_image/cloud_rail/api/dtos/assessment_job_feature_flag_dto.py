from enum import Enum


class AssessmentJobFeatureFlagDTO(int, Enum):
    FEATURE_FLAG_A = 1 << 0
    FEATURE_FLAG_B = 1 << 1
    FEATURE_FLAG_C = 1 << 2
    FEATURE_FLAG_D = 1 << 3
